from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:80]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# -----------------------------------------------------------------------------
# Gameplay Moon: preserve physical orbit/radius/gravity, enlarge only the render
# presentation while the observer is near Aster. The scale fades to 1x in orbit
# and is forced back to 1x when approaching Luna itself.
# -----------------------------------------------------------------------------
main = "native/src/app/Main.cpp"
replace_once(
    main,
    """[[nodiscard]] double smooth01(double value) noexcept {\n    const double t = std::clamp(value, 0.0, 1.0);\n    return t * t * (3.0 - 2.0 * t);\n}\n""",
    """[[nodiscard]] double smooth01(double value) noexcept {\n    const double t = std::clamp(value, 0.0, 1.0);\n    return t * t * (3.0 - 2.0 * t);\n}\n\n// Gameplay presentation only. Luna keeps its physical radius, mass, gravity and 384,400 km\n// orbit. Near Aster's surface the visible disc is enlarged for composition/readability; the\n// presentation smoothly returns to the physical 1x radius in high orbit and always returns to\n// 1x while actually approaching Luna, so landing/navigation geometry remains truthful.\n[[nodiscard]] double gameplayMoonVisualScale(\n    double asterAltitudeMeters,\n    double moonDistanceMeters) noexcept {\n    const double surfaceWeight = 1.0 - smooth01(\n        (std::max(0.0, asterAltitudeMeters) - 250000.0) / 2750000.0);\n    const double farFromMoonWeight = smooth01(\n        (std::max(0.0, moonDistanceMeters) - 12000000.0) / 18000000.0);\n    return 1.0 + 3.0 * surfaceWeight * farFromMoonWeight;\n}\n""",
)

replace_once(
    main,
    """            if (currentMoon != nullptr) {\n                const double moonCameraDistance = glm::length(currentMoon->position - camera.position());\n                const vf::PlanetMesh& moonSource = moonCameraDistance < 12000000.0\n                    ? moonSurfaceMeshNear : moonSurfaceMeshFar;\n                vf::PlanetMesh moonMesh = moonSource;\n                const glm::dvec3 moonRelativeWorld = currentMoon->position - currentAster->position;\n                for (auto& vertex : moonMesh.vertices) {\n                    const glm::dvec3 moonBodyPoint = currentMoon->orientation * glm::dvec3(vertex.position);\n                    const glm::dvec3 pointAsterLocal = inverseAster * (moonRelativeWorld + moonBodyPoint);\n                    const glm::dvec3 normalAsterLocal = inverseAster\n                        * (currentMoon->orientation * glm::dvec3(vertex.normal));\n                    vertex.position = glm::vec3(toSurfacePoint(pointAsterLocal));\n                    vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(normalAsterLocal)));\n                }\n                appendMesh(dynamicMesh, moonMesh);\n            }\n""",
    """            if (currentMoon != nullptr) {\n                const double moonCameraDistance = glm::length(currentMoon->position - camera.position());\n                const double asterObserverAltitude = std::max(\n                    0.0, glm::length(camera.position() - currentAster->position)\n                        - currentAster->radiusMeters);\n                const double moonVisualScale = gameplayMoonVisualScale(\n                    asterObserverAltitude, moonCameraDistance);\n                const vf::PlanetMesh& moonSource = moonCameraDistance < 12000000.0\n                    ? moonSurfaceMeshNear : moonSurfaceMeshFar;\n                vf::PlanetMesh moonMesh = moonSource;\n                const glm::dvec3 moonRelativeWorld = currentMoon->position - currentAster->position;\n                for (auto& vertex : moonMesh.vertices) {\n                    const glm::dvec3 moonBodyPoint = currentMoon->orientation\n                        * (glm::dvec3(vertex.position) * moonVisualScale);\n                    const glm::dvec3 pointAsterLocal = inverseAster * (moonRelativeWorld + moonBodyPoint);\n                    const glm::dvec3 normalAsterLocal = inverseAster\n                        * (currentMoon->orientation * glm::dvec3(vertex.normal));\n                    vertex.position = glm::vec3(toSurfacePoint(pointAsterLocal));\n                    vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(normalAsterLocal)));\n                }\n                appendMesh(dynamicMesh, moonMesh);\n            }\n""",
)

replace_once(
    main,
    """                    const double apparentDiameterPixels = 2.0 * std::tan(angularRadiusRadians) * focalPixels;\n                    std::cout << \"R24 moon evidence: distance_km=\"\n                              << moonDistanceMeters / 1000.0\n                              << \" angular_error_deg=\" << angularErrorDegrees\n                              << \" apparent_diameter_px=\" << apparentDiameterPixels\n                              << \" dynamic_tris=\" << renderer.dynamicTriangleCount() << '\\n';\n""",
    """                    const double apparentDiameterPixels = 2.0 * std::tan(angularRadiusRadians) * focalPixels;\n                    const double asterObserverAltitude = std::max(\n                        0.0, glm::length(camera.position() - currentAster->position)\n                            - currentAster->radiusMeters);\n                    const double moonVisualScale = gameplayMoonVisualScale(\n                        asterObserverAltitude, moonDistanceMeters);\n                    std::cout << \"R24 moon evidence: distance_km=\"\n                              << moonDistanceMeters / 1000.0\n                              << \" angular_error_deg=\" << angularErrorDegrees\n                              << \" apparent_diameter_px=\" << apparentDiameterPixels\n                              << \" visual_scale=\" << moonVisualScale\n                              << \" visual_apparent_diameter_px=\"\n                              << apparentDiameterPixels * moonVisualScale\n                              << \" dynamic_tris=\" << renderer.dynamicTriangleCount() << '\\n';\n""",
)

# Targeted real-terrain evidence points.
replace_once(
    main,
    """            if (target == \"mountain\") {\n                score = terrain.mountain * 3.6 + height01 * 1.1 + terrain.plateBoundary * 0.35\n                    - terrain.glacier * 2.2 - std::abs(d.y) * 0.55;\n            } else if (target == \"highland\") {\n""",
    """            if (target == \"mountain\") {\n                score = terrain.mountain * 3.6 + height01 * 1.1 + terrain.plateBoundary * 0.35\n                    - terrain.glacier * 2.2 - std::abs(d.y) * 0.55;\n            } else if (target == \"rift\") {\n                score = terrain.rift * 4.8 + terrain.divergence * 1.35\n                    + terrain.plateBoundary * 0.55 + height01 * 0.25\n                    - terrain.glacier * 1.4 - terrain.mountain * 0.45;\n            } else if (target == \"alluvial\") {\n                score = terrain.alluvialFan * 4.4 + terrain.river * 1.2\n                    + terrain.moisture * 0.45 - height01 * 0.50;\n            } else if (target == \"highland\") {\n""",
)

# Remove duplicated diagnostics spam left by older migration scripts.
main_text = Path(main).read_text(encoding="utf-8")
triple_diag = """                if (runtimeDiagnosticsStdout)\n                    std::cout << \"R24 DIAG | \" << title.str() << '\\n';\n                if (runtimeDiagnosticsStdout)\n                    std::cout << \"R24 DIAG | \" << title.str() << '\\n';\n                if (runtimeDiagnosticsStdout)\n                    std::cout << \"R24 DIAG | \" << title.str() << '\\n';\n"""
single_diag = """                if (runtimeDiagnosticsStdout)\n                    std::cout << \"R24 DIAG | \" << title.str() << '\\n';\n"""
if triple_diag in main_text:
    Path(main).write_text(main_text.replace(triple_diag, single_diag, 1), encoding="utf-8")


# -----------------------------------------------------------------------------
# Causal landforms: expose divergent continental rifts, transform shear scarps,
# and lowland alluvial deposition. These remain driven by plate relative motion
# and drainage/climate fields; noise only modulates detail inside the process mask.
# -----------------------------------------------------------------------------
header = "native/include/vf/world/PlanetSurface.hpp"
replace_once(
    header,
    """    double convergence{};\n    double divergence{};\n    double oceanRidge{};\n""",
    """    double convergence{};\n    double divergence{};\n    double shear{};\n    double rift{};\n    double oceanRidge{};\n""",
)
replace_once(
    header,
    """    double volcano{};\n    double river{};\n\n    // Subordinate geomorphology/climate fields.\n""",
    """    double volcano{};\n    double river{};\n    double alluvialFan{};\n\n    // Subordinate geomorphology/climate fields.\n""",
)

surface = "native/src/world/PlanetSurface.cpp"
replace_once(
    surface,
    """struct PlateField {\n    PlateSeed primary{};\n    PlateSeed secondary{};\n    double boundary{};\n    double convergence{};\n    double divergence{};\n};\n""",
    """struct PlateField {\n    PlateSeed primary{};\n    PlateSeed secondary{};\n    double boundary{};\n    double convergence{};\n    double divergence{};\n    double shear{};\n};\n""",
)
replace_once(
    surface,
    """    const double separationRate = glm::dot(relativeVelocity, boundaryNormal);\n    const double divergence = boundary * smooth01(0.04, 0.72, separationRate);\n    const double convergence = boundary * smooth01(0.04, 0.72, -separationRate);\n    return {best, second, boundary, convergence, divergence};\n""",
    """    const double separationRate = glm::dot(relativeVelocity, boundaryNormal);\n    const double divergence = boundary * smooth01(0.04, 0.72, separationRate);\n    const double convergence = boundary * smooth01(0.04, 0.72, -separationRate);\n    const glm::dvec3 boundaryTangent = safeNormalize(\n        glm::cross(direction, boundaryNormal), tangentAxis(direction));\n    const double slipRate = std::abs(glm::dot(relativeVelocity, boundaryTangent));\n    const double shear = boundary * smooth01(0.04, 0.72, slipRate);\n    return {best, second, boundary, convergence, divergence, shear};\n""",
)
replace_once(
    surface,
    """    const double oceanRidge = plates.divergence * oceanness;\n    elevation += maxOcean * 0.38 * oceanRidge;\n\n    const double collisionWeight = plates.primary.continental && plates.secondary.continental\n""",
    """    const double oceanRidge = plates.divergence * oceanness;\n    elevation += maxOcean * 0.38 * oceanRidge;\n\n    // Continental extension produces a narrow graben and uplifted shoulders instead of a generic\n    // noisy depression. The mask comes from the signed relative velocity of adjacent plates.\n    const double riftAxis = 1.0 - std::abs(std::sin(\n        w.x * 10.5 + w.z * 8.0 - w.y * 6.0 + p7));\n    const double rift = std::pow(\n        std::clamp(plates.divergence * landness, 0.0, 1.0), 1.08)\n        * (0.28 + 0.72 * std::pow(std::clamp(riftAxis, 0.0, 1.0), 1.6));\n    const double riftShoulder = plates.divergence * landness\n        * (1.0 - std::clamp(riftAxis, 0.0, 1.0))\n        * (0.55 + 0.45 * (0.5 + 0.5 * std::sin(w.y * 13.0 - w.x * 7.0 + p3)));\n    elevation -= maxLand * 0.16 * rift;\n    elevation += maxLand * 0.050 * riftShoulder;\n\n    // Transform boundaries are expressed as opposing scarps along the boundary tangent. They do\n    // not create or destroy crustal area, so the displacement is signed around zero.\n    const double transformWave = std::sin(w.x * 17.0 + w.z * 13.0 - w.y * 9.0 + p2);\n    elevation += maxLand * 0.020 * plates.shear * landness * transformWave;\n\n    const double collisionWeight = plates.primary.continental && plates.secondary.continental\n""",
)
replace_once(
    surface,
    """    const double wetland = std::clamp(\n        landness * lowland * (1.0 - aridity)\n            * (0.46 * moisture + 0.72 * river + 0.25 * coastProximity),\n        0.0,\n        1.0);\n\n    const double polar = smooth01(0.70, 0.91, latitude);\n""",
    """    const double wetland = std::clamp(\n        landness * lowland * (1.0 - aridity)\n            * (0.46 * moisture + 0.72 * river + 0.25 * coastProximity),\n        0.0,\n        1.0);\n\n    // Material eroded from steep source provinces is deposited after the terrain reaches lowland.\n    // This is a bounded game-scale transport proxy: source strength is mountain/rift relief, the\n    // river field transports it, and only low moist ground can retain an alluvial fan/plain.\n    const double alluvialFan = std::clamp(\n        landness * lowland * (1.0 - 0.45 * aridity)\n            * (0.58 * river + 0.26 * mountain * moisture + 0.16 * rift * moisture),\n        0.0,\n        1.0);\n\n    const double polar = smooth01(0.70, 0.91, latitude);\n""",
)
replace_once(
    surface,
    """    if (wetland > 0.0 && elevation > 45.0) {\n        elevation -= (elevation - 45.0) * std::clamp(wetland * 0.52, 0.0, 0.52);\n    }\n    elevation += maxLand * 0.0035 * glacier * (0.55 + 0.45 * regional);\n""",
    """    if (wetland > 0.0 && elevation > 45.0) {\n        elevation -= (elevation - 45.0) * std::clamp(wetland * 0.52, 0.0, 0.52);\n    }\n    elevation += maxLand * 0.0045 * alluvialFan * (0.35 + 0.65 * (0.5 + 0.5 * regional));\n    elevation += maxLand * 0.0035 * glacier * (0.55 + 0.45 * regional);\n""",
)
replace_once(
    surface,
    """    sample.convergence = plates.convergence;\n    sample.divergence = plates.divergence;\n    sample.oceanRidge = oceanRidge;\n""",
    """    sample.convergence = plates.convergence;\n    sample.divergence = plates.divergence;\n    sample.shear = plates.shear;\n    sample.rift = rift;\n    sample.oceanRidge = oceanRidge;\n""",
)
replace_once(
    surface,
    """    sample.volcano = volcano;\n    sample.river = river;\n    sample.hills = hills;\n""",
    """    sample.volcano = volcano;\n    sample.river = river;\n    sample.alluvialFan = alluvialFan;\n    sample.hills = hills;\n""",
)
replace_once(
    surface,
    """    color = mix3(color, {0.56F, 0.28F, 0.13F}, sample.canyon * 0.84);\n    color = mix3(color, {0.34F, 0.32F, 0.29F}, sample.coastalCliff * 0.76);\n""",
    """    color = mix3(color, {0.56F, 0.28F, 0.13F}, sample.canyon * 0.84);\n    color = mix3(color, {0.47F, 0.255F, 0.145F}, sample.rift * 0.82);\n    color = mix3(color, {0.31F, 0.37F, 0.18F}, sample.alluvialFan * 0.72);\n    color = mix3(color, {0.34F, 0.32F, 0.29F}, sample.coastalCliff * 0.76);\n""",
)
replace_once(
    surface,
    """        0.72 * sample.mountain + 0.34 * sample.volcano + 0.24 * highland\n            + 0.58 * sample.coastalCliff + 0.38 * sample.canyon,\n""",
    """        0.72 * sample.mountain + 0.34 * sample.volcano + 0.24 * highland\n            + 0.58 * sample.coastalCliff + 0.38 * sample.canyon\n            + 0.34 * sample.rift + 0.22 * sample.shear,\n""",
)

# -----------------------------------------------------------------------------
# Regression: process fields must exist and remain normalized on the Earth seed.
# -----------------------------------------------------------------------------
test = "native/tests/TerrainLandformTests.cpp"
replace_once(
    test,
    """    double maxHills = 0.0;\n    double maxCanyon = 0.0;\n""",
    """    double maxHills = 0.0;\n    double maxCanyon = 0.0;\n    double maxRift = 0.0;\n    double maxShear = 0.0;\n    double maxAlluvial = 0.0;\n""",
)
replace_once(
    test,
    """                    sample.hills, sample.canyon, sample.dunes, sample.coastalCliff,\n                    sample.wetland, sample.glacier, sample.aridity, sample.moisture,\n""",
    """                    sample.hills, sample.canyon, sample.rift, sample.shear, sample.alluvialFan,\n                    sample.dunes, sample.coastalCliff, sample.wetland, sample.glacier,\n                    sample.aridity, sample.moisture,\n""",
)
replace_once(
    test,
    """                maxHills = std::max(maxHills, sample.hills);\n                maxCanyon = std::max(maxCanyon, sample.canyon);\n""",
    """                maxHills = std::max(maxHills, sample.hills);\n                maxCanyon = std::max(maxCanyon, sample.canyon);\n                maxRift = std::max(maxRift, sample.rift);\n                maxShear = std::max(maxShear, sample.shear);\n                maxAlluvial = std::max(maxAlluvial, sample.alluvialFan);\n""",
)
replace_once(
    test,
    """    require(maxCanyon > 0.015, \"Earth seed must contain incised canyon terrain\");\n    require(maxDunes > 0.015, \"Earth seed must contain dune terrain\");\n""",
    """    require(maxCanyon > 0.015, \"Earth seed must contain incised canyon terrain\");\n    require(maxRift > 0.015, \"Earth seed must contain divergent continental rifts\");\n    require(maxShear > 0.015, \"Earth seed must contain transform-boundary shear terrain\");\n    require(maxAlluvial > 0.005, \"Earth seed must contain lowland alluvial deposition\");\n    require(maxDunes > 0.015, \"Earth seed must contain dune terrain\");\n""",
)
replace_once(
    test,
    """              << \" canyon=\" << maxCanyon\n              << \" dunes=\" << maxDunes\n""",
    """              << \" canyon=\" << maxCanyon\n              << \" rift=\" << maxRift\n              << \" shear=\" << maxShear\n              << \" alluvial=\" << maxAlluvial\n              << \" dunes=\" << maxDunes\n""",
)

print("R24 gameplay Moon + causal terrain closure applied")
