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
    std::unique_ptr<PlanetSurfaceAuthority> surface{};
    std::unique_ptr<PlanetClimateGrid> climate{};
    std::unique_ptr<OceanSpectrum> ocean{};
};

// One registry owns every celestial body and, for solid bodies, the exact same surface/climate/water
// services used at orbital distance and at walking distance. Moon is not a debug sphere class and a
// planet is not a special-case main world; both are CelestialBody + optional planetary services.
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
    [[nodiscard]] OceanSpectrum* ocean(std::uint32_t bodyId) noexcept;

    // Advances N-body/spin state, then advances each enabled climate using the strongest star
    // direction and the sum of stellar irradiances. Fixed-step policy remains owned by AstroTime.
    void step(double deltaSeconds);

private:
    CelestialSystem celestial_{};
    std::vector<std::unique_ptr<PlanetaryBodyRuntime>> runtimes_{};
};

} // namespace vf
