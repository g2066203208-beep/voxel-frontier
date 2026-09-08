#include "vf/world/CelestialSystem.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>

#include <glm/geometric.hpp>

namespace {

constexpr double kPi = 3.1415926535897932384626433832795;

void require(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        std::exit(1);
    }
}

void requireNear(double actual, double expected, double tolerance, const char* message) {
    if (std::abs(actual - expected) > tolerance) {
        std::cerr << "FAIL: " << message << " actual=" << actual
                  << " expected=" << expected << " tolerance=" << tolerance << '\n';
        std::exit(1);
    }
}

void testAnalyticCircularOrbitAvoidsNBodyPairs() {
    vf::CelestialSystem system;
    vf::CelestialBody star{};
    star.type = vf::CelestialBodyType::Star;
    star.massKg = 1.98847e30;
    star.radiusMeters = 696340000.0;
    const auto starId = system.addBody(star);

    constexpr double radius = 149597870700.0;
    vf::CelestialBody planet{};
    planet.type = vf::CelestialBodyType::Planet;
    planet.massKg = 5.9722e24;
    planet.radiusMeters = 6371000.0;
    planet.orbitParentId = starId;
    planet.position = {-radius, 0.0, 0.0};
    planet.linearVelocity = {
        0.0,
        0.0,
        -std::sqrt(vf::CelestialSystem::kGravitationalConstant
            * (star.massKg + planet.massKg) / radius)};
    const auto planetId = system.addBody(planet);
    require(system.setAnalyticOrbitFromCurrentState(planetId),
        "circular planet must configure an analytic ephemeris from its live state");

    const double mu = vf::CelestialSystem::kGravitationalConstant * (star.massKg + planet.massKg);
    const double period = 2.0 * kPi * std::sqrt(radius * radius * radius / mu);
    system.step(period * 2.25);

    const auto* evolvedStar = system.body(starId);
    const auto* evolvedPlanet = system.body(planetId);
    require(evolvedStar != nullptr && evolvedPlanet != nullptr,
        "analytic bodies must remain addressable");
    requireNear(glm::length(evolvedPlanet->position - evolvedStar->position), radius, radius * 2.0e-9,
        "analytic circular orbit must preserve orbital radius over multi-orbit time skips");

    const vf::CelestialSimulationStats stats = system.lastStepStats();
    require(stats.dynamicBodies == 1U && stats.analyticBodies == 1U,
        "root star plus analytic planet must report the correct simulation tiers");
    require(stats.nbodyPairEvaluations == 0U,
        "analytic ephemeris bodies must not enter the quadratic dynamic N-body pair loop");
    require(stats.analyticEvaluations == 1U,
        "analytic planet should be evaluated once at the requested absolute epoch");
}

void testAnalyticHierarchyCarriesMoonWithParent() {
    vf::CelestialSystem system;
    vf::CelestialBody star{};
    star.type = vf::CelestialBodyType::Star;
    star.massKg = 1.98847e30;
    const auto starId = system.addBody(star);

    constexpr double planetRadius = 149597870700.0;
    vf::CelestialBody planet{};
    planet.massKg = 5.9722e24;
    planet.radiusMeters = 6371000.0;
    planet.orbitParentId = starId;
    planet.position = {-planetRadius, 0.0, 0.0};
    planet.linearVelocity = {
        0.0, 0.0,
        -std::sqrt(vf::CelestialSystem::kGravitationalConstant
            * (star.massKg + planet.massKg) / planetRadius)};
    const auto planetId = system.addBody(planet);
    require(system.setAnalyticOrbitFromCurrentState(planetId),
        "planet carrier must enter analytic ephemeris mode");

    constexpr double moonRadius = 384400000.0;
    vf::CelestialBody moon{};
    moon.type = vf::CelestialBodyType::Moon;
    moon.massKg = 7.342e22;
    moon.radiusMeters = 1737400.0;
    moon.orbitParentId = planetId;
    moon.position = planet.position + glm::dvec3{moonRadius, 0.0, 0.0};
    moon.linearVelocity = planet.linearVelocity + glm::dvec3{
        0.0, 0.0,
        std::sqrt(vf::CelestialSystem::kGravitationalConstant
            * (planet.massKg + moon.massKg) / moonRadius)};
    const auto moonId = system.addBody(moon);
    require(system.setAnalyticOrbitFromCurrentState(moonId),
        "moon must enter hierarchical analytic ephemeris mode");

    system.step(17.25 * 86400.0);
    const auto* evolvedStar = system.body(starId);
    const auto* evolvedPlanet = system.body(planetId);
    const auto* evolvedMoon = system.body(moonId);
    require(evolvedStar && evolvedPlanet && evolvedMoon,
        "hierarchical analytic bodies must remain available");
    requireNear(glm::length(evolvedPlanet->position - evolvedStar->position),
        planetRadius, planetRadius * 2.0e-9,
        "analytic planet must preserve parent-relative orbital radius");
    requireNear(glm::length(evolvedMoon->position - evolvedPlanet->position),
        moonRadius, moonRadius * 2.0e-8,
        "analytic moon must follow the moving parent rather than orbiting the inertial origin");
    require(system.lastStepStats().analyticEvaluations == 2U,
        "hierarchical planet+moon should require exactly one ephemeris evaluation each");
}

void testAnalyticSpinIsFrameRateIndependent() {
    vf::CelestialSystem oneStep;
    vf::CelestialSystem manySteps;
    vf::CelestialBody body{};
    body.radiusMeters = 100.0;
    body.massKg = 1.0e15;
    body.spinAxis = glm::normalize(glm::dvec3{0.21, 0.94, -0.17});
    body.spinRateRadPerSecond = 2.0 * kPi / 86164.0905;
    const auto oneId = oneStep.addBody(body);
    const auto manyId = manySteps.addBody(body);

    constexpr double elapsed = 172800.375;
    oneStep.step(elapsed);
    for (int i = 0; i < 2400; ++i) manySteps.step(elapsed / 2400.0);

    const glm::dquat a = oneStep.body(oneId)->orientation;
    const glm::dquat b = manySteps.body(manyId)->orientation;
    require(std::abs(glm::dot(a, b)) > 1.0 - 2.0e-12,
        "epoch-based spin must be independent of render/update cadence");
}

void testManyRemoteAnalyticBodiesScaleWithoutPairLoop() {
    vf::CelestialSystem system;
    vf::CelestialBody star{};
    star.type = vf::CelestialBodyType::Star;
    star.massKg = 1.0e30;
    const auto starId = system.addBody(star);

    constexpr int bodyCount = 64;
    for (int i = 0; i < bodyCount; ++i) {
        const double radius = 5.0e9 + static_cast<double>(i) * 2.0e8;
        const double phase = 2.0 * kPi * static_cast<double>(i) / bodyCount;
        vf::CelestialBody planet{};
        planet.massKg = 1.0e20 + static_cast<double>(i) * 1.0e17;
        planet.radiusMeters = 1000000.0;
        planet.orbitParentId = starId;
        planet.position = {radius * std::cos(phase), 0.0, radius * std::sin(phase)};
        const double speed = std::sqrt(vf::CelestialSystem::kGravitationalConstant
            * (star.massKg + planet.massKg) / radius);
        planet.linearVelocity = {-speed * std::sin(phase), 0.0, speed * std::cos(phase)};
        const auto id = system.addBody(planet);
        require(system.setAnalyticOrbitFromCurrentState(id),
            "remote circular body must accept analytic ephemeris mode");
    }

    system.step(3600.0);
    const auto stats = system.lastStepStats();
    require(stats.analyticBodies == static_cast<std::size_t>(bodyCount),
        "all remote planets must be classified analytic");
    require(stats.analyticEvaluations == static_cast<std::size_t>(bodyCount),
        "remote ephemerides must scale linearly with body count");
    require(stats.nbodyPairEvaluations == 0U,
        "64 analytic planets must not trigger the 2080-pair all-pairs loop");

    std::cout << "R24 celestial simulation LOD tests passed"
              << " analytic=" << stats.analyticBodies
              << " dynamic=" << stats.dynamicBodies
              << " ephemeris_evals=" << stats.analyticEvaluations
              << " nbody_pair_evals=" << stats.nbodyPairEvaluations
              << " dynamic_substeps=" << stats.dynamicSubsteps
              << '\n';
}

} // namespace

int main() {
    testAnalyticCircularOrbitAvoidsNBodyPairs();
    testAnalyticHierarchyCarriesMoonWithParent();
    testAnalyticSpinIsFrameRateIndependent();
    testManyRemoteAnalyticBodiesScaleWithoutPairLoop();
    return 0;
}
