#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / 'native/src/app/Main.cpp'
t = MAIN.read_text(encoding='utf-8')

def once(old, new, label):
    global t
    if old not in t:
        raise RuntimeError(f'missing Main.cpp anchor: {label}')
    t = t.replace(old, new, 1)

once(
    '#include "vf/world/PlanetSurface.hpp"\n#include "vf/world/RegionalHydrology.hpp"',
    '#include "vf/world/PlanetSurface.hpp"\n#include "vf/world/PlanetSurfaceAuthority.hpp"\n#include "vf/world/PlanetLodMeshBuilder.hpp"\n#include "vf/world/RegionalHydrology.hpp"',
    'R24 surface/LOD includes')
once('#include <limits>\n#include <sstream>', '#include <limits>\n#include <memory>\n#include <sstream>', 'memory include')

once(
    '        aster.spinAxis = {0.0, 1.0, 0.0};',
    '        constexpr double asterObliquity = 23.439281 * kPi / 180.0;\n'
    '        aster.spinAxis = safeNormalize({std::sin(asterObliquity), std::cos(asterObliquity), 0.0});',
    'Aster obliquity')

once(
    '        const std::uint32_t asterId = celestial.addBody(aster);',
    '        const std::uint32_t asterId = celestial.addBody(aster);\n'
    '        vf::PlanetClimateGrid climateGrid{planet, {}, aster.spinRateRadPerSecond};\n'
    '        vf::OceanSpectrum oceanSpectrum{};',
    'climate and ocean services')

old_moon = '''        const glm::dvec3 moonRadial = safeNormalize(
            camera.forwardDirection() + camera.up() * 0.34,
            stableTangent(spawnDirection));
        glm::dvec3 moonTangent = glm::cross(moonRadial, camera.up());
        if (glm::dot(moonTangent, moonTangent) < 1.0e-12) moonTangent = stableTangent(moonRadial);
        moonTangent = safeNormalize(moonTangent, stableTangent(moonRadial));
        luna.position = aster.position + moonRadial * moonOrbitRadius;
        luna.linearVelocity = aster.linearVelocity
            + moonTangent * circularOrbitSpeed(aster.massKg, moonOrbitRadius);'''
new_moon = '''        constexpr double moonInclination = 5.145 * kPi / 180.0;
        constexpr double moonEpochPhase = 1.07;
        const glm::dvec3 moonOrbitNormal = safeNormalize(
            {0.0, std::cos(moonInclination), std::sin(moonInclination)});
        const glm::dvec3 moonNode{1.0, 0.0, 0.0};
        const glm::dvec3 moonQuadrature = safeNormalize(glm::cross(moonOrbitNormal, moonNode));
        const glm::dvec3 moonRadial = safeNormalize(
            moonNode * std::cos(moonEpochPhase) + moonQuadrature * std::sin(moonEpochPhase));
        const glm::dvec3 moonTangent = safeNormalize(
            -moonNode * std::sin(moonEpochPhase) + moonQuadrature * std::cos(moonEpochPhase));
        luna.position = aster.position + moonRadial * moonOrbitRadius;
        luna.linearVelocity = aster.linearVelocity
            + moonTangent * circularOrbitSpeed(aster.massKg, moonOrbitRadius);'''
once(old_moon, new_moon, 'camera-independent Moon orbit')

once(
    '        const std::uint32_t moonId = celestial.addBody(luna);',
    '''        const std::uint32_t moonId = celestial.addBody(luna);
        vf::PlanetDefinition moonSurfaceDefinition{};
        moonSurfaceDefinition.seed = 0x4C554E415F523234ULL;
        moonSurfaceDefinition.radius = luna.radiusMeters;
        moonSurfaceDefinition.maxElevation = 9000.0;
        moonSurfaceDefinition.seaLevelElevationMeters = -2500.0;
        moonSurfaceDefinition.maxOceanDepthMeters = 0.0;
        moonSurfaceDefinition.atmosphereHeight = 0.0;
        vf::PlanetMesh moonSurfaceMesh = vf::buildPlanetSurface(moonSurfaceDefinition, 32U);
        for (auto& vertex : moonSurfaceMesh.vertices) {
            const float shade = 0.50F + 0.16F * std::abs(vertex.normal.y);
            vertex.color = {shade, shade * 0.99F, shade * 0.97F};
            vertex.material = {0.0F, 0.92F, 0.0F, -1.0F};
        }''',
    'Moon physical surface mesh')

once(
    '                safeNormalize(tangent * 0.58 - worldUp * 0.82, -worldUp),',
    '                safeNormalize(tangent * 0.78 - worldUp * 0.625, -worldUp),',
    'oblique aerial camera')

start_marker = '        glm::dvec3 lodCenterDirection = patchUp;\n'
end_marker = '        // Local rotating planet frame for high-quality ground physics while CelestialSystem remains\n'
start = t.find(start_marker)
end = t.find(end_marker, start)
if start < 0 or end < 0:
    raise RuntimeError('missing terrain LOD replacement region')

new_lod = '''        vf::PlanetSurfaceAuthority surfaceAuthority{planet};
        glm::dvec3 lodCenterDirection = patchUp;
        struct TerrainBuildResult {
            glm::dvec3 centerDirection{};
            vf::PlanetMesh mesh{};
            std::shared_ptr<const vf::RegionalHydrology> hydrology{};
            vf::PlanetLodStats stats{};
        };

        auto buildTerrainLod = [&](const glm::dvec3& centerDirection, const glm::dvec3& cameraPlanetLocal) {
            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);
            vf::RegionalHydrologyConfig hydroConfig{};
            hydroConfig.resolution = 129U;
            hydroConfig.halfExtentMeters = 220000.0;
            hydroConfig.maxIncisionMeters = 420.0;
            hydroConfig.riverHeadAccumulationFraction = 0.0012;
            hydroConfig.fullChannelAccumulationFraction = 0.022;
            auto hydrology = std::make_shared<vf::RegionalHydrology>(planet, centerUp, hydroConfig);

            vf::PlanetSurfaceAuthority buildSurface{planet};
            buildSurface.setHydrology(hydrology);
            vf::PlanetLodConfig lodConfig{};
            lodConfig.patchResolution = 12U;
            lodConfig.maxDepth = 16U;
            lodConfig.maxLeafPatches = 3200U;
            lodConfig.verticalFovRadians = glm::radians(68.0);
            lodConfig.viewportHeightPixels = 900.0;
            lodConfig.targetScreenErrorPixels = 2.8;
            lodConfig.horizonMarginRadians = 0.018;
            lodConfig.skirtDepthMeters = 6.0;

            TerrainBuildResult result{};
            result.centerDirection = centerUp;
            result.hydrology = hydrology;
            result.mesh = vf::buildAdaptivePlanetSurface(
                buildSurface, cameraPlanetLocal, lodConfig, &result.stats);
            for (auto& vertex : result.mesh.vertices) {
                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
            }

            appendMesh(result.mesh, vf::buildProceduralEcology(planet, centerUp, surfaceFrame));

            vf::PlanetMesh oceanProxy{};
            vf::appendOceanSurfaceProxy(
                oceanProxy, {}, planet.radius + planet.seaLevelElevationMeters - 1.5, 160U);
            for (auto& vertex : oceanProxy.vertices) {
                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
                vertex.material.w = -20.0F;
            }
            appendMesh(result.mesh, oceanProxy);
            return result;
        };

        TerrainBuildResult initialTerrain = buildTerrainLod(lodCenterDirection, initialCameraPlanet);
        surfaceAuthority.setHydrology(initialTerrain.hydrology);
        vf::PlanetLodStats currentLodStats = initialTerrain.stats;
        vf::PlanetMesh staticTerrain = std::move(initialTerrain.mesh);
        renderer.uploadPlanetMesh(staticTerrain);
        std::future<TerrainBuildResult> terrainBuildFuture{};
        bool terrainBuildInFlight = false;

'''
t = t[:start] + new_lod + t[end:]

once(
    '        environment.primaryCelestialBodyId = localGravityId;\n        environment.atmosphere.prevailingWind = {};',
    '        environment.primaryCelestialBodyId = localGravityId;\n'
    '        environment.surfaceAuthority = &surfaceAuthority;\n'
    '        environment.climateGrid = &climateGrid;\n'
    '        environment.oceanSpectrum = &oceanSpectrum;\n'
    '        environment.atmosphere.prevailingWind = {};',
    'physics authority pointers')

once(
    '        characterSettings.walkSpeed = 9.0;\n        characterSettings.sprintSpeed = 18.0;',
    '        characterSettings.walkSpeed = 4.8;\n        characterSettings.sprintSpeed = 8.2;\n        characterSettings.jumpSpeed = 4.7;\n        characterSettings.airAcceleration = 1.6;',
    'Earthlike character movement')

once(
    '''            celestialClock.advance(dt, [&](double astroDt) {
                celestial.step(astroDt);
            });''',
    '''            celestialClock.advance(dt, [&](double astroDt) {
                celestial.step(astroDt);
                const auto* climateAster = celestial.body(asterId);
                const auto* climateSun = celestial.body(sunId);
                if (climateAster != nullptr && climateSun != nullptr) {
                    const glm::dvec3 toSunWorld = safeNormalize(climateSun->position - climateAster->position);
                    const glm::dvec3 toSunBody = safeNormalize(
                        glm::conjugate(glm::normalize(climateAster->orientation)) * toSunWorld);
                    const double starDistance = glm::length(climateSun->position - climateAster->position);
                    const double stellarIrradiance = climateSun->luminosityWatts
                        / (4.0 * kPi * std::max(1.0, starDistance * starDistance));
                    climateGrid.step(astroDt, toSunBody, stellarIrradiance);
                }
            });''',
    'climate clock integration')

once(
    '''                    const glm::dvec3 requestedDirection = cameraDirection;
                    terrainBuildFuture = std::async(std::launch::async, [&, requestedDirection]() {
                        return std::make_pair(requestedDirection, buildTerrainLod(requestedDirection));
                    });
                    terrainBuildInFlight = true;''',
    '''                    const glm::dvec3 requestedDirection = cameraDirection;
                    const glm::dvec3 requestedCameraPlanet = cameraPlanet;
                    terrainBuildFuture = std::async(
                        std::launch::async,
                        [&, requestedDirection, requestedCameraPlanet]() {
                            return buildTerrainLod(requestedDirection, requestedCameraPlanet);
                        });
                    terrainBuildInFlight = true;''',
    'adaptive async request')

once(
    '''                    auto completed = terrainBuildFuture.get();
                    terrainBuildInFlight = false;
                    lodCenterDirection = completed.first;
                    staticTerrain = std::move(completed.second);
                    renderer.uploadPlanetMesh(staticTerrain);
                    lodCooldown = 0.12;''',
    '''                    TerrainBuildResult completed = terrainBuildFuture.get();
                    terrainBuildInFlight = false;
                    lodCenterDirection = completed.centerDirection;
                    surfaceAuthority.setHydrology(completed.hydrology);
                    currentLodStats = completed.stats;
                    staticTerrain = std::move(completed.mesh);
                    renderer.uploadPlanetMesh(staticTerrain);
                    lodCooldown = 0.12;''',
    'adaptive async completion')

moon_dynamic_start = t.find('            if (currentMoon != nullptr) {\n')
moon_dynamic_end = t.find('            if (currentCinder != nullptr) {\n', moon_dynamic_start)
if moon_dynamic_start < 0 or moon_dynamic_end < 0:
    raise RuntimeError('missing dynamic Moon block')
new_moon_dynamic = '''            if (currentMoon != nullptr) {
                vf::PlanetMesh moonMesh = moonSurfaceMesh;
                const glm::dvec3 moonRelativeWorld = currentMoon->position - currentAster->position;
                for (auto& vertex : moonMesh.vertices) {
                    const glm::dvec3 moonBodyPoint = currentMoon->orientation * glm::dvec3(vertex.position);
                    const glm::dvec3 pointAsterLocal = inverseAster * (moonRelativeWorld + moonBodyPoint);
                    const glm::dvec3 normalAsterLocal = inverseAster
                        * (currentMoon->orientation * glm::dvec3(vertex.normal));
                    vertex.position = glm::vec3(toSurfacePoint(pointAsterLocal));
                    vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(normalAsterLocal)));
                }
                appendMesh(dynamicMesh, moonMesh);
            }
'''
t = t[:moon_dynamic_start] + new_moon_dynamic + t[moon_dynamic_end:]

once(
    '''            const auto atmosphere = celestial.sampleEnvironment(camera.position());
            const double densityRatio = std::clamp(atmosphere.densityKgPerM3 / 1.225, 0.0, 1.2);''',
    '''            const vf::PlanetClimateSample climateSample = climateGrid.sample(
                safeNormalize(cameraPlanet, patchUp), std::max(0.0, camera.altitude()));
            const double densityRatio = std::clamp(climateSample.densityKgPerM3 / 1.225, 0.0, 1.2);''',
    'render climate sample')

once(
    '''                const vf::PlanetTerrainSample terrainBelow = vf::samplePlanetTerrain(
                    planet, safeNormalize(cameraPlanet, patchUp));''',
    '''                const vf::PlanetTerrainSample terrainBelow = surfaceAuthority.sample(
                    safeNormalize(cameraPlanet, patchUp));''',
    'diagnostic surface authority')

once(
    '                      << " | STREAM " << (terrainBuildInFlight ? "BUILD" : "READY")\n',
    '                      << " | STREAM " << (terrainBuildInFlight ? "BUILD" : "READY")\n'
    '                      << " | QLOD " << currentLodStats.leafPatches << "/L" << currentLodStats.deepestLevel\n'
    '                      << " | cell " << std::setprecision(1) << currentLodStats.nearestCellMeters << "m"\n',
    'LOD diagnostics title')

once('        std::cout << "Voxel Frontier Earthlike planet runtime\\n";',
     '        std::cout << "Voxel Frontier R24 adaptive physical planet runtime\\n";',
     'runtime banner')
once('        std::cout << "Async terrain synthesis | morphing clipmaps | deterministic stylized ecology\\n";',
     '        std::cout << "SSE cube-sphere quadtree | unified surface authority | deterministic stylized ecology\\n";',
     'runtime feature banner')

MAIN.write_text(t, encoding='utf-8')
print('R24 runtime integration staged: adaptive cube-sphere LOD, unified surface/climate/ocean, physical Moon')
