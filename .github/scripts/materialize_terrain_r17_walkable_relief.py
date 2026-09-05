from pathlib import Path

p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
old = '''    // R17 terminal detail only. These amplitudes are intentionally metre-scale and may not
    // move mountain systems, drainage divides or plateau provinces produced by the global bake.
    const double detailDamp = geomorphLandness
        * (1.0 - 0.80 * std::max(wetland, geomorph.floodplain))
        * (1.0 - 0.70 * bakedTableland);
    elevation += maxLand * detailDamp
        * (0.0024 * local + 0.0010 * micro + 0.00045 * fine + 0.00012 * ultra);
'''
new = '''    // R17 walkable micro-relief floor. The macro silhouette remains exclusively owned by
    // GlobalGeomorph; these bounded terminal amplitudes only restore metre/deca-metre slope
    // variation needed for natural ground traversal without rebuilding mountain systems.
    const double detailDamp = geomorphLandness
        * (1.0 - 0.80 * std::max(wetland, geomorph.floodplain))
        * (1.0 - 0.70 * bakedTableland);
    elevation += maxLand * detailDamp
        * (0.0045 * local + 0.0018 * micro + 0.00065 * fine + 0.00015 * ultra);
'''
if old not in s:
    if 'R17 walkable micro-relief floor' in s:
        raise SystemExit(0)
    raise SystemExit('R17 terminal-detail block not found')
s = s.replace(old, new, 1)
p.write_text(s)
