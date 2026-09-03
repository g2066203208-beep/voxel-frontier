#pragma once

#include "vf/world/Chunk.hpp"

#include <cstdint>
#include <memory>
#include <unordered_map>

namespace vf {

class World final {
public:
    explicit World(std::uint64_t seed = 0x564f58454c46524fULL) noexcept;

    [[nodiscard]] Chunk& ensureChunk(ChunkCoord coord);
    [[nodiscard]] Chunk* findChunk(ChunkCoord coord) noexcept;
    [[nodiscard]] const Chunk* findChunk(ChunkCoord coord) const noexcept;

    [[nodiscard]] BlockId getBlock(std::int32_t worldX, std::int32_t worldY, std::int32_t worldZ) const noexcept;
    void setBlock(std::int32_t worldX, std::int32_t worldY, std::int32_t worldZ, BlockId block);

    void warmup(std::int32_t horizontalRadius, std::int32_t minChunkY, std::int32_t maxChunkY);

    [[nodiscard]] std::size_t loadedChunkCount() const noexcept { return chunks_.size(); }
    [[nodiscard]] std::uint64_t seed() const noexcept { return seed_; }

    [[nodiscard]] static std::int32_t floorDiv(std::int32_t value, std::int32_t divisor) noexcept;
    [[nodiscard]] static std::int32_t positiveMod(std::int32_t value, std::int32_t divisor) noexcept;

private:
    [[nodiscard]] std::unique_ptr<Chunk> generateChunk(ChunkCoord coord) const;
    [[nodiscard]] std::int32_t terrainHeight(std::int32_t worldX, std::int32_t worldZ) const noexcept;
    void markBoundaryNeighborsDirty(ChunkCoord owner, std::int32_t localX, std::int32_t localY, std::int32_t localZ) noexcept;

    std::uint64_t seed_{};
    std::unordered_map<ChunkCoord, std::unique_ptr<Chunk>, ChunkCoordHash> chunks_;
};

} // namespace vf
