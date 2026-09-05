from pathlib import Path


def rep(s, old, new, label):
    if old not in s:
        raise SystemExit(f'{label} not found')
    return s.replace(old, new, 1)

p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
if 'R9 plateau detail suppression' in s:
    raise SystemExit(0)
old = '''    const double detailDamp = geomorphLandness
        * (1.0 - 0.72 * std::max(wetland, geomorph.floodplain))
        * (1.0 - 0.52 * plateau);
'''
new = '''    // R9 plateau detail suppression: R8 correctly built a post-bake tableland but this stage
    // still damped detail with the obsolete pre-bake `plateau` mask, re-wrinkling the flat top.
    const double detailDamp = geomorphLandness
        * (1.0 - 0.72 * std::max(wetland, geomorph.floodplain))
        * (1.0 - 0.88 * std::clamp(std::max(plateau, plateauTerrace), 0.0, 1.0));
'''
s = rep(s, old, new, 'detail damp')
# Make the shelf just high enough that its edge reads from surrounding uplands while remaining plausible.
s = rep(s, 'const double plateauShelf = 2320.0 + 90.0 * plateauTopNoise;',
        'const double plateauShelf = 2580.0 + 75.0 * plateauTopNoise;', 'plateau shelf')
p.write_text(s)

p = Path('native/src/app/Main.cpp')
s = p.read_text()
if 'R9 capture visibility' in s:
    raise SystemExit(0)
old = '''            if (captureMode == "mountain") {
                if (terrain.mountain < 0.20 || aboveSea < 2200.0 || aboveSea > 5200.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 32000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 1500.0 || relief > 4300.0) continue;
                captureScore += terrain.mountain * 4.6 + relief / 390.0
                    + aboveSea / 4400.0 + terrain.canyon * 0.5;
            } else if (captureMode == "river") {
                if (terrain.river < 0.20 || aboveSea < 260.0 || aboveSea > 1700.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 10500.0);
                if (r.minElevation < 45.0) continue; // reject estuaries/coastal channels
                const double valleyDepth = std::max(0.0, r.meanElevation - aboveSea);
                captureScore += terrain.river * 6.4 + valleyDepth / 115.0
                    + terrain.canyon * 1.6;
            } else if (captureMode == "coast") {
                if (aboveSea < 260.0 || aboveSea > 1250.0 || terrain.coastalCliff < 0.24) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 12000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (r.minElevation > -10.0 || relief < 520.0) continue;
                captureScore += terrain.coastalCliff * 7.2 + relief / 125.0
                    + aboveSea / 700.0;
            } else if (captureMode == "highland") {
                if (terrain.plateau < 0.58 || aboveSea < 1800.0 || aboveSea > 3000.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 30000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 600.0 || relief > 2300.0) continue;
                captureScore += terrain.plateau * 7.0 + aboveSea / 2100.0
                    + std::min(relief, 2000.0) / 650.0 - terrain.mountain * 2.0;
            }
'''
new = '''            if (captureMode == "mountain") {
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
s = rep(s, old, new, 'capture target rules')

start = s.index('    // R8 capture geometry:')
end = s.index('    const auto& radii =', start)
s = s[:start] + '''    // R9 capture visibility: the R8 geometry had enough measured relief, but 20-40 km
    // standoff plus atmosphere compressed it into the horizon. Use close oblique/aerial evidence,
    // keep river cameras beside the channel, and put the coast camera safely above open water.
    const std::array<double, 5> mountainRadii{7000.0, 9000.0, 12000.0, 15000.0, 19000.0};
    const std::array<double, 5> highlandRadii{12000.0, 18000.0, 26000.0, 36000.0, 50000.0};
    const std::array<double, 5> coastRadii{2200.0, 3000.0, 4200.0, 5600.0, 7600.0};
    const std::array<double, 5> riverRadii{500.0, 800.0, 1200.0, 1800.0, 2600.0};
''' + s[end:]

old = '''            if (mode == "coast") {
                if (terrain.submerged(planet) || terrain.elevationMeters < 12.0 || terrain.elevationMeters > 150.0) continue;
                score = std::abs(terrain.elevationMeters - 55.0) * 1.4
                    + terrain.coastalCliff * 700.0
                    + std::abs(standOffMeters - 4500.0) * 0.022;
            } else if (mode == "river") {
                if (terrain.submerged(planet) || terrain.river > 0.14 || terrain.elevationMeters < 120.0) continue;
                score = std::abs(terrain.elevationMeters - targetElevation) * 0.15
                    + terrain.river * 2400.0
                    + std::abs(standOffMeters - 2400.0) * 0.036;
            } else if (mode == "mountain") {
                if (terrain.submerged(planet)) continue;
                const double drop = targetElevation - terrain.elevationMeters;
                score = std::abs(drop - 1850.0) * 0.62
                    + terrain.mountain * 780.0
                    + std::abs(standOffMeters - 24000.0) * 0.021;
            } else {
                if (terrain.submerged(planet)) continue;
                const double drop = targetElevation - terrain.elevationMeters;
                score = std::abs(drop - 900.0) * 0.78
                    + terrain.mountain * 980.0
                    + terrain.plateau * 300.0
                    + std::abs(standOffMeters - 18000.0) * 0.024;
            }
'''
new = '''            if (mode == "coast") {
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
s = rep(s, old, new, 'vantage scoring')
old = '''        const double fallbackMeters = mode == "coast" ? 4500.0
            : (mode == "river" ? 2400.0 : (mode == "highland" ? 18000.0 : 24000.0));
'''
new = '''        const double fallbackMeters = mode == "coast" ? 3200.0
            : (mode == "river" ? 1200.0 : (mode == "highland" ? 26000.0 : 11000.0));
'''
s = rep(s, old, new, 'fallback')
old = '''            const double targetLift = captureMode == "mountain" ? 160.0
                : (captureMode == "highland" ? 70.0 : (captureMode == "coast" ? 85.0 : 24.0));
            const double cameraLift = captureMode == "mountain" ? 135.0
                : (captureMode == "highland" ? 110.0
                : (captureMode == "coast" ? 65.0 : 78.0));
'''
new = '''            const double targetLift = captureMode == "mountain" ? 120.0
                : (captureMode == "highland" ? 45.0 : (captureMode == "coast" ? 100.0 : 18.0));
            const double cameraLift = captureMode == "mountain" ? 520.0
                : (captureMode == "highland" ? 520.0
                : (captureMode == "coast" ? 340.0 : 210.0));
'''
s = rep(s, old, new, 'camera lifts')
old = '''            const double visualBase = localSurface;
'''
new = '''            const double visualBase = captureMode == "coast"
                ? std::max(localSurface, planet.radius + planet.seaLevelElevationMeters)
                : localSurface;
'''
s = rep(s, old, new, 'visual base')
p.write_text(s)
