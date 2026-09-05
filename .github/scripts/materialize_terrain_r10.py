from pathlib import Path


def rep(s: str, old: str, new: str, label: str) -> str:
    if old not in s:
        raise SystemExit(f'{label} not found')
    return s.replace(old, new, 1)

# --- Terrain: make the tableland actually read as a tableland, without a vertical wall. ---
p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
if 'R10 tableland profile' not in s:
    old = '''    const double plateauSignal = plateauMacro * 0.82 + plateauMeso * 0.18;
    const double plateauTerrace = globalHighland * smooth01(0.48, 0.61, plateauSignal);
    const double plateauBody = globalHighland * smooth01(0.60, 0.72, plateauSignal);
    const double plateauRim = std::clamp(plateauTerrace - plateauBody * 0.78, 0.0, 1.0);
    const double plateauTopNoise = fbmSurface(
        definition.seed ^ 0x76F988DA831153B5ULL, w, 210.0, 2);
    const double plateauShelf = 2580.0 + 75.0 * plateauTopNoise;
    const double plateauBlend = 0.94 * plateauTerrace;
    elevation = elevation * (1.0 - plateauBlend) + plateauShelf * plateauBlend;
    elevation += maxLand * (0.030 * plateauRim + 0.006 * plateauBody);
'''
    new = '''    // R10 tableland profile: a broad bench, a flatter interior and a finite escarpment belt.
    // Keep C1 transitions (no hard steps), but let the interior converge much more strongly to
    // one shelf elevation so a plateau is not visually indistinguishable from rolling upland.
    const double plateauSignal = plateauMacro * 0.84 + plateauMeso * 0.16;
    const double plateauTerrace = globalHighland * smooth01(0.49, 0.595, plateauSignal);
    const double plateauBody = globalHighland * smooth01(0.605, 0.695, plateauSignal);
    const double plateauRim = std::clamp(plateauTerrace - plateauBody * 0.82, 0.0, 1.0);
    const double plateauTopNoise = fbmSurface(
        definition.seed ^ 0x76F988DA831153B5ULL, w, 175.0, 2);
    const double plateauShelf = 2620.0 + 34.0 * plateauTopNoise;
    const double plateauBlend = std::clamp(0.78 * plateauTerrace + 0.20 * plateauBody, 0.0, 0.975);
    elevation = elevation * (1.0 - plateauBlend) + plateauShelf * plateauBlend;
    elevation += maxLand * (0.026 * plateauRim + 0.003 * plateauBody);
'''
    s = rep(s, old, new, 'plateau profile')
    old = '''    const double detailDamp = geomorphLandness
        * (1.0 - 0.72 * std::max(wetland, geomorph.floodplain))
        * (1.0 - 0.88 * std::clamp(std::max(plateau, plateauTerrace), 0.0, 1.0));
'''
    new = '''    const double detailDamp = geomorphLandness
        * (1.0 - 0.72 * std::max(wetland, geomorph.floodplain))
        * (1.0 - 0.95 * std::clamp(std::max(plateau, plateauTerrace), 0.0, 1.0));
'''
    s = rep(s, old, new, 'plateau detail damp')
    p.write_text(s)

# --- Capture selection: evidence must show the landform, not merely a matching mask. ---
p = Path('native/src/app/Main.cpp')
s = p.read_text()
if 'R10 evidence geometry' not in s:
    old = '''            if (captureMode == "mountain") {
                if (terrain.mountain < 0.20 || aboveSea < 2600.0 || aboveSea > 5200.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 26000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 1700.0 || relief > 4300.0) continue;
                captureScore += terrain.mountain * 4.8 + relief / 360.0
                    + aboveSea / 4600.0 + terrain.canyon * 0.4;
            } else if (captureMode == "river") {
                if (terrain.river < 0.22 || aboveSea < 240.0 || aboveSea > 1500.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 7000.0);
                if (r.minElevation < 80.0) continue;
                const double valleyDepth = std::max(0.0, r.meanElevation - aboveSea);
                captureScore += terrain.river * 7.0 + valleyDepth / 100.0
                    + terrain.canyon * 1.4;
            } else if (captureMode == "coast") {
                if (aboveSea < 320.0 || aboveSea > 1350.0 || terrain.coastalCliff < 0.26) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 10000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (r.minElevation > -8.0 || relief < 560.0) continue;
                captureScore += terrain.coastalCliff * 7.6 + relief / 118.0
                    + aboveSea / 720.0;
            } else if (captureMode == "highland") {
                if (terrain.plateau < 0.40 || terrain.plateau > 0.92
                    || aboveSea < 1900.0 || aboveSea > 3000.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 26000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 650.0 || relief > 2500.0) continue;
                const double edgePreference = 1.0
                    - std::clamp(std::abs(terrain.plateau - 0.68) / 0.28, 0.0, 1.0);
                captureScore += edgePreference * 5.0 + terrain.plateau * 3.2
                    + std::min(relief, 2200.0) / 620.0 - terrain.mountain * 1.8;
            }
'''
    new = '''            if (captureMode == "mountain") {
                if (terrain.mountain < 0.22 || aboveSea < 3000.0 || aboveSea > 5000.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 30000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 2200.0 || relief > 4800.0 || r.minElevation > 1800.0) continue;
                captureScore += terrain.mountain * 4.3 + relief / 300.0
                    + std::max(0.0, 1800.0 - r.minElevation) / 600.0;
            } else if (captureMode == "river") {
                if (terrain.river < 0.22 || aboveSea < 240.0 || aboveSea > 1500.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 7000.0);
                if (r.minElevation < 80.0) continue;
                const double valleyDepth = std::max(0.0, r.meanElevation - aboveSea);
                captureScore += terrain.river * 7.0 + valleyDepth / 100.0
                    + terrain.canyon * 1.4;
            } else if (captureMode == "coast") {
                if (aboveSea < 120.0 || aboveSea > 680.0 || terrain.coastalCliff < 0.20) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 7000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (r.minElevation > -6.0 || relief < 340.0) continue;
                const double cliffHeightPreference = 1.0
                    - std::clamp(std::abs(aboveSea - 360.0) / 360.0, 0.0, 1.0);
                captureScore += terrain.coastalCliff * 6.8 + relief / 105.0
                    + cliffHeightPreference * 3.5;
            } else if (captureMode == "highland") {
                if (terrain.plateau < 0.48 || terrain.plateau > 0.88
                    || aboveSea < 2150.0 || aboveSea > 2950.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 18000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 520.0 || relief > 2200.0 || r.minElevation > 2050.0) continue;
                const double edgePreference = 1.0
                    - std::clamp(std::abs(terrain.plateau - 0.66) / 0.22, 0.0, 1.0);
                captureScore += edgePreference * 6.0 + terrain.plateau * 2.8
                    + std::min(relief, 1800.0) / 500.0 - terrain.mountain * 2.2;
            }
'''
    s = rep(s, old, new, 'target rules')

    start = s.index('    // R9 capture visibility:')
    end = s.index('    const auto& radii =', start)
    s = s[:start] + '''    // R10 evidence geometry: choose baselines that expose vertical relief. Mountain cameras
    // search for a genuinely lower valley; highland cameras sit below the bench edge; coast
    // cameras stay offshore but close enough that the escarpment occupies the frame.
    const std::array<double, 6> mountainRadii{10000.0, 13000.0, 16000.0, 19000.0, 23000.0, 28000.0};
    const std::array<double, 6> highlandRadii{5000.0, 7000.0, 9000.0, 12000.0, 15000.0, 19000.0};
    const std::array<double, 6> coastRadii{1200.0, 1700.0, 2300.0, 3000.0, 3800.0, 4800.0};
    const std::array<double, 6> riverRadii{500.0, 800.0, 1200.0, 1800.0, 2600.0, 3400.0};
''' + s[end:]

    old = '''            if (mode == "coast") {
                if (!terrain.submerged(planet)) continue;
                score = std::abs(terrain.elevationMeters + 18.0) * 0.08
                    + std::abs(standOffMeters - 3200.0) * 0.026;
            } else if (mode == "river") {
                if (terrain.submerged(planet) || terrain.river > 0.10 || terrain.elevationMeters < 120.0) continue;
                score = std::abs(terrain.elevationMeters - targetElevation) * 0.12
                    + terrain.river * 2600.0
                    + std::abs(standOffMeters - 1200.0) * 0.042;
            } else if (mode == "mountain") {
                if (terrain.submerged(planet)) continue;
                const double drop = targetElevation - terrain.elevationMeters;
                score = std::abs(drop - 1450.0) * 0.68
                    + terrain.mountain * 720.0
                    + std::abs(standOffMeters - 11000.0) * 0.032;
            } else {
                if (terrain.submerged(planet)) continue;
                const double drop = targetElevation - terrain.elevationMeters;
                score = std::abs(drop - 1150.0) * 0.70
                    + terrain.mountain * 900.0
                    + terrain.plateau * 160.0
                    + std::abs(standOffMeters - 26000.0) * 0.020;
            }
'''
    new = '''            if (mode == "coast") {
                if (!terrain.submerged(planet)) continue;
                score = std::abs(terrain.elevationMeters + 12.0) * 0.10
                    + std::abs(standOffMeters - 2300.0) * 0.034;
            } else if (mode == "river") {
                if (terrain.submerged(planet) || terrain.river > 0.10 || terrain.elevationMeters < 120.0) continue;
                score = std::abs(terrain.elevationMeters - targetElevation) * 0.12
                    + terrain.river * 2600.0
                    + std::abs(standOffMeters - 1200.0) * 0.042;
            } else if (mode == "mountain") {
                if (terrain.submerged(planet) || terrain.elevationMeters > 1750.0) continue;
                const double drop = targetElevation - terrain.elevationMeters;
                if (drop < 1500.0) continue;
                score = std::abs(drop - 2300.0) * 0.48
                    + terrain.mountain * 850.0
                    + std::abs(standOffMeters - 17000.0) * 0.026;
            } else {
                if (terrain.submerged(planet) || terrain.elevationMeters > 2050.0) continue;
                const double drop = targetElevation - terrain.elevationMeters;
                if (drop < 500.0) continue;
                score = std::abs(drop - 900.0) * 0.60
                    + terrain.mountain * 980.0
                    + terrain.plateau * 520.0
                    + std::abs(standOffMeters - 10000.0) * 0.032;
            }
'''
    s = rep(s, old, new, 'vantage scoring')

    old = '''        const double fallbackMeters = mode == "coast" ? 3200.0
            : (mode == "river" ? 1200.0 : (mode == "highland" ? 26000.0 : 11000.0));
'''
    new = '''        const double fallbackMeters = mode == "coast" ? 2300.0
            : (mode == "river" ? 1200.0 : (mode == "highland" ? 10000.0 : 17000.0));
'''
    s = rep(s, old, new, 'fallback')

    old = '''            const double targetLift = captureMode == "mountain" ? 120.0
                : (captureMode == "highland" ? 45.0 : (captureMode == "coast" ? 100.0 : 18.0));
            const double cameraLift = captureMode == "mountain" ? 520.0
                : (captureMode == "highland" ? 520.0
                : (captureMode == "coast" ? 340.0 : 210.0));
'''
    new = '''            const double targetLift = captureMode == "mountain" ? 180.0
                : (captureMode == "highland" ? 80.0 : (captureMode == "coast" ? 90.0 : 18.0));
            const double cameraLift = captureMode == "mountain" ? 180.0
                : (captureMode == "highland" ? 135.0
                : (captureMode == "coast" ? 115.0 : 210.0));
'''
    s = rep(s, old, new, 'camera lifts')
    p.write_text(s)
