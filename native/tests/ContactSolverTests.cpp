#include "vf/physics/Broadphase.hpp"
#include "vf/physics/PhysicsWorld.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/gtc/constants.hpp>
#include <glm/gtc/quaternion.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "CONTACT SOLVER TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

[[nodiscard]] vf::PhysicsEnvironment isolatedEnvironment() {
    vf::PhysicsEnvironment environment{};
    environment.planet.radius = 1.0;
    environment.planet.maxElevation = 0.0;
    environment.surfaceGravity = 0.0;
    environment.atmosphere.pressureScale = 0.0;
    environment.atmosphere.gustAmplitude = 0.0;
    environment.atmosphere.prevailingWind = {};
    environment.ocean.enabled = false;
    return environment;
}

[[nodiscard]] vf::PhysicsEnvironment flatPlanetEnvironment() {
    vf::PhysicsEnvironment environment{};
    environment.planet.radius = 100.0;
    environment.planet.maxElevation = 0.0;
    environment.surfaceGravity = 9.81;
    environment.atmosphere.pressureScale = 0.0;
    environment.atmosphere.gustAmplitude = 0.0;
    environment.atmosphere.prevailingWind = {};
    environment.weather.windMultiplier = 0.0;
    environment.ocean.enabled = false;
    return environment;
}

[[nodiscard]] vf::RigidBodyDesc sphereBody(const glm::dvec3& position, double radius = 0.25) {
    vf::RigidBodyDesc desc{};
    desc.position = position;
    desc.mass = 1.0;
    desc.collisionShape = vf::CollisionShape::sphere(radius);
    const double inertia = 0.4 * desc.mass * radius * radius;
    desc.inertiaDiagonal = {inertia, inertia, inertia};
    desc.linearDamping = 0.0;
    desc.angularDamping = 0.0;
    desc.aerodynamics.referenceArea = 0.0;
    desc.material.restitution = 0.0;
    desc.material.friction = 0.5;
    return desc;
}

[[nodiscard]] vf::RigidBodyDesc boxBody(
    const glm::dvec3& position,
    const glm::dvec3& halfExtents,
    double mass = 2.0) {
    vf::RigidBodyDesc desc{};
    desc.position = position;
    desc.mass = mass;
    desc.collisionShape = vf::CollisionShape::box(halfExtents);
    desc.inertiaDiagonal = {
        mass / 3.0 * (halfExtents.y * halfExtents.y + halfExtents.z * halfExtents.z),
        mass / 3.0 * (halfExtents.x * halfExtents.x + halfExtents.z * halfExtents.z),
        mass / 3.0 * (halfExtents.x * halfExtents.x + halfExtents.y * halfExtents.y),
    };
    desc.linearDamping = 0.0;
    desc.angularDamping = 0.0;
    desc.aerodynamics.referenceArea = 0.0;
    desc.material.restitution = 0.0;
    desc.material.friction = 0.65;
    return desc;
}

void testBroadphaseUsesOrientedShapeAabb() {
    vf::PhysicsWorld separated{isolatedEnvironment()};
    auto box = boxBody({1000.0, 0.0, 0.0}, {2.0, 0.1, 0.1});
    box.orientation = glm::angleAxis(glm::half_pi<double>(), glm::dvec3{0.0, 0.0, 1.0});
    (void)separated.createRigidBody(box);
    (void)separated.createRigidBody(sphereBody({1001.0, 0.0, 0.0}, 0.2));
    require(vf::buildSweepAndPrunePairs(separated.bodies()).empty(),
        "shape AABB broadphase must reject a pair that only overlaps old bounding spheres");

    vf::PhysicsWorld overlapping{isolatedEnvironment()};
    (void)overlapping.createRigidBody(box);
    (void)overlapping.createRigidBody(sphereBody({1000.25, 0.0, 0.0}, 0.2));
    require(!vf::buildSweepAndPrunePairs(overlapping.bodies()).empty(),
        "shape AABB broadphase must retain a real rotated-box overlap");
}

void testFaceContactProducesFourSolverPoints() {
    vf::PhysicsWorld world{isolatedEnvironment()};
    auto a = boxBody({1000.0, 0.0, 0.0}, {1.0, 1.0, 1.0});
    a.motionType = vf::MotionType::Static;
    auto b = boxBody({1001.8, 0.0, 0.0}, {1.0, 1.0, 1.0});
    (void)world.createRigidBody(a);
    (void)world.createRigidBody(b);

    world.stepFixed();
    require(world.lastBroadphaseCandidateCount() == 1U, "face-contact test must create one broadphase candidate");
    require(world.lastContactPointCount() == 4U, "face/face collision must reach the solver as four contact points");
}

void testOffCenterImpactCreatesAngularResponse() {
    vf::PhysicsWorld world{isolatedEnvironment()};

    auto projectile = sphereBody({997.0, 0.72, 0.0}, 0.25);
    projectile.mass = 1.0;
    projectile.inertiaDiagonal = {0.025, 0.025, 0.025};
    projectile.linearVelocity = {9.0, 0.0, 0.0};
    projectile.material.friction = 0.0;

    auto target = boxBody({1000.0, 0.0, 0.0}, {0.5, 1.0, 0.5}, 2.0);
    target.material.friction = 0.0;

    const auto projectileId = world.createRigidBody(projectile);
    const auto targetId = world.createRigidBody(target);
    (void)projectileId;

    bool observedContact = false;
    for (int step = 0; step < 90; ++step) {
        world.stepFixed();
        observedContact = observedContact || world.lastContactPointCount() > 0U;
    }

    const auto* targetBody = world.body(targetId);
    require(observedContact, "off-center projectile must reach narrowphase/solver contact");
    require(targetBody != nullptr, "off-center target body missing");
    require(std::abs(targetBody->angularVelocity.z) > 0.02,
        "off-center contact impulse must create angular velocity instead of only changing center velocity");
}

void testSingleBoxSleepsAndStopsCreepingOnPlanet() {
    vf::PhysicsWorld world{flatPlanetEnvironment()};
    auto resting = boxBody({0.0, 100.53, 0.0}, {0.5, 0.5, 0.5}, 12.0);
    resting.material.friction = 0.86;
    resting.material.rollingResistance = 0.12;
    resting.linearDamping = 0.09;
    resting.angularDamping = 0.16;
    const auto id = world.createRigidBody(resting);

    for (int step = 0; step < 720; ++step) world.stepFixed();
    const auto* settled = world.body(id);
    require(settled != nullptr, "resting body missing");
    require(settled->sleeping,
        "a supported idle prop must enter sleep instead of being re-awakened by its own contact impulses");
    require(glm::length(settled->linearVelocity) < 1.0e-10,
        "a sleeping prop must have zero linear jitter");
    require(glm::length(settled->angularVelocity) < 1.0e-10,
        "a sleeping prop must have zero angular jitter");

    const glm::dvec3 lockedPosition = settled->position;
    const glm::dquat lockedOrientation = settled->orientation;
    for (int step = 0; step < 720; ++step) world.stepFixed();
    const auto* stillSettled = world.body(id);
    require(stillSettled != nullptr, "resting body missing after hold interval");
    require(glm::length(stillSettled->position - lockedPosition) < 1.0e-9,
        "sleeping prop must not creep across the ground over time");
    require(std::abs(glm::dot(stillSettled->orientation, lockedOrientation)) > 1.0 - 1.0e-12,
        "sleeping prop orientation must remain locked instead of visibly trembling");
}

void testTwoBoxStackSettlesOnPlanet() {
    vf::PhysicsWorld world{flatPlanetEnvironment()};

    auto lower = boxBody({0.0, 100.52, 0.0}, {0.5, 0.5, 0.5}, 4.0);
    lower.material.friction = 0.8;
    auto upper = boxBody({0.0, 101.60, 0.0}, {0.5, 0.5, 0.5}, 4.0);
    upper.material.friction = 0.8;
    const auto lowerId = world.createRigidBody(lower);
    const auto upperId = world.createRigidBody(upper);

    for (int step = 0; step < 720; ++step) world.stepFixed();

    const auto* lowerBody = world.body(lowerId);
    const auto* upperBody = world.body(upperId);
    require(lowerBody != nullptr && upperBody != nullptr, "stack bodies missing");
    require(lowerBody->position.y > 100.45 && lowerBody->position.y < 100.80,
        "lower box must remain supported by the spherical planet surface");
    require(upperBody->position.y > 101.35 && upperBody->position.y < 101.90,
        "upper box must remain stacked instead of tunnelling or exploding");
    require(glm::length(lowerBody->linearVelocity) < 0.6, "lower resting box should settle to low speed");
    require(glm::length(upperBody->linearVelocity) < 0.6, "upper resting box should settle to low speed");
    require(world.lastContactPointCount() >= 1U, "resting stack should retain persistent contact state");
}

} // namespace

int main() {
    testBroadphaseUsesOrientedShapeAabb();
    testFaceContactProducesFourSolverPoints();
    testOffCenterImpactCreatesAngularResponse();
    testSingleBoxSleepsAndStopsCreepingOnPlanet();
    testTwoBoxStackSettlesOnPlanet();
    std::cout << "vf_contact_solver_tests: PASS\n";
    return 0;
}
