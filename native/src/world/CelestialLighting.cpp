#include "vf/world/CelestialLighting.hpp"

#include <algorithm>
#include <cmath>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {1.0, 0.0, 0.0}) noexcept {
    const double l2 = glm::dot(value, value);
    return l2 > 1.0e-24 ? value / std::sqrt(l2) : fallback;
}

[[nodiscard]] double angularRadius(double radius, double distance) noexcept {
    if (distance <= 0.0 || radius <= 0.0) return 0.0;
    return std::asin(std::clamp(radius / distance, 0.0, 1.0));
}

[[nodiscard]] double circleOverlapArea(double r1, double r2, double d) noexcept {
    if (r1 <= 0.0 || r2 <= 0.0) return 0.0;
    if (d >= r1 + r2) return 0.0;
    if (d <= std::abs(r1 - r2)) {
        const double r = std::min(r1, r2);
        return kPi * r * r;
    }
    const double c1 = std::clamp((d * d + r1 * r1 - r2 * r2) / (2.0 * d * r1), -1.0, 1.0);
    const double c2 = std::clamp((d * d + r2 * r2 - r1 * r1) / (2.0 * d * r2), -1.0, 1.0);
    const double term = std::max(
        0.0,
        (-d + r1 + r2) * (d + r1 - r2)
            * (d - r1 + r2) * (d + r1 + r2));
    return r1 * r1 * std::acos(c1)
        + r2 * r2 * std::acos(c2)
        - 0.5 * std::sqrt(term);
}

[[nodiscard]] double meanAlbedo(const CelestialBody& body) noexcept {
    return std::clamp((body.visibleAlbedo.x + body.visibleAlbedo.y + body.visibleAlbedo.z) / 3.0, 0.0, 1.0);
}

} // namespace

StellarLightingSample sampleStellarLighting(
    const CelestialSystem& system,
    std::uint32_t starId,
    const glm::dvec3& observerPosition) noexcept {
    StellarLightingSample result{};
    const CelestialBody* star = system.body(starId);
    if (star == nullptr || star->type != CelestialBodyType::Star || star->luminosityWatts <= 0.0)
        return result;

    const glm::dvec3 starVector = star->position - observerPosition;
    const double starDistance = glm::length(starVector);
    if (starDistance <= 1.0) return result;
    result.directionToStar = starVector / starDistance;
    result.irradianceWm2 = star->luminosityWatts / (4.0 * kPi * starDistance * starDistance);
    result.visibleDiscFraction = 1.0;

    const double starAngularRadius = angularRadius(star->radiusMeters, starDistance);
    const double starDiscArea = kPi * starAngularRadius * starAngularRadius;
    if (starDiscArea <= 1.0e-24) return result;

    for (const CelestialBody& occluder : system.bodies()) {
        if (occluder.id == starId || occluder.radiusMeters <= 0.0) continue;
        const glm::dvec3 occVector = occluder.position - observerPosition;
        const double occDistance = glm::length(occVector);
        if (occDistance <= occluder.radiusMeters || occDistance >= starDistance) continue;
        const glm::dvec3 occDirection = safeNormalize(occVector);
        const double separation = std::acos(std::clamp(
            glm::dot(result.directionToStar, occDirection), -1.0, 1.0));
        const double occAngularRadius = angularRadius(occluder.radiusMeters, occDistance);
        const double overlap = circleOverlapArea(starAngularRadius, occAngularRadius, separation);
        const double occulted = std::clamp(overlap / starDiscArea, 0.0, 1.0);
        // Multiplication is exact for one dominant occluder and conservative for the very rare case
        // of multiple overlapping apparent discs.
        result.visibleDiscFraction *= 1.0 - occulted;
        if (result.visibleDiscFraction <= 1.0e-8) {
            result.visibleDiscFraction = 0.0;
            break;
        }
    }
    return result;
}

double reflectedStellarIrradianceAt(
    const CelestialSystem& system,
    std::uint32_t starId,
    std::uint32_t reflectorId,
    const glm::dvec3& observerPosition) noexcept {
    const CelestialBody* star = system.body(starId);
    const CelestialBody* reflector = system.body(reflectorId);
    if (star == nullptr || reflector == nullptr || star->luminosityWatts <= 0.0
        || reflector->radiusMeters <= 0.0 || starId == reflectorId) return 0.0;

    const glm::dvec3 toStar = star->position - reflector->position;
    const glm::dvec3 toObserver = observerPosition - reflector->position;
    const double starDistance = glm::length(toStar);
    const double observerDistance = glm::length(toObserver);
    if (starDistance <= star->radiusMeters || observerDistance <= reflector->radiusMeters) return 0.0;

    const double incident = star->luminosityWatts / (4.0 * kPi * starDistance * starDistance);
    const double phaseAngle = std::acos(std::clamp(
        glm::dot(safeNormalize(toStar), safeNormalize(toObserver)), -1.0, 1.0));
    const double phase = (std::sin(phaseAngle) + (kPi - phaseAngle) * std::cos(phaseAngle)) / kPi;
    const double apparentArea = (reflector->radiusMeters * reflector->radiusMeters)
        / (observerDistance * observerDistance);
    return std::max(0.0, incident * meanAlbedo(*reflector) * phase * apparentArea);
}

} // namespace vf
