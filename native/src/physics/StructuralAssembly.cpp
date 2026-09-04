#include "vf/physics/StructuralAssembly.hpp"

#include "vf/physics/PhysicsWorld.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kPi = 3.14159265358979323846;
constexpr double kEpsilon = 1.0e-9;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {1.0, 0.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= kEpsilon) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] glm::dvec3 anchorWorld(const RigidBody& body, const glm::dvec3& local) noexcept {
    return body.position + body.orientation * local;
}

[[nodiscard]] glm::dvec3 axisWorld(const RigidBody& body, const glm::dvec3& local) noexcept {
    return safeNormalize(body.orientation * local, {0.0, 1.0, 0.0});
}

} // namespace

std::uint32_t StructuralAssembly::addBond(const StructuralBondDesc& input, const PhysicsWorld& world) {
    const RigidBody* a = world.body(input.bodyA);
    const RigidBody* b = world.body(input.bodyB);
    if (a == nullptr || b == nullptr || input.bodyA == input.bodyB) {
        throw std::invalid_argument("StructuralAssembly bond requires two valid distinct bodies");
    }

    StructuralBond bondValue{};
    bondValue.id = nextBondId_++;
    bondValue.desc = input;
    bondValue.desc.geometry.areaM2 = std::max(1.0e-8, input.geometry.areaM2);
    bondValue.desc.geometry.sectionModulusM3 = std::max(1.0e-10, input.geometry.sectionModulusM3);
    bondValue.desc.geometry.fractureAreaM2 = std::max(1.0e-8, input.geometry.fractureAreaM2);
    bondValue.desc.axialDampingNsPerM = std::max(0.0, input.axialDampingNsPerM);
    bondValue.desc.angularDampingNmsPerRad = std::max(0.0, input.angularDampingNmsPerRad);

    const glm::dvec3 pointA = anchorWorld(*a, input.localAnchorA);
    const glm::dvec3 pointB = anchorWorld(*b, input.localAnchorB);
    bondValue.desc.restLengthMeters = input.restLengthMeters > 0.0
        ? input.restLengthMeters
        : std::max(1.0e-5, glm::length(pointB - pointA));
    bonds_.push_back(bondValue);
    return bondValue.id;
}

StructuralBond* StructuralAssembly::bond(std::uint32_t id) noexcept {
    for (auto& candidate : bonds_) if (candidate.id == id) return &candidate;
    return nullptr;
}

const StructuralBond* StructuralAssembly::bond(std::uint32_t id) const noexcept {
    for (const auto& candidate : bonds_) if (candidate.id == id) return &candidate;
    return nullptr;
}

void StructuralAssembly::step(PhysicsWorld& world, double deltaSeconds) {
    if (deltaSeconds <= 0.0) return;
    deltaSeconds = std::clamp(deltaSeconds, 0.0, 0.05);

    for (auto& bondValue : bonds_) {
        bondValue.lastAxialForceN = 0.0;
        bondValue.lastBendingMomentNm = 0.0;
        bondValue.lastUtilization = bondValue.damageState.broken ? 1.0 : 0.0;
        if (bondValue.damageState.broken) continue;

        RigidBody* a = world.body(bondValue.desc.bodyA);
        RigidBody* b = world.body(bondValue.desc.bodyB);
        if (a == nullptr || b == nullptr) {
            bondValue.damageState.damage = 1.0;
            bondValue.damageState.broken = true;
            continue;
        }

        const glm::dvec3 pointA = anchorWorld(*a, bondValue.desc.localAnchorA);
        const glm::dvec3 pointB = anchorWorld(*b, bondValue.desc.localAnchorB);
        const glm::dvec3 delta = pointB - pointA;
        const double length = std::max(kEpsilon, glm::length(delta));
        const glm::dvec3 direction = delta / length;
        const double restLength = std::max(1.0e-5, bondValue.desc.restLengthMeters);
        const double strain = (length - restLength) / restLength;

        const double strengthScale = temperatureStrengthScale(bondValue.desc.material, bondValue.materialState);
        const double axialStiffness = std::max(0.0, bondValue.desc.material.youngModulusPa)
            * bondValue.desc.geometry.areaM2 / restLength * std::max(0.05, strengthScale);
        const double relativeAxialSpeed = glm::dot(
            b->velocityAtPoint(pointB) - a->velocityAtPoint(pointA), direction);
        const double axialForce = -axialStiffness * (length - restLength)
            - bondValue.desc.axialDampingNsPerM * relativeAxialSpeed;
        bondValue.lastAxialForceN = std::abs(axialForce);

        const glm::dvec3 axisA = axisWorld(*a, bondValue.desc.localBendAxisA);
        const glm::dvec3 axisB = axisWorld(*b, bondValue.desc.localBendAxisB);
        const double cosAngle = std::clamp(glm::dot(axisA, axisB), -1.0, 1.0);
        const double bendAngle = std::acos(cosAngle);
        glm::dvec3 bendAxis = glm::cross(axisA, axisB);
        const double bendAxisLength = glm::length(bendAxis);
        if (bendAxisLength > kEpsilon) bendAxis /= bendAxisLength;
        else bendAxis = safeNormalize(glm::cross(axisA, direction), {0.0, 0.0, 1.0});

        const double equivalentRadius = std::sqrt(bondValue.desc.geometry.areaM2 / kPi);
        const double secondMoment = bondValue.desc.geometry.sectionModulusM3 * std::max(equivalentRadius, 1.0e-4);
        const double bendingStiffness = std::max(0.0, bondValue.desc.material.youngModulusPa)
            * secondMoment / restLength * std::max(0.05, strengthScale);
        const double relativeAngularSpeed = glm::dot(b->angularVelocity - a->angularVelocity, bendAxis);
        const double bendingMoment = -bendingStiffness * bendAngle
            - bondValue.desc.angularDampingNmsPerRad * relativeAngularSpeed;
        bondValue.lastBendingMomentNm = std::abs(bendingMoment);

        StructuralLoad load{};
        load.axialForceN = bondValue.lastAxialForceN;
        load.bendingMomentNm = bondValue.lastBendingMomentNm;
        const StructuralResponse response = evaluateStructuralBond(
            bondValue.desc.material,
            bondValue.materialState,
            bondValue.desc.geometry,
            load);
        bondValue.lastUtilization = std::max(response.strengthUtilization, response.impactUtilization);
        accumulateStructuralBondDamage(response, deltaSeconds, bondValue.damageState);
        if (bondValue.damageState.broken) continue;

        const glm::dvec3 force = direction * axialForce;
        a->addForceAtPoint(-force, pointA);
        b->addForceAtPoint(force, pointB);
        const glm::dvec3 torque = bendAxis * bendingMoment;
        a->addTorque(-torque);
        b->addTorque(torque);
    }
}

} // namespace vf
