from pathlib import Path
p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
old = '''    // R17 walkable micro-relief floor. The macro silhouette remains exclusively owned by
    // GlobalGeomorph; these bounded terminal amplitudes only restore metre/deca-metre slope
    // variation needed for natural ground traversal without rebuilding mountain systems.
    const double detailDamp = geomorphLandness
        * (1.0 - 0.80 * std::max(wetland, geomorph.floodplain))
        * (1.0 - 0.70 * bakedTableland);
    elevation += maxLand * detailDamp
        * (0.0045 * local + 0.0018 * micro + 0.00065 * fine + 0.00015 * ultra);
'''
new = '''    // R17 walkable micro-relief floor v2. Macro silhouette remains exclusively owned by
    // GlobalGeomorph. Most terminal relief is kept in the broad local/micro bands; fine and
    // ultra bands stay strongly bounded so they cannot recreate the former noisy mountain skin.
    const double detailDamp = geomorphLandness
        * (1.0 - 0.80 * std::max(wetland, geomorph.floodplain))
        * (1.0 - 0.70 * bakedTableland);
    elevation += maxLand * detailDamp
        * (0.0075 * local + 0.0028 * micro + 0.0010 * fine + 0.00020 * ultra);
'''
if old not in s:
    if 'R17 walkable micro-relief floor v2' in s: raise SystemExit(0)
    raise SystemExit('R17 v1 detail block not found')
p.write_text(s.replace(old, new, 1))
