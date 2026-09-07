#include "vf/physics/OceanSpectrum.hpp"
#include "vf/world/PlanetClimateGrid.hpp"
#include "vf/world/PlanetLodMeshBuilder.hpp"
#include "vf/world/PlanetSurfaceAuthority.hpp"
#include "vf/world/CelestialSystem.hpp"

#include <algorithm>
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

void testSurfaceSnapshotMatchesAuthoritativeHeightAndNormal() {
    vf::PlanetDefinition planet{};
    planet.radius = 6371000.0;
    planet.maxElevation = 8850.0;
    planet.maxOceanDepthMeters = 11000.0;
    planet.seed = 0x71A9F20DULL;
    const glm::dvec3 direction = glm::normalize(glm::dvec3{0.61, 0.43, -0.66});

    vf::PlanetSurfaceAuthority authority{planet};
    const vf::PlanetSurfaceSample snapshot = authority.sampleSurface(direction);
    const vf::PlanetTerrainSample terrain = authority.sample(direction);
    require(std::isfinite(snapshot.radiusMeters), "surface snapshot radius must stay finite");
    require(std::abs(snapshot.terrain.elevationMeters - terrain.elevationMeters) < 1.0e-9,
        "surface snapshot must share the exact authoritative center terrain sample");
    require(std::abs(snapshot.radiusMeters - (planet.radius + terrain.elevationMeters)) < 1.0e-8,
        "surface snapshot radius must equal planet radius plus authoritative elevation");
    require(glm::length(snapshot.position - direction * snapshot.radiusMeters) < 1.0e-6,
        "surface snapshot position must lie on its reported radius");
    require(std::abs(glm::length(snapshot.normal) - 1.0) < 1.0e-9,
        "surface snapshot normal must remain unit length");
    require(glm::dot(snapshot.normal, direction) > 1.0e-6,
        "surface snapshot normal must remain outward-facing even on near-vertical epic relief");
}

void testHydrologyAuthorityFadesBeforeRegionalGridEdge() {
    vf::PlanetDefinition planet{};
    planet.radius = 6371000.0;
    planet.maxElevation = 8850.0;
    planet.maxOceanDepthMeters = 11000.0;
    planet.seed = 0x71A9F20DULL;
    const glm::dvec3 center = glm::normalize(glm::dvec3{0.72, 0.52, 0.46});
    glm::dvec3 east = glm::normalize(glm::cross(glm::dvec3{0.0, 1.0, 0.0}, center));
    if (glm::length(east) < 0.5) east = glm::normalize(glm::cross(glm::dvec3{1.0, 0.0, 0.0}, center));

    vf::RegionalHydrologyConfig config{};
    config.resolution = 65U;
    config.halfExtentMeters = 45000.0;
    config.maxIncisionMeters = 320.0;
    auto hydro = std::make_shared<vf::RegionalHydrology>(planet, center, config);
    vf::PlanetSurfaceAuthority authority{planet};
    authority.setHydrology(hydro);

    const double outsideArc = config.halfExtentMeters * 0.97;
    const double angle = outsideArc / planet.radius;
    const glm::dvec3 outsideDirection = glm::normalize(center * std::cos(angle) + east * std::sin(angle));
    const double authorityElevation = authority.elevationMeters(outsideDirection);
    const double globalElevation = vf::samplePlanetTerrain(planet, outsideDirection).elevationMeters;
    require(std::abs(authorityElevation - globalElevation) < 1.0e-7,
        "regional hydrology must return to the global surface before the square DEM boundary");
}

void testAdaptiveTerrainLodProducesBoundedFiniteSurface() {
    vf::PlanetDefinition planet{};
    planet.radius = 6371000.0;
    planet.maxElevation = 8850.0;
    planet.maxOceanDepthMeters = 11000.0;
    planet.seed = 0x71A9F20DULL;
    vf::PlanetSurfaceAuthority authority{planet};

    vf::PlanetLodConfig config{};
    config.patchResolution = 6U;
    config.maxDepth = 8U;
    config.maxLeafPatches = 128U;
    config.viewportHeightPixels = 720.0;
    config.targetScreenErrorPixels = 5.0;
    config.skirtDepthMeters = 4.0;
    config.flatTerrainErrorFraction = 0.58;
    config.reliefErrorScale = 1.45;

    const glm::dvec3 cameraDirection = glm::normalize(glm::dvec3{0.72, 0.52, 0.46});
    const glm::dvec3 camera = cameraDirection * (planet.radius + 8000.0);
    vf::PlanetLodStats stats{};
    const vf::PlanetMesh mesh = vf::buildAdaptivePlanetSurface(authority, camera, config, &stats);

    require(!mesh.vertices.empty() && !mesh.indices.empty(),
        "adaptive terrain LOD must produce visible surface geometry");
    require(stats.leafPatches > 0U && stats.leafPatches <= config.maxLeafPatches,
        "adaptive terrain LOD must obey its leaf budget");
    require(stats.deepestLevel <= config.maxDepth,
        "adaptive terrain LOD must obey its maximum depth");
    require(stats.evaluatedNodes >= stats.leafPatches,
        "adaptive terrain LOD diagnostics must count every selected leaf evaluation");
    require(stats.maximumEstimatedErrorMeters > 0.0,
        "terrain-sensitive LOD must report a positive geometric error estimate");
    require(stats.nearestCellMeters > 0.0 && std::isfinite(stats.nearestCellMeters),
        "adaptive terrain LOD must report a finite physical cell scale");

    for (std::size_t i = 0; i < mesh.vertices.size(); i += 23U) {
        const auto& vertex = mesh.vertices[i];
        const glm::dvec3 p = glm::dvec3(vertex.position);
        const glm::dvec3 n = glm::dvec3(vertex.normal);
        require(std::isfinite(p.x) && std::isfinite(p.y) && std::isfinite(p.z),
            "adaptive terrain vertex positions must remain finite");
        require(std::abs(glm::length(n) - 1.0) < 2.0e-4,
            "adaptive terrain snapshot normals must stay normalized");
    }
}


void testNearFieldLodEnforcesContactScaleCells() {
    vf::PlanetDefinition planet{};
    planet.radius = 1000.0;
    planet.maxElevation = 30.0;
    planet.maxOceanDepthMeters = 40.0;
    planet.seed = 0x51A7C0DEULL;
    vf::PlanetSurfaceAuthority authority{planet};

    vf::PlanetLodConfig config{};
    config.patchResolution = 8U;
    config.maxDepth = 9U;
    config.maxLeafPatches = 256U;
    config.viewportHeightPixels = 720.0;
    config.targetScreenErrorPixels = 12.0; // intentionally loose: near-field rule must dominate
    config.nearFieldRadiusMeters = 1.0; // enables continuous camera-centred detail transition
    config.nearFieldCellMeters = 2.5;
    config.detailTransitionStartMeters = 8.0;
    config.detailTransitionEndMeters = 180.0;
    config.transitionFarCellMeters = 18.0;
    config.skirtDepthMeters = 1.0;

    const glm::dvec3 cameraDirection = glm::normalize(glm::dvec3{0.71, 0.49, 0.51});
    const glm::dvec3 camera = cameraDirection * (planet.radius + 12.0);
    vf::PlanetLodStats stats{};
    const vf::PlanetMesh mesh = vf::buildAdaptivePlanetSurface(authority, camera, config, &stats);
    require(!mesh.vertices.empty(), "near-field contact LOD must produce geometry");
    require(stats.nearestCellMeters <= config.nearFieldCellMeters * 1.05,
        "near-field LOD must refine physical cell size even when projected SSE is permissive");
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

void testEarthMoonPhysicalScaleRotationAndRevolution() {
    constexpr double earthRadius = 6371000.0;
    constexpr double moonRadius = 1737400.0;
    constexpr double distance = 384400000.0;
    constexpr double earthMass = 5.9722e24;
    constexpr double moonMass = 7.342e22;
    constexpr double pi = 3.14159265358979323846;

    const double moonAngularDiameter = 2.0 * std::atan(moonRadius / distance) * 180.0 / pi;
    const double earthAngularDiameterFromMoon = 2.0 * std::atan(earthRadius / distance) * 180.0 / pi;
    require(moonAngularDiameter > 0.50 && moonAngularDiameter < 0.54,
        "physical Moon must subtend about half a degree from Earth");
    require(earthAngularDiameterFromMoon > 1.85 && earthAngularDiameterFromMoon < 1.95,
        "physical Earth must subtend about 1.9 degrees from the Moon");

    vf::PlanetDefinition earthDefinition{};
    earthDefinition.radius = earthRadius;
    earthDefinition.maxElevation = 8850.0;
    earthDefinition.maxOceanDepthMeters = 11000.0;
    const vf::PlanetMesh globe = vf::buildPlanetGlobeSurface(earthDefinition, 12U, 1.0);
    require(!globe.vertices.empty() && !globe.indices.empty(),
        "distant globe must contain real displaced 3-D geometry");
    for (std::size_t i = 0; i < globe.vertices.size(); i += 37U) {
        const glm::dvec3 p = glm::dvec3(globe.vertices[i].position);
        const glm::dvec3 n = glm::dvec3(globe.vertices[i].normal);
        require(std::abs(glm::length(n) - 1.0) < 1.0e-5,
            "planet-scale globe normals must stay unit length and smooth");
        require(glm::length(p) > earthRadius - 12000.0 && glm::length(p) < earthRadius + 10000.0,
            "planet-scale globe must preserve physical relief rather than exaggerated chunks");
    }

    vf::CelestialSystem system;
    vf::CelestialBody earth{};
    earth.type = vf::CelestialBodyType::Planet;
    earth.radiusMeters = earthRadius;
    earth.massKg = earthMass;
    earth.spinAxis = {0.0, 1.0, 0.0};
    earth.spinRateRadPerSecond = 2.0 * pi / 86164.0905;

    vf::CelestialBody moon{};
    moon.type = vf::CelestialBodyType::Moon;
    moon.radiusMeters = moonRadius;
    moon.massKg = moonMass;
    moon.spinAxis = {0.0, 1.0, 0.0};
    moon.spinRateRadPerSecond = 2.0 * pi / (27.321661 * 86400.0);

    const double totalMass = earthMass + moonMass;
    const double relativeSpeed = std::sqrt(vf::CelestialSystem::kGravitationalConstant * totalMass / distance);
    earth.position = {-distance * moonMass / totalMass, 0.0, 0.0};
    moon.position = {distance * earthMass / totalMass, 0.0, 0.0};
    earth.linearVelocity = {0.0, 0.0, relativeSpeed * moonMass / totalMass};
    moon.linearVelocity = {0.0, 0.0, -relativeSpeed * earthMass / totalMass};

    const auto earthId = system.addBody(earth);
    const auto moonId = system.addBody(moon);
    const glm::dvec3 initialRelative = system.body(moonId)->position - system.body(earthId)->position;
    const glm::dquat initialEarthOrientation = system.body(earthId)->orientation;

    constexpr int sixHoursInMinuteSteps = 360;
    for (int i = 0; i < sixHoursInMinuteSteps; ++i) system.step(60.0);

    const auto* movedEarth = system.body(earthId);
    const auto* movedMoon = system.body(moonId);
    const glm::dvec3 finalRelative = movedMoon->position - movedEarth->position;
    const double separationError = std::abs(glm::length(finalRelative) - distance) / distance;
    require(separationError < 2.0e-4,
        "Earth-Moon two-body separation must remain stable over a six-hour integration window");
    require(glm::dot(glm::normalize(initialRelative), glm::normalize(finalRelative)) < 0.9995,
        "Moon must visibly revolve around Earth over simulated time");
    require(std::abs(glm::dot(initialEarthOrientation, movedEarth->orientation)) < 0.999,
        "Earth orientation must change from physical self-rotation");
}

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

} // namespace

int main() {
    testSurfaceAuthorityKeepsHydrologyInCollisionHeight();
    testSurfaceSnapshotMatchesAuthoritativeHeightAndNormal();
    testHydrologyAuthorityFadesBeforeRegionalGridEdge();
    testAdaptiveTerrainLodProducesBoundedFiniteSurface();
    testNearFieldLodEnforcesContactScaleCells();
    testClimateRespondsToSunAndCreatesPressureGradientWind();
    testOceanSpectrumHasTargetVarianceAndMoves();
    testEarthMoonPhysicalScaleRotationAndRevolution();
    testAirlessMoonUsesCrateredThreeDimensionalRelief();
    testEarthlikeMountainsDoNotCollapseIntoMaxElevationPlateau();
    std::cout << "vf_r24_physical_planet_tests: PASS\n";
    return 0;
}
