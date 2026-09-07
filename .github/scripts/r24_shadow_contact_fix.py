from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one anchor, found {count}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "native/src/render/VulkanRenderer.cpp",
    """    shadowRaster.depthBiasConstantFactor = 0.55F;\n    shadowRaster.depthBiasSlopeFactor = 1.00F;\n""",
    """    // Keep caster bias deliberately small. The previous values visibly separated long\n    // low-sun shadows from tree/prop contact points (classic peter-panning). Receiver-side bias\n    // below handles the remaining acne with a tightly bounded physical-scale offset.\n    shadowRaster.depthBiasConstantFactor = 0.18F;\n    shadowRaster.depthBiasSlopeFactor = 0.45F;\n""",
)

replace_once(
    "native/shaders/planet.slang",
    """    // Raster depth bias already handles most acne. Keep receiver bias at centimetre-scale\n    // for the 480 m shadow depth range so contact shadows do not visibly detach.\n    float bias = max(0.00004, 0.00030 * (1.0 - noL));\n""",
    """    // Raster bias handles polygon acne. Bound receiver bias to roughly 0.6--3.2 cm over\n    // the 480 m orthographic shadow range; the old grazing-angle term reached ~14 cm and produced\n    // visible peter-panning under trees and props.\n    float bias = 0.000012 + 0.000055 * (1.0 - saturate(noL));\n""",
)

replace_once(
    "native/src/app/Main.cpp",
    """        if (const char* shadowEnv = std::getenv(\"VF_CAPTURE_SHADOW_CONTACT\");\n            shadowEnv != nullptr && std::string_view{shadowEnv} == \"1\") {\n            const glm::dvec3 groundUp = camera.up();\n            const glm::dvec3 tangentForward = safeNormalize(\n                camera.forwardDirection() - groundUp * glm::dot(camera.forwardDirection(), groundUp),\n                stableTangent(groundUp));\n            camera.setViewDirectionWorld(\n                safeNormalize(tangentForward * 0.48 - groundUp * 0.88, -groundUp),\n                groundUp);\n            std::cout << \"R24 capture shadow-contact downward view\\n\";\n        }\n""",
    """        const bool shadowContactCapture = [] {\n            const char* shadowEnv = std::getenv(\"VF_CAPTURE_SHADOW_CONTACT\");\n            return shadowEnv != nullptr && std::string_view{shadowEnv} == \"1\";\n        }();\n        if (shadowContactCapture) {\n            // Do not use the old near-vertical evidence camera: it hid the exact contact point.\n            // The per-frame capture probe below is placed on PlanetSurfaceAuthority and the camera\n            // is aimed at its base from ordinary eye height, exposing even centimetre-scale gaps.\n            std::cout << \"R24 capture shadow-contact low-angle production view\\n\";\n        }\n""",
)

replace_once(
    "native/src/app/Main.cpp",
    """            vf::PlanetMesh dynamicMesh{};\n            if (currentMoon != nullptr) {\n""",
    """            glm::dvec3 frameForwardSurface = forwardSurface;\n            glm::dvec3 frameUpSurface = upSurface;\n            vf::PlanetMesh dynamicMesh{};\n            if (shadowContactCapture) {\n                // Deterministic contact probe rendered through the *production* shadow-map pass.\n                // Its lower face is exactly tangent to the same authoritative surface used by\n                // terrain/collision, so any visible gap is a shadow-bias error rather than a\n                // placement ambiguity. This geometry exists only when the CI capture flag is set.\n                const glm::dvec3 cameraDirectionPlanet = safeNormalize(cameraPlanet, patchUp);\n                const glm::dvec3 tangentPlanet = safeNormalize(\n                    forwardPlanet - cameraDirectionPlanet * glm::dot(forwardPlanet, cameraDirectionPlanet),\n                    patchZ);\n                const glm::dvec3 probeDirection = safeNormalize(\n                    cameraDirectionPlanet + tangentPlanet * (11.0 / planet.radius),\n                    cameraDirectionPlanet);\n                const vf::PlanetSurfaceSample probeSurface = surfaceAuthority.sampleSurface(probeDirection);\n                const glm::dvec3 probeBase = toSurfacePoint(probeSurface.position);\n                const glm::dvec3 probeUp = safeNormalize(\n                    toSurfaceVector(probeSurface.normal), {0.0, 1.0, 0.0});\n                const glm::dvec3 localY{0.0, 1.0, 0.0};\n                const double upDot = std::clamp(glm::dot(localY, probeUp), -1.0, 1.0);\n                glm::dquat probeOrientation{1.0, 0.0, 0.0, 0.0};\n                if (upDot < 0.999999) {\n                    const glm::dvec3 axis = safeNormalize(glm::cross(localY, probeUp), {1.0, 0.0, 0.0});\n                    probeOrientation = glm::angleAxis(std::acos(upDot), axis);\n                }\n                const glm::dvec3 probeHalfExtents{0.75, 1.50, 0.75};\n                const glm::dvec3 probeCenter = probeBase + probeUp * probeHalfExtents.y;\n                vf::appendDebugBox(\n                    dynamicMesh, probeCenter, probeOrientation, probeHalfExtents,\n                    {0.88F, 0.43F, 0.12F}, {0.0F, 0.72F, 0.0F, 0.0F});\n                frameForwardSurface = safeNormalize(probeCenter - cameraSurface, forwardSurface);\n                frameUpSurface = upSurface;\n                if (runtimeDiagnosticsStdout) {\n                    std::cout << \"R24 shadow-contact probe base_y=\" << probeBase.y\n                              << \" center_y=\" << probeCenter.y\n                              << \" half_height=\" << probeHalfExtents.y << '\\n';\n                }\n            }\n            if (currentMoon != nullptr) {\n""",
)

replace_once(
    "native/src/app/Main.cpp",
    """            const glm::mat4 viewProjection = makeReverseZViewProjection(\n                forwardSurface, upSurface, aspect);\n""",
    """            const glm::mat4 viewProjection = makeReverseZViewProjection(\n                frameForwardSurface, frameUpSurface, aspect);\n""",
)

replace_once(
    "native/src/app/Main.cpp",
    """            renderEnvironment.cameraForward = glm::vec3(forwardSurface);\n""",
    """            renderEnvironment.cameraForward = glm::vec3(frameForwardSurface);\n""",
)

replace_once(
    ".github/scripts/r24_stability_capture.sh",
    """# 2) Deterministic downward production-camera view for contact-shadow and ecology placement.\nstart_app \"$OUT/logs/shadow-contact.log\" \\\n  VF_CELESTIAL_TIME_SCALE=1 VF_CAPTURE_SHADOW_CONTACT=1 VF_RUNTIME_DIAGNOSTICS=1\ncapture_frame \"$OUT/shadows/contact-ground.png\"\nstop_app\n""",
    """# 2) Low-angle contact-shadow proof. A deterministic production-rendered box is placed with\n# its bottom face exactly on PlanetSurfaceAuthority. Side views expose peter-panning directly.\nstart_app \"$OUT/logs/shadow-contact.log\" \\\n  VF_CELESTIAL_TIME_SCALE=1 VF_CAPTURE_SHADOW_CONTACT=1 VF_RUNTIME_DIAGNOSTICS=1\ncapture_frame \"$OUT/shadows/contact-side.png\" 512 40\nsleep 1.0\ncapture_frame \"$OUT/shadows/contact-side-late.png\" 512 20\nstop_app\nmontage \"$OUT/shadows/contact-side.png\" \"$OUT/shadows/contact-side-late.png\" \\\n  -tile 2x1 -geometry 800x450+6+6 \"$OUT/shadows/contact-side-montage.png\"\n""",
)

replace_once(
    ".github/scripts/r24_stability_capture.sh",
    """montage \"$OUT/ground/ground-spin-montage.png\" \"$OUT/shadows/contact-ground.png\" \\\n        \"$OUT/space/earth-spin-montage.png\" \"$OUT/high-speed/transit.png\" \\\n""",
    """montage \"$OUT/ground/ground-spin-montage.png\" \"$OUT/shadows/contact-side-montage.png\" \\\n        \"$OUT/space/earth-spin-montage.png\" \"$OUT/high-speed/transit.png\" \\\n""",
)

replace_once(
    ".github/scripts/r24_stability_capture.sh",
    """- shadows/contact-ground.png: downward ordinary-time contact-shadow/ecology placement inspection.\n""",
    """- shadows/contact-side*.png: low-angle production shadow-map proof; the orange probe's bottom\n  face is placed exactly on PlanetSurfaceAuthority, making any contact gap directly visible.\n""",
)

print("R24 focused contact-shadow patch applied")
