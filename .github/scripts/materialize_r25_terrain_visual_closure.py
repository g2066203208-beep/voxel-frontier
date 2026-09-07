from pathlib import Path

MAIN = Path("native/src/app/Main.cpp")
text = MAIN.read_text(encoding="utf-8")

if "R25 TERRAIN EVIDENCE FRAME" in text:
    print("R25 terrain evidence-frame patch already materialized")
    raise SystemExit(0)

old_fallback = '''    if (!foundVantage || glm::dot(best, target) > 0.9999995) {
        const double fallbackMeters = mode == "coast" ? 700.0
            : (mode == "river" ? 1000.0 : (mode == "highland" ? 4500.0 : 9000.0));
        const double angular = fallbackMeters / std::max(1.0, planet.radius);
        best = safeNormalize(target + east * angular, target);
    }
    return safeNormalize(best, target);
'''
new_fallback = '''    // R25 TERRAIN EVIDENCE FRAME: an evidence camera is not allowed to escape the semantic
    // constraints through an unchecked geometric offset. Search progressively wider annuli and
    // either return a physically meaningful vantage or leave the camera on the target, which the
    // evidence gate will reject explicitly instead of producing a misleading green screenshot.
    if (!foundVantage || glm::dot(best, target) > 0.9999995) {
        const std::array<double, 13> emergencyRadii{
            500.0, 900.0, 1500.0, 2500.0, 4000.0, 6500.0, 10000.0,
            16000.0, 24000.0, 36000.0, 52000.0, 80000.0, 120000.0};
        bestScore = std::numeric_limits<double>::infinity();
        foundVantage = false;
        for (double standOffMeters : emergencyRadii) {
            const double angular = standOffMeters / std::max(1.0, planet.radius);
            for (int i = 0; i < 96; ++i) {
                const double a = 2.0 * kPi * static_cast<double>(i) / 96.0;
                const glm::dvec3 d = safeNormalize(
                    target + east * (std::cos(a) * angular) + north * (std::sin(a) * angular),
                    target);
                const vf::PlanetTerrainSample terrain = vf::samplePlanetTerrain(planet, d);
                const double cameraElevation = terrain.elevationMeters - planet.seaLevelElevationMeters;
                const double drop = targetElevation - terrain.elevationMeters;
                double score = std::numeric_limits<double>::infinity();

                if (mode == "coast") {
                    if (!terrain.submerged(planet)) continue;
                    score = std::abs(terrain.elevationMeters + 12.0) * 0.08
                        + std::abs(standOffMeters - 2200.0) * 0.012;
                } else if (mode == "river") {
                    if (terrain.submerged(planet) || terrain.river > 0.16 || cameraElevation < 60.0) continue;
                    score = std::abs(terrain.elevationMeters - targetElevation) * 0.08
                        + terrain.river * 3200.0
                        + std::abs(standOffMeters - 1400.0) * 0.018;
                } else if (mode == "mountain") {
                    if (terrain.submerged(planet) || drop < 700.0) continue;
                    const double apparent = std::atan2(drop, std::max(1.0, standOffMeters));
                    score = -apparent * 22000.0
                        + terrain.mountain * 500.0
                        + std::abs(standOffMeters - 9000.0) * 0.012;
                } else {
                    if (terrain.submerged(planet) || terrain.plateau > 0.24 || drop < 500.0) continue;
                    const double apparent = std::atan2(drop, std::max(1.0, standOffMeters));
                    score = -apparent * 20000.0
                        + terrain.mountain * 1400.0
                        + terrain.plateau * 2800.0
                        + std::abs(standOffMeters - 8500.0) * 0.012;
                }

                if (score < bestScore) {
                    bestScore = score;
                    best = d;
                    foundVantage = true;
                }
            }
        }
        if (!foundVantage) {
            std::cerr << "R25 evidence camera: no semantically valid vantage for " << mode << '\\n';
            best = target;
        }
    }
    return safeNormalize(best, target);
'''
if old_fallback not in text:
    raise SystemExit("R25 patch failed: legacy unchecked vantage fallback not found")
text = text.replace(old_fallback, new_fallback, 1)

old_capture = '''        } else if (!captureMode.empty()) {
            const double targetLift = captureMode == "mountain" ? 120.0
                : (captureMode == "highland" ? 45.0 : (captureMode == "coast" ? 70.0 : 18.0));
            const double cameraLift = captureMode == "mountain" ? 120.0
                : (captureMode == "highland" ? 105.0
                : (captureMode == "coast" ? 45.0 : 180.0));
            const glm::dvec3 targetPlanet = featureDirection
                * (vf::planetSurfaceRadius(planet, featureDirection) + targetLift);
            const double localSurface = vf::planetSurfaceRadius(planet, spawnDirection);
            const double visualBase = captureMode == "coast"
                ? std::max(localSurface, planet.radius + planet.seaLevelElevationMeters)
                : localSurface;
            const glm::dvec3 cameraPlanet = spawnDirection * (visualBase + cameraLift);
            const glm::dvec3 targetWorld = aster.position + aster.orientation * targetPlanet;
            const glm::dvec3 cameraWorld = aster.position + aster.orientation * cameraPlanet;
            camera.setFlightMode(true);
            camera.setExternalWorldState(cameraWorld, aster.linearVelocity, false);
            camera.setViewDirection(
                targetWorld - cameraWorld,
                safeNormalize(aster.orientation * spawnDirection));
            // R12 apparent-prominence evidence diagnostic.
            const double captureDistance = std::acos(std::clamp(
                glm::dot(featureDirection, spawnDirection), -1.0, 1.0)) * planet.radius;
            const double captureDrop = vf::planetHeight(planet, featureDirection)
                - (visualBase - planet.radius);
            std::cout << "Capture target elevation: " << vf::planetHeight(planet, featureDirection)
                      << " m | camera surface: " << (visualBase - planet.radius)
                      << " m | lift: " << cameraLift
                      << " m | stand-off: " << captureDistance
                      << " m | apparent-deg: " << glm::degrees(std::atan2(captureDrop, std::max(1.0, captureDistance)))
                      << "\\n";
        }
'''
new_capture = '''        } else if (!captureMode.empty()) {
            // R25 TERRAIN EVIDENCE FRAME: landform captures must use the same current barycentric
            // Aster state that PlanetCamera, clipmaps and CelestialSystem use. The pre-barycentric
            // local `aster` value is hundreds of kilometres away after the COM shift and was the
            // root cause of R21 screenshots looking away from their selected terrain target.
            const vf::CelestialBody* captureAster = celestial.body(asterId);
            if (captureAster == nullptr) throw std::runtime_error("Aster missing for terrain capture");
            const double targetLift = captureMode == "mountain" ? 120.0
                : (captureMode == "highland" ? 45.0 : (captureMode == "coast" ? 70.0 : 18.0));
            const double cameraLift = captureMode == "mountain" ? 120.0
                : (captureMode == "highland" ? 105.0
                : (captureMode == "coast" ? 45.0 : 180.0));
            const glm::dvec3 targetPlanet = featureDirection
                * (vf::planetSurfaceRadius(planet, featureDirection) + targetLift);
            const double localSurface = vf::planetSurfaceRadius(planet, spawnDirection);
            const double visualBase = captureMode == "coast"
                ? std::max(localSurface, planet.radius + planet.seaLevelElevationMeters)
                : localSurface;
            const glm::dvec3 cameraPlanet = spawnDirection * (visualBase + cameraLift);
            const glm::dvec3 targetWorld = captureAster->position + captureAster->orientation * targetPlanet;
            const glm::dvec3 cameraWorld = captureAster->position + captureAster->orientation * cameraPlanet;
            camera.setFlightMode(true);
            camera.setExternalWorldState(cameraWorld, captureAster->linearVelocity, false);
            camera.setViewDirection(
                targetWorld - cameraWorld,
                safeNormalize(captureAster->orientation * spawnDirection));

            const vf::PlanetTerrainSample targetTerrain = vf::samplePlanetTerrain(planet, featureDirection);
            const double targetElevation = targetTerrain.elevationMeters - planet.seaLevelElevationMeters;
            const double cameraSurfaceElevation = visualBase - planet.radius - planet.seaLevelElevationMeters;
            const double captureDistance = std::acos(std::clamp(
                glm::dot(featureDirection, spawnDirection), -1.0, 1.0)) * planet.radius;
            const double captureDrop = targetElevation - cameraSurfaceElevation;
            const double apparentDeg = glm::degrees(
                std::atan2(captureDrop, std::max(1.0, captureDistance)));

            bool semanticValid = false;
            if (captureMode == "mountain") {
                semanticValid = !targetTerrain.submerged(planet)
                    && targetTerrain.mountain >= 0.14
                    && targetElevation >= 2500.0
                    && captureDrop >= 850.0
                    && apparentDeg >= 6.5;
            } else if (captureMode == "highland") {
                semanticValid = !targetTerrain.submerged(planet)
                    && targetTerrain.plateau >= 0.40
                    && targetElevation >= 1900.0
                    && captureDrop >= 650.0
                    && apparentDeg >= 4.0;
            } else if (captureMode == "coast") {
                semanticValid = !targetTerrain.submerged(planet)
                    && targetTerrain.coastalCliff >= 0.08
                    && targetElevation >= 60.0
                    && targetElevation <= 950.0
                    && spawnTerrain.submerged(planet)
                    && captureDistance >= 500.0
                    && captureDistance <= 120000.0;
            } else if (captureMode == "river") {
                semanticValid = !targetTerrain.submerged(planet)
                    && !spawnTerrain.submerged(planet)
                    && targetTerrain.river >= 0.18
                    && spawnTerrain.river <= 0.18
                    && targetElevation >= 100.0
                    && targetElevation <= 1800.0
                    && captureDistance >= 350.0
                    && captureDistance <= 120000.0;
            }

            std::cout << "Capture target elevation: " << targetElevation
                      << " m | camera surface: " << cameraSurfaceElevation
                      << " m | lift: " << cameraLift
                      << " m | stand-off: " << captureDistance
                      << " m | apparent-deg: " << apparentDeg
                      << "\\n";
            std::cout << "Capture semantic valid: " << (semanticValid ? "YES" : "NO")
                      << " | target mountain=" << targetTerrain.mountain
                      << " river=" << targetTerrain.river
                      << " coast=" << targetTerrain.coastalCliff
                      << " plateau=" << targetTerrain.plateau
                      << " | camera river=" << spawnTerrain.river
                      << " submerged=" << (spawnTerrain.submerged(planet) ? 1 : 0)
                      << "\\n";
        }
'''
if old_capture not in text:
    raise SystemExit("R25 patch failed: legacy landform capture block not found")
text = text.replace(old_capture, new_capture, 1)

MAIN.write_text(text, encoding="utf-8")
print("Materialized R25 terrain evidence-frame closure")
