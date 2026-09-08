#!/usr/bin/env python3
"""Upgrade the R24 low-res screen SkyView into a cached view-independent spherical LUT.

This script is intentionally a second-stage materializer. Run r24_hillaire_skyview_lut.py first.
The old path still ray-marches a screen-space 192x108 LUT every frame. Here the LUT is
parameterized by (cos(view, sun), cos(view, local-up)), so camera rotation becomes a cheap lookup
and the expensive atmosphere is refreshed only when altitude / sun zenith / atmosphere change.
It also removes full-screen procedural solar work and cuts star hashing to one hash per night pixel.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / "native/include/vf/render/VulkanRenderer.hpp"
CPP = ROOT / "native/src/render/VulkanRenderer.cpp"
SHADER = ROOT / "native/shaders/planet.slang"


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"{label}: already materialized")
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{label}: materialized")


# The atmosphere is very low frequency. 128x72 keeps horizon gradients clean at 1080p while
# quartering the old 192x108 refresh work. Since refreshes are cached, this is mostly a spike guard.
replace_once(
    HEADER,
    """    static constexpr std::uint32_t kSkyViewLutWidth = 192;
    static constexpr std::uint32_t kSkyViewLutHeight = 108;
""",
    """    static constexpr std::uint32_t kSkyViewLutWidth = 128;
    static constexpr std::uint32_t kSkyViewLutHeight = 72;
""",
    "cached LUT dimensions",
)

replace_once(
    HEADER,
    """    struct SkyViewFrameResources {
        VkImage image{VK_NULL_HANDLE};
        VkDeviceMemory memory{VK_NULL_HANDLE};
        VkImageView view{VK_NULL_HANDLE};
        bool initialized{};
    };
""",
    """    struct SkyViewFrameResources {
        VkImage image{VK_NULL_HANDLE};
        VkDeviceMemory memory{VK_NULL_HANDLE};
        VkImageView view{VK_NULL_HANDLE};
        bool initialized{};
        // Cache identity. The LUT is independent of camera yaw/pitch; only these slowly-changing
        // spherical-atmosphere quantities invalidate it.
        float cameraRadius{-1.0F};
        float sunZenithCos{2.0F};
        float planetRadius{-1.0F};
        float atmosphereHeight{-1.0F};
        float scaleHeight{-1.0F};
        float mieScale{-1.0F};
        std::uint64_t refreshCount{};
    };
""",
    "SkyView cache identity",
)

cpp = CPP.read_text(encoding="utf-8")
start_marker = "    drawScenePass(opaquePipeline_, false);\n    vkCmdEndRendering(command);\n"
end_marker = "    if (gpuTimestampsSupported_) {\n        vkCmdWriteTimestamp2(\n            command, VK_PIPELINE_STAGE_2_BOTTOM_OF_PIPE_BIT, timestampQueryPools_[frame], 5U);"
if "R24_CACHED_SPHERICAL_SKYVIEW_V2" not in cpp:
    start = cpp.find(start_marker)
    if start < 0:
        raise SystemExit("cached SkyView: materialized Hillaire draw block start not found")
    end = cpp.find(end_marker, start)
    if end < 0:
        raise SystemExit("cached SkyView: sky timing end marker not found")
    new_block = r'''    drawScenePass(opaquePipeline_, false);
    if (gpuTimestampsSupported_) {
        vkCmdWriteTimestamp2(
            command, VK_PIPELINE_STAGE_2_BOTTOM_OF_PIPE_BIT, timestampQueryPools_[frame], 3U);
        vkCmdWriteTimestamp2(
            command, VK_PIPELINE_STAGE_2_TOP_OF_PIPE_BIT, timestampQueryPools_[frame], 4U);
    }

    PushConstants skyPush{};
    skyPush.matrix = glm::inverse(viewProjection);
    skyPush.data0 = glm::vec4(glm::vec3(cameraPosition - environment.planetCenter), 1.0F);
    skyPush.data1 = glm::vec4(
        safeNormalizeFloat(environment.sunDirectionToLight),
        std::clamp(environment.sunAngularRadiusRadians, 0.0001F, 1.45F));
    skyPush.data2 = {
        static_cast<float>(environment.planetRadius),
        static_cast<float>(environment.atmosphereHeight),
        static_cast<float>(environment.atmosphereScaleHeight),
        std::max(environment.mieScale, 0.0F)};
    const glm::vec3 sunRadiance = glm::max(environment.sunLinearColor, glm::vec3{0.0F})
        * std::max(environment.sunIntensity, 0.0F);
    skyPush.data3 = {
        std::max(environment.exposure, 0.01F),
        sunRadiance.r,
        sunRadiance.g,
        sunRadiance.b};

    // R24_CACHED_SPHERICAL_SKYVIEW_V2
    // The LUT axes are cos(view,sun) and cos(view,local-up), not screen UV. Camera yaw/pitch no
    // longer invalidates atmosphere. Each in-flight resource is populated once, then refreshed
    // only after a perceptible altitude / solar-zenith / atmosphere change.
    auto& skyView = skyViewFrames_[frame];
    const glm::vec3 cameraPlanetF = glm::vec3(skyPush.data0);
    const float cameraRadiusF = glm::length(cameraPlanetF);
    const glm::vec3 localUp = safeNormalizeFloat(cameraPlanetF);
    const glm::vec3 sunDirection = safeNormalizeFloat(environment.sunDirectionToLight);
    const float sunZenithCos = glm::dot(localUp, sunDirection);
    const float planetRadiusF = static_cast<float>(environment.planetRadius);
    const float atmosphereHeightF = static_cast<float>(environment.atmosphereHeight);
    const float scaleHeightF = static_cast<float>(environment.atmosphereScaleHeight);
    const float mieScaleF = std::max(environment.mieScale, 0.0F);
    constexpr float kAltitudeRefreshMeters = 180.0F;
    constexpr float kSunZenithCosRefresh = 0.0025F;
    const bool skyViewNeedsRefresh = !skyView.initialized
        || std::abs(cameraRadiusF - skyView.cameraRadius) > kAltitudeRefreshMeters
        || std::abs(sunZenithCos - skyView.sunZenithCos) > kSunZenithCosRefresh
        || std::abs(planetRadiusF - skyView.planetRadius) > 1.0F
        || std::abs(atmosphereHeightF - skyView.atmosphereHeight) > 1.0F
        || std::abs(scaleHeightF - skyView.scaleHeight) > 0.5F
        || std::abs(mieScaleF - skyView.mieScale) > 0.002F;

    if (skyViewNeedsRefresh) {
        vkCmdEndRendering(command);

        VkImageMemoryBarrier2 skyViewToAttachment{};
        skyViewToAttachment.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;
        skyViewToAttachment.srcStageMask = skyView.initialized
            ? VK_PIPELINE_STAGE_2_FRAGMENT_SHADER_BIT : VK_PIPELINE_STAGE_2_NONE;
        skyViewToAttachment.srcAccessMask = skyView.initialized
            ? VK_ACCESS_2_SHADER_SAMPLED_READ_BIT : VK_ACCESS_2_NONE;
        skyViewToAttachment.dstStageMask = VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT;
        skyViewToAttachment.dstAccessMask = VK_ACCESS_2_COLOR_ATTACHMENT_WRITE_BIT;
        skyViewToAttachment.oldLayout = skyView.initialized
            ? VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL : VK_IMAGE_LAYOUT_UNDEFINED;
        skyViewToAttachment.newLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
        skyViewToAttachment.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        skyViewToAttachment.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        skyViewToAttachment.image = skyView.image;
        skyViewToAttachment.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        skyViewToAttachment.subresourceRange.levelCount = 1U;
        skyViewToAttachment.subresourceRange.layerCount = 1U;
        VkDependencyInfo skyViewDependency{};
        skyViewDependency.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO;
        skyViewDependency.imageMemoryBarrierCount = 1U;
        skyViewDependency.pImageMemoryBarriers = &skyViewToAttachment;
        vkCmdPipelineBarrier2(command, &skyViewDependency);

        VkRenderingAttachmentInfo skyViewAttachment{};
        skyViewAttachment.sType = VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO;
        skyViewAttachment.imageView = skyView.view;
        skyViewAttachment.imageLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
        skyViewAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
        skyViewAttachment.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
        VkRenderingInfo skyViewRendering{};
        skyViewRendering.sType = VK_STRUCTURE_TYPE_RENDERING_INFO;
        skyViewRendering.renderArea.extent = {kSkyViewLutWidth, kSkyViewLutHeight};
        skyViewRendering.layerCount = 1U;
        skyViewRendering.colorAttachmentCount = 1U;
        skyViewRendering.pColorAttachments = &skyViewAttachment;
        vkCmdBeginRendering(command, &skyViewRendering);
        VkViewport skyViewViewport{
            0.0F, 0.0F,
            static_cast<float>(kSkyViewLutWidth),
            static_cast<float>(kSkyViewLutHeight),
            0.0F, 1.0F};
        VkRect2D skyViewScissor{{0, 0}, {kSkyViewLutWidth, kSkyViewLutHeight}};
        vkCmdSetViewport(command, 0, 1, &skyViewViewport);
        vkCmdSetScissor(command, 0, 1, &skyViewScissor);
        vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, skyViewPipeline_);
        vkCmdBindDescriptorSets(
            command, VK_PIPELINE_BIND_POINT_GRAPHICS, fullscreenPipelineLayout_, 0, 1,
            &shadowFrames_[frame].descriptorSet, 0, nullptr);
        vkCmdPushConstants(
            command, fullscreenPipelineLayout_,
            VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
            0, sizeof(skyPush), &skyPush);
        vkCmdDraw(command, 3, 1, 0, 0);
        vkCmdEndRendering(command);

        VkImageMemoryBarrier2 skyViewToRead{};
        skyViewToRead.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;
        skyViewToRead.srcStageMask = VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT;
        skyViewToRead.srcAccessMask = VK_ACCESS_2_COLOR_ATTACHMENT_WRITE_BIT;
        skyViewToRead.dstStageMask = VK_PIPELINE_STAGE_2_FRAGMENT_SHADER_BIT;
        skyViewToRead.dstAccessMask = VK_ACCESS_2_SHADER_SAMPLED_READ_BIT;
        skyViewToRead.oldLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
        skyViewToRead.newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
        skyViewToRead.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        skyViewToRead.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        skyViewToRead.image = skyView.image;
        skyViewToRead.subresourceRange = skyViewToAttachment.subresourceRange;
        skyViewDependency.pImageMemoryBarriers = &skyViewToRead;
        vkCmdPipelineBarrier2(command, &skyViewDependency);
        skyView.initialized = true;
        skyView.cameraRadius = cameraRadiusF;
        skyView.sunZenithCos = sunZenithCos;
        skyView.planetRadius = planetRadiusF;
        skyView.atmosphereHeight = atmosphereHeightF;
        skyView.scaleHeight = scaleHeightF;
        skyView.mieScale = mieScaleF;
        ++skyView.refreshCount;

        // We broke dynamic rendering only on refresh frames. Restore reverse-Z depth and color.
        colorAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_LOAD;
        depthAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_LOAD;
        vkCmdBeginRendering(command, &rendering);
        vkCmdSetViewport(command, 0, 1, &mainViewport);
        vkCmdSetScissor(command, 0, 1, &mainScissor);
        vkCmdBindDescriptorSets(
            command, VK_PIPELINE_BIND_POINT_GRAPHICS, fullscreenPipelineLayout_, 0, 1,
            &shadowFrames_[frame].descriptorSet, 0, nullptr);
    }

    // Steady-state sky is now one bilinear LUT fetch + cheap high-frequency masks. No atmosphere
    // ray integration and no render-pass break occur on camera-rotation-only frames.
    vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, skyPipeline_);
    vkCmdPushConstants(
        command, fullscreenPipelineLayout_,
        VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
        0, sizeof(skyPush), &skyPush);
    vkCmdDraw(command, 3, 1, 0, 0);
'''
    CPP.write_text(cpp[:start] + new_block + cpp[end:], encoding="utf-8")
    print("cached spherical SkyView draw scheduling: materialized")
else:
    print("cached spherical SkyView draw scheduling: already materialized")


shader = SHADER.read_text(encoding="utf-8")
if "R24_CACHED_SPHERICAL_SKYVIEW_V2" not in shader:
    # Make night stars substantially cheaper before replacing the SkyView evaluator/compositor.
    stars_start = shader.find("float3 proceduralStars(float3 ray)\n{")
    sun_start = shader.find("float3 proceduralSun(float3 ray, float3 sunDir, bool hitsGround)", stars_start)
    if stars_start < 0 or sun_start < 0:
        raise SystemExit("cached SkyView: procedural star/sun anchors not found; run Hillaire materializer first")
    cheap_stars = r'''float3 proceduralStars(float3 ray)
{
    // One hash, no full-screen high-power exponentials. Brightness and tint are derived from the
    // same deterministic seed; the branch in skyFragmentMain skips this entirely in daylight.
    float3 cell = floor(ray * 1280.0);
    float h = hash31(cell);
    float star = saturate((h - 0.99855) * 689.6552);
    star *= star;
    float temperature = frac(h * 19.371 + cell.x * 0.00017);
    float3 tint = lerp(float3(1.0, 0.72, 0.52), float3(0.66, 0.81, 1.0), temperature);
    return tint * star * (0.62 + 2.15 * star);
}

'''
    shader = shader[:stars_start] + cheap_stars + shader[sun_start:]

    sky_start = shader.find("float3 proceduralSun(float3 ray, float3 sunDir, bool hitsGround)")
    hud_start = shader.find('\n[shader("fragment")]\nfloat4 hudFragmentMain', sky_start)
    if sky_start < 0 or hud_start < 0:
        raise SystemExit("cached SkyView: generated sky shader section not found")
    cached_sky = r'''// R24_CACHED_SPHERICAL_SKYVIEW_V2
float3 proceduralSun(float3 ray, float3 sunDir, bool hitsGround)
{
    if (hitsGround) return float3(0.0, 0.0, 0.0);
    float sunRadius = clamp(abs(gPush.data1.w), 0.0001, 1.45);
    float cosToSun = dot(ray, sunDir);
    // Small-angle metric needs only one dot and one sqrt. All solar detail is skipped for virtually
    // the whole screen instead of constructing a basis + FBM for every sky pixel.
    float angularRatio = sqrt(max(2.0 * (1.0 - cosToSun), 0.0)) / max(sunRadius, 1.0e-5);
    if (angularRatio >= 1.85) return float3(0.0, 0.0, 0.0);

    float corona = exp(-max(angularRatio - 1.0, 0.0) * 5.2)
        * smoothstep(1.85, 0.96, angularRatio);
    float3 result = float3(0.74, 0.18, 0.022) * corona * 0.34;
    if (angularRatio <= 1.0)
    {
        float solarZ = sqrt(max(0.0, 1.0 - angularRatio * angularRatio));
        float limb = 0.56 + 0.62 * sqrt(saturate(solarZ));
        float core = 1.0 - angularRatio * angularRatio;
        float3 solarColor = lerp(float3(1.55, 0.43, 0.055), float3(2.35, 0.86, 0.16), core);
        result += solarColor * limb * max(float3(0.62, 0.52, 0.42), gPush.data3.yzw * 0.72);
    }
    return result;
}

[shader("fragment")]
float4 skyViewFragmentMain(FullscreenOutput input) : SV_Target
{
    // View-independent 2D spherical parameterization. X = cos(view,sun), Y = cos(view,up).
    // A spherically symmetric atmosphere is fully symmetric under azimuth reflection, so these two
    // cosines plus the cached camera radius / solar zenith are sufficient for this single-scatter LUT.
    float groundRadius = max(gPush.data2.x, 1.0);
    float atmosphereRadius = groundRadius + max(gPush.data2.y, 1.0);
    float scaleHeight = max(gPush.data2.z, 100.0);
    float mieScale = max(gPush.data2.w, 0.0);
    float cameraRadius = max(length(gPush.data0.xyz), groundRadius + 0.01);
    float3 actualUp = normalize(gPush.data0.xyz);
    float3 actualSun = normalize(gPush.data1.xyz);
    float sunMu = clamp(dot(actualUp, actualSun), -1.0, 1.0);
    float sunSin = sqrt(max(1.0 - sunMu * sunMu, 1.0e-8));
    float3 cameraPlanet = float3(0.0, cameraRadius, 0.0);
    float3 sunDir = normalize(float3(sunSin, sunMu, 0.0));

    float nu = input.uv.x * 2.0 - 1.0;
    float mu = input.uv.y * 2.0 - 1.0;
    float horizontal = sqrt(max(1.0 - mu * mu, 0.0));
    float rayX = sunSin > 1.0e-4 ? (nu - mu * sunMu) / sunSin : horizontal;
    rayX = clamp(rayX, -horizontal, horizontal);
    float rayZ = sqrt(max(horizontal * horizontal - rayX * rayX, 0.0));
    float3 ray = normalize(float3(rayX, mu, rayZ));

    float atmoNear, atmoFar;
    bool hitsAtmosphere = raySphere(cameraPlanet, ray, atmosphereRadius, atmoNear, atmoFar);
    float groundNear, groundFar;
    bool hitsGround = raySphere(cameraPlanet, ray, groundRadius, groundNear, groundFar)
        && groundFar > 0.0 && groundNear > 0.0;
    float3 spaceBase = float3(0.00035, 0.00045, 0.00075);
    if (!hitsAtmosphere)
        return float4(spaceBase, 1.0);

    float startT = max(atmoNear, 0.0);
    float endT = max(atmoFar, startT);
    if (hitsGround) endT = min(endT, groundNear);
    if (endT <= startT)
        return float4(spaceBase, hitsGround ? -1.0 : 1.0);

    const float3 betaR = float3(5.802e-6, 13.558e-6, 33.100e-6);
    float betaM = 21.0e-6 * mieScale;
    float viewSunCos = dot(ray, sunDir);
    float rayleighPhase = 3.0 * (1.0 + viewSunCos * viewSunCos) / (16.0 * PI);
    float g = 0.76;
    float phaseBase = max(1.0 + g * g - 2.0 * g * viewSunCos, 1.0e-4);
    float miePhase = (1.0 - g * g) / max(4.0 * PI * phaseBase * sqrt(phaseBase), 1.0e-5);

    float segment = (endT - startT) * 0.25;
    float opticalView = 0.0;
    float3 scattering = 0.0;
    [unroll]
    for (int i = 0; i < 4; ++i)
    {
        float t = startT + (i + 0.5) * segment;
        float3 samplePoint = cameraPlanet + ray * t;
        float density = densityAtRadius(length(samplePoint), groundRadius, scaleHeight);
        float sunDepth = sunOpticalDepth(samplePoint, sunDir, atmosphereRadius, groundRadius, scaleHeight);
        if (sunDepth > 1.0e7) continue;
        opticalView += density * segment;
        float3 extinction = (betaR + betaM) * (opticalView + sunDepth);
        float3 lightTransmittance = exp(-extinction);
        float3 source = (betaR * rayleighPhase + betaM * miePhase) * density;
        scattering += source * lightTransmittance * segment * gPush.data3.yzw;
    }

    float3 transmittance = exp(-(betaR + betaM) * opticalView);
    float3 color = scattering * 17.0;
    color += hitsGround
        ? float3(0.008, 0.009, 0.007) * transmittance
        : spaceBase * transmittance;
    float localDensity = densityAtRadius(cameraRadius, groundRadius, scaleHeight);
    float styleWeight = saturate(localDensity * 0.38);
    color = lerp(color, stylizedSkyPalette(ray, sunDir), styleWeight);
    float transmittanceLuma = dot(transmittance, float3(0.2126, 0.7152, 0.0722));
    return float4(color, hitsGround ? -transmittanceLuma : transmittanceLuma);
}

[shader("fragment")]
float4 skyFragmentMain(FullscreenOutput input) : SV_Target
{
    float3 ray = reconstructWorldRay(input.uv);
    float3 cameraPlanet = gPush.data0.xyz;
    float3 sunDir = normalize(gPush.data1.xyz);
    float3 localUp = normalize(cameraPlanet);
    float viewSunCos = clamp(dot(ray, sunDir), -1.0, 1.0);
    float viewUpCos = clamp(dot(ray, localUp), -1.0, 1.0);
    float2 skyUv = float2(viewSunCos, viewUpCos) * 0.5 + 0.5;
    float4 skyView = gSkyViewLut.SampleLevel(gSkyViewSampler, skyUv, 0.0);
    bool hitsGround = skyView.a < 0.0;
    float transmission = saturate(abs(skyView.a));

    float3 highFrequency = float3(0.0, 0.0, 0.0);
    if (!hitsGround)
    {
        // Stars are invisible through a bright daytime atmosphere; skip all hash work there.
        float skyLuma = dot(skyView.rgb, float3(0.2126, 0.7152, 0.0722));
        if (transmission > 0.12 && skyLuma < 0.055)
            highFrequency += proceduralStars(ray);
        highFrequency += proceduralSun(ray, sunDir, false);
    }
    float exposure = max(gPush.data3.x, 0.01);
    float3 color = skyView.rgb + highFrequency * transmission;
    return float4(acesFitted(stylizedWarmCoolGrade(color) * exposure), 1.0);
}
'''
    SHADER.write_text(shader[:sky_start] + cached_sky + shader[hud_start:], encoding="utf-8")
    print("cached spherical SkyView shader + cheap high-frequency sky: materialized")
else:
    print("cached spherical SkyView shader: already materialized")

# Static source contracts: these are deliberately source-level because the actual SPIR-V contract
# test is still run by CTest after this materializer.
for needle, path in [
    ("R24_CACHED_SPHERICAL_SKYVIEW_V2", CPP),
    ("R24_CACHED_SPHERICAL_SKYVIEW_V2", SHADER),
    ("kSkyViewLutWidth = 128", HEADER),
    ("skyViewNeedsRefresh", CPP),
    ("viewSunCos", SHADER),
    ("viewUpCos", SHADER),
]:
    if needle not in path.read_text(encoding="utf-8"):
        raise SystemExit(f"cached SkyView contract missing: {needle} in {path}")

print("R24 cached spherical SkyView V2 materialized")
