#include "vf/player/PlanetCamera.hpp"

#include <algorithm>
#include <cmath>

#include <glm/ext/matrix_clip_space.hpp>
#include <glm/ext/matrix_transform.hpp>
#include <glm/geometric.hpp>

namespace vf {

namespace {

[[nodiscard]] glm::dvec3 safeEast(const glm::dvec3& up) {
    glm::dvec3 east = glm::cross(glm::dvec3{0.0, 1.0, 0.0}, up);
    if (glm::dot(east, east) < 1.0e-8) east = glm::cross(glm::dvec3{1.0, 0.0, 0.0}, up);
    return glm::normalize(east);
}

} // namespace

PlanetCamera::PlanetCamera(const PlanetDefinition& planet) : planet_(&planet) {
    const glm::dvec3 startDirection = glm::normalize(glm::dvec3{0.72, 0.52, 0.46});
    const double surface = planetSurfaceRadius(planet, startDirection);
    position_ = startDirection * (surface + eyeHeight_);
}

glm::dvec3 PlanetCamera::up() const {
    return glm::normalize(position_);
}

double PlanetCamera::altitude() const {
    const glm::dvec3 d = up();
    return glm::length(position_) - planetSurfaceRadius(*planet_, d);
}

glm::dvec3 PlanetCamera::forwardDirection() const {
    const glm::dvec3 localUp = up();
    const glm::dvec3 east = safeEast(localUp);
    const glm::dvec3 north = glm::normalize(glm::cross(localUp, east));
    const glm::dvec3 tangentForward = glm::normalize(std::cos(heading_) * north + std::sin(heading_) * east);
    return glm::normalize(std::cos(pitch_) * tangentForward + std::sin(pitch_) * localUp);
}

void PlanetCamera::update(const PlanetMovementInput& input, double dt) {
    if (dt <= 0.0) return;
    dt = std::min(dt, 0.05);

    constexpr double mouseSensitivity = 0.0022;
    heading_ -= input.mouseDx * mouseSensitivity;
    pitch_ = std::clamp(pitch_ - input.mouseDy * mouseSensitivity, -1.45, 1.45);

    const glm::dvec3 localUp = up();
    const glm::dvec3 east = safeEast(localUp);
    const glm::dvec3 north = glm::normalize(glm::cross(localUp, east));
    const glm::dvec3 tangentForward = glm::normalize(std::cos(heading_) * north + std::sin(heading_) * east);
    const glm::dvec3 tangentRight = glm::normalize(glm::cross(tangentForward, localUp));

    const double currentAltitude = altitude();
    const double altitudeScale = 1.0 + std::max(0.0, currentAltitude) / 80.0;
    const double baseSpeed = input.sprint ? 34.0 : 12.0;
    const double tangentSpeed = baseSpeed * std::min(altitudeScale, 30.0);
    const double verticalSpeed = (input.sprint ? 70.0 : 28.0) * std::min(altitudeScale, 20.0);

    glm::dvec3 candidate = position_;
    candidate += (tangentForward * input.forward + tangentRight * input.right) * tangentSpeed * dt;
    candidate += localUp * input.vertical * verticalSpeed * dt;

    glm::dvec3 direction = glm::normalize(candidate);
    const double minimumRadius = planetSurfaceRadius(*planet_, direction) + eyeHeight_;
    double radius = glm::length(candidate);
    radius = std::max(radius, minimumRadius);
    position_ = direction * radius;
}

glm::mat4 PlanetCamera::viewProjection(float aspectRatio) const {
    aspectRatio = std::max(aspectRatio, 0.1F);
    const glm::dvec3 look = forwardDirection();
    const glm::dvec3 localUp = up();

    // Camera-relative rendering: GPU sees the planet translated by -camera position,
    // keeping float precision stable while the authoritative camera remains double precision.
    const glm::vec3 eye{0.0F};
    const glm::vec3 target = glm::vec3(look);
    const glm::vec3 upVector = glm::vec3(localUp);
    const glm::mat4 view = glm::lookAtRH(eye, target, upVector);

    glm::mat4 projection = glm::perspectiveRH_ZO(glm::radians(68.0F), aspectRatio, 0.05F, 10000.0F);
    projection[1][1] *= -1.0F;
    return projection * view;
}

} // namespace vf
