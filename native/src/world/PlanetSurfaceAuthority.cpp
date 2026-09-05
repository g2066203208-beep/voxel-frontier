#include "vf/world/PlanetSurfaceAuthority.hpp"

#include <algorithm>
#include <cmath>

#include <glm/geometric.hpp>

namespace vf {
namespace {

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    return lengthSquared > 1.0e-18 ? value / std::sqrt(lengthSquared) : fallback;
}

[[nodiscard]] glm::dvec3 tangentAxis(const glm::dvec3& upInput) noexcept {
    const glm::dvec3 up = safeNormalize(upInput);
    const glm::dvec3 a = glm::abs(up);
    glm::dvec3 reference{1.0, 0.0, 0.0};
    if (a.y <= a.x && a.y <= a.z) reference = {0.0, 1.0, 0.0};
    else if (a.z <= a.x && a.z <= a.y) reference = {0.0, 0.0, 1.0};
    return safeNormalize(glm::cross(reference, up), {1.0, 0.0, 0.0});
}

} // namespace

PlanetSurfaceAuthority::PlanetSurfaceAuthority(PlanetDefinition planet) noexcept
    : planet_(planet) {}

void PlanetSurfaceAuthority::setPlanet(PlanetDefinition planet) noexcept {
    planet_ = planet;
}

void PlanetSurfaceAuthority::setHydrology(
    std::shared_ptr<const RegionalHydrology> hydrology) noexcept {
    hydrology_.store(std::move(hydrology), std::memory_order_release);
}

std::shared_ptr<const RegionalHydrology> PlanetSurfaceAuthority::hydrology() const noexcept {
    return hydrology_.load(std::memory_order_acquire);
}

bool PlanetSurfaceAuthority::hydrologyCovers(
    const RegionalHydrology& hydro,
    const glm::dvec3& directionInput) const noexcept {
    if (hydro.empty() || planet_.radius <= 0.0) return false;
    const glm::dvec3 direction = safeNormalize(directionInput, hydro.centerDirection());
    const double cosine = std::clamp(glm::dot(direction, hydro.centerDirection()), -1.0, 1.0);
    const double arcMeters = std::acos(cosine) * planet_.radius;
    // RegionalHydrology is a tangent-plane square. sqrt(2) preserves its corners while the
    // actual sample() call still returns zero outside the exact local grid.
    return arcMeters <= hydro.halfExtentMeters() * 1.4142135623730951;
}

PlanetTerrainSample PlanetSurfaceAuthority::sample(const glm::dvec3& directionInput) const noexcept {
    const glm::dvec3 direction = safeNormalize(directionInput);
    PlanetTerrainSample terrain = samplePlanetTerrain(planet_, direction);

    const auto hydro = hydrology();
    if (hydro && hydrologyCovers(*hydro, direction)) {
        const RegionalHydrologySample drainage = hydro->sample(direction);
        terrain.elevationMeters -= drainage.incisionMeters;
        // Inside a hydrology-authoritative region, river identity comes from drainage topology,
        // not from the legacy pointwise river mask. This is the first step toward one causal chain.
        terrain.river = drainage.channelStrength;
        terrain.wetland = std::clamp(
            std::max(terrain.wetland * 0.35,
                drainage.depositionPotential * 0.72 + drainage.lakePotential * 0.90),
            0.0,
            1.0);
        terrain.oceanDepthMeters = std::max(
            0.0,
            planet_.seaLevelElevationMeters - terrain.elevationMeters);
    }
    return terrain;
}

double PlanetSurfaceAuthority::elevationMeters(const glm::dvec3& direction) const noexcept {
    return sample(direction).elevationMeters;
}

double PlanetSurfaceAuthority::surfaceRadius(const glm::dvec3& direction) const noexcept {
    return planet_.radius + elevationMeters(direction);
}

glm::dvec3 PlanetSurfaceAuthority::surfaceNormal(const glm::dvec3& directionInput) const noexcept {
    const glm::dvec3 d = safeNormalize(directionInput);
    const glm::dvec3 east = tangentAxis(d);
    const glm::dvec3 north = safeNormalize(glm::cross(d, east), {0.0, 0.0, 1.0});
    const double angularStep = std::clamp(
        2.0 / std::max(1.0, planet_.radius),
        1.0e-7,
        2.0e-3);
    const glm::dvec3 dEast = safeNormalize(d + east * angularStep, d);
    const glm::dvec3 dNorth = safeNormalize(d + north * angularStep, d);
    const glm::dvec3 p0 = d * surfaceRadius(d);
    const glm::dvec3 pEast = dEast * surfaceRadius(dEast);
    const glm::dvec3 pNorth = dNorth * surfaceRadius(dNorth);
    glm::dvec3 normal = safeNormalize(glm::cross(pEast - p0, pNorth - p0), d);
    if (glm::dot(normal, d) < 0.0) normal = -normal;
    return normal;
}

} // namespace vf
