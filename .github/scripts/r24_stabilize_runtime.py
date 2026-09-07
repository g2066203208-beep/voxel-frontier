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


def replace_between(text, start, end, replacement, label):
    i = text.find(start)
    if i < 0:
        raise RuntimeError(f"missing start anchor: {label}")
    j = text.find(end, i)
    if j < 0:
        raise RuntimeError(f"missing end anchor: {label}")
    return text[:i] + replacement.rstrip() + "\n\n" + text[j:]


# ---------------------------------------------------------------------------
# Terrain streaming policy: explicit, testable behavior for high-speed travel.
# ---------------------------------------------------------------------------
policy_path = ROOT / "native/include/vf/world/TerrainStreamingPolicy.hpp"
policy_path.write_text(r'''#pragma once

#include <algorithm>
#include <cmath>

namespace vf {

struct TerrainStreamingInput {
    bool onPrimaryPlanet{};
    double altitudeMeters{};
    double localSpeedMetersPerSecond{};
    double arcDistanceFromWindowMeters{};
    bool buildInFlight{};
    double cooldownSeconds{};
};

struct TerrainStreamingDecision {
    double recenterThresholdMeters{};
    double prefetchThresholdMeters{};
    double detailedSpeedLimitMetersPerSecond{};
    double staleAcceptanceMeters{};
    bool detailedSurfaceEligible{};
    bool currentWindowUsable{};
    bool useDistantGlobe{};
    bool requestBuild{};
};

[[nodiscard]] inline TerrainStreamingDecision decideTerrainStreaming(
    const TerrainStreamingInput& input) noexcept {
    TerrainStreamingDecision result{};
    const double altitude = std::max(0.0, input.altitudeMeters);
    result.recenterThresholdMeters = altitude < 20000.0 ? 8000.0
        : (altitude < 100000.0 ? 40000.0
        : (altitude < 350000.0 ? 120000.0 : 350000.0));
    result.prefetchThresholdMeters = result.recenterThresholdMeters * 0.42;
    result.detailedSpeedLimitMetersPerSecond = altitude < 20000.0 ? 2500.0
        : (altitude < 100000.0 ? 12000.0 : 30000.0);
    result.staleAcceptanceMeters = std::max(
        50000.0, result.recenterThresholdMeters * 1.60);

    const double speed = std::max(0.0, input.localSpeedMetersPerSecond);
    result.detailedSurfaceEligible = input.onPrimaryPlanet
        && altitude < 800000.0
        && speed <= result.detailedSpeedLimitMetersPerSecond;
    result.currentWindowUsable = input.arcDistanceFromWindowMeters
        <= result.recenterThresholdMeters * 0.70;
    result.useDistantGlobe = !result.detailedSurfaceEligible || !result.currentWindowUsable;
    result.requestBuild = result.detailedSurfaceEligible
        && !input.buildInFlight
        && input.cooldownSeconds <= 0.0
        && input.arcDistanceFromWindowMeters > result.prefetchThresholdMeters;
    return result;
}

} // namespace vf
''', encoding="utf-8")


# ---------------------------------------------------------------------------
# Ecology: sample the same PlanetSurfaceAuthority (including hydrology incision)
# as rendered/collision terrain. Keep old calls source-compatible via nullable pointer.
# ---------------------------------------------------------------------------
header_path = "native/include/vf/world/ProceduralEcology.hpp"
header = read(header_path)
header = replace_once(
    header,
    "namespace vf {\n",
    "namespace vf {\n\nclass PlanetSurfaceAuthority;\n",
    "ecology authority forward declaration",
)
header = replace_once(
    header,
    "    const SurfaceRenderFrame& frame,\n    const ProceduralEcologySettings& settings = {});",
    "    const SurfaceRenderFrame& frame,\n"
    "    const ProceduralEcologySettings& settings = {},\n"
    "    const PlanetSurfaceAuthority* surfaceAuthority = nullptr);",
    "ecology authority optional parameter",
)
write(header_path, header)

source_path = "native/src/world/ProceduralEcology.cpp"
source = read(source_path)
source = replace_once(
    source,
    '#include "vf/world/ProceduralEcology.hpp"\n',
    '#include "vf/world/ProceduralEcology.hpp"\n#include "vf/world/PlanetSurfaceAuthority.hpp"\n',
    "ecology authority include",
)
source = replace_once(
    source,
    "    const PlanetDefinition& planet,\n    const SurfaceRenderFrame& frame,\n    double x,\n    double z) {\n"
    "    SurfaceCandidate candidate{};\n"
    "    const glm::dvec3 direction = planetDirectionFromRenderXZ(frame, x, z);\n"
    "    candidate.terrain = samplePlanetTerrain(planet, direction);\n"
    "    const glm::dvec3 normalPlanet = planetSurfaceNormal(planet, direction);\n"
    "    candidate.radialAlignment = glm::dot(normalPlanet, direction);\n"
    "    candidate.renderPoint = toRenderPoint(\n"
    "        frame,\n"
    "        direction * (planet.radius + candidate.terrain.elevationMeters));",
    "    const PlanetDefinition& planet,\n    const SurfaceRenderFrame& frame,\n"
    "    const PlanetSurfaceAuthority* surfaceAuthority,\n"
    "    double x,\n    double z) {\n"
    "    SurfaceCandidate candidate{};\n"
    "    const glm::dvec3 direction = planetDirectionFromRenderXZ(frame, x, z);\n"
    "    candidate.terrain = surfaceAuthority != nullptr\n"
    "        ? surfaceAuthority->sample(direction)\n"
    "        : samplePlanetTerrain(planet, direction);\n"
    "    const glm::dvec3 normalPlanet = surfaceAuthority != nullptr\n"
    "        ? surfaceAuthority->surfaceNormal(direction)\n"
    "        : planetSurfaceNormal(planet, direction);\n"
    "    const double surfaceRadius = surfaceAuthority != nullptr\n"
    "        ? surfaceAuthority->surfaceRadius(direction)\n"
    "        : planet.radius + candidate.terrain.elevationMeters;\n"
    "    candidate.radialAlignment = glm::dot(normalPlanet, direction);\n"
    "    candidate.renderPoint = toRenderPoint(frame, direction * surfaceRadius);",
    "ecology authoritative candidate sample",
)
source = replace_once(
    source,
    "    const glm::dvec3& centerDirection,\n    const PlanetDefinition& planet,\n"
    "    double radius,",
    "    const glm::dvec3& centerDirection,\n    const PlanetDefinition& planet,\n"
    "    const PlanetSurfaceAuthority* surfaceAuthority,\n    double radius,",
    "ecology stable cells authority parameter",
)
source = replace_once(
    source,
    "    const glm::dvec3 centerPlanet = centerDirection\n"
    "        * (planet.radius + samplePlanetTerrain(planet, centerDirection).elevationMeters);",
    "    const double centerRadius = surfaceAuthority != nullptr\n"
    "        ? surfaceAuthority->surfaceRadius(centerDirection)\n"
    "        : planet.radius + samplePlanetTerrain(planet, centerDirection).elevationMeters;\n"
    "    const glm::dvec3 centerPlanet = centerDirection * centerRadius;",
    "ecology authoritative center",
)
source = replace_once(
    source,
    "    const SurfaceRenderFrame& frame,\n    const ProceduralEcologySettings& settings) {",
    "    const SurfaceRenderFrame& frame,\n    const ProceduralEcologySettings& settings,\n"
    "    const PlanetSurfaceAuthority* surfaceAuthority) {",
    "ecology public authority parameter",
)
source = source.replace(
    "        planet,\n        settings.",
    "        planet,\n        surfaceAuthority,\n        settings.",
)
source = source.replace(
    "sampleCandidate(planet, frame, x, z)",
    "sampleCandidate(planet, frame, surfaceAuthority, x, z)",
)
write(source_path, source)


# ---------------------------------------------------------------------------
# Physics: local rotating PhysicsWorld already exposes omega; actually apply its
# Coriolis + centrifugal accelerations instead of creating a second fake celestial system.
# ---------------------------------------------------------------------------
physics_path = "native/src/physics/PhysicsWorld.cpp"
physics = read(physics_path)
physics = replace_once(
    physics,
    "    const glm::dvec3 gravityAcceleration = environment_.gravityAcceleration(rigidBody.position);\n"
    "    const double gravity = glm::length(gravityAcceleration);\n"
    "    rigidBody.accumulatedForce += rigidBody.mass * gravityAcceleration;",
    "    const glm::dvec3 gravityAcceleration = environment_.gravityAcceleration(rigidBody.position);\n"
    "    const double gravity = glm::length(gravityAcceleration);\n"
    "    rigidBody.accumulatedForce += rigidBody.mass * gravityAcceleration;\n\n"
    "    const glm::dvec3 omega = environment_.rotatingFrameAngularVelocity;\n"
    "    if (glm::dot(omega, omega) > 1.0e-24) {\n"
    "        const glm::dvec3 coriolis = -2.0 * glm::cross(omega, rigidBody.linearVelocity);\n"
    "        const glm::dvec3 centrifugal = -glm::cross(omega, glm::cross(omega, rigidBody.position));\n"
    "        rigidBody.accumulatedForce += rigidBody.mass * (coriolis + centrifugal);\n"
    "    }",
    "rotating-frame inertial forces",
)
write(physics_path, physics)


# ---------------------------------------------------------------------------
# Runtime: adaptive build quality, authority-aware ecology, no fake gravity system,
# speed-aware/stale-aware streaming, and finer normal-time celestial stepping.
# ---------------------------------------------------------------------------
main_path = "native/src/app/Main.cpp"
main = read(main_path)
main = replace_once(
    main,
    '#include "vf/world/RegionalHydrology.hpp"\n',
    '#include "vf/world/RegionalHydrology.hpp"\n#include "vf/world/TerrainStreamingPolicy.hpp"\n',
    "streaming policy include",
)
main = replace_once(
    main,
    "        vf::CelestialSimulationClock celestialClock{{60.0, celestialTimeScale, 4096U}};",
    "        const double celestialFixedStepSeconds = celestialTimeScale <= 1000.0 ? 5.0\n"
    "            : (celestialTimeScale <= 20000.0 ? 15.0 : 60.0);\n"
    "        vf::CelestialSimulationClock celestialClock{{\n"
    "            celestialFixedStepSeconds, celestialTimeScale, 4096U}};",
    "adaptive celestial fixed step",
)
main = replace_once(
    main,
    "        auto buildTerrainLod = [&](const glm::dvec3& centerDirection, const glm::dvec3& cameraPlanetLocal) {\n"
    "            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);\n"
    "            vf::RegionalHydrologyConfig hydroConfig{};\n"
    "            hydroConfig.resolution = 129U;",
    "        auto buildTerrainLod = [&](const glm::dvec3& centerDirection, const glm::dvec3& cameraPlanetLocal) {\n"
    "            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);\n"
    "            const double buildAltitude = std::max(0.0, glm::length(cameraPlanetLocal) - planet.radius);\n"
    "            vf::RegionalHydrologyConfig hydroConfig{};\n"
    "            hydroConfig.resolution = buildAltitude < 25000.0 ? 129U\n"
    "                : (buildAltitude < 150000.0 ? 97U : 65U);",
    "altitude-aware hydrology quality",
)
main = replace_once(
    main,
    "            lodConfig.maxLeafPatches = 1600U;",
    "            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 1600U\n"
    "                : (buildAltitude < 150000.0 ? 900U : 500U);",
    "altitude-aware leaf budget",
)
main = replace_once(
    main,
    "            lodConfig.targetScreenErrorPixels = 3.4;",
    "            lodConfig.targetScreenErrorPixels = buildAltitude < 25000.0 ? 3.4\n"
    "                : (buildAltitude < 150000.0 ? 5.0 : 8.0);",
    "altitude-aware screen error",
)
main = replace_once(
    main,
    "            appendMesh(result.mesh, vf::buildProceduralEcology(planet, centerUp, surfaceFrame));",
    "            if (buildAltitude < 30000.0) {\n"
    "                appendMesh(result.mesh, vf::buildProceduralEcology(\n"
    "                    planet, centerUp, surfaceFrame, {}, &buildSurface));\n"
    "            }",
    "authority-aware ecology runtime",
)
main = replace_between(
    main,
    "        // Local rotating planet frame for high-quality ground physics while CelestialSystem remains",
    "        vf::CharacterControllerSettings characterSettings{};",
    r'''        // Character/nearby rigid-body physics already runs in Aster body-local coordinates.
        // Do not fabricate a second CelestialSystem at the origin: use radial local gravity and
        // explicitly expose the body's rotating-frame angular velocity to PhysicsWorld.
        vf::PhysicsEnvironment environment{};
        environment.planet = planet;
        environment.surfaceGravity = 9.80665;
        environment.surfaceAuthority = &surfaceAuthority;
        environment.climateGrid = &climateGrid;
        environment.oceanSpectrum = &oceanSpectrum;
        environment.rotatingFrameAngularVelocity = asterFrame.localAngularVelocity(*initialAster);
        environment.atmosphere.prevailingWind = {};
        environment.atmosphere.gustAmplitude = 0.0;
        environment.weather.windMultiplier = 0.0;
        environment.ocean.enabled = true;
        environment.ocean.surfaceRadius = planet.radius + planet.seaLevelElevationMeters;
        environment.ocean.densityKgPerM3 = 1025.0;
        environment.ocean.viscosityPaS = 0.00108;
        environment.ocean.meanCurrent = {};
        vf::PhysicsWorld physics{environment};''',
    "remove fake local celestial gravity system",
)
main = replace_between(
    main,
    "            // CPU synthesis is asynchronous.",
    "            const glm::dvec3 sunWorldDirection = safeNormalize(",
    r'''            // CPU terrain synthesis is asynchronous, but high-speed flight must never queue
            // kilometre-scale near-field work faster than it can be consumed. A testable policy
            // switches to the cheap globe during fast transit, prefetches before the old window is
            // exhausted, and rejects stale completed jobs after a large camera jump.
            lodCooldown = std::max(0.0, lodCooldown - dt);
            const double altitude = camera.altitude();
            const glm::dvec3 cameraDirection = safeNormalize(cameraPlanet, lodCenterDirection);
            const double arcDistance = std::acos(std::clamp(
                glm::dot(cameraDirection, lodCenterDirection), -1.0, 1.0)) * planet.radius;
            const double localSurfaceSpeed = glm::length(localCameraVelocity);
            const vf::TerrainStreamingDecision streaming = vf::decideTerrainStreaming({
                camera.physicsFrameBodyId() == asterId,
                altitude,
                localSurfaceSpeed,
                arcDistance,
                terrainBuildInFlight,
                lodCooldown,
            });

            if (streaming.useDistantGlobe != usingDistantEarthGlobe) {
                usingDistantEarthGlobe = streaming.useDistantGlobe;
                renderer.uploadPlanetMesh(usingDistantEarthGlobe ? earthGlobeMesh : nearTerrain);
                std::cout << "R24 Earth renderer mode: "
                          << (usingDistantEarthGlobe ? "smooth-globe" : "adaptive-terrain")
                          << " speed_mps=" << localSurfaceSpeed << '\n';
            }

            if (streaming.requestBuild) {
                const glm::dvec3 requestedDirection = cameraDirection;
                const glm::dvec3 requestedCameraPlanet = cameraPlanet;
                terrainBuildFuture = std::async(
                    std::launch::async,
                    [&, requestedDirection, requestedCameraPlanet]() {
                        return buildTerrainLod(requestedDirection, requestedCameraPlanet);
                    });
                terrainBuildInFlight = true;
            }

            if (terrainBuildInFlight
                && terrainBuildFuture.wait_for(std::chrono::milliseconds{0})
                    == std::future_status::ready) {
                TerrainBuildResult completed = terrainBuildFuture.get();
                terrainBuildInFlight = false;
                const glm::dvec3 directionNow = safeNormalize(cameraPlanet, completed.centerDirection);
                const double staleArcDistance = std::acos(std::clamp(
                    glm::dot(directionNow, completed.centerDirection), -1.0, 1.0)) * planet.radius;
                if (staleArcDistance <= streaming.staleAcceptanceMeters) {
                    lodCenterDirection = completed.centerDirection;
                    surfaceAuthority.setHydrology(completed.hydrology);
                    currentLodStats = completed.stats;
                    nearTerrain = std::move(completed.mesh);
                    lodCooldown = 0.12;

                    const vf::TerrainStreamingDecision refreshed = vf::decideTerrainStreaming({
                        camera.physicsFrameBodyId() == asterId,
                        altitude,
                        localSurfaceSpeed,
                        staleArcDistance,
                        false,
                        lodCooldown,
                    });
                    if (!refreshed.useDistantGlobe) {
                        renderer.uploadPlanetMesh(nearTerrain);
                        usingDistantEarthGlobe = false;
                    }
                } else {
                    lodCooldown = 0.0;
                    std::cout << "R24 terrain stale build discarded: camera_delta_km="
                              << staleArcDistance / 1000.0 << '\n';
                }
            }''',
    "speed-aware terrain streaming",
)
write(main_path, main)


# ---------------------------------------------------------------------------
# Shadow contact: use raster bias for acne prevention and a much smaller receiver
# bias, avoiding the previous double-bias peter-panning gap under trees/rocks.
# ---------------------------------------------------------------------------
renderer_path = "native/src/render/VulkanRenderer.cpp"
renderer = read(renderer_path)
renderer = replace_once(
    renderer,
    "    shadowRaster.depthBiasConstantFactor = 1.25F;\n"
    "    shadowRaster.depthBiasSlopeFactor = 1.75F;",
    "    shadowRaster.depthBiasConstantFactor = 0.55F;\n"
    "    shadowRaster.depthBiasSlopeFactor = 1.00F;",
    "shadow raster bias",
)
write(renderer_path, renderer)

shader_path = "native/shaders/planet.slang"
shader = read(shader_path)
shader = replace_once(
    shader,
    "    float bias = max(0.00022, 0.0011 * (1.0 - noL));",
    "    // Raster depth bias already handles most acne. Keep receiver bias at centimetre-scale\n"
    "    // for the 480 m shadow depth range so contact shadows do not visibly detach.\n"
    "    float bias = max(0.00004, 0.00030 * (1.0 - noL));",
    "shadow receiver bias",
)
write(shader_path, shader)


# ---------------------------------------------------------------------------
# Regression tests for the new streaming and rotating-frame invariants.
# ---------------------------------------------------------------------------
test_path = ROOT / "native/tests/R24RuntimeStabilityTests.cpp"
test_path.write_text(r'''#include "vf/physics/PhysicsWorld.hpp"
#include "vf/world/TerrainStreamingPolicy.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

namespace {

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "R24 RUNTIME STABILITY TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

vf::PhysicsEnvironment inertialTestEnvironment() {
    vf::PhysicsEnvironment environment{};
    environment.planet.radius = 1000.0;
    environment.planet.maxElevation = 0.0;
    environment.surfaceGravity = 0.0;
    environment.atmosphere.seaLevelPressurePa = 0.0;
    environment.atmosphere.pressureScale = 0.0;
    environment.ocean.enabled = false;
    return environment;
}

vf::RigidBodyDesc testBody(const glm::dvec3& position, const glm::dvec3& velocity = {}) {
    vf::RigidBodyDesc body{};
    body.position = position;
    body.linearVelocity = velocity;
    body.mass = 1.0;
    body.collisionShape = vf::CollisionShape::sphere(0.1);
    body.linearDamping = 0.0;
    body.angularDamping = 0.0;
    body.aerodynamics.referenceArea = 0.0;
    return body;
}

void testCentrifugalAccelerationInRotatingLocalWorld() {
    auto environment = inertialTestEnvironment();
    environment.rotatingFrameAngularVelocity = {0.0, 0.0, 1.0};
    vf::PhysicsWorld world{environment};
    const auto id = world.createRigidBody(testBody({10.0, 0.0, 0.0}));
    world.stepFixed();
    const auto* body = world.body(id);
    require(body != nullptr, "centrifugal test body missing");
    require(body->linearVelocity.x > 0.08,
        "rotating local physics must apply outward centrifugal acceleration");
}

void testCoriolisAccelerationInRotatingLocalWorld() {
    auto environment = inertialTestEnvironment();
    environment.rotatingFrameAngularVelocity = {0.0, 0.0, 1.0};
    vf::PhysicsWorld world{environment};
    const auto id = world.createRigidBody(testBody({0.0, 0.0, 0.0}, {1.0, 0.0, 0.0}));
    world.stepFixed();
    const auto* body = world.body(id);
    require(body != nullptr, "coriolis test body missing");
    require(body->linearVelocity.y < -0.015,
        "positive-X local motion under positive-Z spin must receive negative-Y Coriolis acceleration");
}

void testHighSpeedTransitForcesCheapGlobeAndNoBuild() {
    const auto decision = vf::decideTerrainStreaming({
        true, 5000.0, 250000.0, 20000.0, false, 0.0});
    require(decision.useDistantGlobe,
        "high-speed low-altitude transit must fall back to the cheap globe");
    require(!decision.requestBuild,
        "high-speed transit must not start an expensive near-field rebuild");
}

void testSlowSurfaceTravelPrefetchesBeforeWindowExpires() {
    const auto decision = vf::decideTerrainStreaming({
        true, 5000.0, 45.0, 4200.0, false, 0.0});
    require(decision.detailedSurfaceEligible, "normal walking/driving speeds must retain detailed terrain");
    require(decision.currentWindowUsable, "prefetch must begin while the existing window is still usable");
    require(decision.requestBuild, "slow travel beyond prefetch threshold must request one rebuild");
    require(!decision.useDistantGlobe, "usable detailed window must stay visible during background prefetch");
}

void testStaleWindowFallsBackUntilFreshBuildArrives() {
    const auto decision = vf::decideTerrainStreaming({
        true, 8000.0, 120.0, 9000.0, true, 0.0});
    require(decision.useDistantGlobe,
        "camera beyond the safe detailed window must render the globe while a replacement builds");
    require(!decision.requestBuild,
        "only one terrain build may be in flight at a time");
    require(decision.staleAcceptanceMeters >= decision.recenterThresholdMeters,
        "stale acceptance must be wider than the normal recenter window");
}

} // namespace

int main() {
    testCentrifugalAccelerationInRotatingLocalWorld();
    testCoriolisAccelerationInRotatingLocalWorld();
    testHighSpeedTransitForcesCheapGlobeAndNoBuild();
    testSlowSurfaceTravelPrefetchesBeforeWindowExpires();
    testStaleWindowFallsBackUntilFreshBuildArrives();
    std::cout << "vf_r24_runtime_stability_tests: PASS\n";
    return 0;
}
''', encoding="utf-8")

cmake_path = "native/CMakeLists.txt"
cmake = read(cmake_path)
anchor = "    add_executable(vf_r24_physical_planet_tests tests/R24PhysicalPlanetTests.cpp)\n    target_link_libraries(vf_r24_physical_planet_tests PRIVATE vf_engine glm::glm)\n    add_test(NAME vf_r24_physical_planet_tests COMMAND vf_r24_physical_planet_tests)\n"
replacement = anchor + "    add_executable(vf_r24_runtime_stability_tests tests/R24RuntimeStabilityTests.cpp)\n    target_link_libraries(vf_r24_runtime_stability_tests PRIVATE vf_engine glm::glm)\n    add_test(NAME vf_r24_runtime_stability_tests COMMAND vf_r24_runtime_stability_tests)\n"
cmake = replace_once(cmake, anchor, replacement, "runtime stability test target")
write(cmake_path, cmake)

print("R24 runtime stabilization staged successfully")
