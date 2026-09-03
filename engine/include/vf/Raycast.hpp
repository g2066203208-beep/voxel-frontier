#pragma once

#include <cstdint>
#include <span>

namespace vf {

struct RaycastHit {
  bool hit{};
  std::int32_t x{};
  std::int32_t y{};
  std::int32_t z{};
  std::int32_t normalX{};
  std::int32_t normalY{};
  std::int32_t normalZ{};
  float distance{};
  std::uint8_t block{};
};

[[nodiscard]] RaycastHit raycastDda(
    std::span<const std::uint8_t> blocks,
    std::int32_t width,
    std::int32_t height,
    std::int32_t depth,
    float originX,
    float originY,
    float originZ,
    float directionX,
    float directionY,
    float directionZ,
    float maxDistance) noexcept;

}  // namespace vf
