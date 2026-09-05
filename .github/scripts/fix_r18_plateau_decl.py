from pathlib import Path
p = Path('native/include/vf/world/PlanetGeomorph.hpp')
s = p.read_text()
old = '''        std::vector<float> plateauDrive(kCount, 0.0F);\n        std::vector<float> plateauDrive(kCount, 0.0F);\n'''
new = '''        std::vector<float> plateauDrive(kCount, 0.0F);\n'''
if old not in s:
    raise SystemExit('duplicate plateauDrive declaration not found')
p.write_text(s.replace(old, new, 1))
