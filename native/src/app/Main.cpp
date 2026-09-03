#include "vf/core/Engine.hpp"
#include "vf/platform/SdlPlatform.hpp"
#include "vf/render/VulkanRenderer.hpp"

#include <chrono>
#include <cmath>
#include <exception>
#include <iostream>

int main() {
    try {
        vf::SdlPlatform platform{"Voxel Frontier — Native Engine", 1600, 900};
        vf::VulkanRenderer renderer{platform.window()};
        vf::Engine engine;
        engine.bootstrap();

        std::cout << "Voxel Frontier native runtime\n";
        std::cout << "GPU: " << renderer.gpuName() << '\n';
        std::cout << "Vulkan API: "
                  << VK_API_VERSION_MAJOR(renderer.apiVersion()) << '.'
                  << VK_API_VERSION_MINOR(renderer.apiVersion()) << '.'
                  << VK_API_VERSION_PATCH(renderer.apiVersion()) << '\n';
        std::cout << "Warm chunks: " << engine.world().loadedChunkCount() << '\n';

        using Clock = std::chrono::steady_clock;
        auto previous = Clock::now();

        while (platform.pumpEvents()) {
            const auto now = Clock::now();
            const double dt = std::chrono::duration<double>(now - previous).count();
            previous = now;
            engine.tick(dt);

            if (platform.consumeResize()) renderer.requestResize();

            const float phase = static_cast<float>(std::fmod(engine.elapsedSeconds() * 0.08, 1.0));
            const float skyR = 0.08F + phase * 0.04F;
            const float skyG = 0.16F + phase * 0.05F;
            const float skyB = 0.24F + phase * 0.08F;
            renderer.drawFrame(skyR, skyG, skyB);
        }

        return 0;
    } catch (const std::exception& exception) {
        std::cerr << "Fatal error: " << exception.what() << '\n';
        return 1;
    }
}
