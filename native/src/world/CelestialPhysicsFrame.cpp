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
    if (lengthSquared <= 1.0e-12) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] glm::dvec3 angularVelocityWorld(const CelestialBody& body) noexcept {
    return safeNormalize(body.spinAxis) * body.spinRateRadPerSecond;
}

} // namespace

glm::dvec3 CelestialPhysicsFrame::toLocalPosition(
    const CelestialBody& body,
    const glm::dvec3& worldPosition) const noexcept {
    const glm::dquat inverse = glm::conjugate(glm::normalize(body.orientation));
    return inverse * (worldPosition - body.position);
}

glm::dvec3 CelestialPhysicsFrame::toWorldPosition(
    const CelestialBody& body,
    const glm::dvec3& localPosition) const noexcept {
    return body.position + glm::normalize(body.orientation) * localPosition;
}

glm::dquat CelestialPhysicsFrame::toLocalOrientation(
    const CelestialBody& body,
    const glm::dquat& worldOrientation) const noexcept {
    return glm::normalize(glm::conjugate(glm::normalize(body.orientation)) * worldOrientation);
}

glm::dquat CelestialPhysicsFrame::toWorldOrientation(
    const CelestialBody& body,
    const glm::dquat& localOrientation) const noexcept {
    return glm::normalize(glm::normalize(body.orientation) * localOrientation);
}

glm::dvec3 CelestialPhysicsFrame::toLocalVelocity(
    const CelestialBody& body,
    const glm::dvec3& worldPosition,
    const glm::dvec3& worldVelocity) const noexcept {
    const glm::dvec3 offsetWorld = worldPosition - body.position;
    const glm::dvec3 movingFrameVelocity = body.linearVelocity
        + glm::cross(angularVelocityWorld(body), offsetWorld);
    return glm::conjugate(glm::normalize(body.orientation)) * (worldVelocity - movingFrameVelocity);
}

glm::dvec3 CelestialPhysicsFrame::toWorldVelocity(
    const CelestialBody& body,
    const glm::dvec3& localPosition,
    const glm::dvec3& localVelocity) const noexcept {
    const glm::dquat orientation = glm::normalize(body.orientation);
    const glm::dvec3 offsetWorld = orientation * localPosition;
    return body.linearVelocity
        + glm::cross(angularVelocityWorld(body), offsetWorld)
        + orientation * localVelocity;
}

glm::dvec3 CelestialPhysicsFrame::localAngularVelocity(const CelestialBody& body) const noexcept {
    return glm::conjugate(glm::normalize(body.orientation)) * angularVelocityWorld(body);
}

glm::dvec3 CelestialPhysicsFrame::apparentAcceleration(
    const CelestialBody& body,
    const glm::dvec3& localPosition,
    const glm::dvec3& localVelocity,
    const glm::dvec3& relativePhysicalAccelerationWorld) const noexcept {
    const glm::dquat inverse = glm::conjugate(glm::normalize(body.orientation));
    const glm::dvec3 physicalLocal = inverse * relativePhysicalAccelerationWorld;
    const glm::dvec3 omega = localAngularVelocity(body);
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
