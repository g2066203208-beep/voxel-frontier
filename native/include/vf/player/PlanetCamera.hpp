#pragma once

#include <cstdint>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

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
    bool toggleFlight{};
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
    void rememberLocalFrame(const CelestialBody* bodyValue) noexcept;

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

    // Character motion inside a planetary SOI is solved relative to the moving planet frame.
    // These values store the previous celestial pose so each render frame can carry the player by
    // the exact orbit/spin delta before local walk/jump/creative-flight motion is integrated.
    std::uint32_t localFrameBodyId_{};
    glm::dvec3 previousFramePosition_{};
    glm::dvec3 previousFrameLinearVelocity_{};
    glm::dvec3 previousFrameAngularVelocity_{};
    glm::dquat previousFrameOrientation_{1.0, 0.0, 0.0, 0.0};
    bool localFrameInitialized_{};
};

} // namespace vf
