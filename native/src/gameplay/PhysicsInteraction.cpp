#include "vf/gameplay/PhysicsInteraction.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

#include "vf/physics/CollisionGeometry.hpp"

namespace vf {
namespace {

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 0.0, -1.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-12) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] glm::dvec3 inverseDiagonal(const glm::dvec3& diagonal) noexcept {
    glm::dvec3 inverse{};
    inverse.x = diagonal.x > 1.0e-12 ? 1.0 / diagonal.x : 0.0;
    inverse.y = diagonal.y > 1.0e-12 ? 1.0 / diagonal.y : 0.0;
    inverse.z = diagonal.z > 1.0e-12 ? 1.0 / diagonal.z : 0.0;
    return inverse;
}

} // namespace

bool PhysicsInteraction::isConstrained(std::uint32_t bodyId) const noexcept {
    if (world_ == nullptr || bodyId == 0U) return true;

    for (const auto& c : world_->distanceConstraints()) {
        if (!c.broken && (c.bodyA == bodyId || c.bodyB == bodyId)) return true;
    }
    for (const auto& c : world_->springDamperConstraints()) {
        if (!c.broken && (c.bodyA == bodyId || c.bodyB == bodyId)) return true;
    }
    for (const auto& c : world_->hingeConstraints()) {
        if (!c.broken && (c.bodyA == bodyId || c.bodyB == bodyId)) return true;
    }
    for (const auto& c : world_->gearConstraints()) {
        if (!c.broken && (c.bodyA == bodyId || c.bodyB == bodyId)) return true;
    }
    return false;
}

std::uint32_t PhysicsInteraction::raycastClosestLooseDynamic(
    const glm::dvec3& rayOrigin,
    const glm::dvec3& rayDirection,
    double maxDistanceMeters,
    double& hitDistanceMeters) const noexcept {
    hitDistanceMeters = std::numeric_limits<double>::infinity();
    if (world_ == nullptr) return 0U;

    const glm::dvec3 direction = safeNormalize(rayDirection);
    std::uint32_t bestId = 0U;

    for (const auto& body : world_->bodies()) {
        if (body.motionType != MotionType::Dynamic || isConstrained(body.id)) continue;

        // Selection uses the conservative shape bounding sphere. Narrow-phase collision remains
        // exact; this query is deliberately cheap and forgiving for a first-person grab action.
        const double radius = std::max(0.05, collisionBoundingRadius(body.collisionShape));
        const glm::dvec3 toCenter = body.position - rayOrigin;
        const double along = glm::dot(toCenter, direction);
        if (along < -radius || along > maxDistanceMeters + radius) continue;

        const double centerDistanceSquared = glm::dot(toCenter, toCenter);
        const double perpendicularSquared = std::max(0.0, centerDistanceSquared - along * along);
        const double radiusSquared = radius * radius;
        if (perpendicularSquared > radiusSquared) continue;

        const double halfChord = std::sqrt(std::max(0.0, radiusSquared - perpendicularSquared));
        double hit = along - halfChord;
        if (hit < 0.0) hit = along + halfChord;
        if (hit < 0.0 || hit > maxDistanceMeters) continue;

        if (hit < hitDistanceMeters) {
            hitDistanceMeters = hit;
            bestId = body.id;
        }
    }

    return bestId;
}

void PhysicsInteraction::beginHold(std::uint32_t bodyId, double hitDistanceMeters) noexcept {
    if (world_ == nullptr) return;
    RigidBody* body = world_->body(bodyId);
    if (body == nullptr || body->motionType != MotionType::Dynamic || isConstrained(bodyId)) return;

    heldBodyId_ = bodyId;
    holdDistanceMeters_ = std::clamp(hitDistanceMeters + collisionBoundingRadius(body->collisionShape) * 0.6, 1.4, 4.5);
    heldVelocity_ = {};

    body->motionType = MotionType::Kinematic;
    body->inverseMass = 0.0;
    body->inverseInertiaDiagonal = {};
    body->linearVelocity = {};
    body->angularVelocity = {};
    body->accumulatedForce = {};
    body->accumulatedTorque = {};
    body->sleeping = false;
    body->sleepTimer = 0.0;
}

void PhysicsInteraction::restoreDynamic(RigidBody& body) noexcept {
    body.motionType = MotionType::Dynamic;
    body.inverseMass = body.mass > 1.0e-12 ? 1.0 / body.mass : 0.0;
    body.inverseInertiaDiagonal = inverseDiagonal(body.inertiaDiagonal);
    body.accumulatedForce = {};
    body.accumulatedTorque = {};
    body.sleeping = false;
    body.sleepTimer = 0.0;
}

void PhysicsInteraction::moveHeldBody(
    const glm::dvec3& rayOrigin,
    const glm::dvec3& rayDirection,
    double deltaSeconds) noexcept {
    if (world_ == nullptr || heldBodyId_ == 0U) return;
    RigidBody* body = world_->body(heldBodyId_);
    if (body == nullptr) {
        heldBodyId_ = 0U;
        heldVelocity_ = {};
        return;
    }

    const glm::dvec3 direction = safeNormalize(rayDirection);
    const glm::dvec3 target = rayOrigin + direction * holdDistanceMeters_;
    const double dt = std::clamp(deltaSeconds, 1.0 / 1000.0, 0.05);
    glm::dvec3 followVelocity = (target - body->position) / dt;
    const double speed = glm::length(followVelocity);
    constexpr double kMaxFollowSpeed = 40.0;
    if (speed > kMaxFollowSpeed && speed > 1.0e-9) followVelocity *= kMaxFollowSpeed / speed;

    body->position = target;
    body->linearVelocity = followVelocity;
    body->angularVelocity = {};
    heldVelocity_ = followVelocity;
}

void PhysicsInteraction::drop() noexcept {
    if (world_ == nullptr || heldBodyId_ == 0U) return;
    if (RigidBody* body = world_->body(heldBodyId_)) {
        restoreDynamic(*body);
        // A normal right-click drop should not inherit the artificial hand-follow velocity.
        body->linearVelocity = {};
        body->angularVelocity = {};
    }
    heldBodyId_ = 0U;
    heldVelocity_ = {};
}

void PhysicsInteraction::throwHeld(const glm::dvec3& direction, double speedMetersPerSecond) noexcept {
    if (world_ == nullptr || heldBodyId_ == 0U) return;
    if (RigidBody* body = world_->body(heldBodyId_)) {
        restoreDynamic(*body);
        body->linearVelocity = safeNormalize(direction) * std::max(0.0, speedMetersPerSecond);
        body->angularVelocity = {};
    }
    heldBodyId_ = 0U;
    heldVelocity_ = {};
}

void PhysicsInteraction::update(
    const glm::dvec3& rayOrigin,
    const glm::dvec3& rayDirection,
    const PhysicsInteractionInput& input,
    double deltaSeconds) {
    if (world_ == nullptr) return;

    if (heldBodyId_ != 0U) {
        if (input.leftPressed) {
            throwHeld(rayDirection);
            return;
        }
        if (input.rightPressed) {
            drop();
            return;
        }
        moveHeldBody(rayOrigin, rayDirection, deltaSeconds);
        return;
    }

    if (!input.rightPressed) return;
    double hitDistance = 0.0;
    const std::uint32_t bodyId = raycastClosestLooseDynamic(
        rayOrigin,
        rayDirection,
        7.0,
        hitDistance);
    if (bodyId == 0U) return;

    beginHold(bodyId, hitDistance);
    moveHeldBody(rayOrigin, rayDirection, deltaSeconds);
}

} // namespace vf
