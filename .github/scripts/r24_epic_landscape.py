from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:140]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# -----------------------------------------------------------------------------
# Gameplay-first planet scale: keep an Earth-sized globe, but deliberately make
# surface relief fantastical. Physics uses the same authoritative surface, so
# these are real 3-D collision/render heights rather than shader parallax.
# -----------------------------------------------------------------------------
main = "native/src/app/Main.cpp"
replace_once(main, "        planet.maxElevation = 8850.0;\n", "        planet.maxElevation = 30000.0;\n")
replace_once(main, "        planet.maxOceanDepthMeters = 11000.0;\n", "        planet.maxOceanDepthMeters = 24000.0;\n")
replace_once(main, "        planet.atmosphereHeight = 100000.0;\n", "        planet.atmosphereHeight = 180000.0;\n")

# Let evidence search explicitly find the deepest cavern-throat/sinkhole province.
replace_once(
    main,
    """            } else if (target == \"canyon\") {\n                score = terrain.canyon * 3.6 + terrain.aridity * 0.8 + terrain.hills * 0.5\n                    + height01 * 0.4;\n            } else if (target == \"coast\") {\n""",
    """            } else if (target == \"canyon\") {\n                score = terrain.canyon * 3.6 + terrain.aridity * 0.8 + terrain.hills * 0.5\n                    + height01 * 0.4;\n            } else if (target == \"abyss\") {\n                score = terrain.abyss * 6.2 + terrain.canyon * 1.1 + terrain.rift * 0.55\n                    + height01 * 0.35 - terrain.glacier * 0.55;\n            } else if (target == \"coast\") {\n""",
)

# A mega-abyss is viewed more downward so the throat/depth is readable; mountains stay low-angle
# so their silhouette dominates the horizon.
replace_once(
    main,
    """                if (target == \"mountain\") downwardWeight = 0.17;\n                else if (target == \"rift\") downwardWeight = 0.22;\n                else if (target == \"hydrology\" || target == \"river\") downwardWeight = 0.30;\n""",
    """                if (target == \"mountain\") downwardWeight = 0.10;\n                else if (target == \"rift\") downwardWeight = 0.18;\n                else if (target == \"abyss\") downwardWeight = 0.56;\n                else if (target == \"canyon\") downwardWeight = 0.38;\n                else if (target == \"hydrology\" || target == \"river\") downwardWeight = 0.27;\n""",
)

# Keep more surrounding massifs in the frame: the evidence tangent probe should see 36 km rather
# than just one local 18 km slope.
replace_once(
    main,
    "                constexpr double probeDistanceMeters = 18000.0;\n",
    "                constexpr double probeDistanceMeters = 36000.0;\n",
)

# Terrain streaming should allocate detail by actual projected error, not a centre-out DFS that
# exhausts its budget in one square. The builder patch below converts the scheduling to a global
# highest-error queue; these settings then provide a wide, gradual detail field.
replace_once(
    main,
    """            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 4400U\n                : (buildAltitude < 150000.0 ? 2200U : 900U);\n""",
    """            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 3600U\n                : (buildAltitude < 150000.0 ? 1900U : 850U);\n""",
)
replace_once(main, "            lodConfig.detailTransitionEndMeters = 32000.0;\n", "            lodConfig.detailTransitionEndMeters = 85000.0;\n")
replace_once(main, "            lodConfig.transitionFarCellMeters = 180.0;\n", "            lodConfig.transitionFarCellMeters = 420.0;\n")

# -----------------------------------------------------------------------------
# New normalized geomorph field exposed to materials, tests and evidence target selection.
# -----------------------------------------------------------------------------
header = "native/include/vf/world/PlanetSurface.hpp"
replace_once(
    header,
    """    double hills{};\n    double canyon{};\n    double dunes{};\n""",
    """    double hills{};\n    double canyon{};\n    // Gameplay-scale vertical cave throat / mega-sinkhole mask. This remains a normalized\n    // deterministic field; the physical depth is applied to authoritative 3-D surface geometry.\n    double abyss{};\n    double dunes{};\n""",
)

surface = "native/src/world/PlanetSurface.cpp"

# Extra medium-scale field for broken cirque/canyon rims and cavern throats.
replace_once(
    surface,
    """    const double canyonNoise = fbmSurface(definition.seed ^ 0x5BE0CD19137E2179ULL, w, 8200.0, 3);\n    const double duneNoise = fbmSurface(definition.seed ^ 0xCBBB9D5DC1059ED8ULL, w, 26000.0, 2);\n""",
    """    const double canyonNoise = fbmSurface(definition.seed ^ 0x5BE0CD19137E2179ULL, w, 8200.0, 3);\n    const double abyssNoise = fbmSurface(definition.seed ^ 0x243F6A8885A308D3ULL, w, 3600.0, 4);\n    const double duneNoise = fbmSurface(definition.seed ^ 0xCBBB9D5DC1059ED8ULL, w, 26000.0, 2);\n""",
)

# Add deterministic giant cavern throats. Seeded shafts are broad enough to survive LOD, while the
# canyon/rift component ensures the default planet always contains discoverable deep chasms on land.
replace_once(
    surface,
    """    const double canyon = smooth01(0.76, 0.965, canyonRidge)\n        * aridity\n        * landness\n        * elevatedInterior\n        * (1.0 - 0.48 * mountain)\n        * (1.0 - 0.55 * river);\n\n    // Dunes are low-relief and restricted to dry, non-mountainous low/intermediate land. The field\n""",
    """    const double canyon = smooth01(0.76, 0.965, canyonRidge)\n        * aridity\n        * landness\n        * elevatedInterior\n        * (1.0 - 0.48 * mountain)\n        * (1.0 - 0.55 * river);\n\n    double seededAbyss = 0.0;\n    for (std::uint64_t i = 0; i < 18U; ++i) {\n        const glm::dvec3 throat = seededDirection(\n            definition.seed ^ 0x13198A2E03707344ULL, 9000U + i * 31U);\n        const double width = 0.010 + 0.030 * seedUnit(\n            definition.seed ^ 0xA4093822299F31D0ULL, 9300U + i * 37U);\n        const double throatMask = smooth01(\n            std::cos(width * 2.8),\n            std::cos(width * 0.30),\n            glm::dot(d, throat));\n        seededAbyss = std::max(seededAbyss, std::pow(throatMask, 2.15));\n    }\n    const double fractureAbyss = smooth01(0.78, 0.985, canyonRidge)\n        * elevatedInterior * (0.42 + 0.58 * std::abs(abyssNoise));\n    const double riftAbyss = rift * (0.38 + 0.62 * std::abs(riftFaultFine));\n    const double abyss = std::clamp(\n        landness * std::max({seededAbyss, 0.82 * fractureAbyss, 0.62 * riftAbyss}),\n        0.0,\n        1.0);\n\n    // Dunes are low-relief and restricted to dry, non-mountainous low/intermediate land. The field\n""",
)

# Push the tectonic geometry into intentionally fantastical game scale. Broad uplift creates the
# massif; signed multi-frequency ridges create 5-12 km peak/valley differences inside it. Rifts,
# canyons and abyssal shafts get equally exaggerated negative relief.
replace_once(
    surface,
    """    elevation += maxLand * 0.170 * orogenyMask * alpineSignedRelief\n        * protectedDrainage * iceSmoothing;\n    elevation += maxLand * 0.070 * riftReliefMask * riftFaultProfile;\n    elevation -= maxLand * 0.045 * rift\n        * (0.50 + 0.50 * std::abs(riftFaultFine));\n""",
    """    const double epicOrogeny = std::clamp(\n        alpineSignedRelief + 0.42 * (1.0 - std::abs(orogenyFine)) - 0.18,\n        -1.25,\n        1.55);\n    elevation += maxLand * 0.420 * orogenyMask * epicOrogeny\n        * protectedDrainage * iceSmoothing;\n    elevation += maxLand * 0.165 * riftReliefMask * riftFaultProfile;\n    elevation -= maxLand * 0.145 * rift\n        * (0.50 + 0.50 * std::abs(riftFaultFine));\n""",
)
replace_once(
    surface,
    """    elevation -= maxLand * 0.020 * canyon * (0.55 + 0.45 * canyonRidge);\n    elevation += maxLand * 0.0016 * dunes * duneNoise;\n""",
    """    elevation -= maxLand * 0.105 * canyon * (0.45 + 0.55 * canyonRidge);\n    // Mega-abyss / cavern throats are deliberately beyond terrestrial scale. A strong throat can\n    // descend ten kilometres or more from its surrounding rim, producing a landmark visible from\n    // high-altitude flight. The smooth radial/noise mask avoids a hard circular cut.\n    elevation -= maxLand * 0.385 * abyss\n        * (0.62 + 0.38 * std::abs(abyssNoise));\n    elevation += maxLand * 0.0016 * dunes * duneNoise;\n""",
)

# Game-scale snow line: tall rock faces remain visible instead of every 10 km mountain becoming a
# featureless white sheet.
replace_once(
    surface,
    """    const double highIce = smooth01(3600.0, 5800.0, provisionalAboveSea)\n        * smooth01(0.36, 0.78, latitude);\n""",
    """    const double highIce = smooth01(12500.0, 22000.0, provisionalAboveSea)\n        * smooth01(0.36, 0.78, latitude);\n""",
)
replace_once(
    surface,
    """    sample.hills = hills;\n    sample.canyon = canyon;\n    sample.dunes = dunes;\n""",
    """    sample.hills = hills;\n    sample.canyon = canyon;\n    sample.abyss = abyss;\n    sample.dunes = dunes;\n""",
)
replace_once(
    surface,
    """    const double highland = smooth01(900.0, 3100.0, aboveSea);\n    const double alpine = smooth01(3000.0, 4700.0, aboveSea);\n""",
    """    const double highland = smooth01(2500.0, 9000.0, aboveSea);\n    const double alpine = smooth01(10500.0, 19000.0, aboveSea);\n""",
)

# -----------------------------------------------------------------------------
# Global-error-first quadtree refinement. This removes the old centre-first budget cliff that made
# one crisp square surrounded by suddenly coarse terrain.
# -----------------------------------------------------------------------------
lod = "native/src/world/PlanetLodMeshBuilder.cpp"
replace_once(lod, "#include <limits>\n#include <vector>\n", "#include <limits>\n#include <queue>\n#include <vector>\n")
replace_once(
    lod,
    """    std::vector<Node> pending;\n    pending.reserve(config.maxLeafPatches * 2U);\n    std::array<Node, 6> roots{};\n    for (std::uint32_t face = 0; face < roots.size(); ++face)\n        roots[face] = {face, 0U, -1.0, -1.0, 2.0};\n    std::sort(roots.begin(), roots.end(), [&](const Node& a, const Node& b) {\n        return approximateNodeDistance(a) > approximateNodeDistance(b);\n    });\n    for (const Node& root : roots) pending.push_back(root);\n\n    std::vector<Node> leaves;\n    leaves.reserve(config.maxLeafPatches);\n    while (!pending.empty()) {\n        const Node node = pending.back();\n        pending.pop_back();\n        const NodeMetric metric = metricFor(node, surface, cameraPlanetLocal, config);\n        ++localStats.evaluatedNodes;\n        localStats.maximumEstimatedErrorMeters = std::max(\n            localStats.maximumEstimatedErrorMeters,\n            metric.geometricErrorMeters);\n        if (!metric.aboveHorizon) continue;\n        const bool canSplit = node.depth < config.maxDepth\n            && leaves.size() + pending.size() + 4U < config.maxLeafPatches;\n        const double nodeCellMeters = metric.spanMeters\n            / static_cast<double>(std::max(2U, config.patchResolution));\n        bool forceSmoothDetail = false;\n        if (config.nearFieldRadiusMeters > 0.0) {\n            const double radius = std::max(1.0, surface.planet().radius);\n            const glm::dvec3 cameraDirection = safeNormalize(\n                cameraPlanetLocal, metric.centerDirection);\n            const double surfaceDistanceMeters = angleBetween(\n                cameraDirection, metric.centerDirection) * radius;\n            const double cameraAltitudeMeters = std::max(\n                0.0, glm::length(cameraPlanetLocal) - radius);\n            const double effectiveDistanceMeters = std::sqrt(\n                surfaceDistanceMeters * surfaceDistanceMeters\n                    + 0.20 * cameraAltitudeMeters * cameraAltitudeMeters);\n            const double transitionSpan = std::max(\n                1.0, config.detailTransitionEndMeters - config.detailTransitionStartMeters);\n            const double transitionT = smooth01(\n                (effectiveDistanceMeters - config.detailTransitionStartMeters) / transitionSpan);\n            const double nearCell = std::max(0.5, config.nearFieldCellMeters);\n            const double farCell = std::max(nearCell, config.transitionFarCellMeters);\n            const double desiredCellMeters = std::exp(\n                std::log(nearCell) * (1.0 - transitionT)\n                    + std::log(farCell) * transitionT);\n            forceSmoothDetail = effectiveDistanceMeters <= config.detailTransitionEndMeters\n                && nodeCellMeters > desiredCellMeters * 1.08;\n        }\n        if (canSplit && (forceSmoothDetail\n            || metric.screenErrorPixels > config.targetScreenErrorPixels)) {\n            const double half = node.size * 0.5;\n            const std::uint32_t depth = node.depth + 1U;\n            std::array<Node, 4> children{{\n                {node.face, depth, node.u0, node.v0, half},\n                {node.face, depth, node.u0 + half, node.v0, half},\n                {node.face, depth, node.u0, node.v0 + half, half},\n                {node.face, depth, node.u0 + half, node.v0 + half, half},\n            }};\n            std::sort(children.begin(), children.end(), [&](const Node& a, const Node& b) {\n                return approximateNodeDistance(a) > approximateNodeDistance(b);\n            });\n            for (const Node& child : children) pending.push_back(child);\n        } else {\n            leaves.push_back(node);\n        }\n    }\n""",
    """    struct Candidate {\n        Node node{};\n        double priority{};\n    };\n    struct CandidateLess {\n        bool operator()(const Candidate& a, const Candidate& b) const noexcept {\n            return a.priority < b.priority;\n        }\n    };\n\n    const auto priorityFor = [&](const Node& node) noexcept {\n        const NodeMetric metric = metricFor(node, surface, cameraPlanetLocal, config);\n        ++localStats.evaluatedNodes;\n        localStats.maximumEstimatedErrorMeters = std::max(\n            localStats.maximumEstimatedErrorMeters, metric.geometricErrorMeters);\n        if (!metric.aboveHorizon) return -1.0;\n\n        double priority = metric.screenErrorPixels\n            / std::max(0.001, config.targetScreenErrorPixels);\n        if (config.nearFieldRadiusMeters > 0.0) {\n            const double radius = std::max(1.0, surface.planet().radius);\n            const glm::dvec3 cameraDirection = safeNormalize(\n                cameraPlanetLocal, metric.centerDirection);\n            const double surfaceDistanceMeters = angleBetween(\n                cameraDirection, metric.centerDirection) * radius;\n            const double cameraAltitudeMeters = std::max(\n                0.0, glm::length(cameraPlanetLocal) - radius);\n            const double effectiveDistanceMeters = std::sqrt(\n                surfaceDistanceMeters * surfaceDistanceMeters\n                    + 0.20 * cameraAltitudeMeters * cameraAltitudeMeters);\n            const double transitionSpan = std::max(\n                1.0, config.detailTransitionEndMeters - config.detailTransitionStartMeters);\n            const double transitionT = smooth01(\n                (effectiveDistanceMeters - config.detailTransitionStartMeters) / transitionSpan);\n            const double nearCell = std::max(0.5, config.nearFieldCellMeters);\n            const double farCell = std::max(nearCell, config.transitionFarCellMeters);\n            const double desiredCellMeters = std::exp(\n                std::log(nearCell) * (1.0 - transitionT)\n                    + std::log(farCell) * transitionT);\n            const double nodeCellMeters = metric.spanMeters\n                / static_cast<double>(std::max(2U, config.patchResolution));\n            if (effectiveDistanceMeters <= config.detailTransitionEndMeters\n                && nodeCellMeters > desiredCellMeters * 1.08) {\n                priority = std::max(priority, 1.0 + nodeCellMeters / desiredCellMeters);\n            }\n        }\n        return priority;\n    };\n\n    std::priority_queue<Candidate, std::vector<Candidate>, CandidateLess> pending;\n    for (std::uint32_t face = 0; face < 6U; ++face) {\n        const Node root{face, 0U, -1.0, -1.0, 2.0};\n        const double priority = priorityFor(root);\n        if (priority >= 0.0) pending.push({root, priority});\n    }\n\n    std::vector<Node> leaves;\n    leaves.reserve(config.maxLeafPatches);\n    while (!pending.empty()) {\n        const Candidate candidate = pending.top();\n        pending.pop();\n        const Node node = candidate.node;\n        const bool wantsSplit = candidate.priority > 1.0 && node.depth < config.maxDepth;\n        const bool budgetAllowsSplit = leaves.size() + pending.size() + 4U\n            <= config.maxLeafPatches;\n        if (wantsSplit && budgetAllowsSplit) {\n            const double half = node.size * 0.5;\n            const std::uint32_t depth = node.depth + 1U;\n            const std::array<Node, 4> children{{\n                {node.face, depth, node.u0, node.v0, half},\n                {node.face, depth, node.u0 + half, node.v0, half},\n                {node.face, depth, node.u0, node.v0 + half, half},\n                {node.face, depth, node.u0 + half, node.v0 + half, half},\n            }};\n            for (const Node& child : children) {\n                const double priority = priorityFor(child);\n                if (priority >= 0.0) pending.push({child, priority});\n            }\n        } else {\n            leaves.push_back(node);\n        }\n    }\n""",
)

# -----------------------------------------------------------------------------
# Tests now use the same fantastical gameplay scale and hard-gate the requested spectacle.
# -----------------------------------------------------------------------------
test = "native/tests/TerrainLandformTests.cpp"
replace_once(test, "    planet.maxElevation = 8850.0;\n", "    planet.maxElevation = 30000.0;\n")
replace_once(test, "    planet.maxOceanDepthMeters = 11000.0;\n", "    planet.maxOceanDepthMeters = 24000.0;\n")
replace_once(test, "    double maxCanyon = 0.0;\n", "    double maxCanyon = 0.0;\n    double maxAbyss = 0.0;\n")
replace_once(
    test,
    """                    sample.hills, sample.canyon, sample.rift, sample.shear, sample.alluvialFan,\n""",
    """                    sample.hills, sample.canyon, sample.abyss, sample.rift, sample.shear, sample.alluvialFan,\n""",
)
replace_once(test, "                maxCanyon = std::max(maxCanyon, sample.canyon);\n", "                maxCanyon = std::max(maxCanyon, sample.canyon);\n                maxAbyss = std::max(maxAbyss, sample.abyss);\n")
replace_once(
    test,
    """    require(maxCanyon > 0.015, \"Earth seed must contain incised canyon terrain\");\n""",
    """    require(maxCanyon > 0.015, \"Earth seed must contain incised canyon terrain\");\n    require(maxAbyss > 0.10, \"gameplay planet must contain mega-abyss cave throats\");\n""",
)
replace_once(
    test,
    """    require(mountainLocalRelief > 850.0,\n        \"convergent mountain provinces must contain >850 m real 3-D relief within 28 km\");\n    require(riftLocalRelief > 260.0,\n        \"continental rifts must contain >260 m real 3-D fault relief within 24 km\");\n""",
    """    require(mountainLocalRelief > 4500.0,\n        \"epic convergent mountains must contain >4.5 km real 3-D relief within 28 km\");\n    require(riftLocalRelief > 1800.0,\n        \"epic continental rifts must contain >1.8 km real 3-D fault relief within 24 km\");\n    require(maxElevation > 15000.0,\n        \"gameplay-first planet must generate mountain summits above 15 km\");\n""",
)
replace_once(test, '              << " canyon=" << maxCanyon\n', '              << " canyon=" << maxCanyon\n              << " abyss=" << maxAbyss\n')

print("R24 epic landscape migration applied")
