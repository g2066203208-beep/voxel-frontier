#include "vf/world/PlanetSurface.hpp"

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>

int main() {
    vf::PlanetDefinition planet{};
    planet.seed = 0x71A9F20DULL;
    planet.radius = 240.0;
    planet.maxElevation = 22.0;
    planet.atmosphereHeight = 120.0;

    const vf::PlanetMesh mesh = vf::buildPlanetSurface(planet, 64U);
    if (mesh.drawRanges.empty()) {
        std::cerr << "planet mesh has no draw ranges\n";
        return EXIT_FAILURE;
    }

    std::uint64_t coveredIndices = 0U;
    std::uint32_t previousEnd = 0U;
    std::uint32_t terrainRanges = 0U;
    std::uint32_t treeRanges = 0U;
    std::uint32_t rockRanges = 0U;
    std::uint32_t oceanRanges = 0U;
    std::uint64_t terrainTriangles = 0U;
    std::uint64_t oceanTriangles = 0U;

    for (const auto& range : mesh.drawRanges) {
        if (range.indexCount == 0U || (range.indexCount % 3U) != 0U) {
            std::cerr << "invalid draw range index count\n";
            return EXIT_FAILURE;
        }
        if (range.firstIndex != previousEnd) {
            std::cerr << "draw ranges do not cover the index buffer contiguously\n";
            return EXIT_FAILURE;
        }
        if (static_cast<std::uint64_t>(range.firstIndex) + range.indexCount > mesh.indices.size()) {
            std::cerr << "draw range exceeds index buffer\n";
            return EXIT_FAILURE;
        }
        if (!(range.boundsRadius > 0.0F)) {
            std::cerr << "draw range has invalid bounds\n";
            return EXIT_FAILURE;
        }

        previousEnd = range.firstIndex + range.indexCount;
        coveredIndices += range.indexCount;
        switch (range.drawClass) {
        case vf::PlanetDrawClass::TerrainPatch:
            ++terrainRanges;
            terrainTriangles += range.indexCount / 3U;
            break;
        case vf::PlanetDrawClass::TreeBatch:
            ++treeRanges;
            break;
        case vf::PlanetDrawClass::RockBatch:
            ++rockRanges;
            break;
        case vf::PlanetDrawClass::OceanPatch:
            ++oceanRanges;
            oceanTriangles += range.indexCount / 3U;
            break;
        }
    }

    if (coveredIndices != mesh.indices.size()) {
        std::cerr << "draw ranges do not cover every index exactly once\n";
        return EXIT_FAILURE;
    }
    if (terrainRanges != 6U || treeRanges > 6U || rockRanges > 6U || oceanRanges > 6U) {
        std::cerr << "unexpected spatial batch count\n";
        return EXIT_FAILURE;
    }
    if (!(mesh.horizonOccluderRadius > 0.0F)) {
        std::cerr << "missing conservative horizon occluder radius\n";
        return EXIT_FAILURE;
    }

    // Runtime may request 64 subdivisions, but the V5 visual terrain budget deliberately caps
    // rendering at 44 per cube face. Physics remains analytic and is not reduced by this LOD.
    constexpr std::uint64_t coherentTerrainTriangles = 44ULL * 44ULL * 2ULL * 6ULL;
    if (terrainTriangles != coherentTerrainTriangles) {
        std::cerr << "coherent terrain triangle budget regressed\n";
        return EXIT_FAILURE;
    }

    // Ocean is capped at 32 per face and also omits cells whose four corners are buried under land.
    constexpr std::uint64_t fullOceanTriangles = 32ULL * 32ULL * 2ULL * 6ULL;
    if (oceanTriangles == 0U || oceanTriangles >= fullOceanTriangles) {
        std::cerr << "ocean dry-cell triangle rejection is not active\n";
        return EXIT_FAILURE;
    }

    std::cout << "draw_ranges=" << mesh.drawRanges.size()
              << " terrain=" << terrainRanges
              << " trees=" << treeRanges
              << " rocks=" << rockRanges
              << " ocean=" << oceanRanges
              << " terrain_triangles=" << terrainTriangles
              << " ocean_triangles=" << oceanTriangles
              << " total_triangles=" << mesh.triangleCount() << '\n';
    return EXIT_SUCCESS;
}
