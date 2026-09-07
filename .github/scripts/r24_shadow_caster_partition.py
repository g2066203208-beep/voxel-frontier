from pathlib import Path

HEADER = Path('native/include/vf/render/VulkanRenderer.hpp')
CPP = Path('native/src/render/VulkanRenderer.cpp')
h = HEADER.read_text(encoding='utf-8')
c = CPP.read_text(encoding='utf-8')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {count}')
    return text.replace(old, new, 1)


h = replace_once(
    h,
'''        std::uint32_t indexCount{};
        std::uint32_t opaqueIndexCount{};
        std::uint32_t transparentIndexCount{};
''',
'''        std::uint32_t indexCount{};
        // Static indices are ordered [local shadow casters | opaque receivers | transparent].
        // The main opaque pass still consumes the complete opaque range, while the 250 m contact
        // shadow map only transforms true local casters instead of millions of terrain triangles.
        std::uint32_t shadowCasterIndexCount{};
        std::uint32_t opaqueIndexCount{};
        std::uint32_t transparentIndexCount{};
''',
    'FrameMesh shadow caster count')

h = replace_once(
    h,
'''    std::vector<std::uint32_t> pendingStaticIndices_;
    std::uint32_t pendingStaticOpaqueIndexCount_{};
''',
'''    std::vector<std::uint32_t> pendingStaticIndices_;
    std::uint32_t pendingStaticShadowCasterIndexCount_{};
    std::uint32_t pendingStaticOpaqueIndexCount_{};
''',
    'pending static shadow count')

h = replace_once(
    h,
'''    std::vector<std::uint32_t> pendingDynamicIndices_;
    std::uint32_t pendingDynamicOpaqueIndexCount_{};
''',
'''    std::vector<std::uint32_t> pendingDynamicIndices_;
    std::uint32_t pendingDynamicShadowCasterIndexCount_{};
    std::uint32_t pendingDynamicOpaqueIndexCount_{};
''',
    'pending dynamic shadow count')

old_partition = '''void partitionMeshIndicesByTransmission(
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
'''
new_partition = '''void partitionMeshIndicesForRenderPasses(
    const PlanetMesh& mesh,
    bool excludeTerrainFromLocalShadow,
    std::vector<std::uint32_t>& output,
    std::uint32_t& shadowCasterIndexCount,
    std::uint32_t& opaqueIndexCount,
    std::uint32_t& transparentIndexCount) {
    if ((mesh.indices.size() % 3U) != 0U)
        fail("Planet mesh index stream must contain complete triangles");

    // Classification is paid only when a mesh generation changes. The old implementation scanned
    // every triangle twice just to split opaque/transparent; classify once, then compact three
    // contiguous draw ranges. This mirrors meshlet/material-bin renderers without requiring a GPU
    // driven rewrite in this rescue patch.
    enum class TriangleClass : std::uint8_t { ShadowCaster, OpaqueReceiver, Transparent };
    const std::size_t triangleCount = mesh.indices.size() / 3U;
    std::vector<TriangleClass> classes;
    classes.reserve(triangleCount);

    for (std::size_t base = 0; base < mesh.indices.size(); base += 3U) {
        bool transparent = false;
        bool terrain = true;
        for (std::size_t corner = 0; corner < 3U; ++corner) {
            const std::uint32_t index = mesh.indices[base + corner];
            if (index >= mesh.vertices.size()) fail("Planet mesh index out of range");
            const auto& material = mesh.vertices[index].material;
            // material.z is transmission. material.w == roughly -1 is the terrain semantic used by
            // planet.slang. Terrain remains fully visible and receives shadows; it simply does not
            // re-rasterize itself into a tiny 250 m contact-shadow atlas.
            transparent = transparent || material.z > 0.02F;
            const bool cornerIsTerrain = material.w < -0.5F && material.w > -1.5F;
            terrain = terrain && cornerIsTerrain;
        }
        if (transparent) classes.push_back(TriangleClass::Transparent);
        else if (excludeTerrainFromLocalShadow && terrain)
            classes.push_back(TriangleClass::OpaqueReceiver);
        else
            classes.push_back(TriangleClass::ShadowCaster);
    }

    output.clear();
    output.reserve(mesh.indices.size());
    const auto appendClass = [&](TriangleClass wanted) {
        for (std::size_t triangle = 0; triangle < classes.size(); ++triangle) {
            if (classes[triangle] != wanted) continue;
            const std::size_t base = triangle * 3U;
            output.push_back(mesh.indices[base]);
            output.push_back(mesh.indices[base + 1U]);
            output.push_back(mesh.indices[base + 2U]);
        }
    };

    appendClass(TriangleClass::ShadowCaster);
    shadowCasterIndexCount = static_cast<std::uint32_t>(output.size());
    appendClass(TriangleClass::OpaqueReceiver);
    opaqueIndexCount = static_cast<std::uint32_t>(output.size());
    appendClass(TriangleClass::Transparent);
    transparentIndexCount = static_cast<std::uint32_t>(output.size()) - opaqueIndexCount;
    if (output.size() != mesh.indices.size()) fail("Render pass index partition lost triangles");
}
'''
c = replace_once(c, old_partition, new_partition, 'render pass partition')

c = replace_once(
    c,
'''    partitionMeshIndicesByTransmission(
        mesh,
        pendingStaticIndices_,
        pendingStaticOpaqueIndexCount_,
        pendingStaticTransparentIndexCount_);
''',
'''    partitionMeshIndicesForRenderPasses(
        mesh,
        true,
        pendingStaticIndices_,
        pendingStaticShadowCasterIndexCount_,
        pendingStaticOpaqueIndexCount_,
        pendingStaticTransparentIndexCount_);
    SDL_Log(
        "R24 PERF shadow_caster_indices=%u opaque_indices=%u shadow_reduction=%.3f",
        pendingStaticShadowCasterIndexCount_,
        pendingStaticOpaqueIndexCount_,
        pendingStaticOpaqueIndexCount_ > 0U
            ? 1.0 - static_cast<double>(pendingStaticShadowCasterIndexCount_)
                / static_cast<double>(pendingStaticOpaqueIndexCount_)
            : 1.0);
''',
    'static render pass partition')

c = replace_once(
    c,
'''        mesh.indexCount = 0U;
        mesh.opaqueIndexCount = 0U;
        mesh.transparentIndexCount = 0U;
''',
'''        mesh.indexCount = 0U;
        mesh.shadowCasterIndexCount = 0U;
        mesh.opaqueIndexCount = 0U;
        mesh.transparentIndexCount = 0U;
''',
    'static empty shadow count')

c = replace_once(
    c,
'''    mesh.indexCount = static_cast<std::uint32_t>(pendingStaticIndices_.size());
    mesh.opaqueIndexCount = pendingStaticOpaqueIndexCount_;
''',
'''    mesh.indexCount = static_cast<std::uint32_t>(pendingStaticIndices_.size());
    mesh.shadowCasterIndexCount = pendingStaticShadowCasterIndexCount_;
    mesh.opaqueIndexCount = pendingStaticOpaqueIndexCount_;
''',
    'static upload shadow count')

c = replace_once(
    c,
'''    partitionMeshIndicesByTransmission(
        mesh,
        pendingDynamicIndices_,
        pendingDynamicOpaqueIndexCount_,
        pendingDynamicTransparentIndexCount_);
''',
'''    partitionMeshIndicesForRenderPasses(
        mesh,
        false,
        pendingDynamicIndices_,
        pendingDynamicShadowCasterIndexCount_,
        pendingDynamicOpaqueIndexCount_,
        pendingDynamicTransparentIndexCount_);
''',
    'dynamic render pass partition')

c = replace_once(
    c,
'''    pendingDynamicIndices_.clear();
    pendingDynamicOpaqueIndexCount_ = 0U;
''',
'''    pendingDynamicIndices_.clear();
    pendingDynamicShadowCasterIndexCount_ = 0U;
    pendingDynamicOpaqueIndexCount_ = 0U;
''',
    'dynamic clear shadow count')

# The static empty block was replaced above; now replace the remaining dynamic empty block.
c = replace_once(
    c,
'''        mesh.indexCount = 0U;
        mesh.opaqueIndexCount = 0U;
        mesh.transparentIndexCount = 0U;
        dynamicMeshGenerationByFrame_[frame] = dynamicMeshGeneration_;
''',
'''        mesh.indexCount = 0U;
        mesh.shadowCasterIndexCount = 0U;
        mesh.opaqueIndexCount = 0U;
        mesh.transparentIndexCount = 0U;
        dynamicMeshGenerationByFrame_[frame] = dynamicMeshGeneration_;
''',
    'dynamic empty shadow count')

c = replace_once(
    c,
'''    mesh.indexCount = static_cast<std::uint32_t>(pendingDynamicIndices_.size());
    mesh.opaqueIndexCount = pendingDynamicOpaqueIndexCount_;
''',
'''    mesh.indexCount = static_cast<std::uint32_t>(pendingDynamicIndices_.size());
    mesh.shadowCasterIndexCount = pendingDynamicShadowCasterIndexCount_;
    mesh.opaqueIndexCount = pendingDynamicOpaqueIndexCount_;
''',
    'dynamic upload shadow count')

c = replace_once(
    c,
'''    drawBoundMesh(
        command, staticMesh.vertexBuffer, staticMesh.indexBuffer, staticMesh.opaqueIndexCount, 0U);
''',
'''    // Local contact shadows are a small-caster problem. Terrain still receives the result in the
    // main pass, but only ecology/rocks/props are transformed and rasterized into this 250 m map.
    drawBoundMesh(
        command,
        staticMesh.vertexBuffer,
        staticMesh.indexBuffer,
        staticMesh.shadowCasterIndexCount,
        0U);
''',
    'static shadow draw range')

c = replace_once(
    c,
'''        drawBoundMesh(command, dynamic.vertexBuffer, dynamic.indexBuffer, dynamic.opaqueIndexCount, 0U);
''',
'''        drawBoundMesh(
            command,
            dynamic.vertexBuffer,
            dynamic.indexBuffer,
            dynamic.shadowCasterIndexCount,
            0U);
''',
    'dynamic shadow draw range')

HEADER.write_text(h, encoding='utf-8')
CPP.write_text(c, encoding='utf-8')

print('R24 LOCAL SHADOW CASTER PARTITION materialized')
print(' - static index order: local casters | opaque terrain receivers | transparent')
print(' - terrain remains visible and receives shadows but leaves the 250 m caster pass')
print(' - triangle material classification is performed once per mesh generation')
print(' - shadow pass submits only shadowCasterIndexCount')
