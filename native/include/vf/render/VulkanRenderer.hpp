#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>
#include <volk.h>

#include "vf/world/PlanetSurface.hpp"
#include "vf/world/StreamingEcology.hpp"

struct SDL_Window;

// Keep the proven V14 renderer implementation intact.  Its 2048² shadows, asynchronous mapped
// frame meshes, reverse-Z depth and fullscreen atmosphere remain authoritative; this adapter only
// attaches deterministic near-field ecology immediately before a streamed terrain mesh is uploaded.
#define final
#define VulkanRenderer VulkanRendererV14
#include "vf/render/VulkanRendererV14.hpp"
#undef VulkanRenderer
#undef final

namespace vf {

class VulkanRenderer final : public VulkanRendererV14 {
public:
    explicit VulkanRenderer(SDL_Window* window) : VulkanRendererV14(window) {}

    VulkanRenderer(const VulkanRenderer&) = delete;
    VulkanRenderer& operator=(const VulkanRenderer&) = delete;

    void uploadPlanetMesh(const PlanetMesh& mesh) {
        PlanetMesh decorated = mesh;
        detail::appendStreamingEcology(decorated, lastCameraSurface_, lastPlanetCenterSurface_);
        VulkanRendererV14::uploadPlanetMesh(std::move(decorated));
    }

    void uploadPlanetMesh(PlanetMesh&& mesh) {
        detail::appendStreamingEcology(mesh, lastCameraSurface_, lastPlanetCenterSurface_);
        VulkanRendererV14::uploadPlanetMesh(std::move(mesh));
    }

    void drawFrame(
        const glm::mat4& viewProjection,
        const glm::dvec3& cameraPosition,
        const RenderFrameEnvironment& environment,
        const glm::dquat& staticObjectRotation = glm::dquat{1.0, 0.0, 0.0, 0.0}) {
        lastCameraSurface_ = cameraPosition;
        lastPlanetCenterSurface_ = environment.planetCenter;
        VulkanRendererV14::drawFrame(viewProjection, cameraPosition, environment, staticObjectRotation);
    }

private:
    // Before the first draw the V14 local surface frame is centred on the initial spawn.  This
    // Earth-radius fallback is therefore already a useful radial reference for the first ecology
    // upload; subsequent frames replace it with Main.cpp's exact transformed planet centre.
    glm::dvec3 lastCameraSurface_{0.0, 1.75, 0.0};
    glm::dvec3 lastPlanetCenterSurface_{0.0, -6371000.0, 0.0};
};

} // namespace vf
