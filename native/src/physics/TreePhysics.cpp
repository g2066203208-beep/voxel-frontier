#include "vf/physics/TreePhysics.hpp"

#include <algorithm>
#include <cmath>

namespace vf {
namespace {

[[nodiscard]] glm::dvec3 safeNormalize(const glm::dvec3& value, const glm::dvec3& fallback) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared < 1.0e-12) return fallback;
    return value / std::sqrt(lengthSquared);
}

} // namespace

void TreePhysics::applyCut(double normalizedAmount, const glm::dvec3& preferredFallDirection) noexcept {
    cutFraction = std::clamp(cutFraction + std::max(0.0, normalizedAmount), 0.0, 1.0);
    const glm::dvec3 up = safeNormalize(localUp, {0.0, 1.0, 0.0});
    glm::dvec3 projected = preferredFallDirection - up * glm::dot(preferredFallDirection, up);
    if (glm::dot(projected, projected) > 1.0e-8) fallDirection = safeNormalize(projected, fallDirection);

    if (state == TreeState::Standing && cutFraction >= 0.55) {
        state = TreeState::Hinging;
        hingeAngleRadians = std::max(hingeAngleRadians, 0.025);
    }
    if (cutFraction >= 0.96) state = TreeState::Fallen;
}

void TreePhysics::step(double deltaSeconds, double gravityMagnitude, const glm::dvec3& windVelocity, double airDensityKgPerM3) noexcept {
    if (state == TreeState::Standing) return;
    const double dt = std::clamp(deltaSeconds, 0.0, 0.05);
    if (dt <= 0.0) return;

    const double length = std::max(0.1, trunkLength);
    const double mass = std::max(0.01, trunkMass);
    const double inertiaAboutStump = (1.0 / 3.0) * mass * length * length;
    const double gravityTorque = mass * std::max(0.0, gravityMagnitude) * (length * 0.5) * std::sin(std::max(0.0, hingeAngleRadians));

    const glm::dvec3 up = safeNormalize(localUp, {0.0, 1.0, 0.0});
    const glm::dvec3 horizontalWind = windVelocity - up * glm::dot(windVelocity, up);
    const double windSpeed = glm::length(horizontalWind);
    const double projectedArea = std::max(0.01, 2.0 * trunkRadius * length);
    const double windForce = 0.5 * std::max(0.0, airDensityKgPerM3) * windSpeed * windSpeed * std::max(0.0, dragCoefficient) * projectedArea;
    const double windAlignment = windSpeed > 1.0e-6
        ? std::clamp(glm::dot(horizontalWind / windSpeed, safeNormalize(fallDirection, {1.0, 0.0, 0.0})), -1.0, 1.0)
        : 0.0;
    const double windTorque = windForce * (length * 0.55) * windAlignment;

    const double remainingWood = std::max(0.0, 1.0 - cutFraction);
    const double hingeResistance = state == TreeState::Hinging ? 420.0 * remainingWood * remainingWood : 0.0;
    const double dampingTorque = angularVelocity * (55.0 + 160.0 * remainingWood);
    double netTorque = gravityTorque + windTorque - dampingTorque;
    if (state == TreeState::Hinging) netTorque -= std::copysign(std::min(std::abs(netTorque), hingeResistance), netTorque);

    angularVelocity += (netTorque / inertiaAboutStump) * dt;
    angularVelocity = std::clamp(angularVelocity, -4.0, 4.0);
    hingeAngleRadians = std::clamp(hingeAngleRadians + angularVelocity * dt, 0.0, 1.5707963267948966);

    if (hingeAngleRadians >= 1.20 || cutFraction >= 0.96) state = TreeState::Fallen;
}

glm::dvec3 TreePhysics::trunkDirection() const noexcept {
    const glm::dvec3 up = safeNormalize(localUp, {0.0, 1.0, 0.0});
    const glm::dvec3 fall = safeNormalize(fallDirection - up * glm::dot(fallDirection, up), {1.0, 0.0, 0.0});
    return safeNormalize(up * std::cos(hingeAngleRadians) + fall * std::sin(hingeAngleRadians), up);
}

glm::dvec3 TreePhysics::tipPosition() const noexcept {
    return rootPosition + trunkDirection() * std::max(0.0, trunkLength);
}

} // namespace vf
