#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>

namespace vf {

enum class MotionLodTier : std::uint8_t {
    Inspect,
    Explore,
    Fast,
    Transit
};

struct VelocityLodInput {
    double linearSpeedMetersPerSecond{};
    double angularSpeedRadiansPerSecond{};
    double stableViewSeconds{};
    double baseTargetScreenErrorPixels{2.0};
    double baseNearFieldCellMeters{4.0};
    std::size_t baseMaxLeafPatches{1100U};
    double baseTransitionFarCellMeters{180.0};
};

struct VelocityLodDecision {
    MotionLodTier tier{MotionLodTier::Inspect};
    double motionWeight{};
    double targetScreenErrorPixels{2.0};
    double nearFieldCellMeters{4.0};
    std::size_t maxLeafPatches{1100U};
    double transitionFarCellMeters{180.0};
    double prefetchLookAheadSeconds{0.35};
    double forwardPrefetchMeters{150.0};
    double minimumStableViewSecondsForRefine{0.15};
    bool fineDetailAllowed{true};
};

[[nodiscard]] inline double lodSmooth01(double value) noexcept {
    const double t = std::clamp(value, 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

[[nodiscard]] inline double lodRamp(double value, double begin, double end) noexcept {
    if (end <= begin) return value >= end ? 1.0 : 0.0;
    return lodSmooth01((value - begin) / (end - begin));
}

// R24_VELOCITY_AWARE_LOD_V1
// Perceptual detail policy: faster camera motion increases coverage and look-ahead while reducing
// geometric precision. Refinement is only allowed after the view remains stable long enough to make
// the additional geometry perceptible. This prevents high-speed travel from producing expensive
// fine meshes that leave the screen before the player can inspect them.
[[nodiscard]] inline VelocityLodDecision decideVelocityAwareLod(
    const VelocityLodInput& input) noexcept {
    const double speed = std::max(0.0, input.linearSpeedMetersPerSecond);
    const double angularSpeed = std::max(0.0, input.angularSpeedRadiansPerSecond);

    // Linear motion covers walking -> vehicles -> atmospheric/planetary transit continuously.
    const double linearMotion = lodRamp(speed, 8.0, 2500.0);
    // Rapid camera turns also reduce useful spatial detail even when the camera position is static.
    const double angularMotion = lodRamp(angularSpeed, 0.35, 2.4);
    const double motion = std::max(linearMotion, angularMotion);

    VelocityLodDecision result{};
    result.motionWeight = motion;
    result.tier = motion < 0.10 ? MotionLodTier::Inspect
        : (motion < 0.38 ? MotionLodTier::Explore
        : (motion < 0.72 ? MotionLodTier::Fast : MotionLodTier::Transit));

    const double screenErrorScale = 1.0 + 7.0 * motion;
    const double cellScale = 1.0 + 23.0 * motion;
    const double farCellScale = 1.0 + 5.0 * motion;
    const double leafScale = 1.0 - 0.84 * motion;

    result.targetScreenErrorPixels = std::max(0.5, input.baseTargetScreenErrorPixels) * screenErrorScale;
    result.nearFieldCellMeters = std::max(0.25, input.baseNearFieldCellMeters) * cellScale;
    result.transitionFarCellMeters = std::max(1.0, input.baseTransitionFarCellMeters) * farCellScale;
    result.maxLeafPatches = std::max<std::size_t>(
        64U,
        static_cast<std::size_t>(std::llround(
            static_cast<double>(std::max<std::size_t>(64U, input.baseMaxLeafPatches)) * leafScale)));

    // Spend speed on forward coverage, not precision. High speed sees farther ahead but each cell is
    // cheaper. A minimum distance avoids tiny prefetch windows at walking speed.
    result.prefetchLookAheadSeconds = 0.35 + 1.90 * motion;
    result.forwardPrefetchMeters = std::max(150.0, speed * result.prefetchLookAheadSeconds);

    // Hysteresis-by-dwell: a camera that has just decelerated does not instantly trigger expensive
    // refinement. It must remain visually stable first, preventing rebuild thrash near thresholds.
    result.minimumStableViewSecondsForRefine = 0.15 + 0.85 * motion;
    result.fineDetailAllowed = motion < 0.18
        && input.stableViewSeconds >= result.minimumStableViewSecondsForRefine;
    return result;
}

} // namespace vf
