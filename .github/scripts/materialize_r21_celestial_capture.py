from pathlib import Path


def rep(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'R21 celestial capture anchor not found: {label}')
    return text.replace(old, new, 1)

p = Path('native/src/app/Main.cpp')
s = p.read_text()
if 'R21 CELESTIAL EVIDENCE CAMERA' not in s:
    old = '''        const glm::dvec3 featureDirection = findPlayableSpawnDirection(planet, initialSunDirectionPlanet);
        const char* captureEnv = std::getenv("VF_CAPTURE_LANDFORM");
        const std::string_view captureMode = captureEnv != nullptr
            ? std::string_view{captureEnv} : std::string_view{};
        const glm::dvec3 spawnDirection = captureMode.empty()
            ? featureDirection
            : findCaptureVantageDirection(planet, featureDirection, captureMode);
        const vf::PlanetTerrainSample spawnTerrain = vf::samplePlanetTerrain(planet, spawnDirection);
        vf::PlanetCamera camera{planet, &celestial, asterId, spawnDirection};
'''
    new = '''        const glm::dvec3 featureDirection = findPlayableSpawnDirection(planet, initialSunDirectionPlanet);
        const char* captureEnv = std::getenv("VF_CAPTURE_LANDFORM");
        const std::string_view captureMode = captureEnv != nullptr
            ? std::string_view{captureEnv} : std::string_view{};
        const char* celestialCaptureEnv = std::getenv("VF_CAPTURE_CELESTIAL");
        const std::string_view celestialCaptureMode = celestialCaptureEnv != nullptr
            ? std::string_view{celestialCaptureEnv} : std::string_view{};

        // R21 CELESTIAL EVIDENCE CAMERA. The target direction is derived from the actual N-body
        // world state and transformed into Aster's rotating body frame. We stand 30 degrees from
        // the sub-body point, putting the physical Sun/Moon about 60 degrees above the local
        // horizon. No authored sky angle is used.
        glm::dvec3 celestialSpawnDirection = featureDirection;
        if (!celestialCaptureMode.empty()) {
            const vf::CelestialBody* targetBody = celestialCaptureMode == "moon"
                ? celestial.body(lunaId) : celestial.body(sunId);
            const vf::CelestialBody* storedAster = celestial.body(asterId);
            if (targetBody != nullptr && storedAster != nullptr) {
                const glm::dquat invAster = glm::conjugate(glm::normalize(storedAster->orientation));
                const glm::dvec3 targetBodyLocal = safeNormalize(
                    invAster * (targetBody->position - storedAster->position), featureDirection);
                const glm::dvec3 tangent = stableTangent(targetBodyLocal);
                constexpr double zenithOffset = 30.0 * kPi / 180.0;
                celestialSpawnDirection = safeNormalize(
                    targetBodyLocal * std::cos(zenithOffset)
                        + tangent * std::sin(zenithOffset),
                    targetBodyLocal);
            }
        }
        const glm::dvec3 spawnDirection = !celestialCaptureMode.empty()
            ? celestialSpawnDirection
            : (captureMode.empty() ? featureDirection
                : findCaptureVantageDirection(planet, featureDirection, captureMode));
        const vf::PlanetTerrainSample spawnTerrain = vf::samplePlanetTerrain(planet, spawnDirection);
        vf::PlanetCamera camera{planet, &celestial, asterId, spawnDirection};
'''
    s = rep(s, old, new, 'capture mode setup')

    old2 = '''        if (!captureMode.empty()) {
            const double targetLift = captureMode == "mountain" ? 120.0
'''
    new2 = '''        if (!celestialCaptureMode.empty()) {
            const vf::CelestialBody* targetBody = celestialCaptureMode == "moon"
                ? celestial.body(lunaId) : celestial.body(sunId);
            const vf::CelestialBody* storedAster = celestial.body(asterId);
            if (targetBody != nullptr && storedAster != nullptr) {
                const double localSurface = vf::planetSurfaceRadius(planet, spawnDirection);
                const glm::dvec3 cameraPlanet = spawnDirection * (localSurface + 35.0);
                const glm::dvec3 cameraWorld = storedAster->position
                    + storedAster->orientation * cameraPlanet;
                camera.setFlightMode(true);
                camera.setExternalWorldState(cameraWorld, storedAster->linearVelocity, false);
                camera.setViewDirection(
                    targetBody->position - cameraWorld,
                    safeNormalize(storedAster->orientation * spawnDirection));
                const double targetDistance = glm::length(targetBody->position - cameraWorld);
                const double angularDiameterDeg = 2.0 * glm::degrees(std::asin(std::clamp(
                    targetBody->radiusMeters / std::max(targetDistance, targetBody->radiusMeters),
                    0.0, 1.0)));
                std::cout << "Celestial capture: " << celestialCaptureMode
                          << " | physical distance: " << targetDistance / 1000.0 << " km"
                          << " | physical radius: " << targetBody->radiusMeters / 1000.0 << " km"
                          << " | angular diameter: " << angularDiameterDeg << " deg\\n";
            }
        } else if (!captureMode.empty()) {
            const double targetLift = captureMode == "mountain" ? 120.0
'''
    s = rep(s, old2, new2, 'celestial camera orientation')

    old3 = '''        std::cout << "Spawn land elevation: " << std::fixed << std::setprecision(1)
                  << spawnTerrain.elevationMeters << " m\\n";
'''
    new3 = '''        std::cout << "Spawn land elevation: " << std::fixed << std::setprecision(1)
                  << spawnTerrain.elevationMeters << " m\\n";
        if (const auto* storedAster = celestial.body(asterId)) {
            if (const auto* storedSun = celestial.body(sunId)) {
                std::cout << "Aster-Sun distance: "
                          << glm::length(storedAster->position - storedSun->position) / 1000.0
                          << " km | relative speed: "
                          << glm::length(storedAster->linearVelocity - storedSun->linearVelocity) / 1000.0
                          << " km/s\\n";
            }
            if (const auto* storedMoon = celestial.body(lunaId)) {
                std::cout << "Aster-Luna distance: "
                          << glm::length(storedMoon->position - storedAster->position) / 1000.0
                          << " km | relative speed: "
                          << glm::length(storedMoon->linearVelocity - storedAster->linearVelocity) / 1000.0
                          << " km/s\\n";
            }
        }
'''
    s = rep(s, old3, new3, 'orbital startup diagnostics')
    p.write_text(s)
