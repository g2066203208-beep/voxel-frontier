#include "vf/gameplay/PhysicsPlayground.hpp"
#include "vf/physics/PhysicsWorld.hpp"
#include "vf/physics/SpectralOptics.hpp"
#include "vf/platform/SdlPlatform.hpp"
#include "vf/player/PlanetCamera.hpp"
#include "vf/render/VulkanRenderer.hpp"
#include "vf/world/CelestialSystem.hpp"
#include "vf/world/PlanetSurface.hpp"

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

} // namespace

int main() {
    try {
        vf::SdlPlatform platform{"Voxel Frontier — Celestial Physics v6", 1600, 900};
        vf::VulkanRenderer renderer{platform.window()};

        vf::PlanetDefinition planet{};
        planet.seed = 0x71A9F20DULL;
        planet.radius = 240.0;
        planet.maxElevation = 22.0;
        planet.atmosphereHeight = 120.0;

        // Real game-scale celestial system. Distances/times are intentionally compressed so
        // orbit and rotation are visible during play while preserving Newtonian relationships.
        vf::CelestialSystem celestial;

        vf::CelestialBody primary{};
        primary.type = vf::CelestialBodyType::Planet;
        primary.name = "Aster";
        primary.radiusMeters = planet.radius;
        primary.massKg = 9.81 * primary.radiusMeters * primary.radiusMeters
            / vf::CelestialSystem::kGravitationalConstant;
        primary.spinAxis = safeNormalize({0.08, 1.0, 0.03});
        primary.spinRateRadPerSecond = 2.0 * kPi / 300.0;
        primary.visibleAlbedo = {0.30, 0.55, 0.32};
        primary.atmosphere.enabled = true;
        primary.atmosphere.heightMeters = planet.atmosphereHeight;
        primary.atmosphere.surfacePressurePa = 101325.0;
        primary.atmosphere.surfaceTemperatureK = 288.15;
        primary.atmosphere.scaleHeightMeters = 72.0;
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

        vf::CelestialBody star{};
        star.type = vf::CelestialBodyType::Star;
        star.name = "Helion";
        star.radiusMeters = 180.0;
        star.massKg = 0.0; // Directional gameplay light source; no giant long-range gravity well.
        star.position = {7600.0, 3100.0, -5200.0};
        const double starDistanceSquared = glm::dot(star.position, star.position);
        star.luminosityWatts = 4.0 * kPi * starDistanceSquared * 1320.0;
        const std::uint32_t starId = celestial.addBody(star);

        vf::CelestialBody secondary{};
        secondary.type = vf::CelestialBodyType::Planet;
        secondary.name = "Cinder";
        secondary.radiusMeters = 92.0;
        secondary.massKg = 3.7 * secondary.radiusMeters * secondary.radiusMeters
            / vf::CelestialSystem::kGravitationalConstant;
        secondary.position = {1050.0, 520.0, -760.0};
        secondary.orbitParentId = primaryId;
        const glm::dvec3 orbitalRadius = secondary.position - primary.position;
        const glm::dvec3 orbitalNormal = safeNormalize({0.08, 1.0, 0.20});
        const glm::dvec3 orbitalTangent = safeNormalize(glm::cross(orbitalNormal, orbitalRadius));
        const double orbitalSpeed = std::sqrt(
            vf::CelestialSystem::kGravitationalConstant * primary.massKg / glm::length(orbitalRadius));
        secondary.linearVelocity = orbitalTangent * orbitalSpeed;
        secondary.spinAxis = safeNormalize({0.25, 1.0, -0.12});
        secondary.spinRateRadPerSecond = 2.0 * kPi / 95.0;
        secondary.visibleAlbedo = {0.62, 0.30, 0.22};
        secondary.atmosphere.enabled = true;
        secondary.atmosphere.heightMeters = 72.0;
        secondary.atmosphere.surfacePressurePa = 2200.0;
        secondary.atmosphere.surfaceTemperatureK = 238.0;
        secondary.atmosphere.molarMassKgPerMol = 0.043;
        secondary.atmosphere.scaleHeightMeters = 31.0;
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
        environment.ocean.surfaceRadius = planet.radius - 6.0;
        environment.ocean.densityKgPerM3 = 997.0;
        vf::PhysicsWorld physics{environment};

        // The detailed primary terrain stays in the static mesh. Other celestial bodies are
        // tiny dynamic proxies so orbit/spin costs only a few hundred vertices per frame.
        vf::PlanetMesh mesh = vf::buildPlanetSurface(planet, 64U);
        renderer.uploadPlanetMesh(mesh);

        vf::PlanetCamera camera{planet, &celestial, primaryId};
        const glm::dvec3 cameraUp = camera.up();
        glm::dvec3 tangentForward = camera.forwardDirection()
            - cameraUp * glm::dot(camera.forwardDirection(), cameraUp);
        tangentForward = glm::normalize(tangentForward);
        const glm::dvec3 playgroundDirection = glm::normalize(camera.position() + tangentForward * 22.0);
        vf::PhysicsPlayground playground{physics, planet, playgroundDirection};

        const auto sunSpectrum = vf::blackbodySpectrum(5772.0);
        const glm::dvec3 sunLinearRgb = vf::spectrumToLinearSrgb(sunSpectrum);

        std::cout << "Voxel Frontier celestial + spectral physics runtime\n";
        std::cout << "GPU: " << renderer.gpuName() << '\n';
        std::cout << "Vulkan API: "
                  << VK_API_VERSION_MAJOR(renderer.apiVersion()) << '.'
                  << VK_API_VERSION_MINOR(renderer.apiVersion()) << '.'
                  << VK_API_VERSION_PATCH(renderer.apiVersion()) << '\n';
        std::cout << "Celestial bodies: " << celestial.bodies().size() << " (Aster, Helion, Cinder)\n";
        std::cout << "Primary surface gravity: 9.81 m/s^2; Cinder surface gravity: 3.7 m/s^2\n";
        std::cout << "Celestial tick: 10 Hz; rigid-body physics: " << (1.0 / physics.fixedDeltaSeconds()) << " Hz\n";
        std::cout << "Solar six-band linear RGB reference: "
                  << sunLinearRgb.x << ", " << sunLinearRgb.y << ", " << sunLinearRgb.z << '\n';
        std::cout << "Vacuum background is exact black; atmosphere color exists only inside a body's atmosphere.\n";
        std::cout << "Controls: WASD tangent move, mouse look, Shift boost, Space/Ctrl local thrust, Esc release/capture mouse\n";

        using Clock = std::chrono::steady_clock;
        auto previous = Clock::now();
        double diagnosticsTime = 0.0;
        double celestialAccumulator = 0.0;
        std::uint64_t diagnosticsFrames = 0;

        while (platform.pumpEvents()) {
            const auto now = Clock::now();
            double dt = std::chrono::duration<double>(now - previous).count();
            previous = now;
            dt = std::clamp(dt, 0.0, 0.05);

            celestialAccumulator += dt;
            while (celestialAccumulator >= 0.10) {
                celestial.step(0.10);
                celestialAccumulator -= 0.10;
            }

            physics.advance(dt);
            playground.update(dt);

            if (platform.consumeResize()) renderer.requestResize();

            const auto& input = platform.input();
            vf::PlanetMovementInput movement{};
            movement.forward = (input.forward ? 1.0 : 0.0) - (input.backward ? 1.0 : 0.0);
            movement.right = (input.right ? 1.0 : 0.0) - (input.left ? 1.0 : 0.0);
            movement.vertical = (input.ascend ? 1.0 : 0.0) - (input.descend ? 1.0 : 0.0);
            movement.mouseDx = input.mouseCaptured ? static_cast<double>(input.mouseDx) : 0.0;
            movement.mouseDy = input.mouseCaptured ? static_cast<double>(input.mouseDy) : 0.0;
            movement.sprint = input.sprint;
            camera.update(movement, dt);

            const vf::CelestialEnvironmentSample localEnvironment = celestial.sampleEnvironment(camera.position());
            const vf::CelestialBody* localBody = celestial.body(localEnvironment.bodyId);
            const vf::CelestialBody* sun = celestial.body(starId);

            // Vacuum contains no participating medium, so the clear color is exactly black.
            // Inside an atmosphere use a deliberately cheap density + solar-elevation scattering
            // approximation; a later LUT pass can refine the angular sky without changing physics.
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
                const double daylight = std::clamp((solarElevation + 0.10) / 0.45, 0.0, 1.0);
                const double twilight = std::clamp(1.0 - std::abs(solarElevation + 0.06) / 0.18, 0.0, 1.0);
                const double cloudDimming = 1.0 - 0.40 * std::clamp(localEnvironment.cloudCover, 0.0, 1.0);
                const glm::dvec3 rayleigh = localBody->atmosphere.rayleighRgb
                    * pressureRatio * (0.015 + 0.30 * daylight);
                const glm::dvec3 mie = glm::dvec3{1.0, 0.72, 0.48}
                    * localBody->atmosphere.mieStrength * pressureRatio * (0.08 * daylight + 0.05 * twilight);
                sky = glm::vec3(glm::clamp((rayleigh + mie) * cloudDimming, glm::dvec3{0.0}, glm::dvec3{1.0}));
            }

            const auto [width, height] = platform.drawableSize();
            const float aspect = height > 0 ? static_cast<float>(width) / static_cast<float>(height) : 16.0F / 9.0F;

            vf::PlanetMesh dynamicMesh = playground.buildDebugMesh();
            if (const auto* cinder = celestial.body(secondaryId)) {
                vf::appendCelestialBodyProxy(
                    dynamicMesh,
                    cinder->position,
                    cinder->orientation,
                    cinder->radiusMeters,
                    10U,
                    glm::vec3(cinder->visibleAlbedo));
            }
            renderer.setDynamicMesh(dynamicMesh);
            renderer.drawFrame(sky, camera.viewProjection(aspect), camera.position());

            diagnosticsTime += dt;
            ++diagnosticsFrames;
            if (diagnosticsTime >= 1.0) {
                const double fps = diagnosticsTime > 0.0
                    ? static_cast<double>(diagnosticsFrames) / diagnosticsTime
                    : 0.0;
                const double windSpeed = glm::length(localEnvironment.windVelocity);
                const double gravity = glm::length(localEnvironment.gravityAcceleration);
                std::ostringstream title;
                title << "Voxel Frontier v6 | FPS " << std::fixed << std::setprecision(0) << fps
                      << " | World " << (localBody != nullptr ? localBody->name : std::string{"Vacuum"})
                      << " | Alt " << std::setprecision(1) << localEnvironment.altitudeMeters << " m"
                      << " | g " << gravity << " m/s2"
                      << " | P " << localEnvironment.pressurePa / 1000.0 << " kPa"
                      << " | T " << localEnvironment.temperatureK - 273.15 << " C"
                      << " | Wind " << windSpeed << " m/s"
                      << " | Cloud " << localEnvironment.cloudCover * 100.0 << "%"
                      << " | Ground " << (camera.grounded() ? "YES" : "NO");
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
