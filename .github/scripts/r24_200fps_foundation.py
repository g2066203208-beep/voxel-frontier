#!/usr/bin/env python3
"""Materialize the first R24 >200 FPS renderer foundation.

This deliberately targets structural GPU costs without reducing terrain resolution or visual
features:
  * static terrain becomes DEVICE_LOCAL and is populated through per-frame staging buffers;
  * terrain macro noise moves from fragment frequency to vertex frequency;
  * terrain aerial perspective optical work moves to the vertex stage and is interpolated.

The current CI Vulkan device is llvmpipe, so this script never claims a hardware-GPU FPS result.
It only establishes the correct memory/shader architecture and keeps the real Vulkan capture gates.
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
        raise SystemExit(f"{label}: expected exactly one source match, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{label}: materialized")


replace_once(
    HEADER,
    """        VkBuffer indexBuffer{VK_NULL_HANDLE};
        VkDeviceMemory indexMemory{VK_NULL_HANDLE};
        void* mappedVertices{};
        void* mappedIndices{};
        VkDeviceSize vertexCapacityBytes{};
""",
    """        VkBuffer indexBuffer{VK_NULL_HANDLE};
        VkDeviceMemory indexMemory{VK_NULL_HANDLE};
        // Static terrain is consumed from DEVICE_LOCAL memory. The per-frame upload buffers are
        // only transfer sources, preserving fence ownership without forcing a global GPU idle.
        VkBuffer uploadVertexBuffer{VK_NULL_HANDLE};
        VkDeviceMemory uploadVertexMemory{VK_NULL_HANDLE};
        VkBuffer uploadIndexBuffer{VK_NULL_HANDLE};
        VkDeviceMemory uploadIndexMemory{VK_NULL_HANDLE};
        void* mappedVertices{};
        void* mappedIndices{};
        void* mappedUploadVertices{};
        void* mappedUploadIndices{};
        bool deviceLocalStatic{};
        bool uploadPending{};
        VkDeviceSize vertexCapacityBytes{};
""",
    "header static staging fields",
)

replace_once(
    HEADER,
    """    void destroyFrameMesh(FrameMesh& mesh) noexcept;
    void ensureFrameCapacity(FrameMesh& mesh, VkDeviceSize vertexBytes, VkDeviceSize indexBytes);
    void uploadStaticMeshForFrame(std::uint32_t frame);
""",
    """    void destroyFrameMesh(FrameMesh& mesh) noexcept;
    void ensureFrameCapacity(FrameMesh& mesh, VkDeviceSize vertexBytes, VkDeviceSize indexBytes);
    void ensureStaticFrameCapacity(FrameMesh& mesh, VkDeviceSize vertexBytes, VkDeviceSize indexBytes);
    void uploadStaticMeshForFrame(std::uint32_t frame);
""",
    "header static capacity method",
)

replace_once(
    CPP,
    """void VulkanRenderer::destroyFrameMesh(FrameMesh& mesh) noexcept {
    if (mesh.mappedVertices != nullptr && mesh.vertexMemory != VK_NULL_HANDLE)
        vkUnmapMemory(device_, mesh.vertexMemory);
    if (mesh.mappedIndices != nullptr && mesh.indexMemory != VK_NULL_HANDLE)
        vkUnmapMemory(device_, mesh.indexMemory);
    if (mesh.indexBuffer != VK_NULL_HANDLE) vkDestroyBuffer(device_, mesh.indexBuffer, nullptr);
    if (mesh.indexMemory != VK_NULL_HANDLE) vkFreeMemory(device_, mesh.indexMemory, nullptr);
    if (mesh.vertexBuffer != VK_NULL_HANDLE) vkDestroyBuffer(device_, mesh.vertexBuffer, nullptr);
    if (mesh.vertexMemory != VK_NULL_HANDLE) vkFreeMemory(device_, mesh.vertexMemory, nullptr);
    mesh = {};
}
""",
    """void VulkanRenderer::destroyFrameMesh(FrameMesh& mesh) noexcept {
    if (mesh.mappedVertices != nullptr && mesh.vertexMemory != VK_NULL_HANDLE)
        vkUnmapMemory(device_, mesh.vertexMemory);
    if (mesh.mappedIndices != nullptr && mesh.indexMemory != VK_NULL_HANDLE)
        vkUnmapMemory(device_, mesh.indexMemory);
    if (mesh.mappedUploadVertices != nullptr && mesh.uploadVertexMemory != VK_NULL_HANDLE)
        vkUnmapMemory(device_, mesh.uploadVertexMemory);
    if (mesh.mappedUploadIndices != nullptr && mesh.uploadIndexMemory != VK_NULL_HANDLE)
        vkUnmapMemory(device_, mesh.uploadIndexMemory);
    if (mesh.uploadIndexBuffer != VK_NULL_HANDLE)
        vkDestroyBuffer(device_, mesh.uploadIndexBuffer, nullptr);
    if (mesh.uploadIndexMemory != VK_NULL_HANDLE)
        vkFreeMemory(device_, mesh.uploadIndexMemory, nullptr);
    if (mesh.uploadVertexBuffer != VK_NULL_HANDLE)
        vkDestroyBuffer(device_, mesh.uploadVertexBuffer, nullptr);
    if (mesh.uploadVertexMemory != VK_NULL_HANDLE)
        vkFreeMemory(device_, mesh.uploadVertexMemory, nullptr);
    if (mesh.indexBuffer != VK_NULL_HANDLE) vkDestroyBuffer(device_, mesh.indexBuffer, nullptr);
    if (mesh.indexMemory != VK_NULL_HANDLE) vkFreeMemory(device_, mesh.indexMemory, nullptr);
    if (mesh.vertexBuffer != VK_NULL_HANDLE) vkDestroyBuffer(device_, mesh.vertexBuffer, nullptr);
    if (mesh.vertexMemory != VK_NULL_HANDLE) vkFreeMemory(device_, mesh.vertexMemory, nullptr);
    mesh = {};
}
""",
    "destroy staging buffers",
)

# Insert a static-only DEVICE_LOCAL allocator after the existing dynamic host-visible allocator.
marker = """    mesh.vertexCapacityBytes = vertexCapacity;
    mesh.indexCapacityBytes = indexCapacity;
}

void VulkanRenderer::uploadPlanetMesh(const PlanetMesh& mesh) {
"""
insert = """    mesh.vertexCapacityBytes = vertexCapacity;
    mesh.indexCapacityBytes = indexCapacity;
}

void VulkanRenderer::ensureStaticFrameCapacity(
    FrameMesh& mesh,
    VkDeviceSize vertexBytes,
    VkDeviceSize indexBytes) {
    if (mesh.deviceLocalStatic
        && vertexBytes <= mesh.vertexCapacityBytes
        && indexBytes <= mesh.indexCapacityBytes) return;

    const VkDeviceSize vertexCapacity = growCapacity(
        mesh.vertexCapacityBytes, vertexBytes, 256U * 1024U);
    const VkDeviceSize indexCapacity = growCapacity(
        mesh.indexCapacityBytes, indexBytes, 128U * 1024U);

    // Khronos' recommended static-geometry path: CPU-visible staging -> DEVICE_LOCAL draw buffers.
    // The caller owns this frame slot only after its fence signals, so replacement is race-free.
    destroyFrameMesh(mesh);
    createBuffer(
        vertexCapacity,
        VK_BUFFER_USAGE_VERTEX_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT,
        VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
        mesh.vertexBuffer,
        mesh.vertexMemory);
    createBuffer(
        indexCapacity,
        VK_BUFFER_USAGE_INDEX_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT,
        VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
        mesh.indexBuffer,
        mesh.indexMemory);
    createBuffer(
        vertexCapacity,
        VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
        mesh.uploadVertexBuffer,
        mesh.uploadVertexMemory);
    createBuffer(
        indexCapacity,
        VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
        mesh.uploadIndexBuffer,
        mesh.uploadIndexMemory);

    VkResult result = vkMapMemory(
        device_, mesh.uploadVertexMemory, 0, vertexCapacity, 0, &mesh.mappedUploadVertices);
    if (result != VK_SUCCESS) fail("vkMapMemory(static staging vertex) failed", result);
    result = vkMapMemory(
        device_, mesh.uploadIndexMemory, 0, indexCapacity, 0, &mesh.mappedUploadIndices);
    if (result != VK_SUCCESS) fail("vkMapMemory(static staging index) failed", result);
    mesh.deviceLocalStatic = true;
    mesh.vertexCapacityBytes = vertexCapacity;
    mesh.indexCapacityBytes = indexCapacity;
}

void VulkanRenderer::uploadPlanetMesh(const PlanetMesh& mesh) {
"""
replace_once(CPP, marker, insert, "device local static allocator")

replace_once(
    CPP,
    """    ensureFrameCapacity(mesh, vertexBytes, indexBytes);
    std::memcpy(
        mesh.mappedVertices, pending->vertices.data(), static_cast<std::size_t>(vertexBytes));
    std::memcpy(
        mesh.mappedIndices, pending->indices.data(), static_cast<std::size_t>(indexBytes));
    mesh.indexCount = static_cast<std::uint32_t>(pending->indices.size());
""",
    """    ensureStaticFrameCapacity(mesh, vertexBytes, indexBytes);
    std::memcpy(
        mesh.mappedUploadVertices, pending->vertices.data(), static_cast<std::size_t>(vertexBytes));
    std::memcpy(
        mesh.mappedUploadIndices, pending->indices.data(), static_cast<std::size_t>(indexBytes));
    mesh.uploadPending = true;
    mesh.indexCount = static_cast<std::uint32_t>(pending->indices.size());
""",
    "static staging upload",
)

replace_once(
    CPP,
    """    const auto& staticMesh = staticMeshes_[frame];
    const auto& dynamic = dynamicMeshes_[frame];
""",
    """    auto& staticMesh = staticMeshes_[frame];
    const auto& dynamic = dynamicMeshes_[frame];
""",
    "mutable static frame mesh",
)

copy_anchor = """    if (gpuTimestampsSupported_) {
        vkCmdResetQueryPool(command, timestampQueryPools_[frame], 0U, kTimestampQueryCount);
        vkCmdWriteTimestamp2(
            command, VK_PIPELINE_STAGE_2_TOP_OF_PIPE_BIT, timestampQueryPools_[frame], 0U);
    }

    VkImageMemoryBarrier2 shadowToAttachment{};
"""
copy_block = """    if (gpuTimestampsSupported_) {
        vkCmdResetQueryPool(command, timestampQueryPools_[frame], 0U, kTimestampQueryCount);
        vkCmdWriteTimestamp2(
            command, VK_PIPELINE_STAGE_2_TOP_OF_PIPE_BIT, timestampQueryPools_[frame], 0U);
    }

    if (staticMesh.uploadPending) {
        VkBufferCopy vertexCopy{};
        vertexCopy.size = static_cast<VkDeviceSize>(
            pendingStaticMesh_ ? pendingStaticMesh_->vertices.size() * sizeof(PlanetVertex) : 0U);
        VkBufferCopy indexCopy{};
        indexCopy.size = static_cast<VkDeviceSize>(
            pendingStaticMesh_ ? pendingStaticMesh_->indices.size() * sizeof(std::uint32_t) : 0U);
        if (vertexCopy.size > 0U && indexCopy.size > 0U) {
            vkCmdCopyBuffer(
                command, staticMesh.uploadVertexBuffer, staticMesh.vertexBuffer, 1U, &vertexCopy);
            vkCmdCopyBuffer(
                command, staticMesh.uploadIndexBuffer, staticMesh.indexBuffer, 1U, &indexCopy);

            VkMemoryBarrier2 uploadBarrier{};
            uploadBarrier.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER_2;
            uploadBarrier.srcStageMask = VK_PIPELINE_STAGE_2_TRANSFER_BIT;
            uploadBarrier.srcAccessMask = VK_ACCESS_2_TRANSFER_WRITE_BIT;
            uploadBarrier.dstStageMask = VK_PIPELINE_STAGE_2_VERTEX_INPUT_BIT;
            uploadBarrier.dstAccessMask = VK_ACCESS_2_VERTEX_ATTRIBUTE_READ_BIT
                | VK_ACCESS_2_INDEX_READ_BIT;
            VkDependencyInfo uploadDependency{};
            uploadDependency.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO;
            uploadDependency.memoryBarrierCount = 1U;
            uploadDependency.pMemoryBarriers = &uploadBarrier;
            vkCmdPipelineBarrier2(command, &uploadDependency);
        }
        staticMesh.uploadPending = false;
    }

    VkImageMemoryBarrier2 shadowToAttachment{};
"""
replace_once(CPP, copy_anchor, copy_block, "record static transfer before draw")

# Vertex-frequency terrain macro + terrain-only aerial data. This preserves the same macro function
# and the same atmosphere coefficients; only evaluation frequency changes.
replace_once(
    SHADER,
    """    float4 shadowPosition : TEXCOORD4;
    float3 objectPosition : TEXCOORD5;
};
""",
    """    float4 shadowPosition : TEXCOORD4;
    float3 objectPosition : TEXCOORD5;
    float terrainMacro : TEXCOORD6;
    float3 terrainAerialTransmittance : TEXCOORD7;
    float3 terrainAerialInscatter : TEXCOORD8;
};
""",
    "shader terrain vertex varyings",
)

vertex_old = """    output.material = input.material;
    output.shadowPosition = mul(gScene.lightViewProjection, float4(relativePosition, 1.0));
    output.objectPosition = input.position;
    return output;
}
"""
vertex_new = """    output.material = input.material;
    output.shadowPosition = mul(gScene.lightViewProjection, float4(relativePosition, 1.0));
    output.objectPosition = input.position;

    const bool terrainMaterial = input.material.w < -0.5 && input.material.w > -1.5;
    output.terrainMacro = terrainMaterial ? valueNoise2(input.position.xz * 0.0032) : 0.5;
    output.terrainAerialTransmittance = float3(1.0, 1.0, 1.0);
    output.terrainAerialInscatter = float3(0.0, 0.0, 0.0);
    if (terrainMaterial)
    {
        // Same optical model as the former fragment path, evaluated once per terrain vertex.
        // Planet LOD cells are much smaller than the 350 m haze onset and atmospheric scale,
        // so perspective-correct interpolation preserves the continuous appearance while removing
        // length/normalize/pow/exp work from every covered terrain pixel.
        float distanceMeters = length(relativePosition);
        if (distanceMeters > 350.0)
        {
            float3 viewDir = relativePosition / max(distanceMeters, 1.0e-4);
            float3 sunDir = normalize(gPush.data1.xyz);
            float cameraAltitude = max(gPush.data0.w, 0.0);
            float densityRatio = exp(-cameraAltitude / 8500.0);
            float effectiveDistance = min(max(distanceMeters - 350.0, 0.0), 220000.0);
            float horizon = pow(saturate(1.0 - abs(viewDir.y)), 1.15);
            float opticalLength = effectiveDistance * densityRatio
                * (0.55 + 0.45 * horizon) * 0.58;
            const float3 betaR = float3(5.802e-6, 13.558e-6, 33.100e-6);
            const float betaM = 4.0e-6;
            float3 transmittance = exp(-(betaR + betaM) * opticalLength);
            float3 haze = stylizedSkyPalette(viewDir, sunDir);
            output.terrainAerialTransmittance = transmittance;
            output.terrainAerialInscatter = haze * (1.0 - transmittance);
        }
    }
    return output;
}
"""
replace_once(SHADER, vertex_old, vertex_new, "shader vertex frequency terrain optics")

replace_once(
    SHADER,
    """    float macro = valueNoise2(input.objectPosition.xz * 0.0032);
""",
    """    float macro = input.terrainMacro;
""",
    "terrain macro interpolation",
)

opaque_old = """    float3 linearColor = (terrainMaterial
        ? evaluateTerrainFast(input)
        : evaluatePbr(input, false)) * exposure;
    // Terrain needs enough atmospheric perspective to read planet scale, but not so much that
    // 10--100 km mountain chains disappear. Near-field ecology can take slightly stronger haze.
    float hazeStrength = materialTag < -0.5 && materialTag > -1.5 ? 0.58
        : (materialTag <= -1.5 && materialTag > -4.5 ? 0.72 : 0.66);
    linearColor = applyStylizedAerial(linearColor, input, hazeStrength);
"""
opaque_new = """    float3 linearColor = (terrainMaterial
        ? evaluateTerrainFast(input)
        : evaluatePbr(input, false)) * exposure;
    // Terrain uses the identical atmospheric model evaluated at vertices. Ecology/rocks retain the
    // fragment path because their triangles are larger relative to local silhouettes.
    if (terrainMaterial)
    {
        linearColor = linearColor * input.terrainAerialTransmittance
            + input.terrainAerialInscatter;
    }
    else
    {
        float hazeStrength = materialTag <= -1.5 && materialTag > -4.5 ? 0.72 : 0.66;
        linearColor = applyStylizedAerial(linearColor, input, hazeStrength);
    }
"""
replace_once(SHADER, opaque_old, opaque_new, "terrain aerial interpolation")

# Hard postconditions catch accidental materializer drift before expensive builds.
header = HEADER.read_text(encoding="utf-8")
cpp = CPP.read_text(encoding="utf-8")
shader = SHADER.read_text(encoding="utf-8")
checks = {
    "device-local vertex": "VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT" in cpp,
    "static transfer dst": "VK_BUFFER_USAGE_VERTEX_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT" in cpp,
    "static transfer command": "vkCmdCopyBuffer(" in cpp and "staticMesh.uploadVertexBuffer" in cpp,
    "vertex input barrier": "VK_ACCESS_2_VERTEX_ATTRIBUTE_READ_BIT" in cpp,
    "terrain macro varying": "float terrainMacro : TEXCOORD6;" in shader,
    "fragment macro removed": "float macro = valueNoise2(input.objectPosition.xz * 0.0032);" not in shader,
    "terrain aerial varying": "terrainAerialTransmittance" in shader,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("postcondition failure: " + ", ".join(failed))

print("R24 200 FPS foundation materialized successfully")
