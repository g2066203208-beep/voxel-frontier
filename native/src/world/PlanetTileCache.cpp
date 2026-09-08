#include "vf/world/PlanetTileCache.hpp"

#include <algorithm>
#include <limits>

namespace vf {
namespace {

[[nodiscard]] std::size_t mixHash(std::size_t seed, std::size_t value) noexcept {
    // 64-bit hash-combine constant; truncation on 32-bit platforms remains deterministic.
    return seed ^ (value + static_cast<std::size_t>(0x9E3779B97F4A7C15ULL)
        + (seed << 6U) + (seed >> 2U));
}

} // namespace

PlanetTileCache::PlanetTileCache(std::size_t maximumBytes) noexcept
    : maximumBytes_(std::max<std::size_t>(maximumBytes, 1U)) {}

std::size_t PlanetTileCache::CacheKeyHash::operator()(const CacheKey& value) const noexcept {
    std::size_t hash = std::hash<std::uint64_t>{}(value.epoch);
    hash = mixHash(hash, std::hash<std::uint32_t>{}(value.tile.face));
    hash = mixHash(hash, std::hash<std::uint32_t>{}(value.tile.depth));
    hash = mixHash(hash, std::hash<std::uint32_t>{}(value.tile.x));
    hash = mixHash(hash, std::hash<std::uint32_t>{}(value.tile.y));
    hash = mixHash(hash, std::hash<std::uint32_t>{}(value.tile.patchResolution));
    return hash;
}

std::size_t PlanetTileCache::meshBytes(const PlanetMesh& mesh) noexcept {
    return mesh.vertices.size() * sizeof(PlanetVertex)
        + mesh.indices.size() * sizeof(std::uint32_t);
}

std::shared_ptr<const PlanetMesh> PlanetTileCache::find(
    std::uint64_t epoch,
    const PlanetLodTileKey& key) noexcept {
    std::scoped_lock lock{mutex_};
    const CacheKey cacheKey{epoch, key};
    const auto it = entries_.find(cacheKey);
    if (it == entries_.end()) {
        ++misses_;
        return {};
    }
    ++hits_;
    it->second.lastUseSerial = ++useSerial_;
    return it->second.mesh;
}

void PlanetTileCache::insert(
    std::uint64_t epoch,
    const PlanetLodTileKey& key,
    std::shared_ptr<const PlanetMesh> mesh) noexcept {
    if (!mesh) return;
    const std::size_t bytes = meshBytes(*mesh);
    std::scoped_lock lock{mutex_};
    const CacheKey cacheKey{epoch, key};
    const auto existing = entries_.find(cacheKey);
    if (existing != entries_.end()) {
        residentBytes_ -= std::min(residentBytes_, existing->second.bytes);
        existing->second = {std::move(mesh), bytes, ++useSerial_};
    } else {
        entries_.emplace(cacheKey, Entry{std::move(mesh), bytes, ++useSerial_});
        ++inserts_;
    }
    residentBytes_ += bytes;
    trimLocked();
}

void PlanetTileCache::setMaximumBytes(std::size_t maximumBytes) noexcept {
    std::scoped_lock lock{mutex_};
    maximumBytes_ = std::max<std::size_t>(maximumBytes, 1U);
    trimLocked();
}

void PlanetTileCache::clear() noexcept {
    std::scoped_lock lock{mutex_};
    entries_.clear();
    residentBytes_ = 0U;
}

PlanetTileCacheStats PlanetTileCache::stats() const noexcept {
    std::scoped_lock lock{mutex_};
    return {
        hits_,
        misses_,
        inserts_,
        evictions_,
        entries_.size(),
        residentBytes_,
        maximumBytes_,
    };
}

void PlanetTileCache::trimLocked() noexcept {
    while (residentBytes_ > maximumBytes_ && entries_.size() > 1U) {
        auto victim = entries_.end();
        std::uint64_t oldest = std::numeric_limits<std::uint64_t>::max();
        for (auto it = entries_.begin(); it != entries_.end(); ++it) {
            if (it->second.lastUseSerial < oldest) {
                oldest = it->second.lastUseSerial;
                victim = it;
            }
        }
        if (victim == entries_.end()) break;
        residentBytes_ -= std::min(residentBytes_, victim->second.bytes);
        entries_.erase(victim);
        ++evictions_;
    }
}

} // namespace vf
