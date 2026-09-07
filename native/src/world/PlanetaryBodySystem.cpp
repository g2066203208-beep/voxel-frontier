#include "vf/world/PlanetaryBodySystem.hpp"

#include "vf/world/CelestialPhysicsFrame.hpp"

#include <algorithm>
#include <cmath>
#include <utility>

#include <glm/geometric.hpp>
#include <glm/gtc/quaternion.hpp>

namespace vf {
namespace {
constexpr double kPi = 3.1415926535897932384626433832795;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {1.0, 0.0, 0.0}) noexcept {
    const double l2 = glm::dot(value, value);
    return l2 > 1.0e-24 ? value / std::sqrt(l2) : fallback;
}

[[nodiscard]] glm::dvec3 strongestStarDirectionBodyLocal(
    const CelestialSystem& celestial,
    const CelestialBody& body,
    double& totalIrradiance) noexcept {
    totalIrradiance = 0.0;
    double strongestIrradiance = 0.0;
    glm::dvec3 strongestDirection{1.0, 0.0, 0.0};
    const glm::dquat inverseBody = glm::conjugate(glm::normalize(body.orientation));

    for (const CelestialBody& star : celestial.bodies()) {
        if (star.type != CelestialBodyType::Star || star.luminosityWatts <= 0.0 || star.id == body.id)
            continue;
        const glm::dvec3 delta = star.position - body.position;
        const double distanceSquared = std::max(
            glm::dot(delta, delta),
            star.radiusMeters * star.radiusMeters);
        const double irradiance = star.luminosityWatts / (4.0 * kPi * distanceSquared);
        totalIrradiance += irradiance;
        if (irradiance > strongestIrradiance) {
            strongestIrradiance = irradiance;
            strongestDirection = safeNormalize(inverseBody * delta);
        }
    }
    return strongestDirection;
}

} // namespace

std::uint32_t PlanetaryBodySystem::addBody(PlanetaryBodyDescriptor descriptor) {
    const bool needsPlanetDefinition = descriptor.solidSurface
        || descriptor.climateEnabled
        || descriptor.oceanEnabled;
    if (needsPlanetDefinition) {
        descriptor.terrain.radius = std::max(0.1, descriptor.celestial.radiusMeters);
        descriptor.terrain.maxElevation = std::max(0.0, descriptor.terrain.maxElevation);
        descriptor.terrain.maxOceanDepthMeters = std::max(0.0, descriptor.terrain.maxOceanDepthMeters);
    }

    // An ocean is a surface service in the current architecture. Silently constructing a detached
    // OceanSpectrum on a body with no authoritative surface would recreate the render/physics split
    // this registry exists to prevent, so promote such a descriptor to a solid surface owner.
    if (descriptor.oceanEnabled) descriptor.solidSurface = true;

    const std::uint32_t id = celestial_.addBody(std::move(descriptor.celestial));
    if (!descriptor.solidSurface && !descriptor.climateEnabled && !descriptor.oceanEnabled) return id;

    auto runtimeValue = std::make_unique<PlanetaryBodyRuntime>();
    runtimeValue->bodyId = id;
    runtimeValue->solidSurface = descriptor.solidSurface;
    runtimeValue->oceanEnabled = descriptor.oceanEnabled;
    runtimeValue->terrain = descriptor.terrain;

    const CelestialBody* bodyValue = celestial_.body(id);
    if (descriptor.solidSurface) {
        runtimeValue->surface = std::make_unique<PlanetSurfaceAuthority>(descriptor.terrain);
    }
    if (descriptor.climateEnabled && bodyValue != nullptr) {
        runtimeValue->climate = std::make_unique<PlanetClimateGrid>(
            descriptor.terrain,
            descriptor.climate,
            bodyValue->spinRateRadPerSecond);
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

const PlanetClimateGrid* PlanetaryBodySystem::climate(std::uint32_t bodyId) const noexcept {
    const PlanetaryBodyRuntime* value = runtime(bodyId);
    return value != nullptr ? value->climate.get() : nullptr;
}

OceanSpectrum* PlanetaryBodySystem::ocean(std::uint32_t bodyId) noexcept {
    PlanetaryBodyRuntime* value = runtime(bodyId);
    return value != nullptr ? value->ocean.get() : nullptr;
}

const OceanSpectrum* PlanetaryBodySystem::ocean(std::uint32_t bodyId) const noexcept {
    const PlanetaryBodyRuntime* value = runtime(bodyId);
    return value != nullptr ? value->ocean.get() : nullptr;
}

CelestialEnvironmentSample PlanetaryBodySystem::sampleEnvironment(
    const glm::dvec3& worldPosition) const noexcept {
    CelestialEnvironmentSample sample = celestial_.sampleEnvironment(worldPosition);
    if (sample.bodyId == 0U) return sample;

    const CelestialBody* bodyValue = celestial_.body(sample.bodyId);
    const PlanetaryBodyRuntime* runtimeValue = runtime(sample.bodyId);
    if (bodyValue == nullptr || runtimeValue == nullptr) return sample;

    const glm::dvec3 offsetWorld = worldPosition - bodyValue->position;
    const double centerDistance = glm::length(offsetWorld);
    const glm::dvec3 outwardWorld = safeNormalize(offsetWorld, {0.0, 1.0, 0.0});
    const glm::dquat inverseBody = glm::conjugate(glm::normalize(bodyValue->orientation));
    const glm::dvec3 directionBodyLocal = safeNormalize(inverseBody * outwardWorld, {0.0, 1.0, 0.0});

    double solidRadius = bodyValue->radiusMeters;
    if (runtimeValue->surface) solidRadius = runtimeValue->surface->surfaceRadius(directionBodyLocal);
    sample.altitudeMeters = centerDistance - solidRadius;

    if (!runtimeValue->climate || !celestial_.insideAtmosphere(*bodyValue, worldPosition)) return sample;

    const PlanetClimateSample climateValue = runtimeValue->climate->sample(
        directionBodyLocal,
        std::max(0.0, sample.altitudeMeters));
    sample.temperatureK = climateValue.temperatureK;
    sample.pressurePa = climateValue.pressurePa;
    sample.densityKgPerM3 = climateValue.densityKgPerM3;
    sample.humidity = climateValue.relativeHumidity;
    sample.cloudCover = climateValue.cloudFraction;
    sample.precipitationRateMmPerHour = climateValue.precipitationRateMmPerHour;

    // Use the same rotating-frame velocity transform as nearby rigid bodies. This guarantees that
    // atmosphere wind includes orbital translation and planetary surface rotation exactly once.
    const CelestialPhysicsFrame physicsFrame{bodyValue->id};
    const glm::dvec3 localPosition = physicsFrame.toLocalPosition(*bodyValue, worldPosition);
    sample.windVelocity = physicsFrame.toWorldVelocity(
        *bodyValue,
        localPosition,
        climateValue.windBodyLocalMps);
    return sample;
}

void PlanetaryBodySystem::stepPlanetServices(double deltaSeconds) {
    // The fastest PlanetClimateGrid process has an hours-scale time constant (precipitation is
    // 21,600 s by default) and the grid is only 7.5 degrees wide in longitude. Updating it at the
    // 0.25 s celestial fixed step used by 240x gameplay time is massive oversampling. A 300 s
    // simulated-time cadence is still far finer than the climate grid/process scales while cutting
    // hundreds of redundant global sweeps per real second. Accumulated time is never discarded.
    constexpr double kClimateServiceStepSeconds = 300.0;
    for (auto& runtimeValue : runtimes_) {
        if (!runtimeValue->climate) continue;
        runtimeValue->climateAccumulatorSeconds += deltaSeconds;
        if (runtimeValue->climateAccumulatorSeconds + 1.0e-12 < kClimateServiceStepSeconds)
            continue;

        const CelestialBody* bodyValue = celestial_.body(runtimeValue->bodyId);
        if (bodyValue == nullptr) continue;
        while (runtimeValue->climateAccumulatorSeconds + 1.0e-12
            >= kClimateServiceStepSeconds) {
            double totalIrradiance = 0.0;
            const glm::dvec3 strongestDirection = strongestStarDirectionBodyLocal(
                celestial_,
                *bodyValue,
                totalIrradiance);
            runtimeValue->climate->step(
                kClimateServiceStepSeconds, strongestDirection, totalIrradiance);
            runtimeValue->climateAccumulatorSeconds -= kClimateServiceStepSeconds;
            if (runtimeValue->climateAccumulatorSeconds < 0.0
                && runtimeValue->climateAccumulatorSeconds > -1.0e-9) {
                runtimeValue->climateAccumulatorSeconds = 0.0;
            }
        }
    }
}

void PlanetaryBodySystem::step(double deltaSeconds) {
    if (!std::isfinite(deltaSeconds) || deltaSeconds <= 0.0) return;

    // Orbital integration remains tightly bounded. Slow planet services accumulate these exact
    // simulated substeps and consume them on their own cadence, preserving time without coupling
    // climate cost to render FPS or accelerated orbital step count.
    double remaining = deltaSeconds;
    const double tolerance = 1.0e-12 * std::max(1.0, deltaSeconds);
    while (remaining > tolerance) {
        const double dt = std::min(remaining, CelestialSystem::kMaxOrbitalSubstepSeconds);
        celestial_.step(dt);
        stepPlanetServices(dt);
        remaining -= dt;
        if (remaining < tolerance) remaining = 0.0;
    }
}

} // namespace vf
