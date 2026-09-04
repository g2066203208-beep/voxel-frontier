#include "vf/physics/StructuralDamage.hpp"

#include <algorithm>
#include <cmath>
#include <queue>
#include <stdexcept>
#include <unordered_map>

namespace vf {
namespace {

constexpr double kEpsilon = 1.0e-12;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= kEpsilon) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] double localFalloff(double distanceMeters, double radiusMeters) noexcept {
    const double radius = std::max(1.0e-4, radiusMeters);
    if (distanceMeters >= radius) return 0.0;
    const double x = 1.0 - distanceMeters / radius;
    return x * x * (3.0 - 2.0 * x);
}

[[nodiscard]] double directionalFactor(const DamageEvent& event, const StructuralBond& bond) noexcept {
    const glm::dvec3 direction = safeNormalize(event.direction);
    const glm::dvec3 normal = safeNormalize(bond.normal);
    const double alignment = std::abs(glm::dot(direction, normal));

    switch (event.type) {
    case DamageType::Cut:
    case DamageType::Pierce:
    case DamageType::Shear:
        return 0.70 + 0.30 * alignment;
    case DamageType::Tension:
        return 0.55 + 0.45 * alignment;
    case DamageType::Explosion:
        return 1.0;
    default:
        return 0.80 + 0.20 * alignment;
    }
}

} // namespace

double damageTypeEfficiency(DamageType type) noexcept {
    switch (type) {
    case DamageType::Cut: return 2.40;
    case DamageType::Pierce: return 1.75;
    case DamageType::Shear: return 1.55;
    case DamageType::Crush: return 1.20;
    case DamageType::Explosion: return 1.00;
    case DamageType::Tension: return 0.95;
    case DamageType::Impact: return 0.72;
    case DamageType::Heat: return 0.55;
    case DamageType::Fatigue: return 0.30;
    }
    return 1.0;
}

double structuralBondCapacityJoules(
    const StructuralBond& bond,
    const MaterialDefinition& material) noexcept {
    const double area = std::max(1.0e-8, bond.areaM2);
    const double thickness = std::max(1.0e-5, bond.characteristicThicknessMeters);
    const double toughness = std::max(0.0, material.fractureToughnessJPerM2) * area;
    const double ultimate = std::max(1.0, material.ultimateStrengthPa);
    const double strain = std::max(1.0e-5, material.fractureStrain);
    const double strainEnergy = 0.5 * ultimate * strain * area * thickness;
    return std::max(1.0e-3, toughness + strainEnergy);
}

std::uint32_t StructuralAssembly::addChunk(StructuralChunk chunk) {
    if (chunk.id == 0U) chunk.id = nextChunkId_++;
    else {
        if (containsChunk(chunk.id)) throw std::invalid_argument("structural chunk id must be unique");
        nextChunkId_ = std::max(nextChunkId_, chunk.id + 1U);
    }
    chunk.massKg = std::max(0.0, chunk.massKg);
    chunks_.push_back(chunk);
    return chunk.id;
}

std::uint32_t StructuralAssembly::addBond(StructuralBond bond) {
    if (bond.chunkA == 0U || !containsChunk(bond.chunkA))
        throw std::invalid_argument("structural bond chunkA must reference an existing chunk");
    if (bond.chunkB != 0U && !containsChunk(bond.chunkB))
        throw std::invalid_argument("structural bond chunkB must reference an existing chunk or world");
    if (bond.chunkA == bond.chunkB)
        throw std::invalid_argument("structural bond cannot connect a chunk to itself");
    bond.areaM2 = std::max(1.0e-8, bond.areaM2);
    bond.characteristicThicknessMeters = std::max(1.0e-5, bond.characteristicThicknessMeters);
    bond.health = std::clamp(bond.health, 0.0, 1.0);
    bond.broken = bond.broken || bond.health <= 0.0;
    if (bond.broken) bond.health = 0.0;
    bonds_.push_back(bond);
    return static_cast<std::uint32_t>(bonds_.size() - 1U);
}

bool StructuralAssembly::containsChunk(std::uint32_t id) const noexcept {
    return std::any_of(chunks_.begin(), chunks_.end(), [id](const StructuralChunk& chunk) {
        return chunk.id == id;
    });
}

FractureResult StructuralAssembly::applyDamage(
    const DamageEvent& event,
    const MaterialDefinition& material) {
    FractureResult result{};
    const double availableEnergy = std::max(0.0, event.energyJoules);
    if (availableEnergy <= 0.0 || bonds_.empty()) return result;

    const double efficiency = damageTypeEfficiency(event.type);
    for (std::size_t i = 0; i < bonds_.size(); ++i) {
        auto& bond = bonds_[i];
        if (bond.broken) continue;
        const double falloff = localFalloff(glm::distance(event.position, bond.centroid), event.radiusMeters);
        if (falloff <= 0.0) continue;

        const double deliveredEnergy = availableEnergy * efficiency * falloff * directionalFactor(event, bond);
        const double capacity = structuralBondCapacityJoules(bond, material);
        const double damage = deliveredEnergy / capacity;
        if (!std::isfinite(damage) || damage <= 0.0) continue;

        bond.health = std::clamp(bond.health - damage, 0.0, 1.0);
        if (bond.health <= 0.0) {
            bond.health = 0.0;
            bond.broken = true;
            result.brokenBondIndices.push_back(static_cast<std::uint32_t>(i));
        }
    }

    result.topologyChanged = !result.brokenBondIndices.empty();
    if (result.topologyChanged) result.islands = islands();
    return result;
}

std::vector<StructuralIsland> StructuralAssembly::islands() const {
    std::vector<StructuralIsland> result;
    if (chunks_.empty()) return result;

    std::unordered_map<std::uint32_t, std::size_t> indexById;
    indexById.reserve(chunks_.size());
    for (std::size_t i = 0; i < chunks_.size(); ++i) indexById.emplace(chunks_[i].id, i);

    std::vector<std::vector<std::uint32_t>> adjacency(chunks_.size());
    std::vector<bool> anchored(chunks_.size(), false);
    for (std::size_t i = 0; i < chunks_.size(); ++i) anchored[i] = chunks_[i].worldAnchored;

    for (const auto& bond : bonds_) {
        if (bond.broken) continue;
        const auto aIt = indexById.find(bond.chunkA);
        if (aIt == indexById.end()) continue;
        if (bond.chunkB == 0U) {
            anchored[aIt->second] = true;
            continue;
        }
        const auto bIt = indexById.find(bond.chunkB);
        if (bIt == indexById.end()) continue;
        adjacency[aIt->second].push_back(bond.chunkB);
        adjacency[bIt->second].push_back(bond.chunkA);
    }

    std::vector<bool> visited(chunks_.size(), false);
    for (std::size_t root = 0; root < chunks_.size(); ++root) {
        if (visited[root]) continue;
        StructuralIsland island{};
        std::queue<std::size_t> open;
        open.push(root);
        visited[root] = true;

        while (!open.empty()) {
            const std::size_t current = open.front();
            open.pop();
            island.chunkIds.push_back(chunks_[current].id);
            island.worldAnchored = island.worldAnchored || anchored[current];
            for (const std::uint32_t neighborId : adjacency[current]) {
                const auto it = indexById.find(neighborId);
                if (it == indexById.end() || visited[it->second]) continue;
                visited[it->second] = true;
                open.push(it->second);
            }
        }
        std::sort(island.chunkIds.begin(), island.chunkIds.end());
        result.push_back(std::move(island));
    }

    std::sort(result.begin(), result.end(), [](const StructuralIsland& a, const StructuralIsland& b) {
        const std::uint32_t aFirst = a.chunkIds.empty() ? 0U : a.chunkIds.front();
        const std::uint32_t bFirst = b.chunkIds.empty() ? 0U : b.chunkIds.front();
        return aFirst < bFirst;
    });
    return result;
}

} // namespace vf
