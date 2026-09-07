from pathlib import Path

MAIN = Path("native/src/app/Main.cpp")
text = MAIN.read_text(encoding="utf-8")

old = """            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 6000U\n                : (buildAltitude < 150000.0 ? 1800U : 700U);\n            lodConfig.verticalFovRadians = glm::radians(68.0);\n            lodConfig.viewportHeightPixels = 900.0;\n            lodConfig.targetScreenErrorPixels = buildAltitude < 25000.0 ? 1.8\n                : (buildAltitude < 150000.0 ? 4.5 : 8.0);\n            // Contact detail is deliberately local. Refining kilometres of terrain to metre\n            // scale wastes the patch budget and can still leave the actual feet/prop area coarse.\n            lodConfig.nearFieldRadiusMeters = buildAltitude < 25000.0 ? 240.0 : 0.0;\n            lodConfig.nearFieldCellMeters = buildAltitude < 25000.0 ? 3.0 : 24.0;\n"""
new = """            // The contact zone is processed first by PlanetLodMeshBuilder. Keep enough budget for\n            // metre-scale feet/prop geometry but stop distant low-altitude SSE from saturating the\n            // old 6000-leaf ceiling every frame.\n            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 3600U\n                : (buildAltitude < 150000.0 ? 1600U : 700U);\n            lodConfig.verticalFovRadians = glm::radians(68.0);\n            lodConfig.viewportHeightPixels = 900.0;\n            lodConfig.targetScreenErrorPixels = buildAltitude < 25000.0 ? 3.6\n                : (buildAltitude < 150000.0 ? 5.0 : 8.0);\n            // Contact detail is deliberately local: trees, placed objects and the character need\n            // fine geometry nearby; distant terrain can use screen-space error alone.\n            lodConfig.nearFieldRadiusMeters = buildAltitude < 25000.0 ? 160.0 : 0.0;\n            lodConfig.nearFieldCellMeters = buildAltitude < 25000.0 ? 3.0 : 24.0;\n"""
if old not in text:
    if "lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 3600U" in text:
        print("R24 contact LOD performance bounds already applied")
    else:
        raise SystemExit("Main.cpp: expected contact LOD performance block missing")
else:
    text = text.replace(old, new, 1)
    MAIN.write_text(text, encoding="utf-8")
    print("R24 contact LOD performance bounds applied: 3600 leaves, 160 m contact radius, 3 m target")
