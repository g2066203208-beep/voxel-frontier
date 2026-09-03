#include "vf/world/Chunk.hpp"

namespace vf {

namespace {

[[nodiscard]] constexpr std::uint64_t mix64(std::uint64_t value) noexcept {
    value ^= value >> 30U;
    value *= 0xbf58476d1ce4e5b9ULL;
    value ^= value >> 27U;
    value *= 0x94d049bb133111ebULL;
    value ^= value >> 31U;
    return value;
}

} // namespace

std::size_t ChunkCoordHash::operator()(const ChunkCoord& coord) const noexcept {
    const auto x = mix64(static_cast<std::uint64_t>(static_cast<std::uint32_t>(coord.x)));
    const auto y = mix64(static_cast<std::uint64_t>(static_cast<std::uint32_t>(coord.y)) + 0x9e3779b97f4a7c15ULL);
    const auto z = mix64(static_cast<std::uint64_t>(static_cast<std::uint32_t>(coord.z)) + 0x243f6a8885a308d3ULL);
    return static_cast<std::size_t>(x ^ (y << 1U) ^ (z << 7U));
}

Chunk::Chunk(ChunkCoord coord) noexcept : coord_(coord) {
    blocks_.fill(static_cast<BlockId>(Block::Air));
}

BlockId Chunk::get(std::int32_t x, std::int32_t y, std::int32_t z) const noexcept {
    if (!validLocal(x, y, z)) return static_cast<BlockId>(Block::Air);
    return blocks_[index(x, y, z)];
}

void Chunk::set(std::int32_t x, std::int32_t y, std::int32_t z, BlockId block) noexcept {
    if (!validLocal(x, y, z)) return;
    const auto i = index(x, y, z);
    if (blocks_[i] == block) return;
    blocks_[i] = block;
    dirty_ = true;
}

} // namespace vf
