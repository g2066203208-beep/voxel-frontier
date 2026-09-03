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

void testBeerLambertAndDispersion() {
    requireNear(vf::beerLambertTransmittance(2.0, 1.0), std::exp(-2.0), 1.0e-12,
        "Beer-Lambert transmission must be exponential");
    require(vf::beerLambertTransmittance(2.0, 2.0) < vf::beerLambertTransmittance(2.0, 1.0),
        "thicker absorbing media must transmit less light");

    const double blue = vf::cauchyIor(430.0, 1.50, 0.0040);
    const double red = vf::cauchyIor(670.0, 1.50, 0.0040);
    require(blue > red, "normal Cauchy dispersion must refract blue more strongly than red");
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

void testThinFilmAndPolarization() {
    const auto film = vf::thinFilmReflectance(0.8, 420.0, 1.0, 1.38, 1.52);
    double minimum = 1.0;
    double maximum = 0.0;
    for (const double value : film.values) {
        require(value >= 0.0 && value <= 1.0, "thin-film reflectance must remain physically bounded");
        minimum = std::min(minimum, value);
        maximum = std::max(maximum, value);
    }
    require(maximum - minimum > 1.0e-4, "thin film must produce wavelength-dependent interference");

    const vf::StokesVector unpolarized{1.0, 0.0, 0.0, 0.0};
    const auto polarized = vf::linearPolarizer(unpolarized, 0.0);
    requireNear(polarized.i, 0.5, 1.0e-12, "ideal polarizer must transmit half of unpolarized intensity");
    requireNear(polarized.degreeOfPolarization(), 1.0, 1.0e-12,
        "ideal polarizer output must be fully polarized");
}

} // namespace

int main() {
    testFresnelAndTotalInternalReflection();
    testBeerLambertAndDispersion();
    testBlackbodySpectrumShiftsWithTemperature();
    testThinFilmAndPolarization();
    std::cout << "vf_spectral_optics_tests: PASS\n";
    return 0;
}
