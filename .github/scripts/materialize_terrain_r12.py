from pathlib import Path


def rep(s: str, old: str, new: str, label: str) -> str:
    if old not in s:
        raise SystemExit(f'{label} not found')
    return s.replace(old, new, 1)

# Terrain/material authority: keep erosion hierarchy, make plateau top and rugged coast readable.
p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
if 'R12 visual authority' not in s:
    s = rep(s,
'''    const double plateauShelf = 2620.0 + 34.0 * plateauTopNoise;
    const double plateauBlend = std::clamp(0.78 * plateauTerrace + 0.20 * plateauBody, 0.0, 0.975);
    elevation = elevation * (1.0 - plateauBlend) + plateauShelf * plateauBlend;
    elevation += maxLand * (0.026 * plateauRim + 0.003 * plateauBody);
''',
'''    // R12 visual authority: the inner tableland converges tightly to one shelf while the
    // transition belt retains a finite erosional escarpment. This produces a readable top plane
    // without introducing a discontinuous height step.
    const double plateauShelf = 2660.0 + 20.0 * plateauTopNoise;
    const double plateauBlend = std::clamp(0.74 * plateauTerrace + 0.255 * plateauBody, 0.0, 0.992);
    elevation = elevation * (1.0 - plateauBlend) + plateauShelf * plateauBlend;
    elevation += maxLand * (0.032 * plateauRim + 0.002 * plateauBody);
''', 'plateau authority')

    s = rep(s,
'''    } else if (sample.mountain > 0.24 || sample.canyon > 0.20
        || sample.coastalCliff > 0.30 || sample.elevationMeters > 2500.0) {
''',
'''    } else if (sample.mountain > 0.24 || sample.canyon > 0.20
        || sample.coastalCliff > 0.16 || sample.elevationMeters > 2500.0) {
''', 'terrain material cliff')
    p.write_text(s)

# Renderer/capture: near coastline must live in the fine clipmap; visual evidence is selected by
# apparent prominence (drop / stand-off), not target elevation alone.
p = Path('native/src/app/Main.cpp')
s = p.read_text()
if 'R12 apparent-prominence evidence' not in s:
    old = '''            const std::array<Ring, 7> rings{{
                {384.0,        0.0, 192U},   // 4.0 m cell
                {1536.0,     360.0, 160U},   // 19.2 m cell
                {6144.0,    1450.0, 112U},   // 109.7 m cell
                {24576.0,   5800.0,  80U},   // 614.4 m cell
                {98304.0,  23200.0,  64U},   // 3.07 km cell
                {393216.0, 93000.0,  48U},   // 16.4 km cell
                {2600000.0,370000.0, 40U},   // 130 km orbital support
            }};
'''
    new = '''            // R12 clipmap density: keep ~5.3 m cells for a full kilometre around the
            // camera so shoreline intersections, rocks and local relief do not fall onto the old
            // 19-110 m grids. Outer rings remain progressively cheaper.
            const std::array<Ring, 7> rings{{
                {1024.0,        0.0, 384U},   // 5.33 m cell, 2.05 km fine window
                {4096.0,      960.0, 224U},   // 36.6 m cell
                {16384.0,    3900.0, 144U},   // 227.6 m cell
                {65536.0,   15600.0,  96U},   // 1.37 km cell
                {196608.0,  62000.0,  64U},   // 6.14 km cell
                {786432.0, 186000.0,  48U},   // 32.8 km cell
                {2600000.0,740000.0, 40U},   // 130 km orbital support
            }};
'''
    s = rep(s, old, new, 'clipmap rings')
    s = rep(s,
'''                // Refresh before the 384 m inner ring morph region.
                const double threshold = altitude < 20000.0 ? 600.0
''',
'''                // R12: refresh well before the expanded 1.024 km fine ring morph region.
                const double threshold = altitude < 20000.0 ? 1450.0
''', 'stream threshold')

    start = s.index('    // R10 evidence geometry:')
    end = s.index('    const auto& radii =', start)
    s = s[:start] + '''    // R12 apparent-prominence evidence: visual quality is governed by angular prominence.
    // Search multiple baselines, then explicitly reward vertical drop per metre of stand-off.
    const std::array<double, 7> mountainRadii{5000.0, 7000.0, 9000.0, 12000.0, 15000.0, 19000.0, 24000.0};
    const std::array<double, 7> highlandRadii{2800.0, 4000.0, 5500.0, 7000.0, 9000.0, 12000.0, 16000.0};
    const std::array<double, 7> coastRadii{450.0, 650.0, 850.0, 1100.0, 1400.0, 1800.0, 2400.0};
    const std::array<double, 7> riverRadii{450.0, 700.0, 1000.0, 1400.0, 2000.0, 2800.0, 3600.0};
''' + s[end:]

    old = '''            if (mode == "coast") {
                if (!terrain.submerged(planet)) continue;
                score = std::abs(terrain.elevationMeters + 12.0) * 0.10
                    + std::abs(standOffMeters - 2300.0) * 0.034;
            } else if (mode == "river") {
                if (terrain.submerged(planet) || terrain.river > 0.10 || terrain.elevationMeters < 120.0) continue;
                score = std::abs(terrain.elevationMeters - targetElevation) * 0.12
                    + terrain.river * 2600.0
                    + std::abs(standOffMeters - 1200.0) * 0.042;
            } else if (mode == "mountain") {
                if (terrain.submerged(planet) || terrain.elevationMeters > 1750.0) continue;
                const double drop = targetElevation - terrain.elevationMeters;
                if (drop < 1500.0) continue;
                score = std::abs(drop - 2300.0) * 0.48
                    + terrain.mountain * 850.0
                    + std::abs(standOffMeters - 17000.0) * 0.026;
            } else {
                if (terrain.submerged(planet) || terrain.elevationMeters > 2050.0) continue;
                const double drop = targetElevation - terrain.elevationMeters;
                if (drop < 500.0) continue;
                score = std::abs(drop - 900.0) * 0.60
                    + terrain.mountain * 980.0
                    + terrain.plateau * 520.0
                    + std::abs(standOffMeters - 10000.0) * 0.032;
            }
'''
    new = '''            if (mode == "coast") {
                if (!terrain.submerged(planet)) continue;
                score = std::abs(terrain.elevationMeters + 10.0) * 0.08
                    + std::abs(standOffMeters - 850.0) * 0.055;
            } else if (mode == "river") {
                if (terrain.submerged(planet) || terrain.river > 0.12 || terrain.elevationMeters < 100.0) continue;
                score = std::abs(terrain.elevationMeters - targetElevation) * 0.11
                    + terrain.river * 2600.0
                    + std::abs(standOffMeters - 1000.0) * 0.040;
            } else if (mode == "mountain") {
                if (terrain.submerged(planet)) continue;
                const double drop = targetElevation - terrain.elevationMeters;
                if (drop < 700.0) continue;
                const double apparent = std::atan2(drop, std::max(1.0, standOffMeters));
                score = -apparent * 12000.0
                    + terrain.mountain * 520.0
                    + std::abs(standOffMeters - 9000.0) * 0.020;
            } else {
                if (terrain.submerged(planet) || terrain.plateau > 0.42) continue;
                const double drop = targetElevation - terrain.elevationMeters;
                if (drop < 280.0) continue;
                const double apparent = std::atan2(drop, std::max(1.0, standOffMeters));
                score = -apparent * 10000.0
                    + terrain.mountain * 900.0
                    + terrain.plateau * 900.0
                    + std::abs(standOffMeters - 5500.0) * 0.022;
            }
'''
    s = rep(s, old, new, 'primary vantage')

    s = rep(s,
'''        const double fallbackMeters = mode == "coast" ? 3500.0
            : (mode == "river" ? 1800.0 : (mode == "highland" ? 14000.0 : 22000.0));
''',
'''        const double fallbackMeters = mode == "coast" ? 850.0
            : (mode == "river" ? 1000.0 : (mode == "highland" ? 5500.0 : 9000.0));
''', 'fallback baseline')

    s = rep(s,
'''            const double targetLift = captureMode == "mountain" ? 180.0
                : (captureMode == "highland" ? 80.0 : (captureMode == "coast" ? 90.0 : 18.0));
            const double cameraLift = captureMode == "mountain" ? 180.0
                : (captureMode == "highland" ? 135.0
                : (captureMode == "coast" ? 115.0 : 210.0));
''',
'''            const double targetLift = captureMode == "mountain" ? 120.0
                : (captureMode == "highland" ? 45.0 : (captureMode == "coast" ? 70.0 : 18.0));
            const double cameraLift = captureMode == "mountain" ? 120.0
                : (captureMode == "highland" ? 105.0
                : (captureMode == "coast" ? 45.0 : 180.0));
''', 'camera lift')

    # Add a marker next to the target log and print apparent target/camera relief for audit.
    s = rep(s,
'''            std::cout << "Capture target elevation: " << vf::planetHeight(planet, featureDirection)
                      << " m | camera surface: " << (visualBase - planet.radius)
                      << " m | lift: " << cameraLift << " m\\n";
''',
'''            // R12 apparent-prominence evidence diagnostic.
            const double captureDistance = std::acos(std::clamp(
                glm::dot(featureDirection, spawnDirection), -1.0, 1.0)) * planet.radius;
            const double captureDrop = vf::planetHeight(planet, featureDirection)
                - (visualBase - planet.radius);
            std::cout << "Capture target elevation: " << vf::planetHeight(planet, featureDirection)
                      << " m | camera surface: " << (visualBase - planet.radius)
                      << " m | lift: " << cameraLift
                      << " m | stand-off: " << captureDistance
                      << " m | apparent-deg: " << glm::degrees(std::atan2(captureDrop, std::max(1.0, captureDistance)))
                      << "\\n";
''', 'capture diagnostic')
    p.write_text(s)
