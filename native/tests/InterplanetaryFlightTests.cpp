#include "vf/player/PlanetCamera.hpp"
#include "vf/world/CelestialSystem.hpp"
#include "vf/world/PlanetSurface.hpp"

#include <algorithm>
#include <cmath>
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
    home.physicsBubbleRadiusMeters = 240.0;
    const auto homeId = celestial.addBody(home);

    vf::CelestialBody destination{};
    destination.name = "Destination";
    destination.radiusMeters = 30.0;
    destination.position = {600.0, 0.0, 0.0};
    destination.massKg = 2.0 * destination.radiusMeters * destination.radiusMeters
        / vf::CelestialSystem::kGravitationalConstant;
    destination.gameplaySurfaceGravityMps2 = 2.0;
    destination.gravityInfluenceRadiusMeters = 120.0;
    const auto destinationId = celestial.addBody(destination);
    require(destinationId != 0U, "destination body must be registered");

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

    vf::PlanetMovementInput rise{};
    rise.vertical = 1.0;
    rise.sprint = true;
    for (int i = 0; i < 20; ++i) camera.update(rise, 1.0 / 60.0);
    require(camera.altitude() > 15.0, "creative flight Space must quickly clear the surface");

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

void testCreativeFlightCanLandOnSolidGround() {
    vf::PlanetDefinition terrain{};
    terrain.radius = 100.0;
    terrain.maxElevation = 0.0;
    terrain.atmosphereHeight = 20.0;

    vf::CelestialSystem celestial;
    vf::CelestialBody planet{};
    planet.radiusMeters = terrain.radius;
    planet.massKg = 9.81 * terrain.radius * terrain.radius
        / vf::CelestialSystem::kGravitationalConstant;
    planet.gameplaySurfaceGravityMps2 = 9.81;
    planet.gravityInfluenceRadiusMeters = 300.0;
    planet.physicsBubbleRadiusMeters = 400.0;
    const auto planetId = celestial.addBody(planet);

    vf::PlanetCamera camera{terrain, &celestial, planetId};
    vf::PlanetMovementInput toggle{};
    toggle.toggleFlight = true;
    camera.update(toggle, 1.0 / 60.0);
    require(camera.flightMode(), "creative landing test must enter flight mode");

    vf::PlanetMovementInput rise{};
    rise.vertical = 1.0;
    for (int i = 0; i < 24; ++i) camera.update(rise, 1.0 / 60.0);
    require(camera.altitude() > 10.0, "landing test must first leave the surface");

    vf::PlanetMovementInput descend{};
    descend.vertical = -1.0;
    for (int i = 0; i < 120; ++i) camera.update(descend, 1.0 / 60.0);
    require(camera.altitude() >= 1.749 && camera.altitude() <= 1.755,
        "creative Ctrl descent must stop at the physical eye-height surface instead of tunnelling through the planet");

    toggle.toggleFlight = true;
    camera.update(toggle, 1.0 / 60.0);
    require(!camera.flightMode(), "second double-space event must leave creative flight after landing");

    vf::PlanetMovementInput idle{};
    camera.update(idle, 1.0 / 60.0);
    require(camera.grounded(),
        "leaving creative flight while touching ground must transition immediately to Grounded");
}

void testPlanetaryPhysicsReferenceIsIndependentFromGravity() {
    vf::CelestialSystem celestial;

    vf::CelestialBody home{};
    home.radiusMeters = 100.0;
    home.massKg = 9.0 * 100.0 * 100.0 / vf::CelestialSystem::kGravitationalConstant;
    home.gameplaySurfaceGravityMps2 = 9.0;
    home.gravityFalloffStartRadiusMeters = 130.0;
    home.gravityFalloffPower = 8.0;
    home.gravityInfluenceRadiusMeters = 280.0;
    home.physicsBubbleRadiusMeters = 420.0;
    const auto homeId = celestial.addBody(home);

    vf::CelestialBody destination{};
    destination.radiusMeters = 60.0;
    destination.position = {900.0, 0.0, 0.0};
    destination.massKg = 3.0 * 60.0 * 60.0 / vf::CelestialSystem::kGravitationalConstant;
    destination.gameplaySurfaceGravityMps2 = 3.0;
    destination.gravityInfluenceRadiusMeters = 180.0;
    destination.physicsBubbleRadiusMeters = 250.0;
    const auto destinationId = celestial.addBody(destination);

    const auto* nearHome = celestial.physicsReferenceBodyAt({180.0, 0.0, 0.0});
    const auto* zeroGButStillLocal = celestial.physicsReferenceBodyAt({350.0, 0.0, 0.0});
    const auto* between = celestial.physicsReferenceBodyAt({500.0, 0.0, 0.0});
    const auto* nearDestination = celestial.physicsReferenceBodyAt({840.0, 0.0, 0.0});

    require(nearHome != nullptr && nearHome->id == homeId,
        "home planet must own its nearby precision physics space");
    require(zeroGButStillLocal != nullptr && zeroGButStillLocal->id == homeId,
        "a precision physics bubble may extend beyond the planet's gravity cutoff");
    require(celestial.gravityReferenceBodyAt({350.0, 0.0, 0.0}) == nullptr,
        "zero-g inside a physics bubble must not still be labelled as planetary gravity");
    require(between == nullptr,
        "interplanetary space outside every physics bubble must use inertial world simulation");
    require(nearDestination != nullptr && nearDestination->id == destinationId,
        "destination planet must independently own its nearby physics space");
}

void testGroundedPlayerHasNoOrbitalFrameJitter() {
    vf::PlanetDefinition terrain{};
    terrain.radius = 100.0;
    terrain.maxElevation = 0.0;
    terrain.atmosphereHeight = 30.0;

    vf::CelestialSystem celestial;
    vf::CelestialBody star{};
    star.type = vf::CelestialBodyType::Star;
    star.radiusMeters = 50.0;
    star.massKg = 2.0e16;
    const auto starId = celestial.addBody(star);

    vf::CelestialBody planet{};
    planet.name = "MovingHome";
    planet.radiusMeters = terrain.radius;
    planet.massKg = 9.81 * planet.radiusMeters * planet.radiusMeters
        / vf::CelestialSystem::kGravitationalConstant;
    planet.gameplaySurfaceGravityMps2 = 9.81;
    planet.gravityInfluenceRadiusMeters = 500.0;
    planet.physicsBubbleRadiusMeters = 650.0;
    planet.position = {1000.0, 0.0, 0.0};
    planet.linearVelocity = {0.0, 0.0,
        std::sqrt(vf::CelestialSystem::kGravitationalConstant * star.massKg / 1000.0)};
    planet.orbitParentId = starId;
    planet.spinAxis = {0.0, 1.0, 0.0};
    planet.spinRateRadPerSecond = 0.02;
    const auto planetId = celestial.addBody(planet);

    vf::PlanetCamera camera{terrain, &celestial, planetId};
    const auto* initialPlanet = celestial.body(planetId);
    require(initialPlanet != nullptr, "grounded jitter test planet must exist");
    const glm::dvec3 initialLocal = glm::conjugate(glm::normalize(initialPlanet->orientation))
        * (camera.position() - initialPlanet->position);
    const glm::dvec3 initialLocalDirection = glm::normalize(initialLocal);

    vf::PlanetMovementInput idle{};
    double minAltitude = 1.0e30;
    double maxAltitude = -1.0e30;
    double maxDirectionError = 0.0;
    constexpr double dt = 1.0 / 60.0;

    for (int frame = 0; frame < 360; ++frame) {
        celestial.step(dt);
        camera.update(idle, dt);
        if (frame < 180) continue;

        const auto* movingPlanet = celestial.body(planetId);
        require(movingPlanet != nullptr, "moving home planet must remain valid");
        const glm::dvec3 local = glm::conjugate(glm::normalize(movingPlanet->orientation))
            * (camera.position() - movingPlanet->position);
        const double altitude = glm::length(local) - terrain.radius;
        minAltitude = std::min(minAltitude, altitude);
        maxAltitude = std::max(maxAltitude, altitude);
        maxDirectionError = std::max(
            maxDirectionError,
            glm::length(glm::normalize(local) - initialLocalDirection));
    }

    require(camera.grounded(),
        "idle player must remain grounded while the planet simultaneously orbits and rotates");
    require(maxAltitude - minAltitude < 0.005,
        "grounded player eye height must not oscillate from orbital-frame correction jitter");
    require(std::abs(0.5 * (maxAltitude + minAltitude) - 1.75) < 0.01,
        "grounded player must remain at the configured eye height over the moving planet");
    require(maxDirectionError < 1.0e-5,
        "idle player must remain over the same local surface patch instead of lagging behind the moving planet");
}

void testZeroGInsidePhysicsBubbleCannotWalkAroundPlanet() {
    vf::PlanetDefinition terrain{};
    terrain.radius = 100.0;
    terrain.maxElevation = 0.0;
    terrain.atmosphereHeight = 20.0;

    vf::CelestialSystem celestial;
    vf::CelestialBody planet{};
    planet.radiusMeters = terrain.radius;
    planet.massKg = 9.81 * 100.0 * 100.0 / vf::CelestialSystem::kGravitationalConstant;
    planet.gameplaySurfaceGravityMps2 = 9.81;
    planet.atmosphere.enabled = true;
    planet.atmosphere.heightMeters = terrain.atmosphereHeight;
    planet.gravityFalloffStartRadiusMeters = 120.0;
    planet.gravityFalloffPower = 10.0;
    planet.gravityInfluenceRadiusMeters = 180.0;
    planet.physicsBubbleRadiusMeters = 500.0;
    const auto planetId = celestial.addBody(planet);

    vf::PlanetCamera camera{terrain, &celestial, planetId};
    vf::PlanetMovementInput toggle{};
    toggle.toggleFlight = true;
    camera.update(toggle, 1.0 / 60.0);

    // Use ordinary creative speed and stop while still inside the intentionally larger precision
    // bubble. The previous regression accidentally flew past the 500 m bubble before asserting it.
    vf::PlanetMovementInput rise{};
    rise.vertical = 1.0;
    for (int i = 0; i < 30; ++i) camera.update(rise, 1.0 / 60.0);
    vf::PlanetMovementInput idle{};
    for (int i = 0; i < 45; ++i) camera.update(idle, 1.0 / 60.0);

    require(camera.altitude() > 85.0,
        "test player must reach the zero-g region above the authored gravity cutoff");
    require(camera.inPlanetPhysicsFrame(),
        "zero-g player may remain in the planet precision bubble without being surface-bound");

    toggle.toggleFlight = true;
    camera.update(toggle, 1.0 / 60.0);
    require(!camera.flightMode() && !camera.grounded(),
        "turning off creative flight in near space must produce an airborne/free-flight state");

    const auto* body = celestial.body(planetId);
    require(body != nullptr, "zero-g test planet must exist");
    const glm::dvec3 beforeLocal = glm::conjugate(glm::normalize(body->orientation))
        * (camera.position() - body->position);
    const glm::dvec3 beforeDirection = glm::normalize(beforeLocal);

    vf::PlanetMovementInput forward{};
    forward.forward = 1.0;
    for (int i = 0; i < 120; ++i) camera.update(forward, 1.0 / 60.0);

    const glm::dvec3 afterLocal = glm::conjugate(glm::normalize(body->orientation))
        * (camera.position() - body->position);
    require(glm::length(glm::normalize(afterLocal) - beforeDirection) < 1.0e-4,
        "W input in zero-g must not become spherical surface walking merely because a planet physics frame is active");
}

} // namespace

int main() {
    testCreativeFlightIsExplicitAndGravityIndependent();
    testCreativeFlightCanLandOnSolidGround();
    testPlanetaryPhysicsReferenceIsIndependentFromGravity();
    testGroundedPlayerHasNoOrbitalFrameJitter();
    testZeroGInsidePhysicsBubbleCannotWalkAroundPlanet();
    std::cout << "vf_interplanetary_flight_tests: PASS\n";
    return 0;
}
