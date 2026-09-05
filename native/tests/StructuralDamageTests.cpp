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

vf::MaterialDefinition wood() {
    vf::MaterialDefinition material{};
    material.densityKgPerM3 = 650.0;
    material.ultimateStrengthPa = 42.0e6;
    material.shearStrengthPa = 8.0e6;
    material.fractureStrain = 0.025;
    material.fractureToughnessJPerM2 = 850.0;
    return material;
}

vf::StructuralAssembly makeThreeSegmentColumn() {
    vf::StructuralAssembly assembly{};
    (void)assembly.addChunk({1U, {0.0, 0.50, 0.0}, 40.0, false});
    (void)assembly.addChunk({2U, {0.0, 1.50, 0.0}, 40.0, false});
    (void)assembly.addChunk({3U, {0.0, 2.50, 0.0}, 40.0, false});
    (void)assembly.addBond({1U, 0U, {0.0, 0.0, 0.0}, {0.0, 1.0, 0.0}, 0.020, 0.10, 1.0, false});
    (void)assembly.addBond({1U, 2U, {0.0, 1.0, 0.0}, {0.0, 1.0, 0.0}, 0.020, 0.10, 1.0, false});
    (void)assembly.addBond({2U, 3U, {0.0, 2.0, 0.0}, {0.0, 1.0, 0.0}, 0.020, 0.10, 1.0, false});
    return assembly;
}

void testCutDamagesActualHitLocationOnly() {
    auto assembly = makeThreeSegmentColumn();
    vf::DamageEvent cut{};
    cut.type = vf::DamageType::Cut;
    cut.position = {0.0, 1.0, 0.0};
    cut.direction = {1.0, 0.0, 0.0};
    cut.radiusMeters = 0.26;
    cut.energyJoules = 5000.0;

    const auto result = assembly.applyDamage(cut, wood());
    require(result.topologyChanged, "a sufficiently energetic cut must break the local bond");
    require(assembly.bonds()[1].broken, "the bond at the exact hit height must break");
    require(!assembly.bonds()[0].broken, "the stump bond outside the cut radius must remain intact");
    require(!assembly.bonds()[2].broken, "the upper bond outside the cut radius must remain intact");
}

void testMovingCutChangesWhichBondBreaks() {
    auto lower = makeThreeSegmentColumn();
    auto upper = makeThreeSegmentColumn();

    vf::DamageEvent cut{};
    cut.type = vf::DamageType::Cut;
    cut.direction = {1.0, 0.0, 0.0};
    cut.radiusMeters = 0.25;
    cut.energyJoules = 5000.0;

    cut.position = {0.0, 1.0, 0.0};
    (void)lower.applyDamage(cut, wood());
    cut.position = {0.0, 2.0, 0.0};
    (void)upper.applyDamage(cut, wood());

    require(lower.bonds()[1].broken && !lower.bonds()[2].broken,
        "a low cut must only sever the low structural connection");
    require(!upper.bonds()[1].broken && upper.bonds()[2].broken,
        "moving the hit upward must move the fracture upward instead of using an object-specific root cut");
}

void testBrokenBondSplitsAnchoredAndFreeIslands() {
    auto assembly = makeThreeSegmentColumn();
    vf::DamageEvent cut{};
    cut.type = vf::DamageType::Cut;
    cut.position = {0.0, 1.0, 0.0};
    cut.direction = {0.0, 1.0, 0.0};
    cut.radiusMeters = 0.20;
    cut.energyJoules = 5000.0;
    const auto result = assembly.applyDamage(cut, wood());

    require(result.islands.size() == 2U, "breaking the middle support must split the graph into two islands");
    require(result.islands[0].worldAnchored, "the stump-side island must remain connected to world support");
    require(!result.islands[1].worldAnchored, "the detached upper island must be eligible to become rigid bodies");
    require(result.islands[1].chunkIds.size() == 2U,
        "still-connected upper chunks must remain one rigid island rather than exploding into arbitrary debris");
}

void testLowEnergyImpactDoesNotInventFracture() {
    auto assembly = makeThreeSegmentColumn();
    vf::DamageEvent tap{};
    tap.type = vf::DamageType::Impact;
    tap.position = {0.0, 1.0, 0.0};
    tap.radiusMeters = 0.30;
    tap.energyJoules = 2.0;
    const auto result = assembly.applyDamage(tap, wood());
    require(!result.topologyChanged, "a tiny impact must not fracture a healthy structural bond");
    require(assembly.bonds()[1].health < 1.0 && assembly.bonds()[1].health > 0.9,
        "subcritical local impacts may accumulate small damage without instantly breaking the object");
}

} // namespace

int main() {
    testCutDamagesActualHitLocationOnly();
    testMovingCutChangesWhichBondBreaks();
    testBrokenBondSplitsAnchoredAndFreeIslands();
    testLowEnergyImpactDoesNotInventFracture();
    std::cout << "vf_structural_damage_tests: PASS\n";
    return 0;
}
