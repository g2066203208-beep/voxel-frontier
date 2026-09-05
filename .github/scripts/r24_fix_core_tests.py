#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def rw(rel):
    p = ROOT / rel
    return p, p.read_text(encoding='utf-8')

def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f'missing anchor: {label}')
    return text.replace(old, new, 1)

p, t = rw('native/tests/PlanetPhysicsTests.cpp')
t = replace_once(
    t,
    '    e.weather.stormIntensity = .6;\n    auto sea = e.sampleAtmosphere({0, 1000, 0}, 12);',
    '    e.weather.stormIntensity = .6;\n    e.atmosphere.prevailingWind = {7.0, 0.0, 2.0};\n    auto sea = e.sampleAtmosphere({0, 1000, 0}, 12);',
    'explicit fallback wind test')
p.write_text(t, encoding='utf-8')

p, t = rw('native/tests/CelestialPhysicsFrameTests.cpp')
old = '''void testFiniteGravityBecomesZeroWithoutWaitingForAnotherPlanet() {
    vf::CelestialSystem system;
    vf::CelestialBody planet{};
    planet.radiusMeters = 6000.0;
    planet.massKg = 9.81 * planet.radiusMeters * planet.radiusMeters
        / vf::CelestialSystem::kGravitationalConstant;
    planet.gameplaySurfaceGravityMps2 = 9.81;
    planet.atmosphere.enabled = true;
    planet.atmosphere.heightMeters = 1100.0;
    planet.gravityFalloffStartRadiusMeters = 7100.0;
    planet.gravityFalloffPower = 10.0;
    planet.gravityCutoffAccelerationMps2 = 0.05;
    planet.gravityInfluenceRadiusMeters = 11000.0;
    const auto planetId = system.addBody(planet);
    (void)planetId;

    const glm::dvec3 atmosphereTop{7100.0, 0.0, 0.0};
    const glm::dvec3 deepSpace{12000.0, 0.0, 0.0};
    require(system.gravityMagnitudeFromBody(*system.body(planetId), atmosphereTop) > 1.0,
        "leaving atmosphere must not unrealistically delete gravity at the exact atmosphere boundary");
    requireNear(glm::length(system.gravityAccelerationAt(deepSpace)), 0.0, 1.0e-12,
        "planet gravity must become true zero beyond its finite gameplay gravity well");
    require(system.gravityReferenceBodyAt(deepSpace) == nullptr,
        "zero-g space must not remain owned by the old planet gravity state");
}'''
new = '''void testPhysicalGravityPersistsOutsideReferenceBubble() {
    vf::CelestialSystem system;
    vf::CelestialBody planet{};
    planet.radiusMeters = 6000.0;
    planet.massKg = 9.81 * planet.radiusMeters * planet.radiusMeters
        / vf::CelestialSystem::kGravitationalConstant;
    planet.gameplaySurfaceGravityMps2 = 9.81;
    planet.atmosphere.enabled = true;
    planet.atmosphere.heightMeters = 1100.0;
    planet.gravityInfluenceRadiusMeters = 11000.0; // legacy bubble hint only
    planet.physicsBubbleRadiusMeters = 11000.0;
    const auto planetId = system.addBody(planet);

    const glm::dvec3 atmosphereTop{7100.0, 0.0, 0.0};
    const glm::dvec3 deepSpace{12000.0, 0.0, 0.0};
    require(system.gravityMagnitudeFromBody(*system.body(planetId), atmosphereTop) > 1.0,
        "leaving atmosphere must not delete physical gravity");
    const double expected = vf::CelestialSystem::kGravitationalConstant * planet.massKg
        / glm::dot(deepSpace, deepSpace);
    requireNear(glm::length(system.gravityAccelerationAt(deepSpace)), expected, expected * 1.0e-12,
        "gravity outside the physics bubble must remain Newtonian inverse-square");
    require(system.physicsReferenceBodyAt(deepSpace) == nullptr,
        "reference-frame bubble may end without changing the gravity law");
    require(system.gravityReferenceBodyAt(deepSpace) != nullptr,
        "gravitational dominance and reference-frame ownership are different concepts");
}'''
t = replace_once(t, old, new, 'physical gravity frame test')
t = replace_once(
    t,
    '    testFiniteGravityBecomesZeroWithoutWaitingForAnotherPlanet();',
    '    testPhysicalGravityPersistsOutsideReferenceBubble();',
    'frame test invocation')
p.write_text(t, encoding='utf-8')

p, t = rw('native/tests/InterplanetaryFlightTests.cpp')
t = replace_once(
    t,
    '''    require(zeroGButStillLocal != nullptr && zeroGButStillLocal->id == homeId,
        "a precision physics bubble may extend beyond the planet's gravity cutoff");
    require(celestial.gravityReferenceBodyAt({350.0, 0.0, 0.0}) == nullptr,
        "zero-g inside a physics bubble must not still be labelled as planetary gravity");''',
    '''    require(zeroGButStillLocal != nullptr && zeroGButStillLocal->id == homeId,
        "a precision physics bubble is allowed to extend independently of force magnitude");
    require(celestial.gravityReferenceBodyAt({350.0, 0.0, 0.0}) != nullptr,
        "physical Newtonian gravity must persist independently of the precision bubble");
    require(glm::length(celestial.gravityAccelerationAt({350.0, 0.0, 0.0})) > 1.0e-6,
        "reference-frame policy must never zero the physical force field");''',
    'interplanetary gravity/reference separation')

t = replace_once(
    t,
    'void testZeroGInsidePhysicsBubbleCannotWalkAroundPlanet() {',
    'void testPhysicalGravityInsidePhysicsBubbleRemainsBallistic() {',
    'rename zero-g test')
t = replace_once(
    t,
    '''    require(camera.altitude() > 85.0,
        "test player must reach the zero-g region above the authored gravity cutoff");
    require(camera.inPlanetPhysicsFrame(),
        "zero-g player may remain in the planet precision bubble without being surface-bound");''',
    '''    require(camera.altitude() > 85.0,
        "test player must reach near-space while remaining inside the precision bubble");
    require(camera.inPlanetPhysicsFrame(),
        "near-space player may remain in the planet precision bubble without being surface-bound");''',
    'near-space setup')
t = replace_once(
    t,
    '''    require(!camera.flightMode() && !camera.grounded(),
        "turning off creative flight in near space must produce an airborne/free-flight state");''',
    '''    require(!camera.flightMode() && !camera.grounded(),
        "turning off creative flight in near space must produce a ballistic airborne state");''',
    'ballistic state')
old_tail = '''    const auto* body = celestial.body(planetId);
    require(body != nullptr, "zero-g test planet must exist");
    const glm::dvec3 beforeLocal = glm::conjugate(glm::normalize(body->orientation))
        * (camera.position() - body->position);
    const glm::dvec3 beforeDirection = glm::normalize(beforeLocal);

    vf::PlanetMovementInput forward{};
    forward.forward = 1.0;
    for (int i = 0; i < 120; ++i) camera.update(forward, 1.0 / 60.0);

    const glm::dvec3 afterLocal = glm::conjugate(glm::normalize(body->orientation))
        * (camera.position() - body->position);
    require(glm::length(glm::normalize(afterLocal) - beforeDirection) < 1.0e-4,
        "W input in zero-g must not become spherical surface walking merely because a planet physics frame is active");'''
new_tail = '''    const auto* body = celestial.body(planetId);
    require(body != nullptr, "near-space test planet must exist");
    const double altitudeBefore = camera.altitude();
    vf::PlanetMovementInput idleBallistic{};
    for (int i = 0; i < 60; ++i) camera.update(idleBallistic, 1.0 / 60.0);
    require(camera.altitude() < altitudeBefore - 0.1,
        "disabling creative flight must reveal persistent physical gravity even inside a precision bubble");'''
t = replace_once(t, old_tail, new_tail, 'ballistic tail')
t = replace_once(
    t,
    '    testZeroGInsidePhysicsBubbleCannotWalkAroundPlanet();',
    '    testPhysicalGravityInsidePhysicsBubbleRemainsBallistic();',
    'ballistic invocation')
p.write_text(t, encoding='utf-8')

print('R24 compatibility tests updated for physical gravity and explicit wind')
