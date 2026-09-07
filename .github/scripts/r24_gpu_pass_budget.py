from pathlib import Path

H = Path('native/include/vf/render/VulkanRenderer.hpp')
CPP = Path('native/src/render/VulkanRenderer.cpp')
h = H.read_text(encoding='utf-8')
cpp = CPP.read_text(encoding='utf-8')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {count}')
    return text.replace(old, new, 1)


# -----------------------------------------------------------------------------
# Renderer state: per-frame Vulkan timestamp pools, no blocking readback.
# -----------------------------------------------------------------------------
h = replace_once(
    h,
'''    void createCommands();\n    void createSyncObjects();\n\n    void createSwapchain();\n''',
'''    void createCommands();\n    void createSyncObjects();\n    void destroyTimestampQueries() noexcept;\n    void readTimestampQueries(std::uint32_t frame);\n\n    void createSwapchain();\n''',
    'timestamp method declarations')

h = replace_once(
    h,
'''    std::array<VkSemaphore, kFramesInFlight> imageAvailable_{};\n    std::array<VkSemaphore, kFramesInFlight> renderFinished_{};\n    std::array<VkFence, kFramesInFlight> inFlight_{};\n\n    std::uint32_t frameIndex_{};\n''',
'''    std::array<VkSemaphore, kFramesInFlight> imageAvailable_{};\n    std::array<VkSemaphore, kFramesInFlight> renderFinished_{};\n    std::array<VkFence, kFramesInFlight> inFlight_{};\n\n    // Eight timestamps = [shadow begin/end, opaque begin/end, sky begin/end, transparent begin/end].\n    // Results are read only after this frame slot's fence signals, so profiling never stalls the GPU.\n    static constexpr std::uint32_t kTimestampQueryCount = 8U;\n    std::array<VkQueryPool, kFramesInFlight> timestampQueryPools_{};\n    std::array<bool, kFramesInFlight> timestampQueryWritten_{};\n    float timestampPeriodNanoseconds_{1.0F};\n    std::uint32_t timestampValidBits_{};\n    std::uint64_t timestampMask_{~std::uint64_t{0}};\n    std::uint64_t gpuTimingSamples_{};\n    bool gpuTimestampsSupported_{};\n\n    std::uint32_t frameIndex_{};\n''',
    'timestamp members')

cpp = replace_once(
    cpp,
'''    for (auto& mesh : staticMeshes_) destroyFrameMesh(mesh);\n    for (auto& mesh : dynamicMeshes_) destroyFrameMesh(mesh);\n    destroySwapchainResources();\n''',
'''    for (auto& mesh : staticMeshes_) destroyFrameMesh(mesh);\n    for (auto& mesh : dynamicMeshes_) destroyFrameMesh(mesh);\n    destroyTimestampQueries();\n    destroySwapchainResources();\n''',
    'timestamp destruction')

cpp = replace_once(
    cpp,
'''    if (physicalDevice_ == VK_NULL_HANDLE)\n        fail("No GPU satisfies Vulkan 1.3 + dynamic rendering + synchronization2 + swapchain");\n}\n''',
'''    if (physicalDevice_ == VK_NULL_HANDLE)\n        fail("No GPU satisfies Vulkan 1.3 + dynamic rendering + synchronization2 + swapchain");\n\n    // Timestamp support is a queue-family property, not a feature bit. Vulkan reports the number\n    // of valid timestamp bits for each queue and timestampPeriod in nanoseconds per tick. Keep the\n    // mask so wraparound on implementations with fewer than 64 valid bits is handled correctly.\n    VkPhysicalDeviceProperties selectedProperties{};\n    vkGetPhysicalDeviceProperties(physicalDevice_, &selectedProperties);\n    timestampPeriodNanoseconds_ = selectedProperties.limits.timestampPeriod;\n    std::uint32_t selectedQueueCount = 0U;\n    vkGetPhysicalDeviceQueueFamilyProperties(physicalDevice_, &selectedQueueCount, nullptr);\n    std::vector<VkQueueFamilyProperties> selectedQueues(selectedQueueCount);\n    vkGetPhysicalDeviceQueueFamilyProperties(\n        physicalDevice_, &selectedQueueCount, selectedQueues.data());\n    if (queueFamilyIndex_ < selectedQueues.size()) {\n        timestampValidBits_ = selectedQueues[queueFamilyIndex_].timestampValidBits;\n        gpuTimestampsSupported_ = timestampValidBits_ != 0U;\n        timestampMask_ = timestampValidBits_ >= 64U\n            ? ~std::uint64_t{0}\n            : ((std::uint64_t{1} << timestampValidBits_) - 1U);\n    }\n}\n''',
    'discover queue timestamp support')

cpp = replace_once(
    cpp,
'''void VulkanRenderer::createSyncObjects() {\n    VkSemaphoreCreateInfo semaphore{};\n    semaphore.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;\n    VkFenceCreateInfo fence{};\n    fence.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;\n    fence.flags = VK_FENCE_CREATE_SIGNALED_BIT;\n    for (std::uint32_t i = 0; i < kFramesInFlight; ++i) {\n        if (vkCreateSemaphore(device_, &semaphore, nullptr, &imageAvailable_[i]) != VK_SUCCESS\n            || vkCreateSemaphore(device_, &semaphore, nullptr, &renderFinished_[i]) != VK_SUCCESS\n            || vkCreateFence(device_, &fence, nullptr, &inFlight_[i]) != VK_SUCCESS)\n            fail("Failed to create Vulkan synchronization objects");\n    }\n}\n''',
'''void VulkanRenderer::createSyncObjects() {\n    VkSemaphoreCreateInfo semaphore{};\n    semaphore.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;\n    VkFenceCreateInfo fence{};\n    fence.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;\n    fence.flags = VK_FENCE_CREATE_SIGNALED_BIT;\n    for (std::uint32_t i = 0; i < kFramesInFlight; ++i) {\n        if (vkCreateSemaphore(device_, &semaphore, nullptr, &imageAvailable_[i]) != VK_SUCCESS\n            || vkCreateSemaphore(device_, &semaphore, nullptr, &renderFinished_[i]) != VK_SUCCESS\n            || vkCreateFence(device_, &fence, nullptr, &inFlight_[i]) != VK_SUCCESS)\n            fail("Failed to create Vulkan synchronization objects");\n    }\n\n    if (gpuTimestampsSupported_) {\n        VkQueryPoolCreateInfo query{};\n        query.sType = VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO;\n        query.queryType = VK_QUERY_TYPE_TIMESTAMP;\n        query.queryCount = kTimestampQueryCount;\n        for (auto& pool : timestampQueryPools_) {\n            const VkResult result = vkCreateQueryPool(device_, &query, nullptr, &pool);\n            if (result != VK_SUCCESS) fail("vkCreateQueryPool(timestamp) failed", result);\n        }\n        SDL_Log(\n            "R24 GPU timestamps enabled: valid_bits=%u period_ns=%.6f",\n            timestampValidBits_, timestampPeriodNanoseconds_);\n    }\n}\n\nvoid VulkanRenderer::destroyTimestampQueries() noexcept {\n    if (device_ == VK_NULL_HANDLE) return;\n    for (auto& pool : timestampQueryPools_) {\n        if (pool != VK_NULL_HANDLE) vkDestroyQueryPool(device_, pool, nullptr);\n        pool = VK_NULL_HANDLE;\n    }\n    timestampQueryWritten_.fill(false);\n}\n\nvoid VulkanRenderer::readTimestampQueries(std::uint32_t frame) {\n    if (!gpuTimestampsSupported_ || !timestampQueryWritten_[frame]) return;\n    std::array<std::uint64_t, kTimestampQueryCount> ticks{};\n    const VkResult result = vkGetQueryPoolResults(\n        device_,\n        timestampQueryPools_[frame],\n        0U,\n        kTimestampQueryCount,\n        sizeof(ticks),\n        ticks.data(),\n        sizeof(std::uint64_t),\n        VK_QUERY_RESULT_64_BIT);\n    if (result == VK_NOT_READY) return;\n    if (result != VK_SUCCESS) fail("vkGetQueryPoolResults(timestamp) failed", result);\n\n    const auto milliseconds = [&](std::uint32_t begin, std::uint32_t end) {\n        const std::uint64_t delta = (ticks[end] - ticks[begin]) & timestampMask_;\n        return static_cast<double>(delta)\n            * static_cast<double>(timestampPeriodNanoseconds_) / 1.0e6;\n    };\n    const double shadowMs = milliseconds(0U, 1U);\n    const double opaqueMs = milliseconds(2U, 3U);\n    const double skyMs = milliseconds(4U, 5U);\n    const double transparentMs = milliseconds(6U, 7U);\n    ++gpuTimingSamples_;\n    // Log the first measurement immediately for CI/evidence and then once per ~60 samples so a\n    // normal gameplay log is useful without becoming a per-frame I/O bottleneck.\n    if (gpuTimingSamples_ == 1U || (gpuTimingSamples_ % 60U) == 0U) {\n        SDL_Log(\n            "R24 GPU pass_ms shadow=%.3f opaque=%.3f sky=%.3f transparent=%.3f total_profiled=%.3f",\n            shadowMs, opaqueMs, skyMs, transparentMs,\n            shadowMs + opaqueMs + skyMs + transparentMs);\n    }\n}\n''',
    'create and asynchronously read timestamp queries')

# -----------------------------------------------------------------------------
# Backface culling: opaque solid geometry only. Transparent remains two-sided.
# Grass already emits explicit opposite-winding triangles, so it keeps both visual sides.
# -----------------------------------------------------------------------------
cpp = replace_once(
    cpp,
'''    createColorPipeline(\n        opaquePipeline_, sceneVertex, "vertexMain", opaqueFragment, "opaqueFragmentMain",\n        &vertexInput, &reverseDepth, &opaqueBlend, scenePipelineLayout_);\n    createColorPipeline(\n        transparentPipeline_, sceneVertex, "vertexMain", transparentFragment, "transparentFragmentMain",\n''',
'''    // All production opaque primitives are cull-safe: terrain and closed rock/tree meshes have\n    // consistent outward winding, while grass explicitly emits both opposite-winding faces. Cull\n    // backfaces before fragment generation; keep water/glass transparent geometry two-sided.\n    raster.cullMode = VK_CULL_MODE_BACK_BIT;\n    createColorPipeline(\n        opaquePipeline_, sceneVertex, "vertexMain", opaqueFragment, "opaqueFragmentMain",\n        &vertexInput, &reverseDepth, &opaqueBlend, scenePipelineLayout_);\n    raster.cullMode = VK_CULL_MODE_NONE;\n    createColorPipeline(\n        transparentPipeline_, sceneVertex, "vertexMain", transparentFragment, "transparentFragmentMain",\n''',
    'opaque backface culling')

# -----------------------------------------------------------------------------
# Draw-frame timestamps. Query results are consumed only after this slot's fence has signaled.
# -----------------------------------------------------------------------------
cpp = replace_once(
    cpp,
'''    VkResult result = vkWaitForFences(device_, 1, &inFlight_[frame], VK_TRUE, UINT64_MAX);\n    if (result != VK_SUCCESS) fail("vkWaitForFences failed", result);\n\n    // The frame fence is the ownership gate for both static and dynamic mapped buffers. Static\n''',
'''    VkResult result = vkWaitForFences(device_, 1, &inFlight_[frame], VK_TRUE, UINT64_MAX);\n    if (result != VK_SUCCESS) fail("vkWaitForFences failed", result);\n    readTimestampQueries(frame);\n\n    // The frame fence is the ownership gate for both static and dynamic mapped buffers. Static\n''',
    'timestamp read after frame fence')

cpp = replace_once(
    cpp,
'''    result = vkBeginCommandBuffer(command, &begin);\n    if (result != VK_SUCCESS) fail("vkBeginCommandBuffer failed", result);\n\n    VkImageMemoryBarrier2 shadowToAttachment{};\n''',
'''    result = vkBeginCommandBuffer(command, &begin);\n    if (result != VK_SUCCESS) fail("vkBeginCommandBuffer failed", result);\n    if (gpuTimestampsSupported_) {\n        vkCmdResetQueryPool(command, timestampQueryPools_[frame], 0U, kTimestampQueryCount);\n        vkCmdWriteTimestamp2(\n            command, VK_PIPELINE_STAGE_2_TOP_OF_PIPE_BIT, timestampQueryPools_[frame], 0U);\n    }\n\n    VkImageMemoryBarrier2 shadowToAttachment{};\n''',
    'begin shadow timestamp')

cpp = replace_once(
    cpp,
'''    }\n    vkCmdEndRendering(command);\n\n    VkImageMemoryBarrier2 shadowToRead{};\n''',
'''    }\n    vkCmdEndRendering(command);\n    if (gpuTimestampsSupported_) {\n        vkCmdWriteTimestamp2(\n            command, VK_PIPELINE_STAGE_2_BOTTOM_OF_PIPE_BIT, timestampQueryPools_[frame], 1U);\n    }\n\n    VkImageMemoryBarrier2 shadowToRead{};\n''',
    'end shadow timestamp')

cpp = replace_once(
    cpp,
'''    // Depth-first ordering: fill reverse-Z with opaque terrain, then shade sky only in pixels\n    // that are still at the exact clear depth. Transparent water/glass blends over the completed\n    // opaque+sky background afterwards.\n    drawScenePass(opaquePipeline_, false);\n    vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, skyPipeline_);\n''',
'''    // Depth-first ordering: fill reverse-Z with opaque terrain, then shade sky only in pixels\n    // that are still at the exact clear depth. Transparent water/glass blends over the completed\n    // opaque+sky background afterwards.\n    if (gpuTimestampsSupported_) {\n        vkCmdWriteTimestamp2(\n            command, VK_PIPELINE_STAGE_2_TOP_OF_PIPE_BIT, timestampQueryPools_[frame], 2U);\n    }\n    drawScenePass(opaquePipeline_, false);\n    if (gpuTimestampsSupported_) {\n        vkCmdWriteTimestamp2(\n            command, VK_PIPELINE_STAGE_2_BOTTOM_OF_PIPE_BIT, timestampQueryPools_[frame], 3U);\n        vkCmdWriteTimestamp2(\n            command, VK_PIPELINE_STAGE_2_TOP_OF_PIPE_BIT, timestampQueryPools_[frame], 4U);\n    }\n    vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, skyPipeline_);\n''',
    'opaque and sky timestamp boundary')

cpp = replace_once(
    cpp,
'''    vkCmdDraw(command, 3, 1, 0, 0);\n\n    drawScenePass(transparentPipeline_, true);\n\n    vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, hudPipeline_);\n''',
'''    vkCmdDraw(command, 3, 1, 0, 0);\n    if (gpuTimestampsSupported_) {\n        vkCmdWriteTimestamp2(\n            command, VK_PIPELINE_STAGE_2_BOTTOM_OF_PIPE_BIT, timestampQueryPools_[frame], 5U);\n        vkCmdWriteTimestamp2(\n            command, VK_PIPELINE_STAGE_2_TOP_OF_PIPE_BIT, timestampQueryPools_[frame], 6U);\n    }\n\n    drawScenePass(transparentPipeline_, true);\n    if (gpuTimestampsSupported_) {\n        vkCmdWriteTimestamp2(\n            command, VK_PIPELINE_STAGE_2_BOTTOM_OF_PIPE_BIT, timestampQueryPools_[frame], 7U);\n    }\n\n    vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, hudPipeline_);\n''',
    'sky and transparent timestamp boundary')

cpp = replace_once(
    cpp,
'''    result = vkQueueSubmit2(graphicsQueue_, 1, &submit, inFlight_[frame]);\n    if (result != VK_SUCCESS) fail("vkQueueSubmit2 failed", result);\n\n    VkPresentInfoKHR present{};\n''',
'''    result = vkQueueSubmit2(graphicsQueue_, 1, &submit, inFlight_[frame]);\n    if (result != VK_SUCCESS) fail("vkQueueSubmit2 failed", result);\n    if (gpuTimestampsSupported_) timestampQueryWritten_[frame] = true;\n\n    VkPresentInfoKHR present{};\n''',
    'mark timestamp query submitted')

H.write_text(h, encoding='utf-8')
CPP.write_text(cpp, encoding='utf-8')
print('R24 GPU PASS BUDGET materialized')
print(' - opaque backface culling enabled; transparent remains two-sided')
print(' - 8 Vulkan timestamp queries measure shadow/opaque/sky/transparent')
print(' - timestamp results read only after owning frame fence signals')
print(' - timestamp valid-bit mask handles implementations below 64 bits')
