#include "vf/player/PlanetCamera.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

#include <glm/ext/matrix_clip_space.hpp>
#include <glm/ext/matrix_transform.hpp>
#include <glm/geometric.hpp>

namespace vf {

namespace {

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-12) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] glm::dvec3 safeEast(const glm::dvec3& up) {
    glm::dvec3 east = glm::cross(glm::dvec3{0.0, 1.0, 0.0}, up);
    if (glm::dot(east, east) < 1.0e-8) east = glm::cross(glm::dvec3{1.0, 0.0, 0.0}, up);
    return glm::normalize(east);
}

[[nodiscard]] glm::dvec3 bodyLocalDirection(
    const CelestialBody& body,
    const glm::dvec3& worldDirection) noexcept {
    return safeNormalize(glm::conjugate(glm::normalize(body.orientation)) * safeNormalize(worldDirection));
}

[[nodiscard]] glm::dvec3 celestialSurfaceVelocity(
    const CelestialBody& body,
    const glm::dvec3& worldPoint) noexcept {
    const glm::dvec3 spinAxis = safeNormalize(body.spinAxis);
    const glm::dvec3 angularVelocity = spinAxis * body.spinRateRadPerSecond;
    return body.linearVelocity + glm::cross(angularVelocity, worldPoint - body.position);
}

} // namespace

PlanetCamera::PlanetCamera(
    const PlanetDefinition& planet,
    const CelestialSystem* celestialSystem,
    std::uint32_t primaryCelestialBodyId)
    : planet_(&planet),
      celestialSystem_(celestialSystem),
      primaryCelestialBodyId_(primaryCelestialBodyId) {
    const glm::dvec3 startDirection = glm::normalize(glm::dvec3{0.72, 0.52, 0.46});
    double surface = planetSurfaceRadius(planet, startDirection);
    glm::dvec3 center{};
    if (celestialSystem_ != nullptr && primaryCelestialBodyId_ != 0U) {
        if (const auto* primary = celestialSystem_->body(primaryCelestialBodyId_)) {
            center = primary->position;
            surface = planetSurfaceRadius(planet, bodyLocalDirection(*primary, startDirection));
        }
    }
    position_ = center + startDirection * (surface + eyeHeight_);
}

const CelestialBody* PlanetCamera::referenceBody(const glm::dvec3& position) const noexcept {
    if (celestialSystem_ == nullptr) return nullptr;
    const CelestialBody* dominant = celestialSystem_->dominantBodyAt(position);
    if (dominant != nullptr && dominant->type != CelestialBodyType::Star) return dominant;

    const CelestialBody* closest = nullptr;
    double closestSurface = std::numeric_limits<double>::infinity();
    for (const auto& bodyValue : celestialSystem_->bodies()) {
        if (bodyValue.type == CelestialBodyType::Star) continue;
        const double surfaceDistance = std::abs(glm::length(position - bodyValue.position) - bodyValue.radiusMeters);
        if (surfaceDistance < closestSurface) {
            closestSurface = surfaceDistance;
            closest = &bodyValue;
        }
    }
    return closest;
}

double PlanetCamera::minimumEyeRadius(
    const CelestialBody& bodyValue,
    const glm::dvec3& direction) const noexcept {
    if (bodyValue.id == primaryCelestialBodyId_ && planet_ != nullptr) {
        return planetSurfaceRadius(*planet_, bodyLocalDirection(bodyValue, direction)) + eyeHeight_;
    }
    return bodyValue.radiusMeters + eyeHeight_;
}

glm::dvec3 PlanetCamera::up() const {
    if (const auto* bodyValue = referenceBody(position_)) {
        return safeNormalize(position_ - bodyValue->position);
    }
    return safeNormalize(position_);
}

double PlanetCamera::altitude() const {
    if (const auto* bodyValue = referenceBody(position_)) {
        const glm::dvec3 offset = position_ - bodyValue->position;
        const glm::dvec3 direction = safeNormalize(offset);
        const double surfaceRadius = bodyValue->id == primaryCelestialBodyId_ && planet_ != nullptr
            ? planetSurfaceRadius(*planet_, bodyLocalDirection(*bodyValue, direction))
            : bodyValue->radiusMeters;
        return glm::length(offset) - surfaceRadius;
    }
    const glm::dvec3 direction = up();
    return glm::length(position_) - planetSurfaceRadius(*planet_, direction);
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
    heading_ += input.mouseDx * mouseSensitivity;
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

    glm::dvec3 candidate = position_;
    candidate += (tangentForward * input.forward + tangentRight * input.right) * tangentSpeed * dt;

    grounded_ = false;
    if (celestialSystem_ != nullptr) {
        // The camera remains intentionally lightweight, but radial motion is genuinely
        // gravity-driven. Space/Ctrl act as local thrusters instead of teleporting vertically.
        velocity_ += celestialSystem_->gravityAccelerationAt(position_) * dt;
        const double verticalAcceleration = input.sprint ? 70.0 : 28.0;
        velocity_ += localUp * input.vertical * verticalAcceleration * dt;

        const double speed = glm::length(velocity_);
        if (speed > 220.0) velocity_ *= 220.0 / speed;
        candidate += velocity_ * dt;

        // Small celestial-body counts make an O(N) surface test far cheaper than maintaining a
        // second broadphase. Primary terrain is evaluated in body-local coordinates so mountains
        // rotate with the planet instead of remaining frozen in inertial space.
        for (const auto& bodyValue : celestialSystem_->bodies()) {
            if (bodyValue.type == CelestialBodyType::Star) continue;
            glm::dvec3 offset = candidate - bodyValue.position;
            double distance = glm::length(offset);
            if (distance <= 1.0e-9) {
                offset = {0.0, 1.0, 0.0};
                distance = 1.0;
            }
            const glm::dvec3 direction = safeNormalize(offset);
            const double minimumRadius = minimumEyeRadius(bodyValue, direction);
            if (distance >= minimumRadius) continue;

            candidate = bodyValue.position + direction * minimumRadius;
            const glm::dvec3 surfaceVelocity = celestialSurfaceVelocity(bodyValue, candidate);
            glm::dvec3 relativeVelocity = velocity_ - surfaceVelocity;
            const double inwardSpeed = glm::dot(relativeVelocity, direction);
            if (inwardSpeed < 0.0) relativeVelocity -= direction * inwardSpeed;

            // Ground friction makes a resting camera co-rotate/co-orbit with the surface while
            // preserving responsive direct tangent movement. This is intentionally cheaper than a
            // full character solver and will later be replaced by the physical capsule controller.
            const glm::dvec3 relativeNormal = direction * glm::dot(relativeVelocity, direction);
            glm::dvec3 relativeTangent = relativeVelocity - relativeNormal;
            relativeTangent *= std::exp(-12.0 * dt);
            velocity_ = surfaceVelocity + relativeNormal + relativeTangent;
            grounded_ = true;
        }
    } else {
        const double verticalSpeed = (input.sprint ? 70.0 : 28.0) * std::min(altitudeScale, 20.0);
        candidate += localUp * input.vertical * verticalSpeed * dt;
        glm::dvec3 direction = glm::normalize(candidate);
        const double minimumRadius = planetSurfaceRadius(*planet_, direction) + eyeHeight_;
        double radius = glm::length(candidate);
        radius = std::max(radius, minimumRadius);
        candidate = direction * radius;
    }

    position_ = candidate;
}

glm::mat4 PlanetCamera::viewProjection(float aspectRatio) const {
    aspectRatio = std::max(aspectRatio, 0.1F);
    const glm::dvec3 look = forwardDirection();
    const glm::dvec3 localUp = up();

    // Camera-relative rendering: GPU sees the world translated by -camera position,
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
