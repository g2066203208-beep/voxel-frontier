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

[[nodiscard]] glm::dvec3 safeEast(const glm::dvec3& up) noexcept {
    glm::dvec3 east = glm::cross(glm::dvec3{0.0, 1.0, 0.0}, up);
    if (glm::dot(east, east) < 1.0e-8) east = glm::cross(glm::dvec3{1.0, 0.0, 0.0}, up);
    return safeNormalize(east, {1.0, 0.0, 0.0});
}

} // namespace

PlanetCamera::PlanetCamera(
    const PlanetDefinition& planet,
    const CelestialSystem* celestialSystem,
    std::uint32_t primaryCelestialBodyId)
    : planet_(&planet),
      celestialSystem_(celestialSystem),
      primaryCelestialBodyId_(primaryCelestialBodyId) {
    const glm::dvec3 startDirection = safeNormalize({0.72, 0.52, 0.46});

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
            return;
        }
    }

    const double surface = planetSurfaceRadius(planet, startDirection);
    position_ = startDirection * (surface + eyeHeight_);
    velocity_ = {};
    grounded_ = true;
}

const CelestialBody* PlanetCamera::physicsFrameBody() const noexcept {
    if (!inPhysicsFrame_ || celestialSystem_ == nullptr || physicsFrameBodyId_ == 0U) return nullptr;
    return celestialSystem_->body(physicsFrameBodyId_);
}

double PlanetCamera::localMinimumEyeRadius(
    const CelestialBody& body,
    const glm::dvec3& localDirection) const noexcept {
    if (body.id == primaryCelestialBodyId_ && planet_ != nullptr) {
        return planetSurfaceRadius(*planet_, safeNormalize(localDirection)) + eyeHeight_;
    }
    return body.radiusMeters + eyeHeight_;
}

glm::dvec3 PlanetCamera::localForwardDirection(const glm::dvec3& localUp) const noexcept {
    const glm::dvec3 east = safeEast(localUp);
    const glm::dvec3 north = safeNormalize(glm::cross(localUp, east), {0.0, 0.0, 1.0});
    const glm::dvec3 tangentForward = safeNormalize(
        std::cos(heading_) * north + std::sin(heading_) * east,
        north);
    return safeNormalize(
        std::cos(pitch_) * tangentForward + std::sin(pitch_) * localUp,
        tangentForward);
}

void PlanetCamera::enterPhysicsFrame(const CelestialBody& body) noexcept {
    physicsFrameBodyId_ = body.id;
    physicsFrame_.setBodyId(body.id);
    localPosition_ = physicsFrame_.toLocalPosition(body, position_);
    localVelocity_ = physicsFrame_.toLocalVelocity(body, position_, velocity_);
    inPhysicsFrame_ = true;
    grounded_ = false;
}

void PlanetCamera::leavePhysicsFrame() noexcept {
    inPhysicsFrame_ = false;
    physicsFrameBodyId_ = 0U;
    physicsFrame_.setBodyId(0U);
    grounded_ = false;
}

void PlanetCamera::syncWorldStateFromLocal(const CelestialBody& body) noexcept {
    position_ = physicsFrame_.toWorldPosition(body, localPosition_);
    velocity_ = physicsFrame_.toWorldVelocity(body, localPosition_, localVelocity_);
}

glm::dvec3 PlanetCamera::up() const {
    if (const auto* body = physicsFrameBody()) {
        const glm::dvec3 localUp = safeNormalize(localPosition_);
        const double localGravity = celestialSystem_ != nullptr
            ? celestialSystem_->gravityMagnitudeFromBody(*body, position_)
            : 0.0;
        if (grounded_ || localGravity > 0.10 || celestialSystem_->insideAtmosphere(*body, position_)) {
            return safeNormalize(body->orientation * localUp);
        }
        // Deep zero-g can still remain inside a large coordinate/precision bubble, but it must no
        // longer behave like a spherical walking surface.
        return {0.0, 1.0, 0.0};
    }

    if (celestialSystem_ == nullptr) return safeNormalize(position_);
    return {0.0, 1.0, 0.0};
}

double PlanetCamera::altitude() const {
    if (const auto* body = physicsFrameBody()) {
        const double distance = glm::length(localPosition_);
        if (distance <= 1.0e-9) return -body->radiusMeters;
        const glm::dvec3 direction = localPosition_ / distance;
        const double surface = body->id == primaryCelestialBodyId_ && planet_ != nullptr
            ? planetSurfaceRadius(*planet_, direction)
            : body->radiusMeters;
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
    if (const auto* body = physicsFrameBody()) {
        const glm::dvec3 localUp = safeNormalize(localPosition_);
        return safeNormalize(body->orientation * localForwardDirection(localUp));
    }

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

    // Reconstruct the same local state under the celestial body's latest orbit/spin pose. A player
    // standing still therefore remains at exactly the same planet-local patch without a contact
    // solver having to chase the planet's absolute orbital/surface speed.
    if (const auto* body = physicsFrameBody()) syncWorldStateFromLocal(*body);

    if (celestialSystem_ != nullptr) {
        const CelestialBody* desiredFrame = celestialSystem_->physicsReferenceBodyAt(position_);
        if (inPhysicsFrame_ && (desiredFrame == nullptr || desiredFrame->id != physicsFrameBodyId_)) {
            // position_/velocity_ are already inertial, including orbital + omega x r velocity.
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

    if (auto* body = const_cast<CelestialBody*>(physicsFrameBody())) {
        const glm::dvec3 localUp = safeNormalize(localPosition_);
        const glm::dvec3 localForward = localForwardDirection(localUp);
        glm::dvec3 localRight = glm::cross(localForward, localUp);
        if (glm::dot(localRight, localRight) < 1.0e-10) localRight = safeEast(localUp);
        else localRight = glm::normalize(localRight);

        if (flightMode_) {
            glm::dvec3 move = localForward * input.forward + localRight * input.right + localUp * input.vertical;
            const double moveLength = glm::length(move);
            if (moveLength > 1.0) move /= moveLength;
            const double targetSpeed = input.sprint ? 1200.0 : 320.0;
            const glm::dvec3 desired = moveLength > 1.0e-8 ? move * targetSpeed : glm::dvec3{};
            localVelocity_ += (desired - localVelocity_) * (1.0 - std::exp(-6.0 * dt));
            localPosition_ += localVelocity_ * dt;
            grounded_ = false;
        } else {
            const bool wasGrounded = grounded_;
            if (wasGrounded && input.vertical > 0.5) {
                localVelocity_ += localUp * (input.sprint ? 28.0 : 14.0);
                grounded_ = false;
            }

            if (wasGrounded && input.vertical <= 0.5) {
                glm::dvec3 desiredTangent = localForward * input.forward + localRight * input.right;
                const double desiredLength = glm::length(desiredTangent);
                if (desiredLength > 1.0) desiredTangent /= desiredLength;
                const double targetSpeed = input.sprint ? 26.0 : 9.0;
                desiredTangent *= targetSpeed;

                const glm::dvec3 radial = localUp * glm::dot(localVelocity_, localUp);
                glm::dvec3 tangent = localVelocity_ - radial;
                const double response = 1.0 - std::exp(-(desiredLength > 1.0e-8 ? 18.0 : 14.0) * dt);
                tangent += (desiredTangent - tangent) * response;
                localVelocity_ = radial + tangent;
            }

            if (celestialSystem_ != nullptr) {
                localVelocity_ += physicsFrame_.gravityAcceleration(
                    *celestialSystem_, *body, localPosition_, localVelocity_) * dt;
            }
            localPosition_ += localVelocity_ * dt;

            // Ground state comes ONLY from surface contact. Merely being in a planet physics bubble
            // never enables walking, which prevents the old "walking around Earth in space" bug.
            const glm::dvec3 direction = safeNormalize(localPosition_);
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

        syncWorldStateFromLocal(*body);

        // Crossing the precision bubble boundary is a pure coordinate handoff. There is no speed
        // reset and no gravity switch: the exact inertial velocity is preserved for interplanetary
        // flight, then another planet can independently become the next local physics frame.
        if (celestialSystem_ != nullptr) {
            const CelestialBody* owner = celestialSystem_->physicsReferenceBodyAt(position_);
            if (owner == nullptr || owner->id != physicsFrameBodyId_) leavePhysicsFrame();
        }
        return;
    }

    if (celestialSystem_ != nullptr) {
        const glm::dvec3 localUp = up();
        const glm::dvec3 forward = forwardDirection();
        glm::dvec3 right = glm::cross(forward, localUp);
        if (glm::dot(right, right) < 1.0e-10) right = safeEast(localUp);
        else right = glm::normalize(right);

        if (flightMode_) {
            glm::dvec3 move = forward * input.forward + right * input.right + localUp * input.vertical;
            const double moveLength = glm::length(move);
            if (moveLength > 1.0) move /= moveLength;
            const double targetSpeed = input.sprint ? 1600.0 : 420.0;
            const glm::dvec3 desired = moveLength > 1.0e-8 ? move * targetSpeed : glm::dvec3{};
            velocity_ += (desired - velocity_) * (1.0 - std::exp(-6.0 * dt));
        } else {
            // EVA/free-flight without creative thrusters: no spherical WASD locomotion. Gravity is
            // simply the vector sum of whatever finite fields actually reach this point.
            velocity_ += celestialSystem_->gravityAccelerationAt(position_) * dt;
        }
        position_ += velocity_ * dt;

        if (const auto* newFrame = celestialSystem_->physicsReferenceBodyAt(position_)) {
            enterPhysicsFrame(*newFrame);
        }
        return;
    }

    // Standalone single-planet compatibility path used by low-level tests and tools.
    const glm::dvec3 localUp = safeNormalize(position_);
    const glm::dvec3 forward = forwardDirection();
    glm::dvec3 right = glm::cross(forward, localUp);
    if (glm::dot(right, right) < 1.0e-10) right = safeEast(localUp);
    else right = glm::normalize(right);

    if (flightMode_) {
        glm::dvec3 move = forward * input.forward + right * input.right + localUp * input.vertical;
        const double moveLength = glm::length(move);
        if (moveLength > 1.0) move /= moveLength;
        const double speed = input.sprint ? 70.0 : 28.0;
        velocity_ = moveLength > 1.0e-8 ? move * speed : glm::dvec3{};
        position_ += velocity_ * dt;
        grounded_ = false;
    } else {
        const glm::dvec3 east = safeEast(localUp);
        const glm::dvec3 north = safeNormalize(glm::cross(localUp, east), {0.0, 0.0, 1.0});
        const glm::dvec3 tangentForward = safeNormalize(
            std::cos(heading_) * north + std::sin(heading_) * east,
            north);
        const glm::dvec3 tangentRight = safeNormalize(glm::cross(tangentForward, localUp), east);
        const double tangentSpeed = input.sprint ? 34.0 : 12.0;
        position_ += (tangentForward * input.forward + tangentRight * input.right) * tangentSpeed * dt;
        const glm::dvec3 direction = safeNormalize(position_);
        const double minimumRadius = planetSurfaceRadius(*planet_, direction) + eyeHeight_;
        position_ = direction * std::max(glm::length(position_), minimumRadius);
        velocity_ = {};
        grounded_ = true;
    }
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
