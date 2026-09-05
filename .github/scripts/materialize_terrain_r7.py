from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'{label} block not found')
    return text.replace(old, new, 1)


p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
if 'R7 mountain refinement' in s:
    raise SystemExit(0)

old = '''    // R6 mountain shape: R5 proved that 190-1200 km ridges still read as one giant slope
    // from a player camera. Reconstruct the tectonic authority at 20-160 km wavelengths so
    // individual massifs, passes and inter-range valleys exist inside the same orogenic belt.
    const double rangeRidgeA = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xD6E8FEB86659FD93ULL, w, 260.0, 5));
    const double rangeRidgeB = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xA5A3564E27F8862FULL, w, 760.0, 4));
    const double rangeRidgeC = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0x9E3779B185EBCA87ULL, w, 1900.0, 3));
    const double rangeMask = smooth01(0.05, 0.56, geomorph.mountain) * geomorphLandness;
    const double ridgeCoreA = std::pow(smooth01(0.28, 0.86, rangeRidgeA), 2.00);
    const double ridgeCoreB = std::pow(smooth01(0.32, 0.89, rangeRidgeB), 1.92);
    const double ridgeCoreC = std::pow(smooth01(0.38, 0.93, rangeRidgeC), 1.72);
    const double summitCore = rangeMask * std::pow(
        std::clamp(std::max(ridgeCoreB, ridgeCoreC * 0.92), 0.0, 1.0), 2.35);
    const double rangeRelief = rangeMask * (
        0.160 * (ridgeCoreA - 0.30)
        + 0.100 * (ridgeCoreB - 0.26)
        + 0.060 * (ridgeCoreC - 0.22));
    const double interRangeValley = rangeMask * std::pow(
        1.0 - std::clamp(std::max(ridgeCoreA, ridgeCoreB * 0.82), 0.0, 1.0), 2.0);
    elevation += maxLand * (rangeRelief + 0.220 * summitCore);
    elevation -= maxLand * 0.075 * interRangeValley;
'''
new = '''    // R7 mountain refinement: the R6 screenshot finally produced a recognisable range, but
    // its shortest band could change almost two vertical kilometres across only a few km and
    // read as a wall. Keep the tectonic authority, broaden the summit shoulder and reduce the
    // highest-frequency amplitude so ridges remain dramatic without heightfield cliffs.
    const double rangeRidgeA = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xD6E8FEB86659FD93ULL, w, 220.0, 5));
    const double rangeRidgeB = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xA5A3564E27F8862FULL, w, 540.0, 4));
    const double rangeRidgeC = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0x9E3779B185EBCA87ULL, w, 1050.0, 3));
    const double rangeMask = smooth01(0.05, 0.56, geomorph.mountain) * geomorphLandness;
    const double ridgeCoreA = std::pow(smooth01(0.24, 0.86, rangeRidgeA), 1.68);
    const double ridgeCoreB = std::pow(smooth01(0.29, 0.89, rangeRidgeB), 1.62);
    const double ridgeCoreC = std::pow(smooth01(0.34, 0.93, rangeRidgeC), 1.48);
    const double rangeShoulder = rangeMask * smooth01(
        0.18, 0.68, std::max(ridgeCoreA, ridgeCoreB * 0.82));
    const double summitCore = rangeMask * std::pow(
        std::clamp(std::max(ridgeCoreB, ridgeCoreC * 0.86), 0.0, 1.0), 1.82);
    const double rangeRelief = rangeMask * (
        0.132 * (ridgeCoreA - 0.30)
        + 0.078 * (ridgeCoreB - 0.27)
        + 0.034 * (ridgeCoreC - 0.23));
    const double interRangeValley = rangeMask * std::pow(
        1.0 - std::clamp(std::max(ridgeCoreA, ridgeCoreB * 0.80), 0.0, 1.0), 2.0);
    elevation += maxLand * (rangeRelief + 0.032 * rangeShoulder + 0.142 * summitCore);
    elevation -= maxLand * 0.052 * interRangeValley;
'''
s = replace_once(s, old, new, 'R6 mountain')

old = '''    // R6 plateau shape: a highland must have a broad top and a readable escarpment.
    // Continental-elevation authority still decides where highlands may exist; a regional
    // band-limited mask then flattens only their interiors toward a shelf level and leaves
    // a comparatively sharp rim at the mask boundary.
    const double globalHighland = geomorphLandness
        * smooth01(900.0, 2400.0, geomorph.elevationMeters)
        * (1.0 - smooth01(0.22, 0.68, geomorph.mountain));
    const double plateauMacro = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x4A7484AA6EA6E483ULL, w, 120.0, 4);
    const double plateauMeso = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x5CB0A9DCBD41FBD4ULL, w, 330.0, 3);
    const double plateauSignal = plateauMacro * 0.74 + plateauMeso * 0.26;
    const double plateauBody = globalHighland * smooth01(0.57, 0.69, plateauSignal);
    const double plateauTopNoise = fbmSurface(
        definition.seed ^ 0x76F988DA831153B5ULL, w, 520.0, 2);
    const double plateauShelf = 2350.0 + 260.0 * plateauTopNoise;
    const double plateauBlend = 0.72 * plateauBody;
    elevation = elevation * (1.0 - plateauBlend) + plateauShelf * plateauBlend;
    elevation += maxLand * 0.030 * plateauBody;
'''
new = '''    // R7 plateau refinement: build a broad elevated tableland first, then a narrower flat
    // interior. The transition belt is deliberately wider than a mountain ridge so the edge
    // reads as an escarpment/bench rather than another rounded hill or a numerical wall.
    const double globalHighland = geomorphLandness
        * smooth01(780.0, 2200.0, geomorph.elevationMeters)
        * (1.0 - smooth01(0.18, 0.62, geomorph.mountain));
    const double plateauMacro = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x4A7484AA6EA6E483ULL, w, 72.0, 4);
    const double plateauMeso = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x5CB0A9DCBD41FBD4ULL, w, 190.0, 3);
    const double plateauSignal = plateauMacro * 0.78 + plateauMeso * 0.22;
    const double plateauTerrace = globalHighland * smooth01(0.47, 0.60, plateauSignal);
    const double plateauBody = globalHighland * smooth01(0.56, 0.70, plateauSignal);
    const double plateauRim = std::clamp(plateauTerrace - plateauBody * 0.72, 0.0, 1.0);
    const double plateauTopNoise = fbmSurface(
        definition.seed ^ 0x76F988DA831153B5ULL, w, 260.0, 2);
    const double plateauShelf = 2180.0 + 170.0 * plateauTopNoise;
    const double plateauBlend = 0.84 * plateauTerrace;
    elevation = elevation * (1.0 - plateauBlend) + plateauShelf * plateauBlend;
    elevation += maxLand * (0.014 * plateauRim + 0.010 * plateauBody);
'''
s = replace_once(s, old, new, 'R6 plateau')
s = replace_once(
    s,
    'sample.plateau = std::max(plateau, plateauBody);',
    'sample.plateau = std::max(plateau, plateauTerrace);',
    'plateau sample')
p.write_text(s)

p = Path('native/src/app/Main.cpp')
s = p.read_text()
old = '''    constexpr std::uint32_t sampleCount = 2048U;
    constexpr double goldenAngle = 2.39996322972865332223;
    const glm::dvec3 preferred = safeNormalize({0.72, 0.52, 0.46});
    const glm::dvec3 sunDirection = safeNormalize(sunDirectionInput, {1.0, 0.0, 0.0});
    glm::dvec3 best = preferred;
    double bestScore = -std::numeric_limits<double>::infinity();
    bool found = false;
    const char* captureEnv = std::getenv("VF_CAPTURE_LANDFORM");
    const std::string_view captureMode = captureEnv != nullptr ? std::string_view{captureEnv} : std::string_view{};
'''
new = '''    const char* captureEnv = std::getenv("VF_CAPTURE_LANDFORM");
    const std::string_view captureMode = captureEnv != nullptr ? std::string_view{captureEnv} : std::string_view{};
    const std::uint32_t sampleCount = captureMode.empty() ? 2048U : 8192U;
    constexpr double goldenAngle = 2.39996322972865332223;
    const glm::dvec3 preferred = safeNormalize({0.72, 0.52, 0.46});
    const glm::dvec3 sunDirection = safeNormalize(sunDirectionInput, {1.0, 0.0, 0.0});
    glm::dvec3 best = preferred;
    double bestScore = -std::numeric_limits<double>::infinity();
    bool found = false;
'''
s = replace_once(s, old, new, 'capture sample count')

old = '''            } else if (captureMode == "coast") {
                if (aboveSea < 18.0 || aboveSea > 280.0 || terrain.coastalCliff < 0.08) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 12000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (r.minElevation > -12.0 || relief < 300.0) continue;
                captureScore += terrain.coastalCliff * 5.4 + relief / 170.0
                    - std::abs(aboveSea - 120.0) / 320.0;
            } else if (captureMode == "highland") {
                if (terrain.plateau < 0.40 || aboveSea < 1600.0 || aboveSea > 3300.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 30000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 650.0) continue;
                captureScore += terrain.plateau * 5.6 + aboveSea / 1800.0
                    + std::min(relief, 2400.0) / 900.0 - terrain.mountain * 1.6;
'''
new = '''            } else if (captureMode == "coast") {
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
'''
s = replace_once(s, old, new, 'coast/highland targets')

old = '''    // R6 capture geometry: every target is kept inside the fine/mid clipmap range and
    // mountains/highlands are viewed from a lower flank rather than from kilometres overhead.
    const std::array<double, 5> mountainRadii{8000.0, 12000.0, 18000.0, 26000.0, 38000.0};
    const std::array<double, 5> highlandRadii{8000.0, 12000.0, 18000.0, 26000.0, 36000.0};
    const std::array<double, 5> coastRadii{2500.0, 4500.0, 7000.0, 11000.0, 16000.0};
    const std::array<double, 5> riverRadii{1200.0, 1800.0, 2600.0, 3600.0, 5200.0};
'''
new = '''    // R7 capture geometry: use a guaranteed lateral camera baseline. Highland and mountain
    // evidence deliberately seeks a lower neighbouring surface; coast evidence sits just above
    // sea level and looks inland at an actual rugged margin.
    const std::array<double, 5> mountainRadii{7000.0, 10000.0, 14000.0, 20000.0, 30000.0};
    const std::array<double, 5> highlandRadii{5000.0, 8000.0, 12000.0, 18000.0, 26000.0};
    const std::array<double, 5> coastRadii{2200.0, 3500.0, 5000.0, 7500.0, 11000.0};
    const std::array<double, 5> riverRadii{1200.0, 1800.0, 2600.0, 3600.0, 5200.0};
'''
s = replace_once(s, old, new, 'R6 capture geometry')

s = replace_once(
    s,
    '''    glm::dvec3 best = target;
    double bestScore = std::numeric_limits<double>::infinity();

    for (double standOffMeters : radii) {
''',
    '''    glm::dvec3 best = target;
    double bestScore = std::numeric_limits<double>::infinity();
    bool foundVantage = false;

    for (double standOffMeters : radii) {
''',
    'vantage init')

old = '''            } else if (mode == "mountain") {
                if (terrain.submerged(planet)) continue;
                score = terrain.elevationMeters * 1.45
                    + terrain.mountain * 1900.0
                    + std::abs(standOffMeters - 18000.0) * 0.020;
            } else {
                if (terrain.submerged(planet)) continue;
                score = terrain.elevationMeters * 1.05
                    + terrain.plateau * 1650.0
                    + terrain.mountain * 1200.0
                    + std::abs(standOffMeters - 18000.0) * 0.020;
            }
            if (score < bestScore) {
                bestScore = score;
                best = d;
            }
        }
    }
    return safeNormalize(best, target);
'''
new = '''            } else if (mode == "mountain") {
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
            if (score < bestScore) {
                bestScore = score;
                best = d;
                foundVantage = true;
            }
        }
    }
    if (!foundVantage || glm::dot(best, target) > 0.9999995) {
        const double fallbackMeters = mode == "coast" ? 5000.0
            : (mode == "river" ? 2600.0 : (mode == "highland" ? 12000.0 : 14000.0));
        const double angular = fallbackMeters / std::max(1.0, planet.radius);
        best = safeNormalize(target + east * angular, target);
    }
    return safeNormalize(best, target);
'''
s = replace_once(s, old, new, 'vantage scoring')

old = '''            const double targetLift = captureMode == "mountain" ? 260.0
                : (captureMode == "highland" ? 120.0 : (captureMode == "coast" ? 80.0 : 28.0));
            const double cameraLift = captureMode == "mountain" ? 180.0
                : (captureMode == "highland" ? 180.0
                : (captureMode == "coast" ? 80.0 : 90.0));
'''
new = '''            const double targetLift = captureMode == "mountain" ? 210.0
                : (captureMode == "highland" ? 95.0 : (captureMode == "coast" ? 110.0 : 28.0));
            const double cameraLift = captureMode == "mountain" ? 155.0
                : (captureMode == "highland" ? 120.0
                : (captureMode == "coast" ? 38.0 : 90.0));
'''
s = replace_once(s, old, new, 'camera lifts')
p.write_text(s)
