#pragma once

#include <glm/glm.hpp>

namespace vf {

struct GasVolumeState {
    glm::dvec3 center{};
    double volumeM3{1.0};
    double dryGasMassKg{1.0};
    double waterVaporMassKg{};
    double condensedFogMassKg{};
    double temperatureK{293.15};
    double dryGasMolarMassKgPerMol{0.0289644};
    double fogMassExtinctionM2PerKg{140.0};
};

struct GasLeak {
    double openingAreaM2{};
    double dischargeCoefficient{0.62};
    double externalPressurePa{101325.0};
    double externalTemperatureK{293.15};
    double externalDensityKgPerM3{1.225};
};

[[nodiscard]] double gasDensityKgPerM3(const GasVolumeState& gas) noexcept;
[[nodiscard]] double gasPressurePa(const GasVolumeState& gas) noexcept;
[[nodiscard]] double waterVaporPartialPressurePa(const GasVolumeState& gas) noexcept;
[[nodiscard]] double saturationWaterVaporPressurePa(double temperatureK) noexcept;
[[nodiscard]] double relativeHumidity(const GasVolumeState& gas) noexcept;
[[nodiscard]] double fogMassDensityKgPerM3(const GasVolumeState& gas) noexcept;
[[nodiscard]] double fogExtinctionPerMeter(const GasVolumeState& gas) noexcept;
[[nodiscard]] double fogTransmittance(const GasVolumeState& gas, double pathLengthMeters) noexcept;

void addHeatToGas(GasVolumeState& gas, double heatJoules, double effectiveSpecificHeatJPerKgK = 1005.0) noexcept;
void stepCondensationAndFog(GasVolumeState& gas, double deltaSeconds) noexcept;
void stepGasLeak(GasVolumeState& gas, const GasLeak& leak, double deltaSeconds) noexcept;

} // namespace vf
