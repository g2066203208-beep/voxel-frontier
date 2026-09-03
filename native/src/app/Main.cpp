#include "vf/gameplay/PhysicsPlayground.hpp"
#include "vf/physics/CelestialSurfaceFrames.hpp"
#include "vf/physics/ElectromagneticRadiation.hpp"
#include "vf/physics/PhysicsWorld.hpp"
#include "vf/physics/SpectralOptics.hpp"
#include "vf/platform/SdlPlatform.hpp"
#include "vf/player/PlanetCamera.hpp"
#include "vf/render/PhysicsDebugMesh.hpp"
#include "vf/render/VulkanRenderer.hpp"
#include "vf/world/CelestialSystem.hpp"
#include "vf/world/PlanetSurface.hpp"
#include "vf/world/SparseUniverseCatalog.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <sstream>

#include <glm/common.hpp>
#include <glm/geometric.hpp>

namespace {

constexpr double kPi = 3.1415926535897932384626433832795;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-12) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] bool hasLineOfSightToStar(
    const vf::CelestialSystem& celestial,
    const glm::dvec3& observer,
    std::uint32_t starId) noexcept {
    const auto* star = celestial.body(starId);
    if (star == nullptr) return false;

    const glm::dvec3 toStar = star->position - observer;
    const double starDistance = glm::length(toStar);
    if (starDistance <= 1.0e-9) return true;
    const glm::dvec3 ray = toStar / starDistance;

    for (const auto& body : celestial.bodies()) {
        if (body.id == starId || body.type == vf::CelestialBodyType::Star) continue;
        const glm::dvec3 toCenter = body.position - observer;
        const double alongRay = glm::dot(toCenter, ray);
        if (alongRay <= 1.0e-5 || alongRay >= starDistance) continue;
        const glm::dvec3 closest = observer + ray * alongRay;
        const double clearance = glm::length(closest - body.position);
        if (clearance < body.radiusMeters) return false;
    }
    return true;
}

[[nodiscard]] float atmosphereOpticalStrength(const vf::CelestialBody& body) noexcept {
    if (!body.atmosphere.enabled || body.atmosphere.surfacePressurePa <= 0.0) return 0.0F;
    const double pressureRatio = body.atmosphere.surfacePressurePa / 101325.0;
    const double strength = 0.18 + 0.26 * std::sqrt(std::clamp(pressureRatio, 0.0, 2.0))
        + 0.35 * std::clamp(body.atmosphere.mieStrength, 0.0, 1.0);
    return static_cast<float>(std::clamp(strength, 0.12, 0.72));
}

void rebaseMesh(vf::PlanetMesh& mesh, const glm::dvec3& renderOrigin) {
    const glm::vec3 origin = glm::vec3(renderOrigin);
    for (auto& vertex : mesh.vertices) vertex.position -= origin;
}

[[nodiscard]] double circularOrbitSpeed(double parentMassKg, double radiusMeters) {
    return std::sqrt(vf::CelestialSystem::kGravitationalConstant * parentMassKg
        / std::max(1.0, radiusMeters));
}

} // namespace

int main() {
    try {
        vf::SdlPlatform platform{"Voxel Frontier — Solar System + Sparse Universe v7 Preview", 1600, 900};
        vf::VulkanRenderer renderer{platform.window()};

        // Kilometre-scale gameplay planet. This is deliberately compressed relative to Earth but
        // no longer an asteroid-sized 240 m test sphere. Near-ground patch LOD is the next terrain
        // step; the whole-planet mesh remains a moderately detailed low-poly representation.
        vf::PlanetDefinition planet{};
        planet.seed = 0x71A9F20DULL;
        planet.radius = 6000.0;
        planet.maxElevation = 360.0;
        planet.atmosphereHeight = 1100.0;

        vf::CelestialSystem celestial;

        // Helion is a real celestial object at the inertial solar-system origin. It is both the
        // radiation/light source and the orbital parent; there is no separate invisible world sun.
        vf::CelestialBody star{};
        star.type = vf::CelestialBodyType::Star;
        star.name = "Helion";
        star.radiusMeters = 4200.0;
        constexpr double starMu = 2.80e9; // compressed game-system gravitational parameter m^3/s^2
        star.massKg = starMu / vf::CelestialSystem::kGravitationalConstant;
        star.position = {0.0, 0.0, 0.0};
        star.spinAxis = safeNormalize({0.0, 1.0, 0.12});
        star.spinRateRadPerSecond = 2.0 * kPi / 900.0;
        const double asterOrbitRadius = 45000.0;
        star.luminosityWatts = 4.0 * kPi * asterOrbitRadius * asterOrbitRadius * 1320.0;
        const std::uint32_t starId = celestial.addBody(star);

        vf::CelestialBody primary{};
        primary.type = vf::CelestialBodyType::Planet;
        primary.name = "Aster";
        primary.radiusMeters = planet.radius;
        primary.massKg = 9.81 * primary.radiusMeters * primary.radiusMeters
            / vf::CelestialSystem::kGravitationalConstant;
        primary.gameplaySurfaceGravityMps2 = 9.81;
        primary.gravityInfluenceRadiusMeters = 15000.0;
        primary.position = {asterOrbitRadius, 0.0, 0.0};
        primary.orbitParentId = starId;
        primary.linearVelocity = {0.0, 0.0, circularOrbitSpeed(star.massKg, asterOrbitRadius)};
        primary.spinAxis = safeNormalize({0.08, 1.0, 0.03});
        primary.spinRateRadPerSecond = 2.0 * kPi / 1200.0;
        primary.visibleAlbedo = {0.30, 0.55, 0.32};
        primary.atmosphere.enabled = true;
        primary.atmosphere.heightMeters = planet.atmosphereHeight;
        primary.atmosphere.surfacePressurePa = 101325.0;
        primary.atmosphere.surfaceTemperatureK = 288.15;
        primary.atmosphere.scaleHeightMeters = 360.0;
        primary.atmosphere.lapseRateKPerM = 0.0065;
        primary.atmosphere.rayleighRgb = {0.16, 0.43, 1.00};
        primary.atmosphere.mieStrength = 0.11;
        primary.atmosphere.prevailingWind = {8.0, 0.0, 2.5};
        primary.climate.meanTemperatureK = 288.15;
        primary.climate.bondAlbedo = 0.30;
        primary.climate.greenhouseFactor = 1.12;
        primary.climate.thermalResponseSeconds = 1800.0;
        primary.weather.humidity = 0.58;
        primary.weather.cloudCover = 0.32;
        primary.weather.stormIntensity = 0.08;
        primary.magneticField.enabled = true;
        primary.magneticField.equatorialSurfaceFieldTesla = 32.0e-6;
        const std::uint32_t primaryId = celestial.addBody(primary);

        vf::CelestialBody secondary{};
        secondary.type = vf::CelestialBodyType::Planet;
        secondary.name = "Cinder";
        secondary.radiusMeters = 2800.0;
        secondary.massKg = 3.7 * secondary.radiusMeters * secondary.radiusMeters
            / vf::CelestialSystem::kGravitationalConstant;
        secondary.gameplaySurfaceGravityMps2 = 3.7;
        secondary.gravityInfluenceRadiusMeters = 9000.0;
        const double cinderOrbitRadius = 70000.0;
        secondary.position = {0.0, 0.0, cinderOrbitRadius};
        secondary.orbitParentId = starId;
        secondary.linearVelocity = {-circularOrbitSpeed(star.massKg, cinderOrbitRadius), 0.0, 0.0};
        secondary.spinAxis = safeNormalize({0.25, 1.0, -0.12});
        secondary.spinRateRadPerSecond = 2.0 * kPi / 820.0;
        secondary.visibleAlbedo = {0.62, 0.30, 0.22};
        secondary.atmosphere.enabled = true;
        secondary.atmosphere.heightMeters = 520.0;
        secondary.atmosphere.surfacePressurePa = 2200.0;
        secondary.atmosphere.surfaceTemperatureK = 238.0;
        secondary.atmosphere.molarMassKgPerMol = 0.043;
        secondary.atmosphere.scaleHeightMeters = 170.0;
        secondary.atmosphere.lapseRateKPerM = 0.004;
        secondary.atmosphere.rayleighRgb = {0.70, 0.28, 0.12};
        secondary.atmosphere.mieStrength = 0.22;
        secondary.atmosphere.prevailingWind = {4.0, 0.0, -1.0};
        secondary.climate.meanTemperatureK = 238.0;
        secondary.climate.bondAlbedo = 0.22;
        secondary.climate.greenhouseFactor = 1.04;
        secondary.climate.thermalResponseSeconds = 1200.0;
        secondary.weather.humidity = 0.12;
        secondary.weather.cloudCover = 0.08;
        secondary.magneticField.enabled = true;
        secondary.magneticField.equatorialSurfaceFieldTesla = 7.0e-6;
        const std::uint32_t secondaryId = celestial.addBody(secondary);

        // Hundreds of distant destinations remain coordinate-only metadata until approached.
        // 384 records are enough to make the sky feel populated while staying at tens of KiB.
        vf::SparseUniverseCatalog universe{0xA57E11A5ULL, 384U, 350000.0, 8000000.0};

        vf::PhysicsEnvironment environment{};
        environment.planet = planet;
        environment.surfaceGravity = 9.81;
        environment.atmosphere.seaLevelTemperatureK = 288.15;
        environment.atmosphere.seaLevelPressurePa = 101325.0;
        environment.atmosphere.prevailingWind = {8.0, 0.0, 2.5};
        environment.atmosphere.gustAmplitude = 3.5;
        environment.weather.humidity = 0.58;
        environment.weather.cloudCover = 0.32;
        environment.weather.stormIntensity = 0.08;
        environment.ocean.enabled = true;
        environment.ocean.surfaceRadius = planet.radius - 80.0;
        environment.ocean.densityKgPerM3 = 997.0;
        environment.celestialSystem = &celestial;
        environment.primaryCelestialBodyId = primaryId;
        vf::PhysicsWorld physics{environment};
        vf::CelestialSurfaceFrames surfaceFrames;

        vf::PlanetMesh mesh = vf::buildPlanetSurface(planet, 192U);
        renderer.uploadPlanetMesh(mesh);

        vf::PlanetCamera camera{planet, &celestial, primaryId};
        const auto* asterInitial = celestial.body(primaryId);
        const glm::dvec3 initialAsterOrigin = asterInitial != nullptr ? asterInitial->position : glm::dvec3{};
        const glm::dquat initialAsterOrientation = asterInitial != nullptr
            ? asterInitial->orientation
            : glm::dquat{1.0, 0.0, 0.0, 0.0};
        const glm::dvec3 cameraUp = camera.up();
        glm::dvec3 tangentForward = camera.forwardDirection()
            - cameraUp * glm::dot(camera.forwardDirection(), cameraUp);
        tangentForward = safeNormalize(tangentForward, {0.0, 0.0, 1.0});
        const glm::dvec3 cameraLocal = glm::conjugate(initialAsterOrientation)
            * (camera.position() - initialAsterOrigin);
        const glm::dvec3 playgroundDirectionLocal = safeNormalize(
            cameraLocal + glm::conjugate(initialAsterOrientation) * tangentForward * 22.0);
        vf::PhysicsPlayground playground{
            physics,
            planet,
            playgroundDirectionLocal,
            initialAsterOrigin,
            initialAsterOrientation};

        const auto sunSpectrum = vf::blackbodySpectrum(5772.0);
        const glm::dvec3 sunLinearRgb = vf::spectrumToLinearSrgb(sunSpectrum);
        const double sunMax = std::max({sunLinearRgb.x, sunLinearRgb.y, sunLinearRgb.z, 1.0e-6});
        const glm::vec3 sunDisplayColor = glm::vec3(glm::clamp(
            sunLinearRgb / sunMax,
            glm::dvec3{0.0},
            glm::dvec3{1.0}));

        const glm::dvec3 fieldUpLocal = playgroundDirectionLocal;
        const glm::dvec3 fieldReferenceLocal = std::abs(fieldUpLocal.y) < 0.9
            ? glm::dvec3{0.0, 1.0, 0.0}
            : glm::dvec3{1.0, 0.0, 0.0};
        const glm::dvec3 fieldEastLocal = safeNormalize(glm::cross(fieldReferenceLocal, fieldUpLocal), {1.0, 0.0, 0.0});
        const glm::dvec3 fieldNorthLocal = safeNormalize(glm::cross(fieldUpLocal, fieldEastLocal), {0.0, 0.0, 1.0});
        const auto localSurfacePoint = [&](double eastMeters, double northMeters, double heightMeters) {
            const glm::dvec3 direction = safeNormalize(
                fieldUpLocal
                    + fieldEastLocal * (eastMeters / planet.radius)
                    + fieldNorthLocal * (northMeters / planet.radius),
                fieldUpLocal);
            return direction * (vf::planetSurfaceRadius(planet, direction) + heightMeters);
        };
        const auto asterWorldPoint = [&](const glm::dvec3& localPoint) {
            if (const auto* aster = celestial.body(primaryId)) {
                return aster->position + aster->orientation * localPoint;
            }
            return localPoint;
        };

        const glm::dvec3 pointChargeLocal = localSurfacePoint(5.0, -8.0, 1.2);
        const glm::dvec3 solenoidLocal = localSurfacePoint(10.0, -8.0, 1.0);
        const glm::dvec3 lensLocal = localSurfacePoint(-10.0, -8.0, 1.6);
        glm::dvec3 pointChargePosition = asterWorldPoint(pointChargeLocal);
        glm::dvec3 solenoidPosition = asterWorldPoint(solenoidLocal);
        glm::dvec3 lensPosition = asterWorldPoint(lensLocal);
        glm::dvec3 fieldUpWorld = fieldUpLocal;

        vf::RigidBodyDesc chargedBallDesc{};
        chargedBallDesc.position = asterWorldPoint(localSurfacePoint(7.0, -8.0, 1.4));
        chargedBallDesc.mass = 0.35;
        chargedBallDesc.collisionShape = vf::CollisionShape::sphere(0.24);
        chargedBallDesc.inertiaDiagonal = {0.008, 0.008, 0.008};
        chargedBallDesc.material.restitution = 0.15;
        chargedBallDesc.aerodynamics.referenceArea = 0.08;
        const std::uint32_t chargedBallId = physics.createRigidBody(chargedBallDesc);
        constexpr double chargedBallCoulombs = -2.0e-4;

        vf::ElectromagneticRadiationSystem fields;
        vf::ElectromagneticRadiationSystem::InductionCoil inductionCoil{};
        inductionCoil.position = solenoidPosition;
        inductionCoil.normal = fieldUpWorld;
        inductionCoil.areaSquareMeters = 0.025;
        inductionCoil.turns = 250.0;
        inductionCoil.resistanceOhms = 8.0;

        vf::ElectromagneticRadiationSystem::ThinLens lens{};
        lens.position = lensPosition;
        if (const auto* sun = celestial.body(starId)) lens.opticalAxis = safeNormalize(lens.position - sun->position);
        lens.focalLengthMeters = 0.42;
        lens.apertureRadiusMeters = 0.25;
        lens.transmission = 0.90;
        lens.minimumSpotRadiusMeters = 0.015;
        lens.axialToleranceMeters = 0.035;

        vf::ElectromagneticRadiationSystem::ThermalBody tinder{};
        tinder.position = lens.position + safeNormalize(lens.opticalAxis) * lens.focalLengthMeters;
        tinder.massKg = 0.010;
        tinder.specificHeatJPerKgK = 900.0;
        tinder.surfaceAreaSquareMeters = 0.025;
        tinder.projectedAreaSquareMeters = 0.010;
        tinder.temperatureK = 293.15;
        tinder.ignitionTemperatureK = 620.0;
        tinder.convectiveCoefficientWPerSquareMeterK = 5.0;
        tinder.material.absorptivity = {0.05, 0.10, 0.85, 0.90, 0.92, 0.30};

        vf::ElectromagneticRadiationSystem::LightSensor lightSensor{};
        lightSensor.activeAreaSquareMeters = 2.0e-4;
        lightSensor.responsivityAmperesPerWatt = 0.45;

        surfaceFrames.beforePhysics(physics, celestial);

        std::cout << "Voxel Frontier solar-system + sparse-universe preview\n";
        std::cout << "GPU: " << renderer.gpuName() << '\n';
        std::cout << "Vulkan API: "
                  << VK_API_VERSION_MAJOR(renderer.apiVersion()) << '.'
                  << VK_API_VERSION_MINOR(renderer.apiVersion()) << '.'
                  << VK_API_VERSION_PATCH(renderer.apiVersion()) << '\n';
        std::cout << "Helion is the real star/light/radiation/orbit parent. Aster and Cinder orbit Helion.\n";
        std::cout << "Aster radius 6 km; Cinder radius 2.8 km; Aster/Cinder SOI 15/9 km.\n";
        std::cout << "Sparse universe: " << universe.records().size() << " destinations, approx "
                  << universe.approximateMemoryBytes() / 1024U << " KiB metadata.\n";
        std::cout << "Controls: double-tap Space toggles creative flight; WASD move; Space/Ctrl vertical; Shift fast.\n";

        using Clock = std::chrono::steady_clock;
        auto previous = Clock::now();
        double diagnosticsTime = 0.0;
        std::uint64_t diagnosticsFrames = 0;
        double lastFocusPowerWatts = 0.0;
        double lastLux = 0.0;

        while (platform.pumpEvents()) {
            const auto now = Clock::now();
            double dt = std::chrono::duration<double>(now - previous).count();
            previous = now;
            dt = std::clamp(dt, 0.0, 0.05);

            celestial.step(dt);

            const auto* aster = celestial.body(primaryId);
            if (aster != nullptr) {
                playground.syncPlanetFrame(aster->position, aster->orientation);
                pointChargePosition = aster->position + aster->orientation * pointChargeLocal;
                solenoidPosition = aster->position + aster->orientation * solenoidLocal;
                lensPosition = aster->position + aster->orientation * lensLocal;
                fieldUpWorld = safeNormalize(aster->orientation * fieldUpLocal, fieldUpLocal);
            }
            inductionCoil.position = solenoidPosition;
            inductionCoil.normal = fieldUpWorld;
            lens.position = lensPosition;

            fields.clearSources();

            vf::ElectromagneticRadiationSystem::ElectricPointSource pointCharge{};
            pointCharge.position = pointChargePosition;
            pointCharge.chargeCoulombs = 1.0e-6;
            pointCharge.softeningRadiusMeters = 0.18;
            pointCharge.maxRangeMeters = 12.0;
            fields.addElectricSource(pointCharge);

            vf::ElectromagneticRadiationSystem::SolenoidSource solenoid{};
            solenoid.position = solenoidPosition;
            solenoid.axis = fieldUpWorld;
            solenoid.turns = 600.0;
            solenoid.lengthMeters = 0.70;
            solenoid.radiusMeters = 0.18;
            solenoid.currentAmperes = 4.0 + 3.0 * std::sin(celestial.simulationTime() * 2.0);
            solenoid.relativePermeability = 35.0;
            solenoid.maxRangeMeters = 8.0;
            fields.addSolenoid(solenoid);

            if (const auto* sun = celestial.body(starId)) {
                vf::ElectromagneticRadiationSystem::RadiationSource stellarRadiation{};
                stellarRadiation.position = sun->position;
                stellarRadiation.minimumDistanceMeters = sun->radiusMeters;
                stellarRadiation.maxRangeMeters = 1.0e9;
                stellarRadiation.visibleShape = sunSpectrum;
                stellarRadiation.powerWatts[vf::ElectromagneticRadiationSystem::RadiationBand::Infrared]
                    = sun->luminosityWatts * 0.48;
                stellarRadiation.powerWatts[vf::ElectromagneticRadiationSystem::RadiationBand::Visible]
                    = sun->luminosityWatts * 0.45;
                stellarRadiation.powerWatts[vf::ElectromagneticRadiationSystem::RadiationBand::Ultraviolet]
                    = sun->luminosityWatts * 0.07;
                fields.addRadiationSource(stellarRadiation);

                lens.opticalAxis = safeNormalize(lens.position - sun->position);
                tinder.position = lens.position + lens.opticalAxis * lens.focalLengthMeters;
            }

            fields.stepInductionCoil(inductionCoil, dt);

            if (auto* chargedBall = physics.body(chargedBallId)) {
                const auto chargedField = fields.sample(chargedBall->position);
                chargedBall->addForce(fields.lorentzForce(
                    chargedBallCoulombs,
                    chargedBall->linearVelocity,
                    chargedField));
            }

            surfaceFrames.beforePhysics(physics, celestial);
            physics.advance(dt);
            playground.update(dt);
            surfaceFrames.afterPhysics(physics, celestial, dt);

            const auto lensField = fields.sample(lens.position);
            const bool lensHasSun = hasLineOfSightToStar(celestial, lens.position, starId);
            const double opticalIrradiance = lensHasSun
                ? lensField.irradianceWattsPerSquareMeter[vf::ElectromagneticRadiationSystem::RadiationBand::Infrared]
                    + lensField.irradianceWattsPerSquareMeter[vf::ElectromagneticRadiationSystem::RadiationBand::Visible]
                    + lensField.irradianceWattsPerSquareMeter[vf::ElectromagneticRadiationSystem::RadiationBand::Ultraviolet]
                : 0.0;
            lastFocusPowerWatts = vf::ElectromagneticRadiationSystem::focusedPowerWatts(
                lens,
                opticalIrradiance,
                tinder.position);

            auto tinderField = fields.sample(tinder.position);
            if (!lensHasSun) {
                tinderField.irradianceWattsPerSquareMeter.values.fill(0.0);
                tinderField.visibleIrradianceWattsPerSquareMeter.values.fill(0.0);
            }
            const auto tinderEnvironment = celestial.sampleEnvironment(tinder.position);
            vf::ElectromagneticRadiationSystem::stepThermalBody(
                tinder,
                tinderField,
                tinderEnvironment.temperatureK > 0.0 ? tinderEnvironment.temperatureK : 293.15,
                dt,
                lastFocusPowerWatts);

            if (platform.consumeResize()) renderer.requestResize();

            const auto& input = platform.input();
            vf::PlanetMovementInput movement{};
            movement.forward = (input.forward ? 1.0 : 0.0) - (input.backward ? 1.0 : 0.0);
            movement.right = (input.right ? 1.0 : 0.0) - (input.left ? 1.0 : 0.0);
            movement.vertical = (input.ascend ? 1.0 : 0.0) - (input.descend ? 1.0 : 0.0);
            movement.mouseDx = input.mouseCaptured ? static_cast<double>(input.mouseDx) : 0.0;
            movement.mouseDy = input.mouseCaptured ? static_cast<double>(input.mouseDy) : 0.0;
            movement.sprint = input.sprint;
            movement.toggleFlight = input.toggleFlight;
            camera.update(movement, dt);

            const vf::CelestialEnvironmentSample localEnvironment = celestial.sampleEnvironment(camera.position());
            const vf::CelestialBody* localBody = celestial.body(localEnvironment.bodyId);
            const vf::CelestialBody* sun = celestial.body(starId);
            const bool cameraHasSun = hasLineOfSightToStar(celestial, camera.position(), starId);

            glm::vec3 sky{0.0F};
            if (localBody != nullptr && localEnvironment.pressurePa > 0.0 && localBody->atmosphere.enabled) {
                const double pressureRatio = std::clamp(
                    localEnvironment.pressurePa / std::max(1.0, localBody->atmosphere.surfacePressurePa),
                    0.0,
                    1.0);
                const glm::dvec3 sunDirection = sun != nullptr
                    ? safeNormalize(sun->position - camera.position())
                    : glm::dvec3{0.0, 1.0, 0.0};
                const double solarElevation = glm::dot(camera.up(), sunDirection);
                const double daylight = cameraHasSun
                    ? std::clamp((solarElevation + 0.10) / 0.45, 0.0, 1.0)
                    : 0.0;
                const double twilight = std::clamp(1.0 - std::abs(solarElevation + 0.06) / 0.18, 0.0, 1.0);
                const double cloudDimming = 1.0 - 0.40 * std::clamp(localEnvironment.cloudCover, 0.0, 1.0);
                const glm::dvec3 rayleigh = localBody->atmosphere.rayleighRgb
                    * pressureRatio * (0.008 + 0.30 * daylight);
                const glm::dvec3 mie = glm::dvec3{1.0, 0.72, 0.48}
                    * localBody->atmosphere.mieStrength * pressureRatio * (0.08 * daylight + 0.05 * twilight);
                sky = glm::vec3(glm::clamp((rayleigh + mie) * cloudDimming, glm::dvec3{0.0}, glm::dvec3{1.0}));
            }

            const auto cameraField = fields.sample(camera.position());
            lastLux = cameraHasSun
                ? vf::ElectromagneticRadiationSystem::photopicIlluminanceLux(
                    cameraField.visibleIrradianceWattsPerSquareMeter)
                : 0.0;
            const double sensorCurrent = cameraHasSun
                ? vf::ElectromagneticRadiationSystem::lightSensorCurrentAmperes(
                    lightSensor,
                    cameraField.visibleIrradianceWattsPerSquareMeter)
                : 0.0;
            (void)sensorCurrent;

            const auto [width, height] = platform.drawableSize();
            const float aspect = height > 0 ? static_cast<float>(width) / static_cast<float>(height) : 16.0F / 9.0F;

            vf::PlanetMesh dynamicMesh = playground.buildDebugMesh();
            vf::appendDebugSphere(dynamicMesh, pointChargePosition, 0.20, {0.85F, 0.22F, 0.78F}, 6U, 10U);
            vf::appendDebugRod(
                dynamicMesh,
                solenoidPosition - fieldUpWorld * 0.35,
                solenoidPosition + fieldUpWorld * 0.35,
                0.18,
                {0.24F, 0.62F, 0.95F});
            vf::appendDebugSphere(dynamicMesh, inductionCoil.position, 0.23, {0.20F, 0.92F, 0.88F}, 6U, 10U);
            vf::appendDebugSphere(dynamicMesh, lens.position, lens.apertureRadiusMeters, {0.45F, 0.82F, 0.98F}, 6U, 12U);
            const float heat01 = static_cast<float>(std::clamp((tinder.temperatureK - 293.15) / 500.0, 0.0, 1.0));
            const glm::vec3 tinderColor = tinder.ignited
                ? glm::vec3{1.0F, 0.18F, 0.02F}
                : glm::vec3{0.36F + 0.64F * heat01, 0.22F, 0.08F};
            vf::appendDebugSphere(dynamicMesh, tinder.position, 0.13, tinderColor, 6U, 10U);
            if (const auto* chargedBall = physics.body(chargedBallId)) {
                vf::appendDebugSphere(dynamicMesh, chargedBall->position, 0.24, {0.80F, 0.30F, 0.92F}, 7U, 12U);
            }
            if (const auto* cinder = celestial.body(secondaryId)) {
                vf::appendCelestialBodyProxy(
                    dynamicMesh,
                    cinder->position,
                    cinder->orientation,
                    cinder->radiusMeters,
                    16U,
                    glm::vec3(cinder->visibleAlbedo));
            }
            if (sun != nullptr) {
                // Bright physical photosphere proxy. It is still the exact object used for light,
                // heat and orbital gravity; high vertex color merely keeps an emissive star legible
                // until a dedicated emissive material pass is added.
                vf::appendDebugSphere(
                    dynamicMesh,
                    sun->position,
                    sun->radiusMeters,
                    glm::vec3(sunDisplayColor) * 12.0F,
                    14U,
                    24U);
            }

            for (const auto& body : celestial.bodies()) {
                if (body.type == vf::CelestialBodyType::Star || !body.atmosphere.enabled
                    || body.atmosphere.heightMeters <= 0.0) {
                    continue;
                }
                const double outerRadius = body.radiusMeters + body.atmosphere.heightMeters;
                const double cameraRadius = glm::length(camera.position() - body.position);
                if (cameraRadius <= outerRadius * 0.985) continue;
                vf::appendAtmosphereProxy(
                    dynamicMesh,
                    body.position,
                    outerRadius,
                    14U,
                    glm::vec3(body.atmosphere.rayleighRgb),
                    atmosphereOpticalStrength(body));
            }

            // Far destinations are rendered as tiny sky proxies using their real catalog direction.
            // Their actual multi-million-metre coordinates remain in double precision and no local
            // terrain/collision/weather model exists until the activation query says they are near.
            constexpr double skyProxyDistance = 600000.0;
            for (const auto* record : universe.nearestVisible(camera.position(), 128U)) {
                if (record == nullptr) continue;
                const glm::dvec3 direction = safeNormalize(record->positionMeters - camera.position());
                const glm::dvec3 proxyPosition = camera.position() + direction * skyProxyDistance;
                glm::vec3 color = glm::vec3(record->displayColor);
                double radius = 260.0;
                switch (record->type) {
                case vf::CatalogObjectType::StarSystem:
                    color *= 10.0F;
                    radius = 520.0;
                    break;
                case vf::CatalogObjectType::RoguePlanet:
                    color *= 2.5F;
                    radius = 320.0;
                    break;
                case vf::CatalogObjectType::AsteroidField:
                    color *= 1.8F;
                    radius = 230.0;
                    break;
                case vf::CatalogObjectType::Comet:
                    color *= 4.0F;
                    radius = 280.0;
                    break;
                }
                vf::appendDebugSphere(dynamicMesh, proxyPosition, radius, color, 3U, 5U);
            }

            // GPU positions are rebased around Aster. Authoritative world/physics coordinates stay
            // star-centric doubles; only rendering uses the nearby origin for float precision.
            const glm::dvec3 renderOrigin = aster != nullptr ? aster->position : glm::dvec3{};
            rebaseMesh(dynamicMesh, renderOrigin);
            renderer.setDynamicMesh(dynamicMesh);

            const glm::vec3 sunDirectionToLight = sun != nullptr
                ? glm::vec3(safeNormalize(sun->position - camera.position()))
                : glm::vec3{0.38F, 0.83F, 0.41F};
            const double cameraStellarIrradiance = cameraHasSun
                ? cameraField.irradianceWattsPerSquareMeter.total()
                : 0.0;
            const float sunIntensity = static_cast<float>(
                2.2 * std::clamp(cameraStellarIrradiance / 1320.0, 0.0, 4.0));
            const glm::dquat primaryRotation = aster != nullptr
                ? aster->orientation
                : glm::dquat{1.0, 0.0, 0.0, 0.0};
            renderer.drawFrame(
                sky,
                camera.viewProjection(aspect),
                camera.position() - renderOrigin,
                sunDirectionToLight,
                sunDisplayColor,
                sunIntensity,
                primaryRotation);

            diagnosticsTime += dt;
            ++diagnosticsFrames;
            if (diagnosticsTime >= 1.0) {
                const double fps = diagnosticsTime > 0.0
                    ? static_cast<double>(diagnosticsFrames) / diagnosticsTime
                    : 0.0;
                const double gravity = glm::length(localEnvironment.gravityAcceleration);
                const vf::CelestialBody* gravityBody = celestial.gameplayReferenceBodyAt(camera.position());
                const auto nearbyCatalog = universe.activeWithin(camera.position(), 60000.0);
                std::ostringstream title;
                title << "Voxel Frontier v7 | FPS " << std::fixed << std::setprecision(0) << fps
                      << " | " << (camera.flightMode() ? "FLIGHT" : "SURFACE")
                      << " | SOI " << (gravityBody != nullptr ? gravityBody->name : std::string{"Interplanetary"})
                      << " | g " << std::setprecision(2) << gravity
                      << " | P " << std::setprecision(1) << localEnvironment.pressurePa / 1000.0 << "kPa"
                      << " | Lux " << std::setprecision(0) << lastLux
                      << " | CatalogNear " << nearbyCatalog.size()
                      << " | Coil " << std::setprecision(3) << inductionCoil.inducedEmfVolts << "V"
                      << " | Target " << std::setprecision(1) << tinder.temperatureK - 273.15 << "C"
                      << (tinder.ignited ? " IGNITED" : "")
                      << " | SurfaceLocks " << surfaceFrames.attachmentCount();
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
