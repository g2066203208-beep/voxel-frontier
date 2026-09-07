#include "vf/world/PlanetSurfaceAuthority.hpp"
#include "vf/world/RegionalHydrology.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <memory>

#include <glm/geometric.hpp>

namespace {
void require(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        std::exit(1);
    }
}

glm::dvec3 safeNormalize(const glm::dvec3& value, const glm::dvec3& fallback) {
    const double l2 = glm::dot(value, value);
    return l2 > 1.0e-18 ? value / std::sqrt(l2) : fallback;
}

glm::dvec3 tangentAxis(const glm::dvec3& upInput) {
    const glm::dvec3 up = safeNormalize(upInput, {0.0, 1.0, 0.0});
    const glm::dvec3 ref = std::abs(up.y) < 0.88
        ? glm::dvec3{0.0, 1.0, 0.0}
        : glm::dvec3{1.0, 0.0, 0.0};
    return safeNormalize(glm::cross(ref, up), {1.0, 0.0, 0.0});
}
}

int main() {
    vf::PlanetDefinition planet{};
    planet.seed = 0x71A9F20DULL;
    planet.radius = 6371000.0;
    planet.maxElevation = 30000.0;
    planet.maxOceanDepthMeters = 24000.0;

    // Find the same kind of dry/elevated province used as a gameplay canyon seed. This selection
    // does not carve anything; the hydrology bake below decides where the actual channels exist.
    constexpr std::uint32_t sampleCount = 3072U;
    constexpr double goldenAngle = 2.39996322972865332;
    glm::dvec3 center{0.0, 1.0, 0.0};
    double bestScore = -1.0e30;
    for (std::uint32_t i = 0; i < sampleCount; ++i) {
        const double y = 1.0 - 2.0 * (static_cast<double>(i) + 0.5)
            / static_cast<double>(sampleCount);
        const double radial = std::sqrt(std::max(0.0, 1.0 - y * y));
        const double a = goldenAngle * static_cast<double>(i);
        const glm::dvec3 d{std::cos(a) * radial, y, std::sin(a) * radial};
        const vf::PlanetTerrainSample t = vf::samplePlanetTerrain(planet, d);
        if (t.elevationMeters < 700.0 || t.submerged(planet) || t.glacier > 0.45) continue;
        const double score = t.canyon * 3.0 + t.plateau * 0.8 + t.hills * 0.5
            + t.aridity * 0.6 - t.mountain * 0.55;
        if (score > bestScore) {
            bestScore = score;
            center = d;
        }
    }
    require(bestScore > -1.0e20, "must find a deterministic canyon-prone dry highland");

    vf::RegionalHydrologyConfig config{};
    config.resolution = 193U;
    config.halfExtentMeters = 220000.0;
    config.maxIncisionMeters = std::min(3000.0, planet.maxElevation * 0.10);
    config.riverHeadAccumulationFraction = 0.0012;
    config.fullChannelAccumulationFraction = 0.022;
    auto hydrology = std::make_shared<vf::RegionalHydrology>(planet, center, config);
    vf::PlanetSurfaceAuthority authority{planet};
    authority.setHydrology(hydrology);

    const glm::dvec3 east = tangentAxis(center);
    const glm::dvec3 north = safeNormalize(glm::cross(center, east), {0.0, 0.0, 1.0});
    double maxChannel = 0.0;
    double maxIncision = 0.0;
    double maxAuthorityCut = 0.0;
    double maxCanyon = 0.0;
    double bestEast = 0.0;
    double bestNorth = 0.0;
    constexpr int grid = 65;
    constexpr double extent = 90000.0;
    for (int iy = 0; iy < grid; ++iy) {
        const double n = -extent + 2.0 * extent * static_cast<double>(iy)
            / static_cast<double>(grid - 1);
        for (int ix = 0; ix < grid; ++ix) {
            const double e = -extent + 2.0 * extent * static_cast<double>(ix)
                / static_cast<double>(grid - 1);
            const auto drainage = hydrology->sampleLocal(e, n);
            const glm::dvec3 direction = safeNormalize(
                center + east * (e / planet.radius) + north * (n / planet.radius), center);
            const auto base = vf::samplePlanetTerrain(planet, direction);
            const auto carved = authority.sample(direction);
            const double cut = std::max(0.0, base.elevationMeters - carved.elevationMeters);
            maxChannel = std::max(maxChannel, drainage.channelStrength);
            maxAuthorityCut = std::max(maxAuthorityCut, cut);
            maxCanyon = std::max(maxCanyon, carved.canyon);
            if (drainage.incisionMeters > maxIncision) {
                maxIncision = drainage.incisionMeters;
                bestEast = e;
                bestNorth = n;
            }
        }
    }

    std::cout << "R24 hydrologic canyon diagnostics"
              << " | max_channel=" << maxChannel
              << " max_incision_m=" << maxIncision
              << " max_authority_cut_m=" << maxAuthorityCut
              << " max_canyon=" << maxCanyon << '\n';
    require(maxChannel > 0.80, "Priority-Flood accumulation must create strong regional channels");
    require(maxIncision > 900.0, "stream-power channels must create kilometre-scale canyon incision");
    require(maxAuthorityCut > 850.0, "authoritative rendered/collision surface must receive the incision");
    require(maxCanyon > 0.35, "canyon semantic mask must follow the hydrologic authority");

    // A deep incision sample must belong to a connected corridor, not be an isolated one-cell spike.
    const double neighbourStep = hydrology->cellSizeMeters();
    int connectedNeighbours = 0;
    for (int oy = -1; oy <= 1; ++oy) {
        for (int ox = -1; ox <= 1; ++ox) {
            if (ox == 0 && oy == 0) continue;
            const auto neighbour = hydrology->sampleLocal(
                bestEast + static_cast<double>(ox) * neighbourStep,
                bestNorth + static_cast<double>(oy) * neighbourStep);
            if (neighbour.incisionMeters >= maxIncision * 0.20
                && neighbour.channelStrength > 0.10) {
                ++connectedNeighbours;
            }
        }
    }
    require(connectedNeighbours >= 1,
        "deep canyon incision must connect to a neighbouring drainage cell rather than form a pillar");

    std::cout << "R24 hydrologic canyon tests passed"
              << " | max_channel=" << maxChannel
              << " max_incision_m=" << maxIncision
              << " max_authority_cut_m=" << maxAuthorityCut
              << " max_canyon=" << maxCanyon
              << " connected_neighbours=" << connectedNeighbours << '\n';
    return 0;
}
