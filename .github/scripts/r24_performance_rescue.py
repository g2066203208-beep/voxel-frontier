from pathlib import Path

MAIN = Path('native/src/app/Main.cpp')
text = MAIN.read_text(encoding='utf-8')


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {count}')
    text = text.replace(old, new, 1)


replace_once(
'''        struct TerrainBuildResult {
            glm::dvec3 centerDirection{};
            vf::PlanetMesh mesh{};
            std::shared_ptr<const vf::RegionalHydrology> hydrology{};
            vf::PlanetLodStats stats{};
        };

        auto buildTerrainLod = [&](const glm::dvec3& centerDirection, const glm::dvec3& cameraPlanetLocal) {
            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);
            const double buildAltitude = std::max(0.0, glm::length(cameraPlanetLocal) - planet.radius);
''',
'''        struct TerrainBuildResult {
            glm::dvec3 centerDirection{};
            vf::PlanetMesh mesh{};
            std::shared_ptr<const vf::RegionalHydrology> hydrology{};
            vf::PlanetLodStats stats{};
            double buildMilliseconds{};
            bool reusedHydrology{};
        };

        auto buildTerrainLod = [&](
            const glm::dvec3& centerDirection,
            const glm::dvec3& cameraPlanetLocal,
            std::shared_ptr<const vf::RegionalHydrology> reusableHydrology = {}) {
            const auto buildStarted = std::chrono::steady_clock::now();
            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);
            const double buildAltitude = std::max(0.0, glm::length(cameraPlanetLocal) - planet.radius);
''',
'build result and timer',
)

replace_once(
'''            hydroConfig.maxIncisionMeters = std::min(3000.0, planet.maxElevation * 0.10);
            hydroConfig.riverHeadAccumulationFraction = 0.0012;
            hydroConfig.fullChannelAccumulationFraction = 0.022;
            auto hydrology = std::make_shared<vf::RegionalHydrology>(planet, centerUp, hydroConfig);

            vf::PlanetSurfaceAuthority buildSurface{planet};
''',
'''            hydroConfig.maxIncisionMeters = std::min(3000.0, planet.maxElevation * 0.10);
            hydroConfig.riverHeadAccumulationFraction = 0.0012;
            hydroConfig.fullChannelAccumulationFraction = 0.022;

            // Priority-Flood is a regional authority, not a per-terrain-patch effect. The 220 km
            // hydrology window already covers the entire 85 km high-detail transition band, so
            // rebuilding a 193x193 routed DEM every ~3.36 km of terrain prefetch is pure duplicate
            // work. Reuse an immutable bake while its fully weighted core still covers the new
            // camera neighbourhood; rebuild only when coverage or required resolution changes.
            bool canReuseHydrology = false;
            if (reusableHydrology && !reusableHydrology->empty()
                && reusableHydrology->resolution() >= hydroConfig.resolution
                && reusableHydrology->halfExtentMeters() >= hydroConfig.halfExtentMeters) {
                const double hydroArcMeters = std::acos(std::clamp(
                    glm::dot(centerUp, reusableHydrology->centerDirection()), -1.0, 1.0))
                    * planet.radius;
                const double safeReuseRadiusMeters = std::max(
                    0.0, reusableHydrology->halfExtentMeters() * 0.72 - 90000.0);
                canReuseHydrology = hydroArcMeters <= safeReuseRadiusMeters;
            }
            std::shared_ptr<const vf::RegionalHydrology> hydrology = reusableHydrology;
            if (!canReuseHydrology) {
                hydrology = std::make_shared<vf::RegionalHydrology>(planet, centerUp, hydroConfig);
            }

            vf::PlanetSurfaceAuthority buildSurface{planet};
''',
'hydrology reuse',
)

replace_once(
'''            TerrainBuildResult result{};
            result.centerDirection = centerUp;
            result.hydrology = hydrology;
            result.mesh = vf::buildAdaptivePlanetSurface(
                buildSurface, cameraPlanetLocal, lodConfig, &result.stats);
            for (auto& vertex : result.mesh.vertices) {
                const glm::dvec3 approximatePlanet = glm::dvec3(vertex.position);
                const glm::dvec3 vertexDirection = safeNormalize(approximatePlanet, centerUp);
                const vf::PlanetSurfaceSample preciseSurface = buildSurface.sampleSurface(vertexDirection);
                vertex.position = glm::vec3(toSurfacePoint(preciseSurface.position));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(preciseSurface.normal)));
            }
''',
'''            TerrainBuildResult result{};
            result.centerDirection = centerUp;
            result.hydrology = hydrology;
            result.reusedHydrology = canReuseHydrology;
            result.mesh = vf::buildAdaptivePlanetSurface(
                buildSurface, cameraPlanetLocal, lodConfig, &result.stats);

            // PlanetLodMeshBuilder already emits the authoritative hydrology-displaced position and
            // reconstructs normals from that exact sampled patch grid. The old pass called
            // sampleSurface() for every generated vertex a second time, and sampleSurface() itself
            // performs four additional terrain/hydrology samples for a central-difference normal.
            // Transform the already authoritative mesh directly into the fixed render frame.
            for (auto& vertex : result.mesh.vertices) {
                const glm::dvec3 precisePlanet = glm::dvec3(vertex.position);
                const glm::dvec3 preciseNormal = safeNormalize(
                    glm::dvec3(vertex.normal), safeNormalize(precisePlanet, centerUp));
                vertex.position = glm::vec3(toSurfacePoint(precisePlanet));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(preciseNormal)));
            }
''',
'remove duplicate surface resampling',
)

replace_once(
'''            appendMesh(result.mesh, oceanProxy);
            return result;
        };

        TerrainBuildResult initialTerrain = buildTerrainLod(lodCenterDirection, initialCameraPlanet);
''',
'''            appendMesh(result.mesh, oceanProxy);
            result.buildMilliseconds = std::chrono::duration<double, std::milli>(
                std::chrono::steady_clock::now() - buildStarted).count();
            return result;
        };

        TerrainBuildResult initialTerrain = buildTerrainLod(lodCenterDirection, initialCameraPlanet, {});
        std::cout << "R24 PERF terrain_build_ms=" << initialTerrain.buildMilliseconds
                  << " vertices=" << initialTerrain.mesh.vertices.size()
                  << " indices=" << initialTerrain.mesh.indices.size()
                  << " hydrology_reused=" << (initialTerrain.reusedHydrology ? 1 : 0) << '\\n';
''',
'initial perf diagnostics',
)

replace_once(
'''                const glm::dvec3 requestedDirection = cameraDirection;
                const glm::dvec3 requestedCameraPlanet = cameraPlanet;
                terrainBuildFuture = std::async(
                    std::launch::async,
                    [&, requestedDirection, requestedCameraPlanet]() {
                        return buildTerrainLod(requestedDirection, requestedCameraPlanet);
                    });
''',
'''                const glm::dvec3 requestedDirection = cameraDirection;
                const glm::dvec3 requestedCameraPlanet = cameraPlanet;
                const auto reusableHydrology = surfaceAuthority.hydrology();
                terrainBuildFuture = std::async(
                    std::launch::async,
                    [&, requestedDirection, requestedCameraPlanet, reusableHydrology]() {
                        return buildTerrainLod(
                            requestedDirection, requestedCameraPlanet, reusableHydrology);
                    });
''',
'async hydrology reuse capture',
)

replace_once(
'''                    nearTerrain = std::move(completed.mesh);
                    lodCooldown = 0.12;

                    const vf::TerrainStreamingDecision refreshed = vf::decideTerrainStreaming({
''',
'''                    nearTerrain = std::move(completed.mesh);
                    lodCooldown = 0.12;
                    std::cout << "R24 PERF terrain_build_ms=" << completed.buildMilliseconds
                              << " vertices=" << nearTerrain.vertices.size()
                              << " indices=" << nearTerrain.indices.size()
                              << " hydrology_reused=" << (completed.reusedHydrology ? 1 : 0)
                              << '\\n';

                    const vf::TerrainStreamingDecision refreshed = vf::decideTerrainStreaming({
''',
'completed perf diagnostics',
)

replace_once(
'''        double diagnosticsTime = 0.0;
        std::uint64_t diagnosticsFrames = 0;
        double lodCooldown = 0.0;
''',
'''        double diagnosticsTime = 0.0;
        std::uint64_t diagnosticsFrames = 0;
        double diagnosticsMaxFrameMilliseconds = 0.0;
        double lodCooldown = 0.0;
''',
'frame stall accumulator',
)

replace_once(
'''            previous = now;

            // Surface gameplay may use accelerated day/orbit time.
''',
'''            previous = now;
            diagnosticsMaxFrameMilliseconds = std::max(
                diagnosticsMaxFrameMilliseconds, dt * 1000.0);

            // Surface gameplay may use accelerated day/orbit time.
''',
'frame stall sample',
)

replace_once(
'''                      << " | tris " << renderer.triangleCount() << '+'
                      << renderer.dynamicTriangleCount()
                      << " | FPS " << std::setprecision(0) << fps;
''',
'''                      << " | tris " << renderer.triangleCount() << '+'
                      << renderer.dynamicTriangleCount()
                      << " | maxms " << std::setprecision(1) << diagnosticsMaxFrameMilliseconds
                      << " | FPS " << std::setprecision(0) << fps;
''',
'window perf telemetry',
)

replace_once(
'''                diagnosticsTime = 0.0;
                diagnosticsFrames = 0;
''',
'''                diagnosticsTime = 0.0;
                diagnosticsFrames = 0;
                diagnosticsMaxFrameMilliseconds = 0.0;
''',
'reset stall telemetry',
)

MAIN.write_text(text, encoding='utf-8')
print('R24 performance rescue materialized: duplicate surface resampling removed, hydrology cache reuse enabled, perf telemetry added')
