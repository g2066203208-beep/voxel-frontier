#pragma once

#include "vf/world/ReferenceFrame.hpp"
#include "vf/world/UniverseTime.hpp"

#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <vector>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

namespace vf {

// Game-first celestial physics: coherent gravity/orbit/spin/environment behavior with tiny CPU
// cost. Runtime motion is integrated in double-precision inertial space. Hierarchical inertial
// reference frames mirror the authored orbit-parent graph, while CelestialPhysicsFrame owns the
// separate rotating body-fixed frame used by nearby rigid-body simulation.
enum class CelestialBodyType : std::uint8_t {
    Star,
    Planet,
    Moon,
};

struct KeplerianElements {
    double semiMajorAxisMeters{};
    double eccentricity{};
    double inclinationRadians{};
    double longitudeAscendingNodeRadians{};
    double argumentPeriapsisRadians{};
    double meanAnomalyRadians{};
};

struct OrbitalState {
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

struct CelestialAtmosphere {
    bool enabled{};
    double heightMeters{};
    double surfacePressurePa{101325.0};
    double surfaceTemperatureK{288.15};
    double molarMassKgPerMol{0.0289644};
    double scaleHeightMeters{8500.0};
    double lapseRateKPerM{0.0065};
    glm::dvec3 rayleighRgb{0.18, 0.42, 1.0};
    double mieStrength{0.08};
    glm::dvec3 prevailingWind{6.0, 0.0, 1.5};
};

struct CelestialClimate {
    double bondAlbedo{0.30};
    double greenhouseFactor{1.12};
    double thermalResponseSeconds{7200.0};
    double meanTemperatureK{288.15};
};

struct CelestialWeather {
    double humidity{0.45};
    double cloudCover{0.25};
    double stormIntensity{};
    double precipitationRateMmPerHour{};
    double windMultiplier{1.0};
};

struct CelestialMagneticField {
    bool enabled{};
    glm::dvec3 dipoleAxis{0.0, 1.0, 0.0};
    double equatorialSurfaceFieldTesla{30.0e-6};
};

struct CelestialBody {
    std::uint32_t id{};
    std::uint32_t orbitParentId{};

    // Runtime-owned frame id. It is created and synchronized by CelestialSystem from orbitParentId;
    // authored callers should leave this zero. The frame is inertial/translated, not body-fixed.
    std::uint32_t referenceFrameId{};

    CelestialBodyType type{CelestialBodyType::Planet};
    std::string name{};
    double radiusMeters{100.0};
    double massKg{1.0e18};
    glm::dvec3 position{};
    glm::dvec3 linearVelocity{};
    glm::dquat orientation{1.0, 0.0, 0.0, 0.0};
    glm::dvec3 spinAxis{0.0, 1.0, 0.0};
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
    glm::dvec3 visibleAlbedo{0.45, 0.48, 0.52};

    double gameplaySurfaceGravityMps2{};

    // Legacy authored gravity-well fields are retained for compatibility and for choosing local
    // streaming/physics ownership radii. R24 physical acceleration itself remains Newtonian and is
    // never hard-cut to zero at these distances.
    double gravityFalloffStartRadiusMeters{};
    double gravityFalloffPower{6.0};
    double gravityCutoffAccelerationMps2{0.05};
    double gravityInfluenceRadiusMeters{};

    // Nearby coordinate/physics ownership radius. It is independent from physical gravity.
    double physicsBubbleRadiusMeters{};

    CelestialAtmosphere atmosphere{};
    CelestialClimate climate{};
    CelestialWeather weather{};
    CelestialMagneticField magneticField{};
};

struct CelestialEnvironmentSample {
    std::uint32_t bodyId{};
    double altitudeMeters{};
    glm::dvec3 gravityAcceleration{};
    double temperatureK{};
    double pressurePa{};
    double densityKgPerM3{};
    glm::dvec3 windVelocity{};
    double humidity{};
    double cloudCover{};
    double precipitationRateMmPerHour{};
    glm::dvec3 magneticFieldTesla{};
};

class CelestialSystem final {
public:
    static constexpr double kGravitationalConstant = 6.67430e-11;
    static constexpr double kStefanBoltzmann = 5.670374419e-8;
    static constexpr double kMaxOrbitalSubstepSeconds = 60.0;

    [[nodiscard]] std::uint32_t addBody(CelestialBody body);
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
    // substeps; no remainder is discarded. Wall-clock scaling belongs to CelestialSimulationClock.
    void step(double deltaSeconds);

    [[nodiscard]] ReferenceFrameSystem& referenceFrames() noexcept { return referenceFrames_; }
    [[nodiscard]] const ReferenceFrameSystem& referenceFrames() const noexcept { return referenceFrames_; }
    [[nodiscard]] UniverseTime& timeSystem() noexcept { return timeSystem_; }
    [[nodiscard]] const UniverseTime& timeSystem() const noexcept { return timeSystem_; }

    // Unified R24 physical gravity. Legacy gameplay naming remains as compatibility aliases so old
    // movement code keeps building while all callers observe the same Newtonian vector field.
    [[nodiscard]] glm::dvec3 gravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] glm::dvec3 gameplayGravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept;

    [[nodiscard]] glm::dvec3 gravityAccelerationRelativeTo(
        std::uint32_t frameBodyId,
        const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] glm::dvec3 physicalGravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept;

    [[nodiscard]] double gravityMagnitudeFromBody(
        const CelestialBody& body,
        const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] double gravityCutoffRadius(const CelestialBody& body) const noexcept;
    [[nodiscard]] bool insideAtmosphere(
        const CelestialBody& body,
        const glm::dvec3& worldPosition) const noexcept;

    [[nodiscard]] const CelestialBody* gravityReferenceBodyAt(const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] const CelestialBody* physicsReferenceBodyAt(const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] const CelestialBody* gameplayReferenceBodyAt(const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] const CelestialBody* dominantBodyAt(const glm::dvec3& worldPosition) const noexcept;

    [[nodiscard]] double signedSurfaceDistance(const CelestialBody& body, const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] CelestialEnvironmentSample sampleEnvironment(const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] glm::dvec3 magneticFieldAt(const CelestialBody& body, const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] double stellarIrradianceAt(const CelestialBody& body) const noexcept;

    [[nodiscard]] double simulationTime() const noexcept { return timeSystem_.secondsApprox(); }
    [[nodiscard]] const AstroTime& simulationEpoch() const noexcept { return timeSystem_.time(); }

private:
    void integrateOrbitalSubstep(double deltaSeconds);
    void evaluateAnalyticOrbitsAt(double absoluteSeconds) noexcept;
    void syncReferenceFrames();
    void updateSpinsAt(double absoluteSeconds) noexcept;
    void updateGlobalClimate(CelestialBody& body, double deltaSeconds) noexcept;
    void updateWeatherDiagnostics(CelestialBody& body) noexcept;

    [[nodiscard]] glm::dvec3 gravityFromSource(
        const CelestialBody& body,
        const glm::dvec3& worldPosition) const noexcept;

    std::vector<CelestialBody> bodies_;
    std::uint32_t nextBodyId_{1};
    ReferenceFrameSystem referenceFrames_{};
    UniverseTime timeSystem_{};
    CelestialSimulationStats lastStepStats_{};
};

} // namespace vf
