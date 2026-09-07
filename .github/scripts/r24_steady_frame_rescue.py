from pathlib import Path

FILES = {
    'main': Path('native/src/app/Main.cpp'),
    'renderer_h': Path('native/include/vf/render/VulkanRenderer.hpp'),
    'renderer_cpp': Path('native/src/render/VulkanRenderer.cpp'),
    'shader': Path('native/shaders/planet.slang'),
}
texts = {key: path.read_text(encoding='utf-8') for key, path in FILES.items()}


def replace_once(key: str, old: str, new: str, label: str) -> None:
    text = texts[key]
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {count}')
    texts[key] = text.replace(old, new, 1)


# -----------------------------------------------------------------------------
# 1) Keep the view-aware terrain rescue, but stop spending the full 2200-leaf budget
#    on integrated GPUs. Cesium-style SSE remains authoritative; this only caps the amount
#    of simultaneously resident fine work inside the deliberately oversized prefetch cone.
# -----------------------------------------------------------------------------
replace_once(
    'main',
'''            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 2200U
                : (buildAltitude < 150000.0 ? 1200U : 550U);
''',
'''            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 1500U
                : (buildAltitude < 150000.0 ? 800U : 380U);
''',
    'steady-frame terrain leaf budget')

# -----------------------------------------------------------------------------
# 2) Dynamic meshes are generations, not frame data. The old renderer copied the same pending
#    vertices/indices into a mapped Vulkan buffer every frame even when setDynamicMesh() had not
#    changed anything. Mirror the already-correct static generation ownership model.
# -----------------------------------------------------------------------------
replace_once(
    'renderer_h',
'''    std::uint32_t pendingDynamicOpaqueIndexCount_{};
    std::uint32_t pendingDynamicTransparentIndexCount_{};
    std::array<FrameMesh, kFramesInFlight> dynamicMeshes_{};
''',
'''    std::uint32_t pendingDynamicOpaqueIndexCount_{};
    std::uint32_t pendingDynamicTransparentIndexCount_{};
    std::uint64_t dynamicMeshGeneration_{};
    std::array<std::uint64_t, kFramesInFlight> dynamicMeshGenerationByFrame_{};
    std::array<FrameMesh, kFramesInFlight> dynamicMeshes_{};
''',
    'dynamic mesh generations')

replace_once(
    'renderer_h',
'''    float flightSpeedMps{1.0F};
};
''',
'''    float flightSpeedMps{1.0F};
    // Remote moons/planets are visual dynamic meshes but cannot cast a meaningful shadow into the
    // 250 m local contact-shadow volume. CI can opt the dedicated contact probe back in.
    bool dynamicShadowCasters{false};
};
''',
    'dynamic shadow caster policy')

replace_once(
    'renderer_cpp',
'''void VulkanRenderer::setDynamicMesh(const PlanetMesh& mesh) {
    pendingDynamicVertices_ = mesh.vertices;
    partitionMeshIndicesByTransmission(
        mesh,
        pendingDynamicIndices_,
        pendingDynamicOpaqueIndexCount_,
        pendingDynamicTransparentIndexCount_);
}
''',
'''void VulkanRenderer::setDynamicMesh(const PlanetMesh& mesh) {
    pendingDynamicVertices_ = mesh.vertices;
    partitionMeshIndicesByTransmission(
        mesh,
        pendingDynamicIndices_,
        pendingDynamicOpaqueIndexCount_,
        pendingDynamicTransparentIndexCount_);
    ++dynamicMeshGeneration_;
    if (dynamicMeshGeneration_ == 0U) {
        dynamicMeshGeneration_ = 1U;
        dynamicMeshGenerationByFrame_.fill(0U);
    }
}
''',
    'dynamic set generation')

replace_once(
    'renderer_cpp',
'''void VulkanRenderer::clearDynamicMesh() {
    pendingDynamicVertices_.clear();
    pendingDynamicIndices_.clear();
    pendingDynamicOpaqueIndexCount_ = 0U;
    pendingDynamicTransparentIndexCount_ = 0U;
}
''',
'''void VulkanRenderer::clearDynamicMesh() {
    pendingDynamicVertices_.clear();
    pendingDynamicIndices_.clear();
    pendingDynamicOpaqueIndexCount_ = 0U;
    pendingDynamicTransparentIndexCount_ = 0U;
    ++dynamicMeshGeneration_;
    if (dynamicMeshGeneration_ == 0U) {
        dynamicMeshGeneration_ = 1U;
        dynamicMeshGenerationByFrame_.fill(0U);
    }
}
''',
    'dynamic clear generation')

replace_once(
    'renderer_cpp',
'''void VulkanRenderer::uploadDynamicMeshForFrame(std::uint32_t frame) {
    auto& mesh = dynamicMeshes_[frame];
    if (pendingDynamicVertices_.empty() || pendingDynamicIndices_.empty()) {
        mesh.indexCount = 0U;
        mesh.opaqueIndexCount = 0U;
        mesh.transparentIndexCount = 0U;
        return;
    }
''',
'''void VulkanRenderer::uploadDynamicMeshForFrame(std::uint32_t frame) {
    if (dynamicMeshGenerationByFrame_[frame] == dynamicMeshGeneration_) return;
    auto& mesh = dynamicMeshes_[frame];
    if (pendingDynamicVertices_.empty() || pendingDynamicIndices_.empty()) {
        mesh.indexCount = 0U;
        mesh.opaqueIndexCount = 0U;
        mesh.transparentIndexCount = 0U;
        dynamicMeshGenerationByFrame_[frame] = dynamicMeshGeneration_;
        return;
    }
''',
    'dynamic upload dirty gate')

replace_once(
    'renderer_cpp',
'''    mesh.indexCount = static_cast<std::uint32_t>(pendingDynamicIndices_.size());
    mesh.opaqueIndexCount = pendingDynamicOpaqueIndexCount_;
    mesh.transparentIndexCount = pendingDynamicTransparentIndexCount_;
}
''',
'''    mesh.indexCount = static_cast<std::uint32_t>(pendingDynamicIndices_.size());
    mesh.opaqueIndexCount = pendingDynamicOpaqueIndexCount_;
    mesh.transparentIndexCount = pendingDynamicTransparentIndexCount_;
    dynamicMeshGenerationByFrame_[frame] = dynamicMeshGeneration_;
}
''',
    'dynamic upload generation commit')

replace_once(
    'renderer_cpp',
'''    drawBoundMesh(command, dynamic.vertexBuffer, dynamic.indexBuffer, dynamic.opaqueIndexCount, 0U);
    vkCmdEndRendering(command);
''',
'''    if (environment.dynamicShadowCasters) {
        drawBoundMesh(command, dynamic.vertexBuffer, dynamic.indexBuffer, dynamic.opaqueIndexCount, 0U);
    }
    vkCmdEndRendering(command);
''',
    'skip remote dynamic shadows')

# -----------------------------------------------------------------------------
# 3) Remote celestial geometry changes slowly in screen space. At 240x simulated time the Moon
#    moves ~24 km during 0.1 real seconds, only ~0.06-0.1 pixel at its physical Earth distance in
#    the normal 68 degree view. Rebuild/bake it at 10 Hz instead of every render frame.
# -----------------------------------------------------------------------------
replace_once(
    'main',
'''        double diagnosticsMaxFrameMilliseconds = 0.0;
        double lodCooldown = 0.0;

        while (platform.pumpEvents()) {
''',
'''        double diagnosticsMaxFrameMilliseconds = 0.0;
        double lodCooldown = 0.0;
        double dynamicSceneAccumulator = 1.0;
        constexpr double kDynamicSceneCadenceSeconds = 0.10;

        while (platform.pumpEvents()) {
''',
    'dynamic scene cadence state')

replace_once(
    'main',
'''            glm::dvec3 frameForwardSurface = forwardSurface;
            glm::dvec3 frameUpSurface = upSurface;
            vf::PlanetMesh dynamicMesh{};
''',
'''            glm::dvec3 frameForwardSurface = forwardSurface;
            glm::dvec3 frameUpSurface = upSurface;
            dynamicSceneAccumulator += dt;
            const bool refreshDynamicScene = shadowContactCapture
                || dynamicSceneAccumulator >= kDynamicSceneCadenceSeconds;
            vf::PlanetMesh dynamicMesh{};
''',
    'dynamic scene refresh decision')

replace_once(
    'main',
'''            if (currentMoon != nullptr) {
                const double moonCameraDistance = glm::length(currentMoon->position - camera.position());
''',
'''            if (refreshDynamicScene && currentMoon != nullptr) {
                const double moonCameraDistance = glm::length(currentMoon->position - camera.position());
''',
    'moon 10 Hz geometry refresh')

replace_once(
    'main',
'''            if (currentCinder != nullptr) {
                const glm::dvec3 cinderDirection = safeNormalize(
''',
'''            if (refreshDynamicScene && currentCinder != nullptr) {
                const glm::dvec3 cinderDirection = safeNormalize(
''',
    'remote planet 10 Hz geometry refresh')

replace_once(
    'main',
'''            renderer.setDynamicMesh(dynamicMesh);

            const auto [width, height] = platform.drawableSize();
''',
'''            if (refreshDynamicScene) {
                renderer.setDynamicMesh(dynamicMesh);
                dynamicSceneAccumulator = 0.0;
            }

            const auto [width, height] = platform.drawableSize();
''',
    'only publish changed dynamic mesh')

replace_once(
    'main',
'''            renderEnvironment.flightSpeedMps = static_cast<float>(camera.flightSpeedMps());

            renderer.drawFrame(viewProjection, cameraSurface, renderEnvironment);
''',
'''            renderEnvironment.flightSpeedMps = static_cast<float>(camera.flightSpeedMps());
            renderEnvironment.dynamicShadowCasters = shadowContactCapture;

            renderer.drawFrame(viewProjection, cameraSurface, renderEnvironment);
''',
    'dynamic shadow opt-in')

# -----------------------------------------------------------------------------
# 4) Opaque first, sky second with depth==clear. The old full-screen atmosphere ran beneath every
#    terrain pixel and was immediately overwritten. Reverse-Z clears depth to 0, so an EQUAL test
#    lets early-Z reject the expensive sky shader wherever opaque geometry already wrote depth.
# -----------------------------------------------------------------------------
replace_once(
    'renderer_cpp',
'''    VkPipelineDepthStencilStateCreateInfo transparentDepth = reverseDepth;
    transparentDepth.depthWriteEnable = VK_FALSE;
''',
'''    VkPipelineDepthStencilStateCreateInfo transparentDepth = reverseDepth;
    transparentDepth.depthWriteEnable = VK_FALSE;
    VkPipelineDepthStencilStateCreateInfo skyDepth = reverseDepth;
    skyDepth.depthWriteEnable = VK_FALSE;
    skyDepth.depthCompareOp = VK_COMPARE_OP_EQUAL;
''',
    'sky early depth state')

replace_once(
    'renderer_cpp',
'''    createColorPipeline(
        skyPipeline_, fullscreenVertex, "fullscreenVertexMain", skyFragment, "skyFragmentMain",
        &emptyVertexInput, &noDepth, &opaqueBlend, fullscreenPipelineLayout_);
''',
'''    createColorPipeline(
        skyPipeline_, fullscreenVertex, "fullscreenVertexMain", skyFragment, "skyFragmentMain",
        &emptyVertexInput, &skyDepth, &opaqueBlend, fullscreenPipelineLayout_);
''',
    'sky depth-equal pipeline')

sky_block = '''    vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, skyPipeline_);
    PushConstants skyPush{};
    skyPush.matrix = glm::inverse(viewProjection);
    skyPush.data0 = glm::vec4(glm::vec3(cameraPosition - environment.planetCenter), 1.0F);
    skyPush.data1 = glm::vec4(
        safeNormalizeFloat(environment.sunDirectionToLight),
        std::clamp(environment.sunAngularRadiusRadians, 0.0001F, 1.45F));
    skyPush.data2 = {
        static_cast<float>(environment.planetRadius),
        static_cast<float>(environment.atmosphereHeight),
        static_cast<float>(environment.atmosphereScaleHeight),
        std::max(environment.mieScale, 0.0F)};
    const glm::vec3 sunRadiance = glm::max(environment.sunLinearColor, glm::vec3{0.0F})
        * std::max(environment.sunIntensity, 0.0F);
    skyPush.data3 = {
        std::max(environment.exposure, 0.01F),
        sunRadiance.r,
        sunRadiance.g,
        sunRadiance.b};
    vkCmdPushConstants(
        command, fullscreenPipelineLayout_,
        VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
        0, sizeof(skyPush), &skyPush);
    vkCmdDraw(command, 3, 1, 0, 0);

'''
if texts['renderer_cpp'].count(sky_block) != 1:
    raise SystemExit('sky draw block: expected exactly one anchor')
texts['renderer_cpp'] = texts['renderer_cpp'].replace(sky_block, '', 1)
replace_once(
    'renderer_cpp',
'''    drawScenePass(opaquePipeline_, false);
    drawScenePass(transparentPipeline_, true);
''',
'''    // Depth-first ordering: fill reverse-Z with opaque terrain, then shade sky only in pixels
    // that are still at the exact clear depth. Transparent water/glass blends over the completed
    // opaque+sky background afterwards.
    drawScenePass(opaquePipeline_, false);
''' + sky_block + '''    drawScenePass(transparentPipeline_, true);
''',
    'opaque then sky then transparent')

# -----------------------------------------------------------------------------
# 5) Fragment hotpaths. This is the immediate integrated-GPU rescue while the renderer migrates to
#    Hillaire/Bruneton-style atmosphere LUTs and meshlet/cluster culling. Preserve the physical
#    coefficients and midpoint integration, but cut redundant samples/noise dramatically.
# -----------------------------------------------------------------------------
replace_once(
    'shader',
'''    static const float2 offsets[9] = {
        float2(0.0, 0.0),
        float2(0.84, 0.18), float2(0.36, 0.79), float2(-0.48, 0.72), float2(-0.86, 0.10),
        float2(-0.54, -0.66), float2(0.14, -0.88), float2(0.73, -0.54), float2(1.00, 0.02),
    };
    float visible = 0.0;
    [unroll]
    for (int i = 0; i < 9; ++i)
    {
        float stored = gShadowMap.SampleLevel(gShadowSampler, uv + offsets[i] * texel, 0.0);
        visible += ndc.z - bias <= stored ? 1.0 : 0.0;
    }
    return visible / 9.0;
''',
'''    // Five-tap rotated cross: the 2048 contact map already provides sub-quarter-metre texels in
    // its 250 m box. This keeps a soft footprint while cutting receiver texture fetches by 44%.
    static const float2 offsets[5] = {
        float2(0.0, 0.0),
        float2(0.82, 0.24), float2(-0.24, 0.82),
        float2(-0.82, -0.24), float2(0.24, -0.82),
    };
    float visible = 0.0;
    [unroll]
    for (int i = 0; i < 5; ++i)
    {
        float stored = gShadowMap.SampleLevel(gShadowSampler, uv + offsets[i] * texel, 0.0);
        visible += ndc.z - bias <= stored ? 1.0 : 0.0;
    }
    return visible * 0.2;
''',
    'five tap PCF')

replace_once(
    'shader',
'''        float macro = terrainFbm2(q * 0.0038);
        float medium = terrainFbm2(q * 0.0125 + 31.7);
        float fine = valueNoise2(q * 0.043 + 8.9);
        float value = (macro - 0.5) * 0.20 + (medium - 0.5) * 0.078 + (fine - 0.5) * 0.022;
''',
'''        float macro = terrainFbm2(q * 0.0038);
        float medium = valueNoise2(q * 0.0125 + 31.7);
        float value = (macro - 0.5) * 0.20 + (medium - 0.5) * 0.082;
''',
    'terrain fragment octave reduction')

replace_once(
    'shader',
'''        float crown = terrainFbm2(input.objectPosition.xz * 0.075 + input.objectPosition.y * 0.011);
''',
'''        float crown = valueNoise2(input.objectPosition.xz * 0.075 + input.objectPosition.y * 0.011);
''',
    'foliage fragment octave reduction')

replace_once(
    'shader',
'''        float rockVariation = terrainFbm2(input.objectPosition.xz * 0.055 + 13.0);
''',
'''        float rockVariation = valueNoise2(input.objectPosition.xz * 0.055 + 13.0);
''',
    'rock fragment octave reduction')

replace_once(
    'shader',
'''    float shadow = shadowVisibility(input.shadowPosition, noL);
''',
'''    float shadow = (noL > 0.0001 || foliageMaterial)
        ? shadowVisibility(input.shadowPosition, noL)
        : 1.0;
''',
    'skip irrelevant shadow lookups')

replace_once(
    'shader',
'''    float stepLength = max(t1, 0.0) / 4.0;
    float opticalDepth = 0.0;
    [unroll]
    for (int i = 0; i < 4; ++i)
''',
'''    // Runtime fast path: midpoint integration with two solar samples. The next renderer stage
    // replaces this per-pixel integral with a precomputed transmittance LUT.
    float stepLength = max(t1, 0.0) / 2.0;
    float opticalDepth = 0.0;
    [unroll]
    for (int i = 0; i < 2; ++i)
''',
    'two sample sun optical depth')

replace_once(
    'shader',
'''    float solarR = length(solarPlane);
    float solarAngle = atan2(solarPlane.y, solarPlane.x);

    float coronaEnvelope = exp(-max(solarR - 1.0, 0.0) * 4.8) * smoothstep(1.85, 0.92, solarR);
    float coronaRays = 0.55 + 0.45 * terrainFbm2(float2(solarAngle * 3.2, solarR * 2.7) + 41.0);
    float prominenceRadius = 1.055 + 0.050 * sin(solarAngle * 5.0 + 0.7)
        + 0.025 * sin(solarAngle * 11.0 - 1.2);
    float prominence = exp(-abs(solarR - prominenceRadius) * 48.0)
        * pow(saturate(0.55 + 0.45 * sin(solarAngle * 7.0 + 2.3)), 5.0)
        * smoothstep(0.96, 1.01, solarR) * smoothstep(1.18, 1.03, solarR);
    if (!hitsGround && solarR < 1.85) {
        background += float3(0.72, 0.16, 0.018) * coronaEnvelope * coronaRays * 0.42;
        background += float3(1.00, 0.10, 0.010) * prominence * 1.35;
    }
''',
'''    float solarR = length(solarPlane);
    // Corona FBM/atan/trigonometry used to execute for every full-screen pixel even though the
    // result contributes only within 1.85 apparent solar radii. Keep identical art inside the mask.
    if (!hitsGround && solarR < 1.85) {
        float solarAngle = atan2(solarPlane.y, solarPlane.x);
        float coronaEnvelope = exp(-max(solarR - 1.0, 0.0) * 4.8) * smoothstep(1.85, 0.92, solarR);
        float coronaRays = 0.55 + 0.45 * terrainFbm2(float2(solarAngle * 3.2, solarR * 2.7) + 41.0);
        float prominenceRadius = 1.055 + 0.050 * sin(solarAngle * 5.0 + 0.7)
            + 0.025 * sin(solarAngle * 11.0 - 1.2);
        float prominence = exp(-abs(solarR - prominenceRadius) * 48.0)
            * pow(saturate(0.55 + 0.45 * sin(solarAngle * 7.0 + 2.3)), 5.0)
            * smoothstep(0.96, 1.01, solarR) * smoothstep(1.18, 1.03, solarR);
        background += float3(0.72, 0.16, 0.018) * coronaEnvelope * coronaRays * 0.42;
        background += float3(1.00, 0.10, 0.010) * prominence * 1.35;
    }
''',
    'corona branch hoist')

replace_once(
    'shader',
'''    float segment = (endT - startT) / 8.0;
    float opticalView = 0.0;
    float3 scattering = 0.0;
    float3 transmittance = 1.0;
    [unroll]
    for (int i = 0; i < 8; ++i)
''',
'''    // Four view samples x two sun samples instead of the old 8x4 nested integral. Coefficients,
    // phase functions and midpoint integration stay physical; this is an immediate GPU rescue until
    // the Hillaire-style Transmittance / MultipleScattering / SkyView / AerialPerspective LUT path.
    float segment = (endT - startT) / 4.0;
    float opticalView = 0.0;
    float3 scattering = 0.0;
    float3 transmittance = 1.0;
    [unroll]
    for (int i = 0; i < 4; ++i)
''',
    'four sample atmosphere view integral')

for key, path in FILES.items():
    path.write_text(texts[key], encoding='utf-8')

print('R24 STEADY FRAME RESCUE materialized')
print(' - 1500 low-altitude leaf cap inside view-prefetch cone')
print(' - dynamic geometry rebuild at 10 Hz + per-frame generation dirty gate')
print(' - remote moon/planet removed from local contact-shadow pass')
print(' - opaque depth first; expensive sky shaded only where depth remains clear')
print(' - atmosphere 8x4 -> 4x2, PCF 9 -> 5, redundant fragment FBM removed')
