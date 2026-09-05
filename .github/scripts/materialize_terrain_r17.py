from pathlib import Path

p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()

start_marker = '    // R13 connected orogen structure.'
end_marker = '    // R5 river corridor:'
start = s.find(start_marker)
end = s.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('R17 cleanup anchors not found')

replacement = r'''    // R17 SINGLE MACRO AUTHORITY.
    // R16's cube-sphere tectonics + iterative Priority-Flood/MFD erosion bake is the only
    // source allowed to change continent / mountain / plateau / coast macro elevation here.
    // Older R13/R14 ridged-noise mountain reconstruction and forced 2700 m plateau shelves
    // were deliberately removed because they overwrote the physically-conditioned DEM.
    // We retain only semantic masks derived from the baked field for materials/ecology/capture.
    const double bakedMountain = std::clamp(geomorph.mountain, 0.0, 1.0);
    const double bakedHighland = geomorphLandness
        * smooth01(850.0, 2450.0, geomorph.elevationMeters)
        * (1.0 - 0.70 * smooth01(0.20, 0.72, bakedMountain));
    const double bakedTableland = bakedHighland
        * (1.0 - 0.72 * std::clamp(geomorph.incision, 0.0, 1.0));
    const double bakedCoast = coastProximity * geomorphLandness
        * (1.0 - 0.82 * std::clamp(geomorph.floodplain, 0.0, 1.0));

'''
s = s[:start] + replacement + s[end:]

# Remove the legacy hand-built coast height extrusion, but keep a semantic coast mask.
coast_start = s.find('    // Give hydrologically low coastal margins a readable land/sea break')
coast_end = s.find('    // Walking-scale geometry.', coast_start)
if coast_start < 0 or coast_end < 0:
    raise SystemExit('R17 coast cleanup anchors not found')
s = s[:coast_start] + r'''    // R17 coast semantics only: coast shape itself stays in the baked DEM.
    // No post-bake 430 m extrusion is allowed to create artificial coastal walls.
    const double coastEscarpment = bakedCoast;


''' + s[coast_end:]

# Replace large post-bake detail displacement by walking-scale-only amplitudes.
detail_old = r'''    // R9 plateau detail suppression: R8 correctly built a post-bake tableland but this stage
    // still damped detail with the obsolete pre-bake `plateau` mask, re-wrinkling the flat top.
    const double detailDamp = geomorphLandness
        * (1.0 - 0.72 * std::max(wetland, geomorph.floodplain))
        * (1.0 - 0.992 * std::clamp(std::max(plateau, plateauBody), 0.0, 1.0));
    elevation += maxLand * detailDamp
        * (0.0100 * local + 0.0038 * micro + 0.0062 * fine + 0.0018 * ultra);
'''
detail_new = r'''    // R17 terminal detail only. These amplitudes are intentionally metre-scale and may not
    // move mountain systems, drainage divides or plateau provinces produced by the global bake.
    const double detailDamp = geomorphLandness
        * (1.0 - 0.80 * std::max(wetland, geomorph.floodplain))
        * (1.0 - 0.70 * bakedTableland);
    elevation += maxLand * detailDamp
        * (0.0024 * local + 0.0010 * micro + 0.00045 * fine + 0.00012 * ultra);
'''
if detail_old not in s:
    raise SystemExit('R17 detail block not found')
s = s.replace(detail_old, detail_new, 1)

# Export process-derived macro masks rather than removed legacy overlays.
s = s.replace('    sample.mountain = std::max(mountain, geomorph.mountain);',
              '    sample.mountain = bakedMountain;', 1)
s = s.replace('    sample.plateau = std::clamp(std::max(plateauBody, plateauRim * 0.92), 0.0, 1.0);',
              '    sample.plateau = std::clamp(bakedTableland, 0.0, 1.0);', 1)
s = s.replace('    sample.coastalCliff = std::max(coastalCliff, coastEscarpment);',
              '    sample.coastalCliff = std::clamp(coastEscarpment, 0.0, 1.0);', 1)

# The visible river stays tied to the baked downhill receiver/discharge graph. Reduce the
# second-stage incision so it refines the watercourse without reshaping regional relief.
s = s.replace('    elevation -= riverAuthority * (45.0 + 300.0 * uplandCarve);\n'
              '    elevation -= channelCore * (12.0 + 68.0 * uplandCarve);\n'
              '    elevation -= geomorph.incision * (35.0 + 175.0 * uplandCarve);',
              '    elevation -= riverAuthority * (18.0 + 90.0 * uplandCarve);\n'
              '    elevation -= channelCore * (8.0 + 34.0 * uplandCarve);\n'
              '    elevation -= geomorph.incision * (10.0 + 55.0 * uplandCarve);', 1)

if 'R17 SINGLE MACRO AUTHORITY' not in s:
    raise SystemExit('R17 marker missing after patch')
for forbidden in ('R13 connected orogen structure', 'const double plateauShelf = 2700.0',
                  'elevation += 430.0 * coastEscarpment'):
    if forbidden in s:
        raise SystemExit(f'legacy macro authority still present: {forbidden}')

p.write_text(s)
