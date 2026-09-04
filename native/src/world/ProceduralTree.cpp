#include "vf/world/detail/PlanetGenerationInternal.hpp"

#include <algorithm>
#include <array>
#include <cmath>

#include <glm/geometric.hpp>

namespace vf::detail {

[[nodiscard]] std::array<glm::dvec3, 2> branchFrame(const glm::dvec3& tangentInput) {
    const glm::dvec3 tangent = glm::normalize(tangentInput);
    const glm::dvec3 helper = std::abs(tangent.z) < 0.88
        ? glm::dvec3{0.0, 0.0, 1.0}
        : glm::dvec3{1.0, 0.0, 0.0};
    const glm::dvec3 u = glm::normalize(glm::cross(tangent, helper));
    const glm::dvec3 v = glm::normalize(glm::cross(tangent, u));
    return {u, v};
}

[[nodiscard]] unsigned nearestTrunkSector(
    const LocalMesh& mesh,
    const std::array<std::uint32_t, 8>& ring,
    const glm::dvec3& center,
    double angle) {
    const glm::dvec2 target{std::cos(angle), std::sin(angle)};
    double bestDot = -2.0;
    unsigned best = 0U;
    for (unsigned q = 0; q < 8U; ++q) {
        const glm::dvec3 a = mesh.vertices[ring[q]].position - center;
        const glm::dvec3 b = mesh.vertices[ring[(q + 1U) % 8U]].position - center;
        glm::dvec2 mid{a.x + b.x, a.y + b.y};
        const double lengthSquared = glm::dot(mid, mid);
        if (lengthSquared > 1.0e-12) mid /= std::sqrt(lengthSquared);
        const double alignment = glm::dot(mid, target);
        if (alignment > bestDot) {
            bestDot = alignment;
            best = q;
        }
    }
    return best;
}

struct RingOrder {
    bool reverse{false};
    unsigned shift{0U};
};

[[nodiscard]] RingOrder findBranchRingOrder(
    const std::array<glm::dvec3, 4>& ring,
    const std::array<glm::dvec3, 4>& base) {
    double bestCost = 1.0e100;
    RingOrder best{};
    for (unsigned reverse = 0; reverse < 2U; ++reverse) {
        for (unsigned shift = 0; shift < 4U; ++shift) {
            double cost = 0.0;
            for (unsigned k = 0; k < 4U; ++k) {
                const unsigned source = reverse != 0U
                    ? (3U + shift - k) % 4U
                    : (k + shift) % 4U;
                const glm::dvec3 delta = ring[source] - base[k];
                cost += glm::dot(delta, delta);
            }
            if (cost < bestCost) {
                bestCost = cost;
                best.reverse = reverse != 0U;
                best.shift = shift;
            }
        }
    }
    return best;
}

[[nodiscard]] std::array<glm::dvec3, 4> applyRingOrder(
    const std::array<glm::dvec3, 4>& ring,
    const RingOrder& order) {
    std::array<glm::dvec3, 4> result{};
    for (unsigned k = 0; k < 4U; ++k) {
        const unsigned source = order.reverse
            ? (3U + order.shift - k) % 4U
            : (k + order.shift) % 4U;
        result[k] = ring[source];
    }
    return result;
}

struct TreeRecipe {
    double trunkHeight{5.0};
    double trunkRadius{0.50};
    double crownScale{1.0};
    double branchLengthScale{1.0};
    double branchRadiusScale{1.0};
    double wobble{0.06};
    double twist{0.0};
};

[[nodiscard]] TreeRecipe treeRecipe(std::uint64_t seed) noexcept {
    TreeRecipe recipe{};
    const double maturity = 0.88 + random01(seed, 1U) * 0.34;
    recipe.trunkHeight = 4.45 * maturity * (0.94 + random01(seed, 2U) * 0.12);
    recipe.trunkRadius = 0.46 * (0.90 + random01(seed, 3U) * 0.24) * std::sqrt(maturity);
    recipe.crownScale = 0.90 + random01(seed, 4U) * 0.24;
    recipe.branchLengthScale = 0.86 + random01(seed, 5U) * 0.28;
    recipe.branchRadiusScale = 0.92 + random01(seed, 6U) * 0.20;
    recipe.wobble = 0.035 + random01(seed, 7U) * 0.055;
    recipe.twist = seedPhase(seed, 8U);
    return recipe;
}

[[nodiscard]] LocalMesh buildStylizedTree(std::uint64_t seed) {
    const TreeRecipe recipe = treeRecipe(seed);
    LocalMesh tree;

    constexpr std::array<double, 9> kTrunkT{
        0.00, 0.09, 0.22, 0.38, 0.54, 0.68, 0.80, 0.91, 1.00,
    };
    constexpr std::array<double, 9> kRadiusRatio{
        1.00, 0.88, 0.74, 0.64, 0.56, 0.49, 0.42, 0.35, 0.27,
    };

    std::array<std::array<std::uint32_t, 8>, 9> trunkRings{};
    std::array<glm::dvec3, 9> trunkCenters{};
    const double phase0 = seedPhase(seed, 20U);
    const double phase1 = seedPhase(seed, 21U);

    for (unsigned ringIndex = 0; ringIndex < trunkRings.size(); ++ringIndex) {
        const double t = kTrunkT[ringIndex];
        const double height = recipe.trunkHeight * t;
        const double centerX = recipe.wobble * std::sin(phase0 + t * 4.1) * (0.35 + 0.65 * t);
        const double centerY = recipe.wobble * std::sin(phase1 + t * 3.3) * (0.35 + 0.65 * t);
        trunkCenters[ringIndex] = {centerX, centerY, height};
        const double radius = recipe.trunkRadius * kRadiusRatio[ringIndex];
        const double ringTwist = recipe.twist * 0.08 + t * (0.20 + randomSigned(seed, 22U) * 0.08);

        for (unsigned q = 0; q < 8U; ++q) {
            const double angle = kTau * static_cast<double>(q) / 8.0 + ringTwist;
            const double facetVariation = 1.0 + 0.035 * std::sin(
                static_cast<double>(q) * 2.17 + static_cast<double>(ringIndex) * 0.73 + phase0);
            const glm::dvec3 position = trunkCenters[ringIndex] + glm::dvec3{
                std::cos(angle) * radius * facetVariation,
                std::sin(angle) * radius * facetVariation,
                0.0,
            };
            tree.vertices.push_back({
                position,
                {kBarkMaterialMarker, static_cast<float>(static_cast<double>(q) / 8.0), static_cast<float>(height)},
            });
            trunkRings[ringIndex][q] = static_cast<std::uint32_t>(tree.vertices.size() - 1U);
        }
    }

    constexpr std::array<unsigned, 3> kAttachIntervals{4U, 5U, 6U};
    constexpr std::array<double, 3> kBaseAngles{3.72, 0.44, 2.20};
    constexpr std::array<double, 3> kLengthRatios{0.31, 0.28, 0.24};
    constexpr std::array<double, 3> kUpBias{0.48, 0.56, 0.64};

    std::array<unsigned, 3> attachmentSectors{};
    for (unsigned branch = 0; branch < 3U; ++branch) {
        const double angle = kBaseAngles[branch] + randomSigned(seed, 40U + branch) * 0.18;
        attachmentSectors[branch] = nearestTrunkSector(
            tree,
            trunkRings[kAttachIntervals[branch]],
            trunkCenters[kAttachIntervals[branch]],
            angle);
    }

    // The parent trunk stays one continuous skin. Each side branch owns one local opening in that
    // skin and stitches its collar directly to the four shared opening vertices: no intersecting
    // branch cylinders, no boolean union and no high-poly remesh/decimation pass.
    for (unsigned interval = 0; interval + 1U < trunkRings.size(); ++interval) {
        for (unsigned q = 0; q < 8U; ++q) {
            bool openedForBranch = false;
            for (unsigned branch = 0; branch < 3U; ++branch) {
                if (kAttachIntervals[branch] == interval && attachmentSectors[branch] == q) {
                    openedForBranch = true;
                    break;
                }
            }
            if (openedForBranch) continue;
            const auto& a = trunkRings[interval];
            const auto& b = trunkRings[interval + 1U];
            const unsigned q1 = (q + 1U) % 8U;
            appendQuadBest(tree, a[q], a[q1], b[q1], b[q]);
        }
    }

    const std::uint32_t bottomCenter = static_cast<std::uint32_t>(tree.vertices.size());
    tree.vertices.push_back({{0.0, 0.0, -0.035}, {kBarkMaterialMarker, 0.0F, -0.035F}});
    for (unsigned q = 0; q < 8U; ++q) {
        appendTriangle(tree, bottomCenter, trunkRings[0][(q + 1U) % 8U], trunkRings[0][q]);
    }

    const std::uint32_t topCenter = static_cast<std::uint32_t>(tree.vertices.size());
    tree.vertices.push_back({trunkCenters.back(), {kBarkMaterialMarker, 0.0F, static_cast<float>(recipe.trunkHeight)}});
    for (unsigned q = 0; q < 8U; ++q) {
        appendTriangle(tree, topCenter, trunkRings.back()[q], trunkRings.back()[(q + 1U) % 8U]);
    }

    std::array<glm::dvec3, 3> branchTips{};
    for (unsigned branch = 0; branch < 3U; ++branch) {
        const unsigned interval = kAttachIntervals[branch];
        const unsigned q = attachmentSectors[branch];
        const unsigned q1 = (q + 1U) % 8U;
        const auto& lowerRing = trunkRings[interval];
        const auto& upperRing = trunkRings[interval + 1U];
        const std::array<std::uint32_t, 4> baseIds{
            lowerRing[q], lowerRing[q1], upperRing[q1], upperRing[q],
        };
        std::array<glm::dvec3, 4> basePoints{};
        glm::dvec3 baseCenter{0.0};
        for (unsigned k = 0; k < 4U; ++k) {
            basePoints[k] = tree.vertices[baseIds[k]].position;
            baseCenter += basePoints[k];
        }
        baseCenter *= 0.25;

        const double angle = kBaseAngles[branch] + randomSigned(seed, 40U + branch) * 0.18;
        const double length = recipe.trunkHeight * kLengthRatios[branch]
            * recipe.branchLengthScale * (0.90 + random01(seed, 50U + branch) * 0.18);
        const double upBias = kUpBias[branch] + randomSigned(seed, 60U + branch) * 0.055;
        const glm::dvec3 horizontal{std::cos(angle), std::sin(angle), 0.0};
        const glm::dvec3 lateral{-horizontal.y, horizontal.x, 0.0};
        const double lateralBend = randomSigned(seed, 70U + branch) * length * 0.08;

        const double parentRadius = recipe.trunkRadius * kRadiusRatio[interval];
        const double rootRadius = parentRadius
            * (0.61 - static_cast<double>(branch) * 0.035)
            * recipe.branchRadiusScale;
        constexpr std::array<double, 6> kBranchT{0.07, 0.22, 0.40, 0.60, 0.79, 0.94};
        constexpr std::array<double, 6> kBranchRadius{1.00, 0.87, 0.70, 0.55, 0.41, 0.30};
        std::array<std::array<std::uint32_t, 4>, 6> branchRings{};
        std::array<glm::dvec3, 6> branchCenters{};
        for (unsigned ringIndex = 0; ringIndex < branchCenters.size(); ++ringIndex) {
            const double t = kBranchT[ringIndex];
            const double travel = length * t;
            const double rise = length * upBias * (0.54 * t + 0.46 * t * t);
            const double side = lateralBend * std::sin(kPi * t);
            branchCenters[ringIndex] = baseCenter
                + horizontal * travel + lateral * side + glm::dvec3{0.0, 0.0, rise};
        }

        RingOrder ringOrder{};
        bool ringOrderInitialized = false;
        for (unsigned ringIndex = 0; ringIndex < branchRings.size(); ++ringIndex) {
            const double t = kBranchT[ringIndex];
            const double travel = length * t;
            glm::dvec3 tangent{};
            if (ringIndex == 0U) tangent = branchCenters[1U] - branchCenters[0U];
            else if (ringIndex + 1U == branchRings.size()) tangent = branchCenters[ringIndex] - branchCenters[ringIndex - 1U];
            else tangent = branchCenters[ringIndex + 1U] - branchCenters[ringIndex - 1U];

            const auto axes = branchFrame(tangent);
            std::array<glm::dvec3, 4> rawRing{};
            const double ringRadius = rootRadius * kBranchRadius[ringIndex];
            for (unsigned k = 0; k < 4U; ++k) {
                const double ringAngle = kTau * static_cast<double>(k) / 4.0
                    + 0.16 + static_cast<double>(branch) * 0.09;
                const double facet = 1.0 + 0.035 * std::sin(
                    static_cast<double>(k) * 1.91 + static_cast<double>(ringIndex) * 0.61 + phase1);
                rawRing[k] = branchCenters[ringIndex]
                    + axes[0] * (std::cos(ringAngle) * ringRadius * facet)
                    + axes[1] * (std::sin(ringAngle) * ringRadius * facet);
            }
            if (!ringOrderInitialized) {
                ringOrder = findBranchRingOrder(rawRing, basePoints);
                ringOrderInitialized = true;
            }
            const auto ringPoints = applyRingOrder(rawRing, ringOrder);
            for (unsigned k = 0; k < 4U; ++k) {
                tree.vertices.push_back({
                    ringPoints[k],
                    {kBarkMaterialMarker, static_cast<float>(static_cast<double>(k) / 4.0),
                     static_cast<float>(recipe.trunkHeight * kTrunkT[interval] + travel)},
                });
                branchRings[ringIndex][k] = static_cast<std::uint32_t>(tree.vertices.size() - 1U);
            }
        }

        for (unsigned k = 0; k < 4U; ++k) {
            const unsigned k1 = (k + 1U) % 4U;
            appendQuadBest(tree, baseIds[k], baseIds[k1], branchRings[0][k1], branchRings[0][k]);
        }
        for (unsigned ringIndex = 0; ringIndex + 1U < branchRings.size(); ++ringIndex) {
            for (unsigned k = 0; k < 4U; ++k) {
                const unsigned k1 = (k + 1U) % 4U;
                appendQuadBest(tree,
                    branchRings[ringIndex][k], branchRings[ringIndex][k1],
                    branchRings[ringIndex + 1U][k1], branchRings[ringIndex + 1U][k]);
            }
        }

        branchTips[branch] = baseCenter + horizontal * length + lateral * 0.10 * lateralBend
            + glm::dvec3{0.0, 0.0, length * upBias};
        const std::uint32_t tipIndex = static_cast<std::uint32_t>(tree.vertices.size());
        tree.vertices.push_back({branchTips[branch], {kBarkMaterialMarker, 0.0F,
            static_cast<float>(recipe.trunkHeight + length)}});
        for (unsigned k = 0; k < 4U; ++k) {
            appendTriangle(tree, tipIndex, branchRings.back()[k], branchRings.back()[(k + 1U) % 4U]);
        }
    }

    // Six overlapping 20-triangle crown masses. Branch tips are intentionally buried inside the
    // canopy so the tree reads as a compact stylized broadleaf instead of thin bare whips.
    constexpr double phi = 1.6180339887498948482;
    const std::array<glm::dvec3, 12> icoBase{
        glm::dvec3{-1.0, phi, 0.0}, glm::dvec3{1.0, phi, 0.0},
        glm::dvec3{-1.0, -phi, 0.0}, glm::dvec3{1.0, -phi, 0.0},
        glm::dvec3{0.0, -1.0, phi}, glm::dvec3{0.0, 1.0, phi},
        glm::dvec3{0.0, -1.0, -phi}, glm::dvec3{0.0, 1.0, -phi},
        glm::dvec3{phi, 0.0, -1.0}, glm::dvec3{phi, 0.0, 1.0},
        glm::dvec3{-phi, 0.0, -1.0}, glm::dvec3{-phi, 0.0, 1.0},
    };
    constexpr std::array<std::array<unsigned, 3>, 20> icoFaces{{
        {{0, 11, 5}}, {{0, 5, 1}}, {{0, 1, 7}}, {{0, 7, 10}}, {{0, 10, 11}},
        {{1, 5, 9}}, {{5, 11, 4}}, {{11, 10, 2}}, {{10, 7, 6}}, {{7, 1, 8}},
        {{3, 9, 4}}, {{3, 4, 2}}, {{3, 2, 6}}, {{3, 6, 8}}, {{3, 8, 9}},
        {{4, 9, 5}}, {{2, 4, 11}}, {{6, 2, 10}}, {{8, 6, 7}}, {{9, 8, 1}},
    }};

    std::array<glm::dvec3, 6> crownCenters{
        branchTips[0] * 0.88 + trunkCenters[7] * 0.12 + glm::dvec3{0.0, 0.0, 0.34},
        branchTips[1] * 0.88 + trunkCenters[7] * 0.12 + glm::dvec3{0.0, 0.0, 0.38},
        branchTips[2] * 0.88 + trunkCenters[7] * 0.12 + glm::dvec3{0.0, 0.0, 0.40},
        trunkCenters[7] + glm::dvec3{0.20, -0.12, recipe.trunkHeight * 0.12},
        trunkCenters[8] + glm::dvec3{-0.34, 0.15, recipe.trunkHeight * 0.09},
        trunkCenters[8] + glm::dvec3{0.35, 0.10, recipe.trunkHeight * 0.06},
    };

    for (unsigned cluster = 0; cluster < crownCenters.size(); ++cluster) {
        crownCenters[cluster].x += randomSigned(seed, 100U + cluster * 3U + 0U) * 0.18;
        crownCenters[cluster].y += randomSigned(seed, 100U + cluster * 3U + 1U) * 0.18;
        crownCenters[cluster].z += randomSigned(seed, 100U + cluster * 3U + 2U) * 0.12;
        const double baseRadius = recipe.trunkHeight * 0.235 * recipe.crownScale;
        const glm::dvec3 scale{
            baseRadius * (0.92 + random01(seed, 140U + cluster * 3U + 0U) * 0.22),
            baseRadius * (0.82 + random01(seed, 140U + cluster * 3U + 1U) * 0.22),
            baseRadius * (0.70 + random01(seed, 140U + cluster * 3U + 2U) * 0.18),
        };
        const std::uint32_t base = static_cast<std::uint32_t>(tree.vertices.size());
        for (unsigned i = 0; i < icoBase.size(); ++i) {
            const glm::dvec3 unit = glm::normalize(icoBase[i]);
            const double irregularity = 0.94 + random01(seed, 180U + cluster * 17U + i) * 0.13;
            glm::dvec3 p = crownCenters[cluster] + glm::dvec3{
                unit.x * scale.x * irregularity,
                unit.y * scale.y * irregularity,
                unit.z * scale.z * irregularity,
            };
            if (unit.z < 0.0) p.z -= baseRadius * 0.06;
            tree.vertices.push_back({
                p,
                {kFoliageMaterialMarker, static_cast<float>(random01(seed, 220U + cluster)),
                 static_cast<float>(unit.z * 0.5 + 0.5)},
            });
        }
        for (const auto& face : icoFaces) {
            appendTriangle(tree, base + face[0], base + face[1], base + face[2]);
        }
    }

    return tree;
}

} // namespace vf::detail
