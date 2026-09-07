from pathlib import Path

MAIN = Path("native/src/app/Main.cpp")
text = MAIN.read_text(encoding="utf-8")

capture_block = """        const bool captureHighSpeed = [] {\n            const char* value = std::getenv(\"VF_CAPTURE_HIGH_SPEED\");\n            return value != nullptr && std::string_view{value} == \"1\";\n        }();\n        const bool runtimeDiagnosticsStdout = [] {\n            const char* value = std::getenv(\"VF_RUNTIME_DIAGNOSTICS\");\n            return value != nullptr && std::string_view{value} == \"1\";\n        }();\n        if (captureHighSpeed) {\n            camera.setFlightMode(true);\n            camera.setCreativeFlightSpeedMps(500000.0);\n            std::cout << \"R24 capture high-speed initial_speed_mps=500000\\n\";\n        }\n"""

# Historical migration workflows inserted this capture-only block multiple times. Keep exactly one
# declaration so the real runtime can compile before contact-shadow evidence is attempted.
count = text.count(capture_block)
if count < 1:
    raise SystemExit("Main.cpp: capture state block missing")
if count > 1:
    first = text.find(capture_block)
    prefix = text[: first + len(capture_block)]
    suffix = text[first + len(capture_block) :].replace(capture_block, "")
    text = prefix + suffix

old_placement = """                const glm::dvec3 cameraDirectionPlanet = safeNormalize(cameraPlanet, patchUp);\n                const glm::dvec3 tangentPlanet = safeNormalize(\n                    forwardPlanet - cameraDirectionPlanet * glm::dot(forwardPlanet, cameraDirectionPlanet),\n                    patchZ);\n                const glm::dvec3 probeDirection = safeNormalize(\n                    cameraDirectionPlanet + tangentPlanet * (11.0 / planet.radius),\n                    cameraDirectionPlanet);\n"""
new_placement = """                const glm::dvec3 cameraDirectionPlanet = safeNormalize(cameraPlanet, patchUp);\n                const glm::dvec3 sunPlanetDirection = safeNormalize(\n                    inverseAster * sunWorldDirection, patchEast);\n                const glm::dvec3 sunHorizontalPlanet = safeNormalize(\n                    sunPlanetDirection\n                        - cameraDirectionPlanet * glm::dot(sunPlanetDirection, cameraDirectionPlanet),\n                    patchEast);\n                // Put the proof object sideways to sunlight so its shadow cannot hide directly\n                // behind the caster from the camera. This affects capture mode only.\n                const glm::dvec3 placementTangentPlanet = safeNormalize(\n                    glm::cross(cameraDirectionPlanet, sunHorizontalPlanet), patchZ);\n                const glm::dvec3 probeDirection = safeNormalize(\n                    cameraDirectionPlanet + placementTangentPlanet * (10.0 / planet.radius),\n                    cameraDirectionPlanet);\n"""
if old_placement in text:
    text = text.replace(old_placement, new_placement, 1)
elif "placementTangentPlanet" not in text:
    raise SystemExit("Main.cpp: contact-probe placement anchor missing")

old_aim = """                vf::appendDebugBox(\n                    dynamicMesh, probeCenter, probeOrientation, probeHalfExtents,\n                    {0.88F, 0.43F, 0.12F}, {0.0F, 0.72F, 0.0F, 0.0F});\n                frameForwardSurface = safeNormalize(probeCenter - cameraSurface, forwardSurface);\n                frameUpSurface = upSurface;\n"""
new_aim = """                vf::appendDebugBox(\n                    dynamicMesh, probeCenter, probeOrientation, probeHalfExtents,\n                    {0.88F, 0.43F, 0.12F}, {0.0F, 0.72F, 0.0F, 0.0F});\n                const glm::dvec3 shadowDirectionSurface = safeNormalize(\n                    -(sunSurfaceDirection\n                        - probeUp * glm::dot(sunSurfaceDirection, probeUp)),\n                    {1.0, 0.0, 0.0});\n                // Aim between the caster base and the first metres of shadow. The screenshot must\n                // contain the exact object-ground junction and the shadow origin in the same frame.\n                const glm::dvec3 proofTarget = probeCenter + shadowDirectionSurface * 3.5;\n                frameForwardSurface = safeNormalize(proofTarget - cameraSurface, forwardSurface);\n                frameUpSurface = upSurface;\n"""
if old_aim in text:
    text = text.replace(old_aim, new_aim, 1)
elif "shadowDirectionSurface" not in text:
    raise SystemExit("Main.cpp: contact-probe aim anchor missing")

MAIN.write_text(text, encoding="utf-8")
print(f"R24 shadow repair applied; duplicate capture blocks before cleanup={count}")
