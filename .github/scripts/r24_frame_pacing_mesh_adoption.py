from pathlib import Path

FILES = {
    'renderer_h': Path('native/include/vf/render/VulkanRenderer.hpp'),
    'renderer_cpp': Path('native/src/render/VulkanRenderer.cpp'),
    'main': Path('native/src/app/Main.cpp'),
    'shader': Path('native/shaders/planet.slang'),
}
texts = {key: path.read_text(encoding='utf-8') for key, path in FILES.items()}


def replace_once(key: str, old: str, new: str, label: str) -> None:
    text = texts[key]
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {count}')
    texts[key] = text.replace(old, new, 1)


def replace_all_exact(key: str, old: str, new: str, expected: int, label: str) -> None:
    text = texts[key]
    count = text.count(old)
    if count != expected:
        raise SystemExit(f'{label}: expected {expected} anchors, found {count}')
    texts[key] = text.replace(old, new)


# -----------------------------------------------------------------------------
# 1) Renderer: let terrain workers pre-partition static render meshes.
# -----------------------------------------------------------------------------
replace_once(
    'renderer_h',
'''#include <cstdint>\n#include <string>\n#include <vector>\n''',
'''#include <cstdint>\n#include <memory>\n#include <string>\n#include <vector>\n''',
    'renderer shared_ptr include')

replace_once(
    'renderer_h',
'''struct RenderFrameEnvironment {\n    glm::vec3 sunDirectionToLight{0.38F, 0.83F, 0.41F};\n    glm::vec3 sunLinearColor{1.0F};\n    float sunIntensity{2.2F};\n    float sunAngularRadiusRadians{0.004675F};\n    glm::vec3 skyAmbient{0.10F, 0.16F, 0.26F};\n    glm::vec3 groundAmbient{0.035F, 0.030F, 0.024F};\n    float exposure{1.0F};\n    glm::vec3 cameraForward{0.0F, 0.0F, -1.0F};\n    glm::dvec3 planetCenter{};\n    double planetRadius{6371000.0};\n    double atmosphereHeight{100000.0};\n    double atmosphereScaleHeight{8500.0};\n    float mieScale{1.0F};\n    float flightSpeedMps{1.0F};\n    // Remote moons/planets are visual dynamic meshes but cannot cast a meaningful shadow into the\n    // 250 m local contact-shadow volume. CI can opt the dedicated contact probe back in.\n    bool dynamicShadowCasters{false};\n};\n\nclass VulkanRenderer final {\n''',
'''struct RenderFrameEnvironment {\n    glm::vec3 sunDirectionToLight{0.38F, 0.83F, 0.41F};\n    glm::vec3 sunLinearColor{1.0F};\n    float sunIntensity{2.2F};\n    float sunAngularRadiusRadians{0.004675F};\n    glm::vec3 skyAmbient{0.10F, 0.16F, 0.26F};\n    glm::vec3 groundAmbient{0.035F, 0.030F, 0.024F};\n    float exposure{1.0F};\n    glm::vec3 cameraForward{0.0F, 0.0F, -1.0F};\n    glm::dvec3 planetCenter{};\n    double planetRadius{6371000.0};\n    double atmosphereHeight{100000.0};\n    double atmosphereScaleHeight{8500.0};\n    float mieScale{1.0F};\n    float flightSpeedMps{1.0F};\n    // Remote moons/planets are visual dynamic meshes but cannot cast a meaningful shadow into the\n    // 250 m local contact-shadow volume. CI can opt the dedicated contact probe back in.\n    bool dynamicShadowCasters{false};\n};\n\n// CPU render preparation is intentionally detached from Vulkan object ownership. Terrain workers\n// can classify triangles into [shadow casters | opaque receivers | transparent] while they are\n// already off the render thread. The render thread then adopts this immutable payload by shared_ptr\n// instead of copying tens of megabytes and rescanning every triangle at a streaming boundary.\nstruct PreparedPlanetMesh {\n    std::vector<PlanetVertex> vertices{};\n    std::vector<std::uint32_t> indices{};\n    std::uint32_t shadowCasterIndexCount{};\n    std::uint32_t opaqueIndexCount{};\n    std::uint32_t transparentIndexCount{};\n};\n\n[[nodiscard]] PreparedPlanetMesh preparePlanetMesh(\n    PlanetMesh mesh,\n    bool excludeTerrainFromLocalShadow = true);\n\nclass VulkanRenderer final {\n''',
    'prepared render mesh declaration')

replace_once(
    'renderer_h',
'''    void uploadPlanetMesh(const PlanetMesh& mesh);\n    void setDynamicMesh(const PlanetMesh& mesh);\n''',
'''    void uploadPlanetMesh(const PlanetMesh& mesh);\n    void uploadPlanetMesh(std::shared_ptr<const PreparedPlanetMesh> mesh);\n    void setDynamicMesh(const PlanetMesh& mesh);\n''',
    'prepared static upload overload')

replace_once(
    'renderer_h',
'''    [[nodiscard]] std::uint64_t triangleCount() const noexcept {\n        return static_cast<std::uint64_t>(pendingStaticIndices_.size() / 3U);\n    }\n''',
'''    [[nodiscard]] std::uint64_t triangleCount() const noexcept {\n        return pendingStaticMesh_\n            ? static_cast<std::uint64_t>(pendingStaticMesh_->indices.size() / 3U)\n            : 0U;\n    }\n''',
    'prepared triangle count')

replace_once(
    'renderer_h',
'''    static constexpr std::uint32_t kFramesInFlight = 2;\n    static constexpr std::uint32_t kShadowMapSize = 2048;\n''',
'''    static constexpr std::uint32_t kFramesInFlight = 2;\n    // A 250 m contact-shadow box at 1024 gives ~24 cm texels before PCF. That is sufficient for\n    // tree/prop grounding while quartering depth-raster pixels versus the previous 2048 map.\n    static constexpr std::uint32_t kShadowMapSize = 1024;\n''',
    'contact shadow resolution')

replace_once(
    'renderer_h',
'''    std::vector<PlanetVertex> pendingStaticVertices_;\n    std::vector<std::uint32_t> pendingStaticIndices_;\n    std::uint32_t pendingStaticShadowCasterIndexCount_{};\n    std::uint32_t pendingStaticOpaqueIndexCount_{};\n    std::uint32_t pendingStaticTransparentIndexCount_{};\n    std::uint64_t staticMeshGeneration_{};\n''',
'''    std::shared_ptr<const PreparedPlanetMesh> pendingStaticMesh_{};\n    std::uint64_t staticMeshGeneration_{};\n''',
    'immutable prepared static payload')

replace_once(
    'renderer_cpp',
'''} // namespace\n\nVulkanRenderer::VulkanRenderer(SDL_Window* window) : window_(window) {\n''',
'''} // namespace\n\nPreparedPlanetMesh preparePlanetMesh(PlanetMesh mesh, bool excludeTerrainFromLocalShadow) {\n    if (mesh.vertices.empty() || mesh.indices.empty())\n        fail("Cannot prepare an empty planet mesh");\n\n    PreparedPlanetMesh prepared{};\n    partitionMeshIndicesForRenderPasses(\n        mesh,\n        excludeTerrainFromLocalShadow,\n        prepared.indices,\n        prepared.shadowCasterIndexCount,\n        prepared.opaqueIndexCount,\n        prepared.transparentIndexCount);\n    prepared.vertices = std::move(mesh.vertices);\n    return prepared;\n}\n\nVulkanRenderer::VulkanRenderer(SDL_Window* window) : window_(window) {\n''',
    'background static render preparation')

replace_once(
    'renderer_cpp',
'''void VulkanRenderer::uploadPlanetMesh(const PlanetMesh& mesh) {\n    if (mesh.vertices.empty() || mesh.indices.empty()) fail("Cannot upload an empty planet mesh");\n    pendingStaticVertices_ = mesh.vertices;\n    partitionMeshIndicesForRenderPasses(\n        mesh,\n        true,\n        pendingStaticIndices_,\n        pendingStaticShadowCasterIndexCount_,\n        pendingStaticOpaqueIndexCount_,\n        pendingStaticTransparentIndexCount_);\n    SDL_Log(\n        "R24 PERF shadow_caster_indices=%u opaque_indices=%u shadow_reduction=%.3f",\n        pendingStaticShadowCasterIndexCount_,\n        pendingStaticOpaqueIndexCount_,\n        pendingStaticOpaqueIndexCount_ > 0U\n            ? 1.0 - static_cast<double>(pendingStaticShadowCasterIndexCount_)\n                / static_cast<double>(pendingStaticOpaqueIndexCount_)\n            : 1.0);\n    ++staticMeshGeneration_;\n    if (staticMeshGeneration_ == 0U) {\n        staticMeshGeneration_ = 1U;\n        staticMeshGenerationByFrame_.fill(0U);\n    }\n}\n\nvoid VulkanRenderer::uploadStaticMeshForFrame(std::uint32_t frame) {\n    if (staticMeshGenerationByFrame_[frame] == staticMeshGeneration_) return;\n    auto& mesh = staticMeshes_[frame];\n    if (pendingStaticVertices_.empty() || pendingStaticIndices_.empty()) {\n        mesh.indexCount = 0U;\n        mesh.shadowCasterIndexCount = 0U;\n        mesh.opaqueIndexCount = 0U;\n        mesh.transparentIndexCount = 0U;\n        staticMeshGenerationByFrame_[frame] = staticMeshGeneration_;\n        return;\n    }\n\n    const VkDeviceSize vertexBytes = static_cast<VkDeviceSize>(\n        pendingStaticVertices_.size() * sizeof(PlanetVertex));\n    const VkDeviceSize indexBytes = static_cast<VkDeviceSize>(\n        pendingStaticIndices_.size() * sizeof(std::uint32_t));\n    ensureFrameCapacity(mesh, vertexBytes, indexBytes);\n    std::memcpy(\n        mesh.mappedVertices, pendingStaticVertices_.data(), static_cast<std::size_t>(vertexBytes));\n    std::memcpy(\n        mesh.mappedIndices, pendingStaticIndices_.data(), static_cast<std::size_t>(indexBytes));\n    mesh.indexCount = static_cast<std::uint32_t>(pendingStaticIndices_.size());\n    mesh.shadowCasterIndexCount = pendingStaticShadowCasterIndexCount_;\n    mesh.opaqueIndexCount = pendingStaticOpaqueIndexCount_;\n    mesh.transparentIndexCount = pendingStaticTransparentIndexCount_;\n    staticMeshGenerationByFrame_[frame] = staticMeshGeneration_;\n}\n''',
'''void VulkanRenderer::uploadPlanetMesh(const PlanetMesh& mesh) {\n    // Compatibility path for infrequent callers. Production R24 streaming uses the prepared\n    // shared_ptr overload so this copy/classification never executes at a terrain handoff.\n    uploadPlanetMesh(std::make_shared<PreparedPlanetMesh>(preparePlanetMesh(PlanetMesh{mesh}, true)));\n}\n\nvoid VulkanRenderer::uploadPlanetMesh(std::shared_ptr<const PreparedPlanetMesh> mesh) {\n    if (!mesh || mesh->vertices.empty() || mesh->indices.empty())\n        fail("Cannot upload an empty prepared planet mesh");\n    pendingStaticMesh_ = std::move(mesh);\n    SDL_Log(\n        "R24 PERF shadow_caster_indices=%u opaque_indices=%u shadow_reduction=%.3f",\n        pendingStaticMesh_->shadowCasterIndexCount,\n        pendingStaticMesh_->opaqueIndexCount,\n        pendingStaticMesh_->opaqueIndexCount > 0U\n            ? 1.0 - static_cast<double>(pendingStaticMesh_->shadowCasterIndexCount)\n                / static_cast<double>(pendingStaticMesh_->opaqueIndexCount)\n            : 1.0);\n    ++staticMeshGeneration_;\n    if (staticMeshGeneration_ == 0U) {\n        staticMeshGeneration_ = 1U;\n        staticMeshGenerationByFrame_.fill(0U);\n    }\n}\n\nvoid VulkanRenderer::uploadStaticMeshForFrame(std::uint32_t frame) {\n    if (staticMeshGenerationByFrame_[frame] == staticMeshGeneration_) return;\n    auto& mesh = staticMeshes_[frame];\n    const std::shared_ptr<const PreparedPlanetMesh> pending = pendingStaticMesh_;\n    if (!pending || pending->vertices.empty() || pending->indices.empty()) {\n        mesh.indexCount = 0U;\n        mesh.shadowCasterIndexCount = 0U;\n        mesh.opaqueIndexCount = 0U;\n        mesh.transparentIndexCount = 0U;\n        staticMeshGenerationByFrame_[frame] = staticMeshGeneration_;\n        return;\n    }\n\n    const VkDeviceSize vertexBytes = static_cast<VkDeviceSize>(\n        pending->vertices.size() * sizeof(PlanetVertex));\n    const VkDeviceSize indexBytes = static_cast<VkDeviceSize>(\n        pending->indices.size() * sizeof(std::uint32_t));\n    ensureFrameCapacity(mesh, vertexBytes, indexBytes);\n    std::memcpy(\n        mesh.mappedVertices, pending->vertices.data(), static_cast<std::size_t>(vertexBytes));\n    std::memcpy(\n        mesh.mappedIndices, pending->indices.data(), static_cast<std::size_t>(indexBytes));\n    mesh.indexCount = static_cast<std::uint32_t>(pending->indices.size());\n    mesh.shadowCasterIndexCount = pending->shadowCasterIndexCount;\n    mesh.opaqueIndexCount = pending->opaqueIndexCount;\n    mesh.transparentIndexCount = pending->transparentIndexCount;\n    staticMeshGenerationByFrame_[frame] = staticMeshGeneration_;\n}\n''',
    'adopt immutable prepared static mesh')


# -----------------------------------------------------------------------------
# 2) Main: perform static render partitioning inside the existing terrain worker.
# -----------------------------------------------------------------------------
replace_once(
    'main',
'''        for (auto& vertex : earthGlobeMesh.vertices) {\n            const glm::dvec3 pPlanet = glm::dvec3(vertex.position);\n            const glm::dvec3 nPlanet = safeNormalize(glm::dvec3(vertex.normal));\n            vertex.position = glm::vec3(toSurfacePoint(pPlanet));\n            vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(nPlanet)));\n        }\n\n        glm::dvec3 lodCenterDirection = patchUp;\n''',
'''        for (auto& vertex : earthGlobeMesh.vertices) {\n            const glm::dvec3 pPlanet = glm::dvec3(vertex.position);\n            const glm::dvec3 nPlanet = safeNormalize(glm::dvec3(vertex.normal));\n            vertex.position = glm::vec3(toSurfacePoint(pPlanet));\n            vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(nPlanet)));\n        }\n        const auto earthGlobeRenderMesh = std::make_shared<const vf::PreparedPlanetMesh>(\n            vf::preparePlanetMesh(std::move(earthGlobeMesh), true));\n\n        glm::dvec3 lodCenterDirection = patchUp;\n''',
    'prepare distant globe once')

replace_once(
    'main',
'''        struct TerrainBuildResult {\n            glm::dvec3 centerDirection{};\n            glm::dvec3 viewForwardDirection{};\n            vf::PlanetMesh mesh{};\n            std::shared_ptr<const vf::RegionalHydrology> hydrology{};\n            vf::PlanetLodStats stats{};\n            double buildMilliseconds{};\n            bool reusedHydrology{};\n        };\n''',
'''        struct TerrainBuildResult {\n            glm::dvec3 centerDirection{};\n            glm::dvec3 viewForwardDirection{};\n            std::shared_ptr<const vf::PreparedPlanetMesh> renderMesh{};\n            std::shared_ptr<const vf::RegionalHydrology> hydrology{};\n            vf::PlanetLodStats stats{};\n            std::size_t meshVertices{};\n            std::size_t meshIndices{};\n            double buildMilliseconds{};\n            bool reusedHydrology{};\n        };\n''',
    'terrain result prepared payload')

replace_once(
    'main',
'''            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 1500U\n                : (buildAltitude < 150000.0 ? 800U : 380U);\n            lodConfig.verticalFovRadians = glm::radians(68.0);\n            lodConfig.viewForwardPlanetLocal = safeNormalize(\n                viewForwardPlanetLocal, stableTangent(centerUp));\n            lodConfig.viewConeHalfAngleRadians = glm::radians(100.0);\n            lodConfig.viewportHeightPixels = 900.0;\n            lodConfig.targetScreenErrorPixels = buildAltitude < 25000.0 ? 2.8\n                : (buildAltitude < 150000.0 ? 4.2 : 6.5);\n''',
'''            // Cesium-style view/SSE selection should spend geometry on pixels, not a huge\n            // behind-camera prefetch ring. The 156-degree cone still exceeds the ~100-degree\n            // horizontal gameplay FOV by ~28 degrees per side, while turn-triggered async prefetch\n            // refreshes at 28 degrees. Reduce the hard leaf ceiling as a second safety net.\n            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 1100U\n                : (buildAltitude < 150000.0 ? 650U : 320U);\n            lodConfig.verticalFovRadians = glm::radians(68.0);\n            lodConfig.viewForwardPlanetLocal = safeNormalize(\n                viewForwardPlanetLocal, stableTangent(centerUp));\n            lodConfig.viewConeHalfAngleRadians = glm::radians(78.0);\n            lodConfig.viewportHeightPixels = 900.0;\n            lodConfig.targetScreenErrorPixels = buildAltitude < 25000.0 ? 3.4\n                : (buildAltitude < 150000.0 ? 4.8 : 7.2);\n''',
    'tighter pixel-driven terrain budget')

replace_once(
    'main',
'''            lodConfig.detailTransitionEndMeters = 85000.0;\n            lodConfig.transitionFarCellMeters = 420.0;\n''',
'''            lodConfig.detailTransitionEndMeters = 65000.0;\n            lodConfig.transitionFarCellMeters = 520.0;\n''',
    'shorter full-detail transition')

replace_once(
    'main',
'''            TerrainBuildResult result{};\n            result.centerDirection = centerUp;\n            result.viewForwardDirection = lodConfig.viewForwardPlanetLocal;\n            result.hydrology = hydrology;\n            result.reusedHydrology = canReuseHydrology;\n            result.mesh = vf::buildAdaptivePlanetSurface(\n                buildSurface, cameraPlanetLocal, lodConfig, &result.stats);\n\n            // PlanetLodMeshBuilder already emits the authoritative hydrology-displaced position and\n            // reconstructs normals from that exact sampled patch grid. The old pass called\n            // sampleSurface() for every generated vertex a second time, and sampleSurface() itself\n            // performs four additional terrain/hydrology samples for a central-difference normal.\n            // Transform the already authoritative mesh directly into the fixed render frame.\n            for (auto& vertex : result.mesh.vertices) {\n                const glm::dvec3 precisePlanet = glm::dvec3(vertex.position);\n                const glm::dvec3 preciseNormal = safeNormalize(\n                    glm::dvec3(vertex.normal), safeNormalize(precisePlanet, centerUp));\n                vertex.position = glm::vec3(toSurfacePoint(precisePlanet));\n                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(preciseNormal)));\n            }\n\n            if (buildAltitude < 30000.0) {\n                appendMesh(result.mesh, vf::buildProceduralEcology(\n                    planet, centerUp, surfaceFrame, {}, &buildSurface));\n            }\n\n            vf::PlanetMesh oceanProxy{};\n            vf::appendOceanSurfaceProxy(\n                oceanProxy, {}, planet.radius + planet.seaLevelElevationMeters - 1.5, 96U);\n            for (auto& vertex : oceanProxy.vertices) {\n                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));\n                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));\n                vertex.material.w = -20.0F;\n            }\n            appendMesh(result.mesh, oceanProxy);\n            result.buildMilliseconds = std::chrono::duration<double, std::milli>(\n                std::chrono::steady_clock::now() - buildStarted).count();\n            return result;\n''',
'''            TerrainBuildResult result{};\n            result.centerDirection = centerUp;\n            result.viewForwardDirection = lodConfig.viewForwardPlanetLocal;\n            result.hydrology = hydrology;\n            result.reusedHydrology = canReuseHydrology;\n            vf::PlanetMesh renderMesh = vf::buildAdaptivePlanetSurface(\n                buildSurface, cameraPlanetLocal, lodConfig, &result.stats);\n\n            // PlanetLodMeshBuilder already emits the authoritative hydrology-displaced position and\n            // reconstructs normals from that exact sampled patch grid. The old pass called\n            // sampleSurface() for every generated vertex a second time, and sampleSurface() itself\n            // performs four additional terrain/hydrology samples for a central-difference normal.\n            // Transform the already authoritative mesh directly into the fixed render frame.\n            for (auto& vertex : renderMesh.vertices) {\n                const glm::dvec3 precisePlanet = glm::dvec3(vertex.position);\n                const glm::dvec3 preciseNormal = safeNormalize(\n                    glm::dvec3(vertex.normal), safeNormalize(precisePlanet, centerUp));\n                vertex.position = glm::vec3(toSurfacePoint(precisePlanet));\n                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(preciseNormal)));\n            }\n\n            if (buildAltitude < 30000.0) {\n                appendMesh(renderMesh, vf::buildProceduralEcology(\n                    planet, centerUp, surfaceFrame, {}, &buildSurface));\n            }\n\n            vf::PlanetMesh oceanProxy{};\n            vf::appendOceanSurfaceProxy(\n                oceanProxy, {}, planet.radius + planet.seaLevelElevationMeters - 1.5, 96U);\n            for (auto& vertex : oceanProxy.vertices) {\n                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));\n                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));\n                vertex.material.w = -20.0F;\n            }\n            appendMesh(renderMesh, oceanProxy);\n            result.meshVertices = renderMesh.vertices.size();\n            result.meshIndices = renderMesh.indices.size();\n            // Critical frame-pacing change: material binning and vector ownership transfer occur on\n            // this terrain worker. Main-thread adoption later is only a shared_ptr assignment.\n            result.renderMesh = std::make_shared<const vf::PreparedPlanetMesh>(\n                vf::preparePlanetMesh(std::move(renderMesh), true));\n            result.buildMilliseconds = std::chrono::duration<double, std::milli>(\n                std::chrono::steady_clock::now() - buildStarted).count();\n            return result;\n''',
    'prepare terrain render payload on worker')

replace_once(
    'main',
'''        std::cout << "R24 PERF terrain_build_ms=" << initialTerrain.buildMilliseconds\n                  << " vertices=" << initialTerrain.mesh.vertices.size()\n                  << " indices=" << initialTerrain.mesh.indices.size()\n''',
'''        std::cout << "R24 PERF terrain_build_ms=" << initialTerrain.buildMilliseconds\n                  << " vertices=" << initialTerrain.meshVertices\n                  << " indices=" << initialTerrain.meshIndices\n''',
    'initial prepared mesh telemetry')

replace_once(
    'main',
'''        vf::PlanetLodStats currentLodStats = initialTerrain.stats;\n        vf::PlanetMesh nearTerrain = std::move(initialTerrain.mesh);\n        bool usingDistantEarthGlobe = camera.physicsFrameBodyId() != asterId\n            || camera.altitude() > 900000.0;\n        renderer.uploadPlanetMesh(usingDistantEarthGlobe ? earthGlobeMesh : nearTerrain);\n''',
'''        vf::PlanetLodStats currentLodStats = initialTerrain.stats;\n        std::shared_ptr<const vf::PreparedPlanetMesh> nearTerrain = std::move(initialTerrain.renderMesh);\n        bool usingDistantEarthGlobe = camera.physicsFrameBodyId() != asterId\n            || camera.altitude() > 900000.0;\n        renderer.uploadPlanetMesh(usingDistantEarthGlobe ? earthGlobeRenderMesh : nearTerrain);\n''',
    'initial O1 render mesh adoption')

replace_all_exact(
    'main',
'''renderer.uploadPlanetMesh(usingDistantEarthGlobe ? earthGlobeMesh : nearTerrain);''',
'''renderer.uploadPlanetMesh(usingDistantEarthGlobe ? earthGlobeRenderMesh : nearTerrain);''',
    1,
    'stream mode prepared mesh adoption')

replace_once(
    'main',
'''                    currentLodStats = completed.stats;\n                    nearTerrain = std::move(completed.mesh);\n                    lodCooldown = 0.12;\n                    std::cout << "R24 PERF terrain_build_ms=" << completed.buildMilliseconds\n                              << " vertices=" << nearTerrain.vertices.size()\n                              << " indices=" << nearTerrain.indices.size()\n''',
'''                    currentLodStats = completed.stats;\n                    nearTerrain = std::move(completed.renderMesh);\n                    lodCooldown = 0.12;\n                    std::cout << "R24 PERF terrain_build_ms=" << completed.buildMilliseconds\n                              << " vertices=" << completed.meshVertices\n                              << " indices=" << completed.meshIndices\n''',
    'streamed prepared mesh ownership')

# Truthful frame pacing telemetry: simulation remains clamped, diagnostics do not.
replace_once(
    'main',
'''        double diagnosticsTime = 0.0;\n        std::uint64_t diagnosticsFrames = 0;\n        double diagnosticsMaxFrameMilliseconds = 0.0;\n        double lodCooldown = 0.0;\n''',
'''        double diagnosticsTime = 0.0;\n        std::uint64_t diagnosticsFrames = 0;\n        double diagnosticsMaxFrameMilliseconds = 0.0;\n        double diagnosticsMaxRenderMilliseconds = 0.0;\n        double lodCooldown = 0.0;\n''',
    'render timing diagnostic state')

replace_once(
    'main',
'''            const auto now = Clock::now();\n            const double dt = std::clamp(\n                std::chrono::duration<double>(now - previous).count(),\n                1.0 / 500.0,\n                0.05);\n            previous = now;\n            diagnosticsMaxFrameMilliseconds = std::max(\n                diagnosticsMaxFrameMilliseconds, dt * 1000.0);\n''',
'''            const auto now = Clock::now();\n            const double rawFrameSeconds = std::max(\n                0.0, std::chrono::duration<double>(now - previous).count());\n            const double dt = std::clamp(rawFrameSeconds, 1.0 / 500.0, 0.05);\n            previous = now;\n            // Never hide a hitch by reporting the simulation clamp as frame time. Physics/camera\n            // still receive <=50 ms for stability; performance diagnostics record wall time.\n            diagnosticsMaxFrameMilliseconds = std::max(\n                diagnosticsMaxFrameMilliseconds, rawFrameSeconds * 1000.0);\n''',
    'unclamped frame telemetry')

replace_once(
    'main',
'''            renderer.drawFrame(viewProjection, cameraSurface, renderEnvironment);\n''',
'''            const auto renderStarted = Clock::now();\n            renderer.drawFrame(viewProjection, cameraSurface, renderEnvironment);\n            diagnosticsMaxRenderMilliseconds = std::max(\n                diagnosticsMaxRenderMilliseconds,\n                std::chrono::duration<double, std::milli>(Clock::now() - renderStarted).count());\n''',
    'renderer wall timing')

replace_once(
    'main',
'''            diagnosticsTime += dt;\n''',
'''            diagnosticsTime += rawFrameSeconds;\n''',
    'real-time FPS denominator')

replace_once(
    'main',
'''                      << " | maxms " << std::setprecision(1) << diagnosticsMaxFrameMilliseconds\n                      << " | FPS " << std::setprecision(0) << fps;\n''',
'''                      << " | maxms " << std::setprecision(1) << diagnosticsMaxFrameMilliseconds\n                      << " | renderms " << diagnosticsMaxRenderMilliseconds\n                      << " | FPS " << std::setprecision(0) << fps;\n''',
    'render timing in title')

replace_once(
    'main',
'''                diagnosticsMaxFrameMilliseconds = 0.0;\n''',
'''                diagnosticsMaxFrameMilliseconds = 0.0;\n                diagnosticsMaxRenderMilliseconds = 0.0;\n''',
    'reset render telemetry')


# -----------------------------------------------------------------------------
# 3) Fragment hot path: retain authored vertex palette, remove redundant per-pixel FBM.
# -----------------------------------------------------------------------------
replace_once(
    'shader',
'''    // Five-tap rotated cross: the 2048 contact map already provides sub-quarter-metre texels in\n    // its 250 m box. This keeps a soft footprint while cutting receiver texture fetches by 44%.\n    static const float2 offsets[5] = {\n        float2(0.0, 0.0),\n        float2(0.82, 0.24), float2(-0.24, 0.82),\n        float2(-0.82, -0.24), float2(0.24, -0.82),\n    };\n    float visible = 0.0;\n    [unroll]\n    for (int i = 0; i < 5; ++i)\n    {\n        float stored = gShadowMap.SampleLevel(gShadowSampler, uv + offsets[i] * texel, 0.0);\n        visible += ndc.z - bias <= stored ? 1.0 : 0.0;\n    }\n    return visible * 0.2;\n''',
'''    // Three-tap line PCF matches the 1024 / 250 m local contact map (~24 cm/texel). Terrain\n    // pixels outside this volume already early-return above; inside it, three fetches are enough to\n    // soften the local tree/prop footprint without paying five texture reads per receiver pixel.\n    static const float2 offsets[3] = {\n        float2(0.0, 0.0), float2(0.78, 0.31), float2(-0.78, -0.31),\n    };\n    float visible = 0.0;\n    [unroll]\n    for (int i = 0; i < 3; ++i)\n    {\n        float stored = gShadowMap.SampleLevel(gShadowSampler, uv + offsets[i] * texel, 0.0);\n        visible += ndc.z - bias <= stored ? 1.0 : 0.0;\n    }\n    return visible / 3.0;\n''',
    'three tap contact PCF')

replace_once(
    'shader',
'''    if (terrainMaterial)\n    {\n        // Gradient/triplanar-inspired procedural variation: broad color blocks first, medium-scale\n        // enrichment second, and very little fine grain. This keeps the low-poly terrain readable.\n        float2 q = input.objectPosition.xz;\n        float macro = terrainFbm2(q * 0.0038);\n        float medium = valueNoise2(q * 0.0125 + 31.7);\n        float value = (macro - 0.5) * 0.20 + (medium - 0.5) * 0.082;\n        float warmPatch = smoothstep(0.58, 0.84, macro);\n        float localSlope = saturate(1.0 - n.y);\n        baseColor *= 1.0 + value;\n        baseColor = lerp(baseColor, baseColor * float3(1.045, 1.005, 0.930), warmPatch * 0.20);\n        baseColor = lerp(baseColor, baseColor * float3(0.88, 0.91, 0.89), smoothstep(0.32, 0.72, localSlope) * 0.24);\n        roughness = clamp(roughness + (medium - 0.5) * 0.050, 0.64, 0.98);\n    }\n    else if (foliageMaterial)\n    {\n        float crown = valueNoise2(input.objectPosition.xz * 0.075 + input.objectPosition.y * 0.011);\n        baseColor *= 0.93 + crown * 0.14;\n        roughness = max(roughness, 0.86);\n    }\n    else if (barkMaterial)\n    {\n        float barkVariation = valueNoise2(input.objectPosition.xz * 0.22 + input.objectPosition.y * 0.035);\n        baseColor *= 0.90 + barkVariation * 0.16;\n        roughness = max(roughness, 0.91);\n    }\n    else if (rockMaterial)\n    {\n        float rockVariation = valueNoise2(input.objectPosition.xz * 0.055 + 13.0);\n        baseColor *= 0.90 + rockVariation * 0.16;\n        roughness = clamp(roughness, 0.76, 0.94);\n    }\n''',
'''    if (terrainMaterial)\n    {\n        // PlanetSurface/LodMeshBuilder already bakes biome/elevation variation into vertex.color.\n        // The old fragment path then recomputed one 3-octave FBM plus a second value-noise field on\n        // every terrain pixel (16 hash evaluations before PBR). Keep one broad value-noise sample\n        // for gentle breakup and let slope + the authored vertex palette carry the rest.\n        float2 q = input.objectPosition.xz;\n        float macro = valueNoise2(q * 0.0032);\n        float localSlope = saturate(1.0 - n.y);\n        baseColor *= 0.95 + macro * 0.10;\n        baseColor = lerp(\n            baseColor, baseColor * float3(1.035, 1.005, 0.945),\n            smoothstep(0.62, 0.86, macro) * 0.14);\n        baseColor = lerp(\n            baseColor, baseColor * float3(0.89, 0.92, 0.90),\n            smoothstep(0.32, 0.72, localSlope) * 0.24);\n        roughness = clamp(roughness + (macro - 0.5) * 0.035, 0.64, 0.98);\n    }\n    else if (foliageMaterial)\n    {\n        // Crown geometry/vertex color already varies deterministically on the CPU. Avoid another\n        // four-hash value-noise lookup per leaf fragment.\n        baseColor *= 0.97 + 0.055 * saturate(n.y * 0.5 + 0.5);\n        roughness = max(roughness, 0.86);\n    }\n    else if (barkMaterial)\n    {\n        baseColor *= 0.96 + 0.045 * saturate(abs(n.y));\n        roughness = max(roughness, 0.91);\n    }\n    else if (rockMaterial)\n    {\n        baseColor *= 0.94 + 0.075 * saturate(n.y * 0.5 + 0.5);\n        roughness = clamp(roughness, 0.76, 0.94);\n    }\n''',
    'remove redundant material fragment noise')

for key, path in FILES.items():
    path.write_text(texts[key], encoding='utf-8')

print('R24 FRAME PACING + MESH ADOPTION materialized')
print(' - static render partitioning moved into terrain worker')
print(' - render thread adopts immutable static meshes by shared_ptr')
print(' - 1024 local shadow atlas + 3 tap PCF')
print(' - terrain leaf budget/view cone tightened around visible pixels')
print(' - per-fragment terrain/ecology noise sharply reduced')
print(' - frame diagnostics now report unclamped wall time and render wall time')
