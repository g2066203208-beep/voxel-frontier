#!/usr/bin/env python3
"""Inject a renderer-free engine-core benchmark path into Main.cpp.

The purpose is to measure the real ALL-OFF baseline: SDL/window event pumping plus the main loop
clock only. No VulkanRenderer is constructed, and no camera, planet, terrain, hydrology, physics,
celestial, weather, dynamic-scene, UI, or render/present work is initialized or scheduled.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "native/src/app/Main.cpp"

text = MAIN.read_text(encoding="utf-8")
marker = "R24_ENGINE_CORE_NO_RENDERER_V1"
if marker in text:
    print("engine-core baseline already materialized")
    raise SystemExit(0)

old = '''        vf::SdlPlatform platform{
            "Voxel Frontier — Earthlike Planet + Ocean",
            mainstreamPerfProfile ? 1920 : 1600,
            mainstreamPerfProfile ? 1080 : 900};
        vf::VulkanRenderer renderer{platform.window()};'''

new = '''        vf::SdlPlatform platform{
            "Voxel Frontier — Earthlike Planet + Ocean",
            mainstreamPerfProfile ? 1920 : 1600,
            mainstreamPerfProfile ? 1080 : 900};

        // R24_ENGINE_CORE_NO_RENDERER_V1
        // True ALL-OFF benchmark. Return before VulkanRenderer construction and before any world,
        // camera, terrain, hydrology, physics, celestial, weather, dynamic-scene or UI setup.
        // The loop intentionally retains SDL event pumping because that is irreducible application
        // shell work in the shipping executable. Rendering is uncapped; 120 FPS is only the minimum
        // release acceptance line, never a frame-rate cap.
        const bool engineCoreOnly = [] {
            const char* value = std::getenv("VF_ENGINE_CORE_ONLY");
            return value != nullptr && std::string_view{value} == "1";
        }();
        if (engineCoreOnly) {
            using CoreClock = std::chrono::steady_clock;
            vf::PerformanceBenchmark coreBenchmark{{
                true,
                0.75,
                2.0,
                120.0,
                200U,
                "engine_core_no_renderer"}};
            auto previousCore = CoreClock::now();
            while (platform.pumpEvents()) {
                const auto nowCore = CoreClock::now();
                const double wallSeconds = std::max(
                    1.0e-9,
                    std::chrono::duration<double>(nowCore - previousCore).count());
                previousCore = nowCore;
                coreBenchmark.recordFrame(wallSeconds, 0.0, 0U, 0U, false);
                if (coreBenchmark.complete()) {
                    const auto [benchmarkWidth, benchmarkHeight] = platform.drawableSize();
                    std::cout << "R24 ENGINE_CORE renderer=0 present=0 camera=0 terrain=0"
                              << " physics=0 celestial=0 weather=0 ui=0\\n";
                    std::cout << coreBenchmark.formatSummary(
                        "NO_VULKAN_RENDERER",
                        static_cast<std::uint32_t>(std::max(0, benchmarkWidth)),
                        static_cast<std::uint32_t>(std::max(0, benchmarkHeight)),
                        6U,
                        16U) << '\\n';
                    return 0;
                }
            }
            return 0;
        }

        vf::VulkanRenderer renderer{platform.window()};'''

count = text.count(old)
if count != 1:
    raise SystemExit(f"renderer construction anchor: expected 1 match, got {count}")

MAIN.write_text(text.replace(old, new, 1), encoding="utf-8")
print("R24 renderer-free engine-core benchmark materialized")
