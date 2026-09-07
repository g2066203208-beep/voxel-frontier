from pathlib import Path

SOURCE = Path("native/src/world/PlanetSurface.cpp")
text = SOURCE.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    text = text.replace(old, new, 1)


replace_once(
'''    const double mountainReliefFactor = 0.36
        + 0.19 * mountainFold
        + 0.20 * mountainBackbone;
    elevation += maxLand * mountain * mountainReliefFactor;
''',
'''    // WorldEngine/platec-style ordering: plate convergence carries the macro uplift first.
    // Ridge noise below is subordinate detail, never another full-amplitude mountain range.
    const double mountainReliefFactor = 0.16
        + 0.10 * mountainFold
        + 0.08 * mountainBackbone;
    elevation += maxLand * mountain * mountainReliefFactor;
''',
"macro mountain uplift",
)

replace_once(
'''    const double canyonNoise = fbmSurface(definition.seed ^ 0x5BE0CD19137E2179ULL, w, 8200.0, 3);
    const double abyssNoise = fbmSurface(definition.seed ^ 0x243F6A8885A308D3ULL, w, 3600.0, 4);
''',
'''    // Incision fields deliberately stay below the rock/material octave band. Very high-frequency
    // displacement at kilometre amplitudes creates needles rather than drainage-shaped terrain.
    const double canyonNoise = fbmSurface(definition.seed ^ 0x5BE0CD19137E2179ULL, w, 4200.0, 3);
    const double abyssNoise = fbmSurface(definition.seed ^ 0x243F6A8885A308D3ULL, w, 900.0, 3);
''',
"incision frequencies",
)

replace_once(
'''    // A narrow ridged mask cuts canyon networks into dry elevated interiors. It is intentionally
    // subordinate to the existing river field: broad drainage decides where valleys are; this adds
    // the steep incised morphology visible at human scale.
    const double canyonRidge = 1.0 - std::abs(canyonNoise);
    const double elevatedInterior = std::clamp(
        0.30 + 0.55 * plateau + 0.35 * hills + 0.25 * interior,
        0.0,
        1.0);
    const double canyon = smooth01(0.76, 0.965, canyonRidge)
        * aridity
        * landness
        * elevatedInterior
        * (1.0 - 0.48 * mountain)
        * (1.0 - 0.55 * river);
''',
'''    // Canyon incision follows a broad shoulder plus a narrower core. This mirrors the staged
    // terrain -> erosion ordering used by WorldEngine: drainage-scale morphology shapes the valley,
    // while the narrower ridge field only sharpens the inner channel instead of cutting a wall.
    const double canyonRidge = 1.0 - std::abs(canyonNoise);
    const double canyonShoulder = smooth01(0.50, 0.90, canyonRidge);
    const double canyonCore = smooth01(0.76, 0.965, canyonRidge);
    const double elevatedInterior = std::clamp(
        0.30 + 0.55 * plateau + 0.35 * hills + 0.25 * interior,
        0.0,
        1.0);
    const double canyon = canyonShoulder
        * aridity
        * landness
        * elevatedInterior
        * (1.0 - 0.48 * mountain)
        * (1.0 - 0.55 * river);
''',
"canyon profile",
)

replace_once(
'''        const double throatMask = smooth01(
            std::cos(width * 2.8),
            std::cos(width * 0.30),
            glm::dot(d, throat));
        seededAbyss = std::max(seededAbyss, std::pow(throatMask, 2.15));
    }
    const double fractureAbyss = smooth01(0.78, 0.985, canyonRidge)
        * elevatedInterior * (0.42 + 0.58 * std::abs(abyssNoise));
    const double riftAbyss = rift * (0.38 + 0.62 * std::abs(riftFaultFine));
    const double abyss = std::clamp(
        landness * std::max({seededAbyss, 0.82 * fractureAbyss, 0.62 * riftAbyss}),
        0.0,
        1.0);
''',
'''        const double throatMask = smooth01(
            std::cos(width * 2.8),
            std::cos(width * 0.30),
            glm::dot(d, throat));
        // A lower exponent widens the transition zone so mega-throats read as kilometre-scale bowls
        // instead of cylindrical cut-outs when sampled by the runtime mesh.
        seededAbyss = std::max(seededAbyss, std::pow(throatMask, 1.45));
    }
    const double fractureAbyss = smooth01(0.72, 0.96, canyonRidge)
        * elevatedInterior * (0.52 + 0.48 * std::abs(abyssNoise));
    const double riftAbyss = rift * (0.55 + 0.45 * std::abs(riftFault));
    const double abyss = std::clamp(
        landness * std::max({seededAbyss, 0.34 * fractureAbyss, 0.28 * riftAbyss}),
        0.0,
        1.0);
''',
"abyss profile",
)

replace_once(
'''    // A convergent plate boundary must produce relief, not merely altitude. Convert nested FBM into
    // a ridged multifractal-like signed profile: narrow high crests, broad saddles and carved
    // intermontane valleys. The amplitude is intentionally kilometre-scale inside strong orogeny
    // but fades continuously to zero away from convergent continental boundaries.
    const double orogenySignal = std::clamp(
        0.68 * orogenyRidge + 0.32 * orogenyFine, -1.0, 1.0);
    const double alpineRidge = std::pow(
        std::clamp(1.0 - std::abs(orogenySignal), 0.0, 1.0), 1.50);
    const double alpineValley = std::pow(
        std::clamp(std::abs(orogenySignal) - 0.16, 0.0, 1.0), 1.35);
    const double orogenyMask = smooth01(0.035, 0.62, mountain);
    const double alpineSignedRelief =
        1.28 * alpineRidge - 0.50 - 0.24 * alpineValley
        + 0.24 * orogenyBroad + 0.14 * orogenyFine;
''',
'''    // FastNoiseLite's weighted ridged fractal attenuates later octaves according to the previous
    // ridge response. Apply the same compositional idea here: a broad orogenic envelope controls
    // primary ridges, and primary ridges control the fine ridge band. This keeps the 75 km mountain
    // mass dominant while preventing 8-26 km noise from receiving a second 10+ km displacement.
    const double orogenyMask = smooth01(0.035, 0.62, mountain);
    const double broadUplift = smooth01(-0.35, 0.55, orogenyBroad);
    const double primaryRidge = std::pow(
        std::clamp(1.0 - std::abs(orogenyRidge), 0.0, 1.0), 1.65);
    const double fineRidge = std::pow(
        std::clamp(1.0 - std::abs(orogenyFine), 0.0, 1.0), 1.90);
    const double weightedPrimaryRidge = primaryRidge * (0.30 + 0.70 * broadUplift);
    const double weightedFineRidge = fineRidge * weightedPrimaryRidge;
    const double intermontaneValley = smooth01(0.52, 0.90, std::abs(orogenyRidge))
        * (0.30 + 0.70 * broadUplift);
''',
"weighted orogeny fields",
)

replace_once(
'''    const double riftFaultProfile =
        (riftFaultRidge - 0.46) + 0.24 * riftFaultFine;
''',
'''    const double riftFaultProfile =
        (riftFaultRidge - 0.46) + 0.08 * riftFaultFine;
''',
"rift fine weighting",
)

replace_once(
'''    elevation += maxLand * landRelief * landness;
    const double epicOrogeny = std::clamp(
        alpineSignedRelief + 0.42 * (1.0 - std::abs(orogenyFine)) - 0.18,
        -1.25,
        1.55);
    elevation += maxLand * 0.420 * orogenyMask * epicOrogeny
        * protectedDrainage * iceSmoothing;
    elevation += maxLand * 0.165 * riftReliefMask * riftFaultProfile;
    elevation -= maxLand * 0.145 * rift
        * (0.50 + 0.50 * std::abs(riftFaultFine));
''',
'''    elevation += maxLand * landRelief * landness;
    // Scale-separated orogeny: most vertical energy lives in the broad plate-driven envelope;
    // progressively finer ridges receive progressively smaller amplitudes, like a weighted fractal.
    const double terrainWeathering = protectedDrainage * iceSmoothing;
    elevation += maxLand * 0.155 * orogenyMask * (broadUplift - 0.18)
        * terrainWeathering;
    elevation += maxLand * 0.082 * orogenyMask * (weightedPrimaryRidge - 0.28)
        * terrainWeathering;
    elevation += maxLand * 0.015 * orogenyMask * (weightedFineRidge - 0.18)
        * terrainWeathering;
    elevation -= maxLand * 0.028 * orogenyMask * intermontaneValley
        * terrainWeathering;
    elevation += maxLand * 0.065 * riftReliefMask * riftFaultProfile;
    elevation -= maxLand * 0.045 * rift
        * (0.72 + 0.28 * std::abs(riftFault));
''',
"scale separated displacements",
)

replace_once(
'''    elevation += maxLand * 0.012 * coastalCliff * (0.35 + 0.65 * std::max(0.0, local));
    elevation -= maxLand * 0.105 * canyon * (0.45 + 0.55 * canyonRidge);
    // Mega-abyss / cavern throats are deliberately beyond terrestrial scale. A strong throat can
    // descend ten kilometres or more from its surrounding rim, producing a landmark visible from
    // high-altitude flight. The smooth radial/noise mask avoids a hard circular cut.
    elevation -= maxLand * 0.385 * abyss
        * (0.62 + 0.38 * std::abs(abyssNoise));
''',
'''    elevation += maxLand * 0.012 * coastalCliff * (0.35 + 0.65 * std::max(0.0, local));
    // A broad canyon shoulder carries most incision. The narrow core deepens the channel without
    // turning every high-frequency crest into a vertical wall.
    elevation -= maxLand * 0.060 * canyon * (0.58 + 0.42 * canyonCore);
    // Mega-abyss remains a deliberately non-terrestrial landmark, but its vertical profile is now
    // controlled by a low-frequency modulation and a broad radial throat rather than fracture noise.
    elevation -= maxLand * 0.270 * abyss
        * (0.78 + 0.22 * std::abs(abyssNoise));
''',
"canyon abyss displacement",
)

if "epicOrogeny" in text or "alpineSignedRelief" in text:
    raise SystemExit("legacy full-amplitude orogeny remains after materialization")
if "weightedFineRidge" not in text or "canyonShoulder" not in text:
    raise SystemExit("weighted terrain morphology markers missing")

SOURCE.write_text(text, encoding="utf-8")
print("R24 weighted terrain morphology materialized")
