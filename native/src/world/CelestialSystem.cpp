#include "vf/world/CelestialSystem.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <string>
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

[[nodiscard]] glm::dvec3 gameToStandardAxes(const glm::dvec3& value) noexcept {
    // standardToGameAxes swaps Y/Z; it is its own inverse.
    return {value.x, value.z, value.y};
}

[[nodiscard]] double normalizedAngle(double value) noexcept {
    value = std::remainder(value, 2.0 * kPi);
    return value < 0.0 ? value + 2.0 * kPi : value;
}

[[nodiscard]] double orientedAngle(
    const glm::dvec3& from,
    const glm::dvec3& to,
    const glm::dvec3& normal) noexcept {
    const glm::dvec3 a = safeNormalize(from, {1.0, 0.0, 0.0});
    const glm::dvec3 b = safeNormalize(to, a);
    const glm::dvec3 n = safeNormalize(normal, {0.0, 0.0, 1.0});
    return normalizedAngle(std::atan2(glm::dot(n, glm::cross(a, b)), glm::dot(a, b)));
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

    const glm::dmat3 perifocalToInertial{
        {cO * cw - sO * sw * ci, sO * cw + cO * sw * ci, sw * si},
        {-cO * sw - sO * cw * ci, -sO * sw + cO * cw * ci, cw * si},
        {sO * si, -cO * si, ci},
    };

    result.position = standardToGameAxes(perifocalToInertial * perifocalPosition);
    result.velocity = standardToGameAxes(perifocalToInertial * perifocalVelocity);
    return result;
}

bool keplerianElementsFromState(
    const OrbitalState& state,
    double gravitationalParameterM3PerS2,
    KeplerianElements& elements) noexcept {
    const double mu = gravitationalParameterM3PerS2;
    if (!std::isfinite(mu) || mu <= 0.0) return false;

    const glm::dvec3 r = gameToStandardAxes(state.position);
    const glm::dvec3 v = gameToStandardAxes(state.velocity);
    const double radius = glm::length(r);
    const glm::dvec3 h = glm::cross(r, v);
    const double hLength = glm::length(h);
    if (!std::isfinite(radius) || radius <= 1.0e-6 || hLength <= 1.0e-9) return false;

    const double speedSquared = glm::dot(v, v);
    const double specificEnergy = 0.5 * speedSquared - mu / radius;
    if (!std::isfinite(specificEnergy) || specificEnergy >= -1.0e-18) return false;
    const double semiMajorAxis = -mu / (2.0 * specificEnergy);
    if (!std::isfinite(semiMajorAxis) || semiMajorAxis <= 1.0) return false;

    const glm::dvec3 eccentricityVector = glm::cross(v, h) / mu - r / radius;
    const double eccentricity = glm::length(eccentricityVector);
    if (!std::isfinite(eccentricity) || eccentricity >= 0.999999) return false;

    const glm::dvec3 k{0.0, 0.0, 1.0};
    const glm::dvec3 node = glm::cross(k, h);
    const double nodeLength = glm::length(node);
    const double inclination = std::acos(std::clamp(h.z / hLength, -1.0, 1.0));
    const double ascendingNode = nodeLength > 1.0e-10
        ? normalizedAngle(std::atan2(node.y, node.x)) : 0.0;

    double periapsis = 0.0;
    double trueAnomaly = 0.0;
    if (eccentricity > 1.0e-10) {
        periapsis = nodeLength > 1.0e-10
            ? orientedAngle(node, eccentricityVector, h)
            : normalizedAngle(std::atan2(eccentricityVector.y, eccentricityVector.x));
        trueAnomaly = orientedAngle(eccentricityVector, r, h);
    } else if (nodeLength > 1.0e-10) {
        // Circular inclined orbit: argument of latitude is the only observable in-plane angle.
        periapsis = 0.0;
        trueAnomaly = orientedAngle(node, r, h);
    } else {
        // Circular equatorial orbit: true longitude becomes mean anomaly directly.
        periapsis = 0.0;
        trueAnomaly = normalizedAngle(std::atan2(r.y, r.x));
    }

    const double halfTrue = 0.5 * trueAnomaly;
    const double eccentricAnomaly = 2.0 * std::atan2(
        std::sqrt(std::max(0.0, 1.0 - eccentricity)) * std::sin(halfTrue),
        std::sqrt(1.0 + eccentricity) * std::cos(halfTrue));
    const double meanAnomaly = eccentricAnomaly
        - eccentricity * std::sin(eccentricAnomaly);

    elements.semiMajorAxisMeters = semiMajorAxis;
    elements.eccentricity = eccentricity;
    elements.inclinationRadians = inclination;
    elements.longitudeAscendingNodeRadians = ascendingNode;
    elements.argumentPeriapsisRadians = normalizedAngle(periapsis);
    elements.meanAnomalyRadians = normalizedAngle(meanAnomaly);
    return true;
}

std::uint32_t CelestialSystem::addBody(CelestialBody bodyValue) {
    if (bodyValue.id == 0U) bodyValue.id = nextBodyId_++;
    else nextBodyId_ = std::max(nextBodyId_, bodyValue.id + 1U);

    // Reference-frame ids are runtime handles, never authored/copy-propagated content.
    bodyValue.referenceFrameId = 0U;
    bodyValue.radiusMeters = std::max(0.1, bodyValue.radiusMeters);
    bodyValue.massKg = std::max(0.0, bodyValue.massKg);
    bodyValue.orientation = glm::normalize(bodyValue.orientation);
    bodyValue.spinAxis = safeNormalize(bodyValue.spinAxis);
    bodyValue.spinEpochOrientation = bodyValue.orientation;
    bodyValue.spinEpochSeconds = simulationTime();
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
    syncReferenceFrames();
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

bool CelestialSystem::setAnalyticOrbitFromCurrentState(std::uint32_t bodyId) noexcept {
    CelestialBody* child = body(bodyId);
    if (child == nullptr || child->orbitParentId == 0U || child->orbitParentId == child->id)
        return false;
    const CelestialBody* parent = body(child->orbitParentId);
    if (parent == nullptr) return false;

    KeplerianElements elements{};
    const double mu = kGravitationalConstant * std::max(0.0, parent->massKg + child->massKg);
    const OrbitalState relative{
        child->position - parent->position,
        child->linearVelocity - parent->linearVelocity,
    };
    if (!keplerianElementsFromState(relative, mu, elements)) return false;

    child->analyticOrbit = elements;
    child->analyticOrbitEpochSeconds = simulationTime();
    child->orbitMode = CelestialOrbitMode::AnalyticKepler;
    return true;
}

void CelestialSystem::setDynamicNBody(std::uint32_t bodyId) noexcept {
    CelestialBody* value = body(bodyId);
    if (value == nullptr) return;
    value->orbitMode = CelestialOrbitMode::DynamicNBody;
}

void CelestialSystem::integrateOrbitalSubstep(double deltaSeconds) {
    if (bodies_.empty() || deltaSeconds <= 0.0) return;
    ++lastStepStats_.dynamicSubsteps;

    std::vector<glm::dvec3> acceleration(bodies_.size());
    const auto evaluateAccelerations = [&]() {
        std::fill(acceleration.begin(), acceleration.end(), glm::dvec3{});
        for (std::size_t i = 0; i < bodies_.size(); ++i) {
            if (bodies_[i].orbitMode != CelestialOrbitMode::DynamicNBody) continue;
            for (std::size_t j = i + 1; j < bodies_.size(); ++j) {
                if (bodies_[j].orbitMode != CelestialOrbitMode::DynamicNBody) continue;
                const glm::dvec3 separation = bodies_[j].position - bodies_[i].position;
                const double distanceSquared = std::max(glm::dot(separation, separation), 1.0);
                const double inverseDistance = 1.0 / std::sqrt(distanceSquared);
                const double inverseDistanceCubed = inverseDistance / distanceSquared;
                const glm::dvec3 radialTerm = separation * inverseDistanceCubed;
                acceleration[i] += radialTerm * (kGravitationalConstant * bodies_[j].massKg);
                acceleration[j] -= radialTerm * (kGravitationalConstant * bodies_[i].massKg);
                ++lastStepStats_.nbodyPairEvaluations;
            }
        }
    };

    evaluateAccelerations();
    for (std::size_t i = 0; i < bodies_.size(); ++i) {
        if (bodies_[i].orbitMode != CelestialOrbitMode::DynamicNBody) continue;
        bodies_[i].linearVelocity += acceleration[i] * (0.5 * deltaSeconds);
        bodies_[i].position += bodies_[i].linearVelocity * deltaSeconds;
    }

    evaluateAccelerations();
    for (std::size_t i = 0; i < bodies_.size(); ++i) {
        if (bodies_[i].orbitMode != CelestialOrbitMode::DynamicNBody) continue;
        bodies_[i].linearVelocity += acceleration[i] * (0.5 * deltaSeconds);
    }
}

void CelestialSystem::evaluateAnalyticOrbitsAt(double absoluteSeconds) noexcept {
    std::vector<std::uint8_t> state(bodies_.size(), 0U);
    const auto evaluateOne = [&](auto&& self, std::size_t index) -> void {
        if (index >= bodies_.size() || state[index] == 2U) return;
        if (state[index] == 1U) {
            // Authored parent cycles are invalid; leave the existing Cartesian state rather than
            // recursing forever. Reference-frame validation remains responsible for authoring errors.
            state[index] = 2U;
            return;
        }
        CelestialBody& value = bodies_[index];
        if (value.orbitMode != CelestialOrbitMode::AnalyticKepler) {
            state[index] = 2U;
            return;
        }
        state[index] = 1U;

        std::size_t parentIndex = bodies_.size();
        for (std::size_t i = 0; i < bodies_.size(); ++i) {
            if (bodies_[i].id == value.orbitParentId) {
                parentIndex = i;
                break;
            }
        }
        if (parentIndex >= bodies_.size() || parentIndex == index) {
            state[index] = 2U;
            return;
        }
        self(self, parentIndex);
        const CelestialBody& parent = bodies_[parentIndex];

        const double mu = kGravitationalConstant * std::max(0.0, parent.massKg + value.massKg);
        KeplerianElements elements = value.analyticOrbit;
        const double a = std::max(1.0, elements.semiMajorAxisMeters);
        const double meanMotion = std::sqrt(std::max(1.0e-18, mu / (a * a * a)));
        elements.meanAnomalyRadians += meanMotion
            * (absoluteSeconds - value.analyticOrbitEpochSeconds);
        const OrbitalState relative = keplerianState(elements, mu);
        value.position = parent.position + relative.position;
        value.linearVelocity = parent.linearVelocity + relative.velocity;
        ++lastStepStats_.analyticEvaluations;
        state[index] = 2U;
    };

    for (std::size_t i = 0; i < bodies_.size(); ++i) evaluateOne(evaluateOne, i);
}

void CelestialSystem::updateSpinsAt(double absoluteSeconds) noexcept {
    for (auto& celestialBody : bodies_) {
        if (std::abs(celestialBody.spinRateRadPerSecond) <= 1.0e-15) {
            celestialBody.orientation = celestialBody.spinEpochOrientation;
            continue;
        }
        const double angle = std::remainder(
            celestialBody.spinRateRadPerSecond
                * (absoluteSeconds - celestialBody.spinEpochSeconds),
            2.0 * kPi);
        const glm::dquat delta = glm::angleAxis(angle, safeNormalize(celestialBody.spinAxis));
        celestialBody.orientation = glm::normalize(delta * celestialBody.spinEpochOrientation);
    }
}

void CelestialSystem::step(double deltaSeconds) {
    if (!std::isfinite(deltaSeconds) || deltaSeconds <= 0.0 || bodies_.empty()) return;

    lastStepStats_ = {};
    for (const auto& value : bodies_) {
        if (value.orbitMode == CelestialOrbitMode::AnalyticKepler)
            ++lastStepStats_.analyticBodies;
        else
            ++lastStepStats_.dynamicBodies;
    }

    std::size_t climateTicks = 0U;
    std::size_t weatherTicks = 0U;

    // With zero or one dynamic body there are no mutual gravitational pairs. Linear inertial drift
    // is exact for that root, while every remote planet/moon is evaluated analytically at the final
    // epoch. This collapses production's old 240x/0.25-s substep loop to one O(N) state update/frame.
    if (lastStepStats_.dynamicBodies <= 1U) {
        if (lastStepStats_.dynamicBodies == 1U) {
            for (auto& value : bodies_) {
                if (value.orbitMode == CelestialOrbitMode::DynamicNBody) {
                    value.position += value.linearVelocity * deltaSeconds;
                    ++lastStepStats_.dynamicSubsteps;
                    break;
                }
            }
        }
        timeSystem_.advance(deltaSeconds);
        climateTicks += timeSystem_.consumeClimateTicks();
        weatherTicks += timeSystem_.consumeWeatherTicks();
    } else {
        // Genuine close-encounter/mutual N-body sets retain the bounded velocity-Verlet path.
        double remaining = deltaSeconds;
        const double endTolerance = 1.0e-12 * std::max(1.0, deltaSeconds);
        while (remaining > endTolerance) {
            const double dt = std::min(remaining, kMaxOrbitalSubstepSeconds);
            integrateOrbitalSubstep(dt);
            timeSystem_.advance(dt);
            climateTicks += timeSystem_.consumeClimateTicks();
            weatherTicks += timeSystem_.consumeWeatherTicks();
            remaining -= dt;
            if (remaining < endTolerance) remaining = 0.0;
        }
    }

    const double absoluteSeconds = simulationTime();
    evaluateAnalyticOrbitsAt(absoluteSeconds);
    updateSpinsAt(absoluteSeconds);

    if (climateTicks > 0U) {
        const double diagnosticSeconds = static_cast<double>(climateTicks)
            * timeSystem_.config().climateStepSeconds;
        for (auto& celestialBody : bodies_)
            updateGlobalClimate(celestialBody, diagnosticSeconds);
    }
    if (weatherTicks > 0U) {
        for (auto& celestialBody : bodies_) updateWeatherDiagnostics(celestialBody);
    }

    syncReferenceFrames();
}

void CelestialSystem::syncReferenceFrames() {
    // First make sure every body owns one stable runtime frame id. Then wire parent ids and update
    // parent-relative translation/velocity. Orbital reference frames intentionally stay inertial:
    // planet spin belongs to CelestialPhysicsFrame, otherwise a moon orbit would rotate every day.
    for (auto& celestialBody : bodies_) {
        if (celestialBody.referenceFrameId != 0U
            && referenceFrames_.frame(celestialBody.referenceFrameId) != nullptr) continue;

        ReferenceFrame frameValue{};
        frameValue.name = celestialBody.name.empty()
            ? "celestial_" + std::to_string(celestialBody.id) + "_inertial"
            : celestialBody.name + "_inertial";
        celestialBody.referenceFrameId = referenceFrames_.addFrame(std::move(frameValue));
    }

    for (auto& celestialBody : bodies_) {
        ReferenceFrame* frameValue = referenceFrames_.frame(celestialBody.referenceFrameId);
        if (frameValue == nullptr) continue;

        const CelestialBody* parent = nullptr;
        if (celestialBody.orbitParentId != 0U && celestialBody.orbitParentId != celestialBody.id)
            parent = body(celestialBody.orbitParentId);

        if (parent != nullptr && parent->referenceFrameId != 0U) {
            frameValue->parentId = parent->referenceFrameId;
            frameValue->localPosition = celestialBody.position - parent->position;
            frameValue->localVelocity = celestialBody.linearVelocity - parent->linearVelocity;
        } else {
            frameValue->parentId = 0U;
            frameValue->localPosition = celestialBody.position;
            frameValue->localVelocity = celestialBody.linearVelocity;
        }
        frameValue->localRotation = {1.0, 0.0, 0.0, 0.0};
        frameValue->localAngularVelocity = {};
    }
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

void CelestialSystem::updateGlobalClimate(CelestialBody& celestialBody, double deltaSeconds) noexcept {
    if (celestialBody.type == CelestialBodyType::Star) return;

    // This is only the global radiative-equilibrium diagnostic. Local weather is solved by
    // PlanetClimateGrid from solar zenith, pressure gradients, moisture and Coriolis forcing.
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

void CelestialSystem::updateWeatherDiagnostics(CelestialBody& celestialBody) noexcept {
    if (celestialBody.type == CelestialBodyType::Star) return;
    // Keep authored/fallback values numerically sane without inventing a clock-driven fake weather
    // cycle. PlanetClimateGrid is the authoritative dynamic local weather field.
    celestialBody.weather.humidity = saturate(celestialBody.weather.humidity);
    celestialBody.weather.cloudCover = saturate(celestialBody.weather.cloudCover);
    celestialBody.weather.stormIntensity = saturate(celestialBody.weather.stormIntensity);
    celestialBody.weather.precipitationRateMmPerHour = std::max(
        0.0,
        celestialBody.weather.precipitationRateMmPerHour);
    celestialBody.weather.windMultiplier = std::max(0.0, celestialBody.weather.windMultiplier);
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

glm::dvec3 CelestialSystem::physicalGravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept {
    glm::dvec3 total{};
    for (const auto& source : bodies_) total += gravityFromSource(source, worldPosition);
    return total;
}

glm::dvec3 CelestialSystem::gameplayGravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept {
    return physicalGravityAccelerationAt(worldPosition);
}

glm::dvec3 CelestialSystem::gravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept {
    return physicalGravityAccelerationAt(worldPosition);
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
        relative += gravityFromSource(source, worldPosition)
            - gravityFromSource(source, frameBody->position);
    }
    return relative;
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

    sample.windVelocity = environmentBody->linearVelocity
        + glm::cross(angularVelocityOf(*environmentBody), worldPosition - environmentBody->position)
        + localWind;
    return sample;
}

} // namespace vf
