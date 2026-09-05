#include "vf/world/ProceduralEcology.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;
constexpr double kTau = 2.0 * kPi;

constexpr float kTerrainTag = -1.0F;
constexpr float kFoliageTag = -2.0F;
constexpr float kBarkTag = -3.0F;
constexpr float kRockTag = -4.0F;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-18) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] std::uint64_t mixBits(std::uint64_t x) noexcept {
    x ^= x >> 30U;
    x *= 0xBF58476D1CE4E5B9ULL;
    x ^= x >> 27U;
    x *= 0x94D049BB133111EBULL;
    x ^= x >> 31U;
    return x;
}

[[nodiscard]] std::uint64_t cellBits(
    std::uint64_t seed,
    std::int64_t x,
    std::int64_t z,
    std::uint64_t channel) noexcept {
    std::uint64_t h = seed ^ (channel + 1ULL) * 0x9E3779B97F4A7C15ULL;
    h ^= static_cast<std::uint64_t>(x) * 0xD6E8FEB86659FD93ULL;
    h ^= static_cast<std::uint64_t>(z) * 0xA5A3564E27F8862FULL;
    return mixBits(h);
}

[[nodiscard]] double random01(
    std::uint64_t seed,
    std::int64_t x,
    std::int64_t z,
    std::uint64_t channel) noexcept {
    return static_cast<double>(cellBits(seed, x, z, channel) & 0xFFFFFFULL)
        / static_cast<double>(0xFFFFFFULL);
}

[[nodiscard]] double randomSigned(
    std::uint64_t seed,
    std::int64_t x,
    std::int64_t z,
    std::uint64_t channel) noexcept {
    return random01(seed, x, z, channel) * 2.0 - 1.0;
}

[[nodiscard]] glm::dvec3 toRenderPoint(
    const SurfaceRenderFrame& frame,
    const glm::dvec3& planetPoint) noexcept {
    const glm::dvec3 delta = planetPoint - frame.originPlanet;
    return {
        glm::dot(delta, frame.tangentX),
        glm::dot(delta, frame.up),
        glm::dot(delta, frame.tangentZ),
    };
}

[[nodiscard]] glm::dvec3 toRenderVector(
    const SurfaceRenderFrame& frame,
    const glm::dvec3& planetVector) noexcept {
    return {
        glm::dot(planetVector, frame.tangentX),
        glm::dot(planetVector, frame.up),
        glm::dot(planetVector, frame.tangentZ),
    };
}

[[nodiscard]] glm::dvec3 planetDirectionFromRenderXZ(
    const SurfaceRenderFrame& frame,
    double x,
    double z) noexcept {
    // The frame origin lies on the actual spherical surface. Adding tangent offsets and normalizing
    // maps the stable render-grid cell back onto the planet without introducing a longitude seam.
    return safeNormalize(
        frame.originPlanet + frame.tangentX * x + frame.tangentZ * z,
        frame.up);
}

[[nodiscard]] glm::vec3 mixColor(
    const glm::vec3& a,
    const glm::vec3& b,
    double t) noexcept {
    return glm::mix(a, b, static_cast<float>(std::clamp(t, 0.0, 1.0)));
}

void appendFacetedFrustum(
    PlanetMesh& mesh,
    const glm::dvec3& a,
    const glm::dvec3& b,
    double radiusA,
    double radiusB,
    unsigned sides,
    const glm::vec3& color,
    const glm::vec4& material,
    double phase) {
    const glm::dvec3 axis = safeNormalize(b - a, {0.0, 1.0, 0.0});
    const glm::dvec3 helper = std::abs(axis.y) < 0.82
        ? glm::dvec3{0.0, 1.0, 0.0}
        : glm::dvec3{1.0, 0.0, 0.0};
    const glm::dvec3 u = safeNormalize(glm::cross(axis, helper), {1.0, 0.0, 0.0});
    const glm::dvec3 v = safeNormalize(glm::cross(axis, u), {0.0, 0.0, 1.0});

    for (unsigned side = 0; side < sides; ++side) {
        const double a0 = phase + kTau * static_cast<double>(side) / static_cast<double>(sides);
        const double a1 = phase + kTau * static_cast<double>(side + 1U) / static_cast<double>(sides);
        const glm::dvec3 radial0 = u * std::cos(a0) + v * std::sin(a0);
        const glm::dvec3 radial1 = u * std::cos(a1) + v * std::sin(a1);
        const glm::dvec3 p0 = a + radial0 * radiusA;
        const glm::dvec3 p1 = a + radial1 * radiusA;
        const glm::dvec3 p2 = b + radial1 * radiusB;
        const glm::dvec3 p3 = b + radial0 * radiusB;
        const glm::dvec3 normal = safeNormalize(glm::cross(p1 - p0, p3 - p0), radial0 + radial1);
        const std::uint32_t base = static_cast<std::uint32_t>(mesh.vertices.size());
        const glm::vec3 n = glm::vec3(normal);
        mesh.vertices.push_back({glm::vec3(p0), n, color, material});
        mesh.vertices.push_back({glm::vec3(p1), n, color, material});
        mesh.vertices.push_back({glm::vec3(p2), n, color, material});
        mesh.vertices.push_back({glm::vec3(p3), n, color, material});
        mesh.indices.insert(mesh.indices.end(), {
            base, base + 1U, base + 2U,
            base, base + 2U, base + 3U,
        });
    }
}

constexpr std::array<glm::dvec3, 12> kIcoBase{{
    {-1.0,  1.618033988749895, 0.0}, { 1.0,  1.618033988749895, 0.0},
    {-1.0, -1.618033988749895, 0.0}, { 1.0, -1.618033988749895, 0.0},
    {0.0, -1.0,  1.618033988749895}, {0.0, 1.0,  1.618033988749895},
    {0.0, -1.0, -1.618033988749895}, {0.0, 1.0, -1.618033988749895},
    { 1.618033988749895, 0.0, -1.0}, { 1.618033988749895, 0.0, 1.0},
    {-1.618033988749895, 0.0, -1.0}, {-1.618033988749895, 0.0, 1.0},
}};

constexpr std::array<std::array<unsigned, 3>, 20> kIcoFaces{{
    {{0, 11, 5}}, {{0, 5, 1}}, {{0, 1, 7}}, {{0, 7, 10}}, {{0, 10, 11}},
    {{1, 5, 9}}, {{5, 11, 4}}, {{11, 10, 2}}, {{10, 7, 6}}, {{7, 1, 8}},
    {{3, 9, 4}}, {{3, 4, 2}}, {{3, 2, 6}}, {{3, 6, 8}}, {{3, 8, 9}},
    {{4, 9, 5}}, {{2, 4, 11}}, {{6, 2, 10}}, {{8, 6, 7}}, {{9, 8, 1}},
}};

void appendCanopyLobe(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    const glm::dvec3& axisX,
    const glm::dvec3& axisY,
    const glm::dvec3& axisZ,
    const glm::dvec3& scale,
    const glm::dvec3& canopyCenter,
    const glm::dvec3& canopyExtent,
    std::uint64_t seed,
    std::int64_t cellX,
    std::int64_t cellZ,
    unsigned lobe) {
    const std::uint32_t base = static_cast<std::uint32_t>(mesh.vertices.size());
    const glm::vec4 foliageMaterial{0.0F, 0.88F, 0.0F, kFoliageTag};

    for (unsigned i = 0; i < kIcoBase.size(); ++i) {
        const glm::dvec3 unit = safeNormalize(kIcoBase[i]);
        const double irregularity = 0.90
            + 0.18 * random01(seed, cellX, cellZ, 700U + lobe * 31U + i);
        const glm::dvec3 local{
            unit.x * scale.x * irregularity,
            unit.y * scale.y * irregularity,
            unit.z * scale.z * irregularity,
        };
        const glm::dvec3 p = center
            + axisX * local.x + axisY * local.y + axisZ * local.z;

        const glm::dvec3 canopyOffset = p - canopyCenter;
        glm::dvec3 proxyNormal =
            axisX * (glm::dot(canopyOffset, axisX) / std::max(0.04, canopyExtent.x * canopyExtent.x))
            + axisY * (glm::dot(canopyOffset, axisY) / std::max(0.04, canopyExtent.y * canopyExtent.y))
            + axisZ * (glm::dot(canopyOffset, axisZ) / std::max(0.04, canopyExtent.z * canopyExtent.z));
        proxyNormal = safeNormalize(proxyNormal, axisY);

        glm::dvec3 lobeNormal =
            axisX * (local.x / std::max(0.04, scale.x * scale.x))
            + axisY * (local.y / std::max(0.04, scale.y * scale.y))
            + axisZ * (local.z / std::max(0.04, scale.z * scale.z));
        lobeNormal = safeNormalize(lobeNormal, proxyNormal);
        const glm::dvec3 transferredNormal = safeNormalize(proxyNormal * 0.76 + lobeNormal * 0.24, proxyNormal);

        const double top = std::clamp(0.5 + 0.5 * glm::dot(transferredNormal, axisY), 0.0, 1.0);
        const double hue = random01(seed, cellX, cellZ, 900U + lobe * 17U + i);
        glm::vec3 color = mixColor({0.115F, 0.285F, 0.085F}, {0.285F, 0.510F, 0.125F}, 0.28 + 0.62 * top);
        color = mixColor(color, {0.355F, 0.545F, 0.135F}, std::max(0.0, hue - 0.72) * 0.50);
        mesh.vertices.push_back({glm::vec3(p), glm::vec3(transferredNormal), color, foliageMaterial});
    }

    for (const auto& face : kIcoFaces) {
        mesh.indices.insert(mesh.indices.end(), {
            base + face[0], base + face[1], base + face[2],
        });
    }
}

void appendTree(
    PlanetMesh& mesh,
    const glm::dvec3& base,
    const glm::dvec3& up,
    const glm::dvec3& east,
    const glm::dvec3& north,
    std::uint64_t seed,
    std::int64_t cellX,
    std::int64_t cellZ) {
    const double maturity = 0.84 + 0.34 * random01(seed, cellX, cellZ, 30U);
    const double trunkHeight = (8.5 + 4.5 * random01(seed, cellX, cellZ, 31U)) * maturity;
    const double trunkRadius = (0.40 + 0.18 * random01(seed, cellX, cellZ, 32U)) * std::sqrt(maturity);
    const double phase = kTau * random01(seed, cellX, cellZ, 33U);
    const glm::vec4 barkMaterial{0.0F, 0.93F, 0.0F, kBarkTag};

    std::array<glm::dvec3, 5> trunkCenters{};
    for (unsigned i = 0; i < trunkCenters.size(); ++i) {
        const double t = static_cast<double>(i) / static_cast<double>(trunkCenters.size() - 1U);
        const double bend = (0.12 + 0.18 * t) * std::sin(phase + t * 2.2);
        const double side = (0.08 + 0.12 * t) * std::cos(phase * 0.73 + t * 2.7);
        trunkCenters[i] = base + up * (trunkHeight * t) + east * bend + north * side;
    }

    for (unsigned i = 0; i + 1U < trunkCenters.size(); ++i) {
        const double t0 = static_cast<double>(i) / static_cast<double>(trunkCenters.size() - 1U);
        const double t1 = static_cast<double>(i + 1U) / static_cast<double>(trunkCenters.size() - 1U);
        const double r0 = trunkRadius * (1.0 - 0.70 * t0);
        const double r1 = trunkRadius * (1.0 - 0.70 * t1);
        const glm::vec3 bark = mixColor({0.245F, 0.150F, 0.085F}, {0.365F, 0.230F, 0.120F}, 0.30 + 0.45 * t0);
        appendFacetedFrustum(mesh, trunkCenters[i], trunkCenters[i + 1U], r0, r1, 7U, bark, barkMaterial, phase * 0.13);
    }

    std::array<glm::dvec3, 3> branchTips{};
    for (unsigned branch = 0; branch < branchTips.size(); ++branch) {
        const double attachT = 0.50 + 0.12 * static_cast<double>(branch);
        const glm::dvec3 attach = base + up * (trunkHeight * attachT);
        const double angle = phase + static_cast<double>(branch) * 2.18
            + 0.22 * randomSigned(seed, cellX, cellZ, 80U + branch);
        const glm::dvec3 horizontal = east * std::cos(angle) + north * std::sin(angle);
        const double length = trunkHeight * (0.24 + 0.055 * static_cast<double>(2U - branch))
            * (0.88 + 0.20 * random01(seed, cellX, cellZ, 90U + branch));
        const glm::dvec3 tip = attach + horizontal * length + up * length * (0.42 + 0.10 * branch);
        branchTips[branch] = tip;
        appendFacetedFrustum(
            mesh,
            attach,
            tip,
            trunkRadius * (0.34 - 0.035 * branch),
            trunkRadius * 0.10,
            5U,
            {0.315F, 0.190F, 0.095F},
            barkMaterial,
            phase * 0.21 + branch * 0.31);
    }

    const double crownRadius = trunkHeight * (0.245 + 0.025 * random01(seed, cellX, cellZ, 130U));
    std::array<glm::dvec3, 6> centers{{
        branchTips[0] + up * crownRadius * 0.20,
        branchTips[1] + up * crownRadius * 0.18,
        branchTips[2] + up * crownRadius * 0.22,
        trunkCenters[3] + east * crownRadius * 0.25 + up * crownRadius * 0.54,
        trunkCenters[4] - east * crownRadius * 0.28 + north * crownRadius * 0.10 + up * crownRadius * 0.12,
        trunkCenters[4] + east * crownRadius * 0.22 - north * crownRadius * 0.18 + up * crownRadius * 0.34,
    }};
    std::array<glm::dvec3, 6> scales{};
    glm::dvec3 canopyCenter{0.0};
    for (unsigned i = 0; i < centers.size(); ++i) {
        centers[i] += east * (randomSigned(seed, cellX, cellZ, 150U + i * 3U) * crownRadius * 0.10)
            + north * (randomSigned(seed, cellX, cellZ, 151U + i * 3U) * crownRadius * 0.10)
            + up * (randomSigned(seed, cellX, cellZ, 152U + i * 3U) * crownRadius * 0.08);
        scales[i] = {
            crownRadius * (0.82 + 0.20 * random01(seed, cellX, cellZ, 200U + i * 3U)),
            crownRadius * (0.68 + 0.20 * random01(seed, cellX, cellZ, 201U + i * 3U)),
            crownRadius * (0.78 + 0.20 * random01(seed, cellX, cellZ, 202U + i * 3U)),
        };
        canopyCenter += centers[i];
    }
    canopyCenter /= static_cast<double>(centers.size());

    glm::dvec3 canopyExtent{crownRadius * 1.6, crownRadius * 1.45, crownRadius * 1.6};
    for (const glm::dvec3& center : centers) {
        const glm::dvec3 offset = center - canopyCenter;
        canopyExtent.x = std::max(canopyExtent.x, std::abs(glm::dot(offset, east)) + crownRadius);
        canopyExtent.y = std::max(canopyExtent.y, std::abs(glm::dot(offset, up)) + crownRadius * 0.82);
        canopyExtent.z = std::max(canopyExtent.z, std::abs(glm::dot(offset, north)) + crownRadius);
    }

    for (unsigned i = 0; i < centers.size(); ++i) {
        appendCanopyLobe(mesh, centers[i], east, up, north, scales[i], canopyCenter, canopyExtent, seed, cellX, cellZ, i);
    }
}

void appendRock(
    PlanetMesh& mesh,
    const glm::dvec3& base,
    const glm::dvec3& up,
    const glm::dvec3& east,
    const glm::dvec3& north,
    std::uint64_t seed,
    std::int64_t cellX,
    std::int64_t cellZ) {
    const double scale = 0.65 + 2.10 * random01(seed, cellX, cellZ, 330U);
    const glm::dvec3 radii{
        scale * (0.80 + 0.55 * random01(seed, cellX, cellZ, 331U)),
        scale * (0.48 + 0.42 * random01(seed, cellX, cellZ, 332U)),
        scale * (0.72 + 0.60 * random01(seed, cellX, cellZ, 333U)),
    };
    const double yaw = kTau * random01(seed, cellX, cellZ, 334U);
    const glm::dvec3 rx = east * std::cos(yaw) + north * std::sin(yaw);
    const glm::dvec3 rz = -east * std::sin(yaw) + north * std::cos(yaw);
    const glm::dvec3 center = base + up * radii.y * 0.34;
    const glm::vec4 material{0.0F, 0.84F, 0.0F, kRockTag};
    const glm::vec3 rockBase = mixColor(
        {0.255F, 0.270F, 0.245F},
        {0.430F, 0.390F, 0.315F},
        random01(seed, cellX, cellZ, 335U));

    std::array<glm::dvec3, 12> points{};
    for (unsigned i = 0; i < points.size(); ++i) {
        const glm::dvec3 unit = safeNormalize(kIcoBase[i]);
        const double irregularity = 0.78 + 0.32 * random01(seed, cellX, cellZ, 360U + i);
        points[i] = center
            + rx * (unit.x * radii.x * irregularity)
            + up * (unit.y * radii.y * irregularity)
            + rz * (unit.z * radii.z * irregularity);
    }

    for (unsigned f = 0; f < kIcoFaces.size(); ++f) {
        const auto face = kIcoFaces[f];
        const glm::dvec3 p0 = points[face[0]];
        const glm::dvec3 p1 = points[face[1]];
        const glm::dvec3 p2 = points[face[2]];
        glm::dvec3 normal = safeNormalize(glm::cross(p1 - p0, p2 - p0), up);
        if (glm::dot(normal, (p0 + p1 + p2) / 3.0 - center) < 0.0) normal = -normal;
        const float faceValue = static_cast<float>(0.84 + 0.20 * random01(seed, cellX, cellZ, 420U + f));
        const glm::vec3 color = glm::clamp(rockBase * faceValue, glm::vec3{0.0F}, glm::vec3{1.0F});
        const std::uint32_t baseIndex = static_cast<std::uint32_t>(mesh.vertices.size());
        mesh.vertices.push_back({glm::vec3(p0), glm::vec3(normal), color, material});
        mesh.vertices.push_back({glm::vec3(p1), glm::vec3(normal), color, material});
        mesh.vertices.push_back({glm::vec3(p2), glm::vec3(normal), color, material});
        mesh.indices.insert(mesh.indices.end(), {baseIndex, baseIndex + 1U, baseIndex + 2U});
    }
}

void appendGrassPlane(
    PlanetMesh& mesh,
    const glm::dvec3& base,
    const glm::dvec3& up,
    const glm::dvec3& side,
    double width,
    double height,
    const glm::vec3& color) {
    const glm::dvec3 p0 = base - side * width * 0.50;
    const glm::dvec3 p1 = base + side * width * 0.50;
    const glm::dvec3 p2 = base + side * width * 0.30 + up * height;
    const glm::dvec3 p3 = base - side * width * 0.20 + up * height * 0.94;
    glm::dvec3 normal = safeNormalize(glm::cross(p1 - p0, p3 - p0), up);
    const glm::vec4 material{0.0F, 0.94F, 0.0F, kFoliageTag};
    const std::uint32_t start = static_cast<std::uint32_t>(mesh.vertices.size());
    mesh.vertices.push_back({glm::vec3(p0), glm::vec3(normal), color, material});
    mesh.vertices.push_back({glm::vec3(p1), glm::vec3(normal), color, material});
    mesh.vertices.push_back({glm::vec3(p2), glm::vec3(normal), color, material});
    mesh.vertices.push_back({glm::vec3(p3), glm::vec3(normal), color, material});
    mesh.indices.insert(mesh.indices.end(), {
        start, start + 1U, start + 2U,
        start, start + 2U, start + 3U,
        start + 2U, start + 1U, start,
        start + 3U, start + 2U, start,
    });
}

void appendGrassClump(
    PlanetMesh& mesh,
    const glm::dvec3& base,
    const glm::dvec3& up,
    const glm::dvec3& east,
    const glm::dvec3& north,
    std::uint64_t seed,
    std::int64_t cellX,
    std::int64_t cellZ) {
    const double height = 0.55 + 0.72 * random01(seed, cellX, cellZ, 510U);
    const double width = 0.20 + 0.20 * random01(seed, cellX, cellZ, 511U);
    const double phase = kTau * random01(seed, cellX, cellZ, 512U);
    const glm::vec3 dark{0.145F, 0.315F, 0.085F};
    const glm::vec3 light{0.315F, 0.485F, 0.110F};
    for (unsigned blade = 0; blade < 3U; ++blade) {
        const double angle = phase + static_cast<double>(blade) * kPi / 3.0;
        const glm::dvec3 side = safeNormalize(east * std::cos(angle) + north * std::sin(angle), east);
        const glm::vec3 color = mixColor(dark, light, random01(seed, cellX, cellZ, 520U + blade));
        appendGrassPlane(mesh, base + up * 0.025, up, side, width, height * (0.84 + 0.12 * blade), color);
    }
}

struct SurfaceCandidate {
    glm::dvec3 renderPoint{};
    glm::dvec3 up{};
    glm::dvec3 east{};
    glm::dvec3 north{};
    PlanetTerrainSample terrain{};
    double radialAlignment{};
};

[[nodiscard]] SurfaceCandidate sampleCandidate(
    const PlanetDefinition& planet,
    const SurfaceRenderFrame& frame,
    double x,
    double z) {
    SurfaceCandidate candidate{};
    const glm::dvec3 direction = planetDirectionFromRenderXZ(frame, x, z);
    candidate.terrain = samplePlanetTerrain(planet, direction);
    const glm::dvec3 normalPlanet = planetSurfaceNormal(planet, direction);
    candidate.radialAlignment = glm::dot(normalPlanet, direction);
    candidate.renderPoint = toRenderPoint(
        frame,
        direction * (planet.radius + candidate.terrain.elevationMeters));
    candidate.up = safeNormalize(toRenderVector(frame, normalPlanet));
    candidate.east = safeNormalize(toRenderVector(frame, safeNormalize(glm::cross(glm::dvec3{0.0, 1.0, 0.0}, direction), frame.tangentX)), frame.tangentX);
    if (std::abs(glm::dot(candidate.east, candidate.up)) > 0.96) {
        candidate.east = safeNormalize(glm::cross(frame.tangentZ, candidate.up), frame.tangentX);
    }
    candidate.east = safeNormalize(candidate.east - candidate.up * glm::dot(candidate.east, candidate.up), frame.tangentX);
    candidate.north = safeNormalize(glm::cross(candidate.up, candidate.east), frame.tangentZ);
    return candidate;
}

template <typename Fn>
void forStableCells(
    const SurfaceRenderFrame& frame,
    const glm::dvec3& centerDirection,
    const PlanetDefinition& planet,
    double radius,
    double cellSize,
    std::uint64_t channel,
    Fn&& fn) {
    const glm::dvec3 centerPlanet = centerDirection
        * (planet.radius + samplePlanetTerrain(planet, centerDirection).elevationMeters);
    const glm::dvec3 center = toRenderPoint(frame, centerPlanet);
    const auto centerX = static_cast<std::int64_t>(std::floor(center.x / cellSize));
    const auto centerZ = static_cast<std::int64_t>(std::floor(center.z / cellSize));
    const std::int64_t reach = static_cast<std::int64_t>(std::ceil(radius / cellSize)) + 1;
    const double radiusSquared = radius * radius;

    for (std::int64_t iz = centerZ - reach; iz <= centerZ + reach; ++iz) {
        for (std::int64_t ix = centerX - reach; ix <= centerX + reach; ++ix) {
            const double jitterX = randomSigned(planet.seed, ix, iz, channel + 0U) * 0.34;
            const double jitterZ = randomSigned(planet.seed, ix, iz, channel + 1U) * 0.34;
            const double x = (static_cast<double>(ix) + 0.5 + jitterX) * cellSize;
            const double z = (static_cast<double>(iz) + 0.5 + jitterZ) * cellSize;
            const double dx = x - center.x;
            const double dz = z - center.z;
            if (dx * dx + dz * dz > radiusSquared) continue;
            fn(ix, iz, x, z);
        }
    }
}

} // namespace

PlanetMesh buildProceduralEcology(
    const PlanetDefinition& planet,
    const glm::dvec3& centerDirectionInput,
    const SurfaceRenderFrame& frame,
    const ProceduralEcologySettings& settings) {
    PlanetMesh mesh{};
    const glm::dvec3 centerDirection = safeNormalize(centerDirectionInput, safeNormalize(frame.originPlanet));
    std::uint32_t treeCount = 0U;
    std::uint32_t rockCount = 0U;
    std::uint32_t grassCount = 0U;

    forStableCells(
        frame,
        centerDirection,
        planet,
        settings.treeRadiusMeters,
        settings.treeCellMeters,
        1000U,
        [&](std::int64_t ix, std::int64_t iz, double x, double z) {
            if (treeCount >= settings.maxTrees) return;
            const SurfaceCandidate c = sampleCandidate(planet, frame, x, z);
            const double aboveSea = c.terrain.elevationMeters - planet.seaLevelElevationMeters;
            if (c.terrain.submerged(planet) || aboveSea < 18.0 || aboveSea > 2550.0) return;
            // R5 river exclusion: a hydrology channel is water, not fertile ground under water.
            if (c.terrain.river > 0.16 || c.terrain.wetland > 0.82) return;
            if (c.radialAlignment < 0.935 || c.terrain.mountain > 0.76 || c.terrain.volcano > 0.72) return;
            const double forestSuitability = std::clamp(
                0.27
                + 0.28 * (1.0 - c.terrain.mountain)
                + 0.16 * c.terrain.river
                + 0.08 * (1.0 - std::abs(c.terrain.surfaceDetail)),
                0.12,
                0.68);
            if (random01(planet.seed, ix, iz, 1010U) > forestSuitability) return;
            appendTree(mesh, c.renderPoint, c.up, c.east, c.north, planet.seed, ix, iz);
            ++treeCount;
        });

    forStableCells(
        frame,
        centerDirection,
        planet,
        settings.rockRadiusMeters,
        settings.rockCellMeters,
        2000U,
        [&](std::int64_t ix, std::int64_t iz, double x, double z) {
            if (rockCount >= settings.maxRocks) return;
            const SurfaceCandidate c = sampleCandidate(planet, frame, x, z);
            const double aboveSea = c.terrain.elevationMeters - planet.seaLevelElevationMeters;
            if (c.terrain.submerged(planet) || aboveSea < 8.0) return;
            if (c.radialAlignment < 0.86) return;
            const double rockSuitability = std::clamp(
                0.10 + 0.34 * c.terrain.mountain + 0.18 * c.terrain.plateau
                + 0.22 * c.terrain.volcano + 0.08 * std::abs(c.terrain.surfaceDetail),
                0.08,
                0.62);
            if (random01(planet.seed, ix, iz, 2010U) > rockSuitability) return;
            appendRock(mesh, c.renderPoint, c.up, c.east, c.north, planet.seed, ix, iz);
            ++rockCount;
        });

    forStableCells(
        frame,
        centerDirection,
        planet,
        settings.grassRadiusMeters,
        settings.grassCellMeters,
        3000U,
        [&](std::int64_t ix, std::int64_t iz, double x, double z) {
            if (grassCount >= settings.maxGrassClumps) return;
            const SurfaceCandidate c = sampleCandidate(planet, frame, x, z);
            const double aboveSea = c.terrain.elevationMeters - planet.seaLevelElevationMeters;
            if (c.terrain.submerged(planet) || aboveSea < 7.0 || aboveSea > 2200.0) return;
            if (c.terrain.river > 0.28) return;
            if (c.radialAlignment < 0.955 || c.terrain.mountain > 0.62 || c.terrain.volcano > 0.58) return;
            const double grassSuitability = std::clamp(
                0.30 + 0.22 * (1.0 - c.terrain.mountain) + 0.16 * c.terrain.river,
                0.24,
                0.70);
            if (random01(planet.seed, ix, iz, 3010U) > grassSuitability) return;
            appendGrassClump(mesh, c.renderPoint, c.up, c.east, c.north, planet.seed, ix, iz);
            ++grassCount;
        });

    // Keep terrain tag reserved in this translation unit so marker values remain documented and do
    // not silently drift relative to the shared Slang material dispatch.
    static_assert(kTerrainTag == -1.0F);
    return mesh;
}

} // namespace vf
