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

    [[nodiscard]] glm::dvec3 gravityAccelerationAt(const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] const CelestialBody* dominantBodyAt(const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] double signedSurfaceDistance(const CelestialBody& body, const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] CelestialEnvironmentSample sampleEnvironment(const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] glm::dvec3 magneticFieldAt(const CelestialBody& body, const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] double stellarIrradianceAt(const CelestialBody& body) const noexcept;

    [[nodiscard]] double simulationTime() const noexcept { return simulationTime_; }

private:
    void updateOrbit(CelestialBody& body, double deltaSeconds);
    void updateSpin(CelestialBody& body, double deltaSeconds) noexcept;
    void updateClimateAndWeather(CelestialBody& body, double deltaSeconds) noexcept;

    std::vector<CelestialBody> bodies_;
    std::uint32_t nextBodyId_{1};
    double simulationTime_{};
};

} // namespace vf
