from pathlib import Path

path = Path("native/src/app/Main.cpp")
text = path.read_text(encoding="utf-8")

marker = """    bool found = false;\n\n    for (std::uint32_t i = 0; i < sampleCount; ++i) {"""
inserted = """    bool found = false;

    // Evidence-only extension: select the actual high-valued procedural field for every visible
    // geomorph class instead of renaming arbitrary terrain. The production generator is unchanged;
    // this only chooses where the CI camera is placed.
    const bool extendedCaptureMode = captureMode == \"hills\" || captureMode == \"canyon\"
        || captureMode == \"dunes\" || captureMode == \"wetland\" || captureMode == \"glacier\"
        || captureMode == \"volcano\" || captureMode == \"arid\" || captureMode == \"lowland\";
    if (extendedCaptureMode) {
        for (std::uint32_t i = 0; i < sampleCount; ++i) {
            const double y = 1.0 - 2.0 * (static_cast<double>(i) + 0.5)
                / static_cast<double>(sampleCount);
            const double radial = std::sqrt(std::max(0.0, 1.0 - y * y));
            const double a = goldenAngle * static_cast<double>(i);
            const glm::dvec3 d{std::cos(a) * radial, y, std::sin(a) * radial};
            const vf::PlanetTerrainSample terrain = vf::samplePlanetTerrain(planet, d);
            const double aboveSea = terrain.elevationMeters - planet.seaLevelElevationMeters;
            if (terrain.submerged(planet) || aboveSea < 4.0) continue;
            const double sunElevation = glm::dot(d, sunDirection);
            if (sunElevation < 0.10) continue;
            double score = sunElevation * 0.35;

            if (captureMode == \"hills\") {
                if (terrain.hills < 0.18 || aboveSea > 2600.0) continue;
                score += terrain.hills * 13.0 - terrain.mountain * 4.5
                    - std::abs(aboveSea - 850.0) / 1400.0;
            } else if (captureMode == \"canyon\") {
                if (terrain.canyon < 0.14 || aboveSea > 3000.0) continue;
                score += terrain.canyon * 15.0 + terrain.river * 3.0
                    + terrain.hills * 1.5 - terrain.plateau * 1.5;
            } else if (captureMode == \"dunes\") {
                if (terrain.dunes < 0.15 || terrain.aridity < 0.45 || aboveSea > 1800.0) continue;
                score += terrain.dunes * 15.0 + terrain.aridity * 5.0 - terrain.moisture * 5.0;
            } else if (captureMode == \"wetland\") {
                if (terrain.wetland < 0.12 || terrain.moisture < 0.48 || aboveSea > 800.0) continue;
                score += terrain.wetland * 15.0 + terrain.moisture * 5.0
                    - std::abs(aboveSea - 180.0) / 500.0;
            } else if (captureMode == \"glacier\") {
                if (terrain.glacier < 0.10) continue;
                score += terrain.glacier * 18.0 + aboveSea / 2400.0 - terrain.aridity * 2.0;
            } else if (captureMode == \"volcano\") {
                if (terrain.volcano < 0.16) continue;
                score += terrain.volcano * 19.0 + terrain.mountain * 2.0 + aboveSea / 3000.0;
            } else if (captureMode == \"arid\") {
                if (terrain.aridity < 0.58 || terrain.moisture > 0.48 || aboveSea > 2200.0) continue;
                score += terrain.aridity * 12.0 + terrain.dunes * 3.0 - terrain.moisture * 8.0;
            } else if (captureMode == \"lowland\") {
                if (aboveSea < 25.0 || aboveSea > 650.0 || terrain.mountain > 0.16
                    || terrain.canyon > 0.14 || terrain.plateau > 0.32) continue;
                score += 5.0 - terrain.mountain * 8.0 - terrain.canyon * 6.0
                    - terrain.hills * 2.5 - std::abs(aboveSea - 260.0) / 400.0;
            }

            if (!found || score > bestScore) {
                bestScore = score;
                best = d;
                found = true;
            }
        }
        if (found) return safeNormalize(best, preferred);
    }

    for (std::uint32_t i = 0; i < sampleCount; ++i) {"""
if marker not in text:
    raise SystemExit("spawn selector insertion point not found")
text = text.replace(marker, inserted, 1)

old_spawn = """        const glm::dvec3 spawnDirection = !celestialCaptureMode.empty()
            ? celestialSpawnDirection
            : (captureMode.empty() ? featureDirection
                : findCaptureVantageDirection(planet, featureDirection, captureMode));"""
new_spawn = """        const bool legacyLandformVantage = captureMode == \"mountain\" || captureMode == \"river\"
            || captureMode == \"coast\" || captureMode == \"highland\";
        const double evidenceStandOffMeters = captureMode == \"mountain\" ? 12000.0
            : ((captureMode == \"volcano\" || captureMode == \"glacier\" || captureMode == \"canyon\") ? 9000.0
            : (captureMode == \"highland\" ? 10000.0 : 6000.0));
        const glm::dvec3 evidenceVantageDirection = safeNormalize(
            featureDirection + stableTangent(featureDirection)
                * (evidenceStandOffMeters / std::max(1.0, planet.radius)),
            featureDirection);
        const glm::dvec3 spawnDirection = !celestialCaptureMode.empty()
            ? celestialSpawnDirection
            : (captureMode.empty() ? featureDirection
                : (legacyLandformVantage
                    ? findCaptureVantageDirection(planet, featureDirection, captureMode)
                    : evidenceVantageDirection));"""
if old_spawn not in text:
    raise SystemExit("spawn vantage block not found")
text = text.replace(old_spawn, new_spawn, 1)

old_camera = """            const double cameraLift = captureMode == \"mountain\" ? 120.0
                : (captureMode == \"highland\" ? 105.0
                : (captureMode == \"coast\" ? 45.0 : 180.0));"""
new_camera = """            // Evidence-only overview altitude. Production gameplay camera behavior is untouched.
            const double cameraLift = captureMode == \"mountain\" ? 5500.0
                : (captureMode == \"volcano\" ? 4800.0
                : (captureMode == \"glacier\" ? 4200.0
                : (captureMode == \"highland\" ? 3200.0
                : (captureMode == \"canyon\" ? 3000.0
                : (captureMode == \"hills\" ? 2400.0
                : ((captureMode == \"dunes\" || captureMode == \"arid\") ? 1900.0
                : ((captureMode == \"coast\" || captureMode == \"river\") ? 1600.0
                : ((captureMode == \"wetland\" || captureMode == \"lowland\") ? 1300.0 : 1800.0))))))));"""
if old_camera not in text:
    raise SystemExit("camera lift block not found")
text = text.replace(old_camera, new_camera, 1)

path.write_text(text, encoding="utf-8")
print("Patched R21 evidence target search and camera")
