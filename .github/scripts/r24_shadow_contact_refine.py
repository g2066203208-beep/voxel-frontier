from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# Remove the obsolete top-down camera override. The production view matrix is now explicitly
# framed around the surface-anchored contact probe each frame.
replace_once(
    "native/src/app/Main.cpp",
    """        if (const char* shadowEnv = std::getenv(\"VF_CAPTURE_SHADOW_CONTACT\");\n            shadowEnv != nullptr && std::string_view{shadowEnv} == \"1\") {\n            const glm::dvec3 groundUp = camera.up();\n            const glm::dvec3 tangentForward = safeNormalize(\n                camera.forwardDirection() - groundUp * glm::dot(camera.forwardDirection(), groundUp),\n                stableTangent(groundUp));\n            camera.setViewDirectionWorld(\n                safeNormalize(tangentForward * 0.48 - groundUp * 0.88, -groundUp),\n                groundUp);\n            std::cout << \"R24 capture shadow-contact downward view\\n\";\n        }\n\n""",
    "",
)

replace_once(
    "native/src/app/Main.cpp",
    """                const glm::dvec3 cameraDirectionPlanet = safeNormalize(cameraPlanet, patchUp);\n                const glm::dvec3 tangentPlanet = safeNormalize(\n                    forwardPlanet - cameraDirectionPlanet * glm::dot(forwardPlanet, cameraDirectionPlanet),\n                    patchZ);\n                const glm::dvec3 probeDirection = safeNormalize(\n                    cameraDirectionPlanet + tangentPlanet * (11.0 / planet.radius),\n                    cameraDirectionPlanet);\n""",
    """                const glm::dvec3 cameraDirectionPlanet = safeNormalize(cameraPlanet, patchUp);\n                const glm::dvec3 sunPlanetDirection = safeNormalize(\n                    inverseAster * sunWorldDirection, patchEast);\n                const glm::dvec3 sunHorizontalPlanet = safeNormalize(\n                    sunPlanetDirection\n                        - cameraDirectionPlanet * glm::dot(sunPlanetDirection, cameraDirectionPlanet),\n                    patchEast);\n                // Place the probe sideways relative to the incoming sunlight. Its cast shadow then\n                // travels across the image instead of directly behind the object from the camera.\n                const glm::dvec3 placementTangentPlanet = safeNormalize(\n                    glm::cross(cameraDirectionPlanet, sunHorizontalPlanet), patchZ);\n                const glm::dvec3 probeDirection = safeNormalize(\n                    cameraDirectionPlanet + placementTangentPlanet * (10.0 / planet.radius),\n                    cameraDirectionPlanet);\n""",
)

replace_once(
    "native/src/app/Main.cpp",
    """                vf::appendDebugBox(\n                    dynamicMesh, probeCenter, probeOrientation, probeHalfExtents,\n                    {0.88F, 0.43F, 0.12F}, {0.0F, 0.72F, 0.0F, 0.0F});\n                frameForwardSurface = safeNormalize(probeCenter - cameraSurface, forwardSurface);\n                frameUpSurface = upSurface;\n""",
    """                vf::appendDebugBox(\n                    dynamicMesh, probeCenter, probeOrientation, probeHalfExtents,\n                    {0.88F, 0.43F, 0.12F}, {0.0F, 0.72F, 0.0F, 0.0F});\n                const glm::dvec3 shadowDirectionSurface = safeNormalize(\n                    -(sunSurfaceDirection\n                        - probeUp * glm::dot(sunSurfaceDirection, probeUp)),\n                    {1.0, 0.0, 0.0});\n                // Aim between the caster and the first metres of its shadow so the screenshot\n                // necessarily contains the exact contact origin plus an unobstructed shadow run.\n                const glm::dvec3 proofTarget = probeCenter + shadowDirectionSurface * 3.5;\n                frameForwardSurface = safeNormalize(proofTarget - cameraSurface, forwardSurface);\n                frameUpSurface = upSurface;\n""",
)

print("R24 shadow-contact framing refined")
