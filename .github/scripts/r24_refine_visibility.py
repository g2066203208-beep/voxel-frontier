#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / 'native/src/app/Main.cpp'
SHADER = ROOT / 'native/shaders/planet.slang'
TESTS = ROOT / 'native/tests/R24PhysicalPlanetTests.cpp'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'missing anchor: {label}')
    return text.replace(old, new, 1)

# -----------------------------------------------------------------------------
# Main runtime: keep evidence camera locked to the *real* Moon, widen aerial
# capture altitude, and expose real apparent Moon size/alignment in logs.
# -----------------------------------------------------------------------------
t = MAIN.read_text(encoding='utf-8')
t = replace_once(
    t,
    '                try { aerialAltitude = std::clamp(std::stod(altitudeEnv), 800.0, 18000.0); }',
    '                try { aerialAltitude = std::clamp(std::stod(altitudeEnv), 800.0, 80000.0); }',
    'aerial altitude range')

t = replace_once(
    t,
    '''        if (const char* celestialTargetEnv = std::getenv("VF_CELESTIAL_TARGET");
            celestialTargetEnv != nullptr && *celestialTargetEnv != '\\0') {
            const std::string_view celestialTarget{celestialTargetEnv};
            if (celestialTarget == "sun") {
                camera.setViewDirectionWorld(
                    sun.position - camera.position(), camera.up());
                std::cout << "R23 celestial target: sun\\n";
            } else if (celestialTarget == "moon") {
                camera.setViewDirectionWorld(
                    luna.position - camera.position(), camera.up());
                std::cout << "R23 celestial target: moon\\n";
            }
        }''',
    '''        std::string celestialTargetMode{};
        if (const char* celestialTargetEnv = std::getenv("VF_CELESTIAL_TARGET");
            celestialTargetEnv != nullptr && *celestialTargetEnv != '\\0') {
            celestialTargetMode = celestialTargetEnv;
            if (celestialTargetMode == "sun") {
                camera.setViewDirectionWorld(
                    sun.position - camera.position(), camera.up());
                std::cout << "R24 celestial evidence target: sun\\n";
            } else if (celestialTargetMode == "moon") {
                camera.setViewDirectionWorld(
                    luna.position - camera.position(), camera.up());
                std::cout << "R24 celestial evidence target: moon (physical radius/distance)\\n";
            }
        }
        const bool trackMoonEvidence = celestialTargetMode == "moon";''',
    'persistent celestial evidence target')

t = replace_once(
    t,
    '''            const glm::dvec3 cameraSurface = toSurfacePoint(cameraPlanet);''',
    '''            // CI/test-only tracking lens: VF_CELESTIAL_TARGET=moon continuously points the
            // ordinary production camera at the actual integrated Moon position. It does not move,
            // resize or substitute the Moon; it prevents surface-attitude transport from drifting a
            // six-pixel physical lunar disc out of the evidence frame while accelerated time runs.
            if (trackMoonEvidence && currentMoon != nullptr) {
                camera.setViewDirectionWorld(
                    currentMoon->position - camera.position(), camera.up());
            }

            const glm::dvec3 cameraSurface = toSurfacePoint(cameraPlanet);''',
    'per-frame physical Moon tracking')

t = replace_once(
    t,
    '''                platform.setWindowTitle(title.str());
                diagnosticsTime = 0.0;''',
    '''                platform.setWindowTitle(title.str());
                if (trackMoonEvidence && currentMoon != nullptr) {
                    const glm::dvec3 moonDirectionWorld = safeNormalize(
                        currentMoon->position - camera.position());
                    const double alignment = std::clamp(
                        glm::dot(camera.forwardDirection(), moonDirectionWorld), -1.0, 1.0);
                    const double angularErrorDegrees = std::acos(alignment) * 180.0 / kPi;
                    const double moonDistanceMeters = glm::length(
                        currentMoon->position - camera.position());
                    const double angularRadiusRadians = std::asin(std::clamp(
                        currentMoon->radiusMeters / std::max(moonDistanceMeters, currentMoon->radiusMeters),
                        0.0, 1.0));
                    const double focalPixels = static_cast<double>(height)
                        / (2.0 * std::tan(glm::radians(68.0) * 0.5));
                    const double apparentDiameterPixels = 2.0 * std::tan(angularRadiusRadians) * focalPixels;
                    std::cout << "R24 moon evidence: distance_km="
                              << moonDistanceMeters / 1000.0
                              << " angular_error_deg=" << angularErrorDegrees
                              << " apparent_diameter_px=" << apparentDiameterPixels
                              << " dynamic_tris=" << renderer.dynamicTriangleCount() << '\\n';
                }
                diagnosticsTime = 0.0;''',
    'Moon evidence diagnostics')

t = t.replace('R23 terrain target:', 'R24 terrain target:')
t = t.replace('R23 deterministic aerial camera altitude=', 'R24 deterministic aerial camera altitude=')
MAIN.write_text(t, encoding='utf-8')

# -----------------------------------------------------------------------------
# Shader: replace the old scalar art-directed haze with a compact optical-depth
# approximation using the same RGB Rayleigh coefficients as the sky integrator.
# GPU Gems/Bruneton-style principle: extinction is exp(-beta * optical length).
# The half-strength Mie term avoids the old grey wash while keeping real aerial
# perspective. This is still the inexpensive forward approximation; the sky pass
# remains the higher-fidelity ray integration.
# -----------------------------------------------------------------------------
s = SHADER.read_text(encoding='utf-8')
old_aerial = '''float3 applyStylizedAerial(float3 color, VertexOutput input, float strength)
{
    float distanceMeters = length(input.relativePosition);
    if (distanceMeters <= 350.0 || strength <= 0.0) return color;

    float3 viewDir = input.relativePosition / max(distanceMeters, 1.0e-4);
    float3 sunDir = normalize(gPush.data1.xyz);
    float cameraAltitude = max(gPush.data0.w, 0.0);

    float atmospherePresence = exp(-cameraAltitude / 90000.0);
    float effectiveDistance = min(max(distanceMeters - 350.0, 0.0), 180000.0);
    float horizon = pow(saturate(1.0 - abs(viewDir.y)), 1.35);
    float density = 2.25e-5 * (0.30 + 0.70 * horizon);
    float extinction = 1.0 - exp(-effectiveDistance * density);
    extinction = saturate(extinction * atmospherePresence * strength);

    float3 haze = stylizedSkyPalette(viewDir, sunDir);
    return lerp(color, haze, extinction);
}'''
new_aerial = '''float3 applyStylizedAerial(float3 color, VertexOutput input, float strength)
{
    float distanceMeters = length(input.relativePosition);
    if (distanceMeters <= 350.0 || strength <= 0.0) return color;

    float3 viewDir = input.relativePosition / max(distanceMeters, 1.0e-4);
    float3 sunDir = normalize(gPush.data1.xyz);
    float cameraAltitude = max(gPush.data0.w, 0.0);

    // Compact single-segment optical-depth approximation. The coefficients match the Rayleigh
    // values already used by skyFragmentMain; 8.5 km is the runtime atmosphere scale height.
    // Unlike the previous scalar lerp, wavelength-dependent transmittance preserves ridge and
    // valley luminance contrast while the blue channel scatters more strongly with distance.
    float densityRatio = exp(-cameraAltitude / 8500.0);
    float effectiveDistance = min(max(distanceMeters - 350.0, 0.0), 220000.0);
    float horizon = pow(saturate(1.0 - abs(viewDir.y)), 1.15);
    float opticalLength = effectiveDistance * densityRatio * (0.55 + 0.45 * horizon) * strength;
    const float3 betaR = float3(5.802e-6, 13.558e-6, 33.100e-6);
    const float betaM = 4.0e-6;
    float3 transmittance = exp(-(betaR + betaM) * opticalLength);

    float3 haze = stylizedSkyPalette(viewDir, sunDir);
    float3 inscatter = haze * (1.0 - transmittance);
    return color * transmittance + inscatter;
}'''
s = replace_once(s, old_aerial, new_aerial, 'optical aerial perspective')

s = replace_once(
    s,
    '''    float materialTag = input.material.w;
    float hazeStrength = materialTag <= -1.5 && materialTag > -4.5 ? 0.90 : 1.0;
    linearColor = applyStylizedAerial(linearColor, input, hazeStrength);''',
    '''    float materialTag = input.material.w;
    // Terrain needs enough atmospheric perspective to read planet scale, but not so much that
    // 10--100 km mountain chains disappear. Near-field ecology can take slightly stronger haze.
    float hazeStrength = materialTag < -0.5 && materialTag > -1.5 ? 0.58
        : (materialTag <= -1.5 && materialTag > -4.5 ? 0.72 : 0.66);
    linearColor = applyStylizedAerial(linearColor, input, hazeStrength);''',
    'material-aware terrain haze strength')
SHADER.write_text(s, encoding='utf-8')

# -----------------------------------------------------------------------------
# Regression: hydrology must fade back to the global surface before its tangent
# grid boundary. This guards against reintroducing the visible square process edge.
# -----------------------------------------------------------------------------
r = TESTS.read_text(encoding='utf-8')
insert_after = '''void testSurfaceAuthorityKeepsHydrologyInCollisionHeight() {
    vf::PlanetDefinition planet{};
    planet.radius = 6371000.0;
    planet.maxElevation = 8850.0;
    planet.maxOceanDepthMeters = 11000.0;
    planet.seed = 0x71A9F20DULL;
    const glm::dvec3 center = glm::normalize(glm::dvec3{0.72, 0.52, 0.46});

    vf::RegionalHydrologyConfig config{};
    config.resolution = 65U;
    config.halfExtentMeters = 45000.0;
    config.maxIncisionMeters = 220.0;
    auto hydro = std::make_shared<vf::RegionalHydrology>(planet, center, config);

    vf::PlanetSurfaceAuthority authority{planet};
    authority.setHydrology(hydro);
    const double base = vf::samplePlanetTerrain(planet, center).elevationMeters;
    const auto drainage = hydro->sample(center);
    const auto final = authority.sample(center);
    require(std::isfinite(final.elevationMeters), "surface authority elevation must remain finite");
    require(std::abs(final.elevationMeters - (base - drainage.incisionMeters)) < 1.0e-8,
        "surface authority must apply the exact hydrology incision used by rendering/physics");
}
'''
new_test = '''
void testHydrologyAuthorityFadesBeforeRegionalGridEdge() {
    vf::PlanetDefinition planet{};
    planet.radius = 6371000.0;
    planet.maxElevation = 8850.0;
    planet.maxOceanDepthMeters = 11000.0;
    planet.seed = 0x71A9F20DULL;
    const glm::dvec3 center = glm::normalize(glm::dvec3{0.72, 0.52, 0.46});
    glm::dvec3 east = glm::normalize(glm::cross(glm::dvec3{0.0, 1.0, 0.0}, center));
    if (glm::length(east) < 0.5) east = glm::normalize(glm::cross(glm::dvec3{1.0, 0.0, 0.0}, center));

    vf::RegionalHydrologyConfig config{};
    config.resolution = 65U;
    config.halfExtentMeters = 45000.0;
    config.maxIncisionMeters = 320.0;
    auto hydro = std::make_shared<vf::RegionalHydrology>(planet, center, config);
    vf::PlanetSurfaceAuthority authority{planet};
    authority.setHydrology(hydro);

    const double outsideArc = config.halfExtentMeters * 0.97;
    const double angle = outsideArc / planet.radius;
    const glm::dvec3 outsideDirection = glm::normalize(center * std::cos(angle) + east * std::sin(angle));
    const double authorityElevation = authority.elevationMeters(outsideDirection);
    const double globalElevation = vf::samplePlanetTerrain(planet, outsideDirection).elevationMeters;
    require(std::abs(authorityElevation - globalElevation) < 1.0e-7,
        "regional hydrology must return to the global surface before the square DEM boundary");
}
'''
r = replace_once(r, insert_after, insert_after + new_test, 'hydrology boundary test insertion')
r = replace_once(
    r,
    '    testSurfaceAuthorityKeepsHydrologyInCollisionHeight();\n',
    '    testSurfaceAuthorityKeepsHydrologyInCollisionHeight();\n    testHydrologyAuthorityFadesBeforeRegionalGridEdge();\n',
    'hydrology boundary test invocation')
TESTS.write_text(r, encoding='utf-8')

print('R24.1 visibility refinement staged: optical aerial perspective, physical Moon tracking, hydrology seam regression')
