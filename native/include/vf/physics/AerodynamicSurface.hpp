#pragma once

#include <cstdint>

#include <glm/glm.hpp>

#include "vf/physics/PhysicsWorld.hpp"

namespace vf {

struct AerodynamicSurface {
    std::uint32_t bodyId{};
    glm::dvec3 localPosition{};
    glm::dvec3 localChordAxis{1.0, 0.0, 0.0};
    glm::dvec3 localNormalAxis{0.0, 1.0, 0.0};
    double areaM2{1.0};
    double liftSlopePerRad{6.0};
    double stallAngleRad{0.2617993877991494};
    double maxLiftCoefficient{1.5};
    double zeroLiftDragCoefficient{0.02};
    double inducedDragFactor{0.06};
    double stalledDragCoefficient{1.1};
};

struct AerodynamicSurfaceSample {
    double angleOfAttackRad{};
    double liftCoefficient{};
    double dragCoefficient{};
    double dynamicPressurePa{};
    glm::dvec3 liftForceN{};
    glm::dvec3 dragForceN{};
    glm::dvec3 totalForceN{};
    glm::dvec3 applicationPoint{};
};

[[nodiscard]] AerodynamicSurfaceSample sampleAerodynamicSurface(
    const AerodynamicSurface& surface,
    const RigidBody& body,
    const AtmosphereSample& atmosphere) noexcept;

void applyAerodynamicSurface(
    const AerodynamicSurface& surface,
    RigidBody& body,
    const AtmosphereSample& atmosphere) noexcept;

} // namespace vf
