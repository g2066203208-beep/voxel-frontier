#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <vector>

#include <glm/glm.hpp>
#include <volk.h>

#include "vf/world/PlanetSurface.hpp"

struct SDL_Window;

namespace vf {

class VulkanRenderer final {
public:
    explicit VulkanRenderer(SDL_Window* window);
    ~VulkanRenderer();

    VulkanRenderer(const VulkanRenderer&) = delete;
    VulkanRenderer& operator=(const VulkanRenderer&) = delete;

    void uploadPlanetMesh(const PlanetMesh& mesh);
    void drawFrame(
        const glm::vec3& clearColor,
        const glm::mat4& viewProjection,
        const glm::dvec3& cameraPosition);
    void requestResize() noexcept { resizeRequested_ = true; }

    [[nodiscard]] const std::string& gpuName() const noexcept { return gpuName_; }
    [[nodiscard]] std::uint32_t apiVersion() const noexcept { return apiVersion_; }
    [[nodiscard]] std::uint64_t triangleCount() const noexcept { return static_cast<std::uint64_t>(indexCount_ / 3U); }

private:
    static constexpr std::uint32_t kFramesInFlight = 2;

    void createInstance();
    void createSurface();
    void selectPhysicalDevice();
    void createDevice();
    void createCommands();
    void createSyncObjects();

    void createSwapchain();
    void createSwapchainResources();
    void destroySwapchainResources() noexcept;
    void destroySwapchain() noexcept;
    void recreateSwapchain();

    void createDepthResources();
    void createGraphicsPipeline();
    void destroyMesh() noexcept;

    void createBuffer(
        VkDeviceSize size,
        VkBufferUsageFlags usage,
        VkMemoryPropertyFlags memoryProperties,
        VkBuffer& buffer,
        VkDeviceMemory& memory);
    [[nodiscard]] std::uint32_t findMemoryType(
        std::uint32_t typeFilter,
        VkMemoryPropertyFlags properties) const;
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
    std::vector<VkImageView> swapchainImageViews_;
    std::vector<bool> imageInitialized_;

    VkFormat depthFormat_{VK_FORMAT_D32_SFLOAT};
    VkImage depthImage_{VK_NULL_HANDLE};
    VkDeviceMemory depthMemory_{VK_NULL_HANDLE};
    VkImageView depthImageView_{VK_NULL_HANDLE};

    VkPipelineLayout pipelineLayout_{VK_NULL_HANDLE};
    VkPipeline graphicsPipeline_{VK_NULL_HANDLE};

    VkBuffer vertexBuffer_{VK_NULL_HANDLE};
    VkDeviceMemory vertexMemory_{VK_NULL_HANDLE};
    VkBuffer indexBuffer_{VK_NULL_HANDLE};
    VkDeviceMemory indexMemory_{VK_NULL_HANDLE};
    std::uint32_t indexCount_{};

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
