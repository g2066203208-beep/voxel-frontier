from pathlib import Path

SURFACE = Path('native/src/world/PlanetSurface.cpp')
HYDRO = Path('native/include/vf/world/RegionalHydrology.hpp')
AUTHORITY = Path('native/src/world/PlanetSurfaceAuthority.cpp')
MAIN = Path('native/src/app/Main.cpp')
CMAKE = Path('native/CMakeLists.txt')
TEST = Path('native/tests/R24HydrologicCanyonTests.cpp')


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one anchor in {path}, found {count}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


# WorldEngine/stream-power ordering: global noise may identify an erosion-prone province, but it
# must not excavate a multi-kilometre fake river independently of the Priority-Flood drainage graph.
replace_once(
    SURFACE,
'''    elevation -= maxLand * 0.035 * river;
''',
'''    // Keep only a shallow global drainage precursor. Kilometre-scale fluvial incision is owned by
    // RegionalHydrology, whose Priority-Flood/D8 topology guarantees an outflowing channel network.
    elevation -= maxLand * 0.004 * river;
''',
    'demote global river displacement',
)
replace_once(
    SURFACE,
'''    // A broad canyon shoulder carries most incision. The narrow core deepens the channel without
    // turning every high-frequency crest into a vertical wall.
    elevation -= maxLand * 0.060 * canyon * (0.58 + 0.42 * canyonCore);
''',
'''    // Canyon is now an erodibility/biome propensity only. Do not excavate it here: the regional
    // Priority-Flood drainage authority below the runtime camera owns all kilometre-scale canyon
    // geometry, so canyon floors are necessarily tied to a connected downhill water network.
    (void)canyonCore;
''',
    'remove independent procedural canyon excavation',
)

# Add the runtime-configured incision ceiling as an observable quantity for the authority blend/test.
replace_once(
    HYDRO,
'''    [[nodiscard]] double cellSizeMeters() const noexcept { return cellSizeMeters_; }
    [[nodiscard]] const glm::dvec3& centerDirection() const noexcept { return center_; }
''',
'''    [[nodiscard]] double cellSizeMeters() const noexcept { return cellSizeMeters_; }
    [[nodiscard]] double maxIncisionMeters() const noexcept { return config_.maxIncisionMeters; }
    [[nodiscard]] const glm::dvec3& centerDirection() const noexcept { return center_; }
''',
    'hydrology incision accessor',
)

# Detachment-limited stream-power law: E ~ A^m S^n. EarthSurface and the Schott erosion code use
# drainage area and channel slope as the first-order drivers; common/default exponents are m=0.5,
# n=1. Here A and S are normalized to the finite regional game budget before applying the configured
# maximum incision, preserving the existing deterministic Priority-Flood topology.
replace_once(
    HYDRO,
'''        const double slopeResponse = smooth01(0.0008, 0.075, slope);
        const double incision = config_.maxIncisionMeters * channel
            * (0.22 + 0.78 * slopeResponse);
''',
'''        const double fullChannelArea = std::max(
            config_.fullChannelAccumulationFraction, 1.0e-7);
        const double normalizedArea = std::clamp(areaFraction / fullChannelArea, 0.0, 1.0);
        const double areaPower = std::sqrt(normalizedArea); // stream-power m = 0.5
        const double normalizedSlope = std::clamp(slope / 0.075, 0.0, 1.0); // n = 1
        const double streamPower = areaPower * normalizedSlope;
        // A small channel-floor term keeps Priority-Flood flats connected after depression filling;
        // the large canyon component still requires both accumulated drainage area and real slope.
        const double incisionResponse = std::clamp(0.12 + 0.88 * streamPower, 0.0, 1.0);
        const double incision = config_.maxIncisionMeters * channel * incisionResponse;
''',
    'stream-power incision',
)

# Inside the baked region, canyon semantics follow the same authority that moves the actual surface.
replace_once(
    AUTHORITY,
'''            terrain.elevationMeters -= drainage.incisionMeters * weight;
            terrain.river = std::clamp(
                terrain.river * (1.0 - weight) + drainage.channelStrength * weight,
                0.0,
                1.0);
''',
'''            terrain.elevationMeters -= drainage.incisionMeters * weight;
            terrain.river = std::clamp(
                terrain.river * (1.0 - weight) + drainage.channelStrength * weight,
                0.0,
                1.0);
            const double incisionFraction = std::clamp(
                drainage.incisionMeters / std::max(1.0, hydro->maxIncisionMeters()),
                0.0,
                1.0);
            const double hydrologicCanyon = std::clamp(
                drainage.channelStrength * std::sqrt(incisionFraction),
                0.0,
                1.0);
            terrain.canyon = std::clamp(
                terrain.canyon * (1.0 - 0.92 * weight)
                    + hydrologicCanyon * weight,
                0.0,
                1.0);
''',
    'authority canyon semantics',
)

# Increase only the regional hydrology sampling density and the explicit stream-power incision budget.
# The 3 km ceiling is 10% of the already-promoted 30 km gameplay relief budget; it is not a noise
# amplitude and cannot create a canyon where Priority-Flood finds no accumulated downhill channel.
replace_once(
    MAIN,
'''            hydroConfig.resolution = buildAltitude < 25000.0 ? 129U
                : (buildAltitude < 150000.0 ? 97U : 65U);
            hydroConfig.halfExtentMeters = 220000.0;
            hydroConfig.maxIncisionMeters = 420.0;
''',
'''            hydroConfig.resolution = buildAltitude < 25000.0 ? 193U
                : (buildAltitude < 150000.0 ? 129U : 81U);
            hydroConfig.halfExtentMeters = 220000.0;
            hydroConfig.maxIncisionMeters = std::min(3000.0, planet.maxElevation * 0.10);
''',
    'runtime hydrology resolution and budget',
)

# After the real regional bake exists, point canyon evidence at the deepest actual Priority-Flood
# incision. This is not a special render path: the same PlanetSurfaceAuthority and production mesh
# remain active; only the deterministic CI camera direction changes.
replace_once(
    MAIN,
'''        surfaceAuthority.setHydrology(initialTerrain.hydrology);
        if (moonEvidenceObserverPlaced) {
''',
'''        surfaceAuthority.setHydrology(initialTerrain.hydrology);
        if (const char* targetEnv = std::getenv("VF_TERRAIN_TARGET");
            targetEnv != nullptr && std::string_view{targetEnv} == "canyon"
            && initialTerrain.hydrology) {
            const glm::dvec3 canyonEast = stableTangent(spawnDirection);
            const glm::dvec3 canyonNorth = safeNormalize(
                glm::cross(spawnDirection, canyonEast), {0.0, 0.0, 1.0});
            glm::dvec3 bestCanyonDirection = spawnDirection;
            double bestIncisionMeters = -1.0;
            double bestChannelStrength = 0.0;
            double bestAreaFraction = 0.0;
            constexpr int canyonRings = 12;
            constexpr int canyonAzimuths = 64;
            constexpr double canyonSearchRadiusMeters = 72000.0;
            for (int ring = 2; ring <= canyonRings; ++ring) {
                const double radialMeters = canyonSearchRadiusMeters
                    * static_cast<double>(ring) / static_cast<double>(canyonRings);
                for (int i = 0; i < canyonAzimuths; ++i) {
                    const double angle = 2.0 * kPi * static_cast<double>(i)
                        / static_cast<double>(canyonAzimuths);
                    const glm::dvec3 tangent = safeNormalize(
                        canyonEast * std::cos(angle) + canyonNorth * std::sin(angle),
                        canyonEast);
                    const glm::dvec3 direction = safeNormalize(
                        spawnDirection + tangent * (radialMeters / planet.radius),
                        spawnDirection);
                    const vf::RegionalHydrologySample drainage = initialTerrain.hydrology->sample(direction);
                    if (drainage.incisionMeters > bestIncisionMeters) {
                        bestIncisionMeters = drainage.incisionMeters;
                        bestChannelStrength = drainage.channelStrength;
                        bestAreaFraction = drainage.contributingAreaFraction;
                        bestCanyonDirection = direction;
                    }
                }
            }

            double hydrologicMin = surfaceAuthority.sample(bestCanyonDirection).elevationMeters;
            double hydrologicMax = hydrologicMin;
            const glm::dvec3 targetEast = stableTangent(bestCanyonDirection);
            const glm::dvec3 targetNorth = safeNormalize(
                glm::cross(bestCanyonDirection, targetEast), canyonNorth);
            constexpr int reliefRings = 4;
            constexpr int reliefAzimuths = 48;
            constexpr double reliefRadiusMeters = 36000.0;
            for (int ring = 1; ring <= reliefRings; ++ring) {
                const double radialMeters = reliefRadiusMeters
                    * static_cast<double>(ring) / static_cast<double>(reliefRings);
                for (int i = 0; i < reliefAzimuths; ++i) {
                    const double angle = 2.0 * kPi * static_cast<double>(i)
                        / static_cast<double>(reliefAzimuths);
                    const glm::dvec3 tangent = safeNormalize(
                        targetEast * std::cos(angle) + targetNorth * std::sin(angle),
                        targetEast);
                    const glm::dvec3 direction = safeNormalize(
                        bestCanyonDirection + tangent * (radialMeters / planet.radius),
                        bestCanyonDirection);
                    const double elevation = surfaceAuthority.sample(direction).elevationMeters;
                    hydrologicMin = std::min(hydrologicMin, elevation);
                    hydrologicMax = std::max(hydrologicMax, elevation);
                }
            }
            const double hydrologicRelief = hydrologicMax - hydrologicMin;
            const glm::dvec3 targetPlanetPosition =
                surfaceAuthority.sampleSurface(bestCanyonDirection).position;
            const glm::dvec3 cameraPlanetPosition = initialInverseAster
                * (camera.position() - initialAster->position);
            const glm::dvec3 targetWorldDirection = initialAster->orientation
                * (targetPlanetPosition - cameraPlanetPosition);
            const glm::dvec3 cameraWorldUp = safeNormalize(
                initialAster->orientation * spawnDirection, {0.0, 1.0, 0.0});
            camera.setViewDirectionWorld(targetWorldDirection, cameraWorldUp);
            std::cout << "R24 hydrologic canyon view: incision_m=" << bestIncisionMeters
                      << " channel=" << bestChannelStrength
                      << " contributing_fraction=" << bestAreaFraction
                      << " relief_m=" << hydrologicRelief << '\n';
        }
        if (moonEvidenceObserverPlaced) {
''',
    'hydrologic canyon evidence framing',
)

# Add a deterministic authority-level regression test. It checks a real Priority-Flood region,
# stream-power incision and neighbourhood coherence rather than source-code masks alone.
replace_once(
    CMAKE,
'''    add_executable(vf_r24_runtime_stability_tests tests/R24RuntimeStabilityTests.cpp)
    target_link_libraries(vf_r24_runtime_stability_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_r24_runtime_stability_tests COMMAND vf_r24_runtime_stability_tests)
''',
'''    add_executable(vf_r24_runtime_stability_tests tests/R24RuntimeStabilityTests.cpp)
    target_link_libraries(vf_r24_runtime_stability_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_r24_runtime_stability_tests COMMAND vf_r24_runtime_stability_tests)
    add_executable(vf_r24_hydrologic_canyon_tests tests/R24HydrologicCanyonTests.cpp)
    target_link_libraries(vf_r24_hydrologic_canyon_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_r24_hydrologic_canyon_tests COMMAND vf_r24_hydrologic_canyon_tests)
''',
    'register hydrologic canyon test',
)

TEST.write_text(r'''#include "vf/world/PlanetSurfaceAuthority.hpp"
#include "vf/world/RegionalHydrology.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <memory>

#include <glm/geometric.hpp>

namespace {
void require(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        std::exit(1);
    }
}

glm::dvec3 safeNormalize(const glm::dvec3& value, const glm::dvec3& fallback) {
    const double l2 = glm::dot(value, value);
    return l2 > 1.0e-18 ? value / std::sqrt(l2) : fallback;
}

glm::dvec3 tangentAxis(const glm::dvec3& upInput) {
    const glm::dvec3 up = safeNormalize(upInput, {0.0, 1.0, 0.0});
    const glm::dvec3 ref = std::abs(up.y) < 0.88
        ? glm::dvec3{0.0, 1.0, 0.0}
        : glm::dvec3{1.0, 0.0, 0.0};
    return safeNormalize(glm::cross(ref, up), {1.0, 0.0, 0.0});
}
}

int main() {
    vf::PlanetDefinition planet{};
    planet.seed = 0x71A9F20DULL;
    planet.radius = 6371000.0;
    planet.maxElevation = 30000.0;
    planet.maxOceanDepthMeters = 24000.0;

    // Find the same kind of dry/elevated province used as a gameplay canyon seed. This selection
    // does not carve anything; the hydrology bake below decides where the actual channels exist.
    constexpr std::uint32_t sampleCount = 3072U;
    constexpr double goldenAngle = 2.39996322972865332;
    glm::dvec3 center{0.0, 1.0, 0.0};
    double bestScore = -1.0e30;
    for (std::uint32_t i = 0; i < sampleCount; ++i) {
        const double y = 1.0 - 2.0 * (static_cast<double>(i) + 0.5)
            / static_cast<double>(sampleCount);
        const double radial = std::sqrt(std::max(0.0, 1.0 - y * y));
        const double a = goldenAngle * static_cast<double>(i);
        const glm::dvec3 d{std::cos(a) * radial, y, std::sin(a) * radial};
        const vf::PlanetTerrainSample t = vf::samplePlanetTerrain(planet, d);
        if (t.elevationMeters < 700.0 || t.submerged(planet) || t.glacier > 0.45) continue;
        const double score = t.canyon * 3.0 + t.plateau * 0.8 + t.hills * 0.5
            + t.aridity * 0.6 - t.mountain * 0.55;
        if (score > bestScore) {
            bestScore = score;
            center = d;
        }
    }
    require(bestScore > -1.0e20, "must find a deterministic canyon-prone dry highland");

    vf::RegionalHydrologyConfig config{};
    config.resolution = 193U;
    config.halfExtentMeters = 220000.0;
    config.maxIncisionMeters = std::min(3000.0, planet.maxElevation * 0.10);
    config.riverHeadAccumulationFraction = 0.0012;
    config.fullChannelAccumulationFraction = 0.022;
    auto hydrology = std::make_shared<vf::RegionalHydrology>(planet, center, config);
    vf::PlanetSurfaceAuthority authority{planet};
    authority.setHydrology(hydrology);

    const glm::dvec3 east = tangentAxis(center);
    const glm::dvec3 north = safeNormalize(glm::cross(center, east), {0.0, 0.0, 1.0});
    double maxChannel = 0.0;
    double maxIncision = 0.0;
    double maxAuthorityCut = 0.0;
    double maxCanyon = 0.0;
    double bestEast = 0.0;
    double bestNorth = 0.0;
    constexpr int grid = 65;
    constexpr double extent = 90000.0;
    for (int iy = 0; iy < grid; ++iy) {
        const double n = -extent + 2.0 * extent * static_cast<double>(iy)
            / static_cast<double>(grid - 1);
        for (int ix = 0; ix < grid; ++ix) {
            const double e = -extent + 2.0 * extent * static_cast<double>(ix)
                / static_cast<double>(grid - 1);
            const auto drainage = hydrology->sampleLocal(e, n);
            const glm::dvec3 direction = safeNormalize(
                center + east * (e / planet.radius) + north * (n / planet.radius), center);
            const auto base = vf::samplePlanetTerrain(planet, direction);
            const auto carved = authority.sample(direction);
            const double cut = std::max(0.0, base.elevationMeters - carved.elevationMeters);
            maxChannel = std::max(maxChannel, drainage.channelStrength);
            maxAuthorityCut = std::max(maxAuthorityCut, cut);
            maxCanyon = std::max(maxCanyon, carved.canyon);
            if (drainage.incisionMeters > maxIncision) {
                maxIncision = drainage.incisionMeters;
                bestEast = e;
                bestNorth = n;
            }
        }
    }

    require(maxChannel > 0.80, "Priority-Flood accumulation must create strong regional channels");
    require(maxIncision > 900.0, "stream-power channels must create kilometre-scale canyon incision");
    require(maxAuthorityCut > 850.0, "authoritative rendered/collision surface must receive the incision");
    require(maxCanyon > 0.35, "canyon semantic mask must follow the hydrologic authority");

    // A deep incision sample must belong to a connected corridor, not be an isolated one-cell spike.
    const double neighbourStep = hydrology->cellSizeMeters();
    int connectedNeighbours = 0;
    for (int oy = -1; oy <= 1; ++oy) {
        for (int ox = -1; ox <= 1; ++ox) {
            if (ox == 0 && oy == 0) continue;
            const auto neighbour = hydrology->sampleLocal(
                bestEast + static_cast<double>(ox) * neighbourStep,
                bestNorth + static_cast<double>(oy) * neighbourStep);
            if (neighbour.incisionMeters >= maxIncision * 0.20
                && neighbour.channelStrength > 0.10) {
                ++connectedNeighbours;
            }
        }
    }
    require(connectedNeighbours >= 1,
        "deep canyon incision must connect to a neighbouring drainage cell rather than form a pillar");

    std::cout << "R24 hydrologic canyon tests passed"
              << " | max_channel=" << maxChannel
              << " max_incision_m=" << maxIncision
              << " max_authority_cut_m=" << maxAuthorityCut
              << " max_canyon=" << maxCanyon
              << " connected_neighbours=" << connectedNeighbours << '\n';
    return 0;
}
''', encoding='utf-8')

# Strong postconditions so CI can never silently run the old independent canyon geometry.
for path, marker in [
    (SURFACE, '(void)canyonCore;'),
    (HYDRO, 'const double streamPower = areaPower * normalizedSlope;'),
    (AUTHORITY, 'const double hydrologicCanyon = std::clamp('),
    (MAIN, 'R24 hydrologic canyon view: incision_m='),
    (CMAKE, 'vf_r24_hydrologic_canyon_tests'),
]:
    if marker not in path.read_text(encoding='utf-8'):
        raise SystemExit(f'missing postcondition {marker!r} in {path}')
if 'elevation -= maxLand * 0.060 * canyon' in SURFACE.read_text(encoding='utf-8'):
    raise SystemExit('legacy procedural kilometre-scale canyon excavation still present')

print('R24 hydrologic canyon authority materialized')
