#include "vf/physics/RopeXpbd.hpp"

#include "vf/physics/PhysicsWorld.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kEpsilon = 1.0e-10;
constexpr int kSolverIterations = 8;
constexpr double kTargetSubstep = 1.0 / 120.0;

struct SegmentClosestPoints {
    double s{};
    double t{};
    glm::dvec3 a{};
    glm::dvec3 b{};
};

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {1.0, 0.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= kEpsilon) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] SegmentClosestPoints closestSegmentSegment(
    const glm::dvec3& p1,
    const glm::dvec3& q1,
    const glm::dvec3& p2,
    const glm::dvec3& q2) noexcept {
    const glm::dvec3 d1 = q1 - p1;
    const glm::dvec3 d2 = q2 - p2;
    const glm::dvec3 r = p1 - p2;
    const double a = glm::dot(d1, d1);
    const double e = glm::dot(d2, d2);
    const double f = glm::dot(d2, r);

    double s = 0.0;
    double t = 0.0;
    if (a <= kEpsilon && e <= kEpsilon) {
        return {0.0, 0.0, p1, p2};
    }
    if (a <= kEpsilon) {
        t = std::clamp(f / e, 0.0, 1.0);
    } else {
        const double c = glm::dot(d1, r);
        if (e <= kEpsilon) {
            s = std::clamp(-c / a, 0.0, 1.0);
        } else {
            const double b = glm::dot(d1, d2);
            const double denominator = a * e - b * b;
            if (std::abs(denominator) > kEpsilon) s = std::clamp((b * f - c * e) / denominator, 0.0, 1.0);
            t = (b * s + f) / e;
            if (t < 0.0) {
                t = 0.0;
                s = std::clamp(-c / a, 0.0, 1.0);
            } else if (t > 1.0) {
                t = 1.0;
                s = std::clamp((b - c) / a, 0.0, 1.0);
            }
        }
    }
    return {s, t, p1 + d1 * s, p2 + d2 * t};
}

} // namespace

void RopeXpbd::initialize(std::vector<glm::dvec3> points, double totalMassKg, RopeMaterial material) {
    if (points.size() < 2U) throw std::invalid_argument("RopeXpbd requires at least two particles");
    if (points.size() > 256U) throw std::invalid_argument("RopeXpbd gameplay rope is capped at 256 particles");
    if (!(totalMassKg > 0.0) || !std::isfinite(totalMassKg)) throw std::invalid_argument("RopeXpbd mass must be positive");

    material.radiusMeters = std::max(0.001, material.radiusMeters);
    material.stretchComplianceMPerN = std::max(0.0, material.stretchComplianceMPerN);
    material.bendComplianceMPerN = std::max(0.0, material.bendComplianceMPerN);
    material.damping = std::clamp(material.damping, 0.0, 1.0);
    material.friction = std::clamp(material.friction, 0.0, 1.0);
    material.dragCoefficient = std::max(0.0, material.dragCoefficient);
    material.breakingStrain = std::max(0.001, material.breakingStrain);
    material.maxTensionN = std::max(0.0, material.maxTensionN);
    material_ = material;

    particles_.clear();
    particles_.reserve(points.size());
    const double inverseParticleMass = static_cast<double>(points.size()) / totalMassKg;
    for (const auto& point : points) {
        particles_.push_back({point, point, {}, inverseParticleMass});
    }

    restLengths_.resize(points.size() - 1U);
    distanceLambdas_.assign(restLengths_.size(), 0.0);
    linkBroken_.assign(restLengths_.size(), 0U);
    for (std::size_t i = 0; i < restLengths_.size(); ++i) {
        restLengths_[i] = std::max(1.0e-5, glm::length(points[i + 1U] - points[i]));
    }

    if (points.size() >= 3U) {
        bendRestDistances_.resize(points.size() - 2U);
        bendLambdas_.assign(bendRestDistances_.size(), 0.0);
        for (std::size_t i = 0; i < bendRestDistances_.size(); ++i) {
            bendRestDistances_[i] = std::max(1.0e-5, glm::length(points[i + 2U] - points[i]));
        }
    } else {
        bendRestDistances_.clear();
        bendLambdas_.clear();
    }

    pinned_.assign(points.size(), 0U);
    pinnedPositions_ = points;
    attachments_.clear();
    capsuleColliders_.clear();
    lastMaximumTensionN_ = 0.0;
}

double RopeXpbd::restLengthMeters() const noexcept {
    double total = 0.0;
    for (double length : restLengths_) total += length;
    return total;
}

double RopeXpbd::currentLengthMeters() const noexcept {
    double total = 0.0;
    for (std::size_t i = 0; i + 1U < particles_.size(); ++i) {
        if (i < linkBroken_.size() && linkBroken_[i] != 0U) continue;
        total += glm::length(particles_[i + 1U].position - particles_[i].position);
    }
    return total;
}

std::size_t RopeXpbd::brokenLinkCount() const noexcept {
    return static_cast<std::size_t>(std::count_if(linkBroken_.begin(), linkBroken_.end(), [](std::uint8_t value) {
        return value != 0U;
    }));
}

void RopeXpbd::pinParticle(std::size_t index, const glm::dvec3& worldPosition) {
    if (index >= particles_.size()) throw std::out_of_range("RopeXpbd pin index out of range");
    pinned_[index] = 1U;
    pinnedPositions_[index] = worldPosition;
    particles_[index].position = worldPosition;
    particles_[index].previousPosition = worldPosition;
    particles_[index].velocity = {};
}

void RopeXpbd::setPinnedPosition(std::size_t index, const glm::dvec3& worldPosition) {
    if (index >= particles_.size() || pinned_[index] == 0U) throw std::out_of_range("RopeXpbd particle is not pinned");
    pinnedPositions_[index] = worldPosition;
}

void RopeXpbd::unpinParticle(std::size_t index) {
    if (index >= particles_.size()) throw std::out_of_range("RopeXpbd unpin index out of range");
    pinned_[index] = 0U;
}

void RopeXpbd::attachParticleToRigidBody(std::size_t index, std::uint32_t bodyId, const glm::dvec3& localAnchor) {
    if (index >= particles_.size()) throw std::out_of_range("RopeXpbd attachment index out of range");
    attachments_.erase(std::remove_if(attachments_.begin(), attachments_.end(), [index](const RopeRigidAttachment& value) {
        return value.particleIndex == index;
    }), attachments_.end());
    attachments_.push_back({index, bodyId, localAnchor, true});
}

void RopeXpbd::addCapsuleCollider(RopeCapsuleCollider collider) {
    collider.radiusMeters = std::max(0.0, collider.radiusMeters);
    collider.friction = std::clamp(collider.friction, 0.0, 1.0);
    capsuleColliders_.push_back(collider);
}

bool RopeXpbd::particleConstrained(std::size_t index) const noexcept {
    if (index < pinned_.size() && pinned_[index] != 0U) return true;
    for (const auto& attachment : attachments_) {
        if (attachment.enabled && attachment.particleIndex == index) return true;
    }
    return false;
}

double RopeXpbd::effectiveInverseMass(std::size_t index) const noexcept {
    if (index >= particles_.size() || particleConstrained(index)) return 0.0;
    return particles_[index].inverseMass;
}

void RopeXpbd::applyPinsAndAttachments(PhysicsWorld* rigidWorld, double dt) {
    for (std::size_t i = 0; i < particles_.size(); ++i) {
        if (pinned_[i] == 0U) continue;
        particles_[i].position = pinnedPositions_[i];
        particles_[i].previousPosition = pinnedPositions_[i];
        particles_[i].velocity = {};
    }

    if (rigidWorld == nullptr) return;
    for (const auto& attachment : attachments_) {
        if (!attachment.enabled || attachment.particleIndex >= particles_.size()) continue;
        RigidBody* body = rigidWorld->body(attachment.bodyId);
        if (body == nullptr) continue;
        RopeParticle& particle = particles_[attachment.particleIndex];
        const glm::dvec3 anchor = body->position + body->orientation * attachment.localAnchor;
        const glm::dvec3 anchorVelocity = body->velocityAtPoint(anchor);
        particle.position = anchor;
        particle.previousPosition = anchor - anchorVelocity * dt;
        particle.velocity = anchorVelocity;
    }
}

void RopeXpbd::solveDistanceConstraints(double dt) {
    const double alpha = material_.stretchComplianceMPerN / std::max(kEpsilon, dt * dt);
    for (std::size_t i = 0; i < restLengths_.size(); ++i) {
        if (linkBroken_[i] != 0U) continue;
        RopeParticle& a = particles_[i];
        RopeParticle& b = particles_[i + 1U];
        const glm::dvec3 delta = b.position - a.position;
        const double length = glm::length(delta);
        if (length <= kEpsilon) continue;

        const double strain = (length - restLengths_[i]) / restLengths_[i];
        if (strain > material_.breakingStrain) {
            linkBroken_[i] = 1U;
            distanceLambdas_[i] = 0.0;
            continue;
        }

        const double wa = effectiveInverseMass(i);
        const double wb = effectiveInverseMass(i + 1U);
        const double denominator = wa + wb + alpha;
        if (denominator <= kEpsilon) continue;

        const glm::dvec3 normal = delta / length;
        const double constraint = length - restLengths_[i];
        const double deltaLambda = (-constraint - alpha * distanceLambdas_[i]) / denominator;
        distanceLambdas_[i] += deltaLambda;
        a.position -= normal * (wa * deltaLambda);
        b.position += normal * (wb * deltaLambda);
    }
}

void RopeXpbd::solveBendingConstraints(double dt) {
    const double alpha = material_.bendComplianceMPerN / std::max(kEpsilon, dt * dt);
    for (std::size_t i = 0; i < bendRestDistances_.size(); ++i) {
        if ((i < linkBroken_.size() && linkBroken_[i] != 0U)
            || (i + 1U < linkBroken_.size() && linkBroken_[i + 1U] != 0U)) continue;

        RopeParticle& a = particles_[i];
        RopeParticle& c = particles_[i + 2U];
        const glm::dvec3 delta = c.position - a.position;
        const double distance = glm::length(delta);
        if (distance <= kEpsilon) continue;
        const double wa = effectiveInverseMass(i);
        const double wc = effectiveInverseMass(i + 2U);
        const double denominator = wa + wc + alpha;
        if (denominator <= kEpsilon) continue;

        const glm::dvec3 normal = delta / distance;
        const double constraint = distance - bendRestDistances_[i];
        const double deltaLambda = (-constraint - alpha * bendLambdas_[i]) / denominator;
        bendLambdas_[i] += deltaLambda;
        a.position -= normal * (wa * deltaLambda);
        c.position += normal * (wc * deltaLambda);
    }
}

void RopeXpbd::solveCapsuleCollisions() {
    if (particles_.size() < 2U) return;
    const double ropeRadius = material_.radiusMeters;
    for (const auto& collider : capsuleColliders_) {
        const double minimumDistance = ropeRadius + collider.radiusMeters;
        for (std::size_t i = 0; i + 1U < particles_.size(); ++i) {
            if (linkBroken_[i] != 0U) continue;
            auto closest = closestSegmentSegment(
                particles_[i].position,
                particles_[i + 1U].position,
                collider.a,
                collider.b);
            const glm::dvec3 separation = closest.a - closest.b;
            const double distance = glm::length(separation);
            if (distance >= minimumDistance) continue;

            const glm::dvec3 fallback = safeNormalize(glm::cross(
                particles_[i + 1U].position - particles_[i].position,
                collider.b - collider.a), {1.0, 0.0, 0.0});
            const glm::dvec3 normal = safeNormalize(separation, fallback);
            const double b0 = 1.0 - closest.s;
            const double b1 = closest.s;
            const double w0 = effectiveInverseMass(i);
            const double w1 = effectiveInverseMass(i + 1U);
            const double denominator = w0 * b0 * b0 + w1 * b1 * b1;
            if (denominator <= kEpsilon) continue;

            const double correction = (minimumDistance - distance) / denominator;
            particles_[i].position += normal * (w0 * b0 * correction);
            particles_[i + 1U].position += normal * (w1 * b1 * correction);

            // Coulomb-like positional friction: reduce tangential displacement at the contact.
            const glm::dvec3 previousPoint = particles_[i].previousPosition * b0
                + particles_[i + 1U].previousPosition * b1;
            const glm::dvec3 displacement = closest.a - previousPoint;
            const glm::dvec3 tangent = displacement - normal * glm::dot(displacement, normal);
            const double friction = std::clamp(material_.friction * collider.friction, 0.0, 1.0);
            particles_[i].previousPosition += tangent * (friction * b0);
            particles_[i + 1U].previousPosition += tangent * (friction * b1);
        }
    }
}

void RopeXpbd::solveSelfCollisions() {
    if (!material_.selfCollision || particles_.size() < 4U) return;
    const double minimumDistance = material_.radiusMeters * 2.0;
    for (std::size_t i = 0; i + 1U < particles_.size(); ++i) {
        if (linkBroken_[i] != 0U) continue;
        for (std::size_t j = i + 2U; j + 1U < particles_.size(); ++j) {
            if (j == i + 1U || linkBroken_[j] != 0U) continue;
            auto closest = closestSegmentSegment(
                particles_[i].position,
                particles_[i + 1U].position,
                particles_[j].position,
                particles_[j + 1U].position);
            const glm::dvec3 separation = closest.a - closest.b;
            const double distance = glm::length(separation);
            if (distance >= minimumDistance) continue;

            const glm::dvec3 normal = safeNormalize(separation, {1.0, 0.0, 0.0});
            const double a0 = 1.0 - closest.s;
            const double a1 = closest.s;
            const double b0 = 1.0 - closest.t;
            const double b1 = closest.t;
            const double wi0 = effectiveInverseMass(i);
            const double wi1 = effectiveInverseMass(i + 1U);
            const double wj0 = effectiveInverseMass(j);
            const double wj1 = effectiveInverseMass(j + 1U);
            const double denominator = wi0 * a0 * a0 + wi1 * a1 * a1
                + wj0 * b0 * b0 + wj1 * b1 * b1;
            if (denominator <= kEpsilon) continue;

            const double correction = (minimumDistance - distance) / denominator;
            particles_[i].position += normal * (wi0 * a0 * correction);
            particles_[i + 1U].position += normal * (wi1 * a1 * correction);
            particles_[j].position -= normal * (wj0 * b0 * correction);
            particles_[j + 1U].position -= normal * (wj1 * b1 * correction);
        }
    }
}

void RopeXpbd::applyAttachmentReactions(PhysicsWorld* rigidWorld, double dt) {
    if (rigidWorld == nullptr || dt <= 0.0 || particles_.size() < 2U) return;
    for (const auto& attachment : attachments_) {
        if (!attachment.enabled || attachment.particleIndex >= particles_.size()) continue;
        RigidBody* body = rigidWorld->body(attachment.bodyId);
        if (body == nullptr || body->motionType != MotionType::Dynamic) continue;

        std::size_t linkIndex = 0U;
        std::size_t neighbor = 0U;
        if (attachment.particleIndex == 0U) {
            linkIndex = 0U;
            neighbor = 1U;
        } else if (attachment.particleIndex + 1U == particles_.size()) {
            linkIndex = particles_.size() - 2U;
            neighbor = particles_.size() - 2U;
        } else {
            continue;
        }
        if (linkIndex >= linkBroken_.size() || linkBroken_[linkIndex] != 0U) continue;

        const double tension = std::min(
            material_.maxTensionN,
            std::abs(distanceLambdas_[linkIndex]) / std::max(kEpsilon, dt * dt));
        lastMaximumTensionN_ = std::max(lastMaximumTensionN_, tension);
        if (tension <= 0.0) continue;

        const glm::dvec3 anchor = body->position + body->orientation * attachment.localAnchor;
        const glm::dvec3 direction = safeNormalize(particles_[neighbor].position - anchor);
        body->applyImpulseAtPoint(direction * (tension * dt), anchor);
    }
}

void RopeXpbd::step(
    double deltaSeconds,
    const glm::dvec3& gravityAcceleration,
    const glm::dvec3& windVelocity,
    double airDensityKgPerM3,
    PhysicsWorld* rigidWorld) {
    if (!initialized() || deltaSeconds <= 0.0) return;
    deltaSeconds = std::clamp(deltaSeconds, 0.0, 0.05);
    const int substepCount = std::clamp(static_cast<int>(std::ceil(deltaSeconds / kTargetSubstep)), 1, 8);
    const double dt = deltaSeconds / static_cast<double>(substepCount);
    const double averageSegmentLength = restLengthMeters() / static_cast<double>(restLengths_.size());
    const double projectedArea = 2.0 * material_.radiusMeters * averageSegmentLength;
    lastMaximumTensionN_ = 0.0;

    for (int substep = 0; substep < substepCount; ++substep) {
        std::fill(distanceLambdas_.begin(), distanceLambdas_.end(), 0.0);
        std::fill(bendLambdas_.begin(), bendLambdas_.end(), 0.0);
        applyPinsAndAttachments(rigidWorld, dt);

        for (std::size_t i = 0; i < particles_.size(); ++i) {
            if (particleConstrained(i)) continue;
            RopeParticle& particle = particles_[i];
            particle.previousPosition = particle.position;
            particle.velocity += gravityAcceleration * dt;

            if (airDensityKgPerM3 > 0.0 && material_.dragCoefficient > 0.0) {
                const glm::dvec3 relative = windVelocity - particle.velocity;
                const double speed = glm::length(relative);
                if (speed > 1.0e-6) {
                    const double force = 0.5 * airDensityKgPerM3 * material_.dragCoefficient
                        * projectedArea * speed * speed;
                    particle.velocity += (relative / speed) * (force * particle.inverseMass * dt);
                }
            }
            particle.position += particle.velocity * dt;
        }

        for (int iteration = 0; iteration < kSolverIterations; ++iteration) {
            solveDistanceConstraints(dt);
            solveBendingConstraints(dt);
            solveCapsuleCollisions();
            solveSelfCollisions();
            applyPinsAndAttachments(rigidWorld, dt);
        }

        for (std::size_t i = 0; i < particles_.size(); ++i) {
            if (particleConstrained(i)) continue;
            RopeParticle& particle = particles_[i];
            particle.velocity = (particle.position - particle.previousPosition) / dt;
            particle.velocity *= std::max(0.0, 1.0 - material_.damping);
        }

        for (std::size_t i = 0; i < distanceLambdas_.size(); ++i) {
            if (linkBroken_[i] != 0U) continue;
            lastMaximumTensionN_ = std::max(lastMaximumTensionN_,
                std::min(material_.maxTensionN,
                    std::abs(distanceLambdas_[i]) / std::max(kEpsilon, dt * dt)));
        }
        applyAttachmentReactions(rigidWorld, dt);
    }
}

} // namespace vf
