#pragma once

#include <cstdint>
#include <span>

namespace vf {

constexpr std::uint32_t kEngineAbiVersion = 1;

enum class Block : std::uint8_t {
  Air = 0,
  Stone = 1,
  Dirt = 2,
  Grass = 3,
  Wood = 4,
  Leaves = 5,
};

struct ChunkSpec {
  std::int32_t chunkX{};
  std::int32_t chunkZ{};
  std::int32_t width{16};
  std::int32_t height{64};
  std::int32_t depth{16};
};

[[nodiscard]] std::int32_t terrainHeight(std::int32_t worldX, std::int32_t worldZ) noexcept;

void fillChunk(const ChunkSpec& spec, std::span<std::uint8_t> output) noexcept;

}  // namespace vf
