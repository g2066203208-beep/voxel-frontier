#include "vf/world/detail/PlanetGenerationInternal.hpp"

#include <algorithm>
#include <cmath>
#include <vector>

#include <glm/geometric.hpp>

namespace vf::detail {

[[nodiscard]] std::uint64_t splitMix64(std::uint64_t value) noexcept {
    value += 0x9E3779B97F4A7C15ULL;
    value = (value ^ (value >> 30U)) * 0xBF58476D1CE4E5B9ULL;
    value = (value ^ (value >> 27U)) * 0x94D049BB133111EBULL;
    return value ^ (value >> 31U);
}

[[nodiscard]] std::uint64_t hashChannel(std::uint64_t seed, std::uint64_t channel) noexcept {
    return splitMix64(seed ^ splitMix64(channel + 0xD1B54A32D192ED03ULL));
}

[[nodiscard]] double random01(std::uint64_t seed, std::uint64_t channel) noexcept {
    const std::uint64_t bits = hashChannel(seed, channel) >> 11U;
    return static_cast<double>(bits) * (1.0 / 9007199254740992.0);
}

[[nodiscard]] double randomSigned(std::uint64_t seed, std::uint64_t channel) noexcept {
    return random01(seed, channel) * 2.0 - 1.0;
}

[[nodiscard]] double seedPhase(std::uint64_t seed, std::uint64_t channel) noexcept {
    return random01(seed, channel) * kTau;
}

[[nodiscard]] double smoothCurve(double t) noexcept {
    t = std::clamp(t, 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

[[nodiscard]] double lerpDouble(double a, double b, double t) noexcept {
    return a + (b - a) * t;
}

[[nodiscard]] std::uint64_t latticeHash(
    std::uint64_t seed,
    std::int64_t x,
    std::int64_t y,
    std::int64_t z) noexcept {
    std::uint64_t h = seed;
    h ^= splitMix64(static_cast<std::uint64_t>(x) + 0xA24BAED4963EE407ULL);
    h ^= splitMix64(static_cast<std::uint64_t>(y) + 0x9FB21C651E98DF25ULL);
    h ^= splitMix64(static_cast<std::uint64_t>(z) + 0xC13FA9A902A6328FULL);
    return splitMix64(h);
}

[[nodiscard]] double latticeValue(
    std::uint64_t seed,
    std::int64_t x,
    std::int64_t y,
    std::int64_t z) noexcept {
    return static_cast<double>(latticeHash(seed, x, y, z) >> 11U)
        * (1.0 / 9007199254740992.0);
}

[[nodiscard]] double valueNoise3(std::uint64_t seed, const glm::dvec3& p) noexcept {
    const auto x0 = static_cast<std::int64_t>(std::floor(p.x));
    const auto y0 = static_cast<std::int64_t>(std::floor(p.y));
    const auto z0 = static_cast<std::int64_t>(std::floor(p.z));
    const double tx = smoothCurve(p.x - static_cast<double>(x0));
    const double ty = smoothCurve(p.y - static_cast<double>(y0));
    const double tz = smoothCurve(p.z - static_cast<double>(z0));

    const double c000 = latticeValue(seed, x0 + 0, y0 + 0, z0 + 0);
    const double c100 = latticeValue(seed, x0 + 1, y0 + 0, z0 + 0);
    const double c010 = latticeValue(seed, x0 + 0, y0 + 1, z0 + 0);
    const double c110 = latticeValue(seed, x0 + 1, y0 + 1, z0 + 0);
    const double c001 = latticeValue(seed, x0 + 0, y0 + 0, z0 + 1);
    const double c101 = latticeValue(seed, x0 + 1, y0 + 0, z0 + 1);
    const double c011 = latticeValue(seed, x0 + 0, y0 + 1, z0 + 1);
    const double c111 = latticeValue(seed, x0 + 1, y0 + 1, z0 + 1);

    const double x00 = lerpDouble(c000, c100, tx);
    const double x10 = lerpDouble(c010, c110, tx);
    const double x01 = lerpDouble(c001, c101, tx);
    const double x11 = lerpDouble(c011, c111, tx);
    return lerpDouble(lerpDouble(x00, x10, ty), lerpDouble(x01, x11, ty), tz);
}

[[nodiscard]] double fbm3(std::uint64_t seed, glm::dvec3 p, unsigned octaves) noexcept {
    double sum = 0.0;
    double amplitude = 0.5;
    double normalization = 0.0;
    for (unsigned octave = 0; octave < octaves; ++octave) {
        sum += valueNoise3(seed + static_cast<std::uint64_t>(octave) * 0x9E3779B97F4A7C15ULL, p)
            * amplitude;
        normalization += amplitude;
        p = p * 2.03 + glm::dvec3{11.7, -7.3, 5.1};
        amplitude *= 0.5;
    }
    return normalization > 0.0 ? sum / normalization : 0.5;
}

[[nodiscard]] double centeredFbm(std::uint64_t seed, const glm::dvec3& p, unsigned octaves) noexcept {
    return fbm3(seed, p, octaves) * 2.0 - 1.0;
}

[[nodiscard]] glm::dvec3 seededUnitVector(std::uint64_t seed, std::uint64_t channel) noexcept {
    glm::dvec3 v{
        randomSigned(seed, channel + 0U),
        randomSigned(seed, channel + 1U),
        randomSigned(seed, channel + 2U),
    };
    const double lengthSquared = glm::dot(v, v);
    if (lengthSquared <= 1.0e-12) return {0.0, 1.0, 0.0};
    return v / std::sqrt(lengthSquared);
}

[[nodiscard]] double gaussianFalloff(double x, double sigma) noexcept {
    const double safeSigma = std::max(1.0e-6, sigma);
    const double normalized = x / safeSigma;
    return std::exp(-normalized * normalized);
}

[[nodiscard]] LandformProfile semanticLandform(
    const PlanetDefinition& definition,
    const glm::dvec3& directionInput) noexcept {
    const glm::dvec3 d = glm::normalize(directionInput);
    const glm::dvec3 ridgeNormal = seededUnitVector(definition.seed ^ 0x5A17C9E3D4B286F1ULL, 600U);
    const glm::dvec3 valleyNormal = seededUnitVector(definition.seed ^ 0xA55A6A6D9C27F2C5ULL, 620U);
    const glm::dvec3 basinCenter = seededUnitVector(definition.seed ^ 0xB7E151628AED2A6BULL, 640U);

    const double continentNoise = 0.5 + 0.5 * centeredFbm(
        definition.seed ^ 0x6A09E667F3BCC909ULL,
        d * 1.35 + glm::dvec3{1.7, -2.1, 0.9},
        3U);
    const double mountainDistance = std::abs(glm::dot(d, ridgeNormal));
    const double ridgeModulator = 0.62 + 0.38 * valueNoise3(
        definition.seed ^ 0xBB67AE8584CAA73BULL,
        d * 4.2 + glm::dvec3{-1.0, 2.7, 3.8});
    const double mountainBelt = std::clamp(gaussianFalloff(mountainDistance, 0.115) * ridgeModulator, 0.0, 1.0);

    const double valleyDistance = std::abs(glm::dot(d, valleyNormal));
    const double valleyModulator = 0.55 + 0.45 * valueNoise3(
        definition.seed ^ 0x3C6EF372FE94F82BULL,
        d * 3.5 + glm::dvec3{4.4, -3.1, 0.6});
    const double valleyCorridor = std::clamp(gaussianFalloff(valleyDistance, 0.082) * valleyModulator, 0.0, 1.0);

    const double basinDot = std::clamp(glm::dot(d, basinCenter), -1.0, 1.0);
    const double basinAngle = std::acos(basinDot);
    const double basin = gaussianFalloff(basinAngle, 0.34);

    const double plateauNoise = valueNoise3(
        definition.seed ^ 0x510E527FADE682D1ULL,
        d * 2.35 + glm::dvec3{-4.0, 1.2, 2.5});
    const double plateau = smoothCurve((plateauNoise - 0.56) / 0.30);

    const double forestField = 0.5 + 0.5 * centeredFbm(
        definition.seed ^ 0x8CB92BA72F3D8DD7ULL,
        d * 3.9 + glm::dvec3{2.3, 5.1, -1.7},
        2U);
    const double forestCore = smoothCurve((forestField - 0.42) / 0.42);

    const double talusNoise = valueNoise3(
        definition.seed ^ 0x94D049BB133111EBULL,
        d * 7.2 + glm::dvec3{-2.0, 6.2, 1.1});
    const double talusField = std::clamp(
        mountainBelt * (0.45 + 0.55 * talusNoise)
            + valleyCorridor * 0.18,
        0.0,
        1.0);

    return {
        continentNoise,
        mountainBelt,
        valleyCorridor,
        basin,
        plateau,
        forestCore,
        talusField,
    };
}

[[nodiscard]] double terrainMoisture(const PlanetDefinition& definition, const glm::dvec3& directionInput) noexcept {
    const glm::dvec3 d = glm::normalize(directionInput);
    const LandformProfile landform = semanticLandform(definition, d);
    const double broad = centeredFbm(definition.seed ^ 0x2B992DDFA23249D6ULL, d * 3.2, 3U);
    const double pockets = centeredFbm(definition.seed ^ 0x9E3779B185EBCA87ULL, d * 7.6, 2U);
    return std::clamp(
        0.49 + broad * 0.25 + pockets * 0.10
            + landform.valleyCorridor * 0.22
            + landform.basin * 0.18
            - landform.mountainBelt * 0.09,
        0.0,
        1.0);
}

[[nodiscard]] double terrainTemperature(
    const PlanetDefinition& definition,
    const glm::dvec3& directionInput,
    double normalizedHeight) noexcept {
    const glm::dvec3 d = glm::normalize(directionInput);
    const double latitude = std::abs(d.y);
    const double weather = centeredFbm(definition.seed ^ 0xDB4F0B9175AE2165ULL, d * 4.5, 2U);
    return std::clamp(1.02 - latitude * 0.78 - std::max(0.0, normalizedHeight) * 0.46 + weather * 0.08, 0.0, 1.0);
}

[[nodiscard]] glm::vec3 terrainMaterialData(
    const PlanetDefinition& definition,
    const glm::dvec3& direction,
    double normalizedHeight) noexcept {
    const double moisture = terrainMoisture(definition, direction);
    const double temperature = terrainTemperature(definition, direction, normalizedHeight);
    return {
        kTerrainMaterialMarker + static_cast<float>(temperature) * 0.35F,
        static_cast<float>(normalizedHeight),
        static_cast<float>(moisture),
    };
}

[[nodiscard]] glm::vec3 proxyColor(const glm::vec3& baseColor, const glm::dvec3& localDirection) {
    const double bands = 0.5 + 0.5 * std::sin(localDirection.y * 17.0 + localDirection.x * 5.0);
    const double patches = 0.5 + 0.5 * std::sin(localDirection.x * 11.0 - localDirection.z * 13.0);
    const float scale = static_cast<float>(0.68 + 0.20 * bands + 0.12 * patches);
    return glm::clamp(baseColor * scale, glm::vec3{0.0F}, glm::vec3{1.0F});
}

[[nodiscard]] SurfaceFrame frameForDirection(const glm::dvec3& directionInput) {
    SurfaceFrame frame{};
    frame.up = glm::normalize(directionInput);
    const glm::dvec3 reference = std::abs(frame.up.y) < 0.90
        ? glm::dvec3{0.0, 1.0, 0.0}
        : glm::dvec3{1.0, 0.0, 0.0};
    frame.east = glm::normalize(glm::cross(reference, frame.up));
    frame.north = glm::normalize(glm::cross(frame.up, frame.east));
    return frame;
}

[[nodiscard]] glm::dvec3 rotateLocalZ(const glm::dvec3& p, double yaw) noexcept {
    const double c = std::cos(yaw);
    const double s = std::sin(yaw);
    return {p.x * c - p.y * s, p.x * s + p.y * c, p.z};
}

[[nodiscard]] glm::dvec3 transformLocalPoint(
    const glm::dvec3& localInput,
    const glm::dvec3& origin,
    const SurfaceFrame& frame,
    double yaw,
    double leanEast,
    double leanNorth) noexcept {
    const glm::dvec3 local = rotateLocalZ(localInput, yaw);
    return origin
        + frame.east * (local.x + local.z * leanEast)
        + frame.north * (local.y + local.z * leanNorth)
        + frame.up * local.z;
}

[[nodiscard]] glm::dvec3 transformLocalVector(
    const glm::dvec3& localInput,
    const SurfaceFrame& frame,
    double yaw,
    double leanEast,
    double leanNorth) noexcept {
    const glm::dvec3 local = rotateLocalZ(localInput, yaw);
    return frame.east * (local.x + local.z * leanEast)
        + frame.north * (local.y + local.z * leanNorth)
        + frame.up * local.z;
}

[[nodiscard]] std::vector<glm::dvec3> localSmoothNormals(const LocalMesh& local) {
    std::vector<glm::dvec3> normals(local.vertices.size(), glm::dvec3{0.0});
    for (std::size_t i = 0; i + 2U < local.indices.size(); i += 3U) {
        const std::uint32_t ia = local.indices[i + 0U];
        const std::uint32_t ib = local.indices[i + 1U];
        const std::uint32_t ic = local.indices[i + 2U];
        const glm::dvec3 a = local.vertices[ia].position;
        const glm::dvec3 b = local.vertices[ib].position;
        const glm::dvec3 c = local.vertices[ic].position;
        const glm::dvec3 face = glm::cross(b - a, c - a);
        normals[ia] += face;
        normals[ib] += face;
        normals[ic] += face;
    }
    for (auto& normal : normals) {
        const double lengthSquared = glm::dot(normal, normal);
        normal = lengthSquared > 1.0e-16
            ? normal / std::sqrt(lengthSquared)
            : glm::dvec3{0.0, 0.0, 1.0};
    }
    return normals;
}

void appendLocalMesh(
    PlanetMesh& destination,
    const LocalMesh& local,
    const glm::dvec3& origin,
    const SurfaceFrame& frame,
    double yaw,
    double leanEast,
    double leanNorth) {
    if (local.vertices.empty() || local.indices.empty()) return;

    const auto localNormals = localSmoothNormals(local);
    const std::uint32_t base = static_cast<std::uint32_t>(destination.vertices.size());
    destination.vertices.reserve(destination.vertices.size() + local.vertices.size());
    destination.indices.reserve(destination.indices.size() + local.indices.size());

    for (std::size_t i = 0; i < local.vertices.size(); ++i) {
        PlanetVertex vertex{};
        vertex.position = glm::vec3(transformLocalPoint(
            local.vertices[i].position,
            origin,
            frame,
            yaw,
            leanEast,
            leanNorth));
        const double customLengthSquared = glm::dot(
            local.vertices[i].shadingNormal,
            local.vertices[i].shadingNormal);
        const glm::dvec3 sourceNormal = customLengthSquared > 1.0e-16
            ? local.vertices[i].shadingNormal / std::sqrt(customLengthSquared)
            : localNormals[i];
        vertex.normal = glm::vec3(glm::normalize(transformLocalVector(
            sourceNormal,
            frame,
            yaw,
            leanEast,
            leanNorth)));
        vertex.color = local.vertices[i].material;
        destination.vertices.push_back(vertex);
    }

    for (const std::uint32_t index : local.indices) destination.indices.push_back(base + index);
}

void appendTriangle(LocalMesh& mesh, std::uint32_t a, std::uint32_t b, std::uint32_t c) {
    mesh.indices.insert(mesh.indices.end(), {a, b, c});
}

void appendQuadBest(
    LocalMesh& mesh,
    std::uint32_t a,
    std::uint32_t b,
    std::uint32_t c,
    std::uint32_t d) {
    const auto triangleScore = [&](std::uint32_t i0, std::uint32_t i1, std::uint32_t i2) {
        const glm::dvec3 p0 = mesh.vertices[i0].position;
        const glm::dvec3 p1 = mesh.vertices[i1].position;
        const glm::dvec3 p2 = mesh.vertices[i2].position;
        const double e0 = glm::length(p1 - p0);
        const double e1 = glm::length(p2 - p1);
        const double e2 = glm::length(p0 - p2);
        const double longest = std::max({e0, e1, e2});
        const double shortest = std::max(1.0e-8, std::min({e0, e1, e2}));
        return shortest / longest;
    };

    const double diagAC = std::min(triangleScore(a, b, c), triangleScore(a, c, d));
    const double diagBD = std::min(triangleScore(a, b, d), triangleScore(b, c, d));
    if (diagAC >= diagBD) {
        appendTriangle(mesh, a, b, c);
        appendTriangle(mesh, a, c, d);
    } else {
        appendTriangle(mesh, a, b, d);
        appendTriangle(mesh, b, c, d);
    }
}

} // namespace vf::detail
