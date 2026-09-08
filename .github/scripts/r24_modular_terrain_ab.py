#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "native/src/app/Main.cpp"
RENDER_HPP = ROOT / "native/include/vf/render/VulkanRenderer.hpp"
RENDER_CPP = ROOT / "native/src/render/VulkanRenderer.cpp"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing anchor for {label}")
    return text.replace(old, new, 1)


main = MAIN.read_text(encoding="utf-8")
if "R24_MODULAR_TERRAIN_AB_V1" not in main:
    main = replace_once(
        main,
        '#include "vf/physics/PhysicsWorld.hpp"\n',
        '#include "vf/app/RuntimeFeatureFlags.hpp"\n#include "vf/physics/PhysicsWorld.hpp"\n',
        "feature include",
    )
    main = replace_once(
        main,
        '        vf::VulkanRenderer renderer{platform.window()};\n',
        '        vf::VulkanRenderer renderer{platform.window()};\n'
        '        // R24_MODULAR_TERRAIN_AB_V1: all heavyweight systems are moving behind explicit\n'
        '        // runtime gates. Terrain can be removed from rendering and streaming while the\n'
        '        // mathematical planet surface remains authoritative for coordinates/collision.\n'
        '        const vf::RuntimeFeatureFlags runtimeFeatures = vf::RuntimeFeatureFlags::fromEnvironment();\n'
        '        runtimeFeatures.print();\n',
        "feature construction",
    )

    globe_old = '''        vf::PlanetMesh earthGlobeMesh = vf::buildPlanetGlobeSurface(planet, 96U, 1.0);\n        for (auto& vertex : earthGlobeMesh.vertices) {\n            const glm::dvec3 pPlanet = glm::dvec3(vertex.position);\n            const glm::dvec3 nPlanet = safeNormalize(glm::dvec3(vertex.normal));\n            vertex.position = glm::vec3(toSurfacePoint(pPlanet));\n            vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(nPlanet)));\n        }\n        const auto earthGlobeRenderMesh = std::make_shared<const vf::PreparedPlanetMesh>(\n            vf::preparePlanetMesh(std::move(earthGlobeMesh), true));\n'''
    globe_new = '''        std::shared_ptr<const vf::PreparedPlanetMesh> earthGlobeRenderMesh{};\n        if (runtimeFeatures.terrainRender) {\n            vf::PlanetMesh earthGlobeMesh = vf::buildPlanetGlobeSurface(planet, 96U, 1.0);\n            for (auto& vertex : earthGlobeMesh.vertices) {\n                const glm::dvec3 pPlanet = glm::dvec3(vertex.position);\n                const glm::dvec3 nPlanet = safeNormalize(glm::dvec3(vertex.normal));\n                vertex.position = glm::vec3(toSurfacePoint(pPlanet));\n                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(nPlanet)));\n            }\n            earthGlobeRenderMesh = std::make_shared<const vf::PreparedPlanetMesh>(\n                vf::preparePlanetMesh(std::move(earthGlobeMesh), true));\n        }\n'''
    main = replace_once(main, globe_old, globe_new, "distant globe gate")

    initial_old = '''        TerrainBuildResult initialTerrain = buildTerrainLod(\n            lodCenterDirection, initialCameraPlanet, initialViewForwardPlanet, {});\n'''
    initial_new = '''        TerrainBuildResult initialTerrain{};\n        if (runtimeFeatures.terrainWorkEnabled()) {\n            initialTerrain = buildTerrainLod(\n                lodCenterDirection, initialCameraPlanet, initialViewForwardPlanet, {});\n        } else {\n            std::cout << "R24 TERRAIN_BYPASS render=0 streaming=0 initial_synthesis=0\\n";\n        }\n'''
    main = replace_once(main, initial_old, initial_new, "initial terrain gate")

    upload_old = '''        renderer.uploadPlanetMesh(usingDistantEarthGlobe ? earthGlobeRenderMesh : nearTerrain);\n        std::future<TerrainBuildResult> terrainBuildFuture{};\n'''
    upload_new = '''        if (runtimeFeatures.terrainRender)\n            renderer.uploadPlanetMesh(usingDistantEarthGlobe ? earthGlobeRenderMesh : nearTerrain);\n        else\n            renderer.clearPlanetMesh();\n        std::future<TerrainBuildResult> terrainBuildFuture{};\n'''
    main = replace_once(main, upload_old, upload_new, "initial render gate")

    main = replace_once(
        main,
        '            if (streaming.useDistantGlobe != usingDistantEarthGlobe) {\n',
        '            if (runtimeFeatures.terrainRender\n'
        '                && streaming.useDistantGlobe != usingDistantEarthGlobe) {\n',
        "mode switch render gate",
    )
    main = replace_once(
        main,
        '            if (streaming.requestBuild || viewPrefetchExpired) {\n',
        '            if (runtimeFeatures.terrainWorkEnabled()\n'
        '                && (streaming.requestBuild || viewPrefetchExpired)) {\n',
        "stream request gate",
    )
    main = replace_once(
        main,
        '            if (terrainBuildInFlight\n                && terrainBuildFuture.wait_for(std::chrono::milliseconds{0})\n',
        '            if (runtimeFeatures.terrainWorkEnabled()\n'
        '                && terrainBuildInFlight\n'
        '                && terrainBuildFuture.wait_for(std::chrono::milliseconds{0})\n',
        "stream completion gate",
    )

# A visual/streaming feature gate must never erase gameplay authority. The first A/B version
# intentionally bypassed every terrain-related build to isolate performance, but that also left
# RegionalHydrology empty and changed collision/ecology/canyon targeting. Keep the deterministic
# regional authority alive while bypassing only expensive render mesh synthesis.
if "R24_SURFACE_AUTHORITY_DECOUPLED_V1" not in main:
    old = '''        } else {\n            std::cout << "R24 TERRAIN_BYPASS render=0 streaming=0 initial_synthesis=0\\n";\n        }\n        std::cout << "R24 PERF terrain_build_ms=" << initialTerrain.buildMilliseconds\n'''
    new = '''        } else {\n            // R24_SURFACE_AUTHORITY_DECOUPLED_V1: render/streaming are optional clients.\n            // Collision, geography, hydrology and evidence targeting keep the same authoritative\n            // surface state even when no terrain triangles are ever generated or uploaded.\n            vf::RegionalHydrologyConfig authorityHydroConfig{};\n            const double authorityAltitude = std::max(\n                0.0, glm::length(initialCameraPlanet) - planet.radius);\n            authorityHydroConfig.resolution = authorityAltitude < 25000.0 ? 193U\n                : (authorityAltitude < 150000.0 ? 129U : 81U);\n            authorityHydroConfig.halfExtentMeters = 220000.0;\n            authorityHydroConfig.maxIncisionMeters = std::min(3000.0, planet.maxElevation * 0.10);\n            authorityHydroConfig.riverHeadAccumulationFraction = 0.0012;\n            authorityHydroConfig.fullChannelAccumulationFraction = 0.022;\n            initialTerrain.hydrology = std::make_shared<vf::RegionalHydrology>(\n                planet, safeNormalize(lodCenterDirection, patchUp), authorityHydroConfig);\n            std::cout << "R24 TERRAIN_BYPASS render=0 streaming=0 initial_synthesis=0"\n                      << " surface_authority=1 hydrology=1\\n";\n        }\n        std::cout << "R24 PERF terrain_build_ms=" << initialTerrain.buildMilliseconds\n'''
    main = replace_once(main, old, new, "surface authority decoupling")

MAIN.write_text(main, encoding="utf-8")

hpp = RENDER_HPP.read_text(encoding="utf-8")
if "void clearPlanetMesh();" not in hpp:
    hpp = replace_once(
        hpp,
        '    void uploadPlanetMesh(std::shared_ptr<const PreparedPlanetMesh> mesh);\n',
        '    void uploadPlanetMesh(std::shared_ptr<const PreparedPlanetMesh> mesh);\n'
        '    // Explicit empty-world state used by runtime module gates and A/B performance tests.\n'
        '    void clearPlanetMesh();\n',
        "renderer clear declaration",
    )
RENDER_HPP.write_text(hpp, encoding="utf-8")

cpp = RENDER_CPP.read_text(encoding="utf-8")
if "void VulkanRenderer::clearPlanetMesh()" not in cpp:
    anchor = '''void VulkanRenderer::uploadStaticMeshForFrame(std::uint32_t frame) {\n'''
    impl = '''void VulkanRenderer::clearPlanetMesh() {\n    pendingStaticMesh_.reset();\n    ++staticMeshGeneration_;\n    if (staticMeshGeneration_ == 0U) {\n        staticMeshGeneration_ = 1U;\n        staticUploadScheduler_.reset();\n    }\n    SDL_Log("R24 MODULE terrain static mesh cleared generation=%llu",\n        static_cast<unsigned long long>(staticMeshGeneration_));\n}\n\n'''
    cpp = replace_once(cpp, anchor, impl + anchor, "renderer clear implementation")
RENDER_CPP.write_text(cpp, encoding="utf-8")

print("materialized R24 modular terrain A/B runtime gate")
