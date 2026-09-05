#include "vf/world/PlanetSurface.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>

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
    planet.maxElevation = 8850.0;
    planet.maxOceanDepthMeters = 11000.0;

    double maxHills = 0.0;
    double maxCanyon = 0.0;
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

    for (std::uint32_t face = 0; face < 6U; ++face) {
        for (int y = 0; y <= 72; ++y) {
            for (int x = 0; x <= 72; ++x) {
                const double u = -1.0 + 2.0 * static_cast<double>(x) / 72.0;
                const double v = -1.0 + 2.0 * static_cast<double>(y) / 72.0;
                const auto sample = vf::samplePlanetTerrain(planet, vf::cubeSphereDirection(face, u, v));

                const double masks[] = {
                    sample.hills, sample.canyon, sample.dunes, sample.coastalCliff,
                    sample.wetland, sample.glacier, sample.aridity, sample.moisture,
                };
                for (double mask : masks) {
                    require(std::isfinite(mask) && mask >= 0.0 && mask <= 1.0,
                        "all landform/climate masks must stay finite and normalized");
                }

                maxHills = std::max(maxHills, sample.hills);
                maxCanyon = std::max(maxCanyon, sample.canyon);
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
            }
        }
    }

    require(sawLand && sawOcean, "Earth seed must retain both land and ocean");
    require(maxHills > 0.18, "Earth seed must contain rolling-hill provinces");
    require(maxCanyon > 0.015, "Earth seed must contain incised canyon terrain");
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

    std::cout << "Terrain landform tests passed"
              << " | hills=" << maxHills
              << " canyon=" << maxCanyon
              << " dunes=" << maxDunes
              << " cliff=" << maxCliff
              << " wetland=" << maxWetland
              << " glacier=" << maxGlacier << '\n';
    return 0;
}
