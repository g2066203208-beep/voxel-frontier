#include "vf/physics/PhysicsWorld.hpp"
#include "vf/player/PlanetCamera.hpp"
#include "vf/world/TerrainStreamingPolicy.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "R24 RUNTIME STABILITY TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

vf::PhysicsEnvironment inertialTestEnvironment() {
    vf::PhysicsEnvironment environment{};
    environment.planet.radius = 1000.0;
    environment.planet.maxElevation = 0.0;
    environment.surfaceGravity = 0.0;
    environment.atmosphere.seaLevelPressurePa = 0.0;
    environment.atmosphere.pressureScale = 0.0;
    environment.ocean.enabled = false;
    return environment;
}

vf::RigidBodyDesc testBody(const glm::dvec3& position, const glm::dvec3& velocity = {}) {
    vf::RigidBodyDesc body{};
    body.position = position;
    body.linearVelocity = velocity;
    body.mass = 1.0;
    body.collisionShape = vf::CollisionShape::sphere(0.1);
    body.linearDamping = 0.0;
    body.angularDamping = 0.0;
    body.aerodynamics.referenceArea = 0.0;
    return body;
}


void testCreativeFlightConfigurationUsesProductionLimits() {
    vf::PlanetDefinition planet{};
    planet.radius = 1000.0;
    planet.maxElevation = 0.0;
    vf::PlanetCamera camera{planet};
    camera.setFlightMode(true);
    camera.setCreativeFlightSpeedMps(500000.0);
    require(camera.flightMode(), "runtime/editor flight configuration must enable the production flight path");
    require(!camera.grounded(), "enabling flight must release the grounded state");
    require(std::abs(camera.flightSpeedMps() - 500000.0) < 1.0e-9,
        "configured high-speed capture must use the same production speed value");
    camera.setCreativeFlightSpeedMps(9.0e9);
    require(std::abs(camera.flightSpeedMps() - 2000000.0) < 1.0e-9,
        "runtime/editor speed configuration must preserve the production 2,000 km/s clamp");
}

void testCentrifugalAccelerationInRotatingLocalWorld() {
    auto environment = inertialTestEnvironment();
    environment.rotatingFrameAngularVelocity = {0.0, 0.0, 1.0};
    vf::PhysicsWorld world{environment};
    const auto id = world.createRigidBody(testBody({10.0, 0.0, 0.0}));
    world.stepFixed();
    const auto* body = world.body(id);
    require(body != nullptr, "centrifugal test body missing");
    require(body->linearVelocity.x > 0.08,
        "rotating local physics must apply outward centrifugal acceleration");
}

void testCoriolisAccelerationInRotatingLocalWorld() {
    auto environment = inertialTestEnvironment();
    environment.rotatingFrameAngularVelocity = {0.0, 0.0, 1.0};
    vf::PhysicsWorld world{environment};
    const auto id = world.createRigidBody(testBody({0.0, 0.0, 0.0}, {1.0, 0.0, 0.0}));
    world.stepFixed();
    const auto* body = world.body(id);
    require(body != nullptr, "coriolis test body missing");
    require(body->linearVelocity.y < -0.015,
        "positive-X local motion under positive-Z spin must receive negative-Y Coriolis acceleration");
}

void testHighSpeedTransitForcesCheapGlobeAndNoBuild() {
    const auto decision = vf::decideTerrainStreaming({
        true, 5000.0, 250000.0, 20000.0, false, 0.0});
    require(decision.useDistantGlobe,
        "high-speed low-altitude transit must fall back to the cheap globe");
    require(!decision.requestBuild,
        "high-speed transit must not start an expensive near-field rebuild");
}

void testSlowSurfaceTravelPrefetchesBeforeWindowExpires() {
    const auto decision = vf::decideTerrainStreaming({
        true, 5000.0, 45.0, 4200.0, false, 0.0});
    require(decision.detailedSurfaceEligible, "normal walking/driving speeds must retain detailed terrain");
    require(decision.currentWindowUsable, "prefetch must begin while the existing window is still usable");
    require(decision.requestBuild, "slow travel beyond prefetch threshold must request one rebuild");
    require(!decision.useDistantGlobe, "usable detailed window must stay visible during background prefetch");
}

void testStaleWindowFallsBackUntilFreshBuildArrives() {
    const auto decision = vf::decideTerrainStreaming({
        true, 8000.0, 120.0, 9000.0, true, 0.0});
    require(decision.useDistantGlobe,
        "camera beyond the safe detailed window must render the globe while a replacement builds");
    require(!decision.requestBuild,
        "only one terrain build may be in flight at a time");
    require(decision.staleAcceptanceMeters >= decision.recenterThresholdMeters,
        "stale acceptance must be wider than the normal recenter window");
}

} // namespace

int main() {
    testCreativeFlightConfigurationUsesProductionLimits();
    testCentrifugalAccelerationInRotatingLocalWorld();
    testCoriolisAccelerationInRotatingLocalWorld();
    testHighSpeedTransitForcesCheapGlobeAndNoBuild();
    testSlowSurfaceTravelPrefetchesBeforeWindowExpires();
    testStaleWindowFallsBackUntilFreshBuildArrives();
    std::cout << "vf_r24_runtime_stability_tests: PASS\n";
    return 0;
}
