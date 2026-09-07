#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def patch(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"anchor not found in {path}: {old[:100]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# A physical Moon screenshot must actually be taken from a location where the Moon is above the
# horizon. The old evidence mode only aimed the camera at Luna from the ordinary spawn; depending on
# epoch the planet itself could occlude it. Put the ordinary PlanetCamera on a deterministic Aster
# surface point 60 degrees away from the sub-lunar point, which gives ~30 deg lunar elevation and
# keeps terrain/horizon in the same frame.
patch(
    "native/src/app/Main.cpp",
    """        vf::CelestialPhysicsFrame asterFrame{asterId};\n\n        if (captureSunTransit) {\n""",
    """        vf::CelestialPhysicsFrame asterFrame{asterId};\n        glm::dvec3 moonEvidenceObserverLocalDirection{};\n        bool moonEvidenceObserverPlaced = false;\n        if (trackMoonEvidence) {\n            const glm::dquat inverseInitialAster = glm::conjugate(\n                glm::normalize(initialAster->orientation));\n            const glm::dvec3 moonWorldDirection = safeNormalize(\n                luna.position - initialAster->position, {1.0, 0.0, 0.0});\n            const glm::dvec3 moonLocalDirection = safeNormalize(\n                inverseInitialAster * moonWorldDirection, {1.0, 0.0, 0.0});\n            const glm::dvec3 moonHorizonTangent = stableTangent(moonLocalDirection);\n            constexpr double observerSeparationRadians = 60.0 * kPi / 180.0;\n            moonEvidenceObserverLocalDirection = safeNormalize(\n                moonLocalDirection * std::cos(observerSeparationRadians)\n                    + moonHorizonTangent * std::sin(observerSeparationRadians),\n                moonLocalDirection);\n            const double observerRadius = vf::planetSurfaceRadius(\n                planet, moonEvidenceObserverLocalDirection) + 2.0;\n            const glm::dvec3 observerLocalPosition =\n                moonEvidenceObserverLocalDirection * observerRadius;\n            const glm::dvec3 observerWorldPosition =\n                asterFrame.toWorldPosition(*initialAster, observerLocalPosition);\n            const glm::dvec3 observerWorldUp = safeNormalize(\n                initialAster->orientation * moonEvidenceObserverLocalDirection);\n            camera.setExternalWorldState(\n                observerWorldPosition,\n                asterFrame.toWorldVelocity(\n                    *initialAster, observerLocalPosition, glm::dvec3{}),\n                false);\n            camera.setViewDirectionWorld(luna.position - observerWorldPosition, observerWorldUp);\n            moonEvidenceObserverPlaced = true;\n            std::cout << \"R24 moon ground observer: target_elevation_deg=30\"\n                      << \" surface_offset_m=2\\n\";\n        }\n\n        if (captureSunTransit) {\n""",
)

# After regional hydrology becomes authoritative, snap the evidence eye back onto that exact surface
# rather than leaving the camera at the pre-incision base terrain height.
patch(
    "native/src/app/Main.cpp",
    """        surfaceAuthority.setHydrology(initialTerrain.hydrology);\n        vf::PlanetLodStats currentLodStats = initialTerrain.stats;\n""",
    """        surfaceAuthority.setHydrology(initialTerrain.hydrology);\n        if (moonEvidenceObserverPlaced) {\n            const double exactObserverRadius = surfaceAuthority.surfaceRadius(\n                moonEvidenceObserverLocalDirection) + 2.0;\n            const glm::dvec3 exactObserverLocalPosition =\n                moonEvidenceObserverLocalDirection * exactObserverRadius;\n            const glm::dvec3 exactObserverWorldPosition =\n                asterFrame.toWorldPosition(*initialAster, exactObserverLocalPosition);\n            const glm::dvec3 exactObserverWorldUp = safeNormalize(\n                initialAster->orientation * moonEvidenceObserverLocalDirection);\n            camera.setExternalWorldState(\n                exactObserverWorldPosition,\n                asterFrame.toWorldVelocity(\n                    *initialAster, exactObserverLocalPosition, glm::dvec3{}),\n                false);\n            camera.setViewDirectionWorld(\n                luna.position - exactObserverWorldPosition, exactObserverWorldUp);\n            std::cout << \"R24 moon ground observer authoritative_surface=1\\n\";\n        }\n        vf::PlanetLodStats currentLodStats = initialTerrain.stats;\n""",
)

# Keep the Moon physically tracked during evidence capture but aim the framebuffer a few degrees to
# one side. At true Earth-Moon scale Luna is only about 6 pixels across at 900p; centering it exactly
# under the 22-pixel HUD crosshair made the Moon invisible even though it was rendered correctly.
# The Moon geometry remains at its real position and size; only the evidence camera framing changes.
patch(
    "native/src/app/Main.cpp",
    """            if (currentMoon != nullptr) {\n                const double moonCameraDistance = glm::length(currentMoon->position - camera.position());\n""",
    """            if (trackMoonEvidence && currentMoon != nullptr) {\n                const glm::dvec3 liveMoonWorldDirection = safeNormalize(\n                    currentMoon->position - camera.position());\n                const glm::dvec3 moonSurfaceDirection = safeNormalize(\n                    toSurfaceVector(inverseAster * liveMoonWorldDirection), forwardSurface);\n                glm::dvec3 moonScreenRight = glm::cross(moonSurfaceDirection, upSurface);\n                moonScreenRight = safeNormalize(moonScreenRight, {1.0, 0.0, 0.0});\n                constexpr double moonEvidenceFrameOffset = 3.5 * kPi / 180.0;\n                frameForwardSurface = safeNormalize(\n                    moonSurfaceDirection * std::cos(moonEvidenceFrameOffset)\n                        - moonScreenRight * std::sin(moonEvidenceFrameOffset),\n                    forwardSurface);\n                frameUpSurface = upSurface;\n            }\n            if (currentMoon != nullptr) {\n                const double moonCameraDistance = glm::length(currentMoon->position - camera.position());\n""",
)

# Warp is allowed to be fantastically fast in free space, but once the requested closing-speed cap
# drops, do not let the exponential input smoother retain a superluminal residual that tunnels past
# the target. Clamp only the component along the active travel direction; lateral/orbital carrier
# motion remains untouched.
patch(
    "native/src/player/PlanetCamera.cpp",
    """            inertialFlightControlVelocity_ +=\n                (desiredControl - inertialFlightControlVelocity_) * (1.0 - std::exp(-7.0 * dt));\n            velocity_ = inertialFlightCarrierVelocity_ + inertialFlightControlVelocity_;\n""",
    """            inertialFlightControlVelocity_ +=\n                (desiredControl - inertialFlightControlVelocity_) * (1.0 - std::exp(-7.0 * dt));\n            if (moveLength > 1.0e-8) {\n                const glm::dvec3 travelDirection = safeNormalize(move);\n                const double retainedClosingSpeed = glm::dot(\n                    inertialFlightControlVelocity_, travelDirection);\n                if (retainedClosingSpeed > targetSpeed)\n                    inertialFlightControlVelocity_ -= travelDirection\n                        * (retainedClosingSpeed - targetSpeed);\n            }\n            velocity_ = inertialFlightCarrierVelocity_ + inertialFlightControlVelocity_;\n""",
)

print("R24 interstellar Sun closure hotfix V3 applied")
