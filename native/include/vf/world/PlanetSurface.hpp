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
};

struct PlanetVertex {
    glm::vec3 position{};
    glm::vec3 normal{};
    glm::vec3 color{};

    // glTF-style low-cost material payload:
    // x = metallic, y = roughness, z = transmission, w = emissive intensity.
    // This keeps the runtime vertex-only for now while allowing wood/stone/metal/glass/star
    // to be visibly different without a descriptor/material-buffer system.
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
[[nodiscard]] double planetHeight(const PlanetDefinition& definition, const glm::dvec3& direction);
[[nodiscard]] double planetSurfaceRadius(const PlanetDefinition& definition, const glm::dvec3& direction);

// True geometric normal of the authored height field, sampled in double precision at a
// meter-scale baseline. Physics and lighting must use this rather than the radial sphere normal,
// otherwise visually steep hills behave like a smooth sphere.
[[nodiscard]] glm::dvec3 planetSurfaceNormal(
    const PlanetDefinition& definition,
    const glm::dvec3& direction);

[[nodiscard]] PlanetMesh buildPlanetSurface(const PlanetDefinition& definition, std::uint32_t subdivisionsPerFace);

// Near-surface LOD patch for genuinely large planets. The planet can be thousands of kilometres
// in radius while only a few tens of thousands of triangles are generated around the player.
[[nodiscard]] PlanetMesh buildPlanetSurfacePatch(
    const PlanetDefinition& definition,
    const glm::dvec3& centerDirection,
    double halfExtentMeters,
    std::uint32_t resolution);

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

// Adds one transparent atmosphere shell. The vertex color uses an internal negative marker so
// the shared shader can distinguish participating atmosphere from opaque matter without adding a
// separate pipeline. opticalStrength controls visible rim density.
void appendAtmosphereProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double outerRadius,
    std::uint32_t subdivisionsPerFace,
    const glm::vec3& scatteringColor,
    float opticalStrength);

} // namespace vf
