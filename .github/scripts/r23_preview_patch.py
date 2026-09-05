from pathlib import Path

path = Path("native/src/app/Main.cpp")
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f"R23 patch anchor missing:\n{old[:240]}")
    text = text.replace(old, new, 1)

replace_once(
    '#include "vf/world/CelestialPhysicsFrame.hpp"\n#include "vf/world/CelestialSystem.hpp"\n#include "vf/world/PlanetSurface.hpp"',
    '#include "vf/world/AstroTime.hpp"\n#include "vf/world/CelestialPhysicsFrame.hpp"\n#include "vf/world/CelestialSystem.hpp"\n#include "vf/world/PlanetSurface.hpp"\n#include "vf/world/RegionalHydrology.hpp"')
replace_once(
    '#include <cstdint>\n#include <exception>',
    '#include <cstdint>\n#include <cstdlib>\n#include <exception>')
replace_once(
    '#include <sstream>\n#include <utility>',
    '#include <sstream>\n#include <string>\n#include <string_view>\n#include <utility>')

# Capture-only deterministic target selection. This does not invent geometry: it selects a real
# location by the authoritative terrain fields, then the normal runtime renders it.
anchor = '    bool found = false;\n\n    for (std::uint32_t i = 0; i < sampleCount; ++i) {'
insert = '''    bool found = false;\n\n    if (const char* targetEnv = std::getenv("VF_TERRAIN_TARGET"); targetEnv != nullptr && *targetEnv != '\\0') {\n        const std::string_view target{targetEnv};\n        constexpr std::uint32_t evidenceSamples = 16384U;\n        glm::dvec3 evidenceBest = preferred;\n        double evidenceScore = -std::numeric_limits<double>::infinity();\n        bool evidenceFound = false;\n        for (std::uint32_t i = 0; i < evidenceSamples; ++i) {\n            const double y = 1.0 - 2.0 * (static_cast<double>(i) + 0.5)\n                / static_cast<double>(evidenceSamples);\n            const double radial = std::sqrt(std::max(0.0, 1.0 - y * y));\n            const double a = goldenAngle * static_cast<double>(i);\n            const glm::dvec3 d{std::cos(a) * radial, y, std::sin(a) * radial};\n            const vf::PlanetTerrainSample terrain = vf::samplePlanetTerrain(planet, d);\n            const double aboveSea = terrain.elevationMeters - planet.seaLevelElevationMeters;\n            const double sunElevation = glm::dot(d, sunDirection);\n            if (aboveSea < 8.0 || terrain.submerged(planet) || sunElevation < 0.10) continue;\n\n            const double height01 = std::clamp(aboveSea / std::max(1.0, planet.maxElevation), 0.0, 1.0);\n            double score = -1.0e9;\n            if (target == "mountain") {\n                score = terrain.mountain * 3.4 + height01 * 1.8 + terrain.plateBoundary * 0.4;\n            } else if (target == "highland") {\n                score = terrain.plateau * 2.6 + terrain.hills * 1.3 + height01 * 0.8\n                    - terrain.mountain * 0.7;\n            } else if (target == "canyon") {\n                score = terrain.canyon * 3.6 + terrain.aridity * 0.8 + terrain.hills * 0.5\n                    + height01 * 0.4;\n            } else if (target == "coast") {\n                score = terrain.coastalCliff * 4.0 + terrain.plateBoundary * 0.6\n                    - height01 * 0.3;\n            } else if (target == "dunes") {\n                score = terrain.dunes * 3.5 + terrain.aridity * 1.3\n                    - terrain.mountain * 0.8;\n            } else if (target == "wetland") {\n                score = terrain.wetland * 4.0 + terrain.moisture * 0.7\n                    - height01 * 0.8;\n            } else if (target == "glacier") {\n                score = terrain.glacier * 4.0 + height01 * 0.6;\n            } else if (target == "volcano") {\n                score = terrain.volcano * 4.0 + height01 * 0.4;\n            } else if (target == "hydrology" || target == "river") {\n                // Prefer a broad elevated but non-glaciated drainage province. The R23 regional\n                // Priority-Flood bake then determines the actual channels from DEM topology.\n                score = terrain.hills * 1.5 + terrain.plateau * 1.3 + terrain.moisture * 0.5\n                    + height01 * 0.8 - terrain.mountain * 0.9 - terrain.glacier * 1.2;\n            }\n            if (!evidenceFound || score > evidenceScore) {\n                evidenceFound = true;\n                evidenceScore = score;\n                evidenceBest = d;\n            }\n        }\n        if (evidenceFound) {\n            std::cout << "R23 terrain target: " << target << " score=" << evidenceScore << '\\n';\n            return safeNormalize(evidenceBest, preferred);\n        }\n    }\n\n    for (std::uint32_t i = 0; i < sampleCount; ++i) {'''
replace_once(anchor, insert)

replace_once(
    '        vf::CelestialSystem celestial;\n',
    '''        vf::CelestialSystem celestial;\n        double celestialTimeScale = 1.0;\n        if (const char* scaleEnv = std::getenv("VF_CELESTIAL_TIME_SCALE"); scaleEnv != nullptr) {\n            try { celestialTimeScale = std::clamp(std::stod(scaleEnv), 0.0, 200000.0); }\n            catch (...) { celestialTimeScale = 1.0; }\n        }\n        vf::CelestialSimulationClock celestialClock{{60.0, celestialTimeScale, 4096U}};\n''')

# Add a real orbiting moon after the camera exists so its initial apparent direction is guaranteed
# to be in the user's forward sky, while still using a physically valid circular tangential state.
replace_once(
    '        vf::PlanetCamera camera{planet, &celestial, asterId, spawnDirection};\n',
    '''        vf::PlanetCamera camera{planet, &celestial, asterId, spawnDirection};\n\n        constexpr double moonOrbitRadius = 384400000.0;\n        vf::CelestialBody luna{};\n        luna.type = vf::CelestialBodyType::Moon;\n        luna.name = "Luna";\n        luna.radiusMeters = 1737400.0;\n        luna.massKg = 7.342e22;\n        luna.orbitParentId = asterId;\n        const glm::dvec3 moonRadial = safeNormalize(\n            camera.forwardDirection() + camera.up() * 0.34,\n            stableTangent(spawnDirection));\n        glm::dvec3 moonTangent = glm::cross(moonRadial, camera.up());\n        if (glm::dot(moonTangent, moonTangent) < 1.0e-12) moonTangent = stableTangent(moonRadial);\n        moonTangent = safeNormalize(moonTangent, stableTangent(moonRadial));\n        luna.position = aster.position + moonRadial * moonOrbitRadius;\n        luna.linearVelocity = aster.linearVelocity\n            + moonTangent * circularOrbitSpeed(aster.massKg, moonOrbitRadius);\n        luna.spinAxis = aster.spinAxis;\n        luna.spinRateRadPerSecond = 2.0 * kPi / (27.321661 * 86400.0);\n        luna.visibleAlbedo = {0.62, 0.64, 0.68};\n        const std::uint32_t moonId = celestial.addBody(luna);\n''')

# Build one physical drainage field per streamed regional terrain window and use its incision in the
# near/mid rings. No pointwise river/canyon noise is consulted for this displacement.
replace_once(
    '            const glm::dvec3 centerNorth = safeNormalize(glm::cross(centerUp, centerEast), patchZ);\n\n            struct Ring {',
    '''            const glm::dvec3 centerNorth = safeNormalize(glm::cross(centerUp, centerEast), patchZ);\n            vf::RegionalHydrologyConfig hydroConfig{};\n            hydroConfig.resolution = 129U;\n            hydroConfig.halfExtentMeters = 150000.0;\n            hydroConfig.maxIncisionMeters = 320.0;\n            hydroConfig.riverHeadAccumulationFraction = 0.0014;\n            hydroConfig.fullChannelAccumulationFraction = 0.030;\n            const vf::RegionalHydrology hydrology{planet, centerUp, hydroConfig};\n\n            struct Ring {''')
replace_once(
    '                        double elevation = terrain.elevationMeters;\n',
    '''                        double elevation = terrain.elevationMeters;\n                        if (ring.half <= hydroConfig.halfExtentMeters * 1.05) {\n                            const vf::RegionalHydrologySample hydro = hydrology.sample(direction);\n                            elevation -= hydro.incisionMeters;\n                        }\n''')

replace_once(
    '            celestial.step(dt);\n',
    '''            celestialClock.advance(dt, [&](double astroDt) {\n                celestial.step(astroDt);\n            });\n''')
replace_once(
    '            const auto* currentCinder = celestial.body(cinderId);\n            const auto* currentSun = celestial.body(sunId);',
    '            const auto* currentCinder = celestial.body(cinderId);\n            const auto* currentMoon = celestial.body(moonId);\n            const auto* currentSun = celestial.body(sunId);')

# Render the moon using its true integrated world state and angular size, like the existing Cinder
# body proxy. It therefore moves because the N-body state moves, not because of a sky animation.
moon_render_anchor = '''            if (currentCinder != nullptr) {\n                const glm::dvec3 cinderDirection = safeNormalize(\n                    currentCinder->position - camera.position());'''
moon_render_insert = '''            if (currentMoon != nullptr) {\n                const glm::dvec3 moonDirection = safeNormalize(\n                    currentMoon->position - camera.position());\n                const glm::dvec3 moonSurfaceDirection = safeNormalize(\n                    toSurfaceVector(inverseAster * moonDirection));\n                const double moonDistance = glm::length(currentMoon->position - camera.position());\n                const double moonAngularRadius = std::asin(std::clamp(\n                    currentMoon->radiusMeters / std::max(moonDistance, currentMoon->radiusMeters),\n                    0.0, 0.20));\n                constexpr double moonVisualDistance = 17000000.0;\n                const double moonVisualRadius = std::max(\n                    1400.0, std::tan(moonAngularRadius) * moonVisualDistance);\n                vf::appendDebugSphere(\n                    dynamicMesh,\n                    cameraSurface + moonSurfaceDirection * moonVisualDistance,\n                    moonVisualRadius,\n                    {0.72F, 0.74F, 0.78F},\n                    14U,\n                    24U,\n                    {0.0F, 0.88F, 0.0F, 0.0F});\n            }\n            if (currentCinder != nullptr) {\n                const glm::dvec3 cinderDirection = safeNormalize(\n                    currentCinder->position - camera.position());'''
replace_once(moon_render_anchor, moon_render_insert)

path.write_text(text, encoding="utf-8")
print("R23 preview patch applied")
