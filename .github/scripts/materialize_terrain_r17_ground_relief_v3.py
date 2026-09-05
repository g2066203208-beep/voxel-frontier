from pathlib import Path
p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
old = '''    // R17 walkable micro-relief floor v2. Macro silhouette remains exclusively owned by
    // GlobalGeomorph. Most terminal relief is kept in the broad local/micro bands; fine and
    // ultra bands stay strongly bounded so they cannot recreate the former noisy mountain skin.
    const double detailDamp = geomorphLandness
        * (1.0 - 0.80 * std::max(wetland, geomorph.floodplain))
        * (1.0 - 0.70 * bakedTableland);
    elevation += maxLand * detailDamp
        * (0.0075 * local + 0.0028 * micro + 0.0010 * fine + 0.00020 * ultra);
'''
new = '''    // R17 terminal terrain hierarchy. The global bake is still the sole macro authority.
    // Broad bands provide subdued hills; a separate fixed-metre ground band is sampled at
    // roughly 24/12/6 m lattice scales so the 2 m normal estimator sees real walkable slopes
    // without scaling the effect with an 8.85 km mountain-height budget.
    const double detailDamp = geomorphLandness
        * (1.0 - 0.80 * std::max(wetland, geomorph.floodplain))
        * (1.0 - 0.70 * bakedTableland);
    elevation += maxLand * detailDamp
        * (0.0048 * local + 0.0018 * micro + 0.00055 * fine + 0.00010 * ultra);
    const double groundRelief = fbmSurface(
        definition.seed ^ 0xA24BAED4963EE407ULL, w, 260000.0, 3);
    elevation += detailDamp * 2.8 * groundRelief;
'''
if old not in s:
    if 'R17 terminal terrain hierarchy.' in s: raise SystemExit(0)
    raise SystemExit('R17 v2 detail block not found')
p.write_text(s.replace(old, new, 1))
