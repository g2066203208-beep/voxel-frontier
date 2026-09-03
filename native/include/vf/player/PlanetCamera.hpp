#pragma once

#include <cstdint>

#include <glm/glm.hpp>

#include "vf/world/CelestialSystem.hpp"
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
    explicit PlanetCamera(
        const PlanetDefinition& planet,
        const CelestialSystem* celestialSystem = nullptr,
        std::uint32_t primaryCelestialBodyId = 0U);

    void update(const PlanetMovementInput& input, double dt);

    [[nodiscard]] glm::mat4 viewProjection(float aspectRatio) const;
    [[nodiscard]] const glm::dvec3& position() const noexcept { return position_; }
    [[nodiscard]] const glm::dvec3& velocity() const noexcept { return velocity_; }
    [[nodiscard]] bool grounded() const noexcept { return grounded_; }
    [[nodiscard]] bool flightMode() const noexcept { return flightMode_; }
    [[nodiscard]] glm::dvec3 up() const;
    [[nodiscard]] glm::dvec3 forwardDirection() const;
    [[nodiscard]] double altitude() const;

private:
    [[nodiscard]] const CelestialBody* referenceBody(const glm::dvec3& position) const noexcept;
    [[nodiscard]] double minimumEyeRadius(const CelestialBody& body, const glm::dvec3& direction) const noexcept;

    const PlanetDefinition* planet_{};
    const CelestialSystem* celestialSystem_{};
    std::uint32_t primaryCelestialBodyId_{};
    glm::dvec3 position_{};
    glm::dvec3 velocity_{};
    double heading_{0.0};
    double pitch_{-0.18};
    double eyeHeight_{1.75};
    bool grounded_{};
    bool flightMode_{};
};

} // namespace vf
