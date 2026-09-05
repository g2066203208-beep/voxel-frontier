#include "vf/gameplay/PhysicsInteraction.hpp"
#include "vf/physics/PhysicsWorld.hpp"
#include "vf/world/CelestialSystem.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "GAMEPLAY INTERACTION TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

vf::PhysicsWorld makeLocalPlanetWorld() {
    vf::PlanetDefinition planet{};
    planet.radius = 100.0;
    planet.maxElevation = 0.0;
    planet.atmosphereHeight = 0.0;

    static vf::CelestialSystem celestial;
    celestial = vf::CelestialSystem{};
    vf::CelestialBody body{};
    body.name = "LocalPlanet";
    body.radiusMeters = 100.0;
    body.massKg = 9.81 * 100.0 * 100.0 / vf::CelestialSystem::kGravitationalConstant;
    body.gameplaySurfaceGravityMps2 = 9.81;
    body.gravityInfluenceRadiusMeters = 400.0;
    body.position = {};
    body.orientation = {1.0, 0.0, 0.0, 0.0};
    body.atmosphere.enabled = false;
    const auto bodyId = celestial.addBody(body);

    vf::PhysicsEnvironment environment{};
    environment.planet = planet;
    environment.ocean.enabled = false;
    environment.atmosphere.seaLevelPressurePa = 0.0;
    environment.celestialSystem = &celestial;
    environment.primaryCelestialBodyId = bodyId;
    return vf::PhysicsWorld{environment};
}

vf::RigidBodyDesc looseSphere(const glm::dvec3& position, double radius = 0.5) {
    vf::RigidBodyDesc desc{};
    desc.position = position;
    desc.mass = 2.0;
    desc.collisionShape = vf::CollisionShape::sphere(radius);
    const double inertia = 0.4 * desc.mass * radius * radius;
    desc.inertiaDiagonal = {inertia, inertia, inertia};
    desc.material.friction = 0.82;
    desc.material.restitution = 0.0;
    desc.material.rollingResistance = 0.08;
    desc.linearDamping = 0.06;
    desc.angularDamping = 0.09;
    desc.aerodynamics.referenceArea = 0.0;
    return desc;
}

void testGroundedLooseBodyActuallySettles() {
    auto world = makeLocalPlanetWorld();
    const auto bodyId = world.createRigidBody(looseSphere({100.505, 0.0, 0.0}));

    double minRadius = 1.0e30;
    double maxRadius = 0.0;
    for (int frame = 0; frame < 360; ++frame) {
        world.advance(1.0 / 60.0);
        if (frame < 180) continue;
        const auto* body = world.body(bodyId);
        require(body != nullptr, "resting sphere must remain valid");
        const double radius = glm::length(body->position);
        minRadius = std::min(minRadius, radius);
        maxRadius = std::max(maxRadius, radius);
    }

    const auto* body = world.body(bodyId);
    require(body != nullptr, "resting sphere must exist after settle period");
    require(maxRadius - minRadius < 0.003,
        "a loose sphere on local planetary ground must not visibly bounce or jitter");
    require(std::abs(glm::length(body->position) - 100.5) < 0.01,
        "settled sphere center must remain exactly one radius above the surface");
    require(body->sleeping || glm::length(body->linearVelocity) < 0.03,
        "resting surface body must sleep or have negligible residual speed");
}

void testRightClickPickupDropAndLeftClickThrow() {
    auto world = makeLocalPlanetWorld();
    const auto bodyId = world.createRigidBody(looseSphere({100.5, 0.0, 0.0}));
    vf::PhysicsInteraction interaction{world};

    const glm::dvec3 eye{106.0, 0.0, 0.0};
    const glm::dvec3 towardPlanet{-1.0, 0.0, 0.0};

    vf::PhysicsInteractionInput pickup{};
    pickup.rightPressed = true;
    interaction.update(eye, towardPlanet, pickup, 1.0 / 60.0);
    require(interaction.holding() && interaction.heldBodyId() == bodyId,
        "right click must pick the nearest loose dynamic body");
    require(world.body(bodyId)->motionType == vf::MotionType::Kinematic,
        "held object must become kinematic instead of being teleported as a dynamic body");

    vf::PhysicsInteractionInput idle{};
    interaction.update({107.0, 0.0, 0.0}, towardPlanet, idle, 1.0 / 60.0);
    require(world.body(bodyId)->position.x > 101.0,
        "held object must follow the hand target in front of the camera");

    vf::PhysicsInteractionInput drop{};
    drop.rightPressed = true;
    interaction.update({107.0, 0.0, 0.0}, towardPlanet, drop, 1.0 / 60.0);
    require(!interaction.holding(), "second right click must drop held object");
    require(world.body(bodyId)->motionType == vf::MotionType::Dynamic,
        "dropped object must return to dynamic physics");
    require(glm::length(world.body(bodyId)->linearVelocity) < 1.0e-9,
        "normal drop must not inherit artificial hand-follow velocity");

    pickup.rightPressed = true;
    interaction.update({107.0, 0.0, 0.0}, towardPlanet, pickup, 1.0 / 60.0);
    require(interaction.holding(), "dropped object must be pickable again");

    vf::PhysicsInteractionInput throwInput{};
    throwInput.leftPressed = true;
    const glm::dvec3 outward{1.0, 0.0, 0.0};
    interaction.update({107.0, 0.0, 0.0}, outward, throwInput, 1.0 / 60.0);
    require(!interaction.holding(), "left click must release the held object as a throw");
    require(world.body(bodyId)->motionType == vf::MotionType::Dynamic,
        "thrown object must be dynamic");
    require(world.body(bodyId)->linearVelocity.x > 20.0,
        "left click throw must give the object a clear forward launch velocity");
}

void testConstrainedMachinePartCannotBeGrabbed() {
    auto world = makeLocalPlanetWorld();

    vf::RigidBodyDesc anchorDesc{};
    anchorDesc.motionType = vf::MotionType::Static;
    anchorDesc.mass = 0.0;
    anchorDesc.position = {103.0, 0.0, 0.0};
    anchorDesc.collisionShape = vf::CollisionShape::sphere(0.1);
    anchorDesc.aerodynamics.referenceArea = 0.0;
    const auto anchorId = world.createRigidBody(anchorDesc);

    const auto constrainedId = world.createRigidBody(looseSphere({101.5, 0.0, 0.0}));
    vf::DistanceConstraintDesc tether{};
    tether.bodyA = anchorId;
    tether.bodyB = constrainedId;
    tether.restLength = 1.5;
    (void)world.createDistanceConstraint(tether);

    vf::PhysicsInteraction interaction{world};
    vf::PhysicsInteractionInput pickup{};
    pickup.rightPressed = true;
    interaction.update({106.0, 0.0, 0.0}, {-1.0, 0.0, 0.0}, pickup, 1.0 / 60.0);
    require(!interaction.holding(),
        "right click must not rip a body out of an active mechanical constraint");
}

} // namespace

int main() {
    testGroundedLooseBodyActuallySettles();
    testRightClickPickupDropAndLeftClickThrow();
    testConstrainedMachinePartCannotBeGrabbed();
    std::cout << "vf_gameplay_interaction_tests: PASS\n";
    return 0;
}
