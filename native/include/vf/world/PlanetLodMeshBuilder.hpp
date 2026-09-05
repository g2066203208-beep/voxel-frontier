#pragma once

#include "vf/world/PlanetSurfaceAuthority.hpp"

#include <cstddef>
#include <cstdint>

#include <glm/glm.hpp>

namespace vf {

struct PlanetLodConfig {
    std::uint32_t patchResolution{16U};
    std::uint32_t maxDepth{15U};
    std::size_t maxLeafPatches{5000U};
    double verticalFovRadians{1.1868238913561442}; // 68 degrees
    double viewportHeightPixels{900.0};
    double targetScreenErrorPixels{2.0};
    double horizonMarginRadians{0.012};
    double skirtDepthMeters{3.0};
};

struct PlanetLodStats {
    std::size_t leafPatches{};
    std::uint32_t deepestLevel{};
    double nearestCellMeters{};
};

// Cube-sphere quadtree selected by projected screen-space error. This replaces R23's five giant
// concentric tangent-plane squares: detail now follows what can affect pixels, while horizon culling
// prevents work on the hidden side of the planet. Small inward skirts seal T-junctions between leaf
// depths; they are below the physical surface and never become collision geometry.
[[nodiscard]] PlanetMesh buildAdaptivePlanetSurface(
    const PlanetSurfaceAuthority& surface,
    const glm::dvec3& cameraPlanetLocal,
    const PlanetLodConfig& config = {},
    PlanetLodStats* stats = nullptr);

} // namespace vf
