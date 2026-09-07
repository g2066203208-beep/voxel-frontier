#include "vf/physics/PhysicsWorld.hpp"
#include "vf/world/CelestialSystem.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>
#include <glm/gtc/quaternion.hpp>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "CELESTIAL SYSTEM TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

void requireNear(double actual, double expected, double tolerance, std::string_view message) {
    if (std::abs(actual - expected) > tolerance) fail(message);
}

void requireVecNear(
    const glm::dvec3& actual,
    const glm::dvec3& expected,
    double tolerance,
    std::string_view message) {
    if (glm::length(actual - expected) > tolerance) fail(message);
}

void testSurfaceGravityAndAtmosphereBelongToEachPlanet() {
    vf::CelestialSystem system;

    vf::CelestialBody first{};
    first.name = "A";
    first.radiusMeters = 240.0;
    first.massKg = 9.81 * first.radiusMeters * first.radiusMeters / vf::CelestialSystem::kGravitationalConstant;
    first.gameplaySurfaceGravityMps2 = 9.81;
    first.gravityInfluenceRadiusMeters = 600.0;
    first.atmosphere.enabled = true;
    first.atmosphere.heightMeters = 120.0;
    first.atmosphere.surfacePressurePa = 101325.0;
    first.atmosphere.scaleHeightMeters = 70.0;
    first.climate.meanTemperatureK = 288.15;
    const auto firstId = system.addBody(first);

    const glm::dvec3 primarySurfacePoint{240.0, 0.0, 0.0};
    const auto isolatedSurface = system.sampleEnvironment(primarySurfacePoint);
    require(isolatedSurface.bodyId == firstId, "primary planet must own its local environment");
    requireNear(glm::length(system.gravityAccelerationAt(primarySurfacePoint)), 9.81, 0.02,
        "default world gravity must match configured gameplay surface gravity");
    require(isolatedSurface.pressurePa > 90000.0, "primary planet must expose its own atmosphere");

    vf::CelestialBody second = first;
    second.name = "B";
    second.position = {1200.0, 0.0, 0.0};
    second.massKg *= 0.38;
    second.gameplaySurfaceGravityMps2 = 3.7;
    second.gravityInfluenceRadiusMeters = 420.0;
    second.atmosphere.surfacePressurePa = 600.0;
    second.climate.meanTemperatureK = 220.0;
    const auto secondId = system.addBody(second);

    const auto firstSurface = system.sampleEnvironment(primarySurfacePoint);
    require(firstSurface.bodyId == firstId, "primary planet must retain ownership after another gravity source is added");

    const glm::dvec3 physicalGravity = system.physicalGravityAccelerationAt(primarySurfacePoint);
    const double primaryAcceleration = vf::CelestialSystem::kGravitationalConstant
        * first.massKg / (first.radiusMeters * first.radiusMeters);
    const double secondDistance = second.position.x - primarySurfacePoint.x;
    const double secondaryAcceleration = vf::CelestialSystem::kGravitationalConstant
        * second.massKg / (secondDistance * secondDistance);
    const double expectedX = -primaryAcceleration + secondaryAcceleration;
    requireNear(physicalGravity.x, expectedX, 1.0e-6,
        "explicit physical gravity must equal vector superposition of both bodies");
    require(std::abs(physicalGravity.y) < 1.0e-10 && std::abs(physicalGravity.z) < 1.0e-10,
        "collinear two-body physical gravity must remain collinear");

    const glm::dvec3 gameplayAtPrimary = system.gravityAccelerationAt(primarySurfacePoint);
    require(gameplayAtPrimary.x < -9.0,
        "inside the primary SOI, default game gravity must remain owned by the primary instead of being cancelled by a distant planet");
    require(system.gameplayReferenceBodyAt(primarySurfacePoint)->id == firstId,
        "gameplay reference body must be primary inside its SOI");

    const auto secondSurface = system.sampleEnvironment({1440.0, 0.0, 0.0});
    require(secondSurface.bodyId == secondId, "second planet must own its local environment");
    require(secondSurface.pressurePa > 400.0 && secondSurface.pressurePa < 800.0,
        "second planet must use its own atmosphere rather than the primary atmosphere");
    require(secondSurface.temperatureK < firstSurface.temperatureK,
        "second planet must use its own climate state");
}

void testAtmosphereFadesToVacuum() {
    vf::CelestialSystem system;
    vf::CelestialBody planet{};
    planet.radiusMeters = 100.0;
    planet.massKg = 1.0e15;
    planet.atmosphere.enabled = true;
    planet.atmosphere.heightMeters = 50.0;
    planet.atmosphere.surfacePressurePa = 100000.0;
    planet.atmosphere.scaleHeightMeters = 20.0;
    const auto id = system.addBody(planet);

    const auto surface = system.sampleEnvironment({100.0, 0.0, 0.0});
    const auto high = system.sampleEnvironment({140.0, 0.0, 0.0});
    const auto vacuum = system.sampleEnvironment({200.0, 0.0, 0.0});
    require(surface.bodyId == id && high.bodyId == id, "atmosphere samples must identify the planet");
    require(surface.pressurePa > high.pressurePa, "pressure must fall with altitude");
    require(vacuum.pressurePa == 0.0 && vacuum.densityKgPerM3 == 0.0,
        "outside the atmosphere must be vacuum");
}

void testGameplaySphereOfInfluenceAllowsFreeInterplanetarySpace() {
    vf::CelestialSystem system;

    vf::CelestialBody a{};
    a.radiusMeters = 100.0;
    a.massKg = 9.81 * 100.0 * 100.0 / vf::CelestialSystem::kGravitationalConstant;
    a.gameplaySurfaceGravityMps2 = 9.81;
    a.gravityInfluenceRadiusMeters = 300.0;
    const auto aId = system.addBody(a);

    vf::CelestialBody b{};
    b.radiusMeters = 60.0;
    b.position = {1000.0, 0.0, 0.0};
    b.massKg = 3.0 * 60.0 * 60.0 / vf::CelestialSystem::kGravitationalConstant;
    b.gameplaySurfaceGravityMps2 = 3.0;
    b.gravityInfluenceRadiusMeters = 220.0;
    const auto bId = system.addBody(b);

    require(system.gameplayReferenceBodyAt({150.0, 0.0, 0.0})->id == aId,
        "A must own points inside A SOI");
    require(system.gameplayReferenceBodyAt({940.0, 0.0, 0.0})->id == bId,
        "B must own points inside B SOI");

    const glm::dvec3 midpoint{500.0, 0.0, 0.0};
    require(system.gameplayReferenceBodyAt(midpoint) == nullptr,
        "space outside every physics bubble must remain in the inertial frame");
    require(glm::length(system.gravityAccelerationAt(midpoint)) > 1.0e-6,
        "leaving a reference-frame bubble must not delete Newtonian gravity");
}

void testSpinAndBoundOrbit() {
    vf::CelestialSystem system;
    vf::CelestialBody star{};
    star.type = vf::CelestialBodyType::Star;
    star.radiusMeters = 80.0;
    star.massKg = 1.0e15;
    const auto starId = system.addBody(star);

    vf::CelestialBody planet{};
    planet.radiusMeters = 20.0;
    planet.massKg = 1.0e10;
    planet.position = {1000.0, 0.0, 0.0};
    planet.orbitParentId = starId;
    planet.linearVelocity = {0.0, 0.0, std::sqrt(vf::CelestialSystem::kGravitationalConstant * star.massKg / 1000.0)};
    planet.spinAxis = {0.0, 1.0, 0.0};
    planet.spinRateRadPerSecond = 0.5;
    const auto planetId = system.addBody(planet);

    const glm::dquat initialOrientation = system.body(planetId)->orientation;
    for (int i = 0; i < 1000; ++i) system.step(0.05);

    const auto* evolved = system.body(planetId);
    require(evolved != nullptr, "orbiting body must remain accessible");
    const double radius = glm::length(evolved->position - system.body(starId)->position);
    require(radius > 900.0 && radius < 1100.0, "velocity-Verlet orbit must remain bound over the smoke interval");
    require(std::abs(glm::dot(initialOrientation, evolved->orientation)) < 0.999,
        "planet spin must evolve orientation");
}


void testRecommendedWarpStepHasNoFrozenDisplayFrames() {
    constexpr double scale = 240.0;
    const double stepSeconds = vf::recommendedCelestialFixedStepSeconds(scale);
    require(stepSeconds <= 0.25,
        "240x gameplay time must use a sub-second celestial integration step");

    vf::CelestialSimulationClock clock{{stepSeconds, scale, 4096U}};
    vf::CelestialSystem system;
    vf::CelestialBody body{};
    body.radiusMeters = 10.0;
    body.massKg = 1.0e10;
    body.spinAxis = glm::normalize(glm::dvec3{0.2, 0.96, 0.1});
    body.spinRateRadPerSecond = 0.02;
    const auto id = system.addBody(body);

    for (int frame = 0; frame < 120; ++frame) {
        const glm::dquat before = system.body(id)->orientation;
        const std::size_t steps = clock.advance(1.0 / 60.0, [&](double dt) { system.step(dt); });
        require(steps > 0U,
            "240x celestial motion must not freeze for a display frame and then jump later");
        const glm::dquat after = system.body(id)->orientation;
        require(std::abs(glm::dot(before, after)) < 0.999999999,
            "quaternion spin must evolve continuously on every accelerated display frame");
    }
}

void testKeplerianStateEnergyIdentity() {
    constexpr double mu = 3.98600435507e14;
    vf::KeplerianElements elements{};
    elements.semiMajorAxisMeters = 7000000.0;
    elements.eccentricity = 0.12;
    elements.inclinationRadians = 0.41;
    elements.longitudeAscendingNodeRadians = 0.83;
    elements.argumentPeriapsisRadians = 1.17;
    elements.meanAnomalyRadians = 0.64;

    const vf::OrbitalState state = vf::keplerianState(elements, mu);
    const double radius = glm::length(state.position);
    const double speedSquared = glm::dot(state.velocity, state.velocity);
    const double specificEnergy = 0.5 * speedSquared - mu / radius;
    requireNear(specificEnergy, -mu / (2.0 * elements.semiMajorAxisMeters), 0.05,
        "Keplerian state must satisfy the vis-viva specific-energy identity");
}

void testNBodyStepMovesBothMassiveBodies() {
    vf::CelestialSystem system;

    vf::CelestialBody left{};
    left.type = vf::CelestialBodyType::Star;
    left.radiusMeters = 10.0;
    left.massKg = 1.0e15;
    left.position = {-500.0, 0.0, 0.0};
    const auto leftId = system.addBody(left);

    vf::CelestialBody right = left;
    right.position = {500.0, 0.0, 0.0};
    const auto rightId = system.addBody(right);

    system.step(1.0);

    const auto* movedLeft = system.body(leftId);
    const auto* movedRight = system.body(rightId);
    require(movedLeft != nullptr && movedRight != nullptr, "both N-body sources must remain accessible");
    require(movedLeft->position.x > -500.0, "left massive body must accelerate toward right body");
    require(movedRight->position.x < 500.0, "right massive body must accelerate toward left body");
    requireNear(movedLeft->position.x + movedRight->position.x, 0.0, 1.0e-9,
        "equal-mass pair must preserve its barycenter during the symmetric step");
}

void testDipoleMagneticFieldFallsWithDistance() {
    vf::CelestialSystem system;
    vf::CelestialBody planet{};
    planet.radiusMeters = 100.0;
    planet.massKg = 1.0e15;
    planet.magneticField.enabled = true;
    planet.magneticField.dipoleAxis = {0.0, 1.0, 0.0};
    planet.magneticField.equatorialSurfaceFieldTesla = 30.0e-6;
    const auto id = system.addBody(planet);
    const auto* stored = system.body(id);

    const double surface = glm::length(system.magneticFieldAt(*stored, {100.0, 0.0, 0.0}));
    const double twiceRadius = glm::length(system.magneticFieldAt(*stored, {200.0, 0.0, 0.0}));
    requireNear(surface, 30.0e-6, 1.0e-9, "equatorial field must match configured surface field");
    requireNear(twiceRadius / surface, 1.0 / 8.0, 0.002, "dipole field must follow inverse-cube distance scaling");
}

void testReferenceFrameHierarchyComposesRotationAndVelocity() {
    vf::ReferenceFrameSystem frames;

    vf::ReferenceFrame root{};
    root.name = "root";
    root.localPosition = {100.0, -20.0, 5.0};
    root.localVelocity = {1.0, 2.0, 3.0};
    root.localRotation = glm::angleAxis(0.5, glm::dvec3{0.0, 1.0, 0.0});
    root.localAngularVelocity = {0.0, 0.25, 0.0};
    const auto rootId = frames.addFrame(root);

    vf::ReferenceFrame child{};
    child.name = "child";
    child.parentId = rootId;
    child.localPosition = {10.0, 2.0, -3.0};
    child.localVelocity = {0.5, 0.0, 2.0};
    const auto childId = frames.addFrame(child);

    const auto state = frames.worldState(childId);
    require(state.valid, "nested reference frame must resolve to a valid world state");

    const glm::dvec3 expectedOffset = root.localRotation * child.localPosition;
    const glm::dvec3 expectedPosition = root.localPosition + expectedOffset;
    const glm::dvec3 expectedVelocity = root.localVelocity
        + glm::cross(root.localAngularVelocity, expectedOffset)
        + root.localRotation * child.localVelocity;
    requireVecNear(state.position, expectedPosition, 1.0e-10,
        "child world position must include parent rotation and translation");
    requireVecNear(state.velocity, expectedVelocity, 1.0e-10,
        "child world velocity must include parent translation, rotation and omega-cross-r");

    const glm::dvec3 localPoint{2.0, -1.0, 4.0};
    const glm::dvec3 localVelocity{-0.5, 1.0, 0.25};
    const glm::dvec3 worldPoint = frames.toWorldPosition(childId, localPoint);
    const glm::dvec3 worldVelocity = frames.toWorldVelocity(childId, localPoint, localVelocity);
    requireVecNear(frames.toLocalPosition(childId, worldPoint), localPoint, 1.0e-10,
        "reference-frame position round-trip must be lossless at gameplay scales");
    requireVecNear(frames.toLocalVelocity(childId, worldPoint, worldVelocity), localVelocity, 1.0e-10,
        "reference-frame velocity round-trip must preserve rotating-frame kinematics");
}

void testCelestialReferenceFramesFollowOrbitHierarchy() {
    vf::CelestialSystem system;

    vf::CelestialBody star{};
    star.type = vf::CelestialBodyType::Star;
    star.name = "Helion";
    star.position = {-1000.0, 5.0, 10.0};
    star.linearVelocity = {0.0, 0.0, 1.0};
    star.massKg = 0.0;
    const auto starId = system.addBody(star);

    vf::CelestialBody planet{};
    planet.name = "Aster";
    planet.position = {-800.0, 15.0, 20.0};
    planet.linearVelocity = {0.0, 0.0, 3.0};
    planet.massKg = 0.0;
    planet.orbitParentId = starId;
    const auto planetId = system.addBody(planet);

    vf::CelestialBody moon{};
    moon.type = vf::CelestialBodyType::Moon;
    moon.name = "Cinder";
    moon.position = {-760.0, 17.0, 25.0};
    moon.linearVelocity = {0.0, 0.0, 3.5};
    moon.massKg = 0.0;
    moon.orbitParentId = planetId;
    const auto moonId = system.addBody(moon);

    const auto* storedStar = system.body(starId);
    const auto* storedPlanet = system.body(planetId);
    const auto* storedMoon = system.body(moonId);
    require(storedStar != nullptr && storedPlanet != nullptr && storedMoon != nullptr,
        "hierarchical celestial bodies must remain accessible");
    require(storedStar->referenceFrameId != 0U
        && storedPlanet->referenceFrameId != 0U
        && storedMoon->referenceFrameId != 0U,
        "every celestial body must receive a runtime inertial reference frame");

    const auto* planetFrame = system.referenceFrames().frame(storedPlanet->referenceFrameId);
    const auto* moonFrame = system.referenceFrames().frame(storedMoon->referenceFrameId);
    require(planetFrame != nullptr && moonFrame != nullptr,
        "planet and moon reference frames must exist");
    require(planetFrame->parentId == storedStar->referenceFrameId,
        "planet inertial frame must be parented to the star frame");
    require(moonFrame->parentId == storedPlanet->referenceFrameId,
        "moon inertial frame must be parented to the planet frame");

    requireVecNear(
        system.referenceFrames().worldPosition(storedPlanet->referenceFrameId),
        storedPlanet->position,
        1.0e-10,
        "planet hierarchical frame must reconstruct inertial world position");
    requireVecNear(
        system.referenceFrames().worldVelocity(storedMoon->referenceFrameId),
        storedMoon->linearVelocity,
        1.0e-10,
        "moon hierarchical frame must reconstruct inertial world velocity");

    system.step(120.0);
    storedPlanet = system.body(planetId);
    storedMoon = system.body(moonId);
    requireVecNear(
        system.referenceFrames().worldPosition(storedPlanet->referenceFrameId),
        storedPlanet->position,
        1.0e-9,
        "planet frame must stay synchronized after celestial integration");
    requireVecNear(
        system.referenceFrames().worldPosition(storedMoon->referenceFrameId),
        storedMoon->position,
        1.0e-9,
        "moon frame must stay synchronized after celestial integration");
}

void testUniverseTimeMultiRateSchedulingAndPrecision() {
    vf::UniverseTimeConfig config{};
    config.physicsStepSeconds = 0.01;
    config.gameplayStepSeconds = 0.02;
    config.weatherStepSeconds = 1.0;
    config.climateStepSeconds = 5.0;
    vf::UniverseTime time{config};

    vf::AstroTime epoch{};
    epoch.wholeSeconds = 9000000000LL;
    epoch.fractionalSeconds = 0.25;
    time.reset(epoch);
    time.advance(10.0);

    require(time.time().wholeSeconds == 9000000010LL,
        "UniverseTime must retain integer astronomical epoch seconds");
    requireNear(time.time().fractionalSeconds, 0.25, 1.0e-12,
        "UniverseTime must retain fractional epoch precision");
    require(time.consumePhysicsTicks() == 1000U,
        "10 simulated seconds must yield 1000 100-Hz physics ticks");
    require(time.consumeGameplayTicks() == 500U,
        "10 simulated seconds must yield 500 50-Hz gameplay ticks");
    require(time.consumeWeatherTicks() == 10U,
        "10 simulated seconds must yield ten 1-second weather ticks");
    require(time.consumeClimateTicks() == 2U,
        "10 simulated seconds must yield two 5-second climate ticks");
    requireNear(time.pendingPhysicsSeconds(), 0.0, 1.0e-10,
        "exact tick consumption must not leave an artificial physics remainder");
}

void testLargeCelestialStepConsumesAllSimulatedTime() {
    vf::CelestialSystem system;
    vf::CelestialBody body{};
    body.name = "ClockBody";
    body.massKg = 0.0;
    body.spinAxis = {0.0, 1.0, 0.0};
    body.spinRateRadPerSecond = 0.01;
    const auto bodyId = system.addBody(body);
    const glm::dquat initialOrientation = system.body(bodyId)->orientation;

    system.step(600.0);

    requireNear(system.simulationTime(), 600.0, 1.0e-9,
        "CelestialSystem must consume the complete delta instead of clamping and discarding after 60 seconds");
    const auto* evolved = system.body(bodyId);
    require(evolved != nullptr, "large-step body must remain accessible");
    require(std::abs(glm::dot(initialOrientation, evolved->orientation)) < 0.999,
        "spin integration must advance across all internal large-step substeps");
    requireVecNear(
        system.referenceFrames().worldPosition(evolved->referenceFrameId),
        evolved->position,
        1.0e-10,
        "reference-frame synchronization must survive multi-substep updates");
}

void testRotatingSurfaceTransfersTangentialVelocityToRigidBody() {
    vf::PlanetDefinition terrain{};
    terrain.radius = 100.0;
    terrain.maxElevation = 0.0;

    vf::CelestialSystem celestial;
    vf::CelestialBody planet{};
    planet.radiusMeters = terrain.radius;
    planet.massKg = 9.81 * planet.radiusMeters * planet.radiusMeters
        / vf::CelestialSystem::kGravitationalConstant;
    planet.gameplaySurfaceGravityMps2 = 9.81;
    planet.gravityInfluenceRadiusMeters = 400.0;
    planet.spinAxis = {0.0, 1.0, 0.0};
    planet.spinRateRadPerSecond = 0.01;
    const auto planetId = celestial.addBody(planet);

    vf::PhysicsEnvironment environment{};
    environment.planet = terrain;
    environment.celestialSystem = &celestial;
    environment.primaryCelestialBodyId = planetId;
    environment.ocean.enabled = false;
    environment.atmosphere.seaLevelPressurePa = 0.0;
    vf::PhysicsWorld physics{environment};

    vf::RigidBodyDesc desc{};
    desc.position = {101.0, 0.0, 0.0};
    desc.mass = 1.0;
    desc.collisionShape = vf::CollisionShape::sphere(1.0);
    desc.linearDamping = 0.0;
    desc.angularDamping = 0.0;
    desc.material.friction = 1.0;
    desc.material.restitution = 0.0;
    desc.aerodynamics.referenceArea = 0.0;
    const auto bodyId = physics.createRigidBody(desc);

    for (int i = 0; i < 240; ++i) physics.stepFixed();
    const auto* bodyState = physics.body(bodyId);
    require(bodyState != nullptr, "rotating-surface rigid body must remain accessible");
    require(std::abs(bodyState->linearVelocity.z) > 0.20,
        "ground friction must transfer non-zero tangential velocity from omega-cross-r surface motion");
    require(glm::length(bodyState->position) >= 100.999,
        "moving celestial surface contact must still prevent penetration");
}

} // namespace

int main() {
    testSurfaceGravityAndAtmosphereBelongToEachPlanet();
    testAtmosphereFadesToVacuum();
    testGameplaySphereOfInfluenceAllowsFreeInterplanetarySpace();
    testSpinAndBoundOrbit();
    testRecommendedWarpStepHasNoFrozenDisplayFrames();
    testKeplerianStateEnergyIdentity();
    testNBodyStepMovesBothMassiveBodies();
    testDipoleMagneticFieldFallsWithDistance();
    testReferenceFrameHierarchyComposesRotationAndVelocity();
    testCelestialReferenceFramesFollowOrbitHierarchy();
    testUniverseTimeMultiRateSchedulingAndPrecision();
    testLargeCelestialStepConsumesAllSimulatedTime();
    testRotatingSurfaceTransfersTangentialVelocityToRigidBody();
    std::cout << "vf_celestial_system_tests: PASS\n";
    return 0;
}
