#include "vf/physics/CelestialSurfaceFrames.hpp"

#include "vf/physics/CollisionGeometry.hpp"
#include "vf/physics/PhysicsWorld.hpp"
#include "vf/world/PlanetSurface.hpp"

#include <algorithm>
#include <cmath>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kEpsilon = 1.0e-9;
constexpr double kSpawnFrameCaptureGapMeters = 64.0;
constexpr double kSurfaceBoundGapMeters = 0.24;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= kEpsilon) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] glm::dvec3 bodyLocalDirection(
    const CelestialBody& body,
    const glm::dvec3& worldDirection) noexcept {
    return safeNormalize(glm::conjugate(glm::normalize(body.orientation)) * safeNormalize(worldDirection));
}

[[nodiscard]] glm::dvec3 angularVelocityOf(const CelestialBody& body) noexcept {
    return safeNormalize(body.spinAxis) * body.spinRateRadPerSecond;
}

[[nodiscard]] glm::dvec3 inertialFrameVelocityAt(
    const CelestialBody& body,
    const glm::dvec3& worldPoint) noexcept {
    return body.linearVelocity + glm::cross(angularVelocityOf(body), worldPoint - body.position);
}

[[nodiscard]] double surfaceRadiusAt(
    const CelestialBody& body,
    const PhysicsWorld& world,
    const glm::dvec3& worldDirection) noexcept {
    if (body.id == world.environment().primaryCelestialBodyId) {
        return planetSurfaceRadius(
            world.environment().planet,
            bodyLocalDirection(body, worldDirection));
    }
    return body.radiusMeters;
}

} // namespace

bool CelestialSurfaceFrames::isAttached(std::uint32_t bodyId) const noexcept {
    const auto it = attachments_.find(bodyId);
    return it != attachments_.end() && it->second.locked;
}

const CelestialBody* CelestialSurfaceFrames::nearestSurfaceBody(
    const RigidBody& rigidBody,
    const PhysicsWorld& world,
    const CelestialSystem& celestial,
    double* signedGap) const noexcept {
    const CelestialBody* best = nullptr;
    double bestAbsGap = 1.0e30;
    double bestGap = 1.0e30;
    const double supportRadius = collisionBoundingRadius(rigidBody.collisionShape);

    for (const auto& body : celestial.bodies()) {
        if (body.type == CelestialBodyType::Star) continue;
        const glm::dvec3 offset = rigidBody.position - body.position;
        const double distance = glm::length(offset);
        if (distance <= kEpsilon) continue;
        const glm::dvec3 direction = offset / distance;
        const double radius = surfaceRadiusAt(body, world, direction);
        const double gap = distance - radius - supportRadius;
        const double absGap = std::abs(gap);
        if (absGap < bestAbsGap) {
            bestAbsGap = absGap;
            bestGap = gap;
            best = &body;
        }
    }

    if (signedGap != nullptr) *signedGap = bestGap;
    return best;
}

void CelestialSurfaceFrames::lockToBody(
    RigidBody& rigidBody,
    const CelestialBody& celestialBody,
    Attachment& attachment) noexcept {
    const glm::dquat inverseFrame = glm::conjugate(glm::normalize(celestialBody.orientation));
    attachment.celestialBodyId = celestialBody.id;
    attachment.localPosition = inverseFrame * (rigidBody.position - celestialBody.position);
    attachment.localOrientation = glm::normalize(inverseFrame * rigidBody.orientation);
    attachment.locked = true;
    attachment.surfaceBound = true;
    attachment.dynamicBody = rigidBody.motionType == MotionType::Dynamic;
    attachment.restTimer = 0.0;

    if (attachment.dynamicBody) {
        rigidBody.sleeping = true;
        rigidBody.sleepTimer = 1.0;
    }
    rigidBody.linearVelocity = {};
    rigidBody.angularVelocity = {};
}

void CelestialSurfaceFrames::updateLockedTransform(
    RigidBody& rigidBody,
    const CelestialBody& celestialBody,
    const Attachment& attachment) noexcept {
    rigidBody.position = celestialBody.position + celestialBody.orientation * attachment.localPosition;
    rigidBody.orientation = glm::normalize(celestialBody.orientation * attachment.localOrientation);
    rigidBody.linearVelocity = {};
    rigidBody.angularVelocity = {};
}

void CelestialSurfaceFrames::configureLocalProxy(
    PhysicsWorld& world,
    const CelestialBody& frameBody) {
    CelestialBody proxy = frameBody;
    proxy.orbitParentId = 0U;
    proxy.linearVelocity = {};
    proxy.spinRateRadPerSecond = 0.0;

    if (CelestialBody* existing = localPhysicsCelestial_.body(frameBody.id)) {
        *existing = proxy;
    } else {
        (void)localPhysicsCelestial_.addBody(proxy);
    }

    world.environment().celestialSystem = &localPhysicsCelestial_;
    world.environment().rotatingFrameAngularVelocity = angularVelocityOf(frameBody);
}

void CelestialSurfaceFrames::beforePhysics(
    PhysicsWorld& world,
    const CelestialSystem& celestial) {
    // Defensive recovery for tests/tools that call beforePhysics twice without an intervening
    // solve. Normal runtime always pairs before/after.
    if (localSolveActive_) {
        world.environment().celestialSystem = previousEnvironmentCelestial_;
        world.environment().rotatingFrameAngularVelocity = {};
        localSolveActive_ = false;
    }

    const std::uint32_t primaryId = world.environment().primaryCelestialBodyId;
    const CelestialBody* frameBody = celestial.body(primaryId);
    if (frameBody == nullptr) return;

    frameBodyId_ = frameBody->id;
    previousEnvironmentCelestial_ = world.environment().celestialSystem;
    const glm::dvec3 currentOmega = angularVelocityOf(*frameBody);
    const glm::dquat currentOrientation = glm::normalize(frameBody->orientation);
    const glm::dquat deltaRotation = previousFrameValid_
        ? glm::normalize(currentOrientation * glm::conjugate(previousFrameOrientation_))
        : glm::dquat{1.0, 0.0, 0.0, 0.0};

    for (auto& rigidBody : world.bodies()) {
        Attachment& attachment = attachments_[rigidBody.id];
        if (attachment.celestialBodyId == 0U) attachment.celestialBodyId = frameBody->id;
        attachment.dynamicBody = rigidBody.motionType == MotionType::Dynamic;

        double gap = 1.0e30;
        const CelestialBody* nearest = nearestSurfaceBody(rigidBody, world, celestial, &gap);
        const bool nearFrameSurface = nearest != nullptr && nearest->id == frameBody->id
            && std::abs(gap) <= kSpawnFrameCaptureGapMeters;

        if (rigidBody.motionType != MotionType::Dynamic && nearFrameSurface && !attachment.locked) {
            lockToBody(rigidBody, *frameBody, attachment);
        }

        if (attachment.locked) {
            if (attachment.dynamicBody && !rigidBody.sleeping) {
                // A real force/impulse woke a local sleeper between frames. The body currently has
                // inertial world velocity; release it and convert that state below.
                attachment.locked = false;
                attachment.surfaceBound = true;
            } else {
                updateLockedTransform(rigidBody, *frameBody, attachment);
                continue;
            }
        }

        if (rigidBody.motionType != MotionType::Dynamic) {
            rigidBody.linearVelocity = {};
            rigidBody.angularVelocity = {};
            continue;
        }

        const glm::dvec3 oldPosition = rigidBody.position;
        glm::dvec3 relativeLinear{};
        glm::dvec3 relativeAngular{};

        if (previousFrameValid_ && attachment.surfaceBound && attachment.celestialBodyId == frameBody->id) {
            const glm::dvec3 previousPointVelocity = previousFrameLinearVelocity_
                + glm::cross(previousFrameAngularVelocity_, oldPosition - previousFramePosition_);
            relativeLinear = deltaRotation * (rigidBody.linearVelocity - previousPointVelocity);
            relativeAngular = deltaRotation * (rigidBody.angularVelocity - previousFrameAngularVelocity_);

            // Contact-bound bodies share the surface pose change between render frames. Their own
            // solved local velocity remains independent, so a rover can drive while the planet
            // orbits/spins without being numerically launched by the moving floor.
            rigidBody.position = frameBody->position + deltaRotation * (oldPosition - previousFramePosition_);
            rigidBody.orientation = glm::normalize(deltaRotation * rigidBody.orientation);
        } else {
            relativeLinear = rigidBody.linearVelocity - inertialFrameVelocityAt(*frameBody, rigidBody.position);
            relativeAngular = rigidBody.angularVelocity - currentOmega;

            // Authored gameplay props commonly spawn with world velocity zero even though the
            // surface has a large inertial velocity. Interpret a near-ground zero-speed spawn as
            // "at rest relative to where it was placed", not as a 250 m/s collision with the floor.
            if (!previousFrameValid_ && nearFrameSurface && glm::length(rigidBody.linearVelocity) < 0.25) {
                relativeLinear = {};
            }
            if (!previousFrameValid_ && nearFrameSurface && glm::length(rigidBody.angularVelocity) < 0.05) {
                relativeAngular = {};
            }
        }

        rigidBody.linearVelocity = relativeLinear;
        rigidBody.angularVelocity = relativeAngular;
        attachment.surfaceBound = nearFrameSurface || attachment.surfaceBound;
        attachment.celestialBodyId = frameBody->id;
    }

    configureLocalProxy(world, *frameBody);
    localSolveActive_ = true;
}

void CelestialSurfaceFrames::afterPhysics(
    PhysicsWorld& world,
    const CelestialSystem& celestial,
    double frameDeltaSeconds) {
    const double dt = std::clamp(frameDeltaSeconds, 0.0, 0.10);
    const CelestialBody* frameBody = celestial.body(frameBodyId_);
    if (frameBody == nullptr) {
        if (localSolveActive_) {
            world.environment().celestialSystem = previousEnvironmentCelestial_;
            world.environment().rotatingFrameAngularVelocity = {};
            localSolveActive_ = false;
        }
        return;
    }

    const glm::dvec3 omega = angularVelocityOf(*frameBody);

    for (auto& rigidBody : world.bodies()) {
        Attachment& attachment = attachments_[rigidBody.id];

        if (attachment.locked) {
            updateLockedTransform(rigidBody, *frameBody, attachment);
            if (attachment.dynamicBody) {
                rigidBody.linearVelocity = inertialFrameVelocityAt(*frameBody, rigidBody.position);
                rigidBody.angularVelocity = omega;
            }
            continue;
        }

        if (rigidBody.motionType != MotionType::Dynamic) {
            rigidBody.linearVelocity = inertialFrameVelocityAt(*frameBody, rigidBody.position);
            rigidBody.angularVelocity = omega;
            continue;
        }

        // PhysicsWorld has just solved this body in low-speed frame-relative velocities.
        const double relativeLinearSpeed = glm::length(rigidBody.linearVelocity);
        const double relativeAngularSpeed = glm::length(rigidBody.angularVelocity);

        double gap = 1.0e30;
        const CelestialBody* nearest = nearestSurfaceBody(rigidBody, world, celestial, &gap);
        const bool touchingSurface = nearest != nullptr && nearest->id == frameBody->id
            && std::abs(gap) <= kSurfaceBoundGapMeters;
        const glm::dvec3 outward = safeNormalize(rigidBody.position - frameBody->position);
        const double outwardRelativeSpeed = glm::dot(rigidBody.linearVelocity, outward);
        attachment.surfaceBound = touchingSurface && outwardRelativeSpeed < 0.50;
        attachment.celestialBodyId = frameBody->id;
        attachment.dynamicBody = true;

        if (attachment.surfaceBound && relativeLinearSpeed < 0.12 && relativeAngularSpeed < 0.20) {
            attachment.restTimer += dt;
            if (attachment.restTimer >= 0.45) {
                lockToBody(rigidBody, *frameBody, attachment);
                rigidBody.linearVelocity = inertialFrameVelocityAt(*frameBody, rigidBody.position);
                rigidBody.angularVelocity = omega;
                continue;
            }
        } else {
            attachment.restTimer = 0.0;
        }

        // Return an exact inertial velocity for world-level systems between physics solves.
        rigidBody.linearVelocity += inertialFrameVelocityAt(*frameBody, rigidBody.position);
        rigidBody.angularVelocity += omega;
    }

    if (localSolveActive_) {
        world.environment().celestialSystem = previousEnvironmentCelestial_;
        world.environment().rotatingFrameAngularVelocity = {};
        localSolveActive_ = false;
    }

    previousFramePosition_ = frameBody->position;
    previousFrameLinearVelocity_ = frameBody->linearVelocity;
    previousFrameAngularVelocity_ = omega;
    previousFrameOrientation_ = glm::normalize(frameBody->orientation);
    previousFrameValid_ = true;
}

} // namespace vf
