#pragma once

#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>
#include <volk.h>

#include "vf/world/PlanetSurface.hpp"

struct SDL_Window;

namespace vf {

struct RenderFrameEnvironment {
    glm::vec3 sunDirectionToLight{0.38F, 0.83F, 0.41F};
    glm::vec3 sunLinearColor{1.0F};
    float sunIntensity{2.2F};
    float sunAngularRadiusRadians{0.004675F};
    glm::vec3 skyAmbient{0.10F, 0.16F, 0.26F};
    glm::vec3 groundAmbient{0.035F, 0.030F, 0.024F};
    float exposure{1.0F};
    glm::vec3 cameraForward{0.0F, 0.0F, -1.0F};
    glm::dvec3 planetCenter{};
    double planetRadius{6371000.0};
    double atmosphereHeight{100000.0};
    double atmosphereScaleHeight{8500.0};
    float mieScale{1.0F};
    float flightSpeedMps{1.0F};
    // Remote moons/planets are visual dynamic meshes but cannot cast a meaningful shadow into the
    // 250 m local contact-shadow volume. CI can opt the dedicated contact probe back in.
    bool dynamicShadowCasters{false};
};

// CPU render preparation is intentionally detached from Vulkan object ownership. Terrain workers
// can classify triangles into [shadow casters | opaque receivers | transparent] while they are
// already off the render thread. The render thread then adopts this immutable payload by shared_ptr
// instead of copying tens of megabytes and rescanning every triangle at a streaming boundary.
struct PreparedPlanetMesh {
    std::vector<PlanetVertex> vertices{};
    std::vector<std::uint32_t> indices{};
    std::uint32_t shadowCasterIndexCount{};
    std::uint32_t opaqueIndexCount{};
    std::uint32_t transparentIndexCount{};
};

[[nodiscard]] PreparedPlanetMesh preparePlanetMesh(
    PlanetMesh mesh,
    bool excludeTerrainFromLocalShadow = true);

class VulkanRenderer final {
public:
    explicit VulkanRenderer(SDL_Window* window);
    ~VulkanRenderer();

    VulkanRenderer(const VulkanRenderer&) = delete;
    VulkanRenderer& operator=(const VulkanRenderer&) = delete;

    // Queues the newest static world mesh. Each in-flight frame owns its own mapped buffers and
    // adopts the newest generation only after that frame's fence is signaled; terrain recentering
    // therefore never calls vkDeviceWaitIdle or destroys a buffer still used by the GPU.
    void uploadPlanetMesh(const PlanetMesh& mesh);
    void uploadPlanetMesh(std::shared_ptr<const PreparedPlanetMesh> mesh);
    void setDynamicMesh(const PlanetMesh& mesh);
    void clearDynamicMesh();
    void drawFrame(
        const glm::mat4& viewProjection,
        const glm::dvec3& cameraPosition,
        const RenderFrameEnvironment& environment,
        const glm::dquat& staticObjectRotation = glm::dquat{1.0, 0.0, 0.0, 0.0});
    void requestResize() noexcept { resizeRequested_ = true; }

    [[nodiscard]] const std::string& gpuName() const noexcept { return gpuName_; }
    [[nodiscard]] std::uint32_t apiVersion() const noexcept { return apiVersion_; }
    [[nodiscard]] std::uint64_t triangleCount() const noexcept {
        return pendingStaticMesh_
            ? static_cast<std::uint64_t>(pendingStaticMesh_->indices.size() / 3U)
            : 0U;
    }
    [[nodiscard]] std::uint64_t dynamicTriangleCount() const noexcept {
        return static_cast<std::uint64_t>(pendingDynamicIndices_.size() / 3U);
    }

private:
    static constexpr std::uint32_t kFramesInFlight = 2;
    // A 250 m contact-shadow box at 1024 gives ~24 cm texels before PCF. That is sufficient for
    // tree/prop grounding while quartering depth-raster pixels versus the previous 2048 map.
    static constexpr std::uint32_t kShadowMapSize = 1024;

    struct FrameMesh {
        VkBuffer vertexBuffer{VK_NULL_HANDLE};
        VkDeviceMemory vertexMemory{VK_NULL_HANDLE};
        VkBuffer indexBuffer{VK_NULL_HANDLE};
        VkDeviceMemory indexMemory{VK_NULL_HANDLE};
        void* mappedVertices{};
        void* mappedIndices{};
        VkDeviceSize vertexCapacityBytes{};
        VkDeviceSize indexCapacityBytes{};
        std::uint32_t indexCount{};
        // Static indices are ordered [local shadow casters | opaque receivers | transparent].
        // The main opaque pass still consumes the complete opaque range, while the 250 m contact
        // shadow map only transforms true local casters instead of millions of terrain triangles.
        std::uint32_t shadowCasterIndexCount{};
        std::uint32_t opaqueIndexCount{};
        std::uint32_t transparentIndexCount{};
    };

    struct DepthFrameResources {
        VkImage image{VK_NULL_HANDLE};
        VkDeviceMemory memory{VK_NULL_HANDLE};
        VkImageView view{VK_NULL_HANDLE};
    };

    struct ShadowFrameResources {
        VkImage depthImage{VK_NULL_HANDLE};
        VkDeviceMemory depthMemory{VK_NULL_HANDLE};
        VkImageView depthView{VK_NULL_HANDLE};
        VkBuffer uniformBuffer{VK_NULL_HANDLE};
        VkDeviceMemory uniformMemory{VK_NULL_HANDLE};
        void* mappedUniform{};
        VkDescriptorSet descriptorSet{VK_NULL_HANDLE};
    };

    void createInstance();
    void createSurface();
    void selectPhysicalDevice();
    void createDevice();
    void createCommands();
    void createSyncObjects();
    void destroyTimestampQueries() noexcept;
    void readTimestampQueries(std::uint32_t frame);

    void createSwapchain();
    void createSwapchainResources();
    void destroySwapchainResources() noexcept;
    void destroySwapchain() noexcept;
    void recreateSwapchain();

    void createMainDepthResources();
    void destroyMainDepthResources() noexcept;
    void createShadowResources();
    void destroyShadowResources() noexcept;
    void createDescriptorResources();
    void destroyDescriptorResources() noexcept;
    void createPipelines();
    void destroyPipelines() noexcept;

    void destroyFrameMesh(FrameMesh& mesh) noexcept;
    void ensureFrameCapacity(FrameMesh& mesh, VkDeviceSize vertexBytes, VkDeviceSize indexBytes);
    void uploadStaticMeshForFrame(std::uint32_t frame);
    void uploadDynamicMeshForFrame(std::uint32_t frame);
    void drawBoundMesh(
        VkCommandBuffer commandBuffer,
        VkBuffer vertexBuffer,
        VkBuffer indexBuffer,
        std::uint32_t indexCount,
        std::uint32_t firstIndex = 0U);

    void createBuffer(
        VkDeviceSize size,
        VkBufferUsageFlags usage,
        VkMemoryPropertyFlags memoryProperties,
        VkBuffer& buffer,
        VkDeviceMemory& memory);
    void createDepthImage(
        std::uint32_t width,
        std::uint32_t height,
        VkImageUsageFlags usage,
        VkImage& image,
        VkDeviceMemory& memory,
        VkImageView& view);
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
    std::array<DepthFrameResources, kFramesInFlight> depthFrames_{};

    VkDescriptorSetLayout sceneDescriptorSetLayout_{VK_NULL_HANDLE};
    VkDescriptorPool sceneDescriptorPool_{VK_NULL_HANDLE};
    VkSampler shadowSampler_{VK_NULL_HANDLE};
    std::array<ShadowFrameResources, kFramesInFlight> shadowFrames_{};

    VkPipelineLayout scenePipelineLayout_{VK_NULL_HANDLE};
    VkPipelineLayout fullscreenPipelineLayout_{VK_NULL_HANDLE};
    VkPipeline opaquePipeline_{VK_NULL_HANDLE};
    VkPipeline transparentPipeline_{VK_NULL_HANDLE};
    VkPipeline shadowPipeline_{VK_NULL_HANDLE};
    VkPipeline skyPipeline_{VK_NULL_HANDLE};
    VkPipeline hudPipeline_{VK_NULL_HANDLE};

    std::shared_ptr<const PreparedPlanetMesh> pendingStaticMesh_{};
    std::uint64_t staticMeshGeneration_{};
    std::array<std::uint64_t, kFramesInFlight> staticMeshGenerationByFrame_{};
    std::array<FrameMesh, kFramesInFlight> staticMeshes_{};

    std::vector<PlanetVertex> pendingDynamicVertices_;
    std::vector<std::uint32_t> pendingDynamicIndices_;
    std::uint32_t pendingDynamicShadowCasterIndexCount_{};
    std::uint32_t pendingDynamicOpaqueIndexCount_{};
    std::uint32_t pendingDynamicTransparentIndexCount_{};
    std::uint64_t dynamicMeshGeneration_{};
    std::array<std::uint64_t, kFramesInFlight> dynamicMeshGenerationByFrame_{};
    std::array<FrameMesh, kFramesInFlight> dynamicMeshes_{};

    VkCommandPool commandPool_{VK_NULL_HANDLE};
    std::array<VkCommandBuffer, kFramesInFlight> commandBuffers_{};
    std::array<VkSemaphore, kFramesInFlight> imageAvailable_{};
    std::array<VkSemaphore, kFramesInFlight> renderFinished_{};
    std::array<VkFence, kFramesInFlight> inFlight_{};

    // Eight timestamps = [shadow begin/end, opaque begin/end, sky begin/end, transparent begin/end].
    // Results are read only after this frame slot's fence signals, so profiling never stalls the GPU.
    static constexpr std::uint32_t kTimestampQueryCount = 8U;
    std::array<VkQueryPool, kFramesInFlight> timestampQueryPools_{};
    std::array<bool, kFramesInFlight> timestampQueryWritten_{};
    float timestampPeriodNanoseconds_{1.0F};
    std::uint32_t timestampValidBits_{};
    std::uint64_t timestampMask_{~std::uint64_t{0}};
    std::uint64_t gpuTimingSamples_{};
    bool gpuTimestampsSupported_{};

    std::uint32_t frameIndex_{};
    std::uint32_t apiVersion_{};
    std::string gpuName_;
    bool resizeRequested_{true};
};

} // namespace vf
