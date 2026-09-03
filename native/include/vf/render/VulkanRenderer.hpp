#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <vector>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>
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
    void setDynamicMesh(const PlanetMesh& mesh);
    void clearDynamicMesh();
    void drawFrame(
        const glm::vec3& clearColor,
        const glm::mat4& viewProjection,
        const glm::dvec3& cameraPosition,
        const glm::vec3& sunDirectionToLight = glm::vec3{0.38F, 0.83F, 0.41F},
        const glm::vec3& sunLinearColor = glm::vec3{1.0F},
        float sunIntensity = 2.2F,
        const glm::dvec3& staticObjectOrigin = glm::dvec3{0.0},
        const glm::dquat& staticObjectRotation = glm::dquat{1.0, 0.0, 0.0, 0.0});
    void requestResize() noexcept { resizeRequested_ = true; }

    [[nodiscard]] const std::string& gpuName() const noexcept { return gpuName_; }
    [[nodiscard]] std::uint32_t apiVersion() const noexcept { return apiVersion_; }
    [[nodiscard]] std::uint64_t triangleCount() const noexcept { return static_cast<std::uint64_t>(indexCount_ / 3U); }
    [[nodiscard]] std::uint64_t dynamicTriangleCount() const noexcept { return static_cast<std::uint64_t>(pendingDynamicIndices_.size() / 3U); }

private:
    static constexpr std::uint32_t kFramesInFlight = 2;

    struct DynamicFrameMesh {
        VkBuffer vertexBuffer{VK_NULL_HANDLE};
        VkDeviceMemory vertexMemory{VK_NULL_HANDLE};
        VkBuffer indexBuffer{VK_NULL_HANDLE};
        VkDeviceMemory indexMemory{VK_NULL_HANDLE};
        void* mappedVertices{};
        void* mappedIndices{};
        VkDeviceSize vertexCapacityBytes{};
        VkDeviceSize indexCapacityBytes{};
        std::uint32_t indexCount{};
    };

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
    void destroyDynamicFrameMesh(DynamicFrameMesh& mesh) noexcept;
    void ensureDynamicFrameCapacity(DynamicFrameMesh& mesh, VkDeviceSize vertexBytes, VkDeviceSize indexBytes);
    void uploadDynamicMeshForFrame(std::uint32_t frame);
    void drawBoundMesh(VkCommandBuffer commandBuffer, VkBuffer vertexBuffer, VkBuffer indexBuffer, std::uint32_t indexCount);

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

    std::vector<PlanetVertex> pendingDynamicVertices_;
    std::vector<std::uint32_t> pendingDynamicIndices_;
    std::array<DynamicFrameMesh, kFramesInFlight> dynamicMeshes_{};

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
