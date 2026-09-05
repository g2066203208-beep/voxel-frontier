#include "vf/player/CharacterController.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>

#include <glm/geometric.hpp>

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

    {
        // Regression for terrain-side penetration. Find a real procedural land slope, place the
        // capsule directly on it, then walk across it. The old single center-ray terrain test could
        // let the slope enter through the lower hemisphere even though the center ray was clear.
        vf::PhysicsEnvironment environment{};
        environment.planet.seed = 0x71A9F20DULL;
        environment.planet.radius = 6371000.0;
        environment.planet.maxElevation = 8850.0;
        environment.planet.maxOceanDepthMeters = 11000.0;
        environment.surfaceGravity = 9.80665;
        environment.atmosphere.prevailingWind = {};
        environment.atmosphere.gustAmplitude = 0.0;
        environment.weather.windMultiplier = 0.0;
        environment.ocean.enabled = false;
        vf::PhysicsWorld world{environment};

        glm::dvec3 slopeDirection{1.0, 0.0, 0.0};
        glm::dvec3 slopeNormal{1.0, 0.0, 0.0};
        bool foundSlope = false;
        for (std::uint32_t face = 0; face < 6U && !foundSlope; ++face) {
            for (int y = 0; y <= 36 && !foundSlope; ++y) {
                for (int x = 0; x <= 36; ++x) {
                    const double u = -1.0 + 2.0 * static_cast<double>(x) / 36.0;
                    const double v = -1.0 + 2.0 * static_cast<double>(y) / 36.0;
                    const glm::dvec3 d = vf::cubeSphereDirection(face, u, v);
                    const auto terrain = vf::samplePlanetTerrain(environment.planet, d);
                    if (terrain.submerged(environment.planet)
                        || terrain.elevationMeters < 120.0
                        || terrain.elevationMeters > 2600.0
                        || terrain.canyon > 0.55
                        || terrain.coastalCliff > 0.65) continue;
                    const glm::dvec3 normal = vf::planetSurfaceNormal(environment.planet, d);
                    const double alignment = glm::dot(normal, d);
                    if (alignment > 0.80 && alignment < 0.975) {
                        slopeDirection = d;
                        slopeNormal = normal;
                        foundSlope = true;
                        break;
                    }
                }
            }
        }
        require(foundSlope, "test planet must expose a walkable non-flat procedural slope");

        const double surfaceRadius = vf::planetSurfaceRadius(environment.planet, slopeDirection);
        const glm::dvec3 surfacePoint = slopeDirection * surfaceRadius;
        vf::CharacterController controller{world};
        controller.resetFromEye(surfacePoint + slopeDirection * 1.75, {}, true);
        settle(controller, 180);
        require(controller.grounded(), "capsule must settle on procedural slope without falling through");

        glm::dvec3 tangent = glm::cross(slopeNormal, slopeDirection);
        if (glm::length(tangent) < 1.0e-8) tangent = glm::cross(slopeDirection, glm::dvec3{0.0, 1.0, 0.0});
        tangent = glm::normalize(tangent);
        vf::CharacterControllerInput input{};
        input.forward = tangent;
        input.right = glm::normalize(glm::cross(tangent, slopeDirection));
        input.forwardAxis = 0.65;
        for (int i = 0; i < 180; ++i) controller.update(input, 1.0 / 120.0);
        settle(controller, 60);

        const glm::dvec3 finalDirection = glm::normalize(controller.centerPosition());
        const double finalSurface = vf::planetSurfaceRadius(environment.planet, finalDirection);
        const double radialBottom = glm::length(controller.centerPosition())
            - (controller.settings().halfHeight + controller.settings().radius);
        require(radialBottom >= finalSurface - 0.10,
            "lower capsule must remain above authoritative procedural terrain after slope traversal");
    }

    std::cout << "Character controller tests passed\n";
    return 0;
}
