#include "vf/physics/OceanSpectrum.hpp"

#include <algorithm>
#include <cmath>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;

[[nodiscard]] std::uint64_t mixBits(std::uint64_t x) noexcept {
    x ^= x >> 30U;
    x *= 0xBF58476D1CE4E5B9ULL;
    x ^= x >> 27U;
    x *= 0x94D049BB133111EBULL;
    x ^= x >> 31U;
    return x;
}

[[nodiscard]] double random01(std::uint64_t seed, std::uint64_t channel) noexcept {
    const std::uint64_t bits = mixBits(seed + 0x9E3779B97F4A7C15ULL * (channel + 1ULL));
    return static_cast<double>(bits & 0xFFFFFFULL) / static_cast<double>(0xFFFFFFULL);
}

[[nodiscard]] glm::dvec2 safeNormalize2(const glm::dvec2& value) noexcept {
    const double l2 = glm::dot(value, value);
    return l2 > 1.0e-18 ? value / std::sqrt(l2) : glm::dvec2{1.0, 0.0};
}

[[nodiscard]] double jonswapShape(double frequencyHz, double peakHz, double gamma) noexcept {
    if (frequencyHz <= 0.0 || peakHz <= 0.0) return 0.0;
    const double ratio = peakHz / frequencyHz;
    const double sigma = frequencyHz <= peakHz ? 0.07 : 0.09;
    const double r = std::exp(-0.5 * std::pow((frequencyHz - peakHz) / (sigma * peakHz), 2.0));
    const double pm = std::pow(frequencyHz, -5.0) * std::exp(-1.25 * std::pow(ratio, 4.0));
    return pm * std::pow(std::max(1.0, gamma), r);
}

} // namespace

OceanSpectrum::OceanSpectrum(OceanSpectrumConfig config) {
    rebuild(config);
}

void OceanSpectrum::rebuild(OceanSpectrumConfig config) {
    config.significantWaveHeightMeters = std::clamp(config.significantWaveHeightMeters, 0.0, 20.0);
    config.peakPeriodSeconds = std::clamp(config.peakPeriodSeconds, 1.5, 30.0);
    config.directionalSpreadRadians = std::clamp(config.directionalSpreadRadians, 0.0, 1.2);
    config.jonswapGamma = std::clamp(config.jonswapGamma, 1.0, 7.0);
    config.windDirection = safeNormalize2(config.windDirection);
    config_ = config;

    const double peakHz = 1.0 / config_.peakPeriodSeconds;
    const double minHz = peakHz * 0.48;
    const double maxHz = peakHz * 2.10;
    const double df = (maxHz - minHz) / static_cast<double>(kComponentCount);
    std::array<double, kComponentCount> weights{};
    double discreteVariance = 0.0;

    const double windAngle = std::atan2(config_.windDirection.y, config_.windDirection.x);
    for (std::size_t i = 0; i < kComponentCount; ++i) {
        const double f = minHz + (static_cast<double>(i) + 0.5) * df;
        weights[i] = jonswapShape(f, peakHz, config_.jonswapGamma);
        discreteVariance += weights[i] * df;
        const double offset = (random01(config_.seed, 100U + i) * 2.0 - 1.0)
            * config_.directionalSpreadRadians;
        const double angle = windAngle + offset;
        components_[i].frequencyHz = f;
        components_[i].phaseRadians = random01(config_.seed, 200U + i) * 2.0 * kPi;
        components_[i].direction = {std::cos(angle), std::sin(angle)};
    }

    const double targetVariance = std::pow(config_.significantWaveHeightMeters / 4.0, 2.0);
    const double scale = discreteVariance > 1.0e-18 ? targetVariance / discreteVariance : 0.0;
    for (std::size_t i = 0; i < kComponentCount; ++i) {
        const double componentVariance = std::max(0.0, weights[i] * df * scale);
        components_[i].amplitudeMeters = std::sqrt(2.0 * componentVariance);
    }
}

OceanSurfaceSample OceanSpectrum::sample(
    const glm::dvec2& tangentPositionMeters,
    double timeSeconds,
    double gravityMagnitude) const noexcept {
    OceanSurfaceSample result{};
    const double gravity = std::max(0.1, gravityMagnitude);

    for (const Component& component : components_) {
        const double omega = 2.0 * kPi * component.frequencyHz;
        const double k = omega * omega / gravity; // deep-water dispersion omega^2 = g k
        const double phase = k * glm::dot(component.direction, tangentPositionMeters)
            - omega * timeSeconds + component.phaseRadians;
        const double c = std::cos(phase);
        const double s = std::sin(phase);
        result.heightMeters += component.amplitudeMeters * c;
        result.slope -= component.direction * (component.amplitudeMeters * k * s);
        result.tangentVelocityMps += component.direction * (component.amplitudeMeters * omega * c);
        result.verticalVelocityMps += component.amplitudeMeters * omega * s;
    }
    return result;
}

} // namespace vf
