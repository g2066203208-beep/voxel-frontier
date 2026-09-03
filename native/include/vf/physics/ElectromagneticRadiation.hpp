#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

#include <glm/glm.hpp>

#include "vf/physics/SpectralOptics.hpp"

namespace vf {

// Game-first field physics. The engine samples a small set of nearby analytic sources
// instead of solving Maxwell's equations on a global grid. This keeps the important
// directions, inverse-square/range behavior, energy accounting and induction while
// avoiding FDTD/CFD-scale costs.
class ElectromagneticRadiationSystem final {
public:
    static constexpr double kVacuumPermittivity = 8.8541878128e-12;
    static constexpr double kVacuumPermeability = 1.25663706212e-6;
    static constexpr double kCoulombConstant = 8.9875517923e9;
    static constexpr double kSpeedOfLight = 299792458.0;
    static constexpr double kStefanBoltzmann = 5.670374419e-8;

    enum class RadiationBand : std::uint8_t {
        Radio,
        Microwave,
        Infrared,
        Visible,
        Ultraviolet,
        Ionizing,
        Count,
    };

    static constexpr std::size_t kRadiationBandCount = static_cast<std::size_t>(RadiationBand::Count);

    struct BroadbandSpectrum {
        // Power or irradiance per broad gameplay band. Units depend on use site:
        // watts for a source and W/m^2 for a sampled field.
        std::array<double, kRadiationBandCount> values{};

        [[nodiscard]] double& operator[](RadiationBand band) noexcept {
            return values[static_cast<std::size_t>(band)];
        }
        [[nodiscard]] double operator[](RadiationBand band) const noexcept {
            return values[static_cast<std::size_t>(band)];
        }
        [[nodiscard]] double total() const noexcept;
    };

    struct ElectricPointSource {
        glm::dvec3 position{};
        double chargeCoulombs{};
        double softeningRadiusMeters{0.05};
        double maxRangeMeters{80.0};
    };

    struct MagneticDipoleSource {
        glm::dvec3 position{};
        glm::dvec3 magneticMomentAmpereSquareMeters{0.0, 1.0, 0.0};
        double softeningRadiusMeters{0.05};
        double maxRangeMeters{80.0};
    };

    struct SolenoidSource {
        glm::dvec3 position{};
        glm::dvec3 axis{0.0, 1.0, 0.0};
        double turns{200.0};
        double lengthMeters{0.5};
        double radiusMeters{0.08};
        double currentAmperes{};
        double relativePermeability{1.0};
        double maxRangeMeters{20.0};
    };

    struct DisplacementCurrentSource {
        // Cheap Ampere-Maxwell gameplay source: changing electric flux through a
        // small virtual capacitor produces an azimuthal magnetic field.
        glm::dvec3 position{};
        glm::dvec3 axis{0.0, 1.0, 0.0};
        double electricFluxRateVoltMetersPerSecond{};
        double coreRadiusMeters{0.05};
        double maxRangeMeters{10.0};
    };

    struct RadiationSource {
        glm::dvec3 position{};
        glm::dvec3 direction{0.0, 0.0, 1.0};
        BroadbandSpectrum powerWatts{};
        GameSpectrum visibleShape{};
        // <= -1 means isotropic. Otherwise this is cos(half-angle) of a power-
        // conserving emission cone.
        double coneCosine{-1.0};
        double minimumDistanceMeters{0.10};
        double maxRangeMeters{1.0e9};
    };

    struct FieldSample {
        glm::dvec3 electricFieldVoltsPerMeter{};
        glm::dvec3 magneticFieldTesla{};
        BroadbandSpectrum irradianceWattsPerSquareMeter{};
        GameSpectrum visibleIrradianceWattsPerSquareMeter{};
    };

    struct InductionCoil {
        glm::dvec3 position{};
        glm::dvec3 normal{0.0, 1.0, 0.0};
        double areaSquareMeters{0.01};
        double turns{100.0};
        double resistanceOhms{10.0};
        double previousFluxWebers{};
        double inducedEmfVolts{};
        double inducedCurrentAmperes{};
        bool initialized{};
    };

    struct WaveField {
        glm::dvec3 electricRmsVoltsPerMeter{};
        glm::dvec3 magneticRmsTesla{};
    };

    struct RadiationMaterial {
        std::array<double, kRadiationBandCount> absorptivity{0.05, 0.10, 0.70, 0.65, 0.75, 0.25};
        std::array<double, kRadiationBandCount> attenuationPerMeter{0.0, 0.0, 0.2, 0.2, 0.5, 2.0};
        double emissivity{0.85};
    };

    struct ThermalBody {
        glm::dvec3 position{};
        double massKg{1.0};
        double specificHeatJPerKgK{1200.0};
        double surfaceAreaSquareMeters{1.0};
        double projectedAreaSquareMeters{0.1};
        double temperatureK{293.15};
        double ignitionTemperatureK{650.0};
        double convectiveCoefficientWPerSquareMeterK{8.0};
        RadiationMaterial material{};
        double ultravioletExposureJPerSquareMeter{};
        double ionizingDoseGray{};
        bool ignited{};
    };

    struct ThinLens {
        glm::dvec3 position{};
        glm::dvec3 opticalAxis{0.0, 0.0, 1.0};
        double focalLengthMeters{0.20};
        double apertureRadiusMeters{0.05};
        double transmission{0.92};
        double minimumSpotRadiusMeters{0.004};
        double axialToleranceMeters{0.015};
    };

    struct LightSensor {
        double activeAreaSquareMeters{1.0e-4};
        double responsivityAmperesPerWatt{0.45};
    };

    void addElectricSource(ElectricPointSource source);
    void addMagneticDipole(MagneticDipoleSource source);
    void addSolenoid(SolenoidSource source);
    void addDisplacementCurrentSource(DisplacementCurrentSource source);
    void addRadiationSource(RadiationSource source);
    void clearSources() noexcept;

    [[nodiscard]] FieldSample sample(const glm::dvec3& worldPosition) const noexcept;
    [[nodiscard]] glm::dvec3 lorentzForce(
        double chargeCoulombs,
        const glm::dvec3& velocityMetersPerSecond,
        const FieldSample& sample) const noexcept;
    void stepInductionCoil(InductionCoil& coil, double deltaSeconds) const noexcept;

    [[nodiscard]] static WaveField waveFieldsFromIrradiance(
        double irradianceWattsPerSquareMeter,
        const glm::dvec3& propagationDirection,
        const glm::dvec3& polarizationHint) noexcept;
    [[nodiscard]] static BroadbandSpectrum attenuateRadiation(
        const BroadbandSpectrum& incident,
        const RadiationMaterial& material,
        double thicknessMeters) noexcept;
    [[nodiscard]] static double absorbedRadiationPowerWatts(
        const BroadbandSpectrum& irradiance,
        const RadiationMaterial& material,
        double projectedAreaSquareMeters) noexcept;
    [[nodiscard]] static double photopicIlluminanceLux(const GameSpectrum& visibleIrradiance) noexcept;
    [[nodiscard]] static double lightSensorCurrentAmperes(
        const LightSensor& sensor,
        const GameSpectrum& visibleIrradiance) noexcept;
    [[nodiscard]] static double focusedPowerWatts(
        const ThinLens& lens,
        double incidentIrradianceWattsPerSquareMeter,
        const glm::dvec3& targetWorldPosition) noexcept;
    static void stepThermalBody(
        ThermalBody& body,
        const FieldSample& field,
        double ambientTemperatureK,
        double deltaSeconds,
        double additionalFocusedPowerWatts = 0.0) noexcept;

private:
    std::vector<ElectricPointSource> electricSources_;
    std::vector<MagneticDipoleSource> magneticDipoles_;
    std::vector<SolenoidSource> solenoids_;
    std::vector<DisplacementCurrentSource> displacementSources_;
    std::vector<RadiationSource> radiationSources_;
};

} // namespace vf
