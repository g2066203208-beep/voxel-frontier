#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <unordered_set>

#include <glm/geometric.hpp>

#include "vf/world/PlanetSurface.hpp"

namespace vf::detail {

inline constexpr float kStreamingFoliageTag = -1.0F;
inline constexpr float kStreamingBarkTag = -2.0F;
inline constexpr float kStreamingRockTag = -3.0F;

[[nodiscard]] inline std::uint64_t ecologyMix64(std::uint64_t x) noexcept {
    x += 0x9E3779B97F4A7C15ULL;
    x = (x ^ (x >> 30U)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27U)) * 0x94D049BB133111EBULL;
    return x ^ (x >> 31U);
}

[[nodiscard]] inline double ecologyUnit(std::uint64_t x) noexcept {
    return static_cast<double>(ecologyMix64(x) & 0xFFFFFFULL) / static_cast<double>(0xFFFFFFULL);
}

[[nodiscard]] inline glm::vec3 safeUnit(
    const glm::vec3& value,
    const glm::vec3& fallback = {0.0F, 1.0F, 0.0F}) noexcept {
    const float l2 = glm::dot(value, value);
    return l2 > 1.0e-10F ? value / std::sqrt(l2) : fallback;
}

inline void ecologyTriangle(PlanetMesh& mesh, std::uint32_t a, std::uint32_t b, std::uint32_t c) {
    mesh.indices.insert(mesh.indices.end(), {a, b, c});
}

[[nodiscard]] inline std::array<glm::vec3, 2> ecologyFrame(const glm::vec3& upInput) noexcept {
    const glm::vec3 up = safeUnit(upInput);
    const glm::vec3 helper = std::abs(up.y) < 0.92F
        ? glm::vec3{0.0F, 1.0F, 0.0F}
        : glm::vec3{1.0F, 0.0F, 0.0F};
    const glm::vec3 east = safeUnit(glm::cross(helper, up), {1.0F, 0.0F, 0.0F});
    return {east, safeUnit(glm::cross(up, east), {0.0F, 0.0F, 1.0F})};
}

inline void appendStreamingRock(
    PlanetMesh& mesh,
    const glm::vec3& base,
    const glm::vec3& up,
    std::uint64_t seed,
    float radius) {
    constexpr float phi = 1.61803398875F;
    constexpr std::array<glm::vec3, 12> points{{
        {-1.0F, phi, 0.0F}, {1.0F, phi, 0.0F}, {-1.0F, -phi, 0.0F}, {1.0F, -phi, 0.0F},
        {0.0F, -1.0F, phi}, {0.0F, 1.0F, phi}, {0.0F, -1.0F, -phi}, {0.0F, 1.0F, -phi},
        {phi, 0.0F, -1.0F}, {phi, 0.0F, 1.0F}, {-phi, 0.0F, -1.0F}, {-phi, 0.0F, 1.0F},
    }};
    constexpr std::array<std::array<std::uint32_t, 3>, 20> faces{{
        {{0,11,5}},{{0,5,1}},{{0,1,7}},{{0,7,10}},{{0,10,11}},{{1,5,9}},{{5,11,4}},{{11,10,2}},{{10,7,6}},{{7,1,8}},
        {{3,9,4}},{{3,4,2}},{{3,2,6}},{{3,6,8}},{{3,8,9}},{{4,9,5}},{{2,4,11}},{{6,2,10}},{{8,6,7}},{{9,8,1}},
    }};
    const auto frame = ecologyFrame(up);
    const glm::vec3 east = frame[0];
    const glm::vec3 north = frame[1];
    const float sx = radius * static_cast<float>(0.86 + ecologyUnit(seed + 1U) * 0.42);
    const float sy = radius * static_cast<float>(0.72 + ecologyUnit(seed + 2U) * 0.34);
    const float sz = radius * static_cast<float>(0.62 + ecologyUnit(seed + 3U) * 0.38);
    const glm::vec3 rockColor = glm::mix(
        glm::vec3{0.27F, 0.28F, 0.27F},
        glm::vec3{0.40F, 0.32F, 0.23F},
        static_cast<float>(ecologyUnit(seed + 4U)) * 0.55F);

    for (const auto& face : faces) {
        std::array<glm::vec3, 3> world{};
        for (std::uint32_t k = 0; k < 3U; ++k) {
            glm::vec3 q = safeUnit(points[face[k]], {0.0F, 1.0F, 0.0F});
            const float jitter = static_cast<float>(0.88 + ecologyUnit(seed + 20U + face[k]) * 0.24);
            q = {q.x * sx * jitter, q.y * sy * jitter, q.z * sz * jitter};
            world[k] = base + east * q.x + north * q.y + up * (q.z + sz * 0.15F);
        }
        glm::vec3 normal = safeUnit(glm::cross(world[1] - world[0], world[2] - world[0]), up);
        if (glm::dot(normal, up) < -0.85F) normal = -normal;
        const std::uint32_t first = static_cast<std::uint32_t>(mesh.vertices.size());
        for (std::uint32_t k = 0; k < 3U; ++k) {
            mesh.vertices.push_back({world[k], normal, rockColor, {0.0F, 0.76F, 0.0F, kStreamingRockTag}});
        }
        ecologyTriangle(mesh, first, first + 1U, first + 2U);
    }
}

inline void appendStreamingTree(
    PlanetMesh& mesh,
    const glm::vec3& base,
    const glm::vec3& up,
    std::uint64_t seed) {
    constexpr float pi = 3.14159265358979323846F;
    const auto frame = ecologyFrame(up);
    const glm::vec3 east = frame[0];
    const glm::vec3 north = frame[1];
    const float maturity = static_cast<float>(0.86 + ecologyUnit(seed + 1U) * 0.34);
    const float trunkHeight = 4.7F * maturity;
    const float trunkRadius = 0.38F * std::sqrt(maturity);
    const float yaw = static_cast<float>(ecologyUnit(seed + 2U) * 2.0 * pi);
    constexpr std::uint32_t sides = 7U;
    const glm::vec3 barkColor = glm::mix(
        glm::vec3{0.20F, 0.060F, 0.014F},
        glm::vec3{0.34F, 0.13F, 0.028F},
        static_cast<float>(ecologyUnit(seed + 3U)));

    const std::uint32_t trunkBase = static_cast<std::uint32_t>(mesh.vertices.size());
    for (std::uint32_t ring = 0; ring < 2U; ++ring) {
        const float z = ring == 0U ? -0.05F : trunkHeight;
        const float radius = ring == 0U ? trunkRadius : trunkRadius * 0.42F;
        for (std::uint32_t q = 0; q < sides; ++q) {
            const float angle = yaw + 2.0F * pi * static_cast<float>(q) / static_cast<float>(sides);
            const glm::vec3 radial = safeUnit(east * std::cos(angle) + north * std::sin(angle), east);
            mesh.vertices.push_back({
                base + up * z + radial * radius,
                safeUnit(radial * 0.88F + up * 0.12F, radial),
                barkColor,
                {0.0F, 0.95F, 0.0F, kStreamingBarkTag},
            });
        }
    }
    for (std::uint32_t q = 0; q < sides; ++q) {
        const std::uint32_t q1 = (q + 1U) % sides;
        ecologyTriangle(mesh, trunkBase + q, trunkBase + q1, trunkBase + sides + q1);
        ecologyTriangle(mesh, trunkBase + q, trunkBase + sides + q1, trunkBase + sides + q);
    }

    constexpr float phi = 1.61803398875F;
    constexpr std::array<glm::vec3, 12> ico{{
        {-1.0F, phi, 0.0F}, {1.0F, phi, 0.0F}, {-1.0F, -phi, 0.0F}, {1.0F, -phi, 0.0F},
        {0.0F, -1.0F, phi}, {0.0F, 1.0F, phi}, {0.0F, -1.0F, -phi}, {0.0F, 1.0F, -phi},
        {phi, 0.0F, -1.0F}, {phi, 0.0F, 1.0F}, {-phi, 0.0F, -1.0F}, {-phi, 0.0F, 1.0F},
    }};
    constexpr std::array<std::array<std::uint32_t, 3>, 20> faces{{
        {{0,11,5}},{{0,5,1}},{{0,1,7}},{{0,7,10}},{{0,10,11}},{{1,5,9}},{{5,11,4}},{{11,10,2}},{{10,7,6}},{{7,1,8}},
        {{3,9,4}},{{3,4,2}},{{3,2,6}},{{3,6,8}},{{3,8,9}},{{4,9,5}},{{2,4,11}},{{6,2,10}},{{8,6,7}},{{9,8,1}},
    }};

    const float crownScale = static_cast<float>(0.90 + ecologyUnit(seed + 4U) * 0.24);
    const glm::vec3 canopyCenter = base + up * (trunkHeight + 1.35F * crownScale);
    const glm::vec3 canopyExtent{2.85F * crownScale, 2.45F * crownScale, 2.55F * crownScale};
    constexpr std::array<glm::vec3, 6> lobeOffsets{{
        {0.0F, 0.0F, 0.40F}, {-0.92F, 0.10F, -0.08F}, {0.82F, -0.22F, 0.02F},
        {-0.18F, 0.86F, 0.10F}, {0.26F, -0.80F, -0.02F}, {0.02F, 0.04F, 1.06F},
    }};
    const glm::vec3 foliageDark{0.035F, 0.16F, 0.022F};
    const glm::vec3 foliageLight{0.12F, 0.42F, 0.055F};

    for (std::uint32_t lobe = 0; lobe < lobeOffsets.size(); ++lobe) {
        const float lobeScale = crownScale * static_cast<float>(0.92 + ecologyUnit(seed + 50U + lobe) * 0.20);
        const glm::vec3 lc = canopyCenter
            + east * (lobeOffsets[lobe].x * crownScale)
            + north * (lobeOffsets[lobe].y * crownScale)
            + up * (lobeOffsets[lobe].z * crownScale);
        const float rx = 1.62F * lobeScale;
        const float ry = 1.45F * lobeScale;
        const float rz = 1.36F * lobeScale;
        const std::uint32_t first = static_cast<std::uint32_t>(mesh.vertices.size());
        for (std::uint32_t i = 0; i < ico.size(); ++i) {
            const glm::vec3 unit = safeUnit(ico[i]);
            const glm::vec3 position = lc + east * (unit.x * rx) + north * (unit.y * ry) + up * (unit.z * rz);
            const glm::vec3 q = position - canopyCenter;
            const glm::vec3 transferred = safeUnit(
                east * (glm::dot(q, east) / (canopyExtent.x * canopyExtent.x))
                    + north * (glm::dot(q, north) / (canopyExtent.y * canopyExtent.y))
                    + up * (glm::dot(q, up) / (canopyExtent.z * canopyExtent.z)),
                up);
            const float height01 = std::clamp(0.5F + 0.5F * glm::dot(q, up) / canopyExtent.z, 0.0F, 1.0F);
            const float variation = static_cast<float>(0.72 + ecologyUnit(seed + 100U + lobe * 19U + i) * 0.28);
            const glm::vec3 color = glm::mix(foliageDark, foliageLight, 0.28F + height01 * 0.55F) * variation;
            mesh.vertices.push_back({position, transferred, color, {0.0F, 0.82F, 0.0F, kStreamingFoliageTag}});
        }
        for (const auto& face : faces) {
            ecologyTriangle(mesh, first + face[0], first + face[1], first + face[2]);
        }
    }
}

inline void appendStreamingEcology(
    PlanetMesh& mesh,
    const glm::dvec3& cameraSurfacePosition,
    const glm::dvec3& planetCenterSurface) {
    if (mesh.vertices.empty() || mesh.indices.empty()) return;
    const std::size_t sourceVertexCount = mesh.vertices.size();
    const glm::vec3 camera = glm::vec3(cameraSurfacePosition);
    const glm::vec3 planetCenter = glm::vec3(planetCenterSurface);
    const bool hasPlanetCenter = glm::dot(planetCenter, planetCenter) > 1.0e8F;
    std::unordered_set<std::uint64_t> occupiedTreeCells;
    std::unordered_set<std::uint64_t> occupiedRockCells;
    std::uint32_t treeCount = 0U;
    std::uint32_t rockCount = 0U;
    constexpr std::uint32_t maxTrees = 170U;
    constexpr std::uint32_t maxRocks = 260U;

    for (std::size_t i = 0; i < sourceVertexCount && (treeCount < maxTrees || rockCount < maxRocks); ++i) {
        const PlanetVertex& source = mesh.vertices[i];
        if (source.material.x < -0.5F || source.material.z > 0.02F) continue;
        // V14 tags submerged seafloor with roughness 0.96. Keep ecology strictly above water.
        if (source.material.y >= 0.955F) continue;
        const glm::vec3 delta = source.position - camera;
        const float horizontal2 = delta.x * delta.x + delta.z * delta.z;
        if (horizontal2 > 2400.0F * 2400.0F) continue;

        const glm::vec3 radial = hasPlanetCenter
            ? safeUnit(source.position - planetCenter, {0.0F, 1.0F, 0.0F})
            : glm::vec3{0.0F, 1.0F, 0.0F};
        const glm::vec3 normal = safeUnit(source.normal, radial);
        if (glm::dot(normal, radial) < 0.84F) continue;

        const std::int64_t cellX = static_cast<std::int64_t>(std::floor(source.position.x / 180.0F));
        const std::int64_t cellZ = static_cast<std::int64_t>(std::floor(source.position.z / 180.0F));
        const std::uint64_t cellSeed = ecologyMix64(
            static_cast<std::uint64_t>(cellX * 73856093LL) ^ static_cast<std::uint64_t>(cellZ * 19349663LL));
        const auto basis = ecologyFrame(normal);

        if (treeCount < maxTrees && occupiedTreeCells.insert(cellSeed).second && ecologyUnit(cellSeed + 11U) < 0.72) {
            const std::uint32_t copies = ecologyUnit(cellSeed + 12U) > 0.48 ? 2U : 1U;
            for (std::uint32_t k = 0; k < copies && treeCount < maxTrees; ++k) {
                const float angle = static_cast<float>(ecologyUnit(cellSeed + 20U + k) * 6.28318530718);
                const float radius = static_cast<float>(18.0 + ecologyUnit(cellSeed + 30U + k) * 72.0);
                const glm::vec3 offset = basis[0] * (std::cos(angle) * radius)
                    + basis[1] * (std::sin(angle) * radius);
                appendStreamingTree(mesh, source.position + offset, normal, cellSeed + 1000U + k * 97U);
                ++treeCount;
            }
        }

        if (rockCount < maxRocks && occupiedRockCells.insert(cellSeed ^ 0xA24BAED4963EE407ULL).second
            && ecologyUnit(cellSeed + 41U) < 0.86) {
            const std::uint32_t copies = 1U + static_cast<std::uint32_t>(ecologyUnit(cellSeed + 42U) * 3.0);
            for (std::uint32_t k = 0; k < copies && rockCount < maxRocks; ++k) {
                const float angle = static_cast<float>(ecologyUnit(cellSeed + 50U + k) * 6.28318530718);
                const float radius = static_cast<float>(10.0 + ecologyUnit(cellSeed + 60U + k) * 85.0);
                const glm::vec3 offset = basis[0] * (std::cos(angle) * radius)
                    + basis[1] * (std::sin(angle) * radius);
                const float size = static_cast<float>(0.35 + std::pow(ecologyUnit(cellSeed + 70U + k), 1.45) * 1.15);
                appendStreamingRock(mesh, source.position + offset, normal, cellSeed + 2000U + k * 131U, size);
                ++rockCount;
            }
        }
    }
}

} // namespace vf::detail
