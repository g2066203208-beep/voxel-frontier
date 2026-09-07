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

[[nodiscard]] double smooth01(double value) noexcept {
    const double t = std::clamp(value, 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

struct NodeGeometry {
    glm::dvec3 centerDirection{};
    std::array<glm::dvec3, 4> corners{};
    double angularRadius{};
    double spanMeters{};
};

[[nodiscard]] NodeGeometry geometryFor(
    const Node& node,
    double planetRadius) noexcept {
    NodeGeometry geometry{};
    const double uc = node.u0 + 0.5 * node.size;
    const double vc = node.v0 + 0.5 * node.size;
    geometry.centerDirection = cubeSphereDirection(node.face, uc, vc);
    geometry.corners = {{
        cubeSphereDirection(node.face, node.u0, node.v0),
        cubeSphereDirection(node.face, node.u0 + node.size, node.v0),
        cubeSphereDirection(node.face, node.u0, node.v0 + node.size),
        cubeSphereDirection(node.face, node.u0 + node.size, node.v0 + node.size),
    }};
    for (const auto& corner : geometry.corners) {
        geometry.angularRadius = std::max(
            geometry.angularRadius,
            angleBetween(geometry.centerDirection, corner));
    }
    geometry.spanMeters = 2.0 * geometry.angularRadius * std::max(1.0, planetRadius);
    return geometry;
}

struct NodeMetric {
    glm::dvec3 centerDirection{};
    double angularRadius{};
    double spanMeters{};
    double distanceMeters{};
    double geometricErrorMeters{};
    double screenErrorPixels{};
    bool aboveHorizon{};
};

[[nodiscard]] NodeMetric metricFor(
    const Node& node,
    const PlanetSurfaceAuthority& surface,
    const glm::dvec3& camera,
    const PlanetLodConfig& config) noexcept {
    const PlanetDefinition& planet = surface.planet();
    const NodeGeometry geometry = geometryFor(node, planet.radius);
    const PlanetTerrainSample centerTerrain = surface.sample(geometry.centerDirection);

    const double uc = node.u0 + 0.5 * node.size;
    const double vc = node.v0 + 0.5 * node.size;
    const std::array<glm::dvec3, 8> reliefProbes{{
        geometry.corners[0], geometry.corners[1], geometry.corners[2], geometry.corners[3],
        cubeSphereDirection(node.face, uc, node.v0),
        cubeSphereDirection(node.face, uc, node.v0 + node.size),
        cubeSphereDirection(node.face, node.u0, vc),
        cubeSphereDirection(node.face, node.u0 + node.size, vc),
    }};
    double elevationMin = std::numeric_limits<double>::infinity();
    double elevationMax = -std::numeric_limits<double>::infinity();
    double elevationMean = 0.0;
    for (const glm::dvec3& probe : reliefProbes) {
        const double elevation = surface.sample(probe).elevationMeters;
        elevationMin = std::min(elevationMin, elevation);
        elevationMax = std::max(elevationMax, elevation);
        elevationMean += elevation;
    }
    elevationMean /= static_cast<double>(reliefProbes.size());

    const double cellMeters = geometry.spanMeters
        / static_cast<double>(std::max(2U, config.patchResolution));
    const double reliefSignal = std::max(
        std::abs(centerTerrain.elevationMeters - elevationMean),
        0.40 * std::max(0.0, elevationMax - elevationMin));
    const double geometricError = std::max(
        cellMeters * config.flatTerrainErrorFraction,
        reliefSignal * config.reliefErrorScale);

    const double radius = std::max(1.0, planet.radius);
    const double cameraRadius = glm::length(camera);
    const glm::dvec3 cameraDirection = safeNormalize(camera, geometry.centerDirection);
    const double centerSurfaceRadius = radius + centerTerrain.elevationMeters;
    const double centerDistance = glm::length(
        camera - geometry.centerDirection * centerSurfaceRadius);
    const double focalPixels = config.viewportHeightPixels
        / (2.0 * std::tan(std::max(0.1, config.verticalFovRadians) * 0.5));
    const double conservativeDistance = std::max(
        1.0,
        centerDistance - geometry.spanMeters * 0.55);
    const double screenError = geometricError / conservativeDistance * focalPixels;

    double horizonAngle = 3.14159265358979323846;
    if (cameraRadius > radius + 1.0) {
        horizonAngle = std::acos(std::clamp(radius / cameraRadius, 0.0, 1.0));
    }
    const double cameraSeparation = angleBetween(cameraDirection, geometry.centerDirection);
    const bool visible = cameraSeparation
        <= horizonAngle + geometry.angularRadius + config.horizonMarginRadians;
    return {
        geometry.centerDirection,
        geometry.angularRadius,
        geometry.spanMeters,
        centerDistance,
        geometricError,
        screenError,
        visible,
    };
}

void appendPatch(
    PlanetMesh& mesh,
    const Node& node,
    const PlanetSurfaceAuthority& surface,
    const PlanetLodConfig& config,
    PlanetLodStats* stats) {
    const std::uint32_t resolution = std::max(2U, config.patchResolution);
    const std::uint32_t stride = resolution + 1U;
    const std::uint32_t base = static_cast<std::uint32_t>(mesh.vertices.size());
    const PlanetDefinition& planet = surface.planet();
    const std::size_t pointCount = static_cast<std::size_t>(stride) * stride;

    // Each authoritative terrain point is sampled exactly once for this patch. Normals are then
    // reconstructed from the already sampled mesh grid, avoiding the old sampleSurface() path that
    // performed two extra full procedural/hydrology queries per vertex just to estimate a normal.
    std::vector<glm::dvec3> directions(pointCount);
    std::vector<glm::dvec3> positions(pointCount);
    std::vector<PlanetTerrainSample> terrainSamples(pointCount);

    for (std::uint32_t y = 0; y <= resolution; ++y) {
        const double fy = static_cast<double>(y) / static_cast<double>(resolution);
        const double v = node.v0 + node.size * fy;
        for (std::uint32_t x = 0; x <= resolution; ++x) {
            const double fx = static_cast<double>(x) / static_cast<double>(resolution);
            const double u = node.u0 + node.size * fx;
            const std::size_t index = static_cast<std::size_t>(y) * stride + x;
            directions[index] = cubeSphereDirection(node.face, u, v);
            terrainSamples[index] = surface.sample(directions[index]);
            positions[index] = directions[index]
                * (planet.radius + terrainSamples[index].elevationMeters);
        }
    }

    for (std::uint32_t y = 0; y <= resolution; ++y) {
        const std::uint32_t y0 = y > 0U ? y - 1U : y;
        const std::uint32_t y1 = y < resolution ? y + 1U : y;
        for (std::uint32_t x = 0; x <= resolution; ++x) {
            const std::uint32_t x0 = x > 0U ? x - 1U : x;
            const std::uint32_t x1 = x < resolution ? x + 1U : x;
            const std::size_t index = static_cast<std::size_t>(y) * stride + x;
            const glm::dvec3 du = positions[static_cast<std::size_t>(y) * stride + x1]
                - positions[static_cast<std::size_t>(y) * stride + x0];
            const glm::dvec3 dv = positions[static_cast<std::size_t>(y1) * stride + x]
                - positions[static_cast<std::size_t>(y0) * stride + x];
            glm::dvec3 normal = safeNormalize(glm::cross(du, dv), directions[index]);
            if (glm::dot(normal, directions[index]) < 0.0) normal = -normal;

            PlanetVertex vertex{};
            vertex.position = glm::vec3(positions[index]);
            vertex.normal = glm::vec3(normal);
            vertex.color = planetTerrainColor(planet, terrainSamples[index]);
            vertex.material = planetTerrainMaterial(planet, terrainSamples[index]);
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
        for (std::uint32_t y = 0; y <= resolution; ++y)
            edge.push_back(base + y * stride + resolution);
        appendEdge(edge);
        edge.clear();
        for (std::uint32_t x = 0; x <= resolution; ++x)
            edge.push_back(base + resolution * stride + (resolution - x));
        appendEdge(edge);
        edge.clear();
        for (std::uint32_t y = 0; y <= resolution; ++y)
            edge.push_back(base + (resolution - y) * stride);
        appendEdge(edge);
    }

    if (stats) {
        stats->deepestLevel = std::max(stats->deepestLevel, node.depth);
        const NodeGeometry geometry = geometryFor(node, planet.radius);
        const double cell = geometry.spanMeters / static_cast<double>(std::max(2U, resolution));
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
    config.maxDepth = std::clamp<std::uint32_t>(config.maxDepth, 1U, 20U);
    config.maxLeafPatches = std::clamp<std::size_t>(config.maxLeafPatches, 64U, 20000U);
    config.targetScreenErrorPixels = std::clamp(config.targetScreenErrorPixels, 0.5, 12.0);
    config.viewportHeightPixels = std::max(64.0, config.viewportHeightPixels);
    config.skirtDepthMeters = std::clamp(config.skirtDepthMeters, 0.0, 30.0);
    config.flatTerrainErrorFraction = std::clamp(config.flatTerrainErrorFraction, 0.20, 1.0);
    config.reliefErrorScale = std::clamp(config.reliefErrorScale, 0.5, 4.0);
    config.nearFieldRadiusMeters = std::clamp(config.nearFieldRadiusMeters, 0.0, 50000.0);
    config.nearFieldCellMeters = std::clamp(config.nearFieldCellMeters, 0.5, 500.0);
    config.detailTransitionStartMeters = std::clamp(
        config.detailTransitionStartMeters, 0.0, 200000.0);
    config.detailTransitionEndMeters = std::clamp(
        std::max(config.detailTransitionStartMeters + 1.0, config.detailTransitionEndMeters),
        config.detailTransitionStartMeters + 1.0,
        500000.0);
    config.transitionFarCellMeters = std::clamp(
        std::max(config.nearFieldCellMeters, config.transitionFarCellMeters),
        config.nearFieldCellMeters,
        5000.0);

    PlanetLodStats localStats{};
    localStats.nearestCellMeters = std::numeric_limits<double>::infinity();
    const auto approximateNodeDistance = [&](const Node& node) noexcept {
        const NodeGeometry geometry = geometryFor(node, surface.planet().radius);
        return glm::length(cameraPlanetLocal
            - geometry.centerDirection * surface.planet().radius);
    };

    std::vector<Node> pending;
    pending.reserve(config.maxLeafPatches * 2U);
    std::array<Node, 6> roots{};
    for (std::uint32_t face = 0; face < roots.size(); ++face)
        roots[face] = {face, 0U, -1.0, -1.0, 2.0};
    std::sort(roots.begin(), roots.end(), [&](const Node& a, const Node& b) {
        return approximateNodeDistance(a) > approximateNodeDistance(b);
    });
    for (const Node& root : roots) pending.push_back(root);

    std::vector<Node> leaves;
    leaves.reserve(config.maxLeafPatches);
    while (!pending.empty()) {
        const Node node = pending.back();
        pending.pop_back();
        const NodeMetric metric = metricFor(node, surface, cameraPlanetLocal, config);
        ++localStats.evaluatedNodes;
        localStats.maximumEstimatedErrorMeters = std::max(
            localStats.maximumEstimatedErrorMeters,
            metric.geometricErrorMeters);
        if (!metric.aboveHorizon) continue;
        const bool canSplit = node.depth < config.maxDepth
            && leaves.size() + pending.size() + 4U < config.maxLeafPatches;
        const double nodeCellMeters = metric.spanMeters
            / static_cast<double>(std::max(2U, config.patchResolution));
        bool forceSmoothDetail = false;
        if (config.nearFieldRadiusMeters > 0.0) {
            const double radius = std::max(1.0, surface.planet().radius);
            const glm::dvec3 cameraDirection = safeNormalize(
                cameraPlanetLocal, metric.centerDirection);
            const double surfaceDistanceMeters = angleBetween(
                cameraDirection, metric.centerDirection) * radius;
            const double cameraAltitudeMeters = std::max(
                0.0, glm::length(cameraPlanetLocal) - radius);
            const double effectiveDistanceMeters = std::sqrt(
                surfaceDistanceMeters * surfaceDistanceMeters
                    + 0.20 * cameraAltitudeMeters * cameraAltitudeMeters);
            const double transitionSpan = std::max(
                1.0, config.detailTransitionEndMeters - config.detailTransitionStartMeters);
            const double transitionT = smooth01(
                (effectiveDistanceMeters - config.detailTransitionStartMeters) / transitionSpan);
            const double nearCell = std::max(0.5, config.nearFieldCellMeters);
            const double farCell = std::max(nearCell, config.transitionFarCellMeters);
            const double desiredCellMeters = std::exp(
                std::log(nearCell) * (1.0 - transitionT)
                    + std::log(farCell) * transitionT);
            forceSmoothDetail = effectiveDistanceMeters <= config.detailTransitionEndMeters
                && nodeCellMeters > desiredCellMeters * 1.08;
        }
        if (canSplit && (forceSmoothDetail
            || metric.screenErrorPixels > config.targetScreenErrorPixels)) {
            const double half = node.size * 0.5;
            const std::uint32_t depth = node.depth + 1U;
            std::array<Node, 4> children{{
                {node.face, depth, node.u0, node.v0, half},
                {node.face, depth, node.u0 + half, node.v0, half},
                {node.face, depth, node.u0, node.v0 + half, half},
                {node.face, depth, node.u0 + half, node.v0 + half, half},
            }};
            std::sort(children.begin(), children.end(), [&](const Node& a, const Node& b) {
                return approximateNodeDistance(a) > approximateNodeDistance(b);
            });
            for (const Node& child : children) pending.push_back(child);
        } else {
            leaves.push_back(node);
        }
    }

    PlanetMesh mesh{};
    const std::size_t baseVerticesPerPatch = static_cast<std::size_t>(config.patchResolution + 1U)
        * static_cast<std::size_t>(config.patchResolution + 1U);
    const std::size_t skirtVerticesPerPatch = config.skirtDepthMeters > 0.0
        ? static_cast<std::size_t>(4U * (config.patchResolution + 1U))
        : 0U;
    mesh.vertices.reserve(leaves.size() * (baseVerticesPerPatch + skirtVerticesPerPatch));
    mesh.indices.reserve(leaves.size() * static_cast<std::size_t>(
        6U * config.patchResolution * config.patchResolution
        + (config.skirtDepthMeters > 0.0 ? 24U * config.patchResolution : 0U)));

    for (const Node& node : leaves)
        appendPatch(mesh, node, surface, config, &localStats);
    localStats.leafPatches = leaves.size();
    if (!std::isfinite(localStats.nearestCellMeters)) localStats.nearestCellMeters = 0.0;
    if (stats) *stats = localStats;
    return mesh;
}

} // namespace vf
