from pathlib import Path

FILES = {
    'climate_h': Path('native/include/vf/world/PlanetClimateGrid.hpp'),
    'climate_cpp': Path('native/src/world/PlanetClimateGrid.cpp'),
    'body_h': Path('native/include/vf/world/PlanetaryBodySystem.hpp'),
    'body_cpp': Path('native/src/world/PlanetaryBodySystem.cpp'),
    'lod_h': Path('native/include/vf/world/PlanetLodMeshBuilder.hpp'),
    'lod_cpp': Path('native/src/world/PlanetLodMeshBuilder.cpp'),
    'main': Path('native/src/app/Main.cpp'),
}
texts = {key: path.read_text(encoding='utf-8') for key, path in FILES.items()}


def replace_once(key: str, old: str, new: str, label: str) -> None:
    text = texts[key]
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {count}')
    texts[key] = text.replace(old, new, 1)


# -----------------------------------------------------------------------------
# 1) PlanetClimateGrid: cache immutable terrain classification once.
# -----------------------------------------------------------------------------
replace_once(
    'climate_h',
'''    double spinRateRadPerSecond_{};
    std::vector<PlanetClimateCell> cells_;
''',
'''    double spinRateRadPerSecond_{};
    std::vector<PlanetClimateCell> cells_;
    // Terrain/land/ocean/glacier classification is immutable for a PlanetDefinition. Climate used
    // to resynthesize the full procedural planet for every grid cell on every climate step. Cache
    // those samples once at reset so the dynamic solver only advances atmospheric state.
    std::vector<PlanetTerrainSample> terrainSamples_;
''',
    'climate terrain cache member')

replace_once(
    'climate_cpp',
'''    cells_.assign(static_cast<std::size_t>(latBands_) * lonBands_, {});

    for (std::uint32_t lat = 0; lat < latBands_; ++lat) {
''',
'''    cells_.assign(static_cast<std::size_t>(latBands_) * lonBands_, {});
    terrainSamples_.assign(cells_.size(), {});

    for (std::uint32_t lat = 0; lat < latBands_; ++lat) {
''',
    'climate cache allocation')

replace_once(
    'climate_cpp',
'''            PlanetClimateCell& cell = cells_[index(lat, lon)];
            const PlanetTerrainSample terrain = samplePlanetTerrain(planet_, directionAt(lat, lon));
            const bool ocean = terrain.submerged(planet_);
''',
'''            const std::size_t cellIndex = index(lat, lon);
            PlanetClimateCell& cell = cells_[cellIndex];
            terrainSamples_[cellIndex] = samplePlanetTerrain(planet_, directionAt(lat, lon));
            const PlanetTerrainSample& terrain = terrainSamples_[cellIndex];
            const bool ocean = terrain.submerged(planet_);
''',
    'climate cache initialization')

replace_once(
    'climate_cpp',
'''            const glm::dvec3 direction = directionAt(lat, lon);
            const PlanetTerrainSample terrain = samplePlanetTerrain(planet_, direction);
            const bool ocean = terrain.submerged(planet_);
''',
'''            const glm::dvec3 direction = directionAt(lat, lon);
            const PlanetTerrainSample& terrain = terrainSamples_[index(lat, lon)];
            const bool ocean = terrain.submerged(planet_);
''',
    'climate cached terrain hotpath')

# -----------------------------------------------------------------------------
# 2) PlanetaryBodySystem: global climate is a slow service, not a 0.25 s orbit job.
# -----------------------------------------------------------------------------
replace_once(
    'body_h',
'''    std::unique_ptr<PlanetClimateGrid> climate{};
    std::unique_ptr<OceanSpectrum> ocean{};
''',
'''    std::unique_ptr<PlanetClimateGrid> climate{};
    std::unique_ptr<OceanSpectrum> ocean{};
    // Multi-rate world simulation: orbital integration can run at sub-second cadence while the
    // 24x48 global climate grid advances on a much slower simulated-time service cadence.
    double climateAccumulatorSeconds{};
''',
    'planetary climate accumulator')

replace_once(
    'body_h',
'''    // Advances celestial N-body/spin and all registered local climate fields on the same bounded
    // simulated-time substeps. Direct large calls therefore cannot lose climate time or apply one
    // final solar direction to an entire multi-hour interval.
''',
'''    // Advances celestial N-body/spin on bounded orbital substeps. Slow planet services use their
    // own accumulated simulated-time cadence; a render frame therefore never pays for a full global
    // climate sweep once per orbital substep under time acceleration.
''',
    'planetary step contract comment')

replace_once(
    'body_cpp',
'''void PlanetaryBodySystem::stepPlanetServices(double deltaSeconds) {
    for (auto& runtimeValue : runtimes_) {
        if (!runtimeValue->climate) continue;
        const CelestialBody* bodyValue = celestial_.body(runtimeValue->bodyId);
        if (bodyValue == nullptr) continue;

        double totalIrradiance = 0.0;
        const glm::dvec3 strongestDirection = strongestStarDirectionBodyLocal(
            celestial_,
            *bodyValue,
            totalIrradiance);
        runtimeValue->climate->step(deltaSeconds, strongestDirection, totalIrradiance);
    }
}
''',
'''void PlanetaryBodySystem::stepPlanetServices(double deltaSeconds) {
    // The fastest PlanetClimateGrid process has an hours-scale time constant (precipitation is
    // 21,600 s by default) and the grid is only 7.5 degrees wide in longitude. Updating it at the
    // 0.25 s celestial fixed step used by 240x gameplay time is massive oversampling. A 300 s
    // simulated-time cadence is still far finer than the climate grid/process scales while cutting
    // hundreds of redundant global sweeps per real second. Accumulated time is never discarded.
    constexpr double kClimateServiceStepSeconds = 300.0;
    for (auto& runtimeValue : runtimes_) {
        if (!runtimeValue->climate) continue;
        runtimeValue->climateAccumulatorSeconds += deltaSeconds;
        if (runtimeValue->climateAccumulatorSeconds + 1.0e-12 < kClimateServiceStepSeconds)
            continue;

        const CelestialBody* bodyValue = celestial_.body(runtimeValue->bodyId);
        if (bodyValue == nullptr) continue;
        while (runtimeValue->climateAccumulatorSeconds + 1.0e-12
            >= kClimateServiceStepSeconds) {
            double totalIrradiance = 0.0;
            const glm::dvec3 strongestDirection = strongestStarDirectionBodyLocal(
                celestial_,
                *bodyValue,
                totalIrradiance);
            runtimeValue->climate->step(
                kClimateServiceStepSeconds, strongestDirection, totalIrradiance);
            runtimeValue->climateAccumulatorSeconds -= kClimateServiceStepSeconds;
            if (runtimeValue->climateAccumulatorSeconds < 0.0
                && runtimeValue->climateAccumulatorSeconds > -1.0e-9) {
                runtimeValue->climateAccumulatorSeconds = 0.0;
            }
        }
    }
}
''',
    'multi-rate climate service')

replace_once(
    'body_cpp',
'''    // Keep planet services synchronized with the same bounded celestial substeps. This avoids the
    // old behavior where CelestialSystem advanced a large interval while PlanetClimateGrid clamped
    // its one call to 600 s and silently lost the rest. It also samples solar direction throughout
    // the interval instead of applying only the final star direction to all elapsed climate time.
''',
'''    // Orbital integration remains tightly bounded. Slow planet services accumulate these exact
    // simulated substeps and consume them on their own cadence, preserving time without coupling
    // climate cost to render FPS or accelerated orbital step count.
''',
    'multi-rate step comment')

# -----------------------------------------------------------------------------
# 3) LOD: view-aware cheap rejection before terrain synthesis + reusable patch scratch.
# -----------------------------------------------------------------------------
replace_once(
    'lod_h',
'''    double horizonMarginRadians{0.012};
    double skirtDepthMeters{3.0};
''',
'''    double horizonMarginRadians{0.012};
    double skirtDepthMeters{3.0};

    // View-aware streaming. A value of pi disables the view cone. The cone is deliberately wider
    // than the camera frustum so rapid mouse turns consume prefetched tiles instead of revealing
    // holes, while terrain far behind the player is not synthesized at full SSE detail.
    glm::dvec3 viewForwardPlanetLocal{};
    double viewConeHalfAngleRadians{3.14159265358979323846};
''',
    'LOD view cone config')

replace_once(
    'lod_h',
'''    std::size_t evaluatedNodes{};
    std::uint32_t deepestLevel{};
''',
'''    std::size_t evaluatedNodes{};
    std::size_t culledNodes{};
    std::uint32_t deepestLevel{};
''',
    'LOD culled stats')

replace_once(
    'lod_cpp',
'''    const PlanetDefinition& planet = surface.planet();
    const NodeGeometry geometry = geometryFor(node, planet.radius);
    const PlanetTerrainSample centerTerrain = surface.sample(geometry.centerDirection);
''',
'''    const PlanetDefinition& planet = surface.planet();
    const NodeGeometry geometry = geometryFor(node, planet.radius);
    const double radius = std::max(1.0, planet.radius);
    const double cameraRadius = glm::length(camera);
    const glm::dvec3 cameraDirection = safeNormalize(camera, geometry.centerDirection);

    // Visibility is geometry-only and therefore cheap. The old order paid one center terrain sample
    // plus eight relief samples even for nodes that were behind the player or below the horizon.
    // Reject first, then spend procedural/hydrology work only on nodes that can enter the prefetch
    // cone. This mirrors tile-selection systems such as Cesium Native.
    double horizonAngle = 3.14159265358979323846;
    if (cameraRadius > radius + 1.0) {
        horizonAngle = std::acos(std::clamp(radius / cameraRadius, 0.0, 1.0));
    }
    const double cameraSeparation = angleBetween(cameraDirection, geometry.centerDirection);
    bool visible = cameraSeparation
        <= horizonAngle + geometry.angularRadius + config.horizonMarginRadians;

    const glm::dvec3 baseCenterPosition = geometry.centerDirection * radius;
    const glm::dvec3 toCenter = baseCenterPosition - camera;
    const double baseCenterDistance = glm::length(toCenter);
    if (visible && config.viewConeHalfAngleRadians < 3.14159265358979323846 - 1.0e-6
        && glm::dot(config.viewForwardPlanetLocal, config.viewForwardPlanetLocal) > 1.0e-16
        && baseCenterDistance > 1.0) {
        const glm::dvec3 viewForward = safeNormalize(config.viewForwardPlanetLocal);
        const double conservativeBoundingRadius = 0.55 * geometry.spanMeters
            + std::max(0.0, planet.maxElevation)
            + std::max(0.0, planet.maxOceanDepthMeters);
        const double apparentRadius = baseCenterDistance <= conservativeBoundingRadius
            ? 1.5707963267948966
            : std::asin(std::clamp(
                conservativeBoundingRadius / baseCenterDistance, 0.0, 1.0));
        const double viewSeparation = angleBetween(viewForward, toCenter);
        visible = viewSeparation <= config.viewConeHalfAngleRadians + apparentRadius;
    }
    if (!visible) {
        return {
            geometry.centerDirection,
            geometry.angularRadius,
            geometry.spanMeters,
            baseCenterDistance,
            0.0,
            0.0,
            false,
        };
    }

    const PlanetTerrainSample centerTerrain = surface.sample(geometry.centerDirection);
''',
    'cheap LOD visibility before terrain')

replace_once(
    'lod_cpp',
'''    const double radius = std::max(1.0, planet.radius);
    const double cameraRadius = glm::length(camera);
    const glm::dvec3 cameraDirection = safeNormalize(camera, geometry.centerDirection);
    const double centerSurfaceRadius = radius + centerTerrain.elevationMeters;
''',
'''    const double centerSurfaceRadius = radius + centerTerrain.elevationMeters;
''',
    'remove duplicate camera geometry')

replace_once(
    'lod_cpp',
'''    double horizonAngle = 3.14159265358979323846;
    if (cameraRadius > radius + 1.0) {
        horizonAngle = std::acos(std::clamp(radius / cameraRadius, 0.0, 1.0));
    }
    const double cameraSeparation = angleBetween(cameraDirection, geometry.centerDirection);
    const bool visible = cameraSeparation
        <= horizonAngle + geometry.angularRadius + config.horizonMarginRadians;
    return {
''',
'''    return {
''',
    'remove late visibility work')

replace_once(
    'lod_cpp',
'''void appendPatch(
    PlanetMesh& mesh,
    const Node& node,
    const PlanetSurfaceAuthority& surface,
    const PlanetLodConfig& config,
    PlanetLodStats* stats) {
''',
'''struct PatchScratch {
    std::vector<glm::dvec3> directions{};
    std::vector<glm::dvec3> positions{};
    std::vector<PlanetTerrainSample> terrainSamples{};
    std::vector<std::uint32_t> edge{};
};

void appendPatch(
    PlanetMesh& mesh,
    const Node& node,
    const PlanetSurfaceAuthority& surface,
    const PlanetLodConfig& config,
    PlanetLodStats* stats,
    PatchScratch& scratch) {
''',
    'patch scratch type')

replace_once(
    'lod_cpp',
'''    std::vector<glm::dvec3> directions(pointCount);
    std::vector<glm::dvec3> positions(pointCount);
    std::vector<PlanetTerrainSample> terrainSamples(pointCount);
''',
'''    auto& directions = scratch.directions;
    auto& positions = scratch.positions;
    auto& terrainSamples = scratch.terrainSamples;
    directions.resize(pointCount);
    positions.resize(pointCount);
    terrainSamples.resize(pointCount);
''',
    'reuse patch point buffers')

replace_once(
    'lod_cpp',
'''        std::vector<std::uint32_t> edge;
        edge.reserve(stride);
''',
'''        auto& edge = scratch.edge;
        edge.clear();
        edge.reserve(stride);
''',
    'reuse patch edge buffer')

replace_once(
    'lod_cpp',
'''    config.transitionFarCellMeters = std::clamp(
        std::max(config.nearFieldCellMeters, config.transitionFarCellMeters),
        config.nearFieldCellMeters,
        5000.0);
''',
'''    config.transitionFarCellMeters = std::clamp(
        std::max(config.nearFieldCellMeters, config.transitionFarCellMeters),
        config.nearFieldCellMeters,
        5000.0);
    config.viewConeHalfAngleRadians = std::clamp(
        config.viewConeHalfAngleRadians, 0.25, 3.14159265358979323846);
''',
    'clamp view cone')

replace_once(
    'lod_cpp',
'''        if (!metric.aboveHorizon) return -1.0;
''',
'''        if (!metric.aboveHorizon) {
            ++localStats.culledNodes;
            return -1.0;
        }
''',
    'count culled nodes')

replace_once(
    'lod_cpp',
'''    for (const Node& node : leaves)
        appendPatch(mesh, node, surface, config, &localStats);
''',
'''    PatchScratch scratch{};
    scratch.directions.reserve(baseVerticesPerPatch);
    scratch.positions.reserve(baseVerticesPerPatch);
    scratch.terrainSamples.reserve(baseVerticesPerPatch);
    scratch.edge.reserve(config.patchResolution + 1U);
    for (const Node& node : leaves)
        appendPatch(mesh, node, surface, config, &localStats, scratch);
''',
    'reuse scratch across all patches')

# -----------------------------------------------------------------------------
# 4) Main runtime: feed camera forward into LOD, scale the leaf budget to visible prefetch cone,
#    and rebuild when the player turns far enough that the prefetched view is becoming stale.
# -----------------------------------------------------------------------------
replace_once(
    'main',
'''        const glm::dvec3 patchUp = safeNormalize(initialCameraPlanet);
        const glm::dvec3 patchEast = stableTangent(patchUp);
''',
'''        const glm::dvec3 patchUp = safeNormalize(initialCameraPlanet);
        const glm::dvec3 initialViewForwardPlanet = safeNormalize(
            initialInverseAster * camera.forwardDirection(), stableTangent(patchUp));
        const glm::dvec3 patchEast = stableTangent(patchUp);
''',
    'initial local view forward')

replace_once(
    'main',
'''        glm::dvec3 lodCenterDirection = patchUp;
        struct TerrainBuildResult {
            glm::dvec3 centerDirection{};
''',
'''        glm::dvec3 lodCenterDirection = patchUp;
        glm::dvec3 lodViewForwardDirection = initialViewForwardPlanet;
        struct TerrainBuildResult {
            glm::dvec3 centerDirection{};
            glm::dvec3 viewForwardDirection{};
''',
    'track LOD view direction')

replace_once(
    'main',
'''        auto buildTerrainLod = [&amp;](
            const glm::dvec3& centerDirection,
            const glm::dvec3& cameraPlanetLocal,
            std::shared_ptr<const vf::RegionalHydrology> reusableHydrology = {}) {
'''.replace('&amp;', '&'),
'''        auto buildTerrainLod = [&](
            const glm::dvec3& centerDirection,
            const glm::dvec3& cameraPlanetLocal,
            const glm::dvec3& viewForwardPlanetLocal,
            std::shared_ptr<const vf::RegionalHydrology> reusableHydrology = {}) {
''',
    'terrain build view parameter')

replace_once(
    'main',
'''            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 3600U
                : (buildAltitude < 150000.0 ? 1900U : 850U);
            lodConfig.verticalFovRadians = glm::radians(68.0);
''',
'''            // The old budget covered essentially the whole horizon ring although only one camera
            // frustum can contribute pixels. Keep the same local SSE/cell rules but budget the
            // widened 200-degree prefetch cone instead of a 360-degree high-detail ring.
            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 2200U
                : (buildAltitude < 150000.0 ? 1200U : 550U);
            lodConfig.verticalFovRadians = glm::radians(68.0);
            lodConfig.viewForwardPlanetLocal = safeNormalize(
                viewForwardPlanetLocal, stableTangent(centerUp));
            lodConfig.viewConeHalfAngleRadians = glm::radians(100.0);
''',
    'view-aware LOD budget')

replace_once(
    'main',
'''            TerrainBuildResult result{};
            result.centerDirection = centerUp;
            result.hydrology = hydrology;
''',
'''            TerrainBuildResult result{};
            result.centerDirection = centerUp;
            result.viewForwardDirection = lodConfig.viewForwardPlanetLocal;
            result.hydrology = hydrology;
''',
    'result view direction')

replace_once(
    'main',
'''        TerrainBuildResult initialTerrain = buildTerrainLod(lodCenterDirection, initialCameraPlanet, {});
''',
'''        TerrainBuildResult initialTerrain = buildTerrainLod(
            lodCenterDirection, initialCameraPlanet, initialViewForwardPlanet, {});
''',
    'initial view-aware terrain build')

replace_once(
    'main',
'''                  << " indices=" << initialTerrain.mesh.indices.size()
                  << " hydrology_reused=" << (initialTerrain.reusedHydrology ? 1 : 0) << '\\n';
''',
'''                  << " indices=" << initialTerrain.mesh.indices.size()
                  << " leaf_patches=" << initialTerrain.stats.leafPatches
                  << " culled_nodes=" << initialTerrain.stats.culledNodes
                  << " hydrology_reused=" << (initialTerrain.reusedHydrology ? 1 : 0) << '\\n';
''',
    'initial performance LOD telemetry')

replace_once(
    'main',
'''            if (streaming.requestBuild) {
                const glm::dvec3 requestedDirection = cameraDirection;
                const glm::dvec3 requestedCameraPlanet = cameraPlanet;
                const auto reusableHydrology = surfaceAuthority.hydrology();
''',
'''            const double viewTurnRadians = std::acos(std::clamp(
                glm::dot(
                    safeNormalize(forwardPlanet, lodViewForwardDirection),
                    safeNormalize(lodViewForwardDirection, forwardPlanet)),
                -1.0, 1.0));
            const bool viewPrefetchExpired = viewTurnRadians > glm::radians(28.0)
                && camera.physicsFrameBodyId() == asterId
                && !terrainBuildInFlight
                && lodCooldown <= 0.0;
            if (streaming.requestBuild || viewPrefetchExpired) {
                const glm::dvec3 requestedDirection = cameraDirection;
                const glm::dvec3 requestedCameraPlanet = cameraPlanet;
                const glm::dvec3 requestedViewForward = forwardPlanet;
                const auto reusableHydrology = surfaceAuthority.hydrology();
''',
    'view-turn terrain prefetch')

replace_once(
    'main',
'''                    [&, requestedDirection, requestedCameraPlanet, reusableHydrology]() {
                        return buildTerrainLod(
                            requestedDirection, requestedCameraPlanet, reusableHydrology);
                    });
''',
'''                    [&, requestedDirection, requestedCameraPlanet, requestedViewForward, reusableHydrology]() {
                        return buildTerrainLod(
                            requestedDirection,
                            requestedCameraPlanet,
                            requestedViewForward,
                            reusableHydrology);
                    });
''',
    'capture view forward in terrain job')

replace_once(
    'main',
'''                    lodCenterDirection = completed.centerDirection;
                    surfaceAuthority.setHydrology(completed.hydrology);
''',
'''                    lodCenterDirection = completed.centerDirection;
                    lodViewForwardDirection = completed.viewForwardDirection;
                    surfaceAuthority.setHydrology(completed.hydrology);
''',
    'accept view direction')

replace_once(
    'main',
'''                              << " indices=" << nearTerrain.indices.size()
                              << " hydrology_reused=" << (completed.reusedHydrology ? 1 : 0)
''',
'''                              << " indices=" << nearTerrain.indices.size()
                              << " leaf_patches=" << completed.stats.leafPatches
                              << " culled_nodes=" << completed.stats.culledNodes
                              << " hydrology_reused=" << (completed.reusedHydrology ? 1 : 0)
''',
    'streaming performance LOD telemetry')

for key, path in FILES.items():
    path.write_text(texts[key], encoding='utf-8')

print('R24 EXTREME RUNTIME RESCUE materialized')
print(' - cached static climate terrain samples')
print(' - decoupled global climate from 0.25 s celestial substeps (300 s simulated cadence)')
print(' - cheap horizon/view rejection before relief sampling')
print(' - 200 degree view-prefetch cone with turn-triggered async rebuild')
print(' - reusable patch scratch buffers across the entire terrain build')
