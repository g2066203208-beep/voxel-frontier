#include "vf/physics/AerodynamicSurface.hpp"
#include "vf/physics/Broadphase.hpp"
#include "vf/physics/PhysicsWorld.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "MECHANICS TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

[[nodiscard]] vf::PhysicsEnvironment isolatedEnvironment() {
    vf::PhysicsEnvironment env{};
    env.planet.radius = 1.0;
    env.planet.maxElevation = 0.0;
    env.planet.atmosphereHeight = 1.0;
    env.surfaceGravity = 0.0;
    env.ocean.enabled = false;
    env.atmosphere.pressureScale = 0.0;
    env.atmosphere.gustAmplitude = 0.0;
    env.atmosphere.prevailingWind = {};
    return env;
}

[[nodiscard]] vf::RigidBodyDesc dynamicBody(glm::dvec3 position) {
    vf::RigidBodyDesc desc{};
    desc.position = position;
    desc.mass = 2.0;
    desc.inertiaDiagonal = {1.0, 1.0, 1.0};
    desc.collisionShape = vf::CollisionShape::sphere(0.1);
    desc.linearDamping = 0.0;
    desc.angularDamping = 0.0;
    desc.aerodynamics.referenceArea = 0.0;
    return desc;
}

void testSweepAndPruneRejectsFarPairs() {
    vf::PhysicsWorld world{isolatedEnvironment()};
    for (int i = 0; i < 100; ++i) {
        auto desc = dynamicBody({1000.0 + static_cast<double>(i) * 5.0, 0.0, 0.0});
        desc.collisionShape = vf::CollisionShape::sphere(0.25);
        (void)world.createRigidBody(desc);
    }
    auto overlap = dynamicBody({1000.2, 0.0, 0.0});
    overlap.collisionShape = vf::CollisionShape::sphere(0.25);
    (void)world.createRigidBody(overlap);

    const auto pairs = vf::buildSweepAndPrunePairs(world.bodies());
    require(!pairs.empty(), "broadphase must retain an actual overlapping candidate");
    const std::size_t bruteForcePairs = 101U * 100U / 2U;
    require(pairs.size() < bruteForcePairs / 100U, "sweep-and-prune should reject almost all sparse pairs");
}

void testSpringDamperPullsTowardRestLength() {
    vf::PhysicsWorld world{isolatedEnvironment()};

    auto anchorDesc = dynamicBody({1000.0, 0.0, 0.0});
    anchorDesc.motionType = vf::MotionType::Static;
    const auto anchor = world.createRigidBody(anchorDesc);
    const auto payload = world.createRigidBody(dynamicBody({1003.0, 0.0, 0.0}));

    vf::SpringDamperConstraintDesc spring{};
    spring.bodyA = anchor;
    spring.bodyB = payload;
    spring.restLength = 1.0;
    spring.stiffnessNPerM = 80.0;
    spring.dampingNsPerM = 18.0;
    spring.maxForceN = 1000.0;
    (void)world.createSpringDamperConstraint(spring);

    const double initialX = world.body(payload)->position.x;
    for (int i = 0; i < 45; ++i) world.stepFixed();
    require(world.body(payload)->position.x < initialX - 0.05, "spring must accelerate an extended payload toward its rest length");
}

void testDistanceConstraintResistsSeparation() {
    vf::PhysicsWorld world{isolatedEnvironment()};
    auto anchorDesc = dynamicBody({1000.0, 0.0, 0.0});
    anchorDesc.motionType = vf::MotionType::Static;
    const auto anchor = world.createRigidBody(anchorDesc);

    auto payloadDesc = dynamicBody({1002.0, 0.0, 0.0});
    payloadDesc.linearVelocity = {8.0, 0.0, 0.0};
    const auto payload = world.createRigidBody(payloadDesc);

    vf::DistanceConstraintDesc distance{};
    distance.bodyA = anchor;
    distance.bodyB = payload;
    distance.restLength = 2.0;
    distance.maxForceN = 50000.0;
    (void)world.createDistanceConstraint(distance);

    for (int i = 0; i < 120; ++i) world.stepFixed();
    const double length = glm::length(world.body(payload)->position - world.body(anchor)->position);
    require(std::abs(length - 2.0) < 0.08, "distance constraint should hold its rest length under an outward impulse");
}

void testHingeMotorDrivesAngularSpeed() {
    vf::PhysicsWorld world{isolatedEnvironment()};
    auto anchorDesc = dynamicBody({1000.0, 0.0, 0.0});
    anchorDesc.motionType = vf::MotionType::Static;
    const auto anchor = world.createRigidBody(anchorDesc);

    auto rotorDesc = dynamicBody({1000.0, 1.0, 0.0});
    rotorDesc.collisionShape = vf::CollisionShape::sphere(0.05);
    const auto rotor = world.createRigidBody(rotorDesc);

    vf::HingeConstraintDesc hinge{};
    hinge.bodyA = anchor;
    hinge.bodyB = rotor;
    hinge.localAnchorA = {0.0, 0.0, 0.0};
    hinge.localAnchorB = {0.0, -1.0, 0.0};
    hinge.localAxisA = {0.0, 1.0, 0.0};
    hinge.localAxisB = {0.0, 1.0, 0.0};
    hinge.motorEnabled = true;
    hinge.targetAngularSpeedRadPerS = 6.0;
    hinge.maxMotorTorqueNm = 80.0;
    (void)world.createHingeConstraint(hinge);

    for (int i = 0; i < 90; ++i) world.stepFixed();
    const auto* rotorBody = world.body(rotor);
    require(rotorBody->angularVelocity.y > 1.0, "hinge motor must create rotation around the hinge axis");
    const glm::dvec3 anchorPoint = rotorBody->position + rotorBody->orientation * glm::dvec3{0.0, -1.0, 0.0};
    require(glm::length(anchorPoint - world.body(anchor)->position) < 0.12, "hinge motor must keep the hinge anchor connected");
}

void testGearEnforcesVelocityRatio() {
    vf::PhysicsWorld world{isolatedEnvironment()};
    auto aDesc = dynamicBody({1000.0, 0.0, 0.0});
    auto bDesc = dynamicBody({1005.0, 0.0, 0.0});
    aDesc.angularVelocity = {0.0, 0.0, 10.0};
    bDesc.angularVelocity = {0.0, 0.0, 0.0};
    const auto a = world.createRigidBody(aDesc);
    const auto b = world.createRigidBody(bDesc);

    vf::GearConstraintDesc gear{};
    gear.bodyA = a;
    gear.bodyB = b;
    gear.ratio = 2.0;
    gear.maxTorqueNm = 10000.0;
    (void)world.createGearConstraint(gear);

    world.stepFixed();
    const double residual = world.body(a)->angularVelocity.z + 2.0 * world.body(b)->angularVelocity.z;
    require(std::abs(residual) < 1.0e-5, "gear constraint must enforce omegaA + ratio*omegaB = 0");
}

void testBreakableDistanceConstraint() {
    vf::PhysicsWorld world{isolatedEnvironment()};
    auto anchorDesc = dynamicBody({1000.0, 0.0, 0.0});
    anchorDesc.motionType = vf::MotionType::Static;
    const auto anchor = world.createRigidBody(anchorDesc);
    const auto payload = world.createRigidBody(dynamicBody({1010.0, 0.0, 0.0}));

    vf::DistanceConstraintDesc distance{};
    distance.bodyA = anchor;
    distance.bodyB = payload;
    distance.restLength = 1.0;
    distance.breakForceN = 50.0;
    (void)world.createDistanceConstraint(distance);

    world.stepFixed();
    require(world.distanceConstraints().front().broken, "overloaded distance constraint must break instead of transmitting infinite load");
}

void testAerodynamicSurfaceLiftAndStall() {
    vf::RigidBody body{};
    body.motionType = vf::MotionType::Dynamic;
    body.mass = 100.0;
    body.inverseMass = 0.01;
    body.inertiaDiagonal = {20.0, 20.0, 20.0};
    body.inverseInertiaDiagonal = {0.05, 0.05, 0.05};
    body.linearVelocity = {50.0, -5.0, 0.0};

    vf::AtmosphereSample atmosphere{};
    atmosphere.densityKgPerM3 = 1.225;

    vf::AerodynamicSurface wing{};
    wing.areaM2 = 8.0;
    const auto normalFlight = vf::sampleAerodynamicSurface(wing, body, atmosphere);
    require(normalFlight.angleOfAttackRad > 0.0, "downward relative velocity should produce positive angle of attack for the configured wing frame");
    require(normalFlight.liftCoefficient > 0.0, "positive angle of attack must produce positive lift coefficient before stall");
    require(normalFlight.liftForceN.y > 0.0, "wing lift should act roughly along the positive surface normal");

    body.linearVelocity = {5.0, -50.0, 0.0};
    const auto stalled = vf::sampleAerodynamicSurface(wing, body, atmosphere);
    require(std::abs(stalled.angleOfAttackRad) > wing.stallAngleRad, "high incidence test must be beyond stall");
    require(std::abs(stalled.liftCoefficient) < wing.maxLiftCoefficient, "post-stall lift model must fall below peak lift coefficient");
    require(stalled.dragCoefficient > normalFlight.dragCoefficient, "stalled wing should have substantially more drag");
}

void testHingeFrictionDissipatesMotion() {
    vf::PhysicsWorld world{isolatedEnvironment()};
    auto anchorDesc = dynamicBody({1000.0, 0.0, 0.0});
    anchorDesc.motionType = vf::MotionType::Static;
    const auto anchor = world.createRigidBody(anchorDesc);

    auto rotorDesc = dynamicBody({1000.0, 1.0, 0.0});
    rotorDesc.angularVelocity = {0.0, 8.0, 0.0};
    const auto rotor = world.createRigidBody(rotorDesc);

    vf::HingeConstraintDesc hinge{};
    hinge.bodyA = anchor;
    hinge.bodyB = rotor;
    hinge.localAnchorB = {0.0, -1.0, 0.0};
    hinge.localAxisA = {0.0, 1.0, 0.0};
    hinge.localAxisB = {0.0, 1.0, 0.0};
    hinge.viscousFrictionNmPerRadS = 2.0;
    hinge.coulombFrictionTorqueNm = 1.0;
    (void)world.createHingeConstraint(hinge);

    const double initialSpeed = std::abs(world.body(rotor)->angularVelocity.y);
    for (int i = 0; i < 60; ++i) world.stepFixed();
    require(std::abs(world.body(rotor)->angularVelocity.y) < initialSpeed, "joint friction must dissipate hinge motion");
}

} // namespace

int main() {
    testSweepAndPruneRejectsFarPairs();
    testSpringDamperPullsTowardRestLength();
    testDistanceConstraintResistsSeparation();
    testHingeMotorDrivesAngularSpeed();
    testGearEnforcesVelocityRatio();
    testBreakableDistanceConstraint();
    testAerodynamicSurfaceLiftAndStall();
    testHingeFrictionDissipatesMotion();
    std::cout << "vf_mechanics_tests: PASS\n";
    return 0;
}
