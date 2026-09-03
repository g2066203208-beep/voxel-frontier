#pragma once

#include <array>
#include <cstddef>

#include <glm/glm.hpp>

namespace vf {

struct GameSpectrum {
    static constexpr std::array<double, 6> wavelengthsNm{430.0, 470.0, 510.0, 550.0, 610.0, 670.0};
    std::array<double, 6> values{};

    [[nodiscard]] double& operator[](std::size_t index) noexcept { return values[index]; }
    [[nodiscard]] double operator[](std::size_t index) const noexcept { return values[index]; }
};

struct FresnelPolarized {
    double s{};
    double p{};
    [[nodiscard]] double unpolarized() const noexcept { return 0.5 * (s + p); }
};

struct StokesVector {
    double i{1.0};
    double q{};
    double u{};
    double v{};

    [[nodiscard]] double degreeOfPolarization() const noexcept;
};

[[nodiscard]] GameSpectrum blackbodySpectrum(double temperatureK) noexcept;
[[nodiscard]] glm::dvec3 spectrumToLinearSrgb(const GameSpectrum& spectrum) noexcept;
[[nodiscard]] FresnelPolarized fresnelDielectric(double cosThetaIncident, double nIncident, double nTransmitted) noexcept;
[[nodiscard]] double beerLambertTransmittance(double absorptionPerMeter, double distanceMeters) noexcept;
[[nodiscard]] double cauchyIor(double wavelengthNm, double coefficientA, double coefficientBMicrometerSquared) noexcept;
[[nodiscard]] GameSpectrum thinFilmReflectance(
    double cosThetaIncident,
    double filmThicknessNm,
    double nIncident,
    double nFilm,
    double nSubstrate) noexcept;
[[nodiscard]] StokesVector linearPolarizer(const StokesVector& input, double axisRadians) noexcept;

} // namespace vf
