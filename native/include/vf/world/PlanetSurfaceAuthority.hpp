#pragma once

#include "vf/world/PlanetSurface.hpp"
#include "vf/world/RegionalHydrology.hpp"

#include <atomic>
#include <memory>

namespace vf {

// Single authoritative solid-surface query used by rendering, collision, ecology and water.
// The base tectonic terrain is deterministic and global; an optional immutable regional
// hydrology bake adds process-derived incision without creating a second, render-only heightfield.
class PlanetSurfaceAuthority final {
public:
    explicit PlanetSurfaceAuthority(PlanetDefinition planet = {}) noexcept;

    [[nodiscard]] const PlanetDefinition& planet() const noexcept { return planet_; }
    void setPlanet(PlanetDefinition planet) noexcept;

    void setHydrology(std::shared_ptr<const RegionalHydrology> hydrology) noexcept;
    [[nodiscard]] std::shared_ptr<const RegionalHydrology> hydrology() const noexcept;

    [[nodiscard]] PlanetTerrainSample sample(const glm::dvec3& direction) const noexcept;
    [[nodiscard]] double elevationMeters(const glm::dvec3& direction) const noexcept;
    [[nodiscard]] double surfaceRadius(const glm::dvec3& direction) const noexcept;
    [[nodiscard]] glm::dvec3 surfaceNormal(const glm::dvec3& direction) const noexcept;

private:
    [[nodiscard]] bool hydrologyCovers(
        const RegionalHydrology& hydrology,
        const glm::dvec3& direction) const noexcept;

    PlanetDefinition planet_{};
    std::atomic<std::shared_ptr<const RegionalHydrology>> hydrology_{};
};

} // namespace vf
