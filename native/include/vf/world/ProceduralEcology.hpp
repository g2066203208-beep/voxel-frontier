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
    // Dense enough to read as a forest from walking height, but bounded so every asynchronous
    // terrain rebuild has a predictable CPU/GPU budget. Stable grid cells keep the same props after
    // streaming instead of respawning a new random forest around the camera.
    double treeRadiusMeters{2200.0};
    double treeCellMeters{58.0};
    std::uint32_t maxTrees{760U};

    double rockRadiusMeters{1500.0};
    double rockCellMeters{54.0};
    std::uint32_t maxRocks{360U};

    double grassRadiusMeters{620.0};
    double grassCellMeters{14.0};
    std::uint32_t maxGrassClumps{1500U};
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
