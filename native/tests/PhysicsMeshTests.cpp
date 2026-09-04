#include "vf/physics/PhysicsWorld.hpp"
#include "vf/render/PhysicsDebugMesh.hpp"

#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

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

void testGenericRigidBodyProducesMovingGeometry() {
    vf::PhysicsEnvironment environment{};
    environment.planet.radius = 100.0;
    environment.planet.maxElevation = 0.0;
    environment.surfaceGravity = 0.0;
    environment.atmosphere.seaLevelPressurePa = 0.0;
    environment.atmosphere.gustAmplitude = 0.0;
    environment.atmosphere.prevailingWind = {};
    environment.ocean.enabled = false;
    vf::PhysicsWorld physics{environment};

    vf::RigidBodyDesc desc{};
    desc.mass = 8.0;
    desc.position = {150.0, 0.0, 0.0};
    desc.linearVelocity = {0.0, 3.0, 0.0};
    desc.collisionShape = vf::CollisionShape::box({0.5, 0.8, 0.4});
    desc.linearDamping = 0.0;
    desc.angularDamping = 0.0;
    desc.aerodynamics.referenceArea = 0.0;
    const std::uint32_t id = physics.createRigidBody(desc);

    const auto* initialBody = physics.body(id);
    require(initialBody != nullptr, "generic rigid body should exist");
    vf::PlanetMesh initialMesh{};
    vf::appendDebugBox(initialMesh, initialBody->position, initialBody->orientation,
        {0.5, 0.8, 0.4}, {0.35F, 0.55F, 0.82F});
    requireValidIndices(initialMesh);

    for (int frame = 0; frame < 120; ++frame) physics.advance(1.0 / 60.0);

    const auto* movedBody = physics.body(id);
    require(movedBody != nullptr, "generic rigid body should survive simulation");
    require(glm::length(movedBody->position - desc.position) > 1.0,
        "generic physics body should move without a special-case playground controller");

    vf::PlanetMesh movedMesh{};
    vf::appendDebugBox(movedMesh, movedBody->position, movedBody->orientation,
        {0.5, 0.8, 0.4}, {0.35F, 0.55F, 0.82F});
    requireValidIndices(movedMesh);
    require(movedMesh.vertices.size() == initialMesh.vertices.size(),
        "generic rigid-body render topology should stay stable while its pose changes");

    bool positionChanged = false;
    for (std::size_t i = 0; i < initialMesh.vertices.size(); ++i) {
        if (glm::length(movedMesh.vertices[i].position - initialMesh.vertices[i].position) > 0.5F) {
            positionChanged = true;
            break;
        }
    }
    require(positionChanged, "debug geometry should follow authoritative rigid-body motion");
}

} // namespace

int main() {
    testPrimitiveBuilders();
    testGenericRigidBodyProducesMovingGeometry();
    std::cout << "vf_physics_mesh_tests: PASS\n";
    return 0;
}
