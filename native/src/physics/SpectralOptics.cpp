#include "vf/physics/SpectralOptics.hpp"

#include <algorithm>
#include <cmath>

namespace vf {
namespace {

constexpr double kPlanck = 6.62607015e-34;
constexpr double kLightSpeed = 299792458.0;
constexpr double kBoltzmann = 1.380649e-23;
constexpr double kPi = 3.1415926535897932384626433832795;

[[nodiscard]] double saturate(double value) noexcept {
    return std::clamp(value, 0.0, 1.0);
}

[[nodiscard]] double planckRadiance(double wavelengthMeters, double temperatureK) noexcept {
    if (wavelengthMeters <= 0.0 || temperatureK <= 0.0) return 0.0;
    const double numerator = 2.0 * kPlanck * kLightSpeed * kLightSpeed;
    const double exponent = kPlanck * kLightSpeed / (wavelengthMeters * kBoltzmann * temperatureK);
    if (exponent > 700.0) return 0.0;
    const double denominator = std::pow(wavelengthMeters, 5.0) * std::expm1(exponent);
    return denominator > 0.0 ? numerator / denominator : 0.0;
}

} // namespace

double StokesVector::degreeOfPolarization() const noexcept {
    if (i <= 1.0e-12) return 0.0;
    return saturate(std::sqrt(q * q + u * u + v * v) / i);
}

GameSpectrum blackbodySpectrum(double temperatureK) noexcept {
    GameSpectrum spectrum{};
    double maximum = 0.0;
    for (std::size_t i = 0; i < spectrum.values.size(); ++i) {
        const double wavelengthMeters = GameSpectrum::wavelengthsNm[i] * 1.0e-9;
        spectrum[i] = planckRadiance(wavelengthMeters, std::max(1.0, temperatureK));
        maximum = std::max(maximum, spectrum[i]);
    }
    if (maximum > 0.0) {
        for (double& value : spectrum.values) value /= maximum;
    }
    return spectrum;
}

glm::dvec3 spectrumToLinearSrgb(const GameSpectrum& spectrum) noexcept {
    // Six broad visible bands keep cost tiny while preserving wavelength-dependent behavior.
    // The XYZ rows are sampled approximations of the CIE 1931 2-degree observer response.
    constexpr std::array<glm::dvec3, 6> xyzWeights{
        glm::dvec3{0.283, 0.012, 1.386},
        glm::dvec3{0.195, 0.091, 1.288},
        glm::dvec3{0.009, 0.503, 0.158},
        glm::dvec3{0.433, 0.995, 0.009},
        glm::dvec3{1.003, 0.503, 0.000},
        glm::dvec3{0.087, 0.032, 0.000},
    };

    glm::dvec3 xyz{};
    for (std::size_t i = 0; i < spectrum.values.size(); ++i) xyz += xyzWeights[i] * std::max(0.0, spectrum[i]);
    xyz /= static_cast<double>(spectrum.values.size());

    glm::dvec3 rgb{
         3.2404542 * xyz.x - 1.5371385 * xyz.y - 0.4985314 * xyz.z,
        -0.9692660 * xyz.x + 1.8760108 * xyz.y + 0.0415560 * xyz.z,
         0.0556434 * xyz.x - 0.2040259 * xyz.y + 1.0572252 * xyz.z,
    };
    return glm::max(rgb, glm::dvec3{0.0});
}

FresnelPolarized fresnelDielectric(
    double cosThetaIncident,
    double nIncident,
    double nTransmitted) noexcept {
    FresnelPolarized result{};
    nIncident = std::max(1.0e-6, nIncident);
    nTransmitted = std::max(1.0e-6, nTransmitted);
    double cosI = std::clamp(cosThetaIncident, -1.0, 1.0);
    if (cosI < 0.0) {
        cosI = -cosI;
        std::swap(nIncident, nTransmitted);
    }

    const double eta = nIncident / nTransmitted;
    const double sinTSquared = eta * eta * std::max(0.0, 1.0 - cosI * cosI);
    if (sinTSquared >= 1.0) {
        result.s = 1.0;
        result.p = 1.0;
        return result;
    }

    const double cosT = std::sqrt(std::max(0.0, 1.0 - sinTSquared));
    const double rsNumerator = nIncident * cosI - nTransmitted * cosT;
    const double rsDenominator = nIncident * cosI + nTransmitted * cosT;
    const double rpNumerator = nTransmitted * cosI - nIncident * cosT;
    const double rpDenominator = nTransmitted * cosI + nIncident * cosT;
    result.s = rsDenominator != 0.0 ? std::pow(rsNumerator / rsDenominator, 2.0) : 1.0;
    result.p = rpDenominator != 0.0 ? std::pow(rpNumerator / rpDenominator, 2.0) : 1.0;
    result.s = saturate(result.s);
    result.p = saturate(result.p);
    return result;
}

double beerLambertTransmittance(double absorptionPerMeter, double distanceMeters) noexcept {
    return std::exp(-std::max(0.0, absorptionPerMeter) * std::max(0.0, distanceMeters));
}

double cauchyIor(
    double wavelengthNm,
    double coefficientA,
    double coefficientBMicrometerSquared) noexcept {
    const double wavelengthMicrometers = std::max(0.1, wavelengthNm * 1.0e-3);
    return std::max(1.0e-6, coefficientA + coefficientBMicrometerSquared
        / (wavelengthMicrometers * wavelengthMicrometers));
}

GameSpectrum thinFilmReflectance(
    double cosThetaIncident,
    double filmThicknessNm,
    double nIncident,
    double nFilm,
    double nSubstrate) noexcept {
    GameSpectrum spectrum{};
    const double cosI = std::clamp(std::abs(cosThetaIncident), 0.0, 1.0);
    nIncident = std::max(1.0e-6, nIncident);
    nFilm = std::max(1.0e-6, nFilm);
    nSubstrate = std::max(1.0e-6, nSubstrate);

    const double sinFilmSquared = std::pow(nIncident / nFilm, 2.0) * std::max(0.0, 1.0 - cosI * cosI);
    const double cosFilm = std::sqrt(std::max(0.0, 1.0 - std::min(1.0, sinFilmSquared)));
    const double r01 = (nIncident * cosI - nFilm * cosFilm)
        / std::max(1.0e-12, nIncident * cosI + nFilm * cosFilm);
    const double r12 = (nFilm - nSubstrate) / (nFilm + nSubstrate);

    for (std::size_t i = 0; i < spectrum.values.size(); ++i) {
        const double wavelength = GameSpectrum::wavelengthsNm[i];
        const double phase = 4.0 * kPi * nFilm * std::max(0.0, filmThicknessNm) * cosFilm
            / std::max(1.0, wavelength);
        const double numerator = r01 * r01 + r12 * r12 + 2.0 * r01 * r12 * std::cos(phase);
        const double denominator = 1.0 + r01 * r01 * r12 * r12
            + 2.0 * r01 * r12 * std::cos(phase);
        spectrum[i] = saturate(denominator > 1.0e-12 ? numerator / denominator : 1.0);
    }
    return spectrum;
}

StokesVector linearPolarizer(const StokesVector& input, double axisRadians) noexcept {
    const double c = std::cos(2.0 * axisRadians);
    const double s = std::sin(2.0 * axisRadians);
    StokesVector output{};
    output.i = 0.5 * (input.i + input.q * c + input.u * s);
    output.q = 0.5 * (input.i * c + input.q * c * c + input.u * s * c);
    output.u = 0.5 * (input.i * s + input.q * s * c + input.u * s * s);
    output.v = 0.0;
    return output;
}

} // namespace vf
