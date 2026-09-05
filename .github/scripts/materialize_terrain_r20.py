from pathlib import Path


def rep(s: str, old: str, new: str, label: str) -> str:
    if old not in s:
        raise SystemExit(f'{label} anchor not found')
    return s.replace(old, new, 1)

p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
# Preserve the local plate-boundary orientation so sub-grid folds can align to compression.
s = rep(s,
'''struct PlateField {\n    PlateSeed primary{};\n    PlateSeed secondary{};\n    double boundary{};\n    double convergence{};\n    double divergence{};\n};''',
'''struct PlateField {\n    PlateSeed primary{};\n    PlateSeed secondary{};\n    double boundary{};\n    double convergence{};\n    double divergence{};\n    glm::dvec3 boundaryNormal{};\n};''', 'PlateField orientation')
s = rep(s,
'''    return {best, second, boundary, convergence, divergence};''',
'''    return {best, second, boundary, convergence, divergence, boundaryNormal};''', 'PlateField return')

start = s.index('    // R19 DEMIURGE PROCESS CASCADE.')
end = s.index('    // Walking-scale geometry.', start)
new_block = r'''    // R20 TECTONIC FOLD CASCADE. The 256^2 / 60-step process bake still owns every
    // continent, orogenic belt, plateau province and drainage basin. Query-time geometry now
    // reconstructs the unresolved 2-80 km spectrum *along the local compression geometry*.
    // The fold direction comes from the two actual competing plate centres, not from a random
    // mountain mask, so parallel ranges and intervening valleys follow the tectonic belt.
    const double substrateHardness = std::clamp(geomorph.hardness, 0.0, 1.0);
    const double hardnessTerm = 0.70 + 0.64 * substrateHardness;
    const double processPlateauCore = smooth01(0.30, 0.52, bakedTableland);
    const double processPlateauInner = smooth01(0.48, 0.67, bakedTableland);
    const double processPlateauEdge = std::clamp(processPlateauCore - processPlateauInner, 0.0, 1.0);
    const double processPlateauFoot = smooth01(0.12, 0.31, bakedTableland)
        * (1.0 - processPlateauCore);
    const double processMountainGate = smooth01(0.07, 0.62, bakedMountain)
        * (1.0 - 0.78 * processPlateauInner) * geomorphLandness;

    const glm::dvec3 foldNormal = safeNormalize(plates.boundaryNormal, tangentAxis(d));
    const glm::dvec3 foldTangent = safeNormalize(glm::cross(d, foldNormal), tangentAxis(d));
    const double across = glm::dot(w, foldNormal);
    const double along = glm::dot(w, foldTangent);
    const double foldWarpA = fbmSurface(
        definition.seed ^ 0x6C8E9CF570932BD5ULL, w, 38.0, 4);
    const double foldWarpB = fbmSurface(
        definition.seed ^ 0xDA3E39CB94B95BDBULL, w, 110.0, 3);
    const double alongBreak = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0xA54FF53A5F1D36F1ULL, w, 95.0, 4);

    // Boundary-parallel folds. Absolute sine is used only as a sub-grid fold profile; the
    // baked mountain field remains the spatial gate. Domain warp and along-strike modulation
    // prevent railway-track regularity while preserving a coherent mountain-system direction.
    const double foldA = 1.0 - std::abs(std::sin(
        across * 430.0 + along * 21.0 + foldWarpA * 3.6));
    const double foldB = 1.0 - std::abs(std::sin(
        across * 920.0 - along * 47.0 + foldWarpA * 5.2 + foldWarpB * 1.8));
    const double foldC = 1.0 - std::abs(std::sin(
        across * 1840.0 + along * 103.0 + foldWarpB * 4.4));
    const double mainCrest = std::pow(smooth01(0.38, 0.90,
        foldA * (0.70 + 0.38 * alongBreak)), 1.38);
    const double branchCrest = std::pow(smooth01(0.40, 0.92,
        foldB * (0.66 + 0.44 * alongBreak)), 1.58);
    const double spurCrest = std::pow(smooth01(0.44, 0.94,
        foldC * (0.62 + 0.48 * alongBreak)), 1.78);
    const double crestEnvelope = std::clamp(std::max(
        mainCrest, std::max(0.86 * branchCrest, 0.70 * spurCrest)), 0.0, 1.0);
    const double processValley = processMountainGate
        * std::pow(1.0 - crestEnvelope, 1.55)
        * (0.48 + 0.72 * std::clamp(geomorph.incision, 0.0, 1.0));
    const double summitCrown = processMountainGate
        * std::pow(std::max(branchCrest, 0.92 * spurCrest), 2.65)
        * (0.60 + 0.55 * alongBreak);

    elevation += processMountainGate * hardnessTerm
        * (940.0 * (mainCrest - 0.16)
            + 590.0 * (branchCrest - 0.11)
            + 290.0 * (spurCrest - 0.08));
    elevation += summitCrown * hardnessTerm * 1280.0;
    elevation -= processValley * (760.0 + 260.0 * (1.0 - substrateHardness));

    // Collision tablelands use a sharper but still C1-continuous residual profile. Their
    // altitude remains whatever tectonic uplift/erosion produced; only the unresolved caprock
    // shoulder is reconstructed. Outside the cap, a shallow foot-zone drop makes the escarpment
    // legible from lowland without reinstating the old fixed-2700m shelf.
    const double plateauTopNoise = fbmSurface(
        definition.seed ^ 0xBB67AE8584CAA73BULL, w, 220.0, 3);
    elevation += processPlateauInner * (820.0 + 260.0 * hardnessTerm);
    elevation += processPlateauEdge * (360.0 + 240.0 * hardnessTerm);
    elevation -= processPlateauFoot * (170.0 + 90.0 * (1.0 - substrateHardness));
    elevation += processPlateauInner * plateauTopNoise * 36.0;

    // Stable interiors keep restrained rolling relief; floodplains and tableland tops remain quiet.
    const double processHillGate = geomorphLandness
        * (1.0 - 0.86 * processMountainGate)
        * (1.0 - 0.82 * processPlateauInner)
        * (1.0 - 0.76 * std::clamp(geomorph.floodplain, 0.0, 1.0));
    const double processHillA = fbmSurface(
        definition.seed ^ 0x5BE0CD19137E2179ULL, w, 175.0, 5);
    const double processHillB = fbmSurface(
        definition.seed ^ 0xCBBB9D5DC1059ED8ULL, w, 640.0, 4);
    elevation += processHillGate * (175.0 * processHillA + 72.0 * processHillB);

    // Hard rocky coasts keep an erosional headland; soft coasts remain depositional slopes.
    const double coastRockNoise = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x082EFA98EC4E6C89ULL, w, 240.0, 3);
    const double coastalRock = bakedCoast * smooth01(0.44, 0.74, coastRockNoise)
        * smooth01(0.38, 0.78, substrateHardness);
    elevation += coastalRock * 300.0;

'''
s = s[:start] + new_block + s[end:]
# Semantics: expose stronger fold/plateau geometry to materials and selection.
s = rep(s,
'''    sample.mountain = bakedMountain;''',
'''    sample.mountain = std::clamp(std::max(bakedMountain, processMountainGate * crestEnvelope), 0.0, 1.0);''', 'mountain semantic')
s = rep(s,
'''    sample.plateau = std::clamp(std::max(bakedTableland, processPlateauCore), 0.0, 1.0);''',
'''    sample.plateau = std::clamp(std::max(bakedTableland, processPlateauInner), 0.0, 1.0);''', 'plateau semantic')
p.write_text(s)

# Evidence must choose actual summits/plateau edges, not merely high masks.
p = Path('native/src/app/Main.cpp')
s = p.read_text()
s = rep(s,
'''            if (captureMode == "mountain") {
                if (terrain.mountain < 0.18 || aboveSea < 2500.0 || aboveSea > 5200.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 30000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 1500.0 || relief > 4800.0) continue;
                captureScore += terrain.mountain * 5.0 + relief / 340.0
                    + aboveSea / 5000.0;
''',
'''            if (captureMode == "mountain") {
                if (terrain.mountain < 0.20 || aboveSea < 2800.0 || aboveSea > 6200.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 26000.0);
                const double relief = r.maxElevation - r.minElevation;
                const double summitDeficit = r.maxElevation - aboveSea;
                if (relief < 1800.0 || relief > 5600.0 || summitDeficit > 320.0) continue;
                captureScore += terrain.mountain * 5.5 + relief / 280.0
                    + aboveSea / 4300.0 - summitDeficit / 260.0;
''', 'global mountain target')
s = rep(s,
'''            } else if (captureMode == "highland") {
                if (terrain.plateau < 0.42 || aboveSea < 2250.0 || aboveSea > 3050.0) continue;
                // A useful plateau target must expose its edge within a few kilometres.
                const LocalReliefStats r = sampleLocalRelief(planet, d, 7000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 500.0 || relief > 2600.0) continue;
                const double edgePreference = std::clamp((aboveSea - r.minElevation) / 900.0, 0.0, 1.0);
                captureScore += edgePreference * 7.5 + terrain.plateau * 4.5
                    + relief / 520.0 - terrain.mountain * 2.6;
''',
'''            } else if (captureMode == "highland") {
                if (terrain.plateau < 0.44 || aboveSea < 2100.0 || aboveSea > 5000.0) continue;
                // R20 plateau target must have genuinely lower terrain inside a 20 km annulus.
                // This selects the cap near an escarpment instead of the featureless interior.
                const LocalReliefStats r = sampleLocalRelief(planet, d, 20000.0);
                const double relief = r.maxElevation - r.minElevation;
                const double edgeDrop = aboveSea - r.minElevation;
                if (edgeDrop < 750.0 || relief < 850.0 || relief > 3600.0) continue;
                captureScore += std::clamp(edgeDrop / 1100.0, 0.0, 2.0) * 8.0
                    + terrain.plateau * 5.0 + relief / 600.0 - terrain.mountain * 2.8;
''', 'global highland target')
s = rep(s,
'''                } else if (captureMode == "highland") {
                    const LocalReliefStats r = sampleLocalRelief(planet, d, 7000.0);
                    const double relief = r.maxElevation - r.minElevation;
                    if (terrain.plateau < 0.38 || h < 2100.0 || h > 3150.0
                        || relief < 420.0) continue;
                    score = terrain.plateau * 8.0 + relief / 420.0
                        + std::clamp((h - r.minElevation) / 1000.0, 0.0, 2.0) * 3.0;
                } else if (captureMode == "mountain") {
                    const LocalReliefStats r = sampleLocalRelief(planet, d, 18000.0);
                    const double relief = r.maxElevation - r.minElevation;
                    if (terrain.mountain < 0.10 || h < 2400.0 || relief < 1200.0) continue;
                    score = terrain.mountain * 7.0 + relief / 300.0 + h / 2400.0;
''',
'''                } else if (captureMode == "highland") {
                    const LocalReliefStats r = sampleLocalRelief(planet, d, 20000.0);
                    const double relief = r.maxElevation - r.minElevation;
                    const double edgeDrop = h - r.minElevation;
                    if (terrain.plateau < 0.42 || h < 2000.0 || h > 5200.0
                        || edgeDrop < 700.0 || relief < 800.0) continue;
                    score = terrain.plateau * 8.0 + edgeDrop / 220.0 + relief / 520.0
                        - terrain.mountain * 2.0;
                } else if (captureMode == "mountain") {
                    const LocalReliefStats r = sampleLocalRelief(planet, d, 22000.0);
                    const double relief = r.maxElevation - r.minElevation;
                    const double summitDeficit = r.maxElevation - h;
                    if (terrain.mountain < 0.14 || h < 2700.0 || relief < 1700.0
                        || summitDeficit > 260.0) continue;
                    score = terrain.mountain * 7.0 + relief / 250.0 + h / 2100.0
                        - summitDeficit / 180.0;
''', 'refined targets')
# Make highland vantage prefer the lower outside world rather than a same-height 30-50km fallback.
s = rep(s,
'''        const std::array<double, 8> relaxedRadii{3000.0, 6000.0, 10000.0, 15000.0,
            22000.0, 30000.0, 40000.0, 52000.0};''',
'''        const std::array<double, 8> relaxedRadii{2500.0, 4500.0, 7000.0, 10000.0,
            14000.0, 19000.0, 26000.0, 34000.0};''', 'relaxed radii')
s = rep(s,
'''                    if (drop < 260.0) continue;
                    score = std::abs(drop - 850.0) * 0.30
                        + terrain.plateau * 1400.0
                        + terrain.mountain * 1100.0
                        + std::abs(standOffMeters - 7000.0) * 0.020;''',
'''                    if (drop < 600.0) continue;
                    const double apparent = std::atan2(drop, std::max(1.0, standOffMeters));
                    score = -apparent * 15000.0
                        + terrain.plateau * 1800.0
                        + terrain.mountain * 1200.0
                        + std::abs(standOffMeters - 11000.0) * 0.014;''', 'relaxed highland vantage')
p.write_text(s)
