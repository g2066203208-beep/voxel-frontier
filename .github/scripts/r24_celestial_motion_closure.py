from pathlib import Path

HEADER = Path('native/include/vf/player/PlanetCamera.hpp')
CAMERA = Path('native/src/player/PlanetCamera.cpp')
MAIN = Path('native/src/app/Main.cpp')
ASTRO = Path('native/include/vf/world/AstroTime.hpp')
FLIGHT_TEST = Path('native/tests/InterplanetaryFlightTests.cpp')
CELESTIAL_TEST = Path('native/tests/CelestialSystemTests.cpp')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'{label}: anchor missing')
    return text.replace(old, new, 1)

# -----------------------------------------------------------------------------
# 1. PlanetCamera: free-space creative flight must preserve inertial carrier
#    velocity inherited from the rotating/orbiting parent body.
# -----------------------------------------------------------------------------
header = HEADER.read_text(encoding='utf-8')
old_set_flight = '''    void setFlightMode(bool enabled) noexcept {\n        flightMode_ = enabled;\n        grounded_ = false;\n        if (enabled) {\n            if (inPhysicsFrame_) localVelocity_ = {};\n            else velocity_ = {};\n        }\n    }\n'''
new_set_flight = '''    void setFlightMode(bool enabled) noexcept {\n        if (flightMode_ == enabled) return;\n        flightMode_ = enabled;\n        grounded_ = false;\n        if (enabled && !inPhysicsFrame_) {\n            // Creative controls are relative to the inertial carrier inherited from the frame we\n            // just left. Never zero the absolute world velocity: that would erase a planet's\n            // ~30 km/s orbital velocity and make the planet visibly fly away from the player.\n            inertialFlightCarrierVelocity_ = velocity_;\n            inertialFlightControlVelocity_ = {};\n            inertialFlightCarrierValid_ = true;\n        } else if (!enabled) {\n            inertialFlightCarrierValid_ = false;\n            inertialFlightControlVelocity_ = {};\n        }\n    }\n'''
header = replace_once(header, old_set_flight, new_set_flight, 'PlanetCamera.hpp setFlightMode')
old_fields = '''    glm::dvec3 localPosition_{};\n    glm::dvec3 localVelocity_{};\n    bool inPhysicsFrame_{};\n\n    glm::dvec3 viewForward_{0.0, 0.0, -1.0};\n'''
new_fields = '''    glm::dvec3 localPosition_{};\n    glm::dvec3 localVelocity_{};\n    bool inPhysicsFrame_{};\n\n    // Outside every rotating-body precision frame, creative controls operate relative to this\n    // inertial carrier. The carrier includes parent orbital velocity, body-spin tangential velocity\n    // and any already-existing escape velocity at the exact frame handoff.\n    glm::dvec3 inertialFlightCarrierVelocity_{};\n    glm::dvec3 inertialFlightControlVelocity_{};\n    bool inertialFlightCarrierValid_{};\n\n    glm::dvec3 viewForward_{0.0, 0.0, -1.0};\n'''
header = replace_once(header, old_fields, new_fields, 'PlanetCamera.hpp inertial carrier fields')
HEADER.write_text(header, encoding='utf-8')

camera = CAMERA.read_text(encoding='utf-8')
old_enter = '''    trackedPhysicsFrameOrientation_ = glm::normalize(body.orientation);\n    trackedPhysicsFrameOrientationValid_ = true;\n}\n\nvoid PlanetCamera::leavePhysicsFrame() noexcept {\n    inPhysicsFrame_ = false;\n'''
new_enter = '''    trackedPhysicsFrameOrientation_ = glm::normalize(body.orientation);\n    trackedPhysicsFrameOrientationValid_ = true;\n    // The rotating local frame is now authoritative; any old free-space carrier is stale.\n    inertialFlightCarrierValid_ = false;\n    inertialFlightCarrierVelocity_ = {};\n    inertialFlightControlVelocity_ = {};\n}\n\nvoid PlanetCamera::leavePhysicsFrame() noexcept {\n    // syncWorldStateFromLocal() has already produced the exact inertial velocity, including\n    // body.linearVelocity + omega x r + local relative velocity. Preserve it as the creative-flight\n    // carrier instead of letting free-space controls damp the whole world velocity toward zero.\n    if (flightMode_) {\n        inertialFlightCarrierVelocity_ = velocity_;\n        inertialFlightControlVelocity_ = {};\n        inertialFlightCarrierValid_ = true;\n    }\n    inPhysicsFrame_ = false;\n'''
camera = replace_once(camera, old_enter, new_enter, 'PlanetCamera.cpp frame handoff')
old_toggle = '''    if (input.toggleFlight) {\n        flightMode_ = !flightMode_;\n        grounded_ = false;\n        if (flightMode_) {\n            if (inPhysicsFrame_) localVelocity_ = {};\n            else velocity_ = {};\n        }\n    }\n'''
new_toggle = '''    if (input.toggleFlight) setFlightMode(!flightMode_);\n'''
camera = replace_once(camera, old_toggle, new_toggle, 'PlanetCamera.cpp toggle flight')
old_free = '''        if (flightMode_) {\n            glm::dvec3 move = forward * input.forward + right * input.right + cameraUp * input.vertical;\n            const double moveLength = glm::length(move);\n            if (moveLength > 1.0) move /= moveLength;\n            const double targetSpeed = creativeFlightSpeedMps_ * (input.sprint ? 4.0 : 1.0);\n            const glm::dvec3 desired = moveLength > 1.0e-8 ? move * targetSpeed : glm::dvec3{};\n            velocity_ += (desired - velocity_) * (1.0 - std::exp(-7.0 * dt));\n        } else {\n            velocity_ += celestialSystem_->gravityAccelerationAt(position_) * dt;\n        }\n        position_ += velocity_ * dt;\n'''
new_free = '''        if (flightMode_) {\n            if (!inertialFlightCarrierValid_) {\n                inertialFlightCarrierVelocity_ = velocity_;\n                inertialFlightControlVelocity_ = {};\n                inertialFlightCarrierValid_ = true;\n            }\n            glm::dvec3 move = forward * input.forward + right * input.right + cameraUp * input.vertical;\n            const double moveLength = glm::length(move);\n            if (moveLength > 1.0) move /= moveLength;\n            const double targetSpeed = creativeFlightSpeedMps_ * (input.sprint ? 4.0 : 1.0);\n            const glm::dvec3 desiredControl = moveLength > 1.0e-8\n                ? move * targetSpeed\n                : glm::dvec3{};\n            inertialFlightControlVelocity_ +=\n                (desiredControl - inertialFlightControlVelocity_) * (1.0 - std::exp(-7.0 * dt));\n            velocity_ = inertialFlightCarrierVelocity_ + inertialFlightControlVelocity_;\n        } else {\n            inertialFlightCarrierValid_ = false;\n            inertialFlightControlVelocity_ = {};\n            velocity_ += celestialSystem_->gravityAccelerationAt(position_) * dt;\n        }\n        position_ += velocity_ * dt;\n'''
camera = replace_once(camera, old_free, new_free, 'PlanetCamera.cpp inertial creative flight')
CAMERA.write_text(camera, encoding='utf-8')

# -----------------------------------------------------------------------------
# 2. Astronomical fixed-step policy. At normal and common accelerated time scales,
#    every ordinary display frame receives multiple bounded vector/quaternion steps.
# -----------------------------------------------------------------------------
astro = ASTRO.read_text(encoding='utf-8')
clock_anchor = '''struct CelestialClockConfig {\n'''
clock_helper = '''[[nodiscard]] inline double recommendedCelestialFixedStepSeconds(double timeScale) noexcept {\n    if (!std::isfinite(timeScale) || timeScale <= 0.0) return 1.0 / 120.0;\n    if (timeScale <= 4.0) return 1.0 / 120.0;\n    if (timeScale <= 240.0) return 0.25;\n    if (timeScale <= 1000.0) return 1.0;\n    if (timeScale <= 20000.0) return 5.0;\n    return 30.0;\n}\n\nstruct CelestialClockConfig {\n'''
astro = replace_once(astro, clock_anchor, clock_helper, 'AstroTime.hpp step policy')
ASTRO.write_text(astro, encoding='utf-8')

# -----------------------------------------------------------------------------
# 3. Runtime: use the fine step policy, keep accelerated surface time, but never
#    run celestial bodies at 240x while a free-space player is integrated at 1x.
# -----------------------------------------------------------------------------
main = MAIN.read_text(encoding='utf-8')
old_step = '''        const double celestialFixedStepSeconds = celestialTimeScale <= 1000.0 ? 5.0\n            : (celestialTimeScale <= 20000.0 ? 15.0 : 60.0);\n        vf::CelestialSimulationClock celestialClock{{\n            celestialFixedStepSeconds, celestialTimeScale, 4096U}};\n'''
new_step = '''        const double celestialFixedStepSeconds =\n            vf::recommendedCelestialFixedStepSeconds(celestialTimeScale);\n        vf::CelestialSimulationClock celestialClock{{\n            celestialFixedStepSeconds, celestialTimeScale, 4096U}};\n'''
main = replace_once(main, old_step, new_step, 'Main.cpp celestial fixed step')
old_flags = '''        const bool runtimeDiagnosticsStdout = [] {\n            const char* value = std::getenv("VF_RUNTIME_DIAGNOSTICS");\n            return value != nullptr && std::string_view{value} == "1";\n        }();\n        if (captureHighSpeed) {\n'''
new_flags = '''        const bool runtimeDiagnosticsStdout = [] {\n            const char* value = std::getenv("VF_RUNTIME_DIAGNOSTICS");\n            return value != nullptr && std::string_view{value} == "1";\n        }();\n        const bool captureEscapeInheritance = [] {\n            const char* value = std::getenv("VF_CAPTURE_ESCAPE_INHERITANCE");\n            return value != nullptr && std::string_view{value} == "1";\n        }();\n        if (captureHighSpeed) {\n'''
main = replace_once(main, old_flags, new_flags, 'Main.cpp escape capture flag')
old_frame_init = '''        vf::CelestialPhysicsFrame asterFrame{asterId};\n\n        const glm::dquat initialInverseAster = glm::conjugate(glm::normalize(initialAster->orientation));\n'''
new_frame_init = '''        vf::CelestialPhysicsFrame asterFrame{asterId};\n\n        if (captureEscapeInheritance) {\n            // Start only five kilometres inside the real precision-bubble boundary. The camera is\n            // still owned by Aster, so the outward local velocity is converted through the same\n            // CelestialPhysicsFrame used by production flight: orbital velocity + omega x r are\n            // inherited automatically at the exact handoff to inertial space.\n            const glm::dvec3 escapeDirection = spawnDirection;\n            const double localRadius = std::max(\n                planet.radius + 1000.0, initialAster->physicsBubbleRadiusMeters - 5000.0);\n            const glm::dvec3 localPosition = escapeDirection * localRadius;\n            const glm::dvec3 localVelocity = escapeDirection * 45000.0;\n            camera.setExternalWorldState(\n                asterFrame.toWorldPosition(*initialAster, localPosition),\n                asterFrame.toWorldVelocity(*initialAster, localPosition, localVelocity),\n                false);\n            camera.setFlightMode(true);\n            camera.setCreativeFlightSpeedMps(45000.0);\n            camera.setViewDirectionWorld(\n                initialAster->position - camera.position(), camera.up());\n            std::cout << "R24 escape inheritance armed: boundary_margin_km=5"\n                      << " parent_orbit_mps=" << glm::length(initialAster->linearVelocity) << '\\n';\n        }\n\n        const glm::dquat initialInverseAster = glm::conjugate(glm::normalize(initialAster->orientation));\n'''
main = replace_once(main, old_frame_init, new_frame_init, 'Main.cpp escape initial state')
old_loop_clock = '''            previous = now;\n            celestialClock.advance(dt, [&](double astroDt) {\n                // One authoritative step advances N-body/spin plus every registered planetary\n                // service on the same bounded simulated-time sequence.\n                planetaryBodies.step(astroDt);\n            });\n\n            auto* currentAster = celestial.body(asterId);\n'''
new_loop_clock = '''            previous = now;\n\n            // Surface gameplay may use accelerated day/orbit time. Free inertial player space may\n            // not: until all free-space rigid bodies participate in a global time-warp integrator,\n            // running planets at 240x while the player advances at 1x is physically impossible and\n            // makes the parent planet shoot away. External evidence views are camera tools, not a\n            // free player, so they retain the requested acceleration.\n            const bool freePlayerInertialSpace = camera.physicsFrameBodyId() == 0U\n                && celestialViewMode.empty();\n            const double effectiveCelestialTimeScale = freePlayerInertialSpace\n                ? 1.0\n                : celestialTimeScale;\n            celestialClock.setTimeScale(effectiveCelestialTimeScale);\n            celestialClock.advance(dt, [&](double astroDt) {\n                // One authoritative step advances double-precision N-body vectors and quaternion\n                // spin on the same bounded simulated-time sequence.\n                planetaryBodies.step(astroDt);\n            });\n\n            auto* currentAster = celestial.body(asterId);\n'''
main = replace_once(main, old_loop_clock, new_loop_clock, 'Main.cpp physical time-scale handoff')
old_moon_track = '''            if (trackMoonEvidence && currentMoon != nullptr) {\n                camera.setViewDirectionWorld(\n                    currentMoon->position - camera.position(), camera.up());\n            }\n\n            const glm::dvec3 cameraSurface = toSurfacePoint(cameraPlanet);\n'''
new_moon_track = '''            if (trackMoonEvidence && currentMoon != nullptr) {\n                camera.setViewDirectionWorld(\n                    currentMoon->position - camera.position(), camera.up());\n            }\n\n            if (captureEscapeInheritance && runtimeDiagnosticsStdout) {\n                const glm::dvec3 orbitDirection = safeNormalize(\n                    currentAster->linearVelocity, {0.0, 0.0, -1.0});\n                const glm::dvec3 relativePosition = camera.position() - currentAster->position;\n                const glm::dvec3 radial = safeNormalize(relativePosition, spawnDirection);\n                const glm::dvec3 relativeVelocity = camera.velocity() - currentAster->linearVelocity;\n                const glm::dvec3 transverseRelative = relativeVelocity\n                    - radial * glm::dot(relativeVelocity, radial);\n                std::cout << "R24 escape inheritance: frame="\n                          << (camera.physicsFrameBodyId() == asterId ? "aster" : "inertial")\n                          << " distance_km=" << glm::length(relativePosition) / 1000.0\n                          << " inherited_orbit_mps=" << glm::dot(camera.velocity(), orbitDirection)\n                          << " transverse_relative_mps=" << glm::length(transverseRelative)\n                          << " effective_time_scale=" << effectiveCelestialTimeScale << '\\n';\n            }\n\n            const glm::dvec3 cameraSurface = toSurfacePoint(cameraPlanet);\n'''
main = replace_once(main, old_moon_track, new_moon_track, 'Main.cpp escape diagnostics')
MAIN.write_text(main, encoding='utf-8')

# -----------------------------------------------------------------------------
# 4. Regression: leaving a moving planet in creative mode must preserve orbital
#    carrier velocity instead of exponentially braking it to zero.
# -----------------------------------------------------------------------------
flight_tests = FLIGHT_TEST.read_text(encoding='utf-8')
new_flight_test = r'''
void testCreativeFlightPreservesParentOrbitalVelocityAfterBubbleExit() {
    vf::PlanetDefinition terrain{};
    terrain.radius = 100.0;
    terrain.maxElevation = 0.0;
    terrain.atmosphereHeight = 20.0;

    vf::CelestialSystem celestial;
    vf::CelestialBody home{};
    home.name = "MovingHome";
    home.radiusMeters = terrain.radius;
    home.massKg = 9.81 * 100.0 * 100.0 / vf::CelestialSystem::kGravitationalConstant;
    home.physicsBubbleRadiusMeters = 135.0;
    home.linearVelocity = {0.0, 0.0, -30000.0};
    home.spinAxis = {0.0, 1.0, 0.0};
    home.spinRateRadPerSecond = 0.01;
    const auto homeId = celestial.addBody(home);

    vf::PlanetCamera camera{terrain, &celestial, homeId};
    camera.setFlightMode(true);
    camera.setCreativeFlightSpeedMps(1200.0);

    vf::PlanetMovementInput rise{};
    rise.vertical = 1.0;
    rise.sprint = true;
    for (int frame = 0; frame < 120 && camera.inPlanetPhysicsFrame(); ++frame)
        camera.update(rise, 1.0 / 60.0);
    require(!camera.inPlanetPhysicsFrame(),
        "creative escape test must cross the moving planet precision-bubble boundary");

    const double inheritedBefore = -camera.velocity().z;
    require(inheritedBefore > 29000.0,
        "frame handoff must initially include the parent's 30 km/s orbital carrier velocity");

    vf::PlanetMovementInput idle{};
    for (int frame = 0; frame < 180; ++frame) camera.update(idle, 1.0 / 60.0);
    const double inheritedAfter = -camera.velocity().z;
    require(inheritedAfter > 0.98 * inheritedBefore,
        "idle free-space creative flight must preserve inherited orbital velocity instead of damping absolute world velocity toward zero");
}

'''
if 'void testCreativeFlightPreservesParentOrbitalVelocityAfterBubbleExit()' not in flight_tests:
    marker = 'void testCreativeFlightCanLandOnSolidGround() {'
    if marker not in flight_tests:
        raise SystemExit('InterplanetaryFlightTests.cpp insertion anchor missing')
    flight_tests = flight_tests.replace(marker, new_flight_test + marker, 1)
call_anchor = '    testCreativeFlightIsExplicitAndGravityIndependent();\n'
if '    testCreativeFlightPreservesParentOrbitalVelocityAfterBubbleExit();\n' not in flight_tests:
    if call_anchor not in flight_tests:
        raise SystemExit('InterplanetaryFlightTests.cpp main anchor missing')
    flight_tests = flight_tests.replace(
        call_anchor,
        call_anchor + '    testCreativeFlightPreservesParentOrbitalVelocityAfterBubbleExit();\n',
        1,
    )
FLIGHT_TEST.write_text(flight_tests, encoding='utf-8')

# -----------------------------------------------------------------------------
# 5. Regression: the standard accelerated display configuration must advance the
#    real vector/quaternion state on every ordinary 60 Hz display frame.
# -----------------------------------------------------------------------------
celestial_tests = CELESTIAL_TEST.read_text(encoding='utf-8')
new_clock_test = r'''
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

'''
if 'void testRecommendedWarpStepHasNoFrozenDisplayFrames()' not in celestial_tests:
    marker = 'void testKeplerianStateEnergyIdentity() {'
    if marker not in celestial_tests:
        raise SystemExit('CelestialSystemTests.cpp insertion anchor missing')
    celestial_tests = celestial_tests.replace(marker, new_clock_test + marker, 1)
# Insert call before the final PASS print by anchoring an existing call if possible.
if '    testRecommendedWarpStepHasNoFrozenDisplayFrames();\n' not in celestial_tests:
    # testSpinAndBoundOrbit is guaranteed in this file; add immediately after its call.
    call = '    testSpinAndBoundOrbit();\n'
    if call not in celestial_tests:
        raise SystemExit('CelestialSystemTests.cpp main call anchor missing')
    celestial_tests = celestial_tests.replace(
        call,
        call + '    testRecommendedWarpStepHasNoFrozenDisplayFrames();\n',
        1,
    )
CELESTIAL_TEST.write_text(celestial_tests, encoding='utf-8')

print('R24 celestial motion closure applied: inertial velocity inheritance + coherent free-space time + smooth warp stepping')
