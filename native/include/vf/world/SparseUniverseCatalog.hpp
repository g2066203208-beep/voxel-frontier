#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

#include <glm/glm.hpp>

namespace vf {

enum class CatalogObjectType : std::uint8_t {
    StarSystem,
    RoguePlanet,
    AsteroidField,
    Comet,
};

struct CatalogObjectRecord {
    std::uint64_t id{};
    std::uint64_t seed{};
    CatalogObjectType type{CatalogObjectType::StarSystem};
    glm::dvec3 positionMeters{};
    double proxyRadiusMeters{1000.0};
    double temperatureK{5772.0};
    glm::dvec3 displayColor{1.0};
    std::uint32_t childBodyCount{};
};

// Ultra-cheap universe layer. Far objects are only metadata + double-precision coordinates.
// Detailed terrain, collision, atmosphere and simulation are created by the runtime only after
// a record enters an activation radius. A few hundred records cost only a few tens of KiB.
class SparseUniverseCatalog final {
public:
    explicit SparseUniverseCatalog(
        std::uint64_t seed = 0x51A7E11AULL,
        std::size_t recordCount = 256U,
        double innerRadiusMeters = 350000.0,
        double outerRadiusMeters = 8000000.0);

    [[nodiscard]] std::span<const CatalogObjectRecord> records() const noexcept { return records_; }
    [[nodiscard]] const CatalogObjectRecord* record(std::uint64_t id) const noexcept;

    [[nodiscard]] std::vector<const CatalogObjectRecord*> nearestVisible(
        const glm::dvec3& observer,
        std::size_t maxCount) const;

    [[nodiscard]] std::vector<const CatalogObjectRecord*> activeWithin(
        const glm::dvec3& observer,
        double activationRadiusMeters) const;

    [[nodiscard]] std::size_t approximateMemoryBytes() const noexcept {
        return sizeof(*this) + records_.capacity() * sizeof(CatalogObjectRecord);
    }

private:
    std::vector<CatalogObjectRecord> records_;
};

} // namespace vf
