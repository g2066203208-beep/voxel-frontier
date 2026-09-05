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
    double treeRadiusMeters{2600.0};
    double treeCellMeters{88.0};
    std::uint32_t maxTrees{420U};

    double rockRadiusMeters{1900.0};
    double rockCellMeters{64.0};
    std::uint32_t maxRocks{300U};

    double grassRadiusMeters{520.0};
    double grassCellMeters{18.0};
    std::uint32_t maxGrassClumps{900U};
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
