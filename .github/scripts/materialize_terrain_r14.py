from pathlib import Path


def rep(s, old, new, label):
    if old not in s:
        raise SystemExit(f'{label} not found')
    return s.replace(old, new, 1)

# --- Terrain morphology + river-bank material authority ---
p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
if 'R14 plateau authority' not in s:
    start = s.index('    // R13 tableland:')
    end = s.index('\n\n    // R5 river corridor:', start)
    plateau = '''    // R14 plateau authority: suitability only decides WHERE a tableland may exist; once a
    // province is selected its inner core receives full flattening authority. R13 multiplied the
    // profile by a soft highland gate, which diluted the shelf and turned it back into rolling hills.
    const double plateauSuitability = smooth01(0.32, 0.72, globalHighland);
    const double plateauMacro = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x4A7484AA6EA6E483ULL, w, 180.0, 4);
    const double plateauMeso = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x5CB0A9DCBD41FBD4ULL, w, 620.0, 3);
    const double plateauSignal = plateauMacro * 0.86 + plateauMeso * 0.14;
    const double plateauProvince = smooth01(0.545, 0.595, plateauSignal);
    const double plateauCore = smooth01(0.625, 0.665, plateauSignal);
    const double plateauTerrace = plateauSuitability * plateauProvince;
    const double plateauBody = plateauSuitability * plateauCore;
    const double plateauRim = plateauSuitability
        * std::clamp(plateauProvince - plateauCore * 0.72, 0.0, 1.0);
    const double plateauTopNoise = fbmSurface(
        definition.seed ^ 0x76F988DA831153B5ULL, w, 250.0, 2);
    const double plateauShelf = 2700.0 + 10.0 * plateauTopNoise;
    // Full authority on the inner table, C1 blend only across the finite rim.
    const double coreBlend = smooth01(0.18, 0.72, plateauBody);
    const double terraceBlend = smooth01(0.16, 0.74, plateauTerrace) * (1.0 - coreBlend);
    const double plateauBlend = std::clamp(coreBlend * 0.999 + terraceBlend * 0.78, 0.0, 0.999);
    elevation = elevation * (1.0 - plateauBlend) + plateauShelf * plateauBlend;
    // Resistant caprock makes the rim read as an escarpment instead of a grassy swell.
    elevation += 290.0 * plateauRim + 18.0 * plateauBody;
'''
    s = s[:start] + plateau + s[end:]

    start = s.index('    // R13 coast profiles:')
    end = s.index('\n\n    // Walking-scale geometry.', start)
    coast = '''    // R14 coast authority: distinguish low-energy beach/floodplain margins from resistant
    // rock coasts using an independent hardness-like field. The rocky profile is confined to the
    // first few hundred metres of positive coastal relief so it produces an actual sea cliff,
    // not a ten-kilometre green ramp.
    const double coastLandSide = smooth01(-30.0, 85.0, geomorph.elevationMeters)
        * (1.0 - smooth01(260.0, 620.0, geomorph.elevationMeters));
    const double coastResistanceNoise = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x91E10DA5C79E7B1DULL, w, 235.0, 4);
    const double hardCoast = coastLandSide * smooth01(0.52, 0.72, coastResistanceNoise)
        * (1.0 - 0.72 * std::clamp(geomorph.floodplain, 0.0, 1.0));
    const double coastEscarpment = std::pow(std::clamp(hardCoast, 0.0, 1.0), 1.12);
    elevation += 430.0 * coastEscarpment;
'''
    s = s[:start] + coast + s[end:]

    # Plateau top: almost no walking-scale displacement, but rim remains textured.
    s = rep(s,
'''        * (1.0 - 0.975 * std::clamp(std::max(plateau, plateauBody), 0.0, 1.0));
''',
'''        * (1.0 - 0.992 * std::clamp(std::max(plateau, plateauBody), 0.0, 1.0));
''', 'plateau detail damp')

    # Export the plateau core and its rim distinctly enough for the capture locator.
    s = rep(s,
'''    sample.plateau = std::clamp(std::max(plateauBody, plateauRim * 0.86), 0.0, 1.0);
''',
'''    sample.plateau = std::clamp(std::max(plateauBody, plateauRim * 0.92), 0.0, 1.0);
''', 'plateau export')

    # River banks: use wet mud transition before canyon/rock classification, eliminating the bright
    # hard outline around an otherwise continuous hydrology-driven channel.
    needle = '''    } else if (sample.river > 0.44) {
        surfaceClass = 8; // hydrology-driven river core
    } else if (sample.glacier > 0.38 || sample.elevationMeters > 6200.0) {
'''
    repl = '''    } else if (sample.river > 0.44) {
        surfaceClass = 8; // hydrology-driven river core
    } else if (sample.river > 0.10) {
        surfaceClass = 4; // saturated river bank / floodplain mud
    } else if (sample.glacier > 0.38 || sample.elevationMeters > 6200.0) {
'''
    if s.count(needle) != 2:
        raise SystemExit(f'river bank classification expected twice, found {s.count(needle)}')
    s = s.replace(needle, repl)
    p.write_text(s)

# --- Mid-distance LOD density + capture locator ---
p = Path('native/src/app/Main.cpp')
s = p.read_text()
if 'R14 mid-distance density' not in s:
    old = '''            const std::array<Ring, 7> rings{{
                {1024.0,        0.0, 384U},   // 5.33 m cell, 2.05 km fine window
                {4096.0,      960.0, 224U},   // 36.6 m cell
                {16384.0,    3900.0, 144U},   // 227.6 m cell
                {65536.0,   15600.0,  96U},   // 1.37 km cell
                {196608.0,  62000.0,  64U},   // 6.14 km cell
                {786432.0, 186000.0,  48U},   // 32.8 km cell
                {2600000.0,740000.0, 40U},   // 130 km orbital support
            }};
'''
    new = '''            // R14 mid-distance density: 5-20 km mountain silhouettes were visibly faceted on
            // the 228 m grid. Spend vertices in rings two/three where ground-level relief is read.
            const std::array<Ring, 7> rings{{
                {1024.0,        0.0, 384U},   // 5.33 m cell, 2.05 km fine window
                {4096.0,      960.0, 256U},   // 32.0 m cell
                {16384.0,    3900.0, 256U},   // 128 m cell
                {65536.0,   15600.0, 160U},   // 819 m cell
                {196608.0,  62000.0,  80U},   // 4.92 km cell
                {786432.0, 186000.0,  48U},   // 32.8 km cell
                {2600000.0,740000.0, 40U},   // 130 km orbital support
            }};
'''
    s = rep(s, old, new, 'clipmap rings')

    # Denser global capture scan only affects evidence mode.
    s = rep(s,
'''    const std::uint32_t sampleCount = captureMode.empty() ? 2048U : 8192U;
''',
'''    const std::uint32_t sampleCount = captureMode.empty() ? 2048U : 24576U;
''', 'capture sample count')

    # Replace strict coast/highland criteria by direct near-shore / near-rim neighborhood tests.
    old = '''            } else if (captureMode == "coast") {
                if (aboveSea < 90.0 || aboveSea > 1400.0 || terrain.coastalCliff < 0.14) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 9000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (r.minElevation > 5.0 || relief < 300.0) continue;
                const double cliffHeightPreference = 1.0
                    - std::clamp(std::abs(aboveSea - 420.0) / 900.0, 0.0, 1.0);
                captureScore += terrain.coastalCliff * 7.2 + relief / 120.0
                    + cliffHeightPreference * 2.8;
            } else if (captureMode == "highland") {
                if (terrain.plateau < 0.34 || aboveSea < 1750.0 || aboveSea > 3100.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 24000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 450.0 || relief > 2600.0) continue;
                const double edgePreference = 1.0
                    - std::clamp(std::abs(terrain.plateau - 0.64) / 0.30, 0.0, 1.0);
                captureScore += edgePreference * 5.0 + terrain.plateau * 4.0
                    + std::min(relief, 2200.0) / 620.0 - terrain.mountain * 1.8;
            }
'''
    new = '''            } else if (captureMode == "coast") {
                if (aboveSea < 100.0 || aboveSea > 850.0 || terrain.coastalCliff < 0.10) continue;
                // Target must genuinely border ocean within ~2 km; no more inland "coast" shots.
                const LocalReliefStats r = sampleLocalRelief(planet, d, 1800.0);
                const double relief = r.maxElevation - r.minElevation;
                if (r.minElevation > -2.0 || relief < 140.0) continue;
                captureScore += terrain.coastalCliff * 8.5 + relief / 80.0
                    - std::abs(aboveSea - 420.0) / 420.0;
            } else if (captureMode == "highland") {
                if (terrain.plateau < 0.42 || aboveSea < 2250.0 || aboveSea > 3050.0) continue;
                // A useful plateau target must expose its edge within a few kilometres.
                const LocalReliefStats r = sampleLocalRelief(planet, d, 7000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 500.0 || relief > 2600.0) continue;
                const double edgePreference = std::clamp((aboveSea - r.minElevation) / 900.0, 0.0, 1.0);
                captureScore += edgePreference * 7.5 + terrain.plateau * 4.5
                    + relief / 520.0 - terrain.mountain * 2.6;
            }
'''
    s = rep(s, old, new, 'coast highland target')

    # Vantage radii keep coast inside fine ring and highland close enough to show the scarp.
    old = '''    const std::array<double, 7> mountainRadii{5000.0, 7000.0, 9000.0, 12000.0, 15000.0, 19000.0, 24000.0};
    const std::array<double, 7> highlandRadii{2800.0, 4000.0, 5500.0, 7000.0, 9000.0, 12000.0, 16000.0};
    const std::array<double, 7> coastRadii{450.0, 650.0, 850.0, 1100.0, 1400.0, 1800.0, 2400.0};
'''
    new = '''    const std::array<double, 7> mountainRadii{5000.0, 7000.0, 9000.0, 12000.0, 15000.0, 19000.0, 24000.0};
    const std::array<double, 7> highlandRadii{2200.0, 3200.0, 4500.0, 6000.0, 8000.0, 10500.0, 14000.0};
    const std::array<double, 7> coastRadii{350.0, 500.0, 700.0, 900.0, 1200.0, 1600.0, 2000.0};
'''
    s = rep(s, old, new, 'vantage radii')

    old = '''            if (mode == "coast") {
                if (!terrain.submerged(planet)) continue;
                score = std::abs(terrain.elevationMeters + 10.0) * 0.08
                    + std::abs(standOffMeters - 850.0) * 0.055;
'''
    new = '''            if (mode == "coast") {
                if (!terrain.submerged(planet)) continue;
                score = std::abs(terrain.elevationMeters + 8.0) * 0.05
                    + std::abs(standOffMeters - 700.0) * 0.080;
'''
    s = rep(s, old, new, 'coast vantage score')

    old = '''            } else {
                if (terrain.submerged(planet) || terrain.plateau > 0.42) continue;
                const double drop = targetElevation - terrain.elevationMeters;
                if (drop < 280.0) continue;
                const double apparent = std::atan2(drop, std::max(1.0, standOffMeters));
                score = -apparent * 10000.0
                    + terrain.mountain * 900.0
                    + terrain.plateau * 900.0
                    + std::abs(standOffMeters - 5500.0) * 0.022;
            }
'''
    new = '''            } else {
                if (terrain.submerged(planet) || terrain.plateau > 0.20) continue;
                const double drop = targetElevation - terrain.elevationMeters;
                if (drop < 380.0) continue;
                const double apparent = std::atan2(drop, std::max(1.0, standOffMeters));
                score = -apparent * 13000.0
                    + terrain.mountain * 1400.0
                    + terrain.plateau * 2200.0
                    + std::abs(standOffMeters - 4500.0) * 0.018;
            }
'''
    s = rep(s, old, new, 'highland vantage score')

    # Safer fallback distances, still local enough to read the feature.
    s = rep(s,
'''        const double fallbackMeters = mode == "coast" ? 850.0
            : (mode == "river" ? 1000.0 : (mode == "highland" ? 5500.0 : 9000.0));
''',
'''        const double fallbackMeters = mode == "coast" ? 700.0
            : (mode == "river" ? 1000.0 : (mode == "highland" ? 4500.0 : 9000.0));
''', 'fallback distance')
    p.write_text(s)

# --- Shader: readable blue water, subdued grass, dark wet river banks ---
p = Path('native/shaders/planet.slang')
s = p.read_text()
if 'R14 water readability' not in s:
    s = rep(s,
'''            baseColor = float3(0.115, 0.300, 0.055);
            baseColor *= 0.88 + coarse * 0.18;
''',
'''            baseColor = float3(0.095, 0.245, 0.045);
            baseColor *= 0.86 + coarse * 0.20;
''', 'grass tone')
    s = rep(s,
'''            float3 shallowScatter = baseColor * (0.58 + 0.28 * saturate(n.y * 0.5 + 0.5));
            float3 sunGlint = specular * stellar * noL * shadow * 0.48;
            return shallowScatter * (1.0 - fresnelWater)
                + reflected * fresnelWater * 1.18
                + sunGlint
                + ambientSpecular * 0.55;
''',
'''            // R14 water readability: keep a saturated blue body under bright sky instead of
            // letting atmospheric reflection bleach the entire near-shore surface white.
            float3 shallowScatter = baseColor * (0.86 + 0.22 * saturate(n.y * 0.5 + 0.5));
            float3 sunGlint = specular * stellar * noL * shadow * 0.32;
            return shallowScatter * (1.0 - fresnelWater * 0.55)
                + reflected * fresnelWater * 0.62
                + sunGlint
                + ambientSpecular * 0.35;
''', 'water lighting')
    s = rep(s,
'''        ? saturate(0.66 + fresnel * 0.32)
''',
'''        ? saturate(0.86 + fresnel * 0.11)
''', 'water opacity')
    p.write_text(s)
