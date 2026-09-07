#pragma once

#include "vf/physics/OceanSpectrum.hpp"
#include "vf/world/CelestialSystem.hpp"
#include "vf/world/PlanetClimateGrid.hpp"
#include "vf/world/PlanetSurfaceAuthority.hpp"

#include <cstdint>
#include <memory>
#include <vector>

namespace vf {

struct PlanetaryBodyDescriptor {
    CelestialBody celestial{};
    bool solidSurface{};
    PlanetDefinition terrain{};
    bool climateEnabled{};
    PlanetClimateConfig climate{};
    bool oceanEnabled{};
    OceanSpectrumConfig ocean{};
};

struct PlanetaryBodyRuntime {
    std::uint32_t bodyId{};
    bool solidSurface{};
    bool oceanEnabled{};
    PlanetDefinition terrain{};
    std::unique_ptr<PlanetSurfaceAuthority> surface{};
    std::unique_ptr<PlanetClimateGrid> climate{};
    std::unique_ptr<OceanSpectrum> ocean{};
    // Multi-rate world simulation: orbital integration can run at sub-second cadence while the
    // 24x48 global climate grid advances on a much slower simulated-time service cadence.
    double climateAccumulatorSeconds{};
};

// Authoritative registry for a celestial body and all optional planet-scale services that belong to
// that same physical object. A moon is not a debug sphere and the primary planet is not a special
// application-only world: both are CelestialBody plus optional surface/climate/ocean services.
class PlanetaryBodySystem final {
public:
    [[nodiscard]] std::uint32_t addBody(PlanetaryBodyDescriptor descriptor);

    [[nodiscard]] CelestialSystem& celestial() noexcept { return celestial_; }
    [[nodiscard]] const CelestialSystem& celestial() const noexcept { return celestial_; }

    [[nodiscard]] PlanetaryBodyRuntime* runtime(std::uint32_t bodyId) noexcept;
    [[nodiscard]] const PlanetaryBodyRuntime* runtime(std::uint32_t bodyId) const noexcept;

    [[nodiscard]] PlanetSurfaceAuthority* surface(std::uint32_t bodyId) noexcept;
    [[nodiscard]] const PlanetSurfaceAuthority* surface(std::uint32_t bodyId) const noexcept;
    [[nodiscard]] PlanetClimateGrid* climate(std::uint32_t bodyId) noexcept;
    [[nodiscard]] const PlanetClimateGrid* climate(std::uint32_t bodyId) const noexcept;
    [[nodiscard]] OceanSpectrum* ocean(std::uint32_t bodyId) noexcept;
    [[nodiscard]] const OceanSpectrum* ocean(std::uint32_t bodyId) const noexcept;

    // Unified environment query. CelestialSystem supplies gravity/magnetism/orbital atmosphere
    // ownership; a registered solid surface replaces spherical altitude with authoritative terrain,
    // and PlanetClimateGrid replaces fallback atmosphere/weather with the causal local solution.
    [[nodiscard]] CelestialEnvironmentSample sampleEnvironment(
        const glm::dvec3& worldPosition) const noexcept;

    // Advances celestial N-body/spin on bounded orbital substeps. Slow planet services use their
    // own accumulated simulated-time cadence; a render frame therefore never pays for a full global
    // climate sweep once per orbital substep under time acceleration.
    void step(double deltaSeconds);

private:
    void stepPlanetServices(double deltaSeconds);

    CelestialSystem celestial_{};
    std::vector<std::unique_ptr<PlanetaryBodyRuntime>> runtimes_{};
};

} // namespace vf
