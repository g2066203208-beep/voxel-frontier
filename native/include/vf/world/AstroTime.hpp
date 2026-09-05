#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>

namespace vf {

// High-precision simulation epoch represented as an integer second plus a normalized fractional
// remainder. This avoids tying astronomical state to render-frame count and keeps long-running
// worlds numerically stable while remaining deterministic and serialization-friendly.
struct AstroTime {
    std::int64_t wholeSeconds{};
    double fractionalSeconds{};

    void normalize() noexcept {
        if (!std::isfinite(fractionalSeconds)) {
            fractionalSeconds = 0.0;
            return;
        }
        const double whole = std::floor(fractionalSeconds);
        if (whole != 0.0) {
            if (whole > static_cast<double>(std::numeric_limits<std::int64_t>::max())) {
                wholeSeconds = std::numeric_limits<std::int64_t>::max();
                fractionalSeconds = 0.0;
                return;
            }
            if (whole < static_cast<double>(std::numeric_limits<std::int64_t>::min())) {
                wholeSeconds = std::numeric_limits<std::int64_t>::min();
                fractionalSeconds = 0.0;
                return;
            }
            wholeSeconds += static_cast<std::int64_t>(whole);
            fractionalSeconds -= whole;
        }
        if (fractionalSeconds < 0.0) {
            --wholeSeconds;
            fractionalSeconds += 1.0;
        }
    }

    void advance(double seconds) noexcept {
        if (!std::isfinite(seconds) || seconds == 0.0) return;
        const double integral = std::trunc(seconds);
        if (integral <= static_cast<double>(std::numeric_limits<std::int64_t>::max())
            && integral >= static_cast<double>(std::numeric_limits<std::int64_t>::min())) {
            wholeSeconds += static_cast<std::int64_t>(integral);
            fractionalSeconds += seconds - integral;
            normalize();
        }
    }

    [[nodiscard]] long double secondsFromEpoch() const noexcept {
        return static_cast<long double>(wholeSeconds)
            + static_cast<long double>(fractionalSeconds);
    }
};

struct CelestialClockConfig {
    // Major-body symplectic/Verlet work remains on a bounded fixed step. 60 s is small enough for
    // an Earth/Moon-like hierarchy while still being inexpensive compared with render/terrain work.
    double fixedStepSeconds{60.0};
    double timeScale{1.0};
    std::size_t maxSubstepsPerFrame{4096U};
};

// Converts wall/render delta into deterministic fixed astronomical substeps. Excess accumulated
// time is never silently discarded: if a frame hits the CPU budget, the remainder stays queued for
// later frames. This directly replaces the unsafe pattern of passing a huge time-warped dt to one
// orbital step or clamping a call to 60 s and losing the remainder.
class CelestialSimulationClock final {
public:
    explicit CelestialSimulationClock(CelestialClockConfig config = {}) noexcept
        : config_(config) {
        sanitizeConfig();
    }

    void setConfig(CelestialClockConfig config) noexcept {
        config_ = config;
        sanitizeConfig();
    }

    [[nodiscard]] const CelestialClockConfig& config() const noexcept { return config_; }
    [[nodiscard]] const AstroTime& time() const noexcept { return time_; }
    [[nodiscard]] double pendingSeconds() const noexcept { return pendingSeconds_; }
    [[nodiscard]] double interpolationAlpha() const noexcept {
        return std::clamp(pendingSeconds_ / config_.fixedStepSeconds, 0.0, 1.0);
    }

    void setTimeScale(double timeScale) noexcept {
        if (std::isfinite(timeScale) && timeScale >= 0.0) config_.timeScale = timeScale;
    }

    void reset(AstroTime time = {}) noexcept {
        time.normalize();
        time_ = time;
        pendingSeconds_ = 0.0;
    }

    template <typename StepFn>
    std::size_t advance(double wallDeltaSeconds, StepFn&& stepFn) {
        if (!std::isfinite(wallDeltaSeconds) || wallDeltaSeconds <= 0.0
            || config_.timeScale <= 0.0) {
            return 0U;
        }

        const double scaled = wallDeltaSeconds * config_.timeScale;
        if (!std::isfinite(scaled) || scaled <= 0.0) return 0U;
        pendingSeconds_ += scaled;

        std::size_t steps = 0U;
        while (pendingSeconds_ + 1.0e-12 >= config_.fixedStepSeconds
            && steps < config_.maxSubstepsPerFrame) {
            stepFn(config_.fixedStepSeconds);
            pendingSeconds_ -= config_.fixedStepSeconds;
            if (pendingSeconds_ < 0.0 && pendingSeconds_ > -1.0e-9) pendingSeconds_ = 0.0;
            time_.advance(config_.fixedStepSeconds);
            ++steps;
        }
        return steps;
    }

private:
    void sanitizeConfig() noexcept {
        if (!std::isfinite(config_.fixedStepSeconds) || config_.fixedStepSeconds <= 0.0) {
            config_.fixedStepSeconds = 60.0;
        }
        if (!std::isfinite(config_.timeScale) || config_.timeScale < 0.0) config_.timeScale = 1.0;
        config_.maxSubstepsPerFrame = std::max<std::size_t>(1U, config_.maxSubstepsPerFrame);
    }

    CelestialClockConfig config_{};
    AstroTime time_{};
    double pendingSeconds_{};
};

} // namespace vf
