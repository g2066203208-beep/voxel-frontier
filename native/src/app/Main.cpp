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

int main() {
    try {
        vf::SdlPlatform platform{"Voxel Frontier — Spherical Planet Prototype", 1600, 900};
        vf::VulkanRenderer renderer{platform.window()};

        vf::PlanetDefinition planet{};
        planet.seed = 0x71A9F20DULL;
        planet.radius = 240.0;
        planet.maxElevation = 22.0;
        planet.atmosphereHeight = 120.0;

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

        std::cout << "Voxel Frontier native spherical runtime\n";
        std::cout << "GPU: " << renderer.gpuName() << '\n';
        std::cout << "Vulkan API: "
                  << VK_API_VERSION_MAJOR(renderer.apiVersion()) << '.'
                  << VK_API_VERSION_MINOR(renderer.apiVersion()) << '.'
                  << VK_API_VERSION_PATCH(renderer.apiVersion()) << '\n';
        std::cout << "Planet radius: " << planet.radius << " m\n";
        std::cout << "Surface + celestial proxy triangles: " << renderer.triangleCount() << '\n';
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

            const auto [width, height] = platform.drawableSize();
            const float aspect = height > 0 ? static_cast<float>(width) / static_cast<float>(height) : 16.0F / 9.0F;
            const double altitude = camera.altitude();
            const float spaceBlend = static_cast<float>(std::clamp(altitude / planet.atmosphereHeight, 0.0, 1.0));
            const glm::vec3 atmosphereSky{0.055F, 0.15F, 0.29F};
            const glm::vec3 spaceSky{0.0015F, 0.0025F, 0.008F};
            const glm::vec3 sky = glm::mix(atmosphereSky, spaceSky, spaceBlend);

            renderer.drawFrame(sky, camera.viewProjection(aspect), camera.position());

            diagnosticsTime += dt;
            ++diagnosticsFrames;
            if (diagnosticsTime >= 1.0) {
                const double fps = diagnosticsTime > 0.0
                    ? static_cast<double>(diagnosticsFrames) / diagnosticsTime
                    : 0.0;
                std::ostringstream title;
                title << "Voxel Frontier | FPS " << std::fixed << std::setprecision(0) << fps
                      << " | Tris " << renderer.triangleCount()
                      << " | Alt " << std::setprecision(1) << altitude << " m";
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
