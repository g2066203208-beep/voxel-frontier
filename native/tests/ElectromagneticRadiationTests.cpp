#include "vf/physics/ElectromagneticRadiation.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

namespace {

using System = vf::ElectromagneticRadiationSystem;

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "EM/RADIATION TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void requireNear(double actual, double expected, double tolerance, std::string_view message) {
    if (std::abs(actual - expected) > tolerance) {
        std::cerr << "actual=" << actual << " expected=" << expected << " tolerance=" << tolerance << '\n';
        fail(message);
    }
}

void testElectricFieldInverseSquareAndLorentzForce() {
    System system{};
    System::ElectricPointSource source{};
    source.chargeCoulombs = 1.0e-9;
    source.softeningRadiusMeters = 1.0e-4;
    source.maxRangeMeters = 10.0;
    system.addElectricSource(source);

    const auto oneMeter = system.sample({1.0, 0.0, 0.0});
    const auto twoMeters = system.sample({2.0, 0.0, 0.0});
    require(oneMeter.electricFieldVoltsPerMeter.x > 0.0, "positive point charge must push field outward");
    requireNear(
        oneMeter.electricFieldVoltsPerMeter.x / twoMeters.electricFieldVoltsPerMeter.x,
        4.0,
        0.01,
        "electric field must follow inverse-square behavior away from softening radius");

    System::FieldSample field{};
    field.electricFieldVoltsPerMeter = {1.0, 0.0, 0.0};
    field.magneticFieldTesla = {0.0, 0.0, 1.0};
    const glm::dvec3 force = system.lorentzForce(2.0, {0.0, 1.0, 0.0}, field);
    requireNear(force.x, 4.0, 1.0e-12, "Lorentz force must combine electric and v cross B terms");
    requireNear(force.y, 0.0, 1.0e-12, "Lorentz force y component must stay zero in test geometry");
}

void testElectricityCreatesMagnetism() {
    System off{};
    System::SolenoidSource coil{};
    coil.turns = 500.0;
    coil.lengthMeters = 0.5;
    coil.radiusMeters = 0.1;
    coil.currentAmperes = 0.0;
    off.addSolenoid(coil);

    System on{};
    coil.currentAmperes = 2.0;
    on.addSolenoid(coil);

    const double bOff = glm::length(off.sample({0.0, 0.0, 0.0}).magneticFieldTesla);
    const double bOn = glm::length(on.sample({0.0, 0.0, 0.0}).magneticFieldTesla);
    requireNear(bOff, 0.0, 1.0e-15, "unpowered solenoid must not create a magnetic field");
    require(bOn > 1.0e-4, "powered solenoid must create a gameplay-visible magnetic field");

    System doubled{};
    coil.currentAmperes = 4.0;
    doubled.addSolenoid(coil);
    const double bDouble = glm::length(doubled.sample({0.0, 0.0, 0.0}).magneticFieldTesla);
    requireNear(bDouble / bOn, 2.0, 1.0e-9, "solenoid magnetic field must scale linearly with current");

    System displacement{};
    System::DisplacementCurrentSource changingElectricFlux{};
    changingElectricFlux.electricFluxRateVoltMetersPerSecond = 1.0e12;
    changingElectricFlux.coreRadiusMeters = 0.05;
    displacement.addDisplacementCurrentSource(changingElectricFlux);
    const auto displacementField = displacement.sample({0.1, 0.0, 0.0});
    require(glm::length(displacementField.magneticFieldTesla) > 0.0,
        "changing electric flux must create an azimuthal magnetic field");
}

void testChangingMagnetismCreatesElectricity() {
    System system{};
    System::MagneticDipoleSource magnet{};
    magnet.position = {0.0, 0.0, 0.0};
    magnet.magneticMomentAmpereSquareMeters = {0.0, 0.0, 1.0};
    magnet.softeningRadiusMeters = 0.01;
    system.addMagneticDipole(magnet);

    System::InductionCoil coil{};
    coil.position = {0.0, 0.0, 0.5};
    coil.normal = {0.0, 0.0, 1.0};
    coil.areaSquareMeters = 0.02;
    coil.turns = 200.0;
    coil.resistanceOhms = 5.0;
    system.stepInductionCoil(coil, 0.1);
    requireNear(coil.inducedEmfVolts, 0.0, 1.0e-15,
        "first induction sample must initialize history without a fake voltage spike");

    system.clearSources();
    magnet.magneticMomentAmpereSquareMeters = {0.0, 0.0, 2.0};
    system.addMagneticDipole(magnet);
    system.stepInductionCoil(coil, 0.1);
    require(std::abs(coil.inducedEmfVolts) > 0.0,
        "changing magnetic flux must induce an emf");
    require(std::abs(coil.inducedCurrentAmperes) > 0.0,
        "induced emf across a finite resistance must produce current");
}

void testRadiationInverseSquareWavesAndShielding() {
    System system{};
    System::RadiationSource source{};
    source.minimumDistanceMeters = 0.01;
    source.maxRangeMeters = 100.0;
    source.powerWatts[System::RadiationBand::Visible] = 120.0;
    source.powerWatts[System::RadiationBand::Ionizing] = 20.0;
    source.visibleShape.values = {0.2, 0.4, 0.8, 1.0, 0.5, 0.2};
    system.addRadiationSource(source);

    const auto nearField = system.sample({1.0, 0.0, 0.0});
    const auto farField = system.sample({2.0, 0.0, 0.0});
    const double nearVisible = nearField.irradianceWattsPerSquareMeter[System::RadiationBand::Visible];
    const double farVisible = farField.irradianceWattsPerSquareMeter[System::RadiationBand::Visible];
    requireNear(nearVisible / farVisible, 4.0, 1.0e-10,
        "isotropic radiation must conserve energy with inverse-square irradiance");

    const auto wave = System::waveFieldsFromIrradiance(1000.0, {0.0, 0.0, 1.0}, {1.0, 0.0, 0.0});
    const double electric = glm::length(wave.electricRmsVoltsPerMeter);
    const double magnetic = glm::length(wave.magneticRmsTesla);
    requireNear(electric / magnetic, System::kSpeedOfLight, 1.0,
        "vacuum electromagnetic wave must preserve E/B = c");
    require(std::abs(glm::dot(wave.electricRmsVoltsPerMeter, wave.magneticRmsTesla)) < 1.0e-12,
        "wave electric and magnetic fields must be perpendicular");

    System::RadiationMaterial shielding{};
    shielding.attenuationPerMeter.fill(0.0);
    shielding.attenuationPerMeter[static_cast<std::size_t>(System::RadiationBand::Ionizing)] = 5.0;
    const auto shielded = System::attenuateRadiation(nearField.irradianceWattsPerSquareMeter, shielding, 1.0);
    require(shielded[System::RadiationBand::Ionizing]
            < nearField.irradianceWattsPerSquareMeter[System::RadiationBand::Ionizing] * 0.01,
        "strong shielding attenuation must greatly reduce ionizing radiation");
}

void testVisionSensorAndLensIgnition() {
    vf::GameSpectrum blue{};
    vf::GameSpectrum green{};
    blue[0] = 1.0;
    green[3] = 1.0;
    require(System::photopicIlluminanceLux(green) > System::photopicIlluminanceLux(blue) * 20.0,
        "photopic response must be much more sensitive near green than deep blue");

    System::LightSensor sensor{};
    sensor.activeAreaSquareMeters = 0.01;
    sensor.responsivityAmperesPerWatt = 0.5;
    requireNear(System::lightSensorCurrentAmperes(sensor, green), 0.005, 1.0e-12,
        "light sensor must convert incident optical power to current");

    System::ThinLens lens{};
    lens.position = {0.0, 0.0, 0.0};
    lens.opticalAxis = {0.0, 0.0, 1.0};
    lens.focalLengthMeters = 0.20;
    lens.apertureRadiusMeters = 0.05;
    lens.transmission = 0.90;
    lens.minimumSpotRadiusMeters = 0.003;
    lens.axialToleranceMeters = 0.02;

    const double focusPower = System::focusedPowerWatts(lens, 1000.0, {0.0, 0.0, 0.20});
    const double offFocusPower = System::focusedPowerWatts(lens, 1000.0, {0.05, 0.0, 0.20});
    require(focusPower > 6.0 && focusPower < 8.0,
        "lens must collect approximately irradiance times aperture area times transmission");
    requireNear(offFocusPower, 0.0, 1.0e-12, "target outside the focal spot must not receive focused power");

    System::ThermalBody tinder{};
    tinder.massKg = 0.001;
    tinder.specificHeatJPerKgK = 1000.0;
    tinder.surfaceAreaSquareMeters = 0.0;
    tinder.projectedAreaSquareMeters = 0.0;
    tinder.temperatureK = 300.0;
    tinder.ignitionTemperatureK = 600.0;
    tinder.convectiveCoefficientWPerSquareMeterK = 0.0;
    System::FieldSample noBackgroundRadiation{};
    System::stepThermalBody(tinder, noBackgroundRadiation, 300.0, 50.0, focusPower);
    require(tinder.temperatureK > tinder.ignitionTemperatureK,
        "focused light energy must heat a low-thermal-mass target above ignition temperature");
    require(tinder.ignited, "thermal body must enter ignited gameplay state after reaching ignition temperature");
}

void testUvAndIonizingExposureAccumulates() {
    System::ThermalBody body{};
    body.massKg = 2.0;
    body.projectedAreaSquareMeters = 0.5;
    body.surfaceAreaSquareMeters = 0.0;
    body.convectiveCoefficientWPerSquareMeterK = 0.0;
    body.material.absorptivity.fill(0.0);
    body.material.absorptivity[static_cast<std::size_t>(System::RadiationBand::Ionizing)] = 0.5;

    System::FieldSample field{};
    field.irradianceWattsPerSquareMeter[System::RadiationBand::Ultraviolet] = 10.0;
    field.irradianceWattsPerSquareMeter[System::RadiationBand::Ionizing] = 4.0;
    System::stepThermalBody(body, field, 293.15, 2.0);

    requireNear(body.ultravioletExposureJPerSquareMeter, 20.0, 1.0e-12,
        "UV exposure must accumulate irradiance over time");
    requireNear(body.ionizingDoseGray, 1.0, 1.0e-12,
        "ionizing absorbed energy per kilogram must accumulate as gray");
}

} // namespace

int main() {
    testElectricFieldInverseSquareAndLorentzForce();
    testElectricityCreatesMagnetism();
    testChangingMagnetismCreatesElectricity();
    testRadiationInverseSquareWavesAndShielding();
    testVisionSensorAndLensIgnition();
    testUvAndIonizingExposureAccumulates();
    std::cout << "vf_electromagnetic_radiation_tests: PASS\n";
    return 0;
}
