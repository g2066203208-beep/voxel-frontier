#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SURFACE = ROOT / "native/src/world/PlanetSurface.cpp"
LOD = ROOT / "native/src/world/PlanetLodMeshBuilder.cpp"
MAIN = ROOT / "native/src/app/Main.cpp"
CMAKE = ROOT / "native/CMakeLists.txt"


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: {label}: expected one anchor, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_before_once(path: Path, anchor: str, payload: str, label: str) -> None:
    replace_once(path, anchor, payload + anchor, label)


# -----------------------------------------------------------------------------
# PlanetSurface: precompute immutable seed geometry once per worker thread and
# provide a render-only spatial band limit for signed fine-detail FBM.
# -----------------------------------------------------------------------------
insert_before_once(
    SURFACE,
    "[[nodiscard]] PlateField samplePlateField(std::uint64_t seed, const glm::dvec3& direction) noexcept {\n",
    r'''struct AbyssSeedConstant {
    glm::dvec3 direction{};
    double width{};
};

struct TerrainSeedConstants {
    std::uint64_t seed{};
    bool initialized{};
    std::array<double, 8> phases{};
    std::array<PlateSeed, kPlateCount> plates{};
    std::array<glm::dvec3, 9> hotspots{};
    std::array<AbyssSeedConstant, 18> abysses{};
};

[[nodiscard]] const TerrainSeedConstants& terrainSeedConstants(std::uint64_t seed) noexcept {
    // Terrain workers repeatedly sample hundreds of thousands of directions for one planet. Plate
    // seeds, hotspot directions and abyss throat locations are functions of the planet seed only;
    // rebuilding them per vertex previously repeated hundreds of sin/cos/hash operations per patch.
    thread_local TerrainSeedConstants cache{};
    if (cache.initialized && cache.seed == seed) return cache;

    cache = {};
    cache.seed = seed;
    cache.initialized = true;
    for (std::size_t i = 0; i < cache.phases.size(); ++i)
        cache.phases[i] = seedPhase(seed, static_cast<std::uint64_t>(i));
    for (std::size_t i = 0; i < cache.plates.size(); ++i)
        cache.plates[i] = makePlate(seed, i);
    for (std::uint64_t i = 0; i < cache.hotspots.size(); ++i)
        cache.hotspots[i] = seededDirection(seed, 2000U + i * 7U);
    for (std::uint64_t i = 0; i < cache.abysses.size(); ++i) {
        cache.abysses[i].direction = seededDirection(
            seed ^ 0x13198A2E03707344ULL, 9000U + i * 31U);
        cache.abysses[i].width = 0.010 + 0.030 * seedUnit(
            seed ^ 0xA4093822299F31D0ULL, 9300U + i * 37U);
    }
    return cache;
}

''',
    "insert immutable seed cache",
)

replace_once(
    SURFACE,
    """[[nodiscard]] PlateField samplePlateField(std::uint64_t seed, const glm::dvec3& direction) noexcept {
    double bestScore = -std::numeric_limits<double>::infinity();
""",
    """[[nodiscard]] PlateField samplePlateField(std::uint64_t seed, const glm::dvec3& direction) noexcept {
    const TerrainSeedConstants& constants = terrainSeedConstants(seed);
    double bestScore = -std::numeric_limits<double>::infinity();
""",
    "plate field uses cache",
)
replace_once(
    SURFACE,
    """    for (std::size_t i = 0; i < kPlateCount; ++i) {
        const PlateSeed plate = makePlate(seed, i);
        const double score = glm::dot(direction, plate.center);
""",
    """    for (std::size_t i = 0; i < kPlateCount; ++i) {
        const PlateSeed& plate = constants.plates[i];
        const double score = glm::dot(direction, plate.center);
""",
    "remove per-sample plate seed construction",
)

# A thread-local sampling threshold lets the public full-detail API stay untouched while render LOD
# calls temporarily request a spatial low-pass. This is safe because terrain workers are independent.
insert_before_once(
    SURFACE,
    "[[nodiscard]] double resolvedOceanDepth(const PlanetDefinition& definition) noexcept {\n",
    r'''thread_local double gMinimumTerrainFeatureMeters = 0.0;

struct TerrainFeatureScope {
    explicit TerrainFeatureScope(double minimumMeters) noexcept
        : previous(gMinimumTerrainFeatureMeters) {
        gMinimumTerrainFeatureMeters = std::max(0.0, minimumMeters);
    }
    ~TerrainFeatureScope() { gMinimumTerrainFeatureMeters = previous; }
    double previous{};
};

[[nodiscard]] double fbmSurfaceBandLimited(
    std::uint64_t seed,
    const glm::dvec3& direction,
    double baseFrequency,
    int octaves,
    double planetRadius) noexcept {
    const double minimumFeature = gMinimumTerrainFeatureMeters;
    if (minimumFeature <= 0.0) return fbmSurface(seed, direction, baseFrequency, octaves);

    double amplitude = 1.0;
    double frequency = baseFrequency;
    double sum = 0.0;
    double normalization = 0.0;
    const double circumference = 2.0 * kPi * std::max(1.0, planetRadius);
    for (int octave = 0; octave < octaves; ++octave) {
        // Approximate spherical wavelength. Once a band is smaller than the render grid's Nyquist
        // threshold it cannot form a stable pixel and is deliberately omitted rather than aliased.
        const double wavelengthMeters = circumference / std::max(1.0, frequency);
        if (wavelengthMeters >= minimumFeature) {
            const std::uint64_t octaveSeed = seedBits(
                seed, 4000U + static_cast<std::uint64_t>(octave) * 29U);
            sum += valueNoise3(octaveSeed, direction * frequency) * amplitude;
        }
        // Keep the original full-band normalization so removing high frequencies behaves as a
        // true low-pass residual instead of amplifying the remaining coarse octaves.
        normalization += amplitude;
        frequency *= 2.07;
        amplitude *= 0.48;
    }
    return normalization > 0.0 ? sum / normalization : 0.0;
}

''',
    "insert render spatial band limit",
)

# Keep semantic/nonlinear morphology full fidelity; filter only signed subordinate detail bands where
# zero is the mathematically neutral contribution.
for old, new, label in [
    (
        "const double regional = fbmSurface(definition.seed ^ 0x6A09E667F3BCC909ULL, w, 720.0, 3);",
        "const double regional = fbmSurfaceBandLimited(definition.seed ^ 0x6A09E667F3BCC909ULL, w, 720.0, 3, definition.radius);",
        "band limit regional detail",
    ),
    (
        "const double duneNoise = fbmSurface(definition.seed ^ 0xCBBB9D5DC1059ED8ULL, w, 26000.0, 2);",
        "const double duneNoise = fbmSurfaceBandLimited(definition.seed ^ 0xCBBB9D5DC1059ED8ULL, w, 26000.0, 2, definition.radius);",
        "band limit dune detail",
    ),
    (
        "const double micro = fbmSurface(definition.seed ^ 0x3C6EF372FE94F82BULL, w, 52000.0, 2);",
        "const double micro = fbmSurfaceBandLimited(definition.seed ^ 0x3C6EF372FE94F82BULL, w, 52000.0, 2, definition.radius);",
        "band limit micro detail",
    ),
    (
        "const double fine = fbmSurface(definition.seed ^ 0xA54FF53A5F1D36F1ULL, w, 125000.0, 2);",
        "const double fine = fbmSurfaceBandLimited(definition.seed ^ 0xA54FF53A5F1D36F1ULL, w, 125000.0, 2, definition.radius);",
        "band limit fine detail",
    ),
    (
        "const double riftFaultFine = fbmSurface(\n        definition.seed ^ 0xD192E819D6EF5218ULL, w, 5200.0, 3);",
        "const double riftFaultFine = fbmSurfaceBandLimited(\n        definition.seed ^ 0xD192E819D6EF5218ULL, w, 5200.0, 3, definition.radius);",
        "band limit fine rift detail",
    ),
]:
    replace_once(SURFACE, old, new, label)

replace_once(
    SURFACE,
    """    const PlateField plates = samplePlateField(definition.seed, d);

    const double p0 = seedPhase(definition.seed, 0U);
    const double p1 = seedPhase(definition.seed, 1U);
    const double p2 = seedPhase(definition.seed, 2U);
    const double p3 = seedPhase(definition.seed, 3U);
    const double p4 = seedPhase(definition.seed, 4U);
    const double p5 = seedPhase(definition.seed, 5U);
    const double p6 = seedPhase(definition.seed, 6U);
    const double p7 = seedPhase(definition.seed, 7U);
""",
    """    const TerrainSeedConstants& seedConstants = terrainSeedConstants(definition.seed);
    const PlateField plates = samplePlateField(definition.seed, d);

    const double p0 = seedConstants.phases[0];
    const double p1 = seedConstants.phases[1];
    const double p2 = seedConstants.phases[2];
    const double p3 = seedConstants.phases[3];
    const double p4 = seedConstants.phases[4];
    const double p5 = seedConstants.phases[5];
    const double p6 = seedConstants.phases[6];
    const double p7 = seedConstants.phases[7];
""",
    "cache phase constants",
)
replace_once(
    SURFACE,
    """    for (std::uint64_t i = 0; i < 9U; ++i) {
        const glm::dvec3 hotspot = seededDirection(definition.seed, 2000U + i * 7U);
""",
    """    for (std::uint64_t i = 0; i < 9U; ++i) {
        const glm::dvec3& hotspot = seedConstants.hotspots[i];
""",
    "cache hotspot directions",
)
replace_once(
    SURFACE,
    """    for (std::uint64_t i = 0; i < 18U; ++i) {
        const glm::dvec3 throat = seededDirection(
            definition.seed ^ 0x13198A2E03707344ULL, 9000U + i * 31U);
        const double width = 0.010 + 0.030 * seedUnit(
            definition.seed ^ 0xA4093822299F31D0ULL, 9300U + i * 37U);
""",
    """    for (std::uint64_t i = 0; i < 18U; ++i) {
        const glm::dvec3& throat = seedConstants.abysses[i].direction;
        const double width = seedConstants.abysses[i].width;
""",
    "cache abyss seeds",
)

# Define the public render-LOD wrapper immediately before the ordinary full-detail entry point.
insert_before_once(
    SURFACE,
    "PlanetTerrainSample samplePlanetTerrain(\n    const PlanetDefinition& definition,\n    const glm::dvec3& directionInput) {\n",
    r'''PlanetTerrainSample samplePlanetTerrainLod(
    const PlanetDefinition& definition,
    const glm::dvec3& directionInput,
    double minimumFeatureMeters) {
    TerrainFeatureScope featureScope{minimumFeatureMeters};
    return samplePlanetTerrain(definition, directionInput);
}

''',
    "define LOD sample wrapper",
)

# -----------------------------------------------------------------------------
# PlanetLodMeshBuilder: stable integer tile keys, cheap-first selection, render
# band limiting and persistent cache reuse. Only cache misses run appendPatch.
# -----------------------------------------------------------------------------
replace_once(
    LOD,
    """struct Node {
    std::uint32_t face{};
    std::uint32_t depth{};
    double u0{-1.0};
    double v0{-1.0};
    double size{2.0};
};
""",
    """struct Node {
    std::uint32_t face{};
    std::uint32_t depth{};
    std::uint32_t x{};
    std::uint32_t y{};
    double u0{-1.0};
    double v0{-1.0};
    double size{2.0};
};

[[nodiscard]] PlanetLodTileKey tileKeyFor(
    const Node& node,
    std::uint32_t patchResolution) noexcept {
    return {node.face, node.depth, node.x, node.y, patchResolution};
}

void appendMeshWithOffset(PlanetMesh& destination, const PlanetMesh& source) {
    const std::uint32_t base = static_cast<std::uint32_t>(destination.vertices.size());
    destination.vertices.insert(destination.vertices.end(), source.vertices.begin(), source.vertices.end());
    destination.indices.reserve(destination.indices.size() + source.indices.size());
    for (const std::uint32_t index : source.indices) destination.indices.push_back(base + index);
}
""",
    "stable integer tile identity",
)

# Clamp new LOD policy.
replace_once(
    LOD,
    """    config.viewConeHalfAngleRadians = std::clamp(
        config.viewConeHalfAngleRadians, 0.25, 3.14159265358979323846);
""",
    """    config.viewConeHalfAngleRadians = std::clamp(
        config.viewConeHalfAngleRadians, 0.25, 3.14159265358979323846);
    config.minimumFeatureCells = std::clamp(config.minimumFeatureCells, 1.0, 8.0);
""",
    "clamp minimum feature cells",
)

# Selection relief probes use an already-known grid footprint to avoid evaluating sub-grid bands.
replace_once(
    LOD,
    """    const PlanetTerrainSample centerTerrain = surface.sample(geometry.centerDirection);

    const double uc = node.u0 + 0.5 * node.size;
""",
    """    const double nodeCellMeters = geometry.spanMeters
        / static_cast<double>(std::max(2U, config.patchResolution));
    const double minimumFeatureMeters = nodeCellMeters * config.minimumFeatureCells;
    const PlanetTerrainSample centerTerrain = surface.sampleLod(
        geometry.centerDirection, minimumFeatureMeters);

    const double uc = node.u0 + 0.5 * node.size;
""",
    "LOD-aware center relief sample",
)
replace_once(
    LOD,
    """        const double elevation = surface.sample(probe).elevationMeters;
""",
    """        const double elevation = surface.sampleLod(probe, minimumFeatureMeters).elevationMeters;
""",
    "LOD-aware relief probes",
)
replace_once(
    LOD,
    """    const double cellMeters = geometry.spanMeters
        / static_cast<double>(std::max(2U, config.patchResolution));
""",
    """    const double cellMeters = nodeCellMeters;
""",
    "reuse node cell metric",
)

# Tile generation uses the tile's own cell footprint to low-pass only unrepresentable signed detail.
replace_once(
    LOD,
    """    const std::size_t pointCount = static_cast<std::size_t>(stride) * stride;

    // Each authoritative terrain point is sampled exactly once for this patch. Normals are then
""",
    """    const std::size_t pointCount = static_cast<std::size_t>(stride) * stride;
    const NodeGeometry nodeGeometry = geometryFor(node, planet.radius);
    const double nodeCellMeters = nodeGeometry.spanMeters / static_cast<double>(resolution);
    const double minimumFeatureMeters = nodeCellMeters * config.minimumFeatureCells;

    // Each authoritative terrain point is sampled exactly once for this patch. Normals are then
""",
    "tile render feature threshold",
)
replace_once(
    LOD,
    """            terrainSamples[index] = surface.sample(directions[index]);
""",
    """            terrainSamples[index] = surface.sampleLod(
                directions[index], minimumFeatureMeters);
""",
    "band-limit tile samples",
)

# Signature accepts persistent cache and authority epoch.
replace_once(
    LOD,
    """PlanetMesh buildAdaptivePlanetSurface(
    const PlanetSurfaceAuthority& surface,
    const glm::dvec3& cameraPlanetLocal,
    const PlanetLodConfig& configInput,
    PlanetLodStats* stats) {
""",
    """PlanetMesh buildAdaptivePlanetSurface(
    const PlanetSurfaceAuthority& surface,
    const glm::dvec3& cameraPlanetLocal,
    const PlanetLodConfig& configInput,
    PlanetLodStats* stats,
    PlanetTileCache* tileCache,
    std::uint64_t tileEpoch) {
""",
    "tile-cache build signature",
)

# Root and child integer coordinates.
replace_once(
    LOD,
    """        const Node root{face, 0U, -1.0, -1.0, 2.0};
""",
    """        const Node root{face, 0U, 0U, 0U, -1.0, -1.0, 2.0};
""",
    "root tile coordinates",
)
replace_once(
    LOD,
    """            const std::array<Node, 4> children{{
                {node.face, depth, node.u0, node.v0, half},
                {node.face, depth, node.u0 + half, node.v0, half},
                {node.face, depth, node.u0, node.v0 + half, half},
                {node.face, depth, node.u0 + half, node.v0 + half, half},
            }};
""",
    """            const std::uint32_t childX = node.x * 2U;
            const std::uint32_t childY = node.y * 2U;
            const std::array<Node, 4> children{{
                {node.face, depth, childX, childY, node.u0, node.v0, half},
                {node.face, depth, childX + 1U, childY, node.u0 + half, node.v0, half},
                {node.face, depth, childX, childY + 1U, node.u0, node.v0 + half, half},
                {node.face, depth, childX + 1U, childY + 1U, node.u0 + half, node.v0 + half, half},
            }};
""",
    "child tile coordinates",
)

# Replace final patch loop with persistent cache reuse. Stats are accumulated for every selected tile,
# independent of whether its immutable mesh came from cache or synthesis.
replace_once(
    LOD,
    """    PatchScratch scratch{};
    scratch.directions.reserve(baseVerticesPerPatch);
    scratch.positions.reserve(baseVerticesPerPatch);
    scratch.terrainSamples.reserve(baseVerticesPerPatch);
    scratch.edge.reserve(config.patchResolution + 1U);
    for (const Node& node : leaves)
        appendPatch(mesh, node, surface, config, &localStats, scratch);
    localStats.leafPatches = leaves.size();
""",
    """    PatchScratch scratch{};
    scratch.directions.reserve(baseVerticesPerPatch);
    scratch.positions.reserve(baseVerticesPerPatch);
    scratch.terrainSamples.reserve(baseVerticesPerPatch);
    scratch.edge.reserve(config.patchResolution + 1U);
    for (const Node& node : leaves) {
        const NodeGeometry geometry = geometryFor(node, surface.planet().radius);
        const double cell = geometry.spanMeters
            / static_cast<double>(std::max(2U, config.patchResolution));
        localStats.deepestLevel = std::max(localStats.deepestLevel, node.depth);
        localStats.nearestCellMeters = std::min(localStats.nearestCellMeters, cell);

        if (tileCache == nullptr) {
            appendPatch(mesh, node, surface, config, nullptr, scratch);
            ++localStats.generatedPatches;
            continue;
        }

        const PlanetLodTileKey key = tileKeyFor(node, config.patchResolution);
        std::shared_ptr<const PlanetMesh> patch = tileCache->find(tileEpoch, key);
        if (patch) {
            ++localStats.tileCacheHits;
        } else {
            ++localStats.tileCacheMisses;
            ++localStats.generatedPatches;
            auto generated = std::make_shared<PlanetMesh>();
            generated->vertices.reserve(baseVerticesPerPatch + skirtVerticesPerPatch);
            generated->indices.reserve(static_cast<std::size_t>(
                6U * config.patchResolution * config.patchResolution
                + (config.skirtDepthMeters > 0.0 ? 24U * config.patchResolution : 0U)));
            appendPatch(*generated, node, surface, config, nullptr, scratch);
            tileCache->insert(tileEpoch, key, generated);
            patch = std::move(generated);
        }
        appendMeshWithOffset(mesh, *patch);
    }
    localStats.leafPatches = leaves.size();
""",
    "persistent tile cache patch loop",
)

# -----------------------------------------------------------------------------
# Main: one persistent cache across terrain recenter/turn builds, deterministic
# hydrology epoch, and runtime telemetry proving cache behavior.
# -----------------------------------------------------------------------------
replace_once(
    MAIN,
    """        glm::dvec3 lodCenterDirection = patchUp;
        glm::dvec3 lodViewForwardDirection = initialViewForwardPlanet;
""",
    """        glm::dvec3 lodCenterDirection = patchUp;
        glm::dvec3 lodViewForwardDirection = initialViewForwardPlanet;
        // Cesium-style persistent CPU tile residency. 512 MiB matches a mature practical default
        // cache scale while keeping active visible tiles non-evictable by virtue of immediate reuse.
        vf::PlanetTileCache terrainTileCache{512ULL * 1024ULL * 1024ULL};
""",
    "instantiate persistent terrain cache",
)

# Compute a stable authority epoch from hydrology content identity rather than raw pointer reuse.
replace_once(
    MAIN,
    """            vf::PlanetSurfaceAuthority buildSurface{planet};
            buildSurface.setHydrology(hydrology);
            vf::PlanetLodConfig lodConfig{};
""",
    """            vf::PlanetSurfaceAuthority buildSurface{planet};
            buildSurface.setHydrology(hydrology);
            std::uint64_t tileEpoch = planet.seed ^ 0x9E3779B97F4A7C15ULL;
            const auto mixEpoch = [&](std::int64_t value) {
                tileEpoch ^= static_cast<std::uint64_t>(value) + 0x9E3779B97F4A7C15ULL
                    + (tileEpoch << 6U) + (tileEpoch >> 2U);
            };
            if (hydrology) {
                const glm::dvec3 hc = hydrology->centerDirection();
                mixEpoch(static_cast<std::int64_t>(hydrology->resolution()));
                mixEpoch(std::llround(hc.x * 1.0e9));
                mixEpoch(std::llround(hc.y * 1.0e9));
                mixEpoch(std::llround(hc.z * 1.0e9));
                mixEpoch(std::llround(hydrology->halfExtentMeters()));
                mixEpoch(std::llround(hydrology->maxIncisionMeters()));
            }
            vf::PlanetLodConfig lodConfig{};
""",
    "derive hydrology tile epoch",
)
replace_once(
    MAIN,
    """            vf::PlanetMesh renderMesh = vf::buildAdaptivePlanetSurface(
                buildSurface, cameraPlanetLocal, lodConfig, &result.stats);
""",
    """            vf::PlanetMesh renderMesh = vf::buildAdaptivePlanetSurface(
                buildSurface, cameraPlanetLocal, lodConfig, &result.stats,
                &terrainTileCache, tileEpoch);
""",
    "use persistent cache in runtime builder",
)
replace_once(
    MAIN,
    """                  << " leaf_patches=" << initialTerrain.stats.leafPatches
                  << " culled_nodes=" << initialTerrain.stats.culledNodes
                  << " hydrology_reused=" << (initialTerrain.reusedHydrology ? 1 : 0) << '\\n';
""",
    """                  << " leaf_patches=" << initialTerrain.stats.leafPatches
                  << " culled_nodes=" << initialTerrain.stats.culledNodes
                  << " tile_hits=" << initialTerrain.stats.tileCacheHits
                  << " tile_misses=" << initialTerrain.stats.tileCacheMisses
                  << " generated_patches=" << initialTerrain.stats.generatedPatches
                  << " hydrology_reused=" << (initialTerrain.reusedHydrology ? 1 : 0) << '\\n';
""",
    "initial tile cache telemetry",
)

# Add telemetry when an async build is adopted as well.
replace_once(
    MAIN,
    """                    currentLodStats = completed.stats;
                    nearTerrain = std::move(completed.renderMesh);
""",
    """                    currentLodStats = completed.stats;
                    nearTerrain = std::move(completed.renderMesh);
                    const vf::PlanetTileCacheStats tileCacheStats = terrainTileCache.stats();
                    std::cout << "R24 STREAM tile_hits=" << completed.stats.tileCacheHits
                              << " tile_misses=" << completed.stats.tileCacheMisses
                              << " generated=" << completed.stats.generatedPatches
                              << " resident_tiles=" << tileCacheStats.entries
                              << " resident_mb="
                              << (static_cast<double>(tileCacheStats.residentBytes)
                                  / (1024.0 * 1024.0))
                              << '\\n';
""",
    "async adoption cache telemetry",
)

# -----------------------------------------------------------------------------
# Build graph + regression test.
# -----------------------------------------------------------------------------
replace_once(
    CMAKE,
    """    src/world/PlanetLodMeshBuilder.cpp
    src/world/ProceduralEcology.cpp
""",
    """    src/world/PlanetLodMeshBuilder.cpp
    src/world/PlanetTileCache.cpp
    src/world/ProceduralEcology.cpp
""",
    "compile tile cache",
)
replace_once(
    CMAKE,
    """    add_executable(vf_r24_hydrologic_canyon_tests tests/R24HydrologicCanyonTests.cpp)
    target_link_libraries(vf_r24_hydrologic_canyon_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_r24_hydrologic_canyon_tests COMMAND vf_r24_hydrologic_canyon_tests)

    if(VF_BUILD_RUNTIME)
""",
    """    add_executable(vf_r24_hydrologic_canyon_tests tests/R24HydrologicCanyonTests.cpp)
    target_link_libraries(vf_r24_hydrologic_canyon_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_r24_hydrologic_canyon_tests COMMAND vf_r24_hydrologic_canyon_tests)
    add_executable(vf_planet_tile_streaming_tests tests/PlanetTileStreamingTests.cpp)
    target_link_libraries(vf_planet_tile_streaming_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_planet_tile_streaming_tests COMMAND vf_planet_tile_streaming_tests)

    if(VF_BUILD_RUNTIME)
""",
    "register tile streaming regression",
)

print("R24 visibility-driven streaming foundation materialized")
