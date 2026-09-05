#include "vf/world/PlanetaryBodySystem.hpp"

#include <algorithm>
#include <cmath>

#include <glm/geometric.hpp>

namespace vf {
namespace {
constexpr double kPi = 3.1415926535897932384626433832795;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {1.0, 0.0, 0.0}) noexcept {
    const double l2 = glm::dot(value, value);
    return l2 > 1.0e-24 ? value / std::sqrt(l2) : fallback;
}
} // namespace

std::uint32_t PlanetaryBodySystem::addBody(PlanetaryBodyDescriptor descriptor) {
    if (descriptor.solidSurface) {
        descriptor.terrain.radius = descriptor.celestial.radiusMeters;
        descriptor.terrain.maxElevation = std::max(0.0, descriptor.terrain.maxElevation);
        descriptor.terrain.maxOceanDepthMeters = std::max(0.0, descriptor.terrain.maxOceanDepthMeters);
    }
    const std::uint32_t id = celestial_.addBody(std::move(descriptor.celestial));
    if (!descriptor.solidSurface && !descriptor.climateEnabled && !descriptor.oceanEnabled) return id;

    auto runtimeValue = std::make_unique<PlanetaryBodyRuntime>();
    runtimeValue->bodyId = id;
    runtimeValue->solidSurface = descriptor.solidSurface;
    runtimeValue->oceanEnabled = descriptor.oceanEnabled;
    const CelestialBody* body = celestial_.body(id);
    if (descriptor.solidSurface) {
        runtimeValue->surface = std::make_unique<PlanetSurfaceAuthority>(descriptor.terrain);
    }
    if (descriptor.climateEnabled && body != nullptr) {
        runtimeValue->climate = std::make_unique<PlanetClimateGrid>(
            descriptor.terrain,
            descriptor.climate,
            body->spinRateRadPerSecond);
    }
    if (descriptor.oceanEnabled) {
        runtimeValue->ocean = std::make_unique<OceanSpectrum>(descriptor.ocean);
    }
    runtimes_.push_back(std::move(runtimeValue));
    return id;
}

PlanetaryBodyRuntime* PlanetaryBodySystem::runtime(std::uint32_t bodyId) noexcept {
    for (auto& candidate : runtimes_) if (candidate->bodyId == bodyId) return candidate.get();
    return nullptr;
}

const PlanetaryBodyRuntime* PlanetaryBodySystem::runtime(std::uint32_t bodyId) const noexcept {
    for (const auto& candidate : runtimes_) if (candidate->bodyId == bodyId) return candidate.get();
    return nullptr;
}

PlanetSurfaceAuthority* PlanetaryBodySystem::surface(std::uint32_t bodyId) noexcept {
    PlanetaryBodyRuntime* value = runtime(bodyId);
    return value != nullptr ? value->surface.get() : nullptr;
}

const PlanetSurfaceAuthority* PlanetaryBodySystem::surface(std::uint32_t bodyId) const noexcept {
    const PlanetaryBodyRuntime* value = runtime(bodyId);
    return value != nullptr ? value->surface.get() : nullptr;
}

PlanetClimateGrid* PlanetaryBodySystem::climate(std::uint32_t bodyId) noexcept {
    PlanetaryBodyRuntime* value = runtime(bodyId);
    return value != nullptr ? value->climate.get() : nullptr;
}

OceanSpectrum* PlanetaryBodySystem::ocean(std::uint32_t bodyId) noexcept {
    PlanetaryBodyRuntime* value = runtime(bodyId);
    return value != nullptr ? value->ocean.get() : nullptr;
}

void PlanetaryBodySystem::step(double deltaSeconds) {
    celestial_.step(deltaSeconds);
    if (deltaSeconds <= 0.0) return;

    for (auto& runtimeValue : runtimes_) {
        if (!runtimeValue->climate) continue;
        const CelestialBody* body = celestial_.body(runtimeValue->bodyId);
        if (body == nullptr) continue;

        double totalIrradiance = 0.0;
        double strongestIrradiance = 0.0;
        glm::dvec3 strongestDirection{1.0, 0.0, 0.0};
        for (const CelestialBody& star : celestial_.bodies()) {
            if (star.type != CelestialBodyType::Star || star.luminosityWatts <= 0.0) continue;
            const glm::dvec3 delta = star.position - body->position;
            const double distanceSquared = std::max(glm::dot(delta, delta), star.radiusMeters * star.radiusMeters);
            const double irradiance = star.luminosityWatts / (4.0 * kPi * distanceSquared);
            totalIrradiance += irradiance;
            if (irradiance > strongestIrradiance) {
                strongestIrradiance = irradiance;
                strongestDirection = safeNormalize(glm::conjugate(glm::normalize(body->orientation)) * delta);
            }
        }
        runtimeValue->climate->step(deltaSeconds, strongestDirection, totalIrradiance);
    }
}

} // namespace vf
