#include "vf/world/detail/PlanetGenerationInternal.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

#include <glm/geometric.hpp>

namespace vf::detail {

std::uint32_t dominantCubeFace(const glm::dvec3& directionInput) noexcept {
    const glm::dvec3 d = glm::normalize(directionInput);
    const glm::dvec3 a = glm::abs(d);
    if (a.x >= a.y && a.x >= a.z) return d.x >= 0.0 ? 0U : 1U;
    if (a.y >= a.x && a.y >= a.z) return d.y >= 0.0 ? 2U : 3U;
    return d.z >= 0.0 ? 4U : 5U;
}

void appendDrawRange(
    PlanetMesh& mesh,
    std::uint32_t firstIndex,
    std::uint32_t indexCount,
    PlanetDrawClass drawClass,
    float representativeRadius) {
    if (indexCount == 0U) return;
    const std::uint64_t end = static_cast<std::uint64_t>(firstIndex) + indexCount;
    if (end > mesh.indices.size()) return;

    glm::dvec3 center{0.0};
    std::uint64_t sampleCount = 0U;
    for (std::uint32_t i = firstIndex; i < firstIndex + indexCount; ++i) {
        const std::uint32_t vertexIndex = mesh.indices[i];
        if (vertexIndex >= mesh.vertices.size()) continue;
        center += glm::dvec3(mesh.vertices[vertexIndex].position);
        ++sampleCount;
    }
    if (sampleCount == 0U) return;
    center /= static_cast<double>(sampleCount);

    double radiusSquared = 0.0;
    for (std::uint32_t i = firstIndex; i < firstIndex + indexCount; ++i) {
        const std::uint32_t vertexIndex = mesh.indices[i];
        if (vertexIndex >= mesh.vertices.size()) continue;
        const glm::dvec3 delta = glm::dvec3(mesh.vertices[vertexIndex].position) - center;
        radiusSquared = std::max(radiusSquared, glm::dot(delta, delta));
    }

    PlanetDrawRange range{};
    range.firstIndex = firstIndex;
    range.indexCount = indexCount;
    range.boundsCenter = glm::vec3(center);
    // Small conservative inflation covers float conversion and static water-wave displacement.
    range.boundsRadius = static_cast<float>(std::sqrt(radiusSquared) + 0.12);
    range.drawClass = drawClass;
    range.representativeRadius = std::max(0.0F, representativeRadius);
    mesh.drawRanges.push_back(range);
}

} // namespace vf::detail
