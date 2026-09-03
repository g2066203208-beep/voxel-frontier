#pragma once

#include <cstdint>

#include "vf/physics/CollisionGeometry.hpp"

namespace vf {

// Diagnostics are intentionally optional so the production narrow phase stays allocation-free.
// They exist to keep convergence behavior observable in regression tests and future profiling.
struct GjkEpaDiagnostics {
    std::uint32_t gjkIterations{};
    std::uint32_t epaIterations{};
    bool gjkIntersected{};
    bool epaConverged{};
};

// General support-mapped convex collision query.
//
// GJK determines whether the Minkowski difference contains the origin. EPA then expands
// the terminal simplex to recover penetration normal/depth and witness points. The returned
// normal follows the engine convention: shape A -> shape B. Current output is one contact
// point; face clipping/manifold reduction remains a separate layer for polyhedral patches.
[[nodiscard]] bool collideConvexGjkEpa(
    const CollisionShape& a,
    const ShapePose& poseA,
    const CollisionShape& b,
    const ShapePose& poseB,
    ContactManifold& manifold,
    GjkEpaDiagnostics* diagnostics = nullptr) noexcept;

} // namespace vf
