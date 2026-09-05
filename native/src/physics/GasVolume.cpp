#include "vf/physics/GasVolume.hpp"

#include <algorithm>
#include <cmath>

namespace vf {
namespace {

constexpr double kUniversalGasConstant = 8.314462618;
constexpr double kWaterMolarMass = 0.01801528;
constexpr double kEpsilon = 1.0e-12;

[[nodiscard]] double dryGasMoles(const GasVolumeState& gas) noexcept {
    return std::max(0.0, gas.dryGasMassKg) / std::max(1.0e-9, gas.dryGasMolarMassKgPerMol);
}
[[nodiscard]] double vaporMoles(const GasVolumeState& gas) noexcept {
    return std::max(0.0, gas.waterVaporMassKg) / kWaterMolarMass;
}

} // namespace

double gasMassKg(const GasVolumeState& gas) noexcept {
    return std::max(0.0, gas.dryGasMassKg) + std::max(0.0, gas.waterVaporMassKg);
}
double gasMoles(const GasVolumeState& gas) noexcept { return dryGasMoles(gas) + vaporMoles(gas); }
double gasDensityKgPerM3(const GasVolumeState& gas) noexcept { return gasMassKg(gas) / std::max(1.0e-9, gas.volumeM3); }
double waterVaporPartialPressurePa(const GasVolumeState& gas) noexcept {
    return vaporMoles(gas) * kUniversalGasConstant * std::max(1.0, gas.temperatureK) / std::max(1.0e-9, gas.volumeM3);
}
double gasPressurePa(const GasVolumeState& gas) noexcept {
    return gasMoles(gas) * kUniversalGasConstant * std::max(1.0, gas.temperatureK) / std::max(1.0e-9, gas.volumeM3);
}
double saturationWaterVaporPressurePa(double temperatureK) noexcept {
    const double celsius = std::clamp(temperatureK - 273.15, -80.0, 80.0);
    const double a = celsius >= 0.0 ? 17.625 : 22.587;
    const double b = celsius >= 0.0 ? 243.04 : 273.86;
    return 610.94 * std::exp(a * celsius / (celsius + b));
}
double relativeHumidity(const GasVolumeState& gas) noexcept {
    const double saturation = std::max(1.0e-9, saturationWaterVaporPressurePa(gas.temperatureK));
    return std::max(0.0, waterVaporPartialPressurePa(gas) / saturation);
}
double fogMassDensityKgPerM3(const GasVolumeState& gas) noexcept {
    return std::max(0.0, gas.condensedFogMassKg) / std::max(1.0e-9, gas.volumeM3);
}
double fogExtinctionPerMeter(const GasVolumeState& gas) noexcept {
    return fogMassDensityKgPerM3(gas) * std::max(0.0, gas.fogMassExtinctionM2PerKg);
}
double fogTransmittance(const GasVolumeState& gas, double pathLengthMeters) noexcept {
    return std::exp(-fogExtinctionPerMeter(gas) * std::max(0.0, pathLengthMeters));
}
double gasPistonForceN(const GasVolumeState& gas, double externalPressurePa, double pistonAreaM2) noexcept {
    return (gasPressurePa(gas) - std::max(0.0, externalPressurePa)) * std::max(0.0, pistonAreaM2);
}
double gasNetBuoyantLiftN(const GasVolumeState& gas, double ambientDensityKgPerM3,
    double gravityMagnitude, double envelopeMassKg) noexcept {
    const double displacedFluidMass = std::max(0.0, ambientDensityKgPerM3) * std::max(0.0, gas.volumeM3);
    const double carriedMass = gasMassKg(gas) + std::max(0.0, gas.condensedFogMassKg) + std::max(0.0, envelopeMassKg);
    return (displacedFluidMass - carriedMass) * std::max(0.0, gravityMagnitude);
}
void setGasVolumeIsothermal(GasVolumeState& gas, double newVolumeM3) noexcept { gas.volumeM3 = std::max(1.0e-9, newVolumeM3); }
void setGasVolumeAdiabatic(GasVolumeState& gas, double newVolumeM3) noexcept {
    const double oldVolume = std::max(1.0e-9, gas.volumeM3);
    const double targetVolume = std::max(1.0e-9, newVolumeM3);
    gas.temperatureK = std::max(1.0, gas.temperatureK * std::pow(oldVolume / targetVolume,
        std::max(0.0, gas.heatCapacityRatio - 1.0)));
    gas.volumeM3 = targetVolume;
}
void addHeatToGas(GasVolumeState& gas, double heatJoules, double effectiveSpecificHeatJPerKgK) noexcept {
    const double thermalMass = gasMassKg(gas) + std::max(0.0, gas.condensedFogMassKg);
    const double capacity = thermalMass * std::max(1.0, effectiveSpecificHeatJPerKgK);
    if (capacity <= kEpsilon || !std::isfinite(heatJoules)) return;
    gas.temperatureK = std::max(1.0, gas.temperatureK + heatJoules / capacity);
}
void stepCondensationAndFog(GasVolumeState& gas, double deltaSeconds) noexcept {
    if (deltaSeconds <= 0.0 || gas.volumeM3 <= kEpsilon) return;
    const double saturationPressure = saturationWaterVaporPressurePa(gas.temperatureK);
    const double saturationMoles = saturationPressure * gas.volumeM3 / (kUniversalGasConstant * std::max(1.0, gas.temperatureK));
    const double saturationMass = saturationMoles * kWaterMolarMass;
    if (gas.waterVaporMassKg > saturationMass) {
        const double excess = gas.waterVaporMassKg - saturationMass;
        const double condensed = excess * (1.0 - std::exp(-deltaSeconds / 0.35));
        gas.waterVaporMassKg -= condensed;
        gas.condensedFogMassKg += condensed;
    } else if (gas.condensedFogMassKg > 0.0 && gas.waterVaporMassKg < saturationMass) {
        const double deficit = saturationMass - gas.waterVaporMassKg;
        const double evaporated = std::min(gas.condensedFogMassKg, deficit * (1.0 - std::exp(-deltaSeconds / 1.2)));
        gas.condensedFogMassKg -= evaporated;
        gas.waterVaporMassKg += evaporated;
    }
    gas.waterVaporMassKg = std::max(0.0, gas.waterVaporMassKg);
    gas.condensedFogMassKg = std::max(0.0, gas.condensedFogMassKg);
}
void stepGasLeak(GasVolumeState& gas, const GasLeak& leak, double deltaSeconds) noexcept {
    if (deltaSeconds <= 0.0 || leak.openingAreaM2 <= 0.0 || gas.volumeM3 <= kEpsilon) return;
    const double deltaPressure = gasPressurePa(gas) - std::max(0.0, leak.externalPressurePa);
    if (std::abs(deltaPressure) < 0.5) return;
    const double coefficient = std::clamp(leak.dischargeCoefficient, 0.0, 1.0);
    if (deltaPressure > 0.0) {
        const double density = std::max(1.0e-6, gasDensityKgPerM3(gas));
        const double removed = std::min(gasMassKg(gas), coefficient * leak.openingAreaM2
            * std::sqrt(2.0 * density * deltaPressure) * deltaSeconds);
        const double available = gasMassKg(gas);
        if (removed <= 0.0 || available <= kEpsilon) return;
        const double dryFraction = gas.dryGasMassKg / available;
        const double vaporFraction = gas.waterVaporMassKg / available;
        gas.dryGasMassKg = std::max(0.0, gas.dryGasMassKg - removed * dryFraction);
        gas.waterVaporMassKg = std::max(0.0, gas.waterVaporMassKg - removed * vaporFraction);
    } else {
        const double massFlow = coefficient * leak.openingAreaM2
            * std::sqrt(2.0 * std::max(1.0e-6, leak.externalDensityKgPerM3) * (-deltaPressure));
        const double added = massFlow * deltaSeconds;
        const double oldMass = gasMassKg(gas);
        gas.dryGasMassKg += added;
        const double newMass = oldMass + added;
        if (newMass > kEpsilon) gas.temperatureK = std::max(1.0,
            (gas.temperatureK * std::max(0.0, oldMass) + leak.externalTemperatureK * added) / newMass);
    }
}

} // namespace vf
