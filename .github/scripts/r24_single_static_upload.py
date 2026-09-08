#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HPP = ROOT / "native/include/vf/render/VulkanRenderer.hpp"
CPP = ROOT / "native/src/render/VulkanRenderer.cpp"
MAIN = ROOT / "native/src/app/Main.cpp"
CMAKE = ROOT / "native/CMakeLists.txt"


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: {label}: expected one anchor, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    HPP,
    '#include "vf/world/PlanetSurface.hpp"\n',
    '#include "vf/world/PlanetSurface.hpp"\n#include "vf/render/StaticMeshUploadScheduler.hpp"\n',
    "include static upload scheduler",
)

replace_once(
    HPP,
    '''    [[nodiscard]] std::uint64_t dynamicTriangleCount() const noexcept {
        return static_cast<std::uint64_t>(pendingDynamicIndices_.size() / 3U);
    }
''',
    '''    [[nodiscard]] std::uint64_t dynamicTriangleCount() const noexcept {
        return static_cast<std::uint64_t>(pendingDynamicIndices_.size() / 3U);
    }
    [[nodiscard]] std::uint64_t staticUploadCount() const noexcept {
        return staticUploadScheduler_.uploadCount();
    }
    [[nodiscard]] std::uint64_t staticUploadBytesTotal() const noexcept {
        return staticUploadBytesTotal_;
    }
''',
    "expose static upload telemetry",
)

replace_once(
    HPP,
    '''    std::shared_ptr<const PreparedPlanetMesh> pendingStaticMesh_{};
    std::uint64_t staticMeshGeneration_{};
    std::array<std::uint64_t, kFramesInFlight> staticMeshGenerationByFrame_{};
    std::array<FrameMesh, kFramesInFlight> staticMeshes_{};
''',
    '''    std::shared_ptr<const PreparedPlanetMesh> pendingStaticMesh_{};
    std::uint64_t staticMeshGeneration_{};
    StaticMeshUploadScheduler staticUploadScheduler_{};
    std::uint64_t staticUploadBytesTotal_{};
    std::array<FrameMesh, kFramesInFlight> staticMeshes_{};
''',
    "replace per-frame static generations with shared resident generation",
)

replace_once(
    CPP,
    '''    ++staticMeshGeneration_;
    if (staticMeshGeneration_ == 0U) {
        staticMeshGeneration_ = 1U;
        staticMeshGenerationByFrame_.fill(0U);
    }
}

void VulkanRenderer::uploadStaticMeshForFrame(std::uint32_t frame) {
    if (staticMeshGenerationByFrame_[frame] == staticMeshGeneration_) return;
    auto& mesh = staticMeshes_[frame];
    const std::shared_ptr<const PreparedPlanetMesh> pending = pendingStaticMesh_;
    if (!pending || pending->vertices.empty() || pending->indices.empty()) {
        mesh.indexCount = 0U;
        mesh.shadowCasterIndexCount = 0U;
        mesh.opaqueIndexCount = 0U;
        mesh.transparentIndexCount = 0U;
        staticMeshGenerationByFrame_[frame] = staticMeshGeneration_;
        return;
    }

    const VkDeviceSize vertexBytes = static_cast<VkDeviceSize>(
        pending->vertices.size() * sizeof(PlanetVertex));
    const VkDeviceSize indexBytes = static_cast<VkDeviceSize>(
        pending->indices.size() * sizeof(std::uint32_t));
    ensureStaticFrameCapacity(mesh, vertexBytes, indexBytes);
    std::memcpy(
        mesh.mappedUploadVertices, pending->vertices.data(), static_cast<std::size_t>(vertexBytes));
    std::memcpy(
        mesh.mappedUploadIndices, pending->indices.data(), static_cast<std::size_t>(indexBytes));
    mesh.uploadPending = true;
    mesh.indexCount = static_cast<std::uint32_t>(pending->indices.size());
    mesh.shadowCasterIndexCount = pending->shadowCasterIndexCount;
    mesh.opaqueIndexCount = pending->opaqueIndexCount;
    mesh.transparentIndexCount = pending->transparentIndexCount;
    staticMeshGenerationByFrame_[frame] = staticMeshGeneration_;
}
''',
    '''    ++staticMeshGeneration_;
    if (staticMeshGeneration_ == 0U) {
        staticMeshGeneration_ = 1U;
        staticUploadScheduler_.reset();
    }
}

void VulkanRenderer::uploadStaticMeshForFrame(std::uint32_t frame) {
    (void)frame;
    const StaticMeshUploadDecision decision = staticUploadScheduler_.adopt(staticMeshGeneration_);
    if (!decision.upload) return;

    auto& mesh = staticMeshes_[decision.slot];
    const std::shared_ptr<const PreparedPlanetMesh> pending = pendingStaticMesh_;
    if (!pending || pending->vertices.empty() || pending->indices.empty()) {
        mesh.indexCount = 0U;
        mesh.shadowCasterIndexCount = 0U;
        mesh.opaqueIndexCount = 0U;
        mesh.transparentIndexCount = 0U;
        return;
    }

    const VkDeviceSize vertexBytes = static_cast<VkDeviceSize>(
        pending->vertices.size() * sizeof(PlanetVertex));
    const VkDeviceSize indexBytes = static_cast<VkDeviceSize>(
        pending->indices.size() * sizeof(std::uint32_t));
    ensureStaticFrameCapacity(mesh, vertexBytes, indexBytes);
    std::memcpy(
        mesh.mappedUploadVertices, pending->vertices.data(), static_cast<std::size_t>(vertexBytes));
    std::memcpy(
        mesh.mappedUploadIndices, pending->indices.data(), static_cast<std::size_t>(indexBytes));
    mesh.uploadPending = true;
    mesh.indexCount = static_cast<std::uint32_t>(pending->indices.size());
    mesh.shadowCasterIndexCount = pending->shadowCasterIndexCount;
    mesh.opaqueIndexCount = pending->opaqueIndexCount;
    mesh.transparentIndexCount = pending->transparentIndexCount;
    staticUploadBytesTotal_ += static_cast<std::uint64_t>(vertexBytes + indexBytes);
    SDL_Log(
        "R24 PERF static_upload generation=%llu slot=%u bytes=%llu uploads=%llu",
        static_cast<unsigned long long>(staticMeshGeneration_),
        decision.slot,
        static_cast<unsigned long long>(vertexBytes + indexBytes),
        static_cast<unsigned long long>(staticUploadScheduler_.uploadCount()));
}
''',
    "single static staging and GPU transfer per generation",
)

replace_once(
    CPP,
    '''    // The frame fence is the ownership gate for both static and dynamic mapped buffers. Static
    // terrain updates are therefore incremental across the two frames in flight, with no global
    // GPU idle and no use-after-free risk.
    uploadStaticMeshForFrame(frame);
    uploadDynamicMeshForFrame(frame);
    auto& staticMesh = staticMeshes_[frame];
    const auto& dynamic = dynamicMeshes_[frame];
''',
    '''    // Static terrain is immutable once uploaded. A generation transfers once into an alternating
    // DEVICE_LOCAL slot and both in-flight frames share that resident slot read-only. The current
    // frame fence plus single-queue submission order make slot reuse safe without vkDeviceWaitIdle.
    uploadStaticMeshForFrame(frame);
    uploadDynamicMeshForFrame(frame);
    auto& staticMesh = staticMeshes_[staticUploadScheduler_.residentSlot()];
    const auto& dynamic = dynamicMeshes_[frame];
''',
    "draw from shared resident static generation",
)

# Add the upload telemetry to the exact benchmark output so CI can prove a stationary generation is
# transferred once instead of once per frame-in-flight.
replace_once(
    MAIN,
    '''                    6U,
                    16U) << '\\n';
                break;
''',
    '''                    6U,
                    16U) << '\\n';
                std::cout << "R24 BENCHMARK_GPU_STREAM static_uploads="
                          << renderer.staticUploadCount()
                          << " static_upload_bytes=" << renderer.staticUploadBytesTotal()
                          << '\\n';
                break;
''',
    "report static upload count in benchmark",
)

replace_once(
    CMAKE,
    '''    if(VF_BUILD_RUNTIME)
        add_executable(vf_shader_contract_tests tests/ShaderContractTests.cpp "${VF_SHADER_HEADER}")
''',
    '''    add_executable(vf_static_mesh_upload_scheduler_tests tests/StaticMeshUploadSchedulerTests.cpp)
    target_link_libraries(vf_static_mesh_upload_scheduler_tests PRIVATE vf_engine)
    add_test(NAME vf_static_mesh_upload_scheduler_tests COMMAND vf_static_mesh_upload_scheduler_tests)

    if(VF_BUILD_RUNTIME)
        add_executable(vf_shader_contract_tests tests/ShaderContractTests.cpp "${VF_SHADER_HEADER}")
''',
    "register static upload scheduler test",
)

print("R24 single static upload materialized")
