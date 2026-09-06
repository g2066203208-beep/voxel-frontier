#include "vf/world/ReferenceFrame.hpp"

#include <algorithm>

namespace vf {

std::uint32_t ReferenceFrameSystem::addFrame(ReferenceFrame frame) {
    if (frame.id == 0U) frame.id = nextId_++;
    else nextId_ = std::max(nextId_, frame.id + 1U);
    frames_.push_back(std::move(frame));
    return frames_.back().id;
}

ReferenceFrame* ReferenceFrameSystem::frame(std::uint32_t id) noexcept {
    for (auto& candidate : frames_) {
        if (candidate.id == id) return &candidate;
    }
    return nullptr;
}

const ReferenceFrame* ReferenceFrameSystem::frame(std::uint32_t id) const noexcept {
    for (const auto& candidate : frames_) {
        if (candidate.id == id) return &candidate;
    }
    return nullptr;
}

glm::dvec3 ReferenceFrameSystem::accumulatePosition(std::uint32_t id) const noexcept {
    const ReferenceFrame* current = frame(id);
    if (current == nullptr) return {};
    if (current->parentId == 0U) return current->localPosition;
    return accumulatePosition(current->parentId) + current->localPosition;
}

glm::dvec3 ReferenceFrameSystem::accumulateVelocity(std::uint32_t id) const noexcept {
    const ReferenceFrame* current = frame(id);
    if (current == nullptr) return {};
    if (current->parentId == 0U) return current->localVelocity;
    return accumulateVelocity(current->parentId) + current->localVelocity;
}

glm::dvec3 ReferenceFrameSystem::worldPosition(std::uint32_t id) const noexcept {
    return accumulatePosition(id);
}

glm::dvec3 ReferenceFrameSystem::worldVelocity(std::uint32_t id) const noexcept {
    return accumulateVelocity(id);
}

} // namespace vf
