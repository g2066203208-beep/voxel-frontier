#pragma once

#include <algorithm>

namespace vf {

struct GasChamber {
    double volumeM3{1.0};
    double amountMoles{40.0};
    double temperatureK{288.15};
    double molarMassKgPerMol{0.0289644};
    double heatCapacityRatio{1.4};
    double universalGasConstant{8.314462618};

    [[nodiscard]] double pressurePa() const noexcept;
    [[nodiscard]] double gasMassKg() const noexcept;
    [[nodiscard]] double densityKgPerM3() const noexcept;
    [[nodiscard]] double pistonForceN(double externalPressurePa, double pistonAreaM2) const noexcept;
    [[nodiscard]] double netBuoyantLiftN(double ambientDensityKgPerM3, double gravityMagnitude, double envelopeMassKg = 0.0) const noexcept;

    void setVolumeIsothermal(double newVolumeM3) noexcept;
    void setVolumeAdiabatic(double newVolumeM3) noexcept;
    void addHeatJoules(double heatJoules) noexcept;
};

} // namespace vf
