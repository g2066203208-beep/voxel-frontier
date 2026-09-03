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
    return safeNormalize(east, {1.0, 0.0, 0.0});
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

[[nodiscard]] double surfaceAltitudeFor(
    const CelestialBody& body,
    const PlanetDefinition* primaryTerrain,
    std::uint32_t primaryId,
    const glm::dvec3& position) noexcept {
    const glm::dvec3 offset = position - body.position;
    const double distance = glm::length(offset);
    if (distance <= 1.0e-9) return -body.radiusMeters;
    const glm::dvec3 direction = offset / distance;
    const double radius = body.id == primaryId && primaryTerrain != nullptr
        ? planetSurfaceRadius(*primaryTerrain, bodyLocalDirection(body, direction))
        : body.radiusMeters;
    return distance - radius;
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
            velocity_ = celestialSurfaceVelocity(*primary, center + startDirection * (surface + eyeHeight_));
        }
    }
    position_ = center + startDirection * (surface + eyeHeight_);
}

const CelestialBody* PlanetCamera::referenceBody(const glm::dvec3& position) const noexcept {
    if (celestialSystem_ == nullptr) return nullptr;
    return celestialSystem_->gameplayReferenceBodyAt(position);
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
    return {0.0, 1.0, 0.0};
}

double PlanetCamera::altitude() const {
    if (const auto* bodyValue = referenceBody(position_)) {
        return surfaceAltitudeFor(*bodyValue, planet_, primaryCelestialBodyId_, position_);
    }

    if (celestialSystem_ != nullptr) {
        double closest = std::numeric_limits<double>::infinity();
        for (const auto& bodyValue : celestialSystem_->bodies()) {
            if (bodyValue.type == CelestialBodyType::Star) continue;
            closest = std::min(closest, surfaceAltitudeFor(
                bodyValue, planet_, primaryCelestialBodyId_, position_));
        }
        return closest;
    }

    const glm::dvec3 direction = safeNormalize(position_);
    return glm::length(position_) - planetSurfaceRadius(*planet_, direction);
}

glm::dvec3 PlanetCamera::forwardDirection() const {
    const glm::dvec3 localUp = up();
    const glm::dvec3 east = safeEast(localUp);
    const glm::dvec3 north = safeNormalize(glm::cross(localUp, east), {0.0, 0.0, 1.0});
    const glm::dvec3 tangentForward = safeNormalize(
        std::cos(heading_) * north + std::sin(heading_) * east,
        north);
    return safeNormalize(std::cos(pitch_) * tangentForward + std::sin(pitch_) * localUp, tangentForward);
}

void PlanetCamera::update(const PlanetMovementInput& input, double dt) {
    if (dt <= 0.0) return;
    dt = std::min(dt, 0.05);

    constexpr double mouseSensitivity = 0.0022;
    heading_ += input.mouseDx * mouseSensitivity;
    pitch_ = std::clamp(pitch_ - input.mouseDy * mouseSensitivity, -1.52, 1.52);

    if (input.toggleFlight) {
        flightMode_ = !flightMode_;
        if (flightMode_) {
            if (const auto* bodyValue = referenceBody(position_)) {
                velocity_ = celestialSurfaceVelocity(*bodyValue, position_);
            } else {
                velocity_ = {};
            }
        }
    }

    const glm::dvec3 localUp = up();
    const glm::dvec3 forward = forwardDirection();
    glm::dvec3 right = glm::cross(forward, localUp);
    if (glm::dot(right, right) < 1.0e-10) right = safeEast(localUp);
    else right = glm::normalize(right);

    grounded_ = false;
    glm::dvec3 candidate = position_;

    if (celestialSystem_ != nullptr) {
        if (flightMode_) {
            // Minecraft-style creative travel flight for the player only. The world keeps its
            // real/gameplay gravity; creative flight simply bypasses it so testing another planet
            // never requires performing an orbital transfer with the debug camera.
            glm::dvec3 moveDirection = forward * input.forward + right * input.right + localUp * input.vertical;
            const double moveLength = glm::length(moveDirection);
            if (moveLength > 1.0) moveDirection /= moveLength;

            const double targetSpeed = input.sprint ? 1200.0 : 320.0;
            const glm::dvec3 desiredVelocity = moveLength > 1.0e-8 ? moveDirection * targetSpeed : glm::dvec3{};
            const double response = 1.0 - std::exp(-(moveLength > 1.0e-8 ? 8.0 : 5.0) * dt);
            velocity_ += (desiredVelocity - velocity_) * response;
            candidate += velocity_ * dt;
        } else {
            velocity_ += celestialSystem_->gameplayGravityAccelerationAt(position_) * dt;

            const glm::dvec3 east = safeEast(localUp);
            const glm::dvec3 north = safeNormalize(glm::cross(localUp, east), {0.0, 0.0, 1.0});
            const glm::dvec3 tangentForward = safeNormalize(
                std::cos(heading_) * north + std::sin(heading_) * east,
                north);
            const glm::dvec3 tangentRight = safeNormalize(glm::cross(tangentForward, localUp), east);
            const double walkSpeed = input.sprint ? 26.0 : 9.0;
            candidate += (tangentForward * input.forward + tangentRight * input.right) * walkSpeed * dt;

            const double verticalAcceleration = input.sprint ? 95.0 : 36.0;
            velocity_ += localUp * input.vertical * verticalAcceleration * dt;
            candidate += velocity_ * dt;
        }

        for (const auto& bodyValue : celestialSystem_->bodies()) {
            // Stars are physical celestial bodies too: the camera can approach their photosphere.
            // Radiation/thermal gameplay determines whether ordinary entities can survive there.
            glm::dvec3 offset = candidate - bodyValue.position;
            double distance = glm::length(offset);
            if (distance <= 1.0e-9) {
                offset = {0.0, 1.0, 0.0};
                distance = 1.0;
            }
            const glm::dvec3 direction = safeNormalize(offset);
            const double minimumRadius = bodyValue.type == CelestialBodyType::Star
                ? bodyValue.radiusMeters + eyeHeight_
                : minimumEyeRadius(bodyValue, direction);
            if (distance >= minimumRadius) continue;

            candidate = bodyValue.position + direction * minimumRadius;
            const glm::dvec3 surfaceVelocity = celestialSurfaceVelocity(bodyValue, candidate);
            glm::dvec3 relativeVelocity = velocity_ - surfaceVelocity;
            const double inwardSpeed = glm::dot(relativeVelocity, direction);
            if (inwardSpeed < 0.0) relativeVelocity -= direction * inwardSpeed;

            if (!flightMode_) {
                const glm::dvec3 relativeNormal = direction * glm::dot(relativeVelocity, direction);
                glm::dvec3 relativeTangent = relativeVelocity - relativeNormal;
                relativeTangent *= std::exp(-12.0 * dt);
                velocity_ = surfaceVelocity + relativeNormal + relativeTangent;
                grounded_ = bodyValue.type != CelestialBodyType::Star;
            } else {
                velocity_ = surfaceVelocity + relativeVelocity;
            }
        }
    } else {
        if (flightMode_) {
            glm::dvec3 moveDirection = forward * input.forward + right * input.right + localUp * input.vertical;
            const double moveLength = glm::length(moveDirection);
            if (moveLength > 1.0) moveDirection /= moveLength;
            const double targetSpeed = input.sprint ? 220.0 : 70.0;
            const glm::dvec3 desiredVelocity = moveLength > 1.0e-8 ? moveDirection * targetSpeed : glm::dvec3{};
            velocity_ += (desiredVelocity - velocity_) * (1.0 - std::exp(-8.0 * dt));
            candidate += velocity_ * dt;
        } else {
            const glm::dvec3 east = safeEast(localUp);
            const glm::dvec3 north = safeNormalize(glm::cross(localUp, east), {0.0, 0.0, 1.0});
            const glm::dvec3 tangentForward = safeNormalize(std::cos(heading_) * north + std::sin(heading_) * east, north);
            const glm::dvec3 tangentRight = safeNormalize(glm::cross(tangentForward, localUp), east);
            const double tangentSpeed = input.sprint ? 34.0 : 12.0;
            candidate += (tangentForward * input.forward + tangentRight * input.right) * tangentSpeed * dt;

            const double altitudeScale = 1.0 + std::max(0.0, altitude()) / 80.0;
            const double verticalSpeed = (input.sprint ? 70.0 : 28.0) * std::min(altitudeScale, 20.0);
            candidate += localUp * input.vertical * verticalSpeed * dt;

            glm::dvec3 direction = safeNormalize(candidate);
            const double minimumRadius = planetSurfaceRadius(*planet_, direction) + eyeHeight_;
            double radius = glm::length(candidate);
            radius = std::max(radius, minimumRadius);
            candidate = direction * radius;
        }
    }

    position_ = candidate;
}

glm::mat4 PlanetCamera::viewProjection(float aspectRatio) const {
    aspectRatio = std::max(aspectRatio, 0.1F);
    const glm::dvec3 look = forwardDirection();
    const glm::dvec3 localUp = up();

    const glm::vec3 eye{0.0F};
    const glm::vec3 target = glm::vec3(look);
    const glm::vec3 upVector = glm::vec3(localUp);
    const glm::mat4 view = glm::lookAtRH(eye, target, upVector);

    glm::mat4 projection = glm::perspectiveRH_ZO(glm::radians(68.0F), aspectRatio, 0.05F, 2000000.0F);
    projection[1][1] *= -1.0F;
    return projection * view;
}

} // namespace vf
