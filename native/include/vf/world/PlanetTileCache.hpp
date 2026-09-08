#pragma once

#include "vf/world/PlanetSurface.hpp"

#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>
#include <unordered_map>

namespace vf {

// Stable cube-sphere tile identity. Integer quadtree coordinates avoid using floating-point UVs as
// cache keys. patchResolution is part of the identity because the same geographic tile may be
// requested at a different grid density after a quality-tier/altitude transition.
struct PlanetLodTileKey {
    std::uint32_t face{};
    std::uint32_t depth{};
    std::uint32_t x{};
    std::uint32_t y{};
    std::uint32_t patchResolution{};

    [[nodiscard]] bool operator==(const PlanetLodTileKey&) const noexcept = default;
};

struct PlanetTileCacheStats {
    std::uint64_t hits{};
    std::uint64_t misses{};
    std::uint64_t inserts{};
    std::uint64_t evictions{};
    std::size_t entries{};
    std::size_t residentBytes{};
    std::size_t maximumBytes{};
};

// CPU-side persistent terrain-tile cache. The renderer still owns GPU resources; this cache keeps
// immutable authoritative patch meshes so a camera turn or small recenter does not re-run plate,
// noise, hydrology, material and normal synthesis for tiles that were already generated.
//
// epoch is supplied by the caller and represents non-geographic authority state (currently the
// RegionalHydrology bake identity). When the hydrology window changes, old tiles remain harmlessly
// cached under the old epoch and are removed by the byte-budgeted LRU policy.
class PlanetTileCache final {
public:
    explicit PlanetTileCache(std::size_t maximumBytes = 384ULL * 1024ULL * 1024ULL) noexcept;

    PlanetTileCache(const PlanetTileCache&) = delete;
    PlanetTileCache& operator=(const PlanetTileCache&) = delete;

    [[nodiscard]] std::shared_ptr<const PlanetMesh> find(
        std::uint64_t epoch,
        const PlanetLodTileKey& key) noexcept;

    void insert(
        std::uint64_t epoch,
        const PlanetLodTileKey& key,
        std::shared_ptr<const PlanetMesh> mesh) noexcept;

    void setMaximumBytes(std::size_t maximumBytes) noexcept;
    void clear() noexcept;

    [[nodiscard]] PlanetTileCacheStats stats() const noexcept;

private:
    struct CacheKey {
        std::uint64_t epoch{};
        PlanetLodTileKey tile{};
        [[nodiscard]] bool operator==(const CacheKey&) const noexcept = default;
    };

    struct CacheKeyHash {
        [[nodiscard]] std::size_t operator()(const CacheKey& value) const noexcept;
    };

    struct Entry {
        std::shared_ptr<const PlanetMesh> mesh{};
        std::size_t bytes{};
        std::uint64_t lastUseSerial{};
    };

    [[nodiscard]] static std::size_t meshBytes(const PlanetMesh& mesh) noexcept;
    void trimLocked() noexcept;

    mutable std::mutex mutex_{};
    std::unordered_map<CacheKey, Entry, CacheKeyHash> entries_{};
    std::size_t residentBytes_{};
    std::size_t maximumBytes_{};
    std::uint64_t useSerial_{};
    std::uint64_t hits_{};
    std::uint64_t misses_{};
    std::uint64_t inserts_{};
    std::uint64_t evictions_{};
};

} // namespace vf
