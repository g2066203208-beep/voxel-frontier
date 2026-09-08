#pragma once

#include "vf/world/PlanetSurfaceAuthority.hpp"
#include "vf/world/PlanetTileCache.hpp"

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

    // View-aware streaming. A value of pi disables the view cone. The cone is deliberately wider
    // than the camera frustum so rapid mouse turns consume prefetched tiles instead of revealing
    // holes, while terrain far behind the player is not synthesized at full SSE detail.
    glm::dvec3 viewForwardPlanetLocal{};
    double viewConeHalfAngleRadians{3.14159265358979323846};

    // A patch's projected error is no longer assumed to be its full cell width. Flat terrain gets a
    // conservative fraction of that grid error, while actual center/corner relief raises the error
    // and therefore preserves extra detail in mountains, canyons and hydrology-incised terrain.
    double flatTerrainErrorFraction{0.60};
    double reliefErrorScale{1.35};

    // Ground contact, footsteps and prop placement need a physical cell-size guarantee in addition
    // to projected SSE. Zero nearFieldRadiusMeters disables this constraint for distant globes.
    double nearFieldRadiusMeters{0.0};
    double nearFieldCellMeters{4.0};

    // When nearFieldRadiusMeters is non-zero, render detail no longer ends at a hard radius.
    // Cell size increases continuously across this camera-centred geodesic band, which removes the
    // visible square where a high-detail quadtree island used to meet coarse regional terrain.
    double detailTransitionStartMeters{180.0};
    double detailTransitionEndMeters{32000.0};
    double transitionFarCellMeters{180.0};

    // Nyquist-style procedural band limit for render-only terrain synthesis. A value of 2 means a
    // procedural feature must span at least two local grid cells before we spend CPU evaluating it.
    // Near the player this preserves the full authoritative surface; distant tiles stop evaluating
    // sub-pixel micro/fine displacement that cannot contribute a stable screen sample.
    double minimumFeatureCells{2.0};
};

struct PlanetLodStats {
    std::size_t leafPatches{};
    std::size_t evaluatedNodes{};
    std::size_t culledNodes{};
    std::size_t tileCacheHits{};
    std::size_t tileCacheMisses{};
    std::size_t generatedPatches{};
    std::uint32_t deepestLevel{};
    double nearestCellMeters{};
    double maximumEstimatedErrorMeters{};
};

// Cube-sphere quadtree selected by projected screen-space error. Selection is cheap-first:
// horizon/view-cone rejection occurs before procedural relief probes. When a PlanetTileCache is
// supplied, only cache-miss leaves synthesize terrain; unchanged visible tiles are reused across
// camera turns/recenters. tileEpoch isolates meshes whose non-geographic authority (hydrology) has
// changed without requiring a global cache flush.
[[nodiscard]] PlanetMesh buildAdaptivePlanetSurface(
    const PlanetSurfaceAuthority& surface,
    const glm::dvec3& cameraPlanetLocal,
    const PlanetLodConfig& config = {},
    PlanetLodStats* stats = nullptr,
    PlanetTileCache* tileCache = nullptr,
    std::uint64_t tileEpoch = 0U);

} // namespace vf
