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
    const double cell = 2.0 / static_cast<double>(subdivisions);

    mesh.vertices.reserve(mesh.vertices.size() + static_cast<std::size_t>(stride) * stride);
    mesh.indices.reserve(mesh.indices.size() + static_cast<std::size_t>(subdivisions) * subdivisions * 6U);

    for (std::uint32_t y = 0; y <= subdivisions; ++y) {
        for (std::uint32_t x = 0; x <= subdivisions; ++x) {
            double u = -1.0 + 2.0 * static_cast<double>(x) / static_cast<double>(subdivisions);
            double v = -1.0 + 2.0 * static_cast<double>(y) / static_cast<double>(subdivisions);

            // Interior vertex jitter breaks the obvious square-grid silhouette while keeping cube-face
            // edges exact, so neighboring faces remain watertight. The renderer shades each triangle
            // with a derivative face normal, exposing deliberate low-poly facets rather than smoothing them.
            if (definition != nullptr
                && x > 0U && x < subdivisions
                && y > 0U && y < subdivisions) {
                const std::uint64_t key = static_cast<std::uint64_t>(face) * 0x100000000ULL
                    + static_cast<std::uint64_t>(y) * stride + x;
                u += detail::randomSigned(definition->seed ^ 0x243F6A8885A308D3ULL, key) * cell * 0.18;
                v += detail::randomSigned(definition->seed ^ 0x13198A2E03707344ULL, key) * cell * 0.18;
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
}

} // namespace

glm::dvec3 cubeSphereDirection(std::uint32_t face, double u, double v) {
    glm::dvec3 cube{};
    switch (face) {
    case 0: cube = {1.0, v, -u}; break;   // +X
    case 1: cube = {-1.0, v, u}; break;   // -X
    case 2: cube = {u, 1.0, -v}; break;   // +Y
    case 3: cube = {u, -1.0, v}; break;   // -Y
    case 4: cube = {u, v, 1.0}; break;    // +Z
    case 5: cube = {-u, v, -1.0}; break;  // -Z
    default: throw std::out_of_range("cubeSphereDirection face must be 0..5");
    }
    return glm::normalize(cube);
}

double planetHeight(const PlanetDefinition& definition, const glm::dvec3& directionInput) {
    const glm::dvec3 d = glm::normalize(directionInput);

    // 3D noise evaluated on the unit direction is seam-free over the sphere. Broad fBm creates
    // continents/valleys; a ridged octave creates mountain chains; a smaller octave shapes the
    // low-poly facets without turning the planet into high-frequency static.
    const double broad = detail::centeredFbm(
        definition.seed ^ 0x3C6EF372FE94F82BULL,
        d * 2.15 + glm::dvec3{2.7, -1.9, 4.1},
        5U);
    const double ridgeNoise = detail::valueNoise3(
        definition.seed ^ 0xBB67AE8584CAA73BULL,
        d * 5.1 + glm::dvec3{-3.2, 1.4, 2.6});
    const double ridged = 1.0 - std::abs(ridgeNoise * 2.0 - 1.0);
    const double fineDetail = detail::centeredFbm(
        definition.seed ^ 0xA54FF53A5F1D36F1ULL,
        d * 10.8 + glm::dvec3{0.7, 3.8, -2.4},
        3U);
    const double basin = detail::centeredFbm(
        definition.seed ^ 0x510E527FADE682D1ULL,
        d * 1.25,
        3U);

    double shape = broad * 0.58
        + (ridged - 0.48) * 0.34
        + fineDetail * 0.12
        + basin * 0.10;
    if (shape < 0.0) shape *= 0.86;
    shape = std::clamp(shape, -1.0, 1.0);
    return shape * definition.maxElevation;
}

double planetSurfaceRadius(const PlanetDefinition& definition, const glm::dvec3& direction) {
    return definition.radius + planetHeight(definition, direction);
}

PlanetMesh buildPlanetSurface(const PlanetDefinition& definition, std::uint32_t subdivisionsPerFace) {
    if (subdivisionsPerFace < 2U) throw std::invalid_argument("planet subdivisions must be >= 2");

    PlanetMesh mesh;
    for (std::uint32_t face = 0; face < 6U; ++face) {
        appendFace(mesh, &definition, glm::dvec3{0.0}, nullptr, definition.radius, face, subdivisionsPerFace, nullptr);
    }

    // Ecology and visible ocean are tied to the high-detail planetary surface LOD. Low-resolution
    // meshes remain terrain-only for fast tests/proxies; the runtime 64x64 face mesh receives the
    // deterministic trees, rocks and a deliberately coarser faceted ocean.
    constexpr std::uint32_t kWorldDetailMinSubdivisionsPerFace = 24U;
    if (subdivisionsPerFace >= kWorldDetailMinSubdivisionsPerFace) {
        const auto treePlacements = detail::scatterTrees(mesh, definition);
        detail::scatterRocks(mesh, definition, treePlacements);

        // Main.cpp's authoritative physical ocean currently uses radius - 6 m. Keeping the visible
        // mean sea surface identical prevents the renderer and buoyancy/ocean queries disagreeing.
        constexpr double kMeanSeaLevelBelowReferenceMeters = 6.0;
        constexpr std::uint32_t kOceanSubdivisionsPerFace = 40U;
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
