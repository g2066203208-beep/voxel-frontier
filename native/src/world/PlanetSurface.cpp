#include "vf/world/PlanetSurface.hpp"
#include "vf/world/PlanetGeomorph.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <stdexcept>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;
constexpr std::size_t kPlateCount = 20U;

[[nodiscard]] std::uint64_t seedBits(std::uint64_t seed, std::uint64_t channel) noexcept {
    std::uint64_t x = seed + 0x9E3779B97F4A7C15ULL * (channel + 1ULL);
    x ^= x >> 30U;
    x *= 0xBF58476D1CE4E5B9ULL;
    x ^= x >> 27U;
    x *= 0x94D049BB133111EBULL;
    x ^= x >> 31U;
    return x;
}

[[nodiscard]] double seedUnit(std::uint64_t seed, std::uint64_t channel) noexcept {
    return static_cast<double>(seedBits(seed, channel) & 0xFFFFFFULL)
        / static_cast<double>(0xFFFFFFULL);
}

[[nodiscard]] double seedPhase(std::uint64_t seed, std::uint64_t channel) noexcept {
    return seedUnit(seed, channel) * 2.0 * kPi;
}

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-18) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] double smooth01(double edge0, double edge1, double value) noexcept {
    if (edge1 <= edge0) return value >= edge1 ? 1.0 : 0.0;
    const double x = std::clamp((value - edge0) / (edge1 - edge0), 0.0, 1.0);
    return x * x * (3.0 - 2.0 * x);
}

[[nodiscard]] double quintic(double x) noexcept {
    x = std::clamp(x, 0.0, 1.0);
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0);
}

[[nodiscard]] std::uint64_t latticeBits(
    std::uint64_t seed,
    std::int64_t x,
    std::int64_t y,
    std::int64_t z) noexcept {
    std::uint64_t h = seed ^ 0xD6E8FEB86659FD93ULL;
    h ^= static_cast<std::uint64_t>(x) * 0x9E3779B185EBCA87ULL;
    h ^= static_cast<std::uint64_t>(y) * 0xC2B2AE3D27D4EB4FULL;
    h ^= static_cast<std::uint64_t>(z) * 0x165667B19E3779F9ULL;
    h ^= h >> 29U;
    h *= 0x94D049BB133111EBULL;
    h ^= h >> 31U;
    return h;
}

[[nodiscard]] double latticeValue(
    std::uint64_t seed,
    std::int64_t x,
    std::int64_t y,
    std::int64_t z) noexcept {
    const std::uint64_t bits = latticeBits(seed, x, y, z);
    const double unit = static_cast<double>(bits & 0xFFFFFFULL)
        / static_cast<double>(0xFFFFFFULL);
    return unit * 2.0 - 1.0;
}

[[nodiscard]] double valueNoise3(
    std::uint64_t seed,
    const glm::dvec3& p) noexcept {
    const auto x0 = static_cast<std::int64_t>(std::floor(p.x));
    const auto y0 = static_cast<std::int64_t>(std::floor(p.y));
    const auto z0 = static_cast<std::int64_t>(std::floor(p.z));
    const double tx = quintic(p.x - static_cast<double>(x0));
    const double ty = quintic(p.y - static_cast<double>(y0));
    const double tz = quintic(p.z - static_cast<double>(z0));

    const auto lerpD = [](double a, double b, double t) noexcept {
        return a + (b - a) * t;
    };

    const double n000 = latticeValue(seed, x0,     y0,     z0);
    const double n100 = latticeValue(seed, x0 + 1, y0,     z0);
    const double n010 = latticeValue(seed, x0,     y0 + 1, z0);
    const double n110 = latticeValue(seed, x0 + 1, y0 + 1, z0);
    const double n001 = latticeValue(seed, x0,     y0,     z0 + 1);
    const double n101 = latticeValue(seed, x0 + 1, y0,     z0 + 1);
    const double n011 = latticeValue(seed, x0,     y0 + 1, z0 + 1);
    const double n111 = latticeValue(seed, x0 + 1, y0 + 1, z0 + 1);

    const double nx00 = lerpD(n000, n100, tx);
    const double nx10 = lerpD(n010, n110, tx);
    const double nx01 = lerpD(n001, n101, tx);
    const double nx11 = lerpD(n011, n111, tx);
    return lerpD(lerpD(nx00, nx10, ty), lerpD(nx01, nx11, ty), tz);
}

[[nodiscard]] double fbmSurface(
    std::uint64_t seed,
    const glm::dvec3& direction,
    double baseFrequency,
    int octaves) noexcept {
    double amplitude = 1.0;
    double frequency = baseFrequency;
    double sum = 0.0;
    double normalization = 0.0;
    for (int octave = 0; octave < octaves; ++octave) {
        const std::uint64_t octaveSeed = seedBits(seed, 4000U + static_cast<std::uint64_t>(octave) * 29U);
        sum += valueNoise3(octaveSeed, direction * frequency) * amplitude;
        normalization += amplitude;
        frequency *= 2.07;
        amplitude *= 0.48;
    }
    return normalization > 0.0 ? sum / normalization : 0.0;
}

[[nodiscard]] double resolvedOceanDepth(const PlanetDefinition& definition) noexcept {
    return std::max(0.0, definition.maxOceanDepthMeters > 0.0
        ? definition.maxOceanDepthMeters
        : definition.maxElevation);
}

[[nodiscard]] glm::dvec3 seededDirection(std::uint64_t seed, std::uint64_t channel) noexcept {
    const double longitude = seedPhase(seed, channel);
    const double z = seedUnit(seed, channel + 37U) * 2.0 - 1.0;
    const double radial = std::sqrt(std::max(0.0, 1.0 - z * z));
    return {std::cos(longitude) * radial, z, std::sin(longitude) * radial};
}

[[nodiscard]] glm::dvec3 tangentAxis(const glm::dvec3& upInput) noexcept {
    const glm::dvec3 up = safeNormalize(upInput);
    const glm::dvec3 a = glm::abs(up);
    glm::dvec3 reference{1.0, 0.0, 0.0};
    if (a.y <= a.x && a.y <= a.z) reference = {0.0, 1.0, 0.0};
    else if (a.z <= a.x && a.z <= a.y) reference = {0.0, 0.0, 1.0};
    return safeNormalize(glm::cross(reference, up), {1.0, 0.0, 0.0});
}

struct PlateSeed {
    glm::dvec3 center{};
    glm::dvec3 eulerPole{};
    double speed{};
    bool continental{};
};

[[nodiscard]] PlateSeed makePlate(std::uint64_t seed, std::size_t index) noexcept {
    const std::uint64_t i = static_cast<std::uint64_t>(index);
    PlateSeed plate{};
    plate.center = seededDirection(seed, 100U + i * 11U);
    plate.eulerPole = seededDirection(seed, 500U + i * 13U);
    plate.speed = 0.35 + 0.65 * seedUnit(seed, 800U + i * 17U);
    // Earth is an ocean-dominated planet (NOAA: about 71% water coverage). A smaller population of
    // buoyant continental plate cells, combined with shelves and plate-boundary deformation, keeps
    // the default seed near that large-scale land/ocean balance without hard-coding coastlines.
    plate.continental = seedUnit(seed, 1200U + i * 19U) > 0.82;
    return plate;
}

[[nodiscard]] glm::dvec3 plateVelocityAt(const PlateSeed& plate, const glm::dvec3& direction) noexcept {
    return glm::cross(plate.eulerPole, direction) * plate.speed;
}

struct PlateField {
    PlateSeed primary{};
    PlateSeed secondary{};
    double boundary{};
    double convergence{};
    double divergence{};
};

[[nodiscard]] PlateField samplePlateField(std::uint64_t seed, const glm::dvec3& directionInput) noexcept {
    const glm::dvec3 direction = safeNormalize(directionInput);
    const glm::dvec3 rawWarp{
        fbmSurface(seed ^ 0x6A09E667F3BCC909ULL, direction, 2.8, 3),
        fbmSurface(seed ^ 0xBB67AE8584CAA73BULL, direction, 2.8, 3),
        fbmSurface(seed ^ 0x3C6EF372FE94F82BULL, direction, 2.8, 3)};
    const glm::dvec3 tangentWarp = rawWarp - direction * glm::dot(rawWarp, direction);
    // ~0-250 km nominal lateral bending on an Earth-radius sphere.
    const glm::dvec3 plateDirection = safeNormalize(direction + tangentWarp * 0.050, direction);
    double bestScore = -std::numeric_limits<double>::infinity();
    double secondScore = -std::numeric_limits<double>::infinity();
    PlateSeed best{};
    PlateSeed second{};

    for (std::size_t i = 0; i < kPlateCount; ++i) {
        const PlateSeed plate = makePlate(seed, i);
        const double score = glm::dot(plateDirection, plate.center);
        if (score > bestScore) {
            secondScore = bestScore;
            second = best;
            bestScore = score;
            best = plate;
        } else if (score > secondScore) {
            secondScore = score;
            second = plate;
        }
    }

    const double scoreGap = std::max(0.0, bestScore - secondScore);
    const double boundary = 1.0 - smooth01(0.008, 0.090, scoreGap);

    glm::dvec3 boundaryNormal = second.center - best.center;
    boundaryNormal -= direction * glm::dot(boundaryNormal, direction);
    boundaryNormal = safeNormalize(boundaryNormal, tangentAxis(direction));

    const glm::dvec3 relativeVelocity = plateVelocityAt(second, direction) - plateVelocityAt(best, direction);
    const double separationRate = glm::dot(relativeVelocity, boundaryNormal);
    const double divergence = boundary * smooth01(0.04, 0.72, separationRate);
    const double convergence = boundary * smooth01(0.04, 0.72, -separationRate);
    return {best, second, boundary, convergence, divergence};
}

[[nodiscard]] glm::vec3 proxyColor(const glm::vec3& baseColor, const glm::dvec3& localDirection) {
    if (baseColor.x < 0.0F || baseColor.y < 0.0F || baseColor.z < 0.0F) return baseColor;
    const double bands = 0.5 + 0.5 * std::sin(localDirection.y * 17.0 + localDirection.x * 5.0);
    const double patches = 0.5 + 0.5 * std::sin(localDirection.x * 11.0 - localDirection.z * 13.0);
    const float scale = static_cast<float>(0.68 + 0.20 * bands + 0.12 * patches);
    return glm::clamp(baseColor * scale, glm::vec3{0.0F}, glm::vec3{1.0F});
}

void appendFace(
    PlanetMesh& mesh,
    const PlanetDefinition* definition,
    const glm::dvec3& center,
    const glm::dquat* orientation,
    double radius,
    std::uint32_t face,
    std::uint32_t subdivisions,
    const glm::vec3* constantColor) {
    const std::uint32_t stride = subdivisions + 1U;
    const std::uint32_t baseVertex = static_cast<std::uint32_t>(mesh.vertices.size());
    for (std::uint32_t y = 0; y <= subdivisions; ++y) {
        const double v = -1.0 + 2.0 * static_cast<double>(y) / static_cast<double>(subdivisions);
        for (std::uint32_t x = 0; x <= subdivisions; ++x) {
            const double u = -1.0 + 2.0 * static_cast<double>(x) / static_cast<double>(subdivisions);
            const glm::dvec3 localDirection = cubeSphereDirection(face, u, v);
            const PlanetTerrainSample terrain = definition
                ? samplePlanetTerrain(*definition, localDirection)
                : PlanetTerrainSample{};
            const glm::dvec3 localNormal = definition
                ? planetSurfaceNormal(*definition, localDirection)
                : localDirection;
            const glm::dvec3 worldDirection = orientation
                ? safeNormalize((*orientation) * localDirection)
                : localDirection;
            const glm::dvec3 worldNormal = orientation
                ? safeNormalize((*orientation) * localNormal)
                : localNormal;
            const double elevation = definition ? terrain.elevationMeters : 0.0;
            PlanetVertex vertex{};
            vertex.position = glm::vec3(center + worldDirection * (radius + elevation));
            vertex.normal = glm::vec3(worldNormal);
            vertex.color = constantColor
                ? proxyColor(*constantColor, localDirection)
                : planetTerrainColor(*definition, terrain);
            vertex.material = definition
                ? planetTerrainMaterial(*definition, terrain)
                : glm::vec4{0.0F, 0.72F, 0.0F, 0.0F};
            if (definition) {
                vertex.material.x = static_cast<float>(std::clamp(
                    1.0 - glm::dot(localNormal, localDirection), 0.0, 1.0));
            }
            mesh.vertices.push_back(vertex);
        }
    }
    for (std::uint32_t y = 0; y < subdivisions; ++y) {
        for (std::uint32_t x = 0; x < subdivisions; ++x) {
            const std::uint32_t i0 = baseVertex + y * stride + x;
            const std::uint32_t i1 = i0 + 1U;
            const std::uint32_t i2 = i0 + stride;
            const std::uint32_t i3 = i2 + 1U;
            mesh.indices.insert(mesh.indices.end(), {i0, i2, i1, i1, i2, i3});
        }
    }
}

void appendOceanFace(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double radius,
    std::uint32_t face,
    std::uint32_t subdivisions) {
    const std::uint32_t stride = subdivisions + 1U;
    const std::uint32_t baseVertex = static_cast<std::uint32_t>(mesh.vertices.size());
    for (std::uint32_t y = 0; y <= subdivisions; ++y) {
        const double v = -1.0 + 2.0 * static_cast<double>(y) / static_cast<double>(subdivisions);
        for (std::uint32_t x = 0; x <= subdivisions; ++x) {
            const double u = -1.0 + 2.0 * static_cast<double>(x) / static_cast<double>(subdivisions);
            const glm::dvec3 direction = cubeSphereDirection(face, u, v);
            PlanetVertex vertex{};
            vertex.position = glm::vec3(center + direction * radius);
            vertex.normal = glm::vec3(direction);
            vertex.color = {0.020F, 0.205F, 0.315F};
            vertex.material = {-1.0F, 0.055F, 0.72F, 0.0F};
            mesh.vertices.push_back(vertex);
        }
    }
    for (std::uint32_t y = 0; y < subdivisions; ++y) {
        for (std::uint32_t x = 0; x < subdivisions; ++x) {
            const std::uint32_t i0 = baseVertex + y * stride + x;
            const std::uint32_t i1 = i0 + 1U;
            const std::uint32_t i2 = i0 + stride;
            const std::uint32_t i3 = i2 + 1U;
            mesh.indices.insert(mesh.indices.end(), {i0, i2, i1, i1, i2, i3});
        }
    }
}

} // namespace

glm::dvec3 cubeSphereDirection(std::uint32_t face, double u, double v) {
    glm::dvec3 cube{};
    switch (face) {
    case 0: cube = {1.0, v, -u}; break;
    case 1: cube = {-1.0, v, u}; break;
    case 2: cube = {u, 1.0, -v}; break;
    case 3: cube = {u, -1.0, v}; break;
    case 4: cube = {u, v, 1.0}; break;
    case 5: cube = {-u, v, -1.0}; break;
    default: throw std::out_of_range("cubeSphereDirection face must be 0..5");
    }
    return glm::normalize(cube);
}

PlanetTerrainSample samplePlanetTerrain(
    const PlanetDefinition& definition,
    const glm::dvec3& directionInput) {
    const glm::dvec3 d = safeNormalize(directionInput);
    const PlateField plates = samplePlateField(definition.seed, d);

    // Low-frequency tangent warp bends continental margins and mountain systems before
    // any regional detail is sampled. Macro morphology must exist independently of the
    // walking-scale noise or the planet degenerates into a smooth sphere with texture noise.
    const glm::dvec3 macroWarpRaw{
        fbmSurface(definition.seed ^ 0xB7E151628AED2A6BULL, d, 2.2, 4),
        fbmSurface(definition.seed ^ 0x9E3779B97F4A7C15ULL, d, 2.2, 4),
        fbmSurface(definition.seed ^ 0xC6EF372FE94F82BEULL, d, 2.2, 4)};
    const glm::dvec3 macroWarp = macroWarpRaw - d * glm::dot(macroWarpRaw, d);
    const glm::dvec3 w = safeNormalize(d + macroWarp * 0.060, d);

    // Continental crust is intentionally separate from plate ownership: real plates can
    // carry both continental and oceanic lithosphere. Three spatial bands produce large
    // continents, secondary peninsulas/islands and detailed coastlines.
    const double crustMacro = fbmSurface(
        definition.seed ^ 0x243F6A8885A308D3ULL, w, 3.15, 5);
    const double crustMeso = fbmSurface(
        definition.seed ^ 0x13198A2E03707344ULL, w, 7.8, 4);
    const double crustCoast = fbmSurface(
        definition.seed ^ 0xA4093822299F31D0ULL, w, 21.0, 3);
    const double islandArcNoise = fbmSurface(
        definition.seed ^ 0x082EFA98EC4E6C89ULL, w, 38.0, 3);
    const double continentalness = std::clamp(
        crustMacro * 0.78 + crustMeso * 0.27 + crustCoast * 0.09
            + islandArcNoise * plates.convergence * 0.060 - 0.098,
        -1.0, 1.0);
    const double landness = smooth01(-0.010, 0.082, continentalness);
    const double oceanness = 1.0 - landness;
    const double interior = smooth01(0.06, 0.36, continentalness);
    const double coastProximity = 1.0
        - smooth01(0.018, 0.22, std::abs(continentalness));

    const double maxLand = std::max(0.0, definition.maxElevation);
    const double maxOcean = resolvedOceanDepth(definition);
    double elevation = 0.0;

    // Ocean hypsometry: broad abyssal floor, continental shelves, divergent ridges and
    // convergent trenches. The default seed remains close to Earth's mean ocean depth.
    const double deepOcean = smooth01(0.08, 0.62, -continentalness);
    const double shelfZone = coastProximity * oceanness;
    elevation -= maxOcean * (0.285 + 0.390 * deepOcean) * oceanness;
    elevation += maxOcean * 0.115 * shelfZone;

    const double ridgeShape = 0.5 + 0.5 * (1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xD1310BA698DFB5ACULL, w, 42.0, 4)));
    const double oceanRidge = plates.divergence * oceanness
        * (0.58 + 0.42 * ridgeShape);
    elevation += maxOcean * 0.300 * oceanRidge;

    const double trench = std::pow(
        std::clamp(plates.convergence * oceanness, 0.0, 1.0), 1.22);
    elevation -= maxOcean * 0.500 * trench;

    // Continents are not flat plates. Broad undulation and regional provinces are a
    // mandatory relief floor before hills/mountains are layered on top.
    elevation += maxLand
        * (0.025 + 0.055 * std::pow(landness, 1.30)) * landness;
    const double broadUndulation = fbmSurface(
        definition.seed ^ 0x510E527FADE682D1ULL, w, 6.5, 5);
    const double regionalProvince = fbmSurface(
        definition.seed ^ 0x6A09E667F3BCC909ULL, w, 20.0, 5);
    elevation += maxLand * landness
        * (0.060 * broadUndulation + 0.040 * regionalProvince);

    // Plateaus are broad highlands with their fine hill relief intentionally damped later.
    const double plateauField = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0xBB67AE8584CAA73BULL, w, 10.0, 4);
    const double plateau = smooth01(0.62, 0.84, plateauField)
        * landness * (1.0 - 0.42 * plates.boundary);
    elevation += maxLand * 0.145 * plateau;

    // Orogenic belts: broad uplift gives the range its mass; ridged noise breaks the belt
    // into parallel ranges; a separate sparse field selects high summits so the whole
    // boundary never becomes one uniform 8 km wall.
    const double orogenDrive = std::clamp(
        plates.convergence * landness * (0.66 + 0.34 * interior), 0.0, 1.0);
    const double mountain = std::pow(orogenDrive, 1.12);
    const double ridgeField = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0x3C6EF372FE94F82BULL, w, 38.0, 5));
    const double rangeRidges = smooth01(0.34, 0.82, ridgeField) * mountain;
    elevation += maxLand * (0.285 * mountain + 0.165 * rangeRidges);

    const double summitField = 0.5 + 0.5 * fbmSurface(
        definition.seed ^ 0x452821E638D01377ULL, w, 118.0, 4);
    const double summitGate = smooth01(0.69, 0.89, summitField)
        * smooth01(0.38, 0.86, mountain);
    elevation += maxLand * 0.270 * std::pow(summitGate, 3.2);

    // Climate authority. It affects surface processes/materials, not the existence of the
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

    // Rolling hills are a floor, not a rare mask. This is the layer Trial 6 was missing:
    // even stable continental interiors get 100-300 m relief instead of endless planes.
    const double hillNoise = fbmSurface(
        definition.seed ^ 0x5BE0CD19137E2179ULL, w, 105.0, 5);
    const double hillField = 0.5 + 0.5 * hillNoise;
    const double hills = smooth01(0.27, 0.73, hillField)
        * landness * (1.0 - 0.58 * mountain) * (1.0 - 0.58 * plateau);
    const double hillFloor = landness
        * (1.0 - 0.72 * mountain) * (1.0 - 0.52 * plateau);
    elevation += maxLand * 0.031 * hillNoise
        * (0.62 + 0.38 * hills) * hillFloor;

    // Long valleys and canyon networks. This remains a deterministic analytic drainage
    // approximation; a later coarse DEM hydrology bake can replace only this layer without
    // disturbing the tectonic/LOD/material architecture introduced here.
    const double riverWarp = fbmSurface(
        definition.seed ^ 0xCBBB9D5DC1059ED8ULL, w, 46.0, 3);
    const double p0 = seedPhase(definition.seed, 70U);
    const double p1 = seedPhase(definition.seed, 71U);
    const double p2 = seedPhase(definition.seed, 72U);
    const double channelA = 1.0 - std::abs(std::sin(
        w.x * 9.0 + w.z * 6.0 - w.y * 3.5 + riverWarp * 2.4 + p0));
    const double channelB = 1.0 - std::abs(std::sin(
        w.z * 12.5 - w.x * 7.0 + w.y * 5.0 - riverWarp * 2.1 + p1));
    const double channelField = std::max(channelA, channelB);
    const double river = std::pow(smooth01(0.948, 0.9975, channelField), 1.8)
        * landness * interior * (1.0 - 0.62 * mountain);
    elevation -= maxLand * (0.013 + 0.016 * interior) * river;

    const double canyonGuide = 1.0 - std::abs(std::sin(
        w.x * 31.0 + w.y * 13.0 - w.z * 27.0
            + fbmSurface(definition.seed ^ 0xA54FF53A5F1D36F1ULL, w, 58.0, 3) * 4.0 + p2));
    const double canyon = smooth01(0.972, 0.9993, canyonGuide)
        * landness * interior * (0.35 + 0.65 * aridity)
        * (0.38 + 0.62 * std::clamp(0.5 + 0.5 * regionalProvince, 0.0, 1.0));
    elevation -= maxLand * 0.060 * canyon;

    // Hotspot volcanoes are actual cones with a small summit crater instead of a generic
    // uplift blob. Arc volcanism remains subordinate to convergent margins.
    double hotspotVolcano = 0.0;
    double hotspotCrater = 0.0;
    for (std::uint64_t i = 0; i < 11U; ++i) {
        const glm::dvec3 hotspot = seededDirection(definition.seed, 2000U + i * 7U);
        const double proximity = glm::dot(d, hotspot);
        const double cone = smooth01(std::cos(0.040), std::cos(0.0045), proximity);
        const double crater = smooth01(std::cos(0.0052), std::cos(0.0014), proximity);
        hotspotVolcano = std::max(hotspotVolcano, std::pow(cone, 2.0));
        hotspotCrater = std::max(hotspotCrater, std::pow(crater, 2.3));
    }
    const double arcVolcano = plates.convergence * plates.boundary
        * (0.20 + 0.80 * std::max(landness, 0.30 * oceanness));
    const double volcano = std::clamp(
        std::max(hotspotVolcano, arcVolcano * 0.68), 0.0, 1.0);
    elevation += maxLand * (0.300 * hotspotVolcano + 0.160 * arcVolcano);
    elevation -= maxLand * 0.075 * hotspotCrater * hotspotVolcano;

    // Coastal cliffs, wetlands, dunes and glaciers are geomorphic process masks with
    // visible geometry contributions, not merely colour labels.
    const double localRugged = std::clamp(
        0.22 + std::abs(regionalProvince) * 0.62
            + mountain * 0.80 + plates.boundary * 0.30,
        0.0, 1.0);
    const double coastalCliff = coastProximity * landness
        * smooth01(0.45, 0.82, localRugged) * (1.0 - 0.72 * river);
    elevation += maxLand * 0.020 * coastalCliff;

    const double lowland = 1.0 - smooth01(180.0, 1050.0, elevation);
    const double wetland = std::clamp(
        lowland * moisture * landness
            * (0.28 + 0.72 * std::max(river, coastProximity * 0.35)),
        0.0, 1.0);

    const double duneRegion = aridity * landness
        * (1.0 - 0.78 * mountain) * (1.0 - 0.55 * river);
    const double duneWave = std::sin(
        (w.x * 15000.0 + w.z * 11000.0) + climateNoise * 5.0);
    const double dunes = smooth01(0.48, 0.78, duneRegion);
    elevation += maxLand * 0.0022 * dunes * duneWave;

    const double glacier = smooth01(0.58, 0.79, latitude)
        * smooth01(1700.0, 3600.0, elevation)
        * smooth01(0.34, 0.72, moisture) * landness;
    elevation += maxLand * 0.006 * glacier
        * (1.0 - std::abs(fbmSurface(
            definition.seed ^ 0x6C44198C4A475817ULL, w, 62.0, 4)));

    // R4 macro authority: a globally baked DEM is hydrologically conditioned with
    // Priority-Flood, downhill discharge accumulation, hydraulic incision and conservative
    // thermal relaxation. The old analytic sin()-river remains diagnostic only; it no longer
    // controls the actual terrain elevation.
    const GlobalGeomorphSample geomorph = sampleGlobalGeomorph(
        definition.seed, definition.radius, definition.maxElevation, d);
    elevation = geomorph.elevationMeters;
    const double geomorphLandness = smooth01(-80.0, 220.0, geomorph.elevationMeters);

    // The global 512x256 process bake owns where mountain belts and drainage basins live,
    // but on an Earth-radius sphere one bake texel spans tens of kilometres.  Reconstruct
    // band-limited range structure *inside that authority mask* instead of bilinearly
    // stretching each bake texel into a smooth ramp.  These wavelengths form range mass,
    // sub-ranges and valley shoulders; walking-scale noise remains a separate layer below.
    const double rangeRidgeA = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xD6E8FEB86659FD93ULL, w, 34.0, 5));
    const double rangeRidgeB = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xA5A3564E27F8862FULL, w, 82.0, 4));
    const double rangeRidgeC = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0x9E3779B185EBCA87ULL, w, 210.0, 3));
    const double rangeMask = smooth01(0.10, 0.72, geomorph.mountain) * geomorphLandness;
    const double rangeMass = rangeMask * (0.32 + 0.68 * smooth01(0.30, 0.82, rangeRidgeA));
    const double rangeShoulders = rangeMask * smooth01(0.36, 0.86, rangeRidgeB);
    const double rangeFaces = rangeMask * smooth01(0.42, 0.90, rangeRidgeC);
    elevation += maxLand * (0.075 * rangeMask + 0.145 * rangeMass
        + 0.085 * rangeShoulders + 0.040 * rangeFaces);

    // Hydrology remains the placement authority for valleys.  A narrow deterministic
    // sub-channel only sharpens the coarse baked river corridor; it cannot create a river
    // where the discharge bake has none.
    const double channelRefineNoise = 1.0 - std::abs(fbmSurface(
        definition.seed ^ 0xC2B2AE3D27D4EB4FULL, w, 260.0, 3));
    const double channelCore = geomorph.river
        * smooth01(0.58, 0.91, channelRefineNoise) * geomorphLandness;
    elevation -= maxLand * (0.030 * geomorph.incision + 0.045 * channelCore);

    // Give hydrologically low coastal margins a readable land/sea break without changing
    // the global coastline authority.  Rugged margins expose a short escarpment, while flat
    // margins remain beaches/floodplains.
    const double globalCoastBand = geomorphLandness
        * (1.0 - smooth01(90.0, 680.0, std::abs(geomorph.elevationMeters)));
    const double globalCoastRugged = globalCoastBand
        * smooth01(0.46, 0.86, rangeRidgeB);
    elevation += maxLand * 0.032 * globalCoastRugged;

    // Walking-scale geometry. Frequencies now span tens of kilometres down to a few
    // hundred metres; the new ~4 m innermost clipmap can actually resolve them.
    const double local = fbmSurface(
        definition.seed ^ 0x2FFD72DBD01ADFB7ULL, w, 720.0, 4);
    const double micro = fbmSurface(
        definition.seed ^ 0xB8E1AFED6A267E96ULL, w, 3900.0, 3);
    const double fine = fbmSurface(
        definition.seed ^ 0xBA7C9045F12C7F99ULL, w, 21000.0, 3);
    const double ultra = fbmSurface(
        definition.seed ^ 0x24A19947B3916CF7ULL, w, 98000.0, 2);
    const double detailDamp = geomorphLandness
        * (1.0 - 0.72 * std::max(wetland, geomorph.floodplain))
        * (1.0 - 0.52 * plateau);
    elevation += maxLand * detailDamp
        * (0.0100 * local + 0.0038 * micro + 0.0062 * fine + 0.0018 * ultra);

    elevation = std::clamp(elevation, -maxOcean, maxLand);

    PlanetTerrainSample sample{};
    sample.elevationMeters = elevation;
    sample.continentalness = geomorph.continentalness;
    sample.plateBoundary = plates.boundary;
    sample.convergence = plates.convergence;
    sample.divergence = plates.divergence;
    sample.oceanRidge = oceanRidge;
    sample.mountain = std::max(mountain, geomorph.mountain);
    sample.plateau = plateau;
    sample.trench = trench;
    sample.volcano = volcano;
    sample.river = geomorph.river;
    sample.hills = hills;
    sample.canyon = std::max(canyon, geomorph.incision);
    sample.dunes = dunes;
    sample.coastalCliff = std::max(coastalCliff, globalCoastRugged);
    sample.wetland = std::max(wetland, geomorph.floodplain);
    sample.glacier = glacier;
    sample.aridity = aridity;
    sample.moisture = moisture;
    sample.surfaceDetail = std::clamp(
        0.42 * (0.5 + 0.5 * local)
            + 0.28 * (0.5 + 0.5 * micro)
            + 0.20 * (0.5 + 0.5 * fine)
            + 0.10 * (0.5 + 0.5 * ultra),
        0.0, 1.0);
    sample.oceanDepthMeters = std::max(
        0.0, definition.seaLevelElevationMeters - elevation);
    return sample;
}

double planetHeight(const PlanetDefinition& definition, const glm::dvec3& direction) {
    return samplePlanetTerrain(definition, direction).elevationMeters;
}

double planetSurfaceRadius(const PlanetDefinition& definition, const glm::dvec3& direction) {
    return definition.radius + planetHeight(definition, direction);
}

glm::vec3 planetTerrainColor(
    const PlanetDefinition& definition,
    const PlanetTerrainSample& sample) noexcept {
    int surfaceClass = 3; // soil
    if (sample.submerged(definition)) {
        surfaceClass = sample.oceanDepthMeters < 260.0 ? 6 : 7; // shelf sand / seabed rock
    } else if (sample.glacier > 0.38 || sample.elevationMeters > 3900.0) {
        surfaceClass = 5; // snow/ice
    } else if (sample.wetland > 0.34) {
        surfaceClass = 4; // wet mud
    } else if (sample.dunes > 0.36 || sample.aridity > 0.72) {
        surfaceClass = 2; // sand
    } else if (sample.mountain > 0.24 || sample.canyon > 0.20
        || sample.coastalCliff > 0.30 || sample.elevationMeters > 2500.0) {
        surfaceClass = 1; // exposed rock
    } else if (sample.moisture > 0.34 && sample.aridity < 0.66) {
        surfaceClass = 0; // grassland
    }

    switch (surfaceClass) {
    case 0: return {0.105F, 0.330F, 0.070F}; // grass
    case 1: return {0.315F, 0.300F, 0.275F}; // rock
    case 2: return {0.735F, 0.565F, 0.300F}; // dry sand
    case 4: return {0.175F, 0.155F, 0.095F}; // mud
    case 5: return {0.875F, 0.905F, 0.925F}; // snow/ice
    case 6: return {0.790F, 0.690F, 0.455F}; // beach/shelf sand
    case 7: return {0.205F, 0.220F, 0.215F}; // seabed rock
    default: return {0.345F, 0.205F, 0.100F}; // soil
    }
}

glm::vec4 planetTerrainMaterial(
    const PlanetDefinition& definition,
    const PlanetTerrainSample& sample) noexcept {
    int surfaceClass = 3;
    if (sample.submerged(definition)) {
        surfaceClass = sample.oceanDepthMeters < 260.0 ? 6 : 7;
    } else if (sample.glacier > 0.38 || sample.elevationMeters > 3900.0) {
        surfaceClass = 5;
    } else if (sample.wetland > 0.34) {
        surfaceClass = 4;
    } else if (sample.dunes > 0.36 || sample.aridity > 0.72) {
        surfaceClass = 2;
    } else if (sample.mountain > 0.24 || sample.canyon > 0.20
        || sample.coastalCliff > 0.30 || sample.elevationMeters > 2500.0) {
        surfaceClass = 1;
    } else if (sample.moisture > 0.34 && sample.aridity < 0.66) {
        surfaceClass = 0;
    }

    float roughness = 0.90F;
    if (surfaceClass == 1 || surfaceClass == 7) roughness = 0.82F;
    else if (surfaceClass == 2 || surfaceClass == 6) roughness = 0.92F;
    else if (surfaceClass == 4) roughness = 0.96F;
    else if (surfaceClass == 5) roughness = 0.76F;

    // x is filled by mesh construction with true radial slope; z remains transmission=0.
    // w is a categorical material tag: -10 grass, -11 rock ... -17 seabed.
    return {0.0F, roughness, 0.0F, -10.0F - static_cast<float>(surfaceClass)};
}

glm::dvec3 planetSurfaceNormal(
    const PlanetDefinition& definition,
    const glm::dvec3& directionInput) {
    const glm::dvec3 d = safeNormalize(directionInput);
    const glm::dvec3 east = tangentAxis(d);
    const glm::dvec3 north = safeNormalize(glm::cross(d, east), {0.0, 0.0, 1.0});
    const double angularStep = std::clamp(
        2.0 / std::max(1.0, definition.radius),
        1.0e-7,
        2.0e-3);
    const glm::dvec3 dEast = safeNormalize(d + east * angularStep, d);
    const glm::dvec3 dNorth = safeNormalize(d + north * angularStep, d);
    const glm::dvec3 p0 = d * planetSurfaceRadius(definition, d);
    const glm::dvec3 pEast = dEast * planetSurfaceRadius(definition, dEast);
    const glm::dvec3 pNorth = dNorth * planetSurfaceRadius(definition, dNorth);
    glm::dvec3 normal = safeNormalize(glm::cross(pEast - p0, pNorth - p0), d);
    if (glm::dot(normal, d) < 0.0) normal = -normal;
    return normal;
}

PlanetMesh buildPlanetSurface(
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

PlanetMesh buildPlanetSurfacePatch(
    const PlanetDefinition& definition,
    const glm::dvec3& centerDirectionInput,
    double halfExtentMeters,
    std::uint32_t resolution) {
    if (resolution < 2U)
        throw std::invalid_argument("planet patch resolution must be >= 2");
    halfExtentMeters = std::max(10.0, halfExtentMeters);
    const glm::dvec3 up = safeNormalize(centerDirectionInput);
    const glm::dvec3 east = tangentAxis(up);
    const glm::dvec3 north = safeNormalize(glm::cross(up, east), {0.0, 0.0, 1.0});
    const std::uint32_t stride = resolution + 1U;
    PlanetMesh mesh{};
    for (std::uint32_t y = 0; y <= resolution; ++y) {
        const double fy = static_cast<double>(y) / static_cast<double>(resolution);
        const double northMeters = -halfExtentMeters + 2.0 * halfExtentMeters * fy;
        for (std::uint32_t x = 0; x <= resolution; ++x) {
            const double fx = static_cast<double>(x) / static_cast<double>(resolution);
            const double eastMeters = -halfExtentMeters + 2.0 * halfExtentMeters * fx;
            const glm::dvec3 direction = safeNormalize(
                up + east * (eastMeters / definition.radius)
                    + north * (northMeters / definition.radius),
                up);
            const PlanetTerrainSample terrain = samplePlanetTerrain(definition, direction);
            PlanetVertex vertex{};
            vertex.position = glm::vec3(direction * (definition.radius + terrain.elevationMeters));
            const glm::dvec3 surfaceNormal = planetSurfaceNormal(definition, direction);
            vertex.normal = glm::vec3(surfaceNormal);
            vertex.color = planetTerrainColor(definition, terrain);
            vertex.material = planetTerrainMaterial(definition, terrain);
            vertex.material.x = static_cast<float>(std::clamp(
                1.0 - glm::dot(surfaceNormal, direction), 0.0, 1.0));
            mesh.vertices.push_back(vertex);
        }
    }
    for (std::uint32_t y = 0; y < resolution; ++y) {
        for (std::uint32_t x = 0; x < resolution; ++x) {
            const std::uint32_t i0 = y * stride + x;
            const std::uint32_t i1 = i0 + 1U;
            const std::uint32_t i2 = i0 + stride;
            const std::uint32_t i3 = i2 + 1U;
            mesh.indices.insert(mesh.indices.end(), {i0, i2, i1, i1, i2, i3});
        }
    }
    return mesh;
}

PlanetMesh buildOceanSurfacePatch(
    const PlanetDefinition& definition,
    const glm::dvec3& centerDirectionInput,
    double halfExtentMeters,
    std::uint32_t resolution,
    double radialInsetMeters) {
    if (resolution < 2U)
        throw std::invalid_argument("ocean patch resolution must be >= 2");
    halfExtentMeters = std::max(10.0, halfExtentMeters);
    const glm::dvec3 up = safeNormalize(centerDirectionInput);
    const glm::dvec3 east = tangentAxis(up);
    const glm::dvec3 north = safeNormalize(glm::cross(up, east), {0.0, 0.0, 1.0});
    const std::uint32_t stride = resolution + 1U;
    const double radius = std::max(
        1.0,
        definition.radius + definition.seaLevelElevationMeters
            - std::max(0.0, radialInsetMeters));
    PlanetMesh mesh{};
    for (std::uint32_t y = 0; y <= resolution; ++y) {
        const double fy = static_cast<double>(y) / static_cast<double>(resolution);
        const double northMeters = -halfExtentMeters + 2.0 * halfExtentMeters * fy;
        for (std::uint32_t x = 0; x <= resolution; ++x) {
            const double fx = static_cast<double>(x) / static_cast<double>(resolution);
            const double eastMeters = -halfExtentMeters + 2.0 * halfExtentMeters * fx;
            const glm::dvec3 direction = safeNormalize(
                up + east * (eastMeters / definition.radius)
                    + north * (northMeters / definition.radius),
                up);
            PlanetVertex vertex{};
            vertex.position = glm::vec3(direction * radius);
            vertex.normal = glm::vec3(direction);
            vertex.color = {0.020F, 0.205F, 0.315F};
            vertex.material = {-1.0F, 0.055F, 0.72F, 0.0F};
            mesh.vertices.push_back(vertex);
        }
    }
    for (std::uint32_t y = 0; y < resolution; ++y) {
        for (std::uint32_t x = 0; x < resolution; ++x) {
            const std::uint32_t i0 = y * stride + x;
            const std::uint32_t i1 = i0 + 1U;
            const std::uint32_t i2 = i0 + stride;
            const std::uint32_t i3 = i2 + 1U;
            mesh.indices.insert(mesh.indices.end(), {i0, i2, i1, i1, i2, i3});
        }
    }
    return mesh;
}

void appendOceanSurfaceProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double seaSurfaceRadius,
    std::uint32_t subdivisionsPerFace) {
    if (subdivisionsPerFace < 2U)
        throw std::invalid_argument("ocean proxy subdivisions must be >= 2");
    for (std::uint32_t face = 0; face < 6U; ++face) {
        appendOceanFace(mesh, center, seaSurfaceRadius, face, subdivisionsPerFace);
    }
}

void appendCelestialProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double radius,
    std::uint32_t subdivisionsPerFace,
    const glm::vec3& color) {
    appendCelestialBodyProxy(
        mesh,
        center,
        glm::dquat{1.0, 0.0, 0.0, 0.0},
        radius,
        subdivisionsPerFace,
        color);
}

void appendCelestialBodyProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    const glm::dquat& orientation,
    double radius,
    std::uint32_t subdivisionsPerFace,
    const glm::vec3& baseColor) {
    if (subdivisionsPerFace < 2U)
        throw std::invalid_argument("proxy subdivisions must be >= 2");
    const glm::dquat normalizedOrientation = glm::normalize(orientation);
    for (std::uint32_t face = 0; face < 6U; ++face) {
        appendFace(
            mesh,
            nullptr,
            center,
            &normalizedOrientation,
            radius,
            face,
            subdivisionsPerFace,
            &baseColor);
    }
}

void appendAtmosphereProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double outerRadius,
    std::uint32_t subdivisionsPerFace,
    const glm::vec3& scatteringColor,
    float opticalStrength) {
    if (subdivisionsPerFace < 2U)
        throw std::invalid_argument("atmosphere subdivisions must be >= 2");
    const glm::vec3 tint = glm::clamp(
        scatteringColor,
        glm::vec3{0.01F},
        glm::vec3{1.0F});
    const float strength = std::clamp(opticalStrength, 0.02F, 1.0F);
    const glm::vec3 encoded = -(tint * strength);
    const glm::dquat identity{1.0, 0.0, 0.0, 0.0};
    const std::size_t firstVertex = mesh.vertices.size();
    for (std::uint32_t face = 0; face < 6U; ++face) {
        appendFace(
            mesh,
            nullptr,
            center,
            &identity,
            outerRadius,
            face,
            subdivisionsPerFace,
            &encoded);
    }
    for (std::size_t i = firstVertex; i < mesh.vertices.size(); ++i) {
        mesh.vertices[i].material = {0.0F, 1.0F, 1.0F, 0.0F};
    }
}

} // namespace vf
