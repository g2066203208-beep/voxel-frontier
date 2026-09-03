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

struct ContactPoint {
    glm::dvec3 position{};
    double penetration{};
    double accumulatedNormalImpulse{};
    glm::dvec3 accumulatedTangentImpulse{};
};

struct ContactManifold {
    glm::dvec3 normal{1.0, 0.0, 0.0};
    std::array<ContactPoint, 4> points{};
    std::uint8_t pointCount{};

    [[nodiscard]] bool empty() const noexcept { return pointCount == 0; }
};

[[nodiscard]] Aabb computeWorldAabb(const CollisionShape& shape, const ShapePose& pose) noexcept;
[[nodiscard]] glm::dvec3 supportPoint(const CollisionShape& shape, const ShapePose& pose, const glm::dvec3& direction) noexcept;

// Specialized primitive narrowphase. The architecture intentionally keeps this API
// independent from PhysicsWorld so it can be validated in isolation and later used
// behind the broadphase/narrowphase split. Arbitrary convex pairs will be added via
// GJK/EPA on top of the same support-map interface.
[[nodiscard]] bool collideShapes(
    const CollisionShape& a,
    const ShapePose& poseA,
    const CollisionShape& b,
    const ShapePose& poseB,
    ContactManifold& manifold) noexcept;

} // namespace vf
