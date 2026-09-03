#include "vf/Engine.hpp"
#include "vf/Mesher.hpp"
#include "vf/Raycast.hpp"

#include <cstdint>
#include <span>

#if defined(__EMSCRIPTEN__)
#include <emscripten/emscripten.h>
#define VF_EXPORT EMSCRIPTEN_KEEPALIVE
#else
#define VF_EXPORT
#endif

namespace {
vf::MeshData g_mesh;
vf::RaycastHit g_hit;
}

extern "C" {

VF_EXPORT std::uint32_t vf_engine_abi_version() noexcept {
  return vf::kEngineAbiVersion;
}

VF_EXPORT std::int32_t vf_terrain_height(std::int32_t worldX, std::int32_t worldZ) noexcept {
  return vf::terrainHeight(worldX, worldZ);
}

VF_EXPORT std::int32_t vf_fill_chunk(
    std::uint8_t* output,
    std::int32_t outputLength,
    std::int32_t chunkX,
    std::int32_t chunkZ,
    std::int32_t width,
    std::int32_t height,
    std::int32_t depth) noexcept {
  if (output == nullptr || outputLength <= 0 || width <= 0 || height <= 0 || depth <= 0) return 0;

  const auto required = static_cast<std::int64_t>(width) * height * depth;
  if (required <= 0 || required > outputLength) return 0;

  const vf::ChunkSpec spec{chunkX, chunkZ, width, height, depth};
  vf::fillChunk(spec, std::span<std::uint8_t>(output, static_cast<std::size_t>(required)));
  return static_cast<std::int32_t>(required);
}

VF_EXPORT std::int32_t vf_build_greedy_mesh(
    const std::uint8_t* blocks,
    std::int32_t blockLength,
    std::int32_t width,
    std::int32_t height,
    std::int32_t depth) noexcept {
  if (blocks == nullptr || blockLength <= 0 || width <= 0 || height <= 0 || depth <= 0) return 0;
  const auto required = static_cast<std::int64_t>(width) * height * depth;
  if (required <= 0 || required > blockLength) return 0;

  g_mesh = vf::buildGreedyMesh(
      std::span<const std::uint8_t>(blocks, static_cast<std::size_t>(required)), width, height, depth);
  return static_cast<std::int32_t>(g_mesh.quadCount);
}

VF_EXPORT std::uint32_t vf_mesh_vertex_ptr() noexcept {
  return static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(g_mesh.vertices.data()));
}

VF_EXPORT std::int32_t vf_mesh_vertex_count() noexcept {
  return static_cast<std::int32_t>(g_mesh.vertices.size());
}

VF_EXPORT std::int32_t vf_mesh_vertex_stride() noexcept {
  return static_cast<std::int32_t>(sizeof(vf::MeshVertex));
}

VF_EXPORT std::uint32_t vf_mesh_index_ptr() noexcept {
  return static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(g_mesh.indices.data()));
}

VF_EXPORT std::int32_t vf_mesh_index_count() noexcept {
  return static_cast<std::int32_t>(g_mesh.indices.size());
}

VF_EXPORT std::int32_t vf_raycast(
    const std::uint8_t* blocks,
    std::int32_t blockLength,
    std::int32_t width,
    std::int32_t height,
    std::int32_t depth,
    float originX,
    float originY,
    float originZ,
    float directionX,
    float directionY,
    float directionZ,
    float maxDistance) noexcept {
  g_hit = {};
  if (blocks == nullptr || blockLength <= 0) return 0;
  const auto required = static_cast<std::int64_t>(width) * height * depth;
  if (required <= 0 || required > blockLength) return 0;

  g_hit = vf::raycastDda(
      std::span<const std::uint8_t>(blocks, static_cast<std::size_t>(required)),
      width,
      height,
      depth,
      originX,
      originY,
      originZ,
      directionX,
      directionY,
      directionZ,
      maxDistance);
  return g_hit.hit ? 1 : 0;
}

VF_EXPORT std::int32_t vf_hit_x() noexcept { return g_hit.x; }
VF_EXPORT std::int32_t vf_hit_y() noexcept { return g_hit.y; }
VF_EXPORT std::int32_t vf_hit_z() noexcept { return g_hit.z; }
VF_EXPORT std::int32_t vf_hit_normal_x() noexcept { return g_hit.normalX; }
VF_EXPORT std::int32_t vf_hit_normal_y() noexcept { return g_hit.normalY; }
VF_EXPORT std::int32_t vf_hit_normal_z() noexcept { return g_hit.normalZ; }
VF_EXPORT float vf_hit_distance() noexcept { return g_hit.distance; }
VF_EXPORT std::int32_t vf_hit_block() noexcept { return static_cast<std::int32_t>(g_hit.block); }

}  // extern "C"
