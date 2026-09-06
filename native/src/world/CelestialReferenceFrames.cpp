#include "vf/world/CelestialReferenceFrames.hpp"

namespace vf {

std::uint32_t CelestialReferenceFrames::createBodyFrame(
    const CelestialBody& body,
    std::uint32_t parentFrameId,
    ReferenceFrameSystem& frames) const {
    ReferenceFrame frame{};
    frame.parentId = parentFrameId;
    frame.name = body.name + "_frame";
    frame.localPosition = body.position;
    frame.localVelocity = body.linearVelocity;
    return frames.addFrame(frame);
}

glm::dvec3 CelestialReferenceFrames::bodyWorldPosition(
    const CelestialBody& body,
    const ReferenceFrameSystem& frames) const noexcept {
    return body.position;
}

} // namespace vf
