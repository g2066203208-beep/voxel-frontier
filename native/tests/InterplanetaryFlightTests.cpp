#include "vf/player/PlanetCamera.hpp"
#include "vf/world/CelestialSystem.hpp"
#include "vf/world/PlanetSurface.hpp"

#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "INTERPLANETARY FLIGHT TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void testCameraEscapesSurfaceControllerIntoInertialFlight() {
    vf::PlanetDefinition terrain{};
    terrain.radius = 50.0;
    terrain.maxElevation = 0.0;
    terrain.atmosphereHeight = 30.0;

    vf::CelestialSystem celestial;
    vf::CelestialBody home{};
    home.name = "Home";
    home.radiusMeters = terrain.radius;
    home.massKg = 5.0 * home.radiusMeters * home.radiusMeters
        / vf::CelestialSystem::kGravitationalConstant;
    home.gameplaySurfaceGravityMps2 = 5.0;
    home.gravityInfluenceRadiusMeters = 180.0;
    home.atmosphere.enabled = false;
    const auto homeId = celestial.addBody(home);

    vf::CelestialBody destination{};
    destination.name = "Destination";
    destination.radiusMeters = 30.0;
    destination.position = {600.0, 0.0, 0.0};
    destination.massKg = 2.0 * destination.radiusMeters * destination.radiusMeters
        / vf::CelestialSystem::kGravitationalConstant;
    destination.gameplaySurfaceGravityMps2 = 2.0;
    destination.gravityInfluenceRadiusMeters = 120.0;
    celestial.addBody(destination);

    vf::PlanetCamera camera{terrain, &celestial, homeId};
    vf::PlanetMovementInput ascend{};
    ascend.vertical = 1.0;
    ascend.sprint = true;

    for (int i = 0; i < 180 && !camera.flightMode(); ++i) {
        camera.update(ascend, 1.0 / 60.0);
    }
    require(camera.flightMode(),
        "sustained ascent must leave the near-surface controller and enter true flight mode");
    require(camera.altitude() > 18.0,
        "flight transition must occur only after the camera has physically climbed away from the surface");

    const glm::dvec3 forwardBefore = camera.forwardDirection();
    const double forwardSpeedBefore = glm::dot(camera.velocity(), forwardBefore);

    vf::PlanetMovementInput thrust{};
    thrust.forward = 1.0;
    thrust.sprint = true;
    camera.update(thrust, 0.05);

    const double forwardSpeedAfter = glm::dot(camera.velocity(), forwardBefore);
    require(forwardSpeedAfter > forwardSpeedBefore + 5.0,
        "in flight mode W must add camera-forward inertial velocity instead of tangent-plane teleportation");
}

void testPlanetaryReferenceEndsAtSphereOfInfluence() {
    vf::CelestialSystem celestial;

    vf::CelestialBody home{};
    home.radiusMeters = 100.0;
    home.massKg = 9.0 * 100.0 * 100.0 / vf::CelestialSystem::kGravitationalConstant;
    home.gameplaySurfaceGravityMps2 = 9.0;
    home.gravityInfluenceRadiusMeters = 280.0;
    const auto homeId = celestial.addBody(home);

    vf::CelestialBody destination{};
    destination.radiusMeters = 60.0;
    destination.position = {900.0, 0.0, 0.0};
    destination.massKg = 3.0 * 60.0 * 60.0 / vf::CelestialSystem::kGravitationalConstant;
    destination.gameplaySurfaceGravityMps2 = 3.0;
    destination.gravityInfluenceRadiusMeters = 180.0;
    const auto destinationId = celestial.addBody(destination);

    const auto* nearHome = celestial.gameplayReferenceBodyAt({180.0, 0.0, 0.0});
    const auto* between = celestial.gameplayReferenceBodyAt({450.0, 0.0, 0.0});
    const auto* nearDestination = celestial.gameplayReferenceBodyAt({840.0, 0.0, 0.0});

    require(nearHome != nullptr && nearHome->id == homeId,
        "home planet must own its local gravity sphere");
    require(between == nullptr,
        "interplanetary space must not remain attached to the home planet reference frame");
    require(nearDestination != nullptr && nearDestination->id == destinationId,
        "destination planet must take over the local reference inside its own gravity sphere");
}

} // namespace

int main() {
    testCameraEscapesSurfaceControllerIntoInertialFlight();
    testPlanetaryReferenceEndsAtSphereOfInfluence();
    std::cout << "vf_interplanetary_flight_tests: PASS\n";
    return 0;
}
