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

enum class PlanetDrawClass : std::uint8_t {
    TerrainPatch,
    TreeBatch,
    RockBatch,
    OceanPatch,
};

// One coarse spatial batch. The world intentionally keeps this list tiny (roughly one batch per
// cube-sphere face/material family) so CPU visibility work remains tens of sphere tests, not a
// per-triangle/per-object traversal. The same ranges can later become indirect/meshlet commands.
struct PlanetDrawRange {
    std::uint32_t firstIndex{0U};
    std::uint32_t indexCount{0U};
    glm::vec3 boundsCenter{};
    float boundsRadius{0.0F};
    PlanetDrawClass drawClass{PlanetDrawClass::TerrainPatch};
    // Approximate feature size used only for sub-pixel whole-batch rejection. Zero disables it.
    float representativeRadius{0.0F};
};

struct PlanetMesh {
    std::vector<PlanetVertex> vertices;
    std::vector<std::uint32_t> indices;
    std::vector<PlanetDrawRange> drawRanges;
    std::uint32_t treeCount{0U};
    std::uint32_t rockCount{0U};
    // Ocean indices are appended after opaque planet/ecology indices.
    std::uint32_t oceanFirstIndex{0U};
    std::uint32_t oceanIndexCount{0U};
    // Conservative inner sphere guaranteed to be occupied by the solid planet. A batch wholly
    // behind this sphere can be rejected before issuing a draw.
    float horizonOccluderRadius{0.0F};

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
