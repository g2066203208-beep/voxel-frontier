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
    unsigned segments = 12U);

void appendDebugBox(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    const glm::dquat& orientation,
    const glm::dvec3& halfExtents,
    const glm::vec3& color);

void appendDebugRod(
    PlanetMesh& mesh,
    const glm::dvec3& a,
    const glm::dvec3& b,
    double halfThickness,
    const glm::vec3& color);

} // namespace vf
