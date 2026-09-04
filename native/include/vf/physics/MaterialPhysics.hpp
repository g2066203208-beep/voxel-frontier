#pragma once

#include <cstdint>

namespace vf {

enum class MatterPhase : std::uint8_t {
    Solid,
    Liquid,
    Gas,
};

struct MaterialDefinition {
    double densityKgPerM3{1000.0};
    double hardnessPa{1.0e8};
    double youngModulusPa{1.0e9};
    double yieldStrengthPa{5.0e7};
    double ultimateStrengthPa{1.0e8};
    double bendingStrengthPa{8.0e7};
    double shearStrengthPa{5.0e7};
    double fractureStrain{0.08};
    double fractureToughnessJPerM2{1000.0};

    double thermalConductivityWPerMK{0.5};
    double specificHeatJPerKgK{1000.0};
    double meltingPointK{1000.0};
    double boilingPointK{2000.0};
    double freezingPointK{995.0};
    double ignitionPointK{650.0};
    double latentHeatFusionJPerKg{2.0e5};
    double latentHeatVaporizationJPerKg{2.0e6};
    double emissivity{0.85};
};

struct MaterialState {
    double temperatureK{293.15};
    MatterPhase phase{MatterPhase::Solid};
    double liquidFraction{};
    double vaporFraction{};
    double plasticStrain{};
    double damage{};
    double frostThicknessMeters{};
    double charFraction{};
    bool ignited{};
    bool fractured{};
};

struct ThermalExchange {
    double absorbedPowerWatts{};
    double contactConductanceWPerK{};
    double neighborTemperatureK{293.15};
    double convectionCoefficientWPerM2K{8.0};
    double ambientTemperatureK{293.15};
    double ambientRelativeHumidity{0.5};
    double surfaceAreaM2{1.0};
};

struct BeamLoadSample {
    double restLengthMeters{1.0};
    double currentLengthMeters{1.0};
    double bendAngleRadians{};
    double outerRadiusMeters{0.05};
};

struct BeamResponse {
    double axialStrain{};
    double axialStressPa{};
    double bendingStressPa{};
    double equivalentStressPa{};
};

[[nodiscard]] BeamResponse evaluateBeamLoad(
    const MaterialDefinition& material,
    const BeamLoadSample& load) noexcept;

void accumulateMechanicalDamage(
    const MaterialDefinition& material,
    const BeamResponse& response,
    double deltaSeconds,
    MaterialState& state) noexcept;

void applyThermalEnergy(
    const MaterialDefinition& material,
    double massKg,
    double energyJoules,
    MaterialState& state) noexcept;

void stepThermalMaterial(
    const MaterialDefinition& material,
    double massKg,
    const ThermalExchange& exchange,
    double deltaSeconds,
    MaterialState& state) noexcept;

[[nodiscard]] double thermalEmissionScale(const MaterialState& state) noexcept;

} // namespace vf
