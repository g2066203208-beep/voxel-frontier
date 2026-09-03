#pragma once

#include <cstdint>
#include <limits>

#include <glm/glm.hpp>

namespace vf {

struct DistanceConstraintDesc {
    std::uint32_t bodyA{};
    std::uint32_t bodyB{};
    glm::dvec3 localAnchorA{};
    glm::dvec3 localAnchorB{};
    double restLength{-1.0};
    double baumgarte{0.20};
    double maxForceN{std::numeric_limits<double>::infinity()};
    double breakForceN{std::numeric_limits<double>::infinity()};
};

struct DistanceConstraint {
    std::uint32_t id{};
    std::uint32_t bodyA{};
    std::uint32_t bodyB{};
    glm::dvec3 localAnchorA{};
    glm::dvec3 localAnchorB{};
    double restLength{};
    double baumgarte{0.20};
    double maxForceN{std::numeric_limits<double>::infinity()};
    double breakForceN{std::numeric_limits<double>::infinity()};
    double accumulatedImpulse{};
    double lastForceN{};
    bool broken{};
};

struct SpringDamperConstraintDesc {
    std::uint32_t bodyA{};
    std::uint32_t bodyB{};
    glm::dvec3 localAnchorA{};
    glm::dvec3 localAnchorB{};
    double restLength{-1.0};
    double stiffnessNPerM{1000.0};
    double dampingNsPerM{50.0};
    double maxForceN{std::numeric_limits<double>::infinity()};
    double breakForceN{std::numeric_limits<double>::infinity()};
};

struct SpringDamperConstraint {
    std::uint32_t id{};
    std::uint32_t bodyA{};
    std::uint32_t bodyB{};
    glm::dvec3 localAnchorA{};
    glm::dvec3 localAnchorB{};
    double restLength{};
    double stiffnessNPerM{1000.0};
    double dampingNsPerM{50.0};
    double maxForceN{std::numeric_limits<double>::infinity()};
    double breakForceN{std::numeric_limits<double>::infinity()};
    double lastForceN{};
    bool broken{};
};

struct HingeConstraintDesc {
    std::uint32_t bodyA{};
    std::uint32_t bodyB{};
    glm::dvec3 localAnchorA{};
    glm::dvec3 localAnchorB{};
    glm::dvec3 localAxisA{0.0, 1.0, 0.0};
    glm::dvec3 localAxisB{0.0, 1.0, 0.0};
    double anchorBaumgarte{0.25};
    double axisBaumgarte{0.20};
    bool motorEnabled{};
    double targetAngularSpeedRadPerS{};
    double maxMotorTorqueNm{};
    double viscousFrictionNmPerRadS{};
    double coulombFrictionTorqueNm{};
    double breakForceN{std::numeric_limits<double>::infinity()};
    double breakTorqueNm{std::numeric_limits<double>::infinity()};
};

struct HingeConstraint {
    std::uint32_t id{};
    std::uint32_t bodyA{};
    std::uint32_t bodyB{};
    glm::dvec3 localAnchorA{};
    glm::dvec3 localAnchorB{};
    glm::dvec3 localAxisA{0.0, 1.0, 0.0};
    glm::dvec3 localAxisB{0.0, 1.0, 0.0};
    double anchorBaumgarte{0.25};
    double axisBaumgarte{0.20};
    bool motorEnabled{};
    double targetAngularSpeedRadPerS{};
    double maxMotorTorqueNm{};
    double viscousFrictionNmPerRadS{};
    double coulombFrictionTorqueNm{};
    double breakForceN{std::numeric_limits<double>::infinity()};
    double breakTorqueNm{std::numeric_limits<double>::infinity()};
    double accumulatedMotorImpulse{};
    double lastAnchorForceN{};
    double lastAxisTorqueNm{};
    bool broken{};
};

struct GearConstraintDesc {
    std::uint32_t bodyA{};
    std::uint32_t bodyB{};
    glm::dvec3 localAxisA{0.0, 0.0, 1.0};
    glm::dvec3 localAxisB{0.0, 0.0, 1.0};
    double ratio{1.0};
    double maxTorqueNm{std::numeric_limits<double>::infinity()};
    double breakTorqueNm{std::numeric_limits<double>::infinity()};
};

struct GearConstraint {
    std::uint32_t id{};
    std::uint32_t bodyA{};
    std::uint32_t bodyB{};
    glm::dvec3 localAxisA{0.0, 0.0, 1.0};
    glm::dvec3 localAxisB{0.0, 0.0, 1.0};
    double ratio{1.0};
    double maxTorqueNm{std::numeric_limits<double>::infinity()};
    double breakTorqueNm{std::numeric_limits<double>::infinity()};
    double lastTorqueNm{};
    bool broken{};
};

} // namespace vf
