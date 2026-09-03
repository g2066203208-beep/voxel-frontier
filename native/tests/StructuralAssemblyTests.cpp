#include "vf/physics/StructuralAssembly.hpp"
#include "vf/physics/PhysicsWorld.hpp"

#include <cstdlib>
#include <iostream>
#include <string_view>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "STRUCTURAL ASSEMBLY TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

vf::PhysicsWorld makeWorld() {
    vf::PhysicsEnvironment environment{};
    environment.planet.radius = 1.0;
    environment.planet.maxElevation = 0.0;
    environment.surfaceGravity = 0.0;
    environment.atmosphere.seaLevelPressurePa = 0.0;
    environment.ocean.enabled = false;
    return vf::PhysicsWorld{environment};
}

vf::RigidBodyDesc makeBody(const glm::dvec3& position, vf::MotionType type) {
    vf::RigidBodyDesc desc{};
    desc.position = position;
    desc.motionType = type;
    desc.mass = type == vf::MotionType::Dynamic ? 2.0 : 0.0;
    desc.collisionShape = vf::CollisionShape::sphere(0.15);
    desc.linearDamping = 0.0;
    desc.angularDamping = 0.0;
    desc.aerodynamics.referenceArea = 0.0;
    return desc;
}

vf::MaterialDefinition testMaterial() {
    vf::MaterialDefinition material{};
    material.youngModulusPa = 2.0e6;
    material.ultimateStrengthPa = 5.0e6;
    material.bendingStrengthPa = 4.0e6;
    material.shearStrengthPa = 3.0e6;
    material.fractureToughnessJPerM2 = 5000.0;
    material.meltingPointK = 1000.0;
    return material;
}

void testStretchedBondPullsRigidBodyTowardAnchor() {
    auto world = makeWorld();
    const auto anchorId = world.createRigidBody(makeBody({10.0, 0.0, 0.0}, vf::MotionType::Static));
    const auto payloadId = world.createRigidBody(makeBody({12.0, 0.0, 0.0}, vf::MotionType::Dynamic));

    vf::StructuralAssembly assembly;
    vf::StructuralBondDesc bond{};
    bond.bodyA = anchorId;
    bond.bodyB = payloadId;
    bond.restLengthMeters = 1.5;
    bond.geometry.areaM2 = 0.01;
    bond.geometry.sectionModulusM3 = 1.0e-4;
    bond.material = testMaterial();
    bond.axialDampingNsPerM = 0.0;
    const auto bondId = assembly.addBond(bond, world);

    assembly.step(world, 1.0 / 120.0);
    world.stepFixed();
    const auto* payload = world.body(payloadId);
    const auto* storedBond = assembly.bond(bondId);
    require(payload != nullptr && storedBond != nullptr, "structural test objects must exist");
    require(payload->linearVelocity.x < 0.0, "stretched material bond must pull the payload toward the anchor");
    require(storedBond->lastAxialForceN > 0.0, "material bond must report physical axial force");
    require(!storedBond->damageState.broken, "moderate elastic stretch must not immediately fracture the bond");
}

void testThermallySoftenedAssemblyBreaks() {
    auto world = makeWorld();
    const auto aId = world.createRigidBody(makeBody({10.0, 0.0, 0.0}, vf::MotionType::Static));
    const auto bId = world.createRigidBody(makeBody({11.7, 0.0, 0.0}, vf::MotionType::Dynamic));

    vf::StructuralAssembly assembly;
    vf::StructuralBondDesc desc{};
    desc.bodyA = aId;
    desc.bodyB = bId;
    desc.restLengthMeters = 1.5;
    desc.geometry.areaM2 = 0.002;
    desc.geometry.sectionModulusM3 = 3.0e-5;
    desc.material = testMaterial();
    desc.material.ultimateStrengthPa = 2.0e6;
    const auto id = assembly.addBond(desc, world);
    auto* bond = assembly.bond(id);
    require(bond != nullptr, "hot bond must exist");
    bond->materialState.temperatureK = 990.0;

    assembly.step(world, 1.0 / 120.0);
    require(bond->damageState.broken, "near-melting material bond must fracture under a load it can no longer carry");
}

void testBrokenBondStopsTransmittingForce() {
    auto world = makeWorld();
    const auto aId = world.createRigidBody(makeBody({10.0, 0.0, 0.0}, vf::MotionType::Static));
    const auto bId = world.createRigidBody(makeBody({13.0, 0.0, 0.0}, vf::MotionType::Dynamic));

    vf::StructuralAssembly assembly;
    vf::StructuralBondDesc desc{};
    desc.bodyA = aId;
    desc.bodyB = bId;
    desc.restLengthMeters = 1.0;
    desc.geometry.areaM2 = 0.001;
    desc.material = testMaterial();
    desc.material.ultimateStrengthPa = 1000.0;
    const auto id = assembly.addBond(desc, world);
    auto* bond = assembly.bond(id);
    assembly.step(world, 1.0 / 120.0);
    require(bond != nullptr && bond->damageState.broken, "deliberately weak bond must break");

    auto* payload = world.body(bId);
    require(payload != nullptr, "payload must exist");
    payload->linearVelocity = {};
    assembly.step(world, 1.0 / 120.0);
    world.stepFixed();
    require(glm::length(payload->linearVelocity) < 1.0e-12, "broken bond must stop transmitting elastic force");
}

} // namespace

int main() {
    testStretchedBondPullsRigidBodyTowardAnchor();
    testThermallySoftenedAssemblyBreaks();
    testBrokenBondStopsTransmittingForce();
    std::cout << "vf_structural_assembly_tests: PASS\n";
    return 0;
}
