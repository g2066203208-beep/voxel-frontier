#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_function(path: str, signature: str, next_signature: str, replacement: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    start = text.find(signature)
    if start < 0:
        if replacement in text:
            return
        raise SystemExit(f"missing function signature in {path}: {signature}")
    end = text.find(next_signature, start + len(signature))
    if end < 0:
        raise SystemExit(f"missing next function signature in {path}: {next_signature}")
    text = text[:start] + replacement.rstrip() + "\n\n" + text[end:]
    p.write_text(text, encoding="utf-8")


# Retain the source-generation repairs from V1.
main = ROOT / "native/src/app/Main.cpp"
text = main.read_text(encoding="utf-8")
bad = 'std::cout << "R24 SUN_TRANSIT_ARRIVED\n";'
good = 'std::cout << "R24 SUN_TRANSIT_ARRIVED\\n";'
if bad in text:
    text = text.replace(bad, good, 1)
elif good not in text:
    raise SystemExit("interstellar Sun arrival marker not found after closure patch")
main.write_text(text, encoding="utf-8")

flight_test = ROOT / "native/tests/InterplanetaryFlightTests.cpp"
text = flight_test.read_text(encoding="utf-8")
bad_test = """    star.massKg = 1.0e20;\n    celestial.addBody(star);\n\n    vf::PlanetCamera camera{terrain, &celestial, homeId};\n"""
good_test = """    star.massKg = 1.0e20;\n    const auto starId = celestial.addBody(star);\n    require(starId != 0U, \"interstellar warp test star must be registered\");\n\n    vf::PlanetCamera camera{terrain, &celestial, homeId};\n"""
if bad_test in text:
    text = text.replace(bad_test, good_test, 1)
elif good_test not in text:
    raise SystemExit("interstellar warp test anchor not found after closure patch")
flight_test.write_text(text, encoding="utf-8")

# Wheel control is intentionally split: fine logarithmic control near a body, coarse bands in
# inertial space. The old ×2 assertion remains as a surface gate rather than being deleted.
replace_function(
    "native/tests/CameraInputTests.cpp",
    "void testFlightSpeedUsesLogarithmicWheelSteps() {",
    "void testDMovesToCameraRightInFlight() {",
    r'''void testFlightSpeedUsesLogarithmicWheelSteps() {
    vf::PlanetDefinition planet{};
    planet.radius = 1000.0;
    planet.maxElevation = 0.0;
    planet.atmosphereHeight = 100.0;

    // A camera with no body owner is an inertial-space camera. Two wheel notches intentionally
    // jump four octaves (x16), which makes AU-scale travel selectable without dozens of scrolls.
    vf::PlanetCamera spaceCamera{planet};
    const double spaceBefore = spaceCamera.flightSpeedMps();
    vf::PlanetMovementInput input{};
    input.flightSpeedSteps = 2.0;
    spaceCamera.update(input, 1.0 / 60.0);
    require(spaceCamera.flightSpeedMps() > spaceBefore * 15.99
            && spaceCamera.flightSpeedMps() < spaceBefore * 16.01,
        "two positive wheel steps in inertial space must span sixteen times the creative travel speed");

    input = {};
    input.flightSpeedSteps = -40.0;
    spaceCamera.update(input, 1.0 / 60.0);
    require(spaceCamera.flightSpeedMps() >= 0.999 && spaceCamera.flightSpeedMps() <= 1.001,
        "creative flight must still allow a 1 m/s inspection speed without going below it");

    // Inside a real rotating-body ownership frame the original fine speed selection remains:
    // exactly two wheel notches still double the requested speed.
    vf::CelestialSystem system;
    vf::CelestialBody body{};
    body.type = vf::CelestialBodyType::Planet;
    body.radiusMeters = planet.radius;
    body.massKg = 1.0e12;
    body.physicsBubbleRadiusMeters = 1.0e12;
    body.gravityInfluenceRadiusMeters = 1.0e12;
    const auto bodyId = system.addBody(body);
    vf::PlanetCamera surfaceCamera{planet, &system, bodyId};
    require(surfaceCamera.inPlanetPhysicsFrame(),
        "surface wheel-speed regression must start inside a body physics frame");
    const double surfaceBefore = surfaceCamera.flightSpeedMps();
    input = {};
    input.flightSpeedSteps = 2.0;
    surfaceCamera.update(input, 1.0 / 60.0);
    require(surfaceCamera.flightSpeedMps() > surfaceBefore * 1.99
            && surfaceCamera.flightSpeedMps() < surfaceBefore * 2.01,
        "two positive wheel steps in a body physics frame must retain the original two-times scaling");
}''')

# The old 2,000 km/s production cap is retained for ACTUAL local-body motion, while the stored
# inertial travel request can now reach 1024c (4096c while sprinting). This catches accidental
# removal of either safety side of the split.
runtime_path = ROOT / "native/tests/R24RuntimeStabilityTests.cpp"
runtime_text = runtime_path.read_text(encoding="utf-8")
if "#include <glm/geometric.hpp>" not in runtime_text:
    runtime_text = runtime_text.replace(
        "#include <string_view>\n",
        "#include <string_view>\n\n#include <glm/geometric.hpp>\n",
        1)
    runtime_path.write_text(runtime_text, encoding="utf-8")

replace_function(
    "native/tests/R24RuntimeStabilityTests.cpp",
    "void testCreativeFlightConfigurationUsesProductionLimits() {",
    "void testCentrifugalAccelerationInRotatingLocalWorld() {",
    r'''void testCreativeFlightConfigurationUsesProductionLimits() {
    vf::PlanetDefinition planet{};
    planet.radius = 1000.0;
    planet.maxElevation = 0.0;
    planet.atmosphereHeight = 100.0;

    vf::PlanetCamera spaceCamera{planet};
    spaceCamera.setFlightMode(true);
    spaceCamera.setCreativeFlightSpeedMps(500000.0);
    require(spaceCamera.flightMode(),
        "runtime/editor flight configuration must enable the production flight path");
    require(!spaceCamera.grounded(), "enabling flight must release the grounded state");
    require(std::abs(spaceCamera.flightSpeedMps() - 500000.0) < 1.0e-9,
        "configured ordinary flight speed must use the exact production value");

    spaceCamera.setCreativeFlightSpeedMps(9.0e20);
    require(std::abs(spaceCamera.flightSpeedMps()
            - vf::PlanetCamera::kCreativeInterstellarBaseMaxMps) < 1.0,
        "free-space speed configuration must clamp at the authored 1024c base warp ceiling");

    vf::PlanetMovementInput thrust{};
    thrust.forward = 1.0;
    for (int frame = 0; frame < 4; ++frame) spaceCamera.update(thrust, 1.0 / 60.0);
    require(glm::length(spaceCamera.velocity()) > 2000000.0,
        "free inertial space must permit travel above the local 2,000 km/s terrain safety band");

    vf::CelestialSystem system;
    vf::CelestialBody body{};
    body.type = vf::CelestialBodyType::Planet;
    body.radiusMeters = planet.radius;
    body.massKg = 1.0e12;
    body.physicsBubbleRadiusMeters = 1.0e12;
    body.gravityInfluenceRadiusMeters = 1.0e12;
    const auto bodyId = system.addBody(body);

    vf::PlanetCamera localCamera{planet, &system, bodyId};
    localCamera.setFlightMode(true);
    localCamera.setCreativeFlightSpeedMps(vf::PlanetCamera::kCreativeInterstellarBaseMaxMps);
    require(localCamera.inPlanetPhysicsFrame(),
        "local production speed gate must remain inside the body precision frame");
    thrust = {};
    thrust.forward = 1.0;
    for (int frame = 0; frame < 240; ++frame) localCamera.update(thrust, 1.0 / 120.0);
    require(localCamera.inPlanetPhysicsFrame(),
        "large test physics bubble must keep the local-speed regression body-owned");
    require(glm::length(localCamera.velocity()) <= 2000000.0 + 1.0,
        "actual motion inside a body physics frame must preserve the production 2,000 km/s base safety cap");
}''')

print("R24 interstellar Sun closure hotfix V2 applied")
