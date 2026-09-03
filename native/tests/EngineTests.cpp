#include "vf/core/Engine.hpp"
#include "vf/world/Chunk.hpp"
#include "vf/world/World.hpp"

#include <chrono>
#include <cstdlib>
#include <iostream>
#include <string_view>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void testChunkStorage() {
    vf::Chunk chunk{{1, -2, 3}};
    require(chunk.get(4, 5, 6) == static_cast<vf::BlockId>(vf::Block::Air), "new chunk must be air");
    chunk.clearDirty();
    chunk.set(4, 5, 6, static_cast<vf::BlockId>(vf::Block::Stone));
    require(chunk.get(4, 5, 6) == static_cast<vf::BlockId>(vf::Block::Stone), "chunk set/get mismatch");
    require(chunk.dirty(), "edited chunk must become dirty");
}

void testNegativeWorldCoordinates() {
    require(vf::World::floorDiv(-1, vf::kChunkEdge) == -1, "floorDiv(-1) must map to previous chunk");
    require(vf::World::floorDiv(-32, vf::kChunkEdge) == -1, "floorDiv exact negative boundary failed");
    require(vf::World::floorDiv(-33, vf::kChunkEdge) == -2, "floorDiv below negative boundary failed");
    require(vf::World::positiveMod(-1, vf::kChunkEdge) == 31, "positiveMod(-1) failed");
    require(vf::World::positiveMod(-32, vf::kChunkEdge) == 0, "positiveMod negative boundary failed");
}

void testDeterministicGeneration() {
    vf::World a{123456789ULL};
    vf::World b{123456789ULL};
    auto& ca = a.ensureChunk({-3, 1, 7});
    auto& cb = b.ensureChunk({-3, 1, 7});
    require(ca.blocks() == cb.blocks(), "same seed and coord must generate identical chunk data");
}

void testBoundaryDirtyPropagation() {
    vf::World world{7};
    auto& owner = world.ensureChunk({0, 1, 0});
    auto& neighbor = world.ensureChunk({1, 1, 0});
    owner.clearDirty();
    neighbor.clearDirty();

    world.setBlock(31, 40, 0, static_cast<vf::BlockId>(vf::Block::Air));
    require(owner.dirty(), "owner chunk should be dirty after edit");
    require(neighbor.dirty(), "loaded neighboring chunk should be dirty for border edit");
}

void testBootstrapAndTiming() {
    const auto start = std::chrono::steady_clock::now();
    vf::Engine engine{42};
    engine.bootstrap();
    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - start);

    require(engine.world().loadedChunkCount() == 75, "bootstrap should load 5x5x3 chunks");
    engine.tick(1.0 / 60.0);
    require(engine.frameIndex() == 1, "engine frame counter failed");
    require(engine.elapsedSeconds() > 0.0, "engine elapsed time failed");

    std::cout << "benchmark: generated 75 x 32^3 chunks in " << elapsed.count() << " ms\n";
}

} // namespace

int main() {
    testChunkStorage();
    testNegativeWorldCoordinates();
    testDeterministicGeneration();
    testBoundaryDirtyPropagation();
    testBootstrapAndTiming();
    std::cout << "vf_native_engine_tests: PASS\n";
    return 0;
}
