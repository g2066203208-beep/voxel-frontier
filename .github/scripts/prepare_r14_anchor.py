from pathlib import Path
p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
old = '''    } else if (sample.river > 0.44) {
        surfaceClass = 8;
    } else if (sample.glacier > 0.38 || sample.elevationMeters > 6200.0) {
'''
new = '''    } else if (sample.river > 0.44) {
        surfaceClass = 8; // hydrology-driven river core
    } else if (sample.glacier > 0.38 || sample.elevationMeters > 6200.0) {
'''
if old in s:
    s = s.replace(old, new, 1)
p.write_text(s)
