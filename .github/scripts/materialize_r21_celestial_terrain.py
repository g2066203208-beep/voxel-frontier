from pathlib import Path


def rep(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'R21 patch anchor not found: {label}')
    return text.replace(old, new, 1)

# -----------------------------------------------------------------------------
# PlanetDefinition: orbital/climate forcing becomes authored physical input.
# -----------------------------------------------------------------------------
p = Path('native/include/vf/world/PlanetSurface.hpp')
s = p.read_text()
if 'meanStellarIrradianceWm2' not in s:
    s = rep(s,
'''    double atmosphereHeight{120.0};
    double seaLevelElevationMeters{};
    double maxOceanDepthMeters{};
''',
'''    double atmosphereHeight{120.0};
    double seaLevelElevationMeters{};
    double maxOceanDepthMeters{};

    // R21 orbital/climate forcing. Terrain generation consumes these physical inputs so a newly
    // authored planet does not receive an Earth climate merely because it uses an Earth-like seed.
    double meanStellarIrradianceWm2{1361.0};
    double siderealRotationPeriodSeconds{86164.0905};
    double axialTiltRadians{0.40909280422232897}; // 23.4393 deg
    double orbitalEccentricity{0.01671123};
    double bondAlbedo{0.306};
    double greenhouseFactor{1.12};
''', 'PlanetDefinition forcing')
    p.write_text(s)

# -----------------------------------------------------------------------------
# Celestial public API: Keplerian initialization; propagation remains state-vector based.
# -----------------------------------------------------------------------------
p = Path('native/include/vf/world/CelestialSystem.hpp')
s = p.read_text()
if 'struct KeplerianElements' not in s:
    s = rep(s,
'''enum class CelestialBodyType : std::uint8_t {
    Star,
    Planet,
    Moon,
};
''',
'''enum class CelestialBodyType : std::uint8_t {
    Star,
    Planet,
    Moon,
};

// Classical osculating elements are used only to create an inertial position/velocity at an
// authored epoch. Once initialized, CelestialSystem integrates the Newtonian N-body trajectory.
struct KeplerianElements {
    double semiMajorAxisMeters{};
    double eccentricity{};
    double inclinationRadians{};
    double longitudeAscendingNodeRadians{};
    double argumentPeriapsisRadians{};
    double meanAnomalyRadians{};
};

struct OrbitalState {
    glm::dvec3 position{};
    glm::dvec3 velocity{};
};

[[nodiscard]] OrbitalState keplerianState(
    const KeplerianElements& elements,
    double gravitationalParameterM3PerS2) noexcept;
''', 'Keplerian API')
    p.write_text(s)

# -----------------------------------------------------------------------------
# Celestial dynamics: N-body velocity-Verlet + Kepler element conversion.
# -----------------------------------------------------------------------------
p = Path('native/src/world/CelestialSystem.cpp')
s = p.read_text()
if 'OrbitalState keplerianState' not in s:
    insert_anchor = '} // namespace\n\nstd::uint32_t CelestialSystem::addBody'
    implementation = r'''[[nodiscard]] glm::dvec3 standardToGameAxes(const glm::dvec3& v) noexcept {
    // Classical orbital formulae use Z as the reference-plane normal. Voxel Frontier uses Y-up.
    return {v.x, v.z, v.y};
}

} // namespace

OrbitalState keplerianState(
    const KeplerianElements& elements,
    double gravitationalParameterM3PerS2) noexcept {
    OrbitalState result{};
    const double mu = std::max(1.0e-12, gravitationalParameterM3PerS2);
    const double a = std::max(1.0, elements.semiMajorAxisMeters);
    const double e = std::clamp(elements.eccentricity, 0.0, 0.999999);
    const double M = std::remainder(elements.meanAnomalyRadians, 2.0 * kPi);

    // Newton solve of Kepler's equation M = E - e sin(E).
    double E = e < 0.8 ? M : (M >= 0.0 ? kPi : -kPi);
    for (int i = 0; i < 16; ++i) {
        const double f = E - e * std::sin(E) - M;
        const double fp = std::max(1.0e-10, 1.0 - e * std::cos(E));
        const double dE = f / fp;
        E -= dE;
        if (std::abs(dE) < 1.0e-13) break;
    }

    const double root = std::sqrt(std::max(0.0, 1.0 - e * e));
    const double denom = std::max(1.0e-12, 1.0 - e * std::cos(E));
    const double n = std::sqrt(mu / (a * a * a));
    const glm::dvec3 rPerifocal{a * (std::cos(E) - e), a * root * std::sin(E), 0.0};
    const glm::dvec3 vPerifocal{
        -a * n * std::sin(E) / denom,
        a * n * root * std::cos(E) / denom,
        0.0};

    const double O = elements.longitudeAscendingNodeRadians;
    const double i = elements.inclinationRadians;
    const double w = elements.argumentPeriapsisRadians;
    const double cO = std::cos(O), sO = std::sin(O);
    const double ci = std::cos(i), si = std::sin(i);
    const double cw = std::cos(w), sw = std::sin(w);

    // Q = R3(Omega) R1(i) R3(omega), standard Z-normal celestial frame.
    const glm::dmat3 Q{
        {cO * cw - sO * sw * ci, sO * cw + cO * sw * ci, sw * si},
        {-cO * sw - sO * cw * ci, -sO * sw + cO * cw * ci, cw * si},
        {sO * si, -cO * si, ci},
    };
    result.position = standardToGameAxes(Q * rPerifocal);
    result.velocity = standardToGameAxes(Q * vPerifocal);
    return result;
}

std::uint32_t CelestialSystem::addBody'''
    s = rep(s, insert_anchor, implementation, 'Kepler implementation')

    old_step = r'''void CelestialSystem::step(double deltaSeconds) {
    if (!std::isfinite(deltaSeconds) || deltaSeconds <= 0.0) return;
    const double dt = std::min(deltaSeconds, 60.0);
    for (auto& celestialBody : bodies_) updateOrbit(celestialBody, dt);
    for (auto& celestialBody : bodies_) {
        updateSpin(celestialBody, dt);
        updateClimateAndWeather(celestialBody, dt);
    }
    simulationTime_ += dt;
}
'''
    new_step = r'''void CelestialSystem::step(double deltaSeconds) {
    if (!std::isfinite(deltaSeconds) || deltaSeconds <= 0.0 || bodies_.empty()) return;

    // R21 Newtonian N-body propagation. JPL's ephemeris documentation stresses that real bodies
    // follow perturbed trajectories, not immutable ellipses. A kick-drift-kick velocity-Verlet
    // integrator preserves bound orbital energy far better than the old sequential parent-only
    // Euler pull while remaining cheap for the handful of gameplay-scale celestial bodies.
    double remaining = std::min(deltaSeconds, 86400.0 * 4.0);
    constexpr double maxSubstep = 60.0;
    std::vector<glm::dvec3> acceleration(bodies_.size());

    auto evaluateAccelerations = [&]() {
        std::fill(acceleration.begin(), acceleration.end(), glm::dvec3{});
        for (std::size_t i = 0; i < bodies_.size(); ++i) {
            for (std::size_t j = i + 1; j < bodies_.size(); ++j) {
                const glm::dvec3 delta = bodies_[j].position - bodies_[i].position;
                const double r2 = std::max(glm::dot(delta, delta), 1.0);
                const double invR = 1.0 / std::sqrt(r2);
                const double invR3 = invR / r2;
                const glm::dvec3 directionTerm = delta * invR3;
                acceleration[i] += directionTerm * (kGravitationalConstant * bodies_[j].massKg);
                acceleration[j] -= directionTerm * (kGravitationalConstant * bodies_[i].massKg);
            }
        }
    };

    while (remaining > 1.0e-12) {
        const double h = std::min(remaining, maxSubstep);
        evaluateAccelerations();
        for (std::size_t i = 0; i < bodies_.size(); ++i) {
            bodies_[i].linearVelocity += acceleration[i] * (0.5 * h);
            bodies_[i].position += bodies_[i].linearVelocity * h;
        }
        evaluateAccelerations();
        for (std::size_t i = 0; i < bodies_.size(); ++i) {
            bodies_[i].linearVelocity += acceleration[i] * (0.5 * h);
            updateSpin(bodies_[i], h);
            updateClimateAndWeather(bodies_[i], h);
        }
        simulationTime_ += h;
        remaining -= h;
    }
}
'''
    s = rep(s, old_step, new_step, 'N-body step')
    p.write_text(s)

# -----------------------------------------------------------------------------
# Terrain: orbit/rotation-aware climate forcing, stronger physically gated 2-50 km folds,
# normalized semantic fields.
# -----------------------------------------------------------------------------
p = Path('native/src/world/PlanetSurface.cpp')
s = p.read_text()
if 'R21 ORBIT-COUPLED CLIMATE' not in s:
    old_climate = r'''    // Climate authority. It affects surface processes/materials, not the existence of the
    // macro relief itself.
    const double latitude = std::abs(d.y);
    const double climateNoise = fbmSurface(
        definition.seed ^ 0x1F83D9ABFB41BD6BULL, w, 5.2, 4);
    const double subtropicalBand = smooth01(0.10, 0.30, latitude)
        * (1.0 - smooth01(0.56, 0.78, latitude));
    const double aridity = std::clamp(
        subtropicalBand * (0.52 + 0.48 * (0.5 + 0.5 * climateNoise))
            * (0.58 + 0.42 * interior),
        0.0, 1.0);
    const double moisture = std::clamp(
        0.50 - climateNoise * 0.28 + coastProximity * 0.28 - aridity * 0.56,
        0.0, 1.0);
'''
    new_climate = r'''    // R21 ORBIT-COUPLED CLIMATE. This is deliberately a reduced-order climate closure, not
    // a fake latitude biome switch. Stellar flux enters through radiative-equilibrium T~F^(1/4),
    // axial tilt changes high-latitude seasonality, and the Held-Hou rotation scaling widens the
    // Hadley/subtropical dry belt on slower rotators. ROCKE-3D is the validation reference for
    // the direction of these dependencies; a full GCM is intentionally outside a terrain query.
    const double latitude = std::abs(d.y); // |sin(geographic latitude)|
    const double climateNoise = fbmSurface(
        definition.seed ^ 0x1F83D9ABFB41BD6BULL, w, 5.2, 4);
    const double fluxRatio = std::clamp(definition.meanStellarIrradianceWm2 / 1361.0, 0.08, 5.0);
    const double absorbedRatio = std::max(0.04,
        fluxRatio * (1.0 - std::clamp(definition.bondAlbedo, 0.0, 0.92)) / (1.0 - 0.306));
    const double thermalRatio = std::pow(absorbedRatio, 0.25)
        * std::clamp(definition.greenhouseFactor / 1.12, 0.35, 2.4);
    const double rotationRatio = std::clamp(
        definition.siderealRotationPeriodSeconds / 86164.0905, 0.12, 16.0);
    const double hadleyWidth = std::clamp(std::sqrt(rotationRatio), 0.52, 2.15);
    const double dryLatitudeRadians = std::clamp(
        (26.0 * kPi / 180.0) * hadleyWidth, 13.0 * kPi / 180.0, 55.0 * kPi / 180.0);
    const double dryCenter = std::sin(dryLatitudeRadians);
    const double dryWidth = 0.13 + 0.045 * std::clamp(hadleyWidth - 1.0, -0.5, 1.0);
    const double subtropicalBand = std::exp(
        -std::pow((latitude - dryCenter) / std::max(0.07, dryWidth), 2.0));
    const double tiltStrength = std::clamp(
        std::sin(std::clamp(definition.axialTiltRadians, 0.0, 0.5 * kPi)), 0.0, 1.0);
    const double polarSeasonality = smooth01(0.58, 0.96, latitude) * tiltStrength;
    const double heatDrying = smooth01(1.02, 1.42, thermalRatio);
    const double aridity = std::clamp(
        subtropicalBand * (0.50 + 0.50 * (0.5 + 0.5 * climateNoise))
            * (0.55 + 0.45 * interior) * (0.86 + 0.34 * heatDrying)
            - polarSeasonality * 0.08,
        0.0, 1.0);
    const double moisture = std::clamp(
        0.50 - climateNoise * 0.27 + coastProximity * 0.30 - aridity * 0.58
            + std::clamp(thermalRatio - 0.82, -0.25, 0.25) * 0.13,
        0.0, 1.0);
'''
    s = rep(s, old_climate, new_climate, 'orbit climate')

    old_glacier = r'''    const double glacier = smooth01(0.58, 0.79, latitude)
        * smooth01(1700.0, 3600.0, elevation)
        * smooth01(0.34, 0.72, moisture) * landness;
'''
    new_glacier = r'''    const double climateCold = std::clamp(
        (1.08 - thermalRatio) * 1.35 + latitude * (0.58 + 0.25 * (1.0 - polarSeasonality)),
        0.0, 1.0);
    const double glacier = smooth01(0.52, 0.82, climateCold)
        * smooth01(1450.0, 3350.0, elevation)
        * smooth01(0.30, 0.70, moisture) * landness;
'''
    s = rep(s, old_glacier, new_glacier, 'climate glacier')

    # Correct R20 wavelength scale: 430 on an Earth-radius sphere is ~93 km, far too broad.
    s = rep(s,
'''    const double foldA = 1.0 - std::abs(std::sin(
        across * 430.0 + along * 21.0 + foldWarpA * 3.6));
    const double foldB = 1.0 - std::abs(std::sin(
        across * 920.0 - along * 47.0 + foldWarpA * 5.2 + foldWarpB * 1.8));
    const double foldC = 1.0 - std::abs(std::sin(
        across * 1840.0 + along * 103.0 + foldWarpB * 4.4));
    const double mainCrest = std::pow(smooth01(0.38, 0.90,
        foldA * (0.70 + 0.38 * alongBreak)), 1.38);
    const double branchCrest = std::pow(smooth01(0.40, 0.92,
        foldB * (0.66 + 0.44 * alongBreak)), 1.58);
    const double spurCrest = std::pow(smooth01(0.44, 0.94,
        foldC * (0.62 + 0.48 * alongBreak)), 1.78);
    const double crestEnvelope = std::clamp(std::max(
        mainCrest, std::max(0.86 * branchCrest, 0.70 * spurCrest)), 0.0, 1.0);
''',
'''    // R21 corrected Earth-scale wavelengths: ~47 km main folds, ~18 km parallel ranges,
    // ~6.7 km spurs and ~3.1 km high-ridge detail. All remain gated by the baked orogen field.
    const double foldA = 1.0 - std::abs(std::sin(
        across * 850.0 + along * 31.0 + foldWarpA * 4.0));
    const double foldB = 1.0 - std::abs(std::sin(
        across * 2200.0 - along * 83.0 + foldWarpA * 6.1 + foldWarpB * 2.2));
    const double foldC = 1.0 - std::abs(std::sin(
        across * 6000.0 + along * 211.0 + foldWarpB * 5.4));
    const double foldD = 1.0 - std::abs(std::sin(
        across * 12800.0 - along * 470.0 + foldWarpB * 7.0));
    const double mainCrest = std::pow(smooth01(0.40, 0.91,
        foldA * (0.70 + 0.38 * alongBreak)), 1.45);
    const double branchCrest = std::pow(smooth01(0.42, 0.93,
        foldB * (0.66 + 0.44 * alongBreak)), 1.68);
    const double spurCrest = std::pow(smooth01(0.46, 0.95,
        foldC * (0.62 + 0.48 * alongBreak)), 1.90);
    const double detailCrest = std::pow(smooth01(0.50, 0.965,
        foldD * (0.58 + 0.50 * alongBreak)), 2.15);
    const double crestEnvelope = std::clamp(std::max(
        mainCrest, std::max(0.88 * branchCrest,
            std::max(0.72 * spurCrest, 0.46 * detailCrest))), 0.0, 1.0);
''', 'fold wavelengths')

    s = rep(s,
'''    elevation += processMountainGate * hardnessTerm
        * (940.0 * (mainCrest - 0.16)
            + 590.0 * (branchCrest - 0.11)
            + 290.0 * (spurCrest - 0.08));
    elevation += summitCrown * hardnessTerm * 1280.0;
    elevation -= processValley * (760.0 + 260.0 * (1.0 - substrateHardness));
''',
'''    elevation += processMountainGate * hardnessTerm
        * (760.0 * (mainCrest - 0.15)
            + 520.0 * (branchCrest - 0.10)
            + 300.0 * (spurCrest - 0.065)
            + 115.0 * (detailCrest - 0.045));
    elevation += summitCrown * hardnessTerm * 1120.0;
    elevation -= processValley * (900.0 + 300.0 * (1.0 - substrateHardness));
''', 'fold amplitudes')

    s = rep(s,
'''    elevation += processPlateauInner * (820.0 + 260.0 * hardnessTerm);
    elevation += processPlateauEdge * (360.0 + 240.0 * hardnessTerm);
    elevation -= processPlateauFoot * (170.0 + 90.0 * (1.0 - substrateHardness));
    elevation += processPlateauInner * plateauTopNoise * 36.0;
''',
'''    // R21 tableland cross-section: broad quiet cap, finite resistant rim, then a real lower foot.
    elevation += processPlateauInner * (620.0 + 180.0 * hardnessTerm);
    elevation += processPlateauEdge * (470.0 + 250.0 * hardnessTerm);
    elevation -= processPlateauFoot * (390.0 + 120.0 * (1.0 - substrateHardness));
    elevation += processPlateauInner * plateauTopNoise * 24.0;
''', 'plateau profile')

    old_sample = r'''    PlanetTerrainSample sample{};
    sample.elevationMeters = elevation;
    sample.continentalness = geomorph.continentalness;
    sample.plateBoundary = plates.boundary;
    sample.convergence = plates.convergence;
    sample.divergence = plates.divergence;
    sample.oceanRidge = oceanRidge;
    sample.mountain = std::clamp(std::max(bakedMountain, processMountainGate * crestEnvelope), 0.0, 1.0);
    sample.plateau = std::clamp(std::max(bakedTableland, processPlateauInner), 0.0, 1.0);
    sample.trench = trench;
    sample.volcano = volcano;
    sample.river = channelCore;
    sample.hills = std::clamp(processHillGate * (0.5 + 0.5 * processHillA), 0.0, 1.0);
    sample.canyon = std::max({canyon, geomorph.incision, processValley});
    sample.dunes = dunes;
    sample.coastalCliff = std::clamp(std::max(coastEscarpment, coastalRock), 0.0, 1.0);
    sample.wetland = std::max(wetland, geomorph.floodplain);
    sample.glacier = glacier;
    sample.aridity = aridity;
    sample.moisture = moisture;
'''
    new_sample = r'''    PlanetTerrainSample sample{};
    const auto normalizedMask = [](double value) noexcept {
        return std::isfinite(value) ? std::clamp(value, 0.0, 1.0) : 0.0;
    };
    sample.elevationMeters = std::isfinite(elevation) ? elevation : definition.seaLevelElevationMeters;
    sample.continentalness = std::isfinite(geomorph.continentalness)
        ? std::clamp(geomorph.continentalness, -1.0, 1.0) : 0.0;
    sample.plateBoundary = normalizedMask(plates.boundary);
    sample.convergence = normalizedMask(plates.convergence);
    sample.divergence = normalizedMask(plates.divergence);
    sample.oceanRidge = normalizedMask(oceanRidge);
    sample.mountain = normalizedMask(std::max(bakedMountain, processMountainGate * crestEnvelope));
    sample.plateau = normalizedMask(std::max(bakedTableland, processPlateauInner));
    sample.trench = normalizedMask(trench);
    sample.volcano = normalizedMask(volcano);
    sample.river = normalizedMask(channelCore);
    sample.hills = normalizedMask(processHillGate * (0.5 + 0.5 * processHillA));
    sample.canyon = normalizedMask(std::max({canyon, geomorph.incision, processValley}));
    sample.dunes = normalizedMask(dunes);
    sample.coastalCliff = normalizedMask(std::max(coastEscarpment, coastalRock));
    sample.wetland = normalizedMask(std::max(wetland, geomorph.floodplain));
    sample.glacier = normalizedMask(glacier);
    sample.aridity = normalizedMask(aridity);
    sample.moisture = normalizedMask(moisture);
'''
    s = rep(s, old_sample, new_sample, 'normalized terrain masks')
    p.write_text(s)

# -----------------------------------------------------------------------------
# Main runtime: physical Sun/Aster/Luna initialization, barycentric state, visible Sun+Moon,
# uniform game time acceleration.
# -----------------------------------------------------------------------------
p = Path('native/src/app/Main.cpp')
s = p.read_text()
if 'R21 Earth-Moon-Sun physical baseline' not in s:
    # Add PlanetDefinition forcing defaults near planet setup.
    s = rep(s,
'''        planet.maxOceanDepthMeters = 11000.0;
        planet.atmosphereHeight = 100000.0;
''',
'''        planet.maxOceanDepthMeters = 11000.0;
        planet.atmosphereHeight = 100000.0;
        planet.meanStellarIrradianceWm2 = 1361.0;
        planet.siderealRotationPeriodSeconds = 86164.0905;
        planet.axialTiltRadians = 23.4393 * kPi / 180.0;
        planet.orbitalEccentricity = 0.01671123;
        planet.bondAlbedo = 0.306;
        planet.greenhouseFactor = 1.12;
''', 'planet climate inputs')

    start = s.index('        constexpr double asterOrbitRadius = 149597870700.0;')
    end_marker = '        const std::uint32_t cinderId = celestial.addBody(cinder);\n'
    end = s.index(end_marker, start) + len(end_marker)
    replacement = r'''        // R21 Earth-Moon-Sun physical baseline. Values come from NASA/JPL references recorded in
        // docs/CELESTIAL_PHYSICS_REFERENCES_R21.md. Keplerian elements create the epoch state;
        // CelestialSystem then propagates all massive bodies with Newtonian N-body gravity.
        constexpr double earthMassKg = 5.97217e24;
        constexpr double earthMeanRadiusM = 6371008.4;
        constexpr double earthTilt = 23.4393 * kPi / 180.0;
        constexpr double earthSiderealSeconds = 86164.0905;
        vf::KeplerianElements earthOrbit{};
        earthOrbit.semiMajorAxisMeters = 149598262000.0;
        earthOrbit.eccentricity = 0.01671123;
        earthOrbit.inclinationRadians = 0.0;
        earthOrbit.meanAnomalyRadians = 0.0; // authored epoch phase; physical scale is unchanged
        const vf::OrbitalState earthState = vf::keplerianState(
            earthOrbit,
            vf::CelestialSystem::kGravitationalConstant * (sun.massKg + earthMassKg));

        vf::CelestialBody aster{};
        aster.type = vf::CelestialBodyType::Planet;
        aster.name = "Aster";
        aster.radiusMeters = earthMeanRadiusM;
        aster.massKg = earthMassKg;
        aster.gameplaySurfaceGravityMps2 = 9.80665;
        aster.gravityFalloffStartRadiusMeters = earthMeanRadiusM + planet.atmosphereHeight;
        aster.gravityFalloffPower = 7.0;
        aster.gravityInfluenceRadiusMeters = earthMeanRadiusM + 900000.0;
        aster.physicsBubbleRadiusMeters = earthMeanRadiusM + 1300000.0;
        aster.position = sun.position + earthState.position;
        aster.linearVelocity = sun.linearVelocity + earthState.velocity;
        aster.orbitParentId = sunId;
        aster.spinAxis = safeNormalize({std::sin(earthTilt), std::cos(earthTilt), 0.0});
        aster.orientation = glm::angleAxis(-earthTilt, glm::dvec3{0.0, 0.0, 1.0});
        aster.spinRateRadPerSecond = 2.0 * kPi / earthSiderealSeconds;
        aster.visibleAlbedo = {0.20, 0.42, 0.18};
        aster.atmosphere.enabled = true;
        aster.atmosphere.heightMeters = planet.atmosphereHeight;
        aster.atmosphere.surfacePressurePa = 101325.0;
        aster.atmosphere.surfaceTemperatureK = 288.15;
        aster.atmosphere.scaleHeightMeters = 8500.0;
        aster.atmosphere.lapseRateKPerM = 0.0065;
        aster.atmosphere.rayleighRgb = {0.16, 0.43, 1.00};
        aster.atmosphere.mieStrength = 0.08;
        aster.atmosphere.prevailingWind = {};
        aster.weather.windMultiplier = 0.0;
        aster.weather.stormIntensity = 0.0;
        aster.climate.bondAlbedo = planet.bondAlbedo;
        aster.climate.greenhouseFactor = planet.greenhouseFactor;
        const std::uint32_t asterId = celestial.addBody(aster);

        constexpr double lunarMassKg = 7.34767309245735e22;
        constexpr double lunarRadiusM = 1737400.0;
        constexpr double lunarSiderealSeconds = 27.321661 * 86400.0;
        constexpr double lunarInclination = 5.145 * kPi / 180.0;
        vf::KeplerianElements lunarOrbit{};
        lunarOrbit.semiMajorAxisMeters = 384400000.0;
        lunarOrbit.eccentricity = 0.0549;
        lunarOrbit.inclinationRadians = lunarInclination;
        lunarOrbit.meanAnomalyRadians = 1.15; // authored epoch phase
        const vf::OrbitalState lunarState = vf::keplerianState(
            lunarOrbit,
            vf::CelestialSystem::kGravitationalConstant * (earthMassKg + lunarMassKg));

        vf::CelestialBody luna{};
        luna.type = vf::CelestialBodyType::Moon;
        luna.name = "Luna";
        luna.radiusMeters = lunarRadiusM;
        luna.massKg = lunarMassKg;
        luna.gameplaySurfaceGravityMps2 = 1.624;
        luna.gravityFalloffStartRadiusMeters = lunarRadiusM;
        luna.gravityFalloffPower = 6.0;
        luna.gravityInfluenceRadiusMeters = lunarRadiusM + 420000.0;
        luna.physicsBubbleRadiusMeters = lunarRadiusM + 650000.0;
        luna.orbitParentId = asterId;
        luna.position = aster.position + lunarState.position;
        luna.linearVelocity = aster.linearVelocity + lunarState.velocity;
        luna.spinAxis = safeNormalize({0.0, std::cos(lunarInclination), std::sin(lunarInclination)});
        luna.spinRateRadPerSecond = 2.0 * kPi / lunarSiderealSeconds; // synchronous sidereal spin
        luna.orientation = glm::angleAxis(-6.68 * kPi / 180.0, glm::dvec3{0.0, 0.0, 1.0});
        luna.visibleAlbedo = {0.33, 0.32, 0.30};
        const std::uint32_t lunaId = celestial.addBody(luna);

        // Keep a Mars-like second planet as an interplanetary target; it participates in the same
        // N-body solution instead of moving on a scripted circle.
        constexpr double cinderOrbitRadius = 227939200000.0;
        vf::CelestialBody cinder{};
        cinder.type = vf::CelestialBodyType::Planet;
        cinder.name = "Cinder";
        cinder.radiusMeters = 3389500.0;
        cinder.massKg = 6.4171e23;
        cinder.gameplaySurfaceGravityMps2 = 3.71;
        cinder.gravityInfluenceRadiusMeters = cinder.radiusMeters + 550000.0;
        cinder.physicsBubbleRadiusMeters = cinder.radiusMeters + 800000.0;
        cinder.position = {0.0, 0.0, cinderOrbitRadius};
        cinder.orbitParentId = sunId;
        cinder.linearVelocity = {-circularOrbitSpeed(sun.massKg, cinderOrbitRadius), 0.0, 0.0};
        cinder.visibleAlbedo = {0.62, 0.30, 0.22};
        const std::uint32_t cinderId = celestial.addBody(cinder);

        // Shift into the actual system barycentric frame. This removes arbitrary center-of-mass
        // translation while preserving every relative state and total momentum.
        double systemMass = 0.0;
        glm::dvec3 barycenter{};
        glm::dvec3 barycentricVelocity{};
        for (const auto& body : celestial.bodies()) {
            systemMass += body.massKg;
            barycenter += body.position * body.massKg;
            barycentricVelocity += body.linearVelocity * body.massKg;
        }
        if (systemMass > 0.0) {
            barycenter /= systemMass;
            barycentricVelocity /= systemMass;
            for (auto& body : celestial.bodies()) {
                body.position -= barycenter;
                body.linearVelocity -= barycentricVelocity;
            }
        }
        if (const auto* storedAster = celestial.body(asterId)) {
            planet.meanStellarIrradianceWm2 = celestial.stellarIrradianceAt(*storedAster);
        }
'''
    s = s[:start] + replacement + s[end:]

    # Runtime time scale + Moon handle.
    s = rep(s,
'''        double lodCooldown = 0.0;

        while (platform.pumpEvents()) {
''',
'''        double lodCooldown = 0.0;
        // Uniform simulation-time acceleration: 120x gives a ~12-minute terrestrial sidereal day
        // while preserving every physical period ratio. Override with VF_CELESTIAL_TIME_SCALE.
        double celestialTimeScale = 120.0;
        if (const char* scaleEnv = std::getenv("VF_CELESTIAL_TIME_SCALE")) {
            char* end = nullptr;
            const double parsed = std::strtod(scaleEnv, &end);
            if (end != scaleEnv && std::isfinite(parsed) && parsed > 0.0)
                celestialTimeScale = std::clamp(parsed, 0.01, 20000.0);
        }

        while (platform.pumpEvents()) {
''', 'celestial time scale')
    s = rep(s, '            celestial.step(dt);\n', '            celestial.step(dt * celestialTimeScale);\n', 'scaled celestial step')
    s = rep(s,
'''            const auto* currentCinder = celestial.body(cinderId);
            const auto* currentSun = celestial.body(sunId);
''',
'''            const auto* currentCinder = celestial.body(cinderId);
            const auto* currentMoon = celestial.body(lunaId);
            const auto* currentSun = celestial.body(sunId);
''', 'current moon handle')

    # Replace dynamic celestial proxy block.
    old_dyn = r'''            vf::PlanetMesh dynamicMesh{};
            if (currentCinder != nullptr) {
                const glm::dvec3 cinderDirection = safeNormalize(
                    currentCinder->position - camera.position());
                const glm::dvec3 cinderSurfaceDirection = safeNormalize(
                    toSurfaceVector(inverseAster * cinderDirection));
                const double distance = glm::length(currentCinder->position - camera.position());
                const double angularRadius = std::asin(std::clamp(
                    currentCinder->radiusMeters / std::max(distance, currentCinder->radiusMeters),
                    0.0,
                    0.20));
                constexpr double visualDistance = 25000000.0;
                const double visualRadius = std::max(
                    1800.0, std::tan(angularRadius) * visualDistance);
                vf::appendDebugSphere(
                    dynamicMesh,
                    cameraSurface + cinderSurfaceDirection * visualDistance,
                    visualRadius,
                    {0.62F, 0.30F, 0.22F},
                    9U,
                    16U,
                    {0.0F, 0.82F, 0.0F, 0.0F});
            }
            renderer.setDynamicMesh(dynamicMesh);
'''
    new_dyn = r'''            vf::PlanetMesh dynamicMesh{};
            const auto appendAngularBody = [&](const vf::CelestialBody& body,
                                                const glm::vec3& color,
                                                double visualDistance,
                                                double minVisualRadius,
                                                float emissive,
                                                unsigned rings,
                                                unsigned segments) {
                const glm::dvec3 worldDelta = body.position - camera.position();
                const double distance = glm::length(worldDelta);
                if (distance <= body.radiusMeters * 1.001) return;
                const glm::dvec3 bodyDirection = safeNormalize(worldDelta);
                const glm::dvec3 surfaceDirection = safeNormalize(
                    toSurfaceVector(inverseAster * bodyDirection));
                const double angularRadius = std::asin(std::clamp(
                    body.radiusMeters / distance, 0.0, 0.35));
                const double visualRadius = std::max(
                    minVisualRadius, std::tan(angularRadius) * visualDistance);
                vf::appendDebugSphere(
                    dynamicMesh,
                    cameraSurface + surfaceDirection * visualDistance,
                    visualRadius,
                    color,
                    rings,
                    segments,
                    {0.0F, emissive > 0.5F ? 0.22F : 0.94F, 0.0F, emissive});
            };

            // The local meshes are angular-size-preserving render proxies only. Their angular
            // radius comes from each body's real physical radius / instantaneous N-body distance.
            appendAngularBody(*currentSun, {1.0F, 0.79F, 0.49F},
                30000000.0, 24000.0, 5.0F, 24U, 48U);
            if (currentMoon != nullptr) {
                appendAngularBody(*currentMoon, {0.39F, 0.385F, 0.37F},
                    18000000.0, 12000.0, 0.0F, 28U, 48U);
            }
            if (currentCinder != nullptr) {
                appendAngularBody(*currentCinder, {0.62F, 0.30F, 0.22F},
                    25000000.0, 1800.0, 0.0F, 9U, 16U);
            }
            renderer.setDynamicMesh(dynamicMesh);
'''
    s = rep(s, old_dyn, new_dyn, 'Sun Moon rendering')

    # Window diagnostics include celestial time and Moon distance.
    s = rep(s,
'''                      << " | STREAM " << (terrainBuildInFlight ? "BUILD" : "READY")
                      << " | tris " << renderer.triangleCount() << '+'
''',
'''                      << " | STREAM " << (terrainBuildInFlight ? "BUILD" : "READY")
                      << " | TIME x" << std::setprecision(0) << celestialTimeScale
                      << " | MOON " << std::setprecision(0)
                      << (currentMoon ? glm::length(currentMoon->position - currentAster->position) / 1000.0 : 0.0)
                      << " km"
                      << " | tris " << renderer.triangleCount() << '+'
''', 'title celestial diagnostics')
    p.write_text(s)

# -----------------------------------------------------------------------------
# Add orbital-state validation to existing celestial tests.
# -----------------------------------------------------------------------------
p = Path('native/tests/CelestialSystemTests.cpp')
s = p.read_text()
if 'testKeplerianStateEnergyIdentity' not in s:
    marker = 'void testDipoleMagneticFieldFallsWithDistance() {'
    test = r'''void testKeplerianStateEnergyIdentity() {
    constexpr double mu = 3.98600435507e14;
    vf::KeplerianElements elements{};
    elements.semiMajorAxisMeters = 7000000.0;
    elements.eccentricity = 0.12;
    elements.inclinationRadians = 0.41;
    elements.longitudeAscendingNodeRadians = 0.83;
    elements.argumentPeriapsisRadians = 1.17;
    elements.meanAnomalyRadians = 0.64;
    const vf::OrbitalState state = vf::keplerianState(elements, mu);
    const double r = glm::length(state.position);
    const double v2 = glm::dot(state.velocity, state.velocity);
    const double specificEnergy = 0.5 * v2 - mu / r;
    requireNear(specificEnergy, -mu / (2.0 * elements.semiMajorAxisMeters), 0.05,
        "Keplerian state must satisfy the vis-viva specific-energy identity");
}

'''
    s = rep(s, marker, test + marker, 'Kepler test function')
    s = rep(s,
'''    testSpinAndBoundOrbit();
    testDipoleMagneticFieldFallsWithDistance();
''',
'''    testSpinAndBoundOrbit();
    testKeplerianStateEnergyIdentity();
    testDipoleMagneticFieldFallsWithDistance();
''', 'Kepler test call')
    p.write_text(s)
