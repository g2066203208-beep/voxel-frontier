#include "vf/world/PlanetLodMeshBuilder.hpp"
#include "vf/world/PlanetSurfaceAuthority.hpp"
#include "vf/world/PlanetTileCache.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>

#include <glm/geometric.hpp>

namespace {

void require(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        std::exit(1);
    }
}

[[nodiscard]] glm::dvec3 safeNormalize(const glm::dvec3& value) {
    const double l2 = glm::dot(value, value);
    return l2 > 1.0e-18 ? value / std::sqrt(l2) : glm::dvec3{0.0, 1.0, 0.0};
}

} // namespace

int main() {
    vf::PlanetDefinition planet{};
    planet.seed = 0xA57F0A11ULL;
    planet.radius = 6371000.0;
    planet.maxElevation = 30000.0;
    planet.maxOceanDepthMeters = 24000.0;
    planet.seaLevelElevationMeters = 0.0;

    vf::PlanetSurfaceAuthority surface{planet};
    vf::PlanetTileCache cache{96ULL * 1024ULL * 1024ULL};

    const glm::dvec3 up = safeNormalize({0.72, 0.52, 0.46});
    const glm::dvec3 tangent = safeNormalize(glm::cross(up, glm::dvec3{0.0, 1.0, 0.0}));
    const glm::dvec3 forward = safeNormalize(tangent - up * 0.06);
    const glm::dvec3 camera = up * (planet.radius + 1800.0);

    vf::PlanetLodConfig lod{};
    lod.patchResolution = 8U;
    lod.maxDepth = 13U;
    lod.maxLeafPatches = 220U;
    lod.verticalFovRadians = 1.1868238913561442;
    lod.viewportHeightPixels = 900.0;
    lod.targetScreenErrorPixels = 5.0;
    lod.viewForwardPlanetLocal = forward;
    lod.viewConeHalfAngleRadians = 1.36;
    lod.nearFieldRadiusMeters = 1.0;
    lod.nearFieldCellMeters = 16.0;
    lod.detailTransitionStartMeters = 250.0;
    lod.detailTransitionEndMeters = 26000.0;
    lod.transitionFarCellMeters = 850.0;
    lod.skirtDepthMeters = 4.0;

    vf::PlanetLodStats first{};
    const vf::PlanetMesh firstMesh = vf::buildAdaptivePlanetSurface(
        surface, camera, lod, &first, &cache, 77U);
    require(!firstMesh.vertices.empty() && !firstMesh.indices.empty(),
        "first visible-set build must produce terrain");
    require(first.leafPatches > 0U, "first visible-set build must select leaves");
    require(first.generatedPatches == first.leafPatches,
        "cold cache must generate every selected visible tile exactly once");
    require(first.tileCacheHits == 0U,
        "cold cache must not report tile hits");

    vf::PlanetLodStats second{};
    const vf::PlanetMesh secondMesh = vf::buildAdaptivePlanetSurface(
        surface, camera, lod, &second, &cache, 77U);
    require(secondMesh.vertices.size() == firstMesh.vertices.size()
            && secondMesh.indices.size() == firstMesh.indices.size(),
        "cache reuse must preserve visible geometry size");
    require(second.generatedPatches == 0U,
        "identical visible-set rebuild must synthesize zero terrain patches");
    require(second.tileCacheHits == second.leafPatches,
        "identical visible-set rebuild must hit every selected tile");

    // A modest camera turn should retain substantial overlap. Newly exposed tiles may be generated,
    // but already visible tiles must come from the persistent cache instead of being regenerated.
    vf::PlanetLodConfig turned = lod;
    turned.viewForwardPlanetLocal = safeNormalize(forward + tangent * 0.19);
    vf::PlanetLodStats third{};
    (void)vf::buildAdaptivePlanetSurface(surface, camera, turned, &third, &cache, 77U);
    require(third.tileCacheHits > 0U,
        "small view turn must reuse overlapping terrain tiles");
    require(third.generatedPatches < third.leafPatches,
        "small view turn must generate only cache-miss tiles");

    // Hydrology/authority epochs intentionally invalidate geographic tile reuse without flushing the
    // whole cache. A new epoch must regenerate tiles while old-epoch data remains isolated.
    vf::PlanetLodStats changedEpoch{};
    (void)vf::buildAdaptivePlanetSurface(surface, camera, lod, &changedEpoch, &cache, 78U);
    require(changedEpoch.generatedPatches == changedEpoch.leafPatches,
        "new surface-authority epoch must not reuse stale hydrology tiles");

    const vf::PlanetTileCacheStats cacheStats = cache.stats();
    require(cacheStats.hits >= second.leafPatches,
        "cache telemetry must count persistent tile reuse");
    require(cacheStats.entries > 0U && cacheStats.residentBytes > 0U,
        "tile cache must own resident immutable patch meshes");

    std::cout << "R24 planet tile streaming tests passed"
              << " first_leaves=" << first.leafPatches
              << " second_hits=" << second.tileCacheHits
              << " turn_hits=" << third.tileCacheHits
              << " turn_generated=" << third.generatedPatches
              << " resident_mb=" << (cacheStats.residentBytes / (1024.0 * 1024.0))
              << '\n';
    return 0;
}
