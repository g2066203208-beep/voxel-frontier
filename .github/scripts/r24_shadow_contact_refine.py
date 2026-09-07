from pathlib import Path

MAIN = Path("native/src/app/Main.cpp")
LOD_HEADER = Path("native/include/vf/world/PlanetLodMeshBuilder.hpp")
LOD_SOURCE = Path("native/src/world/PlanetLodMeshBuilder.cpp")
TESTS = Path("native/tests/R24PhysicalPlanetTests.cpp")

text = MAIN.read_text(encoding="utf-8")

capture_block = """        const bool captureHighSpeed = [] {\n            const char* value = std::getenv(\"VF_CAPTURE_HIGH_SPEED\");\n            return value != nullptr && std::string_view{value} == \"1\";\n        }();\n        const bool runtimeDiagnosticsStdout = [] {\n            const char* value = std::getenv(\"VF_RUNTIME_DIAGNOSTICS\");\n            return value != nullptr && std::string_view{value} == \"1\";\n        }();\n        if (captureHighSpeed) {\n            camera.setFlightMode(true);\n            camera.setCreativeFlightSpeedMps(500000.0);\n            std::cout << \"R24 capture high-speed initial_speed_mps=500000\\n\";\n        }\n"""

# Historical migration workflows inserted this capture-only block multiple times. Keep exactly one.
count = text.count(capture_block)
if count < 1:
    raise SystemExit("Main.cpp: capture state block missing")
if count > 1:
    first = text.find(capture_block)
    prefix = text[: first + len(capture_block)]
    suffix = text[first + len(capture_block) :].replace(capture_block, "")
    text = prefix + suffix

# Delete stale evidence-camera overrides. They ran after the new low-angle setup and silently aimed
# the camera back down, making the proof frames useless even when the runtime shadow code was valid.
legacy_downward = """        if (const char* shadowEnv = std::getenv(\"VF_CAPTURE_SHADOW_CONTACT\");\n            shadowEnv != nullptr && std::string_view{shadowEnv} == \"1\") {\n            const glm::dvec3 groundUp = camera.up();\n            const glm::dvec3 tangentForward = safeNormalize(\n                camera.forwardDirection() - groundUp * glm::dot(camera.forwardDirection(), groundUp),\n                stableTangent(groundUp));\n            camera.setViewDirectionWorld(\n                safeNormalize(tangentForward * 0.48 - groundUp * 0.88, -groundUp),\n                groundUp);\n            std::cout << \"R24 capture shadow-contact downward view\\n\";\n        }\n\n"""
legacy_count = text.count(legacy_downward)
text = text.replace(legacy_downward, "")

old_placement = """                const glm::dvec3 cameraDirectionPlanet = safeNormalize(cameraPlanet, patchUp);\n                const glm::dvec3 tangentPlanet = safeNormalize(\n                    forwardPlanet - cameraDirectionPlanet * glm::dot(forwardPlanet, cameraDirectionPlanet),\n                    patchZ);\n                const glm::dvec3 probeDirection = safeNormalize(\n                    cameraDirectionPlanet + tangentPlanet * (11.0 / planet.radius),\n                    cameraDirectionPlanet);\n"""
new_placement = """                const glm::dvec3 cameraDirectionPlanet = safeNormalize(cameraPlanet, patchUp);\n                const glm::dvec3 sunPlanetDirection = safeNormalize(\n                    inverseAster * sunWorldDirection, patchEast);\n                const glm::dvec3 sunHorizontalPlanet = safeNormalize(\n                    sunPlanetDirection\n                        - cameraDirectionPlanet * glm::dot(sunPlanetDirection, cameraDirectionPlanet),\n                    patchEast);\n                // Put the proof object sideways to sunlight so its shadow cannot hide directly\n                // behind the caster from the camera. This affects capture mode only.\n                const glm::dvec3 placementTangentPlanet = safeNormalize(\n                    glm::cross(cameraDirectionPlanet, sunHorizontalPlanet), patchZ);\n                const glm::dvec3 probeDirection = safeNormalize(\n                    cameraDirectionPlanet + placementTangentPlanet * (10.0 / planet.radius),\n                    cameraDirectionPlanet);\n"""
if old_placement in text:
    text = text.replace(old_placement, new_placement, 1)
elif "placementTangentPlanet" not in text:
    raise SystemExit("Main.cpp: contact-probe placement anchor missing")

old_aim = """                vf::appendDebugBox(\n                    dynamicMesh, probeCenter, probeOrientation, probeHalfExtents,\n                    {0.88F, 0.43F, 0.12F}, {0.0F, 0.72F, 0.0F, 0.0F});\n                frameForwardSurface = safeNormalize(probeCenter - cameraSurface, forwardSurface);\n                frameUpSurface = upSurface;\n"""
new_aim = """                vf::appendDebugBox(\n                    dynamicMesh, probeCenter, probeOrientation, probeHalfExtents,\n                    {0.88F, 0.43F, 0.12F}, {0.0F, 0.72F, 0.0F, 0.0F});\n                const glm::dvec3 shadowDirectionSurface = safeNormalize(\n                    -(sunSurfaceDirection\n                        - probeUp * glm::dot(sunSurfaceDirection, probeUp)),\n                    {1.0, 0.0, 0.0});\n                // Aim between the caster base and the first metres of shadow. The screenshot must\n                // contain the exact object-ground junction and the shadow origin in the same frame.\n                const glm::dvec3 proofTarget = probeCenter + shadowDirectionSurface * 3.5;\n                frameForwardSurface = safeNormalize(proofTarget - cameraSurface, forwardSurface);\n                frameUpSurface = upSurface;\n"""
if old_aim in text:
    text = text.replace(old_aim, new_aim, 1)
elif "shadowDirectionSurface" not in text:
    raise SystemExit("Main.cpp: contact-probe aim anchor missing")

# Low-altitude terrain must not exhaust its quadtree budget before reaching contact-scale cells.
text = text.replace(
    "lodConfig.maxDepth = 16U;\n            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 1600U\n                : (buildAltitude < 150000.0 ? 900U : 500U);",
    "lodConfig.maxDepth = 18U;\n            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 6000U\n                : (buildAltitude < 150000.0 ? 1800U : 700U);",
    1,
)
text = text.replace(
    "lodConfig.targetScreenErrorPixels = buildAltitude < 25000.0 ? 3.4\n                : (buildAltitude < 150000.0 ? 5.0 : 8.0);",
    "lodConfig.targetScreenErrorPixels = buildAltitude < 25000.0 ? 1.8\n                : (buildAltitude < 150000.0 ? 4.5 : 8.0);\n            lodConfig.nearFieldRadiusMeters = buildAltitude < 25000.0 ? 1800.0 : 0.0;\n            lodConfig.nearFieldCellMeters = buildAltitude < 25000.0 ? 4.0 : 24.0;",
    1,
)

# PlanetLodMeshBuilder stores planet-scale vertices as float. Recover the authoritative radial
# position in double before converting to the fixed surface render frame. This removes the roughly
# half-metre quantisation possible at a 6,371 km radius without changing PlanetVertex GPU layout.
old_transform = """            for (auto& vertex : result.mesh.vertices) {\n                vertex.position = glm::vec3(toSurfacePoint(glm::dvec3(vertex.position)));\n                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));\n            }\n"""
new_transform = """            for (auto& vertex : result.mesh.vertices) {\n                const glm::dvec3 approximatePlanet = glm::dvec3(vertex.position);\n                const glm::dvec3 vertexDirection = safeNormalize(approximatePlanet, centerUp);\n                const vf::PlanetSurfaceSample preciseSurface = buildSurface.sampleSurface(vertexDirection);\n                vertex.position = glm::vec3(toSurfacePoint(preciseSurface.position));\n                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(preciseSurface.normal)));\n            }\n"""
if old_transform in text:
    text = text.replace(old_transform, new_transform, 1)
elif "preciseSurface = buildSurface.sampleSurface" not in text:
    raise SystemExit("Main.cpp: terrain render-local transform anchor missing")

MAIN.write_text(text, encoding="utf-8")

header = LOD_HEADER.read_text(encoding="utf-8")
header_anchor = """    double flatTerrainErrorFraction{0.60};\n    double reliefErrorScale{1.35};\n"""
header_replacement = """    double flatTerrainErrorFraction{0.60};\n    double reliefErrorScale{1.35};\n\n    // Ground contact, footsteps and prop placement need a physical cell-size guarantee in addition\n    // to projected SSE. Zero nearFieldRadiusMeters disables this constraint for distant globes.\n    double nearFieldRadiusMeters{0.0};\n    double nearFieldCellMeters{4.0};\n"""
if header_anchor in header:
    header = header.replace(header_anchor, header_replacement, 1)
elif "nearFieldRadiusMeters" not in header:
    raise SystemExit("PlanetLodMeshBuilder.hpp: config anchor missing")
LOD_HEADER.write_text(header, encoding="utf-8")

source = LOD_SOURCE.read_text(encoding="utf-8")
clamp_anchor = """    config.flatTerrainErrorFraction = std::clamp(config.flatTerrainErrorFraction, 0.20, 1.0);\n    config.reliefErrorScale = std::clamp(config.reliefErrorScale, 0.5, 4.0);\n"""
clamp_replacement = """    config.flatTerrainErrorFraction = std::clamp(config.flatTerrainErrorFraction, 0.20, 1.0);\n    config.reliefErrorScale = std::clamp(config.reliefErrorScale, 0.5, 4.0);\n    config.nearFieldRadiusMeters = std::clamp(config.nearFieldRadiusMeters, 0.0, 50000.0);\n    config.nearFieldCellMeters = std::clamp(config.nearFieldCellMeters, 0.5, 500.0);\n"""
if clamp_anchor in source:
    source = source.replace(clamp_anchor, clamp_replacement, 1)
elif "config.nearFieldRadiusMeters = std::clamp" not in source:
    raise SystemExit("PlanetLodMeshBuilder.cpp: clamp anchor missing")

split_anchor = """        const bool canSplit = node.depth < config.maxDepth\n            && leaves.size() + pending.size() + 4U < config.maxLeafPatches;\n        if (canSplit && metric.screenErrorPixels > config.targetScreenErrorPixels) {\n"""
split_replacement = """        const bool canSplit = node.depth < config.maxDepth\n            && leaves.size() + pending.size() + 4U < config.maxLeafPatches;\n        const double nodeCellMeters = metric.spanMeters\n            / static_cast<double>(std::max(2U, config.patchResolution));\n        const bool overlapsNearField = config.nearFieldRadiusMeters > 0.0\n            && metric.distanceMeters <= config.nearFieldRadiusMeters + metric.spanMeters * 0.72;\n        const bool forceContactScale = overlapsNearField\n            && nodeCellMeters > config.nearFieldCellMeters;\n        if (canSplit && (forceContactScale\n            || metric.screenErrorPixels > config.targetScreenErrorPixels)) {\n"""
if split_anchor in source:
    source = source.replace(split_anchor, split_replacement, 1)
elif "forceContactScale" not in source:
    raise SystemExit("PlanetLodMeshBuilder.cpp: split anchor missing")
LOD_SOURCE.write_text(source, encoding="utf-8")

tests = TESTS.read_text(encoding="utf-8")
new_test = r'''
void testNearFieldLodEnforcesContactScaleCells() {
    vf::PlanetDefinition planet{};
    planet.radius = 1000.0;
    planet.maxElevation = 30.0;
    planet.maxOceanDepthMeters = 40.0;
    planet.seed = 0x51A7C0DEULL;
    vf::PlanetSurfaceAuthority authority{planet};

    vf::PlanetLodConfig config{};
    config.patchResolution = 8U;
    config.maxDepth = 9U;
    config.maxLeafPatches = 4096U;
    config.viewportHeightPixels = 720.0;
    config.targetScreenErrorPixels = 12.0; // intentionally loose: near-field rule must dominate
    config.nearFieldRadiusMeters = 180.0;
    config.nearFieldCellMeters = 2.5;
    config.skirtDepthMeters = 1.0;

    const glm::dvec3 cameraDirection = glm::normalize(glm::dvec3{0.71, 0.49, 0.51});
    const glm::dvec3 camera = cameraDirection * (planet.radius + 12.0);
    vf::PlanetLodStats stats{};
    const vf::PlanetMesh mesh = vf::buildAdaptivePlanetSurface(authority, camera, config, &stats);
    require(!mesh.vertices.empty(), "near-field contact LOD must produce geometry");
    require(stats.nearestCellMeters <= config.nearFieldCellMeters * 1.05,
        "near-field LOD must refine physical cell size even when projected SSE is permissive");
}

'''
if "void testNearFieldLodEnforcesContactScaleCells()" not in tests:
    marker = "void testClimateRespondsToSunAndCreatesPressureGradientWind() {"
    if marker not in tests:
        raise SystemExit("R24PhysicalPlanetTests.cpp: test insertion anchor missing")
    tests = tests.replace(marker, new_test + marker, 1)
if "    testNearFieldLodEnforcesContactScaleCells();\n" not in tests:
    call_anchor = "    testAdaptiveTerrainLodProducesBoundedFiniteSurface();\n"
    if call_anchor not in tests:
        raise SystemExit("R24PhysicalPlanetTests.cpp: main call anchor missing")
    tests = tests.replace(call_anchor, call_anchor + "    testNearFieldLodEnforcesContactScaleCells();\n", 1)
TESTS.write_text(tests, encoding="utf-8")

print(
    "R24 near-ground repair applied; "
    f"duplicate capture blocks before cleanup={count}; stale downward camera blocks removed={legacy_count}"
)
