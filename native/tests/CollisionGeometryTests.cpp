#include "vf/physics/CollisionGeometry.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/gtc/constants.hpp>
#include <glm/gtx/quaternion.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "COLLISION TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void testAabbs() {
    const auto sphere = vf::CollisionShape::sphere(2.0);
    const vf::ShapePose spherePose{{3.0, -1.0, 5.0}, {1.0, 0.0, 0.0, 0.0}};
    const auto sphereBounds = vf::computeWorldAabb(sphere, spherePose);
    require(glm::length(sphereBounds.minimum - glm::dvec3{1.0, -3.0, 3.0}) < 1.0e-12, "sphere AABB minimum incorrect");
    require(glm::length(sphereBounds.maximum - glm::dvec3{5.0, 1.0, 7.0}) < 1.0e-12, "sphere AABB maximum incorrect");

    const auto box = vf::CollisionShape::box({2.0, 1.0, 0.5});
    vf::ShapePose boxPose{};
    boxPose.orientation = glm::angleAxis(glm::half_pi<double>(), glm::dvec3{0.0, 1.0, 0.0});
    const auto boxBounds = vf::computeWorldAabb(box, boxPose);
    const glm::dvec3 half = 0.5 * (boxBounds.maximum - boxBounds.minimum);
    require(std::abs(half.x - 0.5) < 1.0e-9, "rotated box AABB X extent incorrect");
    require(std::abs(half.y - 1.0) < 1.0e-9, "rotated box AABB Y extent incorrect");
    require(std::abs(half.z - 2.0) < 1.0e-9, "rotated box AABB Z extent incorrect");
}

void testSphereSphere() {
    const auto sphere = vf::CollisionShape::sphere(1.0);
    vf::ContactManifold manifold{};
    require(vf::collideShapes(sphere, {{0.0, 0.0, 0.0}, {}}, sphere, {{1.5, 0.0, 0.0}, {}}, manifold), "overlapping spheres must collide");
    require(manifold.pointCount == 1, "sphere contact should produce one point");
    require(std::abs(manifold.points[0].penetration - 0.5) < 1.0e-9, "sphere penetration incorrect");
    require(glm::dot(manifold.normal, glm::dvec3{1.0, 0.0, 0.0}) > 0.999999, "sphere normal must point A to B");

    require(!vf::collideShapes(sphere, {{0.0, 0.0, 0.0}, {}}, sphere, {{2.1, 0.0, 0.0}, {}}, manifold), "separated spheres must not collide");
}

void testSphereBox() {
    const auto sphere = vf::CollisionShape::sphere(0.75);
    const auto box = vf::CollisionShape::box({1.0, 1.0, 1.0});
    vf::ContactManifold manifold{};
    require(vf::collideShapes(sphere, {{1.5, 0.0, 0.0}, {}}, box, {{0.0, 0.0, 0.0}, {}}, manifold), "sphere/box overlap must collide");
    require(manifold.normal.x < -0.99, "sphere-to-box normal direction incorrect");
    require(std::abs(manifold.points[0].penetration - 0.25) < 1.0e-9, "sphere/box penetration incorrect");

    require(!vf::collideShapes(sphere, {{2.0, 0.0, 0.0}, {}}, box, {{0.0, 0.0, 0.0}, {}}, manifold), "separated sphere/box must not collide");
}

void testCapsules() {
    const auto capsule = vf::CollisionShape::capsule(0.5, 1.0);
    const auto sphere = vf::CollisionShape::sphere(0.6);
    vf::ContactManifold manifold{};
    require(vf::collideShapes(sphere, {{0.9, 0.0, 0.0}, {}}, capsule, {{0.0, 0.0, 0.0}, {}}, manifold), "sphere/capsule overlap must collide");
    require(manifold.normal.x < -0.99, "sphere/capsule normal direction incorrect");

    require(vf::collideShapes(capsule, {{0.0, 0.0, 0.0}, {}}, capsule, {{0.8, 0.0, 0.0}, {}}, manifold), "capsule/capsule overlap must collide");
    require(manifold.points[0].penetration > 0.19 && manifold.points[0].penetration < 0.21, "capsule/capsule penetration incorrect");
}

void testOrientedBoxesSat() {
    const auto box = vf::CollisionShape::box({1.0, 0.5, 0.75});
    vf::ShapePose a{};
    vf::ShapePose b{};
    a.orientation = glm::angleAxis(glm::radians(22.0), glm::normalize(glm::dvec3{0.2, 1.0, 0.1}));
    b.position = {1.4, 0.0, 0.1};
    b.orientation = glm::angleAxis(glm::radians(-31.0), glm::normalize(glm::dvec3{0.1, 0.7, 0.4}));

    vf::ContactManifold manifold{};
    require(vf::collideShapes(box, a, box, b, manifold), "rotated OBBs should overlap under SAT");
    require(manifold.pointCount == 1, "current OBB SAT must emit representative contact");
    require(manifold.points[0].penetration > 0.0, "OBB penetration must be positive");
    require(glm::dot(manifold.normal, b.position - a.position) > 0.0, "OBB normal must point A to B");

    b.position = {4.0, 0.0, 0.0};
    require(!vf::collideShapes(box, a, box, b, manifold), "separated OBBs must fail SAT");
}

void testSupportMapping() {
    const auto box = vf::CollisionShape::box({1.0, 2.0, 3.0});
    vf::ShapePose pose{};
    const auto point = vf::supportPoint(box, pose, {1.0, -1.0, 1.0});
    require(glm::length(point - glm::dvec3{1.0, -2.0, 3.0}) < 1.0e-12, "box support mapping incorrect");

    const auto capsule = vf::CollisionShape::capsule(0.5, 1.5);
    const auto capsulePoint = vf::supportPoint(capsule, pose, {0.0, 1.0, 0.0});
    require(std::abs(capsulePoint.y - 2.0) < 1.0e-12, "capsule support mapping incorrect");
}

} // namespace

int main() {
    testAabbs();
    testSphereSphere();
    testSphereBox();
    testCapsules();
    testOrientedBoxesSat();
    testSupportMapping();
    std::cout << "Collision geometry tests passed\n";
    return 0;
}
