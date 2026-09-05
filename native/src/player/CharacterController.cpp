#include "vf/player/CharacterController.hpp"

#include <algorithm>
#include <array>
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

[[nodiscard]] glm::dvec3 tangentAxis(const glm::dvec3& upInput) noexcept {
    const glm::dvec3 up = safeNormalize(upInput);
    const glm::dvec3 a = glm::abs(up);
    glm::dvec3 reference{1.0, 0.0, 0.0};
    if (a.y <= a.x && a.y <= a.z) reference = {0.0, 1.0, 0.0};
    else if (a.z <= a.x && a.z <= a.y) reference = {0.0, 0.0, 1.0};
    return safeNormalize(glm::cross(reference, up), {1.0, 0.0, 0.0});
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
    settings_.maxMoveSubstep = std::clamp(settings_.maxMoveSubstep, 0.025, 0.25);
    settings_.maxDepenetrationIterations = std::clamp<std::uint32_t>(settings_.maxDepenetrationIterations, 1U, 24U);
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
    ResolveResult accumulated{};
    if (world_ == nullptr) return accumulated;

    const PhysicsEnvironment& environment = world_->environment();
    const CelestialBody* body = primaryBody(environment);
    const glm::dvec3 center = body != nullptr ? body->position : glm::dvec3{};

    struct TerrainSample {
        bool valid{};
        glm::dvec3 surfacePoint{};
        glm::dvec3 normal{0.0, 1.0, 0.0};
        double gap{std::numeric_limits<double>::infinity()};
    };

    const auto queryTerrain = [&](const glm::dvec3& probePoint) noexcept {
        TerrainSample sample{};
        const glm::dvec3 offset = probePoint - center;
        const double distance = glm::length(offset);
        if (distance <= kEpsilon) return sample;

        const glm::dvec3 radialDirection = offset / distance;
        double surfaceRadius = 0.0;
        if (body != nullptr) {
            const glm::dvec3 localDirection = bodyLocalDirection(*body, radialDirection);
            surfaceRadius = planetSurfaceRadius(environment.planet, localDirection);
            sample.normal = bodyWorldNormal(*body, environment.planet, radialDirection);
        } else {
            surfaceRadius = planetSurfaceRadius(environment.planet, radialDirection);
            sample.normal = planetSurfaceNormal(environment.planet, radialDirection);
        }
        sample.surfacePoint = center + radialDirection * surfaceRadius;
        sample.gap = glm::dot(probePoint - sample.surfacePoint, sample.normal);
        sample.valid = true;
        return sample;
    };

    // CharacterVirtual-style supporting-volume idea adapted to an implicit spherical height field:
    // probe the whole lower capsule footprint rather than intersecting the planet at the capsule
    // center direction only. This closes the old failure mode where a hill entered through the side
    // of the lower hemisphere while the center ray still reported clear space.
    constexpr std::array<glm::dvec2, 9> normalizedFootprint{{
        {0.0, 0.0},
        {1.0, 0.0}, {-1.0, 0.0}, {0.0, 1.0}, {0.0, -1.0},
        {0.7071067811865476, 0.7071067811865476},
        {-0.7071067811865476, 0.7071067811865476},
        {0.7071067811865476, -0.7071067811865476},
        {-0.7071067811865476, -0.7071067811865476},
    }};

    const std::uint32_t iterationCount = std::min<std::uint32_t>(settings_.maxDepenetrationIterations, 6U);
    for (std::uint32_t iteration = 0; iteration < iterationCount; ++iteration) {
        const glm::dvec3 gravityUp = gravityUpAt(position);
        const glm::dvec3 tangentA = tangentAxis(gravityUp);
        const glm::dvec3 tangentB = safeNormalize(glm::cross(gravityUp, tangentA), {0.0, 0.0, 1.0});
        const ShapePose pose = {position, capsuleOrientation(gravityUp)};

        double bestCorrection = 0.0;
        glm::dvec3 bestCorrectionNormal = gravityUp;
        bool sawContact = false;
        bool sawBlocking = false;
        bool sawSupport = false;
        glm::dvec3 bestSupportNormal = gravityUp;
        double bestSupportAlignment = -1.0;

        const auto considerPoint = [&](const glm::dvec3& probePoint) {
            const TerrainSample terrain = queryTerrain(probePoint);
            if (!terrain.valid || terrain.gap > settings_.contactOffset + 1.0e-5) return;

            sawContact = true;
            const double alignment = glm::dot(terrain.normal, gravityUp);
            const bool walkable = walkableNormal(terrain.normal, gravityUp);
            if (walkable) {
                sawSupport = true;
                if (alignment > bestSupportAlignment) {
                    bestSupportAlignment = alignment;
                    bestSupportNormal = terrain.normal;
                }
            } else if (alignment < 0.98) {
                sawBlocking = true;
            }

            const double correction = settings_.contactOffset - terrain.gap;
            if (correction > bestCorrection) {
                bestCorrection = correction;
                bestCorrectionNormal = terrain.normal;
            }
        };

        const glm::dvec3 bottomSphereCenter = position - gravityUp * settings_.halfHeight;
        const double footprintRadius = settings_.radius * 0.74;
        for (const glm::dvec2& uv : normalizedFootprint) {
            const double ox = uv.x * footprintRadius;
            const double oz = uv.y * footprintRadius;
            const double radialSquared = std::min(
                settings_.radius * settings_.radius,
                ox * ox + oz * oz);
            const double downwardSphere = std::sqrt(std::max(
                0.0,
                settings_.radius * settings_.radius - radialSquared));
            const glm::dvec3 probePoint = bottomSphereCenter
                + tangentA * ox
                + tangentB * oz
                - gravityUp * downwardSphere;
            considerPoint(probePoint);
        }

        // Refine one true convex support point against the local procedural normal. Two passes are
        // enough for the normal/support direction pair to converge on terrain at human scale.
        glm::dvec3 normalGuess = gravityUp;
        TerrainSample centerTerrain = queryTerrain(position - gravityUp * (settings_.halfHeight + settings_.radius));
        if (centerTerrain.valid) normalGuess = centerTerrain.normal;
        for (int refine = 0; refine < 2; ++refine) {
            const glm::dvec3 support = supportPoint(capsule_, pose, -normalGuess);
            const TerrainSample terrain = queryTerrain(support);
            if (!terrain.valid) break;
            considerPoint(support);
            normalGuess = terrain.normal;
        }

        accumulated.touched = accumulated.touched || sawContact;
        accumulated.blocking = accumulated.blocking || sawBlocking;
        if (sawSupport) {
            accumulated.supported = true;
            accumulated.supportNormal = bestSupportNormal;
            accumulated.supportBodyId = 0U;
        }

        if (bestCorrection <= 1.0e-7) break;
        position += bestCorrectionNormal * bestCorrection;
        const double inwardSpeed = glm::dot(velocity, bestCorrectionNormal);
        if (inwardSpeed < 0.0) velocity -= bestCorrectionNormal * inwardSpeed;
    }

    return accumulated;
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

    // Equivalent of Jolt's StickToFloor shape cast for our analytical terrain: move a candidate
    // down by the configured distance, resolve the full lower-capsule footprint, then accept only a
    // support that stayed within the requested downward interval.
    glm::dvec3 terrainCandidate = ioPosition - gravityUp * maxDrop;
    glm::dvec3 terrainVelocity = ioVelocity;
    const ResolveResult terrainSupport = resolveTerrain(terrainCandidate, terrainVelocity);
    if (terrainSupport.supported) {
        const double verticalDelta = glm::dot(terrainCandidate - ioPosition, gravityUp);
        if (verticalDelta <= settings_.contactOffset
            && verticalDelta >= -(maxDrop + settings_.contactOffset * 2.0)) {
            ioPosition = terrainCandidate;
            ioVelocity = terrainVelocity;
            ioSupport = terrainSupport;
            return true;
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
    // Predictive-contact analogue: never advance farther than both the configured motion step and
    // roughly two contact shells. This is intentionally much smaller than the capsule diameter, so
    // thin floors cannot disappear between two discrete overlap tests during a sprint or fall.
    const double predictiveStep = std::clamp(settings_.contactOffset * 1.75, 0.025, 0.10);
    const double maxStep = std::min(settings_.maxMoveSubstep, predictiveStep);
    const std::uint32_t substepCount = std::max<std::uint32_t>(
        1U,
        static_cast<std::uint32_t>(std::ceil(distance / maxStep)));
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
