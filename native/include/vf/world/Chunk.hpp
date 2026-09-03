#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace vf {

using BlockId = std::uint16_t;

constexpr std::int32_t kChunkEdge = 32;
constexpr std::size_t kChunkVolume =
    static_cast<std::size_t>(kChunkEdge) * kChunkEdge * kChunkEdge;

enum class Block : BlockId {
    Air = 0,
    Stone = 1,
    Dirt = 2,
    Grass = 3,
    Wood = 4,
    Leaves = 5,
};

struct ChunkCoord {
    std::int32_t x{};
    std::int32_t y{};
    std::int32_t z{};

    friend bool operator==(const ChunkCoord&, const ChunkCoord&) = default;
};

struct ChunkCoordHash {
    [[nodiscard]] std::size_t operator()(const ChunkCoord& coord) const noexcept;
};

class Chunk final {
public:
    explicit Chunk(ChunkCoord coord) noexcept;

    [[nodiscard]] ChunkCoord coord() const noexcept { return coord_; }
    [[nodiscard]] BlockId get(std::int32_t x, std::int32_t y, std::int32_t z) const noexcept;
    void set(std::int32_t x, std::int32_t y, std::int32_t z, BlockId block) noexcept;

    [[nodiscard]] const std::array<BlockId, kChunkVolume>& blocks() const noexcept { return blocks_; }
    [[nodiscard]] std::array<BlockId, kChunkVolume>& blocks() noexcept { return blocks_; }

    [[nodiscard]] bool dirty() const noexcept { return dirty_; }
    void markDirty() noexcept { dirty_ = true; }
    void clearDirty() noexcept { dirty_ = false; }

    [[nodiscard]] static constexpr bool validLocal(
        std::int32_t x,
        std::int32_t y,
        std::int32_t z) noexcept {
        return x >= 0 && x < kChunkEdge &&
               y >= 0 && y < kChunkEdge &&
               z >= 0 && z < kChunkEdge;
    }

    [[nodiscard]] static constexpr std::size_t index(
        std::int32_t x,
        std::int32_t y,
        std::int32_t z) noexcept {
        return static_cast<std::size_t>((y * kChunkEdge + z) * kChunkEdge + x);
    }

private:
    ChunkCoord coord_{};
    std::array<BlockId, kChunkVolume> blocks_{};
    bool dirty_{true};
};

} // namespace vf
