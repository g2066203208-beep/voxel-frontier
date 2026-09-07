from pathlib import Path

HEADER = Path('native/include/vf/render/VulkanRenderer.hpp')
SOURCE = Path('native/src/render/VulkanRenderer.cpp')
h = HEADER.read_text(encoding='utf-8')
s = SOURCE.read_text(encoding='utf-8')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {count}')
    return text.replace(old, new, 1)


h = replace_once(
    h,
'''        VkDeviceSize vertexCapacityBytes{};
        VkDeviceSize indexCapacityBytes{};
        std::uint32_t indexCount{};
''',
'''        VkDeviceSize vertexCapacityBytes{};
        VkDeviceSize indexCapacityBytes{};
        std::uint32_t indexCount{};
        std::uint32_t opaqueIndexCount{};
        std::uint32_t transparentIndexCount{};
''',
    'FrameMesh pass counts')

h = replace_once(
    h,
'''    void drawBoundMesh(
        VkCommandBuffer commandBuffer,
        VkBuffer vertexBuffer,
        VkBuffer indexBuffer,
        std::uint32_t indexCount);
''',
'''    void drawBoundMesh(
        VkCommandBuffer commandBuffer,
        VkBuffer vertexBuffer,
        VkBuffer indexBuffer,
        std::uint32_t indexCount,
        std::uint32_t firstIndex = 0U);
''',
    'drawBoundMesh firstIndex')

h = replace_once(
    h,
'''    std::vector<PlanetVertex> pendingStaticVertices_;
    std::vector<std::uint32_t> pendingStaticIndices_;
    std::uint64_t staticMeshGeneration_{};
''',
'''    std::vector<PlanetVertex> pendingStaticVertices_;
    std::vector<std::uint32_t> pendingStaticIndices_;
    std::uint32_t pendingStaticOpaqueIndexCount_{};
    std::uint32_t pendingStaticTransparentIndexCount_{};
    std::uint64_t staticMeshGeneration_{};
''',
    'static pass counts')

h = replace_once(
    h,
'''    std::vector<PlanetVertex> pendingDynamicVertices_;
    std::vector<std::uint32_t> pendingDynamicIndices_;
    std::array<FrameMesh, kFramesInFlight> dynamicMeshes_{};
''',
'''    std::vector<PlanetVertex> pendingDynamicVertices_;
    std::vector<std::uint32_t> pendingDynamicIndices_;
    std::uint32_t pendingDynamicOpaqueIndexCount_{};
    std::uint32_t pendingDynamicTransparentIndexCount_{};
    std::array<FrameMesh, kFramesInFlight> dynamicMeshes_{};
''',
    'dynamic pass counts')

s = replace_once(
    s,
'''[[nodiscard]] VkDeviceSize growCapacity(VkDeviceSize current, VkDeviceSize required, VkDeviceSize minimum) {
    VkDeviceSize capacity = std::max(current, minimum);
    while (capacity < required) {
        if (capacity > std::numeric_limits<VkDeviceSize>::max() / 2U) return required;
        capacity *= 2U;
    }
    return capacity;
}

[[nodiscard]] glm::mat4 makeShadowViewProjection''',
'''[[nodiscard]] VkDeviceSize growCapacity(VkDeviceSize current, VkDeviceSize required, VkDeviceSize minimum) {
    VkDeviceSize capacity = std::max(current, minimum);
    while (capacity < required) {
        if (capacity > std::numeric_limits<VkDeviceSize>::max() / 2U) return required;
        capacity *= 2U;
    }
    return capacity;
}

void partitionMeshIndicesByTransmission(
    const PlanetMesh& mesh,
    std::vector<std::uint32_t>& output,
    std::uint32_t& opaqueIndexCount,
    std::uint32_t& transparentIndexCount) {
    if ((mesh.indices.size() % 3U) != 0U)
        fail("Planet mesh index stream must contain complete triangles");
    output.clear();
    output.reserve(mesh.indices.size());

    const auto triangleIsTransparent = [&](std::size_t base) {
        for (std::size_t corner = 0; corner < 3U; ++corner) {
            const std::uint32_t index = mesh.indices[base + corner];
            if (index >= mesh.vertices.size()) fail("Planet mesh index out of range");
            // material.z is transmission in planet.slang. A triangle touching a transmissive
            // vertex stays in the transparent pass, matching the previous fragment-discard rule.
            if (mesh.vertices[index].material.z > 0.02F) return true;
        }
        return false;
    };

    for (std::size_t base = 0; base < mesh.indices.size(); base += 3U) {
        if (triangleIsTransparent(base)) continue;
        output.insert(output.end(), {
            mesh.indices[base], mesh.indices[base + 1U], mesh.indices[base + 2U]});
    }
    opaqueIndexCount = static_cast<std::uint32_t>(output.size());
    for (std::size_t base = 0; base < mesh.indices.size(); base += 3U) {
        if (!triangleIsTransparent(base)) continue;
        output.insert(output.end(), {
            mesh.indices[base], mesh.indices[base + 1U], mesh.indices[base + 2U]});
    }
    transparentIndexCount = static_cast<std::uint32_t>(output.size()) - opaqueIndexCount;
    if (output.size() != mesh.indices.size()) fail("Render pass index partition lost triangles");
}

[[nodiscard]] glm::mat4 makeShadowViewProjection''',
    'partition helper')

s = replace_once(
    s,
'''void VulkanRenderer::uploadPlanetMesh(const PlanetMesh& mesh) {
    if (mesh.vertices.empty() || mesh.indices.empty()) fail("Cannot upload an empty planet mesh");
    pendingStaticVertices_ = mesh.vertices;
    pendingStaticIndices_ = mesh.indices;
    ++staticMeshGeneration_;
''',
'''void VulkanRenderer::uploadPlanetMesh(const PlanetMesh& mesh) {
    if (mesh.vertices.empty() || mesh.indices.empty()) fail("Cannot upload an empty planet mesh");
    pendingStaticVertices_ = mesh.vertices;
    partitionMeshIndicesByTransmission(
        mesh,
        pendingStaticIndices_,
        pendingStaticOpaqueIndexCount_,
        pendingStaticTransparentIndexCount_);
    ++staticMeshGeneration_;
''',
    'static partition upload')

s = replace_once(
    s,
'''    if (pendingStaticVertices_.empty() || pendingStaticIndices_.empty()) {
        mesh.indexCount = 0U;
        staticMeshGenerationByFrame_[frame] = staticMeshGeneration_;
        return;
    }
''',
'''    if (pendingStaticVertices_.empty() || pendingStaticIndices_.empty()) {
        mesh.indexCount = 0U;
        mesh.opaqueIndexCount = 0U;
        mesh.transparentIndexCount = 0U;
        staticMeshGenerationByFrame_[frame] = staticMeshGeneration_;
        return;
    }
''',
    'static empty counts')

s = replace_once(
    s,
'''    mesh.indexCount = static_cast<std::uint32_t>(pendingStaticIndices_.size());
    staticMeshGenerationByFrame_[frame] = staticMeshGeneration_;
}

void VulkanRenderer::setDynamicMesh(const PlanetMesh& mesh) {
    pendingDynamicVertices_ = mesh.vertices;
    pendingDynamicIndices_ = mesh.indices;
}

void VulkanRenderer::clearDynamicMesh() {
    pendingDynamicVertices_.clear();
    pendingDynamicIndices_.clear();
}
''',
'''    mesh.indexCount = static_cast<std::uint32_t>(pendingStaticIndices_.size());
    mesh.opaqueIndexCount = pendingStaticOpaqueIndexCount_;
    mesh.transparentIndexCount = pendingStaticTransparentIndexCount_;
    staticMeshGenerationByFrame_[frame] = staticMeshGeneration_;
}

void VulkanRenderer::setDynamicMesh(const PlanetMesh& mesh) {
    pendingDynamicVertices_ = mesh.vertices;
    partitionMeshIndicesByTransmission(
        mesh,
        pendingDynamicIndices_,
        pendingDynamicOpaqueIndexCount_,
        pendingDynamicTransparentIndexCount_);
}

void VulkanRenderer::clearDynamicMesh() {
    pendingDynamicVertices_.clear();
    pendingDynamicIndices_.clear();
    pendingDynamicOpaqueIndexCount_ = 0U;
    pendingDynamicTransparentIndexCount_ = 0U;
}
''',
    'dynamic partition upload')

s = replace_once(
    s,
'''    if (pendingDynamicVertices_.empty() || pendingDynamicIndices_.empty()) {
        mesh.indexCount = 0U;
        return;
    }
''',
'''    if (pendingDynamicVertices_.empty() || pendingDynamicIndices_.empty()) {
        mesh.indexCount = 0U;
        mesh.opaqueIndexCount = 0U;
        mesh.transparentIndexCount = 0U;
        return;
    }
''',
    'dynamic empty counts')

s = replace_once(
    s,
'''    mesh.indexCount = static_cast<std::uint32_t>(pendingDynamicIndices_.size());
}

void VulkanRenderer::drawBoundMesh(
    VkCommandBuffer commandBuffer,
    VkBuffer vertexBuffer,
    VkBuffer indexBuffer,
    std::uint32_t indexCount) {
    if (vertexBuffer == VK_NULL_HANDLE || indexBuffer == VK_NULL_HANDLE || indexCount == 0U) return;
    constexpr VkDeviceSize offset = 0;
    vkCmdBindVertexBuffers(commandBuffer, 0, 1, &vertexBuffer, &offset);
    vkCmdBindIndexBuffer(commandBuffer, indexBuffer, 0, VK_INDEX_TYPE_UINT32);
    vkCmdDrawIndexed(commandBuffer, indexCount, 1, 0, 0, 0);
}
''',
'''    mesh.indexCount = static_cast<std::uint32_t>(pendingDynamicIndices_.size());
    mesh.opaqueIndexCount = pendingDynamicOpaqueIndexCount_;
    mesh.transparentIndexCount = pendingDynamicTransparentIndexCount_;
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
''',
    'draw firstIndex')

s = replace_once(
    s,
'''    drawBoundMesh(
        command, staticMesh.vertexBuffer, staticMesh.indexBuffer, staticMesh.indexCount);
''',
'''    drawBoundMesh(
        command, staticMesh.vertexBuffer, staticMesh.indexBuffer, staticMesh.opaqueIndexCount, 0U);
''',
    'static shadow opaque only')

s = replace_once(
    s,
'''    drawBoundMesh(command, dynamic.vertexBuffer, dynamic.indexBuffer, dynamic.indexCount);
    vkCmdEndRendering(command);
''',
'''    drawBoundMesh(command, dynamic.vertexBuffer, dynamic.indexBuffer, dynamic.opaqueIndexCount, 0U);
    vkCmdEndRendering(command);
''',
    'dynamic shadow opaque only')

s = replace_once(
    s,
'''    auto drawScenePass = [&](VkPipeline pipeline) {
''',
'''    auto drawScenePass = [&](VkPipeline pipeline, bool transparentPass) {
''',
    'scene pass selector')

s = replace_once(
    s,
'''        drawBoundMesh(
            command, staticMesh.vertexBuffer, staticMesh.indexBuffer, staticMesh.indexCount);
        scenePush.data3 = {0.0F, 0.0F, 0.0F, 1.0F};
''',
'''        const std::uint32_t staticCount = transparentPass
            ? staticMesh.transparentIndexCount : staticMesh.opaqueIndexCount;
        const std::uint32_t staticFirst = transparentPass ? staticMesh.opaqueIndexCount : 0U;
        drawBoundMesh(
            command, staticMesh.vertexBuffer, staticMesh.indexBuffer, staticCount, staticFirst);
        scenePush.data3 = {0.0F, 0.0F, 0.0F, 1.0F};
''',
    'static main pass range')

s = replace_once(
    s,
'''        drawBoundMesh(command, dynamic.vertexBuffer, dynamic.indexBuffer, dynamic.indexCount);
    };

    drawScenePass(opaquePipeline_);
    drawScenePass(transparentPipeline_);
''',
'''        const std::uint32_t dynamicCount = transparentPass
            ? dynamic.transparentIndexCount : dynamic.opaqueIndexCount;
        const std::uint32_t dynamicFirst = transparentPass ? dynamic.opaqueIndexCount : 0U;
        drawBoundMesh(command, dynamic.vertexBuffer, dynamic.indexBuffer, dynamicCount, dynamicFirst);
    };

    drawScenePass(opaquePipeline_, false);
    drawScenePass(transparentPipeline_, true);
''',
    'dynamic main pass range')

HEADER.write_text(h, encoding='utf-8')
SOURCE.write_text(s, encoding='utf-8')
print('R24 render pass partition materialized: opaque/transparent/shadow draw only their own index ranges')
