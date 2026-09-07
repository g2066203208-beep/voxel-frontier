from pathlib import Path

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

main_path.write_text(main, encoding='utf-8')
print('R24 evidence scan bounded and causal terrain framing upgraded')
