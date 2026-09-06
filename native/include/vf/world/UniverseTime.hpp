#pragma once

#include "vf/world/AstroTime.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>

namespace vf {

struct UniverseTimeConfig {
    double physicsStepSeconds{1.0 / 120.0};
    double gameplayStepSeconds{1.0 / 60.0};
    double weatherStepSeconds{60.0};
    double climateStepSeconds{900.0};
    std::size_t maxTicksPerConsume{1000000U};
};

// Multi-rate simulated-time scheduler. AstroTime remains the high-precision epoch, while the
// accumulators expose deterministic subsystem cadences. `advance()` consumes simulated seconds,
// not wall/render seconds; time-warp policy remains owned by CelestialSimulationClock.
class UniverseTime final {
public:
    explicit UniverseTime(UniverseTimeConfig config = {}) noexcept
        : config_(config) {
        sanitizeConfig();
    }

    void setConfig(UniverseTimeConfig config) noexcept {
        config_ = config;
        sanitizeConfig();
    }

    [[nodiscard]] const UniverseTimeConfig& config() const noexcept { return config_; }
    [[nodiscard]] const AstroTime& time() const noexcept { return time_; }
    [[nodiscard]] long double secondsFromEpoch() const noexcept { return time_.secondsFromEpoch(); }

    [[nodiscard]] double secondsApprox() const noexcept {
        const long double value = secondsFromEpoch();
        const long double maximum = static_cast<long double>(std::numeric_limits<double>::max());
        if (value >= maximum) return std::numeric_limits<double>::max();
        if (value <= -maximum) return -std::numeric_limits<double>::max();
        return static_cast<double>(value);
    }

    void reset(AstroTime time = {}) noexcept {
        time.normalize();
        time_ = time;
        physicsAccumulator_ = 0.0;
        gameplayAccumulator_ = 0.0;
        weatherAccumulator_ = 0.0;
        climateAccumulator_ = 0.0;
    }

    void advance(double simulatedDeltaSeconds) noexcept {
        if (!std::isfinite(simulatedDeltaSeconds) || simulatedDeltaSeconds <= 0.0) return;
        time_.advance(simulatedDeltaSeconds);
        physicsAccumulator_ += simulatedDeltaSeconds;
        gameplayAccumulator_ += simulatedDeltaSeconds;
        weatherAccumulator_ += simulatedDeltaSeconds;
        climateAccumulator_ += simulatedDeltaSeconds;
    }

    [[nodiscard]] std::size_t consumePhysicsTicks() noexcept {
        return consumeTicks(physicsAccumulator_, config_.physicsStepSeconds);
    }
    [[nodiscard]] std::size_t consumeGameplayTicks() noexcept {
        return consumeTicks(gameplayAccumulator_, config_.gameplayStepSeconds);
    }
    [[nodiscard]] std::size_t consumeWeatherTicks() noexcept {
        return consumeTicks(weatherAccumulator_, config_.weatherStepSeconds);
    }
    [[nodiscard]] std::size_t consumeClimateTicks() noexcept {
        return consumeTicks(climateAccumulator_, config_.climateStepSeconds);
    }

    [[nodiscard]] bool consumePhysicsTick() noexcept {
        return consumeOne(physicsAccumulator_, config_.physicsStepSeconds);
    }
    [[nodiscard]] bool consumeGameplayTick() noexcept {
        return consumeOne(gameplayAccumulator_, config_.gameplayStepSeconds);
    }
    [[nodiscard]] bool consumeWeatherTick() noexcept {
        return consumeOne(weatherAccumulator_, config_.weatherStepSeconds);
    }
    [[nodiscard]] bool consumeClimateTick() noexcept {
        return consumeOne(climateAccumulator_, config_.climateStepSeconds);
    }

    [[nodiscard]] double pendingPhysicsSeconds() const noexcept { return physicsAccumulator_; }
    [[nodiscard]] double pendingGameplaySeconds() const noexcept { return gameplayAccumulator_; }
    [[nodiscard]] double pendingWeatherSeconds() const noexcept { return weatherAccumulator_; }
    [[nodiscard]] double pendingClimateSeconds() const noexcept { return climateAccumulator_; }

    [[nodiscard]] double physicsInterpolationAlpha() const noexcept {
        return interpolationAlpha(physicsAccumulator_, config_.physicsStepSeconds);
    }
    [[nodiscard]] double gameplayInterpolationAlpha() const noexcept {
        return interpolationAlpha(gameplayAccumulator_, config_.gameplayStepSeconds);
    }

private:
    void sanitizeConfig() noexcept {
        if (!std::isfinite(config_.physicsStepSeconds) || config_.physicsStepSeconds <= 0.0)
            config_.physicsStepSeconds = 1.0 / 120.0;
        if (!std::isfinite(config_.gameplayStepSeconds) || config_.gameplayStepSeconds <= 0.0)
            config_.gameplayStepSeconds = 1.0 / 60.0;
        if (!std::isfinite(config_.weatherStepSeconds) || config_.weatherStepSeconds <= 0.0)
            config_.weatherStepSeconds = 60.0;
        if (!std::isfinite(config_.climateStepSeconds) || config_.climateStepSeconds <= 0.0)
            config_.climateStepSeconds = 900.0;
        config_.maxTicksPerConsume = std::max<std::size_t>(1U, config_.maxTicksPerConsume);
    }

    [[nodiscard]] std::size_t consumeTicks(double& accumulator, double stepSeconds) noexcept {
        if (!std::isfinite(accumulator) || accumulator <= 0.0) {
            accumulator = 0.0;
            return 0U;
        }
        const double epsilon = 1.0e-12 * std::max(1.0, stepSeconds);
        const double rawTicks = std::floor((accumulator + epsilon) / stepSeconds);
        if (rawTicks < 1.0) return 0U;
        const double bounded = std::min(
            rawTicks,
            static_cast<double>(config_.maxTicksPerConsume));
        const auto ticks = static_cast<std::size_t>(bounded);
        accumulator -= static_cast<double>(ticks) * stepSeconds;
        if (accumulator < 0.0 && accumulator > -epsilon) accumulator = 0.0;
        return ticks;
    }

    [[nodiscard]] static bool consumeOne(double& accumulator, double stepSeconds) noexcept {
        const double epsilon = 1.0e-12 * std::max(1.0, stepSeconds);
        if (!std::isfinite(accumulator) || accumulator + epsilon < stepSeconds) return false;
        accumulator -= stepSeconds;
        if (accumulator < 0.0 && accumulator > -epsilon) accumulator = 0.0;
        return true;
    }

    [[nodiscard]] static double interpolationAlpha(double accumulator, double stepSeconds) noexcept {
        if (!std::isfinite(accumulator) || !std::isfinite(stepSeconds) || stepSeconds <= 0.0)
            return 0.0;
        return std::clamp(accumulator / stepSeconds, 0.0, 1.0);
    }

    UniverseTimeConfig config_{};
    AstroTime time_{};
    double physicsAccumulator_{};
    double gameplayAccumulator_{};
    double weatherAccumulator_{};
    double climateAccumulator_{};
};

} // namespace vf
