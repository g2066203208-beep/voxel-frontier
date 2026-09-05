#pragma once

#include <cmath>
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
    // startDirection is initialization-only; the existing V7 movement, attitude transport and
    // celestial reference-frame behavior remain authoritative after construction.
    explicit PlanetCamera(
        const PlanetDefinition& planet,
        const CelestialSystem* celestialSystem = nullptr,
        std::uint32_t primaryCelestialBodyId = 0U,
        const glm::dvec3& startDirection = glm::dvec3{0.72, 0.52, 0.46});

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

    // Deterministic view hook used by real-framebuffer regression capture and editor/debug tools.
    // It changes view attitude only; it never teleports the camera or alters celestial/physics state.
    // Production input immediately continues from this attitude, which makes the hook safe for
    // fixed-camera Sun/Moon sequences without adding a separate fake rendering path.
    void setViewDirectionWorld(
        const glm::dvec3& forwardInput,
        const glm::dvec3& upHintInput) noexcept {
        const double forwardLengthSquared = glm::dot(forwardInput, forwardInput);
        if (forwardLengthSquared <= 1.0e-18) return;
        const glm::dvec3 forward = forwardInput / std::sqrt(forwardLengthSquared);

        glm::dvec3 upHint = upHintInput;
        double upLengthSquared = glm::dot(upHint, upHint);
        if (upLengthSquared <= 1.0e-18) upHint = {0.0, 1.0, 0.0};
        else upHint /= std::sqrt(upLengthSquared);

        glm::dvec3 right = glm::cross(forward, upHint);
        double rightLengthSquared = glm::dot(right, right);
        if (rightLengthSquared <= 1.0e-18) {
            const glm::dvec3 fallback = std::abs(forward.y) < 0.92
                ? glm::dvec3{0.0, 1.0, 0.0}
                : glm::dvec3{1.0, 0.0, 0.0};
            right = glm::cross(forward, fallback);
            rightLengthSquared = glm::dot(right, right);
            if (rightLengthSquared <= 1.0e-18) return;
        }
        right /= std::sqrt(rightLengthSquared);
        glm::dvec3 up = glm::cross(right, forward);
        const double upSquared = glm::dot(up, up);
        if (upSquared <= 1.0e-18) return;
        up /= std::sqrt(upSquared);

        viewForward_ = forward;
        viewUp_ = up;
        viewAttitudeValid_ = true;
        surfaceTransportValid_ = false;
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
