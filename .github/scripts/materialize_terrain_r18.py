from pathlib import Path


def rep(s: str, old: str, new: str, label: str) -> str:
    if old not in s:
        if new in s:
            return s
        raise SystemExit(f'{label} not found')
    return s.replace(old, new, 1)

p = Path('native/include/vf/world/PlanetGeomorph.hpp')
s = p.read_text()

s = rep(s,
'''    double mountain{};
    double river{};
''',
'''    double mountain{};
    double plateau{};
    double river{};
''', 'sample plateau field')

s = rep(s,
'''constexpr int kRes = 128;
''',
'''// R18: match the mature erosion reference's 256^2 cubemap process grid. At Earth radius this
// puts the global process cell near the 40 km class instead of R16/R17's ~80 km class; local
// clipmaps still refine the baked field continuously down to metre scale.
constexpr int kRes = 256;
''', 'resolution')
s = rep(s, 'constexpr int kErosionSteps = 30;\n', 'constexpr int kErosionSteps = 60;\n', 'erosion iterations')

s = rep(s,
'''    std::vector<float> mountain;
    std::vector<float> river;
''',
'''    std::vector<float> mountain;
    std::vector<float> plateau;
    std::vector<float> river;
''', 'field plateau vector')
s = rep(s,
'''          mountain(kCount), river(kCount), floodplain(kCount), incision(kCount), hardness(kCount),
''',
'''          mountain(kCount), plateau(kCount), river(kCount), floodplain(kCount), incision(kCount), hardness(kCount),
''', 'plateau ctor')

s = rep(s,
'''        std::vector<float> rawCC(kCount, 0.0F);
        std::vector<float> uplift(kCount, 0.0F);
''',
'''        std::vector<float> rawCC(kCount, 0.0F);
        std::vector<float> uplift(kCount, 0.0F);
        std::vector<float> plateauDrive(kCount, 0.0F);
''', 'plateau drive')

s = rep(s,
'''        spreadMax(neighbors, neighborCount, convSpread, 10, 0.82F);
        spreadMax(neighbors, neighborCount, ccSpread, 13, 0.86F);

        for (int i = 0; i < kCount; ++i) {
            const glm::dvec3 d = directionAt(i / kFaceCells, i % kRes, (i % kFaceCells) / kRes);
            const double paleo = std::pow(ridged(seed ^ 0xB7E151628AED2A6BULL, d, 2.6, 4), 2.6);
            const double land = smooth01(-0.03, 0.10, continental[i]);
            uplift[i] = static_cast<float>(std::clamp(
                land * (0.70 * convSpread[i] + 0.75 * ccSpread[i] + 0.18 * paleo), 0.0, 1.0));
        }
''',
'''        // R18 process-scale orogeny. The doubled grid resolution makes these 8/14-cell
        // spreads roughly 300-550 km wide on Earth: regional belts rather than continent-wide
        // blankets. Ridged fields modulate the UPLIFT FORCING before erosion, never the final DEM.
        spreadMax(neighbors, neighborCount, convSpread, 8, 0.80F);
        spreadMax(neighbors, neighborCount, ccSpread, 14, 0.88F);

        for (int i = 0; i < kCount; ++i) {
            const glm::dvec3 d = directionAt(i / kFaceCells, i % kRes, (i % kFaceCells) / kRes);
            const double paleo = std::pow(ridged(seed ^ 0xB7E151628AED2A6BULL, d, 2.6, 4), 2.6);
            const double land = smooth01(-0.03, 0.10, continental[i]);
            const double primaryRidge = std::pow(ridged(seed ^ 0xD6E8FEB86659FD93ULL, d, 11.0, 4), 1.55);
            const double branchRidge = std::pow(ridged(seed ^ 0xA5A3564E27F8862FULL, d, 29.0, 3), 1.70);
            const double activeOrogen = convSpread[i]
                * (0.66 + 0.42 * primaryRidge + 0.18 * branchRidge);
            // Continental collision has a broad, resistant interior shoulder. It participates in
            // uplift and erosion rather than being flattened to an arbitrary post-bake altitude.
            const double collisionInterior = ccSpread[i]
                * (1.0 - 0.48 * static_cast<double>(rawConv[i]));
            plateauDrive[i] = static_cast<float>(std::clamp(land * collisionInterior, 0.0, 1.0));
            uplift[i] = static_cast<float>(std::clamp(
                land * (0.74 * activeOrogen + 0.86 * collisionInterior + 0.18 * paleo), 0.0, 1.0));
            hardness[i] = static_cast<float>(std::clamp(
                static_cast<double>(hardness[i]) + 0.16 * primaryRidge * convSpread[i]
                    + 0.20 * plateauDrive[i],
                0.0, 1.0));
        }
''', 'orogen forcing')

s = rep(s,
'''        constexpr double upliftRateMeters = 62.0;
''',
'''        // 60 process iterations, close to the mature reference. Total maximum tectonic lift is
        // ~3.1 km before differential erosion, enough for coherent ranges without a post-bake peak stamp.
        constexpr double upliftRateMeters = 52.0;
''', 'uplift rate')

s = rep(s,
'''                    const double talus = 105.0 * (0.72 + 0.56 * hardness[id]);
''',
'''                    // Same physical talus angle as the 128 grid: neighbour spacing halves at R18.
                    const double talus = (105.0 * 128.0 / static_cast<double>(kRes))
                        * (0.72 + 0.56 * hardness[id]);
''', 'talus scaling')

s = rep(s,
'''            const double riverMask = smooth01(0.40, 0.84, qNorm);
            const double lowSlope = 1.0 - smooth01(35.0, 280.0, slope);
''',
'''            const double riverMask = smooth01(0.32, 0.74, qNorm);
            const double slopeScale = 128.0 / static_cast<double>(kRes);
            const double lowSlope = 1.0 - smooth01(35.0 * slopeScale, 280.0 * slopeScale, slope);
''', 'river/floodplain thresholds')

s = rep(s,
'''            const double relief = static_cast<double>(localMax - localMin);
            mountain[id] = static_cast<float>(std::clamp(
                0.72 * uplift[id] + 0.45 * smooth01(450.0, 2600.0, relief), 0.0, 1.0));

            // Depositional broadening is geometry, not just a material label.
''',
'''            const double relief = static_cast<double>(localMax - localMin);
            const double reliefMountain = smooth01(240.0, 1800.0, relief);
            const double activeFront = std::clamp(
                0.82 * static_cast<double>(convSpread[id])
                    + 0.28 * static_cast<double>(rawConv[id]), 0.0, 1.0);
            mountain[id] = static_cast<float>(std::clamp(
                0.68 * activeFront + 0.52 * reliefMountain
                    - 0.22 * static_cast<double>(plateauDrive[id]),
                0.0, 1.0));
            const double broadLevel = 1.0 - smooth01(650.0, 2300.0, relief);
            plateau[id] = static_cast<float>(std::clamp(
                static_cast<double>(plateauDrive[id])
                    * smooth01(900.0, 2200.0, static_cast<double>(elevation[id]))
                    * (0.32 + 0.68 * broadLevel)
                    * (1.0 - 0.62 * static_cast<double>(incision[id])),
                0.0, 1.0));

            // Depositional broadening is geometry, not just a material label.
''', 'mountain plateau classification')

s = rep(s,
'''        s.mountain = std::clamp(sampleBilinear(mountain, q), 0.0, 1.0);
        s.river = std::clamp(sampleBilinear(river, q), 0.0, 1.0);
''',
'''        s.mountain = std::clamp(sampleBilinear(mountain, q), 0.0, 1.0);
        s.plateau = std::clamp(sampleBilinear(plateau, q), 0.0, 1.0);
        s.river = std::clamp(sampleBilinear(river, q), 0.0, 1.0);
''', 'sample plateau')

if 'constexpr int kRes = 256;' not in s or 'constexpr int kErosionSteps = 60;' not in s:
    raise SystemExit('R18 process resolution markers missing')
p.write_text(s)

# Re-key PlanetSurface semantic masks to the R18 baked process fields.
p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
s = rep(s,
'''    const double bakedHighland = geomorphLandness
        * smooth01(850.0, 2450.0, geomorph.elevationMeters)
        * (1.0 - 0.70 * smooth01(0.20, 0.72, bakedMountain));
    const double bakedTableland = bakedHighland
        * (1.0 - 0.72 * std::clamp(geomorph.incision, 0.0, 1.0));
    const double bakedCoast = coastProximity * geomorphLandness
        * (1.0 - 0.82 * std::clamp(geomorph.floodplain, 0.0, 1.0));
''',
'''    const double bakedHighland = geomorphLandness
        * smooth01(850.0, 2450.0, geomorph.elevationMeters)
        * (1.0 - 0.70 * smooth01(0.20, 0.72, bakedMountain));
    const double bakedTableland = std::clamp(std::max(
        geomorph.plateau,
        bakedHighland * (1.0 - 0.72 * std::clamp(geomorph.incision, 0.0, 1.0)) * 0.45),
        0.0, 1.0);
    // Coast semantics must follow the baked DEM itself. R17 still used the obsolete analytic
    // pre-bake continentalness field, which could label inland terrain as coast after authority cleanup.
    const double bakedCoast = geomorphLandness
        * (1.0 - smooth01(80.0, 620.0, std::abs(geomorph.elevationMeters)))
        * (1.0 - 0.82 * std::clamp(geomorph.floodplain, 0.0, 1.0));
''', 'R18 baked semantics')
p.write_text(s)
