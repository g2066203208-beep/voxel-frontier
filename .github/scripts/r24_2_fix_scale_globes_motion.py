#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def rw(rel):
    p = ROOT / rel
    return p, p.read_text(encoding='utf-8')

def once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f'missing anchor: {label}')
    return text.replace(old, new, 1)

# -----------------------------------------------------------------------------
# 1) Distant globe builder: preserve the authoritative 3-D height field while
#    using radial normals at planetary distance so the base sphere never turns
#    into giant visibly faceted lighting polygons.
# -----------------------------------------------------------------------------
p, t = rw('native/include/vf/world/PlanetSurface.hpp')
t = once(
    t,
    '[[nodiscard]] PlanetMesh buildPlanetSurface(const PlanetDefinition& definition, std::uint32_t subdivisionsPerFace);\n',
    '[[nodiscard]] PlanetMesh buildPlanetSurface(const PlanetDefinition& definition, std::uint32_t subdivisionsPerFace);\n'
    '[[nodiscard]] PlanetMesh buildPlanetGlobeSurface(\n'
    '    const PlanetDefinition& definition,\n'
    '    std::uint32_t subdivisionsPerFace,\n'
    '    double reliefScale = 1.0);\n',
    'planet globe declaration')
p.write_text(t, encoding='utf-8')

p, t = rw('native/src/world/PlanetSurface.cpp')
anchor = '''PlanetMesh buildPlanetSurface(
    const PlanetDefinition& definition,
    std::uint32_t subdivisionsPerFace) {
    if (subdivisionsPerFace < 2U)
        throw std::invalid_argument("planet subdivisions must be >= 2");
    PlanetMesh mesh;
    for (std::uint32_t face = 0; face < 6U; ++face) {
        appendFace(
            mesh,
            &definition,
            glm::dvec3{0.0},
            nullptr,
            definition.radius,
            face,
            subdivisionsPerFace,
            nullptr);
    }
    return mesh;
}
'''
insert = anchor + '''
PlanetMesh buildPlanetGlobeSurface(
    const PlanetDefinition& definition,
    std::uint32_t subdivisionsPerFace,
    double reliefScale) {
    if (subdivisionsPerFace < 2U)
        throw std::invalid_argument("planet globe subdivisions must be >= 2");
    reliefScale = std::clamp(reliefScale, 0.0, 1.0);

    PlanetMesh mesh{};
    const std::uint32_t stride = subdivisionsPerFace + 1U;
    for (std::uint32_t face = 0; face < 6U; ++face) {
        const std::uint32_t base = static_cast<std::uint32_t>(mesh.vertices.size());
        for (std::uint32_t y = 0; y <= subdivisionsPerFace; ++y) {
            const double v = -1.0 + 2.0 * static_cast<double>(y)
                / static_cast<double>(subdivisionsPerFace);
            for (std::uint32_t x = 0; x <= subdivisionsPerFace; ++x) {
                const double u = -1.0 + 2.0 * static_cast<double>(x)
                    / static_cast<double>(subdivisionsPerFace);
                const glm::dvec3 direction = cubeSphereDirection(face, u, v);
                const PlanetTerrainSample terrain = samplePlanetTerrain(definition, direction);
                const double scaledElevation = definition.seaLevelElevationMeters
                    + (terrain.elevationMeters - definition.seaLevelElevationMeters) * reliefScale;
                PlanetVertex vertex{};
                vertex.position = glm::vec3(direction * (definition.radius + scaledElevation));
                // Planet-scale view must read as a smooth sphere. The geometry is still truly
                // displaced in 3-D; only the distant shading normal is radial. Near-surface LOD
                // continues using the real terrain gradient normal.
                vertex.normal = glm::vec3(direction);
                vertex.color = planetTerrainColor(definition, terrain);
                vertex.material = planetTerrainMaterial(definition, terrain);
                mesh.vertices.push_back(vertex);
            }
        }
        for (std::uint32_t y = 0; y < subdivisionsPerFace; ++y) {
            for (std::uint32_t x = 0; x < subdivisionsPerFace; ++x) {
                const std::uint32_t i0 = base + y * stride + x;
                const std::uint32_t i1 = i0 + 1U;
                const std::uint32_t i2 = i0 + stride;
                const std::uint32_t i3 = i2 + 1U;
                mesh.indices.insert(mesh.indices.end(), {i0, i2, i1, i1, i2, i3});
            }
        }
    }
    return mesh;
}
'''
t = once(t, anchor, insert, 'planet globe implementation')
p.write_text(t, encoding='utf-8')

# -----------------------------------------------------------------------------
# 2) Runtime: correct Earth-Moon scale stays physical, but the renderer gets a
#    cheap smooth far-globe mesh and only uses adaptive high-resolution terrain
#    near the surface. This fixes both the giant polygon look and a major source
#    of stutter.
# -----------------------------------------------------------------------------
p, t = rw('native/src/app/Main.cpp')
t = once(
    t,
    '        double celestialTimeScale = 1.0;\n',
    '        // Gameplay clock is accelerated by default so real self-rotation and orbital motion\n'
    '        // are visible during play. Physical periods remain unchanged in simulation seconds.\n'
    '        double celestialTimeScale = 240.0;\n',
    'default celestial time scale')
t = once(
    t,
    '            catch (...) { celestialTimeScale = 1.0; }\n',
    '            catch (...) { celestialTimeScale = 240.0; }\n',
    'celestial scale fallback')

t = once(
    t,
    '''        luna.massKg = 7.342e22;
        luna.orbitParentId = asterId;''',
    '''        luna.massKg = 7.342e22;
        luna.gameplaySurfaceGravityMps2 = 1.624;
        luna.gravityInfluenceRadiusMeters = luna.radiusMeters + 450000.0;
        luna.physicsBubbleRadiusMeters = luna.radiusMeters + 900000.0;
        luna.orbitParentId = asterId;''',
    'moon physical frame')

t = once(
    t,
    '''        luna.linearVelocity = aster.linearVelocity
            + moonTangent * circularOrbitSpeed(aster.massKg, moonOrbitRadius);''',
    '''        luna.linearVelocity = aster.linearVelocity
            + moonTangent * circularOrbitSpeed(aster.massKg + luna.massKg, moonOrbitRadius);''',
    'earth moon two-body orbital speed')

t = once(
    t,
    '''        moonSurfaceDefinition.maxElevation = 9000.0;
        moonSurfaceDefinition.seaLevelElevationMeters = -2500.0;
        moonSurfaceDefinition.maxOceanDepthMeters = 0.0;
        moonSurfaceDefinition.atmosphereHeight = 0.0;
        vf::PlanetMesh moonSurfaceMesh = vf::buildPlanetSurface(moonSurfaceDefinition, 32U);
        for (auto& vertex : moonSurfaceMesh.vertices) {
            const float shade = 0.50F + 0.16F * std::abs(vertex.normal.y);
            vertex.color = {shade, shade * 0.99F, shade * 0.97F};
            vertex.material = {0.0F, 0.92F, 0.0F, -1.0F};
        }''',
    '''        // Lunar relief is kept at physical kilometre scale relative to a 1,737.4 km radius.
        // The previous 32x32 whole-sphere mesh made the Moon itself visibly polygonal. Keep a cheap
        // far mesh and a much smoother near mesh; both retain real radial displacement.
        moonSurfaceDefinition.maxElevation = 5200.0;
        moonSurfaceDefinition.seaLevelElevationMeters = -900.0;
        moonSurfaceDefinition.maxOceanDepthMeters = 7200.0;
        moonSurfaceDefinition.atmosphereHeight = 0.0;
        vf::PlanetMesh moonSurfaceMeshFar = vf::buildPlanetGlobeSurface(
            moonSurfaceDefinition, 24U, 0.58);
        vf::PlanetMesh moonSurfaceMeshNear = vf::buildPlanetGlobeSurface(
            moonSurfaceDefinition, 80U, 0.58);
        const auto styleMoon = [&](vf::PlanetMesh& mesh) {
            for (auto& vertex : mesh.vertices) {
                const double radius = glm::length(glm::dvec3(vertex.position));
                const double relief = std::clamp(
                    (radius - luna.radiusMeters) / 5200.0, -1.0, 1.0);
                const glm::dvec3 d = safeNormalize(glm::dvec3(vertex.position));
                const double marePattern = 0.5 + 0.5 * std::sin(
                    d.x * 9.0 + d.y * 5.0 - d.z * 7.0);
                const float shade = static_cast<float>(std::clamp(
                    0.43 + 0.055 * relief - 0.035 * marePattern, 0.30, 0.56));
                vertex.color = {shade, shade * 0.985F, shade * 0.955F};
                vertex.material = {0.0F, 0.94F, 0.0F, -1.0F};
            }
        };
        styleMoon(moonSurfaceMeshFar);
        styleMoon(moonSurfaceMeshNear);''',
    'smooth physical moon meshes')

# Evidence-only physical viewpoints. These do not alter normal gameplay unless explicitly set.
t = once(
    t,
    '''        const bool trackMoonEvidence = celestialTargetMode == "moon";
        std::cout << "Spawn land elevation: " << std::fixed << std::setprecision(1)''',
    '''        const bool trackMoonEvidence = celestialTargetMode == "moon";

        std::string celestialViewMode{};
        if (const char* viewEnv = std::getenv("VF_CELESTIAL_VIEW");
            viewEnv != nullptr && *viewEnv != '\\0') {
            celestialViewMode = viewEnv;
            if (celestialViewMode == "earth-globe") {
                const glm::dvec3 observerDirection = safeNormalize({0.44, 0.28, 0.85});
                const glm::dvec3 observerOffset = observerDirection * 24000000.0;
                camera.setExternalWorldState(
                    aster.position + observerOffset, aster.linearVelocity, false);
                camera.setViewDirectionWorld(-observerOffset, observerDirection);
                std::cout << "R24.2 view: earth-globe distance_km=24000\\n";
            } else if (celestialViewMode == "moon-globe") {
                const glm::dvec3 observerDirection = safeNormalize({0.38, 0.31, 0.87});
                const glm::dvec3 observerOffset = observerDirection * 6200000.0;
                camera.setExternalWorldState(
                    luna.position + observerOffset, luna.linearVelocity, false);
                camera.setViewDirectionWorld(-observerOffset, observerDirection);
                std::cout << "R24.2 view: moon-globe distance_km=6200\\n";
            } else if (celestialViewMode == "earth-from-moon") {
                const glm::dvec3 moonToEarth = safeNormalize(aster.position - luna.position);
                const glm::dvec3 observerOffset = moonToEarth * (luna.radiusMeters + 2400.0);
                const glm::dvec3 lunarAngularVelocity = safeNormalize(luna.spinAxis)
                    * luna.spinRateRadPerSecond;
                camera.setExternalWorldState(
                    luna.position + observerOffset,
                    luna.linearVelocity + glm::cross(lunarAngularVelocity, observerOffset),
                    false);
                camera.setViewDirectionWorld(
                    aster.position - camera.position(), moonToEarth);
                std::cout << "R24.2 view: earth-from-moon near-side surface\\n";
            } else if (celestialViewMode == "earth-moon-system") {
                const glm::dvec3 observerOffset = moonOrbitNormal * 760000000.0;
                camera.setExternalWorldState(
                    aster.position + observerOffset, aster.linearVelocity, false);
                camera.setViewDirectionWorld(-observerOffset, moonRadial);
                std::cout << "R24.2 view: earth-moon-system observer_km=760000\\n";
            }
        }

        std::cout << "Spawn land elevation: " << std::fixed << std::setprecision(1)''',
    'celestial physical evidence viewpoints')

# Build the distant Earth once after the body-fixed render frame exists.
t = once(
    t,
    '''        vf::PlanetSurfaceAuthority surfaceAuthority{planet};
        glm::dvec3 lodCenterDirection = patchUp;''',
    '''        vf::PlanetSurfaceAuthority surfaceAuthority{planet};

        // Whole-planet view uses a smooth, physically displaced cube-sphere instead of leaving a
        // near-ground quadtree frozen in space. This is substantially cheaper than rendering the
        // full adaptive hemisphere and prevents the planet silhouette from becoming chunky.
        vf::PlanetMesh earthGlobeMesh = vf::buildPlanetGlobeSurface(planet, 96U, 1.0);
        vf::PlanetMesh earthGlobeOcean{};
        vf::appendOceanSurfaceProxy(
            earthGlobeOcean, {}, planet.radius + planet.seaLevelElevationMeters - 1.5, 96U);
        appendMesh(earthGlobeMesh, earthGlobeOcean);
        for (auto& vertex : earthGlobeMesh.vertices) {
            const glm::dvec3 pPlanet = glm::dvec3(vertex.position);
            const glm::dvec3 nPlanet = safeNormalize(glm::dvec3(vertex.normal));
            vertex.position = glm::vec3(toSurfacePoint(pPlanet));
            vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(nPlanet)));
        }

        glm::dvec3 lodCenterDirection = patchUp;''',
    'distant earth globe')

# Cut near-terrain cost by more than half. The distant globe handles whole-planet smoothness.
t = once(t, '            lodConfig.patchResolution = 12U;\n', '            lodConfig.patchResolution = 10U;\n', 'lod patch resolution')
t = once(t, '            lodConfig.maxLeafPatches = 3200U;\n', '            lodConfig.maxLeafPatches = 1600U;\n', 'lod leaf budget')
t = once(t, '            lodConfig.targetScreenErrorPixels = 2.8;\n', '            lodConfig.targetScreenErrorPixels = 3.4;\n', 'lod sse target')
t = once(t, '                oceanProxy, {}, planet.radius + planet.seaLevelElevationMeters - 1.5, 160U);\n',
         '                oceanProxy, {}, planet.radius + planet.seaLevelElevationMeters - 1.5, 96U);\n',
         'near ocean tessellation')

# Keep a near mesh and a distant globe, upload only on state transitions.
t = once(
    t,
    '''        vf::PlanetLodStats currentLodStats = initialTerrain.stats;
        vf::PlanetMesh staticTerrain = std::move(initialTerrain.mesh);
        renderer.uploadPlanetMesh(staticTerrain);
        std::future<TerrainBuildResult> terrainBuildFuture{};''',
    '''        vf::PlanetLodStats currentLodStats = initialTerrain.stats;
        vf::PlanetMesh nearTerrain = std::move(initialTerrain.mesh);
        bool usingDistantEarthGlobe = camera.physicsFrameBodyId() != asterId
            || camera.altitude() > 900000.0;
        renderer.uploadPlanetMesh(usingDistantEarthGlobe ? earthGlobeMesh : nearTerrain);
        std::future<TerrainBuildResult> terrainBuildFuture{};''',
    'near versus far earth mesh')

# Toggle far/near mesh without rebuilding per frame.
t = once(
    t,
    '''            lodCooldown = std::max(0.0, lodCooldown - dt);
            const double altitude = camera.altitude();
            if (camera.physicsFrameBodyId() == asterId && altitude < 800000.0) {''',
    '''            lodCooldown = std::max(0.0, lodCooldown - dt);
            const double altitude = camera.altitude();
            const bool wantsDistantEarthGlobe = camera.physicsFrameBodyId() != asterId
                || altitude > 900000.0;
            if (wantsDistantEarthGlobe != usingDistantEarthGlobe) {
                usingDistantEarthGlobe = wantsDistantEarthGlobe;
                renderer.uploadPlanetMesh(usingDistantEarthGlobe ? earthGlobeMesh : nearTerrain);
                std::cout << "R24.2 Earth renderer mode: "
                          << (usingDistantEarthGlobe ? "smooth-globe" : "adaptive-terrain") << '\\n';
            }
            if (camera.physicsFrameBodyId() == asterId && altitude < 800000.0) {''',
    'earth render mode switch')

t = once(
    t,
    '''                    currentLodStats = completed.stats;
                    staticTerrain = std::move(completed.mesh);
                    renderer.uploadPlanetMesh(staticTerrain);
                    lodCooldown = 0.12;''',
    '''                    currentLodStats = completed.stats;
                    nearTerrain = std::move(completed.mesh);
                    if (!usingDistantEarthGlobe) renderer.uploadPlanetMesh(nearTerrain);
                    lodCooldown = 0.12;''',
    'terrain completion upload')

# Far Moon = cheap mesh; close Moon = smooth high-resolution physical globe.
t = once(
    t,
    '''            if (currentMoon != nullptr) {
                vf::PlanetMesh moonMesh = moonSurfaceMesh;
                const glm::dvec3 moonRelativeWorld = currentMoon->position - currentAster->position;''',
    '''            if (currentMoon != nullptr) {
                const double moonCameraDistance = glm::length(currentMoon->position - camera.position());
                const vf::PlanetMesh& moonSource = moonCameraDistance < 12000000.0
                    ? moonSurfaceMeshNear : moonSurfaceMeshFar;
                vf::PlanetMesh moonMesh = moonSource;
                const glm::dvec3 moonRelativeWorld = currentMoon->position - currentAster->position;''',
    'moon near far mesh selection')

t = once(
    t,
    '        std::cout << "SSE cube-sphere quadtree | unified surface authority | deterministic stylized ecology\\n";\n',
    '        std::cout << "SSE cube-sphere quadtree | smooth distant globes | deterministic stylized ecology\\n";\n'
    '        std::cout << "Earth-Moon physical scale: Rearth=6371 km Rmoon=1737.4 km distance=384400 km"\n'
    '                  << " | celestial time scale=" << celestialTimeScale << "x\\n";\n',
    'runtime scale banner')

p.write_text(t, encoding='utf-8')

# -----------------------------------------------------------------------------
# 3) Tests: lock in NASA/JPL-scale geometry and prove that self-rotation and
#    revolution genuinely change the integrated state.
# -----------------------------------------------------------------------------
p, t = rw('native/tests/R24PhysicalPlanetTests.cpp')
t = once(
    t,
    '#include "vf/world/PlanetSurfaceAuthority.hpp"\n',
    '#include "vf/world/PlanetSurfaceAuthority.hpp"\n#include "vf/world/CelestialSystem.hpp"\n',
    'celestial test include')

new_test = r'''
void testEarthMoonPhysicalScaleRotationAndRevolution() {
    constexpr double earthRadius = 6371000.0;
    constexpr double moonRadius = 1737400.0;
    constexpr double distance = 384400000.0;
    constexpr double earthMass = 5.9722e24;
    constexpr double moonMass = 7.342e22;
    constexpr double pi = 3.14159265358979323846;

    const double moonAngularDiameter = 2.0 * std::atan(moonRadius / distance) * 180.0 / pi;
    const double earthAngularDiameterFromMoon = 2.0 * std::atan(earthRadius / distance) * 180.0 / pi;
    require(moonAngularDiameter > 0.50 && moonAngularDiameter < 0.54,
        "physical Moon must subtend about half a degree from Earth");
    require(earthAngularDiameterFromMoon > 1.85 && earthAngularDiameterFromMoon < 1.95,
        "physical Earth must subtend about 1.9 degrees from the Moon");

    vf::PlanetDefinition earthDefinition{};
    earthDefinition.radius = earthRadius;
    earthDefinition.maxElevation = 8850.0;
    earthDefinition.maxOceanDepthMeters = 11000.0;
    const vf::PlanetMesh globe = vf::buildPlanetGlobeSurface(earthDefinition, 12U, 1.0);
    require(!globe.vertices.empty() && !globe.indices.empty(),
        "distant globe must contain real displaced 3-D geometry");
    for (std::size_t i = 0; i < globe.vertices.size(); i += 37U) {
        const glm::dvec3 p = glm::dvec3(globe.vertices[i].position);
        const glm::dvec3 n = glm::dvec3(globe.vertices[i].normal);
        require(std::abs(glm::length(n) - 1.0) < 1.0e-5,
            "planet-scale globe normals must stay unit length and smooth");
        require(glm::length(p) > earthRadius - 12000.0 && glm::length(p) < earthRadius + 10000.0,
            "planet-scale globe must preserve physical relief rather than exaggerated chunks");
    }

    vf::CelestialSystem system;
    vf::CelestialBody earth{};
    earth.type = vf::CelestialBodyType::Planet;
    earth.radiusMeters = earthRadius;
    earth.massKg = earthMass;
    earth.spinAxis = {0.0, 1.0, 0.0};
    earth.spinRateRadPerSecond = 2.0 * pi / 86164.0905;

    vf::CelestialBody moon{};
    moon.type = vf::CelestialBodyType::Moon;
    moon.radiusMeters = moonRadius;
    moon.massKg = moonMass;
    moon.spinAxis = {0.0, 1.0, 0.0};
    moon.spinRateRadPerSecond = 2.0 * pi / (27.321661 * 86400.0);

    const double totalMass = earthMass + moonMass;
    const double relativeSpeed = std::sqrt(vf::CelestialSystem::kGravitationalConstant * totalMass / distance);
    earth.position = {-distance * moonMass / totalMass, 0.0, 0.0};
    moon.position = {distance * earthMass / totalMass, 0.0, 0.0};
    earth.linearVelocity = {0.0, 0.0, relativeSpeed * moonMass / totalMass};
    moon.linearVelocity = {0.0, 0.0, -relativeSpeed * earthMass / totalMass};

    const auto earthId = system.addBody(earth);
    const auto moonId = system.addBody(moon);
    const glm::dvec3 initialRelative = system.body(moonId)->position - system.body(earthId)->position;
    const glm::dquat initialEarthOrientation = system.body(earthId)->orientation;

    constexpr int sixHoursInMinuteSteps = 360;
    for (int i = 0; i < sixHoursInMinuteSteps; ++i) system.step(60.0);

    const auto* movedEarth = system.body(earthId);
    const auto* movedMoon = system.body(moonId);
    const glm::dvec3 finalRelative = movedMoon->position - movedEarth->position;
    const double separationError = std::abs(glm::length(finalRelative) - distance) / distance;
    require(separationError < 2.0e-4,
        "Earth-Moon two-body separation must remain stable over a six-hour integration window");
    require(glm::dot(glm::normalize(initialRelative), glm::normalize(finalRelative)) < 0.9995,
        "Moon must visibly revolve around Earth over simulated time");
    require(std::abs(glm::dot(initialEarthOrientation, movedEarth->orientation)) < 0.999,
        "Earth orientation must change from physical self-rotation");
}
'''
t = once(t, '\n} // namespace\n\nint main() {', '\n' + new_test + '\n} // namespace\n\nint main() {', 'earth moon motion test body')
t = once(
    t,
    '    testOceanSpectrumHasTargetVarianceAndMoves();\n',
    '    testOceanSpectrumHasTargetVarianceAndMoves();\n    testEarthMoonPhysicalScaleRotationAndRevolution();\n',
    'earth moon motion test invocation')
p.write_text(t, encoding='utf-8')

print('R24.2 physical scale/globe/motion integration staged')
