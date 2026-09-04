#include "vf/physics/GasVolume.hpp"

#include <algorithm>
#include <cmath>

namespace vf {
namespace {

constexpr double kUniversalGasConstant = 8.314462618;
constexpr double kWaterMolarMass = 0.01801528;
constexpr double kEpsilon = 1.0e-12;

[[nodiscard]] double totalGasMassKg(const GasVolumeState& gas) noexcept {
    return std::max(0.0, gas.dryGasMassKg) + std::max(0.0, gas.waterVaporMassKg);
}

} // namespace

double gasDensityKgPerM3(const GasVolumeState& gas) noexcept {
    return totalGasMassKg(gas) / std::max(1.0e-9, gas.volumeM3);
}

double waterVaporPartialPressurePa(const GasVolumeState& gas) noexcept {
    const double moles = std::max(0.0, gas.waterVaporMassKg) / kWaterMolarMass;
    return moles * kUniversalGasConstant * std::max(1.0, gas.temperatureK)
        / std::max(1.0e-9, gas.volumeM3);
}

double gasPressurePa(const GasVolumeState& gas) noexcept {
    const double dryMoles = std::max(0.0, gas.dryGasMassKg)
        / std::max(1.0e-9, gas.dryGasMolarMassKgPerMol);
    const double vaporMoles = std::max(0.0, gas.waterVaporMassKg) / kWaterMolarMass;
    return (dryMoles + vaporMoles) * kUniversalGasConstant * std::max(1.0, gas.temperatureK)
        / std::max(1.0e-9, gas.volumeM3);
}

double saturationWaterVaporPressurePa(double temperatureK) noexcept {
    // Magnus-Tetens approximation. Accuracy is more than sufficient for gameplay fog/dew/frost.
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

void addHeatToGas(GasVolumeState& gas, double heatJoules, double effectiveSpecificHeatJPerKgK) noexcept {
    const double thermalMass = totalGasMassKg(gas) + std::max(0.0, gas.condensedFogMassKg);
    const double capacity = thermalMass * std::max(1.0, effectiveSpecificHeatJPerKgK);
    if (capacity <= kEpsilon || !std::isfinite(heatJoules)) return;
    gas.temperatureK = std::max(1.0, gas.temperatureK + heatJoules / capacity);
}

void stepCondensationAndFog(GasVolumeState& gas, double deltaSeconds) noexcept {
    if (deltaSeconds <= 0.0 || gas.volumeM3 <= kEpsilon) return;

    const double saturationPressure = saturationWaterVaporPressurePa(gas.temperatureK);
    const double saturationMoles = saturationPressure * gas.volumeM3
        / (kUniversalGasConstant * std::max(1.0, gas.temperatureK));
    const double saturationMass = saturationMoles * kWaterMolarMass;

    if (gas.waterVaporMassKg > saturationMass) {
        const double excess = gas.waterVaporMassKg - saturationMass;
        // Fast but not instantaneous droplet formation; keeps fog evolution visible in play.
        const double fraction = 1.0 - std::exp(-deltaSeconds / 0.35);
        const double condensed = excess * fraction;
        gas.waterVaporMassKg -= condensed;
        gas.condensedFogMassKg += condensed;
    } else if (gas.condensedFogMassKg > 0.0 && gas.waterVaporMassKg < saturationMass) {
        const double deficit = saturationMass - gas.waterVaporMassKg;
        const double fraction = 1.0 - std::exp(-deltaSeconds / 1.2);
        const double evaporated = std::min(gas.condensedFogMassKg, deficit * fraction);
        gas.condensedFogMassKg -= evaporated;
        gas.waterVaporMassKg += evaporated;
    }

    gas.waterVaporMassKg = std::max(0.0, gas.waterVaporMassKg);
    gas.condensedFogMassKg = std::max(0.0, gas.condensedFogMassKg);
}

void stepGasLeak(GasVolumeState& gas, const GasLeak& leak, double deltaSeconds) noexcept {
    if (deltaSeconds <= 0.0 || leak.openingAreaM2 <= 0.0 || gas.volumeM3 <= kEpsilon) return;

    const double internalPressure = gasPressurePa(gas);
    const double deltaPressure = internalPressure - std::max(0.0, leak.externalPressurePa);
    if (std::abs(deltaPressure) < 0.5) return;

    const double coefficient = std::clamp(leak.dischargeCoefficient, 0.0, 1.0);
    if (deltaPressure > 0.0) {
        const double density = std::max(1.0e-6, gasDensityKgPerM3(gas));
        const double massFlow = coefficient * leak.openingAreaM2
            * std::sqrt(2.0 * density * deltaPressure);
        const double available = totalGasMassKg(gas);
        const double removed = std::min(available, massFlow * deltaSeconds);
        if (removed <= 0.0 || available <= kEpsilon) return;
        const double dryFraction = gas.dryGasMassKg / available;
        const double vaporFraction = gas.waterVaporMassKg / available;
        gas.dryGasMassKg = std::max(0.0, gas.dryGasMassKg - removed * dryFraction);
        gas.waterVaporMassKg = std::max(0.0, gas.waterVaporMassKg - removed * vaporFraction);
    } else {
        const double externalDensity = std::max(1.0e-6, leak.externalDensityKgPerM3);
        const double massFlow = coefficient * leak.openingAreaM2
            * std::sqrt(2.0 * externalDensity * (-deltaPressure));
        const double added = massFlow * deltaSeconds;
        gas.dryGasMassKg += added;
        const double oldMass = totalGasMassKg(gas) - added;
        const double newMass = oldMass + added;
        if (newMass > kEpsilon) {
            gas.temperatureK = std::max(1.0,
                (gas.temperatureK * std::max(0.0, oldMass) + leak.externalTemperatureK * added) / newMass);
        }
    }
}

} // namespace vf
