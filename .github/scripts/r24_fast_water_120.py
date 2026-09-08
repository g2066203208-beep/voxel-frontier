#!/usr/bin/env python3
"""Materialize R24 Fast Water V1 with a same-binary runtime A/B switch.

The production shader keeps the legacy water path for measured regression tests. VF_FAST_WATER=1
selects the optimized high-coverage water branch; VF_FAST_WATER=0 restores the old fragment-heavy
path without recompiling shaders, changing assets, or changing scene geometry.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHADER = ROOT / "native/shaders/planet.slang"
HEADER = ROOT / "native/include/vf/render/VulkanRenderer.hpp"
RENDERER = ROOT / "native/src/render/VulkanRenderer.cpp"
MAIN = ROOT / "native/src/app/Main.cpp"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label} anchor count={count}")
    return text.replace(old, new, 1)


shader = SHADER.read_text(encoding="utf-8")
if "R24_FAST_WATER_120_V1" not in shader:
    shader = replace_once(
        shader,
        """struct SceneUniforms\n{\n    float4x4 lightViewProjection;\n    float4 skyAmbientExposure;\n    float4 groundAmbientShadowTexel;\n};\n""",
        """struct SceneUniforms\n{\n    float4x4 lightViewProjection;\n    float4 skyAmbientExposure;\n    float4 groundAmbientShadowTexel;\n    // R24_FAST_WATER_120_V1: x=1 selects the optimized water branch. Kept in the scene UBO so\n    // OFF/ON uses the exact same executable, SPIR-V, mesh and camera path.\n    float4 featureFlags;\n};\n""",
        "shader SceneUniforms",
    )

    shader = replace_once(
        shader,
        """    float3 worldPosition = rotateByQuaternion(input.position, gPush.data3);\n    float3 worldNormal = normalize(rotateByQuaternion(input.normal, gPush.data3));\n    float3 relativePosition = worldPosition - gPush.data0.xyz;\n    output.position = mul(gPush.matrix, float4(relativePosition, 1.0));\n    output.relativePosition = relativePosition;\n    output.normal = worldNormal;\n""",
        """    float3 worldPosition = rotateByQuaternion(input.position, gPush.data3);\n    float3 worldNormal = normalize(rotateByQuaternion(input.normal, gPush.data3));\n    const bool fastWaterVertex = input.material.x < -0.5 && gScene.featureFlags.x > 0.5;\n    if (fastWaterVertex)\n    {\n        // Static waves have no time input. Fast Water moves the two sin/cos pairs from every\n        // covered pixel to the much smaller water vertex set and interpolates the resulting normal.\n        float2 p = input.position.xz * 0.00175;\n        float2 waveSlope = float2(\n            sin(p.x + p.y * 0.57) + 0.48 * sin(p.x * 2.31 - p.y * 1.73),\n            cos(p.y * 1.07 - p.x * 0.61) + 0.44 * cos(p.y * 2.19 + p.x * 1.51));\n        worldNormal = normalize(worldNormal + float3(waveSlope.x, 0.0, waveSlope.y) * 0.055);\n    }\n    float3 relativePosition = worldPosition - gPush.data0.xyz;\n    output.position = mul(gPush.matrix, float4(relativePosition, 1.0));\n    output.relativePosition = relativePosition;\n    output.normal = worldNormal;\n""",
        "shader vertex head",
    )

    old_aerial = """    const bool terrainMaterial = input.material.w < -0.5 && input.material.w > -1.5;\n    output.terrainMacro = terrainMaterial ? valueNoise2(input.position.xz * 0.0032) : 0.5;\n    output.terrainAerialTransmittance = float3(1.0, 1.0, 1.0);\n    output.terrainAerialInscatter = float3(0.0, 0.0, 0.0);\n    if (terrainMaterial)\n    {\n        // Same optical model as the former fragment path, evaluated once per terrain vertex.\n        // Planet LOD cells are much smaller than the 350 m haze onset and atmospheric scale,\n        // so perspective-correct interpolation preserves the continuous appearance while removing\n        // length/normalize/pow/exp work from every covered terrain pixel.\n        float distanceMeters = length(relativePosition);\n        if (distanceMeters > 350.0)\n        {\n            float3 viewDir = relativePosition / max(distanceMeters, 1.0e-4);\n            float3 sunDir = normalize(gPush.data1.xyz);\n            float cameraAltitude = max(gPush.data0.w, 0.0);\n            float densityRatio = exp(-cameraAltitude / 8500.0);\n            float effectiveDistance = min(max(distanceMeters - 350.0, 0.0), 220000.0);\n            float horizon = pow(saturate(1.0 - abs(viewDir.y)), 1.15);\n            float opticalLength = effectiveDistance * densityRatio\n                * (0.55 + 0.45 * horizon) * 0.58;\n            const float3 betaR = float3(5.802e-6, 13.558e-6, 33.100e-6);\n            const float betaM = 4.0e-6;\n            float3 transmittance = exp(-(betaR + betaM) * opticalLength);\n            float3 haze = stylizedSkyPalette(viewDir, sunDir);\n            output.terrainAerialTransmittance = transmittance;\n            output.terrainAerialInscatter = haze * (1.0 - transmittance);\n        }\n    }\n"""
    new_aerial = """    const bool terrainMaterial = input.material.w < -0.5 && input.material.w > -1.5;\n    const bool fastWaterAerial = input.material.x < -0.5 && gScene.featureFlags.x > 0.5;\n    output.terrainMacro = terrainMaterial ? valueNoise2(input.position.xz * 0.0032) : 0.5;\n    output.terrainAerialTransmittance = float3(1.0, 1.0, 1.0);\n    output.terrainAerialInscatter = float3(0.0, 0.0, 0.0);\n    if (terrainMaterial || fastWaterAerial)\n    {\n        // Terrain already uses vertex aerial. Fast Water reuses it at water's historical 0.30\n        // strength, removing length/normalize/pow/three exp operations from every water fragment.\n        float distanceMeters = length(relativePosition);\n        if (distanceMeters > 350.0)\n        {\n            float3 viewDir = relativePosition / max(distanceMeters, 1.0e-4);\n            float3 sunDir = normalize(gPush.data1.xyz);\n            float cameraAltitude = max(gPush.data0.w, 0.0);\n            float densityRatio = exp(-cameraAltitude / 8500.0);\n            float effectiveDistance = min(max(distanceMeters - 350.0, 0.0), 220000.0);\n            float horizon = pow(saturate(1.0 - abs(viewDir.y)), 1.15);\n            float aerialStrength = fastWaterAerial ? 0.30 : 0.58;\n            float opticalLength = effectiveDistance * densityRatio\n                * (0.55 + 0.45 * horizon) * aerialStrength;\n            const float3 betaR = float3(5.802e-6, 13.558e-6, 33.100e-6);\n            const float betaM = 4.0e-6;\n            float3 transmittance = exp(-(betaR + betaM) * opticalLength);\n            float3 haze = stylizedSkyPalette(viewDir, sunDir);\n            output.terrainAerialTransmittance = transmittance;\n            output.terrainAerialInscatter = haze * (1.0 - transmittance);\n        }\n    }\n"""
    shader = replace_once(shader, old_aerial, new_aerial, "shader aerial")

    start = shader.find('[shader("fragment")]\nfloat4 transparentFragmentMain(VertexOutput input) : SV_Target\n{')
    end = shader.find('\n[shader("vertex")]\nFullscreenOutput fullscreenVertexMain', start)
    if start < 0 or end < 0:
        raise SystemExit("transparent shader anchors not found")
    fast_transparent = r'''[shader("fragment")]
float4 transparentFragmentMain(VertexOutput input) : SV_Target
{
    float transmission = saturate(input.material.z);
    if (transmission <= 0.02) discard;

    bool waterMaterial = input.material.x < -0.5;
    bool fastWater = waterMaterial && gScene.featureFlags.x > 0.5;
    float exposure = max(gScene.skyAmbientExposure.a, 0.01);
    if (fastWater)
    {
        // R24_FAST_WATER_120_V1: high-coverage dielectric branch. Vertex-rate waves/aerial above
        // replace fragment trigonometry and atmospheric exponentials; the compact lobe avoids the
        // generic GGX D/G chain while retaining Fresnel, sky reflection and a sharp stellar glint.
        float3 n = normalize(input.normal);
        float3 v = normalize(-input.relativePosition);
        float3 l = normalize(gPush.data1.xyz);
        float noVRaw = dot(n, v);
        if (noVRaw <= 0.015) discard;
        float noV = saturate(abs(noVRaw));
        float oneMinus = 1.0 - noV;
        float oneMinus2 = oneMinus * oneMinus;
        float oneMinus5 = oneMinus2 * oneMinus2 * oneMinus;
        const float waterF0 = 0.02037;
        float fresnel = waterF0 + (1.0 - waterF0) * oneMinus5;
        float opticalOpacity = saturate(0.66 + fresnel * 0.32);
        float cameraAltitude = max(gPush.data0.w, 0.0);
        if (input.material.w < -19.0)
            opticalOpacity *= smoothstep(18000.0, 34000.0, cameraAltitude);
        else if (input.material.w < -9.0)
            opticalOpacity *= 1.0 - smoothstep(14000.0, 30000.0, cameraAltitude);
        if (opticalOpacity < 0.004) discard;

        float3 reflected = stylizedSkyPalette(reflect(-v, n), l);
        float3 baseColor = max(input.color, float3(0.002, 0.004, 0.006));
        float upWeight = saturate(n.y * 0.5 + 0.5);
        float3 shallowScatter = baseColor * (0.56 + 0.30 * upWeight);

        float3 h = normalize(l + v);
        float noH = saturate(dot(n, h));
        float noH2 = noH * noH;
        float noH4 = noH2 * noH2;
        float noH8 = noH4 * noH4;
        float noH16 = noH8 * noH8;
        float noH32 = noH16 * noH16;
        float noL = saturate(dot(n, l));
        float3 stellar = max(gPush.data2.rgb, 0.0) * max(gPush.data2.a, 0.0);
        float3 sunGlint = stellar * noH32 * noL * (0.035 + 0.26 * fresnel);

        float3 linearColor = shallowScatter * (1.0 - fresnel)
            + reflected * fresnel * 1.16 + sunGlint;
        linearColor *= exposure;
        linearColor = linearColor * input.terrainAerialTransmittance
            + input.terrainAerialInscatter;
        return float4(acesFitted(stylizedWarmCoolGrade(linearColor)), opticalOpacity);
    }

    // Exact legacy path is intentionally retained for same-binary A/B and low-coverage glass.
    float3 n = normalize(input.normal);
    float3 v = normalize(-input.relativePosition);
    float ior = waterMaterial ? 1.333 : 1.50;
    float f0Scalar = ((ior - 1.0) / (ior + 1.0));
    f0Scalar *= f0Scalar;
    float fresnel = f0Scalar + (1.0 - f0Scalar) * pow(1.0 - saturate(abs(dot(n, v))), 5.0);
    if (waterMaterial && dot(n, v) <= 0.015) discard;

    float opticalOpacity = waterMaterial
        ? saturate(0.66 + fresnel * 0.32)
        : saturate((1.0 - transmission) * 0.48 + fresnel * 0.72 + 0.025);
    if (waterMaterial)
    {
        float cameraAltitude = max(gPush.data0.w, 0.0);
        if (input.material.w < -19.0)
            opticalOpacity *= smoothstep(18000.0, 34000.0, cameraAltitude);
        else if (input.material.w < -9.0)
            opticalOpacity *= 1.0 - smoothstep(14000.0, 30000.0, cameraAltitude);
        if (opticalOpacity < 0.004) discard;
    }

    float3 linearColor = evaluatePbr(input, true) * exposure;
    linearColor = applyStylizedAerial(linearColor, input, waterMaterial ? 0.30 : 0.46);
    return float4(acesFitted(stylizedWarmCoolGrade(linearColor)), opticalOpacity);
}
'''
    shader = shader[:start] + fast_transparent + shader[end:]
    SHADER.write_text(shader, encoding="utf-8")

header = HEADER.read_text(encoding="utf-8")
if "fastWaterEnabled" not in header:
    header = replace_once(
        header,
        """    bool hudEnabled{true};\n};\n""",
        """    bool hudEnabled{true};\n    // Same-binary water A/B switch. Production defaults ON; CI can set VF_FAST_WATER=0.\n    bool fastWaterEnabled{true};\n};\n""",
        "renderer header fast water flag",
    )
    HEADER.write_text(header, encoding="utf-8")

renderer = RENDERER.read_text(encoding="utf-8")
if "scene.featureFlags" not in renderer:
    renderer = replace_once(
        renderer,
        """struct SceneUniforms {\n    glm::mat4 lightViewProjection{1.0F};\n    glm::vec4 skyAmbientExposure{};\n    glm::vec4 groundAmbientShadowTexel{};\n};\n\nstatic_assert(sizeof(PushConstants) == 128U, \"push constants must fit Vulkan's minimum 128-byte guarantee\");\nstatic_assert(sizeof(SceneUniforms) == 96U, \"scene uniform layout must match Slang\");\n""",
        """struct SceneUniforms {\n    glm::mat4 lightViewProjection{1.0F};\n    glm::vec4 skyAmbientExposure{};\n    glm::vec4 groundAmbientShadowTexel{};\n    glm::vec4 featureFlags{};\n};\n\nstatic_assert(sizeof(PushConstants) == 128U, \"push constants must fit Vulkan's minimum 128-byte guarantee\");\nstatic_assert(sizeof(SceneUniforms) == 112U, \"scene uniform layout must match Slang\");\n""",
        "renderer SceneUniforms",
    )
    renderer = replace_once(
        renderer,
        """    scene.groundAmbientShadowTexel = glm::vec4(\n        glm::max(environment.groundAmbient, glm::vec3{0.0F}),\n        environment.shadowsEnabled\n            ? 1.0F / static_cast<float>(kShadowMapSize) : -1.0F);\n    std::memcpy(shadowFrames_[frame].mappedUniform, &scene, sizeof(scene));\n""",
        """    scene.groundAmbientShadowTexel = glm::vec4(\n        glm::max(environment.groundAmbient, glm::vec3{0.0F}),\n        environment.shadowsEnabled\n            ? 1.0F / static_cast<float>(kShadowMapSize) : -1.0F);\n    scene.featureFlags = glm::vec4(environment.fastWaterEnabled ? 1.0F : 0.0F, 0.0F, 0.0F, 0.0F);\n    std::memcpy(shadowFrames_[frame].mappedUniform, &scene, sizeof(scene));\n""",
        "renderer feature flag upload",
    )
    RENDERER.write_text(renderer, encoding="utf-8")

main = MAIN.read_text(encoding="utf-8")
if "VF_FAST_WATER" not in main:
    main = replace_once(
        main,
        """        const bool highSpeedAutopilot = vf::RuntimeFeatureFlags::readFlag(\n            \"VF_CAPTURE_HIGH_SPEED_AUTOPILOT\", false);\n""",
        """        const bool highSpeedAutopilot = vf::RuntimeFeatureFlags::readFlag(\n            \"VF_CAPTURE_HIGH_SPEED_AUTOPILOT\", false);\n        const bool fastWaterEnabled = vf::RuntimeFeatureFlags::readFlag(\n            \"VF_FAST_WATER\", true);\n        std::cout << \"R24 FAST_WATER enabled=\" << (fastWaterEnabled ? 1 : 0) << std::endl;\n""",
        "main fast water environment",
    )
    main = replace_once(
        main,
        """            renderEnvironment.hudEnabled = runtimeFeatures.uiRender;\n            const auto r24PrepDone = Clock::now();\n""",
        """            renderEnvironment.hudEnabled = runtimeFeatures.uiRender;\n            renderEnvironment.fastWaterEnabled = fastWaterEnabled;\n            const auto r24PrepDone = Clock::now();\n""",
        "main fast water render environment",
    )
    MAIN.write_text(main, encoding="utf-8")

for path, needles in [
    (SHADER, ["R24_FAST_WATER_120_V1", "featureFlags", "fastWaterVertex", "noH32"]),
    (HEADER, ["fastWaterEnabled"]),
    (RENDERER, ["scene.featureFlags", "sizeof(SceneUniforms) == 112U"]),
    (MAIN, ["VF_FAST_WATER", "renderEnvironment.fastWaterEnabled"]),
]:
    out = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in out:
            raise SystemExit(f"fast water contract missing in {path}: {needle}")

print("R24 Fast Water V1 same-binary runtime path materialized")
print("R24 Fast Water V1 source contracts passed")
