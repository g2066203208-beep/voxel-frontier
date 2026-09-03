#include "vf/physics/PhysicsWorld.hpp"

#include "vf/physics/Broadphase.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <utility>

namespace vf {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;
constexpr double kEpsilon = 1.0e-9;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= kEpsilon) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] glm::dmat3 diagonalMatrix(const glm::dvec3& diagonal) noexcept {
    glm::dmat3 matrix{0.0};
    matrix[0][0] = diagonal.x;
    matrix[1][1] = diagonal.y;
    matrix[2][2] = diagonal.z;
    return matrix;
}

[[nodiscard]] glm::dvec3 clampMagnitude(const glm::dvec3& value, double maxMagnitude) noexcept {
    if (!std::isfinite(maxMagnitude)) return value;
    const double magnitude = glm::length(value);
    if (magnitude <= maxMagnitude || magnitude <= kEpsilon) return value;
    return value * (maxMagnitude / magnitude);
}

[[nodiscard]] double sphereSubmergedFraction(double radius, double centerDepthBelowSurface) noexcept {
    if (radius <= kEpsilon) return centerDepthBelowSurface > 0.0 ? 1.0 : 0.0;
    if (centerDepthBelowSurface <= -radius) return 0.0;
    if (centerDepthBelowSurface >= radius) return 1.0;

    const double capHeight = std::clamp(centerDepthBelowSurface + radius, 0.0, 2.0 * radius);
    const double capVolume = kPi * capHeight * capHeight * (radius - capHeight / 3.0);
    const double sphereVolume = (4.0 / 3.0) * kPi * radius * radius * radius;
    return std::clamp(capVolume / sphereVolume, 0.0, 1.0);
}

[[nodiscard]] double combineFriction(double a, double b) noexcept {
    return std::sqrt(std::max(0.0, a) * std::max(0.0, b));
}

[[nodiscard]] glm::dvec3 worldAnchor(const RigidBody& body, const glm::dvec3& localAnchor) noexcept {
    return body.position + body.orientation * localAnchor;
}

[[nodiscard]] glm::dvec3 worldAxis(const RigidBody& body, const glm::dvec3& localAxis) noexcept {
    return safeNormalize(body.orientation * localAxis);
}

[[nodiscard]] double effectiveMassAlong(
    const RigidBody& a,
    const RigidBody& b,
    const glm::dvec3& pointA,
    const glm::dvec3& pointB,
    const glm::dvec3& direction) noexcept {
    double inverseEffectiveMass = a.inverseMass + b.inverseMass;
    const glm::dvec3 ra = pointA - a.position;
    const glm::dvec3 rb = pointB - b.position;

    if (a.motionType == MotionType::Dynamic) {
        const glm::dvec3 angular = a.worldInverseInertia() * glm::cross(ra, direction);
        inverseEffectiveMass += glm::dot(glm::cross(angular, ra), direction);
    }
    if (b.motionType == MotionType::Dynamic) {
        const glm::dvec3 angular = b.worldInverseInertia() * glm::cross(rb, direction);
        inverseEffectiveMass += glm::dot(glm::cross(angular, rb), direction);
    }
    return std::max(inverseEffectiveMass, kEpsilon);
}

[[nodiscard]] double angularInverseMassAlong(const RigidBody& body, const glm::dvec3& axis) noexcept {
    if (body.motionType != MotionType::Dynamic) return 0.0;
    return glm::dot(axis, body.worldInverseInertia() * axis);
}

} // namespace

glm::dvec3 RigidBody::linearMomentum() const noexcept {
    return mass * linearVelocity;
}

double RigidBody::kineticEnergy() const noexcept {
    const double linear = 0.5 * mass * glm::dot(linearVelocity, linearVelocity);
    const glm::dmat3 rotation = glm::mat3_cast(orientation);
    const glm::dmat3 worldInertia = rotation * diagonalMatrix(inertiaDiagonal) * glm::transpose(rotation);
    const double angular = 0.5 * glm::dot(angularVelocity, worldInertia * angularVelocity);
    return linear + angular;
}

glm::dmat3 RigidBody::worldInverseInertia() const noexcept {
    if (motionType != MotionType::Dynamic) return glm::dmat3{0.0};
    const glm::dmat3 rotation = glm::mat3_cast(orientation);
    return rotation * diagonalMatrix(inverseInertiaDiagonal) * glm::transpose(rotation);
}

glm::dvec3 RigidBody::velocityAtPoint(const glm::dvec3& worldPoint) const noexcept {
    return linearVelocity + glm::cross(angularVelocity, worldPoint - position);
}

void RigidBody::addForce(const glm::dvec3& force) noexcept {
    if (motionType != MotionType::Dynamic) return;
    accumulatedForce += force;
    wake();
}

void RigidBody::addTorque(const glm::dvec3& torque) noexcept {
    if (motionType != MotionType::Dynamic) return;
    accumulatedTorque += torque;
    wake();
}

void RigidBody::addForceAtPoint(const glm::dvec3& force, const glm::dvec3& worldPoint) noexcept {
    if (motionType != MotionType::Dynamic) return;
    accumulatedForce += force;
    accumulatedTorque += glm::cross(worldPoint - position, force);
    wake();
}

void RigidBody::applyLinearImpulse(const glm::dvec3& impulse) noexcept {
    if (motionType != MotionType::Dynamic || inverseMass <= 0.0) return;
    linearVelocity += impulse * inverseMass;
    wake();
}

void RigidBody::applyAngularImpulse(const glm::dvec3& angularImpulse) noexcept {
    if (motionType != MotionType::Dynamic) return;
    angularVelocity += worldInverseInertia() * angularImpulse;
    wake();
}

void RigidBody::applyImpulseAtPoint(const glm::dvec3& impulse, const glm::dvec3& worldPoint) noexcept {
    if (motionType != MotionType::Dynamic) return;
    applyLinearImpulse(impulse);
    applyAngularImpulse(glm::cross(worldPoint - position, impulse));
}

void RigidBody::wake() noexcept {
    if (motionType != MotionType::Dynamic) return;
    sleeping = false;
    sleepTimer = 0.0;
}

double PhysicsEnvironment::gravityMagnitude(const glm::dvec3& position) const noexcept {
    const double radius = std::max(planet.radius, 1.0);
    const double distance = std::max(glm::length(position), radius * 0.25);
    const double ratio = radius / distance;
    return std::max(0.0, surfaceGravity) * ratio * ratio;
}

glm::dvec3 PhysicsEnvironment::gravityAcceleration(const glm::dvec3& position) const noexcept {
    const glm::dvec3 outward = safeNormalize(position);
    return -outward * gravityMagnitude(position);
}

AtmosphereSample PhysicsEnvironment::sampleAtmosphere(const glm::dvec3& position, double timeSeconds) const noexcept {
    AtmosphereSample sample{};
    const double altitude = std::max(0.0, glm::length(position) - planet.radius);
    const auto& model = atmosphere;
    const double baseTemperature = std::max(120.0, model.seaLevelTemperatureK + model.temperatureOffsetK);
    const double lapse = std::max(0.0, model.lapseRateKPerM);
    sample.temperatureK = std::max(120.0, baseTemperature - lapse * altitude);

    const double g = std::max(0.01, gravityMagnitude(position));
    const double basePressure = std::max(0.0, model.seaLevelPressurePa * model.pressureScale);
    if (lapse > 1.0e-8) {
        const double exponent = g * model.molarMassKgPerMol / (model.universalGasConstant * lapse);
        const double ratio = std::max(1.0e-6, sample.temperatureK / baseTemperature);
        sample.pressurePa = basePressure * std::pow(ratio, exponent);
    } else {
        const double specificGasConstant = model.universalGasConstant / model.molarMassKgPerMol;
        sample.pressurePa = basePressure * std::exp(-g * altitude / (specificGasConstant * sample.temperatureK));
    }

    const double specificGasConstant = model.universalGasConstant / model.molarMassKgPerMol;
    sample.densityKgPerM3 = sample.temperatureK > 0.0
        ? sample.pressurePa / (specificGasConstant * sample.temperatureK)
        : 0.0;

    const glm::dvec3 outward = safeNormalize(position);
    glm::dvec3 tangentWind = model.prevailingWind - outward * glm::dot(model.prevailingWind, outward);
    const glm::dvec3 reference = std::abs(outward.y) < 0.9 ? glm::dvec3{0.0, 1.0, 0.0} : glm::dvec3{1.0, 0.0, 0.0};
    const glm::dvec3 tangentA = safeNormalize(glm::cross(reference, outward), {1.0, 0.0, 0.0});
    const glm::dvec3 tangentB = safeNormalize(glm::cross(outward, tangentA), {0.0, 0.0, 1.0});
    const double spatialScale = std::max(1.0, model.gustSpatialScale);
    const double phaseA = glm::dot(position, tangentA) / spatialScale + timeSeconds * model.gustTimeScale;
    const double phaseB = glm::dot(position, tangentB) / (spatialScale * 0.67) - timeSeconds * model.gustTimeScale * 1.37;
    const double gustStrength = model.gustAmplitude * (1.0 + 1.8 * std::clamp(weather.stormIntensity, 0.0, 1.0));
    const glm::dvec3 gust = tangentA * std::sin(phaseA) * gustStrength + tangentB * std::cos(phaseB) * gustStrength * 0.55;
    const double altitudeFade = planet.atmosphereHeight > 0.0
        ? std::exp(-altitude / std::max(1.0, planet.atmosphereHeight * 1.5))
        : 1.0;
    sample.windVelocity = (tangentWind + gust) * weather.windMultiplier * altitudeFade;
    return sample;
}

glm::dvec3 PhysicsEnvironment::fluidVelocity(const glm::dvec3& position, double timeSeconds) const noexcept {
    if (!ocean.enabled) return {};
    const glm::dvec3 outward = safeNormalize(position);
    glm::dvec3 tangent = ocean.meanCurrent - outward * glm::dot(ocean.meanCurrent, outward);
    const glm::dvec3 reference = std::abs(outward.y) < 0.9 ? glm::dvec3{0.0, 1.0, 0.0} : glm::dvec3{1.0, 0.0, 0.0};
    const glm::dvec3 waveDirection = safeNormalize(glm::cross(reference, outward), {1.0, 0.0, 0.0});
    tangent += waveDirection * (0.35 * std::sin(timeSeconds * 0.55 + glm::dot(position, waveDirection) * 0.025));
    return tangent;
}

PhysicsWorld::PhysicsWorld(PhysicsEnvironment environment) : environment_(std::move(environment)) {}

std::uint32_t PhysicsWorld::createRigidBody(const RigidBodyDesc& desc) {
    RigidBody newBody{};
    newBody.id = nextBodyId_++;
    newBody.motionType = desc.motionType;
    newBody.mass = desc.motionType == MotionType::Dynamic ? std::max(desc.mass, 1.0e-6) : std::max(desc.mass, 0.0);
    newBody.inverseMass = desc.motionType == MotionType::Dynamic ? 1.0 / newBody.mass : 0.0;
    newBody.position = desc.position;
    newBody.orientation = glm::normalize(desc.orientation);
    newBody.linearVelocity = desc.linearVelocity;
    newBody.angularVelocity = desc.angularVelocity;
    newBody.inertiaDiagonal = glm::max(desc.inertiaDiagonal, glm::dvec3{1.0e-6});
    newBody.inverseInertiaDiagonal = desc.motionType == MotionType::Dynamic
        ? glm::dvec3{1.0 / newBody.inertiaDiagonal.x, 1.0 / newBody.inertiaDiagonal.y, 1.0 / newBody.inertiaDiagonal.z}
        : glm::dvec3{};
    newBody.collisionRadius = std::max(0.001, desc.collisionRadius);
    newBody.linearDamping = std::max(0.0, desc.linearDamping);
    newBody.angularDamping = std::max(0.0, desc.angularDamping);
    newBody.material = desc.material;
    newBody.aerodynamics = desc.aerodynamics;
    newBody.buoyancy = desc.buoyancy;
    bodies_.push_back(newBody);
    return newBody.id;
}

RigidBody* PhysicsWorld::body(std::uint32_t id) noexcept {
    const auto it = std::find_if(bodies_.begin(), bodies_.end(), [id](const RigidBody& candidate) { return candidate.id == id; });
    return it == bodies_.end() ? nullptr : &*it;
}

const RigidBody* PhysicsWorld::body(std::uint32_t id) const noexcept {
    const auto it = std::find_if(bodies_.begin(), bodies_.end(), [id](const RigidBody& candidate) { return candidate.id == id; });
    return it == bodies_.end() ? nullptr : &*it;
}

std::uint32_t PhysicsWorld::createDistanceConstraint(const DistanceConstraintDesc& desc) {
    const RigidBody* a = body(desc.bodyA);
    const RigidBody* b = body(desc.bodyB);
    if (a == nullptr || b == nullptr || desc.bodyA == desc.bodyB) {
        throw std::invalid_argument("distance constraint requires two valid distinct bodies");
    }
    DistanceConstraint constraint{};
    constraint.id = nextConstraintId_++;
    constraint.bodyA = desc.bodyA;
    constraint.bodyB = desc.bodyB;
    constraint.localAnchorA = desc.localAnchorA;
    constraint.localAnchorB = desc.localAnchorB;
    constraint.restLength = desc.restLength >= 0.0
        ? desc.restLength
        : glm::length(worldAnchor(*b, desc.localAnchorB) - worldAnchor(*a, desc.localAnchorA));
    constraint.baumgarte = std::clamp(desc.baumgarte, 0.0, 1.0);
    constraint.maxForceN = std::max(0.0, desc.maxForceN);
    constraint.breakForceN = std::max(0.0, desc.breakForceN);
    distanceConstraints_.push_back(constraint);
    return constraint.id;
}

std::uint32_t PhysicsWorld::createSpringDamperConstraint(const SpringDamperConstraintDesc& desc) {
    const RigidBody* a = body(desc.bodyA);
    const RigidBody* b = body(desc.bodyB);
    if (a == nullptr || b == nullptr || desc.bodyA == desc.bodyB) {
        throw std::invalid_argument("spring-damper requires two valid distinct bodies");
    }
    SpringDamperConstraint constraint{};
    constraint.id = nextConstraintId_++;
    constraint.bodyA = desc.bodyA;
    constraint.bodyB = desc.bodyB;
    constraint.localAnchorA = desc.localAnchorA;
    constraint.localAnchorB = desc.localAnchorB;
    constraint.restLength = desc.restLength >= 0.0
        ? desc.restLength
        : glm::length(worldAnchor(*b, desc.localAnchorB) - worldAnchor(*a, desc.localAnchorA));
    constraint.stiffnessNPerM = std::max(0.0, desc.stiffnessNPerM);
    constraint.dampingNsPerM = std::max(0.0, desc.dampingNsPerM);
    constraint.maxForceN = std::max(0.0, desc.maxForceN);
    constraint.breakForceN = std::max(0.0, desc.breakForceN);
    springDamperConstraints_.push_back(constraint);
    return constraint.id;
}

std::uint32_t PhysicsWorld::createHingeConstraint(const HingeConstraintDesc& desc) {
    if (body(desc.bodyA) == nullptr || body(desc.bodyB) == nullptr || desc.bodyA == desc.bodyB) {
        throw std::invalid_argument("hinge requires two valid distinct bodies");
    }
    HingeConstraint constraint{};
    constraint.id = nextConstraintId_++;
    constraint.bodyA = desc.bodyA;
    constraint.bodyB = desc.bodyB;
    constraint.localAnchorA = desc.localAnchorA;
    constraint.localAnchorB = desc.localAnchorB;
    constraint.localAxisA = safeNormalize(desc.localAxisA);
    constraint.localAxisB = safeNormalize(desc.localAxisB);
    constraint.anchorBaumgarte = std::clamp(desc.anchorBaumgarte, 0.0, 1.0);
    constraint.axisBaumgarte = std::clamp(desc.axisBaumgarte, 0.0, 1.0);
    constraint.motorEnabled = desc.motorEnabled;
    constraint.targetAngularSpeedRadPerS = desc.targetAngularSpeedRadPerS;
    constraint.maxMotorTorqueNm = std::max(0.0, desc.maxMotorTorqueNm);
    constraint.viscousFrictionNmPerRadS = std::max(0.0, desc.viscousFrictionNmPerRadS);
    constraint.coulombFrictionTorqueNm = std::max(0.0, desc.coulombFrictionTorqueNm);
    constraint.breakForceN = std::max(0.0, desc.breakForceN);
    constraint.breakTorqueNm = std::max(0.0, desc.breakTorqueNm);
    hingeConstraints_.push_back(constraint);
    return constraint.id;
}

std::uint32_t PhysicsWorld::createGearConstraint(const GearConstraintDesc& desc) {
    if (body(desc.bodyA) == nullptr || body(desc.bodyB) == nullptr || desc.bodyA == desc.bodyB) {
        throw std::invalid_argument("gear requires two valid distinct bodies");
    }
    GearConstraint constraint{};
    constraint.id = nextConstraintId_++;
    constraint.bodyA = desc.bodyA;
    constraint.bodyB = desc.bodyB;
    constraint.localAxisA = safeNormalize(desc.localAxisA);
    constraint.localAxisB = safeNormalize(desc.localAxisB);
    constraint.ratio = std::abs(desc.ratio) > 1.0e-6 ? desc.ratio : 1.0;
    constraint.maxTorqueNm = std::max(0.0, desc.maxTorqueNm);
    constraint.breakTorqueNm = std::max(0.0, desc.breakTorqueNm);
    gearConstraints_.push_back(constraint);
    return constraint.id;
}

std::size_t PhysicsWorld::activeConstraintCount() const noexcept {
    std::size_t count = 0;
    count += static_cast<std::size_t>(std::count_if(distanceConstraints_.begin(), distanceConstraints_.end(), [](const auto& c) { return !c.broken; }));
    count += static_cast<std::size_t>(std::count_if(springDamperConstraints_.begin(), springDamperConstraints_.end(), [](const auto& c) { return !c.broken; }));
    count += static_cast<std::size_t>(std::count_if(hingeConstraints_.begin(), hingeConstraints_.end(), [](const auto& c) { return !c.broken; }));
    count += static_cast<std::size_t>(std::count_if(gearConstraints_.begin(), gearConstraints_.end(), [](const auto& c) { return !c.broken; }));
    return count;
}

void PhysicsWorld::advance(double frameDeltaSeconds) {
    accumulator_ += std::clamp(frameDeltaSeconds, 0.0, 0.25);
    std::uint32_t substeps = 0;
    constexpr std::uint32_t maxSubsteps = 24;
    while (accumulator_ >= fixedDeltaSeconds_ && substeps < maxSubsteps) {
        stepFixed();
        accumulator_ -= fixedDeltaSeconds_;
        ++substeps;
    }
    if (substeps == maxSubsteps && accumulator_ >= fixedDeltaSeconds_) {
        accumulator_ = std::fmod(accumulator_, fixedDeltaSeconds_);
    }
}

void PhysicsWorld::stepFixed() {
    applySpringDamperForces();
    for (auto& rigidBody : bodies_) {
        if (rigidBody.motionType == MotionType::Dynamic && !rigidBody.sleeping) applyEnvironmentForces(rigidBody);
    }
    for (auto& rigidBody : bodies_) integrateBody(rigidBody);
    for (auto& rigidBody : bodies_) solvePlanetContact(rigidBody);
    solveBodyContacts();
    solveMechanicalConstraints();
    for (auto& rigidBody : bodies_) solvePlanetContact(rigidBody);
    for (auto& rigidBody : bodies_) updateSleeping(rigidBody);

    simulationTime_ += fixedDeltaSeconds_;
    ++stepIndex_;
}

void PhysicsWorld::applySpringDamperForces() {
    for (auto& spring : springDamperConstraints_) {
        if (spring.broken) continue;
        RigidBody* a = body(spring.bodyA);
        RigidBody* b = body(spring.bodyB);
        if (a == nullptr || b == nullptr) {
            spring.broken = true;
            continue;
        }

        const glm::dvec3 pointA = worldAnchor(*a, spring.localAnchorA);
        const glm::dvec3 pointB = worldAnchor(*b, spring.localAnchorB);
        const glm::dvec3 delta = pointB - pointA;
        const double length = glm::length(delta);
        if (length <= kEpsilon) continue;
        const glm::dvec3 direction = delta / length;
        const double extension = length - spring.restLength;
        const double relativeSpeed = glm::dot(b->velocityAtPoint(pointB) - a->velocityAtPoint(pointA), direction);
        double forceMagnitude = spring.stiffnessNPerM * extension + spring.dampingNsPerM * relativeSpeed;
        spring.lastForceN = std::abs(forceMagnitude);
        if (spring.lastForceN > spring.breakForceN) {
            spring.broken = true;
            continue;
        }
        forceMagnitude = std::clamp(forceMagnitude, -spring.maxForceN, spring.maxForceN);
        const glm::dvec3 force = direction * forceMagnitude;
        a->addForceAtPoint(force, pointA);
        b->addForceAtPoint(-force, pointB);
    }
}

void PhysicsWorld::applyEnvironmentForces(RigidBody& rigidBody) {
    const glm::dvec3 gravityAcceleration = environment_.gravityAcceleration(rigidBody.position);
    const double gravity = glm::length(gravityAcceleration);
    rigidBody.accumulatedForce += rigidBody.mass * gravityAcceleration;

    const AtmosphereSample atmosphere = environment_.sampleAtmosphere(rigidBody.position, simulationTime_);
    const glm::dvec3 relativeAirVelocity = rigidBody.linearVelocity - atmosphere.windVelocity;
    const double airSpeed = glm::length(relativeAirVelocity);
    if (airSpeed > 1.0e-5 && atmosphere.densityKgPerM3 > 0.0) {
        const glm::dvec3 flowDirection = relativeAirVelocity / airSpeed;
        const double dynamicPressure = 0.5 * atmosphere.densityKgPerM3 * airSpeed * airSpeed;
        const double dragMagnitude = dynamicPressure * std::max(0.0, rigidBody.aerodynamics.dragCoefficient)
            * std::max(0.0, rigidBody.aerodynamics.referenceArea);
        rigidBody.accumulatedForce -= flowDirection * dragMagnitude;

        if (std::abs(rigidBody.aerodynamics.liftCoefficient) > 1.0e-8 && rigidBody.aerodynamics.liftArea > 0.0) {
            const glm::dvec3 liftAxis = safeNormalize(rigidBody.orientation * rigidBody.aerodynamics.localLiftAxis);
            glm::dvec3 liftDirection = liftAxis - flowDirection * glm::dot(liftAxis, flowDirection);
            const double liftLength = glm::length(liftDirection);
            if (liftLength > 1.0e-6) {
                liftDirection /= liftLength;
                const double liftMagnitude = dynamicPressure * rigidBody.aerodynamics.liftCoefficient * rigidBody.aerodynamics.liftArea;
                rigidBody.accumulatedForce += liftDirection * liftMagnitude;
            }
        }
    }

    if (rigidBody.buoyancy.enabled && rigidBody.buoyancy.displaceAtmosphere
        && rigidBody.buoyancy.displacedVolume > 0.0 && gravity > 0.0) {
        const glm::dvec3 outward = -safeNormalize(gravityAcceleration);
        rigidBody.accumulatedForce += outward
            * (atmosphere.densityKgPerM3 * rigidBody.buoyancy.displacedVolume * gravity);
    }

    if (!rigidBody.buoyancy.enabled || !environment_.ocean.enabled || rigidBody.buoyancy.displacedVolume <= 0.0) return;
    const double radialDistance = glm::length(rigidBody.position);
    const double centerDepth = environment_.ocean.surfaceRadius - radialDistance;
    const double submergedFraction = sphereSubmergedFraction(rigidBody.collisionRadius, centerDepth);
    if (submergedFraction <= 0.0) return;

    const glm::dvec3 outward = safeNormalize(rigidBody.position);
    const double displacedVolume = rigidBody.buoyancy.displacedVolume * submergedFraction;
    rigidBody.accumulatedForce += outward * (environment_.ocean.densityKgPerM3 * displacedVolume * gravity);

    const glm::dvec3 relativeWaterVelocity = rigidBody.linearVelocity - environment_.fluidVelocity(rigidBody.position, simulationTime_);
    const double waterSpeed = glm::length(relativeWaterVelocity);
    if (waterSpeed > 1.0e-5) {
        const double waterDrag = 0.5 * environment_.ocean.densityKgPerM3 * waterSpeed * waterSpeed
            * std::max(0.0, rigidBody.buoyancy.fluidDragCoefficient)
            * std::max(0.0, rigidBody.buoyancy.fluidReferenceArea)
            * submergedFraction;
        rigidBody.accumulatedForce -= (relativeWaterVelocity / waterSpeed) * waterDrag;
    }
}

void PhysicsWorld::integrateBody(RigidBody& rigidBody) {
    if (rigidBody.motionType != MotionType::Dynamic || rigidBody.sleeping) {
        rigidBody.accumulatedForce = {};
        rigidBody.accumulatedTorque = {};
        return;
    }

    const double dt = fixedDeltaSeconds_;
    rigidBody.linearVelocity += rigidBody.accumulatedForce * rigidBody.inverseMass * dt;

    const glm::dmat3 rotation = glm::mat3_cast(rigidBody.orientation);
    const glm::dmat3 worldInertia = rotation * diagonalMatrix(rigidBody.inertiaDiagonal) * glm::transpose(rotation);
    const glm::dmat3 worldInverseInertia = rigidBody.worldInverseInertia();
    const glm::dvec3 gyroscopicTorque = glm::cross(rigidBody.angularVelocity, worldInertia * rigidBody.angularVelocity);
    rigidBody.angularVelocity += worldInverseInertia * (rigidBody.accumulatedTorque - gyroscopicTorque) * dt;

    rigidBody.linearVelocity *= std::exp(-rigidBody.linearDamping * dt);
    rigidBody.angularVelocity *= std::exp(-rigidBody.angularDamping * dt);
    rigidBody.position += rigidBody.linearVelocity * dt;

    const glm::dquat angularVelocityQuat{0.0, rigidBody.angularVelocity.x, rigidBody.angularVelocity.y, rigidBody.angularVelocity.z};
    const glm::dquat derivative = 0.5 * angularVelocityQuat * rigidBody.orientation;
    rigidBody.orientation = glm::normalize(rigidBody.orientation + derivative * dt);

    rigidBody.accumulatedForce = {};
    rigidBody.accumulatedTorque = {};
}

void PhysicsWorld::solvePlanetContact(RigidBody& rigidBody) {
    if (rigidBody.motionType != MotionType::Dynamic || rigidBody.sleeping) return;
    const double distance = glm::length(rigidBody.position);
    if (distance <= kEpsilon) return;

    const glm::dvec3 normal = rigidBody.position / distance;
    const double surfaceRadius = planetSurfaceRadius(environment_.planet, normal);
    const double minimumCenterRadius = surfaceRadius + rigidBody.collisionRadius;
    const double penetration = minimumCenterRadius - distance;
    if (penetration <= 0.0) return;

    rigidBody.position += normal * penetration;
    const double normalVelocity = glm::dot(rigidBody.linearVelocity, normal);
    double normalImpulseMagnitude = 0.0;
    if (normalVelocity < 0.0) {
        normalImpulseMagnitude = -(1.0 + std::clamp(rigidBody.material.restitution, 0.0, 1.0))
            * normalVelocity / rigidBody.inverseMass;
        rigidBody.applyLinearImpulse(normal * normalImpulseMagnitude);
    }

    const glm::dvec3 tangentVelocity = rigidBody.linearVelocity - normal * glm::dot(rigidBody.linearVelocity, normal);
    const double tangentSpeed = glm::length(tangentVelocity);
    if (tangentSpeed > 1.0e-7) {
        const double supportingImpulse = std::max(
            normalImpulseMagnitude,
            rigidBody.mass * environment_.gravityMagnitude(rigidBody.position) * fixedDeltaSeconds_);
        const double maxFrictionImpulse = std::max(0.0, rigidBody.material.friction) * supportingImpulse;
        const double stopImpulse = tangentSpeed / rigidBody.inverseMass;
        const double frictionImpulse = std::min(stopImpulse, maxFrictionImpulse);
        rigidBody.applyLinearImpulse(-(tangentVelocity / tangentSpeed) * frictionImpulse);
    }

    const double rollingFactor = std::exp(
        -std::max(0.0, rigidBody.material.rollingResistance) * 30.0 * fixedDeltaSeconds_);
    rigidBody.angularVelocity *= rollingFactor;
}

void PhysicsWorld::solveBodyContacts() {
    const std::vector<BroadphasePair> pairs = buildSweepAndPrunePairs(bodies_);
    lastBroadphaseCandidateCount_ = pairs.size();

    for (const auto& pair : pairs) {
        RigidBody& a = bodies_[pair.bodyIndexA];
        RigidBody& b = bodies_[pair.bodyIndexB];

        const glm::dvec3 delta = b.position - a.position;
        const double distanceSquared = glm::dot(delta, delta);
        const double radius = a.collisionRadius + b.collisionRadius;
        if (distanceSquared >= radius * radius) continue;

        const double distance = std::sqrt(std::max(distanceSquared, 1.0e-12));
        const glm::dvec3 normal = distance > 1.0e-6 ? delta / distance : glm::dvec3{1.0, 0.0, 0.0};
        const double inverseMassSum = a.inverseMass + b.inverseMass;
        if (inverseMassSum <= 0.0) continue;

        const double penetration = radius - distance;
        const double correctionMagnitude = std::max(0.0, penetration - 1.0e-4) * 0.8 / inverseMassSum;
        const glm::dvec3 correction = normal * correctionMagnitude;
        if (a.motionType == MotionType::Dynamic) a.position -= correction * a.inverseMass;
        if (b.motionType == MotionType::Dynamic) b.position += correction * b.inverseMass;

        glm::dvec3 relativeVelocity = b.linearVelocity - a.linearVelocity;
        const double normalVelocity = glm::dot(relativeVelocity, normal);
        double normalImpulseMagnitude = 0.0;
        if (normalVelocity < 0.0) {
            const double restitution = std::min(
                std::clamp(a.material.restitution, 0.0, 1.0),
                std::clamp(b.material.restitution, 0.0, 1.0));
            normalImpulseMagnitude = -(1.0 + restitution) * normalVelocity / inverseMassSum;
            const glm::dvec3 impulse = normal * normalImpulseMagnitude;
            if (a.motionType == MotionType::Dynamic) a.applyLinearImpulse(-impulse);
            if (b.motionType == MotionType::Dynamic) b.applyLinearImpulse(impulse);
        }

        relativeVelocity = b.linearVelocity - a.linearVelocity;
        glm::dvec3 tangent = relativeVelocity - normal * glm::dot(relativeVelocity, normal);
        const double tangentSpeed = glm::length(tangent);
        if (tangentSpeed > 1.0e-7 && normalImpulseMagnitude > 0.0) {
            tangent /= tangentSpeed;
            double tangentImpulse = -glm::dot(relativeVelocity, tangent) / inverseMassSum;
            const double friction = combineFriction(a.material.friction, b.material.friction);
            const double limit = friction * normalImpulseMagnitude;
            tangentImpulse = std::clamp(tangentImpulse, -limit, limit);
            const glm::dvec3 frictionImpulse = tangent * tangentImpulse;
            if (a.motionType == MotionType::Dynamic) a.applyLinearImpulse(-frictionImpulse);
            if (b.motionType == MotionType::Dynamic) b.applyLinearImpulse(frictionImpulse);
        }
    }
}

void PhysicsWorld::solveMechanicalConstraints() {
    const double dt = fixedDeltaSeconds_;

    // Warm-start persistent impulses from the previous fixed step.
    for (auto& constraint : distanceConstraints_) {
        if (constraint.broken || std::abs(constraint.accumulatedImpulse) <= 1.0e-10) continue;
        RigidBody* a = body(constraint.bodyA);
        RigidBody* b = body(constraint.bodyB);
        if (a == nullptr || b == nullptr) continue;
        const glm::dvec3 pointA = worldAnchor(*a, constraint.localAnchorA);
        const glm::dvec3 pointB = worldAnchor(*b, constraint.localAnchorB);
        const glm::dvec3 direction = safeNormalize(pointB - pointA, {1.0, 0.0, 0.0});
        constraint.accumulatedImpulse *= 0.75;
        const glm::dvec3 impulse = direction * constraint.accumulatedImpulse;
        a->applyImpulseAtPoint(-impulse, pointA);
        b->applyImpulseAtPoint(impulse, pointB);
    }
    for (auto& hinge : hingeConstraints_) {
        if (hinge.broken || std::abs(hinge.accumulatedMotorImpulse) <= 1.0e-10) continue;
        RigidBody* a = body(hinge.bodyA);
        RigidBody* b = body(hinge.bodyB);
        if (a == nullptr || b == nullptr) continue;
        const glm::dvec3 axis = safeNormalize(worldAxis(*a, hinge.localAxisA) + worldAxis(*b, hinge.localAxisB));
        hinge.accumulatedMotorImpulse *= 0.75;
        a->applyAngularImpulse(-axis * hinge.accumulatedMotorImpulse);
        b->applyAngularImpulse(axis * hinge.accumulatedMotorImpulse);
    }

    constexpr std::uint32_t solverIterations = 10;
    for (std::uint32_t iteration = 0; iteration < solverIterations; ++iteration) {
        for (auto& constraint : distanceConstraints_) {
            if (constraint.broken) continue;
            RigidBody* a = body(constraint.bodyA);
            RigidBody* b = body(constraint.bodyB);
            if (a == nullptr || b == nullptr) {
                constraint.broken = true;
                continue;
            }

            const glm::dvec3 pointA = worldAnchor(*a, constraint.localAnchorA);
            const glm::dvec3 pointB = worldAnchor(*b, constraint.localAnchorB);
            const glm::dvec3 delta = pointB - pointA;
            const double length = glm::length(delta);
            if (length <= kEpsilon) continue;
            const glm::dvec3 direction = delta / length;
            const double relativeSpeed = glm::dot(b->velocityAtPoint(pointB) - a->velocityAtPoint(pointA), direction);
            const double error = length - constraint.restLength;
            const double inverseEffectiveMass = effectiveMassAlong(*a, *b, pointA, pointB, direction);
            const double lambda = -(relativeSpeed + constraint.baumgarte * error / dt) / inverseEffectiveMass;
            const double maxImpulse = constraint.maxForceN * dt;
            const double previousImpulse = constraint.accumulatedImpulse;
            constraint.accumulatedImpulse = std::clamp(previousImpulse + lambda, -maxImpulse, maxImpulse);
            const double deltaImpulse = constraint.accumulatedImpulse - previousImpulse;
            constraint.lastForceN = std::abs(constraint.accumulatedImpulse) / dt;
            if (constraint.lastForceN > constraint.breakForceN) {
                constraint.broken = true;
                constraint.accumulatedImpulse = 0.0;
                continue;
            }
            const glm::dvec3 impulse = direction * deltaImpulse;
            a->applyImpulseAtPoint(-impulse, pointA);
            b->applyImpulseAtPoint(impulse, pointB);
        }

        for (auto& hinge : hingeConstraints_) {
            if (hinge.broken) continue;
            RigidBody* a = body(hinge.bodyA);
            RigidBody* b = body(hinge.bodyB);
            if (a == nullptr || b == nullptr) {
                hinge.broken = true;
                continue;
            }

            const glm::dvec3 pointA = worldAnchor(*a, hinge.localAnchorA);
            const glm::dvec3 pointB = worldAnchor(*b, hinge.localAnchorB);
            const glm::dvec3 anchorError = pointB - pointA;
            const glm::dvec3 relativePointVelocity = b->velocityAtPoint(pointB) - a->velocityAtPoint(pointA);
            const double inverseMassSum = std::max(a->inverseMass + b->inverseMass, kEpsilon);
            glm::dvec3 anchorImpulse = -(relativePointVelocity + hinge.anchorBaumgarte * anchorError / dt) / inverseMassSum;
            const double maxAnchorImpulse = hinge.breakForceN * dt;
            anchorImpulse = clampMagnitude(anchorImpulse, maxAnchorImpulse);
            hinge.lastAnchorForceN = glm::length(anchorImpulse) / dt;
            if (hinge.lastAnchorForceN > hinge.breakForceN) {
                hinge.broken = true;
                continue;
            }
            a->applyImpulseAtPoint(-anchorImpulse, pointA);
            b->applyImpulseAtPoint(anchorImpulse, pointB);

            const glm::dvec3 axisA = worldAxis(*a, hinge.localAxisA);
            const glm::dvec3 axisB = worldAxis(*b, hinge.localAxisB);
            const glm::dvec3 hingeAxis = safeNormalize(axisA + axisB, axisA);
            const glm::dvec3 alignmentError = glm::cross(axisA, axisB);
            const glm::dvec3 relativeAngularVelocity = b->angularVelocity - a->angularVelocity;
            const glm::dvec3 perpendicularAngularVelocity = relativeAngularVelocity
                - hingeAxis * glm::dot(relativeAngularVelocity, hingeAxis);
            const glm::dvec3 correctionVelocity = perpendicularAngularVelocity + hinge.axisBaumgarte * alignmentError / dt;

            const glm::dmat3 inverseAngularMass = a->worldInverseInertia() + b->worldInverseInertia();
            glm::dvec3 axisImpulse{};
            const double determinant = glm::determinant(inverseAngularMass);
            if (std::abs(determinant) > 1.0e-12) {
                axisImpulse = -glm::inverse(inverseAngularMass) * correctionVelocity;
            }
            const double maxAxisImpulse = hinge.breakTorqueNm * dt;
            axisImpulse = clampMagnitude(axisImpulse, maxAxisImpulse);
            hinge.lastAxisTorqueNm = glm::length(axisImpulse) / dt;
            if (hinge.lastAxisTorqueNm > hinge.breakTorqueNm) {
                hinge.broken = true;
                continue;
            }
            a->applyAngularImpulse(-axisImpulse);
            b->applyAngularImpulse(axisImpulse);

            const double relativeHingeSpeed = glm::dot(b->angularVelocity - a->angularVelocity, hingeAxis);
            const double inverseAngularMassAlong = angularInverseMassAlong(*a, hingeAxis)
                + angularInverseMassAlong(*b, hingeAxis);
            if (inverseAngularMassAlong <= kEpsilon) continue;

            if (hinge.motorEnabled && hinge.maxMotorTorqueNm > 0.0) {
                const double desiredImpulse = (hinge.targetAngularSpeedRadPerS - relativeHingeSpeed) / inverseAngularMassAlong;
                const double maxMotorImpulse = hinge.maxMotorTorqueNm * dt;
                const double previousMotorImpulse = hinge.accumulatedMotorImpulse;
                hinge.accumulatedMotorImpulse = std::clamp(
                    previousMotorImpulse + desiredImpulse,
                    -maxMotorImpulse,
                    maxMotorImpulse);
                const double deltaMotorImpulse = hinge.accumulatedMotorImpulse - previousMotorImpulse;
                a->applyAngularImpulse(-hingeAxis * deltaMotorImpulse);
                b->applyAngularImpulse(hingeAxis * deltaMotorImpulse);
            }

            if (hinge.viscousFrictionNmPerRadS > 0.0 || hinge.coulombFrictionTorqueNm > 0.0) {
                double frictionTorque = -hinge.viscousFrictionNmPerRadS * relativeHingeSpeed;
                if (std::abs(relativeHingeSpeed) > 1.0e-7) {
                    frictionTorque -= std::copysign(hinge.coulombFrictionTorqueNm, relativeHingeSpeed);
                }
                const double frictionImpulse = frictionTorque * dt;
                a->applyAngularImpulse(-hingeAxis * frictionImpulse);
                b->applyAngularImpulse(hingeAxis * frictionImpulse);
            }
        }

        for (auto& gear : gearConstraints_) {
            if (gear.broken) continue;
            RigidBody* a = body(gear.bodyA);
            RigidBody* b = body(gear.bodyB);
            if (a == nullptr || b == nullptr) {
                gear.broken = true;
                continue;
            }
            const glm::dvec3 axisA = worldAxis(*a, gear.localAxisA);
            const glm::dvec3 axisB = worldAxis(*b, gear.localAxisB);
            const double speedA = glm::dot(a->angularVelocity, axisA);
            const double speedB = glm::dot(b->angularVelocity, axisB);
            const double constraintSpeed = speedA + gear.ratio * speedB;
            const double inverseEffectiveMass = angularInverseMassAlong(*a, axisA)
                + gear.ratio * gear.ratio * angularInverseMassAlong(*b, axisB);
            if (inverseEffectiveMass <= kEpsilon) continue;
            double impulse = -constraintSpeed / inverseEffectiveMass;
            const double maxImpulse = gear.maxTorqueNm * dt;
            impulse = std::clamp(impulse, -maxImpulse, maxImpulse);
            gear.lastTorqueNm = std::abs(impulse) / dt;
            if (gear.lastTorqueNm > gear.breakTorqueNm) {
                gear.broken = true;
                continue;
            }
            a->applyAngularImpulse(axisA * impulse);
            b->applyAngularImpulse(axisB * (gear.ratio * impulse));
        }
    }
}

void PhysicsWorld::updateSleeping(RigidBody& rigidBody) {
    if (rigidBody.motionType != MotionType::Dynamic) return;
    const double linearSpeedSquared = glm::dot(rigidBody.linearVelocity, rigidBody.linearVelocity);
    const double angularSpeedSquared = glm::dot(rigidBody.angularVelocity, rigidBody.angularVelocity);
    if (linearSpeedSquared < 0.025 * 0.025 && angularSpeedSquared < 0.025 * 0.025) {
        rigidBody.sleepTimer += fixedDeltaSeconds_;
        if (rigidBody.sleepTimer >= 1.0) {
            rigidBody.sleeping = true;
            rigidBody.linearVelocity = {};
            rigidBody.angularVelocity = {};
        }
    } else {
        rigidBody.sleepTimer = 0.0;
        rigidBody.sleeping = false;
    }
}

} // namespace vf
