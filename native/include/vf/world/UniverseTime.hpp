#pragma once

namespace vf {

// Independent simulation clocks prevent orbital, climate, and gameplay systems
// from being forced onto the same frame rate.
struct UniverseTime {
    double totalSeconds{};
    double physicsAccumulator{};
    double gameplayAccumulator{};
    double weatherAccumulator{};
    double climateAccumulator{};
    double orbitalAccumulator{};

    double physicsStepSeconds{1.0 / 120.0};
    double gameplayStepSeconds{1.0 / 60.0};
    double weatherStepSeconds{60.0};
    double climateStepSeconds{86400.0};
    double orbitalStepSeconds{3600.0};

    void advance(double realDeltaSeconds) noexcept;

    [[nodiscard]] bool consumePhysicsTick() noexcept;
    [[nodiscard]] bool consumeGameplayTick() noexcept;
    [[nodiscard]] bool consumeWeatherTick() noexcept;
    [[nodiscard]] bool consumeClimateTick() noexcept;
    [[nodiscard]] bool consumeOrbitalTick() noexcept;
};

} // namespace vf
