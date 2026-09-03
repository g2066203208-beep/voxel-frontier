#include "vf/render/VulkanRenderer.hpp"

#include <SDL3/SDL.h>
#include <SDL3/SDL_vulkan.h>

#include <algorithm>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>

namespace vf {

namespace {

[[noreturn]] void fail(const std::string& message, VkResult result = VK_SUCCESS) {
    if (result == VK_SUCCESS) throw std::runtime_error(message);
    throw std::runtime_error(message + " (VkResult=" + std::to_string(static_cast<int>(result)) + ")");
}

[[nodiscard]] VkCompositeAlphaFlagBitsKHR chooseCompositeAlpha(VkCompositeAlphaFlagsKHR supported) {
    constexpr VkCompositeAlphaFlagBitsKHR candidates[] = {
        VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
        VK_COMPOSITE_ALPHA_PRE_MULTIPLIED_BIT_KHR,
        VK_COMPOSITE_ALPHA_POST_MULTIPLIED_BIT_KHR,
        VK_COMPOSITE_ALPHA_INHERIT_BIT_KHR,
    };
    for (const auto candidate : candidates) {
        if ((supported & candidate) != 0U) return candidate;
    }
    return VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
}

} // namespace

VulkanRenderer::VulkanRenderer(SDL_Window* window) : window_(window) {
    if (!window_) throw std::invalid_argument("VulkanRenderer requires a valid SDL window");

    const VkResult volkResult = volkInitialize();
    if (volkResult != VK_SUCCESS) fail("volkInitialize failed", volkResult);

    createInstance();
    createSurface();
    selectPhysicalDevice();
    createDevice();
    createCommands();
    createSyncObjects();
    createSwapchain();
}

VulkanRenderer::~VulkanRenderer() {
    if (device_ != VK_NULL_HANDLE) vkDeviceWaitIdle(device_);

    for (std::uint32_t i = 0; i < kFramesInFlight; ++i) {
        if (inFlight_[i] != VK_NULL_HANDLE) vkDestroyFence(device_, inFlight_[i], nullptr);
        if (renderFinished_[i] != VK_NULL_HANDLE) vkDestroySemaphore(device_, renderFinished_[i], nullptr);
        if (imageAvailable_[i] != VK_NULL_HANDLE) vkDestroySemaphore(device_, imageAvailable_[i], nullptr);
    }

    if (commandPool_ != VK_NULL_HANDLE) vkDestroyCommandPool(device_, commandPool_, nullptr);
    destroySwapchain();
    if (device_ != VK_NULL_HANDLE) vkDestroyDevice(device_, nullptr);
    if (surface_ != VK_NULL_HANDLE && instance_ != VK_NULL_HANDLE) {
        SDL_Vulkan_DestroySurface(instance_, surface_, nullptr);
    }
    if (instance_ != VK_NULL_HANDLE) vkDestroyInstance(instance_, nullptr);
    volkFinalize();
}

void VulkanRenderer::createInstance() {
    std::uint32_t loaderVersion = VK_API_VERSION_1_0;
    if (vkEnumerateInstanceVersion) {
        const VkResult result = vkEnumerateInstanceVersion(&loaderVersion);
        if (result != VK_SUCCESS) fail("vkEnumerateInstanceVersion failed", result);
    }

    if (loaderVersion < VK_API_VERSION_1_3) {
        fail("Voxel Frontier requires Vulkan 1.3 or newer");
    }
    apiVersion_ = std::min(loaderVersion, static_cast<std::uint32_t>(VK_API_VERSION_1_4));

    Uint32 extensionCount = 0;
    const char* const* extensions = SDL_Vulkan_GetInstanceExtensions(&extensionCount);
    if (!extensions || extensionCount == 0) {
        throw std::runtime_error(std::string{"SDL_Vulkan_GetInstanceExtensions failed: "} + SDL_GetError());
    }

    VkApplicationInfo appInfo{};
    appInfo.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    appInfo.pApplicationName = "Voxel Frontier";
    appInfo.applicationVersion = VK_MAKE_API_VERSION(0, 0, 1, 0);
    appInfo.pEngineName = "Voxel Frontier Native Engine";
    appInfo.engineVersion = VK_MAKE_API_VERSION(0, 0, 1, 0);
    appInfo.apiVersion = apiVersion_;

    VkInstanceCreateInfo createInfo{};
    createInfo.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    createInfo.pApplicationInfo = &appInfo;
    createInfo.enabledExtensionCount = extensionCount;
    createInfo.ppEnabledExtensionNames = extensions;

    const VkResult result = vkCreateInstance(&createInfo, nullptr, &instance_);
    if (result != VK_SUCCESS) fail("vkCreateInstance failed", result);
    volkLoadInstance(instance_);
}

void VulkanRenderer::createSurface() {
    if (!SDL_Vulkan_CreateSurface(window_, instance_, nullptr, &surface_)) {
        throw std::runtime_error(std::string{"SDL_Vulkan_CreateSurface failed: "} + SDL_GetError());
    }
}

bool VulkanRenderer::supportsSwapchain(VkPhysicalDevice device) const {
    std::uint32_t extensionCount = 0;
    if (vkEnumerateDeviceExtensionProperties(device, nullptr, &extensionCount, nullptr) != VK_SUCCESS) return false;
    std::vector<VkExtensionProperties> extensions(extensionCount);
    if (vkEnumerateDeviceExtensionProperties(device, nullptr, &extensionCount, extensions.data()) != VK_SUCCESS) return false;

    return std::any_of(extensions.begin(), extensions.end(), [](const VkExtensionProperties& extension) {
        return std::string_view{extension.extensionName} == VK_KHR_SWAPCHAIN_EXTENSION_NAME;
    });
}

std::uint32_t VulkanRenderer::findGraphicsPresentQueue(VkPhysicalDevice device) const {
    std::uint32_t queueCount = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(device, &queueCount, nullptr);
    std::vector<VkQueueFamilyProperties> queues(queueCount);
    vkGetPhysicalDeviceQueueFamilyProperties(device, &queueCount, queues.data());

    for (std::uint32_t i = 0; i < queueCount; ++i) {
        const bool graphics = (queues[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) != 0U;
        const bool present = SDL_Vulkan_GetPresentationSupport(instance_, device, i);
        if (graphics && present) return i;
    }
    return std::numeric_limits<std::uint32_t>::max();
}

void VulkanRenderer::selectPhysicalDevice() {
    std::uint32_t deviceCount = 0;
    VkResult result = vkEnumeratePhysicalDevices(instance_, &deviceCount, nullptr);
    if (result != VK_SUCCESS || deviceCount == 0) fail("No Vulkan physical device found", result);

    std::vector<VkPhysicalDevice> devices(deviceCount);
    result = vkEnumeratePhysicalDevices(instance_, &deviceCount, devices.data());
    if (result != VK_SUCCESS) fail("vkEnumeratePhysicalDevices failed", result);

    std::int32_t bestScore = -1;
    for (const auto device : devices) {
        VkPhysicalDeviceProperties properties{};
        vkGetPhysicalDeviceProperties(device, &properties);
        if (properties.apiVersion < VK_API_VERSION_1_3) continue;
        if (!supportsSwapchain(device)) continue;

        const auto queueFamily = findGraphicsPresentQueue(device);
        if (queueFamily == std::numeric_limits<std::uint32_t>::max()) continue;

        VkPhysicalDeviceVulkan13Features features13{};
        features13.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_3_FEATURES;
        VkPhysicalDeviceFeatures2 features2{};
        features2.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2;
        features2.pNext = &features13;
        vkGetPhysicalDeviceFeatures2(device, &features2);
        if (features13.synchronization2 != VK_TRUE) continue;

        std::uint32_t formatCount = 0;
        std::uint32_t presentModeCount = 0;
        vkGetPhysicalDeviceSurfaceFormatsKHR(device, surface_, &formatCount, nullptr);
        vkGetPhysicalDeviceSurfacePresentModesKHR(device, surface_, &presentModeCount, nullptr);
        if (formatCount == 0 || presentModeCount == 0) continue;

        std::int32_t score = 100;
        if (properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU) score += 1000;
        if (properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU) score += 500;
        score += static_cast<std::int32_t>(properties.limits.maxImageDimension2D / 1024U);

        if (score > bestScore) {
            bestScore = score;
            physicalDevice_ = device;
            queueFamilyIndex_ = queueFamily;
            gpuName_ = properties.deviceName;
        }
    }

    if (physicalDevice_ == VK_NULL_HANDLE) {
        fail("No GPU satisfies Vulkan 1.3 + synchronization2 + swapchain requirements");
    }
}

void VulkanRenderer::createDevice() {
    constexpr float queuePriority = 1.0F;
    VkDeviceQueueCreateInfo queueInfo{};
    queueInfo.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
    queueInfo.queueFamilyIndex = queueFamilyIndex_;
    queueInfo.queueCount = 1;
    queueInfo.pQueuePriorities = &queuePriority;

    VkPhysicalDeviceVulkan13Features features13{};
    features13.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_3_FEATURES;
    features13.synchronization2 = VK_TRUE;

    const char* extensions[] = {VK_KHR_SWAPCHAIN_EXTENSION_NAME};

    VkDeviceCreateInfo createInfo{};
    createInfo.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    createInfo.pNext = &features13;
    createInfo.queueCreateInfoCount = 1;
    createInfo.pQueueCreateInfos = &queueInfo;
    createInfo.enabledExtensionCount = 1;
    createInfo.ppEnabledExtensionNames = extensions;

    const VkResult result = vkCreateDevice(physicalDevice_, &createInfo, nullptr, &device_);
    if (result != VK_SUCCESS) fail("vkCreateDevice failed", result);
    volkLoadDevice(device_);
    vkGetDeviceQueue(device_, queueFamilyIndex_, 0, &graphicsQueue_);
}

void VulkanRenderer::createCommands() {
    VkCommandPoolCreateInfo poolInfo{};
    poolInfo.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    poolInfo.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    poolInfo.queueFamilyIndex = queueFamilyIndex_;
    VkResult result = vkCreateCommandPool(device_, &poolInfo, nullptr, &commandPool_);
    if (result != VK_SUCCESS) fail("vkCreateCommandPool failed", result);

    VkCommandBufferAllocateInfo allocInfo{};
    allocInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    allocInfo.commandPool = commandPool_;
    allocInfo.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    allocInfo.commandBufferCount = kFramesInFlight;
    result = vkAllocateCommandBuffers(device_, &allocInfo, commandBuffers_.data());
    if (result != VK_SUCCESS) fail("vkAllocateCommandBuffers failed", result);
}

void VulkanRenderer::createSyncObjects() {
    VkSemaphoreCreateInfo semaphoreInfo{};
    semaphoreInfo.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;

    VkFenceCreateInfo fenceInfo{};
    fenceInfo.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
    fenceInfo.flags = VK_FENCE_CREATE_SIGNALED_BIT;

    for (std::uint32_t i = 0; i < kFramesInFlight; ++i) {
        if (vkCreateSemaphore(device_, &semaphoreInfo, nullptr, &imageAvailable_[i]) != VK_SUCCESS ||
            vkCreateSemaphore(device_, &semaphoreInfo, nullptr, &renderFinished_[i]) != VK_SUCCESS ||
            vkCreateFence(device_, &fenceInfo, nullptr, &inFlight_[i]) != VK_SUCCESS) {
            fail("Failed to create Vulkan synchronization objects");
        }
    }
}

void VulkanRenderer::createSwapchain() {
    int pixelWidth = 0;
    int pixelHeight = 0;
    if (!SDL_GetWindowSizeInPixels(window_, &pixelWidth, &pixelHeight) || pixelWidth <= 0 || pixelHeight <= 0) {
        return;
    }

    VkSurfaceCapabilitiesKHR capabilities{};
    VkResult result = vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physicalDevice_, surface_, &capabilities);
    if (result != VK_SUCCESS) fail("vkGetPhysicalDeviceSurfaceCapabilitiesKHR failed", result);
    if ((capabilities.supportedUsageFlags & VK_IMAGE_USAGE_TRANSFER_DST_BIT) == 0U) {
        fail("Swapchain surface does not support transfer-destination images");
    }

    std::uint32_t formatCount = 0;
    vkGetPhysicalDeviceSurfaceFormatsKHR(physicalDevice_, surface_, &formatCount, nullptr);
    std::vector<VkSurfaceFormatKHR> formats(formatCount);
    vkGetPhysicalDeviceSurfaceFormatsKHR(physicalDevice_, surface_, &formatCount, formats.data());

    VkSurfaceFormatKHR chosenFormat = formats.front();
    for (const auto& format : formats) {
        if (format.format == VK_FORMAT_B8G8R8A8_SRGB && format.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR) {
            chosenFormat = format;
            break;
        }
    }

    std::uint32_t presentModeCount = 0;
    vkGetPhysicalDeviceSurfacePresentModesKHR(physicalDevice_, surface_, &presentModeCount, nullptr);
    std::vector<VkPresentModeKHR> presentModes(presentModeCount);
    vkGetPhysicalDeviceSurfacePresentModesKHR(physicalDevice_, surface_, &presentModeCount, presentModes.data());
    VkPresentModeKHR presentMode = VK_PRESENT_MODE_FIFO_KHR;
    if (std::find(presentModes.begin(), presentModes.end(), VK_PRESENT_MODE_MAILBOX_KHR) != presentModes.end()) {
        presentMode = VK_PRESENT_MODE_MAILBOX_KHR;
    }

    VkExtent2D extent{};
    if (capabilities.currentExtent.width != std::numeric_limits<std::uint32_t>::max()) {
        extent = capabilities.currentExtent;
    } else {
        extent.width = std::clamp(
            static_cast<std::uint32_t>(pixelWidth),
            capabilities.minImageExtent.width,
            capabilities.maxImageExtent.width);
        extent.height = std::clamp(
            static_cast<std::uint32_t>(pixelHeight),
            capabilities.minImageExtent.height,
            capabilities.maxImageExtent.height);
    }

    std::uint32_t imageCount = capabilities.minImageCount + 1;
    if (capabilities.maxImageCount > 0) imageCount = std::min(imageCount, capabilities.maxImageCount);

    VkSwapchainCreateInfoKHR createInfo{};
    createInfo.sType = VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR;
    createInfo.surface = surface_;
    createInfo.minImageCount = imageCount;
    createInfo.imageFormat = chosenFormat.format;
    createInfo.imageColorSpace = chosenFormat.colorSpace;
    createInfo.imageExtent = extent;
    createInfo.imageArrayLayers = 1;
    createInfo.imageUsage = VK_IMAGE_USAGE_TRANSFER_DST_BIT;
    createInfo.imageSharingMode = VK_SHARING_MODE_EXCLUSIVE;
    createInfo.preTransform = capabilities.currentTransform;
    createInfo.compositeAlpha = chooseCompositeAlpha(capabilities.supportedCompositeAlpha);
    createInfo.presentMode = presentMode;
    createInfo.clipped = VK_TRUE;

    result = vkCreateSwapchainKHR(device_, &createInfo, nullptr, &swapchain_);
    if (result != VK_SUCCESS) fail("vkCreateSwapchainKHR failed", result);

    swapchainFormat_ = chosenFormat.format;
    swapchainExtent_ = extent;

    std::uint32_t actualImageCount = 0;
    vkGetSwapchainImagesKHR(device_, swapchain_, &actualImageCount, nullptr);
    swapchainImages_.resize(actualImageCount);
    vkGetSwapchainImagesKHR(device_, swapchain_, &actualImageCount, swapchainImages_.data());
    imageInitialized_.assign(actualImageCount, false);
    resizeRequested_ = false;
}

void VulkanRenderer::destroySwapchain() noexcept {
    swapchainImages_.clear();
    imageInitialized_.clear();
    if (swapchain_ != VK_NULL_HANDLE && device_ != VK_NULL_HANDLE) {
        vkDestroySwapchainKHR(device_, swapchain_, nullptr);
        swapchain_ = VK_NULL_HANDLE;
    }
}

void VulkanRenderer::recreateSwapchain() {
    if (device_ == VK_NULL_HANDLE) return;
    vkDeviceWaitIdle(device_);
    destroySwapchain();
    createSwapchain();
}

void VulkanRenderer::drawFrame(float r, float g, float b) {
    if (resizeRequested_) recreateSwapchain();
    if (swapchain_ == VK_NULL_HANDLE) return;

    const auto frame = frameIndex_ % kFramesInFlight;
    VkResult result = vkWaitForFences(device_, 1, &inFlight_[frame], VK_TRUE, UINT64_MAX);
    if (result != VK_SUCCESS) fail("vkWaitForFences failed", result);

    std::uint32_t imageIndex = 0;
    result = vkAcquireNextImageKHR(
        device_,
        swapchain_,
        UINT64_MAX,
        imageAvailable_[frame],
        VK_NULL_HANDLE,
        &imageIndex);
    if (result == VK_ERROR_OUT_OF_DATE_KHR) {
        recreateSwapchain();
        return;
    }
    if (result != VK_SUCCESS && result != VK_SUBOPTIMAL_KHR) fail("vkAcquireNextImageKHR failed", result);

    vkResetFences(device_, 1, &inFlight_[frame]);
    vkResetCommandBuffer(commandBuffers_[frame], 0);

    VkCommandBufferBeginInfo beginInfo{};
    beginInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    beginInfo.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    result = vkBeginCommandBuffer(commandBuffers_[frame], &beginInfo);
    if (result != VK_SUCCESS) fail("vkBeginCommandBuffer failed", result);

    VkImageMemoryBarrier2 toTransfer{};
    toTransfer.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;
    toTransfer.srcStageMask = VK_PIPELINE_STAGE_2_NONE;
    toTransfer.srcAccessMask = VK_ACCESS_2_NONE;
    toTransfer.dstStageMask = VK_PIPELINE_STAGE_2_TRANSFER_BIT;
    toTransfer.dstAccessMask = VK_ACCESS_2_TRANSFER_WRITE_BIT;
    toTransfer.oldLayout = imageInitialized_[imageIndex] ? VK_IMAGE_LAYOUT_PRESENT_SRC_KHR : VK_IMAGE_LAYOUT_UNDEFINED;
    toTransfer.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    toTransfer.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toTransfer.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toTransfer.image = swapchainImages_[imageIndex];
    toTransfer.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    toTransfer.subresourceRange.baseMipLevel = 0;
    toTransfer.subresourceRange.levelCount = 1;
    toTransfer.subresourceRange.baseArrayLayer = 0;
    toTransfer.subresourceRange.layerCount = 1;

    VkDependencyInfo dependency{};
    dependency.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO;
    dependency.imageMemoryBarrierCount = 1;
    dependency.pImageMemoryBarriers = &toTransfer;
    vkCmdPipelineBarrier2(commandBuffers_[frame], &dependency);

    VkClearColorValue clearColor{{r, g, b, 1.0F}};
    VkImageSubresourceRange range{};
    range.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    range.baseMipLevel = 0;
    range.levelCount = 1;
    range.baseArrayLayer = 0;
    range.layerCount = 1;
    vkCmdClearColorImage(
        commandBuffers_[frame],
        swapchainImages_[imageIndex],
        VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
        &clearColor,
        1,
        &range);

    VkImageMemoryBarrier2 toPresent{};
    toPresent.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;
    toPresent.srcStageMask = VK_PIPELINE_STAGE_2_TRANSFER_BIT;
    toPresent.srcAccessMask = VK_ACCESS_2_TRANSFER_WRITE_BIT;
    toPresent.dstStageMask = VK_PIPELINE_STAGE_2_NONE;
    toPresent.dstAccessMask = VK_ACCESS_2_NONE;
    toPresent.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    toPresent.newLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
    toPresent.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toPresent.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toPresent.image = swapchainImages_[imageIndex];
    toPresent.subresourceRange = range;

    dependency.pImageMemoryBarriers = &toPresent;
    vkCmdPipelineBarrier2(commandBuffers_[frame], &dependency);

    result = vkEndCommandBuffer(commandBuffers_[frame]);
    if (result != VK_SUCCESS) fail("vkEndCommandBuffer failed", result);

    VkSemaphoreSubmitInfo waitInfo{};
    waitInfo.sType = VK_STRUCTURE_TYPE_SEMAPHORE_SUBMIT_INFO;
    waitInfo.semaphore = imageAvailable_[frame];
    waitInfo.stageMask = VK_PIPELINE_STAGE_2_TRANSFER_BIT;

    VkCommandBufferSubmitInfo commandInfo{};
    commandInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_SUBMIT_INFO;
    commandInfo.commandBuffer = commandBuffers_[frame];

    VkSemaphoreSubmitInfo signalInfo{};
    signalInfo.sType = VK_STRUCTURE_TYPE_SEMAPHORE_SUBMIT_INFO;
    signalInfo.semaphore = renderFinished_[frame];
    signalInfo.stageMask = VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT;

    VkSubmitInfo2 submitInfo{};
    submitInfo.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO_2;
    submitInfo.waitSemaphoreInfoCount = 1;
    submitInfo.pWaitSemaphoreInfos = &waitInfo;
    submitInfo.commandBufferInfoCount = 1;
    submitInfo.pCommandBufferInfos = &commandInfo;
    submitInfo.signalSemaphoreInfoCount = 1;
    submitInfo.pSignalSemaphoreInfos = &signalInfo;

    result = vkQueueSubmit2(graphicsQueue_, 1, &submitInfo, inFlight_[frame]);
    if (result != VK_SUCCESS) fail("vkQueueSubmit2 failed", result);

    VkPresentInfoKHR presentInfo{};
    presentInfo.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
    presentInfo.waitSemaphoreCount = 1;
    presentInfo.pWaitSemaphores = &renderFinished_[frame];
    presentInfo.swapchainCount = 1;
    presentInfo.pSwapchains = &swapchain_;
    presentInfo.pImageIndices = &imageIndex;

    const VkResult presentResult = vkQueuePresentKHR(graphicsQueue_, &presentInfo);
    imageInitialized_[imageIndex] = true;
    ++frameIndex_;

    if (presentResult == VK_ERROR_OUT_OF_DATE_KHR || presentResult == VK_SUBOPTIMAL_KHR || resizeRequested_) {
        recreateSwapchain();
        return;
    }
    if (presentResult != VK_SUCCESS) fail("vkQueuePresentKHR failed", presentResult);
}

} // namespace vf
