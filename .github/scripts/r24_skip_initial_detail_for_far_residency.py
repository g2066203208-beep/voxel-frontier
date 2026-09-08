#!/usr/bin/env python3
from pathlib import Path

path = Path('native/src/app/Main.cpp')
text = path.read_text(encoding='utf-8')
marker = 'R24_INITIAL_PERCEPTUAL_RESIDENCY_V1'
if marker in text:
    print('R24 initial perceptual residency already integrated')
    raise SystemExit(0)

old = '''        const vf::VelocityLodDecision initialMotionLod = vf::decideVelocityAwareLod({\n            0.0, 0.0, 1.0, mainstreamPerfProfile ? 4.08 : 3.4, 3.0, 1100U, 520.0});\n        TerrainBuildResult initialTerrain{};\n        if (runtimeFeatures.terrainRender) {\n            initialTerrain = buildTerrainLod(\n                lodCenterDirection, initialCameraPlanet, initialViewForwardPlanet,\n                initialMotionLod, {});'''
new = '''        const vf::VelocityLodDecision initialMotionLod = vf::decideVelocityAwareLod({\n            0.0, 0.0, 1.0, mainstreamPerfProfile ? 4.08 : 3.4, 3.0, 1100U, 520.0});\n        // R24_INITIAL_PERCEPTUAL_RESIDENCY_V1: a far/ orbital camera never pays to synthesize\n        // detailed near terrain only to replace it with a macro/globe proxy on the first frame.\n        // Visual range and source residency are independent from startup onward.\n        const double initialAltitudeMeters = std::max(\n            0.0, glm::length(initialCameraPlanet) - planet.radius);\n        const vf::PerceptualResidencyDecision initialTerrainResidency =\n            vf::decidePerceptualResidency({\n                std::max(1.0, initialAltitudeMeters),\n                32000.0,\n                std::max(64.0, initialMotionLod.transitionFarCellMeters),\n                mainstreamPerfProfile ? 1080.0 : 900.0,\n                glm::radians(68.0),\n                initialMotionLod.motionWeight,\n                1.0,\n                12000.0,\n                camera.physicsFrameBodyId() == asterId,\n                false,\n                true,\n            });\n        const bool initialProxyPreferred = perceptualResidencyEnabled\n            && initialTerrainResidency.tier != vf::SceneRepresentationTier::Detailed;\n        TerrainBuildResult initialTerrain{};\n        if (runtimeFeatures.terrainRender && !initialProxyPreferred) {\n            initialTerrain = buildTerrainLod(\n                lodCenterDirection, initialCameraPlanet, initialViewForwardPlanet,\n                initialMotionLod, {});'''
if text.count(old) != 1:
    raise SystemExit(f'initial build anchor expected once, found {text.count(old)}')
text = text.replace(old, new, 1)

old2 = '''        bool usingDistantEarthGlobe = camera.physicsFrameBodyId() != asterId\n            || camera.altitude() > 900000.0;'''
new2 = '''        bool usingDistantEarthGlobe = initialProxyPreferred\n            || camera.physicsFrameBodyId() != asterId\n            || camera.altitude() > 900000.0;'''
if text.count(old2) != 1:
    raise SystemExit(f'initial globe anchor expected once, found {text.count(old2)}')
text = text.replace(old2, new2, 1)

# Explicit evidence marker: far residency must prove no near-terrain startup build occurred.
old3 = '''        if (runtimeFeatures.terrainRender)\n            renderer.uploadPlanetMesh(usingDistantEarthGlobe ? earthGlobeRenderMesh : nearTerrain);'''
new3 = '''        if (runtimeFeatures.terrainRender) {\n            renderer.uploadPlanetMesh(usingDistantEarthGlobe ? earthGlobeRenderMesh : nearTerrain);\n            std::cout << "R24 INITIAL RESIDENCY altitude_m=" << initialAltitudeMeters\n                      << " tier=" << static_cast<int>(initialTerrainResidency.tier)\n                      << " proxy=" << (initialProxyPreferred ? 1 : 0)\n                      << " near_terrain_built=" << (nearTerrain ? 1 : 0) << '\\n';\n        }'''
if text.count(old3) != 1:
    raise SystemExit(f'initial upload anchor expected once, found {text.count(old3)}')
text = text.replace(old3, new3, 1)

path.write_text(text, encoding='utf-8')
print('R24 far initial residency integrated: detailed startup can be skipped')
