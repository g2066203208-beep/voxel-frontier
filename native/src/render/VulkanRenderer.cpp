#include "vf/render/VulkanRenderer.hpp"

#include "PlanetShaders.hpp"

#include <SDL3/SDL.h>
#include <SDL3/SDL_vulkan.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace vf {

namespace {

struct PushConstants {
    glm::mat4 viewProjection{1.0F};
    glm::vec4 cameraPosition{0.0F};
    glm::vec4 sunDirection{0.38F, 0.83F, 0.41F, 0.0F};
    glm::vec4 sunColorIntensity{1.0F, 1.0F, 1.0F, 2.2F};
    glm::vec4 objectRotation{0.0F, 0.0F, 0.0F, 1.0F};
};

static_assert(sizeof(PushConstants) <= 128U, "planet push constants must fit the Vulkan minimum guarantee");

[[nodiscard]] glm::vec3 safeNormalizeFloat(
    const glm::vec3& value,
    const glm::vec3& fallback = {0.38F, 0.83F, 0.41F}) noexcept {
    const float lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-10F) return glm::normalize(fallback);
    return value / std::sqrt(lengthSquared);
}

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

[[nodiscard]] VkShaderModule createShaderModule(
    VkDevice device,
    const unsigned char* bytes,
    std::size_t byteCount) {
    if (!bytes || byteCount == 0U || (byteCount % 4U) != 0U) fail("Invalid embedded SPIR-V shader");

    VkShaderModuleCreateInfo createInfo{};
    createInfo.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    createInfo.codeSize = byteCount;
    createInfo.pCode = reinterpret_cast<const std::uint32_t*>(bytes);

    VkShaderModule module = VK_NULL_HANDLE;
    const VkResult result = vkCreateShaderModule(device, &createInfo, nullptr, &module);
    if (result != VK_SUCCESS) fail("vkCreateShaderModule failed", result);
    return module;
}

[[nodiscard]] VkDeviceSize growCapacity(VkDeviceSize current, VkDeviceSize required, VkDeviceSize minimum) {
    VkDeviceSize capacity = std::max(current, minimum);
    while (capacity < required) {
        if (capacity > std::numeric_limits<VkDeviceSize>::max() / 2U) return required;
        capacity *= 2U;
    }
    return capacity;
}

[[nodiscard]] glm::vec4 matrixRow(const glm::mat4& matrix, int row) noexcept {
    return {matrix[0][row], matrix[1][row], matrix[2][row], matrix[3][row]};
}

[[nodiscard]] glm::vec4 normalizedPlane(glm::vec4 plane) noexcept {
    const float normalLength = glm::length(glm::vec3(plane));
    return normalLength > 1.0e-7F ? plane / normalLength : plane;
}

[[nodiscard]] std::array<glm::vec4, 6> extractFrustumPlanes(const glm::mat4& viewProjection) noexcept {
    const glm::vec4 r0 = matrixRow(viewProjection, 0);
    const glm::vec4 r1 = matrixRow(viewProjection, 1);
    const glm::vec4 r2 = matrixRow(viewProjection, 2);
    const glm::vec4 r3 = matrixRow(viewProjection, 3);
    // Vulkan clip depth is 0..w, therefore near = row2 and far = row3-row2.
    return {
        normalizedPlane(r3 + r0),
        normalizedPlane(r3 - r0),
        normalizedPlane(r3 + r1),
        normalizedPlane(r3 - r1),
        normalizedPlane(r2),
        normalizedPlane(r3 - r2),
    };
}

[[nodiscard]] bool sphereIntersectsFrustum(
    const std::array<glm::vec4, 6>& planes,
    const glm::vec3& center,
    float radius) noexcept {
    const float conservativeRadius = radius + 0.20F;
    for (const glm::vec4& plane : planes) {
        const float distance = glm::dot(glm::vec3(plane), center) + plane.w;
        if (distance < -conservativeRadius) return false;
    }
    return true;
}

[[nodiscard]] bool rangeVisible(
    const PlanetDrawRange& range,
    const std::array<glm::vec4, 6>& frustumPlanes,
    const glm::mat4& viewProjection,
    const glm::dvec3& cameraPosition,
    const glm::dquat& objectRotation,
    float horizonOccluderRadius,
    std::uint32_t viewportHeight) noexcept {
    const glm::dvec3 worldCenter = objectRotation * glm::dvec3(range.boundsCenter);
    const glm::dvec3 relativeCenterD = worldCenter - cameraPosition;
    const glm::vec3 relativeCenter = glm::vec3(relativeCenterD);
    const double rangeRadius = static_cast<double>(range.boundsRadius);

    if (!sphereIntersectsFrustum(frustumPlanes, relativeCenter, range.boundsRadius)) return false;

    // Conservative planetary horizon rejection. For every point x in the batch sphere,
    // dot(camera,x) <= dot(camera,center)+|camera|*batchRadius. If even that maximum lies
    // behind the guaranteed-solid inner sphere, no ray from the camera can see the batch.
    const double cameraDistance = glm::length(cameraPosition);
    const double innerRadius = static_cast<double>(horizonOccluderRadius);
    if (innerRadius > 0.0 && cameraDistance > innerRadius + 0.5) {
        const double maximumDot = glm::dot(cameraPosition, worldCenter)
            + cameraDistance * (rangeRadius + 0.35);
        const double conservativeInnerRadius = std::max(0.0, innerRadius - 0.35);
        if (maximumDot < conservativeInnerRadius * conservativeInnerRadius) return false;
    }

    // Whole-batch sub-pixel rejection is only enabled for semantic small assets. We use the
    // closest possible point on the batch sphere, so a face-spanning tree/rock batch is never
    // discarded just because its center is far away.
    if (range.representativeRadius > 0.0F && viewportHeight > 0U) {
        const double closestDistance = std::max(1.0, glm::length(relativeCenterD) - rangeRadius);
        const glm::vec4 row1 = matrixRow(viewProjection, 1);
        const double projectionYScale = glm::length(glm::dvec3(row1.x, row1.y, row1.z));
        const double projectedRadiusPixels = 0.5 * static_cast<double>(viewportHeight)
            * projectionYScale * static_cast<double>(range.representativeRadius) / closestDistance;
        if (projectedRadiusPixels < 0.65) return false;
    }

    return true;
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
    createSwapchainResources();
}

VulkanRenderer::~VulkanRenderer() {
    if (device_ != VK_NULL_HANDLE) vkDeviceWaitIdle(device_);

    for (auto& dynamicMesh : dynamicMeshes_) destroyDynamicFrameMesh(dynamicMesh);
    destroyMesh();
    destroySwapchainResources();
    destroySwapchain();

    for (std::uint32_t i = 0; i < kFramesInFlight; ++i) {
        if (inFlight_[i] != VK_NULL_HANDLE) vkDestroyFence(device_, inFlight_[i], nullptr);
        if (renderFinished_[i] != VK_NULL_HANDLE) vkDestroySemaphore(device_, renderFinished_[i], nullptr);
        if (imageAvailable_[i] != VK_NULL_HANDLE) vkDestroySemaphore(device_, imageAvailable_[i], nullptr);
    }

    if (commandPool_ != VK_NULL_HANDLE) vkDestroyCommandPool(device_, commandPool_, nullptr);
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

    if (loaderVersion < VK_API_VERSION_1_3) fail("Voxel Frontier requires Vulkan 1.3 or newer");
    apiVersion_ = std::min(loaderVersion, static_cast<std::uint32_t>(VK_API_VERSION_1_4));

    Uint32 extensionCount = 0;
    const char* const* extensions = SDL_Vulkan_GetInstanceExtensions(&extensionCount);
    if (!extensions || extensionCount == 0) {
        throw std::runtime_error(std::string{"SDL_Vulkan_GetInstanceExtensions failed: "} + SDL_GetError());
    }

    VkApplicationInfo appInfo{};
    appInfo.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    appInfo.pApplicationName = "Voxel Frontier";
    appInfo.applicationVersion = VK_MAKE_API_VERSION(0, 0, 4, 0);
    appInfo.pEngineName = "Voxel Frontier Native Engine";
    appInfo.engineVersion = VK_MAKE_API_VERSION(0, 0, 4, 0);
    appInfo.apiVersion = apiVersion_;

    VkInstanceCreateInfo createInfo{};
    createInfo.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    createInfo.pApplicationInfo = &appInfo;
    createInfo.enabledExtensionCount = extensionCount;
    createInfo.ppEnabledExtensionNames = extensions;

    const VkResult result = vkCreateInstance(instance_ == VK_NULL_HANDLE ? device_ : device_, &createInfo, nullptr, &instance_);
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
        if (features13.synchronization2 != VK_TRUE || features13.dynamicRendering != VK_TRUE) continue;

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
        fail("No GPU satisfies Vulkan 1.3 + dynamicRendering + synchronization2 + swapchain requirements");
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
    features13.dynamicRendering = VK_TRUE;
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
    if (!SDL_GetWindowSizeInPixels(window_, &pixelWidth, &pixelHeight) || pixelWidth <= 0 || pixelHeight <= 0) return;

    VkSurfaceCapabilitiesKHR capabilities{};
    VkResult result = vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physicalDevice_, surface_, &capabilities);
    if (result != VK_SUCCESS) fail("vkGetPhysicalDeviceSurfaceCapabilitiesKHR failed", result);
    if ((capabilities.supportedUsageFlags & VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT) == 0U) {
        fail("Swapchain surface does not support color attachments");
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
        extent.width = std::clamp(static_cast<std::uint32_t>(pixelWidth), capabilities.minImageExtent.width, capabilities.maxImageExtent.width);
        extent.height = std::clamp(static_cast<std::uint32_t>(pixelHeight), capabilities.minImageExtent.height, capabilities.maxImageExtent.height);
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
    createInfo.imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
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

void VulkanRenderer::createSwapchainResources() {
    if (swapchain_ == VK_NULL_HANDLE) return;

    swapchainImageViews_.reserve(swapchainImages_.size());
    for (VkImage image : swapchainImages_) {
        VkImageViewCreateInfo viewInfo{};
        viewInfo.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        viewInfo.image = image;
        viewInfo.viewType = VK_IMAGE_VIEW_TYPE_2D;
        viewInfo.format = swapchainFormat_;
        viewInfo.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        viewInfo.subresourceRange.baseMipLevel = 0;
        viewInfo.subresourceRange.levelCount = 1;
        viewInfo.subresourceRange.baseArrayLayer = 0;
        viewInfo.subresourceRange.layerCount = 1;

        VkImageView imageView = VK_NULL_HANDLE;
        const VkResult result = vkCreateImageView(device_, &viewInfo, nullptr, &imageView);
        if (result != VK_SUCCESS) fail("vkCreateImageView(swapchain) failed", result);
        swapchainImageViews_.push_back(imageView);
    }

    createDepthResources();
    createGraphicsPipeline();
}

void VulkanRenderer::destroySwapchainResources() noexcept {
    if (graphicsPipeline_ != VK_NULL_HANDLE) {
        vkDestroyPipeline(device_, graphicsPipeline_, nullptr);
        graphicsPipeline_ = VK_NULL_HANDLE;
    }
    if (pipelineLayout_ != VK_NULL_HANDLE) {
        vkDestroyPipelineLayout(device_, pipelineLayout_, nullptr);
        pipelineLayout_ = VK_NULL_HANDLE;
    }
    if (depthImageView_ != VK_NULL_HANDLE) {
        vkDestroyImageView(device_, depthImageView_, nullptr);
        depthImageView_ = VK_NULL_HANDLE;
    }
    if (depthImage_ != VK_NULL_HANDLE) {
        vkDestroyImage(device_, depthImage_, nullptr);
        depthImage_ = VK_NULL_HANDLE;
    }
    if (depthMemory_ != VK_NULL_HANDLE) {
        vkFreeMemory(device_, depthMemory_, nullptr);
        depthMemory_ = VK_NULL_HANDLE;
    }
    for (VkImageView view : swapchainImageViews_) {
        if (view != VK_NULL_HANDLE) vkDestroyImageView(device_, view, nullptr);
    }
    swapchainImageViews_.clear();
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
    destroySwapchainResources();
    destroySwapchain();
    createSwapchain();
    createSwapchainResources();
}

std::uint32_t VulkanRenderer::findMemoryType(std::uint32_t typeFilter, VkMemoryPropertyFlags properties) const {
    VkPhysicalDeviceMemoryProperties memoryProperties{};
    vkGetPhysicalDeviceMemoryProperties(physicalDevice_, &memoryProperties);

    for (std::uint32_t i = 0; i < memoryProperties.memoryTypeCount; ++i) {
        if ((typeFilter & (1U << i)) != 0U &&
            (memoryProperties.memoryTypes[i].propertyFlags & properties) == properties) {
            return i;
        }
    }
    fail("No suitable Vulkan memory type found");
}

void VulkanRenderer::createBuffer(
    VkDeviceSize size,
    VkBufferUsageFlags usage,
    VkMemoryPropertyFlags memoryProperties,
    VkBuffer& buffer,
    VkDeviceMemory& memory) {
    VkBufferCreateInfo bufferInfo{};
    bufferInfo.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    bufferInfo.size = size;
    bufferInfo.usage = usage;
    bufferInfo.sharingMode = VK_SHARING_MODE_EXCLUSIVE;

    VkResult result = vkCreateBuffer(device_, &bufferInfo, nullptr, &buffer);
    if (result != VK_SUCCESS) fail("vkCreateBuffer failed", result);

    VkMemoryRequirements requirements{};
    vkGetBufferMemoryRequirements(device_, buffer, &requirements);

    VkMemoryAllocateInfo allocInfo{};
    allocInfo.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    allocInfo.allocationSize = requirements.size;
    allocInfo.memoryTypeIndex = findMemoryType(requirements.memoryTypeBits, memoryProperties);

    result = vkAllocateMemory(device_, &allocInfo, nullptr, &memory);
    if (result != VK_SUCCESS) fail("vkAllocateMemory(buffer) failed", result);
    result = vkBindBufferMemory(device_, buffer, memory, 0);
    if (result != VK_SUCCESS) fail("vkBindBufferMemory failed", result);
}

void VulkanRenderer::createDepthResources() {
    VkImageCreateInfo imageInfo{};
    imageInfo.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    imageInfo.imageType = VK_IMAGE_TYPE_2D;
    imageInfo.extent = {swapchainExtent_.width, swapchainExtent_.height, 1U};
    imageInfo.mipLevels = 1;
    imageInfo.arrayLayers = 1;
    imageInfo.format = depthFormat_;
    imageInfo.tiling = VK_IMAGE_TILING_OPTIMAL;
    imageInfo.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    imageInfo.usage = VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT;
    imageInfo.samples = VK_SAMPLE_COUNT_1_BIT;
    imageInfo.sharingMode = VK_SHARING_MODE_EXCLUSIVE;

    VkResult result = vkCreateImage(device_, &imageInfo, nullptr, &depthImage_);
    if (result != VK_SUCCESS) fail("vkCreateImage(depth) failed", result);

    VkMemoryRequirements requirements{};
    vkGetImageMemoryRequirements(device_, depthImage_, &requirements);

    VkMemoryAllocateInfo allocInfo{};
    allocInfo.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    allocInfo.allocationSize = requirements.size;
    allocInfo.memoryTypeIndex = findMemoryType(requirements.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);

    result = vkAllocateMemory(device_, &allocInfo, nullptr, &depthMemory_);
    if (result != VK_SUCCESS) fail("vkAllocateMemory(depth) failed", result);
    result = vkBindImageMemory(device_, depthImage_, depthMemory_, 0);
    if (result != VK_SUCCESS) fail("vkBindImageMemory(depth) failed", result);

    VkImageViewCreateInfo viewInfo{};
    viewInfo.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    viewInfo.image = depthImage_;
    viewInfo.viewType = VK_IMAGE_VIEW_TYPE_2D;
    viewInfo.format = depthFormat_;
    viewInfo.subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT;
    viewInfo.subresourceRange.baseMipLevel = 0;
    viewInfo.subresourceRange.levelCount = 1;
    viewInfo.subresourceRange.baseArrayLayer = 0;
    viewInfo.subresourceRange.layerCount = 1;

    result = vkCreateImageView(device_, &viewInfo, nullptr, &depthImageView_);
    if (result != VK_SUCCESS) fail("vkCreateImageView(depth) failed", result);
}

void VulkanRenderer::createGraphicsPipeline() {
    const VkShaderModule vertexShader = createShaderModule(
        device_, shaders::kPlanetVertexSpv, shaders::kPlanetVertexSpvSize);
    const VkShaderModule fragmentShader = createShaderModule(
        device_, shaders::kPlanetFragmentSpv, shaders::kPlanetFragmentSpvSize);

    VkPipelineShaderStageCreateInfo vertexStage{};
    vertexStage.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    vertexStage.stage = VK_SHADER_STAGE_VERTEX_BIT;
    vertexStage.module = vertexShader;
    vertexStage.pName = "vertexMain";

    VkPipelineShaderStageCreateInfo fragmentStage{};
    fragmentStage.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    fragmentStage.stage = VK_SHADER_STAGE_FRAGMENT_BIT;
    fragmentStage.module = fragmentShader;
    fragmentStage.pName = "fragmentMain";

    const VkPipelineShaderStageCreateInfo stages[] = {vertexStage, fragmentStage};

    VkVertexInputBindingDescription binding{};
    binding.binding = 0;
    binding.stride = sizeof(PlanetVertex);
    binding.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;

    std::array<VkVertexInputAttributeDescription, 3> attributes{};
    attributes[0] = {0, 0, VK_FORMAT_R32G32B32_SFLOAT, static_cast<std::uint32_t>(offsetof(PlanetVertex, position))};
    attributes[1] = {1, 0, VK_FORMAT_R32G32B32_SFLOAT, static_cast<std::uint32_t>(offsetof(PlanetVertex, normal))};
    attributes[2] = {2, 0, VK_FORMAT_R32G32B32_SFLOAT, static_cast<std::uint32_t>(offsetof(PlanetVertex, color))};

    VkPipelineVertexInputStateCreateInfo vertexInput{};
    vertexInput.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    vertexInput.vertexBindingDescriptionCount = 1;
    vertexInput.pVertexBindingDescriptions = &binding;
    vertexInput.vertexAttributeDescriptionCount = static_cast<std::uint32_t>(attributes.size());
    vertexInput.pVertexAttributeDescriptions = attributes.data();

    VkPipelineInputAssemblyStateCreateInfo inputAssembly{};
    inputAssembly.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    inputAssembly.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

    VkPipelineViewportStateCreateInfo viewportState{};
    viewportState.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    viewportState.viewportCount = 1;
    viewportState.scissorCount = 1;

    VkPipelineRasterizationStateCreateInfo rasterizer{};
    rasterizer.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    rasterizer.depthClampEnable = VK_FALSE;
    rasterizer.rasterizerDiscardEnable = VK_FALSE;
    rasterizer.polygonMode = VK_POLYGON_MODE_FILL;
    rasterizer.cullMode = VK_CULL_MODE_NONE;
    rasterizer.frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE;
    rasterizer.depthBiasEnable = VK_FALSE;
    rasterizer.lineWidth = 1.0F;

    VkPipelineMultisampleStateCreateInfo multisampling{};
    multisampling.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    multisampling.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;

    VkPipelineDepthStencilStateCreateInfo depthStencil{};
    depthStencil.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
    depthStencil.depthTestEnable = VK_TRUE;
    depthStencil.depthWriteEnable = VK_TRUE;
    depthStencil.depthCompareOp = VK_COMPARE_OP_LESS;
    depthStencil.depthBoundsTestEnable = VK_FALSE;
    depthStencil.stencilTestEnable = VK_FALSE;

    VkPipelineColorBlendAttachmentState colorBlendAttachment{};
    colorBlendAttachment.blendEnable = VK_FALSE;
    colorBlendAttachment.colorWriteMask =
        VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT | VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;

    VkPipelineColorBlendStateCreateInfo colorBlending{};
    colorBlending.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    colorBlending.attachmentCount = 1;
    colorBlending.pAttachments = &colorBlendAttachment;

    constexpr VkDynamicState dynamicStates[] = {
        VK_DYNAMIC_STATE_VIEWPORT,
        VK_DYNAMIC_STATE_SCISSOR,
        VK_DYNAMIC_STATE_CULL_MODE,
    };
    VkPipelineDynamicStateCreateInfo dynamicState{};
    dynamicState.sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
    dynamicState.dynamicStateCount = static_cast<std::uint32_t>(std::size(dynamicStates));
    dynamicState.pDynamicStates = dynamicStates;

    VkPushConstantRange pushRange{};
    pushRange.stageFlags = VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT;
    pushRange.offset = 0;
    pushRange.size = sizeof(PushConstants);

    VkPipelineLayoutCreateInfo layoutInfo{};
    layoutInfo.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    layoutInfo.pushConstantRangeCount = 1;
    layoutInfo.pPushConstantRanges = &pushRange;
    VkResult result = vkCreatePipelineLayout(device_, &layoutInfo, nullptr, &pipelineLayout_);
    if (result != VK_SUCCESS) fail("vkCreatePipelineLayout failed", result);

    VkPipelineRenderingCreateInfo renderingInfo{};
    renderingInfo.sType = VK_STRUCTURE_TYPE_PIPELINE_RENDERING_CREATE_INFO;
    renderingInfo.colorAttachmentCount = 1;
    renderingInfo.pColorAttachmentFormats = &swapchainFormat_;
    renderingInfo.depthAttachmentFormat = depthFormat_;

    VkGraphicsPipelineCreateInfo pipelineInfo{};
    pipelineInfo.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    pipelineInfo.pNext = &renderingInfo;
    pipelineInfo.stageCount = 2;
    pipelineInfo.pStages = stages;
    pipelineInfo.pVertexInputState = &vertexInput;
    pipelineInfo.pInputAssemblyState = &inputAssembly;
    pipelineInfo.pViewportState = &viewportState;
    pipelineInfo.pRasterizationState = &rasterizer;
    pipelineInfo.pMultisampleState = &multisampling;
    pipelineInfo.pDepthStencilState = &depthStencil;
    pipelineInfo.pColorBlendState = &colorBlending;
    pipelineInfo.pDynamicState = &dynamicState;
    pipelineInfo.layout = pipelineLayout_;

    result = vkCreateGraphicsPipelines(device_, VK_NULL_HANDLE, 1, &pipelineInfo, nullptr, &graphicsPipeline_);
    vkDestroyShaderModule(device_, fragmentShader, nullptr);
    vkDestroyShaderModule(device_, vertexShader, nullptr);
    if (result != VK_SUCCESS) fail("vkCreateGraphicsPipelines failed", result);
}

void VulkanRenderer::destroyMesh() noexcept {
    if (indexBuffer_ != VK_NULL_HANDLE) {
        vkDestroyBuffer(device_, indexBuffer_, nullptr);
        indexBuffer_ = VK_NULL_HANDLE;
    }
    if (indexMemory_ != VK_NULL_HANDLE) {
        vkFreeMemory(device_, indexMemory_, nullptr);
        indexMemory_ = VK_NULL_HANDLE;
    }
    if (vertexBuffer_ != VK_NULL_HANDLE) {
        vkDestroyBuffer(device_, vertexBuffer_, nullptr);
        vertexBuffer_ = VK_NULL_HANDLE;
    }
    if (vertexMemory_ != VK_NULL_HANDLE) {
        vkFreeMemory(device_, vertexMemory_, nullptr);
        vertexMemory_ = VK_NULL_HANDLE;
    }
    indexCount_ = 0;
    staticDrawRanges_.clear();
    horizonOccluderRadius_ = 0.0F;
    visibleStaticRangeCount_ = 0U;
    submittedStaticTriangleCount_ = 0U;
}

void VulkanRenderer::destroyDynamicFrameMesh(DynamicFrameMesh& mesh) noexcept {
    if (mesh.mappedVertices != nullptr && mesh.vertexMemory != VK_NULL_HANDLE) vkUnmapMemory(device_, mesh.vertexMemory);
    if (mesh.mappedIndices != nullptr && mesh.indexMemory != VK_NULL_HANDLE) vkUnmapMemory(device_, mesh.indexMemory);
    mesh.mappedVertices = nullptr;
    mesh.mappedIndices = nullptr;
    if (mesh.indexBuffer != VK_NULL_HANDLE) vkDestroyBuffer(device_, mesh.indexBuffer, nullptr);
    if (mesh.indexMemory != VK_NULL_HANDLE) vkFreeMemory(device_, mesh.indexMemory, nullptr);
    if (mesh.vertexBuffer != VK_NULL_HANDLE) vkDestroyBuffer(device_, mesh.vertexBuffer, nullptr);
    if (mesh.vertexMemory != VK_NULL_HANDLE) vkFreeMemory(device_, mesh.vertexMemory, nullptr);
    mesh = {};
}

void VulkanRenderer::ensureDynamicFrameCapacity(
    DynamicFrameMesh& mesh,
    VkDeviceSize vertexBytes,
    VkDeviceSize indexBytes) {
    if (vertexBytes <= mesh.vertexCapacityBytes && indexBytes <= mesh.indexCapacityBytes) return;

    const VkDeviceSize newVertexCapacity = growCapacity(mesh.vertexCapacityBytes, vertexBytes, 64U * 1024U);
    const VkDeviceSize newIndexCapacity = growCapacity(mesh.indexCapacityBytes, indexBytes, 32U * 1024U);
    destroyDynamicFrameMesh(mesh);

    createBuffer(
        newVertexCapacity,
        VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
        mesh.vertexBuffer,
        mesh.vertexMemory);
    createBuffer(
        newIndexCapacity,
        VK_BUFFER_USAGE_INDEX_BUFFER_BIT,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
        mesh.indexBuffer,
        mesh.indexMemory);

    VkResult result = vkMapMemory(device_, mesh.vertexMemory, 0, newVertexCapacity, 0, &mesh.mappedVertices);
    if (result != VK_SUCCESS) fail("vkMapMemory(dynamic vertex) failed", result);
    result = vkMapMemory(device_, mesh.indexMemory, 0, newIndexCapacity, 0, &mesh.mappedIndices);
    if (result != VK_SUCCESS) fail("vkMapMemory(dynamic index) failed", result);
    mesh.vertexCapacityBytes = newVertexCapacity;
    mesh.indexCapacityBytes = newIndexCapacity;
}

void VulkanRenderer::setDynamicMesh(const PlanetMesh& mesh) {
    pendingDynamicVertices_ = mesh.vertices;
    pendingDynamicIndices_ = mesh.indices;
}

void VulkanRenderer::clearDynamicMesh() {
    pendingDynamicVertices_.clear();
    pendingDynamicIndices_.clear();
}

void VulkanRenderer::uploadDynamicMeshForFrame(std::uint32_t frame) {
    auto& mesh = dynamicMeshes_[frame];
    if (pendingDynamicVertices_.empty() || pendingDynamicIndices_.empty()) {
        mesh.indexCount = 0;
        return;
    }

    const VkDeviceSize vertexBytes = static_cast<VkDeviceSize>(pendingDynamicVertices_.size() * sizeof(PlanetVertex));
    const VkDeviceSize indexBytes = static_cast<VkDeviceSize>(pendingDynamicIndices_.size() * sizeof(std::uint32_t));
    ensureDynamicFrameCapacity(mesh, vertexBytes, indexBytes);
    std::memcpy(mesh.mappedVertices, pendingDynamicVertices_.data(), static_cast<std::size_t>(vertexBytes));
    std::memcpy(mesh.mappedIndices, pendingDynamicIndices_.data(), static_cast<std::size_t>(indexBytes));
    mesh.indexCount = static_cast<std::uint32_t>(pendingDynamicIndices_.size());
}

void VulkanRenderer::drawBoundMesh(
    VkCommandBuffer commandBuffer,
    VkBuffer vertexBuffer,
    VkBuffer indexBuffer,
    std::uint32_t indexCount,
    std::uint32_t firstIndex) {
    if (vertexBuffer == VK_NULL_HANDLE || indexBuffer == VK_NULL_HANDLE || indexCount == 0U) return;
    constexpr VkDeviceSize offset = 0;
    vkCmdBindVertexBuffers(commandBuffer, 0, 1, &vertexBuffer, &offset);
    vkCmdBindIndexBuffer(commandBuffer, indexBuffer, 0, VK_INDEX_TYPE_UINT32);
    vkCmdDrawIndexed(commandBuffer, indexCount, 1, firstIndex, 0, 0);
}

void VulkanRenderer::uploadPlanetMesh(const PlanetMesh& mesh) {
    if (mesh.vertices.empty() || mesh.indices.empty()) fail("Cannot upload an empty planet mesh");
    vkDeviceWaitIdle(device_);
    destroyMesh();

    const VkDeviceSize vertexBytes = static_cast<VkDeviceSize>(mesh.vertices.size() * sizeof(PlanetVertex));
    const VkDeviceSize indexBytes = static_cast<VkDeviceSize>(mesh.indices.size() * sizeof(std::uint32_t));

    createBuffer(
        vertexBytes,
        VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
        vertexBuffer_,
        vertexMemory_);
    createBuffer(
        indexBytes,
        VK_BUFFER_USAGE_INDEX_BUFFER_BIT,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
        indexBuffer_,
        indexMemory_);

    void* mapped = nullptr;
    VkResult result = vkMapMemory(device_, vertexMemory_, 0, vertexBytes, 0, &mapped);
    if (result != VK_SUCCESS) fail("vkMapMemory(vertex) failed", result);
    std::memcpy(mapped, mesh.vertices.data(), static_cast<std::size_t>(vertexBytes));
    vkUnmapMemory(device_, vertexMemory_);

    mapped = nullptr;
    result = vkMapMemory(device_, indexMemory_, 0, indexBytes, 0, &mapped);
    if (result != VK_SUCCESS) fail("vkMapMemory(index) failed", result);
    std::memcpy(mapped, mesh.indices.data(), static_cast<std::size_t>(indexBytes));
    vkUnmapMemory(device_, indexMemory_);

    indexCount_ = static_cast<std::uint32_t>(mesh.indices.size());
    staticDrawRanges_ = mesh.drawRanges;
    horizonOccluderRadius_ = mesh.horizonOccluderRadius;
}

void VulkanRenderer::drawFrame(
    const glm::vec3& clearColor,
    const glm::mat4& viewProjection,
    const glm::dvec3& cameraPosition,
    const glm::vec3& sunDirectionToLight,
    const glm::vec3& sunLinearColor,
    float sunIntensity,
    const glm::dquat& staticObjectRotation) {
    if (resizeRequested_) recreateSwapchain();
    if (swapchain_ == VK_NULL_HANDLE || graphicsPipeline_ == VK_NULL_HANDLE) return;

    const auto frame = frameIndex_ % kFramesInFlight;
    VkResult result = vkWaitForFences(device_, 1, &inFlight_[frame], VK_TRUE, UINT64_MAX);
    if (result != VK_SUCCESS) fail("vkWaitForFences failed", result);

    uploadDynamicMeshForFrame(frame);

    std::uint32_t imageIndex = 0;
    result = vkAcquireNextImageKHR(device_, swapchain_, UINT64_MAX, imageAvailable_[frame], VK_NULL_HANDLE, &imageIndex);
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

    VkImageMemoryBarrier2 colorBarrier{};
    colorBarrier.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;
    colorBarrier.srcStageMask = VK_PIPELINE_STAGE_2_NONE;
    colorBarrier.srcAccessMask = VK_ACCESS_2_NONE;
    colorBarrier.dstStageMask = VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT;
    colorBarrier.dstAccessMask = VK_ACCESS_2_COLOR_ATTACHMENT_WRITE_BIT;
    colorBarrier.oldLayout = imageInitialized_[imageIndex] ? VK_IMAGE_LAYOUT_PRESENT_SRC_KHR : VK_IMAGE_LAYOUT_UNDEFINED;
    colorBarrier.newLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    colorBarrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    colorBarrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    colorBarrier.image = swapchainImages_[imageIndex];
    colorBarrier.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    colorBarrier.subresourceRange.baseMipLevel = 0;
    colorBarrier.subresourceRange.levelCount = 1;
    colorBarrier.subresourceRange.baseArrayLayer = 0;
    colorBarrier.subresourceRange.layerCount = 1;

    VkImageMemoryBarrier2 depthBarrier{};
    depthBarrier.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;
    depthBarrier.srcStageMask = VK_PIPELINE_STAGE_2_NONE;
    depthBarrier.srcAccessMask = VK_ACCESS_2_NONE;
    depthBarrier.dstStageMask = VK_PIPELINE_STAGE_2_EARLY_FRAGMENT_TESTS_BIT | VK_PIPELINE_STAGE_2_LATE_FRAGMENT_TESTS_BIT;
    depthBarrier.dstAccessMask = VK_ACCESS_2_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT;
    depthBarrier.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    depthBarrier.newLayout = VK_IMAGE_LAYOUT_DEPTH_ATTACHMENT_OPTIMAL;
    depthBarrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    depthBarrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    depthBarrier.image = depthImage_;
    depthBarrier.subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT;
    depthBarrier.subresourceRange.baseMipLevel = 0;
    depthBarrier.subresourceRange.levelCount = 1;
    depthBarrier.subresourceRange.baseArrayLayer = 0;
    depthBarrier.subresourceRange.layerCount = 1;

    const std::array<VkImageMemoryBarrier2, 2> barriers{colorBarrier, depthBarrier};
    VkDependencyInfo dependency{};
    dependency.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO;
    dependency.imageMemoryBarrierCount = static_cast<std::uint32_t>(barriers.size());
    dependency.pImageMemoryBarriers = barriers.data();
    vkCmdPipelineBarrier2(commandBuffers_[frame], &dependency);

    VkRenderingAttachmentInfo colorAttachment{};
    colorAttachment.sType = VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO;
    colorAttachment.imageView = swapchainImageViews_[imageIndex];
    colorAttachment.imageLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    colorAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    colorAttachment.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
    colorAttachment.clearValue.color = {{clearColor.r, clearColor.g, clearColor.b, 1.0F}};

    VkRenderingAttachmentInfo depthAttachment{};
    depthAttachment.sType = VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO;
    depthAttachment.imageView = depthImageView_;
    depthAttachment.imageLayout = VK_IMAGE_LAYOUT_DEPTH_ATTACHMENT_OPTIMAL;
    depthAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    depthAttachment.storeOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    depthAttachment.clearValue.depthStencil = {1.0F, 0U};

    VkRenderingInfo renderingInfo{};
    renderingInfo.sType = VK_STRUCTURE_TYPE_RENDERING_INFO;
    renderingInfo.renderArea.offset = {0, 0};
    renderingInfo.renderArea.extent = swapchainExtent_;
    renderingInfo.layerCount = 1;
    renderingInfo.colorAttachmentCount = 1;
    renderingInfo.pColorAttachments = &colorAttachment;
    renderingInfo.pDepthAttachment = &depthAttachment;

    vkCmdBeginRendering(commandBuffers_[frame], &renderingInfo);

    VkViewport viewport{};
    viewport.x = 0.0F;
    viewport.y = 0.0F;
    viewport.width = static_cast<float>(swapchainExtent_.width);
    viewport.height = static_cast<float>(swapchainExtent_.height);
    viewport.minDepth = 0.0F;
    viewport.maxDepth = 1.0F;
    vkCmdSetViewport(commandBuffers_[frame], 0, 1, &viewport);

    VkRect2D scissor{{0, 0}, swapchainExtent_};
    vkCmdSetScissor(commandBuffers_[frame], 0, 1, &scissor);
    vkCmdBindPipeline(commandBuffers_[frame], VK_PIPELINE_BIND_POINT_GRAPHICS, graphicsPipeline_);

    PushConstants push{};
    push.viewProjection = viewProjection;
    push.cameraPosition = glm::vec4(glm::vec3(cameraPosition), 1.0F);
    push.sunDirection = glm::vec4(safeNormalizeFloat(sunDirectionToLight), 0.0F);
    push.sunColorIntensity = glm::vec4(glm::max(sunLinearColor, glm::vec3{0.0F}), std::max(0.0F, sunIntensity));
    const glm::dquat normalizedRotation = glm::normalize(staticObjectRotation);
    push.objectRotation = glm::vec4(
        static_cast<float>(normalizedRotation.x),
        static_cast<float>(normalizedRotation.y),
        static_cast<float>(normalizedRotation.z),
        static_cast<float>(normalizedRotation.w));
    vkCmdPushConstants(
        commandBuffers_[frame],
        pipelineLayout_,
        VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
        0,
        sizeof(PushConstants),
        &push);

    visibleStaticRangeCount_ = 0U;
    submittedStaticTriangleCount_ = 0U;
    const auto frustumPlanes = extractFrustumPlanes(viewProjection);

    if (staticDrawRanges_.empty()) {
        // Legacy/proxy fallback.
        vkCmdSetCullMode(commandBuffers_[frame], VK_CULL_MODE_BACK_BIT);
        drawBoundMesh(commandBuffers_[frame], vertexBuffer_, indexBuffer_, indexCount_);
        visibleStaticRangeCount_ = indexCount_ > 0U ? 1U : 0U;
        submittedStaticTriangleCount_ = indexCount_ / 3U;
    } else if (vertexBuffer_ != VK_NULL_HANDLE && indexBuffer_ != VK_NULL_HANDLE) {
        constexpr VkDeviceSize offset = 0;
        vkCmdBindVertexBuffers(commandBuffers_[frame], 0, 1, &vertexBuffer_, &offset);
        vkCmdBindIndexBuffer(commandBuffers_[frame], indexBuffer_, 0, VK_INDEX_TYPE_UINT32);
        VkCullModeFlags activeCullMode = VK_CULL_MODE_FLAG_BITS_MAX_ENUM;

        for (const PlanetDrawRange& range : staticDrawRanges_) {
            if (!rangeVisible(
                    range,
                    frustumPlanes,
                    viewProjection,
                    cameraPosition,
                    normalizedRotation,
                    horizonOccluderRadius_,
                    swapchainExtent_.height)) {
                continue;
            }

            const VkCullModeFlags wantedCullMode = range.drawClass == PlanetDrawClass::OceanPatch
                ? VK_CULL_MODE_NONE
                : VK_CULL_MODE_BACK_BIT;
            if (wantedCullMode != activeCullMode) {
                vkCmdSetCullMode(commandBuffers_[frame], wantedCullMode);
                activeCullMode = wantedCullMode;
            }
            vkCmdDrawIndexed(commandBuffers_[frame], range.indexCount, 1, range.firstIndex, 0, 0);
            ++visibleStaticRangeCount_;
            submittedStaticTriangleCount_ += range.indexCount / 3U;
        }
    }

    // Dynamic debug/celestial geometry can be open or intentionally double-sided, so keep it
    // uncullled. Static natural assets above are closed and use true back-face culling.
    push.objectRotation = {0.0F, 0.0F, 0.0F, 1.0F};
    vkCmdPushConstants(
        commandBuffers_[frame],
        pipelineLayout_,
        VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
        0,
        sizeof(PushConstants),
        &push);
    vkCmdSetCullMode(commandBuffers_[frame], VK_CULL_MODE_NONE);
    const auto& dynamicMesh = dynamicMeshes_[frame];
    drawBoundMesh(
        commandBuffers_[frame],
        dynamicMesh.vertexBuffer,
        dynamicMesh.indexBuffer,
        dynamicMesh.indexCount);

    vkCmdEndRendering(commandBuffers_[frame]);

    VkImageMemoryBarrier2 toPresent{};
    toPresent.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;
    toPresent.srcStageMask = VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT;
    toPresent.srcAccessMask = VK_ACCESS_2_COLOR_ATTACHMENT_WRITE_BIT;
    toPresent.dstStageMask = VK_PIPELINE_STAGE_2_NONE;
    toPresent.dstAccessMask = VK_ACCESS_2_NONE;
    toPresent.oldLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    toPresent.newLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
    toPresent.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toPresent.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toPresent.image = swapchainImages_[imageIndex];
    toPresent.subresourceRange = colorBarrier.subresourceRange;

    dependency.imageMemoryBarrierCount = 1;
    dependency.pImageMemoryBarriers = &toPresent;
    vkCmdPipelineBarrier2(commandBuffers_[frame], &dependency);

    result = vkEndCommandBuffer(commandBuffers_[frame]);
    if (result != VK_SUCCESS) fail("vkEndCommandBuffer failed", result);

    VkSemaphoreSubmitInfo waitInfo{};
    waitInfo.sType = VK_STRUCTURE_TYPE_SEMAPHORE_SUBMIT_INFO;
    waitInfo.semaphore = imageAvailable_[frame];
    waitInfo.stageMask = VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT;

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

    const VkResult presentResult = vkQueuePresentKHR(graphicsQueue_, 1, &presentInfo);
    imageInitialized_[imageIndex] = true;
    ++frameIndex_;

    if (presentResult == VK_ERROR_OUT_OF_DATE_KHR || presentResult == VK_SUBOPTIMAL_KHR || resizeRequested_) {
        recreateSwapchain();
        return;
    }
    if (presentResult != VK_SUCCESS) fail("vkQueuePresentKHR failed", presentResult);
}

} // namespace vf
