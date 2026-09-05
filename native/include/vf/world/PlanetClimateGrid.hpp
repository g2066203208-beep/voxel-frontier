#pragma once

#include "vf/world/PlanetSurface.hpp"

#include <cstdint>
#include <vector>

#include <glm/glm.hpp>

namespace vf {

struct PlanetClimateConfig {
    std::uint32_t latitudeBands{24U};
    std::uint32_t longitudeBands{48U};
    double seaLevelPressurePa{101325.0};
    double molarMassKgPerMol{0.0289644};
    double lapseRateKPerM{0.0065};
    double dryAirGasConstant{287.05};
    double surfaceEmissivity{0.96};
    double clearSkyShortwaveAbsorption{0.23};
    double baseLandAlbedo{0.18};
    double baseOceanAlbedo{0.06};
    double cloudAlbedoContribution{0.35};
    double landHeatCapacityJPerM2K{2.0e6};
    double oceanMixedLayerDepthMeters{20.0};
    double oceanVolumetricHeatCapacityJPerM3K{4.10e6};
    double horizontalThermalDiffusivityM2PerS{8.0e5};
    double windDragTimeSeconds{43200.0};
    double moistureMixTimeSeconds{172800.0};
    double oceanEvaporationTimeSeconds{259200.0};
    double precipitationTimeSeconds{21600.0};
};

struct PlanetClimateCell {
    double temperatureK{288.15};
    double specificHumidity{0.0075};
    double cloudFraction{0.25};
    double precipitationRateKgPerM2S{};
    glm::dvec2 windEastNorthMps{};
};

struct PlanetClimateSample {
    double temperatureK{};
    double pressurePa{};
    double densityKgPerM3{};
    double relativeHumidity{};
    double cloudFraction{};
    double precipitationRateMmPerHour{};
    glm::dvec3 windBodyLocalMps{};
};

// Low-resolution primitive-equation-inspired climate field for gameplay. It is intentionally
// cheaper than a forecast model, but its forcing is causal: stellar shortwave heating, grey-body
// longwave cooling, surface heat capacity, moisture phase change, pressure-gradient acceleration,
// Coriolis acceleration and Rayleigh drag. No sinusoidal weather clock is used.
class PlanetClimateGrid final {
public:
    PlanetClimateGrid() = default;
    PlanetClimateGrid(
        PlanetDefinition planet,
        PlanetClimateConfig config = {},
        double spinRateRadPerSecond = 7.2921150e-5);

    void reset(
        PlanetDefinition planet,
        PlanetClimateConfig config = {},
        double spinRateRadPerSecond = 7.2921150e-5);

    void step(
        double deltaSeconds,
        const glm::dvec3& sunDirectionBodyLocal,
        double stellarIrradianceWm2);

    [[nodiscard]] PlanetClimateSample sample(
        const glm::dvec3& directionBodyLocal,
        double altitudeMeters = 0.0) const noexcept;

    [[nodiscard]] const PlanetClimateConfig& config() const noexcept { return config_; }
    [[nodiscard]] std::uint32_t latitudeBands() const noexcept { return latBands_; }
    [[nodiscard]] std::uint32_t longitudeBands() const noexcept { return lonBands_; }
    [[nodiscard]] const std::vector<PlanetClimateCell>& cells() const noexcept { return cells_; }

private:
    [[nodiscard]] std::size_t index(std::uint32_t lat, std::uint32_t lon) const noexcept;
    [[nodiscard]] glm::dvec3 directionAt(std::uint32_t lat, std::uint32_t lon) const noexcept;
    [[nodiscard]] double latitudeAt(std::uint32_t lat) const noexcept;
    [[nodiscard]] double saturationSpecificHumidity(double temperatureK, double pressurePa) const noexcept;

    PlanetDefinition planet_{};
    PlanetClimateConfig config_{};
    std::uint32_t latBands_{};
    std::uint32_t lonBands_{};
    double spinRateRadPerSecond_{};
    std::vector<PlanetClimateCell> cells_;
};

} // namespace vf
