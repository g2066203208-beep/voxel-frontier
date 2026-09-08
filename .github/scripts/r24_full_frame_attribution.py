#!/usr/bin/env python3
from pathlib import Path

MARKER = "R24_FULL_FRAME_ATTRIBUTION_V1"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing anchor: {label}")
    return text.replace(old, new, 1)


main_path = Path("native/src/app/Main.cpp")
main = main_path.read_text(encoding="utf-8")
if MARKER not in main:
    main = replace_once(
        main,
        "        while (platform.pumpEvents()) {\n"
        "            const auto now = Clock::now();",
        "        // R24_FULL_FRAME_ATTRIBUTION_V1: low-overhead wall-clock attribution.\n"
        "        struct R24CpuStageTelemetry {\n"
        "            std::uint64_t frames{};\n"
        "            double celestial{}, camera{}, physics{}, streaming{}, dynamicScene{}, prep{}, renderer{}, frame{};\n"
        "            double maxFrame{};\n"
        "        } r24CpuStages;\n"
        "        const auto r24Ms = [](Clock::time_point a, Clock::time_point b) {\n"
        "            return std::chrono::duration<double, std::milli>(b - a).count();\n"
        "        };\n\n"
        "        while (platform.pumpEvents()) {\n"
        "            const auto now = Clock::now();\n"
        "            const auto r24FrameCpuStart = now;",
        "main telemetry declaration",
    )
    main = replace_once(
        main,
        "            planetaryBodies.step(dt * effectiveCelestialTimeScale);\n"
        "            if (runtimeDiagnosticsStdout) {",
        "            planetaryBodies.step(dt * effectiveCelestialTimeScale);\n"
        "            const auto r24CelestialDone = Clock::now();\n"
        "            if (runtimeDiagnosticsStdout) {",
        "celestial boundary",
    )
    main = replace_once(
        main,
        "            const bool wasFlightMode = camera.flightMode();\n"
        "            camera.update(movement, dt);\n"
        "            physics.advance(dt);",
        "            const bool wasFlightMode = camera.flightMode();\n"
        "            camera.update(movement, dt);\n"
        "            const auto r24CameraDone = Clock::now();\n"
        "            physics.advance(dt);\n"
        "            const auto r24PhysicsDone = Clock::now();",
        "camera physics boundary",
    )
    main = replace_once(
        main,
        "            const glm::dvec3 sunWorldDirection = safeNormalize(\n"
        "                currentSun->position - camera.position());",
        "            const auto r24StreamingDone = Clock::now();\n"
        "            const glm::dvec3 sunWorldDirection = safeNormalize(\n"
        "                currentSun->position - camera.position());",
        "streaming boundary",
    )
    main = replace_once(
        main,
        "            const auto [width, height] = platform.drawableSize();",
        "            const auto r24DynamicDone = Clock::now();\n"
        "            const auto [width, height] = platform.drawableSize();",
        "dynamic boundary",
    )
    main = replace_once(
        main,
        "            renderEnvironment.dynamicShadowCasters = shadowContactCapture;\n\n"
        "            const auto renderStarted = Clock::now();",
        "            renderEnvironment.dynamicShadowCasters = shadowContactCapture;\n"
        "            const auto r24PrepDone = Clock::now();\n\n"
        "            const auto renderStarted = Clock::now();",
        "render prep boundary",
    )
    main = replace_once(
        main,
        "            diagnosticsMaxRenderMilliseconds = std::max(\n"
        "                diagnosticsMaxRenderMilliseconds, renderWallMilliseconds);\n\n"
        "            performanceBenchmark.recordFrame(",
        "            diagnosticsMaxRenderMilliseconds = std::max(\n"
        "                diagnosticsMaxRenderMilliseconds, renderWallMilliseconds);\n"
        "            const auto r24RenderDone = Clock::now();\n"
        "            r24CpuStages.frames += 1U;\n"
        "            r24CpuStages.celestial += r24Ms(r24FrameCpuStart, r24CelestialDone);\n"
        "            r24CpuStages.camera += r24Ms(r24CelestialDone, r24CameraDone);\n"
        "            r24CpuStages.physics += r24Ms(r24CameraDone, r24PhysicsDone);\n"
        "            r24CpuStages.streaming += r24Ms(r24PhysicsDone, r24StreamingDone);\n"
        "            r24CpuStages.dynamicScene += r24Ms(r24StreamingDone, r24DynamicDone);\n"
        "            r24CpuStages.prep += r24Ms(r24DynamicDone, r24PrepDone);\n"
        "            r24CpuStages.renderer += r24Ms(r24PrepDone, r24RenderDone);\n"
        "            const double r24WholeFrame = r24Ms(r24FrameCpuStart, r24RenderDone);\n"
        "            r24CpuStages.frame += r24WholeFrame;\n"
        "            r24CpuStages.maxFrame = std::max(r24CpuStages.maxFrame, r24WholeFrame);\n"
        "            if ((r24CpuStages.frames % 16U) == 0U) {\n"
        "                const double inv = 1.0 / static_cast<double>(r24CpuStages.frames);\n"
        "                std::cout << \"R24 CPU stage_ms samples=\" << r24CpuStages.frames\n"
        "                          << \" celestial_mean=\" << r24CpuStages.celestial * inv\n"
        "                          << \" camera_mean=\" << r24CpuStages.camera * inv\n"
        "                          << \" physics_mean=\" << r24CpuStages.physics * inv\n"
        "                          << \" streaming_mean=\" << r24CpuStages.streaming * inv\n"
        "                          << \" dynamic_mean=\" << r24CpuStages.dynamicScene * inv\n"
        "                          << \" prep_mean=\" << r24CpuStages.prep * inv\n"
        "                          << \" renderer_mean=\" << r24CpuStages.renderer * inv\n"
        "                          << \" frame_cpu_mean=\" << r24CpuStages.frame * inv\n"
        "                          << \" frame_cpu_max=\" << r24CpuStages.maxFrame << '\\n';\n"
        "            }\n\n"
        "            performanceBenchmark.recordFrame(",
        "main telemetry accumulation",
    )
    main_path.write_text(main, encoding="utf-8")

renderer_path = Path("native/src/render/VulkanRenderer.cpp")
renderer = renderer_path.read_text(encoding="utf-8")
if MARKER not in renderer:
    renderer = replace_once(
        renderer,
        "#include <array>\n#include <cmath>",
        "#include <array>\n#include <chrono>\n#include <cmath>",
        "renderer chrono include",
    )
    renderer = replace_once(
        renderer,
        "    std::uint32_t imageCount = capabilities.minImageCount + 1U;\n"
        "    if (capabilities.maxImageCount > 0U) imageCount = std::min(imageCount, capabilities.maxImageCount);",
        "    std::uint32_t imageCount = capabilities.minImageCount + 1U;\n"
        "    if (capabilities.maxImageCount > 0U) imageCount = std::min(imageCount, capabilities.maxImageCount);\n"
        "    SDL_Log(\"R24 WSI present_mode=%s requested_images=%u extent=%ux%u\",\n"
        "        present == VK_PRESENT_MODE_MAILBOX_KHR ? \"MAILBOX\" :\n"
        "        (present == VK_PRESENT_MODE_IMMEDIATE_KHR ? \"IMMEDIATE\" : \"FIFO\"),\n"
        "        imageCount, extent.width, extent.height);",
        "present mode log",
    )
    renderer = replace_once(
        renderer,
        "    if (resizeRequested_) recreateSwapchain();\n"
        "    if (swapchain_ == VK_NULL_HANDLE || opaquePipeline_ == VK_NULL_HANDLE) return;\n\n"
        "    const std::uint32_t frame = frameIndex_ % kFramesInFlight;\n"
        "    VkResult result = vkWaitForFences(device_, 1, &inFlight_[frame], VK_TRUE, UINT64_MAX);",
        "    if (resizeRequested_) recreateSwapchain();\n"
        "    if (swapchain_ == VK_NULL_HANDLE || opaquePipeline_ == VK_NULL_HANDLE) return;\n\n"
        "    // R24_FULL_FRAME_ATTRIBUTION_V1: expose CPU/WSI back-pressure hidden by GPU pass timestamps.\n"
        "    using R24RenderClock = std::chrono::steady_clock;\n"
        "    const auto r24RenderCpu0 = R24RenderClock::now();\n"
        "    const std::uint32_t frame = frameIndex_ % kFramesInFlight;\n"
        "    VkResult result = vkWaitForFences(device_, 1, &inFlight_[frame], VK_TRUE, UINT64_MAX);\n"
        "    const auto r24RenderCpu1 = R24RenderClock::now();",
        "renderer fence boundary",
    )
    renderer = replace_once(
        renderer,
        "    uploadDynamicMeshForFrame(frame);\n"
        "    auto& staticMesh = staticMeshes_[staticUploadScheduler_.residentSlot()];",
        "    uploadDynamicMeshForFrame(frame);\n"
        "    const auto r24RenderCpu2 = R24RenderClock::now();\n"
        "    auto& staticMesh = staticMeshes_[staticUploadScheduler_.residentSlot()];",
        "renderer upload boundary",
    )
    renderer = replace_once(
        renderer,
        "    if (result != VK_SUCCESS && result != VK_SUBOPTIMAL_KHR)\n"
        "        fail(\"vkAcquireNextImageKHR failed\", result);\n"
        "    vkResetFences(device_, 1, &inFlight_[frame]);",
        "    if (result != VK_SUCCESS && result != VK_SUBOPTIMAL_KHR)\n"
        "        fail(\"vkAcquireNextImageKHR failed\", result);\n"
        "    const auto r24RenderCpu3 = R24RenderClock::now();\n"
        "    vkResetFences(device_, 1, &inFlight_[frame]);",
        "renderer acquire boundary",
    )
    renderer = replace_once(
        renderer,
        "    result = vkEndCommandBuffer(command);\n"
        "    if (result != VK_SUCCESS) fail(\"vkEndCommandBuffer failed\", result);",
        "    result = vkEndCommandBuffer(command);\n"
        "    if (result != VK_SUCCESS) fail(\"vkEndCommandBuffer failed\", result);\n"
        "    const auto r24RenderCpu4 = R24RenderClock::now();",
        "renderer record boundary",
    )
    renderer = replace_once(
        renderer,
        "    result = vkQueueSubmit2(graphicsQueue_, 1, &submit, inFlight_[frame]);\n"
        "    if (result != VK_SUCCESS) fail(\"vkQueueSubmit2 failed\", result);\n"
        "    if (gpuTimestampsSupported_) timestampQueryWritten_[frame] = true;",
        "    result = vkQueueSubmit2(graphicsQueue_, 1, &submit, inFlight_[frame]);\n"
        "    if (result != VK_SUCCESS) fail(\"vkQueueSubmit2 failed\", result);\n"
        "    const auto r24RenderCpu5 = R24RenderClock::now();\n"
        "    if (gpuTimestampsSupported_) timestampQueryWritten_[frame] = true;",
        "renderer submit boundary",
    )
    renderer = replace_once(
        renderer,
        "    const VkResult presentResult = vkQueuePresentKHR(graphicsQueue_, &present);\n"
        "    imageInitialized_[imageIndex] = true;\n"
        "    ++frameIndex_;",
        "    const VkResult presentResult = vkQueuePresentKHR(graphicsQueue_, &present);\n"
        "    const auto r24RenderCpu6 = R24RenderClock::now();\n"
        "    imageInitialized_[imageIndex] = true;\n"
        "    ++frameIndex_;\n"
        "    struct R24RendererCpuTelemetry {\n"
        "        std::uint64_t frames{};\n"
        "        double fence{}, upload{}, acquire{}, record{}, submit{}, present{}, total{};\n"
        "        double maxFence{}, maxAcquire{}, maxPresent{}, maxTotal{};\n"
        "    };\n"
        "    static R24RendererCpuTelemetry r24{};\n"
        "    const auto ms = [](auto a, auto b) {\n"
        "        return std::chrono::duration<double, std::milli>(b - a).count();\n"
        "    };\n"
        "    const double fenceMs = ms(r24RenderCpu0, r24RenderCpu1);\n"
        "    const double uploadMs = ms(r24RenderCpu1, r24RenderCpu2);\n"
        "    const double acquireMs = ms(r24RenderCpu2, r24RenderCpu3);\n"
        "    const double recordMs = ms(r24RenderCpu3, r24RenderCpu4);\n"
        "    const double submitMs = ms(r24RenderCpu4, r24RenderCpu5);\n"
        "    const double presentMs = ms(r24RenderCpu5, r24RenderCpu6);\n"
        "    const double totalMs = ms(r24RenderCpu0, r24RenderCpu6);\n"
        "    ++r24.frames;\n"
        "    r24.fence += fenceMs; r24.upload += uploadMs; r24.acquire += acquireMs;\n"
        "    r24.record += recordMs; r24.submit += submitMs; r24.present += presentMs; r24.total += totalMs;\n"
        "    r24.maxFence = std::max(r24.maxFence, fenceMs);\n"
        "    r24.maxAcquire = std::max(r24.maxAcquire, acquireMs);\n"
        "    r24.maxPresent = std::max(r24.maxPresent, presentMs);\n"
        "    r24.maxTotal = std::max(r24.maxTotal, totalMs);\n"
        "    if ((r24.frames % 16U) == 0U) {\n"
        "        const double inv = 1.0 / static_cast<double>(r24.frames);\n"
        "        SDL_Log(\"R24 RENDER_CPU stage_ms samples=%llu fence_mean=%.3f upload_query_mean=%.3f acquire_mean=%.3f record_mean=%.3f submit_mean=%.3f present_mean=%.3f total_mean=%.3f fence_max=%.3f acquire_max=%.3f present_max=%.3f total_max=%.3f\",\n"
        "            static_cast<unsigned long long>(r24.frames),\n"
        "            r24.fence * inv, r24.upload * inv, r24.acquire * inv, r24.record * inv,\n"
        "            r24.submit * inv, r24.present * inv, r24.total * inv,\n"
        "            r24.maxFence, r24.maxAcquire, r24.maxPresent, r24.maxTotal);\n"
        "    }",
        "renderer present accumulation",
    )
    renderer_path.write_text(renderer, encoding="utf-8")

print("R24 full-frame attribution materialized")
