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
    // Free space is no longer secretly tied to Aster. A stable inertial up keeps mouse yaw/pitch
    // predictable while forward thrust is fully 3D and can point at any other planet.
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

    const CelestialBody* initialReference = referenceBody(position_);
    const double currentAltitude = initialReference != nullptr
        ? surfaceAltitudeFor(*initialReference, planet_, primaryCelestialBodyId_, position_)
        : std::numeric_limits<double>::infinity();
    const double flightTransitionAltitude = initialReference != nullptr
        ? std::clamp(
            10.0 + 0.15 * std::max(0.0, initialReference->atmosphere.heightMeters),
            18.0,
            42.0)
        : 0.0;

    if (grounded_) flightMode_ = false;
    if (initialReference == nullptr || currentAltitude > flightTransitionAltitude) flightMode_ = true;

    const glm::dvec3 localUp = up();
    const glm::dvec3 forward = forwardDirection();
    glm::dvec3 right = glm::cross(forward, localUp);
    if (glm::dot(right, right) < 1.0e-10) right = safeEast(localUp);
    else right = glm::normalize(right);

    grounded_ = false;
    glm::dvec3 candidate = position_;

    if (celestialSystem_ != nullptr) {
        velocity_ += celestialSystem_->gameplayGravityAccelerationAt(position_) * dt;

        if (flightMode_) {
            // Interplanetary mode is true inertial flight. Input changes velocity in camera-space;
            // it never teleports along Aster's tangent plane. Aim at Cinder and hold W/Shift to
            // accelerate toward it, then turn around and brake exactly as the velocity vector says.
            glm::dvec3 thrustDirection = forward * input.forward + right * input.right + localUp * input.vertical;
            const double thrustLength = glm::length(thrustDirection);
            if (thrustLength > 1.0) thrustDirection /= thrustLength;
            const double thrustAcceleration = input.sprint ? 180.0 : 62.0;
            velocity_ += thrustDirection * thrustAcceleration * dt;

            const auto environment = celestialSystem_->sampleEnvironment(position_);
            if (environment.densityKgPerM3 > 1.0e-5) {
                const glm::dvec3 relativeAir = velocity_ - environment.windVelocity;
                const double airSpeed = glm::length(relativeAir);
                if (airSpeed > 1.0e-5) {
                    // Cheap player/ship drag approximation: physically directional and density/
                    // speed dependent, but intentionally avoids modeling a detailed hull here.
                    const double dragAcceleration = std::min(
                        90.0,
                        0.012 * environment.densityKgPerM3 * airSpeed * airSpeed);
                    velocity_ -= (relativeAir / airSpeed) * dragAcceleration * dt;
                }
            }

            const double speed = glm::length(velocity_);
            constexpr double maxFlightSpeed = 900.0;
            if (speed > maxFlightSpeed) velocity_ *= maxFlightSpeed / speed;
            candidate += velocity_ * dt;
        } else {
            // Near a planetary surface, keep responsive on-foot tangent movement while radial
            // motion remains gravity/thrust driven. Once clear of the near-surface zone the same
            // velocity is retained and the controller transitions to inertial flight.
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
            const double speed = glm::length(velocity_);
            if (speed > 260.0) velocity_ *= 260.0 / speed;
            candidate += velocity_ * dt;
        }

        // Every non-star body is a real collision volume. Landing transfers the body's orbital
        // and rotational surface velocity to the player, instead of pinning the player to a
        // fictional world origin.
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

            const glm::dvec3 relativeNormal = direction * glm::dot(relativeVelocity, direction);
            glm::dvec3 relativeTangent = relativeVelocity - relativeNormal;
            relativeTangent *= std::exp(-12.0 * dt);
            velocity_ = surfaceVelocity + relativeNormal + relativeTangent;
            grounded_ = true;
            flightMode_ = false;
        }
    } else {
        const glm::dvec3 east = safeEast(localUp);
        const glm::dvec3 north = safeNormalize(glm::cross(localUp, east), {0.0, 0.0, 1.0});
        const glm::dvec3 tangentForward = safeNormalize(std::cos(heading_) * north + std::sin(heading_) * east, north);
        const glm::dvec3 tangentRight = safeNormalize(glm::cross(tangentForward, localUp), east);
        const double tangentSpeed = input.sprint ? 34.0 : 12.0;
        candidate += (tangentForward * input.forward + tangentRight * input.right) * tangentSpeed * dt;
        const double verticalSpeed = (input.sprint ? 70.0 : 28.0) * dt;
        candidate += localUp * input.vertical * verticalSpeed;
        glm::dvec3 direction = safeNormalize(candidate);
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

    // Camera-relative rendering: authoritative celestial/player coordinates remain double
    // precision in one inertial world, while the GPU sees positions translated by -camera.
    // The universe is not rotated around the player; only the render origin is rebased.
    const glm::vec3 eye{0.0F};
    const glm::vec3 target = glm::vec3(look);
    const glm::vec3 upVector = glm::vec3(localUp);
    const glm::mat4 view = glm::lookAtRH(eye, target, upVector);

    glm::mat4 projection = glm::perspectiveRH_ZO(glm::radians(68.0F), aspectRatio, 0.05F, 20000.0F);
    projection[1][1] *= -1.0F;
    return projection * view;
}

} // namespace vf
