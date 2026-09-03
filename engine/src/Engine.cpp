#include "vf/Engine.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>

namespace vf {
namespace {

[[nodiscard]] float hash2(std::int32_t x, std::int32_t z) noexcept {
  const float n = std::sin(static_cast<float>(x) * 127.1F + static_cast<float>(z) * 311.7F) * 43758.5453123F;
  return n - std::floor(n);
}

[[nodiscard]] std::size_t index3D(
    std::int32_t x,
    std::int32_t y,
    std::int32_t z,
    std::int32_t width,
    std::int32_t depth) noexcept {
  return static_cast<std::size_t>((y * depth + z) * width + x);
}

}  // namespace

std::int32_t terrainHeight(std::int32_t worldX, std::int32_t worldZ) noexcept {
  const float x = static_cast<float>(worldX);
  const float z = static_cast<float>(worldZ);
  const float broad = std::sin(x * 0.19F) * 1.7F + std::cos(z * 0.16F) * 1.45F;
  const float ridge = std::sin((x + z) * 0.085F) * 1.2F + std::cos((x - z) * 0.11F) * 0.8F;
  const float detail = (hash2(worldX, worldZ) - 0.5F) * 0.35F;
  return static_cast<std::int32_t>(std::floor(8.0F + broad + ridge + detail));
}

void fillChunk(const ChunkSpec& spec, std::span<std::uint8_t> output) noexcept {
  const auto expected = static_cast<std::size_t>(spec.width) *
                        static_cast<std::size_t>(spec.height) *
                        static_cast<std::size_t>(spec.depth);
  if (output.size() < expected || spec.width <= 0 || spec.height <= 0 || spec.depth <= 0) return;

  std::fill_n(output.begin(), expected, static_cast<std::uint8_t>(Block::Air));

  const std::int32_t originX = spec.chunkX * spec.width;
  const std::int32_t originZ = spec.chunkZ * spec.depth;

  for (std::int32_t z = 0; z < spec.depth; ++z) {
    for (std::int32_t x = 0; x < spec.width; ++x) {
      const std::int32_t worldX = originX + x;
      const std::int32_t worldZ = originZ + z;
      const std::int32_t top = std::clamp(terrainHeight(worldX, worldZ), 1, spec.height - 1);

      for (std::int32_t y = 0; y <= top; ++y) {
        Block block = Block::Stone;
        if (y == top) block = Block::Grass;
        else if (y >= top - 2) block = Block::Dirt;
        output[index3D(x, y, z, spec.width, spec.depth)] = static_cast<std::uint8_t>(block);
      }
    }
  }
}

}  // namespace vf
