#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

#include <glm/glm.hpp>

namespace vf {

class PhysicsWorld;

struct RopeMaterial {
    double radiusMeters{0.035};
    double stretchComplianceMPerN{2.0e-7};
    double bendComplianceMPerN{5.0e-4};
    double damping{0.025};
    double friction{0.55};
    double dragCoefficient{1.1};
    double breakingStrain{0.35};
    double maxTensionN{25000.0};
    bool selfCollision{true};
};

struct RopeParticle {
    glm::dvec3 position{};
    glm::dvec3 previousPosition{};
    glm::dvec3 velocity{};
    double inverseMass{};
};

struct RopeCapsuleCollider {
    glm::dvec3 a{};
    glm::dvec3 b{0.0, 1.0, 0.0};
    double radiusMeters{0.5};
    double friction{0.7};
};

struct RopeRigidAttachment {
    std::size_t particleIndex{};
    std::uint32_t bodyId{};
    glm::dvec3 localAnchor{};
    bool enabled{true};
};

class RopeXpbd final {
public:
    void initialize(std::vector<glm::dvec3> points, double totalMassKg, RopeMaterial material = {});

    [[nodiscard]] bool initialized() const noexcept { return particles_.size() >= 2U; }
    [[nodiscard]] std::span<const RopeParticle> particles() const noexcept { return particles_; }
    [[nodiscard]] std::span<RopeParticle> particles() noexcept { return particles_; }
    [[nodiscard]] const RopeMaterial& material() const noexcept { return material_; }
    [[nodiscard]] double restLengthMeters() const noexcept;
    [[nodiscard]] double currentLengthMeters() const noexcept;
    [[nodiscard]] std::size_t brokenLinkCount() const noexcept;
    [[nodiscard]] double lastMaximumTensionN() const noexcept { return lastMaximumTensionN_; }

    void pinParticle(std::size_t index, const glm::dvec3& worldPosition);
    void setPinnedPosition(std::size_t index, const glm::dvec3& worldPosition);
    void unpinParticle(std::size_t index);

    void attachParticleToRigidBody(std::size_t index, std::uint32_t bodyId, const glm::dvec3& localAnchor = {});
    void clearRigidAttachments() noexcept { attachments_.clear(); }

    void clearCapsuleColliders() noexcept { capsuleColliders_.clear(); }
    void addCapsuleCollider(RopeCapsuleCollider collider);

    void step(
        double deltaSeconds,
        const glm::dvec3& gravityAcceleration,
        const glm::dvec3& windVelocity = {},
        double airDensityKgPerM3 = 0.0,
        PhysicsWorld* rigidWorld = nullptr);

private:
    [[nodiscard]] bool particleConstrained(std::size_t index) const noexcept;
    [[nodiscard]] double effectiveInverseMass(std::size_t index) const noexcept;
    void applyPinsAndAttachments(PhysicsWorld* rigidWorld, double dt);
    void solveDistanceConstraints(double dt);
    void solveBendingConstraints(double dt);
    void solveCapsuleCollisions();
    void solveSelfCollisions();
    void applyAttachmentReactions(PhysicsWorld* rigidWorld, double dt);

    RopeMaterial material_{};
    std::vector<RopeParticle> particles_;
    std::vector<double> restLengths_;
    std::vector<double> distanceLambdas_;
    std::vector<double> bendRestDistances_;
    std::vector<double> bendLambdas_;
    std::vector<std::uint8_t> linkBroken_;
    std::vector<std::uint8_t> pinned_;
    std::vector<glm::dvec3> pinnedPositions_;
    std::vector<RopeRigidAttachment> attachments_;
    std::vector<RopeCapsuleCollider> capsuleColliders_;
    double lastMaximumTensionN_{};
};

} // namespace vf
