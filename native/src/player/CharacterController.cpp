#include "vf/player/CharacterController.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

#include <glm/geometric.hpp>
#include <glm/gtc/quaternion.hpp>

namespace vf {
namespace {

constexpr double kEpsilon = 1.0e-9;
constexpr double kPi = 3.1415926535897932384626433832795;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= kEpsilon) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] glm::dquat rotateYAxisTo(const glm::dvec3& upInput) noexcept {
    const glm::dvec3 up = safeNormalize(upInput);
    const glm::dvec3 y{0.0, 1.0, 0.0};
    const double cosine = std::clamp(glm::dot(y, up), -1.0, 1.0);
    if (cosine > 1.0 - 1.0e-10) return {1.0, 0.0, 0.0, 0.0};
    if (cosine < -1.0 + 1.0e-10) return glm::angleAxis(kPi, glm::dvec3{1.0, 0.0, 0.0});
    const glm::dvec3 axis = safeNormalize(glm::cross(y, up), {1.0, 0.0, 0.0});
    return glm::normalize(glm::angleAxis(std::acos(cosine), axis));
}

[[nodiscard]] const CelestialBody* primaryBody(const PhysicsEnvironment& environment) noexcept {
    if (environment.celestialSystem == nullptr || environment.primaryCelestialBodyId == 0U) return nullptr;
    return environment.celestialSystem->body(environment.primaryCelestialBodyId);
}

[[nodiscard]] glm::dvec3 bodyLocalDirection(
    const CelestialBody& body,
    const glm::dvec3& worldDirection) noexcept {
    return safeNormalize(glm::conjugate(glm::normalize(body.orientation)) * worldDirection);
}

[[nodiscard]] glm::dvec3 bodyWorldNormal(
    const CelestialBody& body,
    const PlanetDefinition& planet,
    const glm::dvec3& worldDirection) noexcept {
    const glm::dvec3 localDirection = bodyLocalDirection(body, worldDirection);
    return safeNormalize(glm::normalize(body.orientation) * planetSurfaceNormal(planet, localDirection), worldDirection);
}

} // namespace

CharacterController::CharacterController(PhysicsWorld& world, CharacterControllerSettings settings)
    : world_(&world), settings_(settings), capsule_(CollisionShape::capsule(settings.radius, settings.halfHeight)) {
    settings_.radius = std::max(0.05, settings_.radius);
    settings_.halfHeight = std::max(0.0, settings_.halfHeight);
    settings_.eyeHeight = std::max(settings_.radius + settings_.halfHeight + 0.05, settings_.eyeHeight);
    settings_.contactOffset = std::clamp(settings_.contactOffset, 0.001, 0.20);
    settings_.maxSlopeAngleRadians = std::clamp(settings_.maxSlopeAngleRadians, 0.0, 0.5 * kPi - 0.01);
    settings_.stepHeight = std::max(0.0, settings_.stepHeight);
    settings_.stickToFloorDistance = std::max(settings_.contactOffset, settings_.stickToFloorDistance);
    settings_.maxMoveSubstep = std::clamp(settings_.maxMoveSubstep, 0.05, 0.5);
    settings_.maxDepenetrationIterations = std::clamp<std::uint32_t>(settings_.maxDepenetrationIterations, 1U, 20U);
    settings_.characterMassKg = std::max(1.0, settings_.characterMassKg);
    settings_.maxPushImpulseNs = std::max(0.0, settings_.maxPushImpulseNs);
    capsule_ = CollisionShape::capsule(settings_.radius, settings_.halfHeight);
}

void CharacterController::resetFromEye(
    const glm::dvec3& eyePositionInput,
    const glm::dvec3& linearVelocity,
    bool groundedHint) noexcept {
    up_ = gravityUpAt(eyePositionInput);
    const double centerToEye = settings_.eyeHeight - (settings_.radius + settings_.halfHeight);
    position_ = eyePositionInput - up_ * centerToEye;
    velocity_ = linearVelocity;
    grounded_ = groundedHint;
    groundNormal_ = up_;
    groundBodyId_ = 0U;

    glm::dvec3 corrected = position_;
    glm::dvec3 correctedVelocity = velocity_;
    const ResolveResult resolved = resolveAll(corrected, correctedVelocity, false);
    position_ = corrected;
    velocity_ = correctedVelocity;
    if (resolved.supported) {
        grounded_ = true;
        groundNormal_ = resolved.supportNormal;
        groundBodyId_ = resolved.supportBodyId;
    }
}

glm::dvec3 CharacterController::eyePosition() const noexcept {
    const double centerToEye = settings_.eyeHeight - (settings_.radius + settings_.halfHeight);
    return position_ + up_ * centerToEye;
}

glm::dvec3 CharacterController::gravityUpAt(const glm::dvec3& position) const noexcept {
    if (world_ == nullptr) return {0.0, 1.0, 0.0};
    const glm::dvec3 gravity = world_->environment().gravityAcceleration(position);
    if (glm::dot(gravity, gravity) > 1.0e-10) return safeNormalize(-gravity);

    const PhysicsEnvironment& environment = world_->environment();
    if (const CelestialBody* body = primaryBody(environment)) {
        return safeNormalize(position - body->position);
    }
    return safeNormalize(position);
}

glm::dquat CharacterController::capsuleOrientation(const glm::dvec3& up) const noexcept {
    return rotateYAxisTo(up);
}

ShapePose CharacterController::capsulePoseAt(const glm::dvec3& position) const noexcept {
    return {position, capsuleOrientation(gravityUpAt(position))};
}

bool CharacterController::walkableNormal(
    const glm::dvec3& normalInput,
    const glm::dvec3& gravityUp) const noexcept {
    const glm::dvec3 normal = safeNormalize(normalInput, gravityUp);
    return glm::dot(normal, gravityUp) >= std::cos(settings_.maxSlopeAngleRadians);
}

CharacterController::ResolveResult CharacterController::resolveTerrain(
    glm::dvec3& position,
    glm::dvec3& velocity) const noexcept {
    ResolveResult result{};
    if (world_ == nullptr) return result;

    const PhysicsEnvironment& environment = world_->environment();
    const CelestialBody* body = primaryBody(environment);
    const glm::dvec3 center = body != nullptr ? body->position : glm::dvec3{};
    const glm::dvec3 offset = position - center;
    const double distance = glm::length(offset);
    if (distance <= kEpsilon) return result;

    const glm::dvec3 radialDirection = offset / distance;
    double surfaceRadius = 0.0;
    glm::dvec3 surfaceNormal = radialDirection;
    if (body != nullptr) {
        const glm::dvec3 localDirection = bodyLocalDirection(*body, radialDirection);
        surfaceRadius = planetSurfaceRadius(environment.planet, localDirection);
        surfaceNormal = bodyWorldNormal(*body, environment.planet, radialDirection);
    } else {
        surfaceRadius = planetSurfaceRadius(environment.planet, radialDirection);
        surfaceNormal = planetSurfaceNormal(environment.planet, radialDirection);
    }

    const glm::dvec3 surfacePoint = center + radialDirection * surfaceRadius;
    const ShapePose pose = capsulePoseAt(position);
    const glm::dvec3 lowestPoint = supportPoint(capsule_, pose, -surfaceNormal);
    const double gap = glm::dot(lowestPoint - surfacePoint, surfaceNormal);
    if (gap >= settings_.contactOffset) return result;

    result.touched = true;
    const glm::dvec3 gravityUp = gravityUpAt(position);
    const bool walkable = walkableNormal(surfaceNormal, gravityUp);
    result.supported = walkable;
    result.supportNormal = surfaceNormal;
    result.supportBodyId = 0U;
    result.blocking = !walkable && std::abs(glm::dot(surfaceNormal, gravityUp)) < 0.98;

    position += surfaceNormal * (settings_.contactOffset - gap);
    const double inwardSpeed = glm::dot(velocity, surfaceNormal);
    if (inwardSpeed < 0.0) velocity -= surfaceNormal * inwardSpeed;
    return result;
}

CharacterController::ResolveResult CharacterController::resolveBodies(
    glm::dvec3& position,
    glm::dvec3& velocity,
    bool applyPushImpulse) {
    ResolveResult accumulated{};
    if (world_ == nullptr) return accumulated;

    for (std::uint32_t iteration = 0; iteration < settings_.maxDepenetrationIterations; ++iteration) {
        bool changed = false;
        const glm::dvec3 gravityUp = gravityUpAt(position);
        const ShapePose characterPose = {position, capsuleOrientation(gravityUp)};
        const Aabb characterAabb = computeWorldAabb(capsule_, characterPose);

        for (RigidBody& body : world_->bodies()) {
            const Aabb bodyAabb = computeWorldAabb(body.collisionShape, body.shapePose());
            Aabb expandedCharacter = characterAabb;
            expandedCharacter.minimum -= glm::dvec3{settings_.contactOffset};
            expandedCharacter.maximum += glm::dvec3{settings_.contactOffset};
            if (!expandedCharacter.overlaps(bodyAabb)) continue;

            ContactManifold manifold{};
            if (!collideShapes(capsule_, characterPose, body.collisionShape, body.shapePose(), manifold) || manifold.empty()) continue;

            double penetration = 0.0;
            for (std::uint8_t pointIndex = 0; pointIndex < manifold.pointCount; ++pointIndex) {
                penetration = std::max(penetration, manifold.points[pointIndex].penetration);
            }
            if (penetration <= 0.0) continue;

            const glm::dvec3 characterToBody = safeNormalize(manifold.normal, safeNormalize(body.position - position));
            const glm::dvec3 awayFromBody = -characterToBody;
            const bool walkable = walkableNormal(awayFromBody, gravityUp);

            accumulated.touched = true;
            accumulated.blocking = accumulated.blocking || !walkable;
            if (walkable) {
                accumulated.supported = true;
                accumulated.supportNormal = awayFromBody;
                accumulated.supportBodyId = body.id;
            }

            const glm::dvec3 relativeVelocity = velocity - body.velocityAtPoint(manifold.points[0].position);
            const double incomingSpeed = glm::dot(relativeVelocity, awayFromBody);
            if (incomingSpeed < 0.0) velocity -= awayFromBody * incomingSpeed;

            if (applyPushImpulse && body.motionType == MotionType::Dynamic && !body.sleeping) {
                const double towardBodySpeed = std::max(0.0, glm::dot(relativeVelocity, characterToBody));
                if (towardBodySpeed > 1.0e-4) {
                    const double impulseMagnitude = std::min(
                        settings_.maxPushImpulseNs,
                        towardBodySpeed * settings_.characterMassKg * 0.45);
                    body.applyImpulseAtPoint(characterToBody * impulseMagnitude, manifold.points[0].position);
                }
            }

            position += awayFromBody * (penetration + settings_.contactOffset);
            changed = true;
            break;
        }
        if (!changed) break;
    }
    return accumulated;
}

CharacterController::ResolveResult CharacterController::resolveAll(
    glm::dvec3& position,
    glm::dvec3& velocity,
    bool applyPushImpulse) {
    ResolveResult result = resolveTerrain(position, velocity);
    const ResolveResult bodies = resolveBodies(position, velocity, applyPushImpulse);
    result.touched = result.touched || bodies.touched;
    result.blocking = result.blocking || bodies.blocking;
    if (bodies.supported) {
        result.supported = true;
        result.supportNormal = bodies.supportNormal;
        result.supportBodyId = bodies.supportBodyId;
    }
    const ResolveResult terrainAgain = resolveTerrain(position, velocity);
    result.touched = result.touched || terrainAgain.touched;
    result.blocking = result.blocking || terrainAgain.blocking;
    if (terrainAgain.supported && !bodies.supported) {
        result.supported = true;
        result.supportNormal = terrainAgain.supportNormal;
        result.supportBodyId = 0U;
    }
    return result;
}

bool CharacterController::stickToGround(
    glm::dvec3& ioPosition,
    glm::dvec3& ioVelocity,
    ResolveResult& ioSupport) {
    const glm::dvec3 gravityUp = gravityUpAt(ioPosition);
    const double maxDrop = settings_.stickToFloorDistance;

    {
        const PhysicsEnvironment& environment = world_->environment();
        const CelestialBody* body = primaryBody(environment);
        const glm::dvec3 center = body != nullptr ? body->position : glm::dvec3{};
        const glm::dvec3 radialDirection = safeNormalize(ioPosition - center, gravityUp);
        const glm::dvec3 localDirection = body != nullptr ? bodyLocalDirection(*body, radialDirection) : radialDirection;
        const double radius = planetSurfaceRadius(environment.planet, localDirection);
        const glm::dvec3 normal = body != nullptr
            ? bodyWorldNormal(*body, environment.planet, radialDirection)
            : planetSurfaceNormal(environment.planet, radialDirection);
        if (walkableNormal(normal, gravityUp)) {
            const glm::dvec3 surfacePoint = center + radialDirection * radius;
            const ShapePose pose = {ioPosition, capsuleOrientation(gravityUp)};
            const glm::dvec3 foot = supportPoint(capsule_, pose, -normal);
            const double gap = glm::dot(foot - surfacePoint, normal) - settings_.contactOffset;
            if (gap >= 0.0 && gap <= maxDrop) {
                const double denominator = std::max(0.25, glm::dot(normal, gravityUp));
                ioPosition -= gravityUp * (gap / denominator);
                ResolveResult resolved = resolveTerrain(ioPosition, ioVelocity);
                if (resolved.supported) {
                    ioSupport = resolved;
                    return true;
                }
            }
        }
    }

    const glm::dvec3 probePosition = ioPosition - gravityUp * maxDrop;
    const ShapePose probePose = {probePosition, capsuleOrientation(gravityUp)};
    for (RigidBody& body : world_->bodies()) {
        ContactManifold manifold{};
        if (!collideShapes(capsule_, probePose, body.collisionShape, body.shapePose(), manifold) || manifold.empty()) continue;
        const glm::dvec3 away = -safeNormalize(manifold.normal, gravityUp);
        if (!walkableNormal(away, gravityUp)) continue;
        double penetration = 0.0;
        for (std::uint8_t pointIndex = 0; pointIndex < manifold.pointCount; ++pointIndex) {
            penetration = std::max(penetration, manifold.points[pointIndex].penetration);
        }
        glm::dvec3 candidate = probePosition + away * (penetration + settings_.contactOffset);
        if (glm::dot(candidate - ioPosition, gravityUp) > settings_.contactOffset) continue;
        ioPosition = candidate;
        const double inward = glm::dot(ioVelocity - body.linearVelocity, away);
        if (inward < 0.0) ioVelocity -= away * inward;
        ioSupport.touched = true;
        ioSupport.supported = true;
        ioSupport.supportNormal = away;
        ioSupport.supportBodyId = body.id;
        return true;
    }
    return false;
}

bool CharacterController::tryStep(
    const glm::dvec3& delta,
    glm::dvec3& outPosition,
    glm::dvec3& ioVelocity) {
    if (!grounded_ || settings_.stepHeight <= 0.0) return false;
    const glm::dvec3 gravityUp = gravityUpAt(position_);
    if (glm::length(delta - gravityUp * glm::dot(delta, gravityUp)) <= 1.0e-6) return false;

    glm::dvec3 raised = position_ + gravityUp * settings_.stepHeight;
    glm::dvec3 raisedVelocity = ioVelocity;
    const ResolveResult riseClearance = resolveAll(raised, raisedVelocity, false);
    if (riseClearance.blocking) return false;

    glm::dvec3 candidate = raised + delta;
    const ResolveResult forwardResolve = resolveAll(candidate, raisedVelocity, false);
    if (forwardResolve.blocking) return false;

    ResolveResult support = forwardResolve;
    if (!support.supported && !stickToGround(candidate, raisedVelocity, support)) return false;
    if (!support.supported) return false;

    outPosition = candidate;
    ioVelocity = raisedVelocity;
    return true;
}

void CharacterController::moveWithCollisions(const glm::dvec3& displacement) {
    const double distance = glm::length(displacement);
    const std::uint32_t substepCount = std::max<std::uint32_t>(
        1U,
        static_cast<std::uint32_t>(std::ceil(distance / settings_.maxMoveSubstep)));
    const glm::dvec3 step = displacement / static_cast<double>(substepCount);

    ResolveResult latestSupport{};
    for (std::uint32_t substep = 0; substep < substepCount; ++substep) {
        glm::dvec3 candidate = position_ + step;
        glm::dvec3 candidateVelocity = velocity_;
        const ResolveResult resolved = resolveAll(candidate, candidateVelocity, true);

        if (resolved.blocking) {
            glm::dvec3 steppedPosition{};
            glm::dvec3 steppedVelocity = velocity_;
            if (tryStep(step, steppedPosition, steppedVelocity)) {
                position_ = steppedPosition;
                velocity_ = steppedVelocity;
                ResolveResult support{};
                if (glm::dot(velocity_, gravityUpAt(position_)) <= 0.05)
                    (void)stickToGround(position_, velocity_, support);
                if (support.supported) latestSupport = support;
                continue;
            }
        }

        position_ = candidate;
        velocity_ = candidateVelocity;
        if (resolved.supported) latestSupport = resolved;
    }

    const double upwardSpeed = glm::dot(velocity_, gravityUpAt(position_));
    if (!latestSupport.supported && upwardSpeed <= 0.05) {
        ResolveResult support{};
        if (stickToGround(position_, velocity_, support)) latestSupport = support;
    }

    grounded_ = latestSupport.supported;
    if (grounded_) {
        groundNormal_ = latestSupport.supportNormal;
        groundBodyId_ = latestSupport.supportBodyId;
    } else {
        groundNormal_ = gravityUpAt(position_);
        groundBodyId_ = 0U;
    }
}

void CharacterController::update(const CharacterControllerInput& input, double dt) {
    if (world_ == nullptr || dt <= 0.0) return;
    dt = std::clamp(dt, 1.0 / 1000.0, 0.05);

    up_ = gravityUpAt(position_);
    glm::dvec3 forward = input.forward - up_ * glm::dot(input.forward, up_);
    forward = safeNormalize(forward, {0.0, 0.0, -1.0});
    glm::dvec3 right = input.right - up_ * glm::dot(input.right, up_);
    right = safeNormalize(right, safeNormalize(glm::cross(forward, up_), {1.0, 0.0, 0.0}));

    glm::dvec3 desiredDirection = forward * input.forwardAxis + right * input.rightAxis;
    const double desiredLength = glm::length(desiredDirection);
    if (desiredLength > 1.0) desiredDirection /= desiredLength;
    const double desiredSpeed = input.sprint ? settings_.sprintSpeed : settings_.walkSpeed;
    const glm::dvec3 desiredHorizontal = desiredLength > 1.0e-8
        ? desiredDirection * desiredSpeed
        : glm::dvec3{};

    const double verticalSpeed = glm::dot(velocity_, up_);
    glm::dvec3 horizontalVelocity = velocity_ - up_ * verticalSpeed;
    const double acceleration = grounded_ ? settings_.groundAcceleration : settings_.airAcceleration;
    const double blend = 1.0 - std::exp(-acceleration * dt);
    horizontalVelocity += (desiredHorizontal - horizontalVelocity) * blend;
    velocity_ = horizontalVelocity + up_ * verticalSpeed;

    if (grounded_ && groundBodyId_ != 0U) {
        if (const RigidBody* groundBody = world_->body(groundBodyId_)) {
            velocity_ += groundBody->linearVelocity * dt * 2.0;
        }
    }

    if (grounded_ && input.jump) {
        velocity_ -= up_ * glm::dot(velocity_, up_);
        velocity_ += up_ * settings_.jumpSpeed;
        grounded_ = false;
        groundBodyId_ = 0U;
    } else if (!grounded_) {
        velocity_ += world_->environment().gravityAcceleration(position_) * dt;
    } else {
        const double intoGround = glm::dot(velocity_, groundNormal_);
        if (intoGround < 0.0) velocity_ -= groundNormal_ * intoGround;
    }

    moveWithCollisions(velocity_ * dt);
    up_ = gravityUpAt(position_);
}

} // namespace vf
