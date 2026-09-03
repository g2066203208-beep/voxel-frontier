#pragma once

#include <cstdint>

#include <glm/glm.hpp>

#include "vf/world/CelestialPhysicsFrame.hpp"
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
    [[nodiscard]] bool inPlanetPhysicsFrame() const noexcept { return inPhysicsFrame_; }
    [[nodiscard]] std::uint32_t physicsFrameBodyId() const noexcept { return physicsFrameBodyId_; }
    [[nodiscard]] glm::dvec3 up() const;
    [[nodiscard]] glm::dvec3 forwardDirection() const;
    [[nodiscard]] double altitude() const;

private:
    [[nodiscard]] const CelestialBody* physicsFrameBody() const noexcept;
    [[nodiscard]] double localMinimumEyeRadius(
        const CelestialBody& body,
        const glm::dvec3& localDirection) const noexcept;
    [[nodiscard]] glm::dvec3 localForwardDirection(const glm::dvec3& localUp) const noexcept;

    void enterPhysicsFrame(const CelestialBody& body) noexcept;
    void leavePhysicsFrame() noexcept;
    void syncWorldStateFromLocal(const CelestialBody& body) noexcept;

    const PlanetDefinition* planet_{};
    const CelestialSystem* celestialSystem_{};
    std::uint32_t primaryCelestialBodyId_{};

    // Public/render state is always inertial world space. While a nearby planet physics frame is
    // active, the authoritative simulation state is localPosition_/localVelocity_ and these values
    // are reconstructed after each update. This mirrors KSP's separation between sim space and the
    // low-speed local physics space.
    glm::dvec3 position_{};
    glm::dvec3 velocity_{};

    std::uint32_t physicsFrameBodyId_{};
    CelestialPhysicsFrame physicsFrame_{};
    glm::dvec3 localPosition_{};
    glm::dvec3 localVelocity_{};
    bool inPhysicsFrame_{};

    double heading_{0.0};
    double pitch_{-0.18};
    double eyeHeight_{1.75};
    bool grounded_{};
    bool flightMode_{};
};

} // namespace vf
