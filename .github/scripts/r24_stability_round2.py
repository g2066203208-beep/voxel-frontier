#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel, text):
    (ROOT / rel).write_text(text, encoding="utf-8")


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"missing replacement anchor: {label}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# PlanetCamera: expose normal runtime/editor controls for deterministic capture and
# future save/load. These do not create a render-only fake path.
# ---------------------------------------------------------------------------
header_path = "native/include/vf/player/PlanetCamera.hpp"
header = read(header_path)
header = replace_once(
    header,
    "#include <cstdint>\n",
    "#include <algorithm>\n#include <cstdint>\n",
    "camera algorithm include",
)
header = replace_once(
    header,
    "    [[nodiscard]] double flightSpeedMps() const noexcept { return creativeFlightSpeedMps_; }\n",
    "    [[nodiscard]] double flightSpeedMps() const noexcept { return creativeFlightSpeedMps_; }\n"
    "    void setFlightMode(bool enabled) noexcept {\n"
    "        flightMode_ = enabled;\n"
    "        grounded_ = false;\n"
    "        if (enabled) {\n"
    "            if (inPhysicsFrame_) localVelocity_ = {};\n"
    "            else velocity_ = {};\n"
    "        }\n"
    "    }\n"
    "    void setCreativeFlightSpeedMps(double speedMetersPerSecond) noexcept {\n"
    "        creativeFlightSpeedMps_ = std::clamp(speedMetersPerSecond, 1.0, 2000000.0);\n"
    "    }\n",
    "camera flight configuration API",
)
write(header_path, header)


# ---------------------------------------------------------------------------
# Main: deterministic evidence hooks still run the exact production camera/movement,
# renderer and streaming code. They only set initial state/view and enable stdout
# diagnostics so CI can prove the high-speed fallback actually happened.
# ---------------------------------------------------------------------------
main_path = "native/src/app/Main.cpp"
main = read(main_path)
main = replace_once(
    main,
    "        vf::PlanetCamera camera{planet, &celestial, asterId, spawnDirection};\n",
    "        vf::PlanetCamera camera{planet, &celestial, asterId, spawnDirection};\n"
    "        const bool captureHighSpeed = [] {\n"
    "            const char* value = std::getenv(\"VF_CAPTURE_HIGH_SPEED\");\n"
    "            return value != nullptr && std::string_view{value} == \"1\";\n"
    "        }();\n"
    "        const bool runtimeDiagnosticsStdout = [] {\n"
    "            const char* value = std::getenv(\"VF_RUNTIME_DIAGNOSTICS\");\n"
    "            return value != nullptr && std::string_view{value} == \"1\";\n"
    "        }();\n"
    "        if (captureHighSpeed) {\n"
    "            camera.setFlightMode(true);\n"
    "            camera.setCreativeFlightSpeedMps(500000.0);\n"
    "            std::cout << \"R24 capture high-speed initial_speed_mps=500000\\n\";\n"
    "        }\n",
    "high speed capture initial state",
)

main = replace_once(
    main,
    "        std::string celestialTargetMode{};\n",
    "        if (const char* shadowEnv = std::getenv(\"VF_CAPTURE_SHADOW_CONTACT\");\n"
    "            shadowEnv != nullptr && std::string_view{shadowEnv} == \"1\") {\n"
    "            const glm::dvec3 groundUp = camera.up();\n"
    "            const glm::dvec3 tangentForward = safeNormalize(\n"
    "                camera.forwardDirection() - groundUp * glm::dot(camera.forwardDirection(), groundUp),\n"
    "                stableTangent(groundUp));\n"
    "            camera.setViewDirectionWorld(\n"
    "                safeNormalize(tangentForward * 0.48 - groundUp * 0.88, -groundUp),\n"
    "                groundUp);\n"
    "            std::cout << \"R24 capture shadow-contact downward view\\n\";\n"
    "        }\n\n"
    "        std::string celestialTargetMode{};\n",
    "shadow contact capture view",
)

main = replace_once(
    main,
    "                platform.setWindowTitle(title.str());\n",
    "                platform.setWindowTitle(title.str());\n"
    "                if (runtimeDiagnosticsStdout)\n"
    "                    std::cout << \"R24 DIAG | \" << title.str() << '\\n';\n",
    "runtime diagnostics stdout",
)
write(main_path, main)


# ---------------------------------------------------------------------------
# Stability tests: ensure the editor/runtime configuration hook cannot silently
# clamp to the wrong scale or leave the camera grounded.
# ---------------------------------------------------------------------------
test_path = "native/tests/R24RuntimeStabilityTests.cpp"
test = read(test_path)
test = replace_once(
    test,
    '#include "vf/physics/PhysicsWorld.hpp"\n',
    '#include "vf/physics/PhysicsWorld.hpp"\n#include "vf/player/PlanetCamera.hpp"\n',
    "runtime camera test include",
)
insert = r'''
void testCreativeFlightConfigurationUsesProductionLimits() {
    vf::PlanetDefinition planet{};
    planet.radius = 1000.0;
    planet.maxElevation = 0.0;
    vf::PlanetCamera camera{planet};
    camera.setFlightMode(true);
    camera.setCreativeFlightSpeedMps(500000.0);
    require(camera.flightMode(), "runtime/editor flight configuration must enable the production flight path");
    require(!camera.grounded(), "enabling flight must release the grounded state");
    require(std::abs(camera.flightSpeedMps() - 500000.0) < 1.0e-9,
        "configured high-speed capture must use the same production speed value");
    camera.setCreativeFlightSpeedMps(9.0e9);
    require(std::abs(camera.flightSpeedMps() - 2000000.0) < 1.0e-9,
        "runtime/editor speed configuration must preserve the production 2,000 km/s clamp");
}
'''
test = replace_once(
    test,
    "void testCentrifugalAccelerationInRotatingLocalWorld() {",
    insert + "\nvoid testCentrifugalAccelerationInRotatingLocalWorld() {",
    "creative flight stability test",
)
test = replace_once(
    test,
    "int main() {\n    testCentrifugalAccelerationInRotatingLocalWorld();",
    "int main() {\n    testCreativeFlightConfigurationUsesProductionLimits();\n"
    "    testCentrifugalAccelerationInRotatingLocalWorld();",
    "creative flight test invocation",
)
write(test_path, test)

print("R24 stability round2 staged successfully")
