#include "vf/world/PlanetSurface.hpp"
#include "vf/world/detail/PlanetGenerationInternal.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <stdexcept>

#include <glm/geometric.hpp>

namespace vf {

namespace {

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
    const std::uint32_t firstIndex = static_cast<std::uint32_t>(mesh.indices.size());
    const double cell = 2.0 / static_cast<double>(subdivisions);

    mesh.vertices.reserve(mesh.vertices.size() + static_cast<std::size_t>(stride) * stride);
    mesh.indices.reserve(mesh.indices.size() + static_cast<std::size_t>(subdivisions) * subdivisions * 6U);

    for (std::uint32_t y = 0; y <= subdivisions; ++y) {
        for (std::uint32_t x = 0; x <= subdivisions; ++x) {
            double u = -1.0 + 2.0 * static_cast<double>(x) / static_cast<double>(subdivisions);
            double v = -1.0 + 2.0 * static_cast<double>(y) / static_cast<double>(subdivisions);

            // Small deterministic irregularity breaks a perfect grid without turning every cell into
            // its own visual event. Larger jitter was measured to worsen diagonal crease noise in
            // low-poly terrain, so V5 keeps this deliberately subtle.
            if (definition != nullptr
                && x > 0U && x < subdivisions
                && y > 0U && y < subdivisions) {
                const std::uint64_t key = static_cast<std::uint64_t>(face) * 0x100000000ULL
                    + static_cast<std::uint64_t>(y) * stride + x;
                constexpr double kCoherentJitterFraction = 0.07;
                u += detail::randomSigned(definition->seed ^ 0x243F6A8885A308D3ULL, key)
                    * cell * kCoherentJitterFraction;
                v += detail::randomSigned(definition->seed ^ 0x13198A2E03707344ULL, key)
                    * cell * kCoherentJitterFraction;
                u = std::clamp(u, -1.0, 1.0);
                v = std::clamp(v, -1.0, 1.0);
            }

            const glm::dvec3 localDirection = cubeSphereDirection(face, u, v);
            const glm::dvec3 worldDirection = orientation
                ? glm::normalize((*orientation) * localDirection)
                : localDirection;
            const double elevation = definition ? planetHeight(*definition, localDirection) : 0.0;
            const glm::dvec3 world = center + worldDirection * (radius + elevation);
            const double normalizedHeight = definition && definition->maxElevation > 0.0
                ? elevation / definition->maxElevation
                : 0.0;

            PlanetVertex vertex{};
            vertex.position = glm::vec3(world);
            vertex.normal = glm::vec3(worldDirection);
            vertex.color = constantColor
                ? detail::proxyColor(*constantColor, localDirection)
                : detail::terrainMaterialData(*definition, localDirection, normalizedHeight);
            mesh.vertices.push_back(vertex);
        }
    }

    for (std::uint32_t y = 0; y < subdivisions; ++y) {
        for (std::uint32_t x = 0; x < subdivisions; ++x) {
            const std::uint32_t i0 = baseVertex + y * stride + x;
            const std::uint32_t i1 = i0 + 1U;
            const std::uint32_t i2 = i0 + stride;
            const std::uint32_t i3 = i2 + 1U;
            const std::uint64_t key = static_cast<std::uint64_t>(face) * 0x100000000ULL
                + static_cast<std::uint64_t>(y) * subdivisions + x;
            const bool flipDiagonal = definition != nullptr
                && detail::random01(definition->seed ^ 0xA4093822299F31D0ULL, key) > 0.5;
            if (flipDiagonal) {
                mesh.indices.insert(mesh.indices.end(), {i0, i2, i3, i0, i3, i1});
            } else {
                mesh.indices.insert(mesh.indices.end(), {i0, i2, i1, i1, i2, i3});
            }
        }
    }

    if (definition != nullptr) {
        const std::uint32_t indexCount = static_cast<std::uint32_t>(mesh.indices.size()) - firstIndex;
        detail::appendDrawRange(mesh, firstIndex, indexCount, PlanetDrawClass::TerrainPatch);
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

double planetHeight(const PlanetDefinition& definition, const glm::dvec3& directionInput) {
    const glm::dvec3 d = glm::normalize(directionInput);
    const detail::LandformProfile landform = detail::semanticLandform(definition, d);

    // Semantic forms carry the image: continent, mountain belt, valley, plateau and basin. Fine
    // displacement is intentionally subordinate so the terrain reads as broad designed planes.
    const double ridgeDetailNoise = detail::valueNoise3(
        definition.seed ^ 0xBB67AE8584CAA73BULL,
        d * 5.6 + glm::dvec3{-3.2, 1.4, 2.6});
    const double ridgeDetail = 1.0 - std::abs(ridgeDetailNoise * 2.0 - 1.0);
    const double fineDetail = detail::centeredFbm(
        definition.seed ^ 0xA54FF53A5F1D36F1ULL,
        d * 8.8 + glm::dvec3{0.7, 3.8, -2.4},
        2U);

    double shape = (landform.continent - 0.50) * 1.06;
    shape += landform.mountainBelt * (0.24 + 0.22 * ridgeDetail);
    shape += landform.plateau * 0.11 * (0.45 + 0.55 * landform.continent);
    shape -= landform.valleyCorridor * (0.10 + 0.12 * (1.0 - landform.mountainBelt));
    shape -= landform.basin * 0.26;
    shape += fineDetail * (0.028 + 0.040 * landform.mountainBelt);

    // The authoritative ocean is radius-6m. Compress relief near that level to create readable
    // shelves, beaches and broader shore transitions instead of a noisy contour line.
    if (definition.maxElevation > 0.0) {
        const double seaLevelNormalized = -6.0 / definition.maxElevation;
        const double distanceToSea = std::abs(shape - seaLevelNormalized);
        const double coast = 1.0 - std::clamp(distanceToSea / 0.17, 0.0, 1.0);
        const double coastSmooth = coast * coast * (3.0 - 2.0 * coast);
        shape = seaLevelNormalized + (shape - seaLevelNormalized) * (1.0 - coastSmooth * 0.52);

        const double coastalBluff = coastSmooth * landform.mountainBelt
            * std::clamp((ridgeDetailNoise - 0.58) / 0.30, 0.0, 1.0);
        shape += coastalBluff * 0.075;
    }

    shape = std::clamp(shape, -1.0, 1.0);
    return shape * definition.maxElevation;
}

double planetSurfaceRadius(const PlanetDefinition& definition, const glm::dvec3& direction) {
    return definition.radius + planetHeight(definition, direction);
}

PlanetMesh buildPlanetSurface(const PlanetDefinition& definition, std::uint32_t subdivisionsPerFace) {
    if (subdivisionsPerFace < 2U) throw std::invalid_argument("planet subdivisions must be >= 2");

    PlanetMesh mesh;
    mesh.horizonOccluderRadius = static_cast<float>(std::max(0.0, definition.radius - definition.maxElevation));

    // Physics continues to query the analytic height function directly; this only limits visual
    // tessellation. 44 instead of the runtime-requested 64 cuts base terrain triangles by ~53%
    // and makes each polygon plane visually meaningful rather than producing triangle confetti.
    constexpr std::uint32_t kMaxCoherentTerrainSubdivisions = 44U;
    const std::uint32_t terrainSubdivisions = std::min(subdivisionsPerFace, kMaxCoherentTerrainSubdivisions);
    for (std::uint32_t face = 0; face < 6U; ++face) {
        appendFace(mesh, &definition, glm::dvec3{0.0}, nullptr, definition.radius, face, terrainSubdivisions, nullptr);
    }

    constexpr std::uint32_t kWorldDetailMinSubdivisionsPerFace = 24U;
    if (subdivisionsPerFace >= kWorldDetailMinSubdivisionsPerFace) {
        const auto treePlacements = detail::scatterTrees(mesh, definition);
        detail::scatterRocks(mesh, definition, treePlacements);

        constexpr double kMeanSeaLevelBelowReferenceMeters = 6.0;
        constexpr std::uint32_t kOceanSubdivisionsPerFace = 32U;
        appendOceanSurface(
            mesh,
            definition,
            definition.radius - kMeanSeaLevelBelowReferenceMeters,
            kOceanSubdivisionsPerFace);
    }
    return mesh;
}

void appendCelestialProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    double radius,
    std::uint32_t subdivisionsPerFace,
    const glm::vec3& color) {
    appendCelestialBodyProxy(mesh, center, glm::dquat{1.0, 0.0, 0.0, 0.0}, radius, subdivisionsPerFace, color);
}

void appendCelestialBodyProxy(
    PlanetMesh& mesh,
    const glm::dvec3& center,
    const glm::dquat& orientation,
    double radius,
    std::uint32_t subdivisionsPerFace,
    const glm::vec3& baseColor) {
    if (subdivisionsPerFace < 2U) throw std::invalid_argument("proxy subdivisions must be >= 2");
    const glm::dquat normalizedOrientation = glm::normalize(orientation);
    for (std::uint32_t face = 0; face < 6U; ++face) {
        appendFace(mesh, nullptr, center, &normalizedOrientation, radius, face, subdivisionsPerFace, &baseColor);
    }
}

} // namespace vf
