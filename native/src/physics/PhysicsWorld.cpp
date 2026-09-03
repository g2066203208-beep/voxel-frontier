#include "vf/physics/PhysicsWorld.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <utility>

namespace vf {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;
constexpr double kEpsilon = 1.0e-9;

[[nodiscard]] glm::dvec3 safeNormalize(const glm::dvec3& value, const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
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
    RigidBody body{};
    body.id = nextBodyId_++;
    body.motionType = desc.motionType;
    body.mass = desc.motionType == MotionType::Dynamic ? std::max(desc.mass, 1.0e-6) : std::max(desc.mass, 0.0);
    body.inverseMass = desc.motionType == MotionType::Dynamic ? 1.0 / body.mass : 0.0;
    body.position = desc.position;
    body.orientation = glm::normalize(desc.orientation);
    body.linearVelocity = desc.linearVelocity;
    body.angularVelocity = desc.angularVelocity;
    body.inertiaDiagonal = glm::max(desc.inertiaDiagonal, glm::dvec3{1.0e-6});
    body.inverseInertiaDiagonal = desc.motionType == MotionType::Dynamic
        ? glm::dvec3{1.0 / body.inertiaDiagonal.x, 1.0 / body.inertiaDiagonal.y, 1.0 / body.inertiaDiagonal.z}
        : glm::dvec3{};
    body.collisionRadius = std::max(0.001, desc.collisionRadius);
    body.linearDamping = std::max(0.0, desc.linearDamping);
    body.angularDamping = std::max(0.0, desc.angularDamping);
    body.material = desc.material;
    body.aerodynamics = desc.aerodynamics;
    body.buoyancy = desc.buoyancy;
    bodies_.push_back(body);
    return body.id;
}

RigidBody* PhysicsWorld::body(std::uint32_t id) noexcept {
    const auto it = std::find_if(bodies_.begin(), bodies_.end(), [id](const RigidBody& candidate) { return candidate.id == id; });
    return it == bodies_.end() ? nullptr : &*it;
}

const RigidBody* PhysicsWorld::body(std::uint32_t id) const noexcept {
    const auto it = std::find_if(bodies_.begin(), bodies_.end(), [id](const RigidBody& candidate) { return candidate.id == id; });
    return it == bodies_.end() ? nullptr : &*it;
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
    for (auto& body : bodies_) {
        if (body.motionType == MotionType::Dynamic && !body.sleeping) applyEnvironmentForces(body);
    }
    for (auto& body : bodies_) integrateBody(body);
    for (auto& body : bodies_) solvePlanetContact(body);
    solveBodyContacts();
    for (auto& body : bodies_) updateSleeping(body);

    simulationTime_ += fixedDeltaSeconds_;
    ++stepIndex_;
}

void PhysicsWorld::applyEnvironmentForces(RigidBody& body) {
    const glm::dvec3 gravityAcceleration = environment_.gravityAcceleration(body.position);
    const double gravity = glm::length(gravityAcceleration);
    body.accumulatedForce += body.mass * gravityAcceleration;

    const AtmosphereSample atmosphere = environment_.sampleAtmosphere(body.position, simulationTime_);
    const glm::dvec3 relativeAirVelocity = body.linearVelocity - atmosphere.windVelocity;
    const double airSpeed = glm::length(relativeAirVelocity);
    if (airSpeed > 1.0e-5 && atmosphere.densityKgPerM3 > 0.0) {
        const glm::dvec3 flowDirection = relativeAirVelocity / airSpeed;
        const double dynamicPressure = 0.5 * atmosphere.densityKgPerM3 * airSpeed * airSpeed;
        const double dragMagnitude = dynamicPressure * std::max(0.0, body.aerodynamics.dragCoefficient) * std::max(0.0, body.aerodynamics.referenceArea);
        body.accumulatedForce -= flowDirection * dragMagnitude;

        if (std::abs(body.aerodynamics.liftCoefficient) > 1.0e-8 && body.aerodynamics.liftArea > 0.0) {
            const glm::dvec3 liftAxis = safeNormalize(body.orientation * body.aerodynamics.localLiftAxis);
            glm::dvec3 liftDirection = liftAxis - flowDirection * glm::dot(liftAxis, flowDirection);
            const double liftLength = glm::length(liftDirection);
            if (liftLength > 1.0e-6) {
                liftDirection /= liftLength;
                const double liftMagnitude = dynamicPressure * body.aerodynamics.liftCoefficient * body.aerodynamics.liftArea;
                body.accumulatedForce += liftDirection * liftMagnitude;
            }
        }
    }

    if (body.buoyancy.enabled && body.buoyancy.displaceAtmosphere && body.buoyancy.displacedVolume > 0.0 && gravity > 0.0) {
        const glm::dvec3 outward = -safeNormalize(gravityAcceleration);
        body.accumulatedForce += outward * (atmosphere.densityKgPerM3 * body.buoyancy.displacedVolume * gravity);
    }

    if (!body.buoyancy.enabled || !environment_.ocean.enabled || body.buoyancy.displacedVolume <= 0.0) return;
    const double radialDistance = glm::length(body.position);
    const double centerDepth = environment_.ocean.surfaceRadius - radialDistance;
    const double submergedFraction = sphereSubmergedFraction(body.collisionRadius, centerDepth);
    if (submergedFraction <= 0.0) return;

    const glm::dvec3 outward = safeNormalize(body.position);
    const double displacedVolume = body.buoyancy.displacedVolume * submergedFraction;
    body.accumulatedForce += outward * (environment_.ocean.densityKgPerM3 * displacedVolume * gravity);

    const glm::dvec3 relativeWaterVelocity = body.linearVelocity - environment_.fluidVelocity(body.position, simulationTime_);
    const double waterSpeed = glm::length(relativeWaterVelocity);
    if (waterSpeed > 1.0e-5) {
        const double waterDrag = 0.5 * environment_.ocean.densityKgPerM3 * waterSpeed * waterSpeed
            * std::max(0.0, body.buoyancy.fluidDragCoefficient)
            * std::max(0.0, body.buoyancy.fluidReferenceArea)
            * submergedFraction;
        body.accumulatedForce -= (relativeWaterVelocity / waterSpeed) * waterDrag;
    }
}

void PhysicsWorld::integrateBody(RigidBody& body) {
    if (body.motionType != MotionType::Dynamic || body.sleeping) {
        body.accumulatedForce = {};
        body.accumulatedTorque = {};
        return;
    }

    const double dt = fixedDeltaSeconds_;
    body.linearVelocity += body.accumulatedForce * body.inverseMass * dt;

    const glm::dmat3 rotation = glm::mat3_cast(body.orientation);
    const glm::dmat3 worldInertia = rotation * diagonalMatrix(body.inertiaDiagonal) * glm::transpose(rotation);
    const glm::dmat3 worldInverseInertia = rotation * diagonalMatrix(body.inverseInertiaDiagonal) * glm::transpose(rotation);
    const glm::dvec3 gyroscopicTorque = glm::cross(body.angularVelocity, worldInertia * body.angularVelocity);
    body.angularVelocity += worldInverseInertia * (body.accumulatedTorque - gyroscopicTorque) * dt;

    body.linearVelocity *= std::exp(-body.linearDamping * dt);
    body.angularVelocity *= std::exp(-body.angularDamping * dt);
    body.position += body.linearVelocity * dt;

    const glm::dquat angularVelocityQuat{0.0, body.angularVelocity.x, body.angularVelocity.y, body.angularVelocity.z};
    const glm::dquat derivative = 0.5 * angularVelocityQuat * body.orientation;
    body.orientation = glm::normalize(body.orientation + derivative * dt);

    body.accumulatedForce = {};
    body.accumulatedTorque = {};
}

void PhysicsWorld::solvePlanetContact(RigidBody& body) {
    if (body.motionType != MotionType::Dynamic || body.sleeping) return;
    const double distance = glm::length(body.position);
    if (distance <= kEpsilon) return;

    const glm::dvec3 normal = body.position / distance;
    const double surfaceRadius = planetSurfaceRadius(environment_.planet, normal);
    const double minimumCenterRadius = surfaceRadius + body.collisionRadius;
    const double penetration = minimumCenterRadius - distance;
    if (penetration <= 0.0) return;

    body.position += normal * penetration;
    const double normalVelocity = glm::dot(body.linearVelocity, normal);
    double normalImpulseMagnitude = 0.0;
    if (normalVelocity < 0.0) {
        normalImpulseMagnitude = -(1.0 + std::clamp(body.material.restitution, 0.0, 1.0)) * normalVelocity / body.inverseMass;
        body.applyLinearImpulse(normal * normalImpulseMagnitude);
    }

    const glm::dvec3 tangentVelocity = body.linearVelocity - normal * glm::dot(body.linearVelocity, normal);
    const double tangentSpeed = glm::length(tangentVelocity);
    if (tangentSpeed > 1.0e-7) {
        const double supportingImpulse = std::max(normalImpulseMagnitude, body.mass * environment_.gravityMagnitude(body.position) * fixedDeltaSeconds_);
        const double maxFrictionImpulse = std::max(0.0, body.material.friction) * supportingImpulse;
        const double stopImpulse = tangentSpeed / body.inverseMass;
        const double frictionImpulse = std::min(stopImpulse, maxFrictionImpulse);
        body.applyLinearImpulse(-(tangentVelocity / tangentSpeed) * frictionImpulse);
    }

    const double rollingFactor = std::exp(-std::max(0.0, body.material.rollingResistance) * 30.0 * fixedDeltaSeconds_);
    body.angularVelocity *= rollingFactor;
}

void PhysicsWorld::solveBodyContacts() {
    for (std::size_t i = 0; i < bodies_.size(); ++i) {
        for (std::size_t j = i + 1; j < bodies_.size(); ++j) {
            RigidBody& a = bodies_[i];
            RigidBody& b = bodies_[j];
            if (a.motionType == MotionType::Static && b.motionType == MotionType::Static) continue;

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
}

void PhysicsWorld::updateSleeping(RigidBody& body) {
    if (body.motionType != MotionType::Dynamic) return;
    const double linearSpeedSquared = glm::dot(body.linearVelocity, body.linearVelocity);
    const double angularSpeedSquared = glm::dot(body.angularVelocity, body.angularVelocity);
    if (linearSpeedSquared < 0.025 * 0.025 && angularSpeedSquared < 0.025 * 0.025) {
        body.sleepTimer += fixedDeltaSeconds_;
        if (body.sleepTimer >= 1.0) {
            body.sleeping = true;
            body.linearVelocity = {};
            body.angularVelocity = {};
        }
    } else {
        body.sleepTimer = 0.0;
        body.sleeping = false;
    }
}

} // namespace vf
