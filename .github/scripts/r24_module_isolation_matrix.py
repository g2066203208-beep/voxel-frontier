#!/usr/bin/env python3
"""Materialize strict R24 runtime-module isolation for performance attribution.

This patch intentionally keeps the mathematical planet/surface authority alive while making
expensive simulation and render clients independently switchable. It is designed for CI A/B
profiling, but the resulting feature gates are production runtime controls too.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "native/src/app/Main.cpp"
HEADER = ROOT / "native/include/vf/app/RuntimeFeatureFlags.hpp"
RENDER_H = ROOT / "native/include/vf/render/VulkanRenderer.hpp"
RENDER_CPP = ROOT / "native/src/render/VulkanRenderer.cpp"
SHADER = ROOT / "native/shaders/planet.slang"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


HEADER.write_text(r'''#pragma once

#include <cstdlib>
#include <iostream>
#include <string_view>

namespace vf {

// R24_MODULE_ISOLATION_MATRIX_V1
// Strict runtime subsystem gates. A disabled module must stop scheduling its own expensive work;
// mathematical planet/surface authority remains independent so coordinates and test poses do not
// change merely because a visual client is disabled.
struct RuntimeFeatureFlags {
    bool geometryRender{true};
    bool terrainRender{true};
    bool terrainStreaming{true};
    bool waterRender{true};
    bool ecologyRender{true};
    bool dynamicSceneRender{true};
    bool skyRender{true};
    bool shadowRender{true};
    bool physicsSimulation{true};
    bool celestialSimulation{true};
    bool weatherSimulation{true};
    bool uiRender{true};

    [[nodiscard]] static bool readFlag(const char* name, bool fallback = true) noexcept {
        const char* value = std::getenv(name);
        if (value == nullptr || *value == '\0') return fallback;
        const std::string_view text{value};
        if (text == "0" || text == "false" || text == "FALSE" || text == "off" || text == "OFF")
            return false;
        if (text == "1" || text == "true" || text == "TRUE" || text == "on" || text == "ON")
            return true;
        return fallback;
    }

    [[nodiscard]] static RuntimeFeatureFlags fromEnvironment() noexcept {
        RuntimeFeatureFlags flags{};
        flags.geometryRender = readFlag("VF_MODULE_GEOMETRY", true);
        flags.terrainRender = readFlag("VF_MODULE_TERRAIN", true);
        flags.terrainStreaming = readFlag("VF_MODULE_TERRAIN_STREAMING", true);
        flags.waterRender = readFlag("VF_MODULE_WATER", true);
        flags.ecologyRender = readFlag("VF_MODULE_ECOLOGY", true);
        flags.dynamicSceneRender = readFlag("VF_MODULE_DYNAMIC_SCENE", true);
        flags.skyRender = readFlag("VF_MODULE_SKY", true);
        flags.shadowRender = readFlag("VF_MODULE_SHADOWS", true);
        flags.physicsSimulation = readFlag("VF_MODULE_PHYSICS", true);
        flags.celestialSimulation = readFlag("VF_MODULE_CELESTIAL", true);
        flags.weatherSimulation = readFlag("VF_MODULE_WEATHER", true);
        flags.uiRender = readFlag("VF_MODULE_UI", true);
        return flags;
    }

    // Initial static terrain is a render concern. Streaming only controls later rebuild scheduling.
    [[nodiscard]] bool terrainStreamingWorkEnabled() const noexcept {
        return terrainRender && terrainStreaming;
    }

    void print(std::ostream& stream = std::cout) const {
        stream << "R24 MODULES"
               << " geometry=" << (geometryRender ? 1 : 0)
               << " terrain=" << (terrainRender ? 1 : 0)
               << " terrain_streaming=" << (terrainStreaming ? 1 : 0)
               << " water=" << (waterRender ? 1 : 0)
               << " ecology=" << (ecologyRender ? 1 : 0)
               << " dynamic_scene=" << (dynamicSceneRender ? 1 : 0)
               << " sky=" << (skyRender ? 1 : 0)
               << " shadows=" << (shadowRender ? 1 : 0)
               << " physics=" << (physicsSimulation ? 1 : 0)
               << " celestial=" << (celestialSimulation ? 1 : 0)
               << " weather=" << (weatherSimulation ? 1 : 0)
               << " ui=" << (uiRender ? 1 : 0)
               << '\n';
    }
};

} // namespace vf
''', encoding="utf-8")

# Renderer-facing pass switches. They are intentionally frame data rather than global renderer
# state, keeping command recording deterministic and making future hot-toggle support straightforward.
text = RENDER_H.read_text(encoding="utf-8")
if "R24_MODULE_ISOLATION_MATRIX_V1" not in text:
    text = replace_once(
        text,
        "    bool dynamicShadowCasters{false};\n};",
        "    bool dynamicShadowCasters{false};\n"
        "    // R24_MODULE_ISOLATION_MATRIX_V1: independent render-pass gates.\n"
        "    bool geometryEnabled{true};\n"
        "    bool transparentEnabled{true};\n"
        "    bool skyEnabled{true};\n"
        "    bool shadowsEnabled{true};\n"
        "    bool hudEnabled{true};\n"
        "};",
        "RenderFrameEnvironment gates")
    RENDER_H.write_text(text, encoding="utf-8")

# Shadow sampling must be bypassable before touching the shadow texture when the pass is disabled.
text = SHADER.read_text(encoding="utf-8")
if "R24_SHADOW_MODULE_BYPASS_V1" not in text:
    text = replace_once(
        text,
        "float shadowVisibility(float4 lightClip, float noL)\n{\n    if (lightClip.w <= 0.0) return 1.0;",
        "float shadowVisibility(float4 lightClip, float noL)\n{\n"
        "    // R24_SHADOW_MODULE_BYPASS_V1: negative texel size means the entire shadow client is off.\n"
        "    // Return before any texture access so the renderer can skip shadow rasterization.\n"
        "    if (gScene.groundAmbientShadowTexel.w < 0.0) return 1.0;\n"
        "    if (lightClip.w <= 0.0) return 1.0;",
        "shader shadow bypass")
    SHADER.write_text(text, encoding="utf-8")

text = MAIN.read_text(encoding="utf-8")
if "R24_MODULE_ISOLATION_MATRIX_V1" not in text:
    # Simulation gates.
    text = replace_once(
        text,
        "            planetaryBodies.step(dt * effectiveCelestialTimeScale);",
        "            // R24_MODULE_ISOLATION_MATRIX_V1: a frozen celestial module leaves the epoch state intact.\n"
        "            if (runtimeFeatures.celestialSimulation)\n"
        "                planetaryBodies.step(dt * effectiveCelestialTimeScale);",
        "celestial gate")
    text = replace_once(
        text,
        "            physics.advance(dt);",
        "            if (runtimeFeatures.physicsSimulation) physics.advance(dt);",
        "physics advance gate")
    text = replace_once(
        text,
        "            if (camera.physicsFrameBodyId() == asterId) {",
        "            if (runtimeFeatures.physicsSimulation && camera.physicsFrameBodyId() == asterId) {",
        "character physics gate")

    # Initial terrain is independent from later streaming.
    text = replace_once(
        text,
        "        if (runtimeFeatures.terrainWorkEnabled()) {",
        "        if (runtimeFeatures.terrainRender) {",
        "initial terrain gate")
    text = text.replace(
        "runtimeFeatures.terrainWorkEnabled()",
        "runtimeFeatures.terrainStreamingWorkEnabled()")

    # Ecology and water are build-time clients of the terrain mesh, not mandatory terrain content.
    text = replace_once(
        text,
        "            if (buildAltitude < 30000.0) {\n                appendMesh(renderMesh, vf::buildProceduralEcology(\n                    planet, centerUp, surfaceFrame, {}, &buildSurface));\n            }\n\n            vf::PlanetMesh oceanProxy{};\n            vf::appendOceanSurfaceProxy(\n                oceanProxy, {}, planet.radius + planet.seaLevelElevationMeters - 1.5, 96U);\n            for (auto& vertex : oceanProxy.vertices) {\n                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));\n                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));\n                vertex.material.w = -20.0F;\n            }\n            appendMesh(renderMesh, oceanProxy);",
        "            if (runtimeFeatures.ecologyRender && buildAltitude < 30000.0) {\n"
        "                appendMesh(renderMesh, vf::buildProceduralEcology(\n"
        "                    planet, centerUp, surfaceFrame, {}, &buildSurface));\n"
        "            }\n\n"
        "            if (runtimeFeatures.waterRender) {\n"
        "                vf::PlanetMesh oceanProxy{};\n"
        "                vf::appendOceanSurfaceProxy(\n"
        "                    oceanProxy, {}, planet.radius + planet.seaLevelElevationMeters - 1.5, 96U);\n"
        "                for (auto& vertex : oceanProxy.vertices) {\n"
        "                    vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));\n"
        "                    vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));\n"
        "                    vertex.material.w = -20.0F;\n"
        "                }\n"
        "                appendMesh(renderMesh, oceanProxy);\n"
        "            }",
        "ecology/water gates")

    # Dynamic celestial visual meshes are independent from celestial integration itself.
    text = replace_once(
        text,
        "            const bool refreshDynamicScene = shadowContactCapture\n                || dynamicSceneAccumulator >= kDynamicSceneCadenceSeconds;",
        "            const bool refreshDynamicScene = runtimeFeatures.dynamicSceneRender\n"
        "                && (shadowContactCapture || dynamicSceneAccumulator >= kDynamicSceneCadenceSeconds);",
        "dynamic scene refresh gate")
    text = replace_once(
        text,
        "            if (refreshDynamicScene) {\n                renderer.setDynamicMesh(dynamicMesh);\n                dynamicSceneAccumulator = 0.0;\n            }",
        "            if (refreshDynamicScene) {\n"
        "                renderer.setDynamicMesh(dynamicMesh);\n"
        "                dynamicSceneAccumulator = 0.0;\n"
        "            } else if (!runtimeFeatures.dynamicSceneRender) {\n"
        "                renderer.clearDynamicMesh();\n"
        "            }",
        "dynamic scene clear gate")

    # Weather/climate sample can be removed while retaining a deterministic standard-atmosphere
    # lighting density for render modules that remain enabled.
    text = replace_once(
        text,
        "            const vf::PlanetClimateSample climateSample = climateGrid.sample(\n                safeNormalize(cameraPlanet, patchUp), std::max(0.0, camera.altitude()));\n            const double densityRatio = std::clamp(climateSample.densityKgPerM3 / 1.225, 0.0, 1.2);",
        "            const double densityRatio = runtimeFeatures.weatherSimulation\n"
        "                ? std::clamp(climateGrid.sample(\n"
        "                    safeNormalize(cameraPlanet, patchUp),\n"
        "                    std::max(0.0, camera.altitude())).densityKgPerM3 / 1.225, 0.0, 1.2)\n"
        "                : 1.0;",
        "weather sample gate")

    # Frame render-pass gates.
    text = replace_once(
        text,
        "            renderEnvironment.dynamicShadowCasters = shadowContactCapture;",
        "            renderEnvironment.dynamicShadowCasters = shadowContactCapture\n"
        "                && runtimeFeatures.dynamicSceneRender && runtimeFeatures.shadowRender;\n"
        "            renderEnvironment.geometryEnabled = runtimeFeatures.geometryRender;\n"
        "            renderEnvironment.transparentEnabled = runtimeFeatures.geometryRender\n"
        "                && runtimeFeatures.waterRender;\n"
        "            renderEnvironment.skyEnabled = runtimeFeatures.skyRender;\n"
        "            renderEnvironment.shadowsEnabled = runtimeFeatures.shadowRender;\n"
        "            renderEnvironment.hudEnabled = runtimeFeatures.uiRender;",
        "render environment gates")
    MAIN.write_text(text, encoding="utf-8")

text = RENDER_CPP.read_text(encoding="utf-8")
if "R24_MODULE_ISOLATION_MATRIX_V1" not in text:
    # Scene uniform signals disabled shadow sampling with a negative texel size.
    text = replace_once(
        text,
        "    scene.groundAmbientShadowTexel = glm::vec4(\n        glm::max(environment.groundAmbient, glm::vec3{0.0F}),\n        1.0F / static_cast<float>(kShadowMapSize));",
        "    scene.groundAmbientShadowTexel = glm::vec4(\n"
        "        glm::max(environment.groundAmbient, glm::vec3{0.0F}),\n"
        "        environment.shadowsEnabled\n"
        "            ? 1.0F / static_cast<float>(kShadowMapSize) : -1.0F);",
        "shadow uniform switch")

    # Keep the depth image in a legal sampled layout when the shadow client is disabled, but skip
    # the render pass and all caster rasterization. The tiny layout barrier belongs to renderer base.
    start = text.index("    VkRenderingAttachmentInfo shadowDepthAttachment{};")
    end_marker = "    VkImageMemoryBarrier2 colorBarrier{};"
    end = text.index(end_marker, start)
    block = text[start:end]
    if "environment.shadowsEnabled" not in block:
        indented = "\n".join("        " + line if line else line for line in block.splitlines())
        replacement = (
            "    // R24_MODULE_ISOLATION_MATRIX_V1: shadow rasterization is a true optional client.\n"
            "    if (environment.shadowsEnabled) {\n" + indented + "\n"
            "    } else {\n"
            "        if (gpuTimestampsSupported_) {\n"
            "            vkCmdWriteTimestamp2(command, VK_PIPELINE_STAGE_2_TOP_OF_PIPE_BIT,\n"
            "                timestampQueryPools_[frame], 0U);\n"
            "        }\n"
            "        VkImageMemoryBarrier2 shadowBypass{};\n"
            "        shadowBypass.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;\n"
            "        shadowBypass.srcStageMask = VK_PIPELINE_STAGE_2_NONE;\n"
            "        shadowBypass.dstStageMask = VK_PIPELINE_STAGE_2_FRAGMENT_SHADER_BIT;\n"
            "        shadowBypass.dstAccessMask = VK_ACCESS_2_SHADER_SAMPLED_READ_BIT;\n"
            "        shadowBypass.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED;\n"
            "        shadowBypass.newLayout = VK_IMAGE_LAYOUT_DEPTH_READ_ONLY_OPTIMAL;\n"
            "        shadowBypass.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;\n"
            "        shadowBypass.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;\n"
            "        shadowBypass.image = shadowFrames_[frame].depthImage;\n"
            "        shadowBypass.subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT;\n"
            "        shadowBypass.subresourceRange.levelCount = 1;\n"
            "        shadowBypass.subresourceRange.layerCount = 1;\n"
            "        VkDependencyInfo shadowBypassDependency{};\n"
            "        shadowBypassDependency.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO;\n"
            "        shadowBypassDependency.imageMemoryBarrierCount = 1;\n"
            "        shadowBypassDependency.pImageMemoryBarriers = &shadowBypass;\n"
            "        vkCmdPipelineBarrier2(command, &shadowBypassDependency);\n"
            "        if (gpuTimestampsSupported_) {\n"
            "            vkCmdWriteTimestamp2(command, VK_PIPELINE_STAGE_2_BOTTOM_OF_PIPE_BIT,\n"
            "                timestampQueryPools_[frame], 1U);\n"
            "        }\n"
            "    }\n\n")
        text = text[:start] + replacement + text[end:]

    text = replace_once(
        text,
        "    drawScenePass(opaquePipeline_, false);",
        "    if (environment.geometryEnabled) drawScenePass(opaquePipeline_, false);",
        "opaque pass gate")

    sky_start = text.index("    vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, skyPipeline_);")
    sky_end = text.index("    if (gpuTimestampsSupported_) {\n        vkCmdWriteTimestamp2(\n            command, VK_PIPELINE_STAGE_2_BOTTOM_OF_PIPE_BIT, timestampQueryPools_[frame], 5U);", sky_start)
    sky_block = text[sky_start:sky_end]
    if "environment.skyEnabled" not in sky_block:
        sky_indented = "\n".join("        " + line if line else line for line in sky_block.splitlines())
        text = text[:sky_start] + "    if (environment.skyEnabled) {\n" + sky_indented + "\n    }\n" + text[sky_end:]

    text = replace_once(
        text,
        "    drawScenePass(transparentPipeline_, true);",
        "    if (environment.transparentEnabled) drawScenePass(transparentPipeline_, true);",
        "transparent pass gate")

    hud_start = text.index("    vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, hudPipeline_);")
    hud_end = text.index("    vkCmdEndRendering(command);", hud_start)
    hud_block = text[hud_start:hud_end]
    if "environment.hudEnabled" not in hud_block:
        hud_indented = "\n".join("        " + line if line else line for line in hud_block.splitlines())
        text = text[:hud_start] + "    if (environment.hudEnabled) {\n" + hud_indented + "\n    }\n" + text[hud_end:]

    RENDER_CPP.write_text(text, encoding="utf-8")

print("R24 module isolation matrix materialized")
