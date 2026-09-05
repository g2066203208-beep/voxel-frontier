from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one regex match, found {count}")
    return updated


# -----------------------------------------------------------------------------
# 1) Planet terrain authority: keep V7 tectonics, add seamless local detail only.
# -----------------------------------------------------------------------------
hpp = ROOT / "native/include/vf/world/PlanetSurface.hpp"
text = hpp.read_text(encoding="utf-8")
text = replace_once(
    text,
    "    double river{};\n    double oceanDepthMeters{};\n",
    "    double river{};\n    // Seamless deterministic sub-regional detail used by both geometry and procedural material.\n"
    "    // This remains subordinate to the plate/continental morphology above.\n"
    "    double surfaceDetail{};\n    double oceanDepthMeters{};\n",
    "PlanetTerrainSample surfaceDetail",
)
hpp.write_text(text, encoding="utf-8")

cpp = ROOT / "native/src/world/PlanetSurface.cpp"
text = cpp.read_text(encoding="utf-8")

smooth_block = """[[nodiscard]] double smooth01(double edge0, double edge1, double value) noexcept {
    if (edge1 <= edge0) return value >= edge1 ? 1.0 : 0.0;
    const double x = std::clamp((value - edge0) / (edge1 - edge0), 0.0, 1.0);
    return x * x * (3.0 - 2.0 * x);
}
"""
noise_helpers = smooth_block + r'''

[[nodiscard]] double quintic(double x) noexcept {
    x = std::clamp(x, 0.0, 1.0);
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0);
}

[[nodiscard]] std::uint64_t latticeBits(
    std::uint64_t seed,
    std::int64_t x,
    std::int64_t y,
    std::int64_t z) noexcept {
    std::uint64_t h = seed ^ 0xD6E8FEB86659FD93ULL;
    h ^= static_cast<std::uint64_t>(x) * 0x9E3779B185EBCA87ULL;
    h ^= static_cast<std::uint64_t>(y) * 0xC2B2AE3D27D4EB4FULL;
    h ^= static_cast<std::uint64_t>(z) * 0x165667B19E3779F9ULL;
    h ^= h >> 29U;
    h *= 0x94D049BB133111EBULL;
    h ^= h >> 31U;
    return h;
}

[[nodiscard]] double latticeValue(
    std::uint64_t seed,
    std::int64_t x,
    std::int64_t y,
    std::int64_t z) noexcept {
    const std::uint64_t bits = latticeBits(seed, x, y, z);
    const double unit = static_cast<double>(bits & 0xFFFFFFULL)
        / static_cast<double>(0xFFFFFFULL);
    return unit * 2.0 - 1.0;
}

[[nodiscard]] double valueNoise3(
    std::uint64_t seed,
    const glm::dvec3& p) noexcept {
    const auto x0 = static_cast<std::int64_t>(std::floor(p.x));
    const auto y0 = static_cast<std::int64_t>(std::floor(p.y));
    const auto z0 = static_cast<std::int64_t>(std::floor(p.z));
    const double tx = quintic(p.x - static_cast<double>(x0));
    const double ty = quintic(p.y - static_cast<double>(y0));
    const double tz = quintic(p.z - static_cast<double>(z0));

    const auto lerpD = [](double a, double b, double t) noexcept {
        return a + (b - a) * t;
    };

    const double n000 = latticeValue(seed, x0,     y0,     z0);
    const double n100 = latticeValue(seed, x0 + 1, y0,     z0);
    const double n010 = latticeValue(seed, x0,     y0 + 1, z0);
    const double n110 = latticeValue(seed, x0 + 1, y0 + 1, z0);
    const double n001 = latticeValue(seed, x0,     y0,     z0 + 1);
    const double n101 = latticeValue(seed, x0 + 1, y0,     z0 + 1);
    const double n011 = latticeValue(seed, x0,     y0 + 1, z0 + 1);
    const double n111 = latticeValue(seed, x0 + 1, y0 + 1, z0 + 1);

    const double nx00 = lerpD(n000, n100, tx);
    const double nx10 = lerpD(n010, n110, tx);
    const double nx01 = lerpD(n001, n101, tx);
    const double nx11 = lerpD(n011, n111, tx);
    return lerpD(lerpD(nx00, nx10, ty), lerpD(nx01, nx11, ty), tz);
}

[[nodiscard]] double fbmSurface(
    std::uint64_t seed,
    const glm::dvec3& direction,
    double baseFrequency,
    int octaves) noexcept {
    double amplitude = 1.0;
    double frequency = baseFrequency;
    double sum = 0.0;
    double normalization = 0.0;
    for (int octave = 0; octave < octaves; ++octave) {
        const std::uint64_t octaveSeed = seedBits(seed, 4000U + static_cast<std::uint64_t>(octave) * 29U);
        sum += valueNoise3(octaveSeed, direction * frequency) * amplitude;
        normalization += amplitude;
        frequency *= 2.07;
        amplitude *= 0.48;
    }
    return normalization > 0.0 ? sum / normalization : 0.0;
}
'''
text = replace_once(text, smooth_block, noise_helpers, "insert seamless value-noise helpers")

old_detail = r'''    // Multi-scale residual roughness is intentionally subordinate to the tectonic morphology. It
    // supplies local ridges/valleys and abyssal hills without deciding where continents or trenches
    // exist.
    const double regional = std::sin(w.x * 190.0 + w.z * 157.0 + p4)
        * std::cos(w.y * 173.0 - w.x * 117.0 + p5);
    const double local = std::sin(w.x * 1030.0 + w.y * 730.0 + p2)
        * std::cos(w.z * 910.0 - w.x * 570.0 + p1);
    elevation += maxLand * (0.018 * regional + 0.006 * local) * landness;
    elevation += maxOcean * (0.006 * regional + 0.002 * local) * oceanness;
'''
new_detail = r'''    // Seamless 3D fBm is evaluated on the normalized sphere, so there are no longitude/cube-face
    // seams.  It adds the human-scale relief that the old ~40 km trigonometric residual could not
    // provide, while remaining much smaller than the tectonic mountain/trench signal.
    const double regional = fbmSurface(definition.seed ^ 0x6A09E667F3BCC909ULL, w, 720.0, 3);
    const double local = fbmSurface(definition.seed ^ 0xBB67AE8584CAA73BULL, w, 3200.0, 3);
    const double micro = fbmSurface(definition.seed ^ 0x3C6EF372FE94F82BULL, w, 13500.0, 2);
    const double ridged = 1.0 - std::abs(local);
    const double protectedDrainage = 1.0 - 0.74 * river;
    const double landRelief = (
        regional * (0.0030 + 0.0065 * mountain + 0.0028 * plateau)
        + local * (0.0016 + 0.0040 * mountain)
        + micro * 0.00075
        + (ridged - 0.5) * 0.0022 * mountain)
        * protectedDrainage;
    elevation += maxLand * landRelief * landness;
    elevation += maxOcean * (regional * 0.0028 + local * 0.0010) * oceanness;
    const double surfaceDetail = std::clamp(
        0.52 * regional + 0.34 * local + 0.14 * micro,
        -1.0,
        1.0);
'''
text = replace_once(text, old_detail, new_detail, "replace coarse residual with seamless multiscale relief")

text = replace_once(
    text,
    "    sample.river = river;\n    sample.oceanDepthMeters = std::max(\n",
    "    sample.river = river;\n    sample.surfaceDetail = surfaceDetail;\n    sample.oceanDepthMeters = std::max(\n",
    "store surface detail",
)

palette_replacement = r'''glm::vec3 planetTerrainColor(
    const PlanetDefinition& definition,
    const PlanetTerrainSample& sample) noexcept {
    const auto mix3 = [](const glm::vec3& a, const glm::vec3& b, double t) noexcept {
        return glm::mix(a, b, static_cast<float>(std::clamp(t, 0.0, 1.0)));
    };
    const float variation = static_cast<float>(0.92 + 0.14 * (0.5 + 0.5 * sample.surfaceDetail));

    if (sample.submerged(definition)) {
        const double depthScale = resolvedOceanDepth(definition) > 0.0
            ? std::clamp(sample.oceanDepthMeters / resolvedOceanDepth(definition), 0.0, 1.0)
            : 0.0;
        glm::vec3 seabed = mix3(
            {0.43F, 0.43F, 0.32F},
            {0.10F, 0.14F, 0.15F},
            smooth01(0.025, 0.55, depthScale));
        seabed = mix3(seabed, {0.19F, 0.20F, 0.19F}, sample.oceanRidge * 0.70);
        seabed = mix3(seabed, {0.055F, 0.060F, 0.074F}, sample.trench * 0.82);
        return glm::clamp(seabed * variation, glm::vec3{0.0F}, glm::vec3{1.0F});
    }

    const double aboveSea = sample.elevationMeters - definition.seaLevelElevationMeters;
    const double highland = smooth01(900.0, 3100.0, aboveSea);
    const double alpine = smooth01(3000.0, 4700.0, aboveSea);
    const double beach = 1.0 - smooth01(18.0, 95.0, aboveSea);
    const double rockiness = std::clamp(
        0.72 * sample.mountain + 0.34 * sample.volcano + 0.24 * highland,
        0.0,
        1.0);

    const glm::vec3 meadowA{0.18F, 0.38F, 0.145F};
    const glm::vec3 meadowB{0.29F, 0.46F, 0.18F};
    glm::vec3 color = mix3(meadowA, meadowB, 0.5 + 0.5 * sample.surfaceDetail);
    color = mix3(color, {0.39F, 0.34F, 0.23F}, sample.plateau * 0.58 + highland * 0.22);
    color = mix3(color, {0.37F, 0.36F, 0.34F}, rockiness * 0.78);
    color = mix3(color, {0.22F, 0.19F, 0.17F}, sample.volcano * 0.72);
    color = mix3(color, {0.13F, 0.30F, 0.13F}, sample.river * 0.72);
    color = mix3(color, {0.64F, 0.56F, 0.37F}, beach * 0.92);
    const double snow = alpine * std::clamp(0.42 + 0.74 * sample.mountain, 0.0, 1.0);
    color = mix3(color, {0.80F, 0.82F, 0.80F}, snow);
    return glm::clamp(color * variation, glm::vec3{0.0F}, glm::vec3{1.0F});
}

glm::vec4 planetTerrainMaterial(
    const PlanetDefinition& definition,
    const PlanetTerrainSample& sample) noexcept {
    if (sample.submerged(definition)) return {0.0F, 0.91F, 0.0F, 0.0F};
    const double aboveSea = sample.elevationMeters - definition.seaLevelElevationMeters;
    const double highland = smooth01(1200.0, 3800.0, aboveSea);
    const double rockiness = std::clamp(
        0.68 * sample.mountain + 0.40 * sample.volcano + 0.24 * highland,
        0.0,
        1.0);
    const float roughness = static_cast<float>(std::clamp(
        0.91 - 0.17 * rockiness + 0.035 * sample.surfaceDetail,
        0.66,
        0.96));
    return {0.0F, roughness, 0.0F, 0.0F};
}

'''
text = regex_once(
    text,
    r"glm::vec3 planetTerrainColor\(.*?\n\}\n\nglm::vec4 planetTerrainMaterial\(.*?\n\}\n\n(?=glm::dvec3 planetSurfaceNormal)",
    palette_replacement,
    "replace terrain palette/material",
)
cpp.write_text(text, encoding="utf-8")

# -----------------------------------------------------------------------------
# 2) V7 runtime LOD: denser near field, tiny overlaps, no stacked square oceans.
# -----------------------------------------------------------------------------
main = ROOT / "native/src/app/Main.cpp"
text = main.read_text(encoding="utf-8")
old_rings = r'''            struct Ring {
                double half;
                double inner;
                std::uint32_t resolution;
                double terrainBaseInset;
                double terrainEdgeInset;
            };
            // Nested regular grids follow the geometry-clipmap principle: dense near the player,
            // progressively cheaper outwards, with hollow coarser levels instead of duplicating the
            // full inner area.
            const std::array<Ring, 4> rings{{
                {22000.0, 0.0, 220U, 0.0, 1.5},
                {190000.0, 20000.0, 180U, 1.0, 8.0},
                {950000.0, 170000.0, 144U, 7.0, 42.0},
                {2600000.0, 850000.0, 96U, 34.0, 160.0},
            }};
'''
new_rings = r'''            struct Ring {
                double half;
                double inner;
                std::uint32_t resolution;
                double terrainBaseInset;
                double terrainEdgeInset;
            };
            // Concentric clipmap windows keep V7's deterministic spherical surface authority, but
            // reserve real vertex density for walking scale.  Adjacent levels overlap slightly and
            // use only centimetre/metre-class depth bias: the old 160 m edge sink made the LOD
            // boundary itself visible from altitude.
            const std::array<Ring, 5> rings{{
                {4096.0,       0.0, 256U, 0.00, 0.12},
                {24576.0,   3600.0, 192U, 0.12, 0.42},
                {131072.0, 22000.0, 160U, 0.38, 0.95},
                {655360.0,118000.0, 128U, 0.95, 2.80},
                {2600000.0,590000.0,104U, 2.80, 9.00},
            }};
'''
text = replace_once(text, old_rings, new_rings, "replace V7 clipmap ring budget")

# Remove the duplicated ocean mesh generated inside every terrain ring.  It was transparent and
# therefore all overlapped layers remained visible, producing the large square/band artifact.
text = regex_once(
    text,
    r"\n                // Ocean uses the same nested topology at a constant sea-level geoid\..*?\n            \}\n\n            // Coarse full-planet proxies",
    "\n            }\n\n            // Coarse full-planet proxies",
    "remove per-ring stacked oceans",
)

old_proxy = r'''            // Coarse full-planet proxies fill the horizon/space view. They are inset behind the
            // active clipmap window so transitions are hidden by the higher-resolution rings.
            vf::PlanetMesh proxy = vf::buildPlanetSurface(planet, 48U);
            constexpr double proxyInset = 240.0;
            for (auto& vertex : proxy.vertices) {
                glm::dvec3 p = glm::dvec3(vertex.position);
                const double r = glm::length(p);
                if (r > proxyInset + 1.0) p *= (r - proxyInset) / r;
                vertex.position = glm::vec3(toSurfacePoint(p));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
            }
            appendMesh(mesh, proxy);

            vf::PlanetMesh oceanProxy{};
            vf::appendOceanSurfaceProxy(
                oceanProxy,
                {},
                planet.radius + planet.seaLevelElevationMeters - 180.0,
                48U);
            for (auto& vertex : oceanProxy.vertices) {
                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
            }
            appendMesh(mesh, oceanProxy);
'''
new_proxy = r'''            // The orbital proxy is still deliberately cheaper than the local clipmaps, but 96
            // subdivisions removes the giant polygon blocks visible in V7's 48-subdivision Earth.
            // Only a small radial inset is needed because the local rings already overlap.
            vf::PlanetMesh proxy = vf::buildPlanetSurface(planet, 96U);
            constexpr double proxyInset = 24.0;
            for (auto& vertex : proxy.vertices) {
                glm::dvec3 p = glm::dvec3(vertex.position);
                const double r = glm::length(p);
                if (r > proxyInset + 1.0) p *= (r - proxyInset) / r;
                vertex.position = glm::vec3(toSurfacePoint(p));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
            }
            appendMesh(mesh, proxy);

            // Water has exactly two representations, never five stacked transparent squares:
            // a high-resolution local patch (smooth to the ~20 km altitude horizon) and one global
            // geoid shell slightly behind it.  The fragment shader fades the local patch before its
            // square boundary can enter the visible horizon.
            vf::PlanetMesh localOcean = vf::buildOceanSurfacePatch(
                planet, centerUp, 520000.0, 256U, 0.0);
            for (auto& vertex : localOcean.vertices) {
                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
                vertex.material.w = -10.0F;
            }
            appendMesh(mesh, localOcean);

            vf::PlanetMesh oceanProxy{};
            vf::appendOceanSurfaceProxy(
                oceanProxy,
                {},
                planet.radius + planet.seaLevelElevationMeters - 1.5,
                128U);
            for (auto& vertex : oceanProxy.vertices) {
                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
            }
            appendMesh(mesh, oceanProxy);
'''
text = replace_once(text, old_proxy, new_proxy, "replace coarse planet/ocean proxies")
main.write_text(text, encoding="utf-8")

# -----------------------------------------------------------------------------
# 3) Rendering: use true radial altitude for haze + dedicated stylized water path.
# -----------------------------------------------------------------------------
renderer = ROOT / "native/src/render/VulkanRenderer.cpp"
text = renderer.read_text(encoding="utf-8")
text = replace_once(
    text,
    "        scenePush.data0 = glm::vec4(glm::vec3(cameraPosition), 1.0F);\n",
    "        const double cameraAltitude = glm::length(cameraPosition - environment.planetCenter)\n"
    "            - environment.planetRadius;\n"
    "        scenePush.data0 = glm::vec4(\n"
    "            glm::vec3(cameraPosition), static_cast<float>(cameraAltitude));\n",
    "send physical camera altitude to scene shader",
)
renderer.write_text(text, encoding="utf-8")

shader = ROOT / "native/shaders/planet.slang"
text = shader.read_text(encoding="utf-8")
text = replace_once(
    text,
    "    float cameraAltitude = max(gPush.data0.y, 0.0);\n",
    "    float cameraAltitude = max(gPush.data0.w, 0.0);\n",
    "aerial perspective radial altitude",
)

text = replace_once(
    text,
    "    float metallic = saturate(input.material.x);\n    float roughness = clamp(input.material.y, 0.045, 1.0);\n",
    "    bool waterMaterial = input.material.x < -0.5;\n"
    "    float metallic = waterMaterial ? 0.0 : saturate(input.material.x);\n"
    "    float roughness = waterMaterial ? 0.065 : clamp(input.material.y, 0.045, 1.0);\n",
    "tag water before metallic clamp",
)

text = replace_once(
    text,
    "    float3 baseColor = max(input.color, 0.0);\n\n    float noL = saturate(dot(n, l));\n",
    "    float3 baseColor = max(input.color, 0.0);\n\n"
    "    if (waterMaterial)\n"
    "    {\n"
    "        float3 stablePosition = input.relativePosition + gPush.data0.xyz;\n"
    "        float2 p = stablePosition.xz * 0.00135;\n"
    "        float2 waveSlope = float2(\n"
    "            sin(p.x * 1.00 + p.y * 0.57) + 0.48 * sin(p.x * 2.31 - p.y * 1.73),\n"
    "            cos(p.y * 1.07 - p.x * 0.61) + 0.44 * cos(p.y * 2.19 + p.x * 1.51));\n"
    "        n = normalize(n + float3(waveSlope.x, 0.0, waveSlope.y) * 0.055);\n"
    "    }\n\n"
    "    float noL = saturate(dot(n, l));\n",
    "procedural water micro-normal",
)

old_transparent_eval = r'''    if (transparent)
    {
        float cosV = max(abs(dot(n, v)), 0.12);
        float path = 1.0 / cosV;
        float3 absorption = max(0.04, 1.0 - baseColor) * 0.72;
        float3 transmittance = exp(-absorption * path);
        float fresnelAmount = saturate(max(f.x, max(f.y, f.z)));
        float3 glassLighting = ambientSpecular * 2.2 + direct * 0.18;
        glassLighting += baseColor * 0.018;
        glassLighting += transmittance * (1.0 - fresnelAmount) * 0.08;
        return glassLighting;
    }
'''
new_transparent_eval = r'''    if (transparent)
    {
        if (waterMaterial)
        {
            float cosV = max(abs(dot(n, v)), 0.05);
            float fresnelWater = 0.02037 + (1.0 - 0.02037) * pow(1.0 - saturate(cosV), 5.0);
            float3 reflected = stylizedSkyPalette(reflect(-v, n), l);
            float3 shallowScatter = baseColor * (0.20 + 0.32 * saturate(n.y * 0.5 + 0.5));
            float3 sunGlint = specular * stellar * noL * shadow * 0.48;
            return shallowScatter * (1.0 - fresnelWater)
                + reflected * fresnelWater * 1.18
                + sunGlint
                + ambientSpecular * 0.55;
        }

        float cosV = max(abs(dot(n, v)), 0.12);
        float path = 1.0 / cosV;
        float3 absorption = max(0.04, 1.0 - baseColor) * 0.72;
        float3 transmittance = exp(-absorption * path);
        float fresnelAmount = saturate(max(f.x, max(f.y, f.z)));
        float3 glassLighting = ambientSpecular * 2.2 + direct * 0.18;
        glassLighting += baseColor * 0.018;
        glassLighting += transmittance * (1.0 - fresnelAmount) * 0.08;
        return glassLighting;
    }
'''
text = replace_once(text, old_transparent_eval, new_transparent_eval, "dedicated water lighting")

old_trans_frag = r'''    float3 n = normalize(input.normal);
    float3 v = normalize(-input.relativePosition);
    float ior = 1.50;
    float f0Scalar = ((ior - 1.0) / (ior + 1.0));
    f0Scalar *= f0Scalar;
    float fresnel = f0Scalar + (1.0 - f0Scalar) * pow(1.0 - saturate(abs(dot(n, v))), 5.0);
    float opticalOpacity = saturate((1.0 - transmission) * 0.48 + fresnel * 0.72 + 0.025);

    float exposure = max(gScene.skyAmbientExposure.a, 0.01);
    float3 linearColor = evaluatePbr(input, true) * exposure;
    linearColor = applyStylizedAerial(linearColor, input, 0.46);
    float3 color = acesFitted(stylizedWarmCoolGrade(linearColor));
    return float4(color, opticalOpacity);
'''
new_trans_frag = r'''    float3 n = normalize(input.normal);
    float3 v = normalize(-input.relativePosition);
    bool waterMaterial = input.material.x < -0.5;
    float ior = waterMaterial ? 1.333 : 1.50;
    float f0Scalar = ((ior - 1.0) / (ior + 1.0));
    f0Scalar *= f0Scalar;
    float fresnel = f0Scalar + (1.0 - f0Scalar) * pow(1.0 - saturate(abs(dot(n, v))), 5.0);
    float opticalOpacity = waterMaterial
        ? saturate(0.24 + fresnel * 0.70)
        : saturate((1.0 - transmission) * 0.48 + fresnel * 0.72 + 0.025);

    // -10 marks the one high-resolution local ocean patch.  Fade it before its finite patch edge
    // reaches the geometric horizon; the single global geoid remains underneath at all altitudes.
    if (waterMaterial && input.material.w < -9.0)
    {
        float localOceanFade = 1.0 - smoothstep(12000.0, 30000.0, max(gPush.data0.w, 0.0));
        opticalOpacity *= localOceanFade;
        if (opticalOpacity < 0.004) discard;
    }

    float exposure = max(gScene.skyAmbientExposure.a, 0.01);
    float3 linearColor = evaluatePbr(input, true) * exposure;
    linearColor = applyStylizedAerial(linearColor, input, waterMaterial ? 0.30 : 0.46);
    float3 color = acesFitted(stylizedWarmCoolGrade(linearColor));
    return float4(color, opticalOpacity);
'''
text = replace_once(text, old_trans_frag, new_trans_frag, "water IOR/opacity/local fade")
shader.write_text(text, encoding="utf-8")

# Guardrail: this pass must not touch V7's physics/player/camera/celestial files.
for forbidden in [
    ROOT / "native/src/player/PlanetCamera.cpp",
    ROOT / "native/src/player/CharacterController.cpp",
    ROOT / "native/src/physics/PhysicsWorld.cpp",
    ROOT / "native/src/world/CelestialSystem.cpp",
]:
    if not forbidden.exists():
        raise RuntimeError(f"V7 guard file missing: {forbidden}")

print("V8 patch applied: terrain authority + clipmap budget + ocean + stylized water; V7 physics/player untouched")
