#include "vf/world/CelestialSystem.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;
constexpr double kUniversalGasConstant = 8.314462618;
constexpr double kEpsilon = 1.0e-9;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= kEpsilon) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] double saturate(double value) noexcept {
    return std::clamp(value, 0.0, 1.0);
}

[[nodiscard]] double smooth01(double value) noexcept {
    const double x = saturate(value);
    return x * x * (3.0 - 2.0 * x);
}

} // namespace

std::uint32_t CelestialSystem::addBody(CelestialBody bodyValue) {
    if (bodyValue.id == 0U) bodyValue.id = nextBodyId_++;
    else nextBodyId_ = std::max(nextBodyId_, bodyValue.id + 1U);
    bodyValue.radiusMeters = std::max(0.1, bodyValue.radiusMeters);
    bodyValue.massKg = std::max(0.0, bodyValue.massKg);
    bodyValue.orientation = glm::normalize(bodyValue.orientation);
    bodyValue.spinAxis = safeNormalize(bodyValue.spinAxis);
    bodyValue.gameplaySurfaceGravityMps2 = std::max(0.0, bodyValue.gameplaySurfaceGravityMps2);
    if (bodyValue.gravityInfluenceRadiusMeters > 0.0) {
        bodyValue.gravityInfluenceRadiusMeters = std::max(
            bodyValue.radiusMeters * 1.05,
            bodyValue.gravityInfluenceRadiusMeters);
    }
    bodyValue.atmosphere.heightMeters = std::max(0.0, bodyValue.atmosphere.heightMeters);
    bodyValue.atmosphere.scaleHeightMeters = std::max(1.0, bodyValue.atmosphere.scaleHeightMeters);
    bodies_.push_back(std::move(bodyValue));
    return bodies_.back().id;
}

CelestialBody* CelestialSystem::body(std::uint32_t id) noexcept {
    for (auto& candidate : bodies_) if (candidate.id == id) return &candidate;
    return nullptr;
}

const CelestialBody* CelestialSystem::body(std::uint32_t id) const noexcept {
    for (const auto& candidate : bodies_) if (candidate.id == id) return &candidate;
    return nullptr;
}

void CelestialSystem::step(double deltaSeconds) {
    if (!std::isfinite(deltaSeconds) || deltaSeconds <= 0.0) return;
    // Celestial motion is intentionally low-frequency game physics. A caller can feed a
    // coarse tick (e.g. 10-30 Hz or slower); there is no need to run it at rigid-body rate.
    const double dt = std::min(deltaSeconds, 60.0);
    for (auto& celestialBody : bodies_) updateOrbit(celestialBody, dt);
    for (auto& celestialBody : bodies_) {
        updateSpin(celestialBody, dt);
        updateClimateAndWeather(celestialBody, dt);
    }
    simulationTime_ += dt;
}

void CelestialSystem::updateOrbit(CelestialBody& celestialBody, double deltaSeconds) {
    if (celestialBody.orbitParentId == 0U) return;
    const CelestialBody* parent = body(celestialBody.orbitParentId);
    if (parent == nullptr || parent == &celestialBody || parent->massKg <= 0.0) return;

    const glm::dvec3 offset = parent->position - celestialBody.position;
    const double distanceSquared = std::max(glm::dot(offset, offset), 1.0);
    const double inverseDistance = 1.0 / std::sqrt(distanceSquared);
    const glm::dvec3 acceleration = offset * (kGravitationalConstant * parent->massKg * inverseDistance
        / distanceSquared);

    // Parent-only symplectic Euler deliberately avoids an unstable compressed-scale N-body
    // simulation. Moons/planets orbit their declared parent, while player/rigid-body gravity is
    // handled separately by the gameplay SOI model below.
    celestialBody.linearVelocity += acceleration * deltaSeconds;
    celestialBody.position += celestialBody.linearVelocity * deltaSeconds;
}

void CelestialSystem::updateSpin(CelestialBody& celestialBody, double deltaSeconds) noexcept {
    if (std::abs(celestialBody.spinRateRadPerSecond) <= 1.0e-15) return;
    const glm::dquat delta = glm::angleAxis(
        celestialBody.spinRateRadPerSecond * deltaSeconds,
        safeNormalize(celestialBody.spinAxis));
    celestialBody.orientation = glm::normalize(delta * celestialBody.orientation);
}

double CelestialSystem::stellarIrradianceAt(const CelestialBody& target) const noexcept {
    double irradiance = 0.0;
    for (const auto& source : bodies_) {
        if (source.type != CelestialBodyType::Star || source.luminosityWatts <= 0.0 || source.id == target.id) continue;
        const glm::dvec3 delta = source.position - target.position;
        const double distanceSquared = std::max(glm::dot(delta, delta), source.radiusMeters * source.radiusMeters);
        irradiance += source.luminosityWatts / (4.0 * kPi * distanceSquared);
    }
    return irradiance;
}

void CelestialSystem::updateClimateAndWeather(CelestialBody& celestialBody, double deltaSeconds) noexcept {
    if (celestialBody.type == CelestialBodyType::Star) return;

    const double irradiance = stellarIrradianceAt(celestialBody);
    if (irradiance > 0.0) {
        const double absorbed = irradiance * (1.0 - saturate(celestialBody.climate.bondAlbedo));
        const double equilibrium = std::pow(
            std::max(0.0, absorbed) / (4.0 * kStefanBoltzmann), 0.25)
            * std::max(0.1, celestialBody.climate.greenhouseFactor);
        const double response = std::max(1.0, celestialBody.climate.thermalResponseSeconds);
        const double blend = 1.0 - std::exp(-deltaSeconds / response);
        celestialBody.climate.meanTemperatureK += (equilibrium - celestialBody.climate.meanTemperatureK) * blend;
    }

    // Weather is a deterministic, ultra-cheap state model. It gives coherent slow variation
    // without simulating global CFD. Climate sets the envelope; local sampling adds small gusts.
    const double bodyPhase = static_cast<double>(celestialBody.id) * 1.731;
    const double slow = std::sin(simulationTime_ * 0.00045 + bodyPhase);
    const double faster = std::sin(simulationTime_ * 0.0017 + bodyPhase * 0.47);
    const double humidityTarget = saturate(0.48 + 0.22 * slow);
    const double cloudTarget = saturate(0.18 + 0.55 * humidityTarget + 0.18 * faster);
    const double stormTarget = saturate((cloudTarget - 0.62) * 2.4 + 0.15 * faster);
    const double weatherBlend = 1.0 - std::exp(-deltaSeconds / 120.0);
    celestialBody.weather.humidity += (humidityTarget - celestialBody.weather.humidity) * weatherBlend;
    celestialBody.weather.cloudCover += (cloudTarget - celestialBody.weather.cloudCover) * weatherBlend;
    celestialBody.weather.stormIntensity += (stormTarget - celestialBody.weather.stormIntensity) * weatherBlend;
    celestialBody.weather.precipitationRateMmPerHour = 18.0
        * celestialBody.weather.stormIntensity
        * saturate((celestialBody.weather.humidity - 0.60) / 0.40);
    celestialBody.weather.windMultiplier = 0.75 + 1.45 * celestialBody.weather.stormIntensity;
}

glm::dvec3 CelestialSystem::gravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept {
    glm::dvec3 total{};
    for (const auto& source : bodies_) {
        if (source.massKg <= 0.0) continue;
        const glm::dvec3 delta = source.position - worldPosition;
        const double minimumDistance = std::max(1.0, source.radiusMeters * 0.20);
        const double distanceSquared = std::max(glm::dot(delta, delta), minimumDistance * minimumDistance);
        const double inverseDistance = 1.0 / std::sqrt(distanceSquared);
        total += delta * (kGravitationalConstant * source.massKg * inverseDistance / distanceSquared);
    }
    return total;
}

double CelestialSystem::gameplayInfluenceWeight(
    const CelestialBody& celestialBody,
    const glm::dvec3& worldPosition) const noexcept {
    if (celestialBody.type == CelestialBodyType::Star || celestialBody.massKg <= 0.0) return 0.0;
    const double radius = std::max(0.1, celestialBody.radiusMeters);
    const double influence = celestialBody.gravityInfluenceRadiusMeters > radius
        ? celestialBody.gravityInfluenceRadiusMeters
        : radius * 4.0;
    const double distance = glm::length(worldPosition - celestialBody.position);
    if (distance <= radius) return 1.0;
    if (distance >= influence) return 0.0;
    return smooth01((influence - distance) / std::max(1.0e-6, influence - radius));
}

glm::dvec3 CelestialSystem::gameplayBodyGravity(
    const CelestialBody& celestialBody,
    const glm::dvec3& worldPosition) const noexcept {
    if (celestialBody.type == CelestialBodyType::Star || celestialBody.massKg <= 0.0) return {};
    const glm::dvec3 delta = celestialBody.position - worldPosition;
    const double distance = std::max(1.0e-6, glm::length(delta));
    const double radius = std::max(0.1, celestialBody.radiusMeters);
    const double surfaceGravity = celestialBody.gameplaySurfaceGravityMps2 > 0.0
        ? celestialBody.gameplaySurfaceGravityMps2
        : kGravitationalConstant * celestialBody.massKg / (radius * radius);
    const double weight = gameplayInfluenceWeight(celestialBody, worldPosition);
    return safeNormalize(delta, {0.0, -1.0, 0.0}) * surfaceGravity * weight;
}

glm::dvec3 CelestialSystem::gameplayGravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept {
    glm::dvec3 blendedPlanetGravity{};
    double totalWeight = 0.0;

    for (const auto& source : bodies_) {
        if (source.type == CelestialBodyType::Star) continue;
        const double influence = gameplayInfluenceWeight(source, worldPosition);
        if (influence <= 0.0) continue;

        // Squared weight makes ownership decisive near a planet while still producing a smooth
        // hand-over in overlapping SOIs. Normalize instead of summing so two nearby compressed
        // planets do not create an artificial gravity spike between them.
        const double blendWeight = influence * influence;
        blendedPlanetGravity += gameplayBodyGravity(source, worldPosition) * blendWeight;
        totalWeight += blendWeight;
    }

    if (totalWeight > kEpsilon) return blendedPlanetGravity / totalWeight;

    // In interplanetary space, planets stop exerting long-range control. Stars keep ordinary
    // inverse-square gravity so a solar system still has a coherent large-scale centre without
    // trapping the player in the primary planet's orbit.
    glm::dvec3 stellarGravity{};
    for (const auto& source : bodies_) {
        if (source.type != CelestialBodyType::Star || source.massKg <= 0.0) continue;
        const glm::dvec3 delta = source.position - worldPosition;
        const double distanceSquared = std::max(glm::dot(delta, delta), source.radiusMeters * source.radiusMeters);
        const double inverseDistance = 1.0 / std::sqrt(distanceSquared);
        stellarGravity += delta * (kGravitationalConstant * source.massKg * inverseDistance / distanceSquared);
    }
    return stellarGravity;
}

const CelestialBody* CelestialSystem::gameplayReferenceBodyAt(const glm::dvec3& worldPosition) const noexcept {
    const CelestialBody* best = nullptr;
    double bestWeight = 0.0;
    for (const auto& source : bodies_) {
        if (source.type == CelestialBodyType::Star) continue;
        const double weight = gameplayInfluenceWeight(source, worldPosition);
        if (weight > bestWeight) {
            bestWeight = weight;
            best = &source;
        }
    }
    return best;
}

const CelestialBody* CelestialSystem::dominantBodyAt(const glm::dvec3& worldPosition) const noexcept {
    const CelestialBody* best = nullptr;
    double bestAcceleration = -1.0;
    for (const auto& source : bodies_) {
        if (source.massKg <= 0.0) continue;
        const glm::dvec3 delta = source.position - worldPosition;
        const double distanceSquared = std::max(glm::dot(delta, delta), 1.0);
        const double acceleration = kGravitationalConstant * source.massKg / distanceSquared;
        if (acceleration > bestAcceleration) {
            bestAcceleration = acceleration;
            best = &source;
        }
    }
    return best;
}

double CelestialSystem::signedSurfaceDistance(
    const CelestialBody& celestialBody,
    const glm::dvec3& worldPosition) const noexcept {
    return glm::length(worldPosition - celestialBody.position) - celestialBody.radiusMeters;
}

glm::dvec3 CelestialSystem::magneticFieldAt(
    const CelestialBody& celestialBody,
    const glm::dvec3& worldPosition) const noexcept {
    if (!celestialBody.magneticField.enabled || celestialBody.magneticField.equatorialSurfaceFieldTesla <= 0.0) return {};
    const glm::dvec3 offset = worldPosition - celestialBody.position;
    const double radius = std::max(glm::length(offset), celestialBody.radiusMeters * 0.25);
    const glm::dvec3 rHat = safeNormalize(offset);
    const glm::dvec3 dipoleAxisWorld = safeNormalize(
        celestialBody.orientation * safeNormalize(celestialBody.magneticField.dipoleAxis));
    const double scale = celestialBody.magneticField.equatorialSurfaceFieldTesla
        * std::pow(celestialBody.radiusMeters / radius, 3.0);
    return scale * (3.0 * glm::dot(dipoleAxisWorld, rHat) * rHat - dipoleAxisWorld);
}

CelestialEnvironmentSample CelestialSystem::sampleEnvironment(const glm::dvec3& worldPosition) const noexcept {
    CelestialEnvironmentSample sample{};
    sample.gravityAcceleration = gravityAccelerationAt(worldPosition);

    const CelestialBody* environmentBody = nullptr;
    double bestSurfaceDistance = std::numeric_limits<double>::infinity();
    for (const auto& candidate : bodies_) {
        if (candidate.type == CelestialBodyType::Star) continue;
        const double altitude = signedSurfaceDistance(candidate, worldPosition);
        const double influenceHeight = std::max(candidate.atmosphere.heightMeters, candidate.radiusMeters * 0.20);
        if (altitude <= influenceHeight && std::abs(altitude) < bestSurfaceDistance) {
            environmentBody = &candidate;
            bestSurfaceDistance = std::abs(altitude);
        }
    }
    if (environmentBody == nullptr) environmentBody = gameplayReferenceBodyAt(worldPosition);
    if (environmentBody == nullptr) {
        sample.temperatureK = 2.725;
        sample.gravityAcceleration = gameplayGravityAccelerationAt(worldPosition);
        return sample;
    }

    sample.bodyId = environmentBody->id;
    sample.altitudeMeters = signedSurfaceDistance(*environmentBody, worldPosition);
    sample.gravityAcceleration = gameplayGravityAccelerationAt(worldPosition);
    sample.magneticFieldTesla = magneticFieldAt(*environmentBody, worldPosition);
    sample.humidity = environmentBody->weather.humidity;
    sample.cloudCover = environmentBody->weather.cloudCover;
    sample.precipitationRateMmPerHour = environmentBody->weather.precipitationRateMmPerHour;

    const auto& atmosphere = environmentBody->atmosphere;
    if (!atmosphere.enabled || sample.altitudeMeters > atmosphere.heightMeters) {
        sample.temperatureK = 2.725;
        return sample;
    }

    const double altitude = std::max(0.0, sample.altitudeMeters);
    sample.temperatureK = std::max(
        90.0,
        environmentBody->climate.meanTemperatureK - std::max(0.0, atmosphere.lapseRateKPerM) * altitude);
    sample.pressurePa = std::max(0.0, atmosphere.surfacePressurePa)
        * std::exp(-altitude / std::max(1.0, atmosphere.scaleHeightMeters));
    const double specificGasConstant = kUniversalGasConstant / std::max(1.0e-6, atmosphere.molarMassKgPerMol);
    sample.densityKgPerM3 = sample.pressurePa / (specificGasConstant * sample.temperatureK);

    const glm::dvec3 outward = safeNormalize(worldPosition - environmentBody->position);
    glm::dvec3 wind = environmentBody->orientation * atmosphere.prevailingWind;
    wind -= outward * glm::dot(wind, outward);
    const glm::dvec3 reference = std::abs(outward.y) < 0.9
        ? glm::dvec3{0.0, 1.0, 0.0}
        : glm::dvec3{1.0, 0.0, 0.0};
    const glm::dvec3 tangent = safeNormalize(glm::cross(reference, outward), {1.0, 0.0, 0.0});
    const double gust = std::sin(simulationTime_ * 0.11 + glm::dot(worldPosition, tangent) * 0.006 + environmentBody->id)
        * (1.2 + 5.0 * environmentBody->weather.stormIntensity);
    sample.windVelocity = (wind + tangent * gust) * environmentBody->weather.windMultiplier;
    return sample;
}

} // namespace vf
