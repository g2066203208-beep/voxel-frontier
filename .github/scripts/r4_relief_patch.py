from pathlib import Path


def replace_between(text: str, start_marker: str, end_marker: str, replacement: str, start_at: int = 0) -> str:
    start = text.index(start_marker, start_at)
    end = text.index(end_marker, start)
    return text[:start] + replacement + text[end:]


# --- PlanetSurface: signed mountain relief, hydrology-resolved valleys, real highland authority ---
planet_path = Path("native/src/world/PlanetSurface.cpp")
planet = planet_path.read_text()

if "R4 relief V5" not in planet:
    range_start = "    const double rangeRidgeA = 1.0 - std::abs(fbmSurface("
    range_end = "\n\n    // Hydrology remains the placement authority for valleys."
    range_replacement = r'''    const double rangeRidgeA = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xD6E8FEB86659FD93ULL, w, 34.0, 5));
    const double rangeRidgeB = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xA5A3564E27F8862FULL, w, 82.0, 4));
    const double rangeRidgeC = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0x9E3779B185EBCA87ULL, w, 210.0, 3));
    const double rangeMask = smooth01(0.07, 0.66, geomorph.mountain) * geomorphLandness;
    const double ridgeCoreA = std::pow(smooth01(0.30, 0.86, rangeRidgeA), 2.15);
    const double ridgeCoreB = std::pow(smooth01(0.34, 0.88, rangeRidgeB), 1.90);
    const double ridgeCoreC = std::pow(smooth01(0.40, 0.91, rangeRidgeC), 1.65);

    // R4 relief V5: the global geomorph bake owns the mountain-belt location.  These
    // signed bands reconstruct crests AND inter-range valleys instead of lifting a whole
    // orogenic province into one high slab.
    const double rangeRelief = rangeMask * (
        0.260 * (ridgeCoreA - 0.42)
        + 0.160 * (ridgeCoreB - 0.38)
        + 0.090 * (ridgeCoreC - 0.34));
    const double interRangeValley = rangeMask * std::pow(
        1.0 - std::clamp(std::max(ridgeCoreA, ridgeCoreB * 0.72), 0.0, 1.0), 2.2);
    elevation += maxLand * rangeRelief;
    elevation -= maxLand * 0.085 * interRangeValley;

    // Post-bake highland authority: elevated continental interiors that are not mountain
    // cores.  This is what the plateau/highland capture and material logic now query.
    const double globalHighland = geomorphLandness
        * smooth01(900.0, 2400.0, geomorph.elevationMeters)
        * (1.0 - smooth01(0.22, 0.68, geomorph.mountain));'''
    planet = replace_between(planet, range_start, range_end, range_replacement)

    channel_start = "    const double channelRefineNoise = 1.0 - std::abs(fbmSurface("
    channel_end = "\n\n    // Give hydrologically low coastal margins"
    channel_replacement = r'''    const double channelRefineNoise = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xC2B2AE3D27D4EB4FULL, w, 260.0, 3));
    const double riverAuthority = std::pow(std::clamp(geomorph.river, 0.0, 1.0), 1.18)
        * geomorphLandness;
    const double channelCore = std::pow(std::clamp(geomorph.river, 0.0, 1.0), 1.72)
        * (0.76 + 0.24 * smooth01(0.42, 0.88, channelRefineNoise)) * geomorphLandness;
    const double uplandCarve = smooth01(260.0, 2200.0, geomorph.elevationMeters);

    // The Priority-Flood/discharge bake remains authoritative for placement.  Near-field
    // reconstruction resolves its broad corridor into a visible valley floor and a narrower
    // river core instead of inventing sine-wave channels elsewhere.
    elevation -= riverAuthority * (75.0 + 510.0 * uplandCarve);
    elevation -= channelCore * (45.0 + 230.0 * uplandCarve);
    elevation -= geomorph.incision * (55.0 + 240.0 * uplandCarve);'''
    planet = replace_between(planet, channel_start, channel_end, channel_replacement)

    planet = planet.replace(
        "    sample.plateau = plateau;",
        "    sample.plateau = std::max(plateau, globalHighland);",
        1,
    )
    planet = planet.replace(
        "    sample.river = std::max(geomorph.river * 0.48, channelCore);",
        "    sample.river = std::max(geomorph.river * 0.44, channelCore);",
        1,
    )

    # High/steep relief must expose rock before aridity can classify the same point as sand.
    def reorder_surface_classes(text: str, function_marker: str, end_marker: str) -> str:
        f0 = text.index(function_marker)
        a = text.index(
            "    } else if (sample.glacier > 0.38 || sample.elevationMeters > 6200.0) {",
            f0,
        )
        b = text.index(end_marker, a)
        is_color = function_marker.startswith("glm::vec3")
        exposed_comment = " // exposed rock" if is_color else ""
        block = f'''    }} else if (sample.glacier > 0.38 || sample.elevationMeters > 6200.0) {{
        surfaceClass = 5; // snow/ice
    }} else if (sample.mountain > 0.24 || sample.canyon > 0.20
        || sample.coastalCliff > 0.30 || sample.elevationMeters > 2500.0) {{
        surfaceClass = 1;{exposed_comment}
    }} else if (sample.wetland > 0.34) {{
        surfaceClass = 4; // wet mud
    }} else if (sample.dunes > 0.36 || sample.aridity > 0.72) {{
        surfaceClass = 2; // sand
    }} else if (sample.moisture > 0.22 && sample.aridity < 0.72) {{
        surfaceClass = 0; // grassland
    }}'''
        return text[:a] + block + text[b:]

    planet = reorder_surface_classes(
        planet,
        "glm::vec3 planetTerrainColor(",
        "\n\n    switch (surfaceClass)",
    )
    planet = reorder_surface_classes(
        planet,
        "glm::vec4 planetTerrainMaterial(",
        "\n\n    float roughness",
    )

planet_path.write_text(planet)


# --- Main: evidence target selection uses measured local relief, not semantic masks alone ---
main_path = Path("native/src/app/Main.cpp")
main = main_path.read_text()

if "struct LocalReliefStats" not in main:
    find_playable = main.index("[[nodiscard]] glm::dvec3 findPlayableSpawnDirection(")
    helper = r'''struct LocalReliefStats {
    double minElevation{std::numeric_limits<double>::infinity()};
    double maxElevation{-std::numeric_limits<double>::infinity()};
    double meanElevation{};
};

[[nodiscard]] LocalReliefStats sampleLocalRelief(
    const vf::PlanetDefinition& planet,
    const glm::dvec3& centerInput,
    double radiusMeters) {
    const glm::dvec3 center = safeNormalize(centerInput);
    const glm::dvec3 east = stableTangent(center);
    const glm::dvec3 north = safeNormalize(glm::cross(center, east), {0.0, 0.0, 1.0});
    LocalReliefStats stats{};
    double sum = 0.0;
    int count = 0;
    for (double scale : {0.52, 1.0}) {
        const double angular = radiusMeters * scale / std::max(1.0, planet.radius);
        for (int i = 0; i < 12; ++i) {
            const double a = 2.0 * kPi * static_cast<double>(i) / 12.0;
            const glm::dvec3 d = safeNormalize(
                center + east * (std::cos(a) * angular) + north * (std::sin(a) * angular),
                center);
            const double h = vf::planetHeight(planet, d);
            stats.minElevation = std::min(stats.minElevation, h);
            stats.maxElevation = std::max(stats.maxElevation, h);
            sum += h;
            ++count;
        }
    }
    stats.meanElevation = count > 0
        ? sum / static_cast<double>(count)
        : vf::planetHeight(planet, center);
    return stats;
}

'''
    main = main[:find_playable] + helper + main[find_playable:]

    find_playable = main.index("[[nodiscard]] glm::dvec3 findPlayableSpawnDirection(")
    capture_start = main.index("        if (!captureMode.empty()) {", find_playable)
    normal_start = main.index(
        "        if (aboveSea < 80.0 || terrain.submerged(planet)) continue;",
        capture_start,
    )
    capture_block = r'''        if (!captureMode.empty()) {
            if (terrain.submerged(planet) || aboveSea < 8.0) continue;
            const double sunElevation = glm::dot(d, sunDirection);
            if (sunElevation < 0.34 || sunElevation > 0.96) continue;
            const double readableDaylight = 1.0
                - std::clamp(std::abs(sunElevation - 0.64) / 0.32, 0.0, 1.0);
            double captureScore = readableDaylight * 1.8;

            if (captureMode == "mountain") {
                if (terrain.mountain < 0.20 || aboveSea < 900.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 62000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 900.0) continue;
                captureScore += terrain.mountain * 3.8 + relief / 720.0
                    + aboveSea / 5200.0 + terrain.canyon * 0.8;
            } else if (captureMode == "river") {
                if (terrain.river < 0.18) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 10500.0);
                const double valleyDepth = std::max(0.0, r.meanElevation - aboveSea);
                captureScore += terrain.river * 6.0 + valleyDepth / 120.0
                    + terrain.canyon * 1.8
                    - std::max(0.0, aboveSea - 1800.0) / 1800.0;
            } else if (captureMode == "coast") {
                if (std::abs(aboveSea) > 520.0 || terrain.coastalCliff < 0.06) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 18000.0);
                const double relief = r.maxElevation - r.minElevation;
                const double crossesSea = r.minElevation < -15.0 ? 1.0 : 0.0;
                captureScore += terrain.coastalCliff * 4.8 + relief / 240.0
                    + crossesSea * 2.2 - std::abs(aboveSea - 90.0) / 650.0;
            } else if (captureMode == "highland") {
                if (terrain.plateau < 0.18 || aboveSea < 950.0 || aboveSea > 4300.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 52000.0);
                const double relief = r.maxElevation - r.minElevation;
                captureScore += terrain.plateau * 4.8 + aboveSea / 1900.0
                    + std::min(relief, 2600.0) / 1300.0 - terrain.mountain * 1.3;
            }

            if (captureScore > bestScore) {
                bestScore = captureScore;
                best = d;
                found = true;
            }
            continue;
        }
'''
    main = main[:capture_start] + capture_block + main[normal_start:]

    vantage_start = main.index("[[nodiscard]] glm::dvec3 findCaptureVantageDirection(")
    vantage_end = main.index("\nvoid appendMesh", vantage_start)
    vantage = r'''[[nodiscard]] glm::dvec3 findCaptureVantageDirection(
    const vf::PlanetDefinition& planet,
    const glm::dvec3& targetDirectionInput,
    std::string_view mode) {
    const glm::dvec3 target = safeNormalize(targetDirectionInput);
    const glm::dvec3 east = stableTangent(target);
    const glm::dvec3 north = safeNormalize(glm::cross(target, east), {0.0, 0.0, 1.0});
    const std::array<double, 5> mountainRadii{42000.0, 65000.0, 90000.0, 125000.0, 165000.0};
    const std::array<double, 5> highlandRadii{26000.0, 42000.0, 62000.0, 85000.0, 115000.0};
    const std::array<double, 5> coastRadii{7000.0, 11000.0, 17000.0, 24000.0, 32000.0};
    const std::array<double, 5> riverRadii{3200.0, 5200.0, 7800.0, 11000.0, 15500.0};
    const auto& radii = mode == "mountain" ? mountainRadii
        : (mode == "highland" ? highlandRadii : (mode == "coast" ? coastRadii : riverRadii));
    const double targetElevation = vf::planetHeight(planet, target);
    glm::dvec3 best = target;
    double bestScore = std::numeric_limits<double>::infinity();

    for (double standOffMeters : radii) {
        const double angular = standOffMeters / std::max(1.0, planet.radius);
        for (int i = 0; i < 40; ++i) {
            const double a = 2.0 * kPi * static_cast<double>(i) / 40.0;
            const glm::dvec3 d = safeNormalize(
                target + east * (std::cos(a) * angular) + north * (std::sin(a) * angular),
                target);
            const vf::PlanetTerrainSample terrain = vf::samplePlanetTerrain(planet, d);
            double score = 0.0;
            if (mode == "coast") {
                if (!terrain.submerged(planet)) continue;
                score = std::abs(terrain.elevationMeters + 45.0) * 0.08
                    + std::abs(standOffMeters - 15000.0) * 0.015;
            } else if (mode == "river") {
                if (terrain.submerged(planet)) continue;
                score = -terrain.elevationMeters + terrain.river * 900.0
                    + std::abs(standOffMeters - 7800.0) * 0.025;
            } else {
                if (terrain.submerged(planet)) continue;
                score = terrain.elevationMeters - targetElevation
                    + terrain.mountain * 480.0
                    + standOffMeters * (mode == "mountain" ? 0.003 : 0.005);
            }
            if (score < bestScore) {
                bestScore = score;
                best = d;
            }
        }
    }
    return safeNormalize(best, target);
}
'''
    main = main[:vantage_start] + vantage + main[vantage_end:]

    camera_start = main.index('            const double targetLift = captureMode == "mountain"')
    camera_end = main.index("            const glm::dvec3 targetPlanet", camera_start)
    camera_block = r'''            const double targetLift = captureMode == "mountain" ? 950.0
                : (captureMode == "highland" ? 520.0 : (captureMode == "coast" ? 130.0 : 80.0));
            const double cameraLift = captureMode == "mountain" ? 3200.0
                : (captureMode == "highland" ? 2400.0
                : (captureMode == "coast" ? 1050.0 : 760.0));
'''
    main = main[:camera_start] + camera_block + main[camera_end:]

main_path.write_text(main)
