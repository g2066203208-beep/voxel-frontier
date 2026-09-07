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

    // A patch's projected error is no longer assumed to be its full cell width. Flat terrain gets a
    // conservative fraction of that grid error, while actual center/corner relief raises the error
    // and therefore preserves extra detail in mountains, canyons and hydrology-incised terrain.
    double flatTerrainErrorFraction{0.60};
    double reliefErrorScale{1.35};

    // Ground contact, footsteps and prop placement need a physical cell-size guarantee in addition
    // to projected SSE. Zero nearFieldRadiusMeters disables this constraint for distant globes.
    double nearFieldRadiusMeters{0.0};
    double nearFieldCellMeters{4.0};
};

struct PlanetLodStats {
    std::size_t leafPatches{};
    std::size_t evaluatedNodes{};
    std::uint32_t deepestLevel{};
    double nearestCellMeters{};
    double maximumEstimatedErrorMeters{};
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
