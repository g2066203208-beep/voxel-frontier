from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def one(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected 1 match, got {n}")
    return text.replace(old, new, 1)


def alln(text, old, new, expected, label):
    n = text.count(old)
    if n != expected:
        raise RuntimeError(f"{label}: expected {expected} matches, got {n}")
    return text.replace(old, new)

# -----------------------------------------------------------------------------
# PlanetCamera: additive start-direction parameter only. Existing callers retain V7 default.
# No movement, attitude transport, gravity, frame transition or controller logic is changed.
# -----------------------------------------------------------------------------
p = ROOT / "native/include/vf/player/PlanetCamera.hpp"
s = p.read_text(encoding="utf-8")
s = one(
    s,
    "        const PlanetDefinition& planet,\n        const CelestialSystem* celestialSystem = nullptr,\n        std::uint32_t primaryCelestialBodyId = 0U);\n",
    "        const PlanetDefinition& planet,\n        const CelestialSystem* celestialSystem = nullptr,\n        std::uint32_t primaryCelestialBodyId = 0U,\n        const glm::dvec3& startDirection = glm::dvec3{0.72, 0.52, 0.46});\n",
    "PlanetCamera additive spawn parameter",
)
p.write_text(s, encoding="utf-8")

p = ROOT / "native/src/player/PlanetCamera.cpp"
s = p.read_text(encoding="utf-8")
s = one(
    s,
    "    const PlanetDefinition& planet,\n    const CelestialSystem* celestialSystem,\n    std::uint32_t primaryCelestialBodyId)\n",
    "    const PlanetDefinition& planet,\n    const CelestialSystem* celestialSystem,\n    std::uint32_t primaryCelestialBodyId,\n    const glm::dvec3& startDirectionInput)\n",
    "PlanetCamera definition spawn parameter",
)
s = one(
    s,
    "    const glm::dvec3 startDirection = safeNormalize({0.72, 0.52, 0.46});\n",
    "    const glm::dvec3 startDirection = safeNormalize(startDirectionInput, {0.72, 0.52, 0.46});\n",
    "PlanetCamera use supplied spawn direction",
)
p.write_text(s, encoding="utf-8")

# -----------------------------------------------------------------------------
# Main: deterministic safe-land selection; keep all V7 camera/physics systems intact.
# -----------------------------------------------------------------------------
p = ROOT / "native/src/app/Main.cpp"
s = p.read_text(encoding="utf-8")
s = one(s, "#include <iostream>\n#include <sstream>\n", "#include <iostream>\n#include <limits>\n#include <sstream>\n", "Main include limits")
anchor = '''[[nodiscard]] double circularOrbitSpeed(double parentMassKg, double radiusMeters) {
    return std::sqrt(vf::CelestialSystem::kGravitationalConstant * parentMassKg / std::max(1.0, radiusMeters));
}
'''
helper = anchor + r'''

[[nodiscard]] glm::dvec3 findPlayableSpawnDirection(const vf::PlanetDefinition& planet) {
    // Deterministic Fibonacci-sphere scan. This does not alter the terrain seed: it only chooses a
    // gentle, inland point on the already-authoritative V7 planet so the first frame demonstrates
    // terrain rather than dropping the player into the global ocean.
    constexpr std::uint32_t sampleCount = 1536U;
    constexpr double goldenAngle = 2.39996322972865332223;
    const glm::dvec3 preferred = safeNormalize({0.72, 0.52, 0.46});
    glm::dvec3 best = preferred;
    double bestScore = -std::numeric_limits<double>::infinity();
    bool found = false;

    for (std::uint32_t i = 0; i < sampleCount; ++i) {
        const double y = 1.0 - 2.0 * (static_cast<double>(i) + 0.5)
            / static_cast<double>(sampleCount);
        const double radial = std::sqrt(std::max(0.0, 1.0 - y * y));
        const double a = goldenAngle * static_cast<double>(i);
        const glm::dvec3 d{std::cos(a) * radial, y, std::sin(a) * radial};
        const vf::PlanetTerrainSample terrain = vf::samplePlanetTerrain(planet, d);
        const double aboveSea = terrain.elevationMeters - planet.seaLevelElevationMeters;
        if (aboveSea < 80.0 || terrain.submerged(planet)) continue;
        if (terrain.mountain > 0.62 || terrain.volcano > 0.68 || terrain.trench > 0.05) continue;

        const glm::dvec3 normal = vf::planetSurfaceNormal(planet, d);
        const double radialAlignment = glm::dot(normal, d);
        if (radialAlignment < 0.955) continue;

        const double altitudePreference = 1.0 - std::clamp(std::abs(aboveSea - 420.0) / 2200.0, 0.0, 1.0);
        const double oldRegionPreference = 0.5 + 0.5 * glm::dot(d, preferred);
        const double score = radialAlignment * 2.4
            + altitudePreference * 0.75
            + oldRegionPreference * 0.20
            + terrain.plateau * 0.10
            + terrain.river * 0.08
            - terrain.mountain * 0.70
            - terrain.volcano * 0.80;
        if (!found || score > bestScore) {
            bestScore = score;
            best = d;
            found = true;
        }
    }
    return safeNormalize(best, preferred);
}
'''
s = one(s, anchor, helper, "insert deterministic safe spawn search")
s = one(
    s,
    "        vf::PlanetCamera camera{planet, &celestial, asterId};\n",
    "        const glm::dvec3 spawnDirection = findPlayableSpawnDirection(planet);\n"
    "        const vf::PlanetTerrainSample spawnTerrain = vf::samplePlanetTerrain(planet, spawnDirection);\n"
    "        vf::PlanetCamera camera{planet, &celestial, asterId, spawnDirection};\n"
    "        std::cout << \"Spawn land elevation: \" << std::fixed << std::setprecision(1)\n"
    "                  << spawnTerrain.elevationMeters << \" m\\n\";\n",
    "use safe land spawn",
)
s = one(
    s,
    "                {4096.0,       0.0, 256U, 0.00, 0.12},\n",
    "                {4096.0,       0.0, 320U, 0.00, 0.10},\n",
    "increase walking-scale ring density",
)
s = one(
    s,
    "            for (auto& vertex : oceanProxy.vertices) {\n                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));\n                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));\n            }\n",
    "            for (auto& vertex : oceanProxy.vertices) {\n                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));\n                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));\n                vertex.material.w = -20.0F;\n            }\n",
    "tag global ocean separately from local ocean",
)
p.write_text(s, encoding="utf-8")

# -----------------------------------------------------------------------------
# PlanetSurface: add real 50-200 m geometry detail; tag terrain for shader material synthesis.
# -----------------------------------------------------------------------------
p = ROOT / "native/src/world/PlanetSurface.cpp"
s = p.read_text(encoding="utf-8")
s = one(
    s,
    "    const double micro = fbmSurface(definition.seed ^ 0x3C6EF372FE94F82BULL, w, 13500.0, 2);\n",
    "    const double micro = fbmSurface(definition.seed ^ 0x3C6EF372FE94F82BULL, w, 52000.0, 2);\n"
    "    const double fine = fbmSurface(definition.seed ^ 0xA54FF53A5F1D36F1ULL, w, 125000.0, 2);\n",
    "move geometry detail into visible human-scale band",
)
s = one(
    s,
    "        + micro * 0.00075\n        + (ridged - 0.5) * 0.0022 * mountain)\n",
    "        + micro * (0.00105 + 0.00055 * mountain)\n"
    "        + fine * 0.00034\n"
    "        + (ridged - 0.5) * 0.0022 * mountain)\n",
    "add micro/fine geometry amplitudes",
)
s = one(
    s,
    "        0.52 * regional + 0.34 * local + 0.14 * micro,\n",
    "        0.42 * regional + 0.28 * local + 0.20 * micro + 0.10 * fine,\n",
    "blend surface detail channels",
)
# terrain material returns use w=-1 as an internal terrain tag; water remains x<0.
s = one(
    s,
    "    if (sample.submerged(definition)) return {0.0F, 0.91F, 0.0F, 0.0F};\n",
    "    if (sample.submerged(definition)) return {0.0F, 0.91F, 0.0F, -1.0F};\n",
    "tag submerged terrain",
)
s = one(
    s,
    "    return {0.0F, roughness, 0.0F, 0.0F};\n",
    "    return {0.0F, roughness, 0.0F, -1.0F};\n",
    "tag land terrain",
)
s = alln(
    s,
    "vertex.color = {0.018F, 0.145F, 0.255F};",
    "vertex.color = {0.020F, 0.205F, 0.315F};",
    2,
    "deepen stylized ocean base color",
)
p.write_text(s, encoding="utf-8")

# -----------------------------------------------------------------------------
# Shader: object-space procedural material + exclusive local/global water + water backface reject.
# -----------------------------------------------------------------------------
p = ROOT / "native/shaders/planet.slang"
s = p.read_text(encoding="utf-8")
s = one(
    s,
    "    float4 shadowPosition : TEXCOORD4;\n};\n",
    "    float4 shadowPosition : TEXCOORD4;\n    float3 objectPosition : TEXCOORD5;\n};\n",
    "pass object-space position",
)
s = one(
    s,
    "    output.shadowPosition = mul(gScene.lightViewProjection, float4(relativePosition, 1.0));\n    return output;\n",
    "    output.shadowPosition = mul(gScene.lightViewProjection, float4(relativePosition, 1.0));\n"
    "    output.objectPosition = input.position;\n"
    "    return output;\n",
    "write object-space position",
)
noise_anchor = '''float hash31(float3 p)
{
    p = frac(p * 0.1031);
    p += dot(p, p.yzx + 33.33);
    return frac((p.x + p.y) * p.z);
}
'''
noise_add = noise_anchor + r'''

float valueNoise2(float2 p)
{
    float2 i = floor(p);
    float2 f = frac(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash21(i);
    float b = hash21(i + float2(1.0, 0.0));
    float c = hash21(i + float2(0.0, 1.0));
    float d = hash21(i + float2(1.0, 1.0));
    return lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);
}

float terrainFbm2(float2 p)
{
    float n = valueNoise2(p) * 0.58;
    n += valueNoise2(p * 2.07 + 19.37) * 0.28;
    n += valueNoise2(p * 4.21 - 7.11) * 0.14;
    return n;
}
'''
s = one(s, noise_anchor, noise_add, "insert terrain pixel noise")

s = one(
    s,
    "    bool waterMaterial = input.material.x < -0.5;\n    float metallic = waterMaterial ? 0.0 : saturate(input.material.x);\n",
    "    bool waterMaterial = input.material.x < -0.5;\n"
    "    bool terrainMaterial = !waterMaterial && input.material.w < -0.5;\n"
    "    float metallic = waterMaterial ? 0.0 : saturate(input.material.x);\n",
    "detect terrain material tag",
)
s = one(
    s,
    "    float3 baseColor = max(input.color, 0.0);\n\n    if (waterMaterial)\n",
    "    float3 baseColor = max(input.color, 0.0);\n\n"
    "    if (terrainMaterial)\n"
    "    {\n"
    "        // Object-space noise stays attached to the planet as it rotates/recenters. Large color\n"
    "        // masses dominate; mid-scale variation enriches them; fine grain is deliberately weak.\n"
    "        float2 q = input.objectPosition.xz;\n"
    "        float macro = terrainFbm2(q * 0.0045);\n"
    "        float medium = terrainFbm2(q * 0.0145 + 31.7);\n"
    "        float fine = valueNoise2(q * 0.045 + 8.9);\n"
    "        float value = (macro - 0.5) * 0.18 + (medium - 0.5) * 0.085 + (fine - 0.5) * 0.028;\n"
    "        float warmPatch = smoothstep(0.58, 0.84, macro);\n"
    "        baseColor *= 1.0 + value;\n"
    "        baseColor = lerp(baseColor, baseColor * float3(1.035, 1.005, 0.945), warmPatch * 0.18);\n"
    "        roughness = clamp(roughness + (medium - 0.5) * 0.055, 0.62, 0.98);\n"
    "    }\n\n"
    "    if (waterMaterial)\n",
    "add pixel-scale procedural terrain material",
)
s = one(
    s,
    "        float3 stablePosition = input.relativePosition + gPush.data0.xyz;\n        float2 p = stablePosition.xz * 0.00135;\n",
    "        float2 p = input.objectPosition.xz * 0.00175;\n",
    "attach water micro normals to object space",
)
s = one(
    s,
    "            float3 shallowScatter = baseColor * (0.20 + 0.32 * saturate(n.y * 0.5 + 0.5));\n",
    "            float3 shallowScatter = baseColor * (0.58 + 0.28 * saturate(n.y * 0.5 + 0.5));\n",
    "increase readable water body color",
)
s = one(
    s,
    "    float opticalOpacity = waterMaterial\n        ? saturate(0.24 + fresnel * 0.70)\n",
    "    if (waterMaterial && dot(n, v) <= 0.015) discard;\n\n"
    "    float opticalOpacity = waterMaterial\n"
    "        ? saturate(0.66 + fresnel * 0.32)\n",
    "water backface reject and opacity",
)
old_fade = '''    // -10 marks the one high-resolution local ocean patch.  Fade it before its finite patch edge
    // reaches the geometric horizon; the single global geoid remains underneath at all altitudes.
    if (waterMaterial && input.material.w < -9.0)
    {
        float localOceanFade = 1.0 - smoothstep(12000.0, 30000.0, max(gPush.data0.w, 0.0));
        opticalOpacity *= localOceanFade;
        if (opticalOpacity < 0.004) discard;
    }
'''
new_fade = '''    // Keep only one effective water representation at walking altitude. The local patch fades out
    // as the global geoid fades in, preventing transparent-shell stacking and horizon banding.
    if (waterMaterial)
    {
        float cameraAltitude = max(gPush.data0.w, 0.0);
        if (input.material.w < -19.0)
            opticalOpacity *= smoothstep(18000.0, 34000.0, cameraAltitude);
        else if (input.material.w < -9.0)
            opticalOpacity *= 1.0 - smoothstep(14000.0, 30000.0, cameraAltitude);
        if (opticalOpacity < 0.004) discard;
    }
'''
s = one(s, old_fade, new_fade, "exclusive local/global ocean fade")
p.write_text(s, encoding="utf-8")

print("V8 R2 patch applied: safe land spawn + human-scale relief + procedural terrain material + single-layer water")
