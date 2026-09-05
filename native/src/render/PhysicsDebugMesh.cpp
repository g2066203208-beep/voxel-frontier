#include "vf/render/PhysicsDebugMesh.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-18) return fallback;
    return value / std::sqrt(lengthSquared);
}

void appendQuad(
    PlanetMesh& mesh,
    const std::array<glm::dvec3, 4>& positions,
    const glm::dvec3& normal,
    const glm::vec3& color,
    const glm::vec4& material) {
    const auto base = static_cast<std::uint32_t>(mesh.vertices.size());
    const glm::vec3 n = glm::vec3(safeNormalize(normal));
    for (const auto& position : positions) {
        PlanetVertex vertex{};
        vertex.position = glm::vec3(position);
        vertex.normal = n;
        vertex.color = color;
        vertex.material = material;
        mesh.vertices.push_back(vertex);
    }
    mesh.indices.insert(mesh.indices.end(), {
        base + 0U, base + 1U, base + 2U,
        base + 0U, base + 2U, base + 3U,
    });
}

void appendBasisBox(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    const glm::dvec3& xAxis,
    const glm::dvec3& yAxis,
    const glm::dvec3& zAxis,
    const glm::dvec3& halfExtents,
    const glm::vec3& color,
    const glm::vec4& material) {
    const glm::dvec3 x = xAxis * halfExtents.x;
    const glm::dvec3 y = yAxis * halfExtents.y;
    const glm::dvec3 z = zAxis * halfExtents.z;

    appendQuad(mesh, {center + x - y - z, center + x + y - z, center + x + y + z, center + x - y + z}, xAxis, color, material);
    appendQuad(mesh, {center - x - y + z, center - x + y + z, center - x + y - z, center - x - y - z}, -xAxis, color, material);
    appendQuad(mesh, {center - x + y - z, center - x + y + z, center + x + y + z, center + x + y - z}, yAxis, color, material);
    appendQuad(mesh, {center - x - y + z, center - x - y - z, center + x - y - z, center + x - y + z}, -yAxis, color, material);
    appendQuad(mesh, {center + x - y + z, center + x + y + z, center - x + y + z, center - x - y + z}, zAxis, color, material);
    appendQuad(mesh, {center - x - y - z, center - x + y - z, center + x + y - z, center + x - y - z}, -zAxis, color, material);
}

} // namespace

void appendDebugSphere(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double radius,
    const glm::vec3& color,
    unsigned rings,
    unsigned segments,
    glm::vec4 material) {
    radius = std::max(radius, 0.001);
    rings = std::max(rings, 3U);
    segments = std::max(segments, 6U);
    const auto base = static_cast<std::uint32_t>(mesh.vertices.size());

    for (unsigned ring = 0; ring <= rings; ++ring) {
        const double v = static_cast<double>(ring) / static_cast<double>(rings);
        const double latitude = -0.5 * kPi + v * kPi;
        const double y = std::sin(latitude);
        const double radial = std::cos(latitude);
        for (unsigned segment = 0; segment <= segments; ++segment) {
            const double u = static_cast<double>(segment) / static_cast<double>(segments);
            const double longitude = u * 2.0 * kPi;
            const glm::dvec3 normal{
                radial * std::cos(longitude),
                y,
                radial * std::sin(longitude),
            };
            PlanetVertex vertex{};
            vertex.position = glm::vec3(center + normal * radius);
            vertex.normal = glm::vec3(normal);
            vertex.color = color;
            vertex.material = material;
            mesh.vertices.push_back(vertex);
        }
    }

    const std::uint32_t stride = segments + 1U;
    for (unsigned ring = 0; ring < rings; ++ring) {
        for (unsigned segment = 0; segment < segments; ++segment) {
            const std::uint32_t a = base + ring * stride + segment;
            const std::uint32_t b = a + stride;
            mesh.indices.insert(mesh.indices.end(), {
                a, b, a + 1U,
                a + 1U, b, b + 1U,
            });
        }
    }
}

void appendDebugBox(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    const glm::dquat& orientation,
    const glm::dvec3& halfExtents,
    const glm::vec3& color,
    glm::vec4 material) {
    const glm::dquat q = glm::normalize(orientation);
    appendBasisBox(
        mesh,
        center,
        safeNormalize(q * glm::dvec3{1.0, 0.0, 0.0}),
        safeNormalize(q * glm::dvec3{0.0, 1.0, 0.0}),
        safeNormalize(q * glm::dvec3{0.0, 0.0, 1.0}),
        glm::max(halfExtents, glm::dvec3{0.001}),
        color,
        material);
}

void appendDebugRod(
    PlanetMesh& mesh,
    const glm::dvec3& a,
    const glm::dvec3& b,
    double halfThickness,
    const glm::vec3& color,
    glm::vec4 material) {
    const glm::dvec3 delta = b - a;
    const double length = glm::length(delta);
    if (length <= 1.0e-8) {
        appendDebugSphere(mesh, a, std::max(halfThickness, 0.01), color, 4U, 8U, material);
        return;
    }

    const glm::dvec3 xAxis = delta / length;
    const glm::dvec3 reference = std::abs(xAxis.y) < 0.9
        ? glm::dvec3{0.0, 1.0, 0.0}
        : glm::dvec3{0.0, 0.0, 1.0};
    const glm::dvec3 zAxis = safeNormalize(glm::cross(xAxis, reference), {0.0, 0.0, 1.0});
    const glm::dvec3 yAxis = safeNormalize(glm::cross(zAxis, xAxis), {0.0, 1.0, 0.0});
    const glm::dvec3 center = 0.5 * (a + b);
    halfThickness = std::max(halfThickness, 0.002);
    appendBasisBox(
        mesh,
        center,
        xAxis,
        yAxis,
        zAxis,
        {0.5 * length, halfThickness, halfThickness},
        color,
        material);
}

void appendDebugDisc(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    const glm::dvec3& normalInput,
    double radiusX,
    double radiusY,
    const glm::vec3& color,
    unsigned segments,
    glm::vec4 material) {
    const glm::dvec3 normal = safeNormalize(normalInput);
    const glm::dvec3 reference = std::abs(normal.y) < 0.92
        ? glm::dvec3{0.0, 1.0, 0.0}
        : glm::dvec3{1.0, 0.0, 0.0};
    const glm::dvec3 xAxis = safeNormalize(glm::cross(reference, normal), {1.0, 0.0, 0.0});
    const glm::dvec3 yAxis = safeNormalize(glm::cross(normal, xAxis), {0.0, 0.0, 1.0});
    radiusX = std::max(radiusX, 0.01);
    radiusY = std::max(radiusY, 0.01);
    segments = std::max(segments, 8U);

    const std::uint32_t base = static_cast<std::uint32_t>(mesh.vertices.size());
    PlanetVertex centerVertex{};
    centerVertex.position = glm::vec3(center);
    centerVertex.normal = glm::vec3(normal);
    centerVertex.color = color;
    centerVertex.material = material;
    mesh.vertices.push_back(centerVertex);

    for (unsigned i = 0; i <= segments; ++i) {
        const double angle = 2.0 * kPi * static_cast<double>(i) / static_cast<double>(segments);
        PlanetVertex vertex = centerVertex;
        vertex.position = glm::vec3(
            center + xAxis * (std::cos(angle) * radiusX) + yAxis * (std::sin(angle) * radiusY));
        mesh.vertices.push_back(vertex);
    }

    for (unsigned i = 0; i < segments; ++i) {
        mesh.indices.insert(mesh.indices.end(), {base, base + 1U + i, base + 2U + i});
    }
}

} // namespace vf
