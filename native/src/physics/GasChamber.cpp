#include "vf/physics/GasChamber.hpp"

#include <cmath>

namespace vf {

double GasChamber::pressurePa() const noexcept {
    const double volume = std::max(volumeM3, 1.0e-9);
    const double moles = std::max(amountMoles, 0.0);
    const double temperature = std::max(temperatureK, 1.0);
    return moles * universalGasConstant * temperature / volume;
}

double GasChamber::gasMassKg() const noexcept {
    return std::max(0.0, amountMoles) * std::max(0.0, molarMassKgPerMol);
}

double GasChamber::densityKgPerM3() const noexcept {
    return gasMassKg() / std::max(volumeM3, 1.0e-9);
}

double GasChamber::pistonForceN(double externalPressurePa, double pistonAreaM2) const noexcept {
    return (pressurePa() - std::max(0.0, externalPressurePa)) * std::max(0.0, pistonAreaM2);
}

double GasChamber::netBuoyantLiftN(double ambientDensityKgPerM3, double gravityMagnitude, double envelopeMassKg) const noexcept {
    const double displacedFluidMass = std::max(0.0, ambientDensityKgPerM3) * std::max(0.0, volumeM3);
    const double systemMass = gasMassKg() + std::max(0.0, envelopeMassKg);
    return (displacedFluidMass - systemMass) * std::max(0.0, gravityMagnitude);
}

void GasChamber::setVolumeIsothermal(double newVolumeM3) noexcept {
    volumeM3 = std::max(newVolumeM3, 1.0e-9);
}

void GasChamber::setVolumeAdiabatic(double newVolumeM3) noexcept {
    const double oldVolume = std::max(volumeM3, 1.0e-9);
    const double targetVolume = std::max(newVolumeM3, 1.0e-9);
    const double gammaMinusOne = std::max(0.0, heatCapacityRatio - 1.0);
    temperatureK = std::max(1.0, temperatureK * std::pow(oldVolume / targetVolume, gammaMinusOne));
    volumeM3 = targetVolume;
}

void GasChamber::addHeatJoules(double heatJoules) noexcept {
    const double moles = std::max(amountMoles, 1.0e-12);
    const double gamma = std::max(1.000001, heatCapacityRatio);
    const double molarCv = universalGasConstant / (gamma - 1.0);
    temperatureK = std::max(1.0, temperatureK + heatJoules / (moles * molarCv));
}

} // namespace vf
