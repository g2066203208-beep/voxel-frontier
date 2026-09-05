#pragma once

#include <cstdint>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

namespace vf {

class CelestialSystem;
struct CelestialBody;

// Converts between the high-precision inertial solar-system state and a nearby rotating
// planet/moon physics space. Static terrain and buildings are stationary in this frame; dynamic
// bodies carry only their local speeds, so contact solvers never need to resolve a planet's
// hundreds-of-metres-per-second orbital motion or tens-of-metres-per-second surface rotation.
class CelestialPhysicsFrame final {
public:
    CelestialPhysicsFrame() = default;
    explicit CelestialPhysicsFrame(std::uint32_t celestialBodyId) : celestialBodyId_(celestialBodyId) {}

    void setBodyId(std::uint32_t celestialBodyId) noexcept { celestialBodyId_ = celestialBodyId; }
    [[nodiscard]] std::uint32_t bodyId() const noexcept { return celestialBodyId_; }

    [[nodiscard]] glm::dvec3 toLocalPosition(
        const CelestialBody& body,
        const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] glm::dvec3 toWorldPosition(
        const CelestialBody& body,
        const glm::dvec3& localPosition) const noexcept;

    [[nodiscard]] glm::dquat toLocalOrientation(
        const CelestialBody& body,
        const glm::dquat& worldOrientation) const noexcept;
    [[nodiscard]] glm::dquat toWorldOrientation(
        const CelestialBody& body,
        const glm::dquat& localOrientation) const noexcept;

    // Velocity conversion includes both frame translation and the omega x r velocity of the
    // rotating planet. This is the critical no-jitter handoff used when a rover, aircraft or
    // spacecraft enters/leaves the local physics bubble.
    [[nodiscard]] glm::dvec3 toLocalVelocity(
        const CelestialBody& body,
        const glm::dvec3& worldPosition,
        const glm::dvec3& worldVelocity) const noexcept;
    [[nodiscard]] glm::dvec3 toWorldVelocity(
        const CelestialBody& body,
        const glm::dvec3& localPosition,
        const glm::dvec3& localVelocity) const noexcept;

    [[nodiscard]] glm::dvec3 localAngularVelocity(const CelestialBody& body) const noexcept;

    // Apparent acceleration in the rotating local frame. `relativePhysicalAccelerationWorld`
    // should already have the frame origin's common-mode external acceleration removed. For the
    // current constant-spin celestial model Euler acceleration is zero, leaving Coriolis and
    // centrifugal terms. This costs only a few cross products per active body.
    [[nodiscard]] glm::dvec3 apparentAcceleration(
        const CelestialBody& body,
        const glm::dvec3& localPosition,
        const glm::dvec3& localVelocity,
        const glm::dvec3& relativePhysicalAccelerationWorld) const noexcept;

    [[nodiscard]] glm::dvec3 gravityAcceleration(
        const CelestialSystem& system,
        const CelestialBody& body,
        const glm::dvec3& localPosition,
        const glm::dvec3& localVelocity) const noexcept;

private:
    std::uint32_t celestialBodyId_{};
};

} // namespace vf
