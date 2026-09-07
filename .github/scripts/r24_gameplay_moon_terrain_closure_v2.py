from pathlib import Path


def replace_in_file(path: str, old: str, new: str, label: str) -> None:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'v2: {label}: expected exactly one anchor, found {count}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


source_path = Path('.github/scripts/r24_gameplay_moon_terrain_closure.py')
source = source_path.read_text(encoding='utf-8')

bad = r'''replace_once(
    header,
    """    double volcano{};\n    double river{};\n\n    // Subordinate geomorphology/climate fields.\n""",
    """    double volcano{};\n    double river{};\n    double alluvialFan{};\n\n    // Subordinate geomorphology/climate fields.\n""",
)'''

good = r'''replace_once(
    header,
    """    double volcano{};\n    double river{};\n""",
    """    double volcano{};\n    double river{};\n    double alluvialFan{};\n""",
)'''

if bad not in source:
    raise SystemExit('v2: expected legacy header anchor not found in closure script')
source = source.replace(bad, good, 1)

namespace = {'__name__': '__main__', '__file__': str(source_path)}
exec(compile(source, str(source_path), 'exec'), namespace)

main_path = Path('native/src/app/Main.cpp')
main = main_path.read_text(encoding='utf-8')

# VF_TERRAIN_TARGET is an evidence-only deterministic province selector. Sampling the complete
# procedural stack 16k times delayed the first Vulkan frame on CI. 4096 Fibonacci samples still
# resolve the narrow process maxima while bounding startup cost.
old = 'constexpr std::uint32_t evidenceSamples = 16384U;'
new = 'constexpr std::uint32_t evidenceSamples = 4096U;'
if main.count(old) != 1:
    raise SystemExit(f'v2: expected exactly one terrain evidence sample-count anchor, found {main.count(old)}')
main = main.replace(old, new, 1)

# The target marker is consumed by the real-framebuffer harness while stdout is redirected to a
# file. A plain newline may remain block-buffered until shutdown, causing a false timeout even when
# the selected province is already rendering. Flush exactly at the evidence-only marker.
old = '''            std::cout << "R24 terrain target: " << target << " score=" << evidenceScore << '\\n';'''
new = '''            std::cout << "R24 terrain target: " << target << " score=" << evidenceScore << std::endl;'''
if main.count(old) != 1:
    raise SystemExit(f'v2: expected one terrain target log anchor, found {main.count(old)}')
main = main.replace(old, new, 1)

# Prefer a clearly mountainous but not permanently snow-blanketed proof province. Geometry remains
# untouched; this only chooses which deterministic part of the same planet the evidence camera visits.
old = '''                score = terrain.mountain * 3.6 + height01 * 1.1 + terrain.plateBoundary * 0.35
                    - terrain.glacier * 2.2 - std::abs(d.y) * 0.55;'''
new = '''                score = terrain.mountain * 4.4
                    + (1.0 - std::abs(height01 - 0.38)) * 1.25
                    + terrain.plateBoundary * 0.35
                    - terrain.glacier * 2.8
                    - std::max(0.0, height01 - 0.65) * 2.4
                    - std::abs(d.y) * 0.45;'''
if main.count(old) != 1:
    raise SystemExit(f'v2: expected one mountain evidence score anchor, found {main.count(old)}')
main = main.replace(old, new, 1)

# The old aerial proof camera looked steeply down from high altitude, flattening even kilometre-scale
# relief into a white patch. In evidence mode, probe a small ring around the chosen causal province
# and look along the tangent with the largest elevation contrast. This is still the ordinary
# PlanetCamera/Vulkan path and does not alter terrain geometry or gameplay camera behavior.
old = '''            const glm::dvec3 tangent = stableTangent(worldUp);
            camera.setViewDirectionWorld(
                safeNormalize(tangent * 0.78 - worldUp * 0.625, -worldUp),
                worldUp);'''
new = '''            glm::dvec3 localEvidenceTangent = stableTangent(spawnDirection);
            if (const char* targetEnv = std::getenv("VF_TERRAIN_TARGET");
                targetEnv != nullptr && *targetEnv != '\\0') {
                const glm::dvec3 localBitangent = safeNormalize(
                    glm::cross(spawnDirection, localEvidenceTangent),
                    stableTangent(spawnDirection));
                const double centerElevation = vf::samplePlanetTerrain(
                    planet, spawnDirection).elevationMeters;
                double bestContrast = -1.0;
                glm::dvec3 bestTangent = localEvidenceTangent;
                constexpr int directionCount = 16;
                constexpr double probeDistanceMeters = 18000.0;
                for (int i = 0; i < directionCount; ++i) {
                    const double angle = 2.0 * kPi * static_cast<double>(i)
                        / static_cast<double>(directionCount);
                    const glm::dvec3 candidateTangent = safeNormalize(
                        localEvidenceTangent * std::cos(angle)
                            + localBitangent * std::sin(angle),
                        localEvidenceTangent);
                    const glm::dvec3 probeDirection = safeNormalize(
                        spawnDirection
                            + candidateTangent * (probeDistanceMeters / planet.radius),
                        spawnDirection);
                    const vf::PlanetTerrainSample probe = vf::samplePlanetTerrain(
                        planet, probeDirection);
                    const double contrast = std::abs(probe.elevationMeters - centerElevation);
                    if (contrast > bestContrast) {
                        bestContrast = contrast;
                        bestTangent = candidateTangent;
                    }
                }
                localEvidenceTangent = bestTangent;
                std::cout << "R24 terrain evidence view: contrast_m=" << bestContrast
                          << std::endl;
            }
            const glm::dvec3 worldEvidenceTangent = safeNormalize(
                aster.orientation * localEvidenceTangent,
                stableTangent(worldUp));
            double downwardWeight = 0.34;
            if (const char* targetEnv = std::getenv("VF_TERRAIN_TARGET");
                targetEnv != nullptr && *targetEnv != '\\0') {
                const std::string_view target{targetEnv};
                if (target == "mountain") downwardWeight = 0.27;
                else if (target == "rift") downwardWeight = 0.31;
                else if (target == "hydrology" || target == "river") downwardWeight = 0.38;
            }
            const double tangentWeight = std::sqrt(std::max(
                0.0, 1.0 - downwardWeight * downwardWeight));
            camera.setViewDirectionWorld(
                safeNormalize(
                    worldEvidenceTangent * tangentWeight - worldUp * downwardWeight,
                    -worldUp),
                worldUp);'''
if main.count(old) != 1:
    raise SystemExit(f'v2: expected one aerial camera evidence anchor, found {main.count(old)}')
main = main.replace(old, new, 1)

# Replace the binary 160 m contact-detail island with a wide continuous radial transition. Detail
# now grows smoothly from metre-scale near the observer to regional-scale cells over tens of km.
# This prevents the previous "sharp clear square inside blurry terrain" presentation while keeping
# the global hemisphere budget bounded.
old = '''            lodConfig.patchResolution = 10U;
            lodConfig.maxDepth = 20U;
            // The contact zone is processed first by PlanetLodMeshBuilder. Keep enough budget for
            // metre-scale feet/prop geometry but stop distant low-altitude SSE from saturating the
            // old 6000-leaf ceiling every frame.
            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 3600U
                : (buildAltitude < 150000.0 ? 1600U : 700U);
            lodConfig.verticalFovRadians = glm::radians(68.0);
            lodConfig.viewportHeightPixels = 900.0;
            lodConfig.targetScreenErrorPixels = buildAltitude < 25000.0 ? 3.6
                : (buildAltitude < 150000.0 ? 5.0 : 8.0);
            // Contact detail is deliberately local: trees, placed objects and the character need
            // fine geometry nearby; distant terrain can use screen-space error alone.
            lodConfig.nearFieldRadiusMeters = buildAltitude < 25000.0 ? 160.0 : 0.0;
            lodConfig.nearFieldCellMeters = buildAltitude < 25000.0 ? 3.0 : 24.0;
            lodConfig.horizonMarginRadians = 0.018;
            lodConfig.skirtDepthMeters = 6.0;'''
new = '''            lodConfig.patchResolution = buildAltitude < 25000.0 ? 12U : 10U;
            lodConfig.maxDepth = 20U;
            // Low-altitude detail is no longer a binary square. The builder uses a camera-centred
            // geodesic transition band so physical cell size grows continuously with distance.
            lodConfig.maxLeafPatches = buildAltitude < 25000.0 ? 4400U
                : (buildAltitude < 150000.0 ? 2200U : 900U);
            lodConfig.verticalFovRadians = glm::radians(68.0);
            lodConfig.viewportHeightPixels = 900.0;
            lodConfig.targetScreenErrorPixels = buildAltitude < 25000.0 ? 2.8
                : (buildAltitude < 150000.0 ? 4.2 : 6.5);
            lodConfig.nearFieldRadiusMeters = buildAltitude < 25000.0 ? 1.0 : 0.0;
            lodConfig.nearFieldCellMeters = buildAltitude < 25000.0 ? 3.0 : 24.0;
            lodConfig.detailTransitionStartMeters = 180.0;
            lodConfig.detailTransitionEndMeters = 32000.0;
            lodConfig.transitionFarCellMeters = 180.0;
            lodConfig.horizonMarginRadians = 0.020;
            lodConfig.skirtDepthMeters = 6.0;'''
if main.count(old) != 1:
    raise SystemExit(f'v2: expected one runtime LOD config anchor, found {main.count(old)}')
main = main.replace(old, new, 1)

main_path.write_text(main, encoding='utf-8')

# Stronger but still physically bounded kilometre-scale relief. The configured Earthlike maximum
# elevation remains 8.85 km; this only stops convergent mountains and continental rifts from reading
# as nearly flat colour fields at gameplay scale.
surface_path = 'native/src/world/PlanetSurface.cpp'
replace_in_file(
    surface_path,
    '''    const double mountainReliefFactor = 0.30
        + 0.16 * mountainFold
        + 0.13 * std::pow(std::clamp(mountainRidge, 0.0, 1.0), 1.7);''',
    '''    const double mountainBackbone = std::pow(
        std::clamp(mountainRidge, 0.0, 1.0), 1.45);
    const double mountainReliefFactor = 0.36
        + 0.19 * mountainFold
        + 0.20 * mountainBackbone;''',
    'mountain macro relief')
replace_in_file(
    surface_path,
    '''    elevation -= maxLand * 0.16 * rift;
    elevation += maxLand * 0.050 * riftShoulder;''',
    '''    elevation -= maxLand * 0.24 * rift;
    elevation += maxLand * 0.085 * riftShoulder;''',
    'rift graben relief')
replace_in_file(
    surface_path,
    '''    elevation += maxLand * 0.020 * plates.shear * landness * transformWave;''',
    '''    elevation += maxLand * 0.035 * plates.shear * landness * transformWave;''',
    'transform scarp relief')
replace_in_file(
    surface_path,
    '''        regional * (0.0085 + 0.0090 * mountain + 0.0048 * plateau)
        + hillNoise * (0.0042 * hills)
        + local * (0.0031 + 0.0050 * mountain + 0.0014 * coastalCliff)
        + micro * (0.00115 + 0.00060 * mountain)
        + fine * 0.00030
        + (ridged - 0.5) * 0.0024 * mountain)''',
    '''        regional * (0.0085 + 0.0180 * mountain + 0.0048 * plateau)
        + hillNoise * (0.0042 * hills)
        + local * (0.0031 + 0.0100 * mountain + 0.0014 * coastalCliff)
        + micro * (0.00115 + 0.00120 * mountain)
        + fine * 0.00030
        + (ridged - 0.5) * 0.0052 * mountain)''',
    'mountain subordinate relief')

# LOD configuration: wide geodesic detail transition replaces the old binary near-field cutoff.
lod_header = 'native/include/vf/world/PlanetLodMeshBuilder.hpp'
replace_in_file(
    lod_header,
    '''    double nearFieldRadiusMeters{0.0};
    double nearFieldCellMeters{4.0};''',
    '''    double nearFieldRadiusMeters{0.0};
    double nearFieldCellMeters{4.0};

    // When nearFieldRadiusMeters is non-zero, render detail no longer ends at a hard radius.
    // Cell size increases continuously across this camera-centred geodesic band, which removes the
    // visible square where a high-detail quadtree island used to meet coarse regional terrain.
    double detailTransitionStartMeters{180.0};
    double detailTransitionEndMeters{32000.0};
    double transitionFarCellMeters{180.0};''',
    'LOD transition config')

lod_cpp = 'native/src/world/PlanetLodMeshBuilder.cpp'
replace_in_file(
    lod_cpp,
    '''[[nodiscard]] double angleBetween(const glm::dvec3& a, const glm::dvec3& b) noexcept {
    return std::acos(std::clamp(glm::dot(safeNormalize(a), safeNormalize(b)), -1.0, 1.0));
}
''',
    '''[[nodiscard]] double angleBetween(const glm::dvec3& a, const glm::dvec3& b) noexcept {
    return std::acos(std::clamp(glm::dot(safeNormalize(a), safeNormalize(b)), -1.0, 1.0));
}

[[nodiscard]] double smooth01(double value) noexcept {
    const double t = std::clamp(value, 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}
''',
    'LOD smooth helper')

# Center + corners alone miss narrow valleys/rifts inside a patch. Add edge-midpoint probes so SSE
# sees interior relief before it decides a large patch is safe to blur.
replace_in_file(
    lod_cpp,
    '''    std::array<double, 4> elevations{};
    double elevationMin = std::numeric_limits<double>::infinity();
    double elevationMax = -std::numeric_limits<double>::infinity();
    double elevationMean = 0.0;
    for (std::size_t i = 0; i < geometry.corners.size(); ++i) {
        elevations[i] = surface.sample(geometry.corners[i]).elevationMeters;
        elevationMin = std::min(elevationMin, elevations[i]);
        elevationMax = std::max(elevationMax, elevations[i]);
        elevationMean += elevations[i];
    }
    elevationMean /= static_cast<double>(elevations.size());''',
    '''    const double uc = node.u0 + 0.5 * node.size;
    const double vc = node.v0 + 0.5 * node.size;
    const std::array<glm::dvec3, 8> reliefProbes{{
        geometry.corners[0], geometry.corners[1], geometry.corners[2], geometry.corners[3],
        cubeSphereDirection(node.face, uc, node.v0),
        cubeSphereDirection(node.face, uc, node.v0 + node.size),
        cubeSphereDirection(node.face, node.u0, vc),
        cubeSphereDirection(node.face, node.u0 + node.size, vc),
    }};
    double elevationMin = std::numeric_limits<double>::infinity();
    double elevationMax = -std::numeric_limits<double>::infinity();
    double elevationMean = 0.0;
    for (const glm::dvec3& probe : reliefProbes) {
        const double elevation = surface.sample(probe).elevationMeters;
        elevationMin = std::min(elevationMin, elevation);
        elevationMax = std::max(elevationMax, elevation);
        elevationMean += elevation;
    }
    elevationMean /= static_cast<double>(reliefProbes.size());''',
    'LOD interior relief probes')
replace_in_file(
    lod_cpp,
    '''        0.25 * std::max(0.0, elevationMax - elevationMin));''',
    '''        0.40 * std::max(0.0, elevationMax - elevationMin));''',
    'LOD relief sensitivity')

replace_in_file(
    lod_cpp,
    '''    config.nearFieldRadiusMeters = std::clamp(config.nearFieldRadiusMeters, 0.0, 50000.0);
    config.nearFieldCellMeters = std::clamp(config.nearFieldCellMeters, 0.5, 500.0);''',
    '''    config.nearFieldRadiusMeters = std::clamp(config.nearFieldRadiusMeters, 0.0, 50000.0);
    config.nearFieldCellMeters = std::clamp(config.nearFieldCellMeters, 0.5, 500.0);
    config.detailTransitionStartMeters = std::clamp(
        config.detailTransitionStartMeters, 0.0, 200000.0);
    config.detailTransitionEndMeters = std::clamp(
        std::max(config.detailTransitionStartMeters + 1.0, config.detailTransitionEndMeters),
        config.detailTransitionStartMeters + 1.0,
        500000.0);
    config.transitionFarCellMeters = std::clamp(
        std::max(config.nearFieldCellMeters, config.transitionFarCellMeters),
        config.nearFieldCellMeters,
        5000.0);''',
    'LOD transition clamps')

replace_in_file(
    lod_cpp,
    '''        const bool overlapsNearField = config.nearFieldRadiusMeters > 0.0
            && metric.distanceMeters <= config.nearFieldRadiusMeters + metric.spanMeters * 0.72;
        const bool forceContactScale = overlapsNearField
            && nodeCellMeters > config.nearFieldCellMeters;
        if (canSplit && (forceContactScale
            || metric.screenErrorPixels > config.targetScreenErrorPixels)) {''',
    '''        bool forceSmoothDetail = false;
        if (config.nearFieldRadiusMeters > 0.0) {
            const double radius = std::max(1.0, surface.planet().radius);
            const glm::dvec3 cameraDirection = safeNormalize(
                cameraPlanetLocal, metric.centerDirection);
            const double surfaceDistanceMeters = angleBetween(
                cameraDirection, metric.centerDirection) * radius;
            const double cameraAltitudeMeters = std::max(
                0.0, glm::length(cameraPlanetLocal) - radius);
            const double effectiveDistanceMeters = std::sqrt(
                surfaceDistanceMeters * surfaceDistanceMeters
                    + 0.20 * cameraAltitudeMeters * cameraAltitudeMeters);
            const double transitionSpan = std::max(
                1.0, config.detailTransitionEndMeters - config.detailTransitionStartMeters);
            const double transitionT = smooth01(
                (effectiveDistanceMeters - config.detailTransitionStartMeters) / transitionSpan);
            const double nearCell = std::max(0.5, config.nearFieldCellMeters);
            const double farCell = std::max(nearCell, config.transitionFarCellMeters);
            const double desiredCellMeters = std::exp(
                std::log(nearCell) * (1.0 - transitionT)
                    + std::log(farCell) * transitionT);
            forceSmoothDetail = effectiveDistanceMeters <= config.detailTransitionEndMeters
                && nodeCellMeters > desiredCellMeters * 1.08;
        }
        if (canSplit && (forceSmoothDetail
            || metric.screenErrorPixels > config.targetScreenErrorPixels)) {''',
    'smooth geodesic LOD split')

# Keep the existing test intent, but make it explicitly validate that the smooth transition still
# honours contact-scale geometry even though there is no hard 60 m cutoff any more.
test_path = 'native/tests/R24PhysicalPlanetTests.cpp'
replace_in_file(
    test_path,
    '''    config.nearFieldRadiusMeters = 60.0;
    config.nearFieldCellMeters = 2.5;
    config.skirtDepthMeters = 1.0;''',
    '''    config.nearFieldRadiusMeters = 1.0; // enables continuous camera-centred detail transition
    config.nearFieldCellMeters = 2.5;
    config.detailTransitionStartMeters = 8.0;
    config.detailTransitionEndMeters = 180.0;
    config.transitionFarCellMeters = 18.0;
    config.skirtDepthMeters = 1.0;''',
    'near-field transition regression')

print('R24 smooth geodesic terrain LOD + stronger causal relief applied')
