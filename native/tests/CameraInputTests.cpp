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

    const glm::dvec3 after = tangentForward(camera);
    require(glm::dot(after, right) > 0.1,
        "positive SDL mouse X must rotate the view toward camera-right");
}

void testMouseLeftTurnsCameraLeft() {
    const vf::PlanetDefinition planet{};
    vf::PlanetCamera camera{planet};

    const glm::dvec3 before = tangentForward(camera);
    const glm::dvec3 right = glm::normalize(glm::cross(before, camera.up()));

    vf::PlanetMovementInput input{};
    input.mouseDx = -100.0;
    camera.update(input, 1.0 / 60.0);

    const glm::dvec3 after = tangentForward(camera);
    require(glm::dot(after, right) < -0.1,
        "negative SDL mouse X must rotate the view toward camera-left");
}

void testVerticalMouseDirectionRemainsConventional() {
    const vf::PlanetDefinition planet{};
    vf::PlanetCamera camera{planet};
    const double beforeVertical = glm::dot(camera.forwardDirection(), camera.up());

    vf::PlanetMovementInput input{};
    input.mouseDy = 100.0;
    camera.update(input, 1.0 / 60.0);

    const double afterVertical = glm::dot(camera.forwardDirection(), camera.up());
    require(afterVertical < beforeVertical,
        "positive SDL mouse Y (mouse down) must pitch the view downward");
}

} // namespace

int main() {
    testMouseRightTurnsCameraRight();
    testMouseLeftTurnsCameraLeft();
    testVerticalMouseDirectionRemainsConventional();
    std::cout << "vf_camera_input_tests: PASS\n";
    return 0;
}
