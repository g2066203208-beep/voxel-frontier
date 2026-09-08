#!/usr/bin/env python3
"""R24 Fast Water V2: same-binary water binning, backface culling and water-heavy evidence view.

This script first materializes V1 (runtime shader toggle), then upgrades it with a dedicated water
index range/pipeline and a deterministic ocean-facing capture. VF_FAST_WATER=0 remains the exact
legacy two-sided water path; VF_FAST_WATER=1 selects backface-culling plus the cheaper water shader.
"""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
runpy.run_path(str(ROOT / ".github/scripts/r24_fast_water_120.py"), run_name="__main__")

SHADER = ROOT / "native/shaders/planet.slang"
HEADER = ROOT / "native/include/vf/render/VulkanRenderer.hpp"
RENDERER = ROOT / "native/src/render/VulkanRenderer.cpp"
MAIN = ROOT / "native/src/app/Main.cpp"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label} anchor count={count}")
    return text.replace(old, new, 1)

# ---------------- shader: remove costly functions from the high-coverage path ----------------
shader = SHADER.read_text(encoding="utf-8")
if "R24_FAST_WATER_V2_BINNED" not in shader:
    shader = replace_once(
        shader,
        """    const bool fastWaterVertex = input.material.x < -0.5 && gScene.featureFlags.x > 0.5;\n    if (fastWaterVertex)\n    {\n        // Static waves have no time input. Fast Water moves the two sin/cos pairs from every\n        // covered pixel to the much smaller water vertex set and interpolates the resulting normal.\n        float2 p = input.position.xz * 0.00175;\n        float2 waveSlope = float2(\n            sin(p.x + p.y * 0.57) + 0.48 * sin(p.x * 2.31 - p.y * 1.73),\n            cos(p.y * 1.07 - p.x * 0.61) + 0.44 * cos(p.y * 2.19 + p.x * 1.51));\n        worldNormal = normalize(worldNormal + float3(waveSlope.x, 0.0, waveSlope.y) * 0.055);\n    }\n""",
        """    const bool fastWaterVertex = input.material.x < -0.5 && gScene.featureFlags.x > 0.5;\n    if (fastWaterVertex)\n    {\n        // R24_FAST_WATER_V2_BINNED: triangle waves are coherent at this scale but avoid four\n        // transcendental operations per water vertex. Fragment normals remain smoothly interpolated.\n        float2 p = input.position.xz * 0.00125;\n        float2 a = frac(p) - 0.5;\n        float2 b = frac(p * 1.731 + float2(0.37, 0.19)) - 0.5;\n        float2 waveSlope = float2(a.x + 0.46 * b.y, a.y - 0.42 * b.x);\n        worldNormal = normalize(worldNormal + float3(waveSlope.x, 0.0, waveSlope.y) * 0.075);\n    }\n""",
        "V2 vertex waves",
    )

    old_aerial = """    if (terrainMaterial || fastWaterAerial)\n    {\n        // Terrain already uses vertex aerial. Fast Water reuses it at water's historical 0.30\n        // strength, removing length/normalize/pow/three exp operations from every water fragment.\n        float distanceMeters = length(relativePosition);\n        if (distanceMeters > 350.0)\n        {\n            float3 viewDir = relativePosition / max(distanceMeters, 1.0e-4);\n            float3 sunDir = normalize(gPush.data1.xyz);\n            float cameraAltitude = max(gPush.data0.w, 0.0);\n            float densityRatio = exp(-cameraAltitude / 8500.0);\n            float effectiveDistance = min(max(distanceMeters - 350.0, 0.0), 220000.0);\n            float horizon = pow(saturate(1.0 - abs(viewDir.y)), 1.15);\n            float aerialStrength = fastWaterAerial ? 0.30 : 0.58;\n            float opticalLength = effectiveDistance * densityRatio\n                * (0.55 + 0.45 * horizon) * aerialStrength;\n            const float3 betaR = float3(5.802e-6, 13.558e-6, 33.100e-6);\n            const float betaM = 4.0e-6;\n            float3 transmittance = exp(-(betaR + betaM) * opticalLength);\n            float3 haze = stylizedSkyPalette(viewDir, sunDir);\n            output.terrainAerialTransmittance = transmittance;\n            output.terrainAerialInscatter = haze * (1.0 - transmittance);\n        }\n    }\n"""
    new_aerial = """    if (terrainMaterial)\n    {\n        // Preserve the established terrain aerial model exactly.\n        float distanceMeters = length(relativePosition);\n        if (distanceMeters > 350.0)\n        {\n            float3 viewDir = relativePosition / max(distanceMeters, 1.0e-4);\n            float3 sunDir = normalize(gPush.data1.xyz);\n            float cameraAltitude = max(gPush.data0.w, 0.0);\n            float densityRatio = exp(-cameraAltitude / 8500.0);\n            float effectiveDistance = min(max(distanceMeters - 350.0, 0.0), 220000.0);\n            float horizon = pow(saturate(1.0 - abs(viewDir.y)), 1.15);\n            float opticalLength = effectiveDistance * densityRatio\n                * (0.55 + 0.45 * horizon) * 0.58;\n            const float3 betaR = float3(5.802e-6, 13.558e-6, 33.100e-6);\n            const float betaM = 4.0e-6;\n            float3 transmittance = exp(-(betaR + betaM) * opticalLength);\n            float3 haze = stylizedSkyPalette(viewDir, sunDir);\n            output.terrainAerialTransmittance = transmittance;\n            output.terrainAerialInscatter = haze * (1.0 - transmittance);\n        }\n    }\n    else if (fastWaterAerial)\n    {\n        // Water uses a deliberately low-frequency rational haze approximation. It is vertex-rate,\n        // contains no exp/pow/sky function, and converges toward the same ambient palette at range.\n        float distanceMeters = length(relativePosition);\n        float cameraAltitude = max(gPush.data0.w, 0.0);\n        float densityApprox = 1.0 / (1.0 + cameraAltitude * (1.0 / 10500.0));\n        float distanceWeight = saturate((distanceMeters - 350.0) * (1.0 / 90000.0));\n        float hazeWeight = distanceWeight * densityApprox * 0.42;\n        float3 haze = lerp(gScene.groundAmbientShadowTexel.rgb, gScene.skyAmbientExposure.rgb, 0.78);\n        output.terrainAerialTransmittance = float3(1.0 - hazeWeight * 0.46);\n        output.terrainAerialInscatter = haze * hazeWeight;\n    }\n"""
    shader = replace_once(shader, old_aerial, new_aerial, "V2 water aerial")

    fast_begin = shader.find("    if (fastWater)\n    {\n")
    fast_end = shader.find("\n    }\n\n    // Exact legacy path", fast_begin)
    if fast_begin < 0 or fast_end < 0:
        raise SystemExit("V2 fast fragment anchors missing")
    fast_body = r'''    if (fastWater)
    {
        // Dedicated water pipeline culls the closed sphere's backfaces before fragment invocation.
        // This branch then avoids GGX, stylizedSkyPalette, half-vector normalization and pow().
        float3 n = normalize(input.normal);
        float invViewLength = rsqrt(max(dot(input.relativePosition, input.relativePosition), 1.0e-8));
        float3 v = -input.relativePosition * invViewLength;
        float3 l = gPush.data1.xyz;
        float noV = saturate(dot(n, v));
        if (noV <= 0.015) discard;

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

        float3 reflectedView = reflect(-v, n);
        float skyT = saturate(reflectedView.y * 0.5 + 0.5);
        float3 horizonSky = max(gScene.groundAmbientShadowTexel.rgb * 1.8, float3(0.025, 0.055, 0.085));
        float3 zenithSky = max(gScene.skyAmbientExposure.rgb * 1.45, float3(0.08, 0.16, 0.30));
        float3 reflected = lerp(horizonSky, zenithSky, skyT * skyT);
        float3 baseColor = max(input.color, float3(0.002, 0.004, 0.006));
        float upWeight = saturate(n.y * 0.5 + 0.5);
        float3 shallowScatter = baseColor * (0.54 + 0.28 * upWeight);

        float glint = saturate(dot(reflect(-l, n), v));
        float glint2 = glint * glint;
        float glint4 = glint2 * glint2;
        float glint8 = glint4 * glint4;
        float glint16 = glint8 * glint8;
        float noL = saturate(dot(n, l));
        float3 stellar = max(gPush.data2.rgb, 0.0) * max(gPush.data2.a, 0.0);
        float3 sunGlint = stellar * glint16 * noL * (0.028 + 0.22 * fresnel);

        float3 linearColor = shallowScatter * (1.0 - fresnel)
            + reflected * fresnel * 1.12 + sunGlint;
        linearColor *= max(gScene.skyAmbientExposure.a, 0.01);
        linearColor = linearColor * input.terrainAerialTransmittance
            + input.terrainAerialInscatter;
        return float4(acesFitted(linearColor), opticalOpacity);
'''
    shader = shader[:fast_begin] + fast_body + shader[fast_end:]
    SHADER.write_text(shader, encoding="utf-8")

# ---------------- renderer data model: [shadow | opaque | water | glass] ----------------
header = HEADER.read_text(encoding="utf-8")
if "waterIndexCount" not in header:
    header = replace_once(
        header,
        """    std::uint32_t opaqueIndexCount{};\n    std::uint32_t transparentIndexCount{};\n};\n""",
        """    std::uint32_t opaqueIndexCount{};\n    std::uint32_t waterIndexCount{};\n    std::uint32_t transparentIndexCount{};\n};\n""",
        "Prepared water range",
    )
    header = replace_once(
        header,
        """        std::uint32_t opaqueIndexCount{};\n        std::uint32_t transparentIndexCount{};\n    };\n""",
        """        std::uint32_t opaqueIndexCount{};\n        std::uint32_t waterIndexCount{};\n        std::uint32_t transparentIndexCount{};\n    };\n""",
        "FrameMesh water range",
    )
    header = replace_once(
        header,
        """    VkPipeline opaquePipeline_{VK_NULL_HANDLE};\n    VkPipeline transparentPipeline_{VK_NULL_HANDLE};\n""",
        """    VkPipeline opaquePipeline_{VK_NULL_HANDLE};\n    VkPipeline waterPipeline_{VK_NULL_HANDLE};\n    VkPipeline transparentPipeline_{VK_NULL_HANDLE};\n""",
        "water pipeline member",
    )
    header = replace_once(
        header,
        """    std::uint32_t pendingDynamicOpaqueIndexCount_{};\n    std::uint32_t pendingDynamicTransparentIndexCount_{};\n""",
        """    std::uint32_t pendingDynamicOpaqueIndexCount_{};\n    std::uint32_t pendingDynamicWaterIndexCount_{};\n    std::uint32_t pendingDynamicTransparentIndexCount_{};\n""",
        "dynamic water range",
    )
    HEADER.write_text(header, encoding="utf-8")

renderer = RENDERER.read_text(encoding="utf-8")
if "TriangleClass::Water" not in renderer:
    fn_start = renderer.find("void partitionMeshIndicesForRenderPasses(\n")
    fn_end = renderer.find("[[nodiscard]] glm::mat4 makeShadowViewProjection", fn_start)
    if fn_start < 0 or fn_end < 0:
        raise SystemExit("partition function anchors missing")
    new_partition = r'''void partitionMeshIndicesForRenderPasses(
    const PlanetMesh& mesh,
    bool excludeTerrainFromLocalShadow,
    std::vector<std::uint32_t>& output,
    std::uint32_t& shadowCasterIndexCount,
    std::uint32_t& opaqueIndexCount,
    std::uint32_t& waterIndexCount,
    std::uint32_t& transparentIndexCount) {
    if ((mesh.indices.size() % 3U) != 0U)
        fail("Planet mesh index stream must contain complete triangles");

    // R24_FAST_WATER_V2_BINNED: immutable worker-side material bins. Water is separated from
    // general transparent geometry so the closed ocean shell can use backface culling while glass
    // and future thin transparent props remain two-sided.
    enum class TriangleClass : std::uint8_t { ShadowCaster, OpaqueReceiver, Water, Transparent };
    const std::size_t triangleCount = mesh.indices.size() / 3U;
    std::vector<TriangleClass> classes;
    classes.reserve(triangleCount);

    for (std::size_t base = 0; base < mesh.indices.size(); base += 3U) {
        bool transparent = false;
        bool water = true;
        bool terrain = true;
        for (std::size_t corner = 0; corner < 3U; ++corner) {
            const std::uint32_t index = mesh.indices[base + corner];
            if (index >= mesh.vertices.size()) fail("Planet mesh index out of range");
            const auto& material = mesh.vertices[index].material;
            transparent = transparent || material.z > 0.02F;
            water = water && material.x < -0.5F;
            const bool cornerIsTerrain = material.w < -0.5F && material.w > -1.5F;
            terrain = terrain && cornerIsTerrain;
        }
        if (transparent && water) classes.push_back(TriangleClass::Water);
        else if (transparent) classes.push_back(TriangleClass::Transparent);
        else if (excludeTerrainFromLocalShadow && terrain)
            classes.push_back(TriangleClass::OpaqueReceiver);
        else
            classes.push_back(TriangleClass::ShadowCaster);
    }

    output.clear();
    output.reserve(mesh.indices.size());
    const auto appendClass = [&](TriangleClass wanted) {
        for (std::size_t triangle = 0; triangle < classes.size(); ++triangle) {
            if (classes[triangle] != wanted) continue;
            const std::size_t base = triangle * 3U;
            output.push_back(mesh.indices[base]);
            output.push_back(mesh.indices[base + 1U]);
            output.push_back(mesh.indices[base + 2U]);
        }
    };

    appendClass(TriangleClass::ShadowCaster);
    shadowCasterIndexCount = static_cast<std::uint32_t>(output.size());
    appendClass(TriangleClass::OpaqueReceiver);
    opaqueIndexCount = static_cast<std::uint32_t>(output.size());
    appendClass(TriangleClass::Water);
    waterIndexCount = static_cast<std::uint32_t>(output.size()) - opaqueIndexCount;
    appendClass(TriangleClass::Transparent);
    transparentIndexCount = static_cast<std::uint32_t>(output.size()) - opaqueIndexCount - waterIndexCount;
    if (output.size() != mesh.indices.size()) fail("Render pass index partition lost triangles");
}

'''
    renderer = renderer[:fn_start] + new_partition + renderer[fn_end:]

    renderer = replace_once(
        renderer,
        """        prepared.shadowCasterIndexCount,\n        prepared.opaqueIndexCount,\n        prepared.transparentIndexCount);\n""",
        """        prepared.shadowCasterIndexCount,\n        prepared.opaqueIndexCount,\n        prepared.waterIndexCount,\n        prepared.transparentIndexCount);\n""",
        "prepared partition args",
    )
    renderer = replace_once(
        renderer,
        """        pendingDynamicShadowCasterIndexCount_,\n        pendingDynamicOpaqueIndexCount_,\n        pendingDynamicTransparentIndexCount_);\n""",
        """        pendingDynamicShadowCasterIndexCount_,\n        pendingDynamicOpaqueIndexCount_,\n        pendingDynamicWaterIndexCount_,\n        pendingDynamicTransparentIndexCount_);\n""",
        "dynamic partition args",
    )
    renderer = replace_once(
        renderer,
        """    mesh.opaqueIndexCount = pending->opaqueIndexCount;\n    mesh.transparentIndexCount = pending->transparentIndexCount;\n""",
        """    mesh.opaqueIndexCount = pending->opaqueIndexCount;\n    mesh.waterIndexCount = pending->waterIndexCount;\n    mesh.transparentIndexCount = pending->transparentIndexCount;\n""",
        "static water upload",
    )
    renderer = replace_once(
        renderer,
        """        mesh.opaqueIndexCount = 0U;\n        mesh.transparentIndexCount = 0U;\n""",
        """        mesh.opaqueIndexCount = 0U;\n        mesh.waterIndexCount = 0U;\n        mesh.transparentIndexCount = 0U;\n""",
        "dynamic clear frame water",
    )
    renderer = replace_once(
        renderer,
        """    mesh.opaqueIndexCount = pendingDynamicOpaqueIndexCount_;\n    mesh.transparentIndexCount = pendingDynamicTransparentIndexCount_;\n""",
        """    mesh.opaqueIndexCount = pendingDynamicOpaqueIndexCount_;\n    mesh.waterIndexCount = pendingDynamicWaterIndexCount_;\n    mesh.transparentIndexCount = pendingDynamicTransparentIndexCount_;\n""",
        "dynamic water upload",
    )
    renderer = replace_once(
        renderer,
        """    pendingDynamicOpaqueIndexCount_ = 0U;\n    pendingDynamicTransparentIndexCount_ = 0U;\n""",
        """    pendingDynamicOpaqueIndexCount_ = 0U;\n    pendingDynamicWaterIndexCount_ = 0U;\n    pendingDynamicTransparentIndexCount_ = 0U;\n""",
        "dynamic clear pending water",
    )

    renderer = replace_once(
        renderer,
        """    raster.cullMode = VK_CULL_MODE_NONE;\n    createColorPipeline(\n        transparentPipeline_, sceneVertex, \"vertexMain\", transparentFragment, \"transparentFragmentMain\",\n        &vertexInput, &transparentDepth, &alphaBlend, scenePipelineLayout_);\n    createColorPipeline(\n        skyPipeline_, fullscreenVertex, \"fullscreenVertexMain\", skyFragment, \"skyFragmentMain\",\n""",
        """    // Fast water is a closed ocean shell: reject its back hemisphere before fragment work.\n    // Legacy OFF deliberately keeps the historical two-sided transparent pipeline for true A/B.\n    raster.cullMode = VK_CULL_MODE_BACK_BIT;\n    createColorPipeline(\n        waterPipeline_, sceneVertex, \"vertexMain\", transparentFragment, \"transparentFragmentMain\",\n        &vertexInput, &transparentDepth, &alphaBlend, scenePipelineLayout_);\n    raster.cullMode = VK_CULL_MODE_NONE;\n    createColorPipeline(\n        transparentPipeline_, sceneVertex, \"vertexMain\", transparentFragment, \"transparentFragmentMain\",\n        &vertexInput, &transparentDepth, &alphaBlend, scenePipelineLayout_);\n    createColorPipeline(\n        skyPipeline_, fullscreenVertex, \"fullscreenVertexMain\", skyFragment, \"skyFragmentMain\",\n""",
        "water pipeline creation",
    )
    renderer = replace_once(
        renderer,
        """            &opaquePipeline_, &transparentPipeline_, &shadowPipeline_, &skyPipeline_, &hudPipeline_}) {\n""",
        """            &opaquePipeline_, &waterPipeline_, &transparentPipeline_, &shadowPipeline_, &skyPipeline_, &hudPipeline_}) {\n""",
        "water pipeline destroy",
    )

    lambda_start = renderer.find("    auto drawScenePass = [&](VkPipeline pipeline, bool transparentPass) {\n")
    lambda_end = renderer.find("\n    // Depth-first ordering:", lambda_start)
    if lambda_start < 0 or lambda_end < 0:
        raise SystemExit("drawScenePass anchors missing")
    draw_range = r'''    // passKind: 0=opaque, 1=water, 2=general transparent.
    auto drawSceneRange = [&](VkPipeline pipeline, int passKind) {
        vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);
        vkCmdBindDescriptorSets(
            command, VK_PIPELINE_BIND_POINT_GRAPHICS, scenePipelineLayout_, 0, 1,
            &shadowFrames_[frame].descriptorSet, 0, nullptr);
        PushConstants scenePush{};
        scenePush.matrix = viewProjection;
        const double cameraAltitude = glm::length(cameraPosition - environment.planetCenter)
            - environment.planetRadius;
        scenePush.data0 = glm::vec4(
            glm::vec3(cameraPosition), static_cast<float>(cameraAltitude));
        scenePush.data1 = glm::vec4(safeNormalizeFloat(environment.sunDirectionToLight), 0.0F);
        scenePush.data2 = glm::vec4(
            glm::max(environment.sunLinearColor, glm::vec3{0.0F}),
            std::max(environment.sunIntensity, 0.0F));
        scenePush.data3 = {
            static_cast<float>(rotation.x), static_cast<float>(rotation.y),
            static_cast<float>(rotation.z), static_cast<float>(rotation.w)};
        vkCmdPushConstants(
            command, scenePipelineLayout_,
            VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
            0, sizeof(scenePush), &scenePush);

        const auto drawRange = [&](const FrameMesh& mesh) {
            std::uint32_t count = 0U;
            std::uint32_t first = 0U;
            if (passKind == 0) {
                count = mesh.opaqueIndexCount;
            } else if (passKind == 1) {
                count = mesh.waterIndexCount;
                first = mesh.opaqueIndexCount;
            } else {
                count = mesh.transparentIndexCount;
                first = mesh.opaqueIndexCount + mesh.waterIndexCount;
            }
            drawBoundMesh(command, mesh.vertexBuffer, mesh.indexBuffer, count, first);
        };
        drawRange(staticMesh);
        scenePush.data3 = {0.0F, 0.0F, 0.0F, 1.0F};
        vkCmdPushConstants(
            command, scenePipelineLayout_,
            VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
            0, sizeof(scenePush), &scenePush);
        drawRange(dynamic);
    };
'''
    renderer = renderer[:lambda_start] + draw_range + renderer[lambda_end:]
    renderer = renderer.replace(
        "if (environment.geometryEnabled) drawScenePass(opaquePipeline_, false);",
        "if (environment.geometryEnabled) drawSceneRange(opaquePipeline_, 0);",
        1,
    )
    renderer = replace_once(
        renderer,
        """    if (environment.transparentEnabled) drawScenePass(transparentPipeline_, true);\n""",
        """    if (environment.transparentEnabled) {\n        drawSceneRange(environment.fastWaterEnabled ? waterPipeline_ : transparentPipeline_, 1);\n        drawSceneRange(transparentPipeline_, 2);\n    }\n""",
        "water/transparent draw ranges",
    )

    # Make water residency measurable in logs without per-frame spam.
    renderer = replace_once(
        renderer,
        """        \"R24 PERF shadow_caster_indices=%u opaque_indices=%u shadow_reduction=%.3f\",\n        pendingStaticMesh_->shadowCasterIndexCount,\n        pendingStaticMesh_->opaqueIndexCount,\n""",
        """        \"R24 PERF shadow_caster_indices=%u opaque_indices=%u water_indices=%u transparent_other_indices=%u shadow_reduction=%.3f\",\n        pendingStaticMesh_->shadowCasterIndexCount,\n        pendingStaticMesh_->opaqueIndexCount,\n        pendingStaticMesh_->waterIndexCount,\n        pendingStaticMesh_->transparentIndexCount,\n""",
        "water telemetry format",
    )
    RENDERER.write_text(renderer, encoding="utf-8")

# ---------------- deterministic water-heavy evidence camera ----------------
main = MAIN.read_text(encoding="utf-8")
if "R24 WATER_VIEW" not in main:
    anchor = """            camera.setViewDirectionWorld(\n                safeNormalize(\n                    worldEvidenceTangent * tangentWeight - worldUp * downwardWeight,\n                    -worldUp),\n                worldUp);\n            std::cout << \"R24 deterministic aerial camera altitude=\"\n                      << aerialAltitude << \" m\\n\";\n"""
    replacement = """            camera.setViewDirectionWorld(\n                safeNormalize(\n                    worldEvidenceTangent * tangentWeight - worldUp * downwardWeight,\n                    -worldUp),\n                worldUp);\n\n            const bool captureWaterView = vf::RuntimeFeatureFlags::readFlag(\n                \"VF_CAPTURE_WATER_VIEW\", false);\n            if (captureWaterView) {\n                // Deterministically find deep water close to the selected coast and face farther\n                // seaward. This is an evidence camera only; production terrain and ocean are unchanged.\n                const glm::dvec3 waterEast = stableTangent(spawnDirection);\n                const glm::dvec3 waterNorth = safeNormalize(\n                    glm::cross(spawnDirection, waterEast), stableTangent(spawnDirection));\n                glm::dvec3 bestWaterDirection = spawnDirection;\n                glm::dvec3 bestWaterTangent = waterEast;\n                double bestWaterDepth = -1.0e9;\n                constexpr int waterRings = 8;\n                constexpr int waterAzimuths = 64;\n                constexpr double waterSearchRadiusMeters = 180000.0;\n                for (int ring = 1; ring <= waterRings; ++ring) {\n                    const double radialMeters = waterSearchRadiusMeters\n                        * static_cast<double>(ring) / static_cast<double>(waterRings);\n                    for (int i = 0; i < waterAzimuths; ++i) {\n                        const double angle = 2.0 * kPi * static_cast<double>(i)\n                            / static_cast<double>(waterAzimuths);\n                        const glm::dvec3 tangent = safeNormalize(\n                            waterEast * std::cos(angle) + waterNorth * std::sin(angle), waterEast);\n                        const glm::dvec3 direction = safeNormalize(\n                            spawnDirection + tangent * (radialMeters / planet.radius), spawnDirection);\n                        const double depth = planet.seaLevelElevationMeters\n                            - vf::samplePlanetTerrain(planet, direction).elevationMeters;\n                        if (depth > bestWaterDepth) {\n                            bestWaterDepth = depth;\n                            bestWaterDirection = direction;\n                            bestWaterTangent = tangent;\n                        }\n                    }\n                }\n                if (bestWaterDepth < 25.0)\n                    throw std::runtime_error(\"R24 water evidence camera failed to find open water\");\n                aerialAltitude = 1200.0;\n                const double oceanRadius = planet.radius + planet.seaLevelElevationMeters;\n                const glm::dvec3 waterLocalOffset = bestWaterDirection * (oceanRadius + aerialAltitude);\n                const glm::dvec3 waterWorldOffset = aster.orientation * waterLocalOffset;\n                const glm::dvec3 waterWorldUp = safeNormalize(waterWorldOffset, bestWaterDirection);\n                const glm::dvec3 waterForward = safeNormalize(\n                    aster.orientation * bestWaterTangent, stableTangent(waterWorldUp));\n                camera.setExternalWorldState(\n                    aster.position + waterWorldOffset,\n                    aster.linearVelocity + glm::cross(angularVelocity, waterWorldOffset),\n                    false);\n                constexpr double waterDown = 0.16;\n                camera.setViewDirectionWorld(\n                    safeNormalize(waterForward * std::sqrt(1.0 - waterDown * waterDown)\n                        - waterWorldUp * waterDown, -waterWorldUp),\n                    waterWorldUp);\n                std::cout << \"R24 WATER_VIEW depth_m=\" << bestWaterDepth\n                          << \" altitude_m=\" << aerialAltitude\n                          << \" horizon_dominant=1\\n\";\n            }\n            std::cout << \"R24 deterministic aerial camera altitude=\"\n                      << aerialAltitude << \" m\\n\";\n"""
    main = replace_once(main, anchor, replacement, "water evidence camera")
    MAIN.write_text(main, encoding="utf-8")

# Contracts: fail before a costly build if any materialized layer is missing.
contracts = {
    SHADER: ["R24_FAST_WATER_V2_BINNED", "densityApprox", "glint16"],
    HEADER: ["waterIndexCount", "waterPipeline_", "fastWaterEnabled"],
    RENDERER: ["TriangleClass::Water", "waterPipeline_", "water_indices=%u", "drawSceneRange"],
    MAIN: ["R24 WATER_VIEW", "VF_CAPTURE_WATER_VIEW", "VF_FAST_WATER"],
}
for path, needles in contracts.items():
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Fast Water V2 contract missing in {path}: {needle}")

print("R24 Fast Water V2 materialized: binned water + backface culling + water-heavy evidence camera")
