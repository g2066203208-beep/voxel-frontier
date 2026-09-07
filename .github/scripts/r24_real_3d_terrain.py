from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


surface = "native/src/world/PlanetSurface.cpp"

# Real kilometre-scale mountain and rift geometry. The old terrain had high absolute elevation but
# only a few hundred metres of relief over tens of kilometres, so it read as a raised plain. Keep
# plate convergence/divergence as the causal mask, then add nested ridged fields at ~8-75 km scales
# so the authoritative radial height itself contains peaks, saddles, valleys and fault scarps.
replace_once(
    surface,
    """    const double local = fbmSurface(definition.seed ^ 0xBB67AE8584CAA73BULL, w, 3200.0, 3);\n    const double canyonNoise = fbmSurface(definition.seed ^ 0x5BE0CD19137E2179ULL, w, 8200.0, 3);\n    const double duneNoise = fbmSurface(definition.seed ^ 0xCBBB9D5DC1059ED8ULL, w, 26000.0, 2);\n    const double micro = fbmSurface(definition.seed ^ 0x3C6EF372FE94F82BULL, w, 52000.0, 2);\n    const double fine = fbmSurface(definition.seed ^ 0xA54FF53A5F1D36F1ULL, w, 125000.0, 2);\n""",
    """    const double local = fbmSurface(definition.seed ^ 0xBB67AE8584CAA73BULL, w, 3200.0, 3);\n    const double canyonNoise = fbmSurface(definition.seed ^ 0x5BE0CD19137E2179ULL, w, 8200.0, 3);\n    const double duneNoise = fbmSurface(definition.seed ^ 0xCBBB9D5DC1059ED8ULL, w, 26000.0, 2);\n    const double micro = fbmSurface(definition.seed ^ 0x3C6EF372FE94F82BULL, w, 52000.0, 2);\n    const double fine = fbmSurface(definition.seed ^ 0xA54FF53A5F1D36F1ULL, w, 125000.0, 2);\n\n    // Orogenic/fault morphology uses separate deterministic bands rather than reusing the tiny\n    // material-detail amplitudes below. On an Earth-size sphere these frequencies correspond to\n    // broad mountain massifs (~75 km), primary ridges (~26 km), secondary ridges (~8.5 km), and\n    // rift scarps in the same human-visible range. They displace the same authoritative geometry\n    // consumed by collision, ecology and rendering; this is not normal-map or colour-only detail.\n    const double orogenyBroad = fbmSurface(\n        definition.seed ^ 0x9B05688C2B3E6C1FULL, w, 540.0, 4);\n    const double orogenyRidge = fbmSurface(\n        definition.seed ^ 0x1D9ABF5A7C4E21B3ULL, w, 1550.0, 4);\n    const double orogenyFine = fbmSurface(\n        definition.seed ^ 0xC13FA9A902A6328FULL, w, 4700.0, 3);\n    const double riftFault = fbmSurface(\n        definition.seed ^ 0x91E10DA5C79E7B1DULL, w, 1800.0, 3);\n    const double riftFaultFine = fbmSurface(\n        definition.seed ^ 0xD192E819D6EF5218ULL, w, 5200.0, 3);\n""",
)

replace_once(
    surface,
    """    const double ridged = 1.0 - std::abs(local);\n    const double protectedDrainage = 1.0 - 0.74 * river;\n    const double iceSmoothing = 1.0 - 0.62 * glacier;\n    const double landRelief = (\n        regional * (0.0085 + 0.0180 * mountain + 0.0048 * plateau)\n        + hillNoise * (0.0042 * hills)\n        + local * (0.0031 + 0.0100 * mountain + 0.0014 * coastalCliff)\n        + micro * (0.00115 + 0.00120 * mountain)\n        + fine * 0.00030\n        + (ridged - 0.5) * 0.0052 * mountain)\n        * protectedDrainage * iceSmoothing;\n    elevation += maxLand * landRelief * landness;\n    elevation += maxOcean * (regional * 0.0028 + local * 0.0010) * oceanness;\n""",
    """    const double ridged = 1.0 - std::abs(local);\n    const double protectedDrainage = 1.0 - 0.74 * river;\n    const double iceSmoothing = 1.0 - 0.62 * glacier;\n\n    // A convergent plate boundary must produce relief, not merely altitude. Convert nested FBM into\n    // a ridged multifractal-like signed profile: narrow high crests, broad saddles and carved\n    // intermontane valleys. The amplitude is intentionally kilometre-scale inside strong orogeny\n    // but fades continuously to zero away from convergent continental boundaries.\n    const double orogenySignal = std::clamp(\n        0.68 * orogenyRidge + 0.32 * orogenyFine, -1.0, 1.0);\n    const double alpineRidge = std::pow(\n        std::clamp(1.0 - std::abs(orogenySignal), 0.0, 1.0), 1.50);\n    const double alpineValley = std::pow(\n        std::clamp(std::abs(orogenySignal) - 0.16, 0.0, 1.0), 1.35);\n    const double orogenyMask = smooth01(0.035, 0.62, mountain);\n    const double alpineSignedRelief =\n        1.28 * alpineRidge - 0.50 - 0.24 * alpineValley\n        + 0.24 * orogenyBroad + 0.14 * orogenyFine;\n\n    // Divergent continental boundaries receive a separate fault-block profile. This creates real\n    // graben/horst relief at 8-25 km scales on top of the broad rift depression and shoulders.\n    const double riftFaultRidge = std::pow(\n        std::clamp(1.0 - std::abs(riftFault), 0.0, 1.0), 1.45);\n    const double riftFaultProfile =\n        (riftFaultRidge - 0.46) + 0.24 * riftFaultFine;\n    const double riftReliefMask = smooth01(0.025, 0.52, plates.divergence * landness);\n\n    const double landRelief = (\n        regional * (0.0085 + 0.0180 * mountain + 0.0048 * plateau)\n        + hillNoise * (0.0042 * hills)\n        + local * (0.0031 + 0.0100 * mountain + 0.0014 * coastalCliff)\n        + micro * (0.00115 + 0.00120 * mountain)\n        + fine * 0.00030\n        + (ridged - 0.5) * 0.0052 * mountain)\n        * protectedDrainage * iceSmoothing;\n    elevation += maxLand * landRelief * landness;\n    elevation += maxLand * 0.170 * orogenyMask * alpineSignedRelief\n        * protectedDrainage * iceSmoothing;\n    elevation += maxLand * 0.070 * riftReliefMask * riftFaultProfile;\n    elevation -= maxLand * 0.045 * rift\n        * (0.50 + 0.50 * std::abs(riftFaultFine));\n    elevation += maxOcean * (regional * 0.0028 + local * 0.0010) * oceanness;\n""",
)

main = "native/src/app/Main.cpp"

# Evidence target selection now explicitly prefers local geometric relief. A 6.5-km-high plateau is
# no longer allowed to win the mountain target merely because its mountain mask is high.
replace_once(
    main,
    """            const double height01 = std::clamp(aboveSea / std::max(1.0, planet.maxElevation), 0.0, 1.0);\n            double score = -1.0e9;\n            if (target == \"mountain\") {\n                score = terrain.mountain * 4.4\n                    + (1.0 - std::abs(height01 - 0.38)) * 1.25\n                    + terrain.plateBoundary * 0.35\n                    - terrain.glacier * 2.8\n                    - std::max(0.0, height01 - 0.65) * 2.4\n                    - std::abs(d.y) * 0.45;\n            } else if (target == \"rift\") {\n                score = terrain.rift * 4.8 + terrain.divergence * 1.35\n                    + terrain.plateBoundary * 0.55 + height01 * 0.25\n                    - terrain.glacier * 1.4 - terrain.mountain * 0.45;\n""",
    """            const double height01 = std::clamp(aboveSea / std::max(1.0, planet.maxElevation), 0.0, 1.0);\n            double localReliefMeters = 0.0;\n            const bool needsReliefProbe =\n                (target == \"mountain\" && terrain.mountain > 0.16)\n                || (target == \"rift\" && terrain.rift > 0.015);\n            if (needsReliefProbe) {\n                const glm::dvec3 tangentA = stableTangent(d);\n                const glm::dvec3 tangentB = safeNormalize(\n                    glm::cross(d, tangentA), stableTangent(d));\n                constexpr double reliefProbeDistanceMeters = 18000.0;\n                constexpr int reliefProbeDirections = 8;\n                for (int probeIndex = 0; probeIndex < reliefProbeDirections; ++probeIndex) {\n                    const double probeAngle = 2.0 * kPi * static_cast<double>(probeIndex)\n                        / static_cast<double>(reliefProbeDirections);\n                    const glm::dvec3 probeTangent = safeNormalize(\n                        tangentA * std::cos(probeAngle) + tangentB * std::sin(probeAngle),\n                        tangentA);\n                    const glm::dvec3 probeDirection = safeNormalize(\n                        d + probeTangent * (reliefProbeDistanceMeters / planet.radius), d);\n                    const double probeElevation = vf::samplePlanetTerrain(\n                        planet, probeDirection).elevationMeters;\n                    localReliefMeters = std::max(\n                        localReliefMeters, std::abs(probeElevation - terrain.elevationMeters));\n                }\n            }\n\n            double score = -1.0e9;\n            if (target == \"mountain\") {\n                const double reliefScore = std::clamp(localReliefMeters / 900.0, 0.0, 2.8);\n                score = terrain.mountain * 3.4 + reliefScore * 2.3\n                    + terrain.plateBoundary * 0.30\n                    - terrain.glacier * 2.6\n                    - std::max(0.0, height01 - 0.78) * 2.0\n                    - std::abs(d.y) * 0.35;\n            } else if (target == \"rift\") {\n                const double reliefScore = std::clamp(localReliefMeters / 420.0, 0.0, 2.6);\n                score = terrain.rift * 3.7 + terrain.divergence * 1.10\n                    + reliefScore * 2.0 + terrain.plateBoundary * 0.35\n                    - terrain.glacier * 1.2 - terrain.mountain * 0.35;\n""",
)

replace_once(
    main,
    """                if (target == \"mountain\") downwardWeight = 0.27;\n                else if (target == \"rift\") downwardWeight = 0.31;\n                else if (target == \"hydrology\" || target == \"river\") downwardWeight = 0.38;\n""",
    """                if (target == \"mountain\") downwardWeight = 0.17;\n                else if (target == \"rift\") downwardWeight = 0.22;\n                else if (target == \"hydrology\" || target == \"river\") downwardWeight = 0.30;\n""",
)

# Add a hard numerical regression gate. The test samples a ring around the best non-glaciated
# convergent/rift province and requires actual peak-valley elevation range, not just masks.
test = "native/tests/TerrainLandformTests.cpp"
replace_once(
    test,
    """#include <iostream>\n""",
    """#include <iostream>\n\n#include <glm/geometric.hpp>\n""",
)
replace_once(
    test,
    """    bool sawLand = false;\n    bool sawOcean = false;\n""",
    """    bool sawLand = false;\n    bool sawOcean = false;\n    glm::dvec3 mountainProbeDirection{0.0, 1.0, 0.0};\n    glm::dvec3 riftProbeDirection{0.0, 1.0, 0.0};\n    double mountainProbeScore = -1.0e30;\n    double riftProbeScore = -1.0e30;\n""",
)
replace_once(
    test,
    """                const auto sample = vf::samplePlanetTerrain(planet, vf::cubeSphereDirection(face, u, v));\n""",
    """                const glm::dvec3 direction = vf::cubeSphereDirection(face, u, v);\n                const auto sample = vf::samplePlanetTerrain(planet, direction);\n""",
)
replace_once(
    test,
    """                sawLand = sawLand || sample.elevationMeters > 100.0;\n                sawOcean = sawOcean || sample.elevationMeters < -500.0;\n""",
    """                sawLand = sawLand || sample.elevationMeters > 100.0;\n                sawOcean = sawOcean || sample.elevationMeters < -500.0;\n\n                if (sample.elevationMeters > 150.0 && sample.glacier < 0.55) {\n                    const double mountainScore = sample.mountain * 2.0\n                        + sample.convergence * 0.55\n                        - sample.glacier * 0.80\n                        - std::max(0.0, (sample.elevationMeters - 8000.0) / 2000.0);\n                    if (mountainScore > mountainProbeScore) {\n                        mountainProbeScore = mountainScore;\n                        mountainProbeDirection = direction;\n                    }\n                    const double riftScore = sample.rift * 2.0 + sample.divergence * 0.65\n                        - sample.mountain * 0.30;\n                    if (riftScore > riftProbeScore) {\n                        riftProbeScore = riftScore;\n                        riftProbeDirection = direction;\n                    }\n                }\n""",
)
replace_once(
    test,
    """    require(maxElevation <= planet.maxElevation + 1.0e-6,\n        \"new landforms must respect configured elevation clamp\");\n\n    std::cout << \"Terrain landform tests passed\"\n""",
    """    require(maxElevation <= planet.maxElevation + 1.0e-6,\n        \"new landforms must respect configured elevation clamp\");\n\n    const auto localRelief = [&](const glm::dvec3& centerInput, double radiusMeters) {\n        const glm::dvec3 center = glm::normalize(centerInput);\n        const glm::dvec3 reference = std::abs(center.y) < 0.88\n            ? glm::dvec3{0.0, 1.0, 0.0}\n            : glm::dvec3{1.0, 0.0, 0.0};\n        const glm::dvec3 tangent = glm::normalize(glm::cross(reference, center));\n        const glm::dvec3 bitangent = glm::normalize(glm::cross(center, tangent));\n        double localMin = vf::samplePlanetTerrain(planet, center).elevationMeters;\n        double localMax = localMin;\n        constexpr int azimuthSamples = 32;\n        for (int ring = 1; ring <= 3; ++ring) {\n            const double ringRadius = radiusMeters * static_cast<double>(ring) / 3.0;\n            for (int i = 0; i < azimuthSamples; ++i) {\n                const double angle = 6.28318530717958647692 * static_cast<double>(i)\n                    / static_cast<double>(azimuthSamples);\n                const glm::dvec3 outward = tangent * std::cos(angle)\n                    + bitangent * std::sin(angle);\n                const glm::dvec3 direction = glm::normalize(\n                    center + outward * (ringRadius / planet.radius));\n                const double elevation = vf::samplePlanetTerrain(planet, direction).elevationMeters;\n                localMin = std::min(localMin, elevation);\n                localMax = std::max(localMax, elevation);\n            }\n        }\n        return localMax - localMin;\n    };\n\n    const double mountainLocalRelief = localRelief(mountainProbeDirection, 28000.0);\n    const double riftLocalRelief = localRelief(riftProbeDirection, 24000.0);\n    require(mountainLocalRelief > 850.0,\n        \"convergent mountain provinces must contain >850 m real 3-D relief within 28 km\");\n    require(riftLocalRelief > 260.0,\n        \"continental rifts must contain >260 m real 3-D fault relief within 24 km\");\n\n    std::cout << \"Terrain landform tests passed\"\n""",
)
replace_once(
    test,
    """              << \" glacier=\" << maxGlacier << '\\n';\n""",
    """              << \" glacier=\" << maxGlacier\n              << \" mountain_local_relief_m=\" << mountainLocalRelief\n              << \" rift_local_relief_m=\" << riftLocalRelief << '\\n';\n""",
)

print("R24 real 3-D terrain migration applied")
