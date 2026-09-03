#include "vf/physics/CelestialSurfaceFrames.hpp"
#include "vf/physics/PhysicsWorld.hpp"
#include "vf/world/CelestialSystem.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "CELESTIAL SURFACE FRAME TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void requireNear(double actual, double expected, double tolerance, std::string_view message) {
    if (std::abs(actual - expected) > tolerance) fail(message);
}

vf::PhysicsWorld makeWorld(vf::CelestialSystem& celestial, std::uint32_t planetId) {
    vf::PhysicsEnvironment environment{};
    environment.planet.radius = 100.0;
    environment.planet.maxElevation = 0.0;
    environment.planet.atmosphereHeight = 30.0;
    environment.ocean.enabled = false;
    environment.atmosphere.seaLevelPressurePa = 0.0;
    environment.celestialSystem = &celestial;
    environment.primaryCelestialBodyId = planetId;
    return vf::PhysicsWorld{environment};
}

void testStaticFixtureFollowsRealPlanetRotation() {
    vf::CelestialSystem celestial;
    vf::CelestialBody planet{};
    planet.radiusMeters = 100.0;
    planet.massKg = 9.81 * 100.0 * 100.0 / vf::CelestialSystem::kGravitationalConstant;
    planet.spinAxis = {0.0, 1.0, 0.0};
    planet.spinRateRadPerSecond = 0.5;
    const auto planetId = celestial.addBody(planet);
    auto world = makeWorld(celestial, planetId);

    vf::RigidBodyDesc fixture{};
    fixture.motionType = vf::MotionType::Static;
    fixture.position = {101.0, 0.0, 0.0};
    fixture.collisionShape = vf::CollisionShape::sphere(1.0);
    const auto fixtureId = world.createRigidBody(fixture);

    vf::CelestialSurfaceFrames frames;
    frames.beforePhysics(world, celestial);
    require(frames.isAttached(fixtureId), "surface static fixture must bind to its planet-local frame");
    const glm::dvec3 before = world.body(fixtureId)->position;

    celestial.step(0.5);
    frames.beforePhysics(world, celestial);
    const glm::dvec3 after = world.body(fixtureId)->position;

    require(glm::length(after - before) > 1.0,
        "planet-local fixture must move through inertial world when the actual planet rotates");
    require(std::abs(glm::length(after) - glm::length(before)) < 1.0e-6,
        "planet-local fixture must keep the same radius while rotating with the planet");
}

void testRestingDynamicBodySleepsRelativeToMovingSurface() {
    vf::CelestialSystem celestial;
    vf::CelestialBody planet{};
    planet.radiusMeters = 100.0;
    planet.massKg = 9.81 * 100.0 * 100.0 / vf::CelestialSystem::kGravitationalConstant;
    planet.spinAxis = {0.0, 1.0, 0.0};
    planet.spinRateRadPerSecond = 0.05;
    const auto planetId = celestial.addBody(planet);
    auto world = makeWorld(celestial, planetId);

    vf::RigidBodyDesc payload{};
    payload.position = {101.0, 0.0, 0.0};
    payload.mass = 1.0;
    payload.collisionShape = vf::CollisionShape::sphere(1.0);
    payload.linearVelocity = {0.0, 0.0, -5.05}; // omega x r at x=101 m.
    payload.angularVelocity = {0.0, 0.05, 0.0};
    payload.linearDamping = 0.0;
    payload.angularDamping = 0.0;
    payload.aerodynamics.referenceArea = 0.0;
    const auto payloadId = world.createRigidBody(payload);

    vf::CelestialSurfaceFrames frames;
    for (int i = 0; i < 6; ++i) frames.afterPhysics(world, celestial, 0.10);
    auto* body = world.body(payloadId);
    require(body != nullptr, "dynamic surface payload must exist");
    require(frames.isAttached(payloadId),
        "a body stationary relative to a 5 m/s rotating surface must be allowed to sleep");
    require(body->sleeping, "planet-local resting body must enter sleeping state");

    const glm::dvec3 before = body->position;
    celestial.step(0.25);
    frames.beforePhysics(world, celestial);
    const glm::dvec3 after = body->position;
    require(glm::length(after - before) > 0.5,
        "sleeping dynamic body must follow real celestial rotation instead of being left behind");
}

void testSpawnedSurfaceBodyInheritsPlanetFrameVelocity() {
    vf::CelestialSystem celestial;

    vf::CelestialBody star{};
    star.type = vf::CelestialBodyType::Star;
    star.radiusMeters = 50.0;
    star.massKg = 2.0e16;
    const auto starId = celestial.addBody(star);

    vf::CelestialBody planet{};
    planet.radiusMeters = 100.0;
    planet.massKg = 9.81 * 100.0 * 100.0 / vf::CelestialSystem::kGravitationalConstant;
    planet.gameplaySurfaceGravityMps2 = 9.81;
    planet.gravityInfluenceRadiusMeters = 400.0;
    planet.position = {1000.0, 0.0, 0.0};
    planet.linearVelocity = {0.0, 0.0, 50.0};
    planet.orbitParentId = starId;
    planet.spinAxis = {0.0, 1.0, 0.0};
    planet.spinRateRadPerSecond = 0.05;
    const auto planetId = celestial.addBody(planet);
    auto world = makeWorld(celestial, planetId);

    vf::RigidBodyDesc payload{};
    payload.position = {1101.0, 0.0, 0.0};
    payload.mass = 1.0;
    payload.collisionShape = vf::CollisionShape::sphere(1.0);
    payload.linearVelocity = {}; // authored as "at rest relative to the spawn surface"
    payload.angularVelocity = {};
    payload.linearDamping = 0.0;
    payload.angularDamping = 0.0;
    payload.aerodynamics.referenceArea = 0.0;
    const auto payloadId = world.createRigidBody(payload);

    vf::CelestialSurfaceFrames frames;
    frames.beforePhysics(world, celestial);

    const auto* storedPlanet = celestial.body(planetId);
    const auto* body = world.body(payloadId);
    require(storedPlanet != nullptr && body != nullptr, "spawn-frame test bodies must exist");
    const glm::dvec3 angularVelocity = storedPlanet->spinAxis * storedPlanet->spinRateRadPerSecond;
    const glm::dvec3 expected = storedPlanet->linearVelocity
        + glm::cross(angularVelocity, body->position - storedPlanet->position);
    require(glm::length(body->linearVelocity - expected) < 1.0e-9,
        "zero-world-speed surface spawn must inherit orbital plus rotational frame velocity immediately");
}

void testGameplayGravityIncludesCommonOrbitalFrameAcceleration() {
    vf::CelestialSystem celestial;

    vf::CelestialBody star{};
    star.type = vf::CelestialBodyType::Star;
    star.radiusMeters = 50.0;
    star.massKg = 2.0e16;
    const auto starId = celestial.addBody(star);

    vf::CelestialBody planet{};
    planet.radiusMeters = 100.0;
    planet.massKg = 9.81 * 100.0 * 100.0 / vf::CelestialSystem::kGravitationalConstant;
    planet.gameplaySurfaceGravityMps2 = 9.81;
    planet.gravityInfluenceRadiusMeters = 400.0;
    planet.position = {1000.0, 0.0, 0.0};
    planet.orbitParentId = starId;
    const auto planetId = celestial.addBody(planet);

    const glm::dvec3 surfacePoint{1100.0, 0.0, 0.0};
    const glm::dvec3 gravity = celestial.gameplayGravityAccelerationAt(surfacePoint);
    const double orbitalFrameAcceleration = vf::CelestialSystem::kGravitationalConstant
        * star.massKg / (1000.0 * 1000.0);

    requireNear(gravity.x, -(9.81 + orbitalFrameAcceleration), 1.0e-8,
        "surface gameplay gravity must include the planet's common parent-orbit acceleration");
    requireNear(gravity.y, 0.0, 1.0e-10,
        "collinear orbital frame acceleration must not invent transverse gravity");
    requireNear(gravity.z, 0.0, 1.0e-10,
        "collinear orbital frame acceleration must not invent transverse gravity");

    (void)planetId;
}

} // namespace

int main() {
    testStaticFixtureFollowsRealPlanetRotation();
    testRestingDynamicBodySleepsRelativeToMovingSurface();
    testSpawnedSurfaceBodyInheritsPlanetFrameVelocity();
    testGameplayGravityIncludesCommonOrbitalFrameAcceleration();
    std::cout << "vf_celestial_surface_frames_tests: PASS\n";
    return 0;
}
