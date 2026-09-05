#include "vf/player/CharacterController.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>

namespace {

void require(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        std::exit(1);
    }
}

vf::PhysicsWorld makeFlatWorld() {
    vf::PhysicsEnvironment environment{};
    environment.planet.radius = 1000.0;
    environment.planet.maxElevation = 0.0;
    environment.surfaceGravity = 9.80665;
    environment.atmosphere.prevailingWind = {};
    environment.atmosphere.gustAmplitude = 0.0;
    environment.weather.windMultiplier = 0.0;
    environment.ocean.enabled = false;
    return vf::PhysicsWorld{environment};
}

void settle(vf::CharacterController& controller, int steps = 120) {
    vf::CharacterControllerInput input{};
    input.forward = {0.0, 0.0, 1.0};
    input.right = {1.0, 0.0, 0.0};
    for (int i = 0; i < steps; ++i) controller.update(input, 1.0 / 120.0);
}

} // namespace

int main() {
    {
        auto world = makeFlatWorld();
        vf::CharacterController controller{world};
        controller.resetFromEye({0.0, 1001.75, 0.0}, {}, true);
        settle(controller, 240);
        require(controller.grounded(), "idle character must remain grounded");
        require(std::abs(glm::length(controller.eyePosition()) - 1001.795) < 0.09,
            "idle capsule eye height must remain stable above analytical terrain");
        require(glm::length(controller.linearVelocity()) < 0.05,
            "idle grounded capsule must not accumulate drift velocity");
    }

    {
        auto world = makeFlatWorld();
        vf::RigidBodyDesc wall{};
        wall.motionType = vf::MotionType::Static;
        wall.mass = 0.0;
        wall.position = {0.0, 1001.0, 2.2};
        wall.collisionShape = vf::CollisionShape::box({2.0, 1.0, 0.20});
        (void)world.createRigidBody(wall);

        vf::CharacterController controller{world};
        controller.resetFromEye({0.0, 1001.75, 0.0}, {}, true);
        vf::CharacterControllerInput input{};
        input.forward = {0.0, 0.0, 1.0};
        input.right = {1.0, 0.0, 0.0};
        input.forwardAxis = 1.0;
        for (int i = 0; i < 180; ++i) controller.update(input, 1.0 / 120.0);
        require(controller.centerPosition().z < 1.72,
            "capsule must stop at a wall instead of passing through it");
    }

    {
        auto world = makeFlatWorld();
        vf::CharacterController controller{world};
        controller.resetFromEye({0.0, 1001.75, 0.0}, {}, true);
        const double before = glm::length(controller.eyePosition());
        vf::CharacterControllerInput input{};
        input.forward = {0.0, 0.0, 1.0};
        input.right = {1.0, 0.0, 0.0};
        input.jump = true;
        controller.update(input, 1.0 / 120.0);
        input.jump = false;
        for (int i = 0; i < 18; ++i) controller.update(input, 1.0 / 120.0);
        require(glm::length(controller.eyePosition()) > before + 0.20,
            "jump must create measurable upward separation from terrain");
        require(!controller.grounded(), "character must be airborne during the rising part of a jump");
    }

    {
        auto world = makeFlatWorld();
        vf::RigidBodyDesc step{};
        step.motionType = vf::MotionType::Static;
        step.mass = 0.0;
        step.position = {0.0, 1000.15, 1.45};
        step.collisionShape = vf::CollisionShape::box({0.9, 0.15, 0.35});
        (void)world.createRigidBody(step);

        vf::CharacterController controller{world};
        controller.resetFromEye({0.0, 1001.75, 0.0}, {}, true);
        vf::CharacterControllerInput input{};
        input.forward = {0.0, 0.0, 1.0};
        input.right = {1.0, 0.0, 0.0};
        input.forwardAxis = 1.0;
        for (int i = 0; i < 150; ++i) controller.update(input, 1.0 / 120.0);
        require(controller.centerPosition().z > 1.9,
            "controller must negotiate a 0.30 m step below the configured step height");
    }

    {
        // Regression for the user-visible "fall through the floor" bug. The 8 cm-thick platform is
        // deliberately much thinner than a single 40 m/s, 50 ms frame displacement. A controller
        // that only checks the final overlap will tunnel through it and land on the planet below.
        auto world = makeFlatWorld();
        vf::RigidBodyDesc floor{};
        floor.motionType = vf::MotionType::Static;
        floor.mass = 0.0;
        floor.position = {0.0, 1003.0, 0.0};
        floor.collisionShape = vf::CollisionShape::box({4.0, 0.04, 4.0});
        const std::uint32_t floorId = world.createRigidBody(floor);

        vf::CharacterController controller{world};
        controller.resetFromEye({0.0, 1009.0, 0.0}, {0.0, -40.0, 0.0}, false);
        vf::CharacterControllerInput input{};
        input.forward = {0.0, 0.0, 1.0};
        input.right = {1.0, 0.0, 0.0};
        for (int i = 0; i < 20; ++i) controller.update(input, 0.05);

        require(controller.grounded(), "fast falling capsule must become grounded on thin floor");
        require(controller.groundBodyId() == floorId,
            "fast falling capsule must land on thin floor instead of tunneling to planet");
        require(controller.centerPosition().y > 1003.80,
            "capsule center must remain physically above the thin floor");
    }

    std::cout << "Character controller tests passed\n";
    return 0;
}
