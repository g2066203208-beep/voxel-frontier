#include "vf/physics/MaterialPhysics.hpp"

#include <algorithm>
#include <cmath>

namespace vf {
namespace {

constexpr double kStefanBoltzmann = 5.670374419e-8;
constexpr double kEpsilon = 1.0e-12;

[[nodiscard]] double positive(double value) noexcept { return std::max(0.0, value); }

void sensibleHeat(
    const MaterialDefinition& material,
    double massKg,
    double targetTemperatureK,
    double& energyJ,
    MaterialState& state) noexcept {
    const double capacity = std::max(kEpsilon, massKg * std::max(1.0, material.specificHeatJPerKgK));
    const double needed = capacity * (targetTemperatureK - state.temperatureK);
    if ((energyJ > 0.0 && needed > 0.0 && energyJ >= needed)
        || (energyJ < 0.0 && needed < 0.0 && energyJ <= needed)) {
        state.temperatureK = targetTemperatureK;
        energyJ -= needed;
    } else {
        state.temperatureK += energyJ / capacity;
        energyJ = 0.0;
    }
}

} // namespace

BeamResponse evaluateBeamLoad(
    const MaterialDefinition& material,
    const BeamLoadSample& load) noexcept {
    BeamResponse response{};
    const double length = std::max(1.0e-6, load.restLengthMeters);
    response.axialStrain = (load.currentLengthMeters - length) / length;
    response.axialStressPa = material.youngModulusPa * response.axialStrain;

    // Euler-Bernoulli gameplay approximation: curvature ~= angle / span, surface strain = kappa*r.
    const double curvature = load.bendAngleRadians / length;
    response.bendingStressPa = material.youngModulusPa * curvature * std::max(0.0, load.outerRadiusMeters);
    response.equivalentStressPa = std::max(std::abs(response.axialStressPa), std::abs(response.bendingStressPa));
    return response;
}

void accumulateMechanicalDamage(
    const MaterialDefinition& material,
    const BeamResponse& response,
    double deltaSeconds,
    MaterialState& state) noexcept {
    if (state.fractured || deltaSeconds <= 0.0) return;

    const double yield = std::max(1.0, material.yieldStrengthPa);
    if (response.equivalentStressPa > yield) {
        const double overload = response.equivalentStressPa / yield - 1.0;
        state.plasticStrain += overload * deltaSeconds * 0.0025;
        state.damage = std::clamp(state.damage + overload * deltaSeconds * 0.18, 0.0, 1.0);
    }

    const bool axialFracture = std::abs(response.axialStrain) >= std::max(1.0e-6, material.fractureStrain);
    const bool strengthFracture = response.equivalentStressPa >= std::max(yield, material.ultimateStrengthPa);
    const bool accumulatedFracture = state.damage >= 1.0;
    if (axialFracture || strengthFracture || accumulatedFracture) {
        state.damage = 1.0;
        state.fractured = true;
    }
}

void applyThermalEnergy(
    const MaterialDefinition& material,
    double massKg,
    double energyJoules,
    MaterialState& state) noexcept {
    if (massKg <= kEpsilon || !std::isfinite(energyJoules)) return;
    double energy = energyJoules;

    for (int transition = 0; transition < 8 && std::abs(energy) > 1.0e-9; ++transition) {
        if (state.phase == MatterPhase::Solid) {
            state.liquidFraction = std::clamp(state.liquidFraction, 0.0, 1.0);
            if (energy <= 0.0) {
                sensibleHeat(material, massKg, 1.0, energy, state);
                break;
            }
            if (state.temperatureK < material.meltingPointK) {
                sensibleHeat(material, massKg, material.meltingPointK, energy, state);
                continue;
            }
            const double latent = massKg * std::max(1.0, material.latentHeatFusionJPerKg);
            const double remainingFraction = 1.0 - state.liquidFraction;
            const double consume = std::min(energy, latent * remainingFraction);
            state.liquidFraction += consume / latent;
            energy -= consume;
            if (state.liquidFraction >= 1.0 - 1.0e-9) {
                state.liquidFraction = 1.0;
                state.phase = MatterPhase::Liquid;
            } else {
                break;
            }
            continue;
        }

        if (state.phase == MatterPhase::Liquid) {
            state.liquidFraction = 1.0;
            if (energy > 0.0) {
                if (state.temperatureK < material.boilingPointK) {
                    sensibleHeat(material, massKg, material.boilingPointK, energy, state);
                    continue;
                }
                const double latent = massKg * std::max(1.0, material.latentHeatVaporizationJPerKg);
                const double remainingFraction = 1.0 - std::clamp(state.vaporFraction, 0.0, 1.0);
                const double consume = std::min(energy, latent * remainingFraction);
                state.vaporFraction += consume / latent;
                energy -= consume;
                if (state.vaporFraction >= 1.0 - 1.0e-9) {
                    state.vaporFraction = 1.0;
                    state.phase = MatterPhase::Gas;
                } else {
                    break;
                }
                continue;
            }

            if (state.temperatureK > material.freezingPointK) {
                sensibleHeat(material, massKg, material.freezingPointK, energy, state);
                continue;
            }
            const double latent = massKg * std::max(1.0, material.latentHeatFusionJPerKg);
            const double frozenFraction = 1.0 - state.liquidFraction;
            const double remainingToFreeze = 1.0 - frozenFraction;
            const double available = -energy;
            const double consume = std::min(available, latent * remainingToFreeze);
            state.liquidFraction -= consume / latent;
            energy += consume;
            if (state.liquidFraction <= 1.0e-9) {
                state.liquidFraction = 0.0;
                state.phase = MatterPhase::Solid;
            } else {
                break;
            }
            continue;
        }

        // Gas phase.
        state.vaporFraction = 1.0;
        if (energy >= 0.0) {
            const double capacity = massKg * std::max(1.0, material.specificHeatJPerKgK);
            state.temperatureK += energy / capacity;
            energy = 0.0;
            break;
        }
        if (state.temperatureK > material.boilingPointK) {
            sensibleHeat(material, massKg, material.boilingPointK, energy, state);
            continue;
        }
        const double latent = massKg * std::max(1.0, material.latentHeatVaporizationJPerKg);
        const double available = -energy;
        const double consume = std::min(available, latent * state.vaporFraction);
        state.vaporFraction -= consume / latent;
        energy += consume;
        if (state.vaporFraction <= 1.0e-9) {
            state.vaporFraction = 0.0;
            state.phase = MatterPhase::Liquid;
            state.liquidFraction = 1.0;
        } else {
            break;
        }
    }

    state.temperatureK = std::max(1.0, state.temperatureK);
    if (state.temperatureK >= material.ignitionPointK && state.phase != MatterPhase::Gas) state.ignited = true;
}

void stepThermalMaterial(
    const MaterialDefinition& material,
    double massKg,
    const ThermalExchange& exchange,
    double deltaSeconds,
    MaterialState& state) noexcept {
    if (deltaSeconds <= 0.0 || massKg <= kEpsilon) return;

    const double area = positive(exchange.surfaceAreaM2);
    const double convection = positive(exchange.convectionCoefficientWPerM2K)
        * area * (exchange.ambientTemperatureK - state.temperatureK);
    const double contact = positive(exchange.contactConductanceWPerK)
        * (exchange.neighborTemperatureK - state.temperatureK);
    const double radiation = std::clamp(material.emissivity, 0.0, 1.0)
        * kStefanBoltzmann * area
        * (std::pow(std::max(1.0, exchange.ambientTemperatureK), 4.0)
            - std::pow(std::max(1.0, state.temperatureK), 4.0));

    double netPower = exchange.absorbedPowerWatts + convection + contact + radiation;
    if (state.ignited && state.phase == MatterPhase::Solid && state.charFraction < 1.0) {
        // Deliberately bounded gameplay combustion: enough feedback to sustain a fire without
        // requiring combustion CFD or detailed chemistry.
        const double burnPower = 2200.0 * massKg * (1.0 - state.charFraction);
        netPower += burnPower;
        state.charFraction = std::clamp(state.charFraction + deltaSeconds * 0.015, 0.0, 1.0);
        if (state.charFraction >= 0.995) state.ignited = false;
    }
    applyThermalEnergy(material, massKg, netPower * deltaSeconds, state);

    const double humidity = std::clamp(exchange.ambientRelativeHumidity, 0.0, 1.0);
    if (exchange.ambientTemperatureK < 273.15 && humidity > 0.65 && state.temperatureK < 273.15) {
        const double cold = std::clamp((273.15 - state.temperatureK) / 30.0, 0.0, 2.0);
        const double moisture = (humidity - 0.65) / 0.35;
        state.frostThicknessMeters += 2.0e-6 * cold * moisture * deltaSeconds;
    } else if (state.frostThicknessMeters > 0.0 && state.temperatureK > 273.15) {
        const double meltRate = 1.0e-5 * std::clamp((state.temperatureK - 273.15) / 20.0, 0.1, 4.0);
        state.frostThicknessMeters = std::max(0.0, state.frostThicknessMeters - meltRate * deltaSeconds);
    }
}

double thermalEmissionScale(const MaterialState& state) noexcept {
    // Gameplay-visible incandescence begins around a dull red ~700 K and saturates before white-hot.
    return std::clamp((state.temperatureK - 700.0) / 1100.0, 0.0, 1.0);
}

} // namespace vf
