from pathlib import Path


def rep(s, old, new, label):
    if old not in s:
        raise SystemExit(f'{label} not found')
    return s.replace(old, new, 1)

# -----------------------------------------------------------------------------
# Renderer architecture: never overlap the local clipmap with a coarse whole-planet terrain mesh
# at ground/low altitude. R14 screenshots exposed the coarse proxy poking through incised channels,
# mountain valleys and coasts because a fixed 24 m inset cannot cover kilometre-scale relief.
# -----------------------------------------------------------------------------
p = Path('native/src/app/Main.cpp')
s = p.read_text()
if 'R15 mutually exclusive orbital proxy' not in s:
    s = rep(s,
'''        auto buildTerrainLod = [&](const glm::dvec3& centerDirection) {
            vf::PlanetMesh mesh{};
            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);
            const glm::dvec3 centerEast = stableTangent(centerUp);
            const glm::dvec3 centerNorth = safeNormalize(glm::cross(centerUp, centerEast), patchZ);
''',
'''        auto buildTerrainLod = [&](const glm::dvec3& centerDirection, bool orbitalOnly) {
            vf::PlanetMesh mesh{};
            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);
            const glm::dvec3 centerEast = stableTangent(centerUp);
            const glm::dvec3 centerNorth = safeNormalize(glm::cross(centerUp, centerEast), patchZ);

            // R15 mutually exclusive orbital proxy. The full-planet proxy and the local clipmap
            // are never rendered together: their different sampling densities otherwise intersect
            // wherever local incision/relief exceeds the old 24 m inset. Above the orbital switch
            // the global proxy is sufficient; below it the nested local clipmap is authoritative.
            if (orbitalOnly) {
                appendMesh(mesh, orbitalProxy);
                vf::PlanetMesh orbitalOcean{};
                vf::appendOceanSurfaceProxy(
                    orbitalOcean,
                    {},
                    planet.radius + planet.seaLevelElevationMeters - 1.5,
                    128U);
                for (auto& vertex : orbitalOcean.vertices) {
                    vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));
                    vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
                    vertex.material.w = -20.0F;
                }
                appendMesh(mesh, orbitalOcean);
                return mesh;
            }
''', 'build signature')

    s = rep(s,
'''            // Cached whole-planet proxy: no expensive global re-sampling on every local stream update.
            appendMesh(mesh, orbitalProxy);

''',
'''            // R15: no whole-planet terrain proxy in local mode. The outer clipmap ring alone
            // covers the entire ground/low-altitude horizon without a second terrain surface.

''', 'remove local orbital proxy')

    s = rep(s,
'''        vf::PlanetMesh staticTerrain = buildTerrainLod(lodCenterDirection);
        renderer.uploadPlanetMesh(staticTerrain);
        std::future<std::pair<glm::dvec3, vf::PlanetMesh>> terrainBuildFuture{};
        bool terrainBuildInFlight = false;
''',
'''        bool lodIncludesOrbitalProxy = false;
        bool terrainBuildRequestedOrbitalProxy = false;
        vf::PlanetMesh staticTerrain = buildTerrainLod(lodCenterDirection, false);
        renderer.uploadPlanetMesh(staticTerrain);
        std::future<std::pair<glm::dvec3, vf::PlanetMesh>> terrainBuildFuture{};
        bool terrainBuildInFlight = false;
''', 'initial build')

    old = '''                const double prefetchThreshold = threshold * 0.42;

                if (!terrainBuildInFlight && lodCooldown <= 0.0 && arcDistance > prefetchThreshold) {
                    const glm::dvec3 requestedDirection = cameraDirection;
                    terrainBuildFuture = std::async(std::launch::async, [&, requestedDirection]() {
                        return std::make_pair(requestedDirection, buildTerrainLod(requestedDirection));
                    });
                    terrainBuildInFlight = true;
                }

                if (terrainBuildInFlight
                    && terrainBuildFuture.wait_for(std::chrono::milliseconds{0})
                        == std::future_status::ready) {
                    auto completed = terrainBuildFuture.get();
                    terrainBuildInFlight = false;
                    lodCenterDirection = completed.first;
                    staticTerrain = std::move(completed.second);
                    renderer.uploadPlanetMesh(staticTerrain);
                    lodCooldown = 0.12;
                }
'''
    new = '''                const double prefetchThreshold = threshold * 0.42;
                constexpr double orbitalProxyEnableAltitude = 320000.0;
                const bool desiredOrbitalProxy = altitude >= orbitalProxyEnableAltitude;
                const bool proxyModeChanged = desiredOrbitalProxy != lodIncludesOrbitalProxy;
                const bool needsDirectionalRefresh = !desiredOrbitalProxy
                    && arcDistance > prefetchThreshold;

                if (!terrainBuildInFlight && lodCooldown <= 0.0
                    && (proxyModeChanged || needsDirectionalRefresh)) {
                    const glm::dvec3 requestedDirection = cameraDirection;
                    const bool requestedOrbitalProxy = desiredOrbitalProxy;
                    terrainBuildRequestedOrbitalProxy = requestedOrbitalProxy;
                    terrainBuildFuture = std::async(
                        std::launch::async,
                        [&, requestedDirection, requestedOrbitalProxy]() {
                            return std::make_pair(
                                requestedDirection,
                                buildTerrainLod(requestedDirection, requestedOrbitalProxy));
                        });
                    terrainBuildInFlight = true;
                }

                if (terrainBuildInFlight
                    && terrainBuildFuture.wait_for(std::chrono::milliseconds{0})
                        == std::future_status::ready) {
                    auto completed = terrainBuildFuture.get();
                    terrainBuildInFlight = false;
                    lodCenterDirection = completed.first;
                    lodIncludesOrbitalProxy = terrainBuildRequestedOrbitalProxy;
                    staticTerrain = std::move(completed.second);
                    renderer.uploadPlanetMesh(staticTerrain);
                    lodCooldown = 0.12;
                }
'''
    s = rep(s, old, new, 'streaming proxy mode')

    # R15 capture target local refinement. The global Fibonacci pass is deliberately coarse; after
    # it finds the right province, refine within tens of kilometres to locate the actual coast edge,
    # plateau rim or mountain summit instead of photographing the province interior.
    marker = '    return safeNormalize(best, preferred);\n}\n\n[[nodiscard]] glm::dvec3 findCaptureVantageDirection('
    if marker not in s:
        raise SystemExit('capture return marker not found')
    refinement = '''    if (!captureMode.empty() && found) {
        const glm::dvec3 seed = safeNormalize(best, preferred);
        const glm::dvec3 east = stableTangent(seed);
        const glm::dvec3 north = safeNormalize(glm::cross(seed, east), {0.0, 0.0, 1.0});
        const std::array<double, 8> refineRadii{0.0, 1500.0, 3000.0, 5000.0,
            8000.0, 12000.0, 18000.0, 26000.0};
        glm::dvec3 refined = seed;
        double refinedScore = -std::numeric_limits<double>::infinity();
        bool refinedFound = false;
        for (double radiusMeters : refineRadii) {
            const double angular = radiusMeters / std::max(1.0, planet.radius);
            const int samples = radiusMeters <= 0.0 ? 1 : 72;
            for (int j = 0; j < samples; ++j) {
                const double a = samples == 1 ? 0.0
                    : 2.0 * kPi * static_cast<double>(j) / static_cast<double>(samples);
                const glm::dvec3 d = radiusMeters <= 0.0
                    ? seed
                    : safeNormalize(seed
                        + east * (std::cos(a) * angular)
                        + north * (std::sin(a) * angular), seed);
                const vf::PlanetTerrainSample terrain = vf::samplePlanetTerrain(planet, d);
                if (terrain.submerged(planet)) continue;
                const double h = terrain.elevationMeters - planet.seaLevelElevationMeters;
                double score = -std::numeric_limits<double>::infinity();
                if (captureMode == "coast") {
                    const LocalReliefStats r = sampleLocalRelief(planet, d, 1800.0);
                    const double relief = r.maxElevation - r.minElevation;
                    if (r.minElevation > -2.0 || h < 70.0 || h > 900.0) continue;
                    score = terrain.coastalCliff * 10.0 + relief / 70.0
                        - std::abs(h - 360.0) / 420.0;
                } else if (captureMode == "highland") {
                    const LocalReliefStats r = sampleLocalRelief(planet, d, 7000.0);
                    const double relief = r.maxElevation - r.minElevation;
                    if (terrain.plateau < 0.38 || h < 2100.0 || h > 3150.0
                        || relief < 420.0) continue;
                    score = terrain.plateau * 8.0 + relief / 420.0
                        + std::clamp((h - r.minElevation) / 1000.0, 0.0, 2.0) * 3.0;
                } else if (captureMode == "mountain") {
                    const LocalReliefStats r = sampleLocalRelief(planet, d, 18000.0);
                    const double relief = r.maxElevation - r.minElevation;
                    if (terrain.mountain < 0.10 || h < 2400.0 || relief < 1200.0) continue;
                    score = terrain.mountain * 7.0 + relief / 300.0 + h / 2400.0;
                } else {
                    score = terrain.river * 8.0 + terrain.canyon * 1.5;
                }
                if (score > refinedScore) {
                    refinedScore = score;
                    refined = d;
                    refinedFound = true;
                }
            }
        }
        if (refinedFound) best = refined;
    }
    return safeNormalize(best, preferred);
}

[[nodiscard]] glm::dvec3 findCaptureVantageDirection('''
    s = s.replace(marker, refinement, 1)

    # A relaxed highland camera is still required to be below the target; otherwise R14 selected a
    # higher neighbouring shelf and aimed downhill, hiding the escarpment.
    s = rep(s,
'''                } else if (mode == "highland") {
                    if (terrain.submerged(planet)) continue;
                    const double drop = targetElevation - terrain.elevationMeters;
                    score = std::abs(drop - 850.0) * 0.42
                        + terrain.plateau * 780.0
                        + terrain.mountain * 980.0
                        + std::abs(standOffMeters - 14000.0) * 0.018;
''',
'''                } else if (mode == "highland") {
                    if (terrain.submerged(planet)) continue;
                    const double drop = targetElevation - terrain.elevationMeters;
                    if (drop < 260.0) continue;
                    score = std::abs(drop - 850.0) * 0.30
                        + terrain.plateau * 1400.0
                        + terrain.mountain * 1100.0
                        + std::abs(standOffMeters - 7000.0) * 0.020;
''', 'relaxed highland below target')
    p.write_text(s)

# -----------------------------------------------------------------------------
# Material semantics: altitude alone must not turn an entire 2.7 km plateau into gray rock.
# Mountain/canyon/slope authority still exposes rock; a level moist plateau can remain grassland.
# -----------------------------------------------------------------------------
p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
if 'R15 plateau material semantics' not in s:
    if s.count('|| sample.coastalCliff > 0.16 || sample.elevationMeters > 2500.0)') != 1:
        raise SystemExit('color rock altitude marker not found')
    s = s.replace(
        '|| sample.coastalCliff > 0.16 || sample.elevationMeters > 2500.0)',
        '|| sample.coastalCliff > 0.16 || sample.elevationMeters > 4800.0)', 1)
    if s.count('|| sample.coastalCliff > 0.30 || sample.elevationMeters > 2500.0)') != 1:
        raise SystemExit('material rock altitude marker not found')
    s = s.replace(
        '|| sample.coastalCliff > 0.30 || sample.elevationMeters > 2500.0)',
        '|| sample.coastalCliff > 0.30 || sample.elevationMeters > 4800.0)', 1)
    anchor = 'glm::vec3 planetTerrainColor(\n'
    s = s.replace(anchor,
'''// R15 plateau material semantics: level highlands keep biome material; rock exposure follows
// mountain/canyon/cliff/slope authority rather than a blanket 2.5 km altitude threshold.
''' + anchor, 1)
    p.write_text(s)
