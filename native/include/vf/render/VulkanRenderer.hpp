#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <vector>

#include <volk.h>

struct SDL_Window;

namespace vf {

class VulkanRenderer final {
public:
    explicit VulkanRenderer(SDL_Window* window);
    ~VulkanRenderer();

    VulkanRenderer(const VulkanRenderer&) = delete;
    VulkanRenderer& operator=(const VulkanRenderer&) = delete;

    void drawFrame(float r, float g, float b);
    void requestResize() noexcept { resizeRequested_ = true; }

    [[nodiscard]] const std::string& gpuName() const noexcept { return gpuName_; }
    [[nodiscard]] std::uint32_t apiVersion() const noexcept { return apiVersion_; }

private:
    static constexpr std::uint32_t kFramesInFlight = 2;

    void createInstance();
    void createSurface();
    void selectPhysicalDevice();
    void createDevice();
    void createSwapchain();
    void destroySwapchain() noexcept;
    void recreateSwapchain();
    void createCommands();
    void createSyncObjects();

    [[nodiscard]] std::uint32_t findGraphicsPresentQueue(VkPhysicalDevice device) const;
    [[nodiscard]] bool supportsSwapchain(VkPhysicalDevice device) const;

    SDL_Window* window_{};
    VkInstance instance_{VK_NULL_HANDLE};
    VkSurfaceKHR surface_{VK_NULL_HANDLE};
    VkPhysicalDevice physicalDevice_{VK_NULL_HANDLE};
    VkDevice device_{VK_NULL_HANDLE};
    VkQueue graphicsQueue_{VK_NULL_HANDLE};
    std::uint32_t queueFamilyIndex_{};

    VkSwapchainKHR swapchain_{VK_NULL_HANDLE};
    VkFormat swapchainFormat_{VK_FORMAT_UNDEFINED};
    VkExtent2D swapchainExtent_{};
    std::vector<VkImage> swapchainImages_;
    std::vector<bool> imageInitialized_;

    VkCommandPool commandPool_{VK_NULL_HANDLE};
    std::array<VkCommandBuffer, kFramesInFlight> commandBuffers_{};
    std::array<VkSemaphore, kFramesInFlight> imageAvailable_{};
    std::array<VkSemaphore, kFramesInFlight> renderFinished_{};
    std::array<VkFence, kFramesInFlight> inFlight_{};

    std::uint32_t frameIndex_{};
    std::uint32_t apiVersion_{};
    std::string gpuName_;
    bool resizeRequested_{true};
};

} // namespace vf
