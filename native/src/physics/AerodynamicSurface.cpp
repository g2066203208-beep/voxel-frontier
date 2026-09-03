#include "vf/physics/AerodynamicSurface.hpp"

#include <algorithm>
#include <cmath>

namespace vf {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;
constexpr double kEpsilon = 1.0e-9;

[[nodiscard]] glm::dvec3 safeNormalize(const glm::dvec3& value, const glm::dvec3& fallback) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= kEpsilon) return fallback;
    return value / std::sqrt(lengthSquared);
}

} // namespace

AerodynamicSurfaceSample sampleAerodynamicSurface(
    const AerodynamicSurface& surface,
    const RigidBody& body,
    const AtmosphereSample& atmosphere) noexcept {
    AerodynamicSurfaceSample sample{};

    const glm::dvec3 chord = safeNormalize(body.orientation * surface.localChordAxis, {1.0, 0.0, 0.0});
    const glm::dvec3 normal = safeNormalize(body.orientation * surface.localNormalAxis, {0.0, 1.0, 0.0});
    sample.applicationPoint = body.position + body.orientation * surface.localPosition;

    const glm::dvec3 relativeVelocity = body.velocityAtPoint(sample.applicationPoint) - atmosphere.windVelocity;
    const double speed = glm::length(relativeVelocity);
    if (speed <= 1.0e-6 || atmosphere.densityKgPerM3 <= 0.0 || surface.areaM2 <= 0.0) return sample;

    const glm::dvec3 velocityDirection = relativeVelocity / speed;
    const double forward = glm::dot(relativeVelocity, chord);
    const double normalVelocity = glm::dot(relativeVelocity, normal);
    sample.angleOfAttackRad = std::atan2(-normalVelocity, forward);

    const double stallAngle = std::clamp(surface.stallAngleRad, 1.0e-4, 0.5 * kPi - 1.0e-3);
    const double absAlpha = std::abs(sample.angleOfAttackRad);
    const double sign = sample.angleOfAttackRad < 0.0 ? -1.0 : 1.0;
    const double linearLift = surface.liftSlopePerRad * sample.angleOfAttackRad;
    const double maxLift = std::max(0.0, surface.maxLiftCoefficient);

    if (absAlpha <= stallAngle) {
        sample.liftCoefficient = std::clamp(linearLift, -maxLift, maxLift);
    } else {
        const double fade = std::clamp((0.5 * kPi - absAlpha) / (0.5 * kPi - stallAngle), 0.0, 1.0);
        sample.liftCoefficient = sign * maxLift * fade;
    }

    const double separation = std::sin(std::min(absAlpha, 0.5 * kPi));
    sample.dragCoefficient = std::max(0.0, surface.zeroLiftDragCoefficient)
        + std::max(0.0, surface.inducedDragFactor) * sample.liftCoefficient * sample.liftCoefficient
        + std::max(0.0, surface.stalledDragCoefficient) * separation * separation;

    sample.dynamicPressurePa = 0.5 * atmosphere.densityKgPerM3 * speed * speed;
    sample.dragForceN = -velocityDirection * (sample.dynamicPressurePa * sample.dragCoefficient * surface.areaM2);

    glm::dvec3 liftDirection = normal - velocityDirection * glm::dot(normal, velocityDirection);
    const double liftDirectionLength = glm::length(liftDirection);
    if (liftDirectionLength > 1.0e-6) {
        liftDirection /= liftDirectionLength;
        sample.liftForceN = liftDirection * (sample.dynamicPressurePa * sample.liftCoefficient * surface.areaM2);
    }

    sample.totalForceN = sample.liftForceN + sample.dragForceN;
    return sample;
}

void applyAerodynamicSurface(
    const AerodynamicSurface& surface,
    RigidBody& body,
    const AtmosphereSample& atmosphere) noexcept {
    const AerodynamicSurfaceSample sample = sampleAerodynamicSurface(surface, body, atmosphere);
    body.addForceAtPoint(sample.totalForceN, sample.applicationPoint);
}

} // namespace vf
