#include "vf/world/PlanetSurface.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>

#include <glm/geometric.hpp>

namespace {

void require(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        std::exit(1);
    }
}

} // namespace

int main() {
    vf::PlanetDefinition planet{};
    planet.seed = 0x71A9F20DULL;
    planet.radius = 6371000.0;
    planet.maxElevation = 30000.0;
    planet.maxOceanDepthMeters = 24000.0;

    double maxHills = 0.0;
    double maxCanyon = 0.0;
    double maxAbyss = 0.0;
    double maxRift = 0.0;
    double maxShear = 0.0;
    double maxAlluvial = 0.0;
    double maxDunes = 0.0;
    double maxCliff = 0.0;
    double maxWetland = 0.0;
    double maxGlacier = 0.0;
    double maxAridity = 0.0;
    double maxMoisture = 0.0;
    double minElevation = 1.0e30;
    double maxElevation = -1.0e30;
    bool sawLand = false;
    bool sawOcean = false;
    glm::dvec3 mountainProbeDirection{0.0, 1.0, 0.0};
    glm::dvec3 riftProbeDirection{0.0, 1.0, 0.0};
    double mountainProbeScore = -1.0e30;
    double riftProbeScore = -1.0e30;

    for (std::uint32_t face = 0; face < 6U; ++face) {
        for (int y = 0; y <= 72; ++y) {
            for (int x = 0; x <= 72; ++x) {
                const double u = -1.0 + 2.0 * static_cast<double>(x) / 72.0;
                const double v = -1.0 + 2.0 * static_cast<double>(y) / 72.0;
                const glm::dvec3 direction = vf::cubeSphereDirection(face, u, v);
                const auto sample = vf::samplePlanetTerrain(planet, direction);

                const double masks[] = {
                    sample.hills, sample.canyon, sample.abyss, sample.rift, sample.shear, sample.alluvialFan,
                    sample.dunes, sample.coastalCliff, sample.wetland, sample.glacier,
                    sample.aridity, sample.moisture,
                };
                for (double mask : masks) {
                    require(std::isfinite(mask) && mask >= 0.0 && mask <= 1.0,
                        "all landform/climate masks must stay finite and normalized");
                }

                maxHills = std::max(maxHills, sample.hills);
                maxCanyon = std::max(maxCanyon, sample.canyon);
                maxAbyss = std::max(maxAbyss, sample.abyss);
                maxRift = std::max(maxRift, sample.rift);
                maxShear = std::max(maxShear, sample.shear);
                maxAlluvial = std::max(maxAlluvial, sample.alluvialFan);
                maxDunes = std::max(maxDunes, sample.dunes);
                maxCliff = std::max(maxCliff, sample.coastalCliff);
                maxWetland = std::max(maxWetland, sample.wetland);
                maxGlacier = std::max(maxGlacier, sample.glacier);
                maxAridity = std::max(maxAridity, sample.aridity);
                maxMoisture = std::max(maxMoisture, sample.moisture);
                minElevation = std::min(minElevation, sample.elevationMeters);
                maxElevation = std::max(maxElevation, sample.elevationMeters);
                sawLand = sawLand || sample.elevationMeters > 100.0;
                sawOcean = sawOcean || sample.elevationMeters < -500.0;

                if (sample.elevationMeters > 150.0 && sample.glacier < 0.55) {
                    const double mountainScore = sample.mountain * 2.0
                        + sample.convergence * 0.55
                        - sample.glacier * 0.80
                        - std::max(0.0, (sample.elevationMeters - 8000.0) / 2000.0);
                    if (mountainScore > mountainProbeScore) {
                        mountainProbeScore = mountainScore;
                        mountainProbeDirection = direction;
                    }
                    const double riftScore = sample.rift * 2.0 + sample.divergence * 0.65
                        - sample.mountain * 0.30;
                    if (riftScore > riftProbeScore) {
                        riftProbeScore = riftScore;
                        riftProbeDirection = direction;
                    }
                }
            }
        }
    }

    require(sawLand && sawOcean, "Earth seed must retain both land and ocean");
    require(maxHills > 0.18, "Earth seed must contain rolling-hill provinces");
    require(maxCanyon > 0.015, "Earth seed must contain incised canyon terrain");
    require(maxAbyss > 0.10, "gameplay planet must contain mega-abyss cave throats");
    require(maxRift > 0.015, "Earth seed must contain divergent continental rifts");
    require(maxShear > 0.015, "Earth seed must contain transform-boundary shear terrain");
    require(maxAlluvial > 0.005, "Earth seed must contain lowland alluvial deposition");
    require(maxDunes > 0.015, "Earth seed must contain dune terrain");
    require(maxCliff > 0.035, "Earth seed must contain coastal cliffs");
    require(maxWetland > 0.020, "Earth seed must contain lowland wetland terrain");
    require(maxGlacier > 0.050, "Earth seed must contain polar/highland glacier terrain");
    require(maxAridity > 0.10 && maxMoisture > 0.50,
        "Earth seed must contain meaningfully different dry and wet climate regions");
    require(minElevation >= -planet.maxOceanDepthMeters - 1.0e-6,
        "new landforms must respect configured ocean-depth clamp");
    require(maxElevation <= planet.maxElevation + 1.0e-6,
        "new landforms must respect configured elevation clamp");

    const auto localRelief = [&](const glm::dvec3& centerInput, double radiusMeters) {
        const glm::dvec3 center = glm::normalize(centerInput);
        const glm::dvec3 reference = std::abs(center.y) < 0.88
            ? glm::dvec3{0.0, 1.0, 0.0}
            : glm::dvec3{1.0, 0.0, 0.0};
        const glm::dvec3 tangent = glm::normalize(glm::cross(reference, center));
        const glm::dvec3 bitangent = glm::normalize(glm::cross(center, tangent));
        double localMin = vf::samplePlanetTerrain(planet, center).elevationMeters;
        double localMax = localMin;
        constexpr int azimuthSamples = 32;
        for (int ring = 1; ring <= 3; ++ring) {
            const double ringRadius = radiusMeters * static_cast<double>(ring) / 3.0;
            for (int i = 0; i < azimuthSamples; ++i) {
                const double angle = 6.28318530717958647692 * static_cast<double>(i)
                    / static_cast<double>(azimuthSamples);
                const glm::dvec3 outward = tangent * std::cos(angle)
                    + bitangent * std::sin(angle);
                const glm::dvec3 direction = glm::normalize(
                    center + outward * (ringRadius / planet.radius));
                const double elevation = vf::samplePlanetTerrain(planet, direction).elevationMeters;
                localMin = std::min(localMin, elevation);
                localMax = std::max(localMax, elevation);
            }
        }
        return localMax - localMin;
    };

    const double mountainLocalRelief = localRelief(mountainProbeDirection, 28000.0);
    const double riftLocalRelief = localRelief(riftProbeDirection, 24000.0);
    require(mountainLocalRelief > 4500.0,
        "epic convergent mountains must contain >4.5 km real 3-D relief within 28 km");
    require(riftLocalRelief > 1800.0,
        "epic continental rifts must contain >1.8 km real 3-D fault relief within 24 km");
    require(maxElevation > 15000.0,
        "gameplay-first planet must generate mountain summits above 15 km");

    std::cout << "Terrain landform tests passed"
              << " | hills=" << maxHills
              << " canyon=" << maxCanyon
              << " abyss=" << maxAbyss
              << " rift=" << maxRift
              << " shear=" << maxShear
              << " alluvial=" << maxAlluvial
              << " dunes=" << maxDunes
              << " cliff=" << maxCliff
              << " wetland=" << maxWetland
              << " glacier=" << maxGlacier
              << " mountain_local_relief_m=" << mountainLocalRelief
              << " rift_local_relief_m=" << riftLocalRelief << '\n';
    return 0;
}
