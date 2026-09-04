#include "vf/world/detail/PlanetGenerationInternal.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <vector>

#include <glm/geometric.hpp>

namespace vf::detail {

[[nodiscard]] LocalMesh buildLowPolyRock(std::uint64_t seed, double radius) {
    constexpr double phi = 1.6180339887498948482;
    const std::array<glm::dvec3, 12> base{
        glm::dvec3{-1.0, phi, 0.0}, glm::dvec3{1.0, phi, 0.0},
        glm::dvec3{-1.0, -phi, 0.0}, glm::dvec3{1.0, -phi, 0.0},
        glm::dvec3{0.0, -1.0, phi}, glm::dvec3{0.0, 1.0, phi},
        glm::dvec3{0.0, -1.0, -phi}, glm::dvec3{0.0, 1.0, -phi},
        glm::dvec3{phi, 0.0, -1.0}, glm::dvec3{phi, 0.0, 1.0},
        glm::dvec3{-phi, 0.0, -1.0}, glm::dvec3{-phi, 0.0, 1.0},
    };
    constexpr std::array<std::array<unsigned, 3>, 20> faces{{
        {{0, 11, 5}}, {{0, 5, 1}}, {{0, 1, 7}}, {{0, 7, 10}}, {{0, 10, 11}},
        {{1, 5, 9}}, {{5, 11, 4}}, {{11, 10, 2}}, {{10, 7, 6}}, {{7, 1, 8}},
        {{3, 9, 4}}, {{3, 4, 2}}, {{3, 2, 6}}, {{3, 6, 8}}, {{3, 8, 9}},
        {{4, 9, 5}}, {{2, 4, 11}}, {{6, 2, 10}}, {{8, 6, 7}}, {{9, 8, 1}},
    }};

    LocalMesh rock;
    rock.vertices.reserve(base.size());
    rock.indices.reserve(faces.size() * 3U);
    const double sx = radius * (0.88 + random01(seed, 1U) * 0.42);
    const double sy = radius * (0.82 + random01(seed, 2U) * 0.38);
    const double sz = radius * (0.62 + random01(seed, 3U) * 0.44);
    const double variation = random01(seed, 4U);

    for (unsigned i = 0; i < base.size(); ++i) {
        const glm::dvec3 unit = glm::normalize(base[i]);
        const double jitter = 0.84 + random01(seed, 20U + i) * 0.30;
        glm::dvec3 p{unit.x * sx * jitter, unit.y * sy * jitter, unit.z * sz * jitter};
        if (p.z < 0.0) p.z *= 0.64;
        p.z += sz * 0.18;
        rock.vertices.push_back({
            p,
            {kRockMaterialMarker, static_cast<float>(variation), static_cast<float>(p.z / std::max(radius, 0.01))},
        });
    }
    for (const auto& face : faces) appendTriangle(rock, face[0], face[1], face[2]);
    return rock;
}

[[nodiscard]] glm::dvec3 fibonacciDirection(
    std::uint64_t seed,
    std::uint64_t index,
    std::uint64_t count,
    std::uint64_t channel) noexcept {
    const double jitter = randomSigned(seed, channel + index * 2U) * 0.32;
    const double t = (static_cast<double>(index) + 0.5 + jitter) / static_cast<double>(count);
    const double y = std::clamp(1.0 - 2.0 * t, -1.0, 1.0);
    const double radial = std::sqrt(std::max(0.0, 1.0 - y * y));
    const double angle = kGoldenAngle * static_cast<double>(index)
        + seedPhase(seed, channel + 1U)
        + randomSigned(seed, channel + index * 2U + 1U) * 0.18;
    return glm::normalize(glm::dvec3{std::cos(angle) * radial, y, std::sin(angle) * radial});
}

[[nodiscard]] double surfaceSlopeCosine(
    const PlanetDefinition& definition,
    const glm::dvec3& directionInput) {
    const glm::dvec3 direction = glm::normalize(directionInput);
    const SurfaceFrame frame = frameForDirection(direction);
    constexpr double epsilon = 0.0035;
    const glm::dvec3 dEast = glm::normalize(direction + frame.east * epsilon);
    const glm::dvec3 dNorth = glm::normalize(direction + frame.north * epsilon);
    const glm::dvec3 p = direction * planetSurfaceRadius(definition, direction);
    const glm::dvec3 pEast = dEast * planetSurfaceRadius(definition, dEast);
    const glm::dvec3 pNorth = dNorth * planetSurfaceRadius(definition, dNorth);
    glm::dvec3 normal = glm::normalize(glm::cross(pEast - p, pNorth - p));
    if (glm::dot(normal, direction) < 0.0) normal = -normal;
    return std::clamp(glm::dot(normal, direction), -1.0, 1.0);
}

[[nodiscard]] bool separatedFrom(
    const glm::dvec3& direction,
    double clearanceMeters,
    double planetRadius,
    const std::vector<Placement>& accepted) {
    for (const auto& placed : accepted) {
        const double required = std::max(clearanceMeters, placed.clearanceMeters);
        const double cosineThreshold = std::cos(required / std::max(planetRadius, 1.0));
        if (glm::dot(direction, placed.direction) > cosineThreshold) return false;
    }
    return true;
}

[[nodiscard]] std::vector<Placement> scatterTrees(PlanetMesh& mesh, const PlanetDefinition& definition) {
    const std::uint32_t targetCount = static_cast<std::uint32_t>(std::clamp(
        definition.radius * 0.64,
        96.0,
        190.0));
    const std::uint64_t candidateCount = static_cast<std::uint64_t>(targetCount) * 44ULL;
    std::vector<Placement> accepted;
    accepted.reserve(targetCount);

    for (std::uint64_t candidate = 0; candidate < candidateCount && accepted.size() < targetCount; ++candidate) {
        const glm::dvec3 direction = fibonacciDirection(
            definition.seed ^ 0xE7037ED1A0B428DBULL,
            candidate,
            candidateCount,
            10000U);
        const double elevation = planetHeight(definition, direction);
        const double normalizedHeight = definition.maxElevation > 0.0
            ? elevation / definition.maxElevation
            : 0.0;
        if (normalizedHeight < -0.16 || normalizedHeight > 0.40) continue;

        const double moisture = terrainMoisture(definition, direction);
        const double temperature = terrainTemperature(definition, direction, normalizedHeight);
        if (moisture < 0.36 || temperature < 0.38) continue;

        const double slopeCos = surfaceSlopeCosine(definition, direction);
        if (slopeCos < 0.89) continue;

        const double grove = 0.5 + 0.5 * centeredFbm(
            definition.seed ^ 0x8CB92BA72F3D8DD7ULL,
            direction * 5.2,
            3U);
        const double density = std::clamp(
            (moisture - 0.28) * 1.35
                * (temperature - 0.26) * 1.28
                * (0.52 + 0.72 * grove)
                * (1.0 - std::max(0.0, normalizedHeight - 0.15) * 1.6),
            0.0,
            0.93);
        if (random01(definition.seed ^ 0xA24BAED4963EE407ULL, candidate) > density) continue;

        const double sizeClass = random01(definition.seed ^ 0x9FB21C651E98DF25ULL, candidate);
        const double clearance = 7.0 + sizeClass * 4.4;
        if (!separatedFrom(direction, clearance, definition.radius, accepted)) continue;

        accepted.push_back({direction, clearance});
        const std::uint64_t treeSeed = hashChannel(definition.seed ^ 0xD6E8FEB86659FD93ULL, candidate);
        const LocalMesh tree = buildStylizedTree(treeSeed);
        const SurfaceFrame frame = frameForDirection(direction);
        const double surfaceRadius = planetSurfaceRadius(definition, direction);
        const glm::dvec3 origin = direction * (surfaceRadius - 0.045);
        const double yaw = seedPhase(treeSeed, 300U);
        const double leanEast = randomSigned(treeSeed, 301U) * 0.035;
        const double leanNorth = randomSigned(treeSeed, 302U) * 0.035;
        appendLocalMesh(mesh, tree, origin, frame, yaw, leanEast, leanNorth);
        ++mesh.treeCount;
    }
    return accepted;
}

void scatterRocks(
    PlanetMesh& mesh,
    const PlanetDefinition& definition,
    const std::vector<Placement>& treePlacements) {
    const std::uint32_t targetCount = static_cast<std::uint32_t>(std::clamp(
        definition.radius * 1.60,
        220.0,
        520.0));
    const std::uint64_t candidateCount = static_cast<std::uint64_t>(targetCount) * 34ULL;
    std::vector<Placement> accepted;
    accepted.reserve(targetCount);

    for (std::uint64_t candidate = 0; candidate < candidateCount && accepted.size() < targetCount; ++candidate) {
        const glm::dvec3 direction = fibonacciDirection(
            definition.seed ^ 0x589965CC75374CC3ULL,
            candidate,
            candidateCount,
            20000U);
        const double elevation = planetHeight(definition, direction);
        const double normalizedHeight = definition.maxElevation > 0.0
            ? elevation / definition.maxElevation
            : 0.0;
        if (normalizedHeight < -0.20) continue;

        const double slopeCos = surfaceSlopeCosine(definition, direction);
        if (slopeCos < 0.76) continue;
        const double moisture = terrainMoisture(definition, direction);
        const double brokenGround = 0.5 + 0.5 * centeredFbm(
            definition.seed ^ 0xB5AD4ECEDA1CE2A9ULL,
            direction * 9.0,
            3U);
        const double rockiness = std::clamp(
            0.16
                + std::max(0.0, normalizedHeight) * 0.60
                + (1.0 - slopeCos) * 1.30
                + (1.0 - moisture) * 0.20
                + brokenGround * 0.22,
            0.08,
            0.90);
        if (random01(definition.seed ^ 0xC2B2AE3D27D4EB4FULL, candidate) > rockiness) continue;

        const double sizeClass = random01(definition.seed ^ 0x165667B19E3779F9ULL, candidate);
        const double clearance = 2.4 + sizeClass * 2.9;
        if (!separatedFrom(direction, clearance, definition.radius, accepted)) continue;
        bool overlapsTree = false;
        for (const auto& tree : treePlacements) {
            const double required = tree.clearanceMeters * 0.52 + clearance * 0.35;
            const double cosineThreshold = std::cos(required / std::max(definition.radius, 1.0));
            if (glm::dot(direction, tree.direction) > cosineThreshold) {
                overlapsTree = true;
                break;
            }
        }
        if (overlapsTree) continue;

        accepted.push_back({direction, clearance});
        const std::uint64_t rockSeed = hashChannel(definition.seed ^ 0x94D049BB133111EBULL, candidate);
        const double rockRadius = 0.34 + std::pow(sizeClass, 1.7) * 1.15;
        const LocalMesh rock = buildLowPolyRock(rockSeed, rockRadius);
        const SurfaceFrame frame = frameForDirection(direction);
        const double surfaceRadius = planetSurfaceRadius(definition, direction);
        const glm::dvec3 origin = direction * (surfaceRadius - rockRadius * 0.13);
        const double yaw = seedPhase(rockSeed, 400U);
        const double leanEast = randomSigned(rockSeed, 401U) * 0.12;
        const double leanNorth = randomSigned(rockSeed, 402U) * 0.12;
        appendLocalMesh(mesh, rock, origin, frame, yaw, leanEast, leanNorth);
        ++mesh.rockCount;
    }
}

} // namespace vf::detail
