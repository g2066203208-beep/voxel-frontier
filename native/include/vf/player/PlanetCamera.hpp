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
    double flightSpeedSteps{};
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

    void setExternalWorldState(
        const glm::dvec3& worldPosition,
        const glm::dvec3& worldVelocity,
        bool grounded) noexcept {
        position_ = worldPosition;
        velocity_ = worldVelocity;
        grounded_ = grounded;
        if (const CelestialBody* body = physicsFrameBody()) {
            localPosition_ = physicsFrame_.toLocalPosition(*body, worldPosition);
            localVelocity_ = physicsFrame_.toLocalVelocity(*body, worldPosition, worldVelocity);
        }
    }

    [[nodiscard]] glm::mat4 viewProjection(float aspectRatio) const;
    [[nodiscard]] const glm::dvec3& position() const noexcept { return position_; }
    [[nodiscard]] const glm::dvec3& velocity() const noexcept { return velocity_; }
    [[nodiscard]] bool grounded() const noexcept { return grounded_; }
    [[nodiscard]] bool flightMode() const noexcept { return flightMode_; }
    [[nodiscard]] bool inPlanetPhysicsFrame() const noexcept { return inPhysicsFrame_; }
    [[nodiscard]] std::uint32_t physicsFrameBodyId() const noexcept { return physicsFrameBodyId_; }
    [[nodiscard]] double flightSpeedMps() const noexcept { return creativeFlightSpeedMps_; }
    [[nodiscard]] glm::dvec3 up() const;
    [[nodiscard]] glm::dvec3 forwardDirection() const;
    [[nodiscard]] double altitude() const;

private:
    [[nodiscard]] const CelestialBody* physicsFrameBody() const noexcept;
    [[nodiscard]] double localMinimumEyeRadius(
        const CelestialBody& body,
        const glm::dvec3& localDirection) const noexcept;
    [[nodiscard]] glm::dvec3 currentSurfaceUpWorld() const noexcept;
    [[nodiscard]] double surfaceAttitudeInfluence() const noexcept;

    void enterPhysicsFrame(const CelestialBody& body) noexcept;
    void leavePhysicsFrame() noexcept;
    void syncWorldStateFromLocal(const CelestialBody& body) noexcept;

    // View attitude is authoritative in world space in every reference frame. Surface travel only
    // parallel-transports this attitude as the local gravity-up changes; it never rebuilds heading
    // from a global latitude/longitude basis. That removes the pole/high-latitude singularity and
    // also means entering/leaving a celestial physics frame cannot itself snap the camera.
    void initializeViewAttitude(const glm::dvec3& surfaceUpWorld) noexcept;
    void transportViewAttitude(const glm::dvec3& surfaceUpWorld, double influence) noexcept;
    void alignViewUpToSurface(const glm::dvec3& surfaceUpWorld, double influence, double dt) noexcept;
    void rotateSurfaceAttitude(
        double mouseDx,
        double mouseDy,
        const glm::dvec3& surfaceUpWorld) noexcept;
    void rotateFreeAttitude(double mouseDx, double mouseDy) noexcept;

    const PlanetDefinition* planet_{};
    const CelestialSystem* celestialSystem_{};
    std::uint32_t primaryCelestialBodyId_{};

    glm::dvec3 position_{};
    glm::dvec3 velocity_{};

    std::uint32_t physicsFrameBodyId_{};
    CelestialPhysicsFrame physicsFrame_{};
    glm::dvec3 localPosition_{};
    glm::dvec3 localVelocity_{};
    bool inPhysicsFrame_{};

    glm::dvec3 viewForward_{0.0, 0.0, -1.0};
    glm::dvec3 viewUp_{0.0, 1.0, 0.0};
    glm::dvec3 transportedSurfaceUp_{0.0, 1.0, 0.0};
    bool viewAttitudeValid_{};
    bool surfaceTransportValid_{};

    double eyeHeight_{1.75};
    double creativeFlightSpeedMps_{320.0};
    bool grounded_{};
    bool flightMode_{};
};

} // namespace vf
