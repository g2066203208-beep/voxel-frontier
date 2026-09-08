#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "native/src/app/Main.cpp"
CMAKE = ROOT / "native/CMakeLists.txt"


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: {label}: expected one anchor, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Mainstream benchmark instrumentation is production code behind an explicit profile flag. It
# records raw wall time (never the simulation clamp), so the same binary can be compared on CI,
# a 3060/4060-class desktop, or a future GPU without changing the benchmark implementation.
replace_once(
    MAIN,
    '#include "vf/physics/PhysicsWorld.hpp"\n',
    '#include "vf/physics/PhysicsWorld.hpp"\n#include "vf/perf/PerformanceBenchmark.hpp"\n',
    "include benchmark helper",
)

replace_once(
    MAIN,
    '        vf::SdlPlatform platform{"Voxel Frontier — Earthlike Planet + Ocean", 1600, 900};\n',
    '''        const bool mainstreamPerfProfile = [] {
            const char* value = std::getenv("VF_PERF_PROFILE");
            return value != nullptr && std::string_view{value} == "mainstream_1080p";
        }();
        // August-2026 Steam mainstream baseline: 1080p, 6 CPU cores, 16 GiB system RAM,
        // RTX 3060/4060-class discrete GPU. CI may run the same profile on Lavapipe, but its FPS is
        // explicitly labelled software Vulkan and is never reported as a discrete-GPU result.
        vf::SdlPlatform platform{
            "Voxel Frontier — Earthlike Planet + Ocean",
            mainstreamPerfProfile ? 1920 : 1600,
            mainstreamPerfProfile ? 1080 : 900};
''',
    "select deterministic mainstream 1080p window",
)

# Preserve angular geometry quality when the benchmark grows 900p -> 1080p. SSE scales with viewport
# height, therefore the target pixel error scales by 1080/900=1.2 instead of silently increasing
# terrain detail and invalidating A/B comparisons.
replace_once(
    MAIN,
    '''            lodConfig.viewportHeightPixels = 900.0;
            lodConfig.targetScreenErrorPixels = buildAltitude < 25000.0 ? 3.4
                : (buildAltitude < 150000.0 ? 4.8 : 7.2);
''',
    '''            lodConfig.viewportHeightPixels = mainstreamPerfProfile ? 1080.0 : 900.0;
            lodConfig.targetScreenErrorPixels = buildAltitude < 25000.0
                ? (mainstreamPerfProfile ? 4.08 : 3.4)
                : (buildAltitude < 150000.0
                    ? (mainstreamPerfProfile ? 5.76 : 4.8)
                    : (mainstreamPerfProfile ? 8.64 : 7.2));
''',
    "preserve angular terrain quality at 1080p",
)

# Runtime celestial diagnostics are test-only I/O. Thirty frames guarantees the software-Vulkan
# benchmark emits a sample without changing normal gameplay behavior (the entire block remains
# guarded by VF_RUNTIME_DIAGNOSTICS).
replace_once(
    MAIN,
    '                if ((++celestialDiagFrame % 120U) == 0U) {\n',
    '                if ((++celestialDiagFrame % 30U) == 0U) {\n',
    "make test-only celestial telemetry observable on software Vulkan",
)

replace_once(
    MAIN,
    '''        double dynamicSceneAccumulator = 1.0;
        constexpr double kDynamicSceneCadenceSeconds = 0.10;

        while (platform.pumpEvents()) {
''',
    '''        double dynamicSceneAccumulator = 1.0;
        constexpr double kDynamicSceneCadenceSeconds = 0.10;
        vf::PerformanceBenchmark performanceBenchmark{{
            mainstreamPerfProfile,
            2.0,
            6.0,
            60.0,
            40U,
            "mainstream_1080p"}};
        if (mainstreamPerfProfile) {
            std::cout << "R24 BENCHMARK_BEGIN profile=mainstream_1080p resolution=1920x1080"
                      << " cpu_core_limit=6 memory_budget_gib=16 target_fps=60\\n";
        }

        while (platform.pumpEvents()) {
''',
    "initialize mainstream frame benchmark",
)

replace_once(
    MAIN,
    '''            const auto renderStarted = Clock::now();
            renderer.drawFrame(viewProjection, cameraSurface, renderEnvironment);
            diagnosticsMaxRenderMilliseconds = std::max(
                diagnosticsMaxRenderMilliseconds,
                std::chrono::duration<double, std::milli>(Clock::now() - renderStarted).count());

''',
    '''            const auto renderStarted = Clock::now();
            renderer.drawFrame(viewProjection, cameraSurface, renderEnvironment);
            const double renderWallMilliseconds = std::chrono::duration<double, std::milli>(
                Clock::now() - renderStarted).count();
            diagnosticsMaxRenderMilliseconds = std::max(
                diagnosticsMaxRenderMilliseconds, renderWallMilliseconds);

            performanceBenchmark.recordFrame(
                rawFrameSeconds,
                renderWallMilliseconds,
                renderer.triangleCount(),
                renderer.dynamicTriangleCount(),
                terrainBuildInFlight);
            if (performanceBenchmark.complete()) {
                const auto [benchmarkWidth, benchmarkHeight] = platform.drawableSize();
                std::cout << performanceBenchmark.formatSummary(
                    renderer.gpuName(),
                    static_cast<std::uint32_t>(std::max(0, benchmarkWidth)),
                    static_cast<std::uint32_t>(std::max(0, benchmarkHeight)),
                    6U,
                    16U) << '\\n';
                break;
            }

''',
    "record raw wall-clock benchmark frames and auto-exit",
)

# Compile a deterministic statistics contract into the normal native suite.
replace_once(
    CMAKE,
    '''    if(VF_BUILD_RUNTIME)
        add_executable(vf_shader_contract_tests tests/ShaderContractTests.cpp "${VF_SHADER_HEADER}")
''',
    '''    add_executable(vf_performance_benchmark_tests tests/PerformanceBenchmarkTests.cpp)
    target_link_libraries(vf_performance_benchmark_tests PRIVATE vf_engine)
    add_test(NAME vf_performance_benchmark_tests COMMAND vf_performance_benchmark_tests)

    if(VF_BUILD_RUNTIME)
        add_executable(vf_shader_contract_tests tests/ShaderContractTests.cpp "${VF_SHADER_HEADER}")
''',
    "register performance benchmark statistics test",
)

print("R24 mainstream performance foundation materialized")
