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

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-18) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] glm::vec3 terrainColor(double normalizedHeight) {
    if (normalizedHeight < -0.30) return {0.16F, 0.23F, 0.14F};
    if (normalizedHeight < 0.08) return {0.19F, 0.39F, 0.16F};
    if (normalizedHeight < 0.38) return {0.30F, 0.34F, 0.20F};
    if (normalizedHeight < 0.67) return {0.37F, 0.35F, 0.31F};
    return {0.68F, 0.70F, 0.67F};
}

[[nodiscard]] glm::vec3 proxyColor(const glm::vec3& baseColor, const glm::dvec3& localDirection) {
    if (baseColor.x < 0.0F || baseColor.y < 0.0F || baseColor.z < 0.0F) return baseColor;

    const double bands = 0.5 + 0.5 * std::sin(localDirection.y * 17.0 + localDirection.x * 5.0);
    const double patches = 0.5 + 0.5 * std::sin(localDirection.x * 11.0 - localDirection.z * 13.0);
    const float scale = static_cast<float>(0.68 + 0.20 * bands + 0.12 * patches);
    return glm::clamp(baseColor * scale, glm::vec3{0.0F}, glm::vec3{1.0F});
}

[[nodiscard]] glm::dvec3 tangentAxis(const glm::dvec3& up) {
    const glm::dvec3 reference = std::abs(up.y) < 0.92
        ? glm::dvec3{0.0, 1.0, 0.0}
        : glm::dvec3{1.0, 0.0, 0.0};
    return safeNormalize(glm::cross(reference, up), {1.0, 0.0, 0.0});
}

void appendFace(
    PlanetMesh& mesh,
    const PlanetDefinition* definition,
    const glm::dvec3& center,
    const glm::dquat* orientation,
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
            const glm::dvec3 localDirection = cubeSphereDirection(face, u, v);
            const glm::dvec3 localNormal = definition
                ? planetSurfaceNormal(*definition, localDirection)
                : localDirection;
            const glm::dvec3 worldDirection = orientation
                ? safeNormalize((*orientation) * localDirection)
                : localDirection;
            const glm::dvec3 worldNormal = orientation
                ? safeNormalize((*orientation) * localNormal)
                : localNormal;
            const double elevation = definition ? planetHeight(*definition, localDirection) : 0.0;
            const glm::dvec3 world = center + worldDirection * (radius + elevation);
            const double normalizedHeight = definition && definition->maxElevation > 0.0
                ? elevation / definition->maxElevation
                : 0.0;

            PlanetVertex vertex{};
            vertex.position = glm::vec3(world);
            vertex.normal = glm::vec3(worldNormal);
            vertex.color = constantColor
                ? proxyColor(*constantColor, localDirection)
                : terrainColor(normalizedHeight);
            vertex.material = definition
                ? glm::vec4{0.0F, normalizedHeight > 0.55 ? 0.88F : 0.96F, 0.0F, 0.0F}
                : glm::vec4{0.0F, 0.72F, 0.0F, 0.0F};
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
    case 0: cube = {1.0, v, -u}; break;
    case 1: cube = {-1.0, v, u}; break;
    case 2: cube = {u, 1.0, -v}; break;
    case 3: cube = {u, -1.0, v}; break;
    case 4: cube = {u, v, 1.0}; break;
    case 5: cube = {-u, v, -1.0}; break;
    default: throw std::out_of_range("cubeSphereDirection face must be 0..5");
    }
    return glm::normalize(cube);
}

double planetHeight(const PlanetDefinition& definition, const glm::dvec3& directionInput) {
    const glm::dvec3 d = safeNormalize(directionInput);
    const double p0 = seedPhase(definition.seed, 0);
    const double p1 = seedPhase(definition.seed, 1);
    const double p2 = seedPhase(definition.seed, 2);
    const double p3 = seedPhase(definition.seed, 3);
    const double p4 = seedPhase(definition.seed, 4);
    const double p5 = seedPhase(definition.seed, 5);

    const double continental =
        std::sin(d.x * 3.7 + p0) * 0.31 +
        std::sin(d.y * 4.9 + d.z * 2.1 + p1) * 0.27 +
        std::cos(d.z * 5.3 - d.x * 1.7 + p2) * 0.19;
    const double ridges = 1.0 - std::abs(std::sin((d.x * 10.0 + d.y * 8.0 - d.z * 6.0) + p3));
    const double regional =
        std::sin(d.x * 260.0 + d.z * 190.0 + p4) *
        std::cos(d.y * 220.0 - d.x * 140.0 + p5) * 0.075;
    const double hills =
        std::sin(d.x * 1250.0 + d.y * 870.0 + p2) *
        std::cos(d.z * 980.0 - d.x * 640.0 + p1) * 0.035;
    const double localDetail =
        std::sin(d.x * 5200.0 + d.z * 4100.0 + p5) *
        std::cos(d.y * 4700.0 - d.x * 3600.0 + p4) * 0.012;

    const double shape = std::clamp(
        continental + ridges * 0.22 + regional + hills + localDetail,
        -1.0,
        1.0);
    return shape * definition.maxElevation;
}

double planetSurfaceRadius(const PlanetDefinition& definition, const glm::dvec3& direction) {
    return definition.radius + planetHeight(definition, direction);
}

glm::dvec3 planetSurfaceNormal(
    const PlanetDefinition& definition,
    const glm::dvec3& directionInput) {
    const glm::dvec3 d = safeNormalize(directionInput);
    const glm::dvec3 east = tangentAxis(d);
    const glm::dvec3 north = safeNormalize(glm::cross(d, east), {0.0, 0.0, 1.0});

    // About a two-metre baseline on large planets, but never so small that numerical noise wins.
    const double angularStep = std::clamp(2.0 / std::max(1.0, definition.radius), 1.0e-7, 2.0e-3);
    const glm::dvec3 dEast = safeNormalize(d + east * angularStep, d);
    const glm::dvec3 dNorth = safeNormalize(d + north * angularStep, d);

    const glm::dvec3 p0 = d * planetSurfaceRadius(definition, d);
    const glm::dvec3 pEast = dEast * planetSurfaceRadius(definition, dEast);
    const glm::dvec3 pNorth = dNorth * planetSurfaceRadius(definition, dNorth);
    glm::dvec3 normal = safeNormalize(glm::cross(pEast - p0, pNorth - p0), d);
    if (glm::dot(normal, d) < 0.0) normal = -normal;
    return normal;
}

PlanetMesh buildPlanetSurface(const PlanetDefinition& definition, std::uint32_t subdivisionsPerFace) {
    if (subdivisionsPerFace < 2U) throw std::invalid_argument("planet subdivisions must be >= 2");

    PlanetMesh mesh;
    for (std::uint32_t face = 0; face < 6U; ++face) {
        appendFace(mesh, &definition, glm::dvec3{0.0}, nullptr, definition.radius, face, subdivisionsPerFace, nullptr);
    }
    return mesh;
}

PlanetMesh buildPlanetSurfacePatch(
    const PlanetDefinition& definition,
    const glm::dvec3& centerDirectionInput,
    double halfExtentMeters,
    std::uint32_t resolution) {
    if (resolution < 2U) throw std::invalid_argument("planet patch resolution must be >= 2");
    halfExtentMeters = std::max(10.0, halfExtentMeters);

    const glm::dvec3 up = safeNormalize(centerDirectionInput);
    const glm::dvec3 east = tangentAxis(up);
    const glm::dvec3 north = safeNormalize(glm::cross(up, east), {0.0, 0.0, 1.0});
    const std::uint32_t stride = resolution + 1U;

    PlanetMesh mesh{};
    mesh.vertices.reserve(static_cast<std::size_t>(stride) * stride);
    mesh.indices.reserve(static_cast<std::size_t>(resolution) * resolution * 6U);

    for (std::uint32_t y = 0; y <= resolution; ++y) {
        const double fy = static_cast<double>(y) / static_cast<double>(resolution);
        const double northMeters = -halfExtentMeters + 2.0 * halfExtentMeters * fy;
        for (std::uint32_t x = 0; x <= resolution; ++x) {
            const double fx = static_cast<double>(x) / static_cast<double>(resolution);
            const double eastMeters = -halfExtentMeters + 2.0 * halfExtentMeters * fx;
            const glm::dvec3 direction = safeNormalize(
                up + east * (eastMeters / definition.radius) + north * (northMeters / definition.radius),
                up);
            const double elevation = planetHeight(definition, direction);
            const double normalizedHeight = definition.maxElevation > 0.0
                ? elevation / definition.maxElevation
                : 0.0;

            PlanetVertex vertex{};
            vertex.position = glm::vec3(direction * (definition.radius + elevation));
            vertex.normal = glm::vec3(planetSurfaceNormal(definition, direction));
            vertex.color = terrainColor(normalizedHeight);
            vertex.material = {0.0F, normalizedHeight > 0.55 ? 0.88F : 0.96F, 0.0F, 0.0F};
            mesh.vertices.push_back(vertex);
        }
    }

    for (std::uint32_t y = 0; y < resolution; ++y) {
        for (std::uint32_t x = 0; x < resolution; ++x) {
            const std::uint32_t i0 = y * stride + x;
            const std::uint32_t i1 = i0 + 1U;
            const std::uint32_t i2 = i0 + stride;
            const std::uint32_t i3 = i2 + 1U;
            mesh.indices.insert(mesh.indices.end(), {i0, i2, i1, i1, i2, i3});
        }
    }
    return mesh;
}

void appendCelestialProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double radius,
    std::uint32_t subdivisionsPerFace,
    const glm::vec3& color) {
    appendCelestialBodyProxy(mesh, center, glm::dquat{1.0, 0.0, 0.0, 0.0}, radius, subdivisionsPerFace, color);
}

void appendCelestialBodyProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    const glm::dquat& orientation,
    double radius,
    std::uint32_t subdivisionsPerFace,
    const glm::vec3& baseColor) {
    if (subdivisionsPerFace < 2U) throw std::invalid_argument("proxy subdivisions must be >= 2");
    const glm::dquat normalizedOrientation = glm::normalize(orientation);
    for (std::uint32_t face = 0; face < 6U; ++face) {
        appendFace(mesh, nullptr, center, &normalizedOrientation, radius, face, subdivisionsPerFace, &baseColor);
    }
}

void appendAtmosphereProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double outerRadius,
    std::uint32_t subdivisionsPerFace,
    const glm::vec3& scatteringColor,
    float opticalStrength) {
    if (subdivisionsPerFace < 2U) throw std::invalid_argument("atmosphere subdivisions must be >= 2");
    const glm::vec3 tint = glm::clamp(scatteringColor, glm::vec3{0.01F}, glm::vec3{1.0F});
    const float strength = std::clamp(opticalStrength, 0.02F, 1.0F);
    const glm::vec3 encoded = -(tint * strength);
    const glm::dquat identity{1.0, 0.0, 0.0, 0.0};
    const std::size_t firstVertex = mesh.vertices.size();
    for (std::uint32_t face = 0; face < 6U; ++face) {
        appendFace(mesh, nullptr, center, &identity, outerRadius, face, subdivisionsPerFace, &encoded);
    }
    for (std::size_t i = firstVertex; i < mesh.vertices.size(); ++i) {
        mesh.vertices[i].material = {0.0F, 1.0F, 0.0F, 0.0F};
    }
}

} // namespace vf
