#include "vf/physics/PhysicsWorld.hpp"
#include "vf/platform/SdlPlatform.hpp"
#include "vf/player/CharacterController.hpp"
#include "vf/player/PlanetCamera.hpp"
#include "vf/render/PhysicsDebugMesh.hpp"
#include "vf/render/VulkanRenderer.hpp"
#include "vf/world/CelestialPhysicsFrame.hpp"
#include "vf/world/CelestialSystem.hpp"
#include "vf/world/PlanetSurface.hpp"
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
    const char* captureEnv = std::getenv("VF_CAPTURE_LANDFORM");
    const std::string_view captureMode = captureEnv != nullptr ? std::string_view{captureEnv} : std::string_view{};

    for (std::uint32_t i = 0; i < sampleCount; ++i) {
        const double y = 1.0 - 2.0 * (static_cast<double>(i) + 0.5)
            / static_cast<double>(sampleCount);
        const double radial = std::sqrt(std::max(0.0, 1.0 - y * y));
        const double a = goldenAngle * static_cast<double>(i);
        const glm::dvec3 d{std::cos(a) * radial, y, std::sin(a) * radial};
        const vf::PlanetTerrainSample terrain = vf::samplePlanetTerrain(planet, d);
        const double aboveSea = terrain.elevationMeters - planet.seaLevelElevationMeters;
        if (!captureMode.empty()) {
            if (terrain.submerged(planet) || aboveSea < 15.0) continue;
            const double sunElevation = glm::dot(d, sunDirection);
            if (sunElevation < 0.42 || sunElevation > 0.94) continue;
            const double readableDaylight = 1.0
                - std::clamp(std::abs(sunElevation - 0.66) / 0.30, 0.0, 1.0);
            double captureScore = readableDaylight * 1.65;
            if (captureMode == "mountain")
                captureScore = terrain.mountain * 5.0 + aboveSea / 2200.0 + terrain.canyon * 0.8;
            else if (captureMode == "river")
                captureScore = terrain.river * 6.0 + terrain.canyon * 1.8 - std::max(0.0, aboveSea - 1800.0) / 1800.0;
            else if (captureMode == "coast")
                captureScore = terrain.coastalCliff * 5.0 - std::abs(aboveSea - 80.0) / 600.0 + terrain.mountain * 0.4;
            else if (captureMode == "highland")
                captureScore = terrain.plateau * 4.0 + terrain.mountain * 1.6 + aboveSea / 2600.0;
            if (captureScore > bestScore) {
                bestScore = captureScore;
                best = d;
                found = true;
            }
            continue;
        }
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

[[nodiscard]] glm::dvec3 findCaptureVantageDirection(
    const vf::PlanetDefinition& planet,
    const glm::dvec3& targetDirectionInput,
    std::string_view mode) {
    const glm::dvec3 target = safeNormalize(targetDirectionInput);
    const glm::dvec3 east = stableTangent(target);
    const glm::dvec3 north = safeNormalize(glm::cross(target, east), {0.0, 0.0, 1.0});
    double standOffMeters = 6500.0;
    if (mode == "mountain") standOffMeters = 14000.0;
    else if (mode == "river") standOffMeters = 4200.0;
    else if (mode == "coast") standOffMeters = 6500.0;
    else if (mode == "highland") standOffMeters = 12000.0;
    const double angular = standOffMeters / std::max(1.0, planet.radius);

    glm::dvec3 best = target;
    double bestScore = std::numeric_limits<double>::infinity();
    for (int i = 0; i < 24; ++i) {
        const double a = 2.0 * kPi * static_cast<double>(i) / 24.0;
        const glm::dvec3 d = safeNormalize(
            target + east * (std::cos(a) * angular) + north * (std::sin(a) * angular), target);
        const vf::PlanetTerrainSample terrain = vf::samplePlanetTerrain(planet, d);
        if (terrain.submerged(planet) && mode != "coast") continue;
        const double targetElevation = vf::planetHeight(planet, target);
        const double heightPenalty = terrain.elevationMeters - targetElevation;
        const double wetPenalty = terrain.submerged(planet) ? 800.0 : 0.0;
        const double ruggedPenalty = terrain.mountain * 420.0 + terrain.canyon * 180.0;
        const double score = heightPenalty + wetPenalty + ruggedPenalty;
        if (score < bestScore) {
            bestScore = score;
            best = d;
        }
    }
    return safeNormalize(best, target);
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
        const glm::dvec3 featureDirection = findPlayableSpawnDirection(planet, initialSunDirectionPlanet);
        const char* captureEnv = std::getenv("VF_CAPTURE_LANDFORM");
        const std::string_view captureMode = captureEnv != nullptr
            ? std::string_view{captureEnv} : std::string_view{};
        const glm::dvec3 spawnDirection = captureMode.empty()
            ? featureDirection
            : findCaptureVantageDirection(planet, featureDirection, captureMode);
        const vf::PlanetTerrainSample spawnTerrain = vf::samplePlanetTerrain(planet, spawnDirection);
        vf::PlanetCamera camera{planet, &celestial, asterId, spawnDirection};
        if (!captureMode.empty()) {
            const glm::dvec3 targetPlanet = featureDirection
                * (vf::planetSurfaceRadius(planet, featureDirection)
                    + (captureMode == "mountain" || captureMode == "highland" ? 650.0 : 120.0));
            const glm::dvec3 cameraPlanet = spawnDirection
                * (vf::planetSurfaceRadius(planet, spawnDirection) + 1.75);
            const glm::dvec3 targetWorld = aster.position + aster.orientation * targetPlanet;
            const glm::dvec3 cameraWorld = aster.position + aster.orientation * cameraPlanet;
            camera.setViewDirection(
                targetWorld - cameraWorld,
                safeNormalize(aster.orientation * spawnDirection));
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

        // Build the orbital proxy once. Rebuilding a full 96x96x6 planet every few
        // kilometres was pure waste and delayed the near-field high-resolution refresh.
        vf::PlanetMesh orbitalProxy = vf::buildPlanetSurface(planet, 128U);
        constexpr double orbitalProxyInset = 24.0;
        for (auto& vertex : orbitalProxy.vertices) {
            glm::dvec3 p = glm::dvec3(vertex.position);
            const double r = glm::length(p);
            if (r > orbitalProxyInset + 1.0) p *= (r - orbitalProxyInset) / r;
            vertex.position = glm::vec3(toSurfacePoint(p));
            vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
        }

        glm::dvec3 lodCenterDirection = patchUp;
        auto buildTerrainLod = [&](const glm::dvec3& centerDirection) {
            vf::PlanetMesh mesh{};
            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);
            const glm::dvec3 centerEast = stableTangent(centerUp);
            const glm::dvec3 centerNorth = safeNormalize(glm::cross(centerUp, centerEast), patchZ);

            struct Ring {
                double half;
                double inner;
                std::uint32_t resolution;
            };
            // Geometry-clipmap style nested windows. The inner ring keeps walking-scale density;
            // each outer ring is hollow and the fine edge morphs onto positions sampled on the next
            // coarser grid. This follows mature clipmap seam handling instead of hiding cracks with
            // metre-scale vertical skirts/insets.
            // Seven nested rings. The innermost grid is ~4 m/cell instead of 25.6 m/cell.
            // Total sampled vertices stay below the old implementation because outer rings get
            // progressively cheaper; screen-space detail is spent where the player can see it.
            const std::array<Ring, 7> rings{{
                {384.0,        0.0, 192U},   // 4.0 m cell
                {1536.0,     360.0, 160U},   // 19.2 m cell
                {6144.0,    1450.0, 112U},   // 109.7 m cell
                {24576.0,   5800.0,  80U},   // 614.4 m cell
                {98304.0,  23200.0,  64U},   // 3.07 km cell
                {393216.0, 93000.0,  48U},   // 16.4 km cell
                {2600000.0,370000.0, 40U},   // 130 km orbital support
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

                        if (ringIndex + 1U < rings.size()) {
                            const Ring& nextRing = rings[ringIndex + 1U];
                            const double nextCell = 2.0 * nextRing.half
                                / static_cast<double>(nextRing.resolution);
                            const double edge = std::max(std::abs(eastMeters), std::abs(northMeters)) / ring.half;
                            const double morph = smooth01((edge - 0.72) / 0.24);
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
                        vertex.material.x = static_cast<float>(std::clamp(
                            1.0 - glm::dot(normalPlanet, direction), 0.0, 1.0));
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

            // Cached whole-planet proxy: no expensive global re-sampling on every local stream update.
            appendMesh(mesh, orbitalProxy);

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
            celestial.step(dt);

            auto* currentAster = celestial.body(asterId);
            const auto* currentCinder = celestial.body(cinderId);
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
                // Refresh before the 384 m inner ring morph region.
                const double threshold = altitude < 20000.0 ? 600.0
                    : (altitude < 100000.0 ? 4000.0
                    : (altitude < 350000.0 ? 25000.0 : 120000.0));
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
