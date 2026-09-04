#include "vf/player/PlanetCamera.hpp"

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
    const double beforeVertical = glm::dot(camera.forwardDirection(), camera.up());
    vf::PlanetMovementInput input{};
    input.mouseDy = 100.0;
    camera.update(input, 1.0 / 60.0);
    require(glm::dot(camera.forwardDirection(), camera.up()) < beforeVertical,
        "positive SDL mouse Y must pitch the view downward");
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

void testPlanetToSpaceAttitudeIsContinuous() {
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
    toggle.flightSpeedSteps = 8.0; // 5120 m/s inspection escape for a tiny test planet.
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
            break;
        }
        previousForward = camera.forwardDirection();
        previousUp = camera.up();
    }
    require(leftFrame, "test camera must actually cross the authored planet physics bubble");
}

} // namespace

int main() {
    testMouseRightTurnsCameraRight();
    testMouseLeftTurnsCameraLeft();
    testVerticalMouseDirectionRemainsConventional();
    testFlightSpeedUsesLogarithmicWheelSteps();
    testDMovesToCameraRightInFlight();
    testAMovesToCameraLeftInFlight();
    testPlanetToSpaceAttitudeIsContinuous();
    std::cout << "vf_camera_input_tests: PASS\n";
    return 0;
}
