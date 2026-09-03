#include "vf/render/PhysicsDebugMesh.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;

void appendQuad(
    PlanetMesh& mesh,
    const std::array<glm::dvec3, 4>& positions,
    const glm::dvec3& normal,
    const glm::vec3& color) {
    const auto base = static_cast<std::uint32_t>(mesh.vertices.size());
    const glm::vec3 n = glm::vec3(glm::normalize(normal));
    for (const auto& position : positions) {
        mesh.vertices.push_back({glm::vec3(position), n, color});
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
    const glm::vec3& color) {
    const glm::dvec3 x = xAxis * halfExtents.x;
    const glm::dvec3 y = yAxis * halfExtents.y;
    const glm::dvec3 z = zAxis * halfExtents.z;

    appendQuad(mesh, {center + x - y - z, center + x + y - z, center + x + y + z, center + x - y + z}, xAxis, color);
    appendQuad(mesh, {center - x - y + z, center - x + y + z, center - x + y - z, center - x - y - z}, -xAxis, color);
    appendQuad(mesh, {center - x + y - z, center - x + y + z, center + x + y + z, center + x + y - z}, yAxis, color);
    appendQuad(mesh, {center - x - y + z, center - x - y - z, center + x - y - z, center + x - y + z}, -yAxis, color);
    appendQuad(mesh, {center + x - y + z, center + x + y + z, center - x + y + z, center - x - y + z}, zAxis, color);
    appendQuad(mesh, {center - x - y - z, center - x + y - z, center + x + y - z, center + x - y - z}, -zAxis, color);
}

} // namespace

void appendDebugSphere(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double radius,
    const glm::vec3& color,
    unsigned rings,
    unsigned segments) {
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
            mesh.vertices.push_back({
                glm::vec3(center + normal * radius),
                glm::vec3(normal),
                color,
            });
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
    const glm::vec3& color) {
    const glm::dquat q = glm::normalize(orientation);
    appendBasisBox(
        mesh,
        center,
        glm::normalize(q * glm::dvec3{1.0, 0.0, 0.0}),
        glm::normalize(q * glm::dvec3{0.0, 1.0, 0.0}),
        glm::normalize(q * glm::dvec3{0.0, 0.0, 1.0}),
        glm::max(halfExtents, glm::dvec3{0.001}),
        color);
}

void appendDebugRod(
    PlanetMesh& mesh,
    const glm::dvec3& a,
    const glm::dvec3& b,
    double halfThickness,
    const glm::vec3& color) {
    const glm::dvec3 delta = b - a;
    const double length = glm::length(delta);
    if (length <= 1.0e-8) {
        appendDebugSphere(mesh, a, std::max(halfThickness, 0.01), color, 4U, 8U);
        return;
    }

    const glm::dvec3 xAxis = delta / length;
    const glm::dvec3 reference = std::abs(xAxis.y) < 0.9
        ? glm::dvec3{0.0, 1.0, 0.0}
        : glm::dvec3{0.0, 0.0, 1.0};
    const glm::dvec3 zAxis = glm::normalize(glm::cross(xAxis, reference));
    const glm::dvec3 yAxis = glm::normalize(glm::cross(zAxis, xAxis));
    const glm::dvec3 center = 0.5 * (a + b);
    halfThickness = std::max(halfThickness, 0.002);
    appendBasisBox(
        mesh,
        center,
        xAxis,
        yAxis,
        zAxis,
        {0.5 * length, halfThickness, halfThickness},
        color);
}

} // namespace vf
