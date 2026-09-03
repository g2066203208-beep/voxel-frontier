#include "vf/physics/CollisionGeometry.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

#include <glm/common.hpp>
#include <glm/geometric.hpp>
#include <glm/gtx/quaternion.hpp>

namespace vf {
namespace {

constexpr double kEpsilon = 1.0e-9;
constexpr double kSatEpsilon = 1.0e-8;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {1.0, 0.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= kEpsilon) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] glm::dvec3 absVector(const glm::dvec3& value) noexcept {
    return {std::abs(value.x), std::abs(value.y), std::abs(value.z)};
}

[[nodiscard]] double component(const glm::dvec3& value, int axis) noexcept {
    return axis == 0 ? value.x : (axis == 1 ? value.y : value.z);
}

[[nodiscard]] glm::dvec3 boxAxis(const ShapePose& pose, int axis) noexcept {
    const glm::dmat3 rotation = glm::mat3_cast(pose.orientation);
    return safeNormalize(rotation[axis], axis == 0 ? glm::dvec3{1.0, 0.0, 0.0}
        : axis == 1 ? glm::dvec3{0.0, 1.0, 0.0}
                    : glm::dvec3{0.0, 0.0, 1.0});
}

[[nodiscard]] glm::dvec3 capsuleAxis(const ShapePose& pose) noexcept {
    return safeNormalize(pose.orientation * glm::dvec3{0.0, 1.0, 0.0}, {0.0, 1.0, 0.0});
}

void capsuleSegment(
    const CollisionShape& capsule,
    const ShapePose& pose,
    glm::dvec3& outA,
    glm::dvec3& outB) noexcept {
    const glm::dvec3 axis = capsuleAxis(pose);
    const double halfHeight = std::max(0.0, capsule.halfHeight);
    outA = pose.position - axis * halfHeight;
    outB = pose.position + axis * halfHeight;
}

[[nodiscard]] glm::dvec3 closestPointOnSegment(
    const glm::dvec3& a,
    const glm::dvec3& b,
    const glm::dvec3& point) noexcept {
    const glm::dvec3 ab = b - a;
    const double denominator = glm::dot(ab, ab);
    if (denominator <= kEpsilon) return a;
    const double t = std::clamp(glm::dot(point - a, ab) / denominator, 0.0, 1.0);
    return a + ab * t;
}

void closestPointsOnSegments(
    const glm::dvec3& p1,
    const glm::dvec3& q1,
    const glm::dvec3& p2,
    const glm::dvec3& q2,
    glm::dvec3& c1,
    glm::dvec3& c2) noexcept {
    const glm::dvec3 d1 = q1 - p1;
    const glm::dvec3 d2 = q2 - p2;
    const glm::dvec3 r = p1 - p2;
    const double a = glm::dot(d1, d1);
    const double e = glm::dot(d2, d2);
    const double f = glm::dot(d2, r);

    double s = 0.0;
    double t = 0.0;
    if (a <= kEpsilon && e <= kEpsilon) {
        c1 = p1;
        c2 = p2;
        return;
    }
    if (a <= kEpsilon) {
        t = std::clamp(f / e, 0.0, 1.0);
    } else {
        const double c = glm::dot(d1, r);
        if (e <= kEpsilon) {
            s = std::clamp(-c / a, 0.0, 1.0);
        } else {
            const double b = glm::dot(d1, d2);
            const double denominator = a * e - b * b;
            if (std::abs(denominator) > kEpsilon) {
                s = std::clamp((b * f - c * e) / denominator, 0.0, 1.0);
            }
            const double tNumerator = b * s + f;
            if (tNumerator < 0.0) {
                t = 0.0;
                s = std::clamp(-c / a, 0.0, 1.0);
            } else if (tNumerator > e) {
                t = 1.0;
                s = std::clamp((b - c) / a, 0.0, 1.0);
            } else {
                t = tNumerator / e;
            }
        }
    }

    c1 = p1 + d1 * s;
    c2 = p2 + d2 * t;
}

void setSingleContact(
    ContactManifold& manifold,
    const glm::dvec3& normal,
    const glm::dvec3& position,
    double penetration) noexcept {
    manifold.normal = safeNormalize(normal);
    manifold.pointCount = 1;
    manifold.points[0] = ContactPoint{position, std::max(0.0, penetration), 0.0, {}};
}

[[nodiscard]] bool sphereSphere(
    const CollisionShape& a,
    const ShapePose& poseA,
    const CollisionShape& b,
    const ShapePose& poseB,
    ContactManifold& manifold) noexcept {
    const double radiusA = std::max(0.0, a.radius);
    const double radiusB = std::max(0.0, b.radius);
    const glm::dvec3 delta = poseB.position - poseA.position;
    const double distanceSquared = glm::dot(delta, delta);
    const double radiusSum = radiusA + radiusB;
    if (distanceSquared >= radiusSum * radiusSum) return false;

    const double distance = std::sqrt(std::max(distanceSquared, 0.0));
    const glm::dvec3 normal = distance > kEpsilon ? delta / distance : glm::dvec3{1.0, 0.0, 0.0};
    const double penetration = radiusSum - distance;
    const glm::dvec3 pointA = poseA.position + normal * radiusA;
    const glm::dvec3 pointB = poseB.position - normal * radiusB;
    setSingleContact(manifold, normal, 0.5 * (pointA + pointB), penetration);
    return true;
}

[[nodiscard]] bool sphereBox(
    const CollisionShape& sphere,
    const ShapePose& spherePose,
    const CollisionShape& box,
    const ShapePose& boxPose,
    ContactManifold& manifold) noexcept {
    const double radius = std::max(0.0, sphere.radius);
    const glm::dvec3 extents = glm::max(absVector(box.halfExtents), glm::dvec3{1.0e-9});
    const glm::dquat inverseRotation = glm::conjugate(glm::normalize(boxPose.orientation));
    const glm::dvec3 localCenter = inverseRotation * (spherePose.position - boxPose.position);
    const glm::dvec3 localClosest = glm::clamp(localCenter, -extents, extents);
    const glm::dvec3 boxToSphereLocal = localCenter - localClosest;
    const double distanceSquared = glm::dot(boxToSphereLocal, boxToSphereLocal);

    glm::dvec3 normalBoxToSphereLocal{};
    glm::dvec3 contactLocal = localClosest;
    double penetration = 0.0;

    if (distanceSquared > kEpsilon) {
        if (distanceSquared >= radius * radius) return false;
        const double distance = std::sqrt(distanceSquared);
        normalBoxToSphereLocal = boxToSphereLocal / distance;
        penetration = radius - distance;
    } else {
        const glm::dvec3 distances = extents - absVector(localCenter);
        int axis = 0;
        if (distances.y < distances.x) axis = 1;
        if (distances.z < component(distances, axis)) axis = 2;
        normalBoxToSphereLocal = {};
        const double sign = component(localCenter, axis) >= 0.0 ? 1.0 : -1.0;
        normalBoxToSphereLocal[axis] = sign;
        contactLocal = localCenter;
        contactLocal[axis] = sign * component(extents, axis);
        penetration = radius + component(distances, axis);
    }

    const glm::dvec3 normalBoxToSphere = safeNormalize(boxPose.orientation * normalBoxToSphereLocal);
    const glm::dvec3 normalSphereToBox = -normalBoxToSphere;
    const glm::dvec3 pointOnBox = boxPose.position + boxPose.orientation * contactLocal;
    const glm::dvec3 pointOnSphere = spherePose.position + normalSphereToBox * radius;
    setSingleContact(manifold, normalSphereToBox, 0.5 * (pointOnBox + pointOnSphere), penetration);
    return true;
}

[[nodiscard]] bool sphereCapsule(
    const CollisionShape& sphere,
    const ShapePose& spherePose,
    const CollisionShape& capsule,
    const ShapePose& capsulePose,
    ContactManifold& manifold) noexcept {
    glm::dvec3 segmentA{};
    glm::dvec3 segmentB{};
    capsuleSegment(capsule, capsulePose, segmentA, segmentB);
    const glm::dvec3 closest = closestPointOnSegment(segmentA, segmentB, spherePose.position);
    const glm::dvec3 capsuleToSphere = spherePose.position - closest;
    const double distanceSquared = glm::dot(capsuleToSphere, capsuleToSphere);
    const double radiusSum = std::max(0.0, sphere.radius) + std::max(0.0, capsule.radius);
    if (distanceSquared >= radiusSum * radiusSum) return false;

    const double distance = std::sqrt(std::max(0.0, distanceSquared));
    const glm::dvec3 capsuleToSphereNormal = distance > kEpsilon
        ? capsuleToSphere / distance
        : safeNormalize(spherePose.position - capsulePose.position, {1.0, 0.0, 0.0});
    const glm::dvec3 sphereToCapsuleNormal = -capsuleToSphereNormal;
    const double penetration = radiusSum - distance;
    const glm::dvec3 pointSphere = spherePose.position + sphereToCapsuleNormal * std::max(0.0, sphere.radius);
    const glm::dvec3 pointCapsule = closest + capsuleToSphereNormal * std::max(0.0, capsule.radius);
    setSingleContact(manifold, sphereToCapsuleNormal, 0.5 * (pointSphere + pointCapsule), penetration);
    return true;
}

[[nodiscard]] bool capsuleCapsule(
    const CollisionShape& a,
    const ShapePose& poseA,
    const CollisionShape& b,
    const ShapePose& poseB,
    ContactManifold& manifold) noexcept {
    glm::dvec3 a0{};
    glm::dvec3 a1{};
    glm::dvec3 b0{};
    glm::dvec3 b1{};
    capsuleSegment(a, poseA, a0, a1);
    capsuleSegment(b, poseB, b0, b1);

    glm::dvec3 closestA{};
    glm::dvec3 closestB{};
    closestPointsOnSegments(a0, a1, b0, b1, closestA, closestB);
    const glm::dvec3 delta = closestB - closestA;
    const double distanceSquared = glm::dot(delta, delta);
    const double radiusA = std::max(0.0, a.radius);
    const double radiusB = std::max(0.0, b.radius);
    const double radiusSum = radiusA + radiusB;
    if (distanceSquared >= radiusSum * radiusSum) return false;

    const double distance = std::sqrt(std::max(0.0, distanceSquared));
    const glm::dvec3 normal = distance > kEpsilon
        ? delta / distance
        : safeNormalize(poseB.position - poseA.position, {1.0, 0.0, 0.0});
    const double penetration = radiusSum - distance;
    const glm::dvec3 pointA = closestA + normal * radiusA;
    const glm::dvec3 pointB = closestB - normal * radiusB;
    setSingleContact(manifold, normal, 0.5 * (pointA + pointB), penetration);
    return true;
}

[[nodiscard]] bool boxBox(
    const CollisionShape& a,
    const ShapePose& poseA,
    const CollisionShape& b,
    const ShapePose& poseB,
    ContactManifold& manifold) noexcept {
    const glm::dvec3 extentsA = glm::max(absVector(a.halfExtents), glm::dvec3{1.0e-9});
    const glm::dvec3 extentsB = glm::max(absVector(b.halfExtents), glm::dvec3{1.0e-9});

    std::array<glm::dvec3, 3> axesA{boxAxis(poseA, 0), boxAxis(poseA, 1), boxAxis(poseA, 2)};
    std::array<glm::dvec3, 3> axesB{boxAxis(poseB, 0), boxAxis(poseB, 1), boxAxis(poseB, 2)};
    double rotation[3][3]{};
    double absRotation[3][3]{};
    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 3; ++j) {
            rotation[i][j] = glm::dot(axesA[i], axesB[j]);
            absRotation[i][j] = std::abs(rotation[i][j]) + kSatEpsilon;
        }
    }

    const glm::dvec3 centerDelta = poseB.position - poseA.position;
    double t[3]{
        glm::dot(centerDelta, axesA[0]),
        glm::dot(centerDelta, axesA[1]),
        glm::dot(centerDelta, axesA[2]),
    };

    double minimumOverlap = std::numeric_limits<double>::infinity();
    glm::dvec3 minimumAxis{1.0, 0.0, 0.0};
    auto testAxis = [&](const glm::dvec3& worldAxis, double signedDistance, double radiusA, double radiusB) noexcept {
        const double overlap = radiusA + radiusB - std::abs(signedDistance);
        if (overlap < 0.0) return false;
        if (overlap < minimumOverlap) {
            minimumOverlap = overlap;
            minimumAxis = safeNormalize(worldAxis) * (signedDistance >= 0.0 ? 1.0 : -1.0);
        }
        return true;
    };

    for (int i = 0; i < 3; ++i) {
        const double rb = extentsB.x * absRotation[i][0]
            + extentsB.y * absRotation[i][1]
            + extentsB.z * absRotation[i][2];
        if (!testAxis(axesA[i], t[i], component(extentsA, i), rb)) return false;
    }

    for (int j = 0; j < 3; ++j) {
        const double signedDistance = t[0] * rotation[0][j]
            + t[1] * rotation[1][j]
            + t[2] * rotation[2][j];
        const double ra = extentsA.x * absRotation[0][j]
            + extentsA.y * absRotation[1][j]
            + extentsA.z * absRotation[2][j];
        if (!testAxis(axesB[j], signedDistance, ra, component(extentsB, j))) return false;
    }

    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 3; ++j) {
            const glm::dvec3 axis = glm::cross(axesA[i], axesB[j]);
            const double axisLengthSquared = glm::dot(axis, axis);
            if (axisLengthSquared <= 1.0e-12) continue;
            const int i1 = (i + 1) % 3;
            const int i2 = (i + 2) % 3;
            const int j1 = (j + 1) % 3;
            const int j2 = (j + 2) % 3;
            const double ra = component(extentsA, i1) * absRotation[i2][j]
                + component(extentsA, i2) * absRotation[i1][j];
            const double rb = component(extentsB, j1) * absRotation[i][j2]
                + component(extentsB, j2) * absRotation[i][j1];
            const double signedDistance = t[i2] * rotation[i1][j] - t[i1] * rotation[i2][j];
            if (!testAxis(axis, signedDistance, ra, rb)) return false;
        }
    }

    if (!std::isfinite(minimumOverlap)) return false;
    if (glm::dot(minimumAxis, centerDelta) < 0.0) minimumAxis = -minimumAxis;
    const glm::dvec3 pointA = supportPoint(a, poseA, minimumAxis);
    const glm::dvec3 pointB = supportPoint(b, poseB, -minimumAxis);
    setSingleContact(manifold, minimumAxis, 0.5 * (pointA + pointB), minimumOverlap);
    return true;
}

void flipManifold(ContactManifold& manifold) noexcept {
    manifold.normal = -manifold.normal;
}

} // namespace

CollisionShape CollisionShape::sphere(double sphereRadius) noexcept {
    CollisionShape shape{};
    shape.type = CollisionShapeType::Sphere;
    shape.radius = std::max(0.001, sphereRadius);
    shape.halfExtents = {shape.radius, shape.radius, shape.radius};
    shape.halfHeight = 0.0;
    return shape;
}

CollisionShape CollisionShape::box(const glm::dvec3& extents) noexcept {
    CollisionShape shape{};
    shape.type = CollisionShapeType::Box;
    shape.halfExtents = glm::max(absVector(extents), glm::dvec3{0.001});
    shape.radius = glm::length(shape.halfExtents);
    shape.halfHeight = 0.0;
    return shape;
}

CollisionShape CollisionShape::capsule(double capsuleRadius, double capsuleHalfHeight) noexcept {
    CollisionShape shape{};
    shape.type = CollisionShapeType::Capsule;
    shape.radius = std::max(0.001, capsuleRadius);
    shape.halfHeight = std::max(0.0, capsuleHalfHeight);
    shape.halfExtents = {shape.radius, shape.radius + shape.halfHeight, shape.radius};
    return shape;
}

bool Aabb::overlaps(const Aabb& other) const noexcept {
    return minimum.x <= other.maximum.x && maximum.x >= other.minimum.x
        && minimum.y <= other.maximum.y && maximum.y >= other.minimum.y
        && minimum.z <= other.maximum.z && maximum.z >= other.minimum.z;
}

Aabb computeWorldAabb(const CollisionShape& shape, const ShapePose& pose) noexcept {
    glm::dvec3 worldHalfExtents{};
    switch (shape.type) {
    case CollisionShapeType::Sphere:
        worldHalfExtents = glm::dvec3{std::max(0.0, shape.radius)};
        break;
    case CollisionShapeType::Box: {
        const glm::dmat3 rotation = glm::mat3_cast(glm::normalize(pose.orientation));
        const glm::dvec3 local = glm::max(absVector(shape.halfExtents), glm::dvec3{0.0});
        worldHalfExtents = {
            std::abs(rotation[0].x) * local.x + std::abs(rotation[1].x) * local.y + std::abs(rotation[2].x) * local.z,
            std::abs(rotation[0].y) * local.x + std::abs(rotation[1].y) * local.y + std::abs(rotation[2].y) * local.z,
            std::abs(rotation[0].z) * local.x + std::abs(rotation[1].z) * local.y + std::abs(rotation[2].z) * local.z,
        };
        break;
    }
    case CollisionShapeType::Capsule: {
        const glm::dvec3 axis = absVector(capsuleAxis(pose));
        worldHalfExtents = axis * std::max(0.0, shape.halfHeight) + glm::dvec3{std::max(0.0, shape.radius)};
        break;
    }
    }
    return {pose.position - worldHalfExtents, pose.position + worldHalfExtents};
}

glm::dvec3 supportPoint(
    const CollisionShape& shape,
    const ShapePose& pose,
    const glm::dvec3& direction) noexcept {
    const glm::dvec3 worldDirection = safeNormalize(direction);
    switch (shape.type) {
    case CollisionShapeType::Sphere:
        return pose.position + worldDirection * std::max(0.0, shape.radius);
    case CollisionShapeType::Box: {
        const glm::dquat inverseRotation = glm::conjugate(glm::normalize(pose.orientation));
        const glm::dvec3 localDirection = inverseRotation * worldDirection;
        const glm::dvec3 extents = glm::max(absVector(shape.halfExtents), glm::dvec3{0.0});
        const glm::dvec3 localPoint{
            localDirection.x >= 0.0 ? extents.x : -extents.x,
            localDirection.y >= 0.0 ? extents.y : -extents.y,
            localDirection.z >= 0.0 ? extents.z : -extents.z,
        };
        return pose.position + pose.orientation * localPoint;
    }
    case CollisionShapeType::Capsule: {
        const glm::dvec3 axis = capsuleAxis(pose);
        const glm::dvec3 segmentCenter = pose.position
            + axis * (glm::dot(worldDirection, axis) >= 0.0 ? std::max(0.0, shape.halfHeight) : -std::max(0.0, shape.halfHeight));
        return segmentCenter + worldDirection * std::max(0.0, shape.radius);
    }
    }
    return pose.position;
}

bool collideShapes(
    const CollisionShape& a,
    const ShapePose& poseA,
    const CollisionShape& b,
    const ShapePose& poseB,
    ContactManifold& manifold) noexcept {
    manifold = {};

    if (a.type == CollisionShapeType::Sphere && b.type == CollisionShapeType::Sphere) {
        return sphereSphere(a, poseA, b, poseB, manifold);
    }
    if (a.type == CollisionShapeType::Sphere && b.type == CollisionShapeType::Box) {
        return sphereBox(a, poseA, b, poseB, manifold);
    }
    if (a.type == CollisionShapeType::Box && b.type == CollisionShapeType::Sphere) {
        const bool hit = sphereBox(b, poseB, a, poseA, manifold);
        if (hit) flipManifold(manifold);
        return hit;
    }
    if (a.type == CollisionShapeType::Sphere && b.type == CollisionShapeType::Capsule) {
        return sphereCapsule(a, poseA, b, poseB, manifold);
    }
    if (a.type == CollisionShapeType::Capsule && b.type == CollisionShapeType::Sphere) {
        const bool hit = sphereCapsule(b, poseB, a, poseA, manifold);
        if (hit) flipManifold(manifold);
        return hit;
    }
    if (a.type == CollisionShapeType::Capsule && b.type == CollisionShapeType::Capsule) {
        return capsuleCapsule(a, poseA, b, poseB, manifold);
    }
    if (a.type == CollisionShapeType::Box && b.type == CollisionShapeType::Box) {
        return boxBox(a, poseA, b, poseB, manifold);
    }

    // Box/capsule and future general convex pairs deliberately fall through here.
    // They will use the same supportPoint() API through GJK + EPA rather than an
    // approximate ad-hoc test.
    return false;
}

} // namespace vf
