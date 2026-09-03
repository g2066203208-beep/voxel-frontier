#pragma once

#include <cstdint>
#include <unordered_map>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

namespace vf {

class CelestialSystem;
class PhysicsWorld;
struct CelestialBody;
struct RigidBody;

// Stabilizes objects that are at rest on a rotating/orbiting celestial surface.
// Authoritative celestial bodies still move in the inertial world; only bodies that have
// demonstrably come to rest are stored in a planet-local frame. This avoids the classic
// "sleeping object jitters forever because the floor itself has world-space velocity" problem.
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
    };

    [[nodiscard]] const CelestialBody* nearestSurfaceBody(
        const RigidBody& rigidBody,
        const PhysicsWorld& world,
        const CelestialSystem& celestial,
        double* signedGap = nullptr) const noexcept;
    void lockToBody(RigidBody& rigidBody, const CelestialBody& celestialBody, Attachment& attachment) noexcept;
    void updateLockedTransform(RigidBody& rigidBody, const CelestialBody& celestialBody, const Attachment& attachment) noexcept;

    std::unordered_map<std::uint32_t, Attachment> attachments_;
};

} // namespace vf
