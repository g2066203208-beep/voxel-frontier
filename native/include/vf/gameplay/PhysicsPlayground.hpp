#pragma once

#include <cstdint>
#include <vector>

#include <glm/glm.hpp>

#include "vf/physics/PhysicsWorld.hpp"
#include "vf/physics/TreePhysics.hpp"
#include "vf/world/PlanetSurface.hpp"

namespace vf {

class PhysicsPlayground final {
public:
    PhysicsPlayground(
        PhysicsWorld& physics,
        const PlanetDefinition& planet,
        const glm::dvec3& centerDirection);

    void update(double deltaSeconds);
    [[nodiscard]] PlanetMesh buildDebugMesh() const;

    [[nodiscard]] std::size_t visibleBodyCount() const noexcept { return visibleBodyIds_.size(); }
    [[nodiscard]] const TreePhysics& tree() const noexcept { return tree_; }

private:
    [[nodiscard]] glm::dvec3 surfacePoint(double eastMeters, double northMeters, double heightMeters) const;
    [[nodiscard]] bool isSpecialBody(std::uint32_t id) const noexcept;

    PhysicsWorld* physics_{};
    const PlanetDefinition* planet_{};
    glm::dvec3 centerDirection_{};
    glm::dvec3 up_{};
    glm::dvec3 east_{};
    glm::dvec3 north_{};

    std::uint32_t springAnchor_{};
    std::uint32_t springPayload_{};
    std::uint32_t motorAnchor_{};
    std::uint32_t motorRotor_{};
    std::uint32_t gearAnchorA_{};
    std::uint32_t gearAnchorB_{};
    std::uint32_t gearRotorA_{};
    std::uint32_t gearRotorB_{};
    std::uint32_t balloon_{};
    std::vector<std::uint32_t> fallingBodies_;
    std::vector<std::uint32_t> visibleBodyIds_;

    TreePhysics tree_{};
    double elapsedSeconds_{};
};

} // namespace vf
