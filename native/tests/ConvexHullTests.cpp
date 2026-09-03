#include "vf/physics/CollisionGeometry.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <vector>

#include <glm/geometric.hpp>
#include <glm/gtc/quaternion.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "CONVEX HULL TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

template <typename Fn>
void requireInvalidArgument(Fn&& function, std::string_view message) {
    try {
        function();
    } catch (const std::invalid_argument&) {
        return;
    } catch (...) {
        fail("degenerate hull threw the wrong exception type");
    }
    fail(message);
}

std::vector<glm::dvec3> offsetCubePoints(double centerX = 5.0) {
    std::vector<glm::dvec3> points;
    points.reserve(9U);
    for (double x : {-0.5, 0.5}) {
        for (double y : {-0.5, 0.5}) {
            for (double z : {-0.5, 0.5}) {
                points.push_back({centerX + x, y, z});
            }
        }
    }
    // Interior points are legal input and must not change support mapping.
    points.push_back({centerX, 0.0, 0.0});
    return points;
}

void testConstructionAndSharedData() {
    const vf::CollisionShape hull = vf::CollisionShape::convexHull(offsetCubePoints());
    require(hull.type == vf::CollisionShapeType::ConvexHull, "factory must create ConvexHull type");
    require(hull.convexHullData != nullptr, "convex hull data must exist");
    require(hull.convexHullData->points.size() == 9U, "input point set including interior point must be retained");
    require(std::abs(hull.convexHullData->localMinimum.x - 4.5) < 1.0e-12, "local hull minimum incorrect");
    require(std::abs(hull.convexHullData->localMaximum.x - 5.5) < 1.0e-12, "local hull maximum incorrect");

    const vf::CollisionShape copy = hull;
    require(copy.convexHullData.get() == hull.convexHullData.get(), "CollisionShape copies must share immutable hull data");
}

void testDegenerateInputRejected() {
    requireInvalidArgument(
        [] { (void)vf::CollisionShape::convexHull({{0.0, 0.0, 0.0}, {1.0, 0.0, 0.0}, {0.0, 1.0, 0.0}}); },
        "fewer than four points must be rejected");

    requireInvalidArgument(
        [] {
            (void)vf::CollisionShape::convexHull({
                {0.0, 0.0, 0.0},
                {1.0, 0.0, 0.0},
                {2.0, 0.0, 0.0},
                {3.0, 0.0, 0.0},
            });
        },
        "collinear input must be rejected");

    requireInvalidArgument(
        [] {
            (void)vf::CollisionShape::convexHull({
                {-1.0, -1.0, 0.0},
                {1.0, -1.0, 0.0},
                {1.0, 1.0, 0.0},
                {-1.0, 1.0, 0.0},
                {0.0, 0.0, 0.0},
            });
        },
        "coplanar input must be rejected");

    std::vector<glm::dvec3> tooMany;
    tooMany.reserve(vf::CollisionShape::kMaxConvexHullPoints + 1U);
    for (std::size_t i = 0U; i <= vf::CollisionShape::kMaxConvexHullPoints; ++i) {
        const double t = static_cast<double>(i);
        tooMany.push_back({std::cos(t) * (1.0 + 0.001 * t), std::sin(t), 0.01 * t});
    }
    requireInvalidArgument(
        [&tooMany] { (void)vf::CollisionShape::convexHull(tooMany); },
        "point count above the bounded hull limit must be rejected");
}

void testSupportMappingAndExactAabb() {
    const vf::CollisionShape hull = vf::CollisionShape::convexHull(offsetCubePoints());
    const vf::ShapePose identity{};
    const glm::dvec3 positiveX = vf::supportPoint(hull, identity, {1.0, 0.0, 0.0});
    const glm::dvec3 negativeX = vf::supportPoint(hull, identity, {-1.0, 0.0, 0.0});
    require(std::abs(positiveX.x - 5.5) < 1.0e-12, "positive X hull support incorrect");
    require(std::abs(negativeX.x - 4.5) < 1.0e-12, "negative X hull support incorrect");

    vf::ShapePose pose{};
    pose.position = {2.0, 3.0, -4.0};
    pose.orientation = glm::angleAxis(glm::radians(90.0), glm::dvec3{0.0, 0.0, 1.0});
    const vf::Aabb bounds = vf::computeWorldAabb(hull, pose);
    require(std::abs(bounds.minimum.x - 1.5) < 1.0e-9, "rotated hull AABB minimum X incorrect");
    require(std::abs(bounds.maximum.x - 2.5) < 1.0e-9, "rotated hull AABB maximum X incorrect");
    require(std::abs(bounds.minimum.y - 7.5) < 1.0e-9, "rotated hull AABB minimum Y incorrect");
    require(std::abs(bounds.maximum.y - 8.5) < 1.0e-9, "rotated hull AABB maximum Y incorrect");
    require(std::abs(bounds.minimum.z + 4.5) < 1.0e-9, "rotated hull AABB minimum Z incorrect");
    require(std::abs(bounds.maximum.z + 3.5) < 1.0e-9, "rotated hull AABB maximum Z incorrect");
}

void testHullBoxCollisionAndOffsetNormal() {
    // Hull A is geometrically centered at world X=5 while its pose origin is X=0.
    // Box B is at X=4.6. The true A->B contact normal is therefore -X even though
    // poseB.position - poseA.position points +X. This catches pose-origin normal guesses.
    const vf::CollisionShape hull = vf::CollisionShape::convexHull(offsetCubePoints());
    const vf::CollisionShape box = vf::CollisionShape::box({0.5, 0.5, 0.5});

    vf::ContactManifold manifold{};
    require(vf::collideShapes(hull, {}, box, {{4.6, 0.0, 0.0}, {}}, manifold),
        "offset convex hull must collide with overlapping box");
    require(manifold.pointCount == 1U, "generic hull collision currently emits one witness contact");
    require(manifold.normal.x < -0.99, "EPA normal must follow actual A->B geometry, not pose origins");
    require(manifold.points[0].penetration > 0.59 && manifold.points[0].penetration < 0.61,
        "offset hull/box penetration should be approximately 0.6 m");

    require(!vf::collideShapes(hull, {}, box, {{3.9, 0.0, 0.0}, {}}, manifold),
        "separated hull/box pair must be rejected");
}

void testHullCapsuleAndHullHull() {
    const vf::CollisionShape hull = vf::CollisionShape::convexHull({
        {-0.9, -0.7, -0.6},
        {0.9, -0.7, -0.6},
        {0.8, 0.8, -0.5},
        {-0.7, 0.7, -0.4},
        {-0.6, -0.5, 0.8},
        {0.7, -0.4, 0.9},
        {0.5, 0.7, 0.7},
        {-0.5, 0.6, 0.75},
        {0.0, 0.0, 0.0},
    });
    const vf::CollisionShape capsule = vf::CollisionShape::capsule(0.35, 0.75);

    vf::ShapePose hullPose{};
    hullPose.orientation = glm::angleAxis(
        glm::radians(19.0),
        glm::normalize(glm::dvec3{0.3, 1.0, 0.2}));

    vf::ShapePose capsulePose{};
    capsulePose.position = {0.75, 0.05, 0.1};
    capsulePose.orientation = glm::angleAxis(glm::radians(31.0), glm::dvec3{0.0, 0.0, 1.0});

    vf::ContactManifold manifold{};
    require(vf::collideShapes(hull, hullPose, capsule, capsulePose, manifold),
        "rotated hull/capsule pair must use general GJK/EPA path");
    require(manifold.points[0].penetration > 0.0, "hull/capsule penetration must be positive");
    require(std::abs(glm::length(manifold.normal) - 1.0) < 1.0e-6, "hull/capsule normal must be normalized");

    vf::ShapePose secondHullPose{};
    secondHullPose.position = {1.0, 0.1, 0.0};
    secondHullPose.orientation = glm::angleAxis(glm::radians(-23.0), glm::dvec3{0.0, 1.0, 0.0});
    require(vf::collideShapes(hull, hullPose, hull, secondHullPose, manifold),
        "rotated hull/hull pair must collide");
    require(manifold.points[0].penetration > 0.0, "hull/hull penetration must be positive");

    secondHullPose.position = {4.0, 0.0, 0.0};
    require(!vf::collideShapes(hull, hullPose, hull, secondHullPose, manifold),
        "separated hull/hull pair must be rejected");
}

} // namespace

int main() {
    testConstructionAndSharedData();
    testDegenerateInputRejected();
    testSupportMappingAndExactAabb();
    testHullBoxCollisionAndOffsetNormal();
    testHullCapsuleAndHullHull();
    std::cout << "vf_convex_hull_tests: PASS\n";
    return 0;
}
