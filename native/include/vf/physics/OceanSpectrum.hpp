#pragma once

#include <array>
#include <cstdint>

#include <glm/glm.hpp>

namespace vf {

struct OceanSpectrumConfig {
    double significantWaveHeightMeters{1.6};
    double peakPeriodSeconds{7.5};
    glm::dvec2 windDirection{1.0, 0.0};
    double directionalSpreadRadians{0.42};
    double jonswapGamma{3.3};
    std::uint64_t seed{0x4F4345414EULL};
};

struct OceanSurfaceSample {
    double heightMeters{};
    glm::dvec2 slope{};
    glm::dvec2 tangentVelocityMps{};
    double verticalVelocityMps{};
};

// Compact deterministic JONSWAP-shaped deep-water wave spectrum. The runtime shader can mirror the
// same finite components while physics reads height/velocity directly; visible waves and buoyancy
// therefore share one field instead of unrelated sine functions.
class OceanSpectrum final {
public:
    static constexpr std::size_t kComponentCount = 12U;

    explicit OceanSpectrum(OceanSpectrumConfig config = {});
    void rebuild(OceanSpectrumConfig config);

    [[nodiscard]] const OceanSpectrumConfig& config() const noexcept { return config_; }
    [[nodiscard]] OceanSurfaceSample sample(
        const glm::dvec2& tangentPositionMeters,
        double timeSeconds,
        double gravityMagnitude = 9.80665) const noexcept;

private:
    struct Component {
        double frequencyHz{};
        double amplitudeMeters{};
        double phaseRadians{};
        glm::dvec2 direction{1.0, 0.0};
    };

    OceanSpectrumConfig config_{};
    std::array<Component, kComponentCount> components_{};
};

} // namespace vf
