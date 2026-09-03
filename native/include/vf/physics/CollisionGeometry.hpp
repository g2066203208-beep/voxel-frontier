#pragma once

#include <array>
#include <cstdint>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

namespace vf {

enum class CollisionShapeType : std::uint8_t {
    Sphere,
    Box,
    Capsule,
};

struct CollisionShape {
    CollisionShapeType type{CollisionShapeType::Sphere};
    double radius{0.5};
    glm::dvec3 halfExtents{0.5};
    double halfHeight{0.5};

    [[nodiscard]] static CollisionShape sphere(double radius) noexcept;
    [[nodiscard]] static CollisionShape box(const glm::dvec3& halfExtents) noexcept;
    [[nodiscard]] static CollisionShape capsule(double radius, double halfHeight) noexcept;
};

struct ShapePose {
    glm::dvec3 position{};
    glm::dquat orientation{1.0, 0.0, 0.0, 0.0};
};

struct Aabb {
    glm::dvec3 minimum{};
    glm::dvec3 maximum{};

    [[nodiscard]] bool overlaps(const Aabb& other) const noexcept;
};

// Pure narrow-phase geometry. Solver state (warm-start impulses, local anchors,
// lifetime) lives in PhysicsWorld's contact cache rather than leaking into shape code.
struct ContactPoint {
    glm::dvec3 position{};
    double penetration{};
    std::uint32_t featureId{};
};

struct ContactManifold {
    glm::dvec3 normal{1.0, 0.0, 0.0};
    std::array<ContactPoint, 4> points{};
    std::uint8_t pointCount{};

    [[nodiscard]] bool empty() const noexcept { return pointCount == 0; }
};

[[nodiscard]] Aabb computeWorldAabb(const CollisionShape& shape, const ShapePose& pose) noexcept;
[[nodiscard]] double collisionBoundingRadius(const CollisionShape& shape) noexcept;
[[nodiscard]] glm::dvec3 supportPoint(const CollisionShape& shape, const ShapePose& pose, const glm::dvec3& direction) noexcept;

// Primitive narrow phase. Sphere/box/capsule pairs use specialized tests where that
// is clearer and cheaper. Box/box uses full OBB SAT plus reference/incident face
// clipping to generate an actual contact patch (up to four points). General convex
// support-mapped pairs remain the next GJK/EPA layer.
[[nodiscard]] bool collideShapes(
    const CollisionShape& a,
    const ShapePose& poseA,
    const CollisionShape& b,
    const ShapePose& poseB,
    ContactManifold& manifold) noexcept;

} // namespace vf
