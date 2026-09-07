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

[[nodiscard]] double smooth01(double value) noexcept {
    const double t = std::clamp(value, 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
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

double PlanetSurfaceAuthority::hydrologyWeight(
    const RegionalHydrology& hydro,
    const glm::dvec3& directionInput) const noexcept {
    if (hydro.empty() || planet_.radius <= 0.0) return 0.0;
    const glm::dvec3 direction = safeNormalize(directionInput, hydro.centerDirection());
    const double cosine = std::clamp(glm::dot(direction, hydro.centerDirection()), -1.0, 1.0);
    const double arcMeters = std::acos(cosine) * planet_.radius;
    const double halfExtent = std::max(1.0, hydro.halfExtentMeters());
    const double fadeStart = halfExtent * 0.72;
    const double fadeEnd = halfExtent * 0.94;
    if (arcMeters >= fadeEnd) return 0.0;
    if (arcMeters <= fadeStart) return 1.0;
    return 1.0 - smooth01((arcMeters - fadeStart) / std::max(1.0, fadeEnd - fadeStart));
}

PlanetTerrainSample PlanetSurfaceAuthority::sample(const glm::dvec3& directionInput) const noexcept {
    const glm::dvec3 direction = safeNormalize(directionInput);
    PlanetTerrainSample terrain = samplePlanetTerrain(planet_, direction);

    const auto hydro = hydrology();
    if (hydro) {
        const double weight = hydrologyWeight(*hydro, direction);
        if (weight > 0.0) {
            const RegionalHydrologySample drainage = hydro->sample(direction);
            terrain.elevationMeters -= drainage.incisionMeters * weight;
            terrain.river = std::clamp(
                terrain.river * (1.0 - weight) + drainage.channelStrength * weight,
                0.0,
                1.0);
            const double hydrologyWetland = std::clamp(
                drainage.depositionPotential * 0.72 + drainage.lakePotential * 0.90,
                0.0,
                1.0);
            terrain.wetland = std::clamp(
                terrain.wetland * (1.0 - 0.65 * weight)
                    + hydrologyWetland * weight,
                0.0,
                1.0);
            terrain.oceanDepthMeters = std::max(
                0.0,
                planet_.seaLevelElevationMeters - terrain.elevationMeters);
        }
    }
    return terrain;
}

PlanetSurfaceSample PlanetSurfaceAuthority::sampleSurface(
    const glm::dvec3& directionInput) const noexcept {
    PlanetSurfaceSample result{};
    const glm::dvec3 d = safeNormalize(directionInput);
    result.terrain = sample(d);
    result.radiusMeters = planet_.radius + result.terrain.elevationMeters;
    result.position = d * result.radiusMeters;

    // Only two neighbouring authority samples are required. The old call pattern often evaluated
    // the center terrain again inside surfaceNormal() and then once more in surfaceRadius().
    const glm::dvec3 east = tangentAxis(d);
    const glm::dvec3 north = safeNormalize(glm::cross(d, east), {0.0, 0.0, 1.0});
    const double angularStep = std::clamp(
        2.0 / std::max(1.0, planet_.radius),
        1.0e-7,
        2.0e-3);
    const glm::dvec3 dEastPlus = safeNormalize(d + east * angularStep, d);
    const glm::dvec3 dEastMinus = safeNormalize(d - east * angularStep, d);
    const glm::dvec3 dNorthPlus = safeNormalize(d + north * angularStep, d);
    const glm::dvec3 dNorthMinus = safeNormalize(d - north * angularStep, d);
    const PlanetTerrainSample terrainEastPlus = sample(dEastPlus);
    const PlanetTerrainSample terrainEastMinus = sample(dEastMinus);
    const PlanetTerrainSample terrainNorthPlus = sample(dNorthPlus);
    const PlanetTerrainSample terrainNorthMinus = sample(dNorthMinus);
    const glm::dvec3 pEastPlus = dEastPlus
        * (planet_.radius + terrainEastPlus.elevationMeters);
    const glm::dvec3 pEastMinus = dEastMinus
        * (planet_.radius + terrainEastMinus.elevationMeters);
    const glm::dvec3 pNorthPlus = dNorthPlus
        * (planet_.radius + terrainNorthPlus.elevationMeters);
    const glm::dvec3 pNorthMinus = dNorthMinus
        * (planet_.radius + terrainNorthMinus.elevationMeters);
    result.normal = safeNormalize(
        glm::cross(pEastPlus - pEastMinus, pNorthPlus - pNorthMinus), d);
    if (glm::dot(result.normal, d) < 0.0) result.normal = -result.normal;
    return result;
}

double PlanetSurfaceAuthority::elevationMeters(const glm::dvec3& direction) const noexcept {
    return sample(direction).elevationMeters;
}

double PlanetSurfaceAuthority::surfaceRadius(const glm::dvec3& direction) const noexcept {
    return planet_.radius + elevationMeters(direction);
}

glm::dvec3 PlanetSurfaceAuthority::surfaceNormal(const glm::dvec3& direction) const noexcept {
    return sampleSurface(direction).normal;
}

} // namespace vf
