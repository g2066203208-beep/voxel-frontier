#include "vf/world/PlanetSurface.hpp"
#include "vf/world/detail/PlanetGenerationInternal.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <stdexcept>

#include <glm/geometric.hpp>

namespace vf {

void appendOceanSurface(
    PlanetMesh& mesh,
    const PlanetDefinition& definition,
    double oceanSurfaceRadius,
    std::uint32_t subdivisionsPerFace) {
    if (subdivisionsPerFace < 2U) throw std::invalid_argument("ocean subdivisions must be >= 2");
    if (oceanSurfaceRadius <= 0.0) throw std::invalid_argument("ocean surface radius must be positive");
    if (mesh.oceanIndexCount != 0U) throw std::invalid_argument("planet mesh already contains an ocean range");

    mesh.oceanFirstIndex = static_cast<std::uint32_t>(mesh.indices.size());
    const double seaElevation = oceanSurfaceRadius - definition.radius;
    const std::uint32_t stride = subdivisionsPerFace + 1U;
    const double cell = 2.0 / static_cast<double>(subdivisionsPerFace);

    const std::array<glm::dvec3, 3> waveDirections{
        glm::normalize(glm::dvec3{0.82, 0.18, 0.54}),
        glm::normalize(glm::dvec3{-0.28, 0.91, 0.31}),
        glm::normalize(glm::dvec3{0.47, -0.39, 0.79}),
    };
    const std::array<double, 3> waveAmplitude{0.34, 0.17, 0.085};
    const std::array<double, 3> waveFrequency{0.125, 0.215, 0.355};
    const std::array<double, 3> wavePhase{
        detail::seedPhase(definition.seed, 610U),
        detail::seedPhase(definition.seed, 611U),
        detail::seedPhase(definition.seed, 612U),
    };

    for (std::uint32_t face = 0; face < 6U; ++face) {
        const std::uint32_t baseVertex = static_cast<std::uint32_t>(mesh.vertices.size());
        const std::uint32_t faceFirstIndex = static_cast<std::uint32_t>(mesh.indices.size());
        mesh.vertices.reserve(mesh.vertices.size() + static_cast<std::size_t>(stride) * stride);
        mesh.indices.reserve(mesh.indices.size()
            + static_cast<std::size_t>(subdivisionsPerFace) * subdivisionsPerFace * 6U);

        for (std::uint32_t y = 0; y <= subdivisionsPerFace; ++y) {
            for (std::uint32_t x = 0; x <= subdivisionsPerFace; ++x) {
                double u = -1.0 + 2.0 * static_cast<double>(x) / static_cast<double>(subdivisionsPerFace);
                double v = -1.0 + 2.0 * static_cast<double>(y) / static_cast<double>(subdivisionsPerFace);
                if (x > 0U && x < subdivisionsPerFace && y > 0U && y < subdivisionsPerFace) {
                    const std::uint64_t key = static_cast<std::uint64_t>(face) * 0x100000000ULL
                        + static_cast<std::uint64_t>(y) * stride + x;
                    u += detail::randomSigned(definition.seed ^ 0x082EFA98EC4E6C89ULL, key) * cell * 0.10;
                    v += detail::randomSigned(definition.seed ^ 0x452821E638D01377ULL, key) * cell * 0.10;
                    u = std::clamp(u, -1.0, 1.0);
                    v = std::clamp(v, -1.0, 1.0);
                }

                const glm::dvec3 direction = cubeSphereDirection(face, u, v);
                const glm::dvec3 basePoint = direction * oceanSurfaceRadius;
                double waveHeight = 0.0;
                for (std::size_t wave = 0; wave < waveDirections.size(); ++wave) {
                    const double phase = glm::dot(basePoint, waveDirections[wave]) * waveFrequency[wave]
                        + wavePhase[wave];
                    waveHeight += std::sin(phase) * waveAmplitude[wave];
                }
                waveHeight += detail::centeredFbm(
                    definition.seed ^ 0xD1310BA698DFB5ACULL,
                    direction * 8.0,
                    3U) * 0.075;

                const double terrainElevation = planetHeight(definition, direction);
                const double waterDepthMeters = std::max(0.0, seaElevation - terrainElevation);
                const double normalizedDepth = std::clamp(waterDepthMeters / 18.0, 0.0, 1.0);
                const double shoreVariation = 0.5 + 0.5 * detail::centeredFbm(
                    definition.seed ^ 0xBE5466CF34E90C6CULL,
                    direction * 13.0,
                    3U);

                PlanetVertex vertex{};
                vertex.position = glm::vec3(direction * (oceanSurfaceRadius + waveHeight));
                vertex.normal = glm::vec3(direction);
                vertex.color = {
                    detail::kOceanMaterialMarker,
                    static_cast<float>(normalizedDepth),
                    static_cast<float>(shoreVariation),
                };
                mesh.vertices.push_back(vertex);
            }
        }

        for (std::uint32_t y = 0; y < subdivisionsPerFace; ++y) {
            for (std::uint32_t x = 0; x < subdivisionsPerFace; ++x) {
                const std::uint32_t i0 = baseVertex + y * stride + x;
                const std::uint32_t i1 = i0 + 1U;
                const std::uint32_t i2 = i0 + stride;
                const std::uint32_t i3 = i2 + 1U;
                const float deepestCorner = std::max({
                    mesh.vertices[i0].color.y,
                    mesh.vertices[i1].color.y,
                    mesh.vertices[i2].color.y,
                    mesh.vertices[i3].color.y,
                });
                if (deepestCorner <= 1.0e-5F) continue;

                const std::uint64_t key = static_cast<std::uint64_t>(face) * 0x100000000ULL
                    + static_cast<std::uint64_t>(y) * subdivisionsPerFace + x;
                const bool flip = detail::random01(
                    definition.seed ^ 0xC0AC29B7C97C50DDULL,
                    key) > 0.5;
                if (flip) {
                    mesh.indices.insert(mesh.indices.end(), {i0, i2, i3, i0, i3, i1});
                } else {
                    mesh.indices.insert(mesh.indices.end(), {i0, i2, i1, i1, i2, i3});
                }
            }
        }

        const std::uint32_t faceIndexCount = static_cast<std::uint32_t>(mesh.indices.size()) - faceFirstIndex;
        detail::appendDrawRange(mesh, faceFirstIndex, faceIndexCount, PlanetDrawClass::OceanPatch);
    }

    mesh.oceanIndexCount = static_cast<std::uint32_t>(mesh.indices.size()) - mesh.oceanFirstIndex;
}

} // namespace vf
