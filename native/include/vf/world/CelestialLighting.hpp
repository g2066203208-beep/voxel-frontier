#pragma once

#include "vf/world/CelestialSystem.hpp"

#include <cstdint>

#include <glm/glm.hpp>

namespace vf {

struct StellarLightingSample {
    glm::dvec3 directionToStar{1.0, 0.0, 0.0};
    double irradianceWm2{};
    double visibleDiscFraction{1.0};
};

// Finite-disc celestial lighting. Occlusion is evaluated in apparent angular space, so a moon can
// partially or fully eclipse a star without a scripted event. The same positions/radii used by the
// N-body system therefore determine daylight visibility.
[[nodiscard]] StellarLightingSample sampleStellarLighting(
    const CelestialSystem& system,
    std::uint32_t starId,
    const glm::dvec3& observerPosition) noexcept;

// Lambert-sphere reflected irradiance (moonlight/planetshine) at an observer. This is deliberately
// an energy quantity, not a fake point light; render exposure decides how visible it becomes.
[[nodiscard]] double reflectedStellarIrradianceAt(
    const CelestialSystem& system,
    std::uint32_t starId,
    std::uint32_t reflectorId,
    const glm::dvec3& observerPosition) noexcept;

} // namespace vf
