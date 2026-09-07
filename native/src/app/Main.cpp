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
                score = terrain.mountain * 3.6 + height01 * 1.1 + terrain.plateBoundary * 0.35
                    - terrain.glacier * 2.2 - std::abs(d.y) * 0.55;
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
            std::cout << "R24 terrain target: " << target << " score=" << evidenceScore << '\n';
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

        vf::PlanetaryBodySystem planetaryBodies;
        vf::CelestialSystem& celestial = planetaryBodies.celestial();
        // Gameplay clock is accelerated by default so real self-rotation and orbital motion
        // are visible during play. Physical periods remain unchanged in simulation seconds.
        double celestialTimeScale = 240.0;
        if (const char* scaleEnv = std::getenv("VF_CELESTIAL_TIME_SCALE"); scaleEnv != nullptr) {
            try { celestialTimeScale = std::clamp(std::stod(scaleEnv), 0.0, 200000.0); }
            catch (...) { celestialTimeScale = 240.0; }
        }
        const double celestialFixedStepSeconds = celestialTimeScale <= 1000.0 ? 5.0
            : (celestialTimeScale <= 20000.0 ? 15.0 : 60.0);
        vf::CelestialSimulationClock celestialClock{{
            celestialFixedStepSeconds, celestialTimeScale, 4096U}};

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
            const glm::dvec3 tangent = stableTangent(worldUp);
            camera.setViewDirectionWorld(
                safeNormalize(tangent * 0.78 - worldUp * 0.625, -worldUp),
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

        // SurfaceAuthority is owned by PlanetaryBodySystem; hydrology is attached to the same
        // object later, so render, collision, ecology and environment altitude cannot diverge.

        // Whole-planet view uses a smooth, physically displaced cube-sphere instead of leaving a
        // near-ground quadtree frozen in space. This is substantially cheaper than rendering the
        // full adaptive hemisphere and prevents the planet silhouette from becoming chunky.
        vf::PlanetMesh earthGlobeMesh = vf::buildPlanetGlobeSurface(planet, 96U, 1.0);
        for (auto& vertex : earthGlobeMesh.vertices) {
            const glm::dvec3 pPlanet = glm::dvec3(vertex.position);
            const glm::dvec3 nPlanet = safeNormalize(glm::dvec3(vertex.normal));
            vertex.position = glm::vec3(toSurfacePoint(pPlanet));
            vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(nPlanet)));
        }

        glm::dvec3 lodCenterDirection = patchUp;
        struct TerrainBuildResult {
            glm::dvec3 centerDirection{};
            vf::PlanetMesh mesh{};
            std::shared_ptr<const vf::RegionalHydrology> hydrology{};
            vf::PlanetLodStats stats{};
        };

        auto buildTerrainLod = [&](const glm::dvec3& centerDirection, const glm::dvec3& cameraPlanetLocal) {
            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);
            const double buildAltitude = std::max(0.0, glm::length(cameraPlanetLocal) - planet.radius);
            vf::RegionalHydrologyConfig hydroConfig{};
            hydroConfig.resolution = buildAltitude < 25000.0 ? 129U
                : (buildAltitude < 150000.0 ? 97U : 65U);
            hydroConfig.halfExtentMeters = 220000.0;
            hydroConfig.maxIncisionMeters = 420.0;
            hydroConfig.riverHeadAccumulationFraction = 0.0012;
            hydroConfig.fullChannelAccumulationFraction = 0.022;
            auto hydrology = std::make_shared<vf::RegionalHydrology>(planet, centerUp, hydroConfig);

            vf::PlanetSurfaceAuthority buildSurface{planet};
            buildSurface.setHydrology(hydrology);
            vf::PlanetLodConfig lodConfig{};
            lodConfig.patchResolution = 10U;
            lodConfig.maxDepth = 20U;
            // The contact zone is processed first by PlanetLodMeshBuilder. Keep enough budget for
            // metre-scale feet/prop geometry but stop distant low-altitude SSE from saturating the
            // old 6000-leaf ceiling every frame.
            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 3600U
                : (buildAltitude < 150000.0 ? 1600U : 700U);
            lodConfig.verticalFovRadians = glm::radians(68.0);
            lodConfig.viewportHeightPixels = 900.0;
            lodConfig.targetScreenErrorPixels = buildAltitude < 25000.0 ? 3.6
                : (buildAltitude < 150000.0 ? 5.0 : 8.0);
            // Contact detail is deliberately local: trees, placed objects and the character need
            // fine geometry nearby; distant terrain can use screen-space error alone.
            lodConfig.nearFieldRadiusMeters = buildAltitude < 25000.0 ? 160.0 : 0.0;
            lodConfig.nearFieldCellMeters = buildAltitude < 25000.0 ? 3.0 : 24.0;
            lodConfig.horizonMarginRadians = 0.018;
            lodConfig.skirtDepthMeters = 6.0;

            TerrainBuildResult result{};
            result.centerDirection = centerUp;
            result.hydrology = hydrology;
            result.mesh = vf::buildAdaptivePlanetSurface(
                buildSurface, cameraPlanetLocal, lodConfig, &result.stats);
            for (auto& vertex : result.mesh.vertices) {
                const glm::dvec3 approximatePlanet = glm::dvec3(vertex.position);
                const glm::dvec3 vertexDirection = safeNormalize(approximatePlanet, centerUp);
                const vf::PlanetSurfaceSample preciseSurface = buildSurface.sampleSurface(vertexDirection);
                vertex.position = glm::vec3(toSurfacePoint(preciseSurface.position));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(preciseSurface.normal)));
            }

            if (buildAltitude < 30000.0) {
                appendMesh(result.mesh, vf::buildProceduralEcology(
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
            appendMesh(result.mesh, oceanProxy);
            return result;
        };

        TerrainBuildResult initialTerrain = buildTerrainLod(lodCenterDirection, initialCameraPlanet);
        surfaceAuthority.setHydrology(initialTerrain.hydrology);
        vf::PlanetLodStats currentLodStats = initialTerrain.stats;
        vf::PlanetMesh nearTerrain = std::move(initialTerrain.mesh);
        bool usingDistantEarthGlobe = camera.physicsFrameBodyId() != asterId
            || camera.altitude() > 900000.0;
        renderer.uploadPlanetMesh(usingDistantEarthGlobe ? earthGlobeMesh : nearTerrain);
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
        double lodCooldown = 0.0;

        while (platform.pumpEvents()) {
            const auto now = Clock::now();
            const double dt = std::clamp(
                std::chrono::duration<double>(now - previous).count(),
                1.0 / 500.0,
                0.05);
            previous = now;
            celestialClock.advance(dt, [&](double astroDt) {
                // One authoritative step advances N-body/spin plus every registered planetary
                // service on the same bounded simulated-time sequence.
                planetaryBodies.step(astroDt);
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
            }

            const glm::dvec3 sunWorldDirection = safeNormalize(
                currentSun->position - camera.position());
            const glm::dvec3 sunSurfaceDirection = safeNormalize(
                toSurfaceVector(inverseAster * sunWorldDirection), {0.3, 0.8, -0.2});

            glm::dvec3 frameForwardSurface = forwardSurface;
            glm::dvec3 frameUpSurface = upSurface;
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
            if (currentMoon != nullptr) {
                const double moonCameraDistance = glm::length(currentMoon->position - camera.position());
                const vf::PlanetMesh& moonSource = moonCameraDistance < 12000000.0
                    ? moonSurfaceMeshNear : moonSurfaceMeshFar;
                vf::PlanetMesh moonMesh = moonSource;
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
                frameForwardSurface, frameUpSurface, aspect);

            const vf::PlanetClimateSample climateSample = climateGrid.sample(
                safeNormalize(cameraPlanet, patchUp), std::max(0.0, camera.altitude()));
            const double densityRatio = std::clamp(climateSample.densityKgPerM3 / 1.225, 0.0, 1.2);
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
            renderEnvironment.cameraForward = glm::vec3(frameForwardSurface);
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
                      << " | FPS " << std::setprecision(0) << fps;
                platform.setWindowTitle(title.str());
                if (runtimeDiagnosticsStdout)
                    std::cout << "R24 DIAG | " << title.str() << '\n';
                if (runtimeDiagnosticsStdout)
                    std::cout << "R24 DIAG | " << title.str() << '\n';
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
                    std::cout << "R24 moon evidence: distance_km="
                              << moonDistanceMeters / 1000.0
                              << " angular_error_deg=" << angularErrorDegrees
                              << " apparent_diameter_px=" << apparentDiameterPixels
                              << " dynamic_tris=" << renderer.dynamicTriangleCount() << '\n';
                }
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
