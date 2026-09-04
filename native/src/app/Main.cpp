#include "vf/gameplay/PhysicsInteraction.hpp"
#include "vf/physics/PhysicsWorld.hpp"
#include "vf/platform/SdlPlatform.hpp"
#include "vf/player/PlanetCamera.hpp"
#include "vf/render/PhysicsDebugMesh.hpp"
#include "vf/render/VulkanRenderer.hpp"
#include "vf/world/CelestialSystem.hpp"
#include "vf/world/PlanetSurface.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <vector>

#include <glm/common.hpp>
#include <glm/ext/matrix_clip_space.hpp>
#include <glm/ext/matrix_transform.hpp>
#include <glm/geometric.hpp>
#include <glm/gtc/quaternion.hpp>

namespace {

constexpr double kPi = 3.1415926535897932384626433832795;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-18) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] glm::dvec3 safeEast(const glm::dvec3& up) noexcept {
    const glm::dvec3 reference = std::abs(up.y) < 0.92
        ? glm::dvec3{0.0, 1.0, 0.0}
        : glm::dvec3{1.0, 0.0, 0.0};
    return safeNormalize(glm::cross(reference, up), {1.0, 0.0, 0.0});
}

[[nodiscard]] double circularOrbitSpeed(double parentMassKg, double radiusMeters) {
    return std::sqrt(vf::CelestialSystem::kGravitationalConstant * parentMassKg
        / std::max(1.0, radiusMeters));
}

void appendMesh(vf::PlanetMesh& destination, const vf::PlanetMesh& source) {
    const std::uint32_t base = static_cast<std::uint32_t>(destination.vertices.size());
    destination.vertices.insert(destination.vertices.end(), source.vertices.begin(), source.vertices.end());
    destination.indices.reserve(destination.indices.size() + source.indices.size());
    for (const std::uint32_t index : source.indices) destination.indices.push_back(base + index);
}

[[nodiscard]] glm::dvec3 boxInertia(double mass, const glm::dvec3& halfExtents) {
    return {
        mass * (halfExtents.y * halfExtents.y + halfExtents.z * halfExtents.z) / 3.0,
        mass * (halfExtents.x * halfExtents.x + halfExtents.z * halfExtents.z) / 3.0,
        mass * (halfExtents.x * halfExtents.x + halfExtents.y * halfExtents.y) / 3.0,
    };
}

struct PropVisual {
    std::uint32_t bodyId{};
    glm::dvec3 halfExtents{};
    glm::vec3 encodedColor{};
};

[[nodiscard]] glm::mat4 makeLocalViewProjection(
    const glm::dvec3& forward,
    const glm::dvec3& up,
    float aspect) {
    aspect = std::max(aspect, 0.1F);
    const glm::mat4 view = glm::lookAtRH(
        glm::vec3{0.0F},
        glm::vec3(safeNormalize(forward, {0.0, 0.0, -1.0})),
        glm::vec3(safeNormalize(up)));
    glm::mat4 projection = glm::perspectiveRH_ZO(glm::radians(68.0F), aspect, 0.05F, 50000000.0F);
    projection[1][1] *= -1.0F;
    return projection * view;
}

struct ProjectedPoint {
    glm::dvec3 world{};
    double x{};
    double y{};
};

[[nodiscard]] double cross2(const ProjectedPoint& a, const ProjectedPoint& b, const ProjectedPoint& c) {
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
}

void appendDirectionalBoxShadow(
    vf::PlanetMesh& mesh,
    const glm::dvec3& center,
    const glm::dquat& orientation,
    const glm::dvec3& halfExtents,
    const glm::dvec3& groundPoint,
    const glm::dvec3& groundNormalInput,
    const glm::dvec3& lightRayInput,
    const glm::vec3& color) {
    const glm::dvec3 normal = safeNormalize(groundNormalInput);
    const glm::dvec3 lightRay = safeNormalize(lightRayInput, {0.0, -1.0, 0.0});
    const double denominator = glm::dot(lightRay, normal);
    if (denominator >= -0.02) return;

    glm::dvec3 tangentX = safeNormalize(glm::cross(
        std::abs(normal.y) < 0.9 ? glm::dvec3{0.0, 1.0, 0.0} : glm::dvec3{1.0, 0.0, 0.0},
        normal), {1.0, 0.0, 0.0});
    const glm::dvec3 tangentY = safeNormalize(glm::cross(normal, tangentX), {0.0, 0.0, 1.0});
    const glm::dquat q = glm::normalize(orientation);

    std::vector<ProjectedPoint> points;
    points.reserve(8);
    for (int sx : {-1, 1}) {
        for (int sy : {-1, 1}) {
            for (int sz : {-1, 1}) {
                const glm::dvec3 localCorner{
                    halfExtents.x * static_cast<double>(sx),
                    halfExtents.y * static_cast<double>(sy),
                    halfExtents.z * static_cast<double>(sz)};
                const glm::dvec3 corner = center + q * localCorner;
                const double t = glm::dot(groundPoint - corner, normal) / denominator;
                if (t < 0.0 || t > 250.0) continue;
                const glm::dvec3 p = corner + lightRay * t + normal * 0.018;
                const glm::dvec3 rel = p - groundPoint;
                points.push_back({p, glm::dot(rel, tangentX), glm::dot(rel, tangentY)});
            }
        }
    }
    if (points.size() < 3U) return;

    std::sort(points.begin(), points.end(), [](const ProjectedPoint& a, const ProjectedPoint& b) {
        if (a.x != b.x) return a.x < b.x;
        return a.y < b.y;
    });

    std::vector<ProjectedPoint> hull;
    hull.reserve(points.size() * 2U);
    for (const auto& p : points) {
        while (hull.size() >= 2U && cross2(hull[hull.size() - 2U], hull.back(), p) <= 0.0) hull.pop_back();
        hull.push_back(p);
    }
    const std::size_t lowerSize = hull.size();
    for (auto it = points.rbegin() + 1; it != points.rend(); ++it) {
        while (hull.size() > lowerSize && cross2(hull[hull.size() - 2U], hull.back(), *it) <= 0.0) hull.pop_back();
        hull.push_back(*it);
    }
    if (hull.size() > 1U) hull.pop_back();
    if (hull.size() < 3U) return;

    glm::dvec3 centroid{};
    for (const auto& p : hull) centroid += p.world;
    centroid /= static_cast<double>(hull.size());

    const std::uint32_t base = static_cast<std::uint32_t>(mesh.vertices.size());
    vf::PlanetVertex centerVertex{};
    centerVertex.position = glm::vec3(centroid);
    centerVertex.normal = glm::vec3(normal);
    centerVertex.color = color;
    mesh.vertices.push_back(centerVertex);
    for (const auto& p : hull) {
        vf::PlanetVertex v = centerVertex;
        v.position = glm::vec3(p.world);
        mesh.vertices.push_back(v);
    }
    for (std::uint32_t i = 0; i < static_cast<std::uint32_t>(hull.size()); ++i) {
        const std::uint32_t next = (i + 1U) % static_cast<std::uint32_t>(hull.size());
        mesh.indices.insert(mesh.indices.end(), {base, base + 1U + i, base + 1U + next});
    }
}

void appendHud(
    vf::PlanetMesh& mesh,
    const glm::dvec3& camera,
    const glm::dvec3& forward,
    const glm::dvec3& up,
    double flightSpeedMps) {
    const glm::dvec3 right = safeNormalize(glm::cross(forward, up), {1.0, 0.0, 0.0});
    const glm::dvec3 center = camera + forward * 0.45;
    const glm::vec3 white{9.0F, 9.0F, 9.0F};
    constexpr double gap = 0.0028;
    constexpr double outer = 0.0100;
    constexpr double thickness = 0.00072;
    vf::appendDebugRod(mesh, center + right * gap, center + right * outer, thickness, white);
    vf::appendDebugRod(mesh, center - right * gap, center - right * outer, thickness, white);
    vf::appendDebugRod(mesh, center + up * gap, center + up * outer, thickness, white);
    vf::appendDebugRod(mesh, center - up * gap, center - up * outer, thickness, white);

    // Logarithmic 25 m/s -> 2,000,000 m/s speed bar at the lower-right of the reticle.
    const double minLog = std::log10(25.0);
    const double maxLog = std::log10(2000000.0);
    const double value = std::clamp((std::log10(std::max(25.0, flightSpeedMps)) - minLog) / (maxLog - minLog), 0.0, 1.0);
    const glm::dvec3 barBottom = center + right * 0.082 - up * 0.052;
    const glm::dvec3 barTop = barBottom + up * 0.078;
    vf::appendDebugRod(mesh, barBottom, barTop, 0.0026, {8.10F, 8.10F, 8.12F});
    vf::appendDebugRod(mesh, barBottom, barBottom + up * (0.078 * value), 0.0017, {8.12F, 8.78F, 9.0F});
}

} // namespace

int main() {
    try {
        vf::SdlPlatform platform{"Voxel Frontier — Planet / Atmosphere / Lighting Acceptance", 1600, 900};
        vf::VulkanRenderer renderer{platform.window()};

        vf::PlanetDefinition planet{};
        planet.seed = 0x71A9F20DULL;
        planet.radius = 6371000.0;
        planet.maxElevation = 8500.0;
        planet.atmosphereHeight = 100000.0;

        vf::CelestialSystem celestial;

        vf::CelestialBody sun{};
        sun.type = vf::CelestialBodyType::Star;
        sun.name = "Helion";
        sun.radiusMeters = 696340000.0;
        sun.massKg = 1.98847e30;
        sun.position = {};
        sun.spinAxis = safeNormalize({0.0, 1.0, 0.12});
        sun.spinRateRadPerSecond = 2.0 * kPi / (25.38 * 86400.0);
        sun.luminosityWatts = 3.828e26;
        const std::uint32_t sunId = celestial.addBody(sun);

        constexpr double asterOrbitRadius = 149597870700.0;
        vf::CelestialBody aster{};
        aster.type = vf::CelestialBodyType::Planet;
        aster.name = "Aster";
        aster.radiusMeters = planet.radius;
        aster.massKg = 5.9722e24;
        aster.gameplaySurfaceGravityMps2 = 9.80665;
        aster.gravityFalloffStartRadiusMeters = planet.radius + planet.atmosphereHeight;
        aster.gravityFalloffPower = 7.0;
        aster.gravityInfluenceRadiusMeters = planet.radius + 900000.0;
        aster.physicsBubbleRadiusMeters = planet.radius + 1300000.0;
        aster.position = {-asterOrbitRadius, 0.0, 0.0};
        aster.orbitParentId = sunId;
        aster.linearVelocity = {0.0, 0.0, -circularOrbitSpeed(sun.massKg, asterOrbitRadius)};
        aster.spinAxis = safeNormalize({0.0, 1.0, 0.0});
        aster.spinRateRadPerSecond = 2.0 * kPi / 86164.0905;
        aster.visibleAlbedo = {0.20, 0.42, 0.18};
        aster.atmosphere.enabled = true;
        aster.atmosphere.heightMeters = planet.atmosphereHeight;
        aster.atmosphere.surfacePressurePa = 101325.0;
        aster.atmosphere.surfaceTemperatureK = 288.15;
        aster.atmosphere.scaleHeightMeters = 8500.0;
        aster.atmosphere.lapseRateKPerM = 0.0065;
        aster.atmosphere.rayleighRgb = {0.16, 0.43, 1.00};
        aster.atmosphere.mieStrength = 0.08;
        aster.atmosphere.prevailingWind = {};
        aster.weather.windMultiplier = 0.0;
        aster.weather.stormIntensity = 0.0;
        const std::uint32_t asterId = celestial.addBody(aster);

        constexpr double cinderOrbitRadius = 227939200000.0;
        vf::CelestialBody cinder{};
        cinder.type = vf::CelestialBodyType::Planet;
        cinder.name = "Cinder";
        cinder.radiusMeters = 3389500.0;
        cinder.massKg = 6.4171e23;
        cinder.gameplaySurfaceGravityMps2 = 3.71;
        cinder.gravityFalloffStartRadiusMeters = cinder.radiusMeters + 70000.0;
        cinder.gravityFalloffPower = 7.0;
        cinder.gravityInfluenceRadiusMeters = cinder.radiusMeters + 550000.0;
        cinder.physicsBubbleRadiusMeters = cinder.radiusMeters + 800000.0;
        cinder.position = {0.0, 0.0, cinderOrbitRadius};
        cinder.orbitParentId = sunId;
        cinder.linearVelocity = {-circularOrbitSpeed(sun.massKg, cinderOrbitRadius), 0.0, 0.0};
        cinder.spinAxis = safeNormalize({0.08, 1.0, -0.04});
        cinder.spinRateRadPerSecond = 2.0 * kPi / 88642.7;
        cinder.visibleAlbedo = {0.62, 0.30, 0.22};
        const std::uint32_t cinderId = celestial.addBody(cinder);

        vf::PlanetCamera camera{planet, &celestial, asterId};
        const vf::CelestialBody* initialAster = celestial.body(asterId);
        if (initialAster == nullptr) throw std::runtime_error("Aster failed to initialize");

        const glm::dquat initialInverseAster = glm::conjugate(glm::normalize(initialAster->orientation));
        const glm::dvec3 initialCameraPlanet = initialInverseAster * (camera.position() - initialAster->position);
        const glm::dvec3 patchUp = safeNormalize(initialCameraPlanet);
        const glm::dvec3 patchEast = safeEast(patchUp);
        const glm::dvec3 patchNorth = safeNormalize(glm::cross(patchUp, patchEast), {0.0, 0.0, 1.0});
        const glm::dvec3 patchOriginPlanet = patchUp * vf::planetSurfaceRadius(planet, patchUp);

        const auto toSurfacePoint = [&](const glm::dvec3& planetPoint) {
            const glm::dvec3 delta = planetPoint - patchOriginPlanet;
            return glm::dvec3{
                glm::dot(delta, patchEast),
                glm::dot(delta, patchUp),
                glm::dot(delta, patchNorth),
            };
        };
        const auto toSurfaceVector = [&](const glm::dvec3& planetVector) {
            return glm::dvec3{
                glm::dot(planetVector, patchEast),
                glm::dot(planetVector, patchUp),
                glm::dot(planetVector, patchNorth),
            };
        };
        const auto toPlanetPoint = [&](const glm::dvec3& surfacePoint) {
            return patchOriginPlanet
                + patchEast * surfacePoint.x
                + patchUp * surfacePoint.y
                + patchNorth * surfacePoint.z;
        };
        const auto planetSurfaceAtOffset = [&](double eastMeters, double northMeters) {
            const glm::dvec3 direction = safeNormalize(
                patchUp
                    + patchEast * (eastMeters / planet.radius)
                    + patchNorth * (northMeters / planet.radius),
                patchUp);
            return direction * vf::planetSurfaceRadius(planet, direction);
        };

        vf::PlanetMesh staticTerrain{};
        constexpr std::uint32_t terrainResolution = 144U;
        constexpr double terrainHalfExtent = 12000.0;
        constexpr double proxyInsetMeters = 160.0;
        const std::uint32_t terrainStride = terrainResolution + 1U;
        staticTerrain.vertices.reserve(static_cast<std::size_t>(terrainStride) * terrainStride + 10000U);
        staticTerrain.indices.reserve(static_cast<std::size_t>(terrainResolution) * terrainResolution * 6U + 30000U);

        for (std::uint32_t y = 0; y <= terrainResolution; ++y) {
            const double fy = static_cast<double>(y) / static_cast<double>(terrainResolution);
            const double northMeters = -terrainHalfExtent + 2.0 * terrainHalfExtent * fy;
            for (std::uint32_t x = 0; x <= terrainResolution; ++x) {
                const double fx = static_cast<double>(x) / static_cast<double>(terrainResolution);
                const double eastMeters = -terrainHalfExtent + 2.0 * terrainHalfExtent * fx;
                const glm::dvec3 planetPoint = planetSurfaceAtOffset(eastMeters, northMeters);
                const glm::dvec3 direction = safeNormalize(planetPoint);
                glm::dvec3 surfacePosition = toSurfacePoint(planetPoint);
                const glm::dvec3 surfaceNormal = safeNormalize(toSurfaceVector(vf::planetSurfaceNormal(planet, direction)));
                const double edge = std::max(std::abs(eastMeters), std::abs(northMeters)) / terrainHalfExtent;
                const double blend = std::clamp((edge - 0.82) / 0.18, 0.0, 1.0);
                surfacePosition -= surfaceNormal * (proxyInsetMeters * blend);
                const double normalizedHeight = vf::planetHeight(planet, direction) / planet.maxElevation;

                vf::PlanetVertex vertex{};
                vertex.position = glm::vec3(surfacePosition);
                vertex.normal = glm::vec3(surfaceNormal);
                if (normalizedHeight < -0.15) vertex.color = {0.18F, 0.25F, 0.14F};
                else if (normalizedHeight < 0.20) vertex.color = {0.20F, 0.41F, 0.17F};
                else if (normalizedHeight < 0.58) vertex.color = {0.34F, 0.34F, 0.26F};
                else vertex.color = {0.62F, 0.64F, 0.61F};
                staticTerrain.vertices.push_back(vertex);
            }
        }
        for (std::uint32_t y = 0; y < terrainResolution; ++y) {
            for (std::uint32_t x = 0; x < terrainResolution; ++x) {
                const std::uint32_t i0 = y * terrainStride + x;
                const std::uint32_t i1 = i0 + 1U;
                const std::uint32_t i2 = i0 + terrainStride;
                const std::uint32_t i3 = i2 + 1U;
                staticTerrain.indices.insert(staticTerrain.indices.end(), {i0, i2, i1, i1, i2, i3});
            }
        }

        // Whole-planet far proxy: same procedural height function, only ~7k triangles. It is inset
        // slightly so the high-detail patch wins nearby, and the edge blends down to it smoothly.
        vf::PlanetMesh fullPlanetProxy = vf::buildPlanetSurface(planet, 24U);
        for (auto& vertex : fullPlanetProxy.vertices) {
            glm::dvec3 p = glm::dvec3(vertex.position);
            const double length = glm::length(p);
            if (length > proxyInsetMeters + 1.0) p *= (length - proxyInsetMeters) / length;
            vertex.position = glm::vec3(toSurfacePoint(p));
            vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
        }
        appendMesh(staticTerrain, fullPlanetProxy);

        // Blue atmospheric limb visible both from the ground and from orbit. Its current shell
        // shader is density-inspired but still cheaper than the final Bruneton/Hillaire LUT pass.
        vf::appendAtmosphereProxy(
            staticTerrain,
            toSurfacePoint(glm::dvec3{0.0}),
            planet.radius + planet.atmosphereHeight,
            22U,
            glm::vec3(aster.atmosphere.rayleighRgb),
            0.95F);

        renderer.uploadPlanetMesh(staticTerrain);

        vf::CelestialSystem localGravitySystem;
        vf::CelestialBody localGravityBody = aster;
        localGravityBody.position = toSurfacePoint(glm::dvec3{0.0});
        localGravityBody.linearVelocity = {};
        localGravityBody.orientation = glm::dquat{1.0, 0.0, 0.0, 0.0};
        localGravityBody.orbitParentId = 0U;
        localGravityBody.spinRateRadPerSecond = 0.0;
        localGravityBody.atmosphere.enabled = false;
        localGravityBody.weather.windMultiplier = 0.0;
        const std::uint32_t localGravityId = localGravitySystem.addBody(localGravityBody);

        vf::PlanetDefinition fallbackPlanet = planet;
        fallbackPlanet.radius = planet.radius - 2500.0;
        fallbackPlanet.maxElevation = 0.0;

        vf::PhysicsEnvironment environment{};
        environment.planet = fallbackPlanet;
        environment.surfaceGravity = 9.80665;
        environment.celestialSystem = &localGravitySystem;
        environment.primaryCelestialBodyId = localGravityId;
        environment.atmosphere.prevailingWind = {};
        environment.atmosphere.gustAmplitude = 0.0;
        environment.weather.windMultiplier = 0.0;
        environment.ocean.enabled = false;
        vf::PhysicsWorld physics{environment};
        vf::PhysicsInteraction interaction{physics};

        constexpr double tileSpacing = 4.0;
        constexpr int tileRadius = 5;
        for (int z = -tileRadius; z <= tileRadius; ++z) {
            for (int x = -tileRadius; x <= tileRadius; ++x) {
                const double eastMeters = static_cast<double>(x) * tileSpacing;
                const double northMeters = 5.0 + static_cast<double>(z) * tileSpacing;
                const glm::dvec3 planetPoint = planetSurfaceAtOffset(eastMeters, northMeters);
                const glm::dvec3 direction = safeNormalize(planetPoint);
                const glm::dvec3 normal = safeNormalize(toSurfaceVector(vf::planetSurfaceNormal(planet, direction)));
                glm::dvec3 tileX = glm::dvec3{1.0, 0.0, 0.0};
                tileX = safeNormalize(tileX - normal * glm::dot(tileX, normal), {1.0, 0.0, 0.0});
                const glm::dvec3 tileZ = safeNormalize(glm::cross(tileX, normal), {0.0, 0.0, 1.0});
                const glm::dmat3 basis{tileX, normal, tileZ};

                vf::RigidBodyDesc tile{};
                tile.motionType = vf::MotionType::Static;
                tile.mass = 0.0;
                tile.position = toSurfacePoint(planetPoint) - normal * 0.24;
                tile.orientation = glm::normalize(glm::quat_cast(basis));
                tile.collisionShape = vf::CollisionShape::box({2.20, 0.28, 2.20});
                tile.aerodynamics.referenceArea = 0.0;
                (void)physics.createRigidBody(tile);
            }
        }

        const glm::dvec3 pickupGroundPlanet = planetSurfaceAtOffset(0.0, 4.0);
        const glm::dvec3 pickupNormal = safeNormalize(toSurfaceVector(
            vf::planetSurfaceNormal(planet, safeNormalize(pickupGroundPlanet))));
        glm::dvec3 pickupX = safeNormalize(glm::dvec3{1.0, 0.0, 0.0} - pickupNormal * pickupNormal.x);
        const glm::dvec3 pickupZ = safeNormalize(glm::cross(pickupX, pickupNormal), {0.0, 0.0, 1.0});
        const glm::dquat pickupOrientation = glm::normalize(glm::quat_cast(glm::dmat3{pickupX, pickupNormal, pickupZ}));

        struct PropSpec {
            double x;
            double z;
            glm::dvec3 half;
            double mass;
            double friction;
            glm::vec3 encodedColor;
        };
        const std::array<PropSpec, 5> specs{{
            {0.0, 4.0, {0.60, 0.60, 0.60}, 12.0, 0.86, {0.34F, 0.37F, 0.40F}},
            {-1.7, 5.2, {0.70, 0.45, 0.50}, 7.0, 0.80, {1.50F, 1.24F, 1.08F}},
            {1.7, 5.2, {0.62, 0.48, 0.52}, 18.0, 0.58, {2.56F, 2.59F, 2.64F}},
            {-1.0, 7.0, {0.48, 0.72, 0.48}, 9.0, 0.46, {4.08F, 4.36F, 4.98F}},
            {1.0, 7.0, {0.48, 0.72, 0.48}, 9.0, 0.46, {4.98F, 4.55F, 4.08F}},
        }};

        std::vector<PropVisual> props;
        props.reserve(specs.size());
        for (const auto& spec : specs) {
            const glm::dvec3 groundPlanet = planetSurfaceAtOffset(spec.x, spec.z);
            const glm::dvec3 normal = safeNormalize(toSurfaceVector(
                vf::planetSurfaceNormal(planet, safeNormalize(groundPlanet))));
            const glm::dvec3 position = toSurfacePoint(groundPlanet) + normal * (spec.half.y + 0.035);

            vf::RigidBodyDesc desc{};
            desc.mass = spec.mass;
            desc.position = position;
            desc.orientation = pickupOrientation;
            desc.linearVelocity = {};
            desc.angularVelocity = {};
            desc.collisionShape = vf::CollisionShape::box(spec.half);
            desc.inertiaDiagonal = boxInertia(desc.mass, spec.half);
            desc.material.friction = spec.friction;
            desc.material.restitution = 0.0;
            desc.material.rollingResistance = 0.12;
            desc.linearDamping = 0.09;
            desc.angularDamping = 0.16;
            desc.aerodynamics.referenceArea = 0.0;
            desc.buoyancy.enabled = false;
            props.push_back({physics.createRigidBody(desc), spec.half, spec.encodedColor});
        }

        std::cout << "Voxel Frontier real-scale planet / atmosphere acceptance build\n";
        std::cout << "Aster: 6371 km | atmosphere: 100 km | wind OFF\n";
        std::cout << "Double Space: flight | wheel: flight speed | RMB pickup/drop | LMB throw\n";

        using Clock = std::chrono::steady_clock;
        auto previous = Clock::now();
        double diagnosticsTime = 0.0;
        std::uint64_t diagnosticsFrames = 0;

        while (platform.pumpEvents()) {
            const auto now = Clock::now();
            double dt = std::chrono::duration<double>(now - previous).count();
            previous = now;
            dt = std::clamp(dt, 0.0, 0.05);

            celestial.step(dt);
            const vf::CelestialBody* currentAster = celestial.body(asterId);
            const vf::CelestialBody* currentCinder = celestial.body(cinderId);
            const vf::CelestialBody* currentSun = celestial.body(sunId);
            if (currentAster == nullptr || currentSun == nullptr) continue;

            if (platform.consumeResize()) renderer.requestResize();

            const auto& input = platform.input();
            vf::PlanetMovementInput movement{};
            movement.forward = (input.forward ? 1.0 : 0.0) - (input.backward ? 1.0 : 0.0);
            // Hardware acceptance showed A/D reversed after the camera-yaw correction. Keep the
            // camera basis untouched and correct only the semantic input sign here.
            movement.right = (input.left ? 1.0 : 0.0) - (input.right ? 1.0 : 0.0);
            movement.vertical = (input.ascend ? 1.0 : 0.0) - (input.descend ? 1.0 : 0.0);
            movement.mouseDx = input.mouseCaptured ? static_cast<double>(input.mouseDx) : 0.0;
            movement.mouseDy = input.mouseCaptured ? static_cast<double>(input.mouseDy) : 0.0;
            movement.flightSpeedSteps = input.flightSpeedSteps;
            movement.sprint = input.sprint;
            movement.toggleFlight = input.toggleFlight;
            camera.update(movement, dt);

            const glm::dquat inverseAster = glm::conjugate(glm::normalize(currentAster->orientation));
            const glm::dvec3 cameraPlanet = inverseAster * (camera.position() - currentAster->position);
            const glm::dvec3 cameraSurface = toSurfacePoint(cameraPlanet);
            const glm::dvec3 forwardSurface = safeNormalize(toSurfaceVector(inverseAster * camera.forwardDirection()), {0.0, 0.0, 1.0});
            const glm::dvec3 upSurface = safeNormalize(toSurfaceVector(inverseAster * camera.up()), {0.0, 1.0, 0.0});

            if (camera.physicsFrameBodyId() == asterId) {
                vf::PhysicsInteractionInput interactionInput{};
                interactionInput.rightPressed = input.rightPressed;
                interactionInput.leftPressed = input.leftPressed;
                interaction.update(cameraSurface, forwardSurface, interactionInput, dt);
            } else if (interaction.holding()) {
                interaction.drop();
            }

            physics.advance(dt);

            const glm::dvec3 sunWorldDirection = safeNormalize(currentSun->position - camera.position());
            const glm::dvec3 sunPlanetDirection = inverseAster * sunWorldDirection;
            const glm::dvec3 sunSurfaceDirection = safeNormalize(toSurfaceVector(sunPlanetDirection), {0.3, 0.8, 0.2});

            vf::PlanetMesh dynamicMesh{};

            for (const auto& prop : props) {
                const vf::RigidBody* body = physics.body(prop.bodyId);
                if (body == nullptr) continue;
                const glm::dvec3 bodyPlanet = toPlanetPoint(body->position);
                const glm::dvec3 direction = safeNormalize(bodyPlanet);
                const glm::dvec3 groundPlanet = direction * vf::planetSurfaceRadius(planet, direction);
                const glm::dvec3 ground = toSurfacePoint(groundPlanet);
                const glm::dvec3 normal = safeNormalize(toSurfaceVector(vf::planetSurfaceNormal(planet, direction)));
                const bool glass = std::min({prop.encodedColor.x, prop.encodedColor.y, prop.encodedColor.z}) > 3.5F;
                const glm::vec3 projectedColor = glass
                    ? glm::clamp((prop.encodedColor - glm::vec3{4.0F}) * 0.42F + glm::vec3{0.03F}, glm::vec3{0.0F}, glm::vec3{0.48F})
                    : glm::vec3{0.012F, 0.013F, 0.016F};
                appendDirectionalBoxShadow(
                    dynamicMesh,
                    body->position,
                    body->orientation,
                    prop.halfExtents,
                    ground,
                    normal,
                    -sunSurfaceDirection,
                    projectedColor);
            }

            for (const auto& prop : props) {
                const vf::RigidBody* body = physics.body(prop.bodyId);
                if (body == nullptr) continue;
                vf::appendDebugBox(
                    dynamicMesh,
                    body->position,
                    body->orientation,
                    prop.halfExtents,
                    prop.encodedColor);
            }

            const double physicalSunDistance = glm::length(currentSun->position - camera.position());
            const double angularSunRadius = std::asin(std::clamp(
                currentSun->radiusMeters / std::max(physicalSunDistance, currentSun->radiusMeters), 0.0, 0.30));
            constexpr double sunVisualDistance = 20000000.0;
            const double sunVisualRadius = std::max(12000.0, std::tan(angularSunRadius) * sunVisualDistance);
            vf::appendDebugSphere(
                dynamicMesh,
                cameraSurface + sunSurfaceDirection * sunVisualDistance,
                sunVisualRadius,
                {9.0F, 8.82F, 8.48F},
                12U,
                20U);

            if (currentCinder != nullptr) {
                const glm::dvec3 cinderWorldDirection = safeNormalize(currentCinder->position - camera.position());
                const glm::dvec3 cinderSurfaceDirection = safeNormalize(toSurfaceVector(inverseAster * cinderWorldDirection));
                const double physicalDistance = glm::length(currentCinder->position - camera.position());
                const double angularRadius = std::asin(std::clamp(
                    currentCinder->radiusMeters / std::max(physicalDistance, currentCinder->radiusMeters), 0.0, 0.20));
                constexpr double visualDistance = 25000000.0;
                const double visualRadius = std::max(1800.0, std::tan(angularRadius) * visualDistance);
                vf::appendDebugSphere(dynamicMesh, cameraSurface + cinderSurfaceDirection * visualDistance, visualRadius, {0.62F, 0.30F, 0.22F}, 7U, 12U);
            }

            // Dense but cheap star catalogue: metadata-only directions rendered as tiny low-poly
            // proxies. No collision, terrain, atmosphere or per-star simulation is instantiated.
            for (int i = 0; i < 320; ++i) {
                const double a = 0.754877666 * static_cast<double>(i + 1);
                const double b = 1.324717957 * static_cast<double>(i + 3);
                glm::dvec3 inertialDirection = safeNormalize({
                    std::sin(a * 4.7 + b),
                    std::sin(b * 3.1 - a * 0.7) * (0.58 + 0.42 * std::sin(a)),
                    std::cos(a * 2.9 + b * 1.7),
                });
                const glm::dvec3 starSurfaceDirection = safeNormalize(toSurfaceVector(inverseAster * inertialDirection));
                const double size = 2600.0 + static_cast<double>((i * 17) % 11) * 310.0;
                const glm::vec3 tint = (i % 9 == 0)
                    ? glm::vec3{9.0F, 8.78F, 8.55F}
                    : ((i % 13 == 0) ? glm::vec3{8.62F, 8.78F, 9.0F} : glm::vec3{8.92F, 8.94F, 9.0F});
                vf::appendDebugSphere(
                    dynamicMesh,
                    cameraSurface + starSurfaceDirection * 36000000.0,
                    size,
                    tint,
                    3U,
                    6U);
            }

            appendHud(dynamicMesh, cameraSurface, forwardSurface, upSurface, camera.flightSpeedMps());
            renderer.setDynamicMesh(dynamicMesh);

            const auto [width, height] = platform.drawableSize();
            const float aspect = height > 0
                ? static_cast<float>(width) / static_cast<float>(height)
                : 16.0F / 9.0F;
            const glm::mat4 localViewProjection = makeLocalViewProjection(forwardSurface, upSurface, aspect);

            const auto environmentSample = celestial.sampleEnvironment(camera.position());
            const double densityRatio = std::clamp(environmentSample.densityKgPerM3 / 1.225, 0.0, 1.4);
            const double mu = std::clamp(glm::dot(forwardSurface, sunSurfaceDirection), -1.0, 1.0);
            const double rayleighPhase = 3.0 * (1.0 + mu * mu) / (16.0 * kPi);
            constexpr double mieG = 0.76;
            const double mieDen = std::pow(std::max(0.02, 1.0 + mieG * mieG - 2.0 * mieG * mu), 1.5);
            const double miePhase = (1.0 - mieG * mieG) / (4.0 * kPi * mieDen);
            const glm::dvec3 rayleighCoeff = aster.atmosphere.rayleighRgb * densityRatio;
            const glm::dvec3 mieCoeff{aster.atmosphere.mieStrength * densityRatio};
            const glm::dvec3 skyLinear = rayleighCoeff * rayleighPhase * 0.82 + mieCoeff * miePhase * 0.18;
            const glm::vec3 sky = glm::vec3(glm::clamp(skyLinear, glm::dvec3{0.0}, glm::dvec3{1.0}));

            // Atmospheric attenuation of direct sunlight: long horizon paths remove blue first.
            const double sunElevation = glm::dot(camera.up(), sunWorldDirection);
            const double airMass = densityRatio / std::max(0.055, sunElevation + 0.12);
            const glm::dvec3 extinction = glm::dvec3{0.14, 0.32, 0.72} * std::max(0.0, airMass);
            const glm::vec3 sunColor = glm::vec3(glm::exp(-extinction));
            const double irradiance = currentSun->luminosityWatts
                / (4.0 * kPi * std::max(1.0, physicalSunDistance * physicalSunDistance));
            const float sunIntensity = static_cast<float>(2.35 * std::clamp(irradiance / 1361.0, 0.0, 3.0));

            renderer.drawFrame(
                sky,
                localViewProjection,
                cameraSurface,
                glm::vec3(sunSurfaceDirection),
                sunColor,
                sunIntensity,
                glm::dquat{1.0, 0.0, 0.0, 0.0});

            diagnosticsTime += dt;
            ++diagnosticsFrames;
            if (diagnosticsTime >= 0.5) {
                std::size_t sleeping = 0;
                double maxLinear = 0.0;
                double maxAngular = 0.0;
                for (const auto& prop : props) {
                    const vf::RigidBody* body = physics.body(prop.bodyId);
                    if (body == nullptr) continue;
                    if (body->sleeping) ++sleeping;
                    maxLinear = std::max(maxLinear, glm::length(body->linearVelocity));
                    maxAngular = std::max(maxAngular, glm::length(body->angularVelocity));
                }

                const double fps = static_cast<double>(diagnosticsFrames) / diagnosticsTime;
                std::ostringstream title;
                title << "Voxel Frontier | "
                      << (camera.flightMode() ? "FLIGHT" : (camera.grounded() ? "GROUNDED" : "AIRBORNE"))
                      << " | SPEED " << std::fixed << std::setprecision(0) << camera.flightSpeedMps() << " m/s"
                      << " | ALT " << camera.altitude() / 1000.0 << " km"
                      << " | WIND OFF"
                      << " | sleeping " << sleeping << '/' << props.size()
                      << " | vMax " << std::setprecision(3) << maxLinear
                      << " | wMax " << maxAngular
                      << " | " << (interaction.holding() ? "HOLDING" : "HANDS FREE")
                      << " | FPS " << std::setprecision(0) << fps;
                platform.setWindowTitle(title.str());
                diagnosticsTime = 0.0;
                diagnosticsFrames = 0;
            }
        }

        return 0;
    } catch (const std::exception& exception) {
        std::cerr << "Fatal error: " << exception.what() << '\n';
        return 1;
    }
}
