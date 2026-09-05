#pragma once

#include <cstdint>
#include <vector>

#include <glm/glm.hpp>

#include "vf/physics/MaterialPhysics.hpp"

namespace vf {

enum class DamageType : std::uint8_t {
    Impact,
    Cut,
    Crush,
    Pierce,
    Shear,
    Tension,
    Explosion,
    Heat,
    Fatigue,
};

struct DamageEvent {
    DamageType type{DamageType::Impact};
    glm::dvec3 position{};
    glm::dvec3 direction{0.0, 1.0, 0.0};
    double energyJoules{};
    double impulseNewtonSeconds{};
    double radiusMeters{0.20};
};

struct StructuralChunk {
    std::uint32_t id{};
    glm::dvec3 center{};
    double massKg{1.0};
    bool worldAnchored{};
};

struct StructuralBond {
    std::uint32_t chunkA{};
    std::uint32_t chunkB{}; // 0 = world / immovable support.
    glm::dvec3 centroid{};
    glm::dvec3 normal{0.0, 1.0, 0.0};
    double areaM2{0.01};
    double characteristicThicknessMeters{0.05};
    double health{1.0};
    bool broken{};
};

struct StructuralIsland {
    std::vector<std::uint32_t> chunkIds;
    bool worldAnchored{};
};

struct FractureResult {
    std::vector<std::uint32_t> brokenBondIndices;
    std::vector<StructuralIsland> islands;
    bool topologyChanged{};
};

// Event-driven, sparse destruction graph. Idle assemblies cost no simulation work: the graph is
// touched only when gameplay produces damage or when code explicitly asks for islands.
class StructuralAssembly final {
public:
    [[nodiscard]] std::uint32_t addChunk(StructuralChunk chunk);
    [[nodiscard]] std::uint32_t addBond(StructuralBond bond);

    [[nodiscard]] const std::vector<StructuralChunk>& chunks() const noexcept { return chunks_; }
    [[nodiscard]] const std::vector<StructuralBond>& bonds() const noexcept { return bonds_; }
    [[nodiscard]] std::vector<StructuralBond>& bonds() noexcept { return bonds_; }

    [[nodiscard]] FractureResult applyDamage(
        const DamageEvent& event,
        const MaterialDefinition& material);

    [[nodiscard]] std::vector<StructuralIsland> islands() const;

private:
    [[nodiscard]] bool containsChunk(std::uint32_t id) const noexcept;

    std::vector<StructuralChunk> chunks_;
    std::vector<StructuralBond> bonds_;
    std::uint32_t nextChunkId_{1U};
};

[[nodiscard]] double structuralBondCapacityJoules(
    const StructuralBond& bond,
    const MaterialDefinition& material) noexcept;

[[nodiscard]] double damageTypeEfficiency(DamageType type) noexcept;

} // namespace vf
