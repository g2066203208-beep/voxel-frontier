#include "vf/physics/StructuralDamage.hpp"

#include <algorithm>
#include <cmath>

namespace vf {
namespace {

constexpr double kEpsilon = 1.0e-12;

[[nodiscard]] double safeRatio(double numerator, double denominator) noexcept {
    return std::abs(numerator) / std::max(1.0, std::abs(denominator));
}

} // namespace

double temperatureStrengthScale(
    const MaterialDefinition& material,
    const MaterialState& state) noexcept {
    if (state.phase != MatterPhase::Solid) return 0.02;

    const double melt = std::max(2.0, material.meltingPointK);
    const double startSoftening = std::max(1.0, 0.60 * melt);
    if (state.temperatureK <= startSoftening) return 1.0;
    if (state.temperatureK >= melt) return 0.08;

    const double t = std::clamp((state.temperatureK - startSoftening) / (melt - startSoftening), 0.0, 1.0);
    // Preserve useful strength for warm components but rapidly soften near melting.
    return std::clamp(1.0 - 0.92 * t * t, 0.08, 1.0);
}

StructuralResponse evaluateStructuralBond(
    const MaterialDefinition& material,
    const MaterialState& materialState,
    const StructuralBondGeometry& geometry,
    const StructuralLoad& load) noexcept {
    StructuralResponse response{};
    const double area = std::max(kEpsilon, geometry.areaM2);
    const double sectionModulus = std::max(kEpsilon, geometry.sectionModulusM3);
    response.axialStressPa = std::abs(load.axialForceN) / area;
    response.shearStressPa = std::abs(load.shearForceN) / area;
    response.bendingStressPa = std::abs(load.bendingMomentNm) / sectionModulus;

    const double scale = temperatureStrengthScale(material, materialState);
    const double axialUtilization = safeRatio(response.axialStressPa, material.ultimateStrengthPa * scale);
    const double shearUtilization = safeRatio(response.shearStressPa, material.shearStrengthPa * scale);
    const double bendUtilization = safeRatio(response.bendingStressPa, material.bendingStrengthPa * scale);
    response.strengthUtilization = std::max({axialUtilization, shearUtilization, bendUtilization});

    const double fractureEnergyCapacity = std::max(
        kEpsilon,
        material.fractureToughnessJPerM2 * std::max(kEpsilon, geometry.fractureAreaM2));
    response.impactUtilization = std::max(0.0, load.impactEnergyJ) / fractureEnergyCapacity;
    return response;
}

void accumulateStructuralBondDamage(
    const StructuralResponse& response,
    double deltaSeconds,
    StructuralBondState& bondState) noexcept {
    if (bondState.broken || deltaSeconds <= 0.0) return;

    const double peak = std::max(response.strengthUtilization, response.impactUtilization);
    if (peak >= 1.0) {
        bondState.damage = 1.0;
        bondState.broken = true;
        return;
    }

    // Deliberately cheap progressive-fatigue law. Low utilization contributes essentially
    // nothing, while repeated near-limit loads accumulate visible structural degradation.
    if (peak > 0.35) {
        const double normalized = (peak - 0.35) / 0.65;
        const double rate = 0.24 * std::pow(normalized, 6.0);
        bondState.damage = std::clamp(bondState.damage + rate * deltaSeconds, 0.0, 1.0);
    }
    if (bondState.damage >= 1.0) bondState.broken = true;
}

HardnessContactResponse evaluateHardnessContact(
    const MaterialDefinition& material,
    double normalImpulseNs,
    double impactDurationSeconds,
    double contactAreaM2,
    double characteristicDepthMeters) noexcept {
    HardnessContactResponse response{};
    const double duration = std::max(1.0e-6, impactDurationSeconds);
    const double area = std::max(1.0e-10, contactAreaM2);
    const double averageForce = std::abs(normalImpulseNs) / duration;
    response.averagePressurePa = averageForce / area;
    response.hardnessUtilization = response.averagePressurePa / std::max(1.0, material.hardnessPa);

    if (response.hardnessUtilization > 1.0) {
        const double plasticFraction = std::clamp(
            1.0 - 1.0 / response.hardnessUtilization,
            0.0,
            1.0);
        response.permanentIndentationMeters = std::max(0.0, characteristicDepthMeters) * plasticFraction;
    }
    return response;
}

} // namespace vf
