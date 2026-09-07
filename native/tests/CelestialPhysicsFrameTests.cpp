#include "vf/player/PlanetCamera.hpp"
#include "vf/world/CelestialPhysicsFrame.hpp"
#include "vf/world/CelestialSystem.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>
#include <glm/gtc/quaternion.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "CELESTIAL PHYSICS FRAME TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void requireNear(double actual, double expected, double tolerance, std::string_view message) {
    if (std::abs(actual - expected) > tolerance) fail(message);
}

void testWorldLocalRoundTripPreservesState() {
    vf::CelestialBody planet{};
    planet.id = 7U;
    planet.position = {45000.0, -3100.0, 8200.0};
    planet.linearVelocity = {18.0, -4.0, 249.0};
    planet.spinAxis = glm::normalize(glm::dvec3{0.08, 1.0, 0.03});
    planet.spinRateRadPerSecond = 0.0052;
    planet.orientation = glm::normalize(glm::angleAxis(0.73, planet.spinAxis));

    vf::CelestialPhysicsFrame frame{planet.id};
    const glm::dvec3 localPosition{4200.0, 1500.0, -3900.0};
    const glm::dvec3 localVelocity{31.0, -7.0, 82.0};
    const glm::dvec3 worldPosition = frame.toWorldPosition(planet, localPosition);
    const glm::dvec3 worldVelocity = frame.toWorldVelocity(planet, localPosition, localVelocity);

    require(glm::length(frame.toLocalPosition(planet, worldPosition) - localPosition) < 1.0e-9,
        "world/local position handoff must be reversible");
    require(glm::length(frame.toLocalVelocity(planet, worldPosition, worldVelocity) - localVelocity) < 1.0e-9,
        "world/local velocity handoff must preserve orbital and rotational surface velocity exactly");
}

void testSurfaceRestIsZeroLocalVelocity() {
    vf::CelestialBody planet{};
    planet.id = 3U;
    planet.position = {45000.0, 0.0, 0.0};
    planet.linearVelocity = {0.0, 0.0, 250.0};
    planet.spinAxis = {0.0, 1.0, 0.0};
    planet.spinRateRadPerSecond = 0.005;
    planet.orientation = glm::normalize(glm::angleAxis(0.4, glm::dvec3{0.0, 1.0, 0.0}));

    vf::CelestialPhysicsFrame frame{planet.id};
    const glm::dvec3 localSurface{6000.0, 0.0, 0.0};
    const glm::dvec3 worldSurface = frame.toWorldPosition(planet, localSurface);
    const glm::dvec3 worldSurfaceVelocity = frame.toWorldVelocity(planet, localSurface, {});

    require(glm::length(frame.toLocalVelocity(planet, worldSurface, worldSurfaceVelocity)) < 1.0e-10,
        "a building, parked rover or resting item must have zero velocity in planet physics space");
}

void testPhysicalGravityPersistsOutsideReferenceBubble() {
    vf::CelestialSystem system;
    vf::CelestialBody planet{};
    planet.radiusMeters = 6000.0;
    planet.massKg = 9.81 * planet.radiusMeters * planet.radiusMeters
        / vf::CelestialSystem::kGravitationalConstant;
    planet.gameplaySurfaceGravityMps2 = 9.81;
    planet.atmosphere.enabled = true;
    planet.atmosphere.heightMeters = 1100.0;
    planet.gravityInfluenceRadiusMeters = 11000.0; // legacy bubble hint only
    planet.physicsBubbleRadiusMeters = 11000.0;
    const auto planetId = system.addBody(planet);

    const glm::dvec3 atmosphereTop{7100.0, 0.0, 0.0};
    const glm::dvec3 deepSpace{12000.0, 0.0, 0.0};
    require(system.gravityMagnitudeFromBody(*system.body(planetId), atmosphereTop) > 1.0,
        "leaving atmosphere must not delete physical gravity");
    const double expected = vf::CelestialSystem::kGravitationalConstant * planet.massKg
        / glm::dot(deepSpace, deepSpace);
    requireNear(glm::length(system.gravityAccelerationAt(deepSpace)), expected, expected * 1.0e-12,
        "gravity outside the physics bubble must remain Newtonian inverse-square");
    require(system.physicsReferenceBodyAt(deepSpace) == nullptr,
        "reference-frame bubble may end without changing the gravity law");
    require(system.gravityReferenceBodyAt(deepSpace) != nullptr,
        "gravitational dominance and reference-frame ownership are different concepts");
}

void testRotatingFrameIncludesCentrifugalAcceleration() {
    vf::CelestialSystem system;
    vf::CelestialBody planet{};
    planet.radiusMeters = 6000.0;
    planet.massKg = 9.81 * planet.radiusMeters * planet.radiusMeters
        / vf::CelestialSystem::kGravitationalConstant;
    planet.gameplaySurfaceGravityMps2 = 9.81;
    planet.gravityFalloffStartRadiusMeters = 7100.0;
    planet.gravityInfluenceRadiusMeters = 11000.0;
    planet.spinAxis = {0.0, 1.0, 0.0};
    planet.spinRateRadPerSecond = 0.005;
    const auto id = system.addBody(planet);
    const auto* stored = system.body(id);
    require(stored != nullptr, "frame planet must exist");

    vf::CelestialPhysicsFrame frame{id};
    const glm::dvec3 acceleration = frame.gravityAcceleration(system, *stored, {6000.0, 0.0, 0.0}, {});
    const double centrifugal = planet.spinRateRadPerSecond * planet.spinRateRadPerSecond * 6000.0;
    requireNear(acceleration.x, -9.81 + centrifugal, 1.0e-8,
        "rotating planet-local physics must include centrifugal acceleration rather than dragging airborne bodies");
}

void testRealSpinKeepsGroundRenderHeadingFixedForSixHours() {
    constexpr double pi = 3.14159265358979323846;
    vf::PlanetDefinition definition{};
    definition.radius = 6371000.0;
    definition.maxElevation = 0.0;
    definition.atmosphereHeight = 100000.0;

    vf::CelestialSystem system;
    vf::CelestialBody planet{};
    planet.type = vf::CelestialBodyType::Planet;
    planet.radiusMeters = definition.radius;
    planet.massKg = 5.9722e24;
    planet.gameplaySurfaceGravityMps2 = 9.80665;
    planet.gravityFalloffStartRadiusMeters = definition.radius + definition.atmosphereHeight;
    planet.gravityInfluenceRadiusMeters = definition.radius + 900000.0;
    planet.physicsBubbleRadiusMeters = definition.radius + 1300000.0;
    planet.atmosphere.enabled = true;
    planet.atmosphere.heightMeters = definition.atmosphereHeight;
    planet.spinAxis = glm::normalize(glm::dvec3{0.18, 0.97, 0.11});
    planet.spinRateRadPerSecond = 2.0 * pi / 86164.0905;
    const auto id = system.addBody(planet);

    const glm::dvec3 spawn = glm::normalize(glm::dvec3{0.72, 0.52, 0.46});
    vf::PlanetCamera camera{definition, &system, id, spawn};
    const auto* initialBody = system.body(id);
    require(initialBody != nullptr, "real-spin camera planet must exist");

    const glm::dquat initialInverse = glm::conjugate(glm::normalize(initialBody->orientation));
    const glm::dvec3 initialRenderForward = glm::normalize(initialInverse * camera.forwardDirection());
    const glm::dvec3 initialRenderUp = glm::normalize(initialInverse * camera.up());
    const glm::dvec3 initialLocalPosition = initialInverse * (camera.position() - initialBody->position);

    // Main.cpp advances celestial time first, then updates the camera. Reproduce that exact order
    // for six simulated hours at one-minute celestial steps. A grounded observer should see the
    // landscape remain fixed while the inertial body orientation changes by roughly a quarter turn.
    for (int minute = 0; minute < 360; ++minute) {
        system.step(60.0);
        camera.update({}, 1.0 / 120.0);

        const auto* body = system.body(id);
        require(body != nullptr, "real-spin camera planet disappeared");
        const glm::dquat inverse = glm::conjugate(glm::normalize(body->orientation));
        const glm::dvec3 renderForward = glm::normalize(inverse * camera.forwardDirection());
        const glm::dvec3 renderUp = glm::normalize(inverse * camera.up());
        const glm::dvec3 localPosition = inverse * (camera.position() - body->position);

        require(glm::dot(initialRenderForward, renderForward) > 0.999999999,
            "Main render-frame forward must stay fixed for a grounded observer while the planet spins");
        require(glm::dot(initialRenderUp, renderUp) > 0.999999999,
            "Main render-frame up must stay fixed for a grounded observer while the planet spins");
        require(glm::length(localPosition - initialLocalPosition) < 1.0e-5,
            "grounded observer must not drift in body-local position during real spin integration");
    }

    const auto* finalBody = system.body(id);
    require(finalBody != nullptr, "real-spin camera planet must still exist after integration");
    require(std::abs(glm::dot(initialBody->orientation, finalBody->orientation)) < 0.95,
        "six simulated hours must produce a substantial physical planet self-rotation");
}

void testRealSpinLeavesHighAltitudeViewInertialInsidePhysicsBubble() {
    constexpr double pi = 3.14159265358979323846;
    vf::PlanetDefinition definition{};
    definition.radius = 6371000.0;
    definition.maxElevation = 0.0;
    definition.atmosphereHeight = 100000.0;

    vf::CelestialSystem system;
    vf::CelestialBody planet{};
    planet.type = vf::CelestialBodyType::Planet;
    planet.radiusMeters = definition.radius;
    planet.massKg = 5.9722e24;
    planet.gameplaySurfaceGravityMps2 = 9.80665;
    planet.gravityFalloffStartRadiusMeters = definition.radius + definition.atmosphereHeight;
    planet.gravityInfluenceRadiusMeters = definition.radius + 900000.0;
    planet.physicsBubbleRadiusMeters = definition.radius + 1300000.0;
    planet.atmosphere.enabled = true;
    planet.atmosphere.heightMeters = definition.atmosphereHeight;
    planet.spinAxis = glm::normalize(glm::dvec3{-0.21, 0.94, 0.27});
    planet.spinRateRadPerSecond = 2.0 * pi / 86164.0905;
    const auto id = system.addBody(planet);

    const glm::dvec3 radial = glm::normalize(glm::dvec3{0.63, 0.44, 0.64});
    vf::PlanetCamera camera{definition, &system, id, radial};
    vf::PlanetMovementInput toggle{};
    toggle.toggleFlight = true;
    camera.update(toggle, 1.0 / 60.0);

    const auto* body = system.body(id);
    require(body != nullptr, "high-altitude real-spin planet must exist");
    vf::CelestialPhysicsFrame frame{id};
    const glm::dvec3 localHigh = radial * (definition.radius + 400000.0);
    camera.setExternalWorldState(
        frame.toWorldPosition(*body, localHigh),
        frame.toWorldVelocity(*body, localHigh, {}),
        false);
    camera.update({}, 1.0 / 120.0);
    require(camera.inPlanetPhysicsFrame(),
        "400 km observer must remain inside the precision physics bubble for this integration test");

    const glm::dvec3 initialWorldForward = camera.forwardDirection();
    const glm::dvec3 initialWorldUp = camera.up();
    for (int minute = 0; minute < 360; ++minute) {
        system.step(60.0);
        camera.update({}, 1.0 / 120.0);
        require(glm::dot(initialWorldForward, camera.forwardDirection()) > 0.999999999,
            "high-altitude forward must remain inertial while the body rotates inside the precision bubble");
        require(glm::dot(initialWorldUp, camera.up()) > 0.999999999,
            "high-altitude up must remain inertial while the body rotates inside the precision bubble");
    }
}

} // namespace

int main() {
    testWorldLocalRoundTripPreservesState();
    testSurfaceRestIsZeroLocalVelocity();
    testPhysicalGravityPersistsOutsideReferenceBubble();
    testRotatingFrameIncludesCentrifugalAcceleration();
    testRealSpinKeepsGroundRenderHeadingFixedForSixHours();
    testRealSpinLeavesHighAltitudeViewInertialInsidePhysicsBubble();
    std::cout << "vf_celestial_physics_frame_tests: PASS\n";
    return 0;
}
