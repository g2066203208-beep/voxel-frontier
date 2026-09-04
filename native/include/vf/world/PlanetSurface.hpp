#pragma once

#include <cstdint>
#include <vector>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

namespace vf {

struct PlanetDefinition {
    std::uint64_t seed{0xA57F0A11ULL};
    double radius{240.0};
    double maxElevation{24.0};
    double atmosphereHeight{120.0};
    double seaLevelElevationMeters{};
    double maxOceanDepthMeters{};
};

struct PlanetTerrainSample {
    double elevationMeters{};
    double continentalness{};
    double mountain{};
    double plateau{};
    double trench{};
    double volcano{};
    double river{};
    double oceanDepthMeters{};

    [[nodiscard]] bool submerged(const PlanetDefinition& definition) const noexcept {
        return elevationMeters < definition.seaLevelElevationMeters;
    }
};

struct PlanetVertex {
    glm::vec3 position{};
    glm::vec3 normal{};
    glm::vec3 color{};
    glm::vec4 material{0.0F, 0.78F, 0.0F, 0.0F};
};

struct PlanetMesh {
    std::vector<PlanetVertex> vertices;
    std::vector<std::uint32_t> indices;

    [[nodiscard]] std::uint64_t triangleCount() const noexcept {
        return static_cast<std::uint64_t>(indices.size() / 3U);
    }
};

[[nodiscard]] glm::dvec3 cubeSphereDirection(std::uint32_t face, double u, double v);
[[nodiscard]] PlanetTerrainSample samplePlanetTerrain(
    const PlanetDefinition& definition,
    const glm::dvec3& direction);
[[nodiscard]] double planetHeight(const PlanetDefinition& definition, const glm::dvec3& direction);
[[nodiscard]] double planetSurfaceRadius(const PlanetDefinition& definition, const glm::dvec3& direction);
[[nodiscard]] glm::vec3 planetTerrainColor(
    const PlanetDefinition& definition,
    const PlanetTerrainSample& sample) noexcept;
[[nodiscard]] glm::vec4 planetTerrainMaterial(
    const PlanetDefinition& definition,
    const PlanetTerrainSample& sample) noexcept;
[[nodiscard]] glm::dvec3 planetSurfaceNormal(
    const PlanetDefinition& definition,
    const glm::dvec3& direction);

[[nodiscard]] PlanetMesh buildPlanetSurface(const PlanetDefinition& definition, std::uint32_t subdivisionsPerFace);
[[nodiscard]] PlanetMesh buildPlanetSurfacePatch(
    const PlanetDefinition& definition,
    const glm::dvec3& centerDirection,
    double halfExtentMeters,
    std::uint32_t resolution);
[[nodiscard]] PlanetMesh buildOceanSurfacePatch(
    const PlanetDefinition& definition,
    const glm::dvec3& centerDirection,
    double halfExtentMeters,
    std::uint32_t resolution,
    double radialInsetMeters = 0.0);
void appendOceanSurfaceProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double seaSurfaceRadius,
    std::uint32_t subdivisionsPerFace);

void appendCelestialProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double radius,
    std::uint32_t subdivisionsPerFace,
    const glm::vec3& color);
void appendCelestialBodyProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    const glm::dquat& orientation,
    double radius,
    std::uint32_t subdivisionsPerFace,
    const glm::vec3& baseColor);
void appendAtmosphereProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double outerRadius,
    std::uint32_t subdivisionsPerFace,
    const glm::vec3& scatteringColor,
    float opticalStrength);

} // namespace vf
