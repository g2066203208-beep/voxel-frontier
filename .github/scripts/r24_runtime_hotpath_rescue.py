from pathlib import Path

CLIMATE_H = Path('native/include/vf/world/PlanetClimateGrid.hpp')
CLIMATE_CPP = Path('native/src/world/PlanetClimateGrid.cpp')
BODY_H = Path('native/include/vf/world/PlanetaryBodySystem.hpp')
BODY_CPP = Path('native/src/world/PlanetaryBodySystem.cpp')

files = {
    'climate_h': [CLIMATE_H, CLIMATE_H.read_text(encoding='utf-8')],
    'climate_cpp': [CLIMATE_CPP, CLIMATE_CPP.read_text(encoding='utf-8')],
    'body_h': [BODY_H, BODY_H.read_text(encoding='utf-8')],
    'body_cpp': [BODY_CPP, BODY_CPP.read_text(encoding='utf-8')],
}


def replace_once(key, old, new, label):
    path, text = files[key]
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {count}')
    files[key][1] = text.replace(old, new, 1)


replace_once(
    'climate_h',
'''    double spinRateRadPerSecond_{};
    std::vector<PlanetClimateCell> cells_;
''',
'''    double spinRateRadPerSecond_{};
    std::vector<PlanetClimateCell> cells_;
    // Terrain classification is immutable for a PlanetDefinition. Cache it once so the dynamic
    // atmosphere solver never resynthesizes procedural geology for all 1,152 climate cells.
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
    'cache immutable climate terrain')

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
    'remove climate terrain synthesis hotpath')

replace_once(
    'body_h',
'''    std::unique_ptr<PlanetClimateGrid> climate{};
    std::unique_ptr<OceanSpectrum> ocean{};
''',
'''    std::unique_ptr<PlanetClimateGrid> climate{};
    std::unique_ptr<OceanSpectrum> ocean{};
    // Slow world services keep their own simulated-time accumulator instead of running at the
    // sub-second orbital integration cadence selected by accelerated gameplay time.
    double climateAccumulatorSeconds{};
''',
    'climate accumulator')

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
    // The fastest default climate process is precipitation at 21,600 s, while 240x gameplay time
    // drives celestial integration at 0.25 s. Solving a 24x48 global atmosphere on every orbital
    // substep oversamples the slow field by ~86,000x. Advance it at a still-conservative 300 s
    // simulated cadence and preserve every accumulated second exactly.
    constexpr double kClimateServiceStepSeconds = 300.0;
    for (auto& runtimeValue : runtimes_) {
        if (!runtimeValue->climate) continue;
        runtimeValue->climateAccumulatorSeconds += deltaSeconds;
        if (runtimeValue->climateAccumulatorSeconds + 1.0e-12 < kClimateServiceStepSeconds)
            continue;

        const CelestialBody* bodyValue = celestial_.body(runtimeValue->bodyId);
        if (bodyValue == nullptr) continue;
        while (runtimeValue->climateAccumulatorSeconds + 1.0e-12 >= kClimateServiceStepSeconds) {
            double totalIrradiance = 0.0;
            const glm::dvec3 strongestDirection = strongestStarDirectionBodyLocal(
                celestial_, *bodyValue, totalIrradiance);
            runtimeValue->climate->step(
                kClimateServiceStepSeconds, strongestDirection, totalIrradiance);
            runtimeValue->climateAccumulatorSeconds -= kClimateServiceStepSeconds;
            if (runtimeValue->climateAccumulatorSeconds < 0.0
                && runtimeValue->climateAccumulatorSeconds > -1.0e-9)
                runtimeValue->climateAccumulatorSeconds = 0.0;
        }
    }
}
''',
    'multi-rate climate service')

for path, text in files.values():
    path.write_text(text, encoding='utf-8')

print('R24 runtime hotpath rescue materialized: cached climate terrain + 300 s multi-rate climate service')
