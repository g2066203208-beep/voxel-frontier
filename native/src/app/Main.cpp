#include "vf/physics/PhysicsWorld.hpp"
#include "vf/platform/SdlPlatform.hpp"
#include "vf/player/CharacterController.hpp"
#include "vf/player/PlanetCamera.hpp"
#include "vf/render/PhysicsDebugMesh.hpp"
#include "vf/render/VulkanRenderer.hpp"
#include "vf/world/AstroTime.hpp"
#include "vf/world/CelestialPhysicsFrame.hpp"
#include "vf/world/CelestialSystem.hpp"
#include "vf/world/PlanetSurface.hpp"
#include "vf/world/RegionalHydrology.hpp"
#include "vf/world/ProceduralEcology.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <exception>
#include <future>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>

#include <glm/common.hpp>
#include <glm/ext/matrix_transform.hpp>
#include <glm/geometric.hpp>
#include <glm/gtc/quaternion.hpp>

namespace {

constexpr double kPi = 3.1415926535897932384626433832795;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-18) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] double smooth01(double value) noexcept {
    const double t = std::clamp(value, 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

// Degenerate fallback only. Camera heading continuity itself is owned by PlanetCamera and is
// parallel-transported over the sphere; terrain patch construction is free to pick a stable local
// tangent because its vertices are converted back into the fixed render frame before upload.
[[nodiscard]] glm::dvec3 stableTangent(const glm::dvec3& upInput) noexcept {
    const glm::dvec3 up = safeNormalize(upInput);
    const glm::dvec3 a = glm::abs(up);
    glm::dvec3 reference{1.0, 0.0, 0.0};
    if (a.y <= a.x && a.y <= a.z) reference = {0.0, 1.0, 0.0};
    else if (a.z <= a.x && a.z <= a.y) reference = {0.0, 0.0, 1.0};
    return safeNormalize(glm::cross(reference, up), {1.0, 0.0, 0.0});
}

[[nodiscard]] double circularOrbitSpeed(double parentMassKg, double radiusMeters) {
    return std::sqrt(vf::CelestialSystem::kGravitationalConstant * parentMassKg / std::max(1.0, radiusMeters));
}

[[nodiscard]] glm::dvec3 findPlayableSpawnDirection(
    const vf::PlanetDefinition& planet,
    const glm::dvec3& sunDirectionInput) {
    // Deterministic Fibonacci-sphere scan. The terrain seed remains untouched; this only chooses a
    // gentle inland point whose initial sun elevation gives a readable warm daylight scene instead
    // of hiding the terrain and vegetation on the night side of the planet.
    constexpr std::uint32_t sampleCount = 2048U;
    constexpr double goldenAngle = 2.39996322972865332223;
    const glm::dvec3 preferred = safeNormalize({0.72, 0.52, 0.46});
    const glm::dvec3 sunDirection = safeNormalize(sunDirectionInput, {1.0, 0.0, 0.0});
    glm::dvec3 best = preferred;
    double bestScore = -std::numeric_limits<double>::infinity();
    bool found = false;

    if (const char* targetEnv = std::getenv("VF_TERRAIN_TARGET"); targetEnv != nullptr && *targetEnv != '\0') {
        const std::string_view target{targetEnv};
        constexpr std::uint32_t evidenceSamples = 16384U;
        glm::dvec3 evidenceBest = preferred;
        double evidenceScore = -std::numeric_limits<double>::infinity();
        bool evidenceFound = false;
        for (std::uint32_t i = 0; i < evidenceSamples; ++i) {
            const double y = 1.0 - 2.0 * (static_cast<double>(i) + 0.5)
                / static_cast<double>(evidenceSamples);
            const double radial = std::sqrt(std::max(0.0, 1.0 - y * y));
            const double a = goldenAngle * static_cast<double>(i);
            const glm::dvec3 d{std::cos(a) * radial, y, std::sin(a) * radial};
            const vf::PlanetTerrainSample terrain = vf::samplePlanetTerrain(planet, d);
            const double aboveSea = terrain.elevationMeters - planet.seaLevelElevationMeters;
            const double sunElevation = glm::dot(d, sunDirection);
            if (aboveSea < 8.0 || terrain.submerged(planet) || sunElevation < 0.10) continue;

            const double height01 = std::clamp(aboveSea / std::max(1.0, planet.maxElevation), 0.0, 1.0);
            double score = -1.0e9;
            if (target == "mountain") {
                score = terrain.mountain * 3.4 + height01 * 1.8 + terrain.plateBoundary * 0.4;
            } else if (target == "highland") {
                score = terrain.plateau * 2.6 + terrain.hills * 1.3 + height01 * 0.8
                    - terrain.mountain * 0.7;
            } else if (target == "canyon") {
                score = terrain.canyon * 3.6 + terrain.aridity * 0.8 + terrain.hills * 0.5
                    + height01 * 0.4;
            } else if (target == "coast") {
                score = terrain.coastalCliff * 4.0 + terrain.plateBoundary * 0.6
                    - height01 * 0.3;
            } else if (target == "dunes") {
                score = terrain.dunes * 3.5 + terrain.aridity * 1.3
                    - terrain.mountain * 0.8;
            } else if (target == "wetland") {
                score = terrain.wetland * 4.0 + terrain.moisture * 0.7
                    - height01 * 0.8;
            } else if (target == "glacier") {
                score = terrain.glacier * 4.0 + height01 * 0.6;
            } else if (target == "volcano") {
                score = terrain.volcano * 4.0 + height01 * 0.4;
            } else if (target == "hydrology" || target == "river") {
                // Prefer a broad elevated but non-glaciated drainage province. The R23 regional
                // Priority-Flood bake then determines the actual channels from DEM topology.
                score = terrain.hills * 1.5 + terrain.plateau * 1.3 + terrain.moisture * 0.5
                    + height01 * 0.8 - terrain.mountain * 0.9 - terrain.glacier * 1.2;
            }
            if (!evidenceFound || score > evidenceScore) {
                evidenceFound = true;
                evidenceScore = score;
                evidenceBest = d;
            }
        }
        if (evidenceFound) {
            std::cout << "R23 terrain target: " << target << " score=" << evidenceScore << '\n';
            return safeNormalize(evidenceBest, preferred);
        }
    }

    for (std::uint32_t i = 0; i < sampleCount; ++i) {
        const double y = 1.0 - 2.0 * (static_cast<double>(i) + 0.5)
            / static_cast<double>(sampleCount);
        const double radial = std::sqrt(std::max(0.0, 1.0 - y * y));
        const double a = goldenAngle * static_cast<double>(i);
        const glm::dvec3 d{std::cos(a) * radial, y, std::sin(a) * radial};
        const vf::PlanetTerrainSample terrain = vf::samplePlanetTerrain(planet, d);
        const double aboveSea = terrain.elevationMeters - planet.seaLevelElevationMeters;
        if (aboveSea < 80.0 || terrain.submerged(planet)) continue;
        if (terrain.mountain > 0.64 || terrain.volcano > 0.68 || terrain.trench > 0.05) continue;

        const glm::dvec3 normal = vf::planetSurfaceNormal(planet, d);
        const double radialAlignment = glm::dot(normal, d);
        if (radialAlignment < 0.952) continue;

        const double sunElevation = glm::dot(d, sunDirection);
        if (sunElevation < 0.24 || sunElevation > 0.82) continue;
        const double warmDaylight = 1.0 - std::clamp(std::abs(sunElevation - 0.48) / 0.34, 0.0, 1.0);
        const double altitudePreference = 1.0 - std::clamp(std::abs(aboveSea - 460.0) / 2200.0, 0.0, 1.0);
        const double oldRegionPreference = 0.5 + 0.5 * glm::dot(d, preferred);
        const double score = radialAlignment * 2.4
            + warmDaylight * 1.15
            + altitudePreference * 0.70
            + oldRegionPreference * 0.14
            + terrain.plateau * 0.10
            + terrain.river * 0.08
            - terrain.mountain * 0.68
            - terrain.volcano * 0.78;
        if (!found || score > bestScore) {
            bestScore = score;
            best = d;
            found = true;
        }
    }
    return safeNormalize(best, preferred);
}

void appendMesh(vf::PlanetMesh& destination, const vf::PlanetMesh& source) {
    const std::uint32_t base = static_cast<std::uint32_t>(destination.vertices.size());
    destination.vertices.insert(destination.vertices.end(), source.vertices.begin(), source.vertices.end());
    destination.indices.reserve(destination.indices.size() + source.indices.size());
    for (const std::uint32_t index : source.indices) destination.indices.push_back(base + index);
}

[[nodiscard]] glm::mat4 makeReverseZViewProjection(
    const glm::dvec3& forward,
    const glm::dvec3& up,
    float aspect) {
    aspect = std::max(aspect, 0.1F);
    const glm::mat4 view = glm::lookAtRH(
        glm::vec3{0.0F},
        glm::vec3(safeNormalize(forward, {0.0, 0.0, -1.0})),
        glm::vec3(safeNormalize(up)));

    constexpr float nearPlane = 0.05F;
    const float f = 1.0F / std::tan(glm::radians(68.0F) * 0.5F);
    glm::mat4 projection{0.0F};
    projection[0][0] = f / aspect;
    projection[1][1] = -f;
    projection[2][3] = -1.0F;
    projection[3][2] = nearPlane;
    return projection * view;
}

} // namespace

int main() {
    try {
        vf::SdlPlatform platform{"Voxel Frontier — Earthlike Planet + Ocean", 1600, 900};
        vf::VulkanRenderer renderer{platform.window()};

        // Earth-scale gameplay planet. Relief is deterministic procedural morphology rather than a
        // literal GIS copy: continents, shelves, abyssal basins, trenches, mountains, plateaus,
        // volcanic hotspots and river valleys all come from one authoritative height query.
        vf::PlanetDefinition planet{};
        planet.seed = 0x71A9F20DULL;
        planet.radius = 6371000.0;
        planet.maxElevation = 8850.0;
        planet.seaLevelElevationMeters = 0.0;
        planet.maxOceanDepthMeters = 11000.0;
        planet.atmosphereHeight = 100000.0;
        constexpr double opticalAtmosphereHeight = 145000.0;
        constexpr double opticalRayleighScaleHeight = 10200.0;

        vf::CelestialSystem celestial;
        double celestialTimeScale = 1.0;
        if (const char* scaleEnv = std::getenv("VF_CELESTIAL_TIME_SCALE"); scaleEnv != nullptr) {
            try { celestialTimeScale = std::clamp(std::stod(scaleEnv), 0.0, 200000.0); }
            catch (...) { celestialTimeScale = 1.0; }
        }
        vf::CelestialSimulationClock celestialClock{{60.0, celestialTimeScale, 4096U}};

        vf::CelestialBody sun{};
        sun.type = vf::CelestialBodyType::Star;
        sun.name = "Helion";
        sun.radiusMeters = 696340000.0;
        sun.massKg = 1.98847e30;
        sun.position = {};
        sun.spinAxis = safeNormalize({0.0, 1.0, 0.12});
        sun.spinRateRadPerSecond = 2.0 * kPi / (25.38 * 86400.0);
        sun.luminosityWatts = 3.828e26;
        const std::uint32_t sunId = celestial.addBody(sun);

        constexpr double asterOrbitRadius = 149597870700.0;
        vf::CelestialBody aster{};
        aster.type = vf::CelestialBodyType::Planet;
        aster.name = "Aster";
        aster.radiusMeters = planet.radius;
        aster.massKg = 5.9722e24;
        aster.gameplaySurfaceGravityMps2 = 9.80665;
        aster.gravityFalloffStartRadiusMeters = planet.radius + planet.atmosphereHeight;
        aster.gravityFalloffPower = 7.0;
        aster.gravityInfluenceRadiusMeters = planet.radius + 900000.0;
        aster.physicsBubbleRadiusMeters = planet.radius + 1300000.0;
        aster.position = {-asterOrbitRadius, 0.0, 0.0};
        aster.orbitParentId = sunId;
        aster.linearVelocity = {0.0, 0.0, -circularOrbitSpeed(sun.massKg, asterOrbitRadius)};
        aster.spinAxis = {0.0, 1.0, 0.0};
        aster.spinRateRadPerSecond = 2.0 * kPi / 86164.0905;
        aster.visibleAlbedo = {0.20, 0.42, 0.18};
        aster.atmosphere.enabled = true;
        aster.atmosphere.heightMeters = planet.atmosphereHeight;
        aster.atmosphere.surfacePressurePa = 101325.0;
        aster.atmosphere.surfaceTemperatureK = 288.15;
        aster.atmosphere.scaleHeightMeters = 8500.0;
        aster.atmosphere.lapseRateKPerM = 0.0065;
        aster.atmosphere.rayleighRgb = {0.16, 0.43, 1.00};
        aster.atmosphere.mieStrength = 0.08;
        aster.atmosphere.prevailingWind = {};
        aster.weather.windMultiplier = 0.0;
        aster.weather.stormIntensity = 0.0;
        const std::uint32_t asterId = celestial.addBody(aster);

        constexpr double cinderOrbitRadius = 227939200000.0;
        vf::CelestialBody cinder{};
        cinder.type = vf::CelestialBodyType::Planet;
        cinder.name = "Cinder";
        cinder.radiusMeters = 3389500.0;
        cinder.massKg = 6.4171e23;
        cinder.gameplaySurfaceGravityMps2 = 3.71;
        cinder.gravityInfluenceRadiusMeters = cinder.radiusMeters + 550000.0;
        cinder.physicsBubbleRadiusMeters = cinder.radiusMeters + 800000.0;
        cinder.position = {0.0, 0.0, cinderOrbitRadius};
        cinder.orbitParentId = sunId;
        cinder.linearVelocity = {-circularOrbitSpeed(sun.massKg, cinderOrbitRadius), 0.0, 0.0};
        cinder.visibleAlbedo = {0.62, 0.30, 0.22};
        const std::uint32_t cinderId = celestial.addBody(cinder);

        const glm::dvec3 initialSunDirectionPlanet = safeNormalize(
            sun.position - aster.position, {1.0, 0.0, 0.0});
        const glm::dvec3 spawnDirection = findPlayableSpawnDirection(planet, initialSunDirectionPlanet);
        const vf::PlanetTerrainSample spawnTerrain = vf::samplePlanetTerrain(planet, spawnDirection);
        vf::PlanetCamera camera{planet, &celestial, asterId, spawnDirection};

        constexpr double moonOrbitRadius = 384400000.0;
        vf::CelestialBody luna{};
        luna.type = vf::CelestialBodyType::Moon;
        luna.name = "Luna";
        luna.radiusMeters = 1737400.0;
        luna.massKg = 7.342e22;
        luna.orbitParentId = asterId;
        const glm::dvec3 moonRadial = safeNormalize(
            camera.forwardDirection() + camera.up() * 0.34,
            stableTangent(spawnDirection));
        glm::dvec3 moonTangent = glm::cross(moonRadial, camera.up());
        if (glm::dot(moonTangent, moonTangent) < 1.0e-12) moonTangent = stableTangent(moonRadial);
        moonTangent = safeNormalize(moonTangent, stableTangent(moonRadial));
        luna.position = aster.position + moonRadial * moonOrbitRadius;
        luna.linearVelocity = aster.linearVelocity
            + moonTangent * circularOrbitSpeed(aster.massKg, moonOrbitRadius);
        luna.spinAxis = aster.spinAxis;
        luna.spinRateRadPerSecond = 2.0 * kPi / (27.321661 * 86400.0);
        luna.visibleAlbedo = {0.62, 0.64, 0.68};
        const std::uint32_t moonId = celestial.addBody(luna);

        // Deterministic evidence camera. This remains the real PlanetCamera and the real Vulkan
        // renderer; only its initial pose is selected explicitly so CI cannot accidentally stare at
        // empty sky after synthetic mouse input. Production runs do not set this environment flag.
        if (const char* aerialEnv = std::getenv("VF_CAPTURE_AERIAL");
            aerialEnv != nullptr && std::string_view{aerialEnv} == "1") {
            double aerialAltitude = 5200.0;
            if (const char* altitudeEnv = std::getenv("VF_CAPTURE_ALTITUDE_METERS");
                altitudeEnv != nullptr && *altitudeEnv != '\0') {
                try { aerialAltitude = std::clamp(std::stod(altitudeEnv), 800.0, 18000.0); }
                catch (...) { aerialAltitude = 5200.0; }
            }
            const double localSurfaceRadius = vf::planetSurfaceRadius(planet, spawnDirection);
            const glm::dvec3 localOffset = spawnDirection * (localSurfaceRadius + aerialAltitude);
            const glm::dvec3 worldOffset = aster.orientation * localOffset;
            const glm::dvec3 worldUp = safeNormalize(worldOffset, spawnDirection);
            const glm::dvec3 angularVelocity = safeNormalize(aster.spinAxis, {0.0, 1.0, 0.0})
                * aster.spinRateRadPerSecond;
            camera.setExternalWorldState(
                aster.position + worldOffset,
                aster.linearVelocity + glm::cross(angularVelocity, worldOffset),
                false);
            const glm::dvec3 tangent = stableTangent(worldUp);
            camera.setViewDirectionWorld(
                safeNormalize(tangent * 0.58 - worldUp * 0.82, -worldUp),
                worldUp);
            std::cout << "R23 deterministic aerial camera altitude="
                      << aerialAltitude << " m\n";
        }

        if (const char* celestialTargetEnv = std::getenv("VF_CELESTIAL_TARGET");
            celestialTargetEnv != nullptr && *celestialTargetEnv != '\0') {
            const std::string_view celestialTarget{celestialTargetEnv};
            if (celestialTarget == "sun") {
                camera.setViewDirectionWorld(
                    sun.position - camera.position(), camera.up());
                std::cout << "R23 celestial target: sun\n";
            } else if (celestialTarget == "moon") {
                camera.setViewDirectionWorld(
                    luna.position - camera.position(), camera.up());
                std::cout << "R23 celestial target: moon\n";
            }
        }
        std::cout << "Spawn land elevation: " << std::fixed << std::setprecision(1)
                  << spawnTerrain.elevationMeters << " m\n";
        const vf::CelestialBody* initialAster = celestial.body(asterId);
        if (initialAster == nullptr) throw std::runtime_error("Aster failed to initialize");
        vf::CelestialPhysicsFrame asterFrame{asterId};

        const glm::dquat initialInverseAster = glm::conjugate(glm::normalize(initialAster->orientation));
        const glm::dvec3 initialCameraPlanet = initialInverseAster * (camera.position() - initialAster->position);
        const glm::dvec3 patchUp = safeNormalize(initialCameraPlanet);
        const glm::dvec3 patchEast = stableTangent(patchUp);
        const glm::dvec3 patchZ = safeNormalize(glm::cross(patchEast, patchUp), {0.0, 0.0, -1.0});
        const glm::dvec3 patchOriginPlanet = patchUp * vf::planetSurfaceRadius(planet, patchUp);
        const vf::SurfaceRenderFrame surfaceFrame{
            patchOriginPlanet,
            patchEast,
            patchUp,
            patchZ,
        };

        const auto toSurfacePoint = [&](const glm::dvec3& planetPoint) {
            const glm::dvec3 delta = planetPoint - patchOriginPlanet;
            return glm::dvec3{
                glm::dot(delta, patchEast),
                glm::dot(delta, patchUp),
                glm::dot(delta, patchZ),
            };
        };
        const auto toSurfaceVector = [&](const glm::dvec3& planetVector) {
            return glm::dvec3{
                glm::dot(planetVector, patchEast),
                glm::dot(planetVector, patchUp),
                glm::dot(planetVector, patchZ),
            };
        };

        glm::dvec3 lodCenterDirection = patchUp;
        auto buildTerrainLod = [&](const glm::dvec3& centerDirection) {
            vf::PlanetMesh mesh{};
            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);
            const glm::dvec3 centerEast = stableTangent(centerUp);
            const glm::dvec3 centerNorth = safeNormalize(glm::cross(centerUp, centerEast), patchZ);
            vf::RegionalHydrologyConfig hydroConfig{};
            hydroConfig.resolution = 129U;
            hydroConfig.halfExtentMeters = 150000.0;
            hydroConfig.maxIncisionMeters = 320.0;
            hydroConfig.riverHeadAccumulationFraction = 0.0014;
            hydroConfig.fullChannelAccumulationFraction = 0.030;
            const vf::RegionalHydrology hydrology{planet, centerUp, hydroConfig};

            struct Ring {
                double half;
                double inner;
                std::uint32_t resolution;
            };
            // Geometry-clipmap style nested windows. The inner ring keeps walking-scale density;
            // each outer ring is hollow and the fine edge morphs onto positions sampled on the next
            // coarser grid. This follows mature clipmap seam handling instead of hiding cracks with
            // metre-scale vertical skirts/insets.
            const std::array<Ring, 5> rings{{
                {4096.0,       0.0, 320U},
                {24576.0,   3900.0, 192U},
                {131072.0, 23500.0, 160U},
                {655360.0,126000.0, 128U},
                {2600000.0,630000.0,104U},
            }};

            for (std::size_t ringIndex = 0; ringIndex < rings.size(); ++ringIndex) {
                const Ring& ring = rings[ringIndex];
                const std::uint32_t stride = ring.resolution + 1U;
                const std::uint32_t terrainBase = static_cast<std::uint32_t>(mesh.vertices.size());
                for (std::uint32_t y = 0; y <= ring.resolution; ++y) {
                    const double fy = static_cast<double>(y) / static_cast<double>(ring.resolution);
                    const double northMeters = -ring.half + 2.0 * ring.half * fy;
                    for (std::uint32_t x = 0; x <= ring.resolution; ++x) {
                        const double fx = static_cast<double>(x) / static_cast<double>(ring.resolution);
                        const double eastMeters = -ring.half + 2.0 * ring.half * fx;
                        const glm::dvec3 direction = safeNormalize(
                            centerUp + centerEast * (eastMeters / planet.radius)
                                + centerNorth * (northMeters / planet.radius),
                            centerUp);
                        const vf::PlanetTerrainSample terrain = vf::samplePlanetTerrain(planet, direction);
                        glm::dvec3 normalPlanet = vf::planetSurfaceNormal(planet, direction);
                        double elevation = terrain.elevationMeters;
                        if (ring.half <= hydroConfig.halfExtentMeters * 1.05) {
                            const vf::RegionalHydrologySample hydro = hydrology.sample(direction);
                            elevation -= hydro.incisionMeters;
                        }

                        if (ringIndex + 1U < rings.size()) {
                            const Ring& nextRing = rings[ringIndex + 1U];
                            const double nextCell = 2.0 * nextRing.half
                                / static_cast<double>(nextRing.resolution);
                            const double edge = std::max(std::abs(eastMeters), std::abs(northMeters)) / ring.half;
                            const double morph = smooth01((edge - 0.78) / 0.20);
                            if (morph > 0.0) {
                                const double snappedEast = std::round(eastMeters / nextCell) * nextCell;
                                const double snappedNorth = std::round(northMeters / nextCell) * nextCell;
                                const glm::dvec3 coarseDirection = safeNormalize(
                                    centerUp + centerEast * (snappedEast / planet.radius)
                                        + centerNorth * (snappedNorth / planet.radius),
                                    direction);
                                const vf::PlanetTerrainSample coarseTerrain = vf::samplePlanetTerrain(
                                    planet, coarseDirection);
                                const glm::dvec3 coarseNormal = vf::planetSurfaceNormal(planet, coarseDirection);
                                elevation += (coarseTerrain.elevationMeters - elevation) * morph;
                                normalPlanet = safeNormalize(
                                    normalPlanet * (1.0 - morph) + coarseNormal * morph,
                                    normalPlanet);
                            }
                        }

                        const glm::dvec3 worldPoint = direction * (planet.radius + elevation);
                        vf::PlanetVertex vertex{};
                        vertex.position = glm::vec3(toSurfacePoint(worldPoint));
                        vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(normalPlanet)));
                        vertex.color = vf::planetTerrainColor(planet, terrain);
                        vertex.material = vf::planetTerrainMaterial(planet, terrain);
                        mesh.vertices.push_back(vertex);
                    }
                }

                for (std::uint32_t y = 0; y < ring.resolution; ++y) {
                    const double cy = -ring.half + 2.0 * ring.half
                        * (static_cast<double>(y) + 0.5) / ring.resolution;
                    for (std::uint32_t x = 0; x < ring.resolution; ++x) {
                        const double cx = -ring.half + 2.0 * ring.half
                            * (static_cast<double>(x) + 0.5) / ring.resolution;
                        if (ring.inner > 0.0 && std::max(std::abs(cx), std::abs(cy)) < ring.inner) continue;
                        const std::uint32_t i0 = terrainBase + y * stride + x;
                        const std::uint32_t i1 = i0 + 1U;
                        const std::uint32_t i2 = i0 + stride;
                        const std::uint32_t i3 = i2 + 1U;
                        mesh.indices.insert(mesh.indices.end(), {i0, i2, i1, i1, i2, i3});
                    }
                }
            }

            // Near-field ecology is rebuilt from stable grid-cell IDs and authoritative terrain
            // queries, so trees/rocks/grass move with streaming without changing identity or height.
            appendMesh(mesh, vf::buildProceduralEcology(planet, centerUp, surfaceFrame));

            // The orbital proxy is still deliberately cheaper than the local clipmaps, but 96
            // subdivisions removes the giant polygon blocks visible in V7's 48-subdivision Earth.
            vf::PlanetMesh proxy = vf::buildPlanetSurface(planet, 96U);
            constexpr double proxyInset = 24.0;
            for (auto& vertex : proxy.vertices) {
                glm::dvec3 p = glm::dvec3(vertex.position);
                const double r = glm::length(p);
                if (r > proxyInset + 1.0) p *= (r - proxyInset) / r;
                vertex.position = glm::vec3(toSurfacePoint(p));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
            }
            appendMesh(mesh, proxy);

            // Water has exactly two representations, never five stacked transparent squares:
            // a high-resolution local patch and one global geoid shell. The shader cross-fades them
            // by altitude before the local square boundary can enter the visible horizon.
            vf::PlanetMesh localOcean = vf::buildOceanSurfacePatch(
                planet, centerUp, 520000.0, 256U, 0.0);
            for (auto& vertex : localOcean.vertices) {
                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
                vertex.material.w = -10.0F;
            }
            appendMesh(mesh, localOcean);

            vf::PlanetMesh oceanProxy{};
            vf::appendOceanSurfaceProxy(
                oceanProxy,
                {},
                planet.radius + planet.seaLevelElevationMeters - 1.5,
                128U);
            for (auto& vertex : oceanProxy.vertices) {
                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
                vertex.material.w = -20.0F;
            }
            appendMesh(mesh, oceanProxy);
            return mesh;
        };

        vf::PlanetMesh staticTerrain = buildTerrainLod(lodCenterDirection);
        renderer.uploadPlanetMesh(staticTerrain);
        std::future<std::pair<glm::dvec3, vf::PlanetMesh>> terrainBuildFuture{};
        bool terrainBuildInFlight = false;

        // Local rotating planet frame for high-quality ground physics while CelestialSystem remains
        // authoritative for the actual moving body in the solar-system frame.
        vf::CelestialSystem localGravitySystem;
        vf::CelestialBody localGravityBody = aster;
        localGravityBody.position = {};
        localGravityBody.linearVelocity = {};
        localGravityBody.orbitParentId = 0U;
        localGravityBody.spinRateRadPerSecond = 0.0;
        localGravityBody.orientation = {1.0, 0.0, 0.0, 0.0};
        localGravityBody.atmosphere.enabled = false;
        localGravityBody.weather.windMultiplier = 0.0;
        const std::uint32_t localGravityId = localGravitySystem.addBody(localGravityBody);

        vf::PhysicsEnvironment environment{};
        environment.planet = planet;
        environment.surfaceGravity = 9.80665;
        environment.celestialSystem = &localGravitySystem;
        environment.primaryCelestialBodyId = localGravityId;
        environment.atmosphere.prevailingWind = {};
        environment.atmosphere.gustAmplitude = 0.0;
        environment.weather.windMultiplier = 0.0;
        environment.ocean.enabled = true;
        environment.ocean.surfaceRadius = planet.radius + planet.seaLevelElevationMeters;
        environment.ocean.densityKgPerM3 = 1025.0;
        environment.ocean.viscosityPaS = 0.00108;
        environment.ocean.meanCurrent = {};
        vf::PhysicsWorld physics{environment};

        vf::CharacterControllerSettings characterSettings{};
        characterSettings.walkSpeed = 9.0;
        characterSettings.sprintSpeed = 18.0;
        characterSettings.maxSlopeAngleRadians = glm::radians(50.0);
        characterSettings.stepHeight = 0.45;
        vf::CharacterController character{physics, characterSettings};
        character.resetFromEye(initialCameraPlanet, {}, true);

        std::cout << "Voxel Frontier Earthlike planet runtime\n";
        std::cout << "Generic structural damage | Earthlike relief | continuous ocean geoid\n";
        std::cout << "Async terrain synthesis | morphing clipmaps | deterministic stylized ecology\n";

        using Clock = std::chrono::steady_clock;
        auto previous = Clock::now();
        double diagnosticsTime = 0.0;
        std::uint64_t diagnosticsFrames = 0;
        double lodCooldown = 0.0;

        while (platform.pumpEvents()) {
            const auto now = Clock::now();
            const double dt = std::clamp(
                std::chrono::duration<double>(now - previous).count(),
                1.0 / 500.0,
                0.05);
            previous = now;
            celestialClock.advance(dt, [&](double astroDt) {
                celestial.step(astroDt);
            });

            auto* currentAster = celestial.body(asterId);
            const auto* currentCinder = celestial.body(cinderId);
            const auto* currentMoon = celestial.body(moonId);
            const auto* currentSun = celestial.body(sunId);
            if (currentAster == nullptr || currentSun == nullptr) continue;
            currentAster->atmosphere.prevailingWind = {};
            currentAster->weather.windMultiplier = 0.0;
            currentAster->weather.stormIntensity = 0.0;

            if (platform.consumeResize()) renderer.requestResize();
            const auto& input = platform.input();
            vf::PlanetMovementInput movement{};
            movement.forward = (input.forward ? 1.0 : 0.0) - (input.backward ? 1.0 : 0.0);
            movement.right = (input.right ? 1.0 : 0.0) - (input.left ? 1.0 : 0.0);
            movement.vertical = (input.ascend ? 1.0 : 0.0) - (input.descend ? 1.0 : 0.0);
            movement.mouseDx = input.mouseCaptured ? static_cast<double>(input.mouseDx) : 0.0;
            movement.mouseDy = input.mouseCaptured ? static_cast<double>(input.mouseDy) : 0.0;
            movement.flightSpeedSteps = input.flightSpeedSteps;
            movement.sprint = input.sprint;
            movement.toggleFlight = input.toggleFlight;

            const bool wasFlightMode = camera.flightMode();
            camera.update(movement, dt);
            physics.advance(dt);

            glm::dquat inverseAster = glm::conjugate(glm::normalize(currentAster->orientation));
            glm::dvec3 cameraPlanet = inverseAster * (camera.position() - currentAster->position);
            glm::dvec3 localCameraVelocity = asterFrame.toLocalVelocity(
                *currentAster, camera.position(), camera.velocity());

            if (camera.physicsFrameBodyId() == asterId) {
                if (camera.flightMode()) {
                    character.resetFromEye(cameraPlanet, localCameraVelocity, false);
                } else {
                    if (wasFlightMode) character.resetFromEye(cameraPlanet, localCameraVelocity, false);
                    const glm::dvec3 forwardPlanet = safeNormalize(
                        inverseAster * camera.forwardDirection(), {0.0, 0.0, -1.0});
                    const glm::dvec3 gravityUp = character.up();
                    const glm::dvec3 tangentForward = safeNormalize(
                        forwardPlanet - gravityUp * glm::dot(forwardPlanet, gravityUp),
                        patchZ);
                    const glm::dvec3 tangentRight = safeNormalize(
                        glm::cross(tangentForward, gravityUp), patchEast);

                    vf::CharacterControllerInput characterInput{};
                    characterInput.forward = tangentForward;
                    characterInput.right = tangentRight;
                    characterInput.forwardAxis = movement.forward;
                    characterInput.rightAxis = movement.right;
                    characterInput.jump = input.ascend && !input.toggleFlight;
                    characterInput.sprint = input.sprint;
                    character.update(characterInput, dt);

                    const glm::dvec3 worldEye = asterFrame.toWorldPosition(
                        *currentAster, character.eyePosition());
                    const glm::dvec3 worldVelocity = asterFrame.toWorldVelocity(
                        *currentAster, character.eyePosition(), character.linearVelocity());
                    camera.setExternalWorldState(worldEye, worldVelocity, character.grounded());
                    inverseAster = glm::conjugate(glm::normalize(currentAster->orientation));
                    cameraPlanet = inverseAster * (camera.position() - currentAster->position);
                }
            }

            const glm::dvec3 cameraSurface = toSurfacePoint(cameraPlanet);
            const glm::dvec3 forwardPlanet = safeNormalize(
                inverseAster * camera.forwardDirection(), {0.0, 0.0, -1.0});
            const glm::dvec3 forwardSurface = safeNormalize(
                toSurfaceVector(forwardPlanet), {0.0, 0.0, -1.0});
            const glm::dvec3 upSurface = safeNormalize(
                toSurfaceVector(inverseAster * camera.up()), {0.0, 1.0, 0.0});

            // CPU synthesis is asynchronous. The renderer owns the GPU-side streaming policy, so a
            // completed terrain window can be handed over without making the simulation thread wait
            // for procedural generation.
            lodCooldown = std::max(0.0, lodCooldown - dt);
            const double altitude = camera.altitude();
            if (camera.physicsFrameBodyId() == asterId && altitude < 800000.0) {
                const glm::dvec3 cameraDirection = safeNormalize(cameraPlanet, lodCenterDirection);
                const double arcDistance = std::acos(std::clamp(
                    glm::dot(cameraDirection, lodCenterDirection), -1.0, 1.0)) * planet.radius;
                const double threshold = altitude < 20000.0 ? 8000.0
                    : (altitude < 100000.0 ? 40000.0
                    : (altitude < 350000.0 ? 120000.0 : 350000.0));
                const double prefetchThreshold = threshold * 0.42;

                if (!terrainBuildInFlight && lodCooldown <= 0.0 && arcDistance > prefetchThreshold) {
                    const glm::dvec3 requestedDirection = cameraDirection;
                    terrainBuildFuture = std::async(std::launch::async, [&, requestedDirection]() {
                        return std::make_pair(requestedDirection, buildTerrainLod(requestedDirection));
                    });
                    terrainBuildInFlight = true;
                }

                if (terrainBuildInFlight
                    && terrainBuildFuture.wait_for(std::chrono::milliseconds{0})
                        == std::future_status::ready) {
                    auto completed = terrainBuildFuture.get();
                    terrainBuildInFlight = false;
                    lodCenterDirection = completed.first;
                    staticTerrain = std::move(completed.second);
                    renderer.uploadPlanetMesh(staticTerrain);
                    lodCooldown = 0.12;
                }
            }

            const glm::dvec3 sunWorldDirection = safeNormalize(
                currentSun->position - camera.position());
            const glm::dvec3 sunSurfaceDirection = safeNormalize(
                toSurfaceVector(inverseAster * sunWorldDirection), {0.3, 0.8, -0.2});

            vf::PlanetMesh dynamicMesh{};
            if (currentMoon != nullptr) {
                const glm::dvec3 moonDirection = safeNormalize(
                    currentMoon->position - camera.position());
                const glm::dvec3 moonSurfaceDirection = safeNormalize(
                    toSurfaceVector(inverseAster * moonDirection));
                const double moonDistance = glm::length(currentMoon->position - camera.position());
                const double moonAngularRadius = std::asin(std::clamp(
                    currentMoon->radiusMeters / std::max(moonDistance, currentMoon->radiusMeters),
                    0.0, 0.20));
                constexpr double moonVisualDistance = 17000000.0;
                const double moonVisualRadius = std::max(
                    1400.0, std::tan(moonAngularRadius) * moonVisualDistance);
                vf::appendDebugSphere(
                    dynamicMesh,
                    cameraSurface + moonSurfaceDirection * moonVisualDistance,
                    moonVisualRadius,
                    {0.72F, 0.74F, 0.78F},
                    14U,
                    24U,
                    {0.0F, 0.88F, 0.0F, 0.0F});
            }
            if (currentCinder != nullptr) {
                const glm::dvec3 cinderDirection = safeNormalize(
                    currentCinder->position - camera.position());
                const glm::dvec3 cinderSurfaceDirection = safeNormalize(
                    toSurfaceVector(inverseAster * cinderDirection));
                const double distance = glm::length(currentCinder->position - camera.position());
                const double angularRadius = std::asin(std::clamp(
                    currentCinder->radiusMeters / std::max(distance, currentCinder->radiusMeters),
                    0.0,
                    0.20));
                constexpr double visualDistance = 25000000.0;
                const double visualRadius = std::max(
                    1800.0, std::tan(angularRadius) * visualDistance);
                vf::appendDebugSphere(
                    dynamicMesh,
                    cameraSurface + cinderSurfaceDirection * visualDistance,
                    visualRadius,
                    {0.62F, 0.30F, 0.22F},
                    9U,
                    16U,
                    {0.0F, 0.82F, 0.0F, 0.0F});
            }
            renderer.setDynamicMesh(dynamicMesh);

            const auto [width, height] = platform.drawableSize();
            const float aspect = height > 0
                ? static_cast<float>(width) / static_cast<float>(height)
                : 16.0F / 9.0F;
            const glm::mat4 viewProjection = makeReverseZViewProjection(
                forwardSurface, upSurface, aspect);

            const auto atmosphere = celestial.sampleEnvironment(camera.position());
            const double densityRatio = std::clamp(atmosphere.densityKgPerM3 / 1.225, 0.0, 1.2);
            const double physicalSunDistance = glm::length(
                currentSun->position - camera.position());
            const double irradiance = currentSun->luminosityWatts
                / (4.0 * kPi * std::max(1.0, physicalSunDistance * physicalSunDistance));
            const double sunElevation = glm::dot(camera.up(), sunWorldDirection);
            const double airMass = densityRatio / std::max(0.065, sunElevation + 0.14);
            const glm::dvec3 extinction = glm::dvec3{0.10, 0.22, 0.48}
                * std::max(0.0, airMass);

            vf::RenderFrameEnvironment renderEnvironment{};
            renderEnvironment.sunDirectionToLight = glm::vec3(sunSurfaceDirection);
            renderEnvironment.sunLinearColor = glm::vec3(glm::exp(-extinction));
            renderEnvironment.sunIntensity = static_cast<float>(
                3.0 * std::clamp(irradiance / 1361.0, 0.0, 3.0));
            renderEnvironment.skyAmbient = glm::vec3{0.035F, 0.060F, 0.105F}
                + glm::vec3{0.10F, 0.15F, 0.24F} * static_cast<float>(densityRatio);
            renderEnvironment.groundAmbient = glm::vec3{0.018F, 0.016F, 0.013F}
                + glm::vec3{0.030F, 0.042F, 0.022F} * static_cast<float>(densityRatio);
            renderEnvironment.exposure = 1.10F;
            renderEnvironment.cameraForward = glm::vec3(forwardSurface);
            renderEnvironment.planetCenter = toSurfacePoint(glm::dvec3{0.0});
            renderEnvironment.planetRadius = planet.radius;
            renderEnvironment.atmosphereHeight = opticalAtmosphereHeight;
            renderEnvironment.atmosphereScaleHeight = opticalRayleighScaleHeight;
            renderEnvironment.mieScale = 0.78F;
            renderEnvironment.flightSpeedMps = static_cast<float>(camera.flightSpeedMps());

            renderer.drawFrame(viewProjection, cameraSurface, renderEnvironment);

            diagnosticsTime += dt;
            ++diagnosticsFrames;
            if (diagnosticsTime >= 0.5) {
                const double fps = static_cast<double>(diagnosticsFrames) / diagnosticsTime;
                const vf::PlanetTerrainSample terrainBelow = vf::samplePlanetTerrain(
                    planet, safeNormalize(cameraPlanet, patchUp));
                const bool overOcean = terrainBelow.submerged(planet);
                std::ostringstream title;
                title << "Voxel Frontier R4 | "
                      << (camera.flightMode() ? "FLIGHT"
                          : (character.grounded() ? "CAPSULE-GROUNDED" : "CAPSULE-AIR"))
                      << " | SPEED " << std::fixed << std::setprecision(0)
                      << camera.flightSpeedMps() << " m/s"
                      << " | ALT " << std::setprecision(2) << camera.altitude() / 1000.0 << " km"
                      << " | " << (overOcean ? "OCEAN" : "LAND")
                      << " | STREAM " << (terrainBuildInFlight ? "BUILD" : "READY")
                      << " | tris " << renderer.triangleCount() << '+'
                      << renderer.dynamicTriangleCount()
                      << " | FPS " << std::setprecision(0) << fps;
                platform.setWindowTitle(title.str());
                diagnosticsTime = 0.0;
                diagnosticsFrames = 0;
            }
        }

        return 0;
    } catch (const std::exception& exception) {
        std::cerr << "Fatal error: " << exception.what() << '\n';
        return 1;
    }
}
