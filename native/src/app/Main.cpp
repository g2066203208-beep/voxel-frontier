#include "vf/app/RuntimeFeatureFlags.hpp"
#include "vf/physics/PhysicsWorld.hpp"
#include "vf/perf/PerformanceBenchmark.hpp"
#include "vf/platform/SdlPlatform.hpp"
#include "vf/player/CharacterController.hpp"
#include "vf/player/PlanetCamera.hpp"
#include "vf/render/PhysicsDebugMesh.hpp"
#include "vf/render/VulkanRenderer.hpp"
#include "vf/world/AstroTime.hpp"
#include "vf/world/CelestialPhysicsFrame.hpp"
#include "vf/world/CelestialSystem.hpp"
#include "vf/world/PlanetSurface.hpp"
#include "vf/world/PlanetSurfaceAuthority.hpp"
#include "vf/world/PlanetaryBodySystem.hpp"
#include "vf/world/PlanetLodMeshBuilder.hpp"
#include "vf/world/RegionalHydrology.hpp"
#include "vf/world/TerrainStreamingPolicy.hpp"
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
#include <memory>
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

// Gameplay presentation only. Luna keeps its physical radius, mass, gravity and 384,400 km
// orbit. Near Aster's surface the visible disc is enlarged for composition/readability; the
// presentation smoothly returns to the physical 1x radius in high orbit and always returns to
// 1x while actually approaching Luna, so landing/navigation geometry remains truthful.
[[nodiscard]] double gameplayMoonVisualScale(
    double asterAltitudeMeters,
    double moonDistanceMeters) noexcept {
    const double surfaceWeight = 1.0 - smooth01(
        (std::max(0.0, asterAltitudeMeters) - 250000.0) / 2750000.0);
    const double farFromMoonWeight = smooth01(
        (std::max(0.0, moonDistanceMeters) - 12000000.0) / 18000000.0);
    return 1.0 + 3.0 * surfaceWeight * farFromMoonWeight;
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
        constexpr std::uint32_t evidenceSamples = 4096U;
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
            double requiredTargetReliefMeters = 0.0;
            if (target == "mountain") requiredTargetReliefMeters = 4500.0;
            else if (target == "rift") requiredTargetReliefMeters = 1800.0;
            else if (target == "canyon") requiredTargetReliefMeters = 2200.0;
            else if (target == "abyss") requiredTargetReliefMeters = 4500.0;

            double localReliefMeters = 0.0;
            const bool needsReliefProbe = requiredTargetReliefMeters > 0.0
                && ((target == "mountain" && terrain.mountain > 0.16)
                    || (target == "rift" && terrain.rift > 0.015)
                    || (target == "canyon" && terrain.canyon > 0.015)
                    || (target == "abyss" && terrain.abyss > 0.10));
            if (needsReliefProbe) {
                const glm::dvec3 tangentA = stableTangent(d);
                const glm::dvec3 tangentB = safeNormalize(
                    glm::cross(d, tangentA), stableTangent(d));
                constexpr double reliefProbeDistanceMeters = 36000.0;
                constexpr int reliefProbeDirections = 8;
                for (int probeIndex = 0; probeIndex < reliefProbeDirections; ++probeIndex) {
                    const double probeAngle = 2.0 * kPi * static_cast<double>(probeIndex)
                        / static_cast<double>(reliefProbeDirections);
                    const glm::dvec3 probeTangent = safeNormalize(
                        tangentA * std::cos(probeAngle) + tangentB * std::sin(probeAngle),
                        tangentA);
                    const glm::dvec3 probeDirection = safeNormalize(
                        d + probeTangent * (reliefProbeDistanceMeters / planet.radius), d);
                    const double probeElevation = vf::samplePlanetTerrain(
                        planet, probeDirection).elevationMeters;
                    localReliefMeters = std::max(
                        localReliefMeters, std::abs(probeElevation - terrain.elevationMeters));
                }
            }
            if (requiredTargetReliefMeters > 0.0
                && localReliefMeters < requiredTargetReliefMeters) {
                continue;
            }

            double score = -1.0e9;
            if (target == "mountain") {
                const double reliefScore = std::clamp(localReliefMeters / 900.0, 0.0, 2.8);
                score = terrain.mountain * 3.4 + reliefScore * 2.3
                    + terrain.plateBoundary * 0.30
                    - terrain.glacier * 2.6
                    - std::max(0.0, height01 - 0.78) * 2.0
                    - std::abs(d.y) * 0.35;
            } else if (target == "rift") {
                const double reliefScore = std::clamp(localReliefMeters / 420.0, 0.0, 2.6);
                score = terrain.rift * 3.7 + terrain.divergence * 1.10
                    + reliefScore * 2.0 + terrain.plateBoundary * 0.35
                    - terrain.glacier * 1.2 - terrain.mountain * 0.35;
            } else if (target == "alluvial") {
                score = terrain.alluvialFan * 4.4 + terrain.river * 1.2
                    + terrain.moisture * 0.45 - height01 * 0.50;
            } else if (target == "highland") {
                score = terrain.plateau * 2.6 + terrain.hills * 1.3 + height01 * 0.8
                    - terrain.mountain * 0.7;
            } else if (target == "canyon") {
                score = terrain.canyon * 3.6 + terrain.aridity * 0.8 + terrain.hills * 0.5
                    + height01 * 0.4;
            } else if (target == "abyss") {
                score = terrain.abyss * 6.2 + terrain.canyon * 1.1 + terrain.rift * 0.55
                    + height01 * 0.35 - terrain.glacier * 0.55;
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
            std::cout << "R24 terrain target: " << target << " score=" << evidenceScore << std::endl;
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
        const bool mainstreamPerfProfile = [] {
            const char* value = std::getenv("VF_PERF_PROFILE");
            return value != nullptr && std::string_view{value} == "mainstream_1080p";
        }();
        // August-2026 Steam mainstream baseline: 1080p, 6 CPU cores, 16 GiB system RAM,
        // RTX 3060/4060-class discrete GPU. CI may run the same profile on Lavapipe, but its FPS is
        // explicitly labelled software Vulkan and is never reported as a discrete-GPU result.
        vf::SdlPlatform platform{
            "Voxel Frontier — Earthlike Planet + Ocean",
            mainstreamPerfProfile ? 1920 : 1600,
            mainstreamPerfProfile ? 1080 : 900};
        vf::VulkanRenderer renderer{platform.window()};
        // R24_MODULAR_TERRAIN_AB_V1: all heavyweight systems are moving behind explicit
        // runtime gates. Terrain can be removed from rendering and streaming while the
        // mathematical planet surface remains authoritative for coordinates/collision.
        const vf::RuntimeFeatureFlags runtimeFeatures = vf::RuntimeFeatureFlags::fromEnvironment();
        runtimeFeatures.print();

        // Earth-scale gameplay planet. Relief is deterministic procedural morphology rather than a
        // literal GIS copy: continents, shelves, abyssal basins, trenches, mountains, plateaus,
        // volcanic hotspots and river valleys all come from one authoritative height query.
        vf::PlanetDefinition planet{};
        planet.seed = 0x71A9F20DULL;
        planet.radius = 6371000.0;
        planet.maxElevation = 30000.0;
        planet.seaLevelElevationMeters = 0.0;
        planet.maxOceanDepthMeters = 24000.0;
        planet.atmosphereHeight = 180000.0;
        constexpr double opticalAtmosphereHeight = 145000.0;
        constexpr double opticalRayleighScaleHeight = 10200.0;

        vf::PlanetaryBodySystem planetaryBodies;
        vf::CelestialSystem& celestial = planetaryBodies.celestial();
        // Gameplay clock is accelerated by default so real self-rotation and orbital motion
        // are visible during play. Physical periods remain unchanged in simulation seconds.
        double celestialTimeScale = 240.0;
        if (const char* scaleEnv = std::getenv("VF_CELESTIAL_TIME_SCALE"); scaleEnv != nullptr) {
            try { celestialTimeScale = std::clamp(std::stod(scaleEnv), 0.0, 200000.0); }
            catch (...) { celestialTimeScale = 240.0; }
        }
        // Production major-body orbits below use absolute-time ephemerides. This means a 240x
        // day/orbit scale advances once per display frame without the old sixteen 0.25-s callbacks,
        // while dynamic N-body mode remains available for explicit close-encounter simulations.

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
        constexpr double asterObliquity = 23.439281 * kPi / 180.0;
        aster.spinAxis = safeNormalize({std::sin(asterObliquity), std::cos(asterObliquity), 0.0});
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
        vf::PlanetaryBodyDescriptor asterDescriptor{};
        asterDescriptor.celestial = aster;
        asterDescriptor.solidSurface = true;
        asterDescriptor.terrain = planet;
        asterDescriptor.climateEnabled = true;
        asterDescriptor.oceanEnabled = true;
        const std::uint32_t asterId = planetaryBodies.addBody(std::move(asterDescriptor));
        if (!celestial.setAnalyticOrbitFromCurrentState(asterId))
            throw std::runtime_error("Aster analytic ephemeris initialization failed");
        auto* asterSurface = planetaryBodies.surface(asterId);
        auto* asterClimate = planetaryBodies.climate(asterId);
        auto* asterOcean = planetaryBodies.ocean(asterId);
        if (asterSurface == nullptr || asterClimate == nullptr || asterOcean == nullptr)
            throw std::runtime_error("Aster planetary services failed to initialize");
        vf::PlanetSurfaceAuthority& surfaceAuthority = *asterSurface;
        vf::PlanetClimateGrid& climateGrid = *asterClimate;
        vf::OceanSpectrum& oceanSpectrum = *asterOcean;

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
        if (!celestial.setAnalyticOrbitFromCurrentState(cinderId))
            throw std::runtime_error("Cinder analytic ephemeris initialization failed");

        const glm::dvec3 initialSunDirectionPlanet = safeNormalize(
            sun.position - aster.position, {1.0, 0.0, 0.0});
        const glm::dvec3 spawnDirection = findPlayableSpawnDirection(planet, initialSunDirectionPlanet);
        const vf::PlanetTerrainSample spawnTerrain = vf::samplePlanetTerrain(planet, spawnDirection);
        vf::PlanetCamera camera{planet, &celestial, asterId, spawnDirection};
        const bool captureHighSpeed = [] {
            const char* value = std::getenv("VF_CAPTURE_HIGH_SPEED");
            return value != nullptr && std::string_view{value} == "1";
        }();
        const bool runtimeDiagnosticsStdout = [] {
            const char* value = std::getenv("VF_RUNTIME_DIAGNOSTICS");
            return value != nullptr && std::string_view{value} == "1";
        }();
        const bool captureEscapeInheritance = [] {
            const char* value = std::getenv("VF_CAPTURE_ESCAPE_INHERITANCE");
            return value != nullptr && std::string_view{value} == "1";
        }();
        const bool captureSunTransit = [] {
            const char* value = std::getenv("VF_CAPTURE_SUN_TRANSIT");
            return value != nullptr && std::string_view{value} == "1";
        }();
        if (captureHighSpeed) {
            camera.setFlightMode(true);
            camera.setCreativeFlightSpeedMps(500000.0);
            std::cout << "R24 capture high-speed initial_speed_mps=500000\n";
        }

        constexpr double moonOrbitRadius = 384400000.0;
        vf::CelestialBody luna{};
        luna.type = vf::CelestialBodyType::Moon;
        luna.name = "Luna";
        luna.radiusMeters = 1737400.0;
        luna.massKg = 7.342e22;
        luna.gameplaySurfaceGravityMps2 = 1.624;
        luna.gravityInfluenceRadiusMeters = luna.radiusMeters + 450000.0;
        luna.physicsBubbleRadiusMeters = luna.radiusMeters + 900000.0;
        luna.orbitParentId = asterId;
        constexpr double moonInclination = 5.145 * kPi / 180.0;
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
            + moonTangent * circularOrbitSpeed(aster.massKg + luna.massKg, moonOrbitRadius);
        luna.spinAxis = aster.spinAxis;
        luna.spinRateRadPerSecond = 2.0 * kPi / (27.321661 * 86400.0);
        luna.visibleAlbedo = {0.62, 0.64, 0.68};
        const std::uint32_t moonId = celestial.addBody(luna);
        if (!celestial.setAnalyticOrbitFromCurrentState(moonId))
            throw std::runtime_error("Luna analytic ephemeris initialization failed");
        vf::PlanetDefinition moonSurfaceDefinition{};
        moonSurfaceDefinition.seed = 0x4C554E415F523234ULL;
        moonSurfaceDefinition.radius = luna.radiusMeters;
        // Lunar relief is kept at physical kilometre scale relative to a 1,737.4 km radius.
        // The previous 32x32 whole-sphere mesh made the Moon itself visibly polygonal. Keep a cheap
        // far mesh and a much smoother near mesh; both retain real radial displacement.
        moonSurfaceDefinition.maxElevation = 7000.0;
        moonSurfaceDefinition.seaLevelElevationMeters = 0.0;
        moonSurfaceDefinition.maxOceanDepthMeters = 0.0;
        moonSurfaceDefinition.atmosphereHeight = 0.0;
        moonSurfaceDefinition.surfacePreset = vf::PlanetSurfacePreset::AirlessCratered;
        vf::PlanetMesh moonSurfaceMeshDistant = vf::buildPlanetGlobeSurface(
            moonSurfaceDefinition, 6U, 1.0);
        vf::PlanetMesh moonSurfaceMeshFar = vf::buildPlanetGlobeSurface(
            moonSurfaceDefinition, 28U, 1.0);
        vf::PlanetMesh moonSurfaceMeshNear = vf::buildPlanetGlobeSurface(
            moonSurfaceDefinition, 80U, 1.0);

        // Deterministic evidence camera. This remains the real PlanetCamera and the real Vulkan
        // renderer; only its initial pose is selected explicitly so CI cannot accidentally stare at
        // empty sky after synthetic mouse input. Production runs do not set this environment flag.
        if (const char* aerialEnv = std::getenv("VF_CAPTURE_AERIAL");
            aerialEnv != nullptr && std::string_view{aerialEnv} == "1") {
            double aerialAltitude = 5200.0;
            if (const char* altitudeEnv = std::getenv("VF_CAPTURE_ALTITUDE_METERS");
                altitudeEnv != nullptr && *altitudeEnv != '\0') {
                try { aerialAltitude = std::clamp(std::stod(altitudeEnv), 800.0, 80000.0); }
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
            glm::dvec3 localEvidenceTangent = stableTangent(spawnDirection);
            if (const char* targetEnv = std::getenv("VF_TERRAIN_TARGET");
                targetEnv != nullptr && *targetEnv != '\0') {
                const glm::dvec3 localBitangent = safeNormalize(
                    glm::cross(spawnDirection, localEvidenceTangent),
                    stableTangent(spawnDirection));
                const double centerElevation = vf::samplePlanetTerrain(
                    planet, spawnDirection).elevationMeters;
                double highestEvidenceElevation = centerElevation;
                double bestContrast = -1.0;
                glm::dvec3 bestTangent = localEvidenceTangent;
                constexpr int directionCount = 16;
                constexpr int radialRingCount = 3;
                constexpr double probeDistanceMeters = 36000.0;
                for (int ring = 1; ring <= radialRingCount; ++ring) {
                    const double ringDistanceMeters = probeDistanceMeters
                        * static_cast<double>(ring) / static_cast<double>(radialRingCount);
                    for (int i = 0; i < directionCount; ++i) {
                        const double angle = 2.0 * kPi * static_cast<double>(i)
                            / static_cast<double>(directionCount);
                        const glm::dvec3 candidateTangent = safeNormalize(
                            localEvidenceTangent * std::cos(angle)
                                + localBitangent * std::sin(angle),
                            localEvidenceTangent);
                        const glm::dvec3 probeDirection = safeNormalize(
                            spawnDirection
                                + candidateTangent * (ringDistanceMeters / planet.radius),
                            spawnDirection);
                        const vf::PlanetTerrainSample probe = vf::samplePlanetTerrain(
                            planet, probeDirection);
                        highestEvidenceElevation = std::max(
                            highestEvidenceElevation, probe.elevationMeters);
                        const double contrast = std::abs(
                            probe.elevationMeters - centerElevation);
                        if (contrast > bestContrast) {
                            bestContrast = contrast;
                            bestTangent = candidateTangent;
                        }
                    }
                }
                localEvidenceTangent = bestTangent;

                // Keep the camera radially above the highest terrain in the evidence neighbourhood.
                // The environment altitude remains the requested minimum clearance above that rim.
                const double reliefLiftMeters = std::max(
                    0.0, highestEvidenceElevation - centerElevation);
                aerialAltitude += reliefLiftMeters;
                const glm::dvec3 safeLocalOffset = spawnDirection
                    * (localSurfaceRadius + aerialAltitude);
                const glm::dvec3 safeWorldOffset = aster.orientation * safeLocalOffset;
                camera.setExternalWorldState(
                    aster.position + safeWorldOffset,
                    aster.linearVelocity + glm::cross(angularVelocity, safeWorldOffset),
                    false);
                std::cout << "R24 terrain evidence view: contrast_m=" << bestContrast
                          << " highest_elevation_m=" << highestEvidenceElevation
                          << " center_elevation_m=" << centerElevation
                          << " relief_lift_m=" << reliefLiftMeters
                          << std::endl;
            }
            const glm::dvec3 worldEvidenceTangent = safeNormalize(
                aster.orientation * localEvidenceTangent,
                stableTangent(worldUp));
            double downwardWeight = 0.34;
            if (const char* targetEnv = std::getenv("VF_TERRAIN_TARGET");
                targetEnv != nullptr && *targetEnv != '\0') {
                const std::string_view target{targetEnv};
                if (target == "mountain") downwardWeight = 0.10;
                else if (target == "rift") downwardWeight = 0.18;
                else if (target == "abyss") downwardWeight = 0.56;
                else if (target == "canyon") downwardWeight = 0.38;
                else if (target == "hydrology" || target == "river") downwardWeight = 0.27;
            }
            const double tangentWeight = std::sqrt(std::max(
                0.0, 1.0 - downwardWeight * downwardWeight));
            camera.setViewDirectionWorld(
                safeNormalize(
                    worldEvidenceTangent * tangentWeight - worldUp * downwardWeight,
                    -worldUp),
                worldUp);
            std::cout << "R24 deterministic aerial camera altitude="
                      << aerialAltitude << " m\n";
        }

        const bool shadowContactCapture = [] {
            const char* shadowEnv = std::getenv("VF_CAPTURE_SHADOW_CONTACT");
            return shadowEnv != nullptr && std::string_view{shadowEnv} == "1";
        }();
        if (shadowContactCapture) {
            // Do not use the old near-vertical evidence camera: it hid the exact contact point.
            // The per-frame capture probe below is placed on PlanetSurfaceAuthority and the camera
            // is aimed at its base from ordinary eye height, exposing even centimetre-scale gaps.
            std::cout << "R24 capture shadow-contact low-angle production view\n";
        }

        std::string celestialTargetMode{};
        if (const char* celestialTargetEnv = std::getenv("VF_CELESTIAL_TARGET");
            celestialTargetEnv != nullptr && *celestialTargetEnv != '\0') {
            celestialTargetMode = celestialTargetEnv;
            if (celestialTargetMode == "sun") {
                camera.setViewDirectionWorld(
                    sun.position - camera.position(), camera.up());
                std::cout << "R24 celestial evidence target: sun\n";
            } else if (celestialTargetMode == "moon") {
                camera.setViewDirectionWorld(
                    luna.position - camera.position(), camera.up());
                std::cout << "R24 celestial evidence target: moon (physical radius/distance)\n";
            }
        }
        const bool trackMoonEvidence = celestialTargetMode == "moon";

        std::string celestialViewMode{};
        if (const char* viewEnv = std::getenv("VF_CELESTIAL_VIEW");
            viewEnv != nullptr && *viewEnv != '\0') {
            celestialViewMode = viewEnv;
            if (celestialViewMode == "earth-globe") {
                const glm::dvec3 observerDirection = safeNormalize({0.44, 0.28, 0.85});
                const glm::dvec3 observerOffset = observerDirection * 24000000.0;
                camera.setExternalWorldState(
                    aster.position + observerOffset, aster.linearVelocity, false);
                camera.setViewDirectionWorld(-observerOffset, observerDirection);
                std::cout << "R24.2 view: earth-globe distance_km=24000\n";
            } else if (celestialViewMode == "moon-globe") {
                const glm::dvec3 observerDirection = safeNormalize({0.38, 0.31, 0.87});
                const glm::dvec3 observerOffset = observerDirection * 6200000.0;
                camera.setExternalWorldState(
                    luna.position + observerOffset, luna.linearVelocity, false);
                camera.setViewDirectionWorld(-observerOffset, observerDirection);
                std::cout << "R24.2 view: moon-globe distance_km=6200\n";
            } else if (celestialViewMode == "earth-from-moon") {
                const glm::dvec3 moonToEarth = safeNormalize(aster.position - luna.position);
                const glm::dvec3 observerOffset = moonToEarth * (luna.radiusMeters + 2400.0);
                const glm::dvec3 lunarAngularVelocity = safeNormalize(luna.spinAxis)
                    * luna.spinRateRadPerSecond;
                camera.setExternalWorldState(
                    luna.position + observerOffset,
                    luna.linearVelocity + glm::cross(lunarAngularVelocity, observerOffset),
                    false);
                camera.setViewDirectionWorld(
                    aster.position - camera.position(), moonToEarth);
                std::cout << "R24.2 view: earth-from-moon near-side surface\n";
            } else if (celestialViewMode == "earth-moon-system") {
                const glm::dvec3 observerOffset = moonOrbitNormal * 600000000.0;
                camera.setExternalWorldState(
                    aster.position + observerOffset, aster.linearVelocity, false);
                camera.setViewDirectionWorld(-observerOffset, moonRadial);
                std::cout << "R24.3 view: earth-moon-system observer_km=600000\n";
            }
        }

        std::cout << "Spawn land elevation: " << std::fixed << std::setprecision(1)
                  << spawnTerrain.elevationMeters << " m\n";
        const vf::CelestialBody* initialAster = celestial.body(asterId);
        if (initialAster == nullptr) throw std::runtime_error("Aster failed to initialize");
        vf::CelestialPhysicsFrame asterFrame{asterId};
        glm::dvec3 moonEvidenceObserverLocalDirection{};
        bool moonEvidenceObserverPlaced = false;
        if (trackMoonEvidence) {
            const glm::dquat inverseInitialAster = glm::conjugate(
                glm::normalize(initialAster->orientation));
            const glm::dvec3 moonWorldDirection = safeNormalize(
                luna.position - initialAster->position, {1.0, 0.0, 0.0});
            const glm::dvec3 moonLocalDirection = safeNormalize(
                inverseInitialAster * moonWorldDirection, {1.0, 0.0, 0.0});
            const glm::dvec3 moonHorizonTangent = stableTangent(moonLocalDirection);
            constexpr double observerSeparationRadians = 60.0 * kPi / 180.0;
            moonEvidenceObserverLocalDirection = safeNormalize(
                moonLocalDirection * std::cos(observerSeparationRadians)
                    + moonHorizonTangent * std::sin(observerSeparationRadians),
                moonLocalDirection);
            const double observerRadius = vf::planetSurfaceRadius(
                planet, moonEvidenceObserverLocalDirection) + 2.0;
            const glm::dvec3 observerLocalPosition =
                moonEvidenceObserverLocalDirection * observerRadius;
            const glm::dvec3 observerWorldPosition =
                asterFrame.toWorldPosition(*initialAster, observerLocalPosition);
            const glm::dvec3 observerWorldUp = safeNormalize(
                initialAster->orientation * moonEvidenceObserverLocalDirection);
            camera.setExternalWorldState(
                observerWorldPosition,
                asterFrame.toWorldVelocity(
                    *initialAster, observerLocalPosition, glm::dvec3{}),
                false);
            camera.setViewDirectionWorld(luna.position - observerWorldPosition, observerWorldUp);
            moonEvidenceObserverPlaced = true;
            std::cout << "R24 moon ground observer: target_elevation_deg=30"
                      << " surface_offset_m=2\n";
        }

        if (captureSunTransit) {
            // Real gameplay transit starts just outside Aster's production precision bubble, keeps
            // the inherited orbital carrier and then uses ordinary creative-flight input toward the
            // physically located Sun. No teleport occurs after this initial deterministic CI pose.
            const glm::dvec3 sunwardWorld = safeNormalize(
                sun.position - initialAster->position, {1.0, 0.0, 0.0});
            const double departureRadius = initialAster->physicsBubbleRadiusMeters + 5000.0;
            const glm::dvec3 departureWorld = initialAster->position + sunwardWorld * departureRadius;
            camera.setExternalWorldState(departureWorld, initialAster->linearVelocity, false);
            camera.setFlightMode(true);
            camera.setCreativeFlightSpeedMps(vf::PlanetCamera::kCreativeInterstellarBaseMaxMps);
            camera.setViewDirectionWorld(sun.position - departureWorld, camera.up());
            std::cout << "R24 sun transit armed: base_max_c=1024 sprint_max_c=4096"
                      << " departure_clearance_km="
                      << (departureRadius - initialAster->radiusMeters) / 1000.0 << '\n';
        }

        if (captureEscapeInheritance) {
            // Start only five kilometres inside the real precision-bubble boundary. The camera is
            // still owned by Aster, so the outward local velocity is converted through the same
            // CelestialPhysicsFrame used by production flight: orbital velocity + omega x r are
            // inherited automatically at the exact handoff to inertial space.
            const glm::dvec3 escapeDirection = spawnDirection;
            const double localRadius = std::max(
                planet.radius + 1000.0, initialAster->physicsBubbleRadiusMeters - 5000.0);
            const glm::dvec3 localPosition = escapeDirection * localRadius;
            const glm::dvec3 localVelocity = escapeDirection * 45000.0;
            camera.setExternalWorldState(
                asterFrame.toWorldPosition(*initialAster, localPosition),
                asterFrame.toWorldVelocity(*initialAster, localPosition, localVelocity),
                false);
            camera.setFlightMode(true);
            camera.setCreativeFlightSpeedMps(45000.0);
            camera.setViewDirectionWorld(
                initialAster->position - camera.position(), camera.up());
            std::cout << "R24 escape inheritance armed: boundary_margin_km=5"
                      << " parent_orbit_mps=" << glm::length(initialAster->linearVelocity) << '\n';
        }

        const glm::dquat initialInverseAster = glm::conjugate(glm::normalize(initialAster->orientation));
        const glm::dvec3 initialCameraPlanet = initialInverseAster * (camera.position() - initialAster->position);
        const glm::dvec3 patchUp = safeNormalize(initialCameraPlanet);
        const glm::dvec3 initialViewForwardPlanet = safeNormalize(
            initialInverseAster * camera.forwardDirection(), stableTangent(patchUp));
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

        // SurfaceAuthority is owned by PlanetaryBodySystem; hydrology is attached to the same
        // object later, so render, collision, ecology and environment altitude cannot diverge.

        // Whole-planet view uses a smooth, physically displaced cube-sphere instead of leaving a
        // near-ground quadtree frozen in space. This is substantially cheaper than rendering the
        // full adaptive hemisphere and prevents the planet silhouette from becoming chunky.
        std::shared_ptr<const vf::PreparedPlanetMesh> earthGlobeRenderMesh{};
        if (runtimeFeatures.terrainRender) {
            vf::PlanetMesh earthGlobeMesh = vf::buildPlanetGlobeSurface(planet, 96U, 1.0);
            for (auto& vertex : earthGlobeMesh.vertices) {
                const glm::dvec3 pPlanet = glm::dvec3(vertex.position);
                const glm::dvec3 nPlanet = safeNormalize(glm::dvec3(vertex.normal));
                vertex.position = glm::vec3(toSurfacePoint(pPlanet));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(nPlanet)));
            }
            earthGlobeRenderMesh = std::make_shared<const vf::PreparedPlanetMesh>(
                vf::preparePlanetMesh(std::move(earthGlobeMesh), true));
        }

        glm::dvec3 lodCenterDirection = patchUp;
        glm::dvec3 lodViewForwardDirection = initialViewForwardPlanet;
        // Cesium-style persistent CPU tile residency. 512 MiB matches a mature practical default
        // cache scale while keeping active visible tiles non-evictable by virtue of immediate reuse.
        vf::PlanetTileCache terrainTileCache{512ULL * 1024ULL * 1024ULL};
        struct TerrainBuildResult {
            glm::dvec3 centerDirection{};
            glm::dvec3 viewForwardDirection{};
            std::shared_ptr<const vf::PreparedPlanetMesh> renderMesh{};
            std::shared_ptr<const vf::RegionalHydrology> hydrology{};
            vf::PlanetLodStats stats{};
            std::size_t meshVertices{};
            std::size_t meshIndices{};
            double buildMilliseconds{};
            bool reusedHydrology{};
        };

        auto buildTerrainLod = [&](
            const glm::dvec3& centerDirection,
            const glm::dvec3& cameraPlanetLocal,
            const glm::dvec3& viewForwardPlanetLocal,
            std::shared_ptr<const vf::RegionalHydrology> reusableHydrology = {}) {
            const auto buildStarted = std::chrono::steady_clock::now();
            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);
            const double buildAltitude = std::max(0.0, glm::length(cameraPlanetLocal) - planet.radius);
            vf::RegionalHydrologyConfig hydroConfig{};
            hydroConfig.resolution = buildAltitude < 25000.0 ? 193U
                : (buildAltitude < 150000.0 ? 129U : 81U);
            hydroConfig.halfExtentMeters = 220000.0;
            hydroConfig.maxIncisionMeters = std::min(3000.0, planet.maxElevation * 0.10);
            hydroConfig.riverHeadAccumulationFraction = 0.0012;
            hydroConfig.fullChannelAccumulationFraction = 0.022;

            // Priority-Flood is a regional authority, not a per-terrain-patch effect. The 220 km
            // hydrology window already covers the entire 85 km high-detail transition band, so
            // rebuilding a 193x193 routed DEM every ~3.36 km of terrain prefetch is pure duplicate
            // work. Reuse an immutable bake while its fully weighted core still covers the new
            // camera neighbourhood; rebuild only when coverage or required resolution changes.
            bool canReuseHydrology = false;
            if (reusableHydrology && !reusableHydrology->empty()
                && reusableHydrology->resolution() >= hydroConfig.resolution
                && reusableHydrology->halfExtentMeters() >= hydroConfig.halfExtentMeters) {
                const double hydroArcMeters = std::acos(std::clamp(
                    glm::dot(centerUp, reusableHydrology->centerDirection()), -1.0, 1.0))
                    * planet.radius;
                const double safeReuseRadiusMeters = std::max(
                    0.0, reusableHydrology->halfExtentMeters() * 0.72 - 90000.0);
                canReuseHydrology = hydroArcMeters <= safeReuseRadiusMeters;
            }
            std::shared_ptr<const vf::RegionalHydrology> hydrology = reusableHydrology;
            if (!canReuseHydrology) {
                hydrology = std::make_shared<vf::RegionalHydrology>(planet, centerUp, hydroConfig);
            }

            vf::PlanetSurfaceAuthority buildSurface{planet};
            buildSurface.setHydrology(hydrology);
            std::uint64_t tileEpoch = planet.seed ^ 0x9E3779B97F4A7C15ULL;
            const auto mixEpoch = [&](std::int64_t value) {
                tileEpoch ^= static_cast<std::uint64_t>(value) + 0x9E3779B97F4A7C15ULL
                    + (tileEpoch << 6U) + (tileEpoch >> 2U);
            };
            if (hydrology) {
                const glm::dvec3 hc = hydrology->centerDirection();
                mixEpoch(static_cast<std::int64_t>(hydrology->resolution()));
                mixEpoch(std::llround(hc.x * 1.0e9));
                mixEpoch(std::llround(hc.y * 1.0e9));
                mixEpoch(std::llround(hc.z * 1.0e9));
                mixEpoch(std::llround(hydrology->halfExtentMeters()));
                mixEpoch(std::llround(hydrology->maxIncisionMeters()));
            }
            vf::PlanetLodConfig lodConfig{};
            lodConfig.patchResolution = buildAltitude < 25000.0 ? 12U : 10U;
            lodConfig.maxDepth = 20U;
            // Low-altitude detail is no longer a binary square. The builder uses a camera-centred
            // geodesic transition band so physical cell size grows continuously with distance.
            // The old budget covered essentially the whole horizon ring although only one camera
            // frustum can contribute pixels. Keep the same local SSE/cell rules but budget the
            // widened 200-degree prefetch cone instead of a 360-degree high-detail ring.
            // Cesium-style view/SSE selection should spend geometry on pixels, not a huge
            // behind-camera prefetch ring. The 156-degree cone still exceeds the ~100-degree
            // horizontal gameplay FOV by ~28 degrees per side, while turn-triggered async prefetch
            // refreshes at 28 degrees. Reduce the hard leaf ceiling as a second safety net.
            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 1100U
                : (buildAltitude < 150000.0 ? 650U : 320U);
            lodConfig.verticalFovRadians = glm::radians(68.0);
            lodConfig.viewForwardPlanetLocal = safeNormalize(
                viewForwardPlanetLocal, stableTangent(centerUp));
            lodConfig.viewConeHalfAngleRadians = glm::radians(78.0);
            lodConfig.viewportHeightPixels = mainstreamPerfProfile ? 1080.0 : 900.0;
            lodConfig.targetScreenErrorPixels = buildAltitude < 25000.0
                ? (mainstreamPerfProfile ? 4.08 : 3.4)
                : (buildAltitude < 150000.0
                    ? (mainstreamPerfProfile ? 5.76 : 4.8)
                    : (mainstreamPerfProfile ? 8.64 : 7.2));
            lodConfig.nearFieldRadiusMeters = buildAltitude < 25000.0 ? 1.0 : 0.0;
            lodConfig.nearFieldCellMeters = buildAltitude < 25000.0 ? 3.0 : 24.0;
            lodConfig.detailTransitionStartMeters = 180.0;
            lodConfig.detailTransitionEndMeters = 65000.0;
            lodConfig.transitionFarCellMeters = 520.0;
            lodConfig.horizonMarginRadians = 0.020;
            lodConfig.skirtDepthMeters = 6.0;

            TerrainBuildResult result{};
            result.centerDirection = centerUp;
            result.viewForwardDirection = lodConfig.viewForwardPlanetLocal;
            result.hydrology = hydrology;
            result.reusedHydrology = canReuseHydrology;
            vf::PlanetMesh renderMesh = vf::buildAdaptivePlanetSurface(
                buildSurface, cameraPlanetLocal, lodConfig, &result.stats,
                &terrainTileCache, tileEpoch);

            // PlanetLodMeshBuilder already emits the authoritative hydrology-displaced position and
            // reconstructs normals from that exact sampled patch grid. The old pass called
            // sampleSurface() for every generated vertex a second time, and sampleSurface() itself
            // performs four additional terrain/hydrology samples for a central-difference normal.
            // Transform the already authoritative mesh directly into the fixed render frame.
            for (auto& vertex : renderMesh.vertices) {
                const glm::dvec3 precisePlanet = glm::dvec3(vertex.position);
                const glm::dvec3 preciseNormal = safeNormalize(
                    glm::dvec3(vertex.normal), safeNormalize(precisePlanet, centerUp));
                vertex.position = glm::vec3(toSurfacePoint(precisePlanet));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(preciseNormal)));
            }

            if (buildAltitude < 30000.0) {
                appendMesh(renderMesh, vf::buildProceduralEcology(
                    planet, centerUp, surfaceFrame, {}, &buildSurface));
            }

            vf::PlanetMesh oceanProxy{};
            vf::appendOceanSurfaceProxy(
                oceanProxy, {}, planet.radius + planet.seaLevelElevationMeters - 1.5, 96U);
            for (auto& vertex : oceanProxy.vertices) {
                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
                vertex.material.w = -20.0F;
            }
            appendMesh(renderMesh, oceanProxy);
            result.meshVertices = renderMesh.vertices.size();
            result.meshIndices = renderMesh.indices.size();
            // Critical frame-pacing change: material binning and vector ownership transfer occur on
            // this terrain worker. Main-thread adoption later is only a shared_ptr assignment.
            result.renderMesh = std::make_shared<const vf::PreparedPlanetMesh>(
                vf::preparePlanetMesh(std::move(renderMesh), true));
            result.buildMilliseconds = std::chrono::duration<double, std::milli>(
                std::chrono::steady_clock::now() - buildStarted).count();
            return result;
        };

        TerrainBuildResult initialTerrain{};
        if (runtimeFeatures.terrainWorkEnabled()) {
            initialTerrain = buildTerrainLod(
                lodCenterDirection, initialCameraPlanet, initialViewForwardPlanet, {});
        } else {
            std::cout << "R24 TERRAIN_BYPASS render=0 streaming=0 initial_synthesis=0\n";
        }
        std::cout << "R24 PERF terrain_build_ms=" << initialTerrain.buildMilliseconds
                  << " vertices=" << initialTerrain.meshVertices
                  << " indices=" << initialTerrain.meshIndices
                  << " leaf_patches=" << initialTerrain.stats.leafPatches
                  << " culled_nodes=" << initialTerrain.stats.culledNodes
                  << " tile_hits=" << initialTerrain.stats.tileCacheHits
                  << " tile_misses=" << initialTerrain.stats.tileCacheMisses
                  << " generated_patches=" << initialTerrain.stats.generatedPatches
                  << " hydrology_reused=" << (initialTerrain.reusedHydrology ? 1 : 0) << '\n';
        surfaceAuthority.setHydrology(initialTerrain.hydrology);
        if (const char* targetEnv = std::getenv("VF_TERRAIN_TARGET");
            targetEnv != nullptr && std::string_view{targetEnv} == "canyon"
            && initialTerrain.hydrology) {
            const glm::dvec3 canyonEast = stableTangent(spawnDirection);
            const glm::dvec3 canyonNorth = safeNormalize(
                glm::cross(spawnDirection, canyonEast), {0.0, 0.0, 1.0});
            glm::dvec3 bestCanyonDirection = spawnDirection;
            double bestIncisionMeters = -1.0;
            double bestChannelStrength = 0.0;
            double bestAreaFraction = 0.0;
            constexpr int canyonRings = 12;
            constexpr int canyonAzimuths = 64;
            constexpr double canyonSearchRadiusMeters = 72000.0;
            for (int ring = 2; ring <= canyonRings; ++ring) {
                const double radialMeters = canyonSearchRadiusMeters
                    * static_cast<double>(ring) / static_cast<double>(canyonRings);
                for (int i = 0; i < canyonAzimuths; ++i) {
                    const double angle = 2.0 * kPi * static_cast<double>(i)
                        / static_cast<double>(canyonAzimuths);
                    const glm::dvec3 tangent = safeNormalize(
                        canyonEast * std::cos(angle) + canyonNorth * std::sin(angle),
                        canyonEast);
                    const glm::dvec3 direction = safeNormalize(
                        spawnDirection + tangent * (radialMeters / planet.radius),
                        spawnDirection);
                    const vf::RegionalHydrologySample drainage = initialTerrain.hydrology->sample(direction);
                    if (drainage.incisionMeters > bestIncisionMeters) {
                        bestIncisionMeters = drainage.incisionMeters;
                        bestChannelStrength = drainage.channelStrength;
                        bestAreaFraction = drainage.contributingAreaFraction;
                        bestCanyonDirection = direction;
                    }
                }
            }

            double hydrologicMin = surfaceAuthority.sample(bestCanyonDirection).elevationMeters;
            double hydrologicMax = hydrologicMin;
            const glm::dvec3 targetEast = stableTangent(bestCanyonDirection);
            const glm::dvec3 targetNorth = safeNormalize(
                glm::cross(bestCanyonDirection, targetEast), canyonNorth);
            constexpr int reliefRings = 4;
            constexpr int reliefAzimuths = 48;
            constexpr double reliefRadiusMeters = 36000.0;
            for (int ring = 1; ring <= reliefRings; ++ring) {
                const double radialMeters = reliefRadiusMeters
                    * static_cast<double>(ring) / static_cast<double>(reliefRings);
                for (int i = 0; i < reliefAzimuths; ++i) {
                    const double angle = 2.0 * kPi * static_cast<double>(i)
                        / static_cast<double>(reliefAzimuths);
                    const glm::dvec3 tangent = safeNormalize(
                        targetEast * std::cos(angle) + targetNorth * std::sin(angle),
                        targetEast);
                    const glm::dvec3 direction = safeNormalize(
                        bestCanyonDirection + tangent * (radialMeters / planet.radius),
                        bestCanyonDirection);
                    const double elevation = surfaceAuthority.sample(direction).elevationMeters;
                    hydrologicMin = std::min(hydrologicMin, elevation);
                    hydrologicMax = std::max(hydrologicMax, elevation);
                }
            }
            const double hydrologicRelief = hydrologicMax - hydrologicMin;
            const glm::dvec3 targetPlanetPosition =
                surfaceAuthority.sampleSurface(bestCanyonDirection).position;
            const glm::dvec3 cameraPlanetPosition = initialInverseAster
                * (camera.position() - initialAster->position);
            const glm::dvec3 targetWorldDirection = initialAster->orientation
                * (targetPlanetPosition - cameraPlanetPosition);
            const glm::dvec3 cameraWorldUp = safeNormalize(
                initialAster->orientation * spawnDirection, {0.0, 1.0, 0.0});
            camera.setViewDirectionWorld(targetWorldDirection, cameraWorldUp);
            std::cout << "R24 hydrologic canyon view: incision_m=" << bestIncisionMeters
                      << " channel=" << bestChannelStrength
                      << " contributing_fraction=" << bestAreaFraction
                      << " relief_m=" << hydrologicRelief << '\n';
        }
        if (moonEvidenceObserverPlaced) {
            const double exactObserverRadius = surfaceAuthority.surfaceRadius(
                moonEvidenceObserverLocalDirection) + 2.0;
            const glm::dvec3 exactObserverLocalPosition =
                moonEvidenceObserverLocalDirection * exactObserverRadius;
            const glm::dvec3 exactObserverWorldPosition =
                asterFrame.toWorldPosition(*initialAster, exactObserverLocalPosition);
            const glm::dvec3 exactObserverWorldUp = safeNormalize(
                initialAster->orientation * moonEvidenceObserverLocalDirection);
            camera.setExternalWorldState(
                exactObserverWorldPosition,
                asterFrame.toWorldVelocity(
                    *initialAster, exactObserverLocalPosition, glm::dvec3{}),
                false);
            camera.setViewDirectionWorld(
                luna.position - exactObserverWorldPosition, exactObserverWorldUp);
            std::cout << "R24 moon ground observer authoritative_surface=1\n";
        }
        vf::PlanetLodStats currentLodStats = initialTerrain.stats;
        std::shared_ptr<const vf::PreparedPlanetMesh> nearTerrain = std::move(initialTerrain.renderMesh);
        bool usingDistantEarthGlobe = camera.physicsFrameBodyId() != asterId
            || camera.altitude() > 900000.0;
        if (runtimeFeatures.terrainRender)
            renderer.uploadPlanetMesh(usingDistantEarthGlobe ? earthGlobeRenderMesh : nearTerrain);
        else
            renderer.clearPlanetMesh();
        std::future<TerrainBuildResult> terrainBuildFuture{};
        bool terrainBuildInFlight = false;

        // Character/nearby rigid-body physics already runs in Aster body-local coordinates.
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
        vf::PhysicsWorld physics{environment};

        vf::CharacterControllerSettings characterSettings{};
        characterSettings.walkSpeed = 4.8;
        characterSettings.sprintSpeed = 8.2;
        characterSettings.jumpSpeed = 4.7;
        characterSettings.airAcceleration = 1.6;
        characterSettings.maxSlopeAngleRadians = glm::radians(50.0);
        characterSettings.stepHeight = 0.45;
        vf::CharacterController character{physics, characterSettings};
        character.resetFromEye(initialCameraPlanet, {}, true);

        std::cout << "Voxel Frontier R24 adaptive physical planet runtime\n";
        std::cout << "Generic structural damage | Earthlike relief | continuous ocean geoid\n";
        std::cout << "SSE cube-sphere quadtree | cratered Moon | seamless far-globe ocean | stylized ecology\n";
        std::cout << "Earth-Moon physical scale: Rearth=6371 km Rmoon=1737.4 km distance=384400 km"
                  << " | celestial time scale=" << celestialTimeScale << "x\n";

        using Clock = std::chrono::steady_clock;
        auto previous = Clock::now();
        double diagnosticsTime = 0.0;
        std::uint64_t diagnosticsFrames = 0;
        double diagnosticsMaxFrameMilliseconds = 0.0;
        double diagnosticsMaxRenderMilliseconds = 0.0;
        double lodCooldown = 0.0;
        double dynamicSceneAccumulator = 1.0;
        constexpr double kDynamicSceneCadenceSeconds = 0.10;
        vf::PerformanceBenchmark performanceBenchmark{{
            mainstreamPerfProfile,
            2.0,
            6.0,
            120.0,
            40U,
            "mainstream_1080p"}};
        if (mainstreamPerfProfile) {
            std::cout << "R24 BENCHMARK_BEGIN profile=mainstream_1080p resolution=1920x1080"
                      << " cpu_core_limit=6 memory_budget_gib=16 target_fps=120\n";
        }

        // R24_FULL_FRAME_ATTRIBUTION_V1: low-overhead wall-clock attribution.
        struct R24CpuStageTelemetry {
            std::uint64_t frames{};
            double celestial{}, camera{}, physics{}, streaming{}, dynamicScene{}, prep{}, renderer{}, frame{};
            double maxFrame{};
        } r24CpuStages;
        const auto r24Ms = [](Clock::time_point a, Clock::time_point b) {
            return std::chrono::duration<double, std::milli>(b - a).count();
        };

        while (platform.pumpEvents()) {
            const auto now = Clock::now();
            const auto r24FrameCpuStart = now;
            const double rawFrameSeconds = std::max(
                0.0, std::chrono::duration<double>(now - previous).count());
            const double dt = std::clamp(rawFrameSeconds, 1.0 / 500.0, 0.05);
            previous = now;
            // Never hide a hitch by reporting the simulation clamp as frame time. Physics/camera
            // still receive <=50 ms for stability; performance diagnostics record wall time.
            diagnosticsMaxFrameMilliseconds = std::max(
                diagnosticsMaxFrameMilliseconds, rawFrameSeconds * 1000.0);

            // Surface gameplay may use accelerated day/orbit time. Free inertial player space may
            // not: until all free-space rigid bodies participate in a global time-warp integrator,
            // running planets at 240x while the player advances at 1x is physically impossible and
            // makes the parent planet shoot away. External evidence views are camera tools, not a
            // free player, so they retain the requested acceleration.
            const bool freePlayerInertialSpace = camera.physicsFrameBodyId() == 0U
                && celestialViewMode.empty();
            const double effectiveCelestialTimeScale = freePlayerInertialSpace
                ? 1.0
                : celestialTimeScale;
            planetaryBodies.step(dt * effectiveCelestialTimeScale);
            const auto r24CelestialDone = Clock::now();
            if (runtimeDiagnosticsStdout) {
                const vf::CelestialSimulationStats celestialStats = celestial.lastStepStats();
                static std::uint64_t celestialDiagFrame = 0U;
                if ((++celestialDiagFrame % 30U) == 0U) {
                    std::cout << "R24 CELESTIAL dynamic_bodies=" << celestialStats.dynamicBodies
                              << " analytic_bodies=" << celestialStats.analyticBodies
                              << " nbody_pairs=" << celestialStats.nbodyPairEvaluations
                              << " ephemeris_evals=" << celestialStats.analyticEvaluations
                              << " dynamic_substeps=" << celestialStats.dynamicSubsteps
                              << '\n';
                }
            }

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
            if (captureSunTransit) {
                camera.setViewDirectionWorld(
                    currentSun->position - camera.position(), camera.up());
                movement.forward = 1.0;
                movement.right = 0.0;
                movement.vertical = 0.0;
                movement.sprint = true;
                movement.toggleFlight = false;
            }

            const bool wasFlightMode = camera.flightMode();
            camera.update(movement, dt);
            const auto r24CameraDone = Clock::now();
            physics.advance(dt);
            const auto r24PhysicsDone = Clock::now();

            if (celestialViewMode == "earth-globe") {
                const glm::dvec3 observerDirection = safeNormalize({0.44, 0.28, 0.85});
                const glm::dvec3 observerOffset = observerDirection * 24000000.0;
                camera.setExternalWorldState(
                    currentAster->position + observerOffset, currentAster->linearVelocity, false);
                camera.setViewDirectionWorld(-observerOffset, observerDirection);
            } else if (celestialViewMode == "earth-moon-system" && currentMoon != nullptr) {
                const glm::dvec3 observerOffset = moonOrbitNormal * 600000000.0;
                camera.setExternalWorldState(
                    currentAster->position + observerOffset, currentAster->linearVelocity, false);
                camera.setViewDirectionWorld(-observerOffset, moonRadial);
            }

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

            // CI/test-only tracking lens: VF_CELESTIAL_TARGET=moon continuously points the
            // ordinary production camera at the actual integrated Moon position. It does not move,
            // resize or substitute the Moon; it prevents surface-attitude transport from drifting a
            // six-pixel physical lunar disc out of the evidence frame while accelerated time runs.
            if (trackMoonEvidence && currentMoon != nullptr) {
                camera.setViewDirectionWorld(
                    currentMoon->position - camera.position(), camera.up());
            }

            if (captureEscapeInheritance && runtimeDiagnosticsStdout) {
                const glm::dvec3 orbitDirection = safeNormalize(
                    currentAster->linearVelocity, {0.0, 0.0, -1.0});
                const glm::dvec3 relativePosition = camera.position() - currentAster->position;
                const glm::dvec3 radial = safeNormalize(relativePosition, spawnDirection);
                const glm::dvec3 relativeVelocity = camera.velocity() - currentAster->linearVelocity;
                const glm::dvec3 transverseRelative = relativeVelocity
                    - radial * glm::dot(relativeVelocity, radial);
                std::cout << "R24 escape inheritance: frame="
                          << (camera.physicsFrameBodyId() == asterId ? "aster" : "inertial")
                          << " distance_km=" << glm::length(relativePosition) / 1000.0
                          << " inherited_orbit_mps=" << glm::dot(camera.velocity(), orbitDirection)
                          << " transverse_relative_mps=" << glm::length(transverseRelative)
                          << " effective_time_scale=" << effectiveCelestialTimeScale << '\n';
            }

            const glm::dvec3 cameraSurface = toSurfacePoint(cameraPlanet);
            const glm::dvec3 forwardPlanet = safeNormalize(
                inverseAster * camera.forwardDirection(), {0.0, 0.0, -1.0});
            const glm::dvec3 forwardSurface = safeNormalize(
                toSurfaceVector(forwardPlanet), {0.0, 0.0, -1.0});
            const glm::dvec3 upSurface = safeNormalize(
                toSurfaceVector(inverseAster * camera.up()), {0.0, 1.0, 0.0});

            // CPU terrain synthesis is asynchronous, but high-speed flight must never queue
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

            if (runtimeFeatures.terrainRender
                && streaming.useDistantGlobe != usingDistantEarthGlobe) {
                usingDistantEarthGlobe = streaming.useDistantGlobe;
                renderer.uploadPlanetMesh(usingDistantEarthGlobe ? earthGlobeRenderMesh : nearTerrain);
                std::cout << "R24 Earth renderer mode: "
                          << (usingDistantEarthGlobe ? "smooth-globe" : "adaptive-terrain")
                          << " speed_mps=" << localSurfaceSpeed << '\n';
            }

            const double viewTurnRadians = std::acos(std::clamp(
                glm::dot(
                    safeNormalize(forwardPlanet, lodViewForwardDirection),
                    safeNormalize(lodViewForwardDirection, forwardPlanet)),
                -1.0, 1.0));
            const bool viewPrefetchExpired = viewTurnRadians > glm::radians(28.0)
                && camera.physicsFrameBodyId() == asterId
                && !terrainBuildInFlight
                && lodCooldown <= 0.0;
            if (runtimeFeatures.terrainWorkEnabled()
                && (streaming.requestBuild || viewPrefetchExpired)) {
                const glm::dvec3 requestedDirection = cameraDirection;
                const glm::dvec3 requestedCameraPlanet = cameraPlanet;
                const glm::dvec3 requestedViewForward = forwardPlanet;
                const auto reusableHydrology = surfaceAuthority.hydrology();
                terrainBuildFuture = std::async(
                    std::launch::async,
                    [&, requestedDirection, requestedCameraPlanet, requestedViewForward, reusableHydrology]() {
                        return buildTerrainLod(
                            requestedDirection,
                            requestedCameraPlanet,
                            requestedViewForward,
                            reusableHydrology);
                    });
                terrainBuildInFlight = true;
            }

            if (runtimeFeatures.terrainWorkEnabled()
                && terrainBuildInFlight
                && terrainBuildFuture.wait_for(std::chrono::milliseconds{0})
                    == std::future_status::ready) {
                TerrainBuildResult completed = terrainBuildFuture.get();
                terrainBuildInFlight = false;
                const glm::dvec3 directionNow = safeNormalize(cameraPlanet, completed.centerDirection);
                const double staleArcDistance = std::acos(std::clamp(
                    glm::dot(directionNow, completed.centerDirection), -1.0, 1.0)) * planet.radius;
                if (staleArcDistance <= streaming.staleAcceptanceMeters) {
                    lodCenterDirection = completed.centerDirection;
                    lodViewForwardDirection = completed.viewForwardDirection;
                    surfaceAuthority.setHydrology(completed.hydrology);
                    currentLodStats = completed.stats;
                    nearTerrain = std::move(completed.renderMesh);
                    const vf::PlanetTileCacheStats tileCacheStats = terrainTileCache.stats();
                    std::cout << "R24 STREAM tile_hits=" << completed.stats.tileCacheHits
                              << " tile_misses=" << completed.stats.tileCacheMisses
                              << " generated=" << completed.stats.generatedPatches
                              << " resident_tiles=" << tileCacheStats.entries
                              << " resident_mb="
                              << (static_cast<double>(tileCacheStats.residentBytes)
                                  / (1024.0 * 1024.0))
                              << '\n';
                    lodCooldown = 0.12;
                    std::cout << "R24 PERF terrain_build_ms=" << completed.buildMilliseconds
                              << " vertices=" << completed.meshVertices
                              << " indices=" << completed.meshIndices
                              << " leaf_patches=" << completed.stats.leafPatches
                              << " culled_nodes=" << completed.stats.culledNodes
                              << " hydrology_reused=" << (completed.reusedHydrology ? 1 : 0)
                              << '\n';

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
            }

            const auto r24StreamingDone = Clock::now();
            const glm::dvec3 sunWorldDirection = safeNormalize(
                currentSun->position - camera.position());
            const glm::dvec3 sunSurfaceDirection = safeNormalize(
                toSurfaceVector(inverseAster * sunWorldDirection), {0.3, 0.8, -0.2});

            glm::dvec3 frameForwardSurface = forwardSurface;
            glm::dvec3 frameUpSurface = upSurface;
            dynamicSceneAccumulator += dt;
            const bool refreshDynamicScene = shadowContactCapture
                || dynamicSceneAccumulator >= kDynamicSceneCadenceSeconds;
            vf::PlanetMesh dynamicMesh{};
            if (shadowContactCapture) {
                // Deterministic contact probe rendered through the *production* shadow-map pass.
                // Its lower face is exactly tangent to the same authoritative surface used by
                // terrain/collision, so any visible gap is a shadow-bias error rather than a
                // placement ambiguity. This geometry exists only when the CI capture flag is set.
                const glm::dvec3 cameraDirectionPlanet = safeNormalize(cameraPlanet, patchUp);
                const glm::dvec3 sunPlanetDirection = safeNormalize(
                    inverseAster * sunWorldDirection, patchEast);
                const glm::dvec3 sunHorizontalPlanet = safeNormalize(
                    sunPlanetDirection
                        - cameraDirectionPlanet * glm::dot(sunPlanetDirection, cameraDirectionPlanet),
                    patchEast);
                // Put the proof object sideways to sunlight so its shadow cannot hide directly
                // behind the caster from the camera. This affects capture mode only.
                const glm::dvec3 placementTangentPlanet = safeNormalize(
                    glm::cross(cameraDirectionPlanet, sunHorizontalPlanet), patchZ);
                const glm::dvec3 probeDirection = safeNormalize(
                    cameraDirectionPlanet + placementTangentPlanet * (10.0 / planet.radius),
                    cameraDirectionPlanet);
                const vf::PlanetSurfaceSample probeSurface = surfaceAuthority.sampleSurface(probeDirection);
                const glm::dvec3 probeBase = toSurfacePoint(probeSurface.position);
                const glm::dvec3 probeUp = safeNormalize(
                    toSurfaceVector(probeSurface.normal), {0.0, 1.0, 0.0});
                const glm::dvec3 localY{0.0, 1.0, 0.0};
                const double upDot = std::clamp(glm::dot(localY, probeUp), -1.0, 1.0);
                glm::dquat probeOrientation{1.0, 0.0, 0.0, 0.0};
                if (upDot < 0.999999) {
                    const glm::dvec3 axis = safeNormalize(glm::cross(localY, probeUp), {1.0, 0.0, 0.0});
                    probeOrientation = glm::angleAxis(std::acos(upDot), axis);
                }
                const glm::dvec3 probeHalfExtents{0.75, 1.50, 0.75};
                const glm::dvec3 probeCenter = probeBase + probeUp * probeHalfExtents.y;
                vf::appendDebugBox(
                    dynamicMesh, probeCenter, probeOrientation, probeHalfExtents,
                    {0.88F, 0.43F, 0.12F}, {0.0F, 0.72F, 0.0F, 0.0F});
                const glm::dvec3 shadowDirectionSurface = safeNormalize(
                    -(sunSurfaceDirection
                        - probeUp * glm::dot(sunSurfaceDirection, probeUp)),
                    {1.0, 0.0, 0.0});
                // Aim between the caster base and the first metres of shadow. The screenshot must
                // contain the exact object-ground junction and the shadow origin in the same frame.
                const glm::dvec3 proofTarget = probeCenter + shadowDirectionSurface * 3.5;
                frameForwardSurface = safeNormalize(proofTarget - cameraSurface, forwardSurface);
                frameUpSurface = upSurface;
                if (runtimeDiagnosticsStdout) {
                    std::cout << "R24 shadow-contact probe base_y=" << probeBase.y
                              << " center_y=" << probeCenter.y
                              << " half_height=" << probeHalfExtents.y << '\n';
                }
            }
            if (trackMoonEvidence && currentMoon != nullptr) {
                const glm::dvec3 liveMoonWorldDirection = safeNormalize(
                    currentMoon->position - camera.position());
                const glm::dvec3 moonSurfaceDirection = safeNormalize(
                    toSurfaceVector(inverseAster * liveMoonWorldDirection), forwardSurface);
                glm::dvec3 moonScreenRight = glm::cross(moonSurfaceDirection, upSurface);
                moonScreenRight = safeNormalize(moonScreenRight, {1.0, 0.0, 0.0});
                constexpr double moonEvidenceFrameOffset = 3.5 * kPi / 180.0;
                frameForwardSurface = safeNormalize(
                    moonSurfaceDirection * std::cos(moonEvidenceFrameOffset)
                        + moonScreenRight * std::sin(moonEvidenceFrameOffset),
                    forwardSurface);
                frameUpSurface = upSurface;
            }
            if (refreshDynamicScene && currentMoon != nullptr) {
                const glm::dvec3 moonToCamera = currentMoon->position - camera.position();
                const double moonCameraDistance = glm::length(moonToCamera);
                const glm::dvec3 moonViewDirection = safeNormalize(moonToCamera, camera.forwardDirection());
                const bool moonPotentiallyVisible = trackMoonEvidence
                    || glm::dot(camera.forwardDirection(), moonViewDirection) > std::cos(glm::radians(72.0));
                const double asterObserverAltitude = std::max(
                    0.0, glm::length(camera.position() - currentAster->position)
                        - currentAster->radiusMeters);
                const double moonVisualScale = gameplayMoonVisualScale(
                    asterObserverAltitude, moonCameraDistance);
                const double moonAngularRadius = std::asin(std::clamp(
                    currentMoon->radiusMeters * moonVisualScale
                        / std::max(moonCameraDistance, currentMoon->radiusMeters * moonVisualScale),
                    0.0, 1.0));
                const double moonFocalPixels = 900.0
                    / (2.0 * std::tan(glm::radians(68.0) * 0.5));
                const double moonPixelDiameter = 2.0 * std::tan(moonAngularRadius) * moonFocalPixels;
                const vf::PlanetMesh& moonSource = moonPixelDiameter >= 180.0
                    ? moonSurfaceMeshNear
                    : (moonPixelDiameter >= 8.0 ? moonSurfaceMeshFar : moonSurfaceMeshDistant);
                vf::PlanetMesh moonMesh{};
                if (moonPotentiallyVisible) moonMesh = moonSource;
                const glm::dvec3 moonRelativeWorld = currentMoon->position - currentAster->position;
                for (auto& vertex : moonMesh.vertices) {
                    const glm::dvec3 moonBodyPoint = currentMoon->orientation
                        * (glm::dvec3(vertex.position) * moonVisualScale);
                    const glm::dvec3 pointAsterLocal = inverseAster * (moonRelativeWorld + moonBodyPoint);
                    const glm::dvec3 normalAsterLocal = inverseAster
                        * (currentMoon->orientation * glm::dvec3(vertex.normal));
                    vertex.position = glm::vec3(toSurfacePoint(pointAsterLocal));
                    vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(normalAsterLocal)));
                }
                appendMesh(dynamicMesh, moonMesh);
            }
            if (refreshDynamicScene && currentCinder != nullptr) {
                const glm::dvec3 cinderDirection = safeNormalize(
                    currentCinder->position - camera.position());
                const bool cinderPotentiallyVisible = glm::dot(
                    camera.forwardDirection(), cinderDirection) > std::cos(glm::radians(72.0));
                if (cinderPotentiallyVisible) {
                    const glm::dvec3 cinderSurfaceDirection = safeNormalize(
                        toSurfaceVector(inverseAster * cinderDirection));
                    const double distance = glm::length(currentCinder->position - camera.position());
                    const double angularRadius = std::asin(std::clamp(
                        currentCinder->radiusMeters / std::max(distance, currentCinder->radiusMeters),
                        0.0,
                        0.20));
                    const double focalPixels = 900.0
                        / (2.0 * std::tan(glm::radians(68.0) * 0.5));
                    const double pixelDiameter = 2.0 * std::tan(angularRadius) * focalPixels;
                    constexpr double visualDistance = 25000000.0;
                    const double visualRadius = std::max(
                        1800.0, std::tan(angularRadius) * visualDistance);
                    vf::appendDebugSphere(
                        dynamicMesh,
                        cameraSurface + cinderSurfaceDirection * visualDistance,
                        visualRadius,
                        {0.62F, 0.30F, 0.22F},
                        pixelDiameter >= 20.0 ? 9U : 4U,
                        pixelDiameter >= 20.0 ? 16U : 8U,
                        {0.0F, 0.82F, 0.0F, 0.0F});
                }
            }
            if (refreshDynamicScene) {
                renderer.setDynamicMesh(dynamicMesh);
                dynamicSceneAccumulator = 0.0;
            }

            const auto r24DynamicDone = Clock::now();
            const auto [width, height] = platform.drawableSize();
            const float aspect = height > 0
                ? static_cast<float>(width) / static_cast<float>(height)
                : 16.0F / 9.0F;
            const glm::mat4 viewProjection = makeReverseZViewProjection(
                frameForwardSurface, frameUpSurface, aspect);

            const vf::PlanetClimateSample climateSample = climateGrid.sample(
                safeNormalize(cameraPlanet, patchUp), std::max(0.0, camera.altitude()));
            const double densityRatio = std::clamp(climateSample.densityKgPerM3 / 1.225, 0.0, 1.2);
            const double physicalSunDistance = glm::length(
                currentSun->position - camera.position());
            const double irradiance = currentSun->luminosityWatts
                / (4.0 * kPi * std::max(1.0, physicalSunDistance * physicalSunDistance));
            const double sunAngularRadiusRadians = std::asin(std::clamp(
                currentSun->radiusMeters / std::max(physicalSunDistance, currentSun->radiusMeters),
                0.0, 1.0));
            const double sunElevation = glm::dot(camera.up(), sunWorldDirection);
            const double airMass = densityRatio / std::max(0.065, sunElevation + 0.14);
            const glm::dvec3 extinction = glm::dvec3{0.10, 0.22, 0.48}
                * std::max(0.0, airMass);

            vf::RenderFrameEnvironment renderEnvironment{};
            renderEnvironment.sunDirectionToLight = glm::vec3(sunSurfaceDirection);
            renderEnvironment.sunLinearColor = glm::vec3(glm::exp(-extinction));
            renderEnvironment.sunIntensity = static_cast<float>(
                3.0 * std::clamp(irradiance / 1361.0, 0.0, 3.0));
            renderEnvironment.sunAngularRadiusRadians = static_cast<float>(sunAngularRadiusRadians);
            renderEnvironment.skyAmbient = glm::vec3{0.035F, 0.060F, 0.105F}
                + glm::vec3{0.10F, 0.15F, 0.24F} * static_cast<float>(densityRatio);
            renderEnvironment.groundAmbient = glm::vec3{0.018F, 0.016F, 0.013F}
                + glm::vec3{0.030F, 0.042F, 0.022F} * static_cast<float>(densityRatio);
            renderEnvironment.exposure = 1.10F;
            renderEnvironment.cameraForward = glm::vec3(frameForwardSurface);
            renderEnvironment.planetCenter = toSurfacePoint(glm::dvec3{0.0});
            renderEnvironment.planetRadius = planet.radius;
            renderEnvironment.atmosphereHeight = opticalAtmosphereHeight;
            renderEnvironment.atmosphereScaleHeight = opticalRayleighScaleHeight;
            renderEnvironment.mieScale = 0.78F;
            renderEnvironment.flightSpeedMps = static_cast<float>(camera.flightSpeedMps());
            renderEnvironment.dynamicShadowCasters = shadowContactCapture;
            const auto r24PrepDone = Clock::now();

            const auto renderStarted = Clock::now();
            renderer.drawFrame(viewProjection, cameraSurface, renderEnvironment);
            const double renderWallMilliseconds = std::chrono::duration<double, std::milli>(
                Clock::now() - renderStarted).count();
            diagnosticsMaxRenderMilliseconds = std::max(
                diagnosticsMaxRenderMilliseconds, renderWallMilliseconds);
            const auto r24RenderDone = Clock::now();
            r24CpuStages.frames += 1U;
            r24CpuStages.celestial += r24Ms(r24FrameCpuStart, r24CelestialDone);
            r24CpuStages.camera += r24Ms(r24CelestialDone, r24CameraDone);
            r24CpuStages.physics += r24Ms(r24CameraDone, r24PhysicsDone);
            r24CpuStages.streaming += r24Ms(r24PhysicsDone, r24StreamingDone);
            r24CpuStages.dynamicScene += r24Ms(r24StreamingDone, r24DynamicDone);
            r24CpuStages.prep += r24Ms(r24DynamicDone, r24PrepDone);
            r24CpuStages.renderer += r24Ms(r24PrepDone, r24RenderDone);
            const double r24WholeFrame = r24Ms(r24FrameCpuStart, r24RenderDone);
            r24CpuStages.frame += r24WholeFrame;
            r24CpuStages.maxFrame = std::max(r24CpuStages.maxFrame, r24WholeFrame);
            if ((r24CpuStages.frames % 16U) == 0U) {
                const double inv = 1.0 / static_cast<double>(r24CpuStages.frames);
                std::cout << "R24 CPU stage_ms samples=" << r24CpuStages.frames
                          << " celestial_mean=" << r24CpuStages.celestial * inv
                          << " camera_mean=" << r24CpuStages.camera * inv
                          << " physics_mean=" << r24CpuStages.physics * inv
                          << " streaming_mean=" << r24CpuStages.streaming * inv
                          << " dynamic_mean=" << r24CpuStages.dynamicScene * inv
                          << " prep_mean=" << r24CpuStages.prep * inv
                          << " renderer_mean=" << r24CpuStages.renderer * inv
                          << " frame_cpu_mean=" << r24CpuStages.frame * inv
                          << " frame_cpu_max=" << r24CpuStages.maxFrame << '\n';
            }

            performanceBenchmark.recordFrame(
                rawFrameSeconds,
                renderWallMilliseconds,
                renderer.triangleCount(),
                renderer.dynamicTriangleCount(),
                terrainBuildInFlight);
            if (performanceBenchmark.complete()) {
                const auto [benchmarkWidth, benchmarkHeight] = platform.drawableSize();
                std::cout << performanceBenchmark.formatSummary(
                    renderer.gpuName(),
                    static_cast<std::uint32_t>(std::max(0, benchmarkWidth)),
                    static_cast<std::uint32_t>(std::max(0, benchmarkHeight)),
                    6U,
                    16U) << '\n';
                std::cout << "R24 BENCHMARK_GPU_STREAM static_uploads="
                          << renderer.staticUploadCount()
                          << " static_upload_bytes=" << renderer.staticUploadBytesTotal()
                          << '\n';
                break;
            }

            if (captureSunTransit && runtimeDiagnosticsStdout) {
                const double sunClearance = std::max(
                    0.0, physicalSunDistance - currentSun->radiusMeters);
                std::cout << "R24 sun transit: distance_AU="
                          << physicalSunDistance / 149597870700.0
                          << " clearance_solar_radii=" << sunClearance / currentSun->radiusMeters
                          << " speed_c=" << glm::length(camera.velocity())
                              / vf::PlanetCamera::kSpeedOfLightMps
                          << " angular_diameter_deg="
                          << (2.0 * sunAngularRadiusRadians * 180.0 / kPi) << '\n';
                if (sunClearance <= currentSun->radiusMeters * 1.05)
                    std::cout << "R24 SUN_TRANSIT_ARRIVED\n";
            }

            diagnosticsTime += rawFrameSeconds;
            ++diagnosticsFrames;
            if (diagnosticsTime >= 0.5) {
                const double fps = static_cast<double>(diagnosticsFrames) / diagnosticsTime;
                const vf::PlanetTerrainSample terrainBelow = surfaceAuthority.sample(
                    safeNormalize(cameraPlanet, patchUp));
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
                      << " | QLOD " << currentLodStats.leafPatches << "/L" << currentLodStats.deepestLevel
                      << " | cell " << std::setprecision(1) << currentLodStats.nearestCellMeters << "m"
                      << " | tris " << renderer.triangleCount() << '+'
                      << renderer.dynamicTriangleCount()
                      << " | maxms " << std::setprecision(1) << diagnosticsMaxFrameMilliseconds
                      << " | renderms " << diagnosticsMaxRenderMilliseconds
                      << " | FPS " << std::setprecision(0) << fps;
                platform.setWindowTitle(title.str());
                if (runtimeDiagnosticsStdout)
                    std::cout << "R24 DIAG | " << title.str() << '\n';
                if (trackMoonEvidence && currentMoon != nullptr) {
                    const glm::dvec3 moonDirectionWorld = safeNormalize(
                        currentMoon->position - camera.position());
                    const double alignment = std::clamp(
                        glm::dot(camera.forwardDirection(), moonDirectionWorld), -1.0, 1.0);
                    const double angularErrorDegrees = std::acos(alignment) * 180.0 / kPi;
                    const double moonDistanceMeters = glm::length(
                        currentMoon->position - camera.position());
                    const double angularRadiusRadians = std::asin(std::clamp(
                        currentMoon->radiusMeters / std::max(moonDistanceMeters, currentMoon->radiusMeters),
                        0.0, 1.0));
                    const double focalPixels = static_cast<double>(height)
                        / (2.0 * std::tan(glm::radians(68.0) * 0.5));
                    const double apparentDiameterPixels = 2.0 * std::tan(angularRadiusRadians) * focalPixels;
                    const double asterObserverAltitude = std::max(
                        0.0, glm::length(camera.position() - currentAster->position)
                            - currentAster->radiusMeters);
                    const double moonVisualScale = gameplayMoonVisualScale(
                        asterObserverAltitude, moonDistanceMeters);
                    std::cout << "R24 moon evidence: distance_km="
                              << moonDistanceMeters / 1000.0
                              << " angular_error_deg=" << angularErrorDegrees
                              << " apparent_diameter_px=" << apparentDiameterPixels
                              << " visual_scale=" << moonVisualScale
                              << " visual_apparent_diameter_px="
                              << apparentDiameterPixels * moonVisualScale
                              << " dynamic_tris=" << renderer.dynamicTriangleCount() << '\n';
                }
                diagnosticsTime = 0.0;
                diagnosticsFrames = 0;
                diagnosticsMaxFrameMilliseconds = 0.0;
                diagnosticsMaxRenderMilliseconds = 0.0;
            }
        }

        return 0;
    } catch (const std::exception& exception) {
        std::cerr << "Fatal error: " << exception.what() << '\n';
        return 1;
    }
}
