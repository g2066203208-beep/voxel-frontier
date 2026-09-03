#include "vf/physics/SpectralOptics.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "SPECTRAL OPTICS TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void requireNear(double actual, double expected, double tolerance, std::string_view message) {
    if (std::abs(actual - expected) > tolerance) fail(message);
}

void testFresnelAndTotalInternalReflection() {
    const auto normal = vf::fresnelDielectric(1.0, 1.0, 1.5);
    requireNear(normal.unpolarized(), 0.04, 0.002, "air-glass normal-incidence Fresnel reflectance must be about four percent");

    const auto tir = vf::fresnelDielectric(0.4, 1.5, 1.0);
    requireNear(tir.s, 1.0, 1.0e-12, "total internal reflection must return unit s reflectance");
    requireNear(tir.p, 1.0, 1.0e-12, "total internal reflection must return unit p reflectance");
}

void testBeerLambertDispersionAndRefraction() {
    requireNear(vf::beerLambertTransmittance(2.0, 1.0), std::exp(-2.0), 1.0e-12,
        "Beer-Lambert transmission must be exponential");
    require(vf::beerLambertTransmittance(2.0, 2.0) < vf::beerLambertTransmittance(2.0, 1.0),
        "thicker absorbing media must transmit less light");

    const double blue = vf::cauchyIor(430.0, 1.50, 0.0040);
    const double red = vf::cauchyIor(670.0, 1.50, 0.0040);
    require(blue > red, "normal Cauchy dispersion must refract blue more strongly than red");

    glm::dvec3 transmitted{};
    require(vf::refractDirection(glm::normalize(glm::dvec3{0.5, -1.0, 0.0}), {0.0, 1.0, 0.0}, 1.0, 1.5, transmitted),
        "air-to-glass refraction must produce a transmitted ray");
    require(std::abs(transmitted.x) < std::abs(glm::normalize(glm::dvec3{0.5, -1.0, 0.0}).x),
        "air-to-glass ray must bend toward the surface normal");

    require(!vf::refractDirection(glm::normalize(glm::dvec3{0.9, 0.435889894, 0.0}), {0.0, 1.0, 0.0}, 1.5, 1.0, transmitted),
        "glass-to-air ray above critical angle must undergo total internal reflection");
}

void testBlackbodySpectrumShiftsWithTemperature() {
    const auto warm = vf::blackbodySpectrum(3000.0);
    const auto hot = vf::blackbodySpectrum(9000.0);
    const double warmBlueToRed = warm[0] / std::max(1.0e-12, warm[5]);
    const double hotBlueToRed = hot[0] / std::max(1.0e-12, hot[5]);
    require(hotBlueToRed > warmBlueToRed,
        "hotter blackbodies must shift relative visible energy toward shorter wavelengths");

    const auto warmRgb = vf::spectrumToLinearSrgb(warm);
    const auto hotRgb = vf::spectrumToLinearSrgb(hot);
    require(warmRgb.x > 0.0 && hotRgb.z > 0.0, "spectral conversion must produce finite visible RGB energy");
}

void testThinFilmPolarizationPhaseAndDiffraction() {
    const auto film = vf::thinFilmReflectance(0.8, 420.0, 1.0, 1.38, 1.52);
    double minimum = 1.0;
    double maximum = 0.0;
    for (const double value : film.values) {
        require(value >= 0.0 && value <= 1.0, "thin-film reflectance must remain physically bounded");
        minimum = std::min(minimum, value);
        maximum = std::max(maximum, value);
    }
    require(maximum - minimum > 1.0e-4, "thin film must produce wavelength-dependent interference");

    requireNear(vf::opticalPhaseRadians(550.0e-9, 550.0), 0.0, 1.0e-9,
        "one-wavelength path difference must wrap to zero phase");
    double diffractionAngle = 0.0;
    require(vf::diffractionGratingAngle(500.0, 1000.0, 0.0, 1, diffractionAngle),
        "first diffraction order must exist for lambda/d = 0.5");
    requireNear(diffractionAngle, std::asin(0.5), 1.0e-12,
        "grating equation must return the physical first-order angle");
    require(!vf::diffractionGratingAngle(700.0, 500.0, 0.0, 1, diffractionAngle),
        "grating orders outside |sin(theta)| <= 1 must be rejected");

    const vf::StokesVector unpolarized{1.0, 0.0, 0.0, 0.0};
    const auto polarized = vf::linearPolarizer(unpolarized, 0.0);
    requireNear(polarized.i, 0.5, 1.0e-12, "ideal polarizer must transmit half of unpolarized intensity");
    requireNear(polarized.degreeOfPolarization(), 1.0, 1.0e-12,
        "ideal polarizer output must be fully polarized");
}

void testOpticalMaterialTransmissionAndHue() {
    vf::GameSpectrum white{};
    for (double& value : white.values) value = 1.0;

    vf::OpticalMaterial glass{};
    glass.transmission = 0.92;
    glass.iorA = 1.50;
    glass.iorBMicrometerSquared = 0.0040;
    glass.absorptionPerMeter.values = {2.0, 1.4, 0.4, 0.2, 0.15, 0.12};
    glass.baseReflectance.values = {0.02, 0.02, 0.02, 0.02, 0.02, 0.02};

    const auto transmitted = vf::materialTransmission(glass, white, 0.8, 0.9);
    require(transmitted[0] < transmitted[5],
        "spectral absorption must tint transmitted light rather than using an alpha-only fake");
    for (const double value : transmitted.values) {
        require(value >= 0.0 && value <= 1.0, "material transmission must remain bounded for unit incident spectrum");
    }

    glass.thinFilmThicknessNm = 380.0;
    const auto reflected = vf::materialReflection(glass, white, 0.7);
    double minReflected = 1.0;
    double maxReflected = 0.0;
    for (const double value : reflected.values) {
        require(value >= 0.0 && value <= 1.0, "material reflection must remain physically bounded");
        minReflected = std::min(minReflected, value);
        maxReflected = std::max(maxReflected, value);
    }
    require(maxReflected - minReflected > 1.0e-4,
        "thin-film optical material must create wavelength-dependent reflected hue");
}

} // namespace

int main() {
    testFresnelAndTotalInternalReflection();
    testBeerLambertDispersionAndRefraction();
    testBlackbodySpectrumShiftsWithTemperature();
    testThinFilmPolarizationPhaseAndDiffraction();
    testOpticalMaterialTransmissionAndHue();
    std::cout << "vf_spectral_optics_tests: PASS\n";
    return 0;
}
