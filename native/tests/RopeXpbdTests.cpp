#include "vf/physics/RopeXpbd.hpp"
#include "vf/physics/PhysicsWorld.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>
#include <vector>

#include <glm/geometric.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "ROPE XPBD TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

[[nodiscard]] double radialSegmentDistanceToYAxis(const glm::dvec3& a, const glm::dvec3& b) {
    const glm::dvec2 r0{a.x, a.z};
    const glm::dvec2 r1{b.x, b.z};
    const glm::dvec2 d = r1 - r0;
    const double denom = glm::dot(d, d);
    const double t = denom > 1.0e-12 ? std::clamp(-glm::dot(r0, d) / denom, 0.0, 1.0) : 0.0;
    return glm::length(r0 + d * t);
}

void testHangingRopePreservesLength() {
    std::vector<glm::dvec3> points;
    for (int i = 0; i <= 20; ++i) points.push_back({0.25 * i, 2.0, 0.0});

    vf::RopeMaterial material{};
    material.stretchComplianceMPerN = 1.0e-8;
    material.bendComplianceMPerN = 2.0e-3;
    material.breakingStrain = 1.0;
    material.selfCollision = false;

    vf::RopeXpbd rope;
    rope.initialize(points, 2.0, material);
    rope.pinParticle(0, points.front());
    rope.pinParticle(points.size() - 1U, points.back());
    const double rest = rope.restLengthMeters();

    for (int i = 0; i < 600; ++i) rope.step(1.0 / 120.0, {0.0, -9.81, 0.0});
    const double relativeError = std::abs(rope.currentLengthMeters() - rest) / rest;
    require(relativeError < 0.02, "XPBD rope must preserve physical length while sagging under gravity");
    require(rope.particles()[10].position.y < 1.95, "a flexible rope must sag rather than remain a rigid straight line");
}

void testRopeWrapsAroundTreeCapsuleWithoutSegmentTunneling() {
    constexpr double pi = 3.14159265358979323846;
    std::vector<glm::dvec3> points;
    constexpr int segments = 28;
    for (int i = 0; i <= segments; ++i) {
        const double angle = 2.0 * pi * static_cast<double>(i) / static_cast<double>(segments);
        points.push_back({0.62 * std::cos(angle), 0.15 * std::sin(angle * 0.5), 0.62 * std::sin(angle)});
    }

    vf::RopeMaterial material{};
    material.radiusMeters = 0.05;
    material.stretchComplianceMPerN = 5.0e-8;
    material.bendComplianceMPerN = 8.0e-4;
    material.breakingStrain = 1.0;
    material.selfCollision = false;

    vf::RopeXpbd rope;
    rope.initialize(points, 1.5, material);
    rope.pinParticle(0, points.front());
    rope.pinParticle(points.size() - 1U, points.back());
    rope.addCapsuleCollider({{0.0, -2.0, 0.0}, {0.0, 2.0, 0.0}, 0.50, 0.85});

    for (int i = 0; i < 360; ++i) rope.step(1.0 / 120.0, {0.0, -2.0, 0.0});

    const auto particles = rope.particles();
    for (std::size_t i = 0; i + 1U < particles.size(); ++i) {
        const double radial = radialSegmentDistanceToYAxis(particles[i].position, particles[i + 1U].position);
        require(radial >= 0.545, "rope segment capsule must not cut through the tree trunk capsule");
    }
}

void testRopeCanBreakWhenOverstretched() {
    std::vector<glm::dvec3> points{{0.0, 0.0, 0.0}, {1.0, 0.0, 0.0}, {2.0, 0.0, 0.0}, {3.0, 0.0, 0.0}};
    vf::RopeMaterial material{};
    material.breakingStrain = 0.20;
    material.selfCollision = false;

    vf::RopeXpbd rope;
    rope.initialize(points, 1.0, material);
    rope.pinParticle(0, points.front());
    rope.pinParticle(points.size() - 1U, {6.0, 0.0, 0.0});
    rope.step(1.0 / 120.0, {});
    require(rope.brokenLinkCount() > 0U, "rope must fracture when local tensile strain exceeds breaking strain");
}

void testRigidAttachmentReceivesRopeReaction() {
    vf::PhysicsEnvironment environment{};
    environment.planet.radius = 1.0;
    environment.planet.maxElevation = 0.0;
    environment.surfaceGravity = 0.0;
    environment.atmosphere.seaLevelPressurePa = 0.0;
    environment.ocean.enabled = false;
    vf::PhysicsWorld world{environment};

    vf::RigidBodyDesc bodyDesc{};
    bodyDesc.position = {5.0, 0.0, 0.0};
    bodyDesc.mass = 2.0;
    bodyDesc.collisionShape = vf::CollisionShape::sphere(0.2);
    bodyDesc.linearDamping = 0.0;
    bodyDesc.angularDamping = 0.0;
    bodyDesc.aerodynamics.referenceArea = 0.0;
    const auto bodyId = world.createRigidBody(bodyDesc);

    std::vector<glm::dvec3> points{{0.0, 0.0, 0.0}, {1.0, 0.0, 0.0}, {2.0, 0.0, 0.0}, {3.0, 0.0, 0.0}};
    vf::RopeMaterial material{};
    material.stretchComplianceMPerN = 1.0e-7;
    material.breakingStrain = 10.0;
    material.maxTensionN = 10000.0;
    material.selfCollision = false;

    vf::RopeXpbd rope;
    rope.initialize(points, 1.0, material);
    rope.pinParticle(0, points.front());
    rope.attachParticleToRigidBody(points.size() - 1U, bodyId);
    rope.step(1.0 / 120.0, {}, {}, 0.0, &world);

    const auto* body = world.body(bodyId);
    require(body != nullptr, "attached rigid body must still exist");
    require(body->linearVelocity.x < 0.0, "stretched rope must pull the attached rigid body back toward the anchor");
    require(rope.lastMaximumTensionN() > 0.0, "attached rope must expose non-zero physical tension");
}

} // namespace

int main() {
    testHangingRopePreservesLength();
    testRopeWrapsAroundTreeCapsuleWithoutSegmentTunneling();
    testRopeCanBreakWhenOverstretched();
    testRigidAttachmentReceivesRopeReaction();
    std::cout << "vf_rope_xpbd_tests: PASS\n";
    return 0;
}
