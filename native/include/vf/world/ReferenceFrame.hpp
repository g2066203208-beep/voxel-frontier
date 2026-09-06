#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

#include <glm/geometric.hpp>
#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

namespace vf {

// Hierarchical coordinate ownership for large-scale worlds. ReferenceFrameSystem models inertial
// and nested precision frames; body-fixed rotating planet frames remain the responsibility of
// CelestialPhysicsFrame. Keeping those concepts separate prevents orbital hierarchy from being
// accidentally coupled to a planet's daily spin.
struct ReferenceFrame {
    std::uint32_t id{};
    std::uint32_t parentId{};
    std::string name{};
    glm::dvec3 localPosition{};
    glm::dvec3 localVelocity{};
    glm::dquat localRotation{1.0, 0.0, 0.0, 0.0};
    glm::dvec3 localAngularVelocity{};
};

struct ReferenceFrameWorldState {
    glm::dvec3 position{};
    glm::dvec3 velocity{};
    glm::dquat rotation{1.0, 0.0, 0.0, 0.0};
    glm::dvec3 angularVelocity{};
    bool valid{};
};

class ReferenceFrameSystem final {
public:
    [[nodiscard]] std::uint32_t addFrame(ReferenceFrame frameValue) {
        if (frameValue.id == 0U) frameValue.id = nextId_++;
        else nextId_ = std::max(nextId_, frameValue.id + 1U);
        if (frameValue.parentId == frameValue.id) frameValue.parentId = 0U;
        frameValue.localRotation = normalizedRotation(frameValue.localRotation);
        frames_.push_back(std::move(frameValue));
        return frames_.back().id;
    }

    void clear() noexcept {
        frames_.clear();
        nextId_ = 1U;
    }

    [[nodiscard]] std::size_t size() const noexcept { return frames_.size(); }

    [[nodiscard]] ReferenceFrame* frame(std::uint32_t id) noexcept {
        for (auto& candidate : frames_) if (candidate.id == id) return &candidate;
        return nullptr;
    }

    [[nodiscard]] const ReferenceFrame* frame(std::uint32_t id) const noexcept {
        for (const auto& candidate : frames_) if (candidate.id == id) return &candidate;
        return nullptr;
    }

    [[nodiscard]] ReferenceFrameWorldState worldState(std::uint32_t id) const noexcept {
        if (id == 0U) {
            ReferenceFrameWorldState root{};
            root.valid = true;
            return root;
        }

        std::vector<const ReferenceFrame*> chain;
        chain.reserve(frames_.size());
        std::uint32_t currentId = id;
        while (currentId != 0U) {
            const ReferenceFrame* current = frame(currentId);
            if (current == nullptr) return {};
            const auto repeated = std::find_if(
                chain.begin(), chain.end(),
                [currentId](const ReferenceFrame* item) { return item->id == currentId; });
            if (repeated != chain.end()) return {};
            chain.push_back(current);
            if (chain.size() > frames_.size()) return {};
            currentId = current->parentId;
        }

        ReferenceFrameWorldState result{};
        result.valid = true;
        for (auto it = chain.rbegin(); it != chain.rend(); ++it) {
            const ReferenceFrame& local = **it;
            const glm::dquat parentRotation = result.rotation;
            const glm::dvec3 worldOffset = parentRotation * local.localPosition;
            result.velocity += glm::cross(result.angularVelocity, worldOffset)
                + parentRotation * local.localVelocity;
            result.position += worldOffset;
            result.angularVelocity += parentRotation * local.localAngularVelocity;
            result.rotation = normalizedRotation(parentRotation * local.localRotation);
        }
        return result;
    }

    [[nodiscard]] glm::dvec3 worldPosition(std::uint32_t id) const noexcept {
        return worldState(id).position;
    }

    [[nodiscard]] glm::dvec3 worldVelocity(std::uint32_t id) const noexcept {
        return worldState(id).velocity;
    }

    [[nodiscard]] glm::dquat worldRotation(std::uint32_t id) const noexcept {
        return worldState(id).rotation;
    }

    [[nodiscard]] glm::dvec3 worldAngularVelocity(std::uint32_t id) const noexcept {
        return worldState(id).angularVelocity;
    }

    [[nodiscard]] glm::dvec3 toWorldVector(
        std::uint32_t id,
        const glm::dvec3& localVector) const noexcept {
        const ReferenceFrameWorldState state = worldState(id);
        return state.valid ? state.rotation * localVector : localVector;
    }

    [[nodiscard]] glm::dvec3 toLocalVector(
        std::uint32_t id,
        const glm::dvec3& worldVector) const noexcept {
        const ReferenceFrameWorldState state = worldState(id);
        return state.valid ? glm::conjugate(state.rotation) * worldVector : worldVector;
    }

    [[nodiscard]] glm::dvec3 toWorldPosition(
        std::uint32_t id,
        const glm::dvec3& localPosition) const noexcept {
        const ReferenceFrameWorldState state = worldState(id);
        return state.valid ? state.position + state.rotation * localPosition : localPosition;
    }

    [[nodiscard]] glm::dvec3 toLocalPosition(
        std::uint32_t id,
        const glm::dvec3& worldPositionValue) const noexcept {
        const ReferenceFrameWorldState state = worldState(id);
        return state.valid
            ? glm::conjugate(state.rotation) * (worldPositionValue - state.position)
            : worldPositionValue;
    }

    [[nodiscard]] glm::dquat toWorldOrientation(
        std::uint32_t id,
        const glm::dquat& localOrientation) const noexcept {
        const ReferenceFrameWorldState state = worldState(id);
        return state.valid
            ? normalizedRotation(state.rotation * localOrientation)
            : normalizedRotation(localOrientation);
    }

    [[nodiscard]] glm::dquat toLocalOrientation(
        std::uint32_t id,
        const glm::dquat& worldOrientation) const noexcept {
        const ReferenceFrameWorldState state = worldState(id);
        return state.valid
            ? normalizedRotation(glm::conjugate(state.rotation) * worldOrientation)
            : normalizedRotation(worldOrientation);
    }

    [[nodiscard]] glm::dvec3 toWorldVelocity(
        std::uint32_t id,
        const glm::dvec3& localPosition,
        const glm::dvec3& localVelocity) const noexcept {
        const ReferenceFrameWorldState state = worldState(id);
        if (!state.valid) return localVelocity;
        const glm::dvec3 worldOffset = state.rotation * localPosition;
        return state.velocity
            + glm::cross(state.angularVelocity, worldOffset)
            + state.rotation * localVelocity;
    }

    [[nodiscard]] glm::dvec3 toLocalVelocity(
        std::uint32_t id,
        const glm::dvec3& worldPositionValue,
        const glm::dvec3& worldVelocityValue) const noexcept {
        const ReferenceFrameWorldState state = worldState(id);
        if (!state.valid) return worldVelocityValue;
        const glm::dvec3 worldOffset = worldPositionValue - state.position;
        return glm::conjugate(state.rotation)
            * (worldVelocityValue
                - state.velocity
                - glm::cross(state.angularVelocity, worldOffset));
    }

private:
    [[nodiscard]] static glm::dquat normalizedRotation(const glm::dquat& rotation) noexcept {
        const double normSquared = rotation.w * rotation.w
            + rotation.x * rotation.x
            + rotation.y * rotation.y
            + rotation.z * rotation.z;
        if (!std::isfinite(normSquared) || normSquared <= 1.0e-24)
            return {1.0, 0.0, 0.0, 0.0};
        return rotation / std::sqrt(normSquared);
    }

    std::vector<ReferenceFrame> frames_;
    std::uint32_t nextId_{1U};
};

} // namespace vf
