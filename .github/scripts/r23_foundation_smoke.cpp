#include "vf/world/AstroTime.hpp"
#include "vf/world/RegionalHydrology.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>

#include <glm/geometric.hpp>

namespace {

void require(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "R23 FOUNDATION FAILURE: " << message << '\n';
        std::exit(1);
    }
}

} // namespace

int main() {
    // Time-warp regression: 0.5 real seconds at 3600x must execute exactly 30 one-minute orbital
    // steps and advance the astronomical epoch by 1800 s. No simulated time may be discarded.
    vf::CelestialSimulationClock clock{{60.0, 3600.0, 4096U}};
    double integratedSeconds = 0.0;
    std::size_t callbackCount = 0U;
    const std::size_t steps = clock.advance(0.5, [&](double dt) {
        integratedSeconds += dt;
        ++callbackCount;
    });
    require(steps == 30U && callbackCount == 30U,
        "3600x time warp must be decomposed into deterministic 60 s steps");
    require(std::abs(integratedSeconds - 1800.0) < 1.0e-9,
        "fixed-step callbacks must receive the complete scaled time");
    require(std::abs(static_cast<double>(clock.time().secondsFromEpoch()) - 1800.0) < 1.0e-9,
        "AstroTime epoch must advance by the complete integrated interval");
    require(std::abs(clock.pendingSeconds()) < 1.0e-9,
        "exact multiples of fixed step must leave no pending time");

    // Catch-up budget regression: queued time stays queued instead of being silently dropped.
    vf::CelestialSimulationClock budgetClock{{60.0, 3600.0, 4U}};
    const std::size_t budgetSteps = budgetClock.advance(1.0, [](double) {});
    require(budgetSteps == 4U, "per-frame celestial work must obey the configured CPU budget");
    require(budgetClock.pendingSeconds() > 3300.0,
        "unprocessed astronomical time must remain queued after budget exhaustion");

    vf::PlanetDefinition planet{};
    planet.seed = 0x71A9F20DULL;
    planet.radius = 6371000.0;
    planet.maxElevation = 8850.0;
    planet.maxOceanDepthMeters = 11000.0;

    // Pick a deterministic inland area and build a real regional drainage topology.
    const glm::dvec3 center = glm::normalize(glm::dvec3{0.72, 0.52, 0.46});
    vf::RegionalHydrologyConfig config{};
    config.resolution = 97U;
    config.halfExtentMeters = 60000.0;
    config.maxIncisionMeters = 180.0;
    vf::RegionalHydrology hydrology{planet, center, config};

    require(hydrology.resolution() == 97U, "hydrology grid resolution must remain deterministic");
    require(hydrology.cellSizeMeters() > 100.0,
        "regional hydrology must expose a physically scaled DEM cell size");

    double maxChannel = 0.0;
    double maxIncision = 0.0;
    double maxAccumulation = 0.0;
    double maxLake = 0.0;
    for (int y = -24; y <= 24; ++y) {
        for (int x = -24; x <= 24; ++x) {
            const auto sample = hydrology.sampleLocal(
                static_cast<double>(x) * 1800.0,
                static_cast<double>(y) * 1800.0);
            require(std::isfinite(sample.channelStrength)
                    && sample.channelStrength >= 0.0 && sample.channelStrength <= 1.0,
                "channel strength must stay finite and normalized");
            require(std::isfinite(sample.contributingAreaFraction)
                    && sample.contributingAreaFraction >= 0.0
                    && sample.contributingAreaFraction <= 1.0,
                "contributing area must stay finite and normalized");
            maxChannel = std::max(maxChannel, sample.channelStrength);
            maxIncision = std::max(maxIncision, sample.incisionMeters);
            maxAccumulation = std::max(maxAccumulation, sample.contributingAreaFraction);
            maxLake = std::max(maxLake, sample.lakePotential);
        }
    }

    require(maxAccumulation > 0.003,
        "Priority-Flood drainage must produce cells with meaningful contributing area");
    require(maxChannel > 0.02,
        "drainage accumulation must produce a non-trivial channel network");
    require(maxIncision > 1.0,
        "channel network must produce visible process-derived incision potential");

    std::cout << "R23 foundation smoke: PASS"
              << " | astro_steps=" << steps
              << " | max_channel=" << maxChannel
              << " | max_incision_m=" << maxIncision
              << " | max_accumulation=" << maxAccumulation
              << " | max_lake=" << maxLake << '\n';
    return 0;
}
