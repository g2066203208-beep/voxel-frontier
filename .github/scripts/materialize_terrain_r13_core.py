from pathlib import Path


def rep(s, old, new, label):
    if old not in s:
        raise SystemExit(f'{label} not found')
    return s.replace(old, new, 1)

p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
if 'R13 connected orogen structure' not in s:
    old = '''    // The global 512x256 process bake owns where mountain belts and drainage basins live,
    // but on an Earth-radius sphere one bake texel spans tens of kilometres.  Reconstruct
    // band-limited range structure *inside that authority mask* instead of bilinearly
    // stretching each bake texel into a smooth ramp.  These wavelengths form range mass,
    // sub-ranges and valley shoulders; walking-scale noise remains a separate layer below.
    // R8 mountain hierarchy: restore the strong R6 macro relief, but place almost all of the
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
'''
    new = '''    // R13 connected orogen structure. The global geomorph bake owns where an orogen exists;
    // this layer reconstructs coherent spines, branch ridges and interfluve valleys inside it.
    // Macro silhouette is tectonic + ridged + erosion-like dissection, not high-frequency noise.
    const double rangeRidgeA = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xD6E8FEB86659FD93ULL, w, 118.0, 5));
    const double rangeRidgeB = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xA5A3564E27F8862FULL, w, 310.0, 4));
    const double rangeRidgeC = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0x9E3779B185EBCA87ULL, w, 760.0, 3));
    const double valleyNoise = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0xC13FA9A902A6328FULL, w, 420.0, 4);
    const double rangeMask = smooth01(0.035, 0.48, geomorph.mountain) * geomorphLandness;
    const double majorSpine = std::pow(smooth01(0.40, 0.84, rangeRidgeA), 1.55);
    const double branchSpine = std::pow(smooth01(0.47, 0.88, rangeRidgeB), 1.80);
    const double summitTeeth = std::pow(smooth01(0.56, 0.93, rangeRidgeC), 2.05);
    const double branchAuthority = majorSpine * (0.38 + 0.62 * branchSpine);
    const double summitAuthority = branchAuthority * (0.46 + 0.54 * summitTeeth);
    const double broadMass = rangeMask * std::pow(smooth01(0.16, 0.72, majorSpine), 1.15);
    const double ridgeMass = rangeMask * branchAuthority;
    const double summitMass = rangeMask * summitAuthority;
    elevation += maxLand * (0.090 * broadMass + 0.105 * ridgeMass + 0.105 * summitMass);
    const double interfluve = rangeMask
        * std::pow(1.0 - std::clamp(std::max(majorSpine, branchSpine * 0.88), 0.0, 1.0), 1.60);
    const double dendriticCut = interfluve
        * std::pow(smooth01(0.48, 0.90, valleyNoise), 1.25);
    elevation -= maxLand * (0.078 * interfluve + 0.050 * dendriticCut);
'''
    s = rep(s, old, new, 'mountain hierarchy')

    old = '''    const double plateauMacro = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x4A7484AA6EA6E483ULL, w, 46.0, 4);
    const double plateauMeso = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x5CB0A9DCBD41FBD4ULL, w, 118.0, 3);
    // R10 tableland profile: a broad bench, a flatter interior and a finite escarpment belt.
    // Keep C1 transitions (no hard steps), but let the interior converge much more strongly to
    // one shelf elevation so a plateau is not visually indistinguishable from rolling upland.
    const double plateauSignal = plateauMacro * 0.84 + plateauMeso * 0.16;
    const double plateauTerrace = globalHighland * smooth01(0.49, 0.595, plateauSignal);
    const double plateauBody = globalHighland * smooth01(0.605, 0.695, plateauSignal);
    const double plateauRim = std::clamp(plateauTerrace - plateauBody * 0.82, 0.0, 1.0);
    const double plateauTopNoise = fbmSurface(
        definition.seed ^ 0x76F988DA831153B5ULL, w, 175.0, 2);
    // R12 visual authority: the inner tableland converges tightly to one shelf while the
    // transition belt retains a finite erosional escarpment. This produces a readable top plane
    // without introducing a discontinuous height step.
    const double plateauShelf = 2660.0 + 20.0 * plateauTopNoise;
    const double plateauBlend = std::clamp(0.74 * plateauTerrace + 0.255 * plateauBody, 0.0, 0.992);
    elevation = elevation * (1.0 - plateauBlend) + plateauShelf * plateauBlend;
    elevation += maxLand * (0.032 * plateauRim + 0.002 * plateauBody);
'''
    new = '''    // R13 tableland: narrower C1 rim and a nearly level inner table create a readable top+scarp.
    const double plateauMacro = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x4A7484AA6EA6E483ULL, w, 92.0, 4);
    const double plateauMeso = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x5CB0A9DCBD41FBD4ULL, w, 260.0, 3);
    const double plateauSignal = plateauMacro * 0.88 + plateauMeso * 0.12;
    const double plateauTerrace = globalHighland * smooth01(0.535, 0.595, plateauSignal);
    const double plateauBody = globalHighland * smooth01(0.615, 0.665, plateauSignal);
    const double plateauRim = std::clamp(plateauTerrace - plateauBody * 0.72, 0.0, 1.0);
    const double plateauTopNoise = fbmSurface(
        definition.seed ^ 0x76F988DA831153B5ULL, w, 210.0, 2);
    const double plateauShelf = 2680.0 + 14.0 * plateauTopNoise;
    const double plateauBlend = std::clamp(0.80 * plateauTerrace + 0.195 * plateauBody, 0.0, 0.995);
    elevation = elevation * (1.0 - plateauBlend) + plateauShelf * plateauBlend;
    elevation += maxLand * (0.043 * plateauRim + 0.0012 * plateauBody);
'''
    s = rep(s, old, new, 'plateau hierarchy')

    old = '''    const double globalCoastBand = geomorphLandness
        * (1.0 - smooth01(55.0, 520.0, std::abs(geomorph.elevationMeters)));
    const double globalCoastRugged = globalCoastBand
        * smooth01(0.40, 0.82, rangeRidgeB);
    const double coastEscarpment = std::pow(globalCoastRugged, 1.22)
        * (0.64 + 0.36 * smooth01(0.32, 0.84, rangeRidgeA));
    // R8 rugged coast: a short, localised 0.5-0.8 km escarpment is allowed at selected rocky
    // margins, while low-energy margins remain beaches/floodplains.
    elevation += maxLand * 0.086 * coastEscarpment;
'''
    new = '''    // R13 coast profiles: independent resistance field makes both real rocky cliffs and low beaches.
    const double globalCoastBand = geomorphLandness
        * (1.0 - smooth01(70.0, 640.0, std::abs(geomorph.elevationMeters)));
    const double coastResistanceNoise = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x91E10DA5C79E7B1DULL, w, 185.0, 4);
    const double rockyCoast = globalCoastBand * smooth01(0.54, 0.76, coastResistanceNoise)
        * (1.0 - 0.62 * std::clamp(geomorph.floodplain, 0.0, 1.0));
    const double coastEscarpment = std::pow(rockyCoast, 1.18)
        * (0.72 + 0.28 * smooth01(0.38, 0.82, rangeRidgeB));
    elevation += maxLand * 0.062 * coastEscarpment;
'''
    s = rep(s, old, new, 'coast hierarchy')

    s = rep(s,
'''        * (1.0 - 0.95 * std::clamp(std::max(plateau, plateauTerrace), 0.0, 1.0));
''',
'''        * (1.0 - 0.975 * std::clamp(std::max(plateau, plateauBody), 0.0, 1.0));
''', 'plateau detail')
    s = rep(s, '    sample.plateau = plateauTerrace;\n',
        '    sample.plateau = std::clamp(std::max(plateauBody, plateauRim * 0.86), 0.0, 1.0);\n', 'plateau export')
    p.write_text(s)

p = Path('native/shaders/planet.slang')
s = p.read_text()
if 'R13 terrain readability' not in s:
    s = rep(s,
'''            baseColor = float3(0.095, 0.365, 0.060);
            baseColor *= 0.94 + coarse * 0.08;
            baseColor += step(0.82, fine) * 0.012 * float3(0.40, 0.80, 0.24);
''',
'''            // R13 terrain readability: restrained olive grass, no neon blanket.
            baseColor = float3(0.115, 0.300, 0.055);
            baseColor *= 0.88 + coarse * 0.18;
            baseColor += step(0.84, fine) * 0.010 * float3(0.30, 0.56, 0.16);
''', 'grass')
    s = rep(s,
'''            baseColor = float3(0.335, 0.325, 0.305) * (0.91 + coarse * 0.13);
            baseColor = lerp(baseColor, float3(0.19, 0.185, 0.175), fracture * 0.34);
''',
'''            baseColor = float3(0.235, 0.225, 0.210) * (0.84 + coarse * 0.24);
            baseColor = lerp(baseColor, float3(0.115, 0.110, 0.105), fracture * 0.46);
''', 'rock')
    s = rep(s,
'''            baseColor = float3(0.735, 0.565, 0.300) * (0.90 + ripple * 0.15);
''',
'''            baseColor = float3(0.675, 0.505, 0.270) * (0.88 + ripple * 0.18);
''', 'sand')
    s = rep(s,
'''    float hazeStrength = materialTag <= -1.5 && materialTag > -4.5 ? 0.90 : 1.0;
''',
'''    // R13 terrain readability: retain terrain contrast through aerial perspective.
    bool terrainTag = materialTag <= -9.5 && materialTag > -19.5;
    float hazeStrength = terrainTag ? 0.56
        : (materialTag <= -1.5 && materialTag > -4.5 ? 0.88 : 1.0);
''', 'haze')
    p.write_text(s)
