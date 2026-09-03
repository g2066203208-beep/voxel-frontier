#pragma once

#include <glm/glm.hpp>

#include "vf/world/PlanetSurface.hpp"

namespace vf {

struct PlanetMovementInput {
    double forward{};
    double right{};
    double vertical{};
    double mouseDx{};
    double mouseDy{};
    bool sprint{};
};

class PlanetCamera final {
public:
    explicit PlanetCamera(const PlanetDefinition& planet);

    void update(const PlanetMovementInput& input, double dt);

    [[nodiscard]] glm::mat4 viewProjection(float aspectRatio) const;
    [[nodiscard]] const glm::dvec3& position() const noexcept { return position_; }
    [[nodiscard]] glm::dvec3 up() const;
    [[nodiscard]] glm::dvec3 forwardDirection() const;
    [[nodiscard]] double altitude() const;

private:
    const PlanetDefinition* planet_{};
    glm::dvec3 position_{};
    double heading_{0.0};
    double pitch_{-0.18};
    double eyeHeight_{1.75};
};

} // namespace vf
