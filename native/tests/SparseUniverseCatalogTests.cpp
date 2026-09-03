#include "vf/world/SparseUniverseCatalog.hpp"

#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "SPARSE UNIVERSE TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void testCatalogIsDeterministicAndTiny() {
    vf::SparseUniverseCatalog first{0x12345678ULL, 512U, 100000.0, 4000000.0};
    vf::SparseUniverseCatalog second{0x12345678ULL, 512U, 100000.0, 4000000.0};

    require(first.records().size() == 512U && second.records().size() == 512U,
        "catalog must create the requested bounded record count");
    require(first.approximateMemoryBytes() < 128U * 1024U,
        "512 far celestial records should stay well below 128 KiB");

    for (std::size_t i = 0; i < first.records().size(); i += 37U) {
        const auto& a = first.records()[i];
        const auto& b = second.records()[i];
        require(a.id == b.id && a.seed == b.seed && a.type == b.type,
            "same seed must recreate identical catalog metadata");
        require(glm::length(a.positionMeters - b.positionMeters) < 1.0e-9,
            "same seed must recreate identical double-precision coordinates");
    }
}

void testFarRecordsDoNotActivateUntilApproached() {
    vf::SparseUniverseCatalog catalog{0xCAFEULL, 256U, 250000.0, 1500000.0};
    const glm::dvec3 origin{};
    require(catalog.activeWithin(origin, 100000.0).empty(),
        "far catalog objects must not instantiate detailed simulation near the home system");

    const auto nearest = catalog.nearestVisible(origin, 1U);
    require(nearest.size() == 1U && nearest.front() != nullptr,
        "catalog must provide a nearest visible destination without instantiating it");

    const glm::dvec3 observerNear = nearest.front()->positionMeters + glm::dvec3{500.0, 0.0, 0.0};
    const auto active = catalog.activeWithin(observerNear, 1000.0);
    require(!active.empty(),
        "approaching a recorded coordinate must expose it to the active-world loader");
    require(active.front()->id == nearest.front()->id,
        "the activated object must preserve the same catalog identity and seed");
}

void testCatalogContainsReachableDestinationTypes() {
    vf::SparseUniverseCatalog catalog{0xBADC0FFEEULL, 1024U, 100000.0, 5000000.0};
    bool star = false;
    bool rogue = false;
    bool asteroid = false;
    bool comet = false;
    for (const auto& record : catalog.records()) {
        switch (record.type) {
        case vf::CatalogObjectType::StarSystem: star = true; break;
        case vf::CatalogObjectType::RoguePlanet: rogue = true; break;
        case vf::CatalogObjectType::AsteroidField: asteroid = true; break;
        case vf::CatalogObjectType::Comet: comet = true; break;
        }
    }
    require(star && rogue && asteroid && comet,
        "catalog generation must include stars, rogue planets, asteroid fields and comets");
}

} // namespace

int main() {
    testCatalogIsDeterministicAndTiny();
    testFarRecordsDoNotActivateUntilApproached();
    testCatalogContainsReachableDestinationTypes();
    std::cout << "vf_sparse_universe_catalog_tests: PASS\n";
    return 0;
}
