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

// R24_VELOCITY_AWARE_LOD_V2
// Perceptual detail policy: faster camera motion increases forward coverage and look-ahead while
// reducing geometric precision. The speed response is deliberately piecewise: walking/slow flight,
// vehicle/aircraft speeds and high-speed planetary transit each consume a portion of the motion
// budget instead of treating 120 m/s as almost stationary next to a 2500 m/s endpoint.
// Refinement is only allowed after the view remains stable long enough to make the extra geometry
// perceptible. This prevents high-speed travel from generating expensive fine meshes that leave the
// screen before the player can inspect them.
[[nodiscard]] inline VelocityLodDecision decideVelocityAwareLod(
    const VelocityLodInput& input) noexcept {
    const double speed = std::max(0.0, input.linearSpeedMetersPerSecond);
    const double angularSpeed = std::max(0.0, input.angularSpeedRadiansPerSecond);

    // Piecewise perceptual motion response. 120 m/s must already be meaningfully coarser than an
    // inspecting camera, while the policy still has headroom for aircraft and planetary transit.
    const double linearMotion = std::clamp(
        0.22 * lodRamp(speed, 8.0, 120.0)
        + 0.38 * lodRamp(speed, 120.0, 800.0)
        + 0.40 * lodRamp(speed, 800.0, 3200.0),
        0.0,
        1.0);
    // Rapid camera turns reduce useful spatial detail even when the camera position is static.
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

    // Spend speed on forward coverage, not precision. The baseline coverage itself expands with
    // motion, so even moderate travel (e.g. 120 m/s) prefetches farther ahead than a stationary
    // camera. At very high speed, velocity * look-ahead dominates naturally.
    result.prefetchLookAheadSeconds = 0.35 + 1.90 * motion;
    const double motionCoverageFloor = 150.0 * (1.0 + 3.0 * motion);
    result.forwardPrefetchMeters = std::max(
        motionCoverageFloor,
        speed * result.prefetchLookAheadSeconds);

    // Hysteresis-by-dwell: a camera that has just decelerated does not instantly trigger expensive
    // refinement. It must remain visually stable first, preventing rebuild thrash near thresholds.
    result.minimumStableViewSecondsForRefine = 0.15 + 0.85 * motion;
    result.fineDetailAllowed = motion < 0.18
        && input.stableViewSeconds >= result.minimumStableViewSecondsForRefine;
    return result;
}

} // namespace vf
