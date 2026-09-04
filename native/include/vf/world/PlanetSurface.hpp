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
    // Literal RGB stays in [0, 1] for debug/celestial proxy meshes. The primary planet builder
    // also uses this existing three-float channel as a compact procedural-material payload so the
    // Vulkan vertex ABI stays unchanged while terrain, bark, foliage, rocks and ocean receive
    // distinct shader materials. See native/shaders/planet.slang.
    glm::vec3 color{};
};

struct PlanetMesh {
    std::vector<PlanetVertex> vertices;
    std::vector<std::uint32_t> indices;
    std::uint32_t treeCount{0U};
    std::uint32_t rockCount{0U};
    // Ocean indices are appended after all opaque planet/ecology indices. The renderer uses this
    // contiguous range for a transparent water pass without allocating a second static mesh.
    std::uint32_t oceanFirstIndex{0U};
    std::uint32_t oceanIndexCount{0U};

    [[nodiscard]] std::uint64_t triangleCount() const noexcept {
        return static_cast<std::uint64_t>(indices.size() / 3U);
    }
};

[[nodiscard]] glm::dvec3 cubeSphereDirection(std::uint32_t face, double u, double v);
[[nodiscard]] double planetHeight(const PlanetDefinition& definition, const glm::dvec3& direction);
[[nodiscard]] double planetSurfaceRadius(const PlanetDefinition& definition, const glm::dvec3& direction);
[[nodiscard]] PlanetMesh buildPlanetSurface(const PlanetDefinition& definition, std::uint32_t subdivisionsPerFace);
void appendOceanSurface(
    PlanetMesh& mesh,
    const PlanetDefinition& definition,
    double oceanSurfaceRadius,
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

} // namespace vf
