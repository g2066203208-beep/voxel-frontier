#include "vf/world/CelestialPhysicsFrame.hpp"

#include "vf/world/CelestialSystem.hpp"

#include <cmath>

#include <glm/geometric.hpp>

namespace vf {
namespace {

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (!std::isfinite(lengthSquared) || lengthSquared <= 1.0e-12) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] glm::dquat safeRotation(const glm::dquat& value) noexcept {
    const double normSquared = value.w * value.w + value.x * value.x
        + value.y * value.y + value.z * value.z;
    if (!std::isfinite(normSquared) || normSquared <= 1.0e-24)
        return {1.0, 0.0, 0.0, 0.0};
    return value / std::sqrt(normSquared);
}

[[nodiscard]] glm::dvec3 angularVelocityWorld(const CelestialBody& body) noexcept {
    if (!std::isfinite(body.spinRateRadPerSecond)) return {};
    return safeNormalize(body.spinAxis) * body.spinRateRadPerSecond;
}

} // namespace

ReferenceFrameWorldState CelestialPhysicsFrame::worldState(
    const CelestialBody& body) const noexcept {
    ReferenceFrameWorldState state{};
    state.position = body.position;
    state.velocity = body.linearVelocity;
    state.rotation = safeRotation(body.orientation);
    state.angularVelocity = angularVelocityWorld(body);
    state.valid = std::isfinite(state.position.x)
        && std::isfinite(state.position.y)
        && std::isfinite(state.position.z)
        && std::isfinite(state.velocity.x)
        && std::isfinite(state.velocity.y)
        && std::isfinite(state.velocity.z)
        && std::isfinite(state.angularVelocity.x)
        && std::isfinite(state.angularVelocity.y)
        && std::isfinite(state.angularVelocity.z);
    return state;
}

glm::dvec3 CelestialPhysicsFrame::toLocalPosition(
    const CelestialBody& body,
    const glm::dvec3& worldPosition) const noexcept {
    const ReferenceFrameWorldState state = worldState(body);
    return glm::conjugate(state.rotation) * (worldPosition - state.position);
}

glm::dvec3 CelestialPhysicsFrame::toWorldPosition(
    const CelestialBody& body,
    const glm::dvec3& localPosition) const noexcept {
    const ReferenceFrameWorldState state = worldState(body);
    return state.position + state.rotation * localPosition;
}

glm::dvec3 CelestialPhysicsFrame::toLocalDirection(
    const CelestialBody& body,
    const glm::dvec3& worldDirection) const noexcept {
    return glm::conjugate(worldState(body).rotation) * worldDirection;
}

glm::dvec3 CelestialPhysicsFrame::toWorldDirection(
    const CelestialBody& body,
    const glm::dvec3& localDirection) const noexcept {
    return worldState(body).rotation * localDirection;
}

glm::dquat CelestialPhysicsFrame::toLocalOrientation(
    const CelestialBody& body,
    const glm::dquat& worldOrientation) const noexcept {
    const glm::dquat local = glm::conjugate(worldState(body).rotation) * safeRotation(worldOrientation);
    return safeRotation(local);
}

glm::dquat CelestialPhysicsFrame::toWorldOrientation(
    const CelestialBody& body,
    const glm::dquat& localOrientation) const noexcept {
    return safeRotation(worldState(body).rotation * safeRotation(localOrientation));
}

glm::dvec3 CelestialPhysicsFrame::toLocalVelocity(
    const CelestialBody& body,
    const glm::dvec3& worldPosition,
    const glm::dvec3& worldVelocity) const noexcept {
    const ReferenceFrameWorldState state = worldState(body);
    const glm::dvec3 offsetWorld = worldPosition - state.position;
    const glm::dvec3 movingFrameVelocity = state.velocity
        + glm::cross(state.angularVelocity, offsetWorld);
    return glm::conjugate(state.rotation) * (worldVelocity - movingFrameVelocity);
}

glm::dvec3 CelestialPhysicsFrame::toWorldVelocity(
    const CelestialBody& body,
    const glm::dvec3& localPosition,
    const glm::dvec3& localVelocity) const noexcept {
    const ReferenceFrameWorldState state = worldState(body);
    const glm::dvec3 offsetWorld = state.rotation * localPosition;
    return state.velocity
        + glm::cross(state.angularVelocity, offsetWorld)
        + state.rotation * localVelocity;
}

glm::dvec3 CelestialPhysicsFrame::localAngularVelocity(const CelestialBody& body) const noexcept {
    const ReferenceFrameWorldState state = worldState(body);
    return glm::conjugate(state.rotation) * state.angularVelocity;
}

glm::dvec3 CelestialPhysicsFrame::apparentAcceleration(
    const CelestialBody& body,
    const glm::dvec3& localPosition,
    const glm::dvec3& localVelocity,
    const glm::dvec3& relativePhysicalAccelerationWorld) const noexcept {
    const ReferenceFrameWorldState state = worldState(body);
    const glm::dvec3 physicalLocal = glm::conjugate(state.rotation) * relativePhysicalAccelerationWorld;
    const glm::dvec3 omega = glm::conjugate(state.rotation) * state.angularVelocity;
    const glm::dvec3 coriolis = -2.0 * glm::cross(omega, localVelocity);
    const glm::dvec3 centrifugal = -glm::cross(omega, glm::cross(omega, localPosition));
    return physicalLocal + coriolis + centrifugal;
}

glm::dvec3 CelestialPhysicsFrame::gravityAcceleration(
    const CelestialSystem& system,
    const CelestialBody& body,
    const glm::dvec3& localPosition,
    const glm::dvec3& localVelocity) const noexcept {
    const glm::dvec3 worldPosition = toWorldPosition(body, localPosition);
    const glm::dvec3 relativeGravityWorld = system.gravityAccelerationRelativeTo(body.id, worldPosition);
    return apparentAcceleration(body, localPosition, localVelocity, relativeGravityWorld);
}

} // namespace vf
