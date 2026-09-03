#include "vf/physics/GjkEpa.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/gtc/quaternion.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "GJK/EPA TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void testAxisAlignedBoxCapsule() {
    const auto box = vf::CollisionShape::box({1.0, 1.0, 1.0});
    const auto capsule = vf::CollisionShape::capsule(0.4, 0.8);
    const vf::ShapePose boxPose{};
    const vf::ShapePose capsulePose{{1.2, 0.0, 0.0}, {1.0, 0.0, 0.0, 0.0}};

    vf::ContactManifold manifold{};
    vf::GjkEpaDiagnostics diagnostics{};
    require(vf::collideConvexGjkEpa(box, boxPose, capsule, capsulePose, manifold, &diagnostics),
        "overlapping box/capsule must collide");
    require(diagnostics.gjkIntersected, "GJK must report intersection");
    require(diagnostics.epaConverged, "EPA must converge for axis-aligned box/capsule");
    require(diagnostics.gjkIterations > 0U && diagnostics.gjkIterations <= 32U, "GJK iteration count invalid");
    require(diagnostics.epaIterations > 0U && diagnostics.epaIterations <= 64U, "EPA iteration count invalid");
    require(manifold.pointCount == 1U, "GJK/EPA foundation currently emits one witness contact");
    require(manifold.normal.x > 0.99, "box-to-capsule normal must point A to B");
    require(manifold.points[0].penetration > 0.195 && manifold.points[0].penetration < 0.205,
        "axis-aligned box/capsule penetration should be approximately 0.2 m");
    require(std::isfinite(manifold.points[0].position.x), "contact position must be finite");
}

void testReversePairConvention() {
    const auto box = vf::CollisionShape::box({1.0, 1.0, 1.0});
    const auto capsule = vf::CollisionShape::capsule(0.4, 0.8);
    const vf::ShapePose boxPose{};
    const vf::ShapePose capsulePose{{1.2, 0.0, 0.0}, {1.0, 0.0, 0.0, 0.0}};

    vf::ContactManifold manifold{};
    vf::GjkEpaDiagnostics diagnostics{};
    require(vf::collideConvexGjkEpa(capsule, capsulePose, box, boxPose, manifold, &diagnostics),
        "reverse capsule/box pair must collide");
    require(diagnostics.epaConverged, "EPA must converge for reverse pair");
    require(manifold.normal.x < -0.99, "reverse normal must still point A to B");
    require(manifold.points[0].penetration > 0.195 && manifold.points[0].penetration < 0.205,
        "reverse pair penetration must remain invariant");
}

void testSeparatedBoxCapsule() {
    const auto box = vf::CollisionShape::box({1.0, 1.0, 1.0});
    const auto capsule = vf::CollisionShape::capsule(0.4, 0.8);

    vf::ContactManifold manifold{};
    vf::GjkEpaDiagnostics diagnostics{};
    require(!vf::collideConvexGjkEpa(
        box,
        {},
        capsule,
        {{1.5, 0.0, 0.0}, {1.0, 0.0, 0.0, 0.0}},
        manifold,
        &diagnostics),
        "separated box/capsule must not collide");
    require(!diagnostics.gjkIntersected, "separated pair must be rejected by GJK");
    require(manifold.empty(), "separated pair must not emit contacts");
}

void testRotatedBoxCapsule() {
    const auto box = vf::CollisionShape::box({1.1, 0.55, 0.8});
    const auto capsule = vf::CollisionShape::capsule(0.35, 0.9);

    vf::ShapePose boxPose{};
    boxPose.orientation = glm::angleAxis(
        glm::radians(28.0),
        glm::normalize(glm::dvec3{0.2, 1.0, 0.15}));

    vf::ShapePose capsulePose{};
    capsulePose.position = {0.95, 0.10, 0.20};
    capsulePose.orientation = glm::angleAxis(
        glm::radians(37.0),
        glm::normalize(glm::dvec3{0.0, 0.0, 1.0}));

    vf::ContactManifold manifold{};
    vf::GjkEpaDiagnostics diagnostics{};
    require(vf::collideConvexGjkEpa(box, boxPose, capsule, capsulePose, manifold, &diagnostics),
        "rotated support-mapped pair must collide");
    require(diagnostics.gjkIntersected, "rotated pair must reach EPA");
    require(diagnostics.epaConverged, "EPA must converge for rotated box/capsule");
    require(manifold.points[0].penetration > 0.0, "rotated pair penetration must be positive");
    require(std::abs(glm::length(manifold.normal) - 1.0) < 1.0e-6, "EPA normal must be unit length");
    require(glm::dot(manifold.normal, capsulePose.position - boxPose.position) > 0.0,
        "rotated pair normal must follow A-to-B convention");
}

void testDeepOverlapDoesNotDegenerate() {
    const auto box = vf::CollisionShape::box({1.0, 1.0, 1.0});
    const auto capsule = vf::CollisionShape::capsule(0.4, 0.8);

    vf::ContactManifold manifold{};
    vf::GjkEpaDiagnostics diagnostics{};
    require(vf::collideConvexGjkEpa(box, {}, capsule, {}, manifold, &diagnostics),
        "coincident deep overlap must remain solvable");
    require(diagnostics.gjkIntersected, "deep overlap must be detected by GJK");
    require(diagnostics.epaConverged, "deep overlap EPA must converge");
    require(manifold.points[0].penetration > 1.0, "deep overlap must produce substantial penetration depth");
    require(std::isfinite(manifold.points[0].penetration), "deep overlap penetration must be finite");
}

} // namespace

int main() {
    testAxisAlignedBoxCapsule();
    testReversePairConvention();
    testSeparatedBoxCapsule();
    testRotatedBoxCapsule();
    testDeepOverlapDoesNotDegenerate();
    std::cout << "vf_gjk_epa_tests: PASS\n";
    return 0;
}
