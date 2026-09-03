#include "vf/physics/GjkEpa.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <utility>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kDirectionEpsilon = 1.0e-18;
constexpr double kGjkSeparationTolerance = 1.0e-10;
constexpr double kEpaTolerance = 1.0e-6;
constexpr double kEpaVisibleTolerance = 1.0e-9;
constexpr std::uint32_t kMaxGjkIterations = 32U;
constexpr std::uint32_t kMaxEpaIterations = 64U;
constexpr std::size_t kMaxEpaVertices = 64U;
constexpr std::size_t kMaxEpaFaces = 128U;
constexpr std::size_t kMaxBoundaryEdges = 192U;
constexpr std::uint32_t kGjkEpaFeatureId = 0x40000000U;

struct SupportVertex {
    glm::dvec3 point{};
    glm::dvec3 pointA{};
    glm::dvec3 pointB{};
};

struct Simplex {
    std::array<SupportVertex, 4> vertices{};
    std::size_t count{};

    void pushFront(const SupportVertex& vertex) noexcept {
        const std::size_t limit = std::min<std::size_t>(count, vertices.size() - 1U);
        for (std::size_t i = limit; i > 0U; --i) vertices[i] = vertices[i - 1U];
        vertices[0] = vertex;
        count = std::min<std::size_t>(count + 1U, vertices.size());
    }
};

struct EpaFace {
    std::uint16_t a{};
    std::uint16_t b{};
    std::uint16_t c{};
    glm::dvec3 normal{1.0, 0.0, 0.0};
    double distance{};
};

struct Edge {
    std::uint16_t a{};
    std::uint16_t b{};
};

[[nodiscard]] double lengthSquared(const glm::dvec3& value) noexcept {
    return glm::dot(value, value);
}

[[nodiscard]] bool sameDirection(const glm::dvec3& a, const glm::dvec3& b) noexcept {
    return glm::dot(a, b) > 0.0;
}

[[nodiscard]] glm::dvec3 orthogonalDirection(const glm::dvec3& value) noexcept {
    const glm::dvec3 absValue{std::abs(value.x), std::abs(value.y), std::abs(value.z)};
    glm::dvec3 basis{1.0, 0.0, 0.0};
    if (absValue.y <= absValue.x && absValue.y <= absValue.z) {
        basis = {0.0, 1.0, 0.0};
    } else if (absValue.z <= absValue.x && absValue.z <= absValue.y) {
        basis = {0.0, 0.0, 1.0};
    }
    glm::dvec3 result = glm::cross(value, basis);
    if (lengthSquared(result) <= kDirectionEpsilon) result = glm::cross(value, glm::dvec3{0.0, 1.0, 0.0});
    if (lengthSquared(result) <= kDirectionEpsilon) result = {1.0, 0.0, 0.0};
    return result;
}

[[nodiscard]] glm::dvec3 tripleCross(
    const glm::dvec3& a,
    const glm::dvec3& b,
    const glm::dvec3& c) noexcept {
    return glm::cross(glm::cross(a, b), c);
}

[[nodiscard]] SupportVertex supportMinkowski(
    const CollisionShape& a,
    const ShapePose& poseA,
    const CollisionShape& b,
    const ShapePose& poseB,
    const glm::dvec3& direction) noexcept {
    const glm::dvec3 pointA = supportPoint(a, poseA, direction);
    const glm::dvec3 pointB = supportPoint(b, poseB, -direction);
    return {pointA - pointB, pointA, pointB};
}

void keepPoint(Simplex& simplex) noexcept {
    simplex.count = 1U;
}

void keepLine(Simplex& simplex, std::size_t secondIndex) noexcept {
    if (secondIndex != 1U) simplex.vertices[1] = simplex.vertices[secondIndex];
    simplex.count = 2U;
}

void keepTriangle(Simplex& simplex, std::size_t secondIndex, std::size_t thirdIndex) noexcept {
    const SupportVertex second = simplex.vertices[secondIndex];
    const SupportVertex third = simplex.vertices[thirdIndex];
    simplex.vertices[1] = second;
    simplex.vertices[2] = third;
    simplex.count = 3U;
}

void handleLine(Simplex& simplex, glm::dvec3& direction) noexcept {
    const glm::dvec3 a = simplex.vertices[0].point;
    const glm::dvec3 b = simplex.vertices[1].point;
    const glm::dvec3 ab = b - a;
    const glm::dvec3 ao = -a;

    if (!sameDirection(ab, ao)) {
        keepPoint(simplex);
        direction = ao;
        return;
    }

    direction = tripleCross(ab, ao, ab);
    if (lengthSquared(direction) <= kDirectionEpsilon) direction = orthogonalDirection(ab);
}

void handleTriangle(Simplex& simplex, glm::dvec3& direction) noexcept {
    const glm::dvec3 a = simplex.vertices[0].point;
    const glm::dvec3 b = simplex.vertices[1].point;
    const glm::dvec3 c = simplex.vertices[2].point;
    const glm::dvec3 ab = b - a;
    const glm::dvec3 ac = c - a;
    const glm::dvec3 ao = -a;
    const glm::dvec3 abc = glm::cross(ab, ac);

    const glm::dvec3 outsideAc = glm::cross(abc, ac);
    if (sameDirection(outsideAc, ao)) {
        if (sameDirection(ac, ao)) {
            keepLine(simplex, 2U);
            direction = tripleCross(ac, ao, ac);
            if (lengthSquared(direction) <= kDirectionEpsilon) direction = orthogonalDirection(ac);
            return;
        }

        keepLine(simplex, 1U);
        handleLine(simplex, direction);
        return;
    }

    const glm::dvec3 outsideAb = glm::cross(ab, abc);
    if (sameDirection(outsideAb, ao)) {
        keepLine(simplex, 1U);
        handleLine(simplex, direction);
        return;
    }

    if (sameDirection(abc, ao)) {
        direction = abc;
    } else {
        std::swap(simplex.vertices[1], simplex.vertices[2]);
        direction = -abc;
    }

    if (lengthSquared(direction) <= kDirectionEpsilon) direction = orthogonalDirection(ab);
}

[[nodiscard]] glm::dvec3 outwardFaceNormal(
    const glm::dvec3& a,
    const glm::dvec3& b,
    const glm::dvec3& c,
    const glm::dvec3& opposite) noexcept {
    glm::dvec3 normal = glm::cross(b - a, c - a);
    if (glm::dot(normal, opposite - a) > 0.0) normal = -normal;
    return normal;
}

[[nodiscard]] bool handleTetrahedron(Simplex& simplex, glm::dvec3& direction) noexcept {
    const glm::dvec3 a = simplex.vertices[0].point;
    const glm::dvec3 b = simplex.vertices[1].point;
    const glm::dvec3 c = simplex.vertices[2].point;
    const glm::dvec3 d = simplex.vertices[3].point;
    const glm::dvec3 ao = -a;

    const glm::dvec3 abc = outwardFaceNormal(a, b, c, d);
    if (sameDirection(abc, ao)) {
        keepTriangle(simplex, 1U, 2U);
        handleTriangle(simplex, direction);
        return false;
    }

    const glm::dvec3 acd = outwardFaceNormal(a, c, d, b);
    if (sameDirection(acd, ao)) {
        keepTriangle(simplex, 2U, 3U);
        handleTriangle(simplex, direction);
        return false;
    }

    const glm::dvec3 adb = outwardFaceNormal(a, d, b, c);
    if (sameDirection(adb, ao)) {
        keepTriangle(simplex, 3U, 1U);
        handleTriangle(simplex, direction);
        return false;
    }

    return true;
}

[[nodiscard]] bool updateSimplex(Simplex& simplex, glm::dvec3& direction) noexcept {
    switch (simplex.count) {
    case 1U:
        direction = -simplex.vertices[0].point;
        return false;
    case 2U:
        handleLine(simplex, direction);
        return false;
    case 3U:
        handleTriangle(simplex, direction);
        return false;
    case 4U:
        return handleTetrahedron(simplex, direction);
    default:
        return false;
    }
}

[[nodiscard]] bool runGjk(
    const CollisionShape& a,
    const ShapePose& poseA,
    const CollisionShape& b,
    const ShapePose& poseB,
    Simplex& simplex,
    GjkEpaDiagnostics& diagnostics) noexcept {
    glm::dvec3 direction = poseB.position - poseA.position;
    if (lengthSquared(direction) <= kDirectionEpsilon) direction = {1.0, 0.0, 0.0};

    simplex = {};
    simplex.pushFront(supportMinkowski(a, poseA, b, poseB, direction));
    direction = -simplex.vertices[0].point;
    if (lengthSquared(direction) <= kDirectionEpsilon) direction = {0.0, 1.0, 0.0};

    for (std::uint32_t iteration = 0U; iteration < kMaxGjkIterations; ++iteration) {
        diagnostics.gjkIterations = iteration + 1U;
        const SupportVertex next = supportMinkowski(a, poseA, b, poseB, direction);
        if (glm::dot(next.point, direction) <= kGjkSeparationTolerance) return false;

        simplex.pushFront(next);
        if (updateSimplex(simplex, direction)) {
            diagnostics.gjkIntersected = true;
            return true;
        }
        if (lengthSquared(direction) <= kDirectionEpsilon) direction = orthogonalDirection(simplex.vertices[0].point);
    }

    return false;
}

[[nodiscard]] bool makeFace(
    const std::array<SupportVertex, kMaxEpaVertices>& vertices,
    std::uint16_t a,
    std::uint16_t b,
    std::uint16_t c,
    EpaFace& face) noexcept {
    glm::dvec3 normal = glm::cross(vertices[b].point - vertices[a].point, vertices[c].point - vertices[a].point);
    const double normalLengthSquared = lengthSquared(normal);
    if (normalLengthSquared <= kDirectionEpsilon) return false;
    normal /= std::sqrt(normalLengthSquared);

    double distance = glm::dot(normal, vertices[a].point);
    if (distance < 0.0) {
        std::swap(b, c);
        normal = -normal;
        distance = -distance;
    }

    face = {a, b, c, normal, distance};
    return std::isfinite(distance);
}

void addBoundaryEdge(
    std::array<Edge, kMaxBoundaryEdges>& edges,
    std::size_t& edgeCount,
    std::uint16_t a,
    std::uint16_t b) noexcept {
    for (std::size_t i = 0U; i < edgeCount; ++i) {
        if (edges[i].a == b && edges[i].b == a) {
            edges[i] = edges[edgeCount - 1U];
            --edgeCount;
            return;
        }
    }
    if (edgeCount < edges.size()) edges[edgeCount++] = {a, b};
}

[[nodiscard]] std::array<double, 3> barycentricCoordinates(
    const glm::dvec3& point,
    const glm::dvec3& a,
    const glm::dvec3& b,
    const glm::dvec3& c) noexcept {
    const glm::dvec3 v0 = b - a;
    const glm::dvec3 v1 = c - a;
    const glm::dvec3 v2 = point - a;
    const double d00 = glm::dot(v0, v0);
    const double d01 = glm::dot(v0, v1);
    const double d11 = glm::dot(v1, v1);
    const double d20 = glm::dot(v2, v0);
    const double d21 = glm::dot(v2, v1);
    const double denominator = d00 * d11 - d01 * d01;
    if (std::abs(denominator) <= kDirectionEpsilon) return {1.0, 0.0, 0.0};

    double v = (d11 * d20 - d01 * d21) / denominator;
    double w = (d00 * d21 - d01 * d20) / denominator;
    double u = 1.0 - v - w;
    u = std::max(0.0, u);
    v = std::max(0.0, v);
    w = std::max(0.0, w);
    const double sum = u + v + w;
    if (sum <= kDirectionEpsilon) return {1.0, 0.0, 0.0};
    return {u / sum, v / sum, w / sum};
}

[[nodiscard]] bool emitContact(
    const std::array<SupportVertex, kMaxEpaVertices>& vertices,
    const EpaFace& face,
    ContactManifold& manifold) noexcept {
    if (!std::isfinite(face.distance) || face.distance < 0.0) return false;

    const glm::dvec3 closestPoint = face.normal * face.distance;
    const auto weights = barycentricCoordinates(
        closestPoint,
        vertices[face.a].point,
        vertices[face.b].point,
        vertices[face.c].point);

    const glm::dvec3 pointA = vertices[face.a].pointA * weights[0]
        + vertices[face.b].pointA * weights[1]
        + vertices[face.c].pointA * weights[2];
    const glm::dvec3 pointB = vertices[face.a].pointB * weights[0]
        + vertices[face.b].pointB * weights[1]
        + vertices[face.c].pointB * weights[2];

    manifold = {};
    manifold.normal = face.normal;
    manifold.pointCount = 1U;
    manifold.points[0] = ContactPoint{
        0.5 * (pointA + pointB),
        std::max(0.0, face.distance),
        kGjkEpaFeatureId,
    };
    return true;
}

[[nodiscard]] bool runEpa(
    const CollisionShape& a,
    const ShapePose& poseA,
    const CollisionShape& b,
    const ShapePose& poseB,
    const Simplex& simplex,
    ContactManifold& manifold,
    GjkEpaDiagnostics& diagnostics) noexcept {
    if (simplex.count != 4U) return false;

    std::array<SupportVertex, kMaxEpaVertices> vertices{};
    std::size_t vertexCount = 4U;
    for (std::size_t i = 0U; i < 4U; ++i) vertices[i] = simplex.vertices[i];

    std::array<EpaFace, kMaxEpaFaces> faces{};
    std::size_t faceCount = 0U;
    const std::array<std::array<std::uint16_t, 3>, 4> initialFaces{{
        {{0U, 1U, 2U}},
        {{0U, 3U, 1U}},
        {{0U, 2U, 3U}},
        {{1U, 3U, 2U}},
    }};
    for (const auto& indices : initialFaces) {
        EpaFace face{};
        if (makeFace(vertices, indices[0], indices[1], indices[2], face)) faces[faceCount++] = face;
    }
    if (faceCount < 4U) return false;

    EpaFace bestFace = faces[0];
    for (std::uint32_t iteration = 0U; iteration < kMaxEpaIterations; ++iteration) {
        diagnostics.epaIterations = iteration + 1U;

        std::size_t closestFaceIndex = 0U;
        double closestDistance = faces[0].distance;
        for (std::size_t i = 1U; i < faceCount; ++i) {
            if (faces[i].distance < closestDistance) {
                closestDistance = faces[i].distance;
                closestFaceIndex = i;
            }
        }
        bestFace = faces[closestFaceIndex];

        const SupportVertex next = supportMinkowski(a, poseA, b, poseB, bestFace.normal);
        const double supportDistance = glm::dot(next.point, bestFace.normal);
        if (!std::isfinite(supportDistance)) return false;

        if (supportDistance - bestFace.distance <= kEpaTolerance) {
            diagnostics.epaConverged = true;
            return emitContact(vertices, bestFace, manifold);
        }
        if (vertexCount >= vertices.size()) break;

        bool duplicateVertex = false;
        for (std::size_t i = 0U; i < vertexCount; ++i) {
            if (lengthSquared(vertices[i].point - next.point) <= kEpaTolerance * kEpaTolerance) {
                duplicateVertex = true;
                break;
            }
        }
        if (duplicateVertex) {
            diagnostics.epaConverged = true;
            return emitContact(vertices, bestFace, manifold);
        }

        const std::uint16_t newVertexIndex = static_cast<std::uint16_t>(vertexCount);
        vertices[vertexCount++] = next;

        std::array<Edge, kMaxBoundaryEdges> boundaryEdges{};
        std::size_t boundaryEdgeCount = 0U;
        std::array<EpaFace, kMaxEpaFaces> keptFaces{};
        std::size_t keptFaceCount = 0U;

        for (std::size_t i = 0U; i < faceCount; ++i) {
            const EpaFace& face = faces[i];
            const double visibility = glm::dot(
                face.normal,
                next.point - vertices[face.a].point);
            if (visibility > kEpaVisibleTolerance) {
                addBoundaryEdge(boundaryEdges, boundaryEdgeCount, face.a, face.b);
                addBoundaryEdge(boundaryEdges, boundaryEdgeCount, face.b, face.c);
                addBoundaryEdge(boundaryEdges, boundaryEdgeCount, face.c, face.a);
            } else if (keptFaceCount < keptFaces.size()) {
                keptFaces[keptFaceCount++] = face;
            }
        }

        if (boundaryEdgeCount == 0U) {
            diagnostics.epaConverged = true;
            return emitContact(vertices, bestFace, manifold);
        }

        faces = keptFaces;
        faceCount = keptFaceCount;
        for (std::size_t i = 0U; i < boundaryEdgeCount && faceCount < faces.size(); ++i) {
            EpaFace newFace{};
            if (makeFace(vertices, boundaryEdges[i].a, boundaryEdges[i].b, newVertexIndex, newFace)) {
                faces[faceCount++] = newFace;
            }
        }
        if (faceCount == 0U) return false;
    }

    // If the iteration/vertex budget is exhausted, keep the collision rather than
    // tunnelling through the pair. Diagnostics preserve the fact that EPA did not
    // formally converge so tests and profiling can catch pathological shapes.
    return emitContact(vertices, bestFace, manifold);
}

} // namespace

bool collideConvexGjkEpa(
    const CollisionShape& a,
    const ShapePose& poseA,
    const CollisionShape& b,
    const ShapePose& poseB,
    ContactManifold& manifold,
    GjkEpaDiagnostics* diagnostics) noexcept {
    manifold = {};
    GjkEpaDiagnostics localDiagnostics{};

    Simplex simplex{};
    if (!runGjk(a, poseA, b, poseB, simplex, localDiagnostics)) {
        if (diagnostics) *diagnostics = localDiagnostics;
        return false;
    }

    // The Minkowski difference is constructed as A - B. EPA orients the closest
    // polytope face outward from the origin, which directly yields the engine's
    // A -> B penetration normal. Do not re-orient using pose origins: arbitrary
    // convex geometry can be offset from its pose origin.
    const bool hit = runEpa(a, poseA, b, poseB, simplex, manifold, localDiagnostics);
    if (diagnostics) *diagnostics = localDiagnostics;
    return hit;
}

} // namespace vf
