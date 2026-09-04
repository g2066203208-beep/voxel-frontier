#include "vf/physics/GasVolume.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

namespace {
[[noreturn]] void fail(std::string_view message) { std::cerr << "GAS VOLUME TEST FAILURE: " << message << '\n'; std::exit(1); }
void require(bool condition, std::string_view message) { if (!condition) fail(message); }

void testPressureRespondsToVolumeAndTemperature() {
    vf::GasVolumeState gas{}; gas.volumeM3 = 1.0; gas.dryGasMassKg = 1.2; gas.temperatureK = 293.15;
    const double p1 = vf::gasPressurePa(gas);
    vf::setGasVolumeIsothermal(gas, 0.5);
    const double p2 = vf::gasPressurePa(gas);
    require(p2 > p1 * 1.95 && p2 < p1 * 2.05, "halving gas volume must approximately double pressure");
    vf::setGasVolumeIsothermal(gas, 1.0); gas.temperatureK *= 2.0;
    const double p3 = vf::gasPressurePa(gas);
    require(p3 > p1 * 1.95 && p3 < p1 * 2.05, "doubling absolute temperature must approximately double pressure");
}
void testAdiabaticCompression() {
    vf::GasVolumeState gas{}; gas.volumeM3 = 1.0; gas.dryGasMassKg = 1.2; gas.temperatureK = 290.0;
    const double t = gas.temperatureK; const double p = vf::gasPressurePa(gas);
    vf::setGasVolumeAdiabatic(gas, 0.5);
    require(gas.temperatureK > t, "adiabatic compression must heat the authoritative gas volume");
    require(vf::gasPressurePa(gas) > p * 2.0, "adiabatic compression must raise pressure more than isothermal compression");
}
void testPistonAndBuoyancy() {
    vf::GasVolumeState gas{}; gas.volumeM3 = 4.0; gas.dryGasMassKg = 3.0; gas.temperatureK = 310.0;
    require(vf::gasPistonForceN(gas, 50000.0, 0.02) > 0.0, "pressurized gas must produce piston force");
    require(vf::gasNetBuoyantLiftN(gas, 1.225, 9.81, 1.0) > 0.0, "light sealed gas volume must produce positive lift");
}
void testCoolingCreatesFogAndWarmingEvaporatesIt() {
    vf::GasVolumeState gas{}; gas.volumeM3 = 1.0; gas.dryGasMassKg = 1.1; gas.waterVaporMassKg = 0.020; gas.temperatureK = 278.15;
    for (int i = 0; i < 120; ++i) vf::stepCondensationAndFog(gas, 0.05);
    require(gas.condensedFogMassKg > 0.0, "supersaturated cool gas must form suspended fog droplets");
    require(vf::fogExtinctionPerMeter(gas) > 0.0, "fog mass density must create optical extinction");
    require(vf::fogTransmittance(gas, 20.0) < 1.0, "fog must reduce long-path transmittance");
    const double condensed = gas.condensedFogMassKg; gas.temperatureK = 315.0;
    for (int i = 0; i < 400; ++i) vf::stepCondensationAndFog(gas, 0.05);
    require(gas.condensedFogMassKg < condensed, "warming undersaturated gas must evaporate fog droplets");
}
void testLeakMovesPressureTowardAmbient() {
    vf::GasVolumeState gas{}; gas.volumeM3 = 0.5; gas.dryGasMassKg = 1.5; gas.temperatureK = 293.15;
    vf::GasLeak leak{}; leak.openingAreaM2 = 1.0e-4; leak.externalPressurePa = 101325.0; leak.externalDensityKgPerM3 = 1.225;
    const double initialDifference = std::abs(vf::gasPressurePa(gas) - leak.externalPressurePa);
    for (int i = 0; i < 1000; ++i) vf::stepGasLeak(gas, leak, 0.01);
    require(std::abs(vf::gasPressurePa(gas) - leak.externalPressurePa) < initialDifference, "an open gas volume must move toward external pressure");
}
void testHeatChangesGasState() {
    vf::GasVolumeState gas{}; gas.volumeM3 = 1.0; gas.dryGasMassKg = 1.0; gas.temperatureK = 290.0;
    const double before = vf::gasPressurePa(gas); vf::addHeatToGas(gas, 10050.0, 1005.0);
    require(gas.temperatureK > 299.0, "added heat must raise gas temperature");
    require(vf::gasPressurePa(gas) > before, "heating a fixed volume must raise pressure");
}
}
int main() {
    testPressureRespondsToVolumeAndTemperature(); testAdiabaticCompression(); testPistonAndBuoyancy();
    testCoolingCreatesFogAndWarmingEvaporatesIt(); testLeakMovesPressureTowardAmbient(); testHeatChangesGasState();
    std::cout << "vf_gas_volume_tests: PASS\n"; return 0;
}
