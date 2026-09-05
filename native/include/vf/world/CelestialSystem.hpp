#pragma once

#include <cstdint>
#include <span>
#include <string>
#include <vector>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

namespace vf {

// Game-first celestial physics: coherent gravity/orbit/spin/environment behavior with
// tiny CPU cost. Expensive ephemeris, global CFD and full-field plasma simulation are
// deliberately out of scope; visible/gameplay behavior must remain physically plausible.
enum class CelestialBodyType : std::uint8_t {
    Star,
    Planet,
    Moon,
};

// Classical osculating elements are an authoring/initial-state representation only. Runtime
// celestial motion is integrated in Cartesian inertial space so multiple massive bodies can
// perturb each other instead of being locked to immutable parent-only ellipses.
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
    CelestialBodyType type{CelestialBodyType::Planet};
    std::string name{};
    double radiusMeters{100.0};
    double massKg{1.0e18};
    glm::dvec3 position{};
    glm::dvec3 linearVelocity{};
    glm::dquat orientation{1.0, 0.0, 0.0, 0.0};
    glm::dvec3 spinAxis{0.0, 1.0, 0.0};
    double spinRateRadPerSecond{};
    double luminosityWatts{};
    glm::dvec3 visibleAlbedo{0.45, 0.48, 0.52};

    // Gravity and coordinate/reference-frame ranges are intentionally independent.
    // A player can be in a planet-centered precision/physics bubble while already in zero-g,
    // and being inside a gravity field never means the character is allowed to "walk in space".
    double gameplaySurfaceGravityMps2{};

    // Radius where the fast outer-space falloff begins. Zero chooses the top of the atmosphere
    // (or the solid radius for airless bodies). Between the solid surface and this radius the
    // magnitude follows inverse-square gravity. Beyond it a configurable high-power tail gives a
    // Space-Engineers/Astroneer-like finite game gravity well without a hard discontinuity.
    double gravityFalloffStartRadiusMeters{};
    double gravityFalloffPower{6.0};
    double gravityCutoffAccelerationMps2{0.05};

    // Optional explicit hard outer reach. Zero derives it from falloffStart/falloffPower/cutoff-g.
    // Kept for authored worlds and backwards compatibility with existing content.
    double gravityInfluenceRadiusMeters{};

    // Coordinate/nearby-physics ownership radius. This is NOT a gravity cutoff and NOT a walking
    // state. It exists so nearby players/props/vehicles can run in a low-speed planet-centered
    // physics space while the celestial simulation remains in double-precision inertial space.
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

    [[nodiscard]] std::uint32_t addBody(CelestialBody body);
    [[nodiscard]] CelestialBody* body(std::uint32_t id) noexcept;
    [[nodiscard]] const CelestialBody* body(std::uint32_t id) const noexcept;
    [[nodiscard]] std::span<CelestialBody> bodies() noexcept { return bodies_; }
    [[nodiscard]] std::span<const CelestialBody> bodies() const noexcept { return bodies_; }

    void step(double deltaSeconds);

    // Inertial game-world gravity. Planet/moon fields have a finite game reach, stars keep their
    // inverse-square long-range field. Multiple overlapping fields add as vectors; there is never
    // an artificial "wait until the next planet then switch gravity" rule.
    [[nodiscard]] glm::dvec3 gravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] glm::dvec3 gameplayGravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept;

    // Apparent gravity inside a translating planet-centered physics frame. External common-mode
    // acceleration at the frame origin is subtracted, leaving local gravity plus only real tidal
    // differences. This is the KSP-style separation needed to stop an orbiting ground from shaking
    // every rigid body while preserving correct free-flight when the object leaves the frame.
    [[nodiscard]] glm::dvec3 gravityAccelerationRelativeTo(
        std::uint32_t frameBodyId,
        const glm::dvec3& worldPosition) const noexcept;

    // Explicit full GM/r^2 vector superposition for orbital diagnostics, validation and tools.
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

    // Compatibility alias for older callers. New movement code should explicitly choose either
    // gravityReferenceBodyAt() or physicsReferenceBodyAt() instead of conflating the concepts.
    [[nodiscard]] const CelestialBody* gameplayReferenceBodyAt(const glm::dvec3& worldPosition) const noexcept;

    [[nodiscard]] const CelestialBody* dominantBodyAt(const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] double signedSurfaceDistance(const CelestialBody& body, const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] CelestialEnvironmentSample sampleEnvironment(const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] glm::dvec3 magneticFieldAt(const CelestialBody& body, const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] double stellarIrradianceAt(const CelestialBody& body) const noexcept;

    [[nodiscard]] double simulationTime() const noexcept { return simulationTime_; }

private:
    void updateSpin(CelestialBody& body, double deltaSeconds) noexcept;
    void updateClimateAndWeather(CelestialBody& body, double deltaSeconds) noexcept;

    [[nodiscard]] glm::dvec3 gameplayBodyGravity(
        const CelestialBody& body,
        const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] glm::dvec3 gravityFromSource(
        const CelestialBody& body,
        const glm::dvec3& worldPosition) const noexcept;

    std::vector<CelestialBody> bodies_;
    std::uint32_t nextBodyId_{1};
    double simulationTime_{};
};

} // namespace vf