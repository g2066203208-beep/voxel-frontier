from pathlib import Path


def rep(s, old, new, label):
    if old not in s:
        raise SystemExit(f'{label} not found')
    return s.replace(old, new, 1)

p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
if 'R8 mountain hierarchy' in s:
    raise SystemExit(0)

start = s.index('    // R7 mountain refinement:')
end = s.index('    // R7 plateau refinement:', start)
s = s[:start] + '''    // R8 mountain hierarchy: restore the strong R6 macro relief, but place almost all of the
    // vertical range in 12-30 km shoulders and keep the ~6 km band subordinate. This gives a
    // recognisable massif/valley silhouette without the kilometre-high wall artefacts seen in R6.
    const double rangeRidgeA = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xD6E8FEB86659FD93ULL, w, 240.0, 5));
    const double rangeRidgeB = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xA5A3564E27F8862FULL, w, 520.0, 4));
    const double rangeRidgeC = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0x9E3779B185EBCA87ULL, w, 980.0, 3));
    const double rangeMask = smooth01(0.05, 0.56, geomorph.mountain) * geomorphLandness;
    const double ridgeCoreA = std::pow(smooth01(0.26, 0.87, rangeRidgeA), 1.92);
    const double ridgeCoreB = std::pow(smooth01(0.31, 0.90, rangeRidgeB), 1.84);
    const double ridgeCoreC = std::pow(smooth01(0.40, 0.94, rangeRidgeC), 1.70);
    const double rangeShoulder = rangeMask * smooth01(
        0.20, 0.70, std::max(ridgeCoreA, ridgeCoreB * 0.86));
    const double summitCore = rangeMask * std::pow(
        std::clamp(0.58 * ridgeCoreA + 0.42 * ridgeCoreB, 0.0, 1.0), 2.05);
    const double rangeRelief = rangeMask * (
        0.152 * (ridgeCoreA - 0.31)
        + 0.088 * (ridgeCoreB - 0.28)
        + 0.018 * (ridgeCoreC - 0.24));
    const double interRangeValley = rangeMask * std::pow(
        1.0 - std::clamp(std::max(ridgeCoreA, ridgeCoreB * 0.82), 0.0, 1.0), 2.2);
    elevation += maxLand * (rangeRelief + 0.040 * rangeShoulder + 0.170 * summitCore);
    elevation -= maxLand * 0.060 * interRangeValley;

''' + s[end:]

start = s.index('    // R7 plateau refinement:')
end = s.index('    // R5 river corridor:', start)
s = s[:start] + '''    // R8 plateau hierarchy: use a much broader province mask, a nearly level inner table and
    // a distinct transition bench. The previous R7 target often selected the legacy plateau mask,
    // so the exported plateau authority below is now this post-bake terrace only.
    const double globalHighland = geomorphLandness
        * smooth01(720.0, 2100.0, geomorph.elevationMeters)
        * (1.0 - smooth01(0.20, 0.64, geomorph.mountain));
    const double plateauMacro = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x4A7484AA6EA6E483ULL, w, 46.0, 4);
    const double plateauMeso = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x5CB0A9DCBD41FBD4ULL, w, 118.0, 3);
    const double plateauSignal = plateauMacro * 0.82 + plateauMeso * 0.18;
    const double plateauTerrace = globalHighland * smooth01(0.48, 0.61, plateauSignal);
    const double plateauBody = globalHighland * smooth01(0.60, 0.72, plateauSignal);
    const double plateauRim = std::clamp(plateauTerrace - plateauBody * 0.78, 0.0, 1.0);
    const double plateauTopNoise = fbmSurface(
        definition.seed ^ 0x76F988DA831153B5ULL, w, 210.0, 2);
    const double plateauShelf = 2320.0 + 90.0 * plateauTopNoise;
    const double plateauBlend = 0.94 * plateauTerrace;
    elevation = elevation * (1.0 - plateauBlend) + plateauShelf * plateauBlend;
    elevation += maxLand * (0.030 * plateauRim + 0.006 * plateauBody);

''' + s[end:]

old = '''    const double globalCoastBand = geomorphLandness
        * (1.0 - smooth01(70.0, 620.0, std::abs(geomorph.elevationMeters)));
    const double globalCoastRugged = globalCoastBand
        * smooth01(0.44, 0.84, rangeRidgeB);
    const double coastEscarpment = globalCoastRugged
        * (0.62 + 0.38 * smooth01(0.34, 0.86, rangeRidgeA));
    elevation += maxLand * 0.058 * coastEscarpment;
'''
new = '''    const double globalCoastBand = geomorphLandness
        * (1.0 - smooth01(55.0, 520.0, std::abs(geomorph.elevationMeters)));
    const double globalCoastRugged = globalCoastBand
        * smooth01(0.40, 0.82, rangeRidgeB);
    const double coastEscarpment = std::pow(globalCoastRugged, 1.22)
        * (0.64 + 0.36 * smooth01(0.32, 0.84, rangeRidgeA));
    // R8 rugged coast: a short, localised 0.5-0.8 km escarpment is allowed at selected rocky
    // margins, while low-energy margins remain beaches/floodplains.
    elevation += maxLand * 0.086 * coastEscarpment;
'''
s = rep(s, old, new, 'coast block')
s = rep(s, 'sample.plateau = std::max(plateau, plateauTerrace);',
        'sample.plateau = plateauTerrace;', 'plateau authority')
p.write_text(s)

p = Path('native/src/app/Main.cpp')
s = p.read_text()
old = '''            if (captureMode == "mountain") {
                if (terrain.mountain < 0.18 || aboveSea < 1500.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 36000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 1800.0) continue;
                captureScore += terrain.mountain * 4.2 + relief / 460.0
                    + aboveSea / 4200.0 + terrain.canyon * 0.7;
            } else if (captureMode == "river") {
                if (terrain.river < 0.18) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 10500.0);
                const double valleyDepth = std::max(0.0, r.meanElevation - aboveSea);
                captureScore += terrain.river * 6.0 + valleyDepth / 120.0
                    + terrain.canyon * 1.8
                    - std::max(0.0, aboveSea - 1800.0) / 1800.0;
            } else if (captureMode == "coast") {
                if (aboveSea < 90.0 || aboveSea > 980.0 || terrain.coastalCliff < 0.18) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 14000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (r.minElevation > -12.0 || relief < 420.0) continue;
                captureScore += terrain.coastalCliff * 6.2 + relief / 145.0
                    + aboveSea / 720.0;
            } else if (captureMode == "highland") {
                if (terrain.plateau < 0.24 || aboveSea < 1350.0 || aboveSea > 3400.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 26000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 420.0 || relief > 3000.0) continue;
                captureScore += terrain.plateau * 6.4 + aboveSea / 2000.0
                    + std::min(relief, 2200.0) / 780.0 - terrain.mountain * 1.8;
            }
'''
new = '''            if (captureMode == "mountain") {
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
s = rep(s, old, new, 'capture targets')

start = s.index('    // R7 capture geometry:')
end = s.index('    const auto& radii =', start)
s = s[:start] + '''    // R8 capture geometry: choose lower foreground ground for mountain/plateau silhouettes,
    // keep river evidence inland, and keep the coast camera on dry low ground (not over the ocean).
    const std::array<double, 5> mountainRadii{12000.0, 18000.0, 24000.0, 32000.0, 42000.0};
    const std::array<double, 5> highlandRadii{8000.0, 12000.0, 18000.0, 24000.0, 32000.0};
    const std::array<double, 5> coastRadii{1800.0, 3000.0, 4500.0, 6500.0, 9000.0};
    const std::array<double, 5> riverRadii{1000.0, 1600.0, 2400.0, 3400.0, 4800.0};
''' + s[end:]

old = '''            if (mode == "coast") {
                if (!terrain.submerged(planet)) continue;
                score = std::abs(terrain.elevationMeters + 22.0) * 0.05
                    + std::abs(standOffMeters - 7000.0) * 0.018;
            } else if (mode == "river") {
                if (terrain.submerged(planet) || terrain.river > 0.16) continue;
                score = std::abs(terrain.elevationMeters - targetElevation) * 0.18
                    + terrain.river * 2200.0
                    + std::abs(standOffMeters - 2600.0) * 0.035;
            } else if (mode == "mountain") {
                if (terrain.submerged(planet)) continue;
                const double drop = targetElevation - terrain.elevationMeters;
                score = std::abs(drop - 1150.0) * 0.75
                    + terrain.mountain * 900.0
                    + std::abs(standOffMeters - 14000.0) * 0.024;
            } else {
                if (terrain.submerged(planet)) continue;
                const double drop = targetElevation - terrain.elevationMeters;
                score = std::abs(drop - 620.0) * 0.95
                    + terrain.mountain * 1050.0
                    + terrain.plateau * 420.0
                    + std::abs(standOffMeters - 12000.0) * 0.026;
            }
'''
new = '''            if (mode == "coast") {
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
s = rep(s, old, new, 'vantage scoring')

old = '''        const double fallbackMeters = mode == "coast" ? 5000.0
            : (mode == "river" ? 2600.0 : (mode == "highland" ? 12000.0 : 14000.0));
'''
new = '''        const double fallbackMeters = mode == "coast" ? 4500.0
            : (mode == "river" ? 2400.0 : (mode == "highland" ? 18000.0 : 24000.0));
'''
s = rep(s, old, new, 'fallback')

old = '''            const double targetLift = captureMode == "mountain" ? 210.0
                : (captureMode == "highland" ? 95.0 : (captureMode == "coast" ? 110.0 : 28.0));
            const double cameraLift = captureMode == "mountain" ? 155.0
                : (captureMode == "highland" ? 120.0
                : (captureMode == "coast" ? 38.0 : 90.0));
'''
new = '''            const double targetLift = captureMode == "mountain" ? 160.0
                : (captureMode == "highland" ? 70.0 : (captureMode == "coast" ? 85.0 : 24.0));
            const double cameraLift = captureMode == "mountain" ? 135.0
                : (captureMode == "highland" ? 110.0
                : (captureMode == "coast" ? 65.0 : 78.0));
'''
s = rep(s, old, new, 'camera lifts')

old = '''            const double visualBase = captureMode == "coast"
                ? std::max(localSurface, planet.radius + planet.seaLevelElevationMeters)
                : localSurface;
'''
new = '''            const double visualBase = localSurface;
'''
s = rep(s, old, new, 'coast visual base')
p.write_text(s)
