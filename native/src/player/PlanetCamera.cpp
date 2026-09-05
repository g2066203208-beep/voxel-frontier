#include "vf/player/PlanetCamera.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

#include <glm/ext/matrix_clip_space.hpp>
#include <glm/ext/matrix_transform.hpp>
#include <glm/geometric.hpp>
#include <glm/gtc/quaternion.hpp>

namespace vf {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-12) return fallback;
    return value / std::sqrt(lengthSquared);
}

// This is only an initialization/degenerate fallback. Runtime surface heading is never rebuilt
// from this global reference; it is parallel-transported from the previous surface normal.
[[nodiscard]] glm::dvec3 stablePerpendicular(const glm::dvec3& directionInput) noexcept {
    const glm::dvec3 direction = safeNormalize(directionInput);
    const glm::dvec3 absolute = glm::abs(direction);
    glm::dvec3 reference{1.0, 0.0, 0.0};
    if (absolute.y <= absolute.x && absolute.y <= absolute.z) reference = {0.0, 1.0, 0.0};
    else if (absolute.z <= absolute.x && absolute.z <= absolute.y) reference = {0.0, 0.0, 1.0};
    return safeNormalize(glm::cross(reference, direction), {1.0, 0.0, 0.0});
}

[[nodiscard]] glm::dquat shortestArcRotation(
    const glm::dvec3& fromInput,
    const glm::dvec3& toInput) noexcept {
    const glm::dvec3 from = safeNormalize(fromInput);
    const glm::dvec3 to = safeNormalize(toInput, from);
    const double cosine = std::clamp(glm::dot(from, to), -1.0, 1.0);
    if (cosine > 1.0 - 1.0e-12) return {1.0, 0.0, 0.0, 0.0};
    if (cosine < -1.0 + 1.0e-10) {
        return glm::normalize(glm::angleAxis(kPi, stablePerpendicular(from)));
    }
    const glm::dvec3 axis = glm::cross(from, to);
    return glm::normalize(glm::dquat{1.0 + cosine, axis.x, axis.y, axis.z});
}

[[nodiscard]] double smooth01(double value) noexcept {
    const double t = std::clamp(value, 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

} // namespace

PlanetCamera::PlanetCamera(
    const PlanetDefinition& planet,
    const CelestialSystem* celestialSystem,
    std::uint32_t primaryCelestialBodyId,
    const glm::dvec3& startDirectionInput)
    : planet_(&planet),
      celestialSystem_(celestialSystem),
      primaryCelestialBodyId_(primaryCelestialBodyId) {
    const glm::dvec3 startDirection = safeNormalize(startDirectionInput, {0.72, 0.52, 0.46});
    if (celestialSystem_ != nullptr && primaryCelestialBodyId_ != 0U) {
        if (const auto* primary = celestialSystem_->body(primaryCelestialBodyId_)) {
            physicsFrameBodyId_ = primary->id;
            physicsFrame_.setBodyId(primary->id);
            inPhysicsFrame_ = true;
            const double surface = planetSurfaceRadius(planet, startDirection);
            localPosition_ = startDirection * (surface + eyeHeight_);
            localVelocity_ = {};
            grounded_ = true;
            syncWorldStateFromLocal(*primary);
            initializeViewAttitude(primary->orientation * startDirection);
            return;
        }
    }
    const double surface = planetSurfaceRadius(planet, startDirection);
    position_ = startDirection * (surface + eyeHeight_);
    velocity_ = {};
    grounded_ = true;
    initializeViewAttitude(startDirection);
}

void PlanetCamera::setViewDirection(
    const glm::dvec3& forwardInput,
    const glm::dvec3& upHintInput) noexcept {
    viewForward_ = safeNormalize(forwardInput, viewForward_);
    const glm::dvec3 upHint = safeNormalize(upHintInput, currentSurfaceUpWorld());
    glm::dvec3 right = glm::cross(viewForward_, upHint);
    if (glm::dot(right, right) <= 1.0e-12) right = stablePerpendicular(viewForward_);
    right = safeNormalize(right, stablePerpendicular(viewForward_));
    viewUp_ = safeNormalize(glm::cross(right, viewForward_), upHint);
    transportedSurfaceUp_ = upHint;
    viewAttitudeValid_ = true;
    surfaceTransportValid_ = true;
}

const CelestialBody* PlanetCamera::physicsFrameBody() const noexcept {
    if (!inPhysicsFrame_ || celestialSystem_ == nullptr || physicsFrameBodyId_ == 0U) return nullptr;
    return celestialSystem_->body(physicsFrameBodyId_);
}

double PlanetCamera::localMinimumEyeRadius(const CelestialBody& body, const glm::dvec3& localDirection) const noexcept {
    if (body.id == primaryCelestialBodyId_ && planet_ != nullptr)
        return planetSurfaceRadius(*planet_, safeNormalize(localDirection)) + eyeHeight_;
    return body.radiusMeters + eyeHeight_;
}

glm::dvec3 PlanetCamera::currentSurfaceUpWorld() const noexcept {
    if (const CelestialBody* body = physicsFrameBody()) {
        return safeNormalize(body->orientation * safeNormalize(localPosition_), viewUp_);
    }
    if (celestialSystem_ == nullptr) return safeNormalize(position_, viewUp_);
    return safeNormalize(viewUp_);
}

double PlanetCamera::surfaceAttitudeInfluence() const noexcept {
    if (grounded_) return 1.0;

    double localAltitude = 0.0;
    double atmosphereHeight = planet_ != nullptr ? planet_->atmosphereHeight : 0.0;
    if (const CelestialBody* body = physicsFrameBody()) {
        const double distance = glm::length(localPosition_);
        if (distance <= 1.0e-9) return 1.0;
        const glm::dvec3 direction = localPosition_ / distance;
        const double surface = body->id == primaryCelestialBodyId_ && planet_ != nullptr
            ? planetSurfaceRadius(*planet_, direction)
            : body->radiusMeters;
        localAltitude = std::max(0.0, distance - surface);
        if (body->atmosphere.enabled && body->atmosphere.heightMeters > 0.0)
            atmosphereHeight = body->atmosphere.heightMeters;
    } else if (celestialSystem_ == nullptr) {
        localAltitude = std::max(0.0, altitude());
    } else {
        return 0.0;
    }

    // Camera horizon behavior is based on altitude, never on a reference-frame ownership edge.
    // The lower atmosphere remains horizon-relative, then the constraint fades smoothly to free
    // inertial attitude over several atmosphere heights.
    const double fadeStart = std::max(250.0, atmosphereHeight * 0.20);
    const double fadeEnd = std::max(fadeStart + 750.0, atmosphereHeight * 3.0);
    if (localAltitude <= fadeStart) return 1.0;
    if (localAltitude >= fadeEnd) return 0.0;
    return 1.0 - smooth01((localAltitude - fadeStart) / (fadeEnd - fadeStart));
}

void PlanetCamera::initializeViewAttitude(const glm::dvec3& surfaceUpWorldInput) noexcept {
    const glm::dvec3 surfaceUp = safeNormalize(surfaceUpWorldInput);
    const glm::dvec3 east = stablePerpendicular(surfaceUp);
    const glm::dvec3 north = safeNormalize(glm::cross(surfaceUp, east), {0.0, 0.0, 1.0});
    constexpr double initialPitch = -0.18;
    viewForward_ = safeNormalize(
        std::cos(initialPitch) * north + std::sin(initialPitch) * surfaceUp,
        north);

    // Store a real camera-up vector rather than the raw gravity-up hint. glm::lookAt would project
    // a non-orthogonal up internally; keeping the state orthonormal here avoids a hidden one-frame
    // correction when the camera later starts blending back toward a planetary horizon.
    const glm::dvec3 projectedUp = surfaceUp - viewForward_ * glm::dot(surfaceUp, viewForward_);
    viewUp_ = safeNormalize(projectedUp, surfaceUp);
    transportedSurfaceUp_ = surfaceUp;
    viewAttitudeValid_ = true;
    surfaceTransportValid_ = true;
}

void PlanetCamera::transportViewAttitude(
    const glm::dvec3& surfaceUpWorldInput,
    double influence) noexcept {
    const glm::dvec3 surfaceUp = safeNormalize(surfaceUpWorldInput, transportedSurfaceUp_);
    if (!viewAttitudeValid_) initializeViewAttitude(surfaceUp);
    if (!surfaceTransportValid_) {
        transportedSurfaceUp_ = surfaceUp;
        surfaceTransportValid_ = true;
        return;
    }

    influence = std::clamp(influence, 0.0, 1.0);
    if (influence > 1.0e-8) {
        const glm::dquat fullRotation = shortestArcRotation(transportedSurfaceUp_, surfaceUp);
        const glm::dquat applied = glm::normalize(glm::slerp(
            glm::dquat{1.0, 0.0, 0.0, 0.0}, fullRotation, influence));
        viewForward_ = safeNormalize(applied * viewForward_, viewForward_);
        viewUp_ = safeNormalize(applied * viewUp_, viewUp_);
    }
    transportedSurfaceUp_ = surfaceUp;
}

void PlanetCamera::alignViewUpToSurface(
    const glm::dvec3& surfaceUpWorldInput,
    double influence,
    double dt) noexcept {
    influence = std::clamp(influence, 0.0, 1.0);
    if (!viewAttitudeValid_ || influence <= 1.0e-8 || dt <= 0.0) return;

    const glm::dvec3 forward = safeNormalize(viewForward_, {0.0, 0.0, -1.0});
    const glm::dvec3 surfaceUp = safeNormalize(surfaceUpWorldInput, viewUp_);
    const glm::dvec3 desiredProjected = surfaceUp - forward * glm::dot(surfaceUp, forward);
    if (glm::dot(desiredProjected, desiredProjected) <= 1.0e-10) return;
    const glm::dvec3 desiredUp = glm::normalize(desiredProjected);
    const glm::dvec3 currentUp = safeNormalize(viewUp_, desiredUp);

    // Both currentUp and desiredUp are perpendicular to forward, so this is a pure, gradual roll
    // correction around the sight axis. Forward itself never jumps during atmospheric alignment.
    const glm::dquat correction = shortestArcRotation(currentUp, desiredUp);
    const double rate = (grounded_ ? 14.0 : 5.0) * influence;
    const double alpha = 1.0 - std::exp(-rate * dt);
    const glm::dquat applied = glm::normalize(glm::slerp(
        glm::dquat{1.0, 0.0, 0.0, 0.0}, correction, alpha));
    viewUp_ = safeNormalize(applied * currentUp, desiredUp);
}

void PlanetCamera::rotateSurfaceAttitude(
    double mouseDx,
    double mouseDy,
    const glm::dvec3& surfaceUpWorldInput) noexcept {
    if (!viewAttitudeValid_) return;
    constexpr double mouseSensitivity = 0.0022;
    const glm::dvec3 surfaceUp = safeNormalize(surfaceUpWorldInput, viewUp_);

    const double yaw = -mouseDx * mouseSensitivity;
    const glm::dquat yawRotation = glm::angleAxis(yaw, surfaceUp);
    viewForward_ = safeNormalize(yawRotation * viewForward_, viewForward_);
    viewUp_ = safeNormalize(yawRotation * viewUp_, viewUp_);

    glm::dvec3 right = glm::cross(viewForward_, surfaceUp);
    if (glm::dot(right, right) < 1.0e-12) right = stablePerpendicular(surfaceUp);
    else right = glm::normalize(right);

    const double currentPitch = std::asin(std::clamp(glm::dot(viewForward_, surfaceUp), -1.0, 1.0));
    const double targetPitch = std::clamp(currentPitch - mouseDy * mouseSensitivity, -1.52, 1.52);
    const glm::dquat pitchRotation = glm::angleAxis(targetPitch - currentPitch, right);
    viewForward_ = safeNormalize(pitchRotation * viewForward_, viewForward_);
    viewUp_ = safeNormalize(pitchRotation * viewUp_, viewUp_);
}

void PlanetCamera::rotateFreeAttitude(double mouseDx, double mouseDy) noexcept {
    if (!viewAttitudeValid_) return;
    constexpr double mouseSensitivity = 0.0022;
    const double yaw = -mouseDx * mouseSensitivity;
    const glm::dquat yawRotation = glm::angleAxis(yaw, safeNormalize(viewUp_));
    viewForward_ = safeNormalize(yawRotation * viewForward_, viewForward_);

    glm::dvec3 right = glm::cross(viewForward_, viewUp_);
    if (glm::dot(right, right) < 1.0e-12) right = stablePerpendicular(viewUp_);
    else right = glm::normalize(right);
    const double pitchDelta = -mouseDy * mouseSensitivity;
    const glm::dquat pitchRotation = glm::angleAxis(pitchDelta, right);
    const glm::dvec3 candidateForward = safeNormalize(pitchRotation * viewForward_, viewForward_);
    const glm::dvec3 candidateUp = safeNormalize(pitchRotation * viewUp_, viewUp_);
    if (glm::dot(glm::cross(candidateForward, candidateUp), glm::cross(candidateForward, candidateUp)) > 1.0e-10) {
        viewForward_ = candidateForward;
        viewUp_ = candidateUp;
    }
}

void PlanetCamera::enterPhysicsFrame(const CelestialBody& body) noexcept {
    physicsFrameBodyId_ = body.id;
    physicsFrame_.setBodyId(body.id);
    localPosition_ = physicsFrame_.toLocalPosition(body, position_);
    localVelocity_ = physicsFrame_.toLocalVelocity(body, position_, velocity_);
    inPhysicsFrame_ = true;
    grounded_ = false;

    // Reference-frame ownership is only a precision/physics concern. It may establish the next
    // surface-transport baseline, but it never changes the current camera attitude.
    transportedSurfaceUp_ = safeNormalize(body.orientation * safeNormalize(localPosition_), viewUp_);
    surfaceTransportValid_ = true;
}

void PlanetCamera::leavePhysicsFrame() noexcept {
    inPhysicsFrame_ = false;
    physicsFrameBodyId_ = 0U;
    physicsFrame_.setBodyId(0U);
    grounded_ = false;
    surfaceTransportValid_ = false;
}

void PlanetCamera::syncWorldStateFromLocal(const CelestialBody& body) noexcept {
    position_ = physicsFrame_.toWorldPosition(body, localPosition_);
    velocity_ = physicsFrame_.toWorldVelocity(body, localPosition_, localVelocity_);
}

glm::dvec3 PlanetCamera::up() const {
    if (viewAttitudeValid_) return safeNormalize(viewUp_);
    if (const auto* body = physicsFrameBody()) {
        const glm::dvec3 radial = safeNormalize(body->orientation * safeNormalize(localPosition_));
        const glm::dvec3 forward = forwardDirection();
        return safeNormalize(radial - forward * glm::dot(radial, forward), radial);
    }
    if (celestialSystem_ == nullptr) return stablePerpendicular(forwardDirection());
    return {0.0, 1.0, 0.0};
}

double PlanetCamera::altitude() const {
    if (const auto* body = physicsFrameBody()) {
        const double distance = glm::length(localPosition_);
        if (distance <= 1.0e-9) return -body->radiusMeters;
        const glm::dvec3 direction = localPosition_ / distance;
        const double surface = body->id == primaryCelestialBodyId_ && planet_ != nullptr
            ? planetSurfaceRadius(*planet_, direction) : body->radiusMeters;
        return distance - surface;
    }
    if (celestialSystem_ != nullptr) {
        double closest = std::numeric_limits<double>::infinity();
        for (const auto& body : celestialSystem_->bodies()) {
            if (body.type == CelestialBodyType::Star) continue;
            closest = std::min(closest, celestialSystem_->signedSurfaceDistance(body, position_));
        }
        return closest;
    }
    const glm::dvec3 direction = safeNormalize(position_);
    return glm::length(position_) - planetSurfaceRadius(*planet_, direction);
}

glm::dvec3 PlanetCamera::forwardDirection() const {
    if (viewAttitudeValid_) return safeNormalize(viewForward_, {0.0, 0.0, -1.0});
    return {0.0, 0.0, -1.0};
}

void PlanetCamera::update(const PlanetMovementInput& input, double dt) {
    if (dt <= 0.0) return;
    dt = std::min(dt, 0.05);

    if (const auto* body = physicsFrameBody()) syncWorldStateFromLocal(*body);
    if (celestialSystem_ != nullptr) {
        const CelestialBody* desiredFrame = celestialSystem_->physicsReferenceBodyAt(position_);
        if (inPhysicsFrame_ && (desiredFrame == nullptr || desiredFrame->id != physicsFrameBodyId_)) {
            leavePhysicsFrame();
            if (desiredFrame != nullptr) enterPhysicsFrame(*desiredFrame);
        } else if (!inPhysicsFrame_ && desiredFrame != nullptr) {
            enterPhysicsFrame(*desiredFrame);
        }
    }

    if (input.toggleFlight) {
        flightMode_ = !flightMode_;
        grounded_ = false;
        if (flightMode_) {
            if (inPhysicsFrame_) localVelocity_ = {};
            else velocity_ = {};
        }
    }

    if (physicsFrameBody() != nullptr) {
        const glm::dvec3 surfaceUpWorld = currentSurfaceUpWorld();
        const double influence = surfaceAttitudeInfluence();
        transportViewAttitude(surfaceUpWorld, influence);
        if (!flightMode_ || influence >= 0.55)
            rotateSurfaceAttitude(input.mouseDx, input.mouseDy, surfaceUpWorld);
        else
            rotateFreeAttitude(input.mouseDx, input.mouseDy);
        alignViewUpToSurface(surfaceUpWorld, influence, dt);
    } else if (celestialSystem_ == nullptr) {
        const glm::dvec3 surfaceUpWorld = safeNormalize(position_, viewUp_);
        const double influence = surfaceAttitudeInfluence();
        transportViewAttitude(surfaceUpWorld, influence);
        if (!flightMode_ || influence >= 0.55)
            rotateSurfaceAttitude(input.mouseDx, input.mouseDy, surfaceUpWorld);
        else
            rotateFreeAttitude(input.mouseDx, input.mouseDy);
        alignViewUpToSurface(surfaceUpWorld, influence, dt);
    } else {
        rotateFreeAttitude(input.mouseDx, input.mouseDy);
    }

    if (std::abs(input.flightSpeedSteps) > 1.0e-9) {
        creativeFlightSpeedMps_ = std::clamp(
            creativeFlightSpeedMps_ * std::pow(2.0, input.flightSpeedSteps * 0.5),
            1.0,
            2000000.0);
    }

    if (const auto* body = physicsFrameBody()) {
        const glm::dvec3 localUp = safeNormalize(localPosition_);
        const glm::dquat inverseOrientation = glm::conjugate(glm::normalize(body->orientation));
        const glm::dvec3 localForward = safeNormalize(inverseOrientation * viewForward_, {0.0, 0.0, -1.0});
        glm::dvec3 tangentForward = localForward - localUp * glm::dot(localForward, localUp);
        tangentForward = safeNormalize(tangentForward, stablePerpendicular(localUp));
        const glm::dvec3 localRight = safeNormalize(glm::cross(tangentForward, localUp), stablePerpendicular(localUp));

        if (flightMode_) {
            glm::dvec3 move = localForward * input.forward + localRight * input.right + localUp * input.vertical;
            const double moveLength = glm::length(move);
            if (moveLength > 1.0) move /= moveLength;
            const double targetSpeed = creativeFlightSpeedMps_ * (input.sprint ? 4.0 : 1.0);
            const glm::dvec3 desired = moveLength > 1.0e-8 ? move * targetSpeed : glm::dvec3{};
            localVelocity_ += (desired - localVelocity_) * (1.0 - std::exp(-7.0 * dt));
            localPosition_ += localVelocity_ * dt;
            const glm::dvec3 direction = safeNormalize(localPosition_, localUp);
            const double minimumRadius = localMinimumEyeRadius(*body, direction);
            const double radius = glm::length(localPosition_);
            if (radius <= minimumRadius) {
                localPosition_ = direction * minimumRadius;
                const double radialSpeed = glm::dot(localVelocity_, direction);
                if (radialSpeed < 0.0) localVelocity_ -= direction * radialSpeed;
            }
            grounded_ = false;
        } else {
            const bool wasGrounded = grounded_;
            const bool jumping = wasGrounded && input.vertical > 0.5;
            if (wasGrounded && !jumping) {
                glm::dvec3 desiredTangent = tangentForward * input.forward + localRight * input.right;
                const double desiredLength = glm::length(desiredTangent);
                if (desiredLength > 1.0) desiredTangent /= desiredLength;
                desiredTangent *= input.sprint ? 26.0 : 9.0;
                glm::dvec3 tangent = localVelocity_ - localUp * glm::dot(localVelocity_, localUp);
                const double response = 1.0 - std::exp(-(desiredLength > 1.0e-8 ? 18.0 : 14.0) * dt);
                tangent += (desiredTangent - tangent) * response;
                localVelocity_ = tangent;
                localPosition_ += tangent * dt;
                const glm::dvec3 newDirection = safeNormalize(localPosition_, localUp);
                const double minimumRadius = localMinimumEyeRadius(*body, newDirection);
                localPosition_ = newDirection * minimumRadius;
                localVelocity_ -= newDirection * glm::dot(localVelocity_, newDirection);
                grounded_ = true;
            } else {
                if (jumping) {
                    localVelocity_ += localUp * (input.sprint ? 28.0 : 14.0);
                    grounded_ = false;
                }
                if (celestialSystem_ != nullptr)
                    localVelocity_ += physicsFrame_.gravityAcceleration(
                        *celestialSystem_, *body, localPosition_, localVelocity_) * dt;
                localPosition_ += localVelocity_ * dt;
                const glm::dvec3 direction = safeNormalize(localPosition_, localUp);
                const double minimumRadius = localMinimumEyeRadius(*body, direction);
                const double radius = glm::length(localPosition_);
                grounded_ = false;
                if (radius <= minimumRadius) {
                    localPosition_ = direction * minimumRadius;
                    const double radialSpeed = glm::dot(localVelocity_, direction);
                    if (radialSpeed < 0.0) localVelocity_ -= direction * radialSpeed;
                    grounded_ = true;
                }
            }
        }

        const glm::dvec3 newSurfaceUpWorld = safeNormalize(
            body->orientation * safeNormalize(localPosition_, localUp),
            currentSurfaceUpWorld());
        const double newInfluence = surfaceAttitudeInfluence();
        transportViewAttitude(newSurfaceUpWorld, newInfluence);
        alignViewUpToSurface(newSurfaceUpWorld, newInfluence, dt);

        syncWorldStateFromLocal(*body);
        if (celestialSystem_ != nullptr) {
            const CelestialBody* owner = celestialSystem_->physicsReferenceBodyAt(position_);
            if (owner == nullptr || owner->id != physicsFrameBodyId_) leavePhysicsFrame();
        }
        return;
    }

    if (celestialSystem_ != nullptr) {
        const glm::dvec3 cameraUp = up();
        const glm::dvec3 forward = forwardDirection();
        glm::dvec3 right = glm::cross(forward, cameraUp);
        if (glm::dot(right, right) < 1.0e-10) right = stablePerpendicular(cameraUp);
        else right = glm::normalize(right);
        if (flightMode_) {
            glm::dvec3 move = forward * input.forward + right * input.right + cameraUp * input.vertical;
            const double moveLength = glm::length(move);
            if (moveLength > 1.0) move /= moveLength;
            const double targetSpeed = creativeFlightSpeedMps_ * (input.sprint ? 4.0 : 1.0);
            const glm::dvec3 desired = moveLength > 1.0e-8 ? move * targetSpeed : glm::dvec3{};
            velocity_ += (desired - velocity_) * (1.0 - std::exp(-7.0 * dt));
        } else {
            velocity_ += celestialSystem_->gravityAccelerationAt(position_) * dt;
        }
        position_ += velocity_ * dt;
        if (const auto* newFrame = celestialSystem_->physicsReferenceBodyAt(position_)) enterPhysicsFrame(*newFrame);
        return;
    }

    const glm::dvec3 localUp = safeNormalize(position_);
    const glm::dvec3 forward = forwardDirection();
    glm::dvec3 tangentForward = forward - localUp * glm::dot(forward, localUp);
    tangentForward = safeNormalize(tangentForward, stablePerpendicular(localUp));
    const glm::dvec3 right = safeNormalize(glm::cross(tangentForward, localUp), stablePerpendicular(localUp));
    if (flightMode_) {
        glm::dvec3 move = forward * input.forward + right * input.right + localUp * input.vertical;
        const double moveLength = glm::length(move);
        if (moveLength > 1.0) move /= moveLength;
        const double speed = creativeFlightSpeedMps_ * (input.sprint ? 4.0 : 1.0);
        velocity_ = moveLength > 1.0e-8 ? move * speed : glm::dvec3{};
        position_ += velocity_ * dt;
        const glm::dvec3 direction = safeNormalize(position_);
        const double minimumRadius = planetSurfaceRadius(*planet_, direction) + eyeHeight_;
        if (glm::length(position_) < minimumRadius) position_ = direction * minimumRadius;
        grounded_ = false;
    } else {
        const double tangentSpeed = input.sprint ? 34.0 : 12.0;
        position_ += (tangentForward * input.forward + right * input.right) * tangentSpeed * dt;
        const glm::dvec3 direction = safeNormalize(position_);
        const double minimumRadius = planetSurfaceRadius(*planet_, direction) + eyeHeight_;
        position_ = direction * std::max(glm::length(position_), minimumRadius);
        velocity_ = {};
        grounded_ = true;
    }

    const glm::dvec3 newSurfaceUp = safeNormalize(position_, localUp);
    const double influence = surfaceAttitudeInfluence();
    transportViewAttitude(newSurfaceUp, influence);
    alignViewUpToSurface(newSurfaceUp, influence, dt);
}

glm::mat4 PlanetCamera::viewProjection(float aspectRatio) const {
    aspectRatio = std::max(aspectRatio, 0.1F);
    const glm::vec3 eye{0.0F};
    const glm::vec3 target = glm::vec3(forwardDirection());
    const glm::vec3 upVector = glm::vec3(up());
    const glm::mat4 view = glm::lookAtRH(eye, target, upVector);
    glm::mat4 projection = glm::perspectiveRH_ZO(glm::radians(68.0F), aspectRatio, 0.05F, 50000000.0F);
    projection[1][1] *= -1.0F;
    return projection * view;
}

} // namespace vf
