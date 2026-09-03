#include "vf/physics/PhysicsWorld.hpp"
#include "vf/physics/ShallowWater.hpp"
#include "vf/physics/TreePhysics.hpp"
#include "vf/player/PlanetCamera.hpp"
#include "vf/world/PlanetSurface.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "PLANET PHYSICS TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
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
    camera.update(ascend, 0.05);
    require(camera.altitude() > initialAltitude + 3.0, "camera ascend should increase planetary altitude");
    require(std::abs(glm::length(camera.up()) - 1.0) < 1.0e-12, "radial up must remain normalized");
}

vf::PhysicsEnvironment makeVacuumPhysicsEnvironment() {
    vf::PhysicsEnvironment environment{};
    environment.planet.radius = 100.0;
    environment.planet.maxElevation = 0.0;
    environment.planet.atmosphereHeight = 50.0;
    environment.surfaceGravity = 0.0;
    environment.atmosphere.seaLevelPressurePa = 0.0;
    environment.atmosphere.gustAmplitude = 0.0;
    environment.atmosphere.prevailingWind = {};
    environment.ocean.enabled = false;
    return environment;
}

void testFixedStepAndMomentum() {
    const auto environment = makeVacuumPhysicsEnvironment();
    vf::PhysicsWorld worldA{environment};
    vf::PhysicsWorld worldB{environment};

    vf::RigidBodyDesc desc{};
    desc.mass = 4.0;
    desc.position = {150.0, 0.0, 0.0};
    desc.linearVelocity = {3.0, -2.0, 0.5};
    desc.linearDamping = 0.0;
    desc.angularDamping = 0.0;
    desc.aerodynamics.referenceArea = 0.0;
    const auto aId = worldA.createRigidBody(desc);
    const auto bId = worldB.createRigidBody(desc);

    worldA.advance(1.0 / 60.0);
    worldB.advance(1.0 / 120.0);
    worldB.advance(1.0 / 120.0);

    const auto* a = worldA.body(aId);
    const auto* b = worldB.body(bId);
    require(a != nullptr && b != nullptr, "fixed-step bodies missing");
    require(glm::length(a->position - b->position) < 1.0e-12, "fixed-step integration must be frame-rate independent");
    require(glm::length(a->linearMomentum() - glm::dvec3{12.0, -8.0, 2.0}) < 1.0e-10, "linear momentum must equal mass times velocity");
}

void testRigidBodyCollisionMomentumConservation() {
    const auto environment = makeVacuumPhysicsEnvironment();
    vf::PhysicsWorld world{environment};

    vf::RigidBodyDesc aDesc{};
    aDesc.mass = 2.0;
    aDesc.position = {150.0, -2.0, 0.0};
    aDesc.linearVelocity = {0.0, 5.0, 0.0};
    aDesc.collisionRadius = 0.5;
    aDesc.linearDamping = 0.0;
    aDesc.angularDamping = 0.0;
    aDesc.material.friction = 0.0;
    aDesc.material.restitution = 0.6;
    aDesc.aerodynamics.referenceArea = 0.0;

    vf::RigidBodyDesc bDesc = aDesc;
    bDesc.mass = 1.0;
    bDesc.position = {150.0, 2.0, 0.0};
    bDesc.linearVelocity = {0.0, -2.0, 0.0};

    const auto aId = world.createRigidBody(aDesc);
    const auto bId = world.createRigidBody(bDesc);
    const glm::dvec3 initialMomentum = aDesc.mass * aDesc.linearVelocity + bDesc.mass * bDesc.linearVelocity;

    for (int i = 0; i < 120; ++i) world.stepFixed();
    const auto* a = world.body(aId);
    const auto* b = world.body(bId);
    require(a != nullptr && b != nullptr, "collision bodies missing");
    require(glm::length(a->linearMomentum() + b->linearMomentum() - initialMomentum) < 1.0e-8, "isolated collision must conserve linear momentum");
}

void testRadialGravityAndGroundFriction() {
    vf::PhysicsEnvironment environment{};
    environment.planet.radius = 100.0;
    environment.planet.maxElevation = 0.0;
    environment.surfaceGravity = 9.81;
    environment.atmosphere.seaLevelPressurePa = 0.0;
    environment.ocean.enabled = false;
    vf::PhysicsWorld world{environment};

    vf::RigidBodyDesc desc{};
    desc.mass = 10.0;
    desc.position = {0.0, 101.0, 0.0};
    desc.linearVelocity = {8.0, 0.0, 0.0};
    desc.collisionRadius = 1.0;
    desc.linearDamping = 0.0;
    desc.material.friction = 0.9;
    desc.material.restitution = 0.0;
    desc.aerodynamics.referenceArea = 0.0;
    const auto id = world.createRigidBody(desc);

    for (int i = 0; i < 120; ++i) world.stepFixed();
    const auto* body = world.body(id);
    require(body != nullptr, "friction body missing");
    require(glm::length(body->linearVelocity) < 8.0, "ground friction should remove tangential speed");
    require(glm::length(body->position) >= 100.999, "planet contact must prevent terrain penetration");
}

void testAtmospherePressureDensityAndWind() {
    vf::PhysicsEnvironment environment{};
    environment.planet.radius = 1000.0;
    environment.planet.atmosphereHeight = 2000.0;
    environment.surfaceGravity = 9.81;
    environment.weather.stormIntensity = 0.6;
    const auto sea = environment.sampleAtmosphere({0.0, 1000.0, 0.0}, 12.0);
    const auto high = environment.sampleAtmosphere({0.0, 1500.0, 0.0}, 12.0);

    require(sea.temperatureK > high.temperatureK, "temperature should decrease with altitude");
    require(sea.pressurePa > high.pressurePa, "air pressure should decrease with altitude");
    require(sea.densityKgPerM3 > high.densityKgPerM3, "air density should decrease with altitude");
    require(glm::length(sea.windVelocity) > 0.1, "wind field should be non-zero");
}

void testBuoyancy() {
    vf::PhysicsEnvironment environment{};
    environment.planet.radius = 100.0;
    environment.planet.maxElevation = 0.0;
    environment.surfaceGravity = 9.81;
    environment.atmosphere.seaLevelPressurePa = 0.0;
    environment.ocean.enabled = true;
    environment.ocean.surfaceRadius = 110.0;
    environment.ocean.densityKgPerM3 = 1000.0;
    vf::PhysicsWorld world{environment};

    vf::RigidBodyDesc desc{};
    desc.mass = 350.0;
    desc.position = {0.0, 109.0, 0.0};
    desc.collisionRadius = 1.0;
    desc.linearDamping = 0.0;
    desc.aerodynamics.referenceArea = 0.0;
    desc.buoyancy.enabled = true;
    desc.buoyancy.displacedVolume = 1.0;
    desc.buoyancy.fluidDragCoefficient = 0.2;
    desc.buoyancy.fluidReferenceArea = 1.0;
    const auto id = world.createRigidBody(desc);

    for (int i = 0; i < 12; ++i) world.stepFixed();
    const auto* body = world.body(id);
    require(body != nullptr, "buoyant body missing");
    require(glm::dot(body->linearVelocity, glm::normalize(body->position)) > 0.0, "water displacement should create net upward motion");
}

void testShallowWaterConservation() {
    vf::ShallowWaterGrid water{4, 1, 1.0};
    water.cell(0, 0).bedElevation = 2.0;
    water.cell(1, 0).bedElevation = 1.0;
    water.cell(2, 0).bedElevation = 0.0;
    water.cell(3, 0).bedElevation = -0.5;
    water.addWater(0, 0, 1.5);
    const double initialVolume = water.totalWaterVolume();

    for (int i = 0; i < 240; ++i) water.step(1.0 / 120.0, 9.81);
    require(water.cell(3, 0).waterDepth > 0.0, "water should propagate downhill");
    require(std::abs(water.totalWaterVolume() - initialVolume) < 1.0e-9, "closed grid must conserve water volume");
}

void testTreeFallsAfterCut() {
    vf::TreePhysics tree{};
    tree.trunkLength = 9.0;
    tree.trunkMass = 320.0;
    tree.applyCut(0.62, {1.0, 0.0, 0.0});
    require(tree.state == vf::TreeState::Hinging, "sufficient cut should release hinge motion");

    for (int i = 0; i < 360; ++i) tree.step(1.0 / 120.0, 9.81, {8.0, 0.0, 0.0}, 1.225);
    require(tree.hingeAngleRadians > 0.1, "cut tree should rotate under gravity and wind");
    require(tree.tipPosition().x > 0.1, "tree tip should move toward preferred fall direction");
}

} // namespace

int main() {
    testCubeSphereProjection();
    testPlanetSurfaceDeterminism();
    testRadialCamera();
    testFixedStepAndMomentum();
    testRigidBodyCollisionMomentumConservation();
    testRadialGravityAndGroundFriction();
    testAtmospherePressureDensityAndWind();
    testBuoyancy();
    testShallowWaterConservation();
    testTreeFallsAfterCut();
    std::cout << "Planet physics tests passed\n";
    return 0;
}
