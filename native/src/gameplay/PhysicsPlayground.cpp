#include "vf/gameplay/PhysicsPlayground.hpp"

#include "vf/render/PhysicsDebugMesh.hpp"

#include <algorithm>
#include <cmath>
#include <vector>

#include <glm/geometric.hpp>
#include <glm/gtc/quaternion.hpp>

namespace vf {
namespace {

constexpr double kPi = 3.14159265358979323846;

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
    desc.collisionShape = CollisionShape::sphere(radius);
    desc.aerodynamics.referenceArea = 0.0;
    return desc;
}

[[nodiscard]] RigidBodyDesc makeDynamicSphere(
    const glm::dvec3& position,
    double mass,
    double radius) {
    RigidBodyDesc desc{};
    desc.position = position;
    desc.mass = mass;
    desc.collisionShape = CollisionShape::sphere(radius);
    const double inertia = std::max(0.001, 0.4 * mass * radius * radius);
    desc.inertiaDiagonal = {inertia, inertia, inertia};

    // Everyday loose props should come to rest instead of behaving like rubber test particles.
    desc.material.friction = 0.82;
    desc.material.restitution = 0.015;
    desc.material.rollingResistance = 0.085;
    desc.linearDamping = 0.055;
    desc.angularDamping = 0.085;
    desc.aerodynamics.dragCoefficient = 0.47;
    desc.aerodynamics.referenceArea = kPi * radius * radius;
    return desc;
}

} // namespace

PhysicsPlayground::PhysicsPlayground(
    PhysicsWorld& physics,
    const PlanetDefinition& planet,
    const glm::dvec3& centerDirectionLocal,
    const glm::dvec3& planetOriginWorld,
    const glm::dquat& planetOrientationWorld)
    : physics_(&physics),
      planet_(&planet),
      planetOriginWorld_(planetOriginWorld),
      planetOrientationWorld_(glm::normalize(planetOrientationWorld)),
      centerDirectionLocal_(safeNormalize(centerDirectionLocal)) {
    const glm::dvec3 localUp = centerDirectionLocal_;
    const glm::dvec3 localReference = std::abs(localUp.y) < 0.9
        ? glm::dvec3{0.0, 1.0, 0.0}
        : glm::dvec3{1.0, 0.0, 0.0};
    const glm::dvec3 localEast = safeNormalize(glm::cross(localReference, localUp), {1.0, 0.0, 0.0});
    const glm::dvec3 localNorth = safeNormalize(glm::cross(localUp, localEast), {0.0, 0.0, 1.0});
    up_ = safeNormalize(planetOrientationWorld_ * localUp, localUp);
    east_ = safeNormalize(planetOrientationWorld_ * localEast, localEast);
    north_ = safeNormalize(planetOrientationWorld_ * localNorth, localNorth);

    // Spring payload: visibly supported by a real spring, so its height is mechanically explained.
    springAnchor_ = physics_->createRigidBody(makeStaticBody(surfacePoint(-7.0, 0.0, 8.5)));
    auto springPayloadDesc = makeDynamicSphere(surfacePoint(-7.0, 0.0, 4.0), 18.0, 0.65);
    springPayloadDesc.material.restitution = 0.0;
    springPayload_ = physics_->createRigidBody(springPayloadDesc);
    SpringDamperConstraintDesc spring{};
    spring.bodyA = springAnchor_;
    spring.bodyB = springPayload_;
    spring.restLength = 2.7;
    spring.stiffnessNPerM = 260.0;
    spring.dampingNsPerM = 64.0;
    spring.maxForceN = 8000.0;
    spring.breakForceN = 16000.0;
    (void)physics_->createSpringDamperConstraint(spring);

    // Motor rotor and gears are supported by explicit static shafts/hinges.
    const glm::dvec3 motorBase = surfacePoint(0.0, 0.0, 0.2);
    motorAnchor_ = physics_->createRigidBody(makeStaticBody(motorBase + up_ * 2.8, 0.03));
    auto rotorDesc = makeDynamicSphere(motorBase + up_ * 3.3, 12.0, 0.07);
    rotorDesc.collisionShape = CollisionShape::box({2.35, 0.10, 0.24});
    rotorDesc.inertiaDiagonal = {0.2704, 22.3204, 22.13};
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

    const glm::dvec3 gearBaseA = surfacePoint(7.0, -0.5, 0.2);
    const glm::dvec3 gearBaseB = surfacePoint(10.0, -0.5, 0.2);
    gearAnchorA_ = physics_->createRigidBody(makeStaticBody(gearBaseA + up_ * 2.5, 0.03));
    gearAnchorB_ = physics_->createRigidBody(makeStaticBody(gearBaseB + up_ * 2.5, 0.03));

    auto gearRotorDescA = makeDynamicSphere(gearBaseA + up_ * 3.0, 10.0, 0.06);
    gearRotorDescA.collisionShape = CollisionShape::box({1.15, 0.09, 0.20});
    gearRotorDescA.inertiaDiagonal = {4.0, 1.4, 4.0};
    gearRotorDescA.aerodynamics.referenceArea = 0.0;
    auto gearRotorDescB = gearRotorDescA;
    gearRotorDescB.position = gearBaseB + up_ * 3.0;
    gearRotorDescB.collisionShape = CollisionShape::box({0.82, 0.09, 0.18});
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

    // Balloon is now physically tethered to a visible ground anchor rather than hovering with a
    // decorative dangling line.
    const glm::dvec3 balloonGround = surfacePoint(14.0, 2.5, 0.12);
    balloonAnchor_ = physics_->createRigidBody(makeStaticBody(balloonGround, 0.12));
    auto balloonDesc = makeDynamicSphere(surfacePoint(14.0, 2.5, 4.65), 2.2, 0.85);
    balloonDesc.material.restitution = 0.0;
    balloonDesc.aerodynamics.dragCoefficient = 0.48;
    balloonDesc.aerodynamics.referenceArea = 2.3;
    balloonDesc.buoyancy.enabled = true;
    balloonDesc.buoyancy.displaceAtmosphere = true;
    balloonDesc.buoyancy.displacedVolume = 3.6;
    balloon_ = physics_->createRigidBody(balloonDesc);
    DistanceConstraintDesc balloonTether{};
    balloonTether.bodyA = balloonAnchor_;
    balloonTether.bodyB = balloon_;
    balloonTether.restLength = 4.55;
    balloonTether.maxForceN = 9000.0;
    balloonTether.breakForceN = 18000.0;
    balloonTether.baumgarte = 0.20;
    (void)physics_->createDistanceConstraint(balloonTether);

    // Loose interaction props begin ON the ground. They are no longer an unexplained stack of
    // airborne regression particles.
    for (int i = 0; i < 5; ++i) {
        const double radius = 0.45 + 0.05 * static_cast<double>(i);
        auto desc = makeDynamicSphere(
            surfacePoint(-1.5 + 1.25 * static_cast<double>(i), 6.0, radius + 0.025),
            3.0 + static_cast<double>(i) * 2.0,
            radius);
        const auto id = physics_->createRigidBody(desc);
        fallingBodies_.push_back(id);
    }

    // Tree starts healthy and standing. It only falls when a future gameplay cut action actually
    // changes cutFraction; the old timed self-destruction made the scene look broken.
    tree_.rootPosition = surfacePoint(-13.0, 3.5, 0.05);
    tree_.localUp = safeNormalize(tree_.rootPosition - planetOriginWorld_);
    tree_.fallDirection = north_ + east_ * 0.35;
    tree_.trunkLength = 6.8;
    tree_.trunkRadius = 0.28;
    tree_.trunkMass = 360.0;
    tree_.dragCoefficient = 1.1;

    ropeGroundAnchor_ = tree_.rootPosition - east_ * 2.6 + tree_.localUp * 0.18;
    const glm::dvec3 loopCenter = tree_.rootPosition + tree_.localUp * 1.25;
    constexpr int loopSegments = 24;
    const double ropeRadius = 0.045;
    const double loopRadius = tree_.trunkRadius + ropeRadius + 0.08;
    std::vector<glm::dvec3> ropePoints;
    ropePoints.reserve(static_cast<std::size_t>(loopSegments) + 4U);
    ropePoints.push_back(ropeGroundAnchor_);
    for (int i = 0; i <= loopSegments; ++i) {
        const double angle = kPi + 2.0 * kPi * static_cast<double>(i) / static_cast<double>(loopSegments);
        ropePoints.push_back(loopCenter
            + east_ * (std::cos(angle) * loopRadius)
            + north_ * (std::sin(angle) * loopRadius));
    }
    const glm::dvec3 ropePayloadPosition = tree_.rootPosition - east_ * 2.7 + tree_.localUp * 2.1;
    ropePoints.push_back(ropePayloadPosition);

    auto ropePayloadDesc = makeDynamicSphere(ropePayloadPosition, 7.0, 0.34);
    ropePayloadDesc.material.restitution = 0.0;
    ropePayloadDesc.aerodynamics.referenceArea = 0.18;
    ropePayload_ = physics_->createRigidBody(ropePayloadDesc);

    RopeMaterial ropeMaterial{};
    ropeMaterial.radiusMeters = ropeRadius;
    ropeMaterial.stretchComplianceMPerN = 2.0e-7;
    ropeMaterial.bendComplianceMPerN = 1.4e-3;
    ropeMaterial.damping = 0.045;
    ropeMaterial.friction = 0.72;
    ropeMaterial.dragCoefficient = 1.15;
    ropeMaterial.breakingStrain = 0.45;
    ropeMaterial.maxTensionN = 5000.0;
    ropeMaterial.selfCollision = true;
    rope_.initialize(std::move(ropePoints), 2.8, ropeMaterial);
    rope_.pinParticle(0U, ropeGroundAnchor_);
    rope_.attachParticleToRigidBody(rope_.particles().size() - 1U, ropePayload_);
    rope_.addCapsuleCollider({tree_.rootPosition, tree_.tipPosition(), tree_.trunkRadius, 0.85});

    visibleBodyIds_ = {
        springPayload_, motorRotor_, gearRotorA_, gearRotorB_, balloon_, ropePayload_,
    };
    visibleBodyIds_.insert(visibleBodyIds_.end(), fallingBodies_.begin(), fallingBodies_.end());
}

void PhysicsPlayground::syncPlanetFrame(
    const glm::dvec3& planetOriginWorld,
    const glm::dquat& planetOrientationWorld) {
    const glm::dquat oldOrientation = glm::normalize(planetOrientationWorld_);
    const glm::dquat newOrientation = glm::normalize(planetOrientationWorld);
    const glm::dquat deltaRotation = glm::normalize(newOrientation * glm::conjugate(oldOrientation));
    const glm::dvec3 oldOrigin = planetOriginWorld_;

    const auto transformPoint = [&](const glm::dvec3& point) {
        return planetOriginWorld + deltaRotation * (point - oldOrigin);
    };
    const auto rotateVector = [&](const glm::dvec3& vector) {
        return deltaRotation * vector;
    };

    tree_.rootPosition = transformPoint(tree_.rootPosition);
    tree_.localUp = safeNormalize(rotateVector(tree_.localUp), tree_.localUp);
    tree_.fallDirection = safeNormalize(rotateVector(tree_.fallDirection), tree_.fallDirection);
    ropeGroundAnchor_ = transformPoint(ropeGroundAnchor_);

    for (auto& particle : rope_.particles()) {
        particle.position = transformPoint(particle.position);
        particle.previousPosition = transformPoint(particle.previousPosition);
        particle.velocity = rotateVector(particle.velocity);
    }
    if (rope_.initialized()) rope_.setPinnedPosition(0U, ropeGroundAnchor_);

    up_ = safeNormalize(rotateVector(up_), up_);
    east_ = safeNormalize(rotateVector(east_), east_);
    north_ = safeNormalize(rotateVector(north_), north_);
    planetOriginWorld_ = planetOriginWorld;
    planetOrientationWorld_ = newOrientation;
}

glm::dvec3 PhysicsPlayground::surfacePoint(
    double eastMeters,
    double northMeters,
    double heightMeters) const {
    const double radius = std::max(1.0, planet_->radius);
    const glm::dquat inverseOrientation = glm::conjugate(glm::normalize(planetOrientationWorld_));
    const glm::dvec3 localEast = safeNormalize(inverseOrientation * east_, {1.0, 0.0, 0.0});
    const glm::dvec3 localNorth = safeNormalize(inverseOrientation * north_, {0.0, 0.0, 1.0});
    const glm::dvec3 directionLocal = safeNormalize(
        centerDirectionLocal_ + localEast * (eastMeters / radius) + localNorth * (northMeters / radius),
        centerDirectionLocal_);
    const glm::dvec3 localPoint = directionLocal * (planetSurfaceRadius(*planet_, directionLocal) + heightMeters);
    return planetOriginWorld_ + planetOrientationWorld_ * localPoint;
}

bool PhysicsPlayground::isSpecialBody(std::uint32_t id) const noexcept {
    return id == motorRotor_ || id == gearRotorA_ || id == gearRotorB_
        || id == springPayload_ || id == balloon_ || id == ropePayload_;
}

void PhysicsPlayground::update(double deltaSeconds) {
    elapsedSeconds_ += std::clamp(deltaSeconds, 0.0, 0.05);

    const glm::dvec3 trunkMidpoint = tree_.rootPosition + tree_.localUp * (0.5 * tree_.trunkLength);
    const AtmosphereSample atmosphere = physics_->environment().sampleAtmosphere(
        trunkMidpoint,
        physics_->simulationTime());
    tree_.step(
        deltaSeconds,
        physics_->environment().gravityMagnitude(tree_.rootPosition),
        atmosphere.windVelocity,
        atmosphere.densityKgPerM3);

    rope_.clearCapsuleColliders();
    rope_.addCapsuleCollider({tree_.rootPosition, tree_.tipPosition(), tree_.trunkRadius, 0.85});
    const glm::dvec3 gravity = physics_->environment().gravityAcceleration(trunkMidpoint);
    rope_.step(deltaSeconds, gravity, atmosphere.windVelocity, atmosphere.densityKgPerM3, physics_);
}

PlanetMesh PhysicsPlayground::buildDebugMesh() const {
    PlanetMesh mesh{};
    mesh.vertices.reserve(3400U);
    mesh.indices.reserve(7600U);

    const glm::vec3 steel{0.38F, 0.43F, 0.48F};
    const glm::vec3 motorColor{0.93F, 0.55F, 0.10F};
    const glm::vec3 gearAColor{0.25F, 0.67F, 0.93F};
    const glm::vec3 gearBColor{0.92F, 0.32F, 0.29F};
    const glm::vec3 springColor{0.78F, 0.82F, 0.87F};
    const glm::vec3 payloadColor{0.36F, 0.78F, 0.48F};
    const glm::vec3 balloonColor{0.96F, 0.73F, 0.18F};
    const glm::vec3 treeColor{0.40F, 0.22F, 0.08F};
    const glm::vec3 ropeColor{0.72F, 0.55F, 0.31F};
    const glm::vec3 ropePayloadColor{0.55F, 0.24F, 0.72F};

    if (const auto* anchor = physics_->body(springAnchor_)) {
        const glm::dvec3 foot = surfacePoint(-7.0, 0.0, 0.1);
        appendDebugRod(mesh, foot, anchor->position, 0.10, steel);
    }
    if (const auto* anchor = physics_->body(springAnchor_); anchor != nullptr) {
        if (const auto* payload = physics_->body(springPayload_); payload != nullptr) {
            appendDebugRod(mesh, anchor->position, payload->position, 0.045, springColor);
            appendDebugSphere(mesh, payload->position, payload->collisionShape.radius, payloadColor, 7U, 12U);
        }
    }

    const glm::dvec3 motorFoot = surfacePoint(0.0, 0.0, 0.1);
    if (const auto* anchor = physics_->body(motorAnchor_)) {
        appendDebugRod(mesh, motorFoot, anchor->position, 0.12, steel);
    }
    if (const auto* rotor = physics_->body(motorRotor_)) {
        appendDebugBox(mesh, rotor->position, rotor->orientation, {2.35, 0.10, 0.24}, motorColor);
        appendDebugSphere(mesh, rotor->position, 0.22, steel, 5U, 8U);
    }

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
        appendDebugSphere(mesh, balloon->position, balloon->collisionShape.radius, balloonColor, 9U, 14U);
        if (const auto* anchor = physics_->body(balloonAnchor_)) {
            appendDebugSphere(mesh, anchor->position, 0.16, steel, 5U, 8U);
            appendDebugRod(mesh, anchor->position, balloon->position, 0.025, {0.42F, 0.28F, 0.16F});
        }
    }

    for (std::size_t i = 0; i < fallingBodies_.size(); ++i) {
        const auto* body = physics_->body(fallingBodies_[i]);
        if (body == nullptr) continue;
        const float f = static_cast<float>(i) / static_cast<float>(std::max<std::size_t>(1U, fallingBodies_.size() - 1U));
        const glm::vec3 color{0.35F + 0.45F * f, 0.35F, 0.82F - 0.35F * f};
        appendDebugSphere(mesh, body->position, body->collisionShape.radius, color, 7U, 10U);
    }

    appendDebugRod(mesh, tree_.rootPosition, tree_.tipPosition(), tree_.trunkRadius, treeColor);
    appendDebugSphere(mesh, tree_.tipPosition(), 0.75, {0.18F, 0.48F, 0.15F}, 6U, 10U);

    const auto ropeParticles = rope_.particles();
    for (std::size_t i = 0; i + 1U < ropeParticles.size(); ++i) {
        if (rope_.linkBroken(i)) continue;
        appendDebugRod(
            mesh,
            ropeParticles[i].position,
            ropeParticles[i + 1U].position,
            rope_.material().radiusMeters,
            ropeColor);
    }
    if (const auto* payload = physics_->body(ropePayload_)) {
        appendDebugSphere(mesh, payload->position, payload->collisionShape.radius, ropePayloadColor, 7U, 11U);
    }
    appendDebugSphere(mesh, ropeGroundAnchor_, 0.13, steel, 5U, 8U);

    return mesh;
}

} // namespace vf
