from pathlib import Path


def rep(s: str, old: str, new: str, label: str) -> str:
    if old not in s:
        raise SystemExit(f'{label} not found')
    return s.replace(old, new, 1)

p = Path('native/src/app/Main.cpp')
s = p.read_text()
if 'R11 relaxed capture fallback' in s:
    raise SystemExit(0)

old = '''            if (captureMode == "mountain") {
                if (terrain.mountain < 0.22 || aboveSea < 3000.0 || aboveSea > 5000.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 30000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 2200.0 || relief > 4800.0 || r.minElevation > 1800.0) continue;
                captureScore += terrain.mountain * 4.3 + relief / 300.0
                    + std::max(0.0, 1800.0 - r.minElevation) / 600.0;
            } else if (captureMode == "river") {
                if (terrain.river < 0.22 || aboveSea < 240.0 || aboveSea > 1500.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 7000.0);
                if (r.minElevation < 80.0) continue;
                const double valleyDepth = std::max(0.0, r.meanElevation - aboveSea);
                captureScore += terrain.river * 7.0 + valleyDepth / 100.0
                    + terrain.canyon * 1.4;
            } else if (captureMode == "coast") {
                if (aboveSea < 120.0 || aboveSea > 680.0 || terrain.coastalCliff < 0.20) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 7000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (r.minElevation > -6.0 || relief < 340.0) continue;
                const double cliffHeightPreference = 1.0
                    - std::clamp(std::abs(aboveSea - 360.0) / 360.0, 0.0, 1.0);
                captureScore += terrain.coastalCliff * 6.8 + relief / 105.0
                    + cliffHeightPreference * 3.5;
            } else if (captureMode == "highland") {
                if (terrain.plateau < 0.48 || terrain.plateau > 0.88
                    || aboveSea < 2150.0 || aboveSea > 2950.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 18000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 520.0 || relief > 2200.0 || r.minElevation > 2050.0) continue;
                const double edgePreference = 1.0
                    - std::clamp(std::abs(terrain.plateau - 0.66) / 0.22, 0.0, 1.0);
                captureScore += edgePreference * 6.0 + terrain.plateau * 2.8
                    + std::min(relief, 1800.0) / 500.0 - terrain.mountain * 2.2;
            }
'''
new = '''            if (captureMode == "mountain") {
                if (terrain.mountain < 0.18 || aboveSea < 2500.0 || aboveSea > 5200.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 30000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 1500.0 || relief > 4800.0) continue;
                captureScore += terrain.mountain * 5.0 + relief / 340.0
                    + aboveSea / 5000.0;
            } else if (captureMode == "river") {
                if (terrain.river < 0.22 || aboveSea < 240.0 || aboveSea > 1500.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 7000.0);
                if (r.minElevation < 80.0) continue;
                const double valleyDepth = std::max(0.0, r.meanElevation - aboveSea);
                captureScore += terrain.river * 7.0 + valleyDepth / 100.0
                    + terrain.canyon * 1.4;
            } else if (captureMode == "coast") {
                if (aboveSea < 90.0 || aboveSea > 1400.0 || terrain.coastalCliff < 0.14) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 9000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (r.minElevation > 5.0 || relief < 300.0) continue;
                const double cliffHeightPreference = 1.0
                    - std::clamp(std::abs(aboveSea - 420.0) / 900.0, 0.0, 1.0);
                captureScore += terrain.coastalCliff * 7.2 + relief / 120.0
                    + cliffHeightPreference * 2.8;
            } else if (captureMode == "highland") {
                if (terrain.plateau < 0.34 || aboveSea < 1750.0 || aboveSea > 3100.0) continue;
                const LocalReliefStats r = sampleLocalRelief(planet, d, 24000.0);
                const double relief = r.maxElevation - r.minElevation;
                if (relief < 450.0 || relief > 2600.0) continue;
                const double edgePreference = 1.0
                    - std::clamp(std::abs(terrain.plateau - 0.64) / 0.30, 0.0, 1.0);
                captureScore += edgePreference * 5.0 + terrain.plateau * 4.0
                    + std::min(relief, 2200.0) / 620.0 - terrain.mountain * 1.8;
            }
'''
s = rep(s, old, new, 'strict target rules')

old = '''    }
    return safeNormalize(best, preferred);
}

[[nodiscard]] glm::dvec3 findCaptureVantageDirection(
'''
new = '''    }

    // R11 relaxed capture fallback: never silently return the generic preferred direction when
    // a strict evidence predicate finds zero candidates. A second global pass ranks real landforms
    // by their physical fields and measured neighbourhood relief, so every capture mode receives
    // a semantically valid target even when the strict thresholds are too ambitious for this seed.
    if (!captureMode.empty() && !found) {
        for (std::uint32_t i = 0; i < sampleCount; ++i) {
            const double y = 1.0 - 2.0 * (static_cast<double>(i) + 0.5)
                / static_cast<double>(sampleCount);
            const double radial = std::sqrt(std::max(0.0, 1.0 - y * y));
            const double a = goldenAngle * static_cast<double>(i);
            const glm::dvec3 d{std::cos(a) * radial, y, std::sin(a) * radial};
            const vf::PlanetTerrainSample terrain = vf::samplePlanetTerrain(planet, d);
            const double aboveSea = terrain.elevationMeters - planet.seaLevelElevationMeters;
            if (terrain.submerged(planet) || aboveSea < 12.0) continue;
            const double sunElevation = glm::dot(d, sunDirection);
            if (sunElevation < 0.12) continue;
            double score = sunElevation * 0.5;

            if (captureMode == "mountain") {
                const LocalReliefStats r = sampleLocalRelief(planet, d, 32000.0);
                const double relief = r.maxElevation - r.minElevation;
                score += terrain.mountain * 8.0 + relief / 420.0 + aboveSea / 1800.0;
            } else if (captureMode == "river") {
                score += terrain.river * 10.0 + terrain.canyon * 2.0
                    - std::abs(aboveSea - 650.0) / 1800.0;
            } else if (captureMode == "coast") {
                const LocalReliefStats r = sampleLocalRelief(planet, d, 10000.0);
                const double relief = r.maxElevation - r.minElevation;
                score += terrain.coastalCliff * 9.0 + relief / 360.0
                    - std::abs(aboveSea - 420.0) / 650.0
                    + (r.minElevation < 0.0 ? 4.0 : 0.0);
            } else if (captureMode == "highland") {
                const LocalReliefStats r = sampleLocalRelief(planet, d, 26000.0);
                const double relief = r.maxElevation - r.minElevation;
                score += terrain.plateau * 9.0 + relief / 650.0
                    + aboveSea / 2600.0 - terrain.mountain * 2.0;
            }

            if (!found || score > bestScore) {
                bestScore = score;
                best = d;
                found = true;
            }
        }
    }

    if (!captureMode.empty() && !found) {
        // Last-resort invariant: capture targets must still be land, never the arbitrary preferred
        // vector. Select the highest daylight land point; this path should be practically unreachable.
        for (std::uint32_t i = 0; i < sampleCount; ++i) {
            const double y = 1.0 - 2.0 * (static_cast<double>(i) + 0.5)
                / static_cast<double>(sampleCount);
            const double radial = std::sqrt(std::max(0.0, 1.0 - y * y));
            const double a = goldenAngle * static_cast<double>(i);
            const glm::dvec3 d{std::cos(a) * radial, y, std::sin(a) * radial};
            const vf::PlanetTerrainSample terrain = vf::samplePlanetTerrain(planet, d);
            if (terrain.submerged(planet)) continue;
            const double score = terrain.elevationMeters + 500.0 * glm::dot(d, sunDirection);
            if (!found || score > bestScore) {
                bestScore = score;
                best = d;
                found = true;
            }
        }
    }
    return safeNormalize(best, preferred);
}

[[nodiscard]] glm::dvec3 findCaptureVantageDirection(
'''
s = rep(s, old, new, 'target fallback')

old = '''    if (!foundVantage || glm::dot(best, target) > 0.9999995) {
        const double fallbackMeters = mode == "coast" ? 2300.0
            : (mode == "river" ? 1200.0 : (mode == "highland" ? 10000.0 : 17000.0));
        const double angular = fallbackMeters / std::max(1.0, planet.radius);
        best = safeNormalize(target + east * angular, target);
    }
    return safeNormalize(best, target);
}
'''
new = '''    if (!foundVantage) {
        // R11 relaxed vantage fallback: search a wider annulus before ever using an unchecked
        // geometric offset. Mountain/highland cameras remain on land; coast cameras prefer water.
        const std::array<double, 8> relaxedRadii{3000.0, 6000.0, 10000.0, 15000.0,
            22000.0, 30000.0, 40000.0, 52000.0};
        for (double standOffMeters : relaxedRadii) {
            const double angular = standOffMeters / std::max(1.0, planet.radius);
            for (int i = 0; i < 64; ++i) {
                const double a = 2.0 * kPi * static_cast<double>(i) / 64.0;
                const glm::dvec3 d = safeNormalize(
                    target + east * (std::cos(a) * angular) + north * (std::sin(a) * angular),
                    target);
                const vf::PlanetTerrainSample terrain = vf::samplePlanetTerrain(planet, d);
                double score = std::numeric_limits<double>::infinity();
                if (mode == "coast") {
                    if (!terrain.submerged(planet)) continue;
                    score = std::abs(terrain.elevationMeters + 15.0) * 0.10
                        + std::abs(standOffMeters - 3500.0) * 0.018;
                } else if (mode == "mountain") {
                    if (terrain.submerged(planet)) continue;
                    const double drop = targetElevation - terrain.elevationMeters;
                    score = terrain.elevationMeters * 0.55
                        + terrain.mountain * 900.0
                        + std::abs(drop - 1800.0) * 0.28
                        + std::abs(standOffMeters - 22000.0) * 0.018;
                } else if (mode == "highland") {
                    if (terrain.submerged(planet)) continue;
                    const double drop = targetElevation - terrain.elevationMeters;
                    score = std::abs(drop - 850.0) * 0.42
                        + terrain.plateau * 780.0
                        + terrain.mountain * 980.0
                        + std::abs(standOffMeters - 14000.0) * 0.018;
                } else {
                    if (terrain.submerged(planet)) continue;
                    score = terrain.river * 2200.0
                        + std::abs(terrain.elevationMeters - targetElevation) * 0.12
                        + std::abs(standOffMeters - 1800.0) * 0.028;
                }
                if (score < bestScore) {
                    bestScore = score;
                    best = d;
                    foundVantage = true;
                }
            }
        }
    }
    if (!foundVantage || glm::dot(best, target) > 0.9999995) {
        const double fallbackMeters = mode == "coast" ? 3500.0
            : (mode == "river" ? 1800.0 : (mode == "highland" ? 14000.0 : 22000.0));
        const double angular = fallbackMeters / std::max(1.0, planet.radius);
        best = safeNormalize(target + east * angular, target);
    }
    return safeNormalize(best, target);
}
'''
s = rep(s, old, new, 'vantage fallback')

p.write_text(s)
