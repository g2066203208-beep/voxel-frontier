#include "vf/world/PlanetLodMeshBuilder.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <vector>

#include <glm/geometric.hpp>

namespace vf {
namespace {

struct Node {
    std::uint32_t face{};
    std::uint32_t depth{};
    double u0{-1.0};
    double v0{-1.0};
    double size{2.0};
};

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double l2 = glm::dot(value, value);
    return l2 > 1.0e-24 ? value / std::sqrt(l2) : fallback;
}

[[nodiscard]] double angleBetween(const glm::dvec3& a, const glm::dvec3& b) noexcept {
    return std::acos(std::clamp(glm::dot(safeNormalize(a), safeNormalize(b)), -1.0, 1.0));
}

struct NodeMetric {
    glm::dvec3 centerDirection{};
    double angularRadius{};
    double spanMeters{};
    double distanceMeters{};
    double screenErrorPixels{};
    bool aboveHorizon{};
};

[[nodiscard]] NodeMetric metricFor(
    const Node& node,
    const PlanetDefinition& planet,
    const glm::dvec3& camera,
    const PlanetLodConfig& config) noexcept {
    const double uc = node.u0 + 0.5 * node.size;
    const double vc = node.v0 + 0.5 * node.size;
    const glm::dvec3 center = cubeSphereDirection(node.face, uc, vc);
    const std::array<glm::dvec3, 4> corners{{
        cubeSphereDirection(node.face, node.u0, node.v0),
        cubeSphereDirection(node.face, node.u0 + node.size, node.v0),
        cubeSphereDirection(node.face, node.u0, node.v0 + node.size),
        cubeSphereDirection(node.face, node.u0 + node.size, node.v0 + node.size),
    }};
    double angularRadius = 0.0;
    for (const auto& corner : corners) angularRadius = std::max(angularRadius, angleBetween(center, corner));
    const double radius = std::max(1.0, planet.radius);
    const double span = 2.0 * angularRadius * radius;
    const double cameraRadius = glm::length(camera);
    const glm::dvec3 cameraDirection = safeNormalize(camera, center);
    const double centerDistance = glm::length(camera - center * radius);
    const double cellMeters = span / static_cast<double>(std::max(2U, config.patchResolution));
    const double focalPixels = config.viewportHeightPixels
        / (2.0 * std::tan(std::max(0.1, config.verticalFovRadians) * 0.5));
    const double conservativeDistance = std::max(1.0, centerDistance - span * 0.55);
    const double screenError = cellMeters / conservativeDistance * focalPixels;

    double horizonAngle = 3.14159265358979323846;
    if (cameraRadius > radius + 1.0) {
        horizonAngle = std::acos(std::clamp(radius / cameraRadius, 0.0, 1.0));
    }
    const double cameraSeparation = angleBetween(cameraDirection, center);
    const bool visible = cameraSeparation <= horizonAngle + angularRadius + config.horizonMarginRadians;
    return {center, angularRadius, span, centerDistance, screenError, visible};
}

void appendPatch(
    PlanetMesh& mesh,
    const Node& node,
    const PlanetSurfaceAuthority& surface,
    const PlanetLodConfig& config,
    PlanetLodStats* stats,
    const glm::dvec3& cameraPlanetLocal) {
    const std::uint32_t resolution = std::max(2U, config.patchResolution);
    const std::uint32_t stride = resolution + 1U;
    const std::uint32_t base = static_cast<std::uint32_t>(mesh.vertices.size());
    const PlanetDefinition& planet = surface.planet();

    for (std::uint32_t y = 0; y <= resolution; ++y) {
        const double fy = static_cast<double>(y) / static_cast<double>(resolution);
        const double v = node.v0 + node.size * fy;
        for (std::uint32_t x = 0; x <= resolution; ++x) {
            const double fx = static_cast<double>(x) / static_cast<double>(resolution);
            const double u = node.u0 + node.size * fx;
            const glm::dvec3 direction = cubeSphereDirection(node.face, u, v);
            const PlanetTerrainSample terrain = surface.sample(direction);
            PlanetVertex vertex{};
            vertex.position = glm::vec3(direction * (planet.radius + terrain.elevationMeters));
            vertex.normal = glm::vec3(surface.surfaceNormal(direction));
            vertex.color = planetTerrainColor(planet, terrain);
            vertex.material = planetTerrainMaterial(planet, terrain);
            mesh.vertices.push_back(vertex);
        }
    }
    for (std::uint32_t y = 0; y < resolution; ++y) {
        for (std::uint32_t x = 0; x < resolution; ++x) {
            const std::uint32_t i0 = base + y * stride + x;
            const std::uint32_t i1 = i0 + 1U;
            const std::uint32_t i2 = i0 + stride;
            const std::uint32_t i3 = i2 + 1U;
            mesh.indices.insert(mesh.indices.end(), {i0, i2, i1, i1, i2, i3});
        }
    }

    // Skirts exist only below the authoritative surface and solve T-junction cracks where two
    // quadtree neighbours differ in level. They never alter collision or the visible terrain height.
    if (config.skirtDepthMeters > 0.0) {
        const auto appendEdge = [&](const std::vector<std::uint32_t>& edge) {
            const std::uint32_t skirtBase = static_cast<std::uint32_t>(mesh.vertices.size());
            for (std::uint32_t sourceIndex : edge) {
                PlanetVertex skirt = mesh.vertices[sourceIndex];
                glm::dvec3 p = glm::dvec3(skirt.position);
                const double r = glm::length(p);
                if (r > config.skirtDepthMeters + 1.0)
                    p *= (r - config.skirtDepthMeters) / r;
                skirt.position = glm::vec3(p);
                mesh.vertices.push_back(skirt);
            }
            for (std::uint32_t i = 0; i + 1U < edge.size(); ++i) {
                const std::uint32_t a = edge[i];
                const std::uint32_t b = edge[i + 1U];
                const std::uint32_t sa = skirtBase + i;
                const std::uint32_t sb = skirtBase + i + 1U;
                mesh.indices.insert(mesh.indices.end(), {a, sa, b, b, sa, sb});
            }
        };
        std::vector<std::uint32_t> edge;
        edge.reserve(stride);
        for (std::uint32_t x = 0; x <= resolution; ++x) edge.push_back(base + x);
        appendEdge(edge);
        edge.clear();
        for (std::uint32_t y = 0; y <= resolution; ++y) edge.push_back(base + y * stride + resolution);
        appendEdge(edge);
        edge.clear();
        for (std::uint32_t x = 0; x <= resolution; ++x) edge.push_back(base + resolution * stride + (resolution - x));
        appendEdge(edge);
        edge.clear();
        for (std::uint32_t y = 0; y <= resolution; ++y) edge.push_back(base + (resolution - y) * stride);
        appendEdge(edge);
    }

    if (stats) {
        stats->deepestLevel = std::max(stats->deepestLevel, node.depth);
        const NodeMetric metric = metricFor(node, planet, cameraPlanetLocal, config);
        const double cell = metric.spanMeters / static_cast<double>(std::max(2U, resolution));
        stats->nearestCellMeters = std::min(stats->nearestCellMeters, cell);
    }
}

} // namespace

PlanetMesh buildAdaptivePlanetSurface(
    const PlanetSurfaceAuthority& surface,
    const glm::dvec3& cameraPlanetLocal,
    const PlanetLodConfig& configInput,
    PlanetLodStats* stats) {
    PlanetLodConfig config = configInput;
    config.patchResolution = std::clamp<std::uint32_t>(config.patchResolution, 4U, 64U);
    config.maxDepth = std::clamp<std::uint32_t>(config.maxDepth, 1U, 18U);
    config.maxLeafPatches = std::clamp<std::size_t>(config.maxLeafPatches, 64U, 20000U);
    config.targetScreenErrorPixels = std::clamp(config.targetScreenErrorPixels, 0.5, 12.0);
    config.viewportHeightPixels = std::max(64.0, config.viewportHeightPixels);
    config.skirtDepthMeters = std::clamp(config.skirtDepthMeters, 0.0, 30.0);

    PlanetLodStats localStats{};
    localStats.nearestCellMeters = std::numeric_limits<double>::infinity();
    std::vector<Node> pending;
    pending.reserve(config.maxLeafPatches * 2U);
    for (std::uint32_t face = 0; face < 6U; ++face) pending.push_back({face, 0U, -1.0, -1.0, 2.0});

    std::vector<Node> leaves;
    leaves.reserve(config.maxLeafPatches);
    while (!pending.empty()) {
        const Node node = pending.back();
        pending.pop_back();
        const NodeMetric metric = metricFor(node, surface.planet(), cameraPlanetLocal, config);
        if (!metric.aboveHorizon) continue;
        const bool canSplit = node.depth < config.maxDepth
            && leaves.size() + pending.size() + 4U < config.maxLeafPatches;
        if (canSplit && metric.screenErrorPixels > config.targetScreenErrorPixels) {
            const double half = node.size * 0.5;
            const std::uint32_t depth = node.depth + 1U;
            pending.push_back({node.face, depth, node.u0, node.v0, half});
            pending.push_back({node.face, depth, node.u0 + half, node.v0, half});
            pending.push_back({node.face, depth, node.u0, node.v0 + half, half});
            pending.push_back({node.face, depth, node.u0 + half, node.v0 + half, half});
        } else {
            leaves.push_back(node);
        }
    }

    PlanetMesh mesh{};
    for (const Node& node : leaves)
        appendPatch(mesh, node, surface, config, &localStats, cameraPlanetLocal);
    localStats.leafPatches = leaves.size();
    if (!std::isfinite(localStats.nearestCellMeters)) localStats.nearestCellMeters = 0.0;
    if (stats) *stats = localStats;
    return mesh;
}

} // namespace vf
