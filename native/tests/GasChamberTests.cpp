#include "vf/physics/GasChamber.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

} // namespace

int main() {
    vf::GasChamber chamber{};
    chamber.volumeM3 = 1.0;
    chamber.amountMoles = 42.0;
    chamber.temperatureK = 290.0;
    const double initialPressure = chamber.pressurePa();

    chamber.setVolumeIsothermal(0.5);
    require(std::abs(chamber.pressurePa() / initialPressure - 2.0) < 1.0e-12, "isothermal half-volume compression should double ideal-gas pressure");

    const double temperatureBeforeAdiabatic = chamber.temperatureK;
    chamber.setVolumeAdiabatic(0.25);
    require(chamber.temperatureK > temperatureBeforeAdiabatic, "adiabatic compression should raise gas temperature");
    require(chamber.pressurePa() > initialPressure * 2.0, "adiabatic compression should raise pressure beyond the previous compressed state");

    const double temperatureBeforeHeat = chamber.temperatureK;
    chamber.addHeatJoules(5000.0);
    require(chamber.temperatureK > temperatureBeforeHeat, "positive heat input must raise gas temperature");

    vf::GasChamber liftingGas{};
    liftingGas.volumeM3 = 10.0;
    liftingGas.amountMoles = 40.0;
    liftingGas.molarMassKgPerMol = 0.0040026;
    liftingGas.temperatureK = 288.15;
    require(liftingGas.netBuoyantLiftN(1.225, 9.81, 2.0) > 0.0, "low-density sealed lifting-gas chamber should have positive net buoyant lift when displaced air is heavier");

    std::cout << "vf_gas_chamber_tests: PASS\n";
    return 0;
}
