#include "vf/player/PlanetCamera.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "CAMERA INPUT TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

[[nodiscard]] glm::dvec3 tangentForward(const vf::PlanetCamera& camera) {
    const glm::dvec3 up = camera.up();
    const glm::dvec3 forward = camera.forwardDirection();
    return glm::normalize(forward - up * glm::dot(forward, up));
}

void testMouseRightTurnsCameraRight() {
    const vf::PlanetDefinition planet{};
    vf::PlanetCamera camera{planet};
    const glm::dvec3 before = tangentForward(camera);
    const glm::dvec3 right = glm::normalize(glm::cross(before, camera.up()));
    vf::PlanetMovementInput input{};
    input.mouseDx = 100.0;
    camera.update(input, 1.0 / 60.0);
    require(glm::dot(tangentForward(camera), right) > 0.1,
        "positive camera mouse X must rotate view toward camera-right");
}

void testMouseLeftTurnsCameraLeft() {
    const vf::PlanetDefinition planet{};
    vf::PlanetCamera camera{planet};
    const glm::dvec3 before = tangentForward(camera);
    const glm::dvec3 right = glm::normalize(glm::cross(before, camera.up()));
    vf::PlanetMovementInput input{};
    input.mouseDx = -100.0;
    camera.update(input, 1.0 / 60.0);
    require(glm::dot(tangentForward(camera), right) < -0.1,
        "negative camera mouse X must rotate view toward camera-left");
}

void testVerticalMouseDirectionRemainsConventional() {
    const vf::PlanetDefinition planet{};
    vf::PlanetCamera camera{planet};
    const glm::dvec3 physicalUpBefore = glm::normalize(camera.position());
    const double beforeVertical = glm::dot(camera.forwardDirection(), physicalUpBefore);
    vf::PlanetMovementInput input{};
    input.mouseDy = 100.0;
    camera.update(input, 1.0 / 60.0);
    const glm::dvec3 physicalUpAfter = glm::normalize(camera.position());
    require(glm::dot(camera.forwardDirection(), physicalUpAfter) < beforeVertical,
        "positive SDL mouse Y must pitch the view downward relative to the physical horizon");
}

void testFlightSpeedUsesLogarithmicWheelSteps() {
    const vf::PlanetDefinition planet{};
    vf::PlanetCamera camera{planet};
    const double before = camera.flightSpeedMps();
    vf::PlanetMovementInput input{};
    input.flightSpeedSteps = 2.0;
    camera.update(input, 1.0 / 60.0);
    require(camera.flightSpeedMps() > before * 1.99 && camera.flightSpeedMps() < before * 2.01,
        "two positive wheel steps must double creative flight speed");

    input = {};
    input.flightSpeedSteps = -40.0;
    camera.update(input, 1.0 / 60.0);
    require(camera.flightSpeedMps() >= 0.999 && camera.flightSpeedMps() <= 1.001,
        "creative flight must allow a 1 m/s inspection speed without going below it");
}

void testDMovesToCameraRightInFlight() {
    const vf::PlanetDefinition planet{};
    vf::PlanetCamera camera{planet};
    vf::PlanetMovementInput toggle{};
    toggle.toggleFlight = true;
    camera.update(toggle, 1.0 / 60.0);

    const glm::dvec3 start = camera.position();
    const glm::dvec3 right = glm::normalize(glm::cross(camera.forwardDirection(), camera.up()));
    vf::PlanetMovementInput d{};
    d.right = 1.0;
    for (int i = 0; i < 12; ++i) camera.update(d, 1.0 / 60.0);
    require(glm::dot(camera.position() - start, right) > 1.0,
        "D / positive-right input must move in camera-right direction");
}

void testAMovesToCameraLeftInFlight() {
    const vf::PlanetDefinition planet{};
    vf::PlanetCamera camera{planet};
    vf::PlanetMovementInput toggle{};
    toggle.toggleFlight = true;
    camera.update(toggle, 1.0 / 60.0);

    const glm::dvec3 start = camera.position();
    const glm::dvec3 right = glm::normalize(glm::cross(camera.forwardDirection(), camera.up()));
    vf::PlanetMovementInput a{};
    a.right = -1.0;
    for (int i = 0; i < 12; ++i) camera.update(a, 1.0 / 60.0);
    require(glm::dot(camera.position() - start, right) < -1.0,
        "A / negative-right input must move in camera-left direction");
}

void testHighLatitudeTravelDoesNotRebuildHeadingBasis() {
    vf::PlanetDefinition planet{};
    planet.radius = 1000.0;
    planet.maxElevation = 0.0;
    planet.atmosphereHeight = 100.0;
    vf::PlanetCamera camera{planet};

    auto moveToLatitude = [&](double degrees) {
        const double radians = degrees * 3.14159265358979323846 / 180.0;
        const glm::dvec3 direction{std::cos(radians), std::sin(radians), 0.0};
        camera.setExternalWorldState(direction * (planet.radius + 1.75), {}, true);
        camera.update({}, 1.0 / 60.0);
        return camera.forwardDirection();
    };

    glm::dvec3 previous = moveToLatitude(64.0);
    for (double latitude : {65.0, 66.0, 67.0, 68.0, 69.0, 70.0}) {
        const glm::dvec3 current = moveToLatitude(latitude);
        require(glm::dot(previous, current) > 0.995,
            "surface travel through the old high-latitude basis switch must not spin the camera");
        previous = current;
    }
}

void testPlanetToSpaceAttitudeIsContinuousAndMouseXKeepsDirection() {
    vf::PlanetDefinition planet{};
    planet.radius = 1000.0;
    planet.maxElevation = 0.0;
    planet.atmosphereHeight = 80.0;

    vf::CelestialSystem system;
    vf::CelestialBody body{};
    body.type = vf::CelestialBodyType::Planet;
    body.radiusMeters = planet.radius;
    body.massKg = 5.0e15;
    body.gameplaySurfaceGravityMps2 = 9.81;
    body.gravityFalloffStartRadiusMeters = 1080.0;
    body.gravityInfluenceRadiusMeters = 1120.0;
    body.physicsBubbleRadiusMeters = 1120.0;
    body.atmosphere.enabled = true;
    body.atmosphere.heightMeters = 80.0;
    const std::uint32_t id = system.addBody(body);

    vf::PlanetCamera camera{planet, &system, id};
    vf::PlanetMovementInput toggle{};
    toggle.toggleFlight = true;
    toggle.flightSpeedSteps = 8.0;
    camera.update(toggle, 1.0 / 60.0);

    glm::dvec3 previousForward = camera.forwardDirection();
    glm::dvec3 previousUp = camera.up();
    bool leftFrame = false;
    for (int i = 0; i < 40; ++i) {
        vf::PlanetMovementInput climb{};
        climb.vertical = 1.0;
        camera.update(climb, 1.0 / 120.0);
        if (!camera.inPlanetPhysicsFrame()) {
            leftFrame = true;
            require(glm::dot(previousForward, camera.forwardDirection()) > 0.999,
                "leaving the planet physics frame must preserve forward viewing attitude");
            require(glm::dot(previousUp, camera.up()) > 0.999,
                "leaving the planet physics frame must preserve camera up without a global-Y snap");

            const glm::dvec3 spaceForward = camera.forwardDirection();
            const glm::dvec3 spaceRight = glm::normalize(glm::cross(spaceForward, camera.up()));

            vf::PlanetMovementInput lookRight{};
            lookRight.mouseDx = 100.0;
            camera.update(lookRight, 1.0 / 60.0);
            require(glm::dot(camera.forwardDirection(), spaceRight) > 0.1,
                "positive mouse X must still rotate camera-right after entering inertial space");

            vf::PlanetMovementInput lookLeft{};
            lookLeft.mouseDx = -200.0;
            camera.update(lookLeft, 1.0 / 60.0);
            require(glm::dot(camera.forwardDirection(), spaceRight) < -0.1,
                "negative mouse X must still rotate camera-left after entering inertial space");
            break;
        }
        previousForward = camera.forwardDirection();
        previousUp = camera.up();
    }
    require(leftFrame, "test camera must actually cross the authored planet physics bubble");
}

void testSpaceReentryDoesNotSnapAtPhysicsFrameBoundary() {
    vf::PlanetDefinition planet{};
    planet.radius = 6371000.0;
    planet.maxElevation = 0.0;
    planet.atmosphereHeight = 100000.0;

    vf::CelestialSystem system;
    vf::CelestialBody body{};
    body.type = vf::CelestialBodyType::Planet;
    body.radiusMeters = planet.radius;
    body.massKg = 5.9722e24;
    body.gameplaySurfaceGravityMps2 = 9.80665;
    body.gravityFalloffStartRadiusMeters = planet.radius + planet.atmosphereHeight;
    body.gravityInfluenceRadiusMeters = planet.radius + 900000.0;
    body.physicsBubbleRadiusMeters = planet.radius + 1300000.0;
    body.atmosphere.enabled = true;
    body.atmosphere.heightMeters = planet.atmosphereHeight;
    const std::uint32_t id = system.addBody(body);

    vf::PlanetCamera camera{planet, &system, id};
    vf::PlanetMovementInput toggle{};
    toggle.toggleFlight = true;
    camera.update(toggle, 1.0 / 60.0);

    const glm::dvec3 radial = glm::normalize(camera.position());
    camera.setExternalWorldState(radial * (planet.radius + 1500000.0), {}, false);
    camera.update({}, 1.0 / 60.0);
    require(!camera.inPlanetPhysicsFrame(), "test camera must begin re-entry from inertial space");

    vf::PlanetMovementInput tilt{};
    tilt.mouseDy = -180.0;
    tilt.mouseDx = 75.0;
    camera.update(tilt, 1.0 / 60.0);
    const glm::dvec3 beforeForward = camera.forwardDirection();
    const glm::dvec3 beforeUp = camera.up();

    camera.setExternalWorldState(radial * (planet.radius + 1200000.0), {}, false);
    camera.update({}, 1.0 / 60.0);
    require(camera.inPlanetPhysicsFrame(), "test camera must re-enter the planet physics bubble");
    require(glm::dot(beforeForward, camera.forwardDirection()) > 0.99999,
        "entering a planet physics frame at orbital altitude must not rotate forward view");
    require(glm::dot(beforeUp, camera.up()) > 0.99999,
        "entering a planet physics frame at orbital altitude must not snap camera up");

    camera.setExternalWorldState(radial * (planet.radius + 250000.0), {}, false);
    const glm::dvec3 beforeBlendUp = camera.up();
    const glm::dvec3 beforeBlendForward = camera.forwardDirection();
    glm::dvec3 desiredUp = radial - beforeBlendForward * glm::dot(radial, beforeBlendForward);
    desiredUp = glm::normalize(desiredUp);
    const double initialAlignment = glm::dot(beforeBlendUp, desiredUp);

    camera.update({}, 1.0 / 60.0);
    require(glm::dot(beforeBlendUp, camera.up()) > 0.995,
        "first atmospheric horizon-alignment frame must be gradual rather than a landing snap");

    for (int i = 0; i < 180; ++i) camera.update({}, 1.0 / 60.0);
    const glm::dvec3 finalForward = camera.forwardDirection();
    glm::dvec3 finalDesiredUp = radial - finalForward * glm::dot(radial, finalForward);
    finalDesiredUp = glm::normalize(finalDesiredUp);
    require(glm::dot(camera.up(), finalDesiredUp) > initialAlignment + 0.05,
        "descending into the atmosphere must smoothly converge camera up toward the local horizon");
}

} // namespace

int main() {
    testMouseRightTurnsCameraRight();
    testMouseLeftTurnsCameraLeft();
    testVerticalMouseDirectionRemainsConventional();
    testFlightSpeedUsesLogarithmicWheelSteps();
    testDMovesToCameraRightInFlight();
    testAMovesToCameraLeftInFlight();
    testHighLatitudeTravelDoesNotRebuildHeadingBasis();
    testPlanetToSpaceAttitudeIsContinuousAndMouseXKeepsDirection();
    testSpaceReentryDoesNotSnapAtPhysicsFrameBoundary();
    std::cout << "vf_camera_input_tests: PASS\n";
    return 0;
}
