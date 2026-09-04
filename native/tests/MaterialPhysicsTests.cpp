#include "vf/physics/MaterialPhysics.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "MATERIAL PHYSICS TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void testElasticBendingAndFracture() {
    vf::MaterialDefinition wood{};
    wood.youngModulusPa = 9.0e9;
    wood.yieldStrengthPa = 35.0e6;
    wood.ultimateStrengthPa = 70.0e6;
    wood.fractureStrain = 0.025;

    vf::BeamLoadSample mild{};
    mild.restLengthMeters = 2.0;
    mild.currentLengthMeters = 2.002;
    mild.bendAngleRadians = 0.01;
    mild.outerRadiusMeters = 0.04;
    const auto mildResponse = vf::evaluateBeamLoad(wood, mild);
    require(mildResponse.equivalentStressPa > 0.0, "bending must create material stress");

    vf::MaterialState state{};
    vf::accumulateMechanicalDamage(wood, mildResponse, 0.1, state);
    require(!state.fractured, "small elastic load must not fracture the beam");

    vf::BeamLoadSample overload = mild;
    overload.currentLengthMeters = 2.12;
    const auto overloadResponse = vf::evaluateBeamLoad(wood, overload);
    vf::accumulateMechanicalDamage(wood, overloadResponse, 0.1, state);
    require(state.fractured && state.damage >= 1.0, "over-limit strain must fracture the material");
}

void testMeltingBoilingAndFreezingConsumeLatentHeat() {
    vf::MaterialDefinition material{};
    material.specificHeatJPerKgK = 1000.0;
    material.meltingPointK = 350.0;
    material.freezingPointK = 350.0;
    material.boilingPointK = 450.0;
    material.latentHeatFusionJPerKg = 100000.0;
    material.latentHeatVaporizationJPerKg = 300000.0;

    vf::MaterialState state{};
    state.temperatureK = 300.0;

    // 50 kJ reaches the melting point, another 100 kJ melts one kilogram.
    vf::applyThermalEnergy(material, 1.0, 150000.0, state);
    require(state.phase == vf::MatterPhase::Liquid, "latent fusion energy must produce a liquid phase");
    require(std::abs(state.temperatureK - 350.0) < 1.0e-6, "temperature must pause at melting point during fusion");

    // 100 kJ sensible heat to boiling plus 300 kJ vaporization.
    vf::applyThermalEnergy(material, 1.0, 400000.0, state);
    require(state.phase == vf::MatterPhase::Gas, "latent vaporization energy must produce gas");

    // Reverse the same vaporization and sensible heat, then freeze.
    vf::applyThermalEnergy(material, 1.0, -500000.0, state);
    require(state.phase == vf::MatterPhase::Solid, "sufficient cooling must condense and freeze the material");
    require(state.temperatureK <= 350.0 + 1.0e-6, "frozen material must not remain above its freezing point");
}

void testContactHeatTransferAndFrost() {
    vf::MaterialDefinition metal{};
    metal.specificHeatJPerKgK = 500.0;
    metal.ignitionPointK = 2000.0;

    vf::MaterialState state{};
    state.temperatureK = 260.0;

    vf::ThermalExchange coldHumid{};
    coldHumid.ambientTemperatureK = 255.0;
    coldHumid.ambientRelativeHumidity = 0.95;
    coldHumid.surfaceAreaM2 = 1.0;
    for (int i = 0; i < 120; ++i) vf::stepThermalMaterial(metal, 1.0, coldHumid, 1.0, state);
    require(state.frostThicknessMeters > 0.0, "cold humid material must accumulate frost");

    const double frost = state.frostThicknessMeters;
    vf::ThermalExchange warm{};
    warm.ambientTemperatureK = 310.0;
    warm.neighborTemperatureK = 360.0;
    warm.contactConductanceWPerK = 20.0;
    warm.surfaceAreaM2 = 1.0;
    for (int i = 0; i < 300; ++i) vf::stepThermalMaterial(metal, 1.0, warm, 0.1, state);
    require(state.temperatureK > 273.15, "contact conduction must warm the cold material");
    require(state.frostThicknessMeters < frost, "frost must melt after the surface warms above freezing");
}

void testIncandescenceScale() {
    vf::MaterialState state{};
    state.temperatureK = 650.0;
    require(vf::thermalEmissionScale(state) == 0.0, "cool material must not visibly glow");
    state.temperatureK = 1250.0;
    require(vf::thermalEmissionScale(state) > 0.0 && vf::thermalEmissionScale(state) < 1.0,
        "hot material must enter visible incandescence range");
}

} // namespace

int main() {
    testElasticBendingAndFracture();
    testMeltingBoilingAndFreezingConsumeLatentHeat();
    testContactHeatTransferAndFrost();
    testIncandescenceScale();
    std::cout << "vf_material_physics_tests: PASS\n";
    return 0;
}
