#include "vf/Raycast.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>

namespace vf {
namespace {

[[nodiscard]] std::size_t index3D(
    std::int32_t x,
    std::int32_t y,
    std::int32_t z,
    std::int32_t width,
    std::int32_t depth) noexcept {
  return static_cast<std::size_t>((y * depth + z) * width + x);
}

[[nodiscard]] bool inside(
    std::int32_t x,
    std::int32_t y,
    std::int32_t z,
    std::int32_t width,
    std::int32_t height,
    std::int32_t depth) noexcept {
  return x >= 0 && y >= 0 && z >= 0 && x < width && y < height && z < depth;
}

[[nodiscard]] float initialTMax(float origin, float direction, std::int32_t voxel, std::int32_t step) noexcept {
  if (step == 0) return std::numeric_limits<float>::infinity();
  const float boundary = step > 0 ? static_cast<float>(voxel + 1) : static_cast<float>(voxel);
  return (boundary - origin) / direction;
}

}  // namespace

RaycastHit raycastDda(
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
    float maxDistance) noexcept {
  RaycastHit result{};
  if (width <= 0 || height <= 0 || depth <= 0 || maxDistance <= 0.0F) return result;

  const auto required = static_cast<std::size_t>(width) * height * depth;
  if (blocks.size() < required) return result;

  const float length = std::sqrt(directionX * directionX + directionY * directionY + directionZ * directionZ);
  if (!(length > 0.0F) || !std::isfinite(length)) return result;

  directionX /= length;
  directionY /= length;
  directionZ /= length;

  std::int32_t x = static_cast<std::int32_t>(std::floor(originX));
  std::int32_t y = static_cast<std::int32_t>(std::floor(originY));
  std::int32_t z = static_cast<std::int32_t>(std::floor(originZ));

  const std::int32_t stepX = (directionX > 0.0F) - (directionX < 0.0F);
  const std::int32_t stepY = (directionY > 0.0F) - (directionY < 0.0F);
  const std::int32_t stepZ = (directionZ > 0.0F) - (directionZ < 0.0F);

  const float inf = std::numeric_limits<float>::infinity();
  const float deltaX = stepX == 0 ? inf : std::abs(1.0F / directionX);
  const float deltaY = stepY == 0 ? inf : std::abs(1.0F / directionY);
  const float deltaZ = stepZ == 0 ? inf : std::abs(1.0F / directionZ);

  float tMaxX = initialTMax(originX, directionX, x, stepX);
  float tMaxY = initialTMax(originY, directionY, y, stepY);
  float tMaxZ = initialTMax(originZ, directionZ, z, stepZ);

  std::int32_t normalX = 0;
  std::int32_t normalY = 0;
  std::int32_t normalZ = 0;
  float distance = 0.0F;

  const std::int32_t maxSteps = width + height + depth + static_cast<std::int32_t>(maxDistance * 4.0F) + 16;
  for (std::int32_t step = 0; step < maxSteps && distance <= maxDistance; ++step) {
    if (inside(x, y, z, width, height, depth)) {
      const auto block = blocks[index3D(x, y, z, width, depth)];
      if (block != 0) {
        result.hit = true;
        result.x = x;
        result.y = y;
        result.z = z;
        result.normalX = normalX;
        result.normalY = normalY;
        result.normalZ = normalZ;
        result.distance = std::max(0.0F, distance);
        result.block = block;
        return result;
      }
    }

    if (tMaxX <= tMaxY && tMaxX <= tMaxZ) {
      x += stepX;
      distance = tMaxX;
      tMaxX += deltaX;
      normalX = -stepX;
      normalY = 0;
      normalZ = 0;
    } else if (tMaxY <= tMaxZ) {
      y += stepY;
      distance = tMaxY;
      tMaxY += deltaY;
      normalX = 0;
      normalY = -stepY;
      normalZ = 0;
    } else {
      z += stepZ;
      distance = tMaxZ;
      tMaxZ += deltaZ;
      normalX = 0;
      normalY = 0;
      normalZ = -stepZ;
    }
  }

  return result;
}

}  // namespace vf
