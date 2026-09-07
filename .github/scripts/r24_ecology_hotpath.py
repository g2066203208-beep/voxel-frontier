from pathlib import Path

PATH = Path('native/src/world/ProceduralEcology.cpp')
text = PATH.read_text(encoding='utf-8')


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {count}')
    text = text.replace(old, new, 1)


replace_once(
'''    candidate.terrain = surfaceAuthority != nullptr
        ? surfaceAuthority->sample(direction)
        : samplePlanetTerrain(planet, direction);
    const glm::dvec3 normalPlanet = surfaceAuthority != nullptr
        ? surfaceAuthority->surfaceNormal(direction)
        : planetSurfaceNormal(planet, direction);
    const double surfaceRadius = surfaceAuthority != nullptr
        ? surfaceAuthority->surfaceRadius(direction)
        : planet.radius + candidate.terrain.elevationMeters;
    candidate.radialAlignment = glm::dot(normalPlanet, direction);
    candidate.renderPoint = toRenderPoint(frame, direction * surfaceRadius);
''',
'''    glm::dvec3 normalPlanet{};
    double surfaceRadius{};
    if (surfaceAuthority != nullptr) {
        // PlanetSurfaceAuthority already exposes a coherent combined query specifically so callers
        // that need classification + position + normal do not independently resample the same
        // expensive procedural/hydrology center point. Ecology used to do exactly that via
        // sample() + surfaceNormal() + surfaceRadius(). Keep one authoritative combined query.
        const PlanetSurfaceSample surface = surfaceAuthority->sampleSurface(direction);
        candidate.terrain = surface.terrain;
        normalPlanet = surface.normal;
        surfaceRadius = surface.radiusMeters;
        candidate.renderPoint = toRenderPoint(frame, surface.position);
    } else {
        candidate.terrain = samplePlanetTerrain(planet, direction);
        normalPlanet = planetSurfaceNormal(planet, direction);
        surfaceRadius = planet.radius + candidate.terrain.elevationMeters;
        candidate.renderPoint = toRenderPoint(frame, direction * surfaceRadius);
    }
    candidate.radialAlignment = glm::dot(normalPlanet, direction);
''',
'coherent surface query')

replace_once(
'''        [&](std::int64_t ix, std::int64_t iz, double x, double z) {
            if (treeCount >= settings.maxTrees) return;
            const SurfaceCandidate c = sampleCandidate(planet, frame, surfaceAuthority, x, z);
''',
'''        [&](std::int64_t ix, std::int64_t iz, double x, double z) {
            if (treeCount >= settings.maxTrees) return;
            const double forestRoll = random01(planet.seed, ix, iz, 1010U);
            // forestSuitability is clamped to <= 0.68 below. A roll above that can never survive,
            // so reject it before any terrain/hydrology query without changing a single accepted tree.
            if (forestRoll > 0.68) return;
            const SurfaceCandidate c = sampleCandidate(planet, frame, surfaceAuthority, x, z);
''',
'forest early reject')

replace_once(
'''            if (random01(planet.seed, ix, iz, 1010U) > forestSuitability) return;
''',
'''            if (forestRoll > forestSuitability) return;
''',
'forest roll reuse')

replace_once(
'''        [&](std::int64_t ix, std::int64_t iz, double x, double z) {
            if (rockCount >= settings.maxRocks) return;
            const SurfaceCandidate c = sampleCandidate(planet, frame, surfaceAuthority, x, z);
''',
'''        [&](std::int64_t ix, std::int64_t iz, double x, double z) {
            if (rockCount >= settings.maxRocks) return;
            const double rockRoll = random01(planet.seed, ix, iz, 2010U);
            // rockSuitability is clamped to <= 0.62. Preserve exact deterministic placement while
            // skipping impossible candidates before the expensive surface-normal query.
            if (rockRoll > 0.62) return;
            const SurfaceCandidate c = sampleCandidate(planet, frame, surfaceAuthority, x, z);
''',
'rock early reject')

replace_once(
'''            if (random01(planet.seed, ix, iz, 2010U) > rockSuitability) return;
''',
'''            if (rockRoll > rockSuitability) return;
''',
'rock roll reuse')

replace_once(
'''        [&](std::int64_t ix, std::int64_t iz, double x, double z) {
            if (grassCount >= settings.maxGrassClumps) return;
            const SurfaceCandidate c = sampleCandidate(planet, frame, surfaceAuthority, x, z);
''',
'''        [&](std::int64_t ix, std::int64_t iz, double x, double z) {
            if (grassCount >= settings.maxGrassClumps) return;
            const double grassRoll = random01(planet.seed, ix, iz, 3010U);
            // grassSuitability is clamped to <= 0.70. Early rejection is therefore bit-for-bit
            // equivalent for placement decisions but avoids needless terrain/hydrology work.
            if (grassRoll > 0.70) return;
            const SurfaceCandidate c = sampleCandidate(planet, frame, surfaceAuthority, x, z);
''',
'grass early reject')

replace_once(
'''            if (random01(planet.seed, ix, iz, 3010U) > grassSuitability) return;
''',
'''            if (grassRoll > grassSuitability) return;
''',
'grass roll reuse')

PATH.write_text(text, encoding='utf-8')
print('R24 ecology hotpath materialized: impossible cells culled before surface queries; coherent sampleSurface used once')
