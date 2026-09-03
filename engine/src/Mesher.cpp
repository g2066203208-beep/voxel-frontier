#include "vf/Mesher.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

namespace vf {
namespace {

struct MaskCell {
  std::uint8_t block{};
  bool positive{};

  friend bool operator==(const MaskCell&, const MaskCell&) = default;
};

[[nodiscard]] std::size_t index3D(
    std::int32_t x,
    std::int32_t y,
    std::int32_t z,
    const std::array<std::int32_t, 3>& dims) noexcept {
  return static_cast<std::size_t>((y * dims[2] + z) * dims[0] + x);
}

[[nodiscard]] std::uint8_t sample(
    std::span<const std::uint8_t> blocks,
    const std::array<std::int32_t, 3>& dims,
    const std::array<std::int32_t, 3>& p) noexcept {
  if (p[0] < 0 || p[1] < 0 || p[2] < 0 ||
      p[0] >= dims[0] || p[1] >= dims[1] || p[2] >= dims[2]) {
    return 0;
  }
  return blocks[index3D(p[0], p[1], p[2], dims)];
}

[[nodiscard]] std::uint32_t packVertex(std::uint8_t block, std::uint32_t normalIndex) noexcept {
  return static_cast<std::uint32_t>(block) | (normalIndex << 8U);
}

void emitQuad(
    MeshData& mesh,
    const std::array<std::int32_t, 3>& p,
    const std::array<std::int32_t, 3>& du,
    const std::array<std::int32_t, 3>& dv,
    std::uint8_t block,
    bool positive,
    std::int32_t axis) {
  const auto base = static_cast<std::uint32_t>(mesh.vertices.size());
  const auto normalIndex = static_cast<std::uint32_t>(axis * 2 + (positive ? 1 : 0));
  const auto packed = packVertex(block, normalIndex);

  const auto addVertex = [&](std::int32_t ox, std::int32_t oy, std::int32_t oz) {
    mesh.vertices.push_back(MeshVertex{
        static_cast<float>(p[0] + ox),
        static_cast<float>(p[1] + oy),
        static_cast<float>(p[2] + oz),
        packed});
  };

  addVertex(0, 0, 0);
  addVertex(du[0], du[1], du[2]);
  addVertex(du[0] + dv[0], du[1] + dv[1], du[2] + dv[2]);
  addVertex(dv[0], dv[1], dv[2]);

  if (positive) {
    mesh.indices.insert(mesh.indices.end(), {base, base + 1, base + 2, base, base + 2, base + 3});
  } else {
    mesh.indices.insert(mesh.indices.end(), {base, base + 3, base + 2, base, base + 2, base + 1});
  }
  ++mesh.quadCount;
}

}  // namespace

MeshData buildGreedyMesh(
    std::span<const std::uint8_t> blocks,
    std::int32_t width,
    std::int32_t height,
    std::int32_t depth) {
  MeshData mesh;
  const std::array<std::int32_t, 3> dims{width, height, depth};
  if (width <= 0 || height <= 0 || depth <= 0) return mesh;

  const auto required = static_cast<std::size_t>(width) * height * depth;
  if (blocks.size() < required) return mesh;

  const auto maxSlice = static_cast<std::size_t>(
      std::max({width * height, width * depth, height * depth}));
  std::vector<MaskCell> mask(maxSlice);

  for (std::int32_t d = 0; d < 3; ++d) {
    const std::int32_t u = (d + 1) % 3;
    const std::int32_t v = (d + 2) % 3;
    std::array<std::int32_t, 3> x{0, 0, 0};
    std::array<std::int32_t, 3> q{0, 0, 0};
    q[d] = 1;

    for (x[d] = -1; x[d] < dims[d];) {
      std::size_t n = 0;
      for (x[v] = 0; x[v] < dims[v]; ++x[v]) {
        for (x[u] = 0; x[u] < dims[u]; ++x[u]) {
          const auto a = sample(blocks, dims, x);
          std::array<std::int32_t, 3> bPos{x[0] + q[0], x[1] + q[1], x[2] + q[2]};
          const auto b = sample(blocks, dims, bPos);

          if ((a != 0) == (b != 0)) {
            mask[n++] = {};
          } else if (a != 0) {
            mask[n++] = MaskCell{a, true};
          } else {
            mask[n++] = MaskCell{b, false};
          }
        }
      }

      ++x[d];
      n = 0;
      for (std::int32_t j = 0; j < dims[v]; ++j) {
        for (std::int32_t i = 0; i < dims[u];) {
          const auto cell = mask[n];
          if (cell.block == 0) {
            ++i;
            ++n;
            continue;
          }

          std::int32_t quadWidth = 1;
          while (i + quadWidth < dims[u] && mask[n + quadWidth] == cell) ++quadWidth;

          std::int32_t quadHeight = 1;
          bool done = false;
          while (j + quadHeight < dims[v] && !done) {
            const auto row = n + static_cast<std::size_t>(quadHeight * dims[u]);
            for (std::int32_t k = 0; k < quadWidth; ++k) {
              if (!(mask[row + k] == cell)) {
                done = true;
                break;
              }
            }
            if (!done) ++quadHeight;
          }

          x[u] = i;
          x[v] = j;
          std::array<std::int32_t, 3> du{0, 0, 0};
          std::array<std::int32_t, 3> dv{0, 0, 0};
          du[u] = quadWidth;
          dv[v] = quadHeight;
          emitQuad(mesh, x, du, dv, cell.block, cell.positive, d);

          for (std::int32_t h = 0; h < quadHeight; ++h) {
            const auto row = n + static_cast<std::size_t>(h * dims[u]);
            for (std::int32_t k = 0; k < quadWidth; ++k) mask[row + k] = {};
          }

          i += quadWidth;
          n += static_cast<std::size_t>(quadWidth);
        }
      }
    }
  }

  return mesh;
}

}  // namespace vf
