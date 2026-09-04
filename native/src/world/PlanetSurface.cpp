#include "vf/world/PlanetSurface.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;

[[nodiscard]] double seedPhase(std::uint64_t seed, std::uint64_t channel) {
    std::uint64_t x = seed + 0x9E3779B97F4A7C15ULL * (channel + 1ULL);
    x ^= x >> 30U;
    x *= 0xBF58476D1CE4E5B9ULL;
    x ^= x >> 27U;
    x *= 0x94D049BB133111EBULL;
    x ^= x >> 31U;
    return static_cast<double>(x & 0xFFFFFFULL) / static_cast<double>(0xFFFFFFULL) * 2.0 * kPi;
}

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-18) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] double smooth01(double edge0, double edge1, double value) noexcept {
    if (edge1 <= edge0) return value >= edge1 ? 1.0 : 0.0;
    const double x = std::clamp((value - edge0) / (edge1 - edge0), 0.0, 1.0);
    return x * x * (3.0 - 2.0 * x);
}

[[nodiscard]] double resolvedOceanDepth(const PlanetDefinition& definition) noexcept {
    return std::max(0.0, definition.maxOceanDepthMeters > 0.0
        ? definition.maxOceanDepthMeters
        : definition.maxElevation);
}

[[nodiscard]] glm::dvec3 seededDirection(std::uint64_t seed, std::uint64_t channel) noexcept {
    const double longitude = seedPhase(seed, channel);
    const double z = std::sin(seedPhase(seed, channel + 37U));
    const double radial = std::sqrt(std::max(0.0, 1.0 - z * z));
    return {std::cos(longitude) * radial, z, std::sin(longitude) * radial};
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
    for (std::uint32_t y = 0; y <= subdivisions; ++y) {
        const double v = -1.0 + 2.0 * static_cast<double>(y) / static_cast<double>(subdivisions);
        for (std::uint32_t x = 0; x <= subdivisions; ++x) {
            const double u = -1.0 + 2.0 * static_cast<double>(x) / static_cast<double>(subdivisions);
            const glm::dvec3 localDirection = cubeSphereDirection(face, u, v);
            const PlanetTerrainSample terrain = definition ? samplePlanetTerrain(*definition, localDirection) : PlanetTerrainSample{};
            const glm::dvec3 localNormal = definition ? planetSurfaceNormal(*definition, localDirection) : localDirection;
            const glm::dvec3 worldDirection = orientation ? safeNormalize((*orientation) * localDirection) : localDirection;
            const glm::dvec3 worldNormal = orientation ? safeNormalize((*orientation) * localNormal) : localNormal;
            const double elevation = definition ? terrain.elevationMeters : 0.0;
            PlanetVertex vertex{};
            vertex.position = glm::vec3(center + worldDirection * (radius + elevation));
            vertex.normal = glm::vec3(worldNormal);
            vertex.color = constantColor ? proxyColor(*constantColor, localDirection) : planetTerrainColor(*definition, terrain);
            vertex.material = definition ? planetTerrainMaterial(*definition, terrain) : glm::vec4{0.0F, 0.72F, 0.0F, 0.0F};
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

void appendOceanFace(PlanetMesh& mesh, const glm::dvec3& center, double radius, std::uint32_t face, std::uint32_t subdivisions) {
    const std::uint32_t stride = subdivisions + 1U;
    const std::uint32_t baseVertex = static_cast<std::uint32_t>(mesh.vertices.size());
    for (std::uint32_t y = 0; y <= subdivisions; ++y) {
        const double v = -1.0 + 2.0 * static_cast<double>(y) / static_cast<double>(subdivisions);
        for (std::uint32_t x = 0; x <= subdivisions; ++x) {
            const double u = -1.0 + 2.0 * static_cast<double>(x) / static_cast<double>(subdivisions);
            const glm::dvec3 direction = cubeSphereDirection(face, u, v);
            PlanetVertex vertex{};
            vertex.position = glm::vec3(center + direction * radius);
            vertex.normal = glm::vec3(direction);
            vertex.color = {0.025F, 0.16F, 0.27F};
            vertex.material = {-1.0F, 0.075F, 0.78F, 0.0F};
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

PlanetTerrainSample samplePlanetTerrain(const PlanetDefinition& definition, const glm::dvec3& directionInput) {
    const glm::dvec3 d = safeNormalize(directionInput);
    const double p0 = seedPhase(definition.seed, 0);
    const double p1 = seedPhase(definition.seed, 1);
    const double p2 = seedPhase(definition.seed, 2);
    const double p3 = seedPhase(definition.seed, 3);
    const double p4 = seedPhase(definition.seed, 4);
    const double p5 = seedPhase(definition.seed, 5);
    const double p6 = seedPhase(definition.seed, 6);
    const double p7 = seedPhase(definition.seed, 7);
    const glm::dvec3 warp{
        std::sin(d.y * 5.1 + d.z * 3.7 + p4),
        std::sin(d.z * 4.3 - d.x * 3.1 + p5),
        std::sin(d.x * 4.7 + d.y * 3.3 + p6),
    };
    const glm::dvec3 w = safeNormalize(d + warp * 0.12, d);
    const double continentalRaw = std::sin(w.x * 2.15 + p0) * 0.42
        + std::sin(w.y * 2.75 + w.z * 1.40 + p1) * 0.31
        + std::cos(w.z * 2.35 - w.x * 1.55 + p2) * 0.25
        + std::sin((w.x + w.y - w.z) * 4.80 + p3) * 0.18;
    const double continentalness = std::clamp(continentalRaw / 1.16, -1.0, 1.0);
    const double landness = smooth01(0.08, 0.30, continentalness);
    const double oceanness = 1.0 - landness;
    const double maxLand = std::max(0.0, definition.maxElevation);
    const double maxOcean = resolvedOceanDepth(definition);
    const double deepOcean = smooth01(0.05, 0.72, -continentalness);
    const double shelf = smooth01(-0.08, 0.08, -continentalness);
    double elevation = -maxOcean * (0.08 + 0.58 * deepOcean + 0.10 * shelf) * oceanness;
    elevation += maxLand * (0.025 + 0.12 * std::pow(landness, 1.4)) * landness;

    const double ridgeLine = 1.0 - std::abs(std::sin(w.x * 7.3 + w.y * 5.9 - w.z * 6.5 + p4));
    const double ridgeDetail = 0.55 + 0.45 * (0.5 + 0.5 * std::sin(w.x * 31.0 - w.z * 27.0 + p1));
    const double mountain = std::pow(smooth01(0.68, 0.97, ridgeLine), 1.45) * landness * ridgeDetail;
    elevation += maxLand * 0.68 * mountain;

    const double plateauField = 0.5 + 0.5 * std::sin(w.x * 3.8 - w.z * 2.7 + p5)
        * std::cos(w.y * 3.2 + w.x * 1.1 + p2);
    const double plateau = smooth01(0.70, 0.92, plateauField) * landness * (1.0 - 0.55 * mountain);
    elevation += maxLand * 0.30 * plateau;

    const double trenchLine = 1.0 - std::abs(std::sin(w.x * 8.7 - w.y * 7.4 + w.z * 5.8 + p6));
    const double trench = std::pow(smooth01(0.84, 0.985, trenchLine), 1.8) * oceanness;
    elevation -= maxOcean * 0.42 * trench;

    double volcano = 0.0;
    for (std::uint64_t i = 0; i < 7U; ++i) {
        const glm::dvec3 hotspot = seededDirection(definition.seed, 20U + i * 3U);
        const double angularMask = smooth01(std::cos(0.080), std::cos(0.012), glm::dot(d, hotspot));
        volcano = std::max(volcano, angularMask * angularMask);
    }
    elevation += maxLand * 0.42 * volcano;

    const double riverLineA = 1.0 - std::abs(std::sin(w.x * 23.0 + w.y * 11.0 - w.z * 17.0 + p7));
    const double riverLineB = 1.0 - std::abs(std::sin(w.z * 19.0 - w.x * 13.0 + w.y * 7.0 + p3));
    const double riverLine = std::max(riverLineA, riverLineB);
    const double river = std::pow(smooth01(0.955, 0.998, riverLine), 1.5)
        * landness * (1.0 - mountain) * (1.0 - 0.45 * plateau);
    elevation -= maxLand * 0.055 * river;

    const double regional = std::sin(w.x * 210.0 + w.z * 170.0 + p4)
        * std::cos(w.y * 185.0 - w.x * 120.0 + p5);
    const double local = std::sin(w.x * 1150.0 + w.y * 790.0 + p2)
        * std::cos(w.z * 970.0 - w.x * 610.0 + p1);
    elevation += maxLand * (0.020 * regional + 0.008 * local) * (0.35 + 0.65 * landness);

    const double minElevation = definition.seaLevelElevationMeters - maxOcean;
    const double maxElevation = definition.seaLevelElevationMeters + maxLand;
    elevation = std::clamp(elevation + definition.seaLevelElevationMeters, minElevation, maxElevation);

    PlanetTerrainSample sample{};
    sample.elevationMeters = elevation;
    sample.continentalness = continentalness;
    sample.mountain = mountain;
    sample.plateau = plateau;
    sample.trench = trench;
    sample.volcano = volcano;
    sample.river = river;
    sample.oceanDepthMeters = std::max(0.0, definition.seaLevelElevationMeters - elevation);
    return sample;
}

double planetHeight(const PlanetDefinition& definition, const glm::dvec3& direction) {
    return samplePlanetTerrain(definition, direction).elevationMeters;
}

double planetSurfaceRadius(const PlanetDefinition& definition, const glm::dvec3& direction) {
    return definition.radius + planetHeight(definition, direction);
}

glm::vec3 planetTerrainColor(const PlanetDefinition& definition, const PlanetTerrainSample& sample) noexcept {
    if (sample.submerged(definition)) {
        const double depthScale = resolvedOceanDepth(definition) > 0.0
            ? std::clamp(sample.oceanDepthMeters / resolvedOceanDepth(definition), 0.0, 1.0) : 0.0;
        if (sample.trench > 0.55) return {0.075F, 0.080F, 0.095F};
        if (depthScale < 0.035) return {0.58F, 0.52F, 0.36F};
        if (depthScale < 0.22) return {0.30F, 0.34F, 0.28F};
        return {0.12F, 0.15F, 0.16F};
    }
    const double aboveSea = sample.elevationMeters - definition.seaLevelElevationMeters;
    if (aboveSea < 35.0) return {0.64F, 0.58F, 0.39F};
    if (sample.river > 0.55) return {0.16F, 0.32F, 0.15F};
    if (sample.volcano > 0.62) return {0.20F, 0.18F, 0.17F};
    if (sample.mountain > 0.55) return aboveSea > 4200.0 ? glm::vec3{0.78F, 0.80F, 0.79F} : glm::vec3{0.37F, 0.35F, 0.32F};
    if (sample.plateau > 0.55) return {0.45F, 0.37F, 0.25F};
    if (aboveSea > 3600.0) return {0.61F, 0.62F, 0.59F};
    if (aboveSea > 1600.0) return {0.35F, 0.36F, 0.25F};
    return {0.19F, 0.38F, 0.16F};
}

glm::vec4 planetTerrainMaterial(const PlanetDefinition& definition, const PlanetTerrainSample& sample) noexcept {
    if (sample.submerged(definition)) return {0.0F, 0.96F, 0.0F, 0.0F};
    if (sample.volcano > 0.62) return {0.0F, 0.92F, 0.0F, 0.0F};
    if (sample.mountain > 0.50) return {0.0F, 0.84F, 0.0F, 0.0F};
    return {0.0F, 0.94F, 0.0F, 0.0F};
}

glm::dvec3 planetSurfaceNormal(const PlanetDefinition& definition, const glm::dvec3& directionInput) {
    const glm::dvec3 d = safeNormalize(directionInput);
    const glm::dvec3 east = tangentAxis(d);
    const glm::dvec3 north = safeNormalize(glm::cross(d, east), {0.0, 0.0, 1.0});
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
    for (std::uint32_t face = 0; face < 6U; ++face)
        appendFace(mesh, &definition, glm::dvec3{0.0}, nullptr, definition.radius, face, subdivisionsPerFace, nullptr);
    return mesh;
}

PlanetMesh buildPlanetSurfacePatch(const PlanetDefinition& definition, const glm::dvec3& centerDirectionInput,
    double halfExtentMeters, std::uint32_t resolution) {
    if (resolution < 2U) throw std::invalid_argument("planet patch resolution must be >= 2");
    halfExtentMeters = std::max(10.0, halfExtentMeters);
    const glm::dvec3 up = safeNormalize(centerDirectionInput);
    const glm::dvec3 east = tangentAxis(up);
    const glm::dvec3 north = safeNormalize(glm::cross(up, east), {0.0, 0.0, 1.0});
    const std::uint32_t stride = resolution + 1U;
    PlanetMesh mesh{};
    for (std::uint32_t y = 0; y <= resolution; ++y) {
        const double fy = static_cast<double>(y) / static_cast<double>(resolution);
        const double northMeters = -halfExtentMeters + 2.0 * halfExtentMeters * fy;
        for (std::uint32_t x = 0; x <= resolution; ++x) {
            const double fx = static_cast<double>(x) / static_cast<double>(resolution);
            const double eastMeters = -halfExtentMeters + 2.0 * halfExtentMeters * fx;
            const glm::dvec3 direction = safeNormalize(up + east * (eastMeters / definition.radius) + north * (northMeters / definition.radius), up);
            const PlanetTerrainSample terrain = samplePlanetTerrain(definition, direction);
            PlanetVertex vertex{};
            vertex.position = glm::vec3(direction * (definition.radius + terrain.elevationMeters));
            vertex.normal = glm::vec3(planetSurfaceNormal(definition, direction));
            vertex.color = planetTerrainColor(definition, terrain);
            vertex.material = planetTerrainMaterial(definition, terrain);
            mesh.vertices.push_back(vertex);
        }
    }
    for (std::uint32_t y = 0; y < resolution; ++y) for (std::uint32_t x = 0; x < resolution; ++x) {
        const std::uint32_t i0 = y * stride + x;
        const std::uint32_t i1 = i0 + 1U;
        const std::uint32_t i2 = i0 + stride;
        const std::uint32_t i3 = i2 + 1U;
        mesh.indices.insert(mesh.indices.end(), {i0, i2, i1, i1, i2, i3});
    }
    return mesh;
}

PlanetMesh buildOceanSurfacePatch(const PlanetDefinition& definition, const glm::dvec3& centerDirectionInput,
    double halfExtentMeters, std::uint32_t resolution, double radialInsetMeters) {
    if (resolution < 2U) throw std::invalid_argument("ocean patch resolution must be >= 2");
    halfExtentMeters = std::max(10.0, halfExtentMeters);
    const glm::dvec3 up = safeNormalize(centerDirectionInput);
    const glm::dvec3 east = tangentAxis(up);
    const glm::dvec3 north = safeNormalize(glm::cross(up, east), {0.0, 0.0, 1.0});
    const std::uint32_t stride = resolution + 1U;
    const double radius = std::max(1.0, definition.radius + definition.seaLevelElevationMeters - std::max(0.0, radialInsetMeters));
    PlanetMesh mesh{};
    for (std::uint32_t y = 0; y <= resolution; ++y) {
        const double fy = static_cast<double>(y) / static_cast<double>(resolution);
        const double northMeters = -halfExtentMeters + 2.0 * halfExtentMeters * fy;
        for (std::uint32_t x = 0; x <= resolution; ++x) {
            const double fx = static_cast<double>(x) / static_cast<double>(resolution);
            const double eastMeters = -halfExtentMeters + 2.0 * halfExtentMeters * fx;
            const glm::dvec3 direction = safeNormalize(up + east * (eastMeters / definition.radius) + north * (northMeters / definition.radius), up);
            PlanetVertex vertex{};
            vertex.position = glm::vec3(direction * radius);
            vertex.normal = glm::vec3(direction);
            vertex.color = {0.025F, 0.16F, 0.27F};
            vertex.material = {-1.0F, 0.075F, 0.78F, 0.0F};
            mesh.vertices.push_back(vertex);
        }
    }
    for (std::uint32_t y = 0; y < resolution; ++y) for (std::uint32_t x = 0; x < resolution; ++x) {
        const std::uint32_t i0 = y * stride + x;
        const std::uint32_t i1 = i0 + 1U;
        const std::uint32_t i2 = i0 + stride;
        const std::uint32_t i3 = i2 + 1U;
        mesh.indices.insert(mesh.indices.end(), {i0, i2, i1, i1, i2, i3});
    }
    return mesh;
}

void appendOceanSurfaceProxy(PlanetMesh& mesh, const glm::dvec3& center, double seaSurfaceRadius,
    std::uint32_t subdivisionsPerFace) {
    if (subdivisionsPerFace < 2U) throw std::invalid_argument("ocean proxy subdivisions must be >= 2");
    for (std::uint32_t face = 0; face < 6U; ++face) appendOceanFace(mesh, center, seaSurfaceRadius, face, subdivisionsPerFace);
}

void appendCelestialProxy(PlanetMesh& mesh, const glm::dvec3& center, double radius,
    std::uint32_t subdivisionsPerFace, const glm::vec3& color) {
    appendCelestialBodyProxy(mesh, center, glm::dquat{1.0, 0.0, 0.0, 0.0}, radius, subdivisionsPerFace, color);
}

void appendCelestialBodyProxy(PlanetMesh& mesh, const glm::dvec3& center, const glm::dquat& orientation,
    double radius, std::uint32_t subdivisionsPerFace, const glm::vec3& baseColor) {
    if (subdivisionsPerFace < 2U) throw std::invalid_argument("proxy subdivisions must be >= 2");
    const glm::dquat normalizedOrientation = glm::normalize(orientation);
    for (std::uint32_t face = 0; face < 6U; ++face)
        appendFace(mesh, nullptr, center, &normalizedOrientation, radius, face, subdivisionsPerFace, &baseColor);
}

void appendAtmosphereProxy(PlanetMesh& mesh, const glm::dvec3& center, double outerRadius,
    std::uint32_t subdivisionsPerFace, const glm::vec3& scatteringColor, float opticalStrength) {
    if (subdivisionsPerFace < 2U) throw std::invalid_argument("atmosphere subdivisions must be >= 2");
    const glm::vec3 tint = glm::clamp(scatteringColor, glm::vec3{0.01F}, glm::vec3{1.0F});
    const float strength = std::clamp(opticalStrength, 0.02F, 1.0F);
    const glm::vec3 encoded = -(tint * strength);
    const glm::dquat identity{1.0, 0.0, 0.0, 0.0};
    const std::size_t firstVertex = mesh.vertices.size();
    for (std::uint32_t face = 0; face < 6U; ++face)
        appendFace(mesh, nullptr, center, &identity, outerRadius, face, subdivisionsPerFace, &encoded);
    for (std::size_t i = firstVertex; i < mesh.vertices.size(); ++i)
        mesh.vertices[i].material = {0.0F, 1.0F, 1.0F, 0.0F};
}

} // namespace vf
