#include "vf/physics/PhysicsWorld.hpp"
#include "vf/platform/SdlPlatform.hpp"
#include "vf/player/CharacterController.hpp"
#include "vf/player/PlanetCamera.hpp"
#include "vf/render/PhysicsDebugMesh.hpp"
#include "vf/render/VulkanRenderer.hpp"
#include "vf/world/CelestialPhysicsFrame.hpp"
#include "vf/world/CelestialSystem.hpp"
#include "vf/world/PlanetSurface.hpp"

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
#include <sstream>
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
        const bool softwareCapture = std::getenv("VF_SOFTWARE_CAPTURE") != nullptr;

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

        vf::PlanetCamera camera{planet, &celestial, asterId};
        const vf::CelestialBody* initialAster = celestial.body(asterId);
        if (initialAster == nullptr) throw std::runtime_error("Aster failed to initialize");
        vf::CelestialPhysicsFrame asterFrame{asterId};

        // CI capture uses the actual game renderer but moves the camera to a deterministic coastal
        // overlook. A low-discrepancy spherical search finds a real generated coast for this seed;
        // it does not inject a fake test mesh or alter normal gameplay spawn state.
        if (softwareCapture) {
            constexpr std::uint32_t kCaptureCandidates = 320U;
            constexpr double kGoldenAngle = 2.39996322972865332;
            constexpr double kCoastProbeMeters = 160000.0;
            double bestScore = -1.0e30;
            glm::dvec3 bestCoast{0.72, 0.52, 0.46};
            glm::dvec3 bestLandHeading = stableTangent(bestCoast);

            for (std::uint32_t i = 0; i < kCaptureCandidates; ++i) {
                const double u = (static_cast<double>(i) + 0.5)
                    / static_cast<double>(kCaptureCandidates);
                const double y = 1.0 - 2.0 * u;
                const double radial = std::sqrt(std::max(0.0, 1.0 - y * y));
                const double azimuth = kGoldenAngle * static_cast<double>(i);
                const glm::dvec3 direction{
                    radial * std::cos(azimuth), y, radial * std::sin(azimuth)};
                const glm::dvec3 east = stableTangent(direction);
                const glm::dvec3 north = safeNormalize(glm::cross(direction, east));
                const std::array<glm::dvec3, 4> headings{{east, -east, north, -north}};
                const vf::PlanetTerrainSample center = vf::samplePlanetTerrain(planet, direction);

                for (const glm::dvec3& heading : headings) {
                    const double angularProbe = kCoastProbeMeters / planet.radius;
                    const glm::dvec3 landDirection = safeNormalize(direction + heading * angularProbe);
                    const glm::dvec3 seaDirection = safeNormalize(direction - heading * angularProbe);
                    const vf::PlanetTerrainSample land = vf::samplePlanetTerrain(planet, landDirection);
                    const vf::PlanetTerrainSample sea = vf::samplePlanetTerrain(planet, seaDirection);
                    const bool hasLand = land.elevationMeters > 180.0;
                    const bool hasSea = sea.elevationMeters < -80.0;
                    const double coastBonus = hasLand && hasSea ? 12000.0 : 0.0;
                    const double relief = std::clamp(land.elevationMeters, 0.0, 5000.0) * 0.9
                        + std::clamp(-sea.elevationMeters, 0.0, 7000.0) * 0.32;
                    const double morphology = land.mountain * 1800.0 + land.plateau * 650.0;
                    const double centerPenalty = std::min(std::abs(center.elevationMeters), 5000.0) * 0.08;
                    const double score = coastBonus + relief + morphology - centerPenalty;
                    if (score > bestScore) {
                        bestScore = score;
                        bestCoast = direction;
                        bestLandHeading = heading;
                    }
                }
            }

            const glm::dvec3 cameraDirection = safeNormalize(
                bestCoast - bestLandHeading * (130000.0 / planet.radius), bestCoast);
            const glm::dvec3 targetDirection = safeNormalize(
                bestCoast + bestLandHeading * (90000.0 / planet.radius), bestCoast);
            const glm::dvec3 cameraPlanet = cameraDirection
                * (vf::planetSurfaceRadius(planet, cameraDirection) + 52000.0);
            const glm::dvec3 targetPlanet = targetDirection
                * (vf::planetSurfaceRadius(planet, targetDirection) + 900.0);
            const glm::dvec3 localForward = safeNormalize(targetPlanet - cameraPlanet, bestLandHeading);
            const glm::dvec3 worldPosition = asterFrame.toWorldPosition(*initialAster, cameraPlanet);
            const glm::dvec3 worldVelocity = asterFrame.toWorldVelocity(*initialAster, cameraPlanet, {});
            camera.setExternalWorldPose(
                worldPosition,
                worldVelocity,
                initialAster->orientation * localForward,
                initialAster->orientation * cameraDirection,
                false,
                true);
        }

        const glm::dquat initialInverseAster = glm::conjugate(glm::normalize(initialAster->orientation));
        const glm::dvec3 initialCameraPlanet = initialInverseAster * (camera.position() - initialAster->position);
        const glm::dvec3 patchUp = safeNormalize(initialCameraPlanet);
        const glm::dvec3 patchEast = stableTangent(patchUp);
        const glm::dvec3 patchZ = safeNormalize(glm::cross(patchEast, patchUp), {0.0, 0.0, -1.0});
        const glm::dvec3 patchOriginPlanet = patchUp * vf::planetSurfaceRadius(planet, patchUp);

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

        // The whole-planet proxies do not depend on the streaming window. Building them once avoids
        // re-running the expensive procedural terrain sampler every time the viewer moves. GPU Gems
        // geometry clipmaps likewise keep coarse levels resident and only refresh what motion exposes.
        const vf::PlanetMesh planetProxyBase = vf::buildPlanetSurface(planet, 48U);
        vf::PlanetMesh oceanProxyBase{};
        vf::appendOceanSurfaceProxy(
            oceanProxyBase,
            {},
            planet.radius + planet.seaLevelElevationMeters - 180.0,
            48U);
        for (auto& vertex : oceanProxyBase.vertices) {
            // The current shared transparent path blends every overlapping water level. Until water
            // owns a dedicated depth-aware renderer, use an opaque stylized ocean surface so nested
            // transparent layers cannot draw visible square bands.
            vertex.material.z = 0.0F;
        }

        glm::dvec3 lodCenterDirection = patchUp;
        auto buildTerrainLod = [&](const glm::dvec3& centerDirection, std::uint32_t qualityTier) {
            vf::PlanetMesh mesh{};
            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);
            const glm::dvec3 centerEast = stableTangent(centerUp);
            const glm::dvec3 centerNorth = safeNormalize(glm::cross(centerUp, centerEast), patchZ);

            struct Ring {
                double half;
                double inner;
                std::uint32_t resolution;
                double terrainBaseInset;
                double terrainEdgeInset;
            };

            // Screen-space value, not player speed alone, decides how much geometry is worth
            // synthesizing. At extreme flight speed/high altitude the player cannot resolve a 200 m
            // local grid, so rebuilding it is pure CPU waste. These four quality tiers retain the
            // same physical height function and patch extents while reducing only tessellation.
            constexpr std::array<std::array<std::uint32_t, 4>, 4> resolutions{{
                {{192U, 128U, 80U, 48U}},
                {{128U, 92U, 60U, 36U}},
                {{80U, 56U, 38U, 26U}},
                {{48U, 34U, 24U, 16U}},
            }};
            constexpr std::array<std::uint32_t, 4> oceanResolutions{{96U, 72U, 48U, 32U}};
            qualityTier = std::min<std::uint32_t>(qualityTier, 3U);
            const auto& r = resolutions[qualityTier];
            const std::array<Ring, 4> rings{{
                {22000.0, 0.0, r[0], 0.0, 1.5},
                {190000.0, 20000.0, r[1], 1.0, 8.0},
                {950000.0, 170000.0, r[2], 7.0, 42.0},
                {2600000.0, 850000.0, r[3], 34.0, 160.0},
            }};

            for (const Ring& ring : rings) {
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
                        // Finite-difference normals cost three additional full procedural samples.
                        // Keep them only in the high-detail near ring. Fast/high-altitude tiers use
                        // the radial normal because the resulting triangles are sub-pixel anyway.
                        const glm::dvec3 normalPlanet = qualityTier == 0U && ring.inner <= 0.0
                            ? vf::planetSurfaceNormal(planet, direction)
                            : direction;
                        const double edge = std::max(std::abs(eastMeters), std::abs(northMeters)) / ring.half;
                        const double edgeBlend = std::clamp((edge - 0.88) / 0.12, 0.0, 1.0);
                        glm::dvec3 worldPoint = direction * (planet.radius + terrain.elevationMeters);
                        worldPoint -= normalPlanet * (ring.terrainBaseInset + edgeBlend * ring.terrainEdgeInset);

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

            // One continuous local geoid patch replaces the old transparent ocean-per-LOD stack.
            // Because this surface is geometrically smooth, 256x256 was unnecessary tessellation;
            // its screen-space resolution now follows the same quality tier as terrain streaming.
            vf::PlanetMesh localOcean = vf::buildOceanSurfacePatch(
                planet,
                centerUp,
                1200000.0,
                oceanResolutions[qualityTier],
                0.0);
            for (auto& vertex : localOcean.vertices) {
                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
                vertex.material.z = 0.0F;
            }
            appendMesh(mesh, localOcean);

            // Coarse full-planet proxies fill the horizon/space view. They are copied from resident
            // bases instead of procedurally rebuilt for every streamed window.
            vf::PlanetMesh proxy = planetProxyBase;
            constexpr double proxyInset = 240.0;
            for (auto& vertex : proxy.vertices) {
                glm::dvec3 p = glm::dvec3(vertex.position);
                const double radius = glm::length(p);
                if (radius > proxyInset + 1.0) p *= (radius - proxyInset) / radius;
                vertex.position = glm::vec3(toSurfacePoint(p));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
            }
            appendMesh(mesh, proxy);

            vf::PlanetMesh oceanProxy = oceanProxyBase;
            for (auto& vertex : oceanProxy.vertices) {
                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
            }
            appendMesh(mesh, oceanProxy);
            return mesh;
        };

        std::uint32_t currentTerrainQuality = 0U;
        vf::PlanetMesh staticTerrain = buildTerrainLod(lodCenterDirection, currentTerrainQuality);
        renderer.uploadPlanetMesh(staticTerrain);
        struct TerrainBuildResult {
            glm::dvec3 direction{};
            std::uint32_t quality{};
            vf::PlanetMesh mesh{};
        };
        std::future<TerrainBuildResult> terrainBuildFuture{};
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
        character.resetFromEye(initialCameraPlanet, {}, !softwareCapture);

        std::cout << "Voxel Frontier Earthlike planet runtime\n";
        std::cout << "Generic structural damage | Earthlike relief | continuous ocean geoid\n";
        std::cout << "Async terrain synthesis | adaptive tessellation | software-render screenshot gate\n" << std::flush;

        using Clock = std::chrono::steady_clock;
        auto previous = Clock::now();
        double diagnosticsTime = 0.0;
        std::uint64_t diagnosticsFrames = 0;
        double lodCooldown = 0.0;
        std::uint32_t captureFrames = 0U;
        bool captureReadyLogged = false;

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

            // CPU synthesis stays asynchronous. Update radius and tessellation both scale with
            // motion/altitude: high-speed travel neither rebuilds every few kilometres nor asks the
            // worker to generate close-range geometry that cannot contribute a visible pixel.
            lodCooldown = std::max(0.0, lodCooldown - dt);
            const double altitude = camera.altitude();
            if (camera.physicsFrameBodyId() == asterId && altitude < 800000.0) {
                const glm::dvec3 cameraDirection = safeNormalize(cameraPlanet, lodCenterDirection);
                const double arcDistance = std::acos(std::clamp(
                    glm::dot(cameraDirection, lodCenterDirection), -1.0, 1.0)) * planet.radius;
                const double baseThreshold = altitude < 20000.0 ? 8000.0
                    : (altitude < 100000.0 ? 40000.0
                    : (altitude < 350000.0 ? 120000.0 : 350000.0));
                const double flightStreamingDistance = camera.flightMode()
                    ? std::clamp(camera.flightSpeedMps() * 0.65, 0.0, 1300000.0)
                    : 0.0;
                const double threshold = std::max(baseThreshold, flightStreamingDistance);
                const double prefetchThreshold = threshold
                    * (camera.flightSpeedMps() > 5000.0 ? 0.72 : 0.42);

                std::uint32_t desiredQuality = 0U;
                const double speed = camera.flightMode() ? camera.flightSpeedMps() : 0.0;
                if (altitude > 120000.0 || speed > 5000.0) desiredQuality = 1U;
                if (altitude > 280000.0 || speed > 25000.0) desiredQuality = 2U;
                if (altitude > 500000.0 || speed > 120000.0) desiredQuality = 3U;
                const bool qualityMismatch = desiredQuality != currentTerrainQuality;

                if (!terrainBuildInFlight && lodCooldown <= 0.0
                    && (arcDistance > prefetchThreshold || qualityMismatch)) {
                    const glm::dvec3 requestedDirection = cameraDirection;
                    const std::uint32_t requestedQuality = desiredQuality;
                    terrainBuildFuture = std::async(
                        std::launch::async,
                        [&, requestedDirection, requestedQuality]() {
                            return TerrainBuildResult{
                                requestedDirection,
                                requestedQuality,
                                buildTerrainLod(requestedDirection, requestedQuality)};
                        });
                    terrainBuildInFlight = true;
                }

                if (terrainBuildInFlight
                    && terrainBuildFuture.wait_for(std::chrono::milliseconds{0})
                        == std::future_status::ready) {
                    TerrainBuildResult completed = terrainBuildFuture.get();
                    terrainBuildInFlight = false;
                    const glm::dvec3 currentDirection = safeNormalize(cameraPlanet, completed.direction);
                    const double staleDistance = std::acos(std::clamp(
                        glm::dot(currentDirection, completed.direction), -1.0, 1.0)) * planet.radius;
                    const double acceptanceDistance = std::max(
                        threshold * 1.15,
                        camera.flightMode() ? camera.flightSpeedMps() * 0.30 : 0.0);

                    // Do not upload a patch the camera already outran, nor a quality tier made stale
                    // by a large speed/altitude change while the worker was building it.
                    if (staleDistance <= acceptanceDistance && completed.quality == desiredQuality) {
                        lodCenterDirection = completed.direction;
                        currentTerrainQuality = completed.quality;
                        staticTerrain = std::move(completed.mesh);
                        renderer.uploadPlanetMesh(staticTerrain);
                        lodCooldown = currentTerrainQuality >= 2U ? 0.50
                            : (camera.flightSpeedMps() > 5000.0 ? 0.35 : 0.12);
                    } else {
                        lodCooldown = 0.0;
                    }
                }
            }

            const glm::dvec3 sunWorldDirection = safeNormalize(
                currentSun->position - camera.position());
            const glm::dvec3 sunSurfaceDirection = safeNormalize(
                toSurfaceVector(inverseAster * sunWorldDirection), {0.3, 0.8, -0.2});

            vf::PlanetMesh dynamicMesh{};
            if (!softwareCapture && currentCinder != nullptr) {
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

            if (softwareCapture && !captureReadyLogged) {
                ++captureFrames;
                if (captureFrames >= 18U && !terrainBuildInFlight) {
                    std::cout << "VF_CAPTURE_READY\n" << std::flush;
                    captureReadyLogged = true;
                }
            }

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
                      << " Q" << currentTerrainQuality
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
