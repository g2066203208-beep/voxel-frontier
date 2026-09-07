#!/usr/bin/env python3
"""Materialize R24's Hillaire-inspired fast SkyView LUT path.

The expensive atmospheric view/sun integration is evaluated at 192x108, stored as linear
scattering + scalar transmittance, then bilinearly applied at display resolution. Stars and the
procedural solar disc/corona stay full resolution, so this is not whole-frame dynamic resolution.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / "native/include/vf/render/VulkanRenderer.hpp"
CPP = ROOT / "native/src/render/VulkanRenderer.cpp"
SHADER = ROOT / "native/shaders/planet.slang"
CMAKE = ROOT / "native/CMakeLists.txt"
EMBED = ROOT / "native/cmake/EmbedShaders.cmake"
TEST = ROOT / "native/tests/ShaderContractTests.cpp"


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


# ---------------- Renderer header ----------------
replace_once(
    HEADER,
    """    static constexpr std::uint32_t kShadowMapSize = 1024;

    struct FrameMesh {
""",
    """    static constexpr std::uint32_t kShadowMapSize = 1024;
    // Epic/Hillaire-style fast sky view LUT: low-frequency atmosphere is ray-marched here while
    // stars and the solar disc remain full-resolution in the final compositor.
    static constexpr std::uint32_t kSkyViewLutWidth = 192;
    static constexpr std::uint32_t kSkyViewLutHeight = 108;

    struct FrameMesh {
""",
    "header LUT dimensions",
)

replace_once(
    HEADER,
    """    struct ShadowFrameResources {
        VkImage depthImage{VK_NULL_HANDLE};
        VkDeviceMemory depthMemory{VK_NULL_HANDLE};
        VkImageView depthView{VK_NULL_HANDLE};
        VkBuffer uniformBuffer{VK_NULL_HANDLE};
        VkDeviceMemory uniformMemory{VK_NULL_HANDLE};
        void* mappedUniform{};
        VkDescriptorSet descriptorSet{VK_NULL_HANDLE};
    };

    void createInstance();
""",
    """    struct ShadowFrameResources {
        VkImage depthImage{VK_NULL_HANDLE};
        VkDeviceMemory depthMemory{VK_NULL_HANDLE};
        VkImageView depthView{VK_NULL_HANDLE};
        VkBuffer uniformBuffer{VK_NULL_HANDLE};
        VkDeviceMemory uniformMemory{VK_NULL_HANDLE};
        void* mappedUniform{};
        VkDescriptorSet descriptorSet{VK_NULL_HANDLE};
    };

    struct SkyViewFrameResources {
        VkImage image{VK_NULL_HANDLE};
        VkDeviceMemory memory{VK_NULL_HANDLE};
        VkImageView view{VK_NULL_HANDLE};
        bool initialized{};
    };

    void createInstance();
""",
    "header LUT frame resource",
)

replace_once(
    HEADER,
    """    void createShadowResources();
    void destroyShadowResources() noexcept;
    void createDescriptorResources();
""",
    """    void createShadowResources();
    void destroyShadowResources() noexcept;
    void createSkyViewResources();
    void destroySkyViewResources() noexcept;
    void createDescriptorResources();
""",
    "header LUT lifecycle methods",
)

replace_once(
    HEADER,
    """    void createDepthImage(
        std::uint32_t width,
        std::uint32_t height,
        VkImageUsageFlags usage,
        VkImage& image,
        VkDeviceMemory& memory,
        VkImageView& view);
""",
    """    void createDepthImage(
        std::uint32_t width,
        std::uint32_t height,
        VkImageUsageFlags usage,
        VkImage& image,
        VkDeviceMemory& memory,
        VkImageView& view);
    void createColorImage(
        std::uint32_t width,
        std::uint32_t height,
        VkFormat format,
        VkImageUsageFlags usage,
        VkImage& image,
        VkDeviceMemory& memory,
        VkImageView& view);
""",
    "header color image helper",
)

replace_once(
    HEADER,
    """    VkDescriptorSetLayout sceneDescriptorSetLayout_{VK_NULL_HANDLE};
    VkDescriptorPool sceneDescriptorPool_{VK_NULL_HANDLE};
    VkSampler shadowSampler_{VK_NULL_HANDLE};
    std::array<ShadowFrameResources, kFramesInFlight> shadowFrames_{};

    VkPipelineLayout scenePipelineLayout_{VK_NULL_HANDLE};
""",
    """    VkDescriptorSetLayout sceneDescriptorSetLayout_{VK_NULL_HANDLE};
    VkDescriptorPool sceneDescriptorPool_{VK_NULL_HANDLE};
    VkSampler shadowSampler_{VK_NULL_HANDLE};
    VkSampler skyViewSampler_{VK_NULL_HANDLE};
    std::array<ShadowFrameResources, kFramesInFlight> shadowFrames_{};
    std::array<SkyViewFrameResources, kFramesInFlight> skyViewFrames_{};

    VkPipelineLayout scenePipelineLayout_{VK_NULL_HANDLE};
""",
    "header LUT descriptor resources",
)

replace_once(
    HEADER,
    """    VkPipeline shadowPipeline_{VK_NULL_HANDLE};
    VkPipeline skyPipeline_{VK_NULL_HANDLE};
    VkPipeline hudPipeline_{VK_NULL_HANDLE};
""",
    """    VkPipeline shadowPipeline_{VK_NULL_HANDLE};
    VkPipeline skyViewPipeline_{VK_NULL_HANDLE};
    VkPipeline skyPipeline_{VK_NULL_HANDLE};
    VkPipeline hudPipeline_{VK_NULL_HANDLE};
""",
    "header LUT pipeline",
)

# ---------------- C++ image/resource plumbing ----------------
create_depth_tail = """    result = vkCreateImageView(device_, &viewInfo, nullptr, &view);
    if (result != VK_SUCCESS) fail(\"vkCreateImageView(depth) failed\", result);
}

void VulkanRenderer::createMainDepthResources() {
"""
create_color = """    result = vkCreateImageView(device_, &viewInfo, nullptr, &view);
    if (result != VK_SUCCESS) fail(\"vkCreateImageView(depth) failed\", result);
}

void VulkanRenderer::createColorImage(
    std::uint32_t width,
    std::uint32_t height,
    VkFormat format,
    VkImageUsageFlags usage,
    VkImage& image,
    VkDeviceMemory& memory,
    VkImageView& view) {
    VkImageCreateInfo info{};
    info.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    info.imageType = VK_IMAGE_TYPE_2D;
    info.extent = {width, height, 1U};
    info.mipLevels = 1;
    info.arrayLayers = 1;
    info.format = format;
    info.tiling = VK_IMAGE_TILING_OPTIMAL;
    info.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    info.usage = usage;
    info.samples = VK_SAMPLE_COUNT_1_BIT;
    info.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    VkResult result = vkCreateImage(device_, &info, nullptr, &image);
    if (result != VK_SUCCESS) fail(\"vkCreateImage(color) failed\", result);
    VkMemoryRequirements requirements{};
    vkGetImageMemoryRequirements(device_, image, &requirements);
    VkMemoryAllocateInfo alloc{};
    alloc.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    alloc.allocationSize = requirements.size;
    alloc.memoryTypeIndex = findMemoryType(requirements.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    result = vkAllocateMemory(device_, &alloc, nullptr, &memory);
    if (result != VK_SUCCESS) fail(\"vkAllocateMemory(color) failed\", result);
    result = vkBindImageMemory(device_, image, memory, 0);
    if (result != VK_SUCCESS) fail(\"vkBindImageMemory(color) failed\", result);

    VkImageViewCreateInfo viewInfo{};
    viewInfo.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    viewInfo.image = image;
    viewInfo.viewType = VK_IMAGE_VIEW_TYPE_2D;
    viewInfo.format = format;
    viewInfo.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    viewInfo.subresourceRange.levelCount = 1;
    viewInfo.subresourceRange.layerCount = 1;
    result = vkCreateImageView(device_, &viewInfo, nullptr, &view);
    if (result != VK_SUCCESS) fail(\"vkCreateImageView(color) failed\", result);
}

void VulkanRenderer::createMainDepthResources() {
"""
replace_once(CPP, create_depth_tail, create_color, "color image helper")

shadow_destroy = """void VulkanRenderer::destroyShadowResources() noexcept {
    for (auto& shadow : shadowFrames_) {
        if (shadow.mappedUniform != nullptr && shadow.uniformMemory != VK_NULL_HANDLE)
            vkUnmapMemory(device_, shadow.uniformMemory);
        if (shadow.uniformBuffer != VK_NULL_HANDLE) vkDestroyBuffer(device_, shadow.uniformBuffer, nullptr);
        if (shadow.uniformMemory != VK_NULL_HANDLE) vkFreeMemory(device_, shadow.uniformMemory, nullptr);
        if (shadow.depthView != VK_NULL_HANDLE) vkDestroyImageView(device_, shadow.depthView, nullptr);
        if (shadow.depthImage != VK_NULL_HANDLE) vkDestroyImage(device_, shadow.depthImage, nullptr);
        if (shadow.depthMemory != VK_NULL_HANDLE) vkFreeMemory(device_, shadow.depthMemory, nullptr);
        shadow = {};
    }
}

void VulkanRenderer::createDescriptorResources() {
"""
shadow_plus_lut = """void VulkanRenderer::destroyShadowResources() noexcept {
    for (auto& shadow : shadowFrames_) {
        if (shadow.mappedUniform != nullptr && shadow.uniformMemory != VK_NULL_HANDLE)
            vkUnmapMemory(device_, shadow.uniformMemory);
        if (shadow.uniformBuffer != VK_NULL_HANDLE) vkDestroyBuffer(device_, shadow.uniformBuffer, nullptr);
        if (shadow.uniformMemory != VK_NULL_HANDLE) vkFreeMemory(device_, shadow.uniformMemory, nullptr);
        if (shadow.depthView != VK_NULL_HANDLE) vkDestroyImageView(device_, shadow.depthView, nullptr);
        if (shadow.depthImage != VK_NULL_HANDLE) vkDestroyImage(device_, shadow.depthImage, nullptr);
        if (shadow.depthMemory != VK_NULL_HANDLE) vkFreeMemory(device_, shadow.depthMemory, nullptr);
        shadow = {};
    }
}

void VulkanRenderer::createSkyViewResources() {
    constexpr VkFormat skyViewFormat = VK_FORMAT_R16G16B16A16_SFLOAT;
    for (auto& sky : skyViewFrames_) {
        createColorImage(
            kSkyViewLutWidth,
            kSkyViewLutHeight,
            skyViewFormat,
            VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
            sky.image,
            sky.memory,
            sky.view);
    }
}

void VulkanRenderer::destroySkyViewResources() noexcept {
    for (auto& sky : skyViewFrames_) {
        if (sky.view != VK_NULL_HANDLE) vkDestroyImageView(device_, sky.view, nullptr);
        if (sky.image != VK_NULL_HANDLE) vkDestroyImage(device_, sky.image, nullptr);
        if (sky.memory != VK_NULL_HANDLE) vkFreeMemory(device_, sky.memory, nullptr);
        sky = {};
    }
}

void VulkanRenderer::createDescriptorResources() {
"""
replace_once(CPP, shadow_destroy, shadow_plus_lut, "LUT lifecycle implementation")

replace_once(
    CPP,
    """    std::array<VkDescriptorSetLayoutBinding, 3> bindings{};
    bindings[0] = {0U, VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, 1U,
        VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
    bindings[1] = {1U, VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE, 1U, VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
    bindings[2] = {2U, VK_DESCRIPTOR_TYPE_SAMPLER, 1U, VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
""",
    """    std::array<VkDescriptorSetLayoutBinding, 5> bindings{};
    bindings[0] = {0U, VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, 1U,
        VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
    bindings[1] = {1U, VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE, 1U, VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
    bindings[2] = {2U, VK_DESCRIPTOR_TYPE_SAMPLER, 1U, VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
    bindings[3] = {3U, VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE, 1U, VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
    bindings[4] = {4U, VK_DESCRIPTOR_TYPE_SAMPLER, 1U, VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
""",
    "descriptor bindings 3/4",
)

replace_once(
    CPP,
    """    result = vkCreateSampler(device_, &sampler, nullptr, &shadowSampler_);
    if (result != VK_SUCCESS) fail(\"vkCreateSampler(shadow) failed\", result);

    createShadowResources();

    const std::array<VkDescriptorPoolSize, 3> sizes{{
        {VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, kFramesInFlight},
        {VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE, kFramesInFlight},
        {VK_DESCRIPTOR_TYPE_SAMPLER, kFramesInFlight},
    }};
""",
    """    result = vkCreateSampler(device_, &sampler, nullptr, &shadowSampler_);
    if (result != VK_SUCCESS) fail(\"vkCreateSampler(shadow) failed\", result);

    VkSamplerCreateInfo skySampler = sampler;
    skySampler.magFilter = VK_FILTER_LINEAR;
    skySampler.minFilter = VK_FILTER_LINEAR;
    skySampler.mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST;
    skySampler.addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    skySampler.addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    skySampler.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    skySampler.borderColor = VK_BORDER_COLOR_FLOAT_TRANSPARENT_BLACK;
    result = vkCreateSampler(device_, &skySampler, nullptr, &skyViewSampler_);
    if (result != VK_SUCCESS) fail(\"vkCreateSampler(sky view LUT) failed\", result);

    createShadowResources();
    createSkyViewResources();

    const std::array<VkDescriptorPoolSize, 3> sizes{{
        {VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, kFramesInFlight},
        {VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE, kFramesInFlight * 2U},
        {VK_DESCRIPTOR_TYPE_SAMPLER, kFramesInFlight * 2U},
    }};
""",
    "LUT sampler and descriptor pool",
)

replace_once(
    CPP,
    """        VkDescriptorImageInfo samplerInfo{};
        samplerInfo.sampler = shadowSampler_;
        std::array<VkWriteDescriptorSet, 3> writes{};
""",
    """        VkDescriptorImageInfo samplerInfo{};
        samplerInfo.sampler = shadowSampler_;
        VkDescriptorImageInfo skyViewInfo{};
        skyViewInfo.imageView = skyViewFrames_[i].view;
        skyViewInfo.imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
        VkDescriptorImageInfo skySamplerInfo{};
        skySamplerInfo.sampler = skyViewSampler_;
        std::array<VkWriteDescriptorSet, 5> writes{};
""",
    "LUT descriptor infos",
)

replace_once(
    CPP,
    """        writes[2].descriptorType = VK_DESCRIPTOR_TYPE_SAMPLER;
        writes[2].pImageInfo = &samplerInfo;
        vkUpdateDescriptorSets(
""",
    """        writes[2].descriptorType = VK_DESCRIPTOR_TYPE_SAMPLER;
        writes[2].pImageInfo = &samplerInfo;
        writes[3].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[3].dstSet = sets[i];
        writes[3].dstBinding = 3;
        writes[3].descriptorCount = 1;
        writes[3].descriptorType = VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE;
        writes[3].pImageInfo = &skyViewInfo;
        writes[4].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[4].dstSet = sets[i];
        writes[4].dstBinding = 4;
        writes[4].descriptorCount = 1;
        writes[4].descriptorType = VK_DESCRIPTOR_TYPE_SAMPLER;
        writes[4].pImageInfo = &skySamplerInfo;
        vkUpdateDescriptorSets(
""",
    "write LUT descriptors",
)

replace_once(
    CPP,
    """void VulkanRenderer::destroyDescriptorResources() noexcept {
    destroyShadowResources();
    if (sceneDescriptorPool_ != VK_NULL_HANDLE) vkDestroyDescriptorPool(device_, sceneDescriptorPool_, nullptr);
    sceneDescriptorPool_ = VK_NULL_HANDLE;
    if (shadowSampler_ != VK_NULL_HANDLE) vkDestroySampler(device_, shadowSampler_, nullptr);
    shadowSampler_ = VK_NULL_HANDLE;
""",
    """void VulkanRenderer::destroyDescriptorResources() noexcept {
    destroySkyViewResources();
    destroyShadowResources();
    if (sceneDescriptorPool_ != VK_NULL_HANDLE) vkDestroyDescriptorPool(device_, sceneDescriptorPool_, nullptr);
    sceneDescriptorPool_ = VK_NULL_HANDLE;
    if (skyViewSampler_ != VK_NULL_HANDLE) vkDestroySampler(device_, skyViewSampler_, nullptr);
    skyViewSampler_ = VK_NULL_HANDLE;
    if (shadowSampler_ != VK_NULL_HANDLE) vkDestroySampler(device_, shadowSampler_, nullptr);
    shadowSampler_ = VK_NULL_HANDLE;
""",
    "destroy LUT resources",
)

# ---------------- Pipelines ----------------
replace_once(
    CPP,
    """    const VkShaderModule skyFragment = createShaderModule(
        device_, shaders::kSkyFragmentSpv, shaders::kSkyFragmentSpvSize);
    const VkShaderModule hudFragment = createShaderModule(
""",
    """    const VkShaderModule skyViewFragment = createShaderModule(
        device_, shaders::kSkyViewFragmentSpv, shaders::kSkyViewFragmentSpvSize);
    const VkShaderModule skyFragment = createShaderModule(
        device_, shaders::kSkyFragmentSpv, shaders::kSkyFragmentSpvSize);
    const VkShaderModule hudFragment = createShaderModule(
""",
    "create LUT shader module",
)

replace_once(
    CPP,
    """    createColorPipeline(
        transparentPipeline_, sceneVertex, \"vertexMain\", transparentFragment, \"transparentFragmentMain\",
        &vertexInput, &transparentDepth, &alphaBlend, scenePipelineLayout_);
    createColorPipeline(
        skyPipeline_, fullscreenVertex, \"fullscreenVertexMain\", skyFragment, \"skyFragmentMain\",
        &emptyVertexInput, &skyDepth, &opaqueBlend, fullscreenPipelineLayout_);
""",
    """    createColorPipeline(
        transparentPipeline_, sceneVertex, \"vertexMain\", transparentFragment, \"transparentFragmentMain\",
        &vertexInput, &transparentDepth, &alphaBlend, scenePipelineLayout_);

    // Render the expensive atmosphere into a tiny floating-point target first. Hillaire's
    // production approach similarly evaluates sky radiance in low-resolution view LUTs instead of
    // ray marching every display pixel.
    constexpr VkFormat skyViewFormat = VK_FORMAT_R16G16B16A16_SFLOAT;
    const VkFormat* mainColorFormat = rendering.pColorAttachmentFormats;
    const VkFormat mainDepthFormat = rendering.depthAttachmentFormat;
    rendering.pColorAttachmentFormats = &skyViewFormat;
    rendering.depthAttachmentFormat = VK_FORMAT_UNDEFINED;
    createColorPipeline(
        skyViewPipeline_, fullscreenVertex, \"fullscreenVertexMain\", skyViewFragment, \"skyViewFragmentMain\",
        &emptyVertexInput, &noDepth, &opaqueBlend, fullscreenPipelineLayout_);
    rendering.pColorAttachmentFormats = mainColorFormat;
    rendering.depthAttachmentFormat = mainDepthFormat;

    createColorPipeline(
        skyPipeline_, fullscreenVertex, \"fullscreenVertexMain\", skyFragment, \"skyFragmentMain\",
        &emptyVertexInput, &skyDepth, &opaqueBlend, fullscreenPipelineLayout_);
""",
    "create LUT pipeline",
)

replace_once(
    CPP,
    """            fullscreenVertex,
            skyFragment,
            hudFragment}) {
""",
    """            fullscreenVertex,
            skyViewFragment,
            skyFragment,
            hudFragment}) {
""",
    "destroy LUT shader module",
)

replace_once(
    CPP,
    """    for (VkPipeline* pipeline : {
            &opaquePipeline_, &transparentPipeline_, &shadowPipeline_, &skyPipeline_, &hudPipeline_}) {
""",
    """    for (VkPipeline* pipeline : {
            &opaquePipeline_, &transparentPipeline_, &shadowPipeline_, &skyViewPipeline_, &skyPipeline_, &hudPipeline_}) {
""",
    "destroy LUT pipeline",
)

# Depth must survive the short offscreen LUT rendering interval so sky/transparent can resume.
replace_once(
    CPP,
    """    depthAttachment.storeOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
""",
    """    depthAttachment.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
""",
    "store depth across LUT pass",
)

# Replace the old full-resolution expensive sky draw with: end main -> low-res LUT -> barrier ->
# resume main with LOAD -> cheap full-res LUT compositor.
old_sky_block = """    drawScenePass(opaquePipeline_, false);
    if (gpuTimestampsSupported_) {
        vkCmdWriteTimestamp2(
            command, VK_PIPELINE_STAGE_2_BOTTOM_OF_PIPE_BIT, timestampQueryPools_[frame], 3U);
        vkCmdWriteTimestamp2(
            command, VK_PIPELINE_STAGE_2_TOP_OF_PIPE_BIT, timestampQueryPools_[frame], 4U);
    }
    vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, skyPipeline_);
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
    vkCmdPushConstants(
        command, fullscreenPipelineLayout_,
        VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
        0, sizeof(skyPush), &skyPush);
    vkCmdDraw(command, 3, 1, 0, 0);
"""
new_sky_block = """    drawScenePass(opaquePipeline_, false);
    vkCmdEndRendering(command);
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

    auto& skyView = skyViewFrames_[frame];
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

    // Resume the main target without clearing: reverse-Z depth from opaque terrain is preserved,
    // so the full-resolution compositor still shades only clear-depth sky pixels.
    colorAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_LOAD;
    depthAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_LOAD;
    vkCmdBeginRendering(command, &rendering);
    vkCmdSetViewport(command, 0, 1, &mainViewport);
    vkCmdSetScissor(command, 0, 1, &mainScissor);
    vkCmdBindDescriptorSets(
        command, VK_PIPELINE_BIND_POINT_GRAPHICS, fullscreenPipelineLayout_, 0, 1,
        &shadowFrames_[frame].descriptorSet, 0, nullptr);
    vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, skyPipeline_);
    vkCmdPushConstants(
        command, fullscreenPipelineLayout_,
        VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
        0, sizeof(skyPush), &skyPush);
    vkCmdDraw(command, 3, 1, 0, 0);
"""
replace_once(CPP, old_sky_block, new_sky_block, "record fast SkyView LUT pass")

# ---------------- Shader: bindings + expensive low-res evaluator + cheap compositor ----------------
replace_once(
    SHADER,
    """[[vk::binding(1, 0)]] Texture2D<float> gShadowMap;
[[vk::binding(2, 0)]] SamplerState gShadowSampler;
""",
    """[[vk::binding(1, 0)]] Texture2D<float> gShadowMap;
[[vk::binding(2, 0)]] SamplerState gShadowSampler;
[[vk::binding(3, 0)]] Texture2D<float4> gSkyViewLut;
[[vk::binding(4, 0)]] SamplerState gSkyViewSampler;
""",
    "shader LUT bindings",
)

sky_start = SHADER.read_text(encoding="utf-8").index('[shader("fragment")]\nfloat4 skyFragmentMain')
sky_end = SHADER.read_text(encoding="utf-8").index('\n[shader("fragment")]\nfloat4 hudFragmentMain', sky_start)
shader_text = SHADER.read_text(encoding="utf-8")
old_sky_shader = shader_text[sky_start:sky_end]
new_sky_shader = r'''float3 proceduralSun(float3 ray, float3 sunDir, bool hitsGround)
{
    if (hitsGround) return float3(0.0, 0.0, 0.0);
    float sunAngularRadius = clamp(abs(gPush.data1.w), 0.0001, 1.45);
    float3 helper = abs(sunDir.y) < 0.92 ? float3(0.0, 1.0, 0.0) : float3(1.0, 0.0, 0.0);
    float3 sunRight = normalize(cross(helper, sunDir));
    float3 sunUp = normalize(cross(sunDir, sunRight));
    float sinRadius = max(sin(sunAngularRadius), 1.0e-5);
    float2 solarPlane = float2(dot(ray, sunRight), dot(ray, sunUp)) / sinRadius;
    float solarR = length(solarPlane);
    float3 result = float3(0.0, 0.0, 0.0);

    if (solarR < 1.85)
    {
        float solarAngle = atan2(solarPlane.y, solarPlane.x);
        float coronaEnvelope = exp(-max(solarR - 1.0, 0.0) * 4.8) * smoothstep(1.85, 0.92, solarR);
        float coronaRays = 0.55 + 0.45 * terrainFbm2(float2(solarAngle * 3.2, solarR * 2.7) + 41.0);
        float prominenceRadius = 1.055 + 0.050 * sin(solarAngle * 5.0 + 0.7)
            + 0.025 * sin(solarAngle * 11.0 - 1.2);
        float prominence = exp(-abs(solarR - prominenceRadius) * 48.0)
            * pow(saturate(0.55 + 0.45 * sin(solarAngle * 7.0 + 2.3)), 5.0)
            * smoothstep(0.96, 1.01, solarR) * smoothstep(1.18, 1.03, solarR);
        result += float3(0.72, 0.16, 0.018) * coronaEnvelope * coronaRays * 0.42;
        result += float3(1.00, 0.10, 0.010) * prominence * 1.35;
    }

    if (solarR <= 1.0)
    {
        float solarZ = sqrt(max(0.0, 1.0 - solarR * solarR));
        float2 sphereUv = solarPlane / max(0.24 + 0.76 * solarZ, 0.16);
        float granA = terrainFbm2(sphereUv * 34.0 + 5.3);
        float granB = terrainFbm2(sphereUv * 73.0 - 17.9);
        float cells = saturate(granA * 0.72 + granB * 0.28);
        float activeNoise = terrainFbm2(sphereUv * 4.1 + 67.2);
        float magnetic = terrainFbm2(sphereUv * 8.7 - 29.4);
        float active = smoothstep(0.63, 0.86, activeNoise) * smoothstep(0.42, 0.78, magnetic);
        float spots = smoothstep(0.78, 0.94, activeNoise) * smoothstep(0.70, 0.91, 1.0 - magnetic);
        float limb = pow(saturate(solarZ), 0.34);
        float3 solarColor = lerp(
            float3(0.95, 0.22, 0.018),
            float3(2.15, 0.78, 0.10),
            saturate(cells * 0.78 + active * 0.42));
        solarColor *= 0.58 + 0.58 * limb;
        solarColor = lerp(solarColor, solarColor * float3(0.14, 0.10, 0.08), spots * 0.82);
        solarColor += float3(1.35, 0.38, 0.055) * active * 0.62;
        result += solarColor * max(float3(0.62, 0.52, 0.42), gPush.data3.yzw * 0.72);
    }
    return result;
}

[shader("fragment")]
float4 skyViewFragmentMain(FullscreenOutput input) : SV_Target
{
    float3 ray = reconstructWorldRay(input.uv);
    float3 cameraPlanet = gPush.data0.xyz;
    float3 sunDir = normalize(gPush.data1.xyz);
    float groundRadius = max(gPush.data2.x, 1.0);
    float atmosphereRadius = groundRadius + max(gPush.data2.y, 1.0);
    float scaleHeight = max(gPush.data2.z, 100.0);
    float mieScale = max(gPush.data2.w, 0.0);

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
    float mu = dot(ray, sunDir);
    float rayleighPhase = 3.0 * (1.0 + mu * mu) / (16.0 * PI);
    float g = 0.76;
    float miePhase = (1.0 - g * g)
        / max(4.0 * PI * pow(1.0 + g * g - 2.0 * g * mu, 1.5), 1.0e-5);

    float segment = (endT - startT) / 4.0;
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
    float localDensity = densityAtRadius(length(cameraPlanet), groundRadius, scaleHeight);
    float styleWeight = saturate(localDensity * 0.38);
    color = lerp(color, stylizedSkyPalette(ray, sunDir), styleWeight);

    // RGB stores low-frequency linear radiance. Alpha stores scalar view transmittance and uses its
    // sign as the ground-intersection bit. High-frequency stars/sun are composited full-res later.
    float transmittanceLuma = dot(transmittance, float3(0.2126, 0.7152, 0.0722));
    return float4(color, hitsGround ? -transmittanceLuma : transmittanceLuma);
}

[shader("fragment")]
float4 skyFragmentMain(FullscreenOutput input) : SV_Target
{
    float4 skyView = gSkyViewLut.SampleLevel(gSkyViewSampler, input.uv, 0.0);
    float3 ray = reconstructWorldRay(input.uv);
    float3 sunDir = normalize(gPush.data1.xyz);
    bool hitsGround = skyView.a < 0.0;
    float transmission = saturate(abs(skyView.a));

    // Keep tiny high-frequency content at native resolution; only the smooth atmospheric integral
    // is reconstructed from the 192x108 LUT.
    float3 highFrequency = float3(0.0, 0.0, 0.0);
    if (!hitsGround)
    {
        highFrequency += proceduralStars(ray);
        highFrequency += proceduralSun(ray, sunDir, false);
    }
    float exposure = max(gPush.data3.x, 0.01);
    float3 color = skyView.rgb + highFrequency * transmission;
    return float4(acesFitted(stylizedWarmCoolGrade(color) * exposure), 1.0);
}
'''
if 'float4 skyViewFragmentMain' not in shader_text:
    SHADER.write_text(shader_text[:sky_start] + new_sky_shader + shader_text[sky_end:], encoding="utf-8")
    print("shader SkyView LUT evaluator/compositor: materialized")
else:
    print("shader SkyView LUT evaluator/compositor: already materialized")

# ---------------- Shader build/embed/tests ----------------
replace_once(
    CMAKE,
    """    set(VF_FULLSCREEN_VERTEX_SPV \"${VF_GENERATED_DIR}/fullscreen.vert.spv\")
    set(VF_SKY_FRAGMENT_SPV \"${VF_GENERATED_DIR}/sky.frag.spv\")
""",
    """    set(VF_FULLSCREEN_VERTEX_SPV \"${VF_GENERATED_DIR}/fullscreen.vert.spv\")
    set(VF_SKY_VIEW_FRAGMENT_SPV \"${VF_GENERATED_DIR}/sky_view.frag.spv\")
    set(VF_SKY_FRAGMENT_SPV \"${VF_GENERATED_DIR}/sky.frag.spv\")
""",
    "CMake LUT shader variable",
)
replace_once(
    CMAKE,
    """        \"${VF_FULLSCREEN_VERTEX_SPV}\"
        \"${VF_SKY_FRAGMENT_SPV}\"
""",
    """        \"${VF_FULLSCREEN_VERTEX_SPV}\"
        \"${VF_SKY_VIEW_FRAGMENT_SPV}\"
        \"${VF_SKY_FRAGMENT_SPV}\"
""",
    "CMake LUT shader output",
)
replace_once(
    CMAKE,
    """        COMMAND \"${SLANGC_EXECUTABLE}\" \"${CMAKE_CURRENT_SOURCE_DIR}/shaders/planet.slang\"
                -target spirv -entry skyFragmentMain -stage fragment -fvk-use-entrypoint-name
                -matrix-layout-column-major -O2 -o \"${VF_SKY_FRAGMENT_SPV}\"
""",
    """        COMMAND \"${SLANGC_EXECUTABLE}\" \"${CMAKE_CURRENT_SOURCE_DIR}/shaders/planet.slang\"
                -target spirv -entry skyViewFragmentMain -stage fragment -fvk-use-entrypoint-name
                -matrix-layout-column-major -O2 -o \"${VF_SKY_VIEW_FRAGMENT_SPV}\"
        COMMAND \"${SLANGC_EXECUTABLE}\" \"${CMAKE_CURRENT_SOURCE_DIR}/shaders/planet.slang\"
                -target spirv -entry skyFragmentMain -stage fragment -fvk-use-entrypoint-name
                -matrix-layout-column-major -O2 -o \"${VF_SKY_FRAGMENT_SPV}\"
""",
    "CMake compile LUT shader",
)
replace_once(
    CMAKE,
    """            \"-DFULLSCREEN_VERT=${VF_FULLSCREEN_VERTEX_SPV}\"
            \"-DSKY_FRAG=${VF_SKY_FRAGMENT_SPV}\"
""",
    """            \"-DFULLSCREEN_VERT=${VF_FULLSCREEN_VERTEX_SPV}\"
            \"-DSKY_VIEW_FRAG=${VF_SKY_VIEW_FRAGMENT_SPV}\"
            \"-DSKY_FRAG=${VF_SKY_FRAGMENT_SPV}\"
""",
    "CMake embed LUT shader",
)

replace_once(
    EMBED,
    """if(NOT DEFINED VERT OR NOT DEFINED OPAQUE_FRAG OR NOT DEFINED TRANSPARENT_FRAG OR NOT DEFINED SHADOW_VERT OR NOT DEFINED SHADOW_FRAG OR NOT DEFINED FULLSCREEN_VERT OR NOT DEFINED SKY_FRAG OR NOT DEFINED HUD_FRAG OR NOT DEFINED OUT)
""",
    """if(NOT DEFINED VERT OR NOT DEFINED OPAQUE_FRAG OR NOT DEFINED TRANSPARENT_FRAG OR NOT DEFINED SHADOW_VERT OR NOT DEFINED SHADOW_FRAG OR NOT DEFINED FULLSCREEN_VERT OR NOT DEFINED SKY_VIEW_FRAG OR NOT DEFINED SKY_FRAG OR NOT DEFINED HUD_FRAG OR NOT DEFINED OUT)
""",
    "Embed LUT requirement",
)
replace_once(
    EMBED,
    """read_spirv(\"${FULLSCREEN_VERT}\" FULLSCREEN_VERT_BYTES)
read_spirv(\"${SKY_FRAG}\" SKY_FRAG_BYTES)
""",
    """read_spirv(\"${FULLSCREEN_VERT}\" FULLSCREEN_VERT_BYTES)
read_spirv(\"${SKY_VIEW_FRAG}\" SKY_VIEW_FRAG_BYTES)
read_spirv(\"${SKY_FRAG}\" SKY_FRAG_BYTES)
""",
    "Embed read LUT shader",
)
replace_once(
    EMBED,
    """foreach(NAME IN ITEMS PlanetVertex OpaqueFragment TransparentFragment ShadowVertex ShadowFragment FullscreenVertex SkyFragment HudFragment)
""",
    """foreach(NAME IN ITEMS PlanetVertex OpaqueFragment TransparentFragment ShadowVertex ShadowFragment FullscreenVertex SkyViewFragment SkyFragment HudFragment)
""",
    "Embed LUT shader item",
)
replace_once(
    EMBED,
    """    elseif(NAME STREQUAL \"SkyFragment\")
        set(BYTES \"${SKY_FRAG_BYTES}\")
    else()
""",
    """    elseif(NAME STREQUAL \"SkyViewFragment\")
        set(BYTES \"${SKY_VIEW_FRAG_BYTES}\")
    elseif(NAME STREQUAL \"SkyFragment\")
        set(BYTES \"${SKY_FRAG_BYTES}\")
    else()
""",
    "Embed map LUT shader",
)

replace_once(
    TEST,
    """    validateEntryPoint(vf::shaders::kSkyFragmentSpv, vf::shaders::kSkyFragmentSpvSize,
        kSpirvExecutionModelFragment, \"skyFragmentMain\");
""",
    """    validateEntryPoint(vf::shaders::kSkyViewFragmentSpv, vf::shaders::kSkyViewFragmentSpvSize,
        kSpirvExecutionModelFragment, \"skyViewFragmentMain\");
    validateEntryPoint(vf::shaders::kSkyFragmentSpv, vf::shaders::kSkyFragmentSpvSize,
        kSpirvExecutionModelFragment, \"skyFragmentMain\");
""",
    "shader contract LUT entry",
)

# ---------------- Postconditions ----------------
checks = {
    "192x108 LUT": "kSkyViewLutWidth = 192" in HEADER.read_text(encoding="utf-8"),
    "RGBA16F target": "VK_FORMAT_R16G16B16A16_SFLOAT" in CPP.read_text(encoding="utf-8"),
    "LUT color pass": "skyViewPipeline_" in CPP.read_text(encoding="utf-8"),
    "LUT barrier": "VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL" in CPP.read_text(encoding="utf-8"),
    "LUT sampler": "gSkyViewLut.SampleLevel" in SHADER.read_text(encoding="utf-8"),
    "expensive LUT entry": "skyViewFragmentMain" in SHADER.read_text(encoding="utf-8"),
    "cheap final sky": "highFrequency += proceduralStars(ray);" in SHADER.read_text(encoding="utf-8"),
    "SPIR-V LUT": "VF_SKY_VIEW_FRAGMENT_SPV" in CMAKE.read_text(encoding="utf-8"),
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("postcondition failure: " + ", ".join(failed))
print("R24 Hillaire-inspired SkyView LUT materialized successfully")
