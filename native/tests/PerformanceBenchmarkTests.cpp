#include "vf/perf/PerformanceBenchmark.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "R24 PERFORMANCE BENCHMARK TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void requireNear(double actual, double expected, double tolerance, std::string_view message) {
    if (std::abs(actual - expected) > tolerance) fail(message);
}

} // namespace

int main() {
    vf::PerformanceBenchmark benchmark{{true, 0.5, 1.0, 60.0, 50U, "mainstream_1080p"}};

    // 0.5 s deterministic warm-up at 100 FPS: none of these may leak into the sample.
    for (int i = 0; i < 50; ++i)
        benchmark.recordFrame(0.010, 6.0, 300000U, 0U, true);
    require(!benchmark.complete(), "warm-up frames must not complete the sample window");

    // One second steady-state at 100 FPS. Mark one quarter of frames as streaming busy.
    for (int i = 0; i < 100; ++i)
        benchmark.recordFrame(0.010, 6.0 + static_cast<double>(i % 3), 350000U, 1200U, (i % 4) == 0);

    require(benchmark.complete(), "steady-state sample must complete after configured duration");
    const vf::PerformanceBenchmarkSummary summary = benchmark.summary();
    require(summary.valid, "complete sample must be valid");
    require(summary.sampleFrames == 100U, "warm-up frames must be excluded from sample count");
    requireNear(summary.averageFps, 100.0, 1.0e-9, "average FPS must use wall time");
    requireNear(summary.frameP50Ms, 10.0, 1.0e-9, "P50 must be deterministic");
    requireNear(summary.frameP99Ms, 10.0, 1.0e-9, "P99 must be deterministic");
    requireNear(summary.onePercentLowFps, 100.0, 1.0e-9, "1% low must derive from P99 frame time");
    requireNear(summary.streamingBusyPercent, 25.0, 1.0e-9, "streaming busy percentage must count sampled frames only");
    require(summary.staticTrianglesMax == 350000U && summary.dynamicTrianglesMax == 1200U,
        "benchmark must preserve worst-case triangle counts");

    const std::string text = benchmark.formatSummary("Test GPU", 1920U, 1080U, 6U, 16U);
    require(text.find("R24 BENCHMARK profile=mainstream_1080p") != std::string::npos,
        "machine-readable summary prefix must remain stable");
    require(text.find("resolution=1920x1080") != std::string::npos,
        "benchmark must report exact output resolution");
    require(text.find("cpu_core_limit=6") != std::string::npos,
        "mainstream CPU limit must be explicit");
    require(text.find("memory_budget_gib=16") != std::string::npos,
        "mainstream memory budget must be explicit");

    std::cout << "R24 performance benchmark tests passed avg_fps=" << summary.averageFps
              << " p99_ms=" << summary.frameP99Ms
              << " one_percent_low_fps=" << summary.onePercentLowFps << '\n';
    return 0;
}
