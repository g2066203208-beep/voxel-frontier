#include "vf/gameplay/PhysicsPlayground.hpp"

#include "vf/render/PhysicsDebugMesh.hpp"

#include <algorithm>
#include <cmath>

#include <glm/geometric.hpp>

namespace vf {
namespace {

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-12) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] RigidBodyDesc makeStaticBody(const glm::dvec3& position, double radius = 0.05) {
    RigidBodyDesc desc{};
    desc.motionType = MotionType::Static;
    desc.position = position;
    desc.mass = 0.0;
    desc.collisionRadius = radius;
    desc.aerodynamics.referenceArea = 0.0;
    return desc;
}

[[nodiscard]] RigidBodyDesc makeDynamicBody(
    const glm::dvec3& position,
    double mass,
    double radius) {
    RigidBodyDesc desc{};
    desc.position = position;
    desc.mass = mass;
    desc.collisionRadius = radius;
    const double inertia = std::max(0.001, 0.4 * mass * radius * radius);
    desc.inertiaDiagonal = {inertia, inertia, inertia};
    desc.material.friction = 0.62;
    desc.material.restitution = 0.22;
    desc.material.rollingResistance = 0.012;
    desc.linearDamping = 0.015;
    desc.angularDamping = 0.025;
    desc.aerodynamics.dragCoefficient = 0.47;
    desc.aerodynamics.referenceArea = 3.14159265358979323846 * radius * radius;
    return desc;
}

} // namespace

PhysicsPlayground::PhysicsPlayground(
    PhysicsWorld& physics,
    const PlanetDefinition& planet,
    const glm::dvec3& centerDirection)
    : physics_(&physics), planet_(&planet), centerDirection_(safeNormalize(centerDirection)) {
    up_ = centerDirection_;
    const glm::dvec3 reference = std::abs(up_.y) < 0.9
        ? glm::dvec3{0.0, 1.0, 0.0}
        : glm::dvec3{1.0, 0.0, 0.0};
    east_ = safeNormalize(glm::cross(reference, up_), {1.0, 0.0, 0.0});
    north_ = safeNormalize(glm::cross(up_, east_), {0.0, 0.0, 1.0});

    // Spring station: an elevated ceiling anchor and a massive payload visibly oscillate.
    springAnchor_ = physics_->createRigidBody(makeStaticBody(surfacePoint(-7.0, 0.0, 8.5)));
    auto springPayloadDesc = makeDynamicBody(surfacePoint(-7.0, 0.0, 4.0), 18.0, 0.65);
    springPayloadDesc.material.restitution = 0.08;
    springPayload_ = physics_->createRigidBody(springPayloadDesc);
    SpringDamperConstraintDesc spring{};
    spring.bodyA = springAnchor_;
    spring.bodyB = springPayload_;
    spring.restLength = 2.7;
    spring.stiffnessNPerM = 260.0;
    spring.dampingNsPerM = 48.0;
    spring.maxForceN = 8000.0;
    spring.breakForceN = 16000.0;
    (void)physics_->createSpringDamperConstraint(spring);

    // Motorized hinge station: the rotor body spins because the joint transmits torque.
    const glm::dvec3 motorBase = surfacePoint(0.0, 0.0, 0.2);
    motorAnchor_ = physics_->createRigidBody(makeStaticBody(motorBase + up_ * 2.8, 0.03));
    auto rotorDesc = makeDynamicBody(motorBase + up_ * 3.3, 12.0, 0.07);
    rotorDesc.inertiaDiagonal = {5.0, 1.6, 5.0};
    rotorDesc.aerodynamics.referenceArea = 0.0;
    motorRotor_ = physics_->createRigidBody(rotorDesc);
    HingeConstraintDesc motorHinge{};
    motorHinge.bodyA = motorAnchor_;
    motorHinge.bodyB = motorRotor_;
    motorHinge.localAnchorA = up_ * 0.5;
    motorHinge.localAnchorB = {};
    motorHinge.localAxisA = up_;
    motorHinge.localAxisB = up_;
    motorHinge.motorEnabled = true;
    motorHinge.targetAngularSpeedRadPerS = 2.6;
    motorHinge.maxMotorTorqueNm = 90.0;
    motorHinge.viscousFrictionNmPerRadS = 0.35;
    motorHinge.coulombFrictionTorqueNm = 0.18;
    motorHinge.breakForceN = 12000.0;
    motorHinge.breakTorqueNm = 1800.0;
    (void)physics_->createHingeConstraint(motorHinge);

    // Gear station: one powered shaft drives the neighboring shaft at a real angular ratio.
    const glm::dvec3 gearBaseA = surfacePoint(7.0, -0.5, 0.2);
    const glm::dvec3 gearBaseB = surfacePoint(10.0, -0.5, 0.2);
    gearAnchorA_ = physics_->createRigidBody(makeStaticBody(gearBaseA + up_ * 2.5, 0.03));
    gearAnchorB_ = physics_->createRigidBody(makeStaticBody(gearBaseB + up_ * 2.5, 0.03));

    auto gearRotorDescA = makeDynamicBody(gearBaseA + up_ * 3.0, 10.0, 0.06);
    gearRotorDescA.inertiaDiagonal = {4.0, 1.4, 4.0};
    gearRotorDescA.aerodynamics.referenceArea = 0.0;
    auto gearRotorDescB = gearRotorDescA;
    gearRotorDescB.position = gearBaseB + up_ * 3.0;
    gearRotorB_ = physics_->createRigidBody(gearRotorDescB);
    gearRotorA_ = physics_->createRigidBody(gearRotorDescA);

    HingeConstraintDesc gearHingeA{};
    gearHingeA.bodyA = gearAnchorA_;
    gearHingeA.bodyB = gearRotorA_;
    gearHingeA.localAnchorA = up_ * 0.5;
    gearHingeA.localAxisA = up_;
    gearHingeA.localAxisB = up_;
    gearHingeA.motorEnabled = true;
    gearHingeA.targetAngularSpeedRadPerS = 3.2;
    gearHingeA.maxMotorTorqueNm = 100.0;
    gearHingeA.viscousFrictionNmPerRadS = 0.20;
    gearHingeA.breakTorqueNm = 2000.0;
    (void)physics_->createHingeConstraint(gearHingeA);

    HingeConstraintDesc gearHingeB = gearHingeA;
    gearHingeB.bodyA = gearAnchorB_;
    gearHingeB.bodyB = gearRotorB_;
    gearHingeB.motorEnabled = false;
    gearHingeB.maxMotorTorqueNm = 0.0;
    (void)physics_->createHingeConstraint(gearHingeB);

    GearConstraintDesc gear{};
    gear.bodyA = gearRotorA_;
    gear.bodyB = gearRotorB_;
    gear.localAxisA = up_;
    gear.localAxisB = up_;
    gear.ratio = 1.5;
    gear.maxTorqueNm = 180.0;
    gear.breakTorqueNm = 900.0;
    (void)physics_->createGearConstraint(gear);

    // Atmospheric buoyancy: a light sealed envelope rises from displaced air, not a scripted animation.
    auto balloonDesc = makeDynamicBody(surfacePoint(14.0, 2.5, 2.1), 2.2, 0.85);
    balloonDesc.material.restitution = 0.05;
    balloonDesc.aerodynamics.dragCoefficient = 0.48;
    balloonDesc.aerodynamics.referenceArea = 2.3;
    balloonDesc.buoyancy.enabled = true;
    balloonDesc.buoyancy.displaceAtmosphere = true;
    balloonDesc.buoyancy.displacedVolume = 3.6;
    balloon_ = physics_->createRigidBody(balloonDesc);

    // A small pile proves mass, gravity, collision, restitution, friction and rolling resistance visually.
    for (int i = 0; i < 5; ++i) {
        auto desc = makeDynamicBody(
            surfacePoint(-1.5 + 1.0 * static_cast<double>(i), 6.0, 7.0 + static_cast<double>(i) * 1.8),
            3.0 + static_cast<double>(i) * 2.0,
            0.45 + 0.05 * static_cast<double>(i));
        desc.material.restitution = 0.30 - 0.035 * static_cast<double>(i);
        const auto id = physics_->createRigidBody(desc);
        fallingBodies_.push_back(id);
    }

    visibleBodyIds_ = {
        springPayload_, motorRotor_, gearRotorA_, gearRotorB_, balloon_,
    };
    visibleBodyIds_.insert(visibleBodyIds_.end(), fallingBodies_.begin(), fallingBodies_.end());

    tree_.rootPosition = surfacePoint(-13.0, 3.5, 0.05);
    tree_.localUp = safeNormalize(tree_.rootPosition);
    tree_.fallDirection = north_ + east_ * 0.35;
    tree_.trunkLength = 6.8;
    tree_.trunkRadius = 0.28;
    tree_.trunkMass = 360.0;
    tree_.dragCoefficient = 1.1;
}

glm::dvec3 PhysicsPlayground::surfacePoint(
    double eastMeters,
    double northMeters,
    double heightMeters) const {
    const double radius = std::max(1.0, planet_->radius);
    const glm::dvec3 direction = safeNormalize(
        centerDirection_ + east_ * (eastMeters / radius) + north_ * (northMeters / radius),
        centerDirection_);
    return direction * (planetSurfaceRadius(*planet_, direction) + heightMeters);
}

bool PhysicsPlayground::isSpecialBody(std::uint32_t id) const noexcept {
    return id == motorRotor_ || id == gearRotorA_ || id == gearRotorB_ || id == springPayload_ || id == balloon_;
}

void PhysicsPlayground::update(double deltaSeconds) {
    elapsedSeconds_ += std::clamp(deltaSeconds, 0.0, 0.05);

    // Demonstration cut begins after the player has had time to see the standing tree.
    if (elapsedSeconds_ >= 4.0 && elapsedSeconds_ <= 7.4 && tree_.cutFraction < 0.70) {
        tree_.applyCut(deltaSeconds * 0.22, north_ + east_ * 0.35);
    }

    const AtmosphereSample atmosphere = physics_->environment().sampleAtmosphere(
        tree_.rootPosition + tree_.localUp * (0.5 * tree_.trunkLength),
        physics_->simulationTime());
    tree_.step(
        deltaSeconds,
        physics_->environment().gravityMagnitude(tree_.rootPosition),
        atmosphere.windVelocity,
        atmosphere.densityKgPerM3);
}

PlanetMesh PhysicsPlayground::buildDebugMesh() const {
    PlanetMesh mesh{};
    mesh.vertices.reserve(1600U);
    mesh.indices.reserve(3600U);

    const glm::vec3 steel{0.38F, 0.43F, 0.48F};
    const glm::vec3 motorColor{0.93F, 0.55F, 0.10F};
    const glm::vec3 gearAColor{0.25F, 0.67F, 0.93F};
    const glm::vec3 gearBColor{0.92F, 0.32F, 0.29F};
    const glm::vec3 springColor{0.78F, 0.82F, 0.87F};
    const glm::vec3 payloadColor{0.36F, 0.78F, 0.48F};
    const glm::vec3 balloonColor{0.96F, 0.73F, 0.18F};
    const glm::vec3 treeColor{0.40F, 0.22F, 0.08F};

    // Spring mast + current spring line + payload.
    if (const auto* anchor = physics_->body(springAnchor_)) {
        const glm::dvec3 foot = surfacePoint(-7.0, 0.0, 0.1);
        appendDebugRod(mesh, foot, anchor->position, 0.10, steel);
    }
    if (const auto* anchor = physics_->body(springAnchor_); anchor != nullptr) {
        if (const auto* payload = physics_->body(springPayload_); payload != nullptr) {
            appendDebugRod(mesh, anchor->position, payload->position, 0.045, springColor);
            appendDebugSphere(mesh, payload->position, payload->collisionRadius, payloadColor, 7U, 12U);
        }
    }

    // Motor mast and a long rotor blade whose orientation comes directly from the rigid body quaternion.
    const glm::dvec3 motorFoot = surfacePoint(0.0, 0.0, 0.1);
    if (const auto* anchor = physics_->body(motorAnchor_)) {
        appendDebugRod(mesh, motorFoot, anchor->position, 0.12, steel);
    }
    if (const auto* rotor = physics_->body(motorRotor_)) {
        appendDebugBox(mesh, rotor->position, rotor->orientation, {2.35, 0.10, 0.24}, motorColor);
        appendDebugSphere(mesh, rotor->position, 0.22, steel, 5U, 8U);
    }

    // Gear shafts. Cross-bars make opposite/ratio rotation easy to see even before textured gear teeth exist.
    if (const auto* anchor = physics_->body(gearAnchorA_)) {
        appendDebugRod(mesh, surfacePoint(7.0, -0.5, 0.1), anchor->position, 0.10, steel);
    }
    if (const auto* anchor = physics_->body(gearAnchorB_)) {
        appendDebugRod(mesh, surfacePoint(10.0, -0.5, 0.1), anchor->position, 0.10, steel);
    }
    if (const auto* rotor = physics_->body(gearRotorA_)) {
        appendDebugBox(mesh, rotor->position, rotor->orientation, {1.15, 0.09, 0.20}, gearAColor);
        appendDebugBox(mesh, rotor->position, rotor->orientation, {0.20, 0.09, 1.15}, gearAColor);
    }
    if (const auto* rotor = physics_->body(gearRotorB_)) {
        appendDebugBox(mesh, rotor->position, rotor->orientation, {0.82, 0.09, 0.18}, gearBColor);
        appendDebugBox(mesh, rotor->position, rotor->orientation, {0.18, 0.09, 0.82}, gearBColor);
    }

    if (const auto* balloon = physics_->body(balloon_)) {
        appendDebugSphere(mesh, balloon->position, balloon->collisionRadius, balloonColor, 9U, 14U);
        const glm::dvec3 tetherEnd = balloon->position - safeNormalize(balloon->position) * 1.35;
        appendDebugRod(mesh, balloon->position, tetherEnd, 0.025, {0.42F, 0.28F, 0.16F});
    }

    for (std::size_t i = 0; i < fallingBodies_.size(); ++i) {
        const auto* body = physics_->body(fallingBodies_[i]);
        if (body == nullptr) continue;
        const float f = static_cast<float>(i) / static_cast<float>(std::max<std::size_t>(1U, fallingBodies_.size() - 1U));
        const glm::vec3 color{0.35F + 0.45F * f, 0.35F, 0.82F - 0.35F * f};
        appendDebugSphere(mesh, body->position, body->collisionRadius, color, 7U, 10U);
    }

    appendDebugRod(mesh, tree_.rootPosition, tree_.tipPosition(), tree_.trunkRadius, treeColor);
    appendDebugSphere(mesh, tree_.tipPosition(), 0.75, {0.18F, 0.48F, 0.15F}, 6U, 10U);

    return mesh;
}

} // namespace vf
