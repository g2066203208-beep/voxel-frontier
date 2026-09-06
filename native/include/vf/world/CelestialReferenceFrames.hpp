#pragma once

#include <cstdint>

#include "vf/world/CelestialSystem.hpp"
#include "vf/world/ReferenceFrame.hpp"

namespace vf {

// Bridges celestial bodies into hierarchical precision frames.
// This keeps orbital simulation in inertial space while allowing planets and moons
// to own local precision spaces.
class CelestialReferenceFrames final {
public:
    [[nodiscard]] std::uint32_t createBodyFrame(
        const CelestialBody& body,
        std::uint32_t parentFrameId,
        ReferenceFrameSystem& frames) const;

    [[nodiscard]] glm::dvec3 bodyWorldPosition(
        const CelestialBody& body,
        const ReferenceFrameSystem& frames) const noexcept;
};

} // namespace vf
