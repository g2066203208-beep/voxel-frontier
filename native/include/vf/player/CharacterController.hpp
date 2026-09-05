#pragma once

#include <cstdint>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

#include "vf/physics/PhysicsWorld.hpp"

namespace vf {

struct CharacterControllerSettings {
    double radius{0.36};
    double halfHeight{0.54};
    double eyeHeight{1.75};
    // Jolt CharacterVirtual keeps an explicit character padding and predictive-contact distance.
    // Our analytical terrain equivalent uses a slightly larger contact shell so the visible capsule
    // never needs to sink through the procedural surface before recovery begins.
    double contactOffset{0.045};
    double maxSlopeAngleRadians{0.8726646259971648}; // 50 degrees
    double stepHeight{0.45};
    double stickToFloorDistance{0.30};
    double walkSpeed{9.0};
    double sprintSpeed{18.0};
    double jumpSpeed{6.2};
    double groundAcceleration{28.0};
    double airAcceleration{7.0};
    // 8 cm keeps a fast 18 m/s sprint and ordinary falls from skipping thin floors while still
    // remaining cheap. moveWithCollisions also clamps this against the contact shell at runtime.
    double maxMoveSubstep{0.08};
    std::uint32_t maxDepenetrationIterations{12U};
    double characterMassKg{75.0};
    double maxPushImpulseNs{160.0};
};

struct CharacterControllerInput {
    glm::dvec3 forward{0.0, 0.0, -1.0};
    glm::dvec3 right{1.0, 0.0, 0.0};
    double forwardAxis{};
    double rightAxis{};
    bool jump{};
    bool sprint{};
};

class CharacterController final {
public:
    explicit CharacterController(PhysicsWorld& world, CharacterControllerSettings settings = {});

    void resetFromEye(
        const glm::dvec3& eyePosition,
        const glm::dvec3& linearVelocity = {},
        bool groundedHint = false) noexcept;

    void update(const CharacterControllerInput& input, double dt);

    [[nodiscard]] glm::dvec3 eyePosition() const noexcept;
    [[nodiscard]] const glm::dvec3& centerPosition() const noexcept { return position_; }
    [[nodiscard]] const glm::dvec3& linearVelocity() const noexcept { return velocity_; }
    [[nodiscard]] const glm::dvec3& up() const noexcept { return up_; }
    [[nodiscard]] const glm::dvec3& groundNormal() const noexcept { return groundNormal_; }
    [[nodiscard]] bool grounded() const noexcept { return grounded_; }
    [[nodiscard]] std::uint32_t groundBodyId() const noexcept { return groundBodyId_; }
    [[nodiscard]] const CharacterControllerSettings& settings() const noexcept { return settings_; }

private:
    struct ResolveResult {
        bool touched{};
        bool blocking{};
        bool supported{};
        glm::dvec3 supportNormal{0.0, 1.0, 0.0};
        std::uint32_t supportBodyId{};
    };

    [[nodiscard]] glm::dvec3 gravityUpAt(const glm::dvec3& position) const noexcept;
    [[nodiscard]] glm::dquat capsuleOrientation(const glm::dvec3& up) const noexcept;
    [[nodiscard]] ShapePose capsulePoseAt(const glm::dvec3& position) const noexcept;
    [[nodiscard]] bool walkableNormal(const glm::dvec3& normal, const glm::dvec3& gravityUp) const noexcept;

    ResolveResult resolveTerrain(glm::dvec3& position, glm::dvec3& velocity) const noexcept;
    ResolveResult resolveBodies(glm::dvec3& position, glm::dvec3& velocity, bool applyPushImpulse);
    ResolveResult resolveAll(glm::dvec3& position, glm::dvec3& velocity, bool applyPushImpulse);
    bool tryStep(const glm::dvec3& delta, glm::dvec3& outPosition, glm::dvec3& ioVelocity);
    bool stickToGround(glm::dvec3& ioPosition, glm::dvec3& ioVelocity, ResolveResult& ioSupport);
    void moveWithCollisions(const glm::dvec3& displacement);

    PhysicsWorld* world_{};
    CharacterControllerSettings settings_{};
    CollisionShape capsule_{};
    glm::dvec3 position_{};
    glm::dvec3 velocity_{};
    glm::dvec3 up_{0.0, 1.0, 0.0};
    glm::dvec3 groundNormal_{0.0, 1.0, 0.0};
    bool grounded_{};
    std::uint32_t groundBodyId_{};
};

} // namespace vf
