#include "vf/physics/CelestialSurfaceFrames.hpp"
#include "vf/physics/PhysicsWorld.hpp"
#include "vf/world/CelestialSystem.hpp"

#include <algorithm>
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

[[nodiscard]] glm::dvec3 surfaceVelocity(const vf::CelestialBody& body, const glm::dvec3& point) {
    const glm::dvec3 omega = glm::normalize(body.spinAxis) * body.spinRateRadPerSecond;
    return body.linearVelocity + glm::cross(omega, point - body.position);
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
    frames.afterPhysics(world, celestial, 1.0 / 60.0);
    const glm::dvec3 before = world.body(fixtureId)->position;

    celestial.step(0.5);
    frames.beforePhysics(world, celestial);
    const glm::dvec3 after = world.body(fixtureId)->position;
    frames.afterPhysics(world, celestial, 0.5);

    require(glm::length(after - before) > 1.0,
        "planet-local fixture must move through inertial world when the actual planet rotates");
    require(std::abs(glm::length(after) - glm::length(before)) < 1.0e-6,
        "planet-local fixture must keep the same radius while rotating with the planet");
}

void testLocalSolveRemovesLargeSurfaceVelocityThenRestoresIt() {
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
    payload.linearVelocity = {};
    payload.angularVelocity = {};
    payload.linearDamping = 0.0;
    payload.angularDamping = 0.0;
    payload.aerodynamics.referenceArea = 0.0;
    const auto payloadId = world.createRigidBody(payload);

    vf::CelestialSurfaceFrames frames;
    frames.beforePhysics(world, celestial);
    auto* body = world.body(payloadId);
    require(body != nullptr, "surface payload must exist");
    require(glm::length(body->linearVelocity) < 1.0e-10,
        "inside the fixed-step local physics solve a resting prop must not carry orbital/surface speed");
    require(world.environment().celestialSystem != &celestial,
        "fixed-step solve must use a frozen local celestial proxy rather than the moving global planet");

    frames.afterPhysics(world, celestial, 1.0 / 60.0);
    const auto* storedPlanet = celestial.body(planetId);
    require(storedPlanet != nullptr, "surface planet must exist");
    const glm::dvec3 expected = surfaceVelocity(*storedPlanet, body->position);
    require(glm::length(body->linearVelocity - expected) < 1.0e-9,
        "after the solve the prop must recover exact inertial orbital plus rotational velocity");
    require(world.environment().celestialSystem == &celestial,
        "world-level systems must regain the authoritative inertial celestial system after physics");
}

void testRelativeGravityRemovesOnlyCommonOrbitalAcceleration() {
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
    const glm::dvec3 relative = celestial.gravityAccelerationRelativeTo(planetId, surfacePoint);

    const double starAtSurface = vf::CelestialSystem::kGravitationalConstant * star.massKg / (1100.0 * 1100.0);
    const double starAtPlanet = vf::CelestialSystem::kGravitationalConstant * star.massKg / (1000.0 * 1000.0);
    // The point is on the far side of the planet from the star. Both stellar accelerations point
    // toward -X, but the planet center is pulled slightly harder; after subtracting common-mode
    // frame acceleration the residual tide therefore points +X.
    const double expectedX = -9.81 + (starAtPlanet - starAtSurface);
    requireNear(relative.x, expectedX, 1.0e-8,
        "local planet frame must subtract common parent acceleration but preserve real tidal difference");
    requireNear(relative.y, 0.0, 1.0e-10, "relative frame gravity must not invent transverse acceleration");
    requireNear(relative.z, 0.0, 1.0e-10, "relative frame gravity must not invent transverse acceleration");
}

void testRestingDynamicBodyCanSleepInLocalSolve() {
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
    payload.material.restitution = 0.0;
    payload.material.friction = 1.0;
    payload.linearDamping = 0.10;
    payload.angularDamping = 0.10;
    payload.aerodynamics.referenceArea = 0.0;
    const auto payloadId = world.createRigidBody(payload);

    vf::CelestialSurfaceFrames frames;
    constexpr double dt = 1.0 / 60.0;
    for (int i = 0; i < 120; ++i) {
        celestial.step(dt);
        frames.beforePhysics(world, celestial);
        world.advance(dt);
        frames.afterPhysics(world, celestial, dt);
    }

    const auto* body = world.body(payloadId);
    require(body != nullptr, "dynamic surface payload must exist");
    require(frames.isAttached(payloadId),
        "a body genuinely stationary relative to a rotating surface must enter planet-local sleep");
    require(body->sleeping, "planet-local resting body must enter sleeping state");
}

void testOrbitingSurfaceBodySettlesWithoutLocalFrameJitter() {
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
    planet.gravityInfluenceRadiusMeters = 500.0;
    planet.position = {1000.0, 0.0, 0.0};
    planet.linearVelocity = {0.0, 0.0,
        std::sqrt(vf::CelestialSystem::kGravitationalConstant * star.massKg / 1000.0)};
    planet.orbitParentId = starId;
    planet.spinAxis = {0.0, 1.0, 0.0};
    planet.spinRateRadPerSecond = 0.02;
    const auto planetId = celestial.addBody(planet);
    auto world = makeWorld(celestial, planetId);

    vf::RigidBodyDesc payload{};
    payload.position = {1101.0, 0.0, 0.0};
    payload.mass = 2.0;
    payload.collisionShape = vf::CollisionShape::sphere(1.0);
    payload.material.friction = 1.0;
    payload.material.restitution = 0.0;
    payload.material.rollingResistance = 0.08;
    payload.linearDamping = 0.05;
    payload.angularDamping = 0.08;
    payload.aerodynamics.referenceArea = 0.0;
    const auto payloadId = world.createRigidBody(payload);

    vf::CelestialSurfaceFrames frames;
    double minLocalRadius = 1.0e30;
    double maxLocalRadius = 0.0;

    constexpr double dt = 1.0 / 60.0;
    for (int frame = 0; frame < 360; ++frame) {
        celestial.step(dt);
        frames.beforePhysics(world, celestial);
        world.advance(dt);
        frames.afterPhysics(world, celestial, dt);

        const auto* p = celestial.body(planetId);
        const auto* b = world.body(payloadId);
        require(p != nullptr && b != nullptr, "jitter regression bodies must remain valid");
        if (frame >= 180) {
            const glm::dvec3 local = glm::conjugate(glm::normalize(p->orientation)) * (b->position - p->position);
            const double localRadius = glm::length(local);
            minLocalRadius = std::min(minLocalRadius, localRadius);
            maxLocalRadius = std::max(maxLocalRadius, localRadius);
        }
    }

    require(frames.isAttached(payloadId),
        "a stationary prop on an orbiting and rotating planet must eventually enter planet-local sleep");
    require(maxLocalRadius - minLocalRadius < 0.02,
        "settled surface prop must not exhibit visible frame-to-frame radial jitter in planet-local coordinates");
    requireNear(0.5 * (maxLocalRadius + minLocalRadius), 101.0, 0.03,
        "settled surface prop must stay on the expected local surface radius while the planet orbits");
}

} // namespace

int main() {
    testStaticFixtureFollowsRealPlanetRotation();
    testLocalSolveRemovesLargeSurfaceVelocityThenRestoresIt();
    testRelativeGravityRemovesOnlyCommonOrbitalAcceleration();
    testRestingDynamicBodyCanSleepInLocalSolve();
    testOrbitingSurfaceBodySettlesWithoutLocalFrameJitter();
    std::cout << "vf_celestial_surface_frames_tests: PASS\n";
    return 0;
}
