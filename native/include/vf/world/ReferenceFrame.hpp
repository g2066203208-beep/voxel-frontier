#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

namespace vf {

// Hierarchical coordinate ownership for large-scale worlds.
// A frame keeps a local precision space while preserving a parent-relative transform.
// This is the first step toward planet -> surface -> gameplay precision separation.
struct ReferenceFrame {
    std::uint32_t id{};
    std::uint32_t parentId{};
    std::string name{};
    glm::dvec3 localPosition{};
    glm::dvec3 localVelocity{};
    glm::dquat localRotation{1.0, 0.0, 0.0, 0.0};
};

class ReferenceFrameSystem final {
public:
    [[nodiscard]] std::uint32_t addFrame(ReferenceFrame frame);
    [[nodiscard]] ReferenceFrame* frame(std::uint32_t id) noexcept;
    [[nodiscard]] const ReferenceFrame* frame(std::uint32_t id) const noexcept;

    [[nodiscard]] glm::dvec3 worldPosition(std::uint32_t id) const noexcept;
    [[nodiscard]] glm::dvec3 worldVelocity(std::uint32_t id) const noexcept;

private:
    [[nodiscard]] glm::dvec3 accumulatePosition(std::uint32_t id) const noexcept;
    [[nodiscard]] glm::dvec3 accumulateVelocity(std::uint32_t id) const noexcept;

    std::vector<ReferenceFrame> frames_;
    std::uint32_t nextId_{1};
};

} // namespace vf
