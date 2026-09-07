#pragma once

#include <algorithm>
#include <cmath>

namespace vf {

struct TerrainStreamingInput {
    bool onPrimaryPlanet{};
    double altitudeMeters{};
    double localSpeedMetersPerSecond{};
    double arcDistanceFromWindowMeters{};
    bool buildInFlight{};
    double cooldownSeconds{};
};

struct TerrainStreamingDecision {
    double recenterThresholdMeters{};
    double prefetchThresholdMeters{};
    double detailedSpeedLimitMetersPerSecond{};
    double staleAcceptanceMeters{};
    bool detailedSurfaceEligible{};
    bool currentWindowUsable{};
    bool useDistantGlobe{};
    bool requestBuild{};
};

[[nodiscard]] inline TerrainStreamingDecision decideTerrainStreaming(
    const TerrainStreamingInput& input) noexcept {
    TerrainStreamingDecision result{};
    const double altitude = std::max(0.0, input.altitudeMeters);
    result.recenterThresholdMeters = altitude < 20000.0 ? 8000.0
        : (altitude < 100000.0 ? 40000.0
        : (altitude < 350000.0 ? 120000.0 : 350000.0));
    result.prefetchThresholdMeters = result.recenterThresholdMeters * 0.42;
    result.detailedSpeedLimitMetersPerSecond = altitude < 20000.0 ? 2500.0
        : (altitude < 100000.0 ? 12000.0 : 30000.0);
    result.staleAcceptanceMeters = std::max(
        50000.0, result.recenterThresholdMeters * 1.60);

    const double speed = std::max(0.0, input.localSpeedMetersPerSecond);
    result.detailedSurfaceEligible = input.onPrimaryPlanet
        && altitude < 800000.0
        && speed <= result.detailedSpeedLimitMetersPerSecond;
    result.currentWindowUsable = input.arcDistanceFromWindowMeters
        <= result.recenterThresholdMeters * 0.70;
    result.useDistantGlobe = !result.detailedSurfaceEligible || !result.currentWindowUsable;
    result.requestBuild = result.detailedSurfaceEligible
        && !input.buildInFlight
        && input.cooldownSeconds <= 0.0
        && input.arcDistanceFromWindowMeters > result.prefetchThresholdMeters;
    return result;
}

} // namespace vf
