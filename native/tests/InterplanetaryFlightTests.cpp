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

void testCreativeFlightIsExplicitAndGravityIndependent() {
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
    require(!camera.flightMode(), "camera must spawn with creative flight disabled");

    vf::PlanetMovementInput toggle{};
    toggle.toggleFlight = true;
    camera.update(toggle, 1.0 / 60.0);
    require(camera.flightMode(), "double-space event must enable creative flight explicitly");

    const glm::dvec3 hoverStart = camera.position();
    vf::PlanetMovementInput idle{};
    for (int i = 0; i < 180; ++i) camera.update(idle, 1.0 / 60.0);
    require(glm::length(camera.position() - hoverStart) < 0.15,
        "creative flight must bypass planetary gravity so an idle player can hover");

    const glm::dvec3 forwardBefore = camera.forwardDirection();
    vf::PlanetMovementInput thrust{};
    thrust.forward = 1.0;
    thrust.sprint = true;
    for (int i = 0; i < 30; ++i) camera.update(thrust, 1.0 / 60.0);
    require(glm::dot(camera.velocity(), forwardBefore) > 100.0,
        "creative flight W must produce strong camera-forward travel instead of a planet tangent walk");

    toggle.toggleFlight = true;
    camera.update(toggle, 1.0 / 60.0);
    require(!camera.flightMode(), "a second double-space event must disable creative flight");
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
    testCreativeFlightIsExplicitAndGravityIndependent();
    testPlanetaryReferenceEndsAtSphereOfInfluence();
    std::cout << "vf_interplanetary_flight_tests: PASS\n";
    return 0;
}
