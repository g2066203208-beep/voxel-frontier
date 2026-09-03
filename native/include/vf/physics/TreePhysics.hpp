#pragma once

#include <cstdint>

#include <glm/glm.hpp>

namespace vf {

enum class TreeState : std::uint8_t {
    Standing,
    Hinging,
    Fallen,
};

struct TreePhysics {
    glm::dvec3 rootPosition{};
    glm::dvec3 localUp{0.0, 1.0, 0.0};
    glm::dvec3 fallDirection{1.0, 0.0, 0.0};
    double trunkLength{8.0};
    double trunkRadius{0.22};
    double trunkMass{280.0};
    double dragCoefficient{1.1};
    double cutFraction{};
    double hingeAngleRadians{};
    double angularVelocity{};
    TreeState state{TreeState::Standing};

    void applyCut(double normalizedAmount, const glm::dvec3& preferredFallDirection) noexcept;
    void step(double deltaSeconds, double gravityMagnitude, const glm::dvec3& windVelocity, double airDensityKgPerM3) noexcept;

    [[nodiscard]] glm::dvec3 trunkDirection() const noexcept;
    [[nodiscard]] glm::dvec3 tipPosition() const noexcept;
};

} // namespace vf
