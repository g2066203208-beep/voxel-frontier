from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:140]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# Extreme gameplay terrain legitimately creates near-vertical slopes. Use symmetric finite
# differences in the authoritative surface normal so a one-sided sample cannot flip or bias the
# normal on a sharp ridge. The final orientation is explicitly kept on the outward hemisphere.
authority = "native/src/world/PlanetSurfaceAuthority.cpp"
replace_once(
    authority,
    """    const glm::dvec3 dEast = safeNormalize(d + east * angularStep, d);\n    const glm::dvec3 dNorth = safeNormalize(d + north * angularStep, d);\n    const PlanetTerrainSample terrainEast = sample(dEast);\n    const PlanetTerrainSample terrainNorth = sample(dNorth);\n    const glm::dvec3 pEast = dEast * (planet_.radius + terrainEast.elevationMeters);\n    const glm::dvec3 pNorth = dNorth * (planet_.radius + terrainNorth.elevationMeters);\n    result.normal = safeNormalize(\n        glm::cross(pEast - result.position, pNorth - result.position), d);\n    if (glm::dot(result.normal, d) < 0.0) result.normal = -result.normal;\n""",
    """    const glm::dvec3 dEastPlus = safeNormalize(d + east * angularStep, d);\n    const glm::dvec3 dEastMinus = safeNormalize(d - east * angularStep, d);\n    const glm::dvec3 dNorthPlus = safeNormalize(d + north * angularStep, d);\n    const glm::dvec3 dNorthMinus = safeNormalize(d - north * angularStep, d);\n    const PlanetTerrainSample terrainEastPlus = sample(dEastPlus);\n    const PlanetTerrainSample terrainEastMinus = sample(dEastMinus);\n    const PlanetTerrainSample terrainNorthPlus = sample(dNorthPlus);\n    const PlanetTerrainSample terrainNorthMinus = sample(dNorthMinus);\n    const glm::dvec3 pEastPlus = dEastPlus\n        * (planet_.radius + terrainEastPlus.elevationMeters);\n    const glm::dvec3 pEastMinus = dEastMinus\n        * (planet_.radius + terrainEastMinus.elevationMeters);\n    const glm::dvec3 pNorthPlus = dNorthPlus\n        * (planet_.radius + terrainNorthPlus.elevationMeters);\n    const glm::dvec3 pNorthMinus = dNorthMinus\n        * (planet_.radius + terrainNorthMinus.elevationMeters);\n    result.normal = safeNormalize(\n        glm::cross(pEastPlus - pEastMinus, pNorthPlus - pNorthMinus), d);\n    if (glm::dot(result.normal, d) < 0.0) result.normal = -result.normal;\n""",
)

# Keep the standalone normal helper consistent with PlanetSurfaceAuthority.
surface = "native/src/world/PlanetSurface.cpp"
replace_once(
    surface,
    """    const glm::dvec3 dEast = safeNormalize(d + east * angularStep, d);\n    const glm::dvec3 dNorth = safeNormalize(d + north * angularStep, d);\n    const glm::dvec3 p0 = d * planetSurfaceRadius(definition, d);\n    const glm::dvec3 pEast = dEast * planetSurfaceRadius(definition, dEast);\n    const glm::dvec3 pNorth = dNorth * planetSurfaceRadius(definition, dNorth);\n    glm::dvec3 normal = safeNormalize(glm::cross(pEast - p0, pNorth - p0), d);\n    if (glm::dot(normal, d) < 0.0) normal = -normal;\n""",
    """    const glm::dvec3 dEastPlus = safeNormalize(d + east * angularStep, d);\n    const glm::dvec3 dEastMinus = safeNormalize(d - east * angularStep, d);\n    const glm::dvec3 dNorthPlus = safeNormalize(d + north * angularStep, d);\n    const glm::dvec3 dNorthMinus = safeNormalize(d - north * angularStep, d);\n    const glm::dvec3 pEastPlus = dEastPlus * planetSurfaceRadius(definition, dEastPlus);\n    const glm::dvec3 pEastMinus = dEastMinus * planetSurfaceRadius(definition, dEastMinus);\n    const glm::dvec3 pNorthPlus = dNorthPlus * planetSurfaceRadius(definition, dNorthPlus);\n    const glm::dvec3 pNorthMinus = dNorthMinus * planetSurfaceRadius(definition, dNorthMinus);\n    glm::dvec3 normal = safeNormalize(\n        glm::cross(pEastPlus - pEastMinus, pNorthPlus - pNorthMinus), d);\n    if (glm::dot(normal, d) < 0.0) normal = -normal;\n""",
)

# The epic generator can legitimately compute raw summits above the configured gameplay ceiling.
# A hard clamp would turn those summits into broad, perfectly flat mesas. Compress positive relief
# smoothly as it approaches maxLand instead: the surface asymptotically approaches 98.5% of the
# ceiling while preserving peak/ridge/valley ordering and leaving negative canyon/abyss relief alone.
replace_once(
    surface,
    """    const double minElevation = definition.seaLevelElevationMeters - maxOcean;\n    const double maxElevation = definition.seaLevelElevationMeters + maxLand;\n    elevation = std::clamp(\n        elevation + definition.seaLevelElevationMeters,\n        minElevation,\n        maxElevation);\n""",
    """    if (maxLand > 0.0 && elevation > 0.0) {\n        constexpr double softCeilingFraction = 0.985;\n        constexpr double compressionScale = 0.78;\n        elevation = maxLand * softCeilingFraction * std::tanh(\n            elevation / (maxLand * compressionScale));\n    }\n    const double minElevation = definition.seaLevelElevationMeters - maxOcean;\n    const double maxElevation = definition.seaLevelElevationMeters + maxLand;\n    elevation = std::clamp(\n        elevation + definition.seaLevelElevationMeters,\n        minElevation,\n        maxElevation);\n""",
)

# The historical 0.35 radial-dot threshold encoded a maximum slope of about 69.5 degrees.
# Gameplay-first cliffs and abyss walls are intentionally steeper than that. The invariant we
# actually need is: finite unit normal, never inward-facing. Keep the test strict on that property.
test = "native/tests/R24PhysicalPlanetTests.cpp"
replace_once(
    test,
    """    require(glm::dot(snapshot.normal, direction) > 0.35,\n        \"surface snapshot normal must remain outward-facing even on steep procedural relief\");\n""",
    """    require(glm::dot(snapshot.normal, direction) > 1.0e-6,\n        \"surface snapshot normal must remain outward-facing even on near-vertical epic relief\");\n""",
)

print("R24 epic landscape normal/peak hierarchy hotfix applied")
