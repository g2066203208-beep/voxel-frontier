#include "vf/world/CelestialSystem.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "CELESTIAL CONSERVATION TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

double totalMechanicalEnergy(const vf::CelestialSystem& system) {
    double energy = 0.0;
    const auto bodies = system.bodies();
    for (const auto& body : bodies) {
        energy += 0.5 * body.massKg * glm::dot(body.linearVelocity, body.linearVelocity);
    }
    for (std::size_t i = 0; i < bodies.size(); ++i) {
        for (std::size_t j = i + 1; j < bodies.size(); ++j) {
            const double distance = glm::length(bodies[j].position - bodies[i].position);
            energy -= vf::CelestialSystem::kGravitationalConstant
                * bodies[i].massKg * bodies[j].massKg / distance;
        }
    }
    return energy;
}

glm::dvec3 totalMomentum(const vf::CelestialSystem& system) {
    glm::dvec3 momentum{};
    for (const auto& body : system.bodies()) momentum += body.linearVelocity * body.massKg;
    return momentum;
}

glm::dvec3 barycentre(const vf::CelestialSystem& system) {
    double totalMass = 0.0;
    glm::dvec3 weightedPosition{};
    for (const auto& body : system.bodies()) {
        totalMass += body.massKg;
        weightedPosition += body.position * body.massKg;
    }
    return totalMass > 0.0 ? weightedPosition / totalMass : glm::dvec3{};
}

double totalMass(const vf::CelestialSystem& system) {
    double mass = 0.0;
    for (const auto& body : system.bodies()) mass += body.massKg;
    return mass;
}

void testLongHorizonCircularTwoBodyConservation() {
    constexpr double primaryMass = 1.0e20;
    constexpr double secondaryMass = 1.0e15;
    constexpr double separation = 1.0e6;
    const double combinedMass = primaryMass + secondaryMass;
    const double relativeSpeed = std::sqrt(
        vf::CelestialSystem::kGravitationalConstant * combinedMass / separation);
    const double period = 2.0 * 3.14159265358979323846 * std::sqrt(
        separation * separation * separation
        / (vf::CelestialSystem::kGravitationalConstant * combinedMass));

    vf::CelestialSystem system;
    vf::CelestialBody primary{};
    primary.type = vf::CelestialBodyType::Star;
    primary.name = "conservation-primary";
    primary.massKg = primaryMass;
    primary.radiusMeters = 1000.0;
    primary.position = {-secondaryMass / combinedMass * separation, 0.0, 0.0};
    primary.linearVelocity = {0.0, 0.0, -secondaryMass / combinedMass * relativeSpeed};
    system.addBody(primary);

    vf::CelestialBody secondary{};
    secondary.type = vf::CelestialBodyType::Planet;
    secondary.name = "conservation-secondary";
    secondary.massKg = secondaryMass;
    secondary.radiusMeters = 100.0;
    secondary.position = {primaryMass / combinedMass * separation, 0.0, 0.0};
    secondary.linearVelocity = {0.0, 0.0, primaryMass / combinedMass * relativeSpeed};
    system.addBody(secondary);

    const double initialEnergy = totalMechanicalEnergy(system);
    const glm::dvec3 initialMomentum = totalMomentum(system);
    const glm::dvec3 initialBarycentre = barycentre(system);
    const double momentumScale = secondaryMass * relativeSpeed;

    constexpr double stepSeconds = 60.0;
    const int stepCount = static_cast<int>(std::ceil(5.0 * period / stepSeconds));
    for (int i = 0; i < stepCount; ++i) system.step(stepSeconds);

    const double finalEnergy = totalMechanicalEnergy(system);
    const glm::dvec3 finalMomentum = totalMomentum(system);
    const glm::dvec3 finalBarycentre = barycentre(system);
    const auto bodies = system.bodies();
    const double finalSeparation = glm::length(bodies[1].position - bodies[0].position);

    const double relativeEnergyDrift = std::abs(finalEnergy - initialEnergy)
        / std::max(1.0, std::abs(initialEnergy));
    const double relativeMomentumDrift = glm::length(finalMomentum - initialMomentum)
        / std::max(1.0, momentumScale);
    const double relativeRadiusDrift = std::abs(finalSeparation - separation) / separation;

    require(relativeEnergyDrift < 1.0e-8,
        "velocity-Verlet must keep two-body mechanical energy bounded over five orbits");
    require(relativeMomentumDrift < 1.0e-10,
        "pairwise N-body kicks must conserve total linear momentum");
    require(glm::length(finalBarycentre - initialBarycentre) < 1.0e-5,
        "zero-momentum isolated two-body barycentre must remain stationary");
    require(relativeRadiusDrift < 1.0e-5,
        "a circular two-body orbit must not secularly spiral over the long-horizon gate");
}

void testThreeBodyBarycentreFollowsTotalMomentum() {
    vf::CelestialSystem system;

    vf::CelestialBody star{};
    star.type = vf::CelestialBodyType::Star;
    star.name = "three-body-star";
    star.massKg = 1.0e22;
    star.radiusMeters = 1000.0;
    system.addBody(star);

    vf::CelestialBody planet{};
    planet.type = vf::CelestialBodyType::Planet;
    planet.name = "three-body-planet";
    planet.massKg = 1.0e18;
    planet.radiusMeters = 100.0;
    planet.position = {2.0e6, 0.0, 0.0};
    const double planetSpeed = std::sqrt(
        vf::CelestialSystem::kGravitationalConstant * star.massKg / glm::length(planet.position));
    planet.linearVelocity = {0.0, 0.0, planetSpeed};
    system.addBody(planet);

    vf::CelestialBody moon{};
    moon.type = vf::CelestialBodyType::Moon;
    moon.name = "three-body-moon";
    moon.massKg = 1.0e15;
    moon.radiusMeters = 20.0;
    moon.position = planet.position + glm::dvec3{2.0e5, 0.0, 0.0};
    const double moonRelativeSpeed = std::sqrt(
        vf::CelestialSystem::kGravitationalConstant * planet.massKg / 2.0e5);
    moon.linearVelocity = planet.linearVelocity + glm::dvec3{0.0, 0.0, moonRelativeSpeed};
    system.addBody(moon);

    const glm::dvec3 initialMomentum = totalMomentum(system);
    const glm::dvec3 initialBarycentre = barycentre(system);
    const double mass = totalMass(system);
    double momentumScale = 0.0;
    for (const auto& body : system.bodies()) {
        momentumScale += body.massKg * glm::length(body.linearVelocity);
    }

    constexpr double stepSeconds = 10.0;
    constexpr int stepCount = 4000;
    for (int i = 0; i < stepCount; ++i) system.step(stepSeconds);

    const double elapsed = stepSeconds * static_cast<double>(stepCount);
    const glm::dvec3 expectedBarycentre = initialBarycentre + initialMomentum / mass * elapsed;
    const glm::dvec3 finalMomentum = totalMomentum(system);
    const double relativeMomentumDrift = glm::length(finalMomentum - initialMomentum)
        / std::max(1.0, momentumScale);

    require(relativeMomentumDrift < 1.0e-10,
        "three-body integration must conserve total linear momentum without a privileged parent");
    require(glm::length(barycentre(system) - expectedBarycentre) < 1.0e-4,
        "isolated three-body barycentre must move uniformly according to conserved momentum");
}

} // namespace

int main() {
    testLongHorizonCircularTwoBodyConservation();
    testThreeBodyBarycentreFollowsTotalMomentum();
    std::cout << "vf_celestial_conservation_tests: PASS\n";
    return 0;
}
