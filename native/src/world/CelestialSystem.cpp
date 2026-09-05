#include "vf/world/CelestialSystem.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <utility>
#include <vector>

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

[[nodiscard]] glm::dvec3 angularVelocityOf(const CelestialBody& body) noexcept {
    return safeNormalize(body.spinAxis) * body.spinRateRadPerSecond;
}

[[nodiscard]] glm::dvec3 standardToGameAxes(const glm::dvec3& value) noexcept {
    // Classical orbital formulae use Z as the reference-plane normal. Voxel Frontier is Y-up.
    return {value.x, value.z, value.y};
}

} // namespace

OrbitalState keplerianState(
    const KeplerianElements& elements,
    double gravitationalParameterM3PerS2) noexcept {
    OrbitalState result{};
    const double mu = std::max(1.0e-12, gravitationalParameterM3PerS2);
    const double a = std::max(1.0, elements.semiMajorAxisMeters);
    const double e = std::clamp(elements.eccentricity, 0.0, 0.999999);
    const double meanAnomaly = std::remainder(elements.meanAnomalyRadians, 2.0 * kPi);

    // Solve Kepler's equation M = E - e sin(E) for eccentric anomaly E.
    double eccentricAnomaly = e < 0.8 ? meanAnomaly : (meanAnomaly >= 0.0 ? kPi : -kPi);
    for (int iteration = 0; iteration < 16; ++iteration) {
        const double residual = eccentricAnomaly - e * std::sin(eccentricAnomaly) - meanAnomaly;
        const double derivative = std::max(1.0e-10, 1.0 - e * std::cos(eccentricAnomaly));
        const double delta = residual / derivative;
        eccentricAnomaly -= delta;
        if (std::abs(delta) < 1.0e-13) break;
    }

    const double eccentricityRoot = std::sqrt(std::max(0.0, 1.0 - e * e));
    const double denominator = std::max(1.0e-12, 1.0 - e * std::cos(eccentricAnomaly));
    const double meanMotion = std::sqrt(mu / (a * a * a));
    const glm::dvec3 perifocalPosition{
        a * (std::cos(eccentricAnomaly) - e),
        a * eccentricityRoot * std::sin(eccentricAnomaly),
        0.0};
    const glm::dvec3 perifocalVelocity{
        -a * meanMotion * std::sin(eccentricAnomaly) / denominator,
        a * meanMotion * eccentricityRoot * std::cos(eccentricAnomaly) / denominator,
        0.0};

    const double ascendingNode = elements.longitudeAscendingNodeRadians;
    const double inclination = elements.inclinationRadians;
    const double periapsis = elements.argumentPeriapsisRadians;
    const double cO = std::cos(ascendingNode);
    const double sO = std::sin(ascendingNode);
    const double ci = std::cos(inclination);
    const double si = std::sin(inclination);
    const double cw = std::cos(periapsis);
    const double sw = std::sin(periapsis);

    // Q = R3(Omega) R1(i) R3(omega). GLM matrices are column-major.
    const glm::dmat3 perifocalToInertial{
        {cO * cw - sO * sw * ci, sO * cw + cO * sw * ci, sw * si},
        {-cO * sw - sO * cw * ci, -sO * sw + cO * cw * ci, cw * si},
        {sO * si, -cO * si, ci},
    };

    result.position = standardToGameAxes(perifocalToInertial * perifocalPosition);
    result.velocity = standardToGameAxes(perifocalToInertial * perifocalVelocity);
    return result;
}

std::uint32_t CelestialSystem::addBody(CelestialBody bodyValue) {
    if (bodyValue.id == 0U) bodyValue.id = nextBodyId_++;
    else nextBodyId_ = std::max(nextBodyId_, bodyValue.id + 1U);

    bodyValue.radiusMeters = std::max(0.1, bodyValue.radiusMeters);
    bodyValue.massKg = std::max(0.0, bodyValue.massKg);
    bodyValue.orientation = glm::normalize(bodyValue.orientation);
    bodyValue.spinAxis = safeNormalize(bodyValue.spinAxis);
    bodyValue.gameplaySurfaceGravityMps2 = std::max(0.0, bodyValue.gameplaySurfaceGravityMps2);
    bodyValue.gravityFalloffPower = std::max(2.0, bodyValue.gravityFalloffPower);
    bodyValue.gravityCutoffAccelerationMps2 = std::max(1.0e-4, bodyValue.gravityCutoffAccelerationMps2);
    bodyValue.atmosphere.heightMeters = std::max(0.0, bodyValue.atmosphere.heightMeters);
    bodyValue.atmosphere.scaleHeightMeters = std::max(1.0, bodyValue.atmosphere.scaleHeightMeters);

    const double atmosphereTop = bodyValue.radiusMeters
        + (bodyValue.atmosphere.enabled ? bodyValue.atmosphere.heightMeters : 0.0);
    if (bodyValue.gravityFalloffStartRadiusMeters <= bodyValue.radiusMeters) {
        bodyValue.gravityFalloffStartRadiusMeters = std::max(bodyValue.radiusMeters, atmosphereTop);
    }
    if (bodyValue.gravityInfluenceRadiusMeters > 0.0) {
        bodyValue.gravityInfluenceRadiusMeters = std::max(
            bodyValue.radiusMeters * 1.001,
            bodyValue.gravityInfluenceRadiusMeters);
    }
    if (bodyValue.physicsBubbleRadiusMeters > 0.0) {
        bodyValue.physicsBubbleRadiusMeters = std::max(
            bodyValue.radiusMeters * 1.05,
            bodyValue.physicsBubbleRadiusMeters);
    }

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
    if (!std::isfinite(deltaSeconds) || deltaSeconds <= 0.0 || bodies_.empty()) return;

    // The caller (AstroTime/CelestialSimulationClock) supplies bounded fixed substeps. Keep an
    // additional 60 s safety cap here so a direct caller cannot accidentally integrate a huge dt.
    const double dt = std::min(deltaSeconds, 60.0);
    std::vector<glm::dvec3> acceleration(bodies_.size());

    const auto evaluateAccelerations = [&]() {
        std::fill(acceleration.begin(), acceleration.end(), glm::dvec3{});
        for (std::size_t i = 0; i < bodies_.size(); ++i) {
            for (std::size_t j = i + 1; j < bodies_.size(); ++j) {
                const glm::dvec3 separation = bodies_[j].position - bodies_[i].position;
                const double distanceSquared = std::max(glm::dot(separation, separation), 1.0);
                const double inverseDistance = 1.0 / std::sqrt(distanceSquared);
                const double inverseDistanceCubed = inverseDistance / distanceSquared;
                const glm::dvec3 radialTerm = separation * inverseDistanceCubed;
                acceleration[i] += radialTerm * (kGravitationalConstant * bodies_[j].massKg);
                acceleration[j] -= radialTerm * (kGravitationalConstant * bodies_[i].massKg);
            }
        }
    };

    evaluateAccelerations();
    for (std::size_t i = 0; i < bodies_.size(); ++i) {
        bodies_[i].linearVelocity += acceleration[i] * (0.5 * dt);
        bodies_[i].position += bodies_[i].linearVelocity * dt;
    }

    evaluateAccelerations();
    for (std::size_t i = 0; i < bodies_.size(); ++i) {
        bodies_[i].linearVelocity += acceleration[i] * (0.5 * dt);
        updateSpin(bodies_[i], dt);
        updateClimateAndWeather(bodies_[i], dt);
    }
    simulationTime_ += dt;
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

    // Keep only a slowly varying global radiative-equilibrium diagnostic here. Local temperature,
    // humidity, cloud, precipitation and wind belong to PlanetClimateGrid, where they are forced by
    // local solar zenith angle, heat capacity, pressure gradients and Coriolis acceleration. R24
    // intentionally removes the old sin(simulationTime) weather oscillator.
    const double irradiance = stellarIrradianceAt(celestialBody);
    if (irradiance <= 0.0) return;
    const double absorbed = irradiance * (1.0 - saturate(celestialBody.climate.bondAlbedo));
    const double equilibrium = std::pow(
        std::max(0.0, absorbed) / (4.0 * kStefanBoltzmann), 0.25)
        * std::max(0.1, celestialBody.climate.greenhouseFactor);
    const double response = std::max(1.0, celestialBody.climate.thermalResponseSeconds);
    const double blend = 1.0 - std::exp(-deltaSeconds / response);
    celestialBody.climate.meanTemperatureK += (equilibrium - celestialBody.climate.meanTemperatureK) * blend;
}

double CelestialSystem::gravityCutoffRadius(const CelestialBody& celestialBody) const noexcept {
    // Compatibility query only. R24 no longer cuts off physical gravity. Legacy authored
    // gravityInfluenceRadiusMeters may still be used as a reference-frame/streaming hint.
    if (celestialBody.gravityInfluenceRadiusMeters > celestialBody.radiusMeters)
        return celestialBody.gravityInfluenceRadiusMeters;
    return std::numeric_limits<double>::infinity();
}

double CelestialSystem::gravityMagnitudeFromBody(
    const CelestialBody& celestialBody,
    const glm::dvec3& worldPosition) const noexcept {
    if (celestialBody.massKg <= 0.0) return 0.0;

    const double radius = std::max(0.1, celestialBody.radiusMeters);
    const double distance = glm::length(worldPosition - celestialBody.position);
    if (distance <= 1.0e-12) return 0.0;

    if (distance < radius) {
        // Uniform-density sphere interior: g(r)=GM r/R^3. It is finite and reaches zero at center.
        return kGravitationalConstant * celestialBody.massKg * distance
            / (radius * radius * radius);
    }
    return kGravitationalConstant * celestialBody.massKg / (distance * distance);
}

glm::dvec3 CelestialSystem::gravityFromSource(
    const CelestialBody& celestialBody,
    const glm::dvec3& worldPosition) const noexcept {
    const double magnitude = gravityMagnitudeFromBody(celestialBody, worldPosition);
    if (magnitude <= 0.0) return {};
    return safeNormalize(celestialBody.position - worldPosition, {0.0, -1.0, 0.0}) * magnitude;
}

glm::dvec3 CelestialSystem::gameplayBodyGravity(
    const CelestialBody& celestialBody,
    const glm::dvec3& worldPosition) const noexcept {
    return gravityFromSource(celestialBody, worldPosition);
}

glm::dvec3 CelestialSystem::gameplayGravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept {
    glm::dvec3 total{};
    for (const auto& source : bodies_) total += gravityFromSource(source, worldPosition);
    return total;
}

glm::dvec3 CelestialSystem::gravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept {
    return gameplayGravityAccelerationAt(worldPosition);
}

glm::dvec3 CelestialSystem::gravityAccelerationRelativeTo(
    std::uint32_t frameBodyId,
    const glm::dvec3& worldPosition) const noexcept {
    const CelestialBody* frameBody = body(frameBodyId);
    if (frameBody == nullptr) return gravityAccelerationAt(worldPosition);

    glm::dvec3 relative{};
    for (const auto& source : bodies_) {
        if (source.id == frameBodyId) {
            relative += gravityFromSource(source, worldPosition);
            continue;
        }
        // Remove external common-mode acceleration at the frame origin, retaining true tides.
        relative += gravityFromSource(source, worldPosition)
            - gravityFromSource(source, frameBody->position);
    }
    return relative;
}

glm::dvec3 CelestialSystem::physicalGravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept {
    glm::dvec3 total{};
    for (const auto& source : bodies_) total += gravityFromSource(source, worldPosition);
    return total;
}

bool CelestialSystem::insideAtmosphere(
    const CelestialBody& celestialBody,
    const glm::dvec3& worldPosition) const noexcept {
    if (!celestialBody.atmosphere.enabled || celestialBody.atmosphere.heightMeters <= 0.0) return false;
    return glm::length(worldPosition - celestialBody.position)
        <= celestialBody.radiusMeters + celestialBody.atmosphere.heightMeters;
}

const CelestialBody* CelestialSystem::gravityReferenceBodyAt(const glm::dvec3& worldPosition) const noexcept {
    const CelestialBody* best = nullptr;
    double bestGravity = 0.0;
    for (const auto& source : bodies_) {
        if (source.type == CelestialBodyType::Star) continue;
        const double gravity = gravityMagnitudeFromBody(source, worldPosition);
        if (gravity > bestGravity) {
            bestGravity = gravity;
            best = &source;
        }
    }
    return best;
}

const CelestialBody* CelestialSystem::physicsReferenceBodyAt(const glm::dvec3& worldPosition) const noexcept {
    const CelestialBody* best = nullptr;
    double bestNormalizedDistance = std::numeric_limits<double>::infinity();

    for (const auto& source : bodies_) {
        if (source.type == CelestialBodyType::Star) continue;
        const double atmosphereTop = source.radiusMeters
            + (source.atmosphere.enabled ? source.atmosphere.heightMeters : 0.0);
        double bubble = source.physicsBubbleRadiusMeters;
        if (bubble <= source.radiusMeters && source.gravityInfluenceRadiusMeters > source.radiusMeters)
            bubble = source.gravityInfluenceRadiusMeters;
        if (bubble <= source.radiusMeters) bubble = atmosphereTop * 1.35;
        bubble = std::max(bubble, source.radiusMeters * 1.05);

        const double distance = glm::length(worldPosition - source.position);
        if (distance > bubble) continue;
        const double normalized = distance / std::max(1.0, bubble);
        if (normalized < bestNormalizedDistance) {
            bestNormalizedDistance = normalized;
            best = &source;
        }
    }
    return best;
}

const CelestialBody* CelestialSystem::gameplayReferenceBodyAt(const glm::dvec3& worldPosition) const noexcept {
    return physicsReferenceBodyAt(worldPosition);
}

const CelestialBody* CelestialSystem::dominantBodyAt(const glm::dvec3& worldPosition) const noexcept {
    const CelestialBody* best = nullptr;
    double bestAcceleration = -1.0;
    for (const auto& source : bodies_) {
        if (source.massKg <= 0.0) continue;
        const double acceleration = gravityMagnitudeFromBody(source, worldPosition);
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
    if (!celestialBody.magneticField.enabled
        || celestialBody.magneticField.equatorialSurfaceFieldTesla <= 0.0) return {};

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
    double bestAltitude = std::numeric_limits<double>::infinity();
    for (const auto& candidate : bodies_) {
        if (candidate.type == CelestialBodyType::Star || !insideAtmosphere(candidate, worldPosition)) continue;
        const double altitude = signedSurfaceDistance(candidate, worldPosition);
        if (altitude < bestAltitude) {
            bestAltitude = altitude;
            environmentBody = &candidate;
        }
    }

    if (environmentBody == nullptr) environmentBody = gravityReferenceBodyAt(worldPosition);
    if (environmentBody == nullptr) {
        sample.temperatureK = 2.725;
        return sample;
    }

    sample.bodyId = environmentBody->id;
    sample.altitudeMeters = signedSurfaceDistance(*environmentBody, worldPosition);
    sample.magneticFieldTesla = magneticFieldAt(*environmentBody, worldPosition);
    sample.humidity = environmentBody->weather.humidity;
    sample.cloudCover = environmentBody->weather.cloudCover;
    sample.precipitationRateMmPerHour = environmentBody->weather.precipitationRateMmPerHour;

    const auto& atmosphere = environmentBody->atmosphere;
    if (!insideAtmosphere(*environmentBody, worldPosition)) {
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
    glm::dvec3 localWind = environmentBody->orientation * atmosphere.prevailingWind;
    localWind -= outward * glm::dot(localWind, outward);
    localWind *= environmentBody->weather.windMultiplier;

    // Atmosphere co-moves with its planet. PlanetClimateGrid may replace localWind with a solved
    // body-local climate sample in the local PhysicsEnvironment; no synthetic sine gust is added.
    sample.windVelocity = environmentBody->linearVelocity
        + glm::cross(angularVelocityOf(*environmentBody), worldPosition - environmentBody->position)
        + localWind;
    return sample;
}

} // namespace vf
