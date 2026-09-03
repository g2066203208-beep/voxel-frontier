#include "vf/gameplay/PhysicsPlayground.hpp"
#include "vf/physics/PhysicsWorld.hpp"
#include "vf/platform/SdlPlatform.hpp"
#include "vf/player/PlanetCamera.hpp"
#include "vf/render/VulkanRenderer.hpp"
#include "vf/world/PlanetSurface.hpp"

#include <algorithm>
#include <chrono>
#include <exception>
#include <iomanip>
#include <iostream>
#include <sstream>

#include <glm/common.hpp>
#include <glm/geometric.hpp>

int main() {
    try {
        vf::SdlPlatform platform{"Voxel Frontier — Native Physics Planet", 1600, 900};
        vf::VulkanRenderer renderer{platform.window()};

        vf::PlanetDefinition planet{};
        planet.seed = 0x71A9F20DULL;
        planet.radius = 240.0;
        planet.maxElevation = 22.0;
        planet.atmosphereHeight = 120.0;

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

        vf::PlanetMesh mesh = vf::buildPlanetSurface(planet, 64U);
        // A second celestial body is a real geometry proxy with a real world-space location,
        // not a skybox decoration. Later LOD stages will promote it into its own full planet.
        vf::appendCelestialProxy(
            mesh,
            glm::dvec3{1050.0, 520.0, -760.0},
            92.0,
            10U,
            glm::vec3{0.62F, 0.30F, 0.22F});
        renderer.uploadPlanetMesh(mesh);

        vf::PlanetCamera camera{planet};
        const glm::dvec3 cameraUp = camera.up();
        glm::dvec3 tangentForward = camera.forwardDirection()
            - cameraUp * glm::dot(camera.forwardDirection(), cameraUp);
        tangentForward = glm::normalize(tangentForward);
        const glm::dvec3 playgroundDirection = glm::normalize(camera.position() + tangentForward * 22.0);
        vf::PhysicsPlayground playground{physics, planet, playgroundDirection};

        const auto seaLevelAtmosphere = physics.environment().sampleAtmosphere({0.0, planet.radius, 0.0}, 0.0);

        std::cout << "Voxel Frontier native spherical physics runtime\n";
        std::cout << "GPU: " << renderer.gpuName() << '\n';
        std::cout << "Vulkan API: "
                  << VK_API_VERSION_MAJOR(renderer.apiVersion()) << '.'
                  << VK_API_VERSION_MINOR(renderer.apiVersion()) << '.'
                  << VK_API_VERSION_PATCH(renderer.apiVersion()) << '\n';
        std::cout << "Planet radius: " << planet.radius << " m\n";
        std::cout << "Physics fixed step: " << (1.0 / physics.fixedDeltaSeconds()) << " Hz\n";
        std::cout << "Sea-level atmosphere: " << seaLevelAtmosphere.temperatureK - 273.15 << " C, "
                  << seaLevelAtmosphere.pressurePa / 1000.0 << " kPa, "
                  << seaLevelAtmosphere.densityKgPerM3 << " kg/m^3\n";
        std::cout << "Static planet/celestial triangles: " << renderer.triangleCount() << '\n';
        std::cout << "Physics playground: spring payload, powered hinge rotor, geared shafts, air-buoyant envelope, falling rigid bodies, wind/gravity tree felling\n";
        std::cout << "Controls: WASD move, mouse look, Shift boost, Space ascend, Ctrl descend, Esc release/capture mouse\n";

        using Clock = std::chrono::steady_clock;
        auto previous = Clock::now();
        double diagnosticsTime = 0.0;
        std::uint64_t diagnosticsFrames = 0;

        while (platform.pumpEvents()) {
            const auto now = Clock::now();
            double dt = std::chrono::duration<double>(now - previous).count();
            previous = now;
            dt = std::clamp(dt, 0.0, 0.05);

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

            const auto atmosphere = physics.environment().sampleAtmosphere(camera.position(), physics.simulationTime());
            const auto [width, height] = platform.drawableSize();
            const float aspect = height > 0 ? static_cast<float>(width) / static_cast<float>(height) : 16.0F / 9.0F;
            const double densityReference = std::max(1.0e-6, seaLevelAtmosphere.densityKgPerM3);
            const float atmosphereVisibility = static_cast<float>(std::clamp(atmosphere.densityKgPerM3 / densityReference, 0.0, 1.0));
            const float cloudDimming = static_cast<float>(1.0 - 0.28 * std::clamp(physics.environment().weather.cloudCover, 0.0, 1.0));
            const glm::vec3 atmosphereSky{0.055F * cloudDimming, 0.15F * cloudDimming, 0.29F * cloudDimming};
            const glm::vec3 spaceSky{0.0015F, 0.0025F, 0.008F};
            const glm::vec3 sky = glm::mix(spaceSky, atmosphereSky, atmosphereVisibility);

            const vf::PlanetMesh dynamicMesh = playground.buildDebugMesh();
            renderer.setDynamicMesh(dynamicMesh);
            renderer.drawFrame(sky, camera.viewProjection(aspect), camera.position());

            diagnosticsTime += dt;
            ++diagnosticsFrames;
            if (diagnosticsTime >= 1.0) {
                const double fps = diagnosticsTime > 0.0
                    ? static_cast<double>(diagnosticsFrames) / diagnosticsTime
                    : 0.0;
                const double windSpeed = glm::length(atmosphere.windVelocity);
                std::ostringstream title;
                title << "Voxel Frontier | FPS " << std::fixed << std::setprecision(0) << fps
                      << " | Bodies " << physics.bodies().size()
                      << " | Pairs " << physics.lastBroadphaseCandidateCount()
                      << " | Joints " << physics.activeConstraintCount()
                      << " | DynTris " << renderer.dynamicTriangleCount()
                      << " | T " << std::setprecision(1) << atmosphere.temperatureK - 273.15 << " C"
                      << " | P " << atmosphere.pressurePa / 1000.0 << " kPa"
                      << " | Wind " << windSpeed << " m/s";
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
