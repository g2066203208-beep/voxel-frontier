#include "vf/world/PlanetaryBodySystem.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "PLANETARY BODY SYSTEM TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void requireNear(double actual, double expected, double tolerance, std::string_view message) {
    if (std::abs(actual - expected) > tolerance) fail(message);
}

std::uint32_t populateSystem(vf::PlanetaryBodySystem& system, bool withOcean = true) {
    vf::PlanetaryBodyDescriptor star{};
    star.celestial.type = vf::CelestialBodyType::Star;
    star.celestial.name = "Helion";
    star.celestial.radiusMeters = 100.0;
    star.celestial.massKg = 0.0;
    star.celestial.position = {1000000.0, 0.0, 0.0};
    star.celestial.luminosityWatts = 1.0e20;
    const std::uint32_t starId = system.addBody(star);

    vf::PlanetaryBodyDescriptor planet{};
    planet.celestial.type = vf::CelestialBodyType::Planet;
    planet.celestial.name = "Aster";
    planet.celestial.radiusMeters = 1000.0;
    planet.celestial.massKg = 1.0e18;
    planet.celestial.position = {};
    planet.celestial.orbitParentId = starId;
    planet.celestial.spinAxis = {0.0, 1.0, 0.0};
    planet.celestial.spinRateRadPerSecond = 0.001;
    planet.celestial.atmosphere.enabled = true;
    planet.celestial.atmosphere.heightMeters = 500.0;
    planet.celestial.atmosphere.surfacePressurePa = 101325.0;
    planet.celestial.atmosphere.scaleHeightMeters = 800.0;
    planet.solidSurface = true;
    planet.terrain.seed = 0xA57EULL;
    planet.terrain.radius = 12.0; // Must be overridden by the celestial radius.
    planet.terrain.maxElevation = 0.0;
    planet.terrain.maxOceanDepthMeters = 0.0;
    planet.climateEnabled = true;
    planet.climate.latitudeBands = 8U;
    planet.climate.longitudeBands = 16U;
    planet.climate.seaLevelPressurePa = 54321.0;
    planet.oceanEnabled = withOcean;
    return system.addBody(planet);
}

void testRegistryOwnsSurfaceClimateOceanAndRadiusContract() {
    vf::PlanetaryBodySystem system;
    const std::uint32_t planetId = populateSystem(system);

    const vf::PlanetaryBodyRuntime* runtime = system.runtime(planetId);
    require(runtime != nullptr, "planet runtime must exist");
    require(runtime->solidSurface, "ocean/climate planet must own one solid surface authority");
    require(runtime->surface != nullptr, "solid body must expose PlanetSurfaceAuthority");
    require(runtime->climate != nullptr, "climate-enabled body must expose PlanetClimateGrid");
    require(runtime->ocean != nullptr, "ocean-enabled body must expose OceanSpectrum");
    requireNear(runtime->terrain.radius, 1000.0, 1.0e-12,
        "planet service radius must be forced to the authoritative celestial radius");
    requireNear(runtime->surface->planet().radius, 1000.0, 1.0e-12,
        "surface authority and celestial body must share one physical radius");

    const vf::PlanetaryBodySystem& constSystem = system;
    require(constSystem.surface(planetId) != nullptr,
        "const planetary registry must expose its authoritative surface");
    require(constSystem.climate(planetId) != nullptr,
        "const planetary registry must expose its climate field");
    require(constSystem.ocean(planetId) != nullptr,
        "const planetary registry must expose its ocean spectrum");
}

void testUnifiedEnvironmentUsesTerrainAltitudeAndClimateField() {
    vf::PlanetaryBodySystem system;
    const std::uint32_t planetId = populateSystem(system, false);
    const auto* body = system.celestial().body(planetId);
    const auto* surface = system.surface(planetId);
    const auto* climate = system.climate(planetId);
    require(body != nullptr && surface != nullptr && climate != nullptr,
        "environment test requires celestial, surface and climate services");

    const glm::dvec3 localDirection{1.0, 0.0, 0.0};
    const double radius = surface->surfaceRadius(localDirection);
    const glm::dvec3 worldSurface = body->position + body->orientation * (localDirection * radius);
    const vf::CelestialEnvironmentSample sample = system.sampleEnvironment(worldSurface);
    const vf::PlanetClimateSample expected = climate->sample(localDirection, 0.0);

    require(sample.bodyId == planetId, "unified environment must identify the registered planet");
    requireNear(sample.altitudeMeters, 0.0, 1.0e-8,
        "unified environment altitude must use authoritative terrain instead of bare sphere radius");
    requireNear(sample.pressurePa, expected.pressurePa, 1.0e-8,
        "unified environment pressure must come from PlanetClimateGrid");
    requireNear(sample.temperatureK, expected.temperatureK, 1.0e-8,
        "unified environment temperature must come from PlanetClimateGrid");
    requireNear(sample.humidity, expected.relativeHumidity, 1.0e-8,
        "unified environment humidity must come from PlanetClimateGrid");
    require(std::abs(sample.pressurePa - body->atmosphere.surfacePressurePa) > 10000.0,
        "planetary climate pressure must override the fallback CelestialAtmosphere value");
}

void testLargePlanetaryStepMatchesRepeatedBoundedSubsteps() {
    vf::PlanetaryBodySystem largeStep;
    vf::PlanetaryBodySystem repeatedStep;
    const std::uint32_t largeId = populateSystem(largeStep, false);
    const std::uint32_t repeatedId = populateSystem(repeatedStep, false);

    largeStep.step(1200.0);
    for (int i = 0; i < 20; ++i) repeatedStep.step(60.0);

    const auto* largeBody = largeStep.celestial().body(largeId);
    const auto* repeatedBody = repeatedStep.celestial().body(repeatedId);
    const auto* largeClimate = largeStep.climate(largeId);
    const auto* repeatedClimate = repeatedStep.climate(repeatedId);
    require(largeBody != nullptr && repeatedBody != nullptr
        && largeClimate != nullptr && repeatedClimate != nullptr,
        "large-step comparison requires both complete planet runtimes");

    requireNear(largeStep.celestial().simulationTime(), 1200.0, 1.0e-9,
        "PlanetaryBodySystem must advance the complete requested celestial interval");
    requireNear(repeatedStep.celestial().simulationTime(), 1200.0, 1.0e-9,
        "repeated bounded planetary steps must advance the same interval");
    require(glm::length(largeBody->position - repeatedBody->position) < 1.0e-8,
        "large planetary step must use the same bounded orbital sequence as repeated 60-second steps");
    require(std::abs(glm::dot(largeBody->orientation, repeatedBody->orientation)) > 0.999999999999,
        "large planetary step must preserve the same spin sequence as repeated substeps");

    require(largeClimate->cells().size() == repeatedClimate->cells().size(),
        "climate grids must have identical topology");
    double maxTemperatureDifference = 0.0;
    double maxWindDifference = 0.0;
    for (std::size_t i = 0; i < largeClimate->cells().size(); ++i) {
        const auto& a = largeClimate->cells()[i];
        const auto& b = repeatedClimate->cells()[i];
        maxTemperatureDifference = std::max(
            maxTemperatureDifference,
            std::abs(a.temperatureK - b.temperatureK));
        maxWindDifference = std::max(
            maxWindDifference,
            glm::length(a.windEastNorthMps - b.windEastNorthMps));
    }
    require(maxTemperatureDifference < 1.0e-10,
        "large planetary step must not lose climate time through PlanetClimateGrid's internal dt clamp");
    require(maxWindDifference < 1.0e-10,
        "large planetary step must sample the same evolving solar forcing as repeated bounded steps");
}

void testOceanDescriptorCannotCreateDetachedWaterWithoutSurface() {
    vf::PlanetaryBodySystem system;
    vf::PlanetaryBodyDescriptor descriptor{};
    descriptor.celestial.name = "OceanBody";
    descriptor.celestial.radiusMeters = 800.0;
    descriptor.oceanEnabled = true;
    descriptor.solidSurface = false;
    descriptor.terrain.maxElevation = 20.0;
    descriptor.terrain.maxOceanDepthMeters = 100.0;
    const std::uint32_t id = system.addBody(descriptor);

    const auto* runtime = system.runtime(id);
    require(runtime != nullptr, "ocean body must have a planetary runtime");
    require(runtime->solidSurface && runtime->surface != nullptr && runtime->ocean != nullptr,
        "ocean service must be anchored to an authoritative solid surface");
}

} // namespace

int main() {
    testRegistryOwnsSurfaceClimateOceanAndRadiusContract();
    testUnifiedEnvironmentUsesTerrainAltitudeAndClimateField();
    testLargePlanetaryStepMatchesRepeatedBoundedSubsteps();
    testOceanDescriptorCannotCreateDetachedWaterWithoutSurface();
    std::cout << "vf_planetary_body_system_tests: PASS\n";
    return 0;
}
