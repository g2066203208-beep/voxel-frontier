#include "vf/physics/CelestialSurfaceFrames.hpp"

#include "vf/physics/CollisionGeometry.hpp"
#include "vf/physics/PhysicsWorld.hpp"
#include "vf/world/CelestialSystem.hpp"
#include "vf/world/PlanetSurface.hpp"

#include <algorithm>
#include <cmath>
#include <vector>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kEpsilon = 1.0e-9;
constexpr double kSpawnFrameCaptureGapMeters = 64.0;

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

[[nodiscard]] glm::dvec3 surfaceVelocityAt(
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
    attachment.dynamicBody = rigidBody.motionType == MotionType::Dynamic;
    attachment.restTimer = 0.0;

    if (attachment.dynamicBody) {
        rigidBody.sleeping = true;
        rigidBody.sleepTimer = 1.0;
        // A locked sleeper is stored in planet-local coordinates. World velocity is reconstructed
        // when it is released; keeping zero here prevents the generic world-space sleep detector
        // from immediately waking a perfectly still local object just because the planet orbits.
        rigidBody.linearVelocity = {};
        rigidBody.angularVelocity = {};
    }
}

void CelestialSurfaceFrames::updateLockedTransform(
    RigidBody& rigidBody,
    const CelestialBody& celestialBody,
    const Attachment& attachment) noexcept {
    rigidBody.position = celestialBody.position + celestialBody.orientation * attachment.localPosition;
    rigidBody.orientation = glm::normalize(celestialBody.orientation * attachment.localOrientation);

    if (rigidBody.motionType == MotionType::Dynamic) {
        rigidBody.linearVelocity = {};
        rigidBody.angularVelocity = {};
    } else {
        // Static fixtures are moved with a valid point velocity so dynamic contacts see a moving
        // platform rather than a teleporting wall/floor.
        rigidBody.linearVelocity = surfaceVelocityAt(celestialBody, rigidBody.position);
        rigidBody.angularVelocity = angularVelocityOf(celestialBody);
    }
}

void CelestialSurfaceFrames::beforePhysics(
    PhysicsWorld& world,
    const CelestialSystem& celestial) {
    std::vector<std::uint32_t> eraseIds;

    for (auto& rigidBody : world.bodies()) {
        auto found = attachments_.find(rigidBody.id);

        if (found == attachments_.end()) {
            double gap = 0.0;
            const CelestialBody* surface = nearestSurfaceBody(rigidBody, world, celestial, &gap);
            if (surface != nullptr) {
                if (rigidBody.motionType != MotionType::Dynamic && std::abs(gap) <= 24.0) {
                    // Static fixtures authored on a planet are permanently planet-local.
                    Attachment attachment{};
                    lockToBody(rigidBody, *surface, attachment);
                    attachments_.emplace(rigidBody.id, attachment);
                    found = attachments_.find(rigidBody.id);
                } else if (rigidBody.motionType == MotionType::Dynamic
                    && std::abs(gap) <= kSpawnFrameCaptureGapMeters) {
                    // Most gameplay props are spawned "at rest on/near the ground". In an
                    // inertial solar-system frame, zero world velocity is *not* at rest: Aster is
                    // already orbiting Helion and spinning. Bootstrap zero-velocity props with the
                    // local surface inertial velocity once so the contact solver only handles their
                    // small relative motion instead of a 50-100 m/s frame mismatch.
                    Attachment attachment{};
                    attachment.celestialBodyId = surface->id;
                    attachment.dynamicBody = true;
                    attachment.locked = false;
                    attachments_.emplace(rigidBody.id, attachment);
                    found = attachments_.find(rigidBody.id);

                    if (glm::length(rigidBody.linearVelocity) < 0.25) {
                        rigidBody.linearVelocity = surfaceVelocityAt(*surface, rigidBody.position);
                    }
                    if (glm::length(rigidBody.angularVelocity) < 0.05) {
                        rigidBody.angularVelocity = angularVelocityOf(*surface);
                    }
                }
            }
        }

        if (found == attachments_.end() || !found->second.locked) continue;
        Attachment& attachment = found->second;
        const CelestialBody* frame = celestial.body(attachment.celestialBodyId);
        if (frame == nullptr) {
            eraseIds.push_back(rigidBody.id);
            continue;
        }

        // A real force/impact wakes a dynamic local sleeper. Restore the inertial motion of the
        // moving surface exactly once and then let normal rigid-body physics take over.
        if (attachment.dynamicBody && !rigidBody.sleeping) {
            rigidBody.linearVelocity += surfaceVelocityAt(*frame, rigidBody.position);
            rigidBody.angularVelocity += angularVelocityOf(*frame);
            attachment.locked = false;
            attachment.restTimer = 0.0;
            continue;
        }

        updateLockedTransform(rigidBody, *frame, attachment);
    }

    for (const std::uint32_t id : eraseIds) attachments_.erase(id);
}

void CelestialSurfaceFrames::afterPhysics(
    PhysicsWorld& world,
    const CelestialSystem& celestial,
    double frameDeltaSeconds) {
    const double dt = std::clamp(frameDeltaSeconds, 0.0, 0.10);

    for (auto& rigidBody : world.bodies()) {
        if (rigidBody.motionType != MotionType::Dynamic) continue;

        Attachment& attachment = attachments_[rigidBody.id];
        if (attachment.locked) {
            const CelestialBody* frame = celestial.body(attachment.celestialBodyId);
            if (frame == nullptr) {
                attachments_.erase(rigidBody.id);
                continue;
            }
            if (!rigidBody.sleeping) {
                rigidBody.linearVelocity += surfaceVelocityAt(*frame, rigidBody.position);
                rigidBody.angularVelocity += angularVelocityOf(*frame);
                attachment.locked = false;
                attachment.restTimer = 0.0;
            }
            continue;
        }

        double gap = 0.0;
        const CelestialBody* frame = nearestSurfaceBody(rigidBody, world, celestial, &gap);
        if (frame == nullptr || std::abs(gap) > 0.16) {
            attachment.restTimer = 0.0;
            continue;
        }

        attachment.celestialBodyId = frame->id;
        attachment.dynamicBody = true;

        const glm::dvec3 expectedLinear = surfaceVelocityAt(*frame, rigidBody.position);
        const glm::dvec3 expectedAngular = angularVelocityOf(*frame);
        const double relativeLinearSpeed = glm::length(rigidBody.linearVelocity - expectedLinear);
        const double relativeAngularSpeed = glm::length(rigidBody.angularVelocity - expectedAngular);

        // Sleeping is judged in the local rotating frame. Once genuinely at rest, store an exact
        // local transform so there is no residual solver chatter at all.
        if (relativeLinearSpeed < 0.12 && relativeAngularSpeed < 0.20) {
            attachment.restTimer += dt;
            if (attachment.restTimer >= 0.45) lockToBody(rigidBody, *frame, attachment);
        } else {
            attachment.restTimer = 0.0;
        }
    }
}

} // namespace vf
