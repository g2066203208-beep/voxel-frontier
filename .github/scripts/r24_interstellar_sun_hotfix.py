#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

main = ROOT / "native/src/app/Main.cpp"
text = main.read_text(encoding="utf-8")
bad = 'std::cout << "R24 SUN_TRANSIT_ARRIVED\n";'
good = 'std::cout << "R24 SUN_TRANSIT_ARRIVED\\n";'
if bad in text:
    text = text.replace(bad, good, 1)
elif good not in text:
    raise SystemExit("interstellar Sun arrival marker not found after closure patch")
main.write_text(text, encoding="utf-8")

test = ROOT / "native/tests/InterplanetaryFlightTests.cpp"
text = test.read_text(encoding="utf-8")
bad_test = """    star.massKg = 1.0e20;\n    celestial.addBody(star);\n\n    vf::PlanetCamera camera{terrain, &celestial, homeId};\n"""
good_test = """    star.massKg = 1.0e20;\n    const auto starId = celestial.addBody(star);\n    require(starId != 0U, \"interstellar warp test star must be registered\");\n\n    vf::PlanetCamera camera{terrain, &celestial, homeId};\n"""
if bad_test in text:
    text = text.replace(bad_test, good_test, 1)
elif good_test not in text:
    raise SystemExit("interstellar warp test anchor not found after closure patch")
test.write_text(text, encoding="utf-8")

print("R24 interstellar Sun closure hotfix applied")
