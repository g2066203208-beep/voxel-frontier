#!/usr/bin/env python3
from pathlib import Path

path = Path('native/src/app/Main.cpp')
text = path.read_text(encoding='utf-8')
marker = 'R24_RUNTIME_LOD_RESIDENCY_V1'
if marker in text:
    print('R24 runtime LOD/residency already integrated')
    raise SystemExit(0)


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {count}')
    text = text.replace(old, new, 1)

replace_once(
'''#include "vf/world/RegionalHydrology.hpp"\n#include "vf/world/TerrainStreamingPolicy.hpp"\n#include "vf/world/ProceduralEcology.hpp"''',
'''#include "vf/world/RegionalHydrology.hpp"\n#include "vf/world/TerrainStreamingPolicy.hpp"\n#include "vf/world/VelocityAwareLodPolicy.hpp"\n#include "vf/world/PerceptualResidencyPolicy.hpp"\n#include "vf/world/ProceduralEcology.hpp"''',
'includes')

replace_once(
'''        const vf::RuntimeFeatureFlags runtimeFeatures = vf::RuntimeFeatureFlags::fromEnvironment();\n        runtimeFeatures.print();''',
'''        const vf::RuntimeFeatureFlags runtimeFeatures = vf::RuntimeFeatureFlags::fromEnvironment();\n        runtimeFeatures.print();\n        // R24_RUNTIME_LOD_RESIDENCY_V1: same binary supports strict A/B gates. These are policy\n        // switches, not module switches: disabling them restores the legacy altitude-only terrain\n        // behavior so CI can measure the exact frame/build cost of each new optimization.\n        const bool velocityAwareLodEnabled = vf::RuntimeFeatureFlags::readFlag(\n            "VF_VELOCITY_AWARE_LOD", true);\n        const bool perceptualResidencyEnabled = vf::RuntimeFeatureFlags::readFlag(\n            "VF_PERCEPTUAL_RESIDENCY", true);\n        const bool highSpeedAutopilot = vf::RuntimeFeatureFlags::readFlag(\n            "VF_CAPTURE_HIGH_SPEED_AUTOPILOT", false);\n        std::cout << "R24 LOD_RESIDENCY velocity=" << (velocityAwareLodEnabled ? 1 : 0)\n                  << " perceptual=" << (perceptualResidencyEnabled ? 1 : 0)\n                  << " autopilot=" << (highSpeedAutopilot ? 1 : 0) << '\\n';''',
'policy toggles')

replace_once(
'''        if (captureHighSpeed) {\n            camera.setFlightMode(true);\n            camera.setCreativeFlightSpeedMps(500000.0);\n            std::cout << "R24 capture high-speed initial_speed_mps=500000\\n";\n        }''',
'''        double captureHighSpeedMetersPerSecond = 500000.0;\n        if (const char* speedEnv = std::getenv("VF_CAPTURE_SPEED_MPS");\n            speedEnv != nullptr && *speedEnv != '\\0') {\n            char* end = nullptr;\n            const double parsed = std::strtod(speedEnv, &end);\n            if (end != speedEnv && std::isfinite(parsed) && parsed > 0.0)\n                captureHighSpeedMetersPerSecond = parsed;\n        }\n        if (captureHighSpeed) {\n            camera.setFlightMode(true);\n            camera.setCreativeFlightSpeedMps(captureHighSpeedMetersPerSecond);\n            std::cout << "R24 capture high-speed initial_speed_mps="\n                      << captureHighSpeedMetersPerSecond << '\\n';\n        }''',
'high speed configurable speed')

replace_once(
'''        auto buildTerrainLod = [&](\n            const glm::dvec3& centerDirection,\n            const glm::dvec3& cameraPlanetLocal,\n            const glm::dvec3& viewForwardPlanetLocal,\n            std::shared_ptr<const vf::RegionalHydrology> reusableHydrology = {}) {''',
'''        auto buildTerrainLod = [&](\n            const glm::dvec3& centerDirection,\n            const glm::dvec3& cameraPlanetLocal,\n            const glm::dvec3& viewForwardPlanetLocal,\n            const vf::VelocityLodDecision& motionLod,\n            std::shared_ptr<const vf::RegionalHydrology> reusableHydrology = {}) {''',
'build lambda signature')

replace_once(
'''            vf::PlanetLodConfig lodConfig{};\n            lodConfig.patchResolution = buildAltitude < 25000.0 ? 12U : 10U;\n            lodConfig.maxDepth = 20U;''',
'''            vf::PlanetLodConfig lodConfig{};\n            const std::uint32_t basePatchResolution = buildAltitude < 25000.0 ? 12U : 10U;\n            lodConfig.patchResolution = motionLod.tier == vf::MotionLodTier::Transit ? 6U\n                : (motionLod.tier == vf::MotionLodTier::Fast\n                    ? std::min(basePatchResolution, 8U)\n                    : (motionLod.tier == vf::MotionLodTier::Explore\n                        ? std::min(basePatchResolution, 10U)\n                        : basePatchResolution));\n            lodConfig.maxDepth = 20U;''',
'patch resolution')

replace_once(
'''            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 1100U\n                : (buildAltitude < 150000.0 ? 650U : 320U);''',
'''            const std::size_t altitudeLeafBudget = buildAltitude < 25000.0 ? 1100U\n                : (buildAltitude < 150000.0 ? 650U : 320U);\n            lodConfig.maxLeafPatches = std::min(altitudeLeafBudget, motionLod.maxLeafPatches);''',
'leaf budget')

replace_once(
'''            lodConfig.targetScreenErrorPixels = buildAltitude < 25000.0\n                ? (mainstreamPerfProfile ? 4.08 : 3.4)\n                : (buildAltitude < 150000.0\n                    ? (mainstreamPerfProfile ? 5.76 : 4.8)\n                    : (mainstreamPerfProfile ? 8.64 : 7.2));\n            lodConfig.nearFieldRadiusMeters = buildAltitude < 25000.0 ? 1.0 : 0.0;\n            lodConfig.nearFieldCellMeters = buildAltitude < 25000.0 ? 3.0 : 24.0;\n            lodConfig.detailTransitionStartMeters = 180.0;\n            lodConfig.detailTransitionEndMeters = 65000.0;\n            lodConfig.transitionFarCellMeters = 520.0;''',
'''            const double altitudeScreenError = buildAltitude < 25000.0\n                ? (mainstreamPerfProfile ? 4.08 : 3.4)\n                : (buildAltitude < 150000.0\n                    ? (mainstreamPerfProfile ? 5.76 : 4.8)\n                    : (mainstreamPerfProfile ? 8.64 : 7.2));\n            lodConfig.targetScreenErrorPixels = std::max(\n                altitudeScreenError, motionLod.targetScreenErrorPixels);\n            lodConfig.nearFieldRadiusMeters = buildAltitude < 25000.0 ? 1.0 : 0.0;\n            const double altitudeNearCell = buildAltitude < 25000.0 ? 3.0 : 24.0;\n            lodConfig.nearFieldCellMeters = std::max(\n                altitudeNearCell, motionLod.nearFieldCellMeters);\n            lodConfig.detailTransitionStartMeters = 180.0;\n            lodConfig.detailTransitionEndMeters = 65000.0;\n            lodConfig.transitionFarCellMeters = std::max(\n                520.0, motionLod.transitionFarCellMeters);''',
'sse cell scaling')

replace_once(
'''        TerrainBuildResult initialTerrain{};\n        if (runtimeFeatures.terrainRender) {\n            initialTerrain = buildTerrainLod(\n                lodCenterDirection, initialCameraPlanet, initialViewForwardPlanet, {});''',
'''        const vf::VelocityLodDecision initialMotionLod = vf::decideVelocityAwareLod({\n            0.0, 0.0, 1.0, mainstreamPerfProfile ? 4.08 : 3.4, 3.0, 1100U, 520.0});\n        TerrainBuildResult initialTerrain{};\n        if (runtimeFeatures.terrainRender) {\n            initialTerrain = buildTerrainLod(\n                lodCenterDirection, initialCameraPlanet, initialViewForwardPlanet,\n                initialMotionLod, {});''',
'initial build')

replace_once(
'''        double diagnosticsMaxRenderMilliseconds = 0.0;\n        double lodCooldown = 0.0;\n        double dynamicSceneAccumulator = 1.0;''',
'''        double diagnosticsMaxRenderMilliseconds = 0.0;\n        double lodCooldown = 0.0;\n        double lodStableViewSeconds = 0.0;\n        glm::dvec3 previousMotionForward = initialViewForwardPlanet;\n        double dynamicSceneAccumulator = 1.0;''',
'motion state')

replace_once(
'''            movement.toggleFlight = input.toggleFlight;\n            if (captureSunTransit) {''',
'''            movement.toggleFlight = input.toggleFlight;\n            if (captureHighSpeed && highSpeedAutopilot) {\n                // Deterministic benchmark/gameplay capture hook: this is real PlanetCamera motion,\n                // not an LOD-only synthetic speed override.\n                movement.forward = 1.0;\n                movement.right = 0.0;\n                movement.vertical = 0.0;\n                movement.sprint = false;\n                movement.toggleFlight = false;\n            }\n            if (captureSunTransit) {''',
'high speed movement')

replace_once(
'''            const double localSurfaceSpeed = glm::length(localCameraVelocity);\n            const vf::TerrainStreamingDecision streaming = vf::decideTerrainStreaming({''',
'''            const double localSurfaceSpeed = glm::length(localCameraVelocity);\n            const glm::dvec3 normalizedForwardForMotion = safeNormalize(\n                forwardPlanet, previousMotionForward);\n            const double frameTurnRadians = std::acos(std::clamp(\n                glm::dot(normalizedForwardForMotion, safeNormalize(previousMotionForward, normalizedForwardForMotion)),\n                -1.0, 1.0));\n            previousMotionForward = normalizedForwardForMotion;\n            const double angularSpeedRadiansPerSecond = frameTurnRadians / std::max(1.0e-4, dt);\n            if (localSurfaceSpeed < 8.0 && angularSpeedRadiansPerSecond < 0.12)\n                lodStableViewSeconds = std::min(5.0, lodStableViewSeconds + dt);\n            else\n                lodStableViewSeconds = 0.0;\n\n            const double baseScreenError = altitude < 25000.0\n                ? (mainstreamPerfProfile ? 4.08 : 3.4)\n                : (altitude < 150000.0\n                    ? (mainstreamPerfProfile ? 5.76 : 4.8)\n                    : (mainstreamPerfProfile ? 8.64 : 7.2));\n            const double baseNearCell = altitude < 25000.0 ? 3.0 : 24.0;\n            const std::size_t baseLeafBudget = altitude < 25000.0 ? 1100U\n                : (altitude < 150000.0 ? 650U : 320U);\n            const vf::VelocityLodDecision legacyMotionLod = vf::decideVelocityAwareLod({\n                0.0, 0.0, 1.0, baseScreenError, baseNearCell, baseLeafBudget, 520.0});\n            const vf::VelocityLodDecision motionLod = velocityAwareLodEnabled\n                ? vf::decideVelocityAwareLod({\n                    localSurfaceSpeed, angularSpeedRadiansPerSecond, lodStableViewSeconds,\n                    baseScreenError, baseNearCell, baseLeafBudget, 520.0})\n                : legacyMotionLod;\n\n            const vf::PerceptualResidencyDecision terrainResidency = vf::decidePerceptualResidency({\n                std::max(1.0, altitude),\n                32000.0,\n                std::max(64.0, motionLod.transitionFarCellMeters),\n                mainstreamPerfProfile ? 1080.0 : 900.0,\n                glm::radians(68.0),\n                motionLod.motionWeight,\n                1.0,\n                12000.0,\n                camera.physicsFrameBodyId() == asterId,\n                false,\n                true,\n            });\n            const bool perceptualProxyPreferred = perceptualResidencyEnabled\n                && terrainResidency.tier != vf::SceneRepresentationTier::Detailed;\n\n            const vf::TerrainStreamingDecision streaming = vf::decideTerrainStreaming({''',
'motion and residency decision')

replace_once(
'''            if (runtimeFeatures.terrainRender\n                && streaming.useDistantGlobe != usingDistantEarthGlobe) {\n                usingDistantEarthGlobe = streaming.useDistantGlobe;''',
'''            const bool effectiveUseDistantGlobe = streaming.useDistantGlobe\n                || perceptualProxyPreferred;\n            if (runtimeFeatures.terrainRender\n                && effectiveUseDistantGlobe != usingDistantEarthGlobe) {\n                usingDistantEarthGlobe = effectiveUseDistantGlobe;''',
'proxy mode switch')

replace_once(
'''            const bool viewPrefetchExpired = viewTurnRadians > glm::radians(28.0)\n                && camera.physicsFrameBodyId() == asterId\n                && !terrainBuildInFlight\n                && lodCooldown <= 0.0;\n            if (runtimeFeatures.terrainStreamingWorkEnabled()\n                && (streaming.requestBuild || viewPrefetchExpired)) {''',
'''            const bool viewPrefetchExpired = viewTurnRadians > glm::radians(28.0)\n                && camera.physicsFrameBodyId() == asterId\n                && !terrainBuildInFlight\n                && lodCooldown <= 0.0;\n            const double velocityPrefetchThreshold = std::min(\n                streaming.prefetchThresholdMeters,\n                std::max(500.0,\n                    streaming.recenterThresholdMeters - motionLod.forwardPrefetchMeters));\n            const bool velocityPrefetchExpired = velocityAwareLodEnabled\n                && streaming.detailedSurfaceEligible\n                && arcDistance > velocityPrefetchThreshold\n                && !terrainBuildInFlight\n                && lodCooldown <= 0.0;\n            if (runtimeFeatures.terrainStreamingWorkEnabled()\n                && !perceptualProxyPreferred\n                && (streaming.requestBuild || velocityPrefetchExpired || viewPrefetchExpired)) {''',
'speed aware prefetch')

replace_once(
'''                const glm::dvec3 requestedViewForward = forwardPlanet;\n                const auto reusableHydrology = surfaceAuthority.hydrology();\n                terrainBuildFuture = std::async(\n                    std::launch::async,\n                    [&, requestedDirection, requestedCameraPlanet, requestedViewForward, reusableHydrology]() {\n                        return buildTerrainLod(\n                            requestedDirection,\n                            requestedCameraPlanet,\n                            requestedViewForward,\n                            reusableHydrology);\n                    });''',
'''                const glm::dvec3 requestedViewForward = forwardPlanet;\n                const vf::VelocityLodDecision requestedMotionLod = motionLod;\n                const auto reusableHydrology = surfaceAuthority.hydrology();\n                terrainBuildFuture = std::async(\n                    std::launch::async,\n                    [&, requestedDirection, requestedCameraPlanet, requestedViewForward,\n                        requestedMotionLod, reusableHydrology]() {\n                        return buildTerrainLod(\n                            requestedDirection,\n                            requestedCameraPlanet,\n                            requestedViewForward,\n                            requestedMotionLod,\n                            reusableHydrology);\n                    });''',
'async lod snapshot')

replace_once(
'''                    if (!refreshed.useDistantGlobe) {\n                        renderer.uploadPlanetMesh(nearTerrain);\n                        usingDistantEarthGlobe = false;\n                    }''',
'''                    if (!refreshed.useDistantGlobe && !perceptualProxyPreferred) {\n                        renderer.uploadPlanetMesh(nearTerrain);\n                        usingDistantEarthGlobe = false;\n                    }''',
'completion residency guard')

# Add compact telemetry to the existing renderer-mode log without changing benchmark parser prefixes.
replace_once(
'''                          << (usingDistantEarthGlobe ? "smooth-globe" : "adaptive-terrain")\n                          << " speed_mps=" << localSurfaceSpeed << '\\n';''',
'''                          << (usingDistantEarthGlobe ? "smooth-globe" : "adaptive-terrain")\n                          << " speed_mps=" << localSurfaceSpeed\n                          << " motion=" << motionLod.motionWeight\n                          << " leaf_budget=" << motionLod.maxLeafPatches\n                          << " prefetch_m=" << motionLod.forwardPrefetchMeters\n                          << " residency=" << static_cast<int>(terrainResidency.tier)\n                          << '\\n';''',
'mode telemetry')

path.write_text(text, encoding='utf-8')
print('R24 runtime LOD/residency integration materialized')
