#pragma once

#include "vf/physics/MaterialPhysics.hpp"

namespace vf {

struct StructuralBondGeometry {
    double areaM2{0.01};
    double sectionModulusM3{1.0e-4};
    double fractureAreaM2{0.01};
};

struct StructuralLoad {
    double axialForceN{};
    double shearForceN{};
    double bendingMomentNm{};
    double impactEnergyJ{};
};

struct StructuralResponse {
    double axialStressPa{};
    double shearStressPa{};
    double bendingStressPa{};
    double strengthUtilization{};
    double impactUtilization{};
};

struct StructuralBondState {
    double damage{};
    bool broken{};
};

struct HardnessContactResponse {
    double averagePressurePa{};
    double hardnessUtilization{};
    double permanentIndentationMeters{};
};

[[nodiscard]] double temperatureStrengthScale(
    const MaterialDefinition& material,
    const MaterialState& state) noexcept;

[[nodiscard]] StructuralResponse evaluateStructuralBond(
    const MaterialDefinition& material,
    const MaterialState& materialState,
    const StructuralBondGeometry& geometry,
    const StructuralLoad& load) noexcept;

void accumulateStructuralBondDamage(
    const StructuralResponse& response,
    double deltaSeconds,
    StructuralBondState& bondState) noexcept;

[[nodiscard]] HardnessContactResponse evaluateHardnessContact(
    const MaterialDefinition& material,
    double normalImpulseNs,
    double impactDurationSeconds,
    double contactAreaM2,
    double characteristicDepthMeters) noexcept;

} // namespace vf
