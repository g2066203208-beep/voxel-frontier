#pragma once

#include <cstdint>

#include <glm/glm.hpp>

#include "vf/physics/PhysicsWorld.hpp"

namespace vf {

struct PhysicsInteractionInput {
    bool rightPressed{};
    bool leftPressed{};
};

class PhysicsInteraction final {
public:
    explicit PhysicsInteraction(PhysicsWorld& world) noexcept : world_(&world) {}

    void update(
        const glm::dvec3& rayOrigin,
        const glm::dvec3& rayDirection,
        const PhysicsInteractionInput& input,
        double deltaSeconds);

    void drop() noexcept;
    void throwHeld(const glm::dvec3& direction, double speedMetersPerSecond = 22.0) noexcept;

    [[nodiscard]] bool holding() const noexcept { return heldBodyId_ != 0U; }
    [[nodiscard]] std::uint32_t heldBodyId() const noexcept { return heldBodyId_; }
    [[nodiscard]] double holdDistance() const noexcept { return holdDistanceMeters_; }

private:
    [[nodiscard]] bool isConstrained(std::uint32_t bodyId) const noexcept;
    [[nodiscard]] std::uint32_t raycastClosestLooseDynamic(
        const glm::dvec3& rayOrigin,
        const glm::dvec3& rayDirection,
        double maxDistanceMeters,
        double& hitDistanceMeters) const noexcept;

    void beginHold(std::uint32_t bodyId, double hitDistanceMeters) noexcept;
    void restoreDynamic(RigidBody& body) noexcept;
    void moveHeldBody(
        const glm::dvec3& rayOrigin,
        const glm::dvec3& rayDirection,
        double deltaSeconds) noexcept;

    PhysicsWorld* world_{};
    std::uint32_t heldBodyId_{};
    double holdDistanceMeters_{3.0};
    glm::dvec3 heldVelocity_{};
};

} // namespace vf
