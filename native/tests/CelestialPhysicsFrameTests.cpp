#include "vf/world/CelestialPhysicsFrame.hpp"
#include "vf/world/CelestialSystem.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

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

void testFiniteGravityBecomesZeroWithoutWaitingForAnotherPlanet() {
    vf::CelestialSystem system;
    vf::CelestialBody planet{};
    planet.radiusMeters = 6000.0;
    planet.massKg = 9.81 * planet.radiusMeters * planet.radiusMeters
        / vf::CelestialSystem::kGravitationalConstant;
    planet.gameplaySurfaceGravityMps2 = 9.81;
    planet.atmosphere.enabled = true;
    planet.atmosphere.heightMeters = 1100.0;
    planet.gravityFalloffStartRadiusMeters = 7100.0;
    planet.gravityFalloffPower = 10.0;
    planet.gravityCutoffAccelerationMps2 = 0.05;
    planet.gravityInfluenceRadiusMeters = 11000.0;
    const auto planetId = system.addBody(planet);
    (void)planetId;

    const glm::dvec3 atmosphereTop{7100.0, 0.0, 0.0};
    const glm::dvec3 deepSpace{12000.0, 0.0, 0.0};
    require(system.gravityMagnitudeFromBody(*system.body(planetId), atmosphereTop) > 1.0,
        "leaving atmosphere must not unrealistically delete gravity at the exact atmosphere boundary");
    requireNear(glm::length(system.gravityAccelerationAt(deepSpace)), 0.0, 1.0e-12,
        "planet gravity must become true zero beyond its finite gameplay gravity well");
    require(system.gravityReferenceBodyAt(deepSpace) == nullptr,
        "zero-g space must not remain owned by the old planet gravity state");
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

} // namespace

int main() {
    testWorldLocalRoundTripPreservesState();
    testSurfaceRestIsZeroLocalVelocity();
    testFiniteGravityBecomesZeroWithoutWaitingForAnotherPlanet();
    testRotatingFrameIncludesCentrifugalAcceleration();
    std::cout << "vf_celestial_physics_frame_tests: PASS\n";
    return 0;
}
