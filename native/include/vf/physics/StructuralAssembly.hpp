#pragma once

#include <cstdint>
#include <span>
#include <vector>

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

#include "vf/physics/MaterialPhysics.hpp"
#include "vf/physics/StructuralDamage.hpp"

namespace vf {

class PhysicsWorld;

struct StructuralBondDesc {
    std::uint32_t bodyA{};
    std::uint32_t bodyB{};
    glm::dvec3 localAnchorA{};
    glm::dvec3 localAnchorB{};
    glm::dvec3 localBendAxisA{0.0, 1.0, 0.0};
    glm::dvec3 localBendAxisB{0.0, 1.0, 0.0};
    double restLengthMeters{-1.0};
    StructuralBondGeometry geometry{};
    MaterialDefinition material{};
    double axialDampingNsPerM{400.0};
    double angularDampingNmsPerRad{30.0};
};

struct StructuralBond {
    std::uint32_t id{};
    StructuralBondDesc desc{};
    MaterialState materialState{};
    StructuralBondState damageState{};
    double lastAxialForceN{};
    double lastBendingMomentNm{};
    double lastUtilization{};
};

class StructuralAssembly final {
public:
    [[nodiscard]] std::uint32_t addBond(const StructuralBondDesc& desc, const PhysicsWorld& world);
    [[nodiscard]] StructuralBond* bond(std::uint32_t id) noexcept;
    [[nodiscard]] const StructuralBond* bond(std::uint32_t id) const noexcept;
    [[nodiscard]] std::span<StructuralBond> bonds() noexcept { return bonds_; }
    [[nodiscard]] std::span<const StructuralBond> bonds() const noexcept { return bonds_; }

    void step(PhysicsWorld& world, double deltaSeconds);

private:
    std::vector<StructuralBond> bonds_;
    std::uint32_t nextBondId_{1};
};

} // namespace vf
