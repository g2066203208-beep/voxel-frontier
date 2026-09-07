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
# Render-only celestial prediction: the authoritative N-body state remains fixed-step/double.
# Rendering advances each body's translation by v*pending and its constant spin analytically.
# This removes visible stair-stepping without feeding extrapolated data back into physics.
# ---------------------------------------------------------------------------
predict_path = ROOT / "native/include/vf/world/CelestialRenderState.hpp"
predict_path.write_text(r'''#pragma once

#include "vf/world/CelestialSystem.hpp"

#include <algorithm>
#include <cmath>

#include <glm/geometric.hpp>
#include <glm/gtc/quaternion.hpp>

namespace vf {

struct CelestialRenderState {
    glm::dvec3 position{};
    glm::dvec3 linearVelocity{};
    glm::dquat orientation{1.0, 0.0, 0.0, 0.0};
};

[[nodiscard]] inline CelestialRenderState predictCelestialRenderState(
    const CelestialBody& body,
    double pendingSimulationSeconds) noexcept {
    const double dt = std::isfinite(pendingSimulationSeconds)
        ? std::max(0.0, pendingSimulationSeconds)
        : 0.0;

    CelestialRenderState result{};
    result.position = body.position + body.linearVelocity * dt;
    result.linearVelocity = body.linearVelocity;
    result.orientation = glm::normalize(body.orientation);

    if (dt <= 0.0 || std::abs(body.spinRateRadPerSecond) <= 1.0e-15) return result;
    const double axisLengthSquared = glm::dot(body.spinAxis, body.spinAxis);
    if (axisLengthSquared <= 1.0e-24) return result;
    const glm::dvec3 axis = body.spinAxis / std::sqrt(axisLengthSquared);
    const glm::dquat delta = glm::angleAxis(body.spinRateRadPerSecond * dt, axis);
    result.orientation = glm::normalize(delta * result.orientation);
    return result;
}

} // namespace vf
''', encoding="utf-8")


main_path = "native/src/app/Main.cpp"
main = read(main_path)
main = replace_once(
    main,
    '#include "vf/world/CelestialPhysicsFrame.hpp"\n',
    '#include "vf/world/CelestialPhysicsFrame.hpp"\n#include "vf/world/CelestialRenderState.hpp"\n',
    "celestial render state include",
)

# Better contact-shadow framing: see object bases and projected shadows together.
main = replace_once(
    main,
    "                safeNormalize(tangentForward * 0.48 - groundUp * 0.88, -groundUp),",
    "                safeNormalize(tangentForward * 0.82 - groundUp * 0.57, -groundUp),",
    "shadow capture angle",
)
main = replace_once(
    main,
    '            std::cout << "R24 capture shadow-contact downward view\\n";',
    '            std::cout << "R24 capture shadow-contact oblique view\\n";',
    "shadow capture diagnostic",
)

# Terrain build wall-time instrumentation.
main = replace_once(
    main,
    "            vf::PlanetLodStats stats{};\n        };",
    "            vf::PlanetLodStats stats{};\n            double buildMilliseconds{};\n        };",
    "terrain build timing field",
)
main = replace_once(
    main,
    "        auto buildTerrainLod = [&](const glm::dvec3& centerDirection, const glm::dvec3& cameraPlanetLocal) {\n"
    "            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);",
    "        auto buildTerrainLod = [&](const glm::dvec3& centerDirection, const glm::dvec3& cameraPlanetLocal) {\n"
    "            const auto buildStarted = std::chrono::steady_clock::now();\n"
    "            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);",
    "terrain build timing start",
)
main = replace_once(
    main,
    "            appendMesh(result.mesh, oceanProxy);\n            return result;",
    "            appendMesh(result.mesh, oceanProxy);\n"
    "            result.buildMilliseconds = std::chrono::duration<double, std::milli>(\n"
    "                std::chrono::steady_clock::now() - buildStarted).count();\n"
    "            return result;",
    "terrain build timing finish",
)
main = replace_once(
    main,
    "        vf::PlanetMesh nearTerrain = std::move(initialTerrain.mesh);",
    "        std::cout << \"R24 initial terrain build_ms=\" << std::fixed << std::setprecision(1)\n"
    "                  << initialTerrain.buildMilliseconds << \" leaf=\" << initialTerrain.stats.leafPatches\n"
    "                  << \" tris=\" << initialTerrain.mesh.triangleCount() << '\\n';\n"
    "        vf::PlanetMesh nearTerrain = std::move(initialTerrain.mesh);",
    "initial terrain timing log",
)

# High-speed recovery state.
main = replace_once(
    main,
    "        double lodCooldown = 0.0;\n",
    "        double lodCooldown = 0.0;\n        double highSpeedRecoverySeconds = 0.0;\n",
    "high speed recovery state",
)

# Predict render states after authoritative celestial fixed-step advance.
main = replace_once(
    main,
    "            if (currentAster == nullptr || currentSun == nullptr) continue;\n"
    "            currentAster->atmosphere.prevailingWind = {};",
    "            if (currentAster == nullptr || currentSun == nullptr) continue;\n"
    "            const double celestialRenderLeadSeconds = celestialClock.pendingSeconds();\n"
    "            const vf::CelestialRenderState renderAster = vf::predictCelestialRenderState(\n"
    "                *currentAster, celestialRenderLeadSeconds);\n"
    "            const vf::CelestialRenderState renderSun = vf::predictCelestialRenderState(\n"
    "                *currentSun, celestialRenderLeadSeconds);\n"
    "            const vf::CelestialRenderState renderMoon = currentMoon != nullptr\n"
    "                ? vf::predictCelestialRenderState(*currentMoon, celestialRenderLeadSeconds)\n"
    "                : vf::CelestialRenderState{};\n"
    "            const vf::CelestialRenderState renderCinder = currentCinder != nullptr\n"
    "                ? vf::predictCelestialRenderState(*currentCinder, celestialRenderLeadSeconds)\n"
    "                : vf::CelestialRenderState{};\n"
    "            currentAster->atmosphere.prevailingWind = {};",
    "celestial render prediction states",
)

# External evidence camera follows predicted center so orbit translation doesn't create a false wobble.
main = replace_once(
    main,
    "                    currentAster->position + observerOffset, currentAster->linearVelocity, false);",
    "                    renderAster.position + observerOffset, renderAster.linearVelocity, false);",
    "earth globe predicted observer",
)

# Remove current render-coordinate block; it will be rebuilt after streaming selects near/far mode.
main = replace_once(
    main,
    "            const glm::dvec3 cameraSurface = toSurfacePoint(cameraPlanet);\n"
    "            const glm::dvec3 forwardPlanet = safeNormalize(\n"
    "                inverseAster * camera.forwardDirection(), {0.0, 0.0, -1.0});\n"
    "            const glm::dvec3 forwardSurface = safeNormalize(\n"
    "                toSurfaceVector(forwardPlanet), {0.0, 0.0, -1.0});\n"
    "            const glm::dvec3 upSurface = safeNormalize(\n"
    "                toSurfaceVector(inverseAster * camera.up()), {0.0, 1.0, 0.0});\n\n",
    "",
    "defer render coordinates until streaming mode known",
)

# Streaming recovery hysteresis: fast flight arms 2.5 s during which no expensive build starts.
main = replace_once(
    main,
    "            const double localSurfaceSpeed = glm::length(localCameraVelocity);\n"
    "            const vf::TerrainStreamingDecision streaming = vf::decideTerrainStreaming({\n"
    "                camera.physicsFrameBodyId() == asterId,\n"
    "                altitude,\n"
    "                localSurfaceSpeed,\n"
    "                arcDistance,\n"
    "                terrainBuildInFlight,\n"
    "                lodCooldown,\n"
    "            });",
    "            const double localSurfaceSpeed = glm::length(localCameraVelocity);\n"
    "            const bool onPrimaryPlanet = camera.physicsFrameBodyId() == asterId;\n"
    "            const vf::TerrainStreamingDecision streamingProbe = vf::decideTerrainStreaming({\n"
    "                onPrimaryPlanet, altitude, localSurfaceSpeed, arcDistance,\n"
    "                terrainBuildInFlight, lodCooldown});\n"
    "            if (onPrimaryPlanet && altitude < 800000.0\n"
    "                && localSurfaceSpeed > streamingProbe.detailedSpeedLimitMetersPerSecond) {\n"
    "                highSpeedRecoverySeconds = 2.5;\n"
    "            } else {\n"
    "                highSpeedRecoverySeconds = std::max(0.0, highSpeedRecoverySeconds - dt);\n"
    "            }\n"
    "            const double effectiveStreamingCooldown = std::max(\n"
    "                lodCooldown, highSpeedRecoverySeconds);\n"
    "            const vf::TerrainStreamingDecision streaming = vf::decideTerrainStreaming({\n"
    "                onPrimaryPlanet, altitude, localSurfaceSpeed, arcDistance,\n"
    "                terrainBuildInFlight, effectiveStreamingCooldown});",
    "high speed recovery policy",
)

# Log expensive build cost and restore render coordinates with predicted celestial frame when far.
insert_anchor = "            const glm::dvec3 sunWorldDirection = safeNormalize(\n                currentSun->position - camera.position());"
insert_replacement = r'''            const bool usePredictedBodyRenderFrame = usingDistantEarthGlobe
                || camera.physicsFrameBodyId() != asterId;
            const glm::dquat celestialInverseAster = glm::conjugate(
                glm::normalize(renderAster.orientation));
            const glm::dquat renderFrameInverseAster = usePredictedBodyRenderFrame
                ? celestialInverseAster
                : inverseAster;
            const glm::dvec3 renderFrameAsterPosition = usePredictedBodyRenderFrame
                ? renderAster.position
                : currentAster->position;
            const glm::dvec3 cameraPlanetRender = renderFrameInverseAster
                * (camera.position() - renderFrameAsterPosition);
            const glm::dvec3 cameraSurface = toSurfacePoint(cameraPlanetRender);
            const glm::dvec3 forwardPlanet = safeNormalize(
                renderFrameInverseAster * camera.forwardDirection(), {0.0, 0.0, -1.0});
            const glm::dvec3 forwardSurface = safeNormalize(
                toSurfaceVector(forwardPlanet), {0.0, 0.0, -1.0});
            const glm::dvec3 upSurface = safeNormalize(
                toSurfaceVector(renderFrameInverseAster * camera.up()), {0.0, 1.0, 0.0});

            const glm::dvec3 sunWorldDirection = safeNormalize(
                renderSun.position - camera.position());'''
main = replace_once(main, insert_anchor, insert_replacement, "predicted render frame")

# Celestial direction in body-local render sky uses predicted Aster spin even when ground is current.
main = replace_once(
    main,
    "                toSurfaceVector(inverseAster * sunWorldDirection), {0.3, 0.8, -0.2});",
    "                toSurfaceVector(celestialInverseAster * sunWorldDirection), {0.3, 0.8, -0.2});",
    "predicted sun body-local direction",
)

# Moon render prediction.
main = replace_once(
    main,
    "                const double moonCameraDistance = glm::length(currentMoon->position - camera.position());",
    "                const double moonCameraDistance = glm::length(renderMoon.position - camera.position());",
    "predicted moon distance",
)
main = replace_once(
    main,
    "                const glm::dvec3 moonRelativeWorld = currentMoon->position - currentAster->position;\n"
    "                for (auto& vertex : moonMesh.vertices) {\n"
    "                    const glm::dvec3 moonBodyPoint = currentMoon->orientation * glm::dvec3(vertex.position);\n"
    "                    const glm::dvec3 pointAsterLocal = inverseAster * (moonRelativeWorld + moonBodyPoint);\n"
    "                    const glm::dvec3 normalAsterLocal = inverseAster\n"
    "                        * (currentMoon->orientation * glm::dvec3(vertex.normal));",
    "                const glm::dvec3 moonRelativeWorld = renderMoon.position - renderAster.position;\n"
    "                for (auto& vertex : moonMesh.vertices) {\n"
    "                    const glm::dvec3 moonBodyPoint = renderMoon.orientation * glm::dvec3(vertex.position);\n"
    "                    const glm::dvec3 pointAsterLocal = celestialInverseAster * (moonRelativeWorld + moonBodyPoint);\n"
    "                    const glm::dvec3 normalAsterLocal = celestialInverseAster\n"
    "                        * (renderMoon.orientation * glm::dvec3(vertex.normal));",
    "predicted moon transform",
)

# Cinder predicted direction/distance.
main = replace_once(
    main,
    "                    currentCinder->position - camera.position());",
    "                    renderCinder.position - camera.position());",
    "predicted cinder direction",
)
main = replace_once(
    main,
    "                    toSurfaceVector(inverseAster * cinderDirection));",
    "                    toSurfaceVector(celestialInverseAster * cinderDirection));",
    "predicted cinder local direction",
)
main = replace_once(
    main,
    "                const double distance = glm::length(currentCinder->position - camera.position());",
    "                const double distance = glm::length(renderCinder.position - camera.position());",
    "predicted cinder distance",
)

main = replace_once(
    main,
    "                currentSun->position - camera.position());",
    "                renderSun.position - camera.position());",
    "predicted physical sun distance",
)

# Build completion timing log.
main = replace_once(
    main,
    "                terrainBuildInFlight = false;\n"
    "                const glm::dvec3 directionNow = safeNormalize(cameraPlanet, completed.centerDirection);",
    "                terrainBuildInFlight = false;\n"
    "                std::cout << \"R24 terrain build complete_ms=\" << std::fixed << std::setprecision(1)\n"
    "                          << completed.buildMilliseconds << \" leaf=\" << completed.stats.leafPatches\n"
    "                          << \" tris=\" << completed.mesh.triangleCount() << '\\n';\n"
    "                const glm::dvec3 directionNow = safeNormalize(cameraPlanet, completed.centerDirection);",
    "terrain completion timing log",
)

# Diagnostics expose recovery state and pending render prediction time.
main = replace_once(
    main,
    "                      << \" | STREAM \" << (terrainBuildInFlight ? \"BUILD\" : \"READY\")\n",
    "                      << \" | STREAM \" << (terrainBuildInFlight ? \"BUILD\" : \"READY\")\n"
    "                      << (highSpeedRecoverySeconds > 0.0 ? \"/RECOVER\" : \"\")\n",
    "stream recovery diagnostics",
)
main = replace_once(
    main,
    "                      << \" | FPS \" << std::setprecision(0) << fps;",
    "                      << \" | PRED \" << std::setprecision(1) << celestialRenderLeadSeconds << \"s\"\n"
    "                      << \" | FPS \" << std::setprecision(0) << fps;",
    "celestial prediction diagnostics",
)
write(main_path, main)


# ---------------------------------------------------------------------------
# Regression tests for prediction math and high-speed rebuild hysteresis.
# ---------------------------------------------------------------------------
test_path = "native/tests/R24RuntimeStabilityTests.cpp"
test = read(test_path)
test = replace_once(
    test,
    '#include "vf/world/TerrainStreamingPolicy.hpp"\n',
    '#include "vf/world/TerrainStreamingPolicy.hpp"\n#include "vf/world/CelestialRenderState.hpp"\n',
    "render prediction test include",
)
predict_test = r'''
void testCelestialRenderPredictionIsSmoothAndNonMutating() {
    vf::CelestialBody body{};
    body.position = {100.0, -20.0, 3.0};
    body.linearVelocity = {4.0, 2.0, -1.0};
    body.orientation = {1.0, 0.0, 0.0, 0.0};
    body.spinAxis = {0.0, 1.0, 0.0};
    body.spinRateRadPerSecond = 0.2;
    const glm::dvec3 originalPosition = body.position;
    const glm::dquat originalOrientation = body.orientation;

    const auto render = vf::predictCelestialRenderState(body, 2.5);
    require(glm::length(render.position - glm::dvec3{110.0, -15.0, 0.5}) < 1.0e-12,
        "celestial render translation must extrapolate current inertial velocity through pending time");
    const glm::dquat expected = glm::angleAxis(0.5, glm::dvec3{0.0, 1.0, 0.0});
    require(std::abs(glm::dot(glm::normalize(render.orientation), expected)) > 0.999999999999,
        "celestial render spin must analytically advance through pending simulation time");
    require(glm::length(body.position - originalPosition) < 1.0e-12
            && std::abs(glm::dot(body.orientation, originalOrientation)) > 0.999999999999,
        "render prediction must never feed extrapolated state back into authoritative celestial physics");
}

void testHighSpeedRecoveryCooldownSuppressesImmediateRebuild() {
    const auto decision = vf::decideTerrainStreaming({
        true, 5000.0, 100.0, 5000.0, false, 2.5});
    require(decision.detailedSurfaceEligible,
        "after deceleration the detailed terrain may become eligible again");
    require(!decision.requestBuild,
        "a non-zero high-speed recovery cooldown must suppress immediate expensive terrain rebuild");
}
'''
test = replace_once(
    test,
    "void testCreativeFlightConfigurationUsesProductionLimits() {",
    predict_test + "\nvoid testCreativeFlightConfigurationUsesProductionLimits() {",
    "prediction and recovery tests",
)
test = replace_once(
    test,
    "int main() {\n    testCreativeFlightConfigurationUsesProductionLimits();",
    "int main() {\n    testCelestialRenderPredictionIsSmoothAndNonMutating();\n"
    "    testHighSpeedRecoveryCooldownSuppressesImmediateRebuild();\n"
    "    testCreativeFlightConfigurationUsesProductionLimits();",
    "prediction tests invocation",
)
write(test_path, test)

print("R24 stability round3 staged successfully")
