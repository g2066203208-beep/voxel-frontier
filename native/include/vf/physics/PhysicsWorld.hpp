#pragma once

#include <array>
#include <cstdint>
#include <span>
#include <unordered_map>
#include <vector>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

#include "vf/physics/CollisionGeometry.hpp"
#include "vf/physics/ConstraintTypes.hpp"
#include "vf/physics/OceanSpectrum.hpp"
#include "vf/world/CelestialSystem.hpp"
#include "vf/world/PlanetClimateGrid.hpp"
#include "vf/world/PlanetSurface.hpp"
#include "vf/world/PlanetSurfaceAuthority.hpp"

namespace vf {

enum class MotionType : std::uint8_t {
    Static,
    Dynamic,
    Kinematic,
};

struct PhysicsMaterial {
    double friction{0.65};
    double restitution{0.05};
    double rollingResistance{0.015};
};

struct AerodynamicProperties {
    double dragCoefficient{0.47};
    double referenceArea{1.0};
    double liftCoefficient{};
    double liftArea{};
    glm::dvec3 localLiftAxis{0.0, 1.0, 0.0};
};

struct BuoyancyProperties {
    bool enabled{};
    double displacedVolume{1.0};
    double fluidDragCoefficient{0.8};
    double fluidReferenceArea{1.0};
    bool displaceAtmosphere{};
};

struct RigidBodyDesc {
    MotionType motionType{MotionType::Dynamic};
    double mass{1.0};
    glm::dvec3 position{};
    glm::dquat orientation{1.0, 0.0, 0.0, 0.0};
    glm::dvec3 linearVelocity{};
    glm::dvec3 angularVelocity{};
    glm::dvec3 inertiaDiagonal{1.0};
    CollisionShape collisionShape{CollisionShape::sphere(0.5)};
    double linearDamping{0.01};
    double angularDamping{0.02};
    PhysicsMaterial material{};
    AerodynamicProperties aerodynamics{};
    BuoyancyProperties buoyancy{};
};

struct RigidBody {
    std::uint32_t id{};
    MotionType motionType{MotionType::Dynamic};
    double mass{1.0};
    double inverseMass{1.0};
    glm::dvec3 position{};
    glm::dquat orientation{1.0, 0.0, 0.0, 0.0};
    glm::dvec3 linearVelocity{};
    glm::dvec3 angularVelocity{};
    glm::dvec3 inertiaDiagonal{1.0};
    glm::dvec3 inverseInertiaDiagonal{1.0};
    glm::dvec3 accumulatedForce{};
    glm::dvec3 accumulatedTorque{};
    CollisionShape collisionShape{CollisionShape::sphere(0.5)};
    double linearDamping{0.01};
    double angularDamping{0.02};
    PhysicsMaterial material{};
    AerodynamicProperties aerodynamics{};
    BuoyancyProperties buoyancy{};
    bool sleeping{};
    double sleepTimer{};

    [[nodiscard]] glm::dvec3 linearMomentum() const noexcept;
    [[nodiscard]] double kineticEnergy() const noexcept;
    [[nodiscard]] glm::dmat3 worldInverseInertia() const noexcept;
    [[nodiscard]] glm::dvec3 velocityAtPoint(const glm::dvec3& worldPoint) const noexcept;
    [[nodiscard]] ShapePose shapePose() const noexcept { return {position, orientation}; }

    void addForce(const glm::dvec3& force) noexcept;
    void addTorque(const glm::dvec3& torque) noexcept;
    void addForceAtPoint(const glm::dvec3& force, const glm::dvec3& worldPoint) noexcept;
    void applyLinearImpulse(const glm::dvec3& impulse) noexcept;
    void applyAngularImpulse(const glm::dvec3& angularImpulse) noexcept;
    void applyImpulseAtPoint(const glm::dvec3& impulse, const glm::dvec3& worldPoint) noexcept;
    void wake() noexcept;
};

struct AtmosphereDefinition {
    double seaLevelTemperatureK{288.15};
    double seaLevelPressurePa{101325.0};
    double molarMassKgPerMol{0.0289644};
    double lapseRateKPerM{0.0065};
    double universalGasConstant{8.314462618};
    glm::dvec3 prevailingWind{};
    double gustAmplitude{};
    double gustSpatialScale{180.0};
    double gustTimeScale{0.08};
    double temperatureOffsetK{};
    double pressureScale{1.0};
};

struct WeatherState {
    double humidity{0.45};
    double cloudCover{0.25};
    double precipitationRateMmPerHour{};
    double stormIntensity{};
    double windMultiplier{1.0};
};

struct AtmosphereSample {
    double temperatureK{};
    double pressurePa{};
    double densityKgPerM3{};
    glm::dvec3 windVelocity{};
};

struct FluidDefinition {
    bool enabled{true};
    double surfaceRadius{235.0};
    double densityKgPerM3{997.0};
    double viscosityPaS{0.001};
    glm::dvec3 meanCurrent{};
};

struct PhysicsEnvironment {
    PlanetDefinition planet{};
    double surfaceGravity{9.81};
    AtmosphereDefinition atmosphere{};
    WeatherState weather{};
    FluidDefinition ocean{};
    const CelestialSystem* celestialSystem{};
    std::uint32_t primaryCelestialBodyId{};

    // R24 authority pointers. These are immutable/read-mostly fields owned by the runtime and may be
    // shared by renderer, collision, ecology and climate without copying a second fake planet.
    const PlanetSurfaceAuthority* surfaceAuthority{};
    const PlanetClimateGrid* climateGrid{};
    const OceanSpectrum* oceanSpectrum{};

    // When non-zero this PhysicsWorld is expressed in a planet/moon rotating local frame. Coriolis
    // and centrifugal accelerations are applied here instead of making the contact solver chase a
    // moving/rotating celestial mesh.
    glm::dvec3 rotatingFrameAngularVelocity{};

    [[nodiscard]] double gravityMagnitude(const glm::dvec3& position) const noexcept;
    [[nodiscard]] glm::dvec3 gravityAcceleration(const glm::dvec3& position) const noexcept;
    [[nodiscard]] double solidSurfaceRadius(const glm::dvec3& direction) const noexcept;
    [[nodiscard]] glm::dvec3 solidSurfaceNormal(const glm::dvec3& direction) const noexcept;
    [[nodiscard]] double oceanSurfaceRadiusAt(const glm::dvec3& position, double timeSeconds) const noexcept;
    [[nodiscard]] AtmosphereSample sampleAtmosphere(const glm::dvec3& position, double timeSeconds) const noexcept;
    [[nodiscard]] glm::dvec3 fluidVelocity(const glm::dvec3& position, double timeSeconds) const noexcept;
};

class PhysicsWorld final {
public:
    explicit PhysicsWorld(PhysicsEnvironment environment = {});

    [[nodiscard]] std::uint32_t createRigidBody(const RigidBodyDesc& desc);
    [[nodiscard]] RigidBody* body(std::uint32_t id) noexcept;
    [[nodiscard]] const RigidBody* body(std::uint32_t id) const noexcept;
    [[nodiscard]] std::span<RigidBody> bodies() noexcept { return bodies_; }
    [[nodiscard]] std::span<const RigidBody> bodies() const noexcept { return bodies_; }

    [[nodiscard]] std::uint32_t createDistanceConstraint(const DistanceConstraintDesc& desc);
    [[nodiscard]] std::uint32_t createSpringDamperConstraint(const SpringDamperConstraintDesc& desc);
    [[nodiscard]] std::uint32_t createHingeConstraint(const HingeConstraintDesc& desc);
    [[nodiscard]] std::uint32_t createGearConstraint(const GearConstraintDesc& desc);

    [[nodiscard]] std::span<DistanceConstraint> distanceConstraints() noexcept { return distanceConstraints_; }
    [[nodiscard]] std::span<const DistanceConstraint> distanceConstraints() const noexcept { return distanceConstraints_; }
    [[nodiscard]] std::span<SpringDamperConstraint> springDamperConstraints() noexcept { return springDamperConstraints_; }
    [[nodiscard]] std::span<const SpringDamperConstraint> springDamperConstraints() const noexcept { return springDamperConstraints_; }
    [[nodiscard]] std::span<HingeConstraint> hingeConstraints() noexcept { return hingeConstraints_; }
    [[nodiscard]] std::span<const HingeConstraint> hingeConstraints() const noexcept { return hingeConstraints_; }
    [[nodiscard]] std::span<GearConstraint> gearConstraints() noexcept { return gearConstraints_; }
    [[nodiscard]] std::span<const GearConstraint> gearConstraints() const noexcept { return gearConstraints_; }

    void advance(double frameDeltaSeconds);
    void stepFixed();

    [[nodiscard]] const PhysicsEnvironment& environment() const noexcept { return environment_; }
    [[nodiscard]] PhysicsEnvironment& environment() noexcept { return environment_; }
    [[nodiscard]] double fixedDeltaSeconds() const noexcept { return fixedDeltaSeconds_; }
    [[nodiscard]] double simulationTime() const noexcept { return simulationTime_; }
    [[nodiscard]] std::uint64_t stepIndex() const noexcept { return stepIndex_; }
    [[nodiscard]] std::size_t lastBroadphaseCandidateCount() const noexcept { return lastBroadphaseCandidateCount_; }
    [[nodiscard]] std::size_t lastContactPointCount() const noexcept { return lastContactPointCount_; }
    [[nodiscard]] std::size_t activeConstraintCount() const noexcept;

private:
    struct CachedContactPoint {
        glm::dvec3 localAnchorA{};
        glm::dvec3 localAnchorB{};
        double accumulatedNormalImpulse{};
        glm::dvec3 accumulatedTangentImpulse{};
        std::uint32_t featureId{};
    };

    struct CachedContactManifold {
        std::uint32_t bodyA{};
        std::uint32_t bodyB{};
        glm::dvec3 normal{1.0, 0.0, 0.0};
        std::array<CachedContactPoint, 4> points{};
        std::uint8_t pointCount{};
    };

    void applyEnvironmentForces(RigidBody& body);
    void applySpringDamperForces();
    void integrateBody(RigidBody& body);
    void solvePlanetContact(RigidBody& body);
    void solveBodyContacts();
    void solveMechanicalConstraints();
    void updateSleeping(RigidBody& body);

    PhysicsEnvironment environment_{};
    std::vector<RigidBody> bodies_;
    std::vector<DistanceConstraint> distanceConstraints_;
    std::vector<SpringDamperConstraint> springDamperConstraints_;
    std::vector<HingeConstraint> hingeConstraints_;
    std::vector<GearConstraint> gearConstraints_;
    std::unordered_map<std::uint64_t, CachedContactManifold> contactCache_;
    std::uint32_t nextBodyId_{1};
    std::uint32_t nextConstraintId_{1};
    double fixedDeltaSeconds_{1.0 / 120.0};
    double accumulator_{};
    double simulationTime_{};
    std::uint64_t stepIndex_{};
    std::size_t lastBroadphaseCandidateCount_{};
    std::size_t lastContactPointCount_{};
};

} // namespace vf
