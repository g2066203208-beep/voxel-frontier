#include "vf/physics/CollisionGeometry.hpp"
#include "vf/physics/GjkEpa.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>

#include <glm/common.hpp>
#include <glm/geometric.hpp>
#include <glm/gtc/quaternion.hpp>

namespace vf {
namespace {

constexpr double kEpsilon = 1.0e-9;
constexpr double kSatEpsilon = 1.0e-8;
constexpr double kContactTolerance = 1.0e-7;

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

[[nodiscard]] std::array<glm::dvec3, 3> boxAxes(const ShapePose& pose) noexcept {
    const glm::dmat3 rotation = glm::mat3_cast(glm::normalize(pose.orientation));
    return {
        safeNormalize(rotation[0], {1.0, 0.0, 0.0}),
        safeNormalize(rotation[1], {0.0, 1.0, 0.0}),
        safeNormalize(rotation[2], {0.0, 0.0, 1.0}),
    };
}

[[nodiscard]] glm::dvec3 capsuleAxis(const ShapePose& pose) noexcept {
    return safeNormalize(glm::normalize(pose.orientation) * glm::dvec3{0.0, 1.0, 0.0}, {0.0, 1.0, 0.0});
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
    double penetration,
    std::uint32_t featureId = 0U) noexcept {
    manifold.normal = safeNormalize(normal);
    manifold.pointCount = 1;
    manifold.points[0] = ContactPoint{position, std::max(0.0, penetration), featureId};
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
    const glm::dquat orientation = glm::normalize(boxPose.orientation);
    const glm::dquat inverseRotation = glm::conjugate(orientation);
    const glm::dvec3 localCenter = inverseRotation * (spherePose.position - boxPose.position);
    const glm::dvec3 localClosest = glm::clamp(localCenter, -extents, extents);
    const glm::dvec3 boxToSphereLocal = localCenter - localClosest;
    const double distanceSquared = glm::dot(boxToSphereLocal, boxToSphereLocal);

    glm::dvec3 normalBoxToSphereLocal{};
    glm::dvec3 contactLocal = localClosest;
    double penetration = 0.0;
    std::uint32_t feature = 0U;

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
        feature = static_cast<std::uint32_t>(axis * 2 + (sign > 0.0 ? 1 : 0));
    }

    const glm::dvec3 normalBoxToSphere = safeNormalize(orientation * normalBoxToSphereLocal);
    const glm::dvec3 normalSphereToBox = -normalBoxToSphere;
    const glm::dvec3 pointOnBox = boxPose.position + orientation * contactLocal;
    const glm::dvec3 pointOnSphere = spherePose.position + normalSphereToBox * radius;
    setSingleContact(manifold, normalSphereToBox, 0.5 * (pointOnBox + pointOnSphere), penetration, feature);
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

enum class SatAxisKind : std::uint8_t {
    FaceA,
    FaceB,
    EdgeEdge,
};

struct SatResult {
    double overlap{std::numeric_limits<double>::infinity()};
    glm::dvec3 normal{1.0, 0.0, 0.0};
    SatAxisKind kind{SatAxisKind::FaceA};
    int axisA{};
    int axisB{};
};

[[nodiscard]] bool updateSatResult(
    SatResult& result,
    double overlap,
    const glm::dvec3& axis,
    const glm::dvec3& centerDelta,
    SatAxisKind kind,
    int axisA,
    int axisB) noexcept {
    if (overlap < 0.0) return false;
    if (overlap >= result.overlap) return true;

    glm::dvec3 normal = safeNormalize(axis);
    if (glm::dot(normal, centerDelta) < 0.0) normal = -normal;
    result.overlap = overlap;
    result.normal = normal;
    result.kind = kind;
    result.axisA = axisA;
    result.axisB = axisB;
    return true;
}

struct ClippedPolygon {
    std::array<glm::dvec3, 8> points{};
    std::size_t count{};
};

void clipPolygonAgainstSidePlane(
    ClippedPolygon& polygon,
    const glm::dvec3& faceCenter,
    const glm::dvec3& planeNormal,
    double limit) noexcept {
    if (polygon.count == 0) return;

    ClippedPolygon output{};
    glm::dvec3 previous = polygon.points[polygon.count - 1];
    double previousDistance = glm::dot(previous - faceCenter, planeNormal) - limit;
    bool previousInside = previousDistance <= kContactTolerance;

    for (std::size_t i = 0; i < polygon.count; ++i) {
        const glm::dvec3 current = polygon.points[i];
        const double currentDistance = glm::dot(current - faceCenter, planeNormal) - limit;
        const bool currentInside = currentDistance <= kContactTolerance;
        if (currentInside != previousInside) {
            const double denominator = previousDistance - currentDistance;
            if (std::abs(denominator) > kEpsilon && output.count < output.points.size()) {
                const double t = std::clamp(previousDistance / denominator, 0.0, 1.0);
                output.points[output.count++] = previous + (current - previous) * t;
            }
        }
        if (currentInside && output.count < output.points.size()) {
            output.points[output.count++] = current;
        }
        previous = current;
        previousDistance = currentDistance;
        previousInside = currentInside;
    }
    polygon = output;
}

void buildBoxFaceContacts(
    const CollisionShape& reference,
    const ShapePose& referencePose,
    int referenceAxisIndex,
    const CollisionShape& incident,
    const ShapePose& incidentPose,
    const glm::dvec3& referenceOutwardNormal,
    const glm::dvec3& manifoldNormalAtoB,
    std::uint32_t featurePrefix,
    ContactManifold& manifold) noexcept {
    const auto refAxes = boxAxes(referencePose);
    const auto incAxes = boxAxes(incidentPose);
    const glm::dvec3 refExtents = glm::max(absVector(reference.halfExtents), glm::dvec3{1.0e-9});
    const glm::dvec3 incExtents = glm::max(absVector(incident.halfExtents), glm::dvec3{1.0e-9});

    const int refTangentIndex0 = (referenceAxisIndex + 1) % 3;
    const int refTangentIndex1 = (referenceAxisIndex + 2) % 3;
    const glm::dvec3 refTangent0 = refAxes[refTangentIndex0];
    const glm::dvec3 refTangent1 = refAxes[refTangentIndex1];
    const double refTangentExtent0 = component(refExtents, refTangentIndex0);
    const double refTangentExtent1 = component(refExtents, refTangentIndex1);
    const glm::dvec3 refFaceCenter = referencePose.position
        + referenceOutwardNormal * component(refExtents, referenceAxisIndex);

    int incidentAxisIndex = 0;
    double bestAlignment = std::abs(glm::dot(incAxes[0], referenceOutwardNormal));
    for (int axis = 1; axis < 3; ++axis) {
        const double alignment = std::abs(glm::dot(incAxes[axis], referenceOutwardNormal));
        if (alignment > bestAlignment) {
            bestAlignment = alignment;
            incidentAxisIndex = axis;
        }
    }

    const double incidentFaceSign = glm::dot(incAxes[incidentAxisIndex], referenceOutwardNormal) > 0.0 ? -1.0 : 1.0;
    const glm::dvec3 incidentFaceCenter = incidentPose.position
        + incAxes[incidentAxisIndex] * (incidentFaceSign * component(incExtents, incidentAxisIndex));
    const int incidentTangentIndex0 = (incidentAxisIndex + 1) % 3;
    const int incidentTangentIndex1 = (incidentAxisIndex + 2) % 3;
    const glm::dvec3 incidentTangent0 = incAxes[incidentTangentIndex0]
        * component(incExtents, incidentTangentIndex0);
    const glm::dvec3 incidentTangent1 = incAxes[incidentTangentIndex1]
        * component(incExtents, incidentTangentIndex1);

    ClippedPolygon polygon{};
    polygon.count = 4;
    polygon.points[0] = incidentFaceCenter + incidentTangent0 + incidentTangent1;
    polygon.points[1] = incidentFaceCenter - incidentTangent0 + incidentTangent1;
    polygon.points[2] = incidentFaceCenter - incidentTangent0 - incidentTangent1;
    polygon.points[3] = incidentFaceCenter + incidentTangent0 - incidentTangent1;

    clipPolygonAgainstSidePlane(polygon, refFaceCenter, refTangent0, refTangentExtent0);
    clipPolygonAgainstSidePlane(polygon, refFaceCenter, -refTangent0, refTangentExtent0);
    clipPolygonAgainstSidePlane(polygon, refFaceCenter, refTangent1, refTangentExtent1);
    clipPolygonAgainstSidePlane(polygon, refFaceCenter, -refTangent1, refTangentExtent1);

    manifold.normal = safeNormalize(manifoldNormalAtoB);
    manifold.pointCount = 0;
    for (std::size_t i = 0; i < polygon.count && manifold.pointCount < manifold.points.size(); ++i) {
        const glm::dvec3 incidentPoint = polygon.points[i];
        const double separation = glm::dot(incidentPoint - refFaceCenter, referenceOutwardNormal);
        if (separation > kContactTolerance) continue;
        const double penetration = std::max(0.0, -separation);
        const glm::dvec3 referencePoint = incidentPoint - referenceOutwardNormal * separation;
        const glm::dvec3 contactPoint = 0.5 * (incidentPoint + referencePoint);
        const std::uint32_t featureId = featurePrefix
            | (static_cast<std::uint32_t>(referenceAxisIndex & 0x3) << 8U)
            | (static_cast<std::uint32_t>(incidentAxisIndex & 0x3) << 4U)
            | static_cast<std::uint32_t>(i & 0xFU);
        manifold.points[manifold.pointCount++] = ContactPoint{contactPoint, penetration, featureId};
    }
}

[[nodiscard]] bool boxBox(
    const CollisionShape& a,
    const ShapePose& poseA,
    const CollisionShape& b,
    const ShapePose& poseB,
    ContactManifold& manifold) noexcept {
    const glm::dvec3 extentsA = glm::max(absVector(a.halfExtents), glm::dvec3{1.0e-9});
    const glm::dvec3 extentsB = glm::max(absVector(b.halfExtents), glm::dvec3{1.0e-9});
    const auto axesA = boxAxes(poseA);
    const auto axesB = boxAxes(poseB);

    double rotation[3][3]{};
    double absRotation[3][3]{};
    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 3; ++j) {
            rotation[i][j] = glm::dot(axesA[i], axesB[j]);
            absRotation[i][j] = std::abs(rotation[i][j]) + kSatEpsilon;
        }
    }

    const glm::dvec3 centerDelta = poseB.position - poseA.position;
    const double t[3]{
        glm::dot(centerDelta, axesA[0]),
        glm::dot(centerDelta, axesA[1]),
        glm::dot(centerDelta, axesA[2]),
    };

    SatResult sat{};
    for (int i = 0; i < 3; ++i) {
        const double rb = extentsB.x * absRotation[i][0]
            + extentsB.y * absRotation[i][1]
            + extentsB.z * absRotation[i][2];
        const double overlap = component(extentsA, i) + rb - std::abs(t[i]);
        if (!updateSatResult(sat, overlap, axesA[i], centerDelta, SatAxisKind::FaceA, i, -1)) return false;
    }

    for (int j = 0; j < 3; ++j) {
        const double signedDistance = t[0] * rotation[0][j]
            + t[1] * rotation[1][j]
            + t[2] * rotation[2][j];
        const double ra = extentsA.x * absRotation[0][j]
            + extentsA.y * absRotation[1][j]
            + extentsA.z * absRotation[2][j];
        const double overlap = ra + component(extentsB, j) - std::abs(signedDistance);
        if (!updateSatResult(sat, overlap, axesB[j], centerDelta, SatAxisKind::FaceB, -1, j)) return false;
    }

    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 3; ++j) {
            const glm::dvec3 crossAxis = glm::cross(axesA[i], axesB[j]);
            const double axisLength = glm::length(crossAxis);
            if (axisLength <= 1.0e-8) continue;
            const int i1 = (i + 1) % 3;
            const int i2 = (i + 2) % 3;
            const int j1 = (j + 1) % 3;
            const int j2 = (j + 2) % 3;
            const double ra = component(extentsA, i1) * absRotation[i2][j]
                + component(extentsA, i2) * absRotation[i1][j];
            const double rb = component(extentsB, j1) * absRotation[i][j2]
                + component(extentsB, j2) * absRotation[i][j1];
            const double signedDistance = t[i2] * rotation[i1][j] - t[i1] * rotation[i2][j];
            const double overlapUnnormalized = ra + rb - std::abs(signedDistance);
            if (overlapUnnormalized < 0.0) return false;
            const double overlap = overlapUnnormalized / axisLength;
            if (!updateSatResult(sat, overlap, crossAxis, centerDelta, SatAxisKind::EdgeEdge, i, j)) return false;
        }
    }

    if (!std::isfinite(sat.overlap)) return false;
    if (sat.kind == SatAxisKind::FaceA) {
        buildBoxFaceContacts(a, poseA, sat.axisA, b, poseB, sat.normal, sat.normal, 0x10000U, manifold);
    } else if (sat.kind == SatAxisKind::FaceB) {
        buildBoxFaceContacts(b, poseB, sat.axisB, a, poseA, -sat.normal, sat.normal, 0x20000U, manifold);
    } else {
        const glm::dvec3 pointA = supportPoint(a, poseA, sat.normal);
        const glm::dvec3 pointB = supportPoint(b, poseB, -sat.normal);
        setSingleContact(
            manifold,
            sat.normal,
            0.5 * (pointA + pointB),
            sat.overlap,
            0x30000U | (static_cast<std::uint32_t>(sat.axisA & 0x3) << 4U)
                | static_cast<std::uint32_t>(sat.axisB & 0x3));
    }

    if (manifold.empty()) {
        const glm::dvec3 pointA = supportPoint(a, poseA, sat.normal);
        const glm::dvec3 pointB = supportPoint(b, poseB, -sat.normal);
        setSingleContact(manifold, sat.normal, 0.5 * (pointA + pointB), sat.overlap, 0x3FFFFU);
    }
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

double collisionBoundingRadius(const CollisionShape& shape) noexcept {
    switch (shape.type) {
    case CollisionShapeType::Sphere:
        return std::max(0.0, shape.radius);
    case CollisionShapeType::Box:
        return glm::length(glm::max(absVector(shape.halfExtents), glm::dvec3{0.0}));
    case CollisionShapeType::Capsule:
        return std::max(0.0, shape.radius) + std::max(0.0, shape.halfHeight);
    }
    return 0.0;
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
    const glm::dquat orientation = glm::normalize(pose.orientation);
    switch (shape.type) {
    case CollisionShapeType::Sphere:
        return pose.position + worldDirection * std::max(0.0, shape.radius);
    case CollisionShapeType::Box: {
        const glm::dquat inverseRotation = glm::conjugate(orientation);
        const glm::dvec3 localDirection = inverseRotation * worldDirection;
        const glm::dvec3 extents = glm::max(absVector(shape.halfExtents), glm::dvec3{0.0});
        const glm::dvec3 localPoint{
            localDirection.x >= 0.0 ? extents.x : -extents.x,
            localDirection.y >= 0.0 ? extents.y : -extents.y,
            localDirection.z >= 0.0 ? extents.z : -extents.z,
        };
        return pose.position + orientation * localPoint;
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

    // Remaining support-mapped convex pairs share one general GJK + EPA path.
    // At v5 this principally activates Box/Capsule in production; future convex
    // hull types plug into the same supportPoint() contract rather than adding
    // pair-specific approximations.
    return collideConvexGjkEpa(a, poseA, b, poseB, manifold);
}

} // namespace vf
