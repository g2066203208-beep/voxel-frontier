#include "vf/physics/StructuralDamage.hpp"

#include <cstdlib>
#include <iostream>
#include <string_view>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "STRUCTURAL DAMAGE TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

vf::MaterialDefinition steelLike() {
    vf::MaterialDefinition material{};
    material.hardnessPa = 1.8e9;
    material.ultimateStrengthPa = 500.0e6;
    material.shearStrengthPa = 300.0e6;
    material.bendingStrengthPa = 420.0e6;
    material.fractureToughnessJPerM2 = 12000.0;
    material.meltingPointK = 1800.0;
    return material;
}

void testStrongerMaterialHasLowerUtilization() {
    auto weak = steelLike();
    weak.ultimateStrengthPa *= 0.5;
    weak.shearStrengthPa *= 0.5;
    weak.bendingStrengthPa *= 0.5;
    auto strong = steelLike();

    vf::MaterialState state{};
    vf::StructuralBondGeometry geometry{};
    geometry.areaM2 = 0.01;
    geometry.sectionModulusM3 = 2.0e-4;
    vf::StructuralLoad load{};
    load.axialForceN = 1.5e6;
    load.shearForceN = 0.8e6;
    load.bendingMomentNm = 40000.0;

    const auto weakResponse = vf::evaluateStructuralBond(weak, state, geometry, load);
    const auto strongResponse = vf::evaluateStructuralBond(strong, state, geometry, load);
    require(strongResponse.strengthUtilization < weakResponse.strengthUtilization,
        "higher strength material must carry the same structural load at lower utilization");
}

void testHotMaterialSoftensAndBreaks() {
    const auto material = steelLike();
    vf::StructuralBondGeometry geometry{};
    geometry.areaM2 = 0.01;
    geometry.sectionModulusM3 = 2.0e-4;
    vf::StructuralLoad load{};
    load.axialForceN = 2.0e6;

    vf::MaterialState cold{};
    cold.temperatureK = 300.0;
    const auto coldResponse = vf::evaluateStructuralBond(material, cold, geometry, load);
    require(coldResponse.strengthUtilization < 1.0, "cold structural bond should survive the selected load");

    vf::MaterialState hot = cold;
    hot.temperatureK = 1750.0;
    const auto hotResponse = vf::evaluateStructuralBond(material, hot, geometry, load);
    require(hotResponse.strengthUtilization > coldResponse.strengthUtilization,
        "heating near melting must reduce structural strength");

    vf::StructuralBondState bond{};
    vf::accumulateStructuralBondDamage(hotResponse, 0.1, bond);
    require(bond.broken, "same load must be able to break a thermally softened bond");
}

void testImpactEnergyCanFractureBond() {
    const auto material = steelLike();
    vf::MaterialState state{};
    vf::StructuralBondGeometry geometry{};
    geometry.fractureAreaM2 = 0.002;
    vf::StructuralLoad impact{};
    impact.impactEnergyJ = material.fractureToughnessJPerM2 * geometry.fractureAreaM2 * 1.2;
    const auto response = vf::evaluateStructuralBond(material, state, geometry, impact);
    require(response.impactUtilization > 1.0, "impact energy above fracture capacity must exceed unity utilization");
    vf::StructuralBondState bond{};
    vf::accumulateStructuralBondDamage(response, 1.0 / 120.0, bond);
    require(bond.broken, "over-capacity impact must break the structural bond immediately");
}

void testRepeatedNearLimitLoadAccumulatesDamage() {
    const auto material = steelLike();
    vf::StructuralResponse response{};
    response.strengthUtilization = 0.92;
    vf::StructuralBondState bond{};
    for (int i = 0; i < 10000 && !bond.broken; ++i) {
        vf::accumulateStructuralBondDamage(response, 1.0 / 120.0, bond);
    }
    require(bond.damage > 0.0, "repeated high utilization must accumulate damage");
    require(bond.broken, "sustained near-limit loading must eventually break a structural bond");
}

void testHardnessControlsPermanentIndentation() {
    auto material = steelLike();
    const auto light = vf::evaluateHardnessContact(material, 120.0, 0.01, 1.0e-4, 0.01);
    require(light.hardnessUtilization < 1.0, "sub-hardness contact pressure must stay elastic in this gameplay model");
    require(light.permanentIndentationMeters == 0.0, "sub-hardness contact must not leave a permanent dent");

    const auto heavy = vf::evaluateHardnessContact(material, 4000.0, 0.002, 1.0e-5, 0.01);
    require(heavy.hardnessUtilization > 1.0, "high contact pressure must exceed hardness");
    require(heavy.permanentIndentationMeters > 0.0, "contact above hardness must create permanent indentation");
}

} // namespace

int main() {
    testStrongerMaterialHasLowerUtilization();
    testHotMaterialSoftensAndBreaks();
    testImpactEnergyCanFractureBond();
    testRepeatedNearLimitLoadAccumulatesDamage();
    testHardnessControlsPermanentIndentation();
    std::cout << "vf_structural_damage_tests: PASS\n";
    return 0;
}
