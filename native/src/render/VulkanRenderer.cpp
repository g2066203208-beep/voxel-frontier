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

#include <glm/ext/matrix_clip_space.hpp>
#include <glm/ext/matrix_transform.hpp>
#include <glm/gtc/matrix_inverse.hpp>

namespace vf {
namespace {

struct PushConstants {
    glm::mat4 matrix{1.0F};
    glm::vec4 data0{};
    glm::vec4 data1{};
    glm::vec4 data2{};
    glm::vec4 data3{};
};

struct SceneUniforms {
    glm::mat4 lightViewProjection{1.0F};
    glm::vec4 skyAmbientExposure{};
    glm::vec4 groundAmbientShadowTexel{};
};

static_assert(sizeof(PushConstants) == 128U, "push constants must fit Vulkan's minimum 128-byte guarantee");
static_assert(sizeof(SceneUniforms) == 96U, "scene uniform layout must match Slang");

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
    VkShaderModuleCreateInfo info{};
    info.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    info.codeSize = byteCount;
    info.pCode = reinterpret_cast<const std::uint32_t*>(bytes);
    VkShaderModule module = VK_NULL_HANDLE;
    const VkResult result = vkCreateShaderModule(device, &info, nullptr, &module);
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

[[nodiscard]] glm::mat4 makeShadowViewProjection(const glm::vec3& sunDirection, const glm::vec3& cameraForward) {
    const glm::vec3 light = safeNormalizeFloat(sunDirection);
    const glm::vec3 forward = safeNormalizeFloat(cameraForward, {0.0F, 0.0F, -1.0F});
    const glm::vec3 focus = forward * 28.0F;
    const glm::vec3 eye = focus + light * 210.0F;
    glm::vec3 up{0.0F, 1.0F, 0.0F};
    if (std::abs(glm::dot(light, up)) > 0.94F) up = {1.0F, 0.0F, 0.0F};
    const glm::mat4 view = glm::lookAtRH(eye, focus, up);
    glm::mat4 projection = glm::orthoRH_ZO(-125.0F, 125.0F, -125.0F, 125.0F, 1.0F, 480.0F);
    projection[1][1] *= -1.0F;
    return projection * view;
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
    createDescriptorResources();
    createSwapchain();
    createSwapchainResources();
}

VulkanRenderer::~VulkanRenderer() {
    if (device_ != VK_NULL_HANDLE) vkDeviceWaitIdle(device_);
    for (auto& dynamicMesh : dynamicMeshes_) destroyDynamicFrameMesh(dynamicMesh);
    destroyMesh();
    destroySwapchainResources();
    destroySwapchain();
    destroyDescriptorResources();
    for (std::uint32_t i = 0; i < kFramesInFlight; ++i) {
        if (inFlight_[i] != VK_NULL_HANDLE) vkDestroyFence(device_, inFlight_[i], nullptr);
        if (renderFinished_[i] != VK_NULL_HANDLE) vkDestroySemaphore(device_, renderFinished_[i], nullptr);
        if (imageAvailable_[i] != VK_NULL_HANDLE) vkDestroySemaphore(device_, imageAvailable_[i], nullptr);
    }
    if (commandPool_ != VK_NULL_HANDLE) vkDestroyCommandPool(device_, commandPool_, nullptr);
    if (device_ != VK_NULL_HANDLE) vkDestroyDevice(device_, nullptr);
    if (surface_ != VK_NULL_HANDLE && instance_ != VK_NULL_HANDLE) SDL_Vulkan_DestroySurface(instance_, surface_, nullptr);
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
    if (!extensions || extensionCount == 0) throw std::runtime_error(std::string{"SDL Vulkan extensions unavailable: "} + SDL_GetError());

    VkApplicationInfo app{};
    app.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    app.pApplicationName = "Voxel Frontier";
    app.applicationVersion = VK_MAKE_API_VERSION(0, 0, 9, 2);
    app.pEngineName = "Voxel Frontier Native Engine";
    app.engineVersion = VK_MAKE_API_VERSION(0, 0, 9, 2);
    app.apiVersion = apiVersion_;

    VkInstanceCreateInfo info{};
    info.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    info.pApplicationInfo = &app;
    info.enabledExtensionCount = extensionCount;
    info.ppEnabledExtensionNames = extensions;
    const VkResult result = vkCreateInstance(&info, nullptr, &instance_);
    if (result != VK_SUCCESS) fail("vkCreateInstance failed", result);
    volkLoadInstance(instance_);
}

void VulkanRenderer::createSurface() {
    if (!SDL_Vulkan_CreateSurface(window_, instance_, nullptr, &surface_))
        throw std::runtime_error(std::string{"SDL_Vulkan_CreateSurface failed: "} + SDL_GetError());
}

bool VulkanRenderer::supportsSwapchain(VkPhysicalDevice device) const {
    std::uint32_t count = 0;
    if (vkEnumerateDeviceExtensionProperties(device, nullptr, &count, nullptr) != VK_SUCCESS) return false;
    std::vector<VkExtensionProperties> extensions(count);
    if (vkEnumerateDeviceExtensionProperties(device, nullptr, &count, extensions.data()) != VK_SUCCESS) return false;
    return std::any_of(extensions.begin(), extensions.end(), [](const auto& extension) {
        return std::string_view{extension.extensionName} == VK_KHR_SWAPCHAIN_EXTENSION_NAME;
    });
}

std::uint32_t VulkanRenderer::findGraphicsPresentQueue(VkPhysicalDevice device) const {
    std::uint32_t count = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(device, &count, nullptr);
    std::vector<VkQueueFamilyProperties> queues(count);
    vkGetPhysicalDeviceQueueFamilyProperties(device, &count, queues.data());
    for (std::uint32_t i = 0; i < count; ++i) {
        const bool graphics = (queues[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) != 0U;
        const bool present = SDL_Vulkan_GetPresentationSupport(instance_, device, i);
        if (graphics && present) return i;
    }
    return std::numeric_limits<std::uint32_t>::max();
}

void VulkanRenderer::selectPhysicalDevice() {
    std::uint32_t count = 0;
    VkResult result = vkEnumeratePhysicalDevices(instance_, &count, nullptr);
    if (result != VK_SUCCESS || count == 0U) fail("No Vulkan physical device found", result);
    std::vector<VkPhysicalDevice> devices(count);
    result = vkEnumeratePhysicalDevices(instance_, &count, devices.data());
    if (result != VK_SUCCESS) fail("vkEnumeratePhysicalDevices failed", result);

    std::int32_t bestScore = -1;
    for (VkPhysicalDevice device : devices) {
        VkPhysicalDeviceProperties properties{};
        vkGetPhysicalDeviceProperties(device, &properties);
        if (properties.apiVersion < VK_API_VERSION_1_3 || !supportsSwapchain(device)) continue;
        const auto queue = findGraphicsPresentQueue(device);
        if (queue == std::numeric_limits<std::uint32_t>::max()) continue;

        VkPhysicalDeviceVulkan13Features features13{};
        features13.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_3_FEATURES;
        VkPhysicalDeviceFeatures2 features2{};
        features2.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2;
        features2.pNext = &features13;
        vkGetPhysicalDeviceFeatures2(device, &features2);
        if (features13.synchronization2 != VK_TRUE || features13.dynamicRendering != VK_TRUE) continue;

        std::uint32_t formatCount = 0;
        std::uint32_t presentCount = 0;
        vkGetPhysicalDeviceSurfaceFormatsKHR(device, surface_, &formatCount, nullptr);
        vkGetPhysicalDeviceSurfacePresentModesKHR(device, surface_, &presentCount, nullptr);
        if (formatCount == 0U || presentCount == 0U) continue;

        std::int32_t score = 100;
        if (properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU) score += 1000;
        else if (properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU) score += 500;
        score += static_cast<std::int32_t>(properties.limits.maxImageDimension2D / 1024U);
        if (score > bestScore) {
            bestScore = score;
            physicalDevice_ = device;
            queueFamilyIndex_ = queue;
            gpuName_ = properties.deviceName;
        }
    }
    if (physicalDevice_ == VK_NULL_HANDLE) fail("No GPU satisfies Vulkan 1.3 + dynamic rendering + synchronization2 + swapchain");
}

void VulkanRenderer::createDevice() {
    constexpr float priority = 1.0F;
    VkDeviceQueueCreateInfo queue{};
    queue.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
    queue.queueFamilyIndex = queueFamilyIndex_;
    queue.queueCount = 1;
    queue.pQueuePriorities = &priority;

    VkPhysicalDeviceVulkan13Features features13{};
    features13.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_3_FEATURES;
    features13.dynamicRendering = VK_TRUE;
    features13.synchronization2 = VK_TRUE;
    const char* extensions[] = {VK_KHR_SWAPCHAIN_EXTENSION_NAME};

    VkDeviceCreateInfo info{};
    info.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    info.pNext = &features13;
    info.queueCreateInfoCount = 1;
    info.pQueueCreateInfos = &queue;
    info.enabledExtensionCount = 1;
    info.ppEnabledExtensionNames = extensions;
    const VkResult result = vkCreateDevice(physicalDevice_, &info, nullptr, &device_);
    if (result != VK_SUCCESS) fail("vkCreateDevice failed", result);
    volkLoadDevice(device_);
    vkGetDeviceQueue(device_, queueFamilyIndex_, 0, &graphicsQueue_);
}

void VulkanRenderer::createCommands() {
    VkCommandPoolCreateInfo pool{};
    pool.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    pool.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    pool.queueFamilyIndex = queueFamilyIndex_;
    VkResult result = vkCreateCommandPool(device_, &pool, nullptr, &commandPool_);
    if (result != VK_SUCCESS) fail("vkCreateCommandPool failed", result);

    VkCommandBufferAllocateInfo alloc{};
    alloc.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    alloc.commandPool = commandPool_;
    alloc.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    alloc.commandBufferCount = kFramesInFlight;
    result = vkAllocateCommandBuffers(device_, &alloc, commandBuffers_.data());
    if (result != VK_SUCCESS) fail("vkAllocateCommandBuffers failed", result);
}

void VulkanRenderer::createSyncObjects() {
    VkSemaphoreCreateInfo semaphore{};
    semaphore.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
    VkFenceCreateInfo fence{};
    fence.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
    fence.flags = VK_FENCE_CREATE_SIGNALED_BIT;
    for (std::uint32_t i = 0; i < kFramesInFlight; ++i) {
        if (vkCreateSemaphore(device_, &semaphore, nullptr, &imageAvailable_[i]) != VK_SUCCESS
            || vkCreateSemaphore(device_, &semaphore, nullptr, &renderFinished_[i]) != VK_SUCCESS
            || vkCreateFence(device_, &fence, nullptr, &inFlight_[i]) != VK_SUCCESS)
            fail("Failed to create Vulkan synchronization objects");
    }
}

void VulkanRenderer::createSwapchain() {
    int pixelWidth = 0;
    int pixelHeight = 0;
    if (!SDL_GetWindowSizeInPixels(window_, &pixelWidth, &pixelHeight) || pixelWidth <= 0 || pixelHeight <= 0) return;

    VkSurfaceCapabilitiesKHR capabilities{};
    VkResult result = vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physicalDevice_, surface_, &capabilities);
    if (result != VK_SUCCESS) fail("vkGetPhysicalDeviceSurfaceCapabilitiesKHR failed", result);
    if ((capabilities.supportedUsageFlags & VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT) == 0U)
        fail("Swapchain surface does not support color attachments");

    std::uint32_t formatCount = 0;
    vkGetPhysicalDeviceSurfaceFormatsKHR(physicalDevice_, surface_, &formatCount, nullptr);
    std::vector<VkSurfaceFormatKHR> formats(formatCount);
    vkGetPhysicalDeviceSurfaceFormatsKHR(physicalDevice_, surface_, &formatCount, formats.data());
    VkSurfaceFormatKHR chosen = formats.front();
    for (const auto& format : formats) {
        if (format.format == VK_FORMAT_B8G8R8A8_SRGB && format.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR) {
            chosen = format;
            break;
        }
    }

    std::uint32_t presentCount = 0;
    vkGetPhysicalDeviceSurfacePresentModesKHR(physicalDevice_, surface_, &presentCount, nullptr);
    std::vector<VkPresentModeKHR> presentModes(presentCount);
    vkGetPhysicalDeviceSurfacePresentModesKHR(physicalDevice_, surface_, &presentCount, presentModes.data());
    VkPresentModeKHR present = VK_PRESENT_MODE_FIFO_KHR;
    if (std::find(presentModes.begin(), presentModes.end(), VK_PRESENT_MODE_MAILBOX_KHR) != presentModes.end())
        present = VK_PRESENT_MODE_MAILBOX_KHR;

    VkExtent2D extent{};
    if (capabilities.currentExtent.width != std::numeric_limits<std::uint32_t>::max()) extent = capabilities.currentExtent;
    else {
        extent.width = std::clamp(static_cast<std::uint32_t>(pixelWidth), capabilities.minImageExtent.width, capabilities.maxImageExtent.width);
        extent.height = std::clamp(static_cast<std::uint32_t>(pixelHeight), capabilities.minImageExtent.height, capabilities.maxImageExtent.height);
    }

    std::uint32_t imageCount = capabilities.minImageCount + 1U;
    if (capabilities.maxImageCount > 0U) imageCount = std::min(imageCount, capabilities.maxImageCount);

    VkSwapchainCreateInfoKHR info{};
    info.sType = VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR;
    info.surface = surface_;
    info.minImageCount = imageCount;
    info.imageFormat = chosen.format;
    info.imageColorSpace = chosen.colorSpace;
    info.imageExtent = extent;
    info.imageArrayLayers = 1;
    info.imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
    info.imageSharingMode = VK_SHARING_MODE_EXCLUSIVE;
    info.preTransform = capabilities.currentTransform;
    info.compositeAlpha = chooseCompositeAlpha(capabilities.supportedCompositeAlpha);
    info.presentMode = present;
    info.clipped = VK_TRUE;
    result = vkCreateSwapchainKHR(device_, &info, nullptr, &swapchain_);
    if (result != VK_SUCCESS) fail("vkCreateSwapchainKHR failed", result);

    swapchainFormat_ = chosen.format;
    swapchainExtent_ = extent;
    std::uint32_t actualCount = 0;
    vkGetSwapchainImagesKHR(device_, swapchain_, &actualCount, nullptr);
    swapchainImages_.resize(actualCount);
    vkGetSwapchainImagesKHR(device_, swapchain_, &actualCount, swapchainImages_.data());
    imageInitialized_.assign(actualCount, false);
    resizeRequested_ = false;
}

void VulkanRenderer::createSwapchainResources() {
    if (swapchain_ == VK_NULL_HANDLE) return;
    swapchainImageViews_.reserve(swapchainImages_.size());
    for (VkImage image : swapchainImages_) {
        VkImageViewCreateInfo info{};
        info.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        info.image = image;
        info.viewType = VK_IMAGE_VIEW_TYPE_2D;
        info.format = swapchainFormat_;
        info.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        info.subresourceRange.levelCount = 1;
        info.subresourceRange.layerCount = 1;
        VkImageView view = VK_NULL_HANDLE;
        const VkResult result = vkCreateImageView(device_, &info, nullptr, &view);
        if (result != VK_SUCCESS) fail("vkCreateImageView(swapchain) failed", result);
        swapchainImageViews_.push_back(view);
    }
    createMainDepthResources();
    createPipelines();
}

void VulkanRenderer::destroySwapchainResources() noexcept {
    destroyPipelines();
    destroyMainDepthResources();
    for (VkImageView view : swapchainImageViews_) if (view != VK_NULL_HANDLE) vkDestroyImageView(device_, view, nullptr);
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
    VkPhysicalDeviceMemoryProperties memory{};
    vkGetPhysicalDeviceMemoryProperties(physicalDevice_, &memory);
    for (std::uint32_t i = 0; i < memory.memoryTypeCount; ++i) {
        if ((typeFilter & (1U << i)) != 0U && (memory.memoryTypes[i].propertyFlags & properties) == properties) return i;
    }
    fail("No suitable Vulkan memory type found");
}

void VulkanRenderer::createBuffer(
    VkDeviceSize size,
    VkBufferUsageFlags usage,
    VkMemoryPropertyFlags properties,
    VkBuffer& buffer,
    VkDeviceMemory& memory) {
    VkBufferCreateInfo info{};
    info.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    info.size = size;
    info.usage = usage;
    info.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    VkResult result = vkCreateBuffer(device_, &info, nullptr, &buffer);
    if (result != VK_SUCCESS) fail("vkCreateBuffer failed", result);
    VkMemoryRequirements requirements{};
    vkGetBufferMemoryRequirements(device_, buffer, &requirements);
    VkMemoryAllocateInfo alloc{};
    alloc.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    alloc.allocationSize = requirements.size;
    alloc.memoryTypeIndex = findMemoryType(requirements.memoryTypeBits, properties);
    result = vkAllocateMemory(device_, &alloc, nullptr, &memory);
    if (result != VK_SUCCESS) fail("vkAllocateMemory(buffer) failed", result);
    result = vkBindBufferMemory(device_, buffer, memory, 0);
    if (result != VK_SUCCESS) fail("vkBindBufferMemory failed", result);
}

void VulkanRenderer::createDepthImage(
    std::uint32_t width,
    std::uint32_t height,
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
    info.format = depthFormat_;
    info.tiling = VK_IMAGE_TILING_OPTIMAL;
    info.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    info.usage = usage;
    info.samples = VK_SAMPLE_COUNT_1_BIT;
    info.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    VkResult result = vkCreateImage(device_, &info, nullptr, &image);
    if (result != VK_SUCCESS) fail("vkCreateImage(depth) failed", result);
    VkMemoryRequirements requirements{};
    vkGetImageMemoryRequirements(device_, image, &requirements);
    VkMemoryAllocateInfo alloc{};
    alloc.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    alloc.allocationSize = requirements.size;
    alloc.memoryTypeIndex = findMemoryType(requirements.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    result = vkAllocateMemory(device_, &alloc, nullptr, &memory);
    if (result != VK_SUCCESS) fail("vkAllocateMemory(depth) failed", result);
    result = vkBindImageMemory(device_, image, memory, 0);
    if (result != VK_SUCCESS) fail("vkBindImageMemory(depth) failed", result);

    VkImageViewCreateInfo viewInfo{};
    viewInfo.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    viewInfo.image = image;
    viewInfo.viewType = VK_IMAGE_VIEW_TYPE_2D;
    viewInfo.format = depthFormat_;
    viewInfo.subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT;
    viewInfo.subresourceRange.levelCount = 1;
    viewInfo.subresourceRange.layerCount = 1;
    result = vkCreateImageView(device_, &viewInfo, nullptr, &view);
    if (result != VK_SUCCESS) fail("vkCreateImageView(depth) failed", result);
}

void VulkanRenderer::createMainDepthResources() {
    for (auto& depth : depthFrames_)
        createDepthImage(swapchainExtent_.width, swapchainExtent_.height, VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT, depth.image, depth.memory, depth.view);
}

void VulkanRenderer::destroyMainDepthResources() noexcept {
    for (auto& depth : depthFrames_) {
        if (depth.view != VK_NULL_HANDLE) vkDestroyImageView(device_, depth.view, nullptr);
        if (depth.image != VK_NULL_HANDLE) vkDestroyImage(device_, depth.image, nullptr);
        if (depth.memory != VK_NULL_HANDLE) vkFreeMemory(device_, depth.memory, nullptr);
        depth = {};
    }
}

void VulkanRenderer::createShadowResources() {
    for (auto& shadow : shadowFrames_) {
        createDepthImage(kShadowMapSize, kShadowMapSize,
            VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
            shadow.depthImage, shadow.depthMemory, shadow.depthView);
        createBuffer(sizeof(SceneUniforms), VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
            shadow.uniformBuffer, shadow.uniformMemory);
        const VkResult result = vkMapMemory(device_, shadow.uniformMemory, 0, sizeof(SceneUniforms), 0, &shadow.mappedUniform);
        if (result != VK_SUCCESS) fail("vkMapMemory(scene uniform) failed", result);
    }
}

void VulkanRenderer::destroyShadowResources() noexcept {
    for (auto& shadow : shadowFrames_) {
        if (shadow.mappedUniform != nullptr && shadow.uniformMemory != VK_NULL_HANDLE) vkUnmapMemory(device_, shadow.uniformMemory);
        if (shadow.uniformBuffer != VK_NULL_HANDLE) vkDestroyBuffer(device_, shadow.uniformBuffer, nullptr);
        if (shadow.uniformMemory != VK_NULL_HANDLE) vkFreeMemory(device_, shadow.uniformMemory, nullptr);
        if (shadow.depthView != VK_NULL_HANDLE) vkDestroyImageView(device_, shadow.depthView, nullptr);
        if (shadow.depthImage != VK_NULL_HANDLE) vkDestroyImage(device_, shadow.depthImage, nullptr);
        if (shadow.depthMemory != VK_NULL_HANDLE) vkFreeMemory(device_, shadow.depthMemory, nullptr);
        shadow = {};
    }
}

void VulkanRenderer::createDescriptorResources() {
    std::array<VkDescriptorSetLayoutBinding, 3> bindings{};
    bindings[0] = {0U, VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, 1U, VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
    bindings[1] = {1U, VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE, 1U, VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
    bindings[2] = {2U, VK_DESCRIPTOR_TYPE_SAMPLER, 1U, VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
    VkDescriptorSetLayoutCreateInfo layout{};
    layout.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    layout.bindingCount = static_cast<std::uint32_t>(bindings.size());
    layout.pBindings = bindings.data();
    VkResult result = vkCreateDescriptorSetLayout(device_, &layout, nullptr, &sceneDescriptorSetLayout_);
    if (result != VK_SUCCESS) fail("vkCreateDescriptorSetLayout failed", result);

    VkSamplerCreateInfo sampler{};
    sampler.sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO;
    sampler.magFilter = VK_FILTER_NEAREST;
    sampler.minFilter = VK_FILTER_NEAREST;
    sampler.mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST;
    sampler.addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_BORDER;
    sampler.addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_BORDER;
    sampler.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_BORDER;
    sampler.borderColor = VK_BORDER_COLOR_FLOAT_OPAQUE_WHITE;
    sampler.maxLod = 0.0F;
    result = vkCreateSampler(device_, &sampler, nullptr, &shadowSampler_);
    if (result != VK_SUCCESS) fail("vkCreateSampler(shadow) failed", result);

    createShadowResources();

    const std::array<VkDescriptorPoolSize, 3> sizes{{
        {VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, kFramesInFlight},
        {VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE, kFramesInFlight},
        {VK_DESCRIPTOR_TYPE_SAMPLER, kFramesInFlight},
    }};
    VkDescriptorPoolCreateInfo pool{};
    pool.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    pool.maxSets = kFramesInFlight;
    pool.poolSizeCount = static_cast<std::uint32_t>(sizes.size());
    pool.pPoolSizes = sizes.data();
    result = vkCreateDescriptorPool(device_, &pool, nullptr, &sceneDescriptorPool_);
    if (result != VK_SUCCESS) fail("vkCreateDescriptorPool failed", result);

    std::array<VkDescriptorSetLayout, kFramesInFlight> layouts{};
    layouts.fill(sceneDescriptorSetLayout_);
    std::array<VkDescriptorSet, kFramesInFlight> sets{};
    VkDescriptorSetAllocateInfo alloc{};
    alloc.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    alloc.descriptorPool = sceneDescriptorPool_;
    alloc.descriptorSetCount = kFramesInFlight;
    alloc.pSetLayouts = layouts.data();
    result = vkAllocateDescriptorSets(device_, &alloc, sets.data());
    if (result != VK_SUCCESS) fail("vkAllocateDescriptorSets failed", result);

    for (std::uint32_t i = 0; i < kFramesInFlight; ++i) {
        shadowFrames_[i].descriptorSet = sets[i];
        VkDescriptorBufferInfo bufferInfo{shadowFrames_[i].uniformBuffer, 0, sizeof(SceneUniforms)};
        VkDescriptorImageInfo imageInfo{};
        imageInfo.imageView = shadowFrames_[i].depthView;
        imageInfo.imageLayout = VK_IMAGE_LAYOUT_DEPTH_READ_ONLY_OPTIMAL;
        VkDescriptorImageInfo samplerInfo{};
        samplerInfo.sampler = shadowSampler_;
        std::array<VkWriteDescriptorSet, 3> writes{};
        writes[0].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[0].dstSet = sets[i];
        writes[0].dstBinding = 0;
        writes[0].descriptorCount = 1;
        writes[0].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
        writes[0].pBufferInfo = &bufferInfo;
        writes[1].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[1].dstSet = sets[i];
        writes[1].dstBinding = 1;
        writes[1].descriptorCount = 1;
        writes[1].descriptorType = VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE;
        writes[1].pImageInfo = &imageInfo;
        writes[2].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[2].dstSet = sets[i];
        writes[2].dstBinding = 2;
        writes[2].descriptorCount = 1;
        writes[2].descriptorType = VK_DESCRIPTOR_TYPE_SAMPLER;
        writes[2].pImageInfo = &samplerInfo;
        vkUpdateDescriptorSets(device_, static_cast<std::uint32_t>(writes.size()), writes.data(), 0, nullptr);
    }
}

void VulkanRenderer::destroyDescriptorResources() noexcept {
    destroyShadowResources();
    if (sceneDescriptorPool_ != VK_NULL_HANDLE) vkDestroyDescriptorPool(device_, sceneDescriptorPool_, nullptr);
    sceneDescriptorPool_ = VK_NULL_HANDLE;
    if (shadowSampler_ != VK_NULL_HANDLE) vkDestroySampler(device_, shadowSampler_, nullptr);
    shadowSampler_ = VK_NULL_HANDLE;
    if (sceneDescriptorSetLayout_ != VK_NULL_HANDLE) vkDestroyDescriptorSetLayout(device_, sceneDescriptorSetLayout_, nullptr);
    sceneDescriptorSetLayout_ = VK_NULL_HANDLE;
}

void VulkanRenderer::createPipelines() {
    VkPushConstantRange pushRange{};
    pushRange.stageFlags = VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT;
    pushRange.size = sizeof(PushConstants);
    VkPipelineLayoutCreateInfo layout{};
    layout.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    layout.setLayoutCount = 1;
    layout.pSetLayouts = &sceneDescriptorSetLayout_;
    layout.pushConstantRangeCount = 1;
    layout.pPushConstantRanges = &pushRange;
    VkResult result = vkCreatePipelineLayout(device_, &layout, nullptr, &scenePipelineLayout_);
    if (result != VK_SUCCESS) fail("vkCreatePipelineLayout(scene) failed", result);
    result = vkCreatePipelineLayout(device_, &layout, nullptr, &fullscreenPipelineLayout_);
    if (result != VK_SUCCESS) fail("vkCreatePipelineLayout(fullscreen) failed", result);

    VkVertexInputBindingDescription binding{0U, sizeof(PlanetVertex), VK_VERTEX_INPUT_RATE_VERTEX};
    std::array<VkVertexInputAttributeDescription, 4> attributes{};
    attributes[0] = {0U, 0U, VK_FORMAT_R32G32B32_SFLOAT, static_cast<std::uint32_t>(offsetof(PlanetVertex, position))};
    attributes[1] = {1U, 0U, VK_FORMAT_R32G32B32_SFLOAT, static_cast<std::uint32_t>(offsetof(PlanetVertex, normal))};
    attributes[2] = {2U, 0U, VK_FORMAT_R32G32B32_SFLOAT, static_cast<std::uint32_t>(offsetof(PlanetVertex, color))};
    attributes[3] = {3U, 0U, VK_FORMAT_R32G32B32A32_SFLOAT, static_cast<std::uint32_t>(offsetof(PlanetVertex, material))};
    VkPipelineVertexInputStateCreateInfo vertexInput{};
    vertexInput.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    vertexInput.vertexBindingDescriptionCount = 1;
    vertexInput.pVertexBindingDescriptions = &binding;
    vertexInput.vertexAttributeDescriptionCount = static_cast<std::uint32_t>(attributes.size());
    vertexInput.pVertexAttributeDescriptions = attributes.data();
    VkPipelineVertexInputStateCreateInfo emptyVertexInput{};
    emptyVertexInput.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;

    VkPipelineInputAssemblyStateCreateInfo assembly{};
    assembly.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    assembly.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
    VkPipelineViewportStateCreateInfo viewport{};
    viewport.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    viewport.viewportCount = 1;
    viewport.scissorCount = 1;
    VkPipelineRasterizationStateCreateInfo raster{};
    raster.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    raster.polygonMode = VK_POLYGON_MODE_FILL;
    raster.cullMode = VK_CULL_MODE_NONE;
    raster.frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE;
    raster.lineWidth = 1.0F;
    VkPipelineMultisampleStateCreateInfo multisample{};
    multisample.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    multisample.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
    VkPipelineDepthStencilStateCreateInfo reverseDepth{};
    reverseDepth.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
    reverseDepth.depthTestEnable = VK_TRUE;
    reverseDepth.depthWriteEnable = VK_TRUE;
    reverseDepth.depthCompareOp = VK_COMPARE_OP_GREATER_OR_EQUAL;
    VkPipelineDepthStencilStateCreateInfo noDepth = reverseDepth;
    noDepth.depthTestEnable = VK_FALSE;
    noDepth.depthWriteEnable = VK_FALSE;
    VkPipelineDepthStencilStateCreateInfo transparentDepth = reverseDepth;
    transparentDepth.depthWriteEnable = VK_FALSE;
    VkPipelineDepthStencilStateCreateInfo shadowDepth{};
    shadowDepth.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
    shadowDepth.depthTestEnable = VK_TRUE;
    shadowDepth.depthWriteEnable = VK_TRUE;
    shadowDepth.depthCompareOp = VK_COMPARE_OP_LESS_OR_EQUAL;

    VkPipelineColorBlendAttachmentState opaqueBlend{};
    opaqueBlend.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT | VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;
    VkPipelineColorBlendAttachmentState alphaBlend = opaqueBlend;
    alphaBlend.blendEnable = VK_TRUE;
    alphaBlend.srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA;
    alphaBlend.dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    alphaBlend.colorBlendOp = VK_BLEND_OP_ADD;
    alphaBlend.srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
    alphaBlend.dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    alphaBlend.alphaBlendOp = VK_BLEND_OP_ADD;
    VkPipelineColorBlendStateCreateInfo blend{};
    blend.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    blend.attachmentCount = 1;
    blend.pAttachments = &opaqueBlend;
    constexpr VkDynamicState states[] = {VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
    VkPipelineDynamicStateCreateInfo dynamic{};
    dynamic.sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
    dynamic.dynamicStateCount = 2;
    dynamic.pDynamicStates = states;

    VkPipelineRenderingCreateInfo rendering{};
    rendering.sType = VK_STRUCTURE_TYPE_PIPELINE_RENDERING_CREATE_INFO;
    rendering.colorAttachmentCount = 1;
    rendering.pColorAttachmentFormats = &swapchainFormat_;
    rendering.depthAttachmentFormat = depthFormat_;

    const VkShaderModule sceneVertex = createShaderModule(device_, shaders::kPlanetVertexSpv, shaders::kPlanetVertexSpvSize);
    const VkShaderModule opaqueFragment = createShaderModule(device_, shaders::kOpaqueFragmentSpv, shaders::kOpaqueFragmentSpvSize);
    const VkShaderModule transparentFragment = createShaderModule(device_, shaders::kTransparentFragmentSpv, shaders::kTransparentFragmentSpvSize);
    const VkShaderModule shadowVertex = createShaderModule(device_, shaders::kShadowVertexSpv, shaders::kShadowVertexSpvSize);
    const VkShaderModule shadowFragment = createShaderModule(device_, shaders::kShadowFragmentSpv, shaders::kShadowFragmentSpvSize);
    const VkShaderModule fullscreenVertex = createShaderModule(device_, shaders::kFullscreenVertexSpv, shaders::kFullscreenVertexSpvSize);
    const VkShaderModule skyFragment = createShaderModule(device_, shaders::kSkyFragmentSpv, shaders::kSkyFragmentSpvSize);
    const VkShaderModule hudFragment = createShaderModule(device_, shaders::kHudFragmentSpv, shaders::kHudFragmentSpvSize);

    auto makeStage = [](VkShaderStageFlagBits stage, VkShaderModule module, const char* name) {
        VkPipelineShaderStageCreateInfo info{};
        info.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        info.stage = stage;
        info.module = module;
        info.pName = name;
        return info;
    };

    auto createColorPipeline = [&](VkPipeline& pipeline, VkShaderModule vert, const char* vertName,
                                   VkShaderModule frag, const char* fragName,
                                   VkPipelineVertexInputStateCreateInfo* vi,
                                   VkPipelineDepthStencilStateCreateInfo* ds,
                                   VkPipelineColorBlendAttachmentState* attachment,
                                   VkPipelineLayout pipelineLayout) {
        const std::array stagesLocal{
            makeStage(VK_SHADER_STAGE_VERTEX_BIT, vert, vertName),
            makeStage(VK_SHADER_STAGE_FRAGMENT_BIT, frag, fragName),
        };
        VkPipelineColorBlendStateCreateInfo localBlend = blend;
        localBlend.pAttachments = attachment;
        VkGraphicsPipelineCreateInfo info{};
        info.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
        info.pNext = &rendering;
        info.stageCount = static_cast<std::uint32_t>(stagesLocal.size());
        info.pStages = stagesLocal.data();
        info.pVertexInputState = vi;
        info.pInputAssemblyState = &assembly;
        info.pViewportState = &viewport;
        info.pRasterizationState = &raster;
        info.pMultisampleState = &multisample;
        info.pDepthStencilState = ds;
        info.pColorBlendState = &localBlend;
        info.pDynamicState = &dynamic;
        info.layout = pipelineLayout;
        const VkResult createResult = vkCreateGraphicsPipelines(device_, VK_NULL_HANDLE, 1, &info, nullptr, &pipeline);
        if (createResult != VK_SUCCESS) fail("vkCreateGraphicsPipelines(color) failed", createResult);
    };

    createColorPipeline(opaquePipeline_, sceneVertex, "vertexMain", opaqueFragment, "opaqueFragmentMain",
        &vertexInput, &reverseDepth, &opaqueBlend, scenePipelineLayout_);
    createColorPipeline(transparentPipeline_, sceneVertex, "vertexMain", transparentFragment, "transparentFragmentMain",
        &vertexInput, &transparentDepth, &alphaBlend, scenePipelineLayout_);
    createColorPipeline(skyPipeline_, fullscreenVertex, "fullscreenVertexMain", skyFragment, "skyFragmentMain",
        &emptyVertexInput, &noDepth, &opaqueBlend, fullscreenPipelineLayout_);
    createColorPipeline(hudPipeline_, fullscreenVertex, "fullscreenVertexMain", hudFragment, "hudFragmentMain",
        &emptyVertexInput, &noDepth, &alphaBlend, fullscreenPipelineLayout_);

    VkPipelineRenderingCreateInfo shadowRendering{};
    shadowRendering.sType = VK_STRUCTURE_TYPE_PIPELINE_RENDERING_CREATE_INFO;
    shadowRendering.depthAttachmentFormat = depthFormat_;
    const std::array shadowStages{
        makeStage(VK_SHADER_STAGE_VERTEX_BIT, shadowVertex, "shadowVertexMain"),
        makeStage(VK_SHADER_STAGE_FRAGMENT_BIT, shadowFragment, "shadowFragmentMain"),
    };
    VkPipelineRasterizationStateCreateInfo shadowRaster = raster;
    shadowRaster.cullMode = VK_CULL_MODE_BACK_BIT;
    shadowRaster.depthBiasEnable = VK_TRUE;
    shadowRaster.depthBiasConstantFactor = 1.25F;
    shadowRaster.depthBiasSlopeFactor = 1.75F;
    VkPipelineColorBlendStateCreateInfo noColorBlend{};
    noColorBlend.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    VkGraphicsPipelineCreateInfo shadowInfo{};
    shadowInfo.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    shadowInfo.pNext = &shadowRendering;
    shadowInfo.stageCount = static_cast<std::uint32_t>(shadowStages.size());
    shadowInfo.pStages = shadowStages.data();
    shadowInfo.pVertexInputState = &vertexInput;
    shadowInfo.pInputAssemblyState = &assembly;
    shadowInfo.pViewportState = &viewport;
    shadowInfo.pRasterizationState = &shadowRaster;
    shadowInfo.pMultisampleState = &multisample;
    shadowInfo.pDepthStencilState = &shadowDepth;
    shadowInfo.pColorBlendState = &noColorBlend;
    shadowInfo.pDynamicState = &dynamic;
    shadowInfo.layout = scenePipelineLayout_;
    result = vkCreateGraphicsPipelines(device_, VK_NULL_HANDLE, 1, &shadowInfo, nullptr, &shadowPipeline_);
    if (result != VK_SUCCESS) fail("vkCreateGraphicsPipelines(shadow) failed", result);

    for (VkShaderModule module : {sceneVertex, opaqueFragment, transparentFragment, shadowVertex, shadowFragment,
                                  fullscreenVertex, skyFragment, hudFragment})
        vkDestroyShaderModule(device_, module, nullptr);
}

void VulkanRenderer::destroyPipelines() noexcept {
    for (VkPipeline* pipeline : {&opaquePipeline_, &transparentPipeline_, &shadowPipeline_, &skyPipeline_, &hudPipeline_}) {
        if (*pipeline != VK_NULL_HANDLE) vkDestroyPipeline(device_, *pipeline, nullptr);
        *pipeline = VK_NULL_HANDLE;
    }
    if (scenePipelineLayout_ != VK_NULL_HANDLE) vkDestroyPipelineLayout(device_, scenePipelineLayout_, nullptr);
    scenePipelineLayout_ = VK_NULL_HANDLE;
    if (fullscreenPipelineLayout_ != VK_NULL_HANDLE) vkDestroyPipelineLayout(device_, fullscreenPipelineLayout_, nullptr);
    fullscreenPipelineLayout_ = VK_NULL_HANDLE;
}

void VulkanRenderer::destroyMesh() noexcept {
    if (indexBuffer_ != VK_NULL_HANDLE) vkDestroyBuffer(device_, indexBuffer_, nullptr);
    if (indexMemory_ != VK_NULL_HANDLE) vkFreeMemory(device_, indexMemory_, nullptr);
    if (vertexBuffer_ != VK_NULL_HANDLE) vkDestroyBuffer(device_, vertexBuffer_, nullptr);
    if (vertexMemory_ != VK_NULL_HANDLE) vkFreeMemory(device_, vertexMemory_, nullptr);
    indexBuffer_ = VK_NULL_HANDLE;
    indexMemory_ = VK_NULL_HANDLE;
    vertexBuffer_ = VK_NULL_HANDLE;
    vertexMemory_ = VK_NULL_HANDLE;
    indexCount_ = 0;
}

void VulkanRenderer::destroyDynamicFrameMesh(DynamicFrameMesh& mesh) noexcept {
    if (mesh.mappedVertices != nullptr && mesh.vertexMemory != VK_NULL_HANDLE) vkUnmapMemory(device_, mesh.vertexMemory);
    if (mesh.mappedIndices != nullptr && mesh.indexMemory != VK_NULL_HANDLE) vkUnmapMemory(device_, mesh.indexMemory);
    if (mesh.indexBuffer != VK_NULL_HANDLE) vkDestroyBuffer(device_, mesh.indexBuffer, nullptr);
    if (mesh.indexMemory != VK_NULL_HANDLE) vkFreeMemory(device_, mesh.indexMemory, nullptr);
    if (mesh.vertexBuffer != VK_NULL_HANDLE) vkDestroyBuffer(device_, mesh.vertexBuffer, nullptr);
    if (mesh.vertexMemory != VK_NULL_HANDLE) vkFreeMemory(device_, mesh.vertexMemory, nullptr);
    mesh = {};
}

void VulkanRenderer::ensureDynamicFrameCapacity(DynamicFrameMesh& mesh, VkDeviceSize vertexBytes, VkDeviceSize indexBytes) {
    if (vertexBytes <= mesh.vertexCapacityBytes && indexBytes <= mesh.indexCapacityBytes) return;
    const VkDeviceSize vertexCapacity = growCapacity(mesh.vertexCapacityBytes, vertexBytes, 64U * 1024U);
    const VkDeviceSize indexCapacity = growCapacity(mesh.indexCapacityBytes, indexBytes, 32U * 1024U);
    destroyDynamicFrameMesh(mesh);
    createBuffer(vertexCapacity, VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT, mesh.vertexBuffer, mesh.vertexMemory);
    createBuffer(indexCapacity, VK_BUFFER_USAGE_INDEX_BUFFER_BIT,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT, mesh.indexBuffer, mesh.indexMemory);
    VkResult result = vkMapMemory(device_, mesh.vertexMemory, 0, vertexCapacity, 0, &mesh.mappedVertices);
    if (result != VK_SUCCESS) fail("vkMapMemory(dynamic vertex) failed", result);
    result = vkMapMemory(device_, mesh.indexMemory, 0, indexCapacity, 0, &mesh.mappedIndices);
    if (result != VK_SUCCESS) fail("vkMapMemory(dynamic index) failed", result);
    mesh.vertexCapacityBytes = vertexCapacity;
    mesh.indexCapacityBytes = indexCapacity;
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

void VulkanRenderer::drawBoundMesh(VkCommandBuffer commandBuffer, VkBuffer vertexBuffer, VkBuffer indexBuffer, std::uint32_t indexCount) {
    if (vertexBuffer == VK_NULL_HANDLE || indexBuffer == VK_NULL_HANDLE || indexCount == 0U) return;
    constexpr VkDeviceSize offset = 0;
    vkCmdBindVertexBuffers(commandBuffer, 0, 1, &vertexBuffer, &offset);
    vkCmdBindIndexBuffer(commandBuffer, indexBuffer, 0, VK_INDEX_TYPE_UINT32);
    vkCmdDrawIndexed(commandBuffer, indexCount, 1, 0, 0, 0);
}

void VulkanRenderer::uploadPlanetMesh(const PlanetMesh& mesh) {
    if (mesh.vertices.empty() || mesh.indices.empty()) fail("Cannot upload an empty planet mesh");
    vkDeviceWaitIdle(device_);
    destroyMesh();
    const VkDeviceSize vertexBytes = static_cast<VkDeviceSize>(mesh.vertices.size() * sizeof(PlanetVertex));
    const VkDeviceSize indexBytes = static_cast<VkDeviceSize>(mesh.indices.size() * sizeof(std::uint32_t));
    createBuffer(vertexBytes, VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT, vertexBuffer_, vertexMemory_);
    createBuffer(indexBytes, VK_BUFFER_USAGE_INDEX_BUFFER_BIT,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT, indexBuffer_, indexMemory_);
    void* mapped = nullptr;
    VkResult result = vkMapMemory(device_, vertexMemory_, 0, vertexBytes, 0, &mapped);
    if (result != VK_SUCCESS) fail("vkMapMemory(vertex) failed", result);
    std::memcpy(mapped, mesh.vertices.data(), static_cast<std::size_t>(vertexBytes));
    vkUnmapMemory(device_, vertexMemory_);
    result = vkMapMemory(device_, indexMemory_, 0, indexBytes, 0, &mapped);
    if (result != VK_SUCCESS) fail("vkMapMemory(index) failed", result);
    std::memcpy(mapped, mesh.indices.data(), static_cast<std::size_t>(indexBytes));
    vkUnmapMemory(device_, indexMemory_);
    indexCount_ = static_cast<std::uint32_t>(mesh.indices.size());
}

void VulkanRenderer::drawFrame(
    const glm::mat4& viewProjection,
    const glm::dvec3& cameraPosition,
    const RenderFrameEnvironment& environment,
    const glm::dquat& staticObjectRotation) {
    if (resizeRequested_) recreateSwapchain();
    if (swapchain_ == VK_NULL_HANDLE || opaquePipeline_ == VK_NULL_HANDLE) return;

    const std::uint32_t frame = frameIndex_ % kFramesInFlight;
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

    const glm::mat4 shadowVP = makeShadowViewProjection(environment.sunDirectionToLight, environment.cameraForward);
    SceneUniforms scene{};
    scene.lightViewProjection = shadowVP;
    scene.skyAmbientExposure = glm::vec4(glm::max(environment.skyAmbient, glm::vec3{0.0F}), std::max(environment.exposure, 0.01F));
    scene.groundAmbientShadowTexel = glm::vec4(glm::max(environment.groundAmbient, glm::vec3{0.0F}), 1.0F / static_cast<float>(kShadowMapSize));
    std::memcpy(shadowFrames_[frame].mappedUniform, &scene, sizeof(scene));

    VkCommandBuffer command = commandBuffers_[frame];
    VkCommandBufferBeginInfo begin{};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    result = vkBeginCommandBuffer(command, &begin);
    if (result != VK_SUCCESS) fail("vkBeginCommandBuffer failed", result);

    // Shadow depth pass: real scene depth from the directional light, no painted footprint polygons.
    VkImageMemoryBarrier2 shadowToAttachment{};
    shadowToAttachment.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;
    shadowToAttachment.srcStageMask = VK_PIPELINE_STAGE_2_NONE;
    shadowToAttachment.dstStageMask = VK_PIPELINE_STAGE_2_EARLY_FRAGMENT_TESTS_BIT | VK_PIPELINE_STAGE_2_LATE_FRAGMENT_TESTS_BIT;
    shadowToAttachment.dstAccessMask = VK_ACCESS_2_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT;
    shadowToAttachment.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    shadowToAttachment.newLayout = VK_IMAGE_LAYOUT_DEPTH_ATTACHMENT_OPTIMAL;
    shadowToAttachment.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    shadowToAttachment.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    shadowToAttachment.image = shadowFrames_[frame].depthImage;
    shadowToAttachment.subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT;
    shadowToAttachment.subresourceRange.levelCount = 1;
    shadowToAttachment.subresourceRange.layerCount = 1;
    VkDependencyInfo dependency{};
    dependency.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO;
    dependency.imageMemoryBarrierCount = 1;
    dependency.pImageMemoryBarriers = &shadowToAttachment;
    vkCmdPipelineBarrier2(command, &dependency);

    VkRenderingAttachmentInfo shadowDepthAttachment{};
    shadowDepthAttachment.sType = VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO;
    shadowDepthAttachment.imageView = shadowFrames_[frame].depthView;
    shadowDepthAttachment.imageLayout = VK_IMAGE_LAYOUT_DEPTH_ATTACHMENT_OPTIMAL;
    shadowDepthAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    shadowDepthAttachment.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
    shadowDepthAttachment.clearValue.depthStencil = {1.0F, 0U};
    VkRenderingInfo shadowRendering{};
    shadowRendering.sType = VK_STRUCTURE_TYPE_RENDERING_INFO;
    shadowRendering.renderArea.extent = {kShadowMapSize, kShadowMapSize};
    shadowRendering.layerCount = 1;
    shadowRendering.pDepthAttachment = &shadowDepthAttachment;
    vkCmdBeginRendering(command, &shadowRendering);
    VkViewport shadowViewport{0.0F, 0.0F, static_cast<float>(kShadowMapSize), static_cast<float>(kShadowMapSize), 0.0F, 1.0F};
    VkRect2D shadowScissor{{0, 0}, {kShadowMapSize, kShadowMapSize}};
    vkCmdSetViewport(command, 0, 1, &shadowViewport);
    vkCmdSetScissor(command, 0, 1, &shadowScissor);
    vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, shadowPipeline_);
    vkCmdBindDescriptorSets(command, VK_PIPELINE_BIND_POINT_GRAPHICS, scenePipelineLayout_, 0, 1,
        &shadowFrames_[frame].descriptorSet, 0, nullptr);

    PushConstants push{};
    push.matrix = shadowVP;
    push.data0 = glm::vec4(glm::vec3(cameraPosition), 1.0F);
    const glm::dquat rotation = glm::normalize(staticObjectRotation);
    push.data3 = {static_cast<float>(rotation.x), static_cast<float>(rotation.y), static_cast<float>(rotation.z), static_cast<float>(rotation.w)};
    vkCmdPushConstants(command, scenePipelineLayout_, VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, 0, sizeof(push), &push);
    drawBoundMesh(command, vertexBuffer_, indexBuffer_, indexCount_);
    push.data3 = {0.0F, 0.0F, 0.0F, 1.0F};
    vkCmdPushConstants(command, scenePipelineLayout_, VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, 0, sizeof(push), &push);
    const auto& dynamic = dynamicMeshes_[frame];
    drawBoundMesh(command, dynamic.vertexBuffer, dynamic.indexBuffer, dynamic.indexCount);
    vkCmdEndRendering(command);

    VkImageMemoryBarrier2 shadowToRead{};
    shadowToRead.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;
    shadowToRead.srcStageMask = VK_PIPELINE_STAGE_2_EARLY_FRAGMENT_TESTS_BIT | VK_PIPELINE_STAGE_2_LATE_FRAGMENT_TESTS_BIT;
    shadowToRead.srcAccessMask = VK_ACCESS_2_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT;
    shadowToRead.dstStageMask = VK_PIPELINE_STAGE_2_FRAGMENT_SHADER_BIT;
    shadowToRead.dstAccessMask = VK_ACCESS_2_SHADER_SAMPLED_READ_BIT;
    shadowToRead.oldLayout = VK_IMAGE_LAYOUT_DEPTH_ATTACHMENT_OPTIMAL;
    shadowToRead.newLayout = VK_IMAGE_LAYOUT_DEPTH_READ_ONLY_OPTIMAL;
    shadowToRead.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    shadowToRead.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    shadowToRead.image = shadowFrames_[frame].depthImage;
    shadowToRead.subresourceRange = shadowToAttachment.subresourceRange;
    dependency.pImageMemoryBarriers = &shadowToRead;
    vkCmdPipelineBarrier2(command, &dependency);

    // Main color + per-frame reversed-Z depth target.
    VkImageMemoryBarrier2 colorBarrier{};
    colorBarrier.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;
    colorBarrier.srcStageMask = VK_PIPELINE_STAGE_2_NONE;
    colorBarrier.dstStageMask = VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT;
    colorBarrier.dstAccessMask = VK_ACCESS_2_COLOR_ATTACHMENT_WRITE_BIT;
    colorBarrier.oldLayout = imageInitialized_[imageIndex] ? VK_IMAGE_LAYOUT_PRESENT_SRC_KHR : VK_IMAGE_LAYOUT_UNDEFINED;
    colorBarrier.newLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    colorBarrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    colorBarrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    colorBarrier.image = swapchainImages_[imageIndex];
    colorBarrier.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    colorBarrier.subresourceRange.levelCount = 1;
    colorBarrier.subresourceRange.layerCount = 1;

    VkImageMemoryBarrier2 depthBarrier{};
    depthBarrier.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;
    depthBarrier.srcStageMask = VK_PIPELINE_STAGE_2_NONE;
    depthBarrier.dstStageMask = VK_PIPELINE_STAGE_2_EARLY_FRAGMENT_TESTS_BIT | VK_PIPELINE_STAGE_2_LATE_FRAGMENT_TESTS_BIT;
    depthBarrier.dstAccessMask = VK_ACCESS_2_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT;
    depthBarrier.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    depthBarrier.newLayout = VK_IMAGE_LAYOUT_DEPTH_ATTACHMENT_OPTIMAL;
    depthBarrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    depthBarrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    depthBarrier.image = depthFrames_[frame].image;
    depthBarrier.subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT;
    depthBarrier.subresourceRange.levelCount = 1;
    depthBarrier.subresourceRange.layerCount = 1;
    const std::array mainBarriers{colorBarrier, depthBarrier};
    dependency.imageMemoryBarrierCount = static_cast<std::uint32_t>(mainBarriers.size());
    dependency.pImageMemoryBarriers = mainBarriers.data();
    vkCmdPipelineBarrier2(command, &dependency);

    VkRenderingAttachmentInfo colorAttachment{};
    colorAttachment.sType = VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO;
    colorAttachment.imageView = swapchainImageViews_[imageIndex];
    colorAttachment.imageLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    colorAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    colorAttachment.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
    colorAttachment.clearValue.color = {{0.0F, 0.0F, 0.0F, 1.0F}};
    VkRenderingAttachmentInfo depthAttachment{};
    depthAttachment.sType = VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO;
    depthAttachment.imageView = depthFrames_[frame].view;
    depthAttachment.imageLayout = VK_IMAGE_LAYOUT_DEPTH_ATTACHMENT_OPTIMAL;
    depthAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    depthAttachment.storeOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    depthAttachment.clearValue.depthStencil = {0.0F, 0U};
    VkRenderingInfo rendering{};
    rendering.sType = VK_STRUCTURE_TYPE_RENDERING_INFO;
    rendering.renderArea.extent = swapchainExtent_;
    rendering.layerCount = 1;
    rendering.colorAttachmentCount = 1;
    rendering.pColorAttachments = &colorAttachment;
    rendering.pDepthAttachment = &depthAttachment;
    vkCmdBeginRendering(command, &rendering);

    VkViewport mainViewport{0.0F, 0.0F, static_cast<float>(swapchainExtent_.width), static_cast<float>(swapchainExtent_.height), 0.0F, 1.0F};
    VkRect2D mainScissor{{0, 0}, swapchainExtent_};
    vkCmdSetViewport(command, 0, 1, &mainViewport);
    vkCmdSetScissor(command, 0, 1, &mainScissor);
    vkCmdBindDescriptorSets(command, VK_PIPELINE_BIND_POINT_GRAPHICS, fullscreenPipelineLayout_, 0, 1,
        &shadowFrames_[frame].descriptorSet, 0, nullptr);

    // Physically motivated analytic atmosphere replaces the noisy dither shell and flat clear color.
    vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, skyPipeline_);
    PushConstants skyPush{};
    skyPush.matrix = glm::inverse(viewProjection);
    skyPush.data0 = glm::vec4(glm::vec3(cameraPosition - environment.planetCenter), 1.0F);
    skyPush.data1 = glm::vec4(safeNormalizeFloat(environment.sunDirectionToLight), 0.0F);
    skyPush.data2 = {static_cast<float>(environment.planetRadius), static_cast<float>(environment.atmosphereHeight),
                     static_cast<float>(environment.atmosphereScaleHeight), std::max(environment.mieScale, 0.0F)};
    const glm::vec3 sunRadiance = glm::max(environment.sunLinearColor, glm::vec3{0.0F}) * std::max(environment.sunIntensity, 0.0F);
    skyPush.data3 = {std::max(environment.exposure, 0.01F), sunRadiance.r, sunRadiance.g, sunRadiance.b};
    vkCmdPushConstants(command, fullscreenPipelineLayout_, VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, 0, sizeof(skyPush), &skyPush);
    vkCmdDraw(command, 3, 1, 0, 0);

    auto drawScenePass = [&](VkPipeline pipeline) {
        vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);
        vkCmdBindDescriptorSets(command, VK_PIPELINE_BIND_POINT_GRAPHICS, scenePipelineLayout_, 0, 1,
            &shadowFrames_[frame].descriptorSet, 0, nullptr);
        PushConstants scenePush{};
        scenePush.matrix = viewProjection;
        scenePush.data0 = glm::vec4(glm::vec3(cameraPosition), 1.0F);
        scenePush.data1 = glm::vec4(safeNormalizeFloat(environment.sunDirectionToLight), 0.0F);
        scenePush.data2 = glm::vec4(glm::max(environment.sunLinearColor, glm::vec3{0.0F}), std::max(environment.sunIntensity, 0.0F));
        scenePush.data3 = {static_cast<float>(rotation.x), static_cast<float>(rotation.y), static_cast<float>(rotation.z), static_cast<float>(rotation.w)};
        vkCmdPushConstants(command, scenePipelineLayout_, VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, 0, sizeof(scenePush), &scenePush);
        drawBoundMesh(command, vertexBuffer_, indexBuffer_, indexCount_);
        scenePush.data3 = {0.0F, 0.0F, 0.0F, 1.0F};
        vkCmdPushConstants(command, scenePipelineLayout_, VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, 0, sizeof(scenePush), &scenePush);
        drawBoundMesh(command, dynamic.vertexBuffer, dynamic.indexBuffer, dynamic.indexCount);
    };

    drawScenePass(opaquePipeline_);
    drawScenePass(transparentPipeline_);

    // True screen-space HUD: never depth tested, never hidden behind terrain or glass.
    vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, hudPipeline_);
    vkCmdBindDescriptorSets(command, VK_PIPELINE_BIND_POINT_GRAPHICS, fullscreenPipelineLayout_, 0, 1,
        &shadowFrames_[frame].descriptorSet, 0, nullptr);
    PushConstants hudPush{};
    const float speedNorm = std::clamp((std::log10(std::max(1.0F, environment.flightSpeedMps)) - 0.0F)
        / (std::log10(2000000.0F) - 0.0F), 0.0F, 1.0F);
    hudPush.data0 = {static_cast<float>(swapchainExtent_.width), static_cast<float>(swapchainExtent_.height), speedNorm, 0.0F};
    vkCmdPushConstants(command, fullscreenPipelineLayout_, VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, 0, sizeof(hudPush), &hudPush);
    vkCmdDraw(command, 3, 1, 0, 0);
    vkCmdEndRendering(command);

    VkImageMemoryBarrier2 toPresent{};
    toPresent.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;
    toPresent.srcStageMask = VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT;
    toPresent.srcAccessMask = VK_ACCESS_2_COLOR_ATTACHMENT_WRITE_BIT;
    toPresent.dstStageMask = VK_PIPELINE_STAGE_2_NONE;
    toPresent.oldLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    toPresent.newLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
    toPresent.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toPresent.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toPresent.image = swapchainImages_[imageIndex];
    toPresent.subresourceRange = colorBarrier.subresourceRange;
    dependency.imageMemoryBarrierCount = 1;
    dependency.pImageMemoryBarriers = &toPresent;
    vkCmdPipelineBarrier2(command, &dependency);

    result = vkEndCommandBuffer(command);
    if (result != VK_SUCCESS) fail("vkEndCommandBuffer failed", result);

    VkSemaphoreSubmitInfo wait{};
    wait.sType = VK_STRUCTURE_TYPE_SEMAPHORE_SUBMIT_INFO;
    wait.semaphore = imageAvailable_[frame];
    wait.stageMask = VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT;
    VkCommandBufferSubmitInfo commandInfo{};
    commandInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_SUBMIT_INFO;
    commandInfo.commandBuffer = command;
    VkSemaphoreSubmitInfo signal{};
    signal.sType = VK_STRUCTURE_TYPE_SEMAPHORE_SUBMIT_INFO;
    signal.semaphore = renderFinished_[frame];
    signal.stageMask = VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT;
    VkSubmitInfo2 submit{};
    submit.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO_2;
    submit.waitSemaphoreInfoCount = 1;
    submit.pWaitSemaphoreInfos = &wait;
    submit.commandBufferInfoCount = 1;
    submit.pCommandBufferInfos = &commandInfo;
    submit.signalSemaphoreInfoCount = 1;
    submit.pSignalSemaphoreInfos = &signal;
    result = vkQueueSubmit2(graphicsQueue_, 1, &submit, inFlight_[frame]);
    if (result != VK_SUCCESS) fail("vkQueueSubmit2 failed", result);

    VkPresentInfoKHR present{};
    present.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
    present.waitSemaphoreCount = 1;
    present.pWaitSemaphores = &renderFinished_[frame];
    present.swapchainCount = 1;
    present.pSwapchains = &swapchain_;
    present.pImageIndices = &imageIndex;
    const VkResult presentResult = vkQueuePresentKHR(graphicsQueue_, &present);
    imageInitialized_[imageIndex] = true;
    ++frameIndex_;
    if (presentResult == VK_ERROR_OUT_OF_DATE_KHR || presentResult == VK_SUBOPTIMAL_KHR || resizeRequested_) {
        recreateSwapchain();
        return;
    }
    if (presentResult != VK_SUCCESS) fail("vkQueuePresentKHR failed", presentResult);
}

} // namespace vf
