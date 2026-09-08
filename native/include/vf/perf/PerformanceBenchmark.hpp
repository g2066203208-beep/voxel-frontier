#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <iomanip>
#include <limits>
#include <numeric>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

namespace vf {

struct PerformanceBenchmarkConfig {
    bool enabled{};
    double warmupSeconds{2.0};
    double sampleSeconds{6.0};
    double targetFps{60.0};
    std::size_t minimumSampleFrames{40U};
    std::string profileName{"mainstream_1080p"};
};

struct PerformanceBenchmarkSummary {
    bool valid{};
    std::string profileName{};
    std::size_t sampleFrames{};
    double sampleSeconds{};
    double averageFps{};
    double onePercentLowFps{};
    double frameMeanMs{};
    double frameP50Ms{};
    double frameP95Ms{};
    double frameP99Ms{};
    double frameMaxMs{};
    double renderMeanMs{};
    double renderP95Ms{};
    double renderMaxMs{};
    double streamingBusyPercent{};
    std::uint64_t staticTrianglesMax{};
    std::uint64_t dynamicTrianglesMax{};
};

class PerformanceBenchmark final {
public:
    explicit PerformanceBenchmark(PerformanceBenchmarkConfig config = {})
        : config_(std::move(config)) {
        if (!std::isfinite(config_.warmupSeconds) || config_.warmupSeconds < 0.0)
            config_.warmupSeconds = 2.0;
        if (!std::isfinite(config_.sampleSeconds) || config_.sampleSeconds <= 0.0)
            config_.sampleSeconds = 6.0;
        if (!std::isfinite(config_.targetFps) || config_.targetFps <= 0.0)
            config_.targetFps = 60.0;
        config_.minimumSampleFrames = std::max<std::size_t>(1U, config_.minimumSampleFrames);
    }

    [[nodiscard]] bool enabled() const noexcept { return config_.enabled; }
    [[nodiscard]] bool complete() const noexcept {
        return config_.enabled
            && warmupElapsedSeconds_ + 1.0e-12 >= config_.warmupSeconds
            && sampleElapsedSeconds_ + 1.0e-12 >= config_.sampleSeconds
            && frameMilliseconds_.size() >= config_.minimumSampleFrames;
    }

    void recordFrame(
        double wallSeconds,
        double renderMilliseconds,
        std::uint64_t staticTriangles,
        std::uint64_t dynamicTriangles,
        bool streamingBusy) {
        if (!config_.enabled || !std::isfinite(wallSeconds) || wallSeconds <= 0.0) return;
        if (warmupElapsedSeconds_ + 1.0e-12 < config_.warmupSeconds) {
            warmupElapsedSeconds_ += wallSeconds;
            return;
        }

        const double frameMs = wallSeconds * 1000.0;
        frameMilliseconds_.push_back(frameMs);
        renderMilliseconds_.push_back(
            std::isfinite(renderMilliseconds) ? std::max(0.0, renderMilliseconds) : 0.0);
        sampleElapsedSeconds_ += wallSeconds;
        if (streamingBusy) ++streamingBusyFrames_;
        staticTrianglesMax_ = std::max(staticTrianglesMax_, staticTriangles);
        dynamicTrianglesMax_ = std::max(dynamicTrianglesMax_, dynamicTriangles);
    }

    [[nodiscard]] PerformanceBenchmarkSummary summary() const {
        PerformanceBenchmarkSummary result{};
        result.profileName = config_.profileName;
        result.sampleFrames = frameMilliseconds_.size();
        result.sampleSeconds = sampleElapsedSeconds_;
        result.staticTrianglesMax = staticTrianglesMax_;
        result.dynamicTrianglesMax = dynamicTrianglesMax_;
        if (frameMilliseconds_.empty() || sampleElapsedSeconds_ <= 0.0) return result;

        result.valid = frameMilliseconds_.size() >= config_.minimumSampleFrames;
        result.averageFps = static_cast<double>(frameMilliseconds_.size()) / sampleElapsedSeconds_;
        result.frameMeanMs = mean(frameMilliseconds_);
        result.frameP50Ms = percentile(frameMilliseconds_, 0.50);
        result.frameP95Ms = percentile(frameMilliseconds_, 0.95);
        result.frameP99Ms = percentile(frameMilliseconds_, 0.99);
        result.frameMaxMs = *std::max_element(frameMilliseconds_.begin(), frameMilliseconds_.end());
        result.onePercentLowFps = result.frameP99Ms > 1.0e-9 ? 1000.0 / result.frameP99Ms : 0.0;
        result.renderMeanMs = mean(renderMilliseconds_);
        result.renderP95Ms = percentile(renderMilliseconds_, 0.95);
        result.renderMaxMs = renderMilliseconds_.empty()
            ? 0.0 : *std::max_element(renderMilliseconds_.begin(), renderMilliseconds_.end());
        result.streamingBusyPercent = 100.0 * static_cast<double>(streamingBusyFrames_)
            / static_cast<double>(frameMilliseconds_.size());
        return result;
    }

    [[nodiscard]] std::string formatSummary(
        std::string_view gpuName,
        std::uint32_t width,
        std::uint32_t height,
        std::size_t cpuCoreLimit,
        std::size_t memoryBudgetGiB) const {
        const PerformanceBenchmarkSummary s = summary();
        std::ostringstream out;
        out << std::fixed << std::setprecision(3)
            << "R24 BENCHMARK profile=" << s.profileName
            << " resolution=" << width << 'x' << height
            << " gpu=\"" << gpuName << "\""
            << " cpu_core_limit=" << cpuCoreLimit
            << " memory_budget_gib=" << memoryBudgetGiB
            << " target_fps=" << config_.targetFps
            << " frames=" << s.sampleFrames
            << " seconds=" << s.sampleSeconds
            << " avg_fps=" << s.averageFps
            << " one_percent_low_fps=" << s.onePercentLowFps
            << " frame_mean_ms=" << s.frameMeanMs
            << " p50_ms=" << s.frameP50Ms
            << " p95_ms=" << s.frameP95Ms
            << " p99_ms=" << s.frameP99Ms
            << " max_ms=" << s.frameMaxMs
            << " render_mean_ms=" << s.renderMeanMs
            << " render_p95_ms=" << s.renderP95Ms
            << " render_max_ms=" << s.renderMaxMs
            << " streaming_busy_pct=" << s.streamingBusyPercent
            << " static_tris_max=" << s.staticTrianglesMax
            << " dynamic_tris_max=" << s.dynamicTrianglesMax
            << " valid=" << (s.valid ? 1 : 0);
        return out.str();
    }

private:
    [[nodiscard]] static double mean(const std::vector<double>& values) {
        if (values.empty()) return 0.0;
        return std::accumulate(values.begin(), values.end(), 0.0)
            / static_cast<double>(values.size());
    }

    [[nodiscard]] static double percentile(std::vector<double> values, double q) {
        if (values.empty()) return 0.0;
        std::sort(values.begin(), values.end());
        const double position = std::clamp(q, 0.0, 1.0)
            * static_cast<double>(values.size() - 1U);
        const std::size_t lower = static_cast<std::size_t>(std::floor(position));
        const std::size_t upper = static_cast<std::size_t>(std::ceil(position));
        if (lower == upper) return values[lower];
        const double t = position - static_cast<double>(lower);
        return values[lower] * (1.0 - t) + values[upper] * t;
    }

    PerformanceBenchmarkConfig config_{};
    double warmupElapsedSeconds_{};
    double sampleElapsedSeconds_{};
    std::vector<double> frameMilliseconds_{};
    std::vector<double> renderMilliseconds_{};
    std::size_t streamingBusyFrames_{};
    std::uint64_t staticTrianglesMax_{};
    std::uint64_t dynamicTrianglesMax_{};
};

} // namespace vf
