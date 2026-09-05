from pathlib import Path


def rep(s: str, old: str, new: str, label: str) -> str:
    if old not in s:
        raise SystemExit(f'{label} anchor not found')
    return s.replace(old, new, 1)

# Expose baked substrate hardness to the query-time process cascade.
p = Path('native/include/vf/world/PlanetGeomorph.hpp')
s = p.read_text()
s = rep(s, '    double incision{};\n};', '    double incision{};\n    double hardness{};\n};', 'geomorph sample hardness field')
s = rep(s,
'''        s.incision = std::clamp(sampleBilinear(incision, q), 0.0, 1.0);\n''',
'''        s.incision = std::clamp(sampleBilinear(incision, q), 0.0, 1.0);\n        s.hardness = std::clamp(sampleBilinear(hardness, q), 0.0, 1.0);\n''', 'geomorph hardness sample')
p.write_text(s)

# Faithful Demiurge-style query-time detail cascade: macro shape stays baked, but sub-grid
# mountain dissection, resistant tablelands and rolling terrain are driven by baked process fields.
p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
anchor = '''    const double coastEscarpment = bakedCoast;\n\n\n    // Walking-scale geometry.'''
block = '''    const double coastEscarpment = bakedCoast;\n\n    // R19 DEMIURGE PROCESS CASCADE. The 256^2 process bake remains the sole macro authority.\n    // These bands reconstruct terrain BELOW the global process-cell scale, following the upstream\n    // terrainSampler pattern: tectonic ruggedness, substrate hardness, plateau resistance and\n    // erosion state modulate query-time ridged/FBM detail. Noise never decides where a mountain,\n    // plateau or coast exists; baked process fields do.\n    const double substrateHardness = std::clamp(geomorph.hardness, 0.0, 1.0);\n    const double hardnessTerm = 0.72 + 0.56 * substrateHardness;\n    const double processPlateauCore = smooth01(0.22, 0.62, bakedTableland);\n    const double processPlateauInner = smooth01(0.52, 0.86, bakedTableland);\n    const double processPlateauEdge = std::clamp(processPlateauCore - 0.82 * processPlateauInner, 0.0, 1.0);\n    const double processMountainGate = smooth01(0.08, 0.70, bakedMountain)\n        * (1.0 - 0.72 * processPlateauInner) * geomorphLandness;\n\n    // Orogen cascade: ~35 km primary ranges, ~12 km secondary ridges and ~4-5 km spurs.\n    // Positive interfluves and negative valleys are both present, so the belt reads as a mountain\n    // system rather than a raised carpet. Incision strengthens valleys; hard rock preserves ridges.\n    const double orogenA = 1.0 - std::abs(fbmSurface(\n        definition.seed ^ 0xD6E8FEB86659FD93ULL, w, 180.0, 5));\n    const double orogenB = 1.0 - std::abs(fbmSurface(\n        definition.seed ^ 0xA5A3564E27F8862FULL, w, 520.0, 4));\n    const double orogenC = 1.0 - std::abs(fbmSurface(\n        definition.seed ^ 0x9E3779B97F4A7C15ULL, w, 1400.0, 3));\n    const double spineA = std::pow(smooth01(0.30, 0.88, orogenA), 1.55);\n    const double spineB = std::pow(smooth01(0.32, 0.90, orogenB), 1.70);\n    const double spineC = std::pow(smooth01(0.36, 0.92, orogenC), 1.85);\n    const double interfluve = std::clamp(std::max(spineA, std::max(0.82 * spineB, 0.66 * spineC)), 0.0, 1.0);\n    const double processValley = processMountainGate * std::pow(1.0 - interfluve, 1.85)\n        * (0.30 + 0.70 * std::clamp(geomorph.incision, 0.0, 1.0));\n    elevation += processMountainGate * hardnessTerm\n        * (620.0 * (spineA - 0.24) + 360.0 * (spineB - 0.20) + 180.0 * (spineC - 0.16));\n    elevation += processMountainGate * hardnessTerm\n        * 760.0 * std::pow(std::max(spineB, 0.92 * spineC), 2.45);\n    elevation -= processValley * 620.0;\n\n    // Collision tablelands: sharpen a baked plateau mask into a resistant cap-rock shoulder,\n    // while preserving a genuinely broad, quiet top. This is relative residual relief, never a\n    // forced world altitude, so different plateaus still sit at different elevations.\n    const double plateauTopNoise = fbmSurface(\n        definition.seed ^ 0xBB67AE8584CAA73BULL, w, 240.0, 3);\n    elevation += processPlateauInner * (520.0 + 170.0 * hardnessTerm);\n    elevation += processPlateauEdge * (260.0 + 180.0 * hardnessTerm);\n    elevation += processPlateauInner * plateauTopNoise * 48.0;\n\n    // Stable interiors retain rolling relief instead of becoming a billiard table after the\n    // coarse erosion bake. Unlike R13, this is explicitly suppressed inside active orogens and\n    // plateau tops, matching Demiurge's HILL_FLOOR / ruggedness-cascade role.\n    const double processHillGate = geomorphLandness\n        * (1.0 - 0.78 * processMountainGate)\n        * (1.0 - 0.72 * processPlateauInner)\n        * (1.0 - 0.70 * std::clamp(geomorph.floodplain, 0.0, 1.0));\n    const double processHillA = fbmSurface(\n        definition.seed ^ 0x5BE0CD19137E2179ULL, w, 190.0, 5);\n    const double processHillB = fbmSurface(\n        definition.seed ^ 0xCBBB9D5DC1059ED8ULL, w, 720.0, 4);\n    elevation += processHillGate * (150.0 * processHillA + 62.0 * processHillB);\n\n    // Hard rocky coasts preserve short escarpments; soft coasts remain low and depositional.\n    // The coast location still comes from the baked DEM, only its sub-grid cross-section changes.\n    const double coastRockNoise = 0.5 + 0.5 * fbmSurface(\n        definition.seed ^ 0x082EFA98EC4E6C89ULL, w, 260.0, 3);\n    const double coastalRock = bakedCoast * smooth01(0.48, 0.76, coastRockNoise)\n        * smooth01(0.42, 0.82, substrateHardness);\n    elevation += coastalRock * 230.0;\n\n    // Walking-scale geometry.'''
s = rep(s, anchor, block, 'R19 process cascade insertion')
s = rep(s, '    sample.plateau = std::clamp(bakedTableland, 0.0, 1.0);',
        '    sample.plateau = std::clamp(std::max(bakedTableland, processPlateauCore), 0.0, 1.0);', 'plateau semantic')
s = rep(s, '    sample.hills = hills;', '    sample.hills = std::clamp(processHillGate * (0.5 + 0.5 * processHillA), 0.0, 1.0);', 'hill semantic')
s = rep(s, '    sample.canyon = std::max(canyon, geomorph.incision);',
        '    sample.canyon = std::max({canyon, geomorph.incision, processValley});', 'canyon semantic')
s = rep(s, '    sample.coastalCliff = std::clamp(coastEscarpment, 0.0, 1.0);',
        '    sample.coastalCliff = std::clamp(std::max(coastEscarpment, coastalRock), 0.0, 1.0);', 'coastal semantic')
p.write_text(s)

# Capture only geometrically readable examples. This does not alter terrain; it prevents another
# mislabeled flat screenshot from being presented as evidence.
p = Path('native/src/app/Main.cpp')
s = p.read_text()
s = rep(s,
'''    const std::array<double, 7> mountainRadii{5000.0, 7000.0, 9000.0, 12000.0, 15000.0, 19000.0, 24000.0};\n    const std::array<double, 7> highlandRadii{2200.0, 3200.0, 4500.0, 6000.0, 8000.0, 10500.0, 14000.0};\n    const std::array<double, 7> coastRadii{350.0, 500.0, 700.0, 900.0, 1200.0, 1600.0, 2000.0};\n''',
'''    const std::array<double, 7> mountainRadii{3500.0, 5000.0, 7000.0, 9000.0, 12000.0, 16000.0, 22000.0};\n    const std::array<double, 7> highlandRadii{3000.0, 4500.0, 6500.0, 9000.0, 12000.0, 17000.0, 24000.0};\n    const std::array<double, 7> coastRadii{700.0, 1000.0, 1400.0, 1800.0, 2400.0, 3200.0, 4200.0};\n''', 'capture radii')
s = rep(s,
'''                if (!terrain.submerged(planet)) continue;\n                score = std::abs(terrain.elevationMeters + 8.0) * 0.05\n                    + std::abs(standOffMeters - 700.0) * 0.080;\n''',
'''                if (!terrain.submerged(planet)) continue;\n                score = std::abs(terrain.elevationMeters + 12.0) * 0.04\n                    + std::abs(standOffMeters - 1800.0) * 0.050;\n''', 'coast vantage')
s = rep(s,
'''                if (drop < 700.0) continue;\n                const double apparent = std::atan2(drop, std::max(1.0, standOffMeters));\n                score = -apparent * 12000.0\n                    + terrain.mountain * 520.0\n                    + std::abs(standOffMeters - 9000.0) * 0.020;\n''',
'''                if (drop < 900.0) continue;\n                const double apparent = std::atan2(drop, std::max(1.0, standOffMeters));\n                if (apparent < glm::radians(7.0)) continue;\n                score = -apparent * 18000.0\n                    + terrain.mountain * 420.0\n                    + std::abs(standOffMeters - 7000.0) * 0.018;\n''', 'mountain vantage')
s = rep(s,
'''                if (terrain.submerged(planet) || terrain.plateau > 0.20) continue;\n                const double drop = targetElevation - terrain.elevationMeters;\n                if (drop < 380.0) continue;\n                const double apparent = std::atan2(drop, std::max(1.0, standOffMeters));\n                score = -apparent * 13000.0\n                    + terrain.mountain * 1400.0\n                    + terrain.plateau * 2200.0\n                    + std::abs(standOffMeters - 4500.0) * 0.018;\n''',
'''                if (terrain.submerged(planet) || terrain.plateau > 0.18) continue;\n                const double drop = targetElevation - terrain.elevationMeters;\n                if (drop < 500.0) continue;\n                const double apparent = std::atan2(drop, std::max(1.0, standOffMeters));\n                if (apparent < glm::radians(4.0)) continue;\n                score = -apparent * 17000.0\n                    + terrain.mountain * 1500.0\n                    + terrain.plateau * 2600.0\n                    + std::abs(standOffMeters - 8000.0) * 0.016;\n''', 'highland vantage')
p.write_text(s)
