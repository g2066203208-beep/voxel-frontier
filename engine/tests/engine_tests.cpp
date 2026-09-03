#include "vf/Engine.hpp"
#include "vf/Mesher.hpp"
#include "vf/Raycast.hpp"

#include <cassert>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <span>
#include <vector>

namespace {

std::size_t idx(int x, int y, int z, int w, int d) {
  return static_cast<std::size_t>((y * d + z) * w + x);
}

void testSingleVoxelGreedyMesh() {
  std::vector<std::uint8_t> blocks(4 * 4 * 4, 0);
  blocks[idx(1, 1, 1, 4, 4)] = static_cast<std::uint8_t>(vf::Block::Stone);
  const auto mesh = vf::buildGreedyMesh(blocks, 4, 4, 4);
  assert(mesh.quadCount == 6);
  assert(mesh.vertices.size() == 24);
  assert(mesh.indices.size() == 36);
}

void testSolidChunkGreedyCollapse() {
  std::vector<std::uint8_t> blocks(16 * 16 * 16, static_cast<std::uint8_t>(vf::Block::Stone));
  const auto mesh = vf::buildGreedyMesh(blocks, 16, 16, 16);
  assert(mesh.quadCount == 6);
  assert(mesh.vertices.size() == 24);
  assert(mesh.indices.size() == 36);
}

void testMaterialBoundaryIsPreserved() {
  std::vector<std::uint8_t> blocks(4 * 2 * 2, 0);
  blocks[idx(0, 0, 0, 4, 2)] = static_cast<std::uint8_t>(vf::Block::Stone);
  blocks[idx(1, 0, 0, 4, 2)] = static_cast<std::uint8_t>(vf::Block::Dirt);
  const auto mesh = vf::buildGreedyMesh(blocks, 4, 2, 2);
  assert(mesh.quadCount >= 6);
}

void testDdaRaycast() {
  std::vector<std::uint8_t> blocks(8 * 8 * 8, 0);
  blocks[idx(4, 3, 3, 8, 8)] = static_cast<std::uint8_t>(vf::Block::Grass);
  const auto hit = vf::raycastDda(blocks, 8, 8, 8, 0.5F, 3.5F, 3.5F, 1.0F, 0.0F, 0.0F, 10.0F);
  assert(hit.hit);
  assert(hit.x == 4 && hit.y == 3 && hit.z == 3);
  assert(hit.normalX == -1 && hit.normalY == 0 && hit.normalZ == 0);
  assert(hit.block == static_cast<std::uint8_t>(vf::Block::Grass));
  assert(hit.distance > 3.4F && hit.distance < 3.6F);
}

void testGeneratedChunk() {
  constexpr int width = 16;
  constexpr int height = 64;
  constexpr int depth = 16;
  std::vector<std::uint8_t> blocks(width * height * depth);
  vf::fillChunk(vf::ChunkSpec{0, 0, width, height, depth}, blocks);

  std::size_t solids = 0;
  for (const auto block : blocks) solids += block != 0;
  assert(solids > 0);
  assert(solids < blocks.size());

  const auto mesh = vf::buildGreedyMesh(blocks, width, height, depth);
  assert(mesh.quadCount > 0);
  assert(mesh.indices.size() == static_cast<std::size_t>(mesh.quadCount) * 6);
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
  assert(totalQuads > 0);
  assert(elapsed.count() < 10000);
}

}  // namespace

int main() {
  testSingleVoxelGreedyMesh();
  testSolidChunkGreedyCollapse();
  testMaterialBoundaryIsPreserved();
  testDdaRaycast();
  testGeneratedChunk();
  performanceSmoke();
  std::cout << "vf_engine_tests: PASS\n";
  return 0;
}
