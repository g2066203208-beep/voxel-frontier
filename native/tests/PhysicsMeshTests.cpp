#include "vf/gameplay/PhysicsPlayground.hpp"
#include "vf/render/PhysicsDebugMesh.hpp"

#include <cstdlib>
#include <iostream>
#include <string_view>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "PHYSICS MESH TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void requireValidIndices(const vf::PlanetMesh& mesh) {
    require(!mesh.vertices.empty(), "debug mesh should contain vertices");
    require(!mesh.indices.empty(), "debug mesh should contain indices");
    require((mesh.indices.size() % 3U) == 0U, "debug mesh index count must be divisible by three");
    for (const auto index : mesh.indices) {
        require(index < mesh.vertices.size(), "debug mesh index escaped vertex range");
    }
}

void testPrimitiveBuilders() {
    vf::PlanetMesh mesh{};
    vf::appendDebugSphere(mesh, {1.0, 2.0, 3.0}, 0.7, {1.0F, 0.0F, 0.0F});
    vf::appendDebugBox(mesh, {4.0, 2.0, 1.0}, {}, {0.5, 1.0, 1.5}, {0.0F, 1.0F, 0.0F});
    vf::appendDebugRod(mesh, {-2.0, 0.0, 0.0}, {2.0, 3.0, 1.0}, 0.08, {0.0F, 0.0F, 1.0F});
    requireValidIndices(mesh);
    require(mesh.triangleCount() > 100U, "primitive builder should produce meaningful visible geometry");
}

void testPlaygroundProducesMovingGeometry() {
    vf::PlanetDefinition planet{};
    planet.radius = 240.0;
    planet.maxElevation = 22.0;
    planet.atmosphereHeight = 120.0;

    vf::PhysicsEnvironment environment{};
    environment.planet = planet;
    environment.surfaceGravity = 9.81;
    environment.ocean.enabled = false;
    environment.atmosphere.prevailingWind = {6.0, 0.0, 2.0};
    vf::PhysicsWorld physics{environment};
    vf::PhysicsPlayground playground{physics, planet, glm::normalize(glm::dvec3{0.72, 0.52, 0.46})};

    const auto initialMesh = playground.buildDebugMesh();
    requireValidIndices(initialMesh);
    require(physics.bodies().size() >= 14U, "playground should instantiate multiple mechanical and environmental bodies");
    require(physics.activeConstraintCount() >= 5U, "playground should instantiate spring, hinge and gear constraints");

    for (int frame = 0; frame < 240; ++frame) {
        physics.advance(1.0 / 60.0);
        playground.update(1.0 / 60.0);
    }
    const auto movedMesh = playground.buildDebugMesh();
    requireValidIndices(movedMesh);
    require(movedMesh.vertices.size() == initialMesh.vertices.size(), "playground topology should stay stable for inexpensive streaming");

    bool positionChanged = false;
    const std::size_t sampleCount = std::min(initialMesh.vertices.size(), movedMesh.vertices.size());
    for (std::size_t i = 0; i < sampleCount; i += 17U) {
        if (glm::length(movedMesh.vertices[i].position - initialMesh.vertices[i].position) > 0.01F) {
            positionChanged = true;
            break;
        }
    }
    require(positionChanged, "physics playground geometry must actually move after simulation advances");
}

} // namespace

int main() {
    testPrimitiveBuilders();
    testPlaygroundProducesMovingGeometry();
    std::cout << "vf_physics_mesh_tests: PASS\n";
    return 0;
}
