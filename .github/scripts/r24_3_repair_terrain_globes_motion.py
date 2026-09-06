#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def rw(rel):
    p = ROOT / rel
    return p, p.read_text(encoding='utf-8')

def once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f'missing anchor: {label}')
    return text.replace(old, new, 1)

# -----------------------------------------------------------------------------
# Planet surface presets: Earthlike causal geomorphology and an airless impact
# surface must not share the same generator. This keeps the Moon cratered and
# dry without destroying Earth's existing 3-D terrain authority.
# -----------------------------------------------------------------------------
p, t = rw('native/include/vf/world/PlanetSurface.hpp')
t = once(
    t,
    'namespace vf {\n\nstruct PlanetDefinition {\n',
    'namespace vf {\n\nenum class PlanetSurfacePreset : std::uint8_t {\n'
    '    Earthlike,\n'
    '    AirlessCratered,\n'
    '};\n\nstruct PlanetDefinition {\n',
    'surface preset enum')
t = once(
    t,
    '    double maxOceanDepthMeters{};\n};\n',
    '    double maxOceanDepthMeters{};\n'
    '    PlanetSurfacePreset surfacePreset{PlanetSurfacePreset::Earthlike};\n};\n',
    'surface preset field')
p.write_text(t, encoding='utf-8')

p, t = rw('native/src/world/PlanetSurface.cpp')

crater_fn = r'''
[[nodiscard]] PlanetTerrainSample sampleAirlessCrateredTerrain(
    const PlanetDefinition& definition,
    const glm::dvec3& directionInput) noexcept {
    const glm::dvec3 d = safeNormalize(directionInput);
    const double maxRelief = std::max(100.0, definition.maxElevation);

    // Airless-body morphology: broad ancient basins + impact craters + small regolith roughness.
    // All displacement is radial 3-D geometry. Crater profiles use a depressed bowl, raised ejecta
    // rim and (for larger impacts) a subdued central peak; there is no ocean/plate/river mask.
    const double basinNoise = fbmSurface(
        definition.seed ^ 0xA1F1E55B0D4C7A31ULL, d, 7.0, 3);
    const double regionalNoise = fbmSurface(
        definition.seed ^ 0x5EEDC0FFEE123451ULL, d, 42.0, 3);
    const double regolithNoise = fbmSurface(
        definition.seed ^ 0xC8A7E4D19B20536FULL, d, 520.0, 3);

    double elevation = maxRelief * (
        basinNoise * 0.075
        + regionalNoise * 0.028
        + regolithNoise * 0.0065);
    double craterMask = 0.0;
    double rimMask = 0.0;

    constexpr std::uint64_t craterCount = 44U;
    for (std::uint64_t i = 0; i < craterCount; ++i) {
        const glm::dvec3 center = seededDirection(
            definition.seed ^ 0x9E3779B97F4A7C15ULL, 12000U + i * 17U);
        const double sizeUnit = seedUnit(definition.seed ^ 0xD1B54A32D192ED03ULL, 14000U + i * 23U);
        // Chord-space radius avoids an acos per crater sample. The distribution produces many
        // small/medium craters and only a few basin-scale impacts.
        const double radiusChord = 0.007 + 0.145 * std::pow(sizeUnit, 2.65);
        const double chord = std::sqrt(std::max(
            0.0, 2.0 - 2.0 * std::clamp(glm::dot(d, center), -1.0, 1.0)));
        const double r = chord / radiusChord;
        if (r >= 1.42) continue;

        const double sizeScale = std::pow(radiusChord / 0.152, 0.72);
        const double depth = maxRelief * (0.035 + 0.31 * sizeScale);
        double bowl = 0.0;
        if (r < 1.0) {
            const double q = 1.0 - r * r;
            bowl = -depth * q * q;
            craterMask = std::max(craterMask, q);
        }
        const double rimX = (r - 1.0) / 0.105;
        const double rim = depth * 0.18 * std::exp(-rimX * rimX);
        rimMask = std::max(rimMask, std::clamp(rim / std::max(1.0, depth * 0.18), 0.0, 1.0));

        double centralPeak = 0.0;
        if (radiusChord > 0.055 && r < 0.34) {
            const double peakX = r / 0.16;
            centralPeak = depth * 0.085 * std::exp(-peakX * peakX);
        }
        elevation += bowl + rim + centralPeak;
    }

    elevation = std::clamp(elevation, -maxRelief * 0.88, maxRelief);
    PlanetTerrainSample sample{};
    sample.elevationMeters = elevation;
    sample.continentalness = 1.0;
    sample.mountain = rimMask;
    sample.canyon = craterMask;
    sample.hills = std::clamp(0.5 + 0.5 * regionalNoise, 0.0, 1.0);
    sample.aridity = 1.0;
    sample.moisture = 0.0;
    sample.surfaceDetail = std::clamp(
        0.48 * regionalNoise + 0.30 * regolithNoise + 0.22 * (rimMask - craterMask),
        -1.0,
        1.0);
    sample.oceanDepthMeters = 0.0;
    return sample;
}
'''

t = once(
    t,
    '\n} // namespace\n\nglm::dvec3 cubeSphereDirection',
    '\n' + crater_fn + '\n} // namespace\n\nglm::dvec3 cubeSphereDirection',
    'airless crater generator')

t = once(
    t,
    '''PlanetTerrainSample samplePlanetTerrain(
    const PlanetDefinition& definition,
    const glm::dvec3& directionInput) {
    const glm::dvec3 d = safeNormalize(directionInput);''',
    '''PlanetTerrainSample samplePlanetTerrain(
    const PlanetDefinition& definition,
    const glm::dvec3& directionInput) {
    if (definition.surfacePreset == PlanetSurfacePreset::AirlessCratered)
        return sampleAirlessCrateredTerrain(definition, directionInput);
    const glm::dvec3 d = safeNormalize(directionInput);''',
    'surface preset dispatch')

# Prevent tectonic uplift from saturating at maxElevation and becoming a white flat cap.
t = once(
    t,
    '    elevation += maxLand * 0.72 * mountain;\n',
    '''    const double mountainFold = 0.5 + 0.5 * std::sin(
        w.x * 11.0 - w.z * 8.0 + w.y * 5.0 + p6);
    const double mountainRidge = 1.0 - std::abs(std::sin(
        w.z * 15.0 + w.x * 7.0 - w.y * 4.0 + p4));
    const double mountainReliefFactor = 0.30
        + 0.16 * mountainFold
        + 0.13 * std::pow(std::clamp(mountainRidge, 0.0, 1.0), 1.7);
    elevation += maxLand * mountain * mountainReliefFactor;
''',
    'hierarchical mountain uplift')
t = once(t, '    elevation += maxLand * 0.27 * plateau;\n', '    elevation += maxLand * 0.16 * plateau;\n', 'plateau cap reduction')
t = once(t, '    elevation += maxLand * 0.36 * volcano;\n', '    elevation += maxLand * 0.24 * volcano;\n', 'volcano cap reduction')
t = once(
    t,
    '    const double highIce = smooth01(2500.0, 4700.0, provisionalAboveSea)\n',
    '    const double highIce = smooth01(3600.0, 5800.0, provisionalAboveSea)\n',
    'snowline reduction of white plateaus')

# Give airless surfaces their own neutral lunar palette/material.
t = once(
    t,
    '''glm::vec3 planetTerrainColor(
    const PlanetDefinition& definition,
    const PlanetTerrainSample& sample) noexcept {
    const auto mix3 = [](const glm::vec3& a, const glm::vec3& b, double t) noexcept {''',
    '''glm::vec3 planetTerrainColor(
    const PlanetDefinition& definition,
    const PlanetTerrainSample& sample) noexcept {
    if (definition.surfacePreset == PlanetSurfacePreset::AirlessCratered) {
        const double heightNorm = definition.maxElevation > 0.0
            ? std::clamp(sample.elevationMeters / definition.maxElevation, -1.0, 1.0)
            : 0.0;
        const float value = static_cast<float>(std::clamp(
            0.43 + 0.055 * heightNorm
                + 0.060 * sample.surfaceDetail
                + 0.035 * sample.mountain
                - 0.055 * sample.canyon,
            0.24,
            0.62));
        return {value, value * 0.985F, value * 0.955F};
    }
    const auto mix3 = [](const glm::vec3& a, const glm::vec3& b, double t) noexcept {''',
    'airless terrain color')
t = once(
    t,
    '''glm::vec4 planetTerrainMaterial(
    const PlanetDefinition& definition,
    const PlanetTerrainSample& sample) noexcept {
    if (sample.submerged(definition))''',
    '''glm::vec4 planetTerrainMaterial(
    const PlanetDefinition& definition,
    const PlanetTerrainSample& sample) noexcept {
    if (definition.surfacePreset == PlanetSurfacePreset::AirlessCratered)
        return {0.0F, 0.94F, 0.0F, -1.0F};
    if (sample.submerged(definition))''',
    'airless terrain material')

# Distant Earth does not need a second full transparent ocean sphere. Color submerged terrain as
# the ocean at planet scale: one smooth displaced globe, half the triangles, no depth/intersection seam.
old = '''                vertex.normal = glm::vec3(direction);
                vertex.color = planetTerrainColor(definition, terrain);
                vertex.material = planetTerrainMaterial(definition, terrain);
                mesh.vertices.push_back(vertex);'''
new = '''                vertex.normal = glm::vec3(direction);
                if (definition.surfacePreset == PlanetSurfacePreset::Earthlike
                    && terrain.submerged(definition)) {
                    const double depthScale = resolvedOceanDepth(definition) > 0.0
                        ? std::clamp(terrain.oceanDepthMeters / resolvedOceanDepth(definition), 0.0, 1.0)
                        : 0.0;
                    const glm::vec3 shallow{0.025F, 0.285F, 0.430F};
                    const glm::vec3 deep{0.006F, 0.055F, 0.125F};
                    vertex.color = glm::mix(
                        shallow, deep,
                        static_cast<float>(smooth01(0.05, 0.72, depthScale)));
                    vertex.material = {0.0F, 0.76F, 0.0F, -1.0F};
                } else {
                    vertex.color = planetTerrainColor(definition, terrain);
                    vertex.material = planetTerrainMaterial(definition, terrain);
                }
                mesh.vertices.push_back(vertex);'''
t = once(t, old, new, 'far globe ocean integration')
p.write_text(t, encoding='utf-8')

# -----------------------------------------------------------------------------
# Runtime fixes: use the dedicated Moon generator, remove the far Earth ocean
# overlay, keep evidence cameras tracking body centres, and select non-glacial
# mountain proof so terrain regressions cannot hide behind a white ice cap.
# -----------------------------------------------------------------------------
p, t = rw('native/src/app/Main.cpp')
t = once(
    t,
    '''            if (target == "mountain") {
                score = terrain.mountain * 3.4 + height01 * 1.8 + terrain.plateBoundary * 0.4;''',
    '''            if (target == "mountain") {
                score = terrain.mountain * 3.6 + height01 * 1.1 + terrain.plateBoundary * 0.35
                    - terrain.glacier * 2.2 - std::abs(d.y) * 0.55;''',
    'mountain evidence target')

t = once(
    t,
    '''        moonSurfaceDefinition.maxElevation = 5200.0;
        moonSurfaceDefinition.seaLevelElevationMeters = -900.0;
        moonSurfaceDefinition.maxOceanDepthMeters = 7200.0;
        moonSurfaceDefinition.atmosphereHeight = 0.0;
        vf::PlanetMesh moonSurfaceMeshFar = vf::buildPlanetGlobeSurface(
            moonSurfaceDefinition, 24U, 0.58);
        vf::PlanetMesh moonSurfaceMeshNear = vf::buildPlanetGlobeSurface(
            moonSurfaceDefinition, 80U, 0.58);
        const auto styleMoon = [&](vf::PlanetMesh& mesh) {
            for (auto& vertex : mesh.vertices) {
                const double radius = glm::length(glm::dvec3(vertex.position));
                const double relief = std::clamp(
                    (radius - luna.radiusMeters) / 5200.0, -1.0, 1.0);
                const glm::dvec3 d = safeNormalize(glm::dvec3(vertex.position));
                const double marePattern = 0.5 + 0.5 * std::sin(
                    d.x * 9.0 + d.y * 5.0 - d.z * 7.0);
                const float shade = static_cast<float>(std::clamp(
                    0.43 + 0.055 * relief - 0.035 * marePattern, 0.30, 0.56));
                vertex.color = {shade, shade * 0.985F, shade * 0.955F};
                vertex.material = {0.0F, 0.94F, 0.0F, -1.0F};
            }
        };
        styleMoon(moonSurfaceMeshFar);
        styleMoon(moonSurfaceMeshNear);''',
    '''        moonSurfaceDefinition.maxElevation = 7000.0;
        moonSurfaceDefinition.seaLevelElevationMeters = 0.0;
        moonSurfaceDefinition.maxOceanDepthMeters = 0.0;
        moonSurfaceDefinition.atmosphereHeight = 0.0;
        moonSurfaceDefinition.surfacePreset = vf::PlanetSurfacePreset::AirlessCratered;
        vf::PlanetMesh moonSurfaceMeshFar = vf::buildPlanetGlobeSurface(
            moonSurfaceDefinition, 28U, 1.0);
        vf::PlanetMesh moonSurfaceMeshNear = vf::buildPlanetGlobeSurface(
            moonSurfaceDefinition, 80U, 1.0);''',
    'dedicated cratered moon surface')

t = once(
    t,
    '''        vf::PlanetMesh earthGlobeMesh = vf::buildPlanetGlobeSurface(planet, 96U, 1.0);
        vf::PlanetMesh earthGlobeOcean{};
        vf::appendOceanSurfaceProxy(
            earthGlobeOcean, {}, planet.radius + planet.seaLevelElevationMeters - 1.5, 96U);
        appendMesh(earthGlobeMesh, earthGlobeOcean);
        for (auto& vertex : earthGlobeMesh.vertices) {''',
    '''        vf::PlanetMesh earthGlobeMesh = vf::buildPlanetGlobeSurface(planet, 96U, 1.0);
        for (auto& vertex : earthGlobeMesh.vertices) {''',
    'remove distant transparent ocean overlay')

# Add exact tracking after the normal camera update, so accelerated celestial time shows body motion
# instead of merely letting the entire Earth-Moon system fly out of the test camera.
t = once(
    t,
    '''            const bool wasFlightMode = camera.flightMode();
            camera.update(movement, dt);
            physics.advance(dt);

            glm::dquat inverseAster = glm::conjugate(glm::normalize(currentAster->orientation));''',
    '''            const bool wasFlightMode = camera.flightMode();
            camera.update(movement, dt);
            physics.advance(dt);

            if (celestialViewMode == "earth-globe") {
                const glm::dvec3 observerDirection = safeNormalize({0.44, 0.28, 0.85});
                const glm::dvec3 observerOffset = observerDirection * 24000000.0;
                camera.setExternalWorldState(
                    currentAster->position + observerOffset, currentAster->linearVelocity, false);
                camera.setViewDirectionWorld(-observerOffset, observerDirection);
            } else if (celestialViewMode == "earth-moon-system" && currentMoon != nullptr) {
                const glm::dvec3 observerOffset = moonOrbitNormal * 600000000.0;
                camera.setExternalWorldState(
                    currentAster->position + observerOffset, currentAster->linearVelocity, false);
                camera.setViewDirectionWorld(-observerOffset, moonRadial);
            }

            glm::dquat inverseAster = glm::conjugate(glm::normalize(currentAster->orientation));''',
    'accelerated evidence camera tracking')

# Match the initial wide-system observer to the runtime tracking distance.
t = once(
    t,
    '''            } else if (celestialViewMode == "earth-moon-system") {
                const glm::dvec3 observerOffset = moonOrbitNormal * 760000000.0;
                camera.setExternalWorldState(
                    aster.position + observerOffset, aster.linearVelocity, false);
                camera.setViewDirectionWorld(-observerOffset, moonRadial);
                std::cout << "R24.2 view: earth-moon-system observer_km=760000\\n";''',
    '''            } else if (celestialViewMode == "earth-moon-system") {
                const glm::dvec3 observerOffset = moonOrbitNormal * 600000000.0;
                camera.setExternalWorldState(
                    aster.position + observerOffset, aster.linearVelocity, false);
                camera.setViewDirectionWorld(-observerOffset, moonRadial);
                std::cout << "R24.3 view: earth-moon-system observer_km=600000\\n";''',
    'wide system view distance')

t = once(
    t,
    '        std::cout << "SSE cube-sphere quadtree | smooth distant globes | deterministic stylized ecology\\n";\n',
    '        std::cout << "SSE cube-sphere quadtree | cratered Moon | seamless far-globe ocean | stylized ecology\\n";\n',
    'runtime feature banner r24.3')
p.write_text(t, encoding='utf-8')

# -----------------------------------------------------------------------------
# Tests: Moon must be airless/cratered, Earth far globe stays one smooth mesh,
# and mountain saturation must leave non-clamped relief available.
# -----------------------------------------------------------------------------
p, t = rw('native/tests/R24PhysicalPlanetTests.cpp')
new_tests = r'''
void testAirlessMoonUsesCrateredThreeDimensionalRelief() {
    vf::PlanetDefinition moon{};
    moon.seed = 0x4C554E415F523234ULL;
    moon.radius = 1737400.0;
    moon.maxElevation = 7000.0;
    moon.atmosphereHeight = 0.0;
    moon.surfacePreset = vf::PlanetSurfacePreset::AirlessCratered;

    double minimum = 1.0e30;
    double maximum = -1.0e30;
    double maxCrater = 0.0;
    double maxRim = 0.0;
    for (int i = 0; i < 4096; ++i) {
        const double y = 1.0 - 2.0 * (static_cast<double>(i) + 0.5) / 4096.0;
        const double r = std::sqrt(std::max(0.0, 1.0 - y * y));
        const double a = 2.3999632297286533 * static_cast<double>(i);
        const glm::dvec3 d{std::cos(a) * r, y, std::sin(a) * r};
        const auto sample = vf::samplePlanetTerrain(moon, d);
        minimum = std::min(minimum, sample.elevationMeters);
        maximum = std::max(maximum, sample.elevationMeters);
        maxCrater = std::max(maxCrater, sample.canyon);
        maxRim = std::max(maxRim, sample.mountain);
        require(sample.oceanDepthMeters == 0.0, "airless Moon must never create an ocean field");
        require(sample.moisture == 0.0, "airless Moon must never create terrestrial moisture");
    }
    require(maximum - minimum > 1800.0,
        "Moon surface must contain true kilometre-scale radial 3-D relief");
    require(maxCrater > 0.45 && maxRim > 0.25,
        "Moon sampling must contain both crater bowls and raised impact rims");
}

void testEarthlikeMountainsDoNotCollapseIntoMaxElevationPlateau() {
    vf::PlanetDefinition earth{};
    earth.seed = 0x71A9F20DULL;
    earth.radius = 6371000.0;
    earth.maxElevation = 8850.0;
    earth.maxOceanDepthMeters = 11000.0;

    int mountainSamples = 0;
    int clampedSamples = 0;
    double minimumMountainElevation = 1.0e30;
    double maximumMountainElevation = -1.0e30;
    for (int i = 0; i < 8192; ++i) {
        const double y = 1.0 - 2.0 * (static_cast<double>(i) + 0.5) / 8192.0;
        const double r = std::sqrt(std::max(0.0, 1.0 - y * y));
        const double a = 2.3999632297286533 * static_cast<double>(i);
        const glm::dvec3 d{std::cos(a) * r, y, std::sin(a) * r};
        const auto sample = vf::samplePlanetTerrain(earth, d);
        if (sample.mountain < 0.48 || sample.submerged(earth)) continue;
        ++mountainSamples;
        minimumMountainElevation = std::min(minimumMountainElevation, sample.elevationMeters);
        maximumMountainElevation = std::max(maximumMountainElevation, sample.elevationMeters);
        if (sample.elevationMeters > earth.maxElevation - 1.0) ++clampedSamples;
    }
    require(mountainSamples > 10, "terrain seed must expose enough mountain samples for regression testing");
    require(maximumMountainElevation - minimumMountainElevation > 900.0,
        "mountain belts must retain vertical hierarchy instead of becoming one flat cap");
    require(clampedSamples * 5 < mountainSamples,
        "fewer than 20 percent of sampled mountain cells may saturate at maxElevation");
}
'''
t = once(t, '\n} // namespace\n\nint main() {', '\n' + new_tests + '\n} // namespace\n\nint main() {', 'r24.3 terrain tests')
t = once(
    t,
    '    testEarthMoonPhysicalScaleRotationAndRevolution();\n',
    '    testEarthMoonPhysicalScaleRotationAndRevolution();\n'
    '    testAirlessMoonUsesCrateredThreeDimensionalRelief();\n'
    '    testEarthlikeMountainsDoNotCollapseIntoMaxElevationPlateau();\n',
    'r24.3 test invocation')
p.write_text(t, encoding='utf-8')

print('R24.3 terrain/globe/motion repair staged')
