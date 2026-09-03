#include "vf/Engine.hpp"

#include <cstdint>
#include <span>

#if defined(__EMSCRIPTEN__)
#include <emscripten/emscripten.h>
#define VF_EXPORT EMSCRIPTEN_KEEPALIVE
#else
#define VF_EXPORT
#endif

extern "C" {

VF_EXPORT std::uint32_t vf_engine_abi_version() noexcept {
  return vf::kEngineAbiVersion;
}

VF_EXPORT std::int32_t vf_terrain_height(std::int32_t worldX, std::int32_t worldZ) noexcept {
  return vf::terrainHeight(worldX, worldZ);
}

VF_EXPORT std::int32_t vf_fill_chunk(
    std::uint8_t* output,
    std::int32_t outputLength,
    std::int32_t chunkX,
    std::int32_t chunkZ,
    std::int32_t width,
    std::int32_t height,
    std::int32_t depth) noexcept {
  if (output == nullptr || outputLength <= 0 || width <= 0 || height <= 0 || depth <= 0) return 0;

  const auto required = static_cast<std::int64_t>(width) * height * depth;
  if (required <= 0 || required > outputLength) return 0;

  const vf::ChunkSpec spec{chunkX, chunkZ, width, height, depth};
  vf::fillChunk(spec, std::span<std::uint8_t>(output, static_cast<std::size_t>(required)));
  return static_cast<std::int32_t>(required);
}

}  // extern "C"
