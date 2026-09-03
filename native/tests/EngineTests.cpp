#include "vf/core/Engine.hpp"
#include "vf/player/PlanetCamera.hpp"
#include "vf/world/Chunk.hpp"
#include "vf/world/PlanetSurface.hpp"
#include "vf/world/World.hpp"

#include <chrono>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

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

void testCubeSphereProjection() {
    for (std::uint32_t face = 0; face < 6U; ++face) {
        for (double u : {-1.0, -0.25, 0.0, 0.75, 1.0}) {
            for (double v : {-1.0, 0.0, 1.0}) {
                const auto direction = vf::cubeSphereDirection(face, u, v);
                require(std::abs(glm::length(direction) - 1.0) < 1.0e-12, "cube-sphere direction must be normalized");
            }
        }
    }
}

void testPlanetSurfaceDeterminism() {
    vf::PlanetDefinition definition{};
    definition.seed = 99;
    definition.radius = 200.0;
    definition.maxElevation = 20.0;

    const auto a = vf::buildPlanetSurface(definition, 12U);
    const auto b = vf::buildPlanetSurface(definition, 12U);
    require(a.vertices.size() == 6U * 13U * 13U, "planet vertex count mismatch");
    require(a.indices.size() == 6U * 12U * 12U * 6U, "planet index count mismatch");
    require(a.vertices.size() == b.vertices.size() && a.indices == b.indices, "planet topology must be deterministic");

    for (std::size_t i = 0; i < a.vertices.size(); i += 37U) {
        const auto& va = a.vertices[i];
        const auto& vb = b.vertices[i];
        require(glm::length(va.position - vb.position) < 1.0e-6F, "planet positions must be deterministic");
        const double radius = glm::length(glm::dvec3{va.position});
        require(radius >= definition.radius - definition.maxElevation - 1.0e-3, "planet vertex fell below height bound");
        require(radius <= definition.radius + definition.maxElevation + 1.0e-3, "planet vertex exceeded height bound");
    }
}

void testRadialCamera() {
    vf::PlanetDefinition definition{};
    definition.radius = 240.0;
    definition.maxElevation = 18.0;
    vf::PlanetCamera camera{definition};
    const double initialAltitude = camera.altitude();
    require(initialAltitude >= 1.70 && initialAltitude <= 1.80, "camera must spawn at eye height over terrain");

    vf::PlanetMovementInput ascend{};
    ascend.vertical = 1.0;
    ascend.sprint = true;
    camera.update(ascend, 0.5);
    require(camera.altitude() > initialAltitude + 5.0, "camera ascend should increase planetary altitude");

    const auto localUp = camera.up();
    require(std::abs(glm::length(localUp) - 1.0) < 1.0e-12, "radial up must remain normalized");
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

    std::cout << "legacy benchmark: generated 75 x 32^3 chunks in " << elapsed.count() << " ms\n";
}

} // namespace

int main() {
    testChunkStorage();
    testNegativeWorldCoordinates();
    testDeterministicGeneration();
    testBoundaryDirtyPropagation();
    testCubeSphereProjection();
    testPlanetSurfaceDeterminism();
    testRadialCamera();
    testBootstrapAndTiming();
    std::cout << "vf_native_engine_tests: PASS\n";
    return 0;
}
