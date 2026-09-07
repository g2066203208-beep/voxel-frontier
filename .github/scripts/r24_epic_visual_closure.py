from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one anchor, found {count}: {old[:140]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# -----------------------------------------------------------------------------
# 1) Evidence-camera clearance on extreme relief.
#
# The requested capture altitude is a clearance, not an absolute guarantee that
# the camera is above every nearby ridge. Canyon/abyss targets can sit several
# kilometres below their rim, so a camera placed only N metres above the target
# point may end up inside the surrounding terrain. Sample the same 36 km
# evidence neighbourhood at three radial rings and place the camera at least the
# requested clearance above the highest sampled terrain.
# -----------------------------------------------------------------------------
main = "native/src/app/Main.cpp"
replace_once(
    main,
    """                const double centerElevation = vf::samplePlanetTerrain(\n                    planet, spawnDirection).elevationMeters;\n                double bestContrast = -1.0;\n                glm::dvec3 bestTangent = localEvidenceTangent;\n                constexpr int directionCount = 16;\n                constexpr double probeDistanceMeters = 36000.0;\n                for (int i = 0; i < directionCount; ++i) {\n                    const double angle = 2.0 * kPi * static_cast<double>(i)\n                        / static_cast<double>(directionCount);\n                    const glm::dvec3 candidateTangent = safeNormalize(\n                        localEvidenceTangent * std::cos(angle)\n                            + localBitangent * std::sin(angle),\n                        localEvidenceTangent);\n                    const glm::dvec3 probeDirection = safeNormalize(\n                        spawnDirection\n                            + candidateTangent * (probeDistanceMeters / planet.radius),\n                        spawnDirection);\n                    const vf::PlanetTerrainSample probe = vf::samplePlanetTerrain(\n                        planet, probeDirection);\n                    const double contrast = std::abs(probe.elevationMeters - centerElevation);\n                    if (contrast > bestContrast) {\n                        bestContrast = contrast;\n                        bestTangent = candidateTangent;\n                    }\n                }\n                localEvidenceTangent = bestTangent;\n                std::cout << \"R24 terrain evidence view: contrast_m=\" << bestContrast\n                          << std::endl;\n""",
    """                const double centerElevation = vf::samplePlanetTerrain(\n                    planet, spawnDirection).elevationMeters;\n                double highestEvidenceElevation = centerElevation;\n                double bestContrast = -1.0;\n                glm::dvec3 bestTangent = localEvidenceTangent;\n                constexpr int directionCount = 16;\n                constexpr int radialRingCount = 3;\n                constexpr double probeDistanceMeters = 36000.0;\n                for (int ring = 1; ring <= radialRingCount; ++ring) {\n                    const double ringDistanceMeters = probeDistanceMeters\n                        * static_cast<double>(ring) / static_cast<double>(radialRingCount);\n                    for (int i = 0; i < directionCount; ++i) {\n                        const double angle = 2.0 * kPi * static_cast<double>(i)\n                            / static_cast<double>(directionCount);\n                        const glm::dvec3 candidateTangent = safeNormalize(\n                            localEvidenceTangent * std::cos(angle)\n                                + localBitangent * std::sin(angle),\n                            localEvidenceTangent);\n                        const glm::dvec3 probeDirection = safeNormalize(\n                            spawnDirection\n                                + candidateTangent * (ringDistanceMeters / planet.radius),\n                            spawnDirection);\n                        const vf::PlanetTerrainSample probe = vf::samplePlanetTerrain(\n                            planet, probeDirection);\n                        highestEvidenceElevation = std::max(\n                            highestEvidenceElevation, probe.elevationMeters);\n                        const double contrast = std::abs(\n                            probe.elevationMeters - centerElevation);\n                        if (contrast > bestContrast) {\n                            bestContrast = contrast;\n                            bestTangent = candidateTangent;\n                        }\n                    }\n                }\n                localEvidenceTangent = bestTangent;\n\n                // Keep the camera radially above the highest terrain in the evidence neighbourhood.\n                // The environment altitude remains the requested minimum clearance above that rim.\n                const double reliefLiftMeters = std::max(\n                    0.0, highestEvidenceElevation - centerElevation);\n                aerialAltitude += reliefLiftMeters;\n                const glm::dvec3 safeLocalOffset = spawnDirection\n                    * (localSurfaceRadius + aerialAltitude);\n                const glm::dvec3 safeWorldOffset = aster.orientation * safeLocalOffset;\n                camera.setExternalWorldState(\n                    aster.position + safeWorldOffset,\n                    aster.linearVelocity + glm::cross(angularVelocity, safeWorldOffset),\n                    false);\n                std::cout << \"R24 terrain evidence view: contrast_m=\" << bestContrast\n                          << \" highest_elevation_m=\" << highestEvidenceElevation\n                          << \" center_elevation_m=\" << centerElevation\n                          << \" relief_lift_m=\" << reliefLiftMeters\n                          << std::endl;\n""",
)

# -----------------------------------------------------------------------------
# 2) Relief-aware screen-space-error distance.
#
# Cesium-style HLOD assumes the tile bounding volume encloses its actual
# contents. We already sample elevationMin/elevationMax for geometric error, so
# include that radial extent in the conservative camera distance instead of
# measuring only to the tile centre and horizontal span. This gives tall relief
# the refinement priority it deserves without globally increasing patch count.
# -----------------------------------------------------------------------------
lod = "native/src/world/PlanetLodMeshBuilder.cpp"
replace_once(
    lod,
    """    const double focalPixels = config.viewportHeightPixels\n        / (2.0 * std::tan(std::max(0.1, config.verticalFovRadians) * 0.5));\n    const double conservativeDistance = std::max(\n        1.0,\n        centerDistance - geometry.spanMeters * 0.55);\n    const double screenError = geometricError / conservativeDistance * focalPixels;\n""",
    """    const double focalPixels = config.viewportHeightPixels\n        / (2.0 * std::tan(std::max(0.1, config.verticalFovRadians) * 0.5));\n    const double radialReliefRadius = std::max(\n        std::abs(elevationMax - centerTerrain.elevationMeters),\n        std::abs(elevationMin - centerTerrain.elevationMeters));\n    const double conservativeDistance = std::max(\n        1.0,\n        centerDistance - geometry.spanMeters * 0.55 - radialReliefRadius);\n    const double screenError = geometricError / conservativeDistance * focalPixels;\n""",
)

print("R24 epic visual closure patch applied: safe camera + relief-aware SSE")
