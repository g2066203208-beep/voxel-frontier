#pragma once

#include <cstdint>
#include <unordered_map>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

#include "vf/world/CelestialSystem.hpp"

namespace vf {

class PhysicsWorld;
struct RigidBody;

// Bridges inertial celestial motion and a low-speed nearby PhysicsWorld. During a fixed-step solve
// the active planet proxy is frozen in translation and rotation and rigid-body velocities are
// expressed relative to that frame. After the solve velocities are converted back to inertial
// world values for rendering and world-level systems. This prevents a contact solver from having
// to chase a 200+ m/s orbiting floor while preserving exact world-space handoff semantics.
class CelestialSurfaceFrames final {
public:
    void beforePhysics(PhysicsWorld& world, const CelestialSystem& celestial);
    void afterPhysics(PhysicsWorld& world, const CelestialSystem& celestial, double frameDeltaSeconds);

    [[nodiscard]] std::size_t attachmentCount() const noexcept { return attachments_.size(); }
    [[nodiscard]] bool isAttached(std::uint32_t bodyId) const noexcept;

private:
    struct Attachment {
        std::uint32_t celestialBodyId{};
        glm::dvec3 localPosition{};
        glm::dquat localOrientation{1.0, 0.0, 0.0, 0.0};
        double restTimer{};
        bool locked{};
        bool dynamicBody{};
        bool surfaceBound{};
    };

    [[nodiscard]] const CelestialBody* nearestSurfaceBody(
        const RigidBody& rigidBody,
        const PhysicsWorld& world,
        const CelestialSystem& celestial,
        double* signedGap = nullptr) const noexcept;

    void lockToBody(
        RigidBody& rigidBody,
        const CelestialBody& celestialBody,
        Attachment& attachment) noexcept;
    void updateLockedTransform(
        RigidBody& rigidBody,
        const CelestialBody& celestialBody,
        const Attachment& attachment) noexcept;
    void configureLocalProxy(PhysicsWorld& world, const CelestialBody& frameBody);

    std::unordered_map<std::uint32_t, Attachment> attachments_;
    CelestialSystem localPhysicsCelestial_{};
    const CelestialSystem* previousEnvironmentCelestial_{};

    std::uint32_t frameBodyId_{};
    glm::dvec3 previousFramePosition_{};
    glm::dvec3 previousFrameLinearVelocity_{};
    glm::dvec3 previousFrameAngularVelocity_{};
    glm::dquat previousFrameOrientation_{1.0, 0.0, 0.0, 0.0};
    bool previousFrameValid_{};
    bool localSolveActive_{};
};

} // namespace vf
