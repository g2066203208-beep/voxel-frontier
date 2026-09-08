#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / "native/include/vf/world/CelestialSystem.hpp"
CPP = ROOT / "native/src/world/CelestialSystem.cpp"
MAIN = ROOT / "native/src/app/Main.cpp"
CMAKE = ROOT / "native/CMakeLists.txt"


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: {label}: expected one anchor, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_before_once(path: Path, anchor: str, payload: str, label: str) -> None:
    replace_once(path, anchor, payload + anchor, label)


# -----------------------------------------------------------------------------
# Public celestial policy: default remains DynamicNBody for backwards-compatible
# physics tests. Production stable planets opt into AnalyticKepler explicitly.
# -----------------------------------------------------------------------------
replace_once(
    HEADER,
    """struct OrbitalState {
    glm::dvec3 position{};
    glm::dvec3 velocity{};
};

[[nodiscard]] OrbitalState keplerianState(
    const KeplerianElements& elements,
    double gravitationalParameterM3PerS2) noexcept;
""",
    """struct OrbitalState {
    glm::dvec3 position{};
    glm::dvec3 velocity{};
};

[[nodiscard]] OrbitalState keplerianState(
    const KeplerianElements& elements,
    double gravitationalParameterM3PerS2) noexcept;

// Convert a bound Cartesian state into the same classical element convention consumed by
// keplerianState(). This lets authored physically-correct position/velocity initial conditions
// switch to ephemeris mode without hand-maintaining a second orbital description.
[[nodiscard]] bool keplerianElementsFromState(
    const OrbitalState& state,
    double gravitationalParameterM3PerS2,
    KeplerianElements& elements) noexcept;

enum class CelestialOrbitMode : std::uint8_t {
    // Mutual velocity-Verlet integration. Use this for genuine close encounters / dynamically
    // interacting massive bodies. This remains the default so existing physics behavior is exact.
    DynamicNBody,
    // Stable remote orbit evaluated from absolute simulation epoch. The body remains a Newtonian
    // gravity source for gameplay queries but does not waste O(N^2) pair integration against other
    // remote ephemerides every render frame.
    AnalyticKepler,
};

struct CelestialSimulationStats {
    std::size_t dynamicBodies{};
    std::size_t analyticBodies{};
    std::uint64_t dynamicSubsteps{};
    std::uint64_t nbodyPairEvaluations{};
    std::uint64_t analyticEvaluations{};
};
""",
    "add orbit LOD policy and state conversion API",
)

# Need size_t in public stats.
replace_once(
    HEADER,
    """#include <cstdint>
#include <span>
""",
    """#include <cstddef>
#include <cstdint>
#include <span>
""",
    "include cstddef",
)

replace_once(
    HEADER,
    """    glm::dvec3 spinAxis{0.0, 1.0, 0.0};
    double spinRateRadPerSecond{};
    double luminosityWatts{};
""",
    """    glm::dvec3 spinAxis{0.0, 1.0, 0.0};
    double spinRateRadPerSecond{};

    // Simulation LOD. DynamicNBody preserves mutual integration; AnalyticKepler stores one compact
    // parent-relative ephemeris and evaluates current position/velocity directly from absolute time.
    CelestialOrbitMode orbitMode{CelestialOrbitMode::DynamicNBody};
    KeplerianElements analyticOrbit{};
    double analyticOrbitEpochSeconds{};

    // Self-rotation is also epoch based. orientation is still updated for all existing consumers,
    // but it is derived from these immutable epoch values instead of accumulating one quaternion
    // multiply for every accelerated celestial substep.
    glm::dquat spinEpochOrientation{1.0, 0.0, 0.0, 0.0};
    double spinEpochSeconds{};

    double luminosityWatts{};
""",
    "add analytic orbit and spin epoch state",
)

replace_once(
    HEADER,
    """    [[nodiscard]] std::uint32_t addBody(CelestialBody body);
    [[nodiscard]] CelestialBody* body(std::uint32_t id) noexcept;
    [[nodiscard]] const CelestialBody* body(std::uint32_t id) const noexcept;
    [[nodiscard]] std::span<CelestialBody> bodies() noexcept { return bodies_; }
    [[nodiscard]] std::span<const CelestialBody> bodies() const noexcept { return bodies_; }

    // deltaSeconds is already simulated time. Large calls are fully consumed using <=60 s orbital
""",
    """    [[nodiscard]] std::uint32_t addBody(CelestialBody body);
    [[nodiscard]] CelestialBody* body(std::uint32_t id) noexcept;
    [[nodiscard]] const CelestialBody* body(std::uint32_t id) const noexcept;
    [[nodiscard]] std::span<CelestialBody> bodies() noexcept { return bodies_; }
    [[nodiscard]] std::span<const CelestialBody> bodies() const noexcept { return bodies_; }

    // Promote a stable authored orbit to an absolute-time ephemeris using its current parent-relative
    // Cartesian state. Returns false for missing parents, unbound/degenerate states or invalid ids.
    [[nodiscard]] bool setAnalyticOrbitFromCurrentState(std::uint32_t bodyId) noexcept;
    void setDynamicNBody(std::uint32_t bodyId) noexcept;
    [[nodiscard]] const CelestialSimulationStats& lastStepStats() const noexcept {
        return lastStepStats_;
    }

    // deltaSeconds is already simulated time. Dynamic close-encounter bodies still use bounded
""",
    "add public celestial simulation LOD controls",
)

replace_once(
    HEADER,
    """private:
    void integrateOrbitalSubstep(double deltaSeconds);
    void syncReferenceFrames();
    void updateSpin(CelestialBody& body, double deltaSeconds) noexcept;
""",
    """private:
    void integrateOrbitalSubstep(double deltaSeconds);
    void evaluateAnalyticOrbitsAt(double absoluteSeconds) noexcept;
    void syncReferenceFrames();
    void updateSpinsAt(double absoluteSeconds) noexcept;
""",
    "replace substep spin with epoch evaluators",
)
replace_once(
    HEADER,
    """    ReferenceFrameSystem referenceFrames_{};
    UniverseTime timeSystem_{};
};
""",
    """    ReferenceFrameSystem referenceFrames_{};
    UniverseTime timeSystem_{};
    CelestialSimulationStats lastStepStats_{};
};
""",
    "store simulation telemetry",
)

# -----------------------------------------------------------------------------
# CelestialSystem implementation.
# -----------------------------------------------------------------------------
insert_before_once(
    CPP,
    "[[nodiscard]] glm::dvec3 standardToGameAxes(const glm::dvec3& value) noexcept {\n",
    """[[nodiscard]] glm::dvec3 gameToStandardAxes(const glm::dvec3& value) noexcept {
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

""",
    "add element inversion helpers",
)

insert_before_once(
    CPP,
    "std::uint32_t CelestialSystem::addBody(CelestialBody bodyValue) {\n",
    r'''bool keplerianElementsFromState(
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

''',
    "add Cartesian to Kepler conversion",
)

# Initialize spin epoch at the exact runtime time when a body enters the system.
replace_once(
    CPP,
    """    bodyValue.orientation = glm::normalize(bodyValue.orientation);
    bodyValue.spinAxis = safeNormalize(bodyValue.spinAxis);
""",
    """    bodyValue.orientation = glm::normalize(bodyValue.orientation);
    bodyValue.spinAxis = safeNormalize(bodyValue.spinAxis);
    bodyValue.spinEpochOrientation = bodyValue.orientation;
    bodyValue.spinEpochSeconds = simulationTime();
""",
    "initialize analytic spin epoch",
)

# New policy controls immediately after body lookup methods.
insert_before_once(
    CPP,
    "void CelestialSystem::integrateOrbitalSubstep(double deltaSeconds) {\n",
    r'''bool CelestialSystem::setAnalyticOrbitFromCurrentState(std::uint32_t bodyId) noexcept {
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

''',
    "add celestial LOD controls",
)

# Replace pair integration with dynamic-only mutual N-body. Analytic bodies remain available to
# gravityAccelerationAt() but are ephemeris sources, not participants in the quadratic solver.
replace_once(
    CPP,
    """void CelestialSystem::integrateOrbitalSubstep(double deltaSeconds) {
    if (bodies_.empty() || deltaSeconds <= 0.0) return;

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
        bodies_[i].linearVelocity += acceleration[i] * (0.5 * deltaSeconds);
        bodies_[i].position += bodies_[i].linearVelocity * deltaSeconds;
    }

    evaluateAccelerations();
    for (std::size_t i = 0; i < bodies_.size(); ++i) {
        bodies_[i].linearVelocity += acceleration[i] * (0.5 * deltaSeconds);
    }
}
""",
    r'''void CelestialSystem::integrateOrbitalSubstep(double deltaSeconds) {
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
''',
    "dynamic-only pair integration and analytic ephemeris",
)

# Replace step: one body is exact linear drift, many dynamic bodies retain <=60 s Verlet, analytic
# hierarchy and spin are evaluated exactly once at final epoch. Slow diagnostics are accumulated.
replace_once(
    CPP,
    """void CelestialSystem::step(double deltaSeconds) {
    if (!std::isfinite(deltaSeconds) || deltaSeconds <= 0.0 || bodies_.empty()) return;

    // Unlike the old clamp-only implementation, every simulated second is consumed. Very large
    // caller deltas are split into bounded Verlet steps so direct callers cannot silently lose the
    // remainder after 60 s. Normal runtime use still arrives pre-bounded from CelestialSimulationClock.
    double remaining = deltaSeconds;
    const double endTolerance = 1.0e-12 * std::max(1.0, deltaSeconds);
    while (remaining > endTolerance) {
        const double dt = std::min(remaining, kMaxOrbitalSubstepSeconds);
        integrateOrbitalSubstep(dt);
        for (auto& celestialBody : bodies_) updateSpin(celestialBody, dt);

        timeSystem_.advance(dt);

        const std::size_t climateTicks = timeSystem_.consumeClimateTicks();
        for (std::size_t tick = 0; tick < climateTicks; ++tick) {
            for (auto& celestialBody : bodies_)
                updateGlobalClimate(celestialBody, timeSystem_.config().climateStepSeconds);
        }

        const std::size_t weatherTicks = timeSystem_.consumeWeatherTicks();
        if (weatherTicks > 0U) {
            for (auto& celestialBody : bodies_) updateWeatherDiagnostics(celestialBody);
        }

        syncReferenceFrames();
        remaining -= dt;
        if (remaining < endTolerance) remaining = 0.0;
    }
}
""",
    r'''void CelestialSystem::step(double deltaSeconds) {
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
''',
    "multirate celestial public step",
)

# Remove old accumulating spin implementation because updateSpinsAt owns absolute-time orientation.
old_spin = """void CelestialSystem::updateSpin(CelestialBody& celestialBody, double deltaSeconds) noexcept {
    if (std::abs(celestialBody.spinRateRadPerSecond) <= 1.0e-15) return;
    const glm::dquat delta = glm::angleAxis(
        celestialBody.spinRateRadPerSecond * deltaSeconds,
        safeNormalize(celestialBody.spinAxis));
    celestialBody.orientation = glm::normalize(delta * celestialBody.orientation);
}

"""
replace_once(CPP, old_spin, "", "remove accumulating spin implementation")

# -----------------------------------------------------------------------------
# Production Main: stable major planets/moon become analytic ephemerides. Render-frame celestial
# time advances once using exact absolute-time evaluation instead of 16 x 0.25s calls at 240x.
# Moon/Cinder mesh work is also view-aware and angular-size LOD controlled.
# -----------------------------------------------------------------------------
replace_once(
    MAIN,
    """        const double celestialFixedStepSeconds =
            vf::recommendedCelestialFixedStepSeconds(celestialTimeScale);
        vf::CelestialSimulationClock celestialClock{{
            celestialFixedStepSeconds, celestialTimeScale, 4096U}};

""",
    """        // Production major-body orbits below use absolute-time ephemerides. This means a 240x
        // day/orbit scale advances once per display frame without the old sixteen 0.25-s callbacks,
        // while dynamic N-body mode remains available for explicit close-encounter simulations.

""",
    "remove production fixed-step callback clock",
)

# Promote Aster/Cinder/Luna after they have a valid parent and initial Cartesian state.
replace_once(
    MAIN,
    """        const std::uint32_t asterId = planetaryBodies.addBody(std::move(asterDescriptor));
        auto* asterSurface = planetaryBodies.surface(asterId);
""",
    """        const std::uint32_t asterId = planetaryBodies.addBody(std::move(asterDescriptor));
        if (!celestial.setAnalyticOrbitFromCurrentState(asterId))
            throw std::runtime_error("Aster analytic ephemeris initialization failed");
        auto* asterSurface = planetaryBodies.surface(asterId);
""",
    "promote Aster ephemeris",
)
replace_once(
    MAIN,
    """        const std::uint32_t cinderId = celestial.addBody(cinder);

        const glm::dvec3 initialSunDirectionPlanet = safeNormalize(
""",
    """        const std::uint32_t cinderId = celestial.addBody(cinder);
        if (!celestial.setAnalyticOrbitFromCurrentState(cinderId))
            throw std::runtime_error("Cinder analytic ephemeris initialization failed");

        const glm::dvec3 initialSunDirectionPlanet = safeNormalize(
""",
    "promote Cinder ephemeris",
)
replace_once(
    MAIN,
    """        const std::uint32_t moonId = celestial.addBody(luna);
        vf::PlanetDefinition moonSurfaceDefinition{};
""",
    """        const std::uint32_t moonId = celestial.addBody(luna);
        if (!celestial.setAnalyticOrbitFromCurrentState(moonId))
            throw std::runtime_error("Luna analytic ephemeris initialization failed");
        vf::PlanetDefinition moonSurfaceDefinition{};
""",
    "promote Luna ephemeris",
)

# Add an ultra-cheap distant moon mesh; angular pixel footprint selects tiers rather than an arbitrary
# 12,000km switch.
replace_once(
    MAIN,
    """        vf::PlanetMesh moonSurfaceMeshFar = vf::buildPlanetGlobeSurface(
            moonSurfaceDefinition, 28U, 1.0);
        vf::PlanetMesh moonSurfaceMeshNear = vf::buildPlanetGlobeSurface(
            moonSurfaceDefinition, 80U, 1.0);
""",
    """        vf::PlanetMesh moonSurfaceMeshDistant = vf::buildPlanetGlobeSurface(
            moonSurfaceDefinition, 6U, 1.0);
        vf::PlanetMesh moonSurfaceMeshFar = vf::buildPlanetGlobeSurface(
            moonSurfaceDefinition, 28U, 1.0);
        vf::PlanetMesh moonSurfaceMeshNear = vf::buildPlanetGlobeSurface(
            moonSurfaceDefinition, 80U, 1.0);
""",
    "add angular distant moon mesh",
)

# One exact celestial update per render frame. CelestialSystem itself retains <=60s dynamic-Nbody
# subdivision only when >=2 bodies are genuinely dynamic.
replace_once(
    MAIN,
    """            celestialClock.setTimeScale(effectiveCelestialTimeScale);
            celestialClock.advance(dt, [&](double astroDt) {
                // One authoritative step advances double-precision N-body vectors and quaternion
                // spin on the same bounded simulated-time sequence.
                planetaryBodies.step(astroDt);
            });

""",
    """            planetaryBodies.step(dt * effectiveCelestialTimeScale);
            if (runtimeDiagnosticsStdout) {
                const vf::CelestialSimulationStats celestialStats = celestial.lastStepStats();
                static std::uint64_t celestialDiagFrame = 0U;
                if ((++celestialDiagFrame % 120U) == 0U) {
                    std::cout << "R24 CELESTIAL dynamic_bodies=" << celestialStats.dynamicBodies
                              << " analytic_bodies=" << celestialStats.analyticBodies
                              << " nbody_pairs=" << celestialStats.nbodyPairEvaluations
                              << " ephemeris_evals=" << celestialStats.analyticEvaluations
                              << " dynamic_substeps=" << celestialStats.dynamicSubsteps
                              << '\\n';
                }
            }

""",
    "single exact celestial update per frame",
)

# Replace moon distance switch with frustum/view and angular pixel LOD. The margin is wider than the
# actual 68-degree vertical view, so turning remains smooth without baking a moon behind the player.
replace_once(
    MAIN,
    """            if (refreshDynamicScene && currentMoon != nullptr) {
                const double moonCameraDistance = glm::length(currentMoon->position - camera.position());
                const double asterObserverAltitude = std::max(
                    0.0, glm::length(camera.position() - currentAster->position)
                        - currentAster->radiusMeters);
                const double moonVisualScale = gameplayMoonVisualScale(
                    asterObserverAltitude, moonCameraDistance);
                const vf::PlanetMesh& moonSource = moonCameraDistance < 12000000.0
                    ? moonSurfaceMeshNear : moonSurfaceMeshFar;
                vf::PlanetMesh moonMesh = moonSource;
""",
    """            if (refreshDynamicScene && currentMoon != nullptr) {
                const glm::dvec3 moonToCamera = currentMoon->position - camera.position();
                const double moonCameraDistance = glm::length(moonToCamera);
                const glm::dvec3 moonViewDirection = safeNormalize(moonToCamera, camera.forwardDirection());
                const bool moonPotentiallyVisible = trackMoonEvidence
                    || glm::dot(camera.forwardDirection(), moonViewDirection) > std::cos(glm::radians(72.0));
                const double asterObserverAltitude = std::max(
                    0.0, glm::length(camera.position() - currentAster->position)
                        - currentAster->radiusMeters);
                const double moonVisualScale = gameplayMoonVisualScale(
                    asterObserverAltitude, moonCameraDistance);
                const double moonAngularRadius = std::asin(std::clamp(
                    currentMoon->radiusMeters * moonVisualScale
                        / std::max(moonCameraDistance, currentMoon->radiusMeters * moonVisualScale),
                    0.0, 1.0));
                const double moonFocalPixels = 900.0
                    / (2.0 * std::tan(glm::radians(68.0) * 0.5));
                const double moonPixelDiameter = 2.0 * std::tan(moonAngularRadius) * moonFocalPixels;
                const vf::PlanetMesh& moonSource = moonPixelDiameter >= 180.0
                    ? moonSurfaceMeshNear
                    : (moonPixelDiameter >= 8.0 ? moonSurfaceMeshFar : moonSurfaceMeshDistant);
                vf::PlanetMesh moonMesh{};
                if (moonPotentiallyVisible) moonMesh = moonSource;
""",
    "angular/view-aware moon mesh LOD",
)
# The transform loop and append operate on empty mesh if culled, which is cheap and preserves anchors.

# Cinder debug sphere: do not synthesize off-view geometry; reduce tessellation when its apparent
# diameter is small. This is the same pixel-footprint principle Celestia uses for minimum features.
replace_once(
    MAIN,
    """            if (refreshDynamicScene && currentCinder != nullptr) {
                const glm::dvec3 cinderDirection = safeNormalize(
                    currentCinder->position - camera.position());
                const glm::dvec3 cinderSurfaceDirection = safeNormalize(
                    toSurfaceVector(inverseAster * cinderDirection));
                const double distance = glm::length(currentCinder->position - camera.position());
                const double angularRadius = std::asin(std::clamp(
                    currentCinder->radiusMeters / std::max(distance, currentCinder->radiusMeters),
                    0.0,
                    0.20));
                constexpr double visualDistance = 25000000.0;
                const double visualRadius = std::max(
                    1800.0, std::tan(angularRadius) * visualDistance);
                vf::appendDebugSphere(
                    dynamicMesh,
                    cameraSurface + cinderSurfaceDirection * visualDistance,
                    visualRadius,
                    {0.62F, 0.30F, 0.22F},
                    9U,
                    16U,
                    {0.0F, 0.82F, 0.0F, 0.0F});
            }
""",
    """            if (refreshDynamicScene && currentCinder != nullptr) {
                const glm::dvec3 cinderDirection = safeNormalize(
                    currentCinder->position - camera.position());
                const bool cinderPotentiallyVisible = glm::dot(
                    camera.forwardDirection(), cinderDirection) > std::cos(glm::radians(72.0));
                if (cinderPotentiallyVisible) {
                    const glm::dvec3 cinderSurfaceDirection = safeNormalize(
                        toSurfaceVector(inverseAster * cinderDirection));
                    const double distance = glm::length(currentCinder->position - camera.position());
                    const double angularRadius = std::asin(std::clamp(
                        currentCinder->radiusMeters / std::max(distance, currentCinder->radiusMeters),
                        0.0,
                        0.20));
                    const double focalPixels = 900.0
                        / (2.0 * std::tan(glm::radians(68.0) * 0.5));
                    const double pixelDiameter = 2.0 * std::tan(angularRadius) * focalPixels;
                    constexpr double visualDistance = 25000000.0;
                    const double visualRadius = std::max(
                        1800.0, std::tan(angularRadius) * visualDistance);
                    vf::appendDebugSphere(
                        dynamicMesh,
                        cameraSurface + cinderSurfaceDirection * visualDistance,
                        visualRadius,
                        {0.62F, 0.30F, 0.22F},
                        pixelDiameter >= 20.0 ? 9U : 4U,
                        pixelDiameter >= 20.0 ? 16U : 8U,
                        {0.0F, 0.82F, 0.0F, 0.0F});
                }
            }
""",
    "view and angular LOD for Cinder",
)

# Register focused regression executable.
replace_once(
    CMAKE,
    """    add_executable(vf_celestial_system_tests tests/CelestialSystemTests.cpp)
    target_link_libraries(vf_celestial_system_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_celestial_system_tests COMMAND vf_celestial_system_tests)
""",
    """    add_executable(vf_celestial_system_tests tests/CelestialSystemTests.cpp)
    target_link_libraries(vf_celestial_system_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_celestial_system_tests COMMAND vf_celestial_system_tests)
    add_executable(vf_celestial_simulation_lod_tests tests/CelestialSimulationLodTests.cpp)
    target_link_libraries(vf_celestial_simulation_lod_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_celestial_simulation_lod_tests COMMAND vf_celestial_simulation_lod_tests)
""",
    "register celestial simulation LOD tests",
)

print("R24 celestial simulation LOD foundation materialized")
