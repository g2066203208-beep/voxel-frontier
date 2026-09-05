#pragma once

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

#include "vf/world/PlanetSurface.hpp"

namespace vf {

void appendDebugSphere(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double radius,
    const glm::vec3& color,
    unsigned rings = 8U,
    unsigned segments = 12U,
    glm::vec4 material = {0.0F, 0.72F, 0.0F, 0.0F});

void appendDebugBox(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    const glm::dquat& orientation,
    const glm::dvec3& halfExtents,
    const glm::vec3& color,
    glm::vec4 material = {0.0F, 0.72F, 0.0F, 0.0F});

void appendDebugRod(
    PlanetMesh& mesh,
    const glm::dvec3& a,
    const glm::dvec3& b,
    double halfThickness,
    const glm::vec3& color,
    glm::vec4 material = {0.0F, 0.72F, 0.0F, 0.0F});

// Very cheap projected solar-shadow receiver primitive used by the stability preview. It is not a
// replacement for the general shadow-map path, but gives contact/scale cues for local props for
// only a few dozen triangles and no extra Vulkan pass.
void appendDebugDisc(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    const glm::dvec3& normal,
    double radiusX,
    double radiusY,
    const glm::vec3& color,
    unsigned segments = 20U,
    glm::vec4 material = {0.0F, 1.0F, 0.0F, 0.0F});

} // namespace vf
