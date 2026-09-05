#pragma once

#include <cstdint>

#include <glm/glm.hpp>

#include "vf/world/PlanetSurface.hpp"

namespace vf {

// Fixed render-local frame used by the Earth-scale runtime. Procedural props are generated directly
// in this high-precision local frame, avoiding float precision loss from authoring tiny trees at a
// 6,371 km planet radius and transforming them afterwards.
struct SurfaceRenderFrame {
    glm::dvec3 originPlanet{};
    glm::dvec3 tangentX{1.0, 0.0, 0.0};
    glm::dvec3 up{0.0, 1.0, 0.0};
    glm::dvec3 tangentZ{0.0, 0.0, 1.0};
};

struct ProceduralEcologySettings {
    // Caps intentionally sit above the expected accepted-cell count. The generator currently walks
    // stable cells lexicographically, so a tight cap would bias all accepted props toward one side
    // of the square search window and leave the camera neighbourhood empty. These radii/cell sizes
    // keep the full accepted set bounded while preserving nearby forest structure.
    double treeRadiusMeters{1800.0};
    double treeCellMeters{56.0};
    std::uint32_t maxTrees{2400U};

    double rockRadiusMeters{1400.0};
    double rockCellMeters{50.0};
    std::uint32_t maxRocks{1800U};

    double grassRadiusMeters{620.0};
    double grassCellMeters{14.0};
    std::uint32_t maxGrassClumps{6000U};
};

// Builds only near-field visual ecology. Placement is derived from stable render-frame grid cells and
// the same authoritative planet height/normal query used by physics, so streaming/rebuilds do not
// move props or let them float above the terrain.
[[nodiscard]] PlanetMesh buildProceduralEcology(
    const PlanetDefinition& planet,
    const glm::dvec3& centerDirection,
    const SurfaceRenderFrame& frame,
    const ProceduralEcologySettings& settings = {});

} // namespace vf
