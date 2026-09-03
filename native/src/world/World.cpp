#include "vf/world/World.hpp"

#include <algorithm>
#include <cmath>

namespace vf {

namespace {

[[nodiscard]] std::uint64_t splitmix64(std::uint64_t value) noexcept {
    value += 0x9e3779b97f4a7c15ULL;
    value = (value ^ (value >> 30U)) * 0xbf58476d1ce4e5b9ULL;
    value = (value ^ (value >> 27U)) * 0x94d049bb133111ebULL;
    return value ^ (value >> 31U);
}

[[nodiscard]] float hash01(std::int32_t x, std::int32_t z, std::uint64_t seed) noexcept {
    const auto ux = static_cast<std::uint64_t>(static_cast<std::uint32_t>(x));
    const auto uz = static_cast<std::uint64_t>(static_cast<std::uint32_t>(z));
    const auto h = splitmix64(seed ^ (ux * 0x9e3779b185ebca87ULL) ^ (uz * 0xc2b2ae3d27d4eb4fULL));
    return static_cast<float>((h >> 40U) & 0xFFFFFFULL) / static_cast<float>(0xFFFFFFU);
}

} // namespace

World::World(std::uint64_t seed) noexcept : seed_(seed) {}

std::int32_t World::floorDiv(std::int32_t value, std::int32_t divisor) noexcept {
    const auto q = value / divisor;
    const auto r = value % divisor;
    return (r != 0 && ((r < 0) != (divisor < 0))) ? q - 1 : q;
}

std::int32_t World::positiveMod(std::int32_t value, std::int32_t divisor) noexcept {
    const auto m = value % divisor;
    return m < 0 ? m + divisor : m;
}

Chunk& World::ensureChunk(ChunkCoord coord) {
    if (auto* existing = findChunk(coord)) return *existing;
    auto chunk = generateChunk(coord);
    auto* raw = chunk.get();
    chunks_.emplace(coord, std::move(chunk));
    return *raw;
}

Chunk* World::findChunk(ChunkCoord coord) noexcept {
    const auto it = chunks_.find(coord);
    return it == chunks_.end() ? nullptr : it->second.get();
}

const Chunk* World::findChunk(ChunkCoord coord) const noexcept {
    const auto it = chunks_.find(coord);
    return it == chunks_.end() ? nullptr : it->second.get();
}

BlockId World::getBlock(std::int32_t worldX, std::int32_t worldY, std::int32_t worldZ) const noexcept {
    const ChunkCoord coord{
        floorDiv(worldX, kChunkEdge),
        floorDiv(worldY, kChunkEdge),
        floorDiv(worldZ, kChunkEdge),
    };
    const auto* chunk = findChunk(coord);
    if (!chunk) return static_cast<BlockId>(Block::Air);
    return chunk->get(
        positiveMod(worldX, kChunkEdge),
        positiveMod(worldY, kChunkEdge),
        positiveMod(worldZ, kChunkEdge));
}

void World::setBlock(std::int32_t worldX, std::int32_t worldY, std::int32_t worldZ, BlockId block) {
    const ChunkCoord coord{
        floorDiv(worldX, kChunkEdge),
        floorDiv(worldY, kChunkEdge),
        floorDiv(worldZ, kChunkEdge),
    };
    const auto localX = positiveMod(worldX, kChunkEdge);
    const auto localY = positiveMod(worldY, kChunkEdge);
    const auto localZ = positiveMod(worldZ, kChunkEdge);
    auto& chunk = ensureChunk(coord);
    chunk.set(localX, localY, localZ, block);
    markBoundaryNeighborsDirty(coord, localX, localY, localZ);
}

void World::warmup(std::int32_t horizontalRadius, std::int32_t minChunkY, std::int32_t maxChunkY) {
    horizontalRadius = std::max(horizontalRadius, 0);
    if (minChunkY > maxChunkY) std::swap(minChunkY, maxChunkY);

    for (std::int32_t cy = minChunkY; cy <= maxChunkY; ++cy) {
        for (std::int32_t cz = -horizontalRadius; cz <= horizontalRadius; ++cz) {
            for (std::int32_t cx = -horizontalRadius; cx <= horizontalRadius; ++cx) {
                (void)ensureChunk({cx, cy, cz});
            }
        }
    }
}

std::int32_t World::terrainHeight(std::int32_t worldX, std::int32_t worldZ) const noexcept {
    const float x = static_cast<float>(worldX);
    const float z = static_cast<float>(worldZ);
    const float broad = std::sin(x * 0.011F) * 15.0F + std::cos(z * 0.009F) * 12.0F;
    const float ridge = std::sin((x + z) * 0.0045F) * 18.0F + std::cos((x - z) * 0.006F) * 8.0F;
    const float detail = (hash01(worldX, worldZ, seed_) - 0.5F) * 4.0F;
    return static_cast<std::int32_t>(std::floor(54.0F + broad + ridge + detail));
}

std::unique_ptr<Chunk> World::generateChunk(ChunkCoord coord) const {
    auto chunk = std::make_unique<Chunk>(coord);
    const auto originX = coord.x * kChunkEdge;
    const auto originY = coord.y * kChunkEdge;
    const auto originZ = coord.z * kChunkEdge;

    for (std::int32_t z = 0; z < kChunkEdge; ++z) {
        for (std::int32_t x = 0; x < kChunkEdge; ++x) {
            const auto worldX = originX + x;
            const auto worldZ = originZ + z;
            const auto top = terrainHeight(worldX, worldZ);

            for (std::int32_t y = 0; y < kChunkEdge; ++y) {
                const auto worldY = originY + y;
                Block block = Block::Air;
                if (worldY <= top) {
                    block = Block::Stone;
                    if (worldY == top) block = Block::Grass;
                    else if (worldY >= top - 3) block = Block::Dirt;
                }
                chunk->blocks()[Chunk::index(x, y, z)] = static_cast<BlockId>(block);
            }
        }
    }

    chunk->markDirty();
    return chunk;
}

void World::markBoundaryNeighborsDirty(
    ChunkCoord owner,
    std::int32_t localX,
    std::int32_t localY,
    std::int32_t localZ) noexcept {
    const auto mark = [this](ChunkCoord coord) {
        if (auto* chunk = findChunk(coord)) chunk->markDirty();
    };

    if (localX == 0) mark({owner.x - 1, owner.y, owner.z});
    if (localX == kChunkEdge - 1) mark({owner.x + 1, owner.y, owner.z});
    if (localY == 0) mark({owner.x, owner.y - 1, owner.z});
    if (localY == kChunkEdge - 1) mark({owner.x, owner.y + 1, owner.z});
    if (localZ == 0) mark({owner.x, owner.y, owner.z - 1});
    if (localZ == kChunkEdge - 1) mark({owner.x, owner.y, owner.z + 1});
}

} // namespace vf
