#include "vf/physics/PhysicsWorld.hpp"
#include "vf/world/CelestialSystem.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "CELESTIAL SYSTEM TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void requireNear(double actual, double expected, double tolerance, std::string_view message) {
    if (std::abs(actual - expected) > tolerance) fail(message);
}

void testSurfaceGravityAndAtmosphereBelongToEachPlanet() {
    vf::CelestialSystem system;

    vf::CelestialBody first{};
    first.name = "A";
    first.radiusMeters = 240.0;
    first.massKg = 9.81 * first.radiusMeters * first.radiusMeters / vf::CelestialSystem::kGravitationalConstant;
    first.atmosphere.enabled = true;
    first.atmosphere.heightMeters = 120.0;
    first.atmosphere.surfacePressurePa = 101325.0;
    first.atmosphere.scaleHeightMeters = 70.0;
    first.climate.meanTemperatureK = 288.15;
    const auto firstId = system.addBody(first);

    const glm::dvec3 primarySurfacePoint{240.0, 0.0, 0.0};
    const auto isolatedSurface = system.sampleEnvironment(primarySurfacePoint);
    require(isolatedSurface.bodyId == firstId, "primary planet must own its local environment");
    requireNear(glm::length(isolatedSurface.gravityAcceleration), 9.81, 0.02,
        "isolated primary surface gravity must match GM/R^2");
    require(isolatedSurface.pressurePa > 90000.0, "primary planet must expose its own atmosphere");

    vf::CelestialBody second = first;
    second.name = "B";
    second.position = {1200.0, 0.0, 0.0};
    second.massKg *= 0.38;
    second.atmosphere.surfacePressurePa = 600.0;
    second.climate.meanTemperatureK = 220.0;
    const auto secondId = system.addBody(second);

    const auto firstSurface = system.sampleEnvironment(primarySurfacePoint);
    require(firstSurface.bodyId == firstId, "primary planet must retain ownership after another gravity source is added");

    const double primaryAcceleration = vf::CelestialSystem::kGravitationalConstant
        * first.massKg / (first.radiusMeters * first.radiusMeters);
    const double secondDistance = second.position.x - primarySurfacePoint.x;
    const double secondaryAcceleration = vf::CelestialSystem::kGravitationalConstant
        * second.massKg / (secondDistance * secondDistance);
    const double expectedX = -primaryAcceleration + secondaryAcceleration;
    requireNear(firstSurface.gravityAcceleration.x, expectedX, 1.0e-6,
        "multi-body gravity must equal the vector superposition of both bodies");
    require(std::abs(firstSurface.gravityAcceleration.y) < 1.0e-10
        && std::abs(firstSurface.gravityAcceleration.z) < 1.0e-10,
        "collinear two-body gravity must remain collinear");

    const auto secondSurface = system.sampleEnvironment({1440.0, 0.0, 0.0});
    require(secondSurface.bodyId == secondId, "second planet must own its local environment");
    require(secondSurface.pressurePa > 400.0 && secondSurface.pressurePa < 800.0,
        "second planet must use its own atmosphere rather than the primary atmosphere");
    require(secondSurface.temperatureK < firstSurface.temperatureK,
        "second planet must use its own climate state");
}

void testAtmosphereFadesToVacuum() {
    vf::CelestialSystem system;
    vf::CelestialBody planet{};
    planet.radiusMeters = 100.0;
    planet.massKg = 1.0e15;
    planet.atmosphere.enabled = true;
    planet.atmosphere.heightMeters = 50.0;
    planet.atmosphere.surfacePressurePa = 100000.0;
    planet.atmosphere.scaleHeightMeters = 20.0;
    const auto id = system.addBody(planet);

    const auto surface = system.sampleEnvironment({100.0, 0.0, 0.0});
    const auto high = system.sampleEnvironment({140.0, 0.0, 0.0});
    const auto vacuum = system.sampleEnvironment({200.0, 0.0, 0.0});
    require(surface.bodyId == id && high.bodyId == id, "atmosphere samples must identify the planet");
    require(surface.pressurePa > high.pressurePa, "pressure must fall with altitude");
    require(vacuum.pressurePa == 0.0 && vacuum.densityKgPerM3 == 0.0,
        "outside the atmosphere must be vacuum");
}

void testSpinAndBoundOrbit() {
    vf::CelestialSystem system;
    vf::CelestialBody star{};
    star.type = vf::CelestialBodyType::Star;
    star.radiusMeters = 80.0;
    star.massKg = 1.0e15;
    const auto starId = system.addBody(star);

    vf::CelestialBody planet{};
    planet.radiusMeters = 20.0;
    planet.massKg = 1.0e10;
    planet.position = {1000.0, 0.0, 0.0};
    planet.orbitParentId = starId;
    planet.linearVelocity = {0.0, 0.0, std::sqrt(vf::CelestialSystem::kGravitationalConstant * star.massKg / 1000.0)};
    planet.spinAxis = {0.0, 1.0, 0.0};
    planet.spinRateRadPerSecond = 0.5;
    const auto planetId = system.addBody(planet);

    const glm::dquat initialOrientation = system.body(planetId)->orientation;
    for (int i = 0; i < 1000; ++i) system.step(0.05);

    const auto* evolved = system.body(planetId);
    require(evolved != nullptr, "orbiting body must remain accessible");
    const double radius = glm::length(evolved->position - system.body(starId)->position);
    require(radius > 900.0 && radius < 1100.0, "cheap symplectic orbit must remain bound over the smoke interval");
    require(std::abs(glm::dot(initialOrientation, evolved->orientation)) < 0.999,
        "planet spin must evolve orientation");
}

void testDipoleMagneticFieldFallsWithDistance() {
    vf::CelestialSystem system;
    vf::CelestialBody planet{};
    planet.radiusMeters = 100.0;
    planet.massKg = 1.0e15;
    planet.magneticField.enabled = true;
    planet.magneticField.dipoleAxis = {0.0, 1.0, 0.0};
    planet.magneticField.equatorialSurfaceFieldTesla = 30.0e-6;
    const auto id = system.addBody(planet);
    const auto* stored = system.body(id);

    const double surface = glm::length(system.magneticFieldAt(*stored, {100.0, 0.0, 0.0}));
    const double twiceRadius = glm::length(system.magneticFieldAt(*stored, {200.0, 0.0, 0.0}));
    requireNear(surface, 30.0e-6, 1.0e-9, "equatorial field must match configured surface field");
    requireNear(twiceRadius / surface, 1.0 / 8.0, 0.002, "dipole field must follow inverse-cube distance scaling");
}

void testRotatingSurfaceTransfersTangentialVelocityToRigidBody() {
    vf::PlanetDefinition terrain{};
    terrain.radius = 100.0;
    terrain.maxElevation = 0.0;

    vf::CelestialSystem celestial;
    vf::CelestialBody planet{};
    planet.radiusMeters = terrain.radius;
    planet.massKg = 9.81 * planet.radiusMeters * planet.radiusMeters
        / vf::CelestialSystem::kGravitationalConstant;
    planet.spinAxis = {0.0, 1.0, 0.0};
    planet.spinRateRadPerSecond = 0.01;
    const auto planetId = celestial.addBody(planet);

    vf::PhysicsEnvironment environment{};
    environment.planet = terrain;
    environment.celestialSystem = &celestial;
    environment.primaryCelestialBodyId = planetId;
    environment.ocean.enabled = false;
    environment.atmosphere.seaLevelPressurePa = 0.0;
    vf::PhysicsWorld physics{environment};

    vf::RigidBodyDesc desc{};
    desc.position = {101.0, 0.0, 0.0};
    desc.mass = 1.0;
    desc.collisionShape = vf::CollisionShape::sphere(1.0);
    desc.linearDamping = 0.0;
    desc.angularDamping = 0.0;
    desc.material.friction = 1.0;
    desc.material.restitution = 0.0;
    desc.aerodynamics.referenceArea = 0.0;
    const auto bodyId = physics.createRigidBody(desc);

    for (int i = 0; i < 240; ++i) physics.stepFixed();
    const auto* body = physics.body(bodyId);
    require(body != nullptr, "rotating-surface rigid body must remain accessible");
    require(std::abs(body->linearVelocity.z) > 0.20,
        "ground friction must transfer non-zero tangential velocity from omega-cross-r surface motion");
    require(glm::length(body->position) >= 100.999,
        "moving celestial surface contact must still prevent penetration");
}

} // namespace

int main() {
    testSurfaceGravityAndAtmosphereBelongToEachPlanet();
    testAtmosphereFadesToVacuum();
    testSpinAndBoundOrbit();
    testDipoleMagneticFieldFallsWithDistance();
    testRotatingSurfaceTransfersTangentialVelocityToRigidBody();
    std::cout << "vf_celestial_system_tests: PASS\n";
    return 0;
}
