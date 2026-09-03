#include "vf/world/PlanetSurface.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>

#include <glm/geometric.hpp>

namespace vf {

namespace {

[[nodiscard]] double seedPhase(std::uint64_t seed, std::uint64_t channel) {
    std::uint64_t x = seed + 0x9E3779B97F4A7C15ULL * (channel + 1ULL);
    x ^= x >> 30U;
    x *= 0xBF58476D1CE4E5B9ULL;
    x ^= x >> 27U;
    x *= 0x94D049BB133111EBULL;
    x ^= x >> 31U;
    return static_cast<double>(x & 0xFFFFFFULL) / static_cast<double>(0xFFFFFFULL) * 6.283185307179586;
}

[[nodiscard]] glm::vec3 terrainColor(double normalizedHeight) {
    if (normalizedHeight < -0.28) return {0.34F, 0.45F, 0.30F};
    if (normalizedHeight < 0.18) return {0.24F, 0.56F, 0.24F};
    if (normalizedHeight < 0.52) return {0.42F, 0.40F, 0.30F};
    return {0.76F, 0.78F, 0.72F};
}

void appendFace(
    PlanetMesh& mesh,
    const PlanetDefinition* definition,
    const glm::dvec3& center,
    double radius,
    std::uint32_t face,
    std::uint32_t subdivisions,
    const glm::vec3* constantColor) {
    const std::uint32_t stride = subdivisions + 1U;
    const std::uint32_t baseVertex = static_cast<std::uint32_t>(mesh.vertices.size());

    mesh.vertices.reserve(mesh.vertices.size() + static_cast<std::size_t>(stride) * stride);
    mesh.indices.reserve(mesh.indices.size() + static_cast<std::size_t>(subdivisions) * subdivisions * 6U);

    for (std::uint32_t y = 0; y <= subdivisions; ++y) {
        const double v = -1.0 + 2.0 * static_cast<double>(y) / static_cast<double>(subdivisions);
        for (std::uint32_t x = 0; x <= subdivisions; ++x) {
            const double u = -1.0 + 2.0 * static_cast<double>(x) / static_cast<double>(subdivisions);
            const glm::dvec3 direction = cubeSphereDirection(face, u, v);
            const double elevation = definition ? planetHeight(*definition, direction) : 0.0;
            const glm::dvec3 world = center + direction * (radius + elevation);
            const double normalizedHeight = definition && definition->maxElevation > 0.0
                ? elevation / definition->maxElevation
                : 0.0;

            PlanetVertex vertex{};
            vertex.position = glm::vec3(world);
            vertex.normal = glm::vec3(direction);
            vertex.color = constantColor ? *constantColor : terrainColor(normalizedHeight);
            mesh.vertices.push_back(vertex);
        }
    }

    for (std::uint32_t y = 0; y < subdivisions; ++y) {
        for (std::uint32_t x = 0; x < subdivisions; ++x) {
            const std::uint32_t i0 = baseVertex + y * stride + x;
            const std::uint32_t i1 = i0 + 1U;
            const std::uint32_t i2 = i0 + stride;
            const std::uint32_t i3 = i2 + 1U;
            mesh.indices.insert(mesh.indices.end(), {i0, i2, i1, i1, i2, i3});
        }
    }
}

} // namespace

glm::dvec3 cubeSphereDirection(std::uint32_t face, double u, double v) {
    glm::dvec3 cube{};
    switch (face) {
    case 0: cube = {1.0, v, -u}; break;   // +X
    case 1: cube = {-1.0, v, u}; break;   // -X
    case 2: cube = {u, 1.0, -v}; break;   // +Y
    case 3: cube = {u, -1.0, v}; break;   // -Y
    case 4: cube = {u, v, 1.0}; break;    // +Z
    case 5: cube = {-u, v, -1.0}; break;  // -Z
    default: throw std::out_of_range("cubeSphereDirection face must be 0..5");
    }
    return glm::normalize(cube);
}

double planetHeight(const PlanetDefinition& definition, const glm::dvec3& directionInput) {
    const glm::dvec3 d = glm::normalize(directionInput);
    const double p0 = seedPhase(definition.seed, 0);
    const double p1 = seedPhase(definition.seed, 1);
    const double p2 = seedPhase(definition.seed, 2);
    const double p3 = seedPhase(definition.seed, 3);

    const double continental =
        std::sin(d.x * 3.7 + p0) * 0.38 +
        std::sin(d.y * 4.9 + d.z * 2.1 + p1) * 0.31 +
        std::cos(d.z * 5.3 - d.x * 1.7 + p2) * 0.22;
    const double ridges = 1.0 - std::abs(std::sin((d.x * 10.0 + d.y * 8.0 - d.z * 6.0) + p3));
    const double detail =
        std::sin(d.x * 21.0 + d.z * 17.0 + p1) *
        std::cos(d.y * 19.0 - d.x * 11.0 + p2) * 0.12;

    const double shape = std::clamp(continental + ridges * 0.28 + detail, -1.0, 1.0);
    return shape * definition.maxElevation;
}

double planetSurfaceRadius(const PlanetDefinition& definition, const glm::dvec3& direction) {
    return definition.radius + planetHeight(definition, direction);
}

PlanetMesh buildPlanetSurface(const PlanetDefinition& definition, std::uint32_t subdivisionsPerFace) {
    if (subdivisionsPerFace < 2U) throw std::invalid_argument("planet subdivisions must be >= 2");

    PlanetMesh mesh;
    for (std::uint32_t face = 0; face < 6U; ++face) {
        appendFace(mesh, &definition, glm::dvec3{0.0}, definition.radius, face, subdivisionsPerFace, nullptr);
    }
    return mesh;
}

void appendCelestialProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double radius,
    std::uint32_t subdivisionsPerFace,
    const glm::vec3& color) {
    if (subdivisionsPerFace < 2U) throw std::invalid_argument("proxy subdivisions must be >= 2");
    for (std::uint32_t face = 0; face < 6U; ++face) {
        appendFace(mesh, nullptr, center, radius, face, subdivisionsPerFace, &color);
    }
}

} // namespace vf
