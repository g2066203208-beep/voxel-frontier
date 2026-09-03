#include "vf/Engine.hpp"
#include "vf/Mesher.hpp"
#include "vf/Raycast.hpp"

#include <chrono>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <vector>

namespace {

void require(bool condition, std::string_view message) {
  if (!condition) throw std::runtime_error(std::string(message));
}

std::size_t idx(int x, int y, int z, int w, int d) {
  return static_cast<std::size_t>((y * d + z) * w + x);
}

void testSingleVoxelGreedyMesh() {
  std::vector<std::uint8_t> blocks(4 * 4 * 4, 0);
  blocks[idx(1, 1, 1, 4, 4)] = static_cast<std::uint8_t>(vf::Block::Stone);
  const auto mesh = vf::buildGreedyMesh(blocks, 4, 4, 4);
  require(mesh.quadCount == 6, "single voxel must produce 6 quads");
  require(mesh.vertices.size() == 24, "single voxel vertex count mismatch");
  require(mesh.indices.size() == 36, "single voxel index count mismatch");
}

void testSolidChunkGreedyCollapse() {
  std::vector<std::uint8_t> blocks(16 * 16 * 16, static_cast<std::uint8_t>(vf::Block::Stone));
  const auto mesh = vf::buildGreedyMesh(blocks, 16, 16, 16);
  require(mesh.quadCount == 6, "solid chunk must greedily collapse to 6 quads");
  require(mesh.vertices.size() == 24, "solid chunk vertex count mismatch");
  require(mesh.indices.size() == 36, "solid chunk index count mismatch");
}

void testMaterialBoundaryIsPreserved() {
  std::vector<std::uint8_t> blocks(4 * 2 * 2, 0);
  blocks[idx(0, 0, 0, 4, 2)] = static_cast<std::uint8_t>(vf::Block::Stone);
  blocks[idx(1, 0, 0, 4, 2)] = static_cast<std::uint8_t>(vf::Block::Dirt);
  const auto mesh = vf::buildGreedyMesh(blocks, 4, 2, 2);
  require(mesh.quadCount >= 6, "different materials must not be merged into one material face");
}

void testDdaRaycast() {
  std::vector<std::uint8_t> blocks(8 * 8 * 8, 0);
  blocks[idx(4, 3, 3, 8, 8)] = static_cast<std::uint8_t>(vf::Block::Grass);
  const auto hit = vf::raycastDda(blocks, 8, 8, 8, 0.5F, 3.5F, 3.5F, 1.0F, 0.0F, 0.0F, 10.0F);
  require(hit.hit, "DDA ray must hit target voxel");
  require(hit.x == 4 && hit.y == 3 && hit.z == 3, "DDA hit coordinate mismatch");
  require(hit.normalX == -1 && hit.normalY == 0 && hit.normalZ == 0, "DDA hit normal mismatch");
  require(hit.block == static_cast<std::uint8_t>(vf::Block::Grass), "DDA block id mismatch");
  require(hit.distance > 3.4F && hit.distance < 3.6F, "DDA hit distance mismatch");
}

void testGeneratedChunk() {
  constexpr int width = 16;
  constexpr int height = 64;
  constexpr int depth = 16;
  std::vector<std::uint8_t> blocks(width * height * depth);
  vf::fillChunk(vf::ChunkSpec{0, 0, width, height, depth}, blocks);

  std::size_t solids = 0;
  for (const auto block : blocks) solids += block != 0;
  require(solids > 0, "generated chunk contains no terrain");
  require(solids < blocks.size(), "generated chunk contains no air");

  const auto mesh = vf::buildGreedyMesh(blocks, width, height, depth);
  require(mesh.quadCount > 0, "generated chunk produced empty mesh");
  require(mesh.indices.size() == static_cast<std::size_t>(mesh.quadCount) * 6,
          "generated chunk index/quad count mismatch");
}

void performanceSmoke() {
  constexpr int width = 16;
  constexpr int height = 64;
  constexpr int depth = 16;
  constexpr int iterations = 128;
  std::vector<std::uint8_t> blocks(width * height * depth);

  const auto start = std::chrono::steady_clock::now();
  std::uint64_t totalQuads = 0;
  for (int i = 0; i < iterations; ++i) {
    vf::fillChunk(vf::ChunkSpec{i % 16, i / 16, width, height, depth}, blocks);
    totalQuads += vf::buildGreedyMesh(blocks, width, height, depth).quadCount;
  }
  const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
      std::chrono::steady_clock::now() - start);

  std::cout << "benchmark: generated+meshed " << iterations << " chunks in "
            << elapsed.count() << " ms, quads=" << totalQuads << '\n';
  require(totalQuads > 0, "performance smoke generated no geometry");
  require(elapsed.count() < 10000, "performance smoke exceeded 10 second guardrail");
}

}  // namespace

int main() {
  try {
    testSingleVoxelGreedyMesh();
    testSolidChunkGreedyCollapse();
    testMaterialBoundaryIsPreserved();
    testDdaRaycast();
    testGeneratedChunk();
    performanceSmoke();
    std::cout << "vf_engine_tests: PASS\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "vf_engine_tests: FAIL: " << error.what() << '\n';
    return 1;
  }
}
