from pathlib import Path

MAIN = Path("native/src/app/Main.cpp")
LOD_SOURCE = Path("native/src/world/PlanetLodMeshBuilder.cpp")
TESTS = Path("native/tests/R24PhysicalPlanetTests.cpp")

main = MAIN.read_text(encoding="utf-8")
source = LOD_SOURCE.read_text(encoding="utf-8")
tests = TESTS.read_text(encoding="utf-8")

# The first contact pass proved the constraint itself worked, but the 6000-leaf budget was being
# consumed by broad SSE refinement before the camera neighbourhood reached contact scale. Keep the
# broad budget, but make the physically important near field tiny and deep enough to reach ~3 m.
main_old = """            lodConfig.maxDepth = 18U;\n            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 6000U\n                : (buildAltitude < 150000.0 ? 1800U : 700U);\n"""
main_new = """            lodConfig.maxDepth = 20U;\n            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 6000U\n                : (buildAltitude < 150000.0 ? 1800U : 700U);\n"""
if main_old in main:
    main = main.replace(main_old, main_new, 1)
elif "lodConfig.maxDepth = 20U;" not in main:
    raise SystemExit("Main.cpp: maxDepth contact LOD anchor missing")

main_old = """            lodConfig.nearFieldRadiusMeters = buildAltitude < 25000.0 ? 1800.0 : 0.0;\n            lodConfig.nearFieldCellMeters = buildAltitude < 25000.0 ? 4.0 : 24.0;\n"""
main_new = """            // Contact detail is deliberately local. Refining kilometres of terrain to metre\n            // scale wastes the patch budget and can still leave the actual feet/prop area coarse.\n            lodConfig.nearFieldRadiusMeters = buildAltitude < 25000.0 ? 240.0 : 0.0;\n            lodConfig.nearFieldCellMeters = buildAltitude < 25000.0 ? 3.0 : 24.0;\n"""
if main_old in main:
    main = main.replace(main_old, main_new, 1)
elif "nearFieldRadiusMeters = buildAltitude < 25000.0 ? 240.0" not in main:
    raise SystemExit("Main.cpp: near-field contact radius anchor missing")

# Permit two more quadtree levels. On an Earth-radius cube sphere with 10 cells/patch, level 19 is
# about 2.9 m/cell near this spawn; the old hard clamp at 18 made a 3 m guarantee unreachable.
source = source.replace(
    "config.maxDepth = std::clamp<std::uint32_t>(config.maxDepth, 1U, 18U);",
    "config.maxDepth = std::clamp<std::uint32_t>(config.maxDepth, 1U, 20U);",
    1,
)
if "config.maxDepth = std::clamp<std::uint32_t>(config.maxDepth, 1U, 20U);" not in source:
    raise SystemExit("PlanetLodMeshBuilder.cpp: maxDepth clamp anchor missing")

# Process the camera-nearest root/children first. The traversal is LIFO, so nodes are pushed in
# far-to-near order and the nearest node is popped immediately. This means the contact guarantee is
# satisfied before distant SSE leaves can consume maxLeafPatches.
root_old = """    std::vector<Node> pending;\n    pending.reserve(config.maxLeafPatches * 2U);\n    for (std::uint32_t face = 0; face < 6U; ++face)\n        pending.push_back({face, 0U, -1.0, -1.0, 2.0});\n\n    std::vector<Node> leaves;\n"""
root_new = """    const auto approximateNodeDistance = [&](const Node& node) noexcept {\n        const NodeGeometry geometry = geometryFor(node, surface.planet().radius);\n        return glm::length(cameraPlanetLocal\n            - geometry.centerDirection * surface.planet().radius);\n    };\n\n    std::vector<Node> pending;\n    pending.reserve(config.maxLeafPatches * 2U);\n    std::array<Node, 6> roots{};\n    for (std::uint32_t face = 0; face < roots.size(); ++face)\n        roots[face] = {face, 0U, -1.0, -1.0, 2.0};\n    std::sort(roots.begin(), roots.end(), [&](const Node& a, const Node& b) {\n        return approximateNodeDistance(a) > approximateNodeDistance(b);\n    });\n    for (const Node& root : roots) pending.push_back(root);\n\n    std::vector<Node> leaves;\n"""
if root_old in source:
    source = source.replace(root_old, root_new, 1)
elif "approximateNodeDistance" not in source:
    raise SystemExit("PlanetLodMeshBuilder.cpp: root traversal anchor missing")

children_old = """            const double half = node.size * 0.5;\n            const std::uint32_t depth = node.depth + 1U;\n            pending.push_back({node.face, depth, node.u0, node.v0, half});\n            pending.push_back({node.face, depth, node.u0 + half, node.v0, half});\n            pending.push_back({node.face, depth, node.u0, node.v0 + half, half});\n            pending.push_back({node.face, depth, node.u0 + half, node.v0 + half, half});\n"""
children_new = """            const double half = node.size * 0.5;\n            const std::uint32_t depth = node.depth + 1U;\n            std::array<Node, 4> children{{\n                {node.face, depth, node.u0, node.v0, half},\n                {node.face, depth, node.u0 + half, node.v0, half},\n                {node.face, depth, node.u0, node.v0 + half, half},\n                {node.face, depth, node.u0 + half, node.v0 + half, half},\n            }};\n            std::sort(children.begin(), children.end(), [&](const Node& a, const Node& b) {\n                return approximateNodeDistance(a) > approximateNodeDistance(b);\n            });\n            for (const Node& child : children) pending.push_back(child);\n"""
if children_old in source:
    source = source.replace(children_old, children_new, 1)
elif "std::array<Node, 4> children" not in source:
    raise SystemExit("PlanetLodMeshBuilder.cpp: child traversal anchor missing")

# Tight-budget regression: the near camera patch must still reach the requested cell scale instead
# of losing to far-field SSE work.
tests = tests.replace("    config.maxLeafPatches = 4096U;", "    config.maxLeafPatches = 256U;", 1)
tests = tests.replace("    config.nearFieldRadiusMeters = 180.0;", "    config.nearFieldRadiusMeters = 60.0;", 1)
if "config.maxLeafPatches = 256U;" not in tests or "config.nearFieldRadiusMeters = 60.0;" not in tests:
    raise SystemExit("R24PhysicalPlanetTests.cpp: tight-budget contact regression anchor missing")

MAIN.write_text(main, encoding="utf-8")
LOD_SOURCE.write_text(source, encoding="utf-8")
TESTS.write_text(tests, encoding="utf-8")
print("R24 contact LOD priority repair applied: 240 m near field, <=3 m target, near-first traversal")
