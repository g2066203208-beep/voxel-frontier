#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>

namespace vf::core {

struct FixedStepConfig {
    double simulationHz{120.0};
    double maxAcceptedFrameSeconds{0.050};
    std::uint32_t maxSimulationStepsPerFrame{8U};
};

struct FixedStepResult {
    std::uint32_t simulationSteps{};
    double fixedDeltaSeconds{};
    double interpolationAlpha{};
    double acceptedFrameSeconds{};
    double droppedSimulationSeconds{};
};

// R24_ENGINE_FOUNDATION_V1
// A render frame is never allowed to create an unbounded simulation catch-up spiral.
// Simulation remains fixed-step/deterministic while rendering stays completely uncapped.
class FixedStepClock final {
public:
    explicit FixedStepClock(FixedStepConfig config = {}) noexcept
        : config_(sanitize(config)),
          fixedDeltaSeconds_(1.0 / config_.simulationHz) {}

    [[nodiscard]] FixedStepResult advance(double wallFrameSeconds) noexcept {
        FixedStepResult result{};
        result.fixedDeltaSeconds = fixedDeltaSeconds_;

        if (!std::isfinite(wallFrameSeconds) || wallFrameSeconds < 0.0) wallFrameSeconds = 0.0;
        result.acceptedFrameSeconds = std::min(wallFrameSeconds, config_.maxAcceptedFrameSeconds);
        accumulatorSeconds_ += result.acceptedFrameSeconds;

        const auto availableSteps = static_cast<std::uint64_t>(
            std::floor(accumulatorSeconds_ / fixedDeltaSeconds_));
        result.simulationSteps = static_cast<std::uint32_t>(std::min<std::uint64_t>(
            availableSteps, config_.maxSimulationStepsPerFrame));
        accumulatorSeconds_ -= static_cast<double>(result.simulationSteps) * fixedDeltaSeconds_;

        // If a pathological stall still left more than one frame's worth of fixed steps queued,
        // discard whole old steps instead of turning one hitch into seconds of catch-up hitches.
        if (accumulatorSeconds_ >= fixedDeltaSeconds_) {
            const double remainder = std::fmod(accumulatorSeconds_, fixedDeltaSeconds_);
            result.droppedSimulationSeconds = accumulatorSeconds_ - remainder;
            accumulatorSeconds_ = remainder;
            droppedSimulationSeconds_ += result.droppedSimulationSeconds;
        }

        result.interpolationAlpha = std::clamp(
            accumulatorSeconds_ / fixedDeltaSeconds_, 0.0, 1.0);
        return result;
    }

    void reset() noexcept {
        accumulatorSeconds_ = 0.0;
        droppedSimulationSeconds_ = 0.0;
    }

    [[nodiscard]] double fixedDeltaSeconds() const noexcept { return fixedDeltaSeconds_; }
    [[nodiscard]] double totalDroppedSimulationSeconds() const noexcept {
        return droppedSimulationSeconds_;
    }
    [[nodiscard]] const FixedStepConfig& config() const noexcept { return config_; }

private:
    [[nodiscard]] static FixedStepConfig sanitize(FixedStepConfig config) noexcept {
        if (!std::isfinite(config.simulationHz) || config.simulationHz < 1.0)
            config.simulationHz = 120.0;
        config.simulationHz = std::clamp(config.simulationHz, 1.0, 1000.0);
        if (!std::isfinite(config.maxAcceptedFrameSeconds) || config.maxAcceptedFrameSeconds <= 0.0)
            config.maxAcceptedFrameSeconds = 0.050;
        config.maxAcceptedFrameSeconds = std::clamp(config.maxAcceptedFrameSeconds, 0.001, 0.250);
        config.maxSimulationStepsPerFrame = std::clamp<std::uint32_t>(
            config.maxSimulationStepsPerFrame, 1U, 64U);
        return config;
    }

    FixedStepConfig config_{};
    double fixedDeltaSeconds_{1.0 / 120.0};
    double accumulatorSeconds_{};
    double droppedSimulationSeconds_{};
};

} // namespace vf::core
