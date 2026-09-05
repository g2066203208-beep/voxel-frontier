#include "vf/physics/OceanSpectrum.hpp"
#include "vf/world/PlanetClimateGrid.hpp"
#include "vf/world/PlanetSurfaceAuthority.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <string_view>

#include <glm/geometric.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "R24 PHYSICAL PLANET TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void testSurfaceAuthorityKeepsHydrologyInCollisionHeight() {
    vf::PlanetDefinition planet{};
    planet.radius = 6371000.0;
    planet.maxElevation = 8850.0;
    planet.maxOceanDepthMeters = 11000.0;
    planet.seed = 0x71A9F20DULL;
    const glm::dvec3 center = glm::normalize(glm::dvec3{0.72, 0.52, 0.46});

    vf::RegionalHydrologyConfig config{};
    config.resolution = 65U;
    config.halfExtentMeters = 45000.0;
    config.maxIncisionMeters = 220.0;
    auto hydro = std::make_shared<vf::RegionalHydrology>(planet, center, config);

    vf::PlanetSurfaceAuthority authority{planet};
    authority.setHydrology(hydro);
    const double base = vf::samplePlanetTerrain(planet, center).elevationMeters;
    const auto drainage = hydro->sample(center);
    const auto final = authority.sample(center);
    require(std::isfinite(final.elevationMeters), "surface authority elevation must remain finite");
    require(std::abs(final.elevationMeters - (base - drainage.incisionMeters)) < 1.0e-8,
        "surface authority must apply the exact hydrology incision used by rendering/physics");
}

void testClimateRespondsToSunAndCreatesPressureGradientWind() {
    vf::PlanetDefinition planet{};
    planet.radius = 6371000.0;
    planet.maxElevation = 8850.0;
    planet.maxOceanDepthMeters = 11000.0;
    planet.seed = 0x71A9F20DULL;

    vf::PlanetClimateConfig config{};
    config.latitudeBands = 16U;
    config.longitudeBands = 32U;
    vf::PlanetClimateGrid climate{planet, config, 7.2921150e-5};
    const glm::dvec3 sun{1.0, 0.0, 0.0};
    for (int i = 0; i < 720; ++i) climate.step(60.0, sun, 1361.0);

    const auto noon = climate.sample({1.0, 0.0, 0.0});
    const auto midnight = climate.sample({-1.0, 0.0, 0.0});
    require(noon.temperatureK > midnight.temperatureK,
        "stellar shortwave forcing must warm the illuminated hemisphere above the night hemisphere");

    double maxWind = 0.0;
    for (const auto& cell : climate.cells()) maxWind = std::max(maxWind, glm::length(cell.windEastNorthMps));
    require(maxWind > 0.01, "temperature gradients plus Coriolis/drag must generate a non-zero wind field");
}

void testOceanSpectrumHasTargetVarianceAndMoves() {
    vf::OceanSpectrumConfig config{};
    config.significantWaveHeightMeters = 2.0;
    config.peakPeriodSeconds = 8.0;
    vf::OceanSpectrum ocean{config};

    double mean = 0.0;
    double meanSquare = 0.0;
    constexpr int count = 4096;
    for (int i = 0; i < count; ++i) {
        const double t = static_cast<double>(i) * 0.37;
        const auto sample = ocean.sample({17.0, -23.0}, t);
        require(std::isfinite(sample.heightMeters), "ocean height must remain finite");
        mean += sample.heightMeters;
        meanSquare += sample.heightMeters * sample.heightMeters;
    }
    mean /= count;
    meanSquare /= count;
    const double sigma = std::sqrt(std::max(0.0, meanSquare - mean * mean));
    require(std::abs(4.0 * sigma - 2.0) < 0.25,
        "discrete JONSWAP-shaped packet must reproduce configured significant wave height");

    const auto a = ocean.sample({0.0, 0.0}, 0.0);
    const auto b = ocean.sample({0.0, 0.0}, 1.0);
    require(std::abs(a.heightMeters - b.heightMeters) > 1.0e-5,
        "physics ocean surface must evolve in time rather than being a static material normal");
}

} // namespace

int main() {
    testSurfaceAuthorityKeepsHydrologyInCollisionHeight();
    testClimateRespondsToSunAndCreatesPressureGradientWind();
    testOceanSpectrumHasTargetVarianceAndMoves();
    std::cout << "vf_r24_physical_planet_tests: PASS\n";
    return 0;
}
