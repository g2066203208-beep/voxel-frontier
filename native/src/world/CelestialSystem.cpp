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

[[nodiscard]] double surfaceGravityOf(const CelestialBody& body) noexcept {
    const double radius = std::max(0.1, body.radiusMeters);
    if (body.gameplaySurfaceGravityMps2 > 0.0) return body.gameplaySurfaceGravityMps2;
    return CelestialSystem::kGravitationalConstant * body.massKg / (radius * radius);
}

[[nodiscard]] glm::dvec3 angularVelocityOf(const CelestialBody& body) noexcept {
    return safeNormalize(body.spinAxis) * body.spinRateRadPerSecond;
}

[[nodiscard]] glm::dvec3 standardToGameAxes(const glm::dvec3& v) noexcept {
    // Classical orbital formulae use Z as the reference-plane normal. Voxel Frontier uses Y-up.
    return {v.x, v.z, v.y};
}

} // namespace

OrbitalState keplerianState(
    const KeplerianElements& elements,
    double gravitationalParameterM3PerS2) noexcept {
    OrbitalState result{};
    const double mu = std::max(1.0e-12, gravitationalParameterM3PerS2);
    const double a = std::max(1.0, elements.semiMajorAxisMeters);
    const double e = std::clamp(elements.eccentricity, 0.0, 0.999999);
    const double M = std::remainder(elements.meanAnomalyRadians, 2.0 * kPi);

    // Newton solve of Kepler's equation M = E - e sin(E).
    double E = e < 0.8 ? M : (M >= 0.0 ? kPi : -kPi);
    for (int i = 0; i < 16; ++i) {
        const double f = E - e * std::sin(E) - M;
        const double fp = std::max(1.0e-10, 1.0 - e * std::cos(E));
        const double dE = f / fp;
        E -= dE;
        if (std::abs(dE) < 1.0e-13) break;
    }

    const double root = std::sqrt(std::max(0.0, 1.0 - e * e));
    const double denom = std::max(1.0e-12, 1.0 - e * std::cos(E));
    const double n = std::sqrt(mu / (a * a * a));
    const glm::dvec3 rPerifocal{a * (std::cos(E) - e), a * root * std::sin(E), 0.0};
    const glm::dvec3 vPerifocal{
        -a * n * std::sin(E) / denom,
        a * n * root * std::cos(E) / denom,
        0.0};

    const double O = elements.longitudeAscendingNodeRadians;
    const double i = elements.inclinationRadians;
    const double w = elements.argumentPeriapsisRadians;
    const double cO = std::cos(O), sO = std::sin(O);
    const double ci = std::cos(i), si = std::sin(i);
    const double cw = std::cos(w), sw = std::sin(w);

    // Q = R3(Omega) R1(i) R3(omega), standard Z-normal celestial frame.
    const glm::dmat3 Q{
        {cO * cw - sO * sw * ci, sO * cw + cO * sw * ci, sw * si},
        {-cO * sw - sO * cw * ci, -sO * sw + cO * cw * ci, cw * si},
        {sO * si, -cO * si, ci},
    };
    result.position = standardToGameAxes(Q * rPerifocal);
    result.velocity = standardToGameAxes(Q * vPerifocal);
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
            bodyValue.gravityFalloffStartRadiusMeters * 1.001,
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

    // R21 Newtonian N-body propagation. JPL's ephemeris documentation stresses that real bodies
    // follow perturbed trajectories, not immutable ellipses. A kick-drift-kick velocity-Verlet
    // integrator preserves bound orbital energy far better than the old sequential parent-only
    // Euler pull while remaining cheap for the handful of gameplay-scale celestial bodies.
    double remaining = std::min(deltaSeconds, 86400.0 * 4.0);
    constexpr double maxSubstep = 60.0;
    std::vector<glm::dvec3> acceleration(bodies_.size());

    auto evaluateAccelerations = [&]() {
        std::fill(acceleration.begin(), acceleration.end(), glm::dvec3{});
        for (std::size_t i = 0; i < bodies_.size(); ++i) {
            for (std::size_t j = i + 1; j < bodies_.size(); ++j) {
                const glm::dvec3 delta = bodies_[j].position - bodies_[i].position;
                const double r2 = std::max(glm::dot(delta, delta), 1.0);
                const double invR = 1.0 / std::sqrt(r2);
                const double invR3 = invR / r2;
                const glm::dvec3 directionTerm = delta * invR3;
                acceleration[i] += directionTerm * (kGravitationalConstant * bodies_[j].massKg);
                acceleration[j] -= directionTerm * (kGravitationalConstant * bodies_[i].massKg);
            }
        }
    };

    while (remaining > 1.0e-12) {
        const double h = std::min(remaining, maxSubstep);
        evaluateAccelerations();
        for (std::size_t i = 0; i < bodies_.size(); ++i) {
            bodies_[i].linearVelocity += acceleration[i] * (0.5 * h);
            bodies_[i].position += bodies_[i].linearVelocity * h;
        }
        evaluateAccelerations();
        for (std::size_t i = 0; i < bodies_.size(); ++i) {
            bodies_[i].linearVelocity += acceleration[i] * (0.5 * h);
            updateSpin(bodies_[i], h);
            updateClimateAndWeather(bodies_[i], h);
        }
        simulationTime_ += h;
        remaining -= h;
    }
}

void CelestialSystem::updateOrbit(CelestialBody& celestialBody, double deltaSeconds) {
    if (celestialBody.orbitParentId == 0U) return;
    const CelestialBody* parent = body(celestialBody.orbitParentId);
    if (parent == nullptr || parent == &celestialBody || parent->massKg <= 0.0) return;

    const glm::dvec3 offset = parent->position - celestialBody.position;
    const double distanceSquared = std::max(glm::dot(offset, offset), 1.0);
    const double inverseDistance = 1.0 / std::sqrt(distanceSquared);
    const glm::dvec3 acceleration = offset
        * (kGravitationalConstant * parent->massKg * inverseDistance / distanceSquared);

    // Celestial motion lives in the high-precision inertial simulation. Nearby gameplay physics
    // runs in planet-centered physics spaces and therefore does not need to carry this large
    // orbital velocity through every contact solve.
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

double CelestialSystem::gravityCutoffRadius(const CelestialBody& celestialBody) const noexcept {
    if (celestialBody.type == CelestialBodyType::Star) {
        return std::numeric_limits<double>::infinity();
    }

    const double radius = std::max(0.1, celestialBody.radiusMeters);
    const double start = std::max(radius, celestialBody.gravityFalloffStartRadiusMeters);
    if (celestialBody.gravityInfluenceRadiusMeters > start) {
        return celestialBody.gravityInfluenceRadiusMeters;
    }

    const double gSurface = surfaceGravityOf(celestialBody);
    const double gAtStart = gSurface * (radius * radius) / (start * start);
    const double cutoffG = std::max(1.0e-4, celestialBody.gravityCutoffAccelerationMps2);
    if (gAtStart <= cutoffG) return start * 1.001;

    return start * std::pow(
        gAtStart / cutoffG,
        1.0 / std::max(2.0, celestialBody.gravityFalloffPower));
}

double CelestialSystem::gravityMagnitudeFromBody(
    const CelestialBody& celestialBody,
    const glm::dvec3& worldPosition) const noexcept {
    if (celestialBody.massKg <= 0.0) return 0.0;

    const double radius = std::max(0.1, celestialBody.radiusMeters);
    const double distance = glm::length(worldPosition - celestialBody.position);

    if (celestialBody.type == CelestialBodyType::Star) {
        const double r = std::max(distance, radius * 0.20);
        return kGravitationalConstant * celestialBody.massKg / (r * r);
    }

    const double gSurface = surfaceGravityOf(celestialBody);
    if (distance < radius) {
        // A linear interior field is stable for caves/cores and avoids a singularity at the center.
        return gSurface * std::max(0.01, distance / radius);
    }

    const double start = std::max(radius, celestialBody.gravityFalloffStartRadiusMeters);
    const double cutoff = gravityCutoffRadius(celestialBody);
    if (distance >= cutoff) return 0.0;

    double magnitude = 0.0;
    if (distance <= start) {
        const double ratio = radius / std::max(distance, radius);
        magnitude = gSurface * ratio * ratio;
    } else {
        const double gAtStart = gSurface * (radius * radius) / (start * start);
        magnitude = gAtStart * std::pow(
            start / distance,
            std::max(2.0, celestialBody.gravityFalloffPower));
    }

    // Do not snap from a measurable acceleration to exactly zero in one centimetre. The final 15%
    // of the authored gravity well is smoothly faded to zero; this preserves stable transitions
    // while still giving an Astroneer/Space-Engineers-like finite zero-g region.
    const double fadeStart = start + (cutoff - start) * 0.85;
    if (cutoff > fadeStart && distance > fadeStart) {
        magnitude *= smooth01((cutoff - distance) / (cutoff - fadeStart));
    }
    return std::max(0.0, magnitude);
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
            // Keep the frame body's own radial gravity. Its center is the origin of this local
            // physics frame, so subtracting its center field would be meaningless.
            relative += gravityFromSource(source, worldPosition);
            continue;
        }

        // Remove only the external source's common-mode acceleration at the frame origin. The
        // remaining difference is the real tidal acceleration experienced inside the local frame.
        relative += gravityFromSource(source, worldPosition) - gravityFromSource(source, frameBody->position);
    }
    return relative;
}

glm::dvec3 CelestialSystem::physicalGravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept {
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
        const double defaultBubble = std::max(
            gravityCutoffRadius(source) * 1.20,
            atmosphereTop * 1.35);
        const double bubble = source.physicsBubbleRadiusMeters > source.radiusMeters
            ? source.physicsBubbleRadiusMeters
            : defaultBubble;
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
    const glm::dvec3 reference = std::abs(outward.y) < 0.9
        ? glm::dvec3{0.0, 1.0, 0.0}
        : glm::dvec3{1.0, 0.0, 0.0};
    const glm::dvec3 tangent = safeNormalize(glm::cross(reference, outward), {1.0, 0.0, 0.0});
    const double gust = std::sin(
        simulationTime_ * 0.11 + glm::dot(worldPosition, tangent) * 0.006 + environmentBody->id)
        * (1.2 + 5.0 * environmentBody->weather.stormIntensity);
    localWind = (localWind + tangent * gust) * environmentBody->weather.windMultiplier;

    // Atmosphere co-moves with its planet before local weather is added. Global/inertial callers
    // therefore see correct relative air speed; a planet-centered physics proxy simply has zero
    // translational velocity and gets the same formula for free.
    sample.windVelocity = environmentBody->linearVelocity
        + glm::cross(angularVelocityOf(*environmentBody), worldPosition - environmentBody->position)
        + localWind;
    return sample;
}

} // namespace vf
