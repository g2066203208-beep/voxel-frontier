#include "vf/physics/ElectromagneticRadiation.hpp"

#include <algorithm>
#include <cmath>
#include <numeric>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;
constexpr double kEpsilon = 1.0e-12;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= kEpsilon) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] double clampUnit(double value) noexcept {
    return std::clamp(value, 0.0, 1.0);
}

[[nodiscard]] glm::dvec3 dipoleField(
    const glm::dvec3& sourcePosition,
    const glm::dvec3& magneticMoment,
    double softeningRadius,
    const glm::dvec3& worldPosition) noexcept {
    const glm::dvec3 displacement = worldPosition - sourcePosition;
    const double rawDistance = glm::length(displacement);
    if (rawDistance <= kEpsilon) return {};

    const glm::dvec3 radial = displacement / rawDistance;
    const double distance = std::max(rawDistance, std::max(softeningRadius, 1.0e-4));
    const double scale = ElectromagneticRadiationSystem::kVacuumPermeability
        / (4.0 * kPi * distance * distance * distance);
    return scale * (3.0 * radial * glm::dot(magneticMoment, radial) - magneticMoment);
}

[[nodiscard]] double sourceSolidAngle(double coneCosine) noexcept {
    if (coneCosine <= -1.0) return 4.0 * kPi;
    return std::max(1.0e-6, 2.0 * kPi * (1.0 - std::clamp(coneCosine, -1.0, 0.999999)));
}

} // namespace

double ElectromagneticRadiationSystem::BroadbandSpectrum::total() const noexcept {
    return std::accumulate(values.begin(), values.end(), 0.0);
}

void ElectromagneticRadiationSystem::addElectricSource(ElectricPointSource source) {
    source.softeningRadiusMeters = std::max(1.0e-4, source.softeningRadiusMeters);
    source.maxRangeMeters = std::max(source.softeningRadiusMeters, source.maxRangeMeters);
    electricSources_.push_back(source);
}

void ElectromagneticRadiationSystem::addMagneticDipole(MagneticDipoleSource source) {
    source.softeningRadiusMeters = std::max(1.0e-4, source.softeningRadiusMeters);
    source.maxRangeMeters = std::max(source.softeningRadiusMeters, source.maxRangeMeters);
    magneticDipoles_.push_back(source);
}

void ElectromagneticRadiationSystem::addSolenoid(SolenoidSource source) {
    source.axis = safeNormalize(source.axis);
    source.turns = std::max(0.0, source.turns);
    source.lengthMeters = std::max(1.0e-4, source.lengthMeters);
    source.radiusMeters = std::max(1.0e-4, source.radiusMeters);
    source.relativePermeability = std::max(0.0, source.relativePermeability);
    source.maxRangeMeters = std::max(source.radiusMeters, source.maxRangeMeters);
    solenoids_.push_back(source);
}

void ElectromagneticRadiationSystem::addDisplacementCurrentSource(DisplacementCurrentSource source) {
    source.axis = safeNormalize(source.axis);
    source.coreRadiusMeters = std::max(1.0e-4, source.coreRadiusMeters);
    source.maxRangeMeters = std::max(source.coreRadiusMeters, source.maxRangeMeters);
    displacementSources_.push_back(source);
}

void ElectromagneticRadiationSystem::addRadiationSource(RadiationSource source) {
    source.direction = safeNormalize(source.direction, {0.0, 0.0, 1.0});
    source.minimumDistanceMeters = std::max(1.0e-4, source.minimumDistanceMeters);
    source.maxRangeMeters = std::max(source.minimumDistanceMeters, source.maxRangeMeters);
    for (auto& power : source.powerWatts.values) power = std::max(0.0, power);
    for (auto& value : source.visibleShape.values) value = std::max(0.0, value);
    radiationSources_.push_back(source);
}

void ElectromagneticRadiationSystem::clearSources() noexcept {
    electricSources_.clear();
    magneticDipoles_.clear();
    solenoids_.clear();
    displacementSources_.clear();
    radiationSources_.clear();
}

ElectromagneticRadiationSystem::FieldSample ElectromagneticRadiationSystem::sample(
    const glm::dvec3& worldPosition) const noexcept {
    FieldSample result{};

    for (const auto& source : electricSources_) {
        const glm::dvec3 displacement = worldPosition - source.position;
        const double distanceSquared = glm::dot(displacement, displacement);
        if (distanceSquared <= kEpsilon) continue;
        const double rawDistance = std::sqrt(distanceSquared);
        if (rawDistance > source.maxRangeMeters) continue;

        const double softenedSquared = distanceSquared
            + source.softeningRadiusMeters * source.softeningRadiusMeters;
        const double inverseSoftenedCube = 1.0 / std::pow(softenedSquared, 1.5);
        result.electricFieldVoltsPerMeter +=
            kCoulombConstant * source.chargeCoulombs * displacement * inverseSoftenedCube;
    }

    for (const auto& source : magneticDipoles_) {
        if (glm::distance(source.position, worldPosition) > source.maxRangeMeters) continue;
        result.magneticFieldTesla += dipoleField(
            source.position,
            source.magneticMomentAmpereSquareMeters,
            source.softeningRadiusMeters,
            worldPosition);
    }

    for (const auto& source : solenoids_) {
        const glm::dvec3 displacement = worldPosition - source.position;
        const double distance = glm::length(displacement);
        if (distance > source.maxRangeMeters) continue;

        const double axial = glm::dot(displacement, source.axis);
        const glm::dvec3 radialVector = displacement - source.axis * axial;
        const double radialDistance = glm::length(radialVector);
        const bool inside = std::abs(axial) <= 0.5 * source.lengthMeters
            && radialDistance <= source.radiusMeters;

        if (inside) {
            const double turnsPerMeter = source.turns / source.lengthMeters;
            const double magnitude = kVacuumPermeability * source.relativePermeability
                * turnsPerMeter * source.currentAmperes;
            result.magneticFieldTesla += source.axis * magnitude;
        } else {
            const double loopArea = kPi * source.radiusMeters * source.radiusMeters;
            const glm::dvec3 magneticMoment = source.axis
                * (source.relativePermeability * source.turns * source.currentAmperes * loopArea);
            result.magneticFieldTesla += dipoleField(
                source.position,
                magneticMoment,
                source.radiusMeters * 0.5,
                worldPosition);
        }
    }

    for (const auto& source : displacementSources_) {
        const glm::dvec3 displacement = worldPosition - source.position;
        if (glm::length(displacement) > source.maxRangeMeters) continue;
        const double axial = glm::dot(displacement, source.axis);
        const glm::dvec3 radialVector = displacement - source.axis * axial;
        const double rawRadius = glm::length(radialVector);
        if (rawRadius <= kEpsilon) continue;

        const glm::dvec3 radial = radialVector / rawRadius;
        const glm::dvec3 azimuth = safeNormalize(glm::cross(source.axis, radial), {1.0, 0.0, 0.0});
        const double effectiveRadius = std::max(rawRadius, source.coreRadiusMeters);
        const double magnitude = kVacuumPermeability * kVacuumPermittivity
            * source.electricFluxRateVoltMetersPerSecond
            / (2.0 * kPi * effectiveRadius);
        result.magneticFieldTesla += azimuth * magnitude;
    }

    for (const auto& source : radiationSources_) {
        const glm::dvec3 displacement = worldPosition - source.position;
        const double rawDistance = glm::length(displacement);
        if (rawDistance <= kEpsilon || rawDistance > source.maxRangeMeters) continue;
        const glm::dvec3 radial = displacement / rawDistance;

        if (source.coneCosine > -1.0
            && glm::dot(source.direction, radial) < source.coneCosine) {
            continue;
        }

        const double distance = std::max(rawDistance, source.minimumDistanceMeters);
        const double denominator = sourceSolidAngle(source.coneCosine) * distance * distance;
        if (denominator <= kEpsilon) continue;

        for (std::size_t i = 0; i < kRadiationBandCount; ++i) {
            result.irradianceWattsPerSquareMeter.values[i] += source.powerWatts.values[i] / denominator;
        }

        const double visiblePower = source.powerWatts[RadiationBand::Visible];
        if (visiblePower <= 0.0) continue;
        const double shapeSum = std::accumulate(
            source.visibleShape.values.begin(), source.visibleShape.values.end(), 0.0);
        for (std::size_t i = 0; i < source.visibleShape.values.size(); ++i) {
            const double fraction = shapeSum > kEpsilon
                ? source.visibleShape.values[i] / shapeSum
                : 1.0 / static_cast<double>(source.visibleShape.values.size());
            result.visibleIrradianceWattsPerSquareMeter[i] += visiblePower * fraction / denominator;
        }
    }

    return result;
}

glm::dvec3 ElectromagneticRadiationSystem::lorentzForce(
    double chargeCoulombs,
    const glm::dvec3& velocityMetersPerSecond,
    const FieldSample& field) const noexcept {
    return chargeCoulombs
        * (field.electricFieldVoltsPerMeter
            + glm::cross(velocityMetersPerSecond, field.magneticFieldTesla));
}

void ElectromagneticRadiationSystem::stepInductionCoil(
    InductionCoil& coil,
    double deltaSeconds) const noexcept {
    coil.normal = safeNormalize(coil.normal);
    coil.areaSquareMeters = std::max(0.0, coil.areaSquareMeters);
    coil.turns = std::max(0.0, coil.turns);
    coil.resistanceOhms = std::max(1.0e-9, coil.resistanceOhms);

    const double fluxWebers = glm::dot(sample(coil.position).magneticFieldTesla, coil.normal)
        * coil.areaSquareMeters;

    if (!coil.initialized || deltaSeconds <= 0.0) {
        coil.previousFluxWebers = fluxWebers;
        coil.inducedEmfVolts = 0.0;
        coil.inducedCurrentAmperes = 0.0;
        coil.initialized = true;
        return;
    }

    const double fluxRate = (fluxWebers - coil.previousFluxWebers) / deltaSeconds;
    coil.inducedEmfVolts = -coil.turns * fluxRate;
    coil.inducedCurrentAmperes = coil.inducedEmfVolts / coil.resistanceOhms;
    coil.previousFluxWebers = fluxWebers;
}

ElectromagneticRadiationSystem::WaveField ElectromagneticRadiationSystem::waveFieldsFromIrradiance(
    double irradianceWattsPerSquareMeter,
    const glm::dvec3& propagationDirection,
    const glm::dvec3& polarizationHint) noexcept {
    WaveField result{};
    const double irradiance = std::max(0.0, irradianceWattsPerSquareMeter);
    if (irradiance <= 0.0) return result;

    const glm::dvec3 direction = safeNormalize(propagationDirection, {0.0, 0.0, 1.0});
    glm::dvec3 polarization = polarizationHint
        - direction * glm::dot(polarizationHint, direction);
    if (glm::dot(polarization, polarization) <= kEpsilon) {
        const glm::dvec3 reference = std::abs(direction.y) < 0.9
            ? glm::dvec3{0.0, 1.0, 0.0}
            : glm::dvec3{1.0, 0.0, 0.0};
        polarization = glm::cross(reference, direction);
    }
    polarization = safeNormalize(polarization, {1.0, 0.0, 0.0});

    const double vacuumImpedance = kVacuumPermeability * kSpeedOfLight;
    const double electricMagnitude = std::sqrt(irradiance * vacuumImpedance);
    result.electricRmsVoltsPerMeter = polarization * electricMagnitude;
    result.magneticRmsTesla = glm::cross(direction, result.electricRmsVoltsPerMeter) / kSpeedOfLight;
    return result;
}

ElectromagneticRadiationSystem::BroadbandSpectrum ElectromagneticRadiationSystem::attenuateRadiation(
    const BroadbandSpectrum& incident,
    const RadiationMaterial& material,
    double thicknessMeters) noexcept {
    BroadbandSpectrum result{};
    const double thickness = std::max(0.0, thicknessMeters);
    for (std::size_t i = 0; i < kRadiationBandCount; ++i) {
        const double attenuation = std::max(0.0, material.attenuationPerMeter[i]);
        result.values[i] = std::max(0.0, incident.values[i]) * std::exp(-attenuation * thickness);
    }
    return result;
}

double ElectromagneticRadiationSystem::absorbedRadiationPowerWatts(
    const BroadbandSpectrum& irradiance,
    const RadiationMaterial& material,
    double projectedAreaSquareMeters) noexcept {
    const double area = std::max(0.0, projectedAreaSquareMeters);
    double absorbed = 0.0;
    for (std::size_t i = 0; i < kRadiationBandCount; ++i) {
        absorbed += std::max(0.0, irradiance.values[i])
            * clampUnit(material.absorptivity[i]) * area;
    }
    return absorbed;
}

double ElectromagneticRadiationSystem::photopicIlluminanceLux(
    const GameSpectrum& visibleIrradiance) noexcept {
    // Sparse samples of the CIE photopic response around the six gameplay wavelengths.
    // The 683 lm/W scale anchors the green peak while keeping evaluation to six multiplies.
    constexpr std::array<double, 6> photopicWeight{0.0116, 0.0910, 0.5030, 0.9950, 0.5030, 0.0320};
    double weightedWattsPerSquareMeter = 0.0;
    for (std::size_t i = 0; i < photopicWeight.size(); ++i) {
        weightedWattsPerSquareMeter += std::max(0.0, visibleIrradiance[i]) * photopicWeight[i];
    }
    return 683.0 * weightedWattsPerSquareMeter;
}

double ElectromagneticRadiationSystem::lightSensorCurrentAmperes(
    const LightSensor& sensor,
    const GameSpectrum& visibleIrradiance) noexcept {
    double visiblePowerDensity = 0.0;
    for (const double value : visibleIrradiance.values) visiblePowerDensity += std::max(0.0, value);
    return visiblePowerDensity
        * std::max(0.0, sensor.activeAreaSquareMeters)
        * std::max(0.0, sensor.responsivityAmperesPerWatt);
}

double ElectromagneticRadiationSystem::focusedPowerWatts(
    const ThinLens& lens,
    double incidentIrradianceWattsPerSquareMeter,
    const glm::dvec3& targetWorldPosition) noexcept {
    const double irradiance = std::max(0.0, incidentIrradianceWattsPerSquareMeter);
    const double focalLength = std::max(1.0e-4, lens.focalLengthMeters);
    const double apertureRadius = std::max(0.0, lens.apertureRadiusMeters);
    const double minimumSpot = std::max(1.0e-5, lens.minimumSpotRadiusMeters);
    const double axialTolerance = std::max(1.0e-5, lens.axialToleranceMeters);
    if (irradiance <= 0.0 || apertureRadius <= 0.0) return 0.0;

    const glm::dvec3 axis = safeNormalize(lens.opticalAxis, {0.0, 0.0, 1.0});
    const glm::dvec3 relative = targetWorldPosition - lens.position;
    const double axialDistance = glm::dot(relative, axis);
    if (axialDistance <= 0.0) return 0.0;

    const double defocus = axialDistance - focalLength;
    if (std::abs(defocus) >= axialTolerance) return 0.0;
    const glm::dvec3 radialVector = relative - axis * axialDistance;
    const double radialDistance = glm::length(radialVector);
    const double spotRadius = minimumSpot
        + apertureRadius * std::abs(defocus) / focalLength;
    if (radialDistance >= spotRadius) return 0.0;

    const double axialWeight = 1.0 - std::abs(defocus) / axialTolerance;
    const double radialWeight = 1.0 - radialDistance / spotRadius;
    const double collectedPower = irradiance * kPi * apertureRadius * apertureRadius
        * clampUnit(lens.transmission);
    return collectedPower * axialWeight * radialWeight;
}

void ElectromagneticRadiationSystem::stepThermalBody(
    ThermalBody& body,
    const FieldSample& field,
    double ambientTemperatureK,
    double deltaSeconds,
    double additionalFocusedPowerWatts) noexcept {
    if (deltaSeconds <= 0.0) return;

    const double mass = std::max(1.0e-6, body.massKg);
    const double specificHeat = std::max(1.0, body.specificHeatJPerKgK);
    const double area = std::max(0.0, body.surfaceAreaSquareMeters);
    const double projectedArea = std::max(0.0, body.projectedAreaSquareMeters);
    const double ambient = std::max(2.7, ambientTemperatureK);
    const double temperature = std::max(2.7, body.temperatureK);

    const double absorbedPower = absorbedRadiationPowerWatts(
        field.irradianceWattsPerSquareMeter, body.material, projectedArea);
    const double focusedPower = std::max(0.0, additionalFocusedPowerWatts);
    const double emissivity = clampUnit(body.material.emissivity);
    const double radiativeLoss = emissivity * kStefanBoltzmann * area
        * (std::pow(temperature, 4.0) - std::pow(ambient, 4.0));
    const double convection = std::max(0.0, body.convectiveCoefficientWPerSquareMeterK)
        * area * (temperature - ambient);
    const double netPower = absorbedPower + focusedPower - radiativeLoss - convection;

    body.temperatureK = std::clamp(
        temperature + netPower * deltaSeconds / (mass * specificHeat),
        2.7,
        5000.0);

    const double uvIrradiance = std::max(0.0,
        field.irradianceWattsPerSquareMeter[RadiationBand::Ultraviolet]);
    body.ultravioletExposureJPerSquareMeter += uvIrradiance * deltaSeconds;

    const double ionizingIrradiance = std::max(0.0,
        field.irradianceWattsPerSquareMeter[RadiationBand::Ionizing]);
    const double ionizingAbsorbedPower = ionizingIrradiance * projectedArea
        * clampUnit(body.material.absorptivity[static_cast<std::size_t>(RadiationBand::Ionizing)]);
    body.ionizingDoseGray += ionizingAbsorbedPower * deltaSeconds / mass;

    if (body.temperatureK >= std::max(2.7, body.ignitionTemperatureK)) {
        body.ignited = true;
    }
}

} // namespace vf
