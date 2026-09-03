#include "vf/world/SparseUniverseCatalog.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

#include <glm/geometric.hpp>

namespace vf {
namespace {

[[nodiscard]] std::uint64_t mix64(std::uint64_t x) noexcept {
    x += 0x9E3779B97F4A7C15ULL;
    x = (x ^ (x >> 30U)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27U)) * 0x94D049BB133111EBULL;
    return x ^ (x >> 31U);
}

[[nodiscard]] double unit01(std::uint64_t value) noexcept {
    return static_cast<double>(value >> 11U) * (1.0 / 9007199254740992.0);
}

[[nodiscard]] glm::dvec3 starColor(double temperatureK) noexcept {
    // Very cheap blackbody-display approximation. SpectralOptics provides the accurate six-band
    // path for active stars; far catalog dots only need a stable cool/red -> hot/blue cue.
    const double t = std::clamp((temperatureK - 2200.0) / (12000.0 - 2200.0), 0.0, 1.0);
    const glm::dvec3 cool{1.0, 0.48, 0.22};
    const glm::dvec3 warm{1.0, 0.92, 0.72};
    const glm::dvec3 hot{0.62, 0.78, 1.0};
    if (t < 0.55) return glm::mix(cool, warm, t / 0.55);
    return glm::mix(warm, hot, (t - 0.55) / 0.45);
}

} // namespace

SparseUniverseCatalog::SparseUniverseCatalog(
    std::uint64_t seed,
    std::size_t recordCount,
    double innerRadiusMeters,
    double outerRadiusMeters) {
    innerRadiusMeters = std::max(1000.0, innerRadiusMeters);
    outerRadiusMeters = std::max(innerRadiusMeters + 1000.0, outerRadiusMeters);
    recordCount = std::min<std::size_t>(recordCount, 8192U);
    records_.reserve(recordCount);

    const double inner3 = innerRadiusMeters * innerRadiusMeters * innerRadiusMeters;
    const double outer3 = outerRadiusMeters * outerRadiusMeters * outerRadiusMeters;

    for (std::size_t index = 0; index < recordCount; ++index) {
        const std::uint64_t base = mix64(seed ^ (static_cast<std::uint64_t>(index) * 0xD1B54A32D192ED03ULL));
        const double u0 = unit01(mix64(base + 1U));
        const double u1 = unit01(mix64(base + 2U));
        const double u2 = unit01(mix64(base + 3U));
        const double u3 = unit01(mix64(base + 4U));
        const double u4 = unit01(mix64(base + 5U));

        const double z = 2.0 * u0 - 1.0;
        const double azimuth = 6.28318530717958647692 * u1;
        const double radial = std::sqrt(std::max(0.0, 1.0 - z * z));
        const glm::dvec3 direction{radial * std::cos(azimuth), z, radial * std::sin(azimuth)};
        const double distance = std::cbrt(inner3 + u2 * (outer3 - inner3));

        CatalogObjectRecord record{};
        record.id = static_cast<std::uint64_t>(index) + 1U;
        record.seed = mix64(base + 9U);
        record.positionMeters = direction * distance;

        if (u3 < 0.72) {
            record.type = CatalogObjectType::StarSystem;
            record.temperatureK = 2400.0 + 9000.0 * u4;
            record.proxyRadiusMeters = 2400.0 + 8500.0 * unit01(mix64(base + 6U));
            record.displayColor = starColor(record.temperatureK);
            record.childBodyCount = 1U + static_cast<std::uint32_t>(mix64(base + 7U) % 9U);
        } else if (u3 < 0.84) {
            record.type = CatalogObjectType::RoguePlanet;
            record.temperatureK = 35.0 + 180.0 * u4;
            record.proxyRadiusMeters = 1200.0 + 8000.0 * unit01(mix64(base + 6U));
            record.displayColor = {0.32, 0.40, 0.48};
            record.childBodyCount = static_cast<std::uint32_t>(mix64(base + 7U) % 3U);
        } else if (u3 < 0.96) {
            record.type = CatalogObjectType::AsteroidField;
            record.temperatureK = 80.0 + 160.0 * u4;
            record.proxyRadiusMeters = 6000.0 + 28000.0 * unit01(mix64(base + 6U));
            record.displayColor = {0.46, 0.43, 0.40};
            record.childBodyCount = 32U + static_cast<std::uint32_t>(mix64(base + 7U) % 225U);
        } else {
            record.type = CatalogObjectType::Comet;
            record.temperatureK = 45.0 + 90.0 * u4;
            record.proxyRadiusMeters = 80.0 + 900.0 * unit01(mix64(base + 6U));
            record.displayColor = {0.72, 0.86, 1.0};
            record.childBodyCount = 1U;
        }

        records_.push_back(record);
    }
}

const CatalogObjectRecord* SparseUniverseCatalog::record(std::uint64_t id) const noexcept {
    if (id == 0U || id > records_.size()) return nullptr;
    return &records_[static_cast<std::size_t>(id - 1U)];
}

std::vector<const CatalogObjectRecord*> SparseUniverseCatalog::nearestVisible(
    const glm::dvec3& observer,
    std::size_t maxCount) const {
    maxCount = std::min(maxCount, records_.size());
    std::vector<const CatalogObjectRecord*> result;
    result.reserve(records_.size());
    for (const auto& recordValue : records_) result.push_back(&recordValue);

    std::partial_sort(
        result.begin(),
        result.begin() + static_cast<std::ptrdiff_t>(maxCount),
        result.end(),
        [&observer](const CatalogObjectRecord* a, const CatalogObjectRecord* b) {
            const glm::dvec3 da = a->positionMeters - observer;
            const glm::dvec3 db = b->positionMeters - observer;
            return glm::dot(da, da) < glm::dot(db, db);
        });
    result.resize(maxCount);
    return result;
}

std::vector<const CatalogObjectRecord*> SparseUniverseCatalog::activeWithin(
    const glm::dvec3& observer,
    double activationRadiusMeters) const {
    activationRadiusMeters = std::max(0.0, activationRadiusMeters);
    const double radiusSquared = activationRadiusMeters * activationRadiusMeters;
    std::vector<const CatalogObjectRecord*> active;
    for (const auto& recordValue : records_) {
        const glm::dvec3 delta = recordValue.positionMeters - observer;
        if (glm::dot(delta, delta) <= radiusSquared) active.push_back(&recordValue);
    }
    return active;
}

} // namespace vf
