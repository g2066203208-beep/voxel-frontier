#pragma once

#include <cstdint>
#include <span>
#include <vector>

namespace vf {

struct MeshVertex {
  float x{};
  float y{};
  float z{};
  std::uint32_t packed{};
};

static_assert(sizeof(MeshVertex) == 16);

struct MeshData {
  std::vector<MeshVertex> vertices;
  std::vector<std::uint32_t> indices;
  std::uint32_t quadCount{};

  void clear() {
    vertices.clear();
    indices.clear();
    quadCount = 0;
  }
};

[[nodiscard]] MeshData buildGreedyMesh(
    std::span<const std::uint8_t> blocks,
    std::int32_t width,
    std::int32_t height,
    std::int32_t depth);

}  // namespace vf
