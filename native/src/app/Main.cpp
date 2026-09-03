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
    double shadowRadius{0.7};
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
    glm::mat4 projection = glm::perspectiveRH_ZO(glm::radians(68.0F), aspect, 0.05F, 2000000.0F);
    projection[1][1] *= -1.0F;
    return projection * view;
}

} // namespace

int main() {
    try {
        vf::SdlPlatform platform{"Voxel Frontier — Surface Physics + Material Acceptance", 1600, 900};
        vf::VulkanRenderer renderer{platform.window()};

        // ---------------------------------------------------------------------
        // Real-scale authored celestial bodies. Physics near the player does NOT use these huge
        // inertial coordinates directly; they remain the authoritative universe/orbit layer.
        // ---------------------------------------------------------------------
        vf::PlanetDefinition planet{};
        planet.seed = 0x71A9F20DULL;
        planet.radius = 6371000.0;       // Earth-class radius, metres.
        planet.maxElevation = 8500.0;    // Earth-class relief scale.
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
        // Start at -X so PlanetCamera's authored +X-biased spawn patch is on the daylight
        // hemisphere facing Helion at the origin. Circular-orbit velocity sign follows this pose.
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
        // Acceptance scene deliberately has no weather wind. Wind will be re-enabled only after
        // resting contact is verified on hardware.
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

        // ---------------------------------------------------------------------
        // Render terrain in the same surface-local frame used by nearby gameplay. Double precision
        // is kept until after the huge 6,371 km planet-center offset has been removed.
        // ---------------------------------------------------------------------
        vf::PlanetMesh staticTerrain{};
        constexpr std::uint32_t terrainResolution = 144U;
        constexpr double terrainHalfExtent = 12000.0;
        const std::uint32_t terrainStride = terrainResolution + 1U;
        staticTerrain.vertices.reserve(static_cast<std::size_t>(terrainStride) * terrainStride);
        staticTerrain.indices.reserve(static_cast<std::size_t>(terrainResolution) * terrainResolution * 6U);

        for (std::uint32_t y = 0; y <= terrainResolution; ++y) {
            const double fy = static_cast<double>(y) / static_cast<double>(terrainResolution);
            const double northMeters = -terrainHalfExtent + 2.0 * terrainHalfExtent * fy;
            for (std::uint32_t x = 0; x <= terrainResolution; ++x) {
                const double fx = static_cast<double>(x) / static_cast<double>(terrainResolution);
                const double eastMeters = -terrainHalfExtent + 2.0 * terrainHalfExtent * fx;
                const glm::dvec3 planetPoint = planetSurfaceAtOffset(eastMeters, northMeters);
                const glm::dvec3 direction = safeNormalize(planetPoint);
                const glm::dvec3 surfacePosition = toSurfacePoint(planetPoint);
                const glm::dvec3 surfaceNormal = safeNormalize(toSurfaceVector(vf::planetSurfaceNormal(planet, direction)));
                const double normalizedHeight = vf::planetHeight(planet, direction) / planet.maxElevation;

                vf::PlanetVertex vertex{};
                vertex.position = glm::vec3(surfacePosition);
                vertex.normal = glm::vec3(surfaceNormal);
                if (normalizedHeight < -0.15) vertex.color = {0.18F, 0.25F, 0.14F};
                else if (normalizedHeight < 0.20) vertex.color = {0.20F, 0.41F, 0.17F};
                else if (normalizedHeight < 0.58) vertex.color = {0.34F, 0.34F, 0.26F};
                else vertex.color = {0.62F, 0.64F, 0.61F};
                vertex.material = {0.0F, 0.96F, 0.0F, 0.0F};
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
        renderer.uploadPlanetMesh(staticTerrain);

        // ---------------------------------------------------------------------
        // Surface PhysicsSystem: origin is the player's local terrain patch, not the planet center.
        // This is the Jolt-recommended space-simulation architecture: low coordinates, low speeds,
        // static planet in the local solver, inertial orbit/spin outside the solver.
        // ---------------------------------------------------------------------
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
        // The old analytic radial planet contact remains far below the real terrain. Nearby ground
        // collision is provided by static terrain-chunk tiles and therefore uses the existing
        // persistent multi-point body contact manifold / warm-start solver.
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

        // Real terrain collision patch: overlapping static boxes follow the actual procedural
        // height and normal. This makes slopes physically slopes instead of using a radial normal.
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

        // ---------------------------------------------------------------------
        // Material lab. Encoded colors feed the current zero-descriptor PBR preview shader:
        // stone, wood, steel, blue glass, amber glass. Every object is a real dynamic body.
        // ---------------------------------------------------------------------
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
            {0.0, 4.0, {0.60, 0.60, 0.60}, 12.0, 0.86, {0.34F, 0.37F, 0.40F}},             // stone
            {-1.7, 5.2, {0.70, 0.45, 0.50}, 7.0, 0.80, {1.50F, 1.24F, 1.08F}},            // wood (+1)
            {1.7, 5.2, {0.62, 0.48, 0.52}, 18.0, 0.58, {2.56F, 2.59F, 2.64F}},            // steel (+2)
            {-1.0, 7.0, {0.48, 0.72, 0.48}, 9.0, 0.46, {4.10F, 4.42F, 4.95F}},            // blue glass (+4)
            {1.0, 7.0, {0.48, 0.72, 0.48}, 9.0, 0.46, {4.96F, 4.52F, 4.10F}},             // amber glass (+4)
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
            props.push_back({physics.createRigidBody(desc), spec.half, spec.encodedColor, std::max(spec.half.x, spec.half.z)});
        }

        std::cout << "Voxel Frontier real-scale planet acceptance build\n";
        std::cout << "Aster radius: 6371 km | Helion radius: 696340 km | local physics near origin\n";
        std::cout << "Wind: OFF for stability acceptance\n";
        std::cout << "Double Space: creative flight | Right click: pickup/drop | Left click: throw\n";
        std::cout << "Materials: stone / wood / steel / blue glass / amber glass\n";

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
            movement.right = (input.right ? 1.0 : 0.0) - (input.left ? 1.0 : 0.0);
            movement.vertical = (input.ascend ? 1.0 : 0.0) - (input.descend ? 1.0 : 0.0);
            movement.mouseDx = input.mouseCaptured ? static_cast<double>(input.mouseDx) : 0.0;
            movement.mouseDy = input.mouseCaptured ? static_cast<double>(input.mouseDy) : 0.0;
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

            // Contact shadows: exact directional projection onto the local procedural surface.
            const auto appendPropShadow = [&](const vf::RigidBody& body, double radius) {
                const glm::dvec3 bodyPlanet = toPlanetPoint(body.position);
                const glm::dvec3 direction = safeNormalize(bodyPlanet);
                const glm::dvec3 groundPlanet = direction * vf::planetSurfaceRadius(planet, direction);
                const glm::dvec3 ground = toSurfacePoint(groundPlanet);
                const glm::dvec3 normal = safeNormalize(toSurfaceVector(vf::planetSurfaceNormal(planet, direction)));
                const glm::dvec3 ray = -sunSurfaceDirection;
                const double denominator = glm::dot(ray, normal);
                if (denominator >= -0.04) return;
                const double t = glm::dot(ground - body.position, normal) / denominator;
                if (t < 0.0 || t > 40.0) return;
                const glm::dvec3 center = body.position + ray * t + normal * 0.025;
                const double stretch = std::clamp(1.0 / std::max(0.20, -denominator), 1.0, 3.5);
                vf::appendDebugDisc(dynamicMesh, center, normal, radius * stretch, radius * 0.82, {0.008F, 0.009F, 0.011F}, 20U);
            };

            for (const auto& prop : props) {
                const vf::RigidBody* body = physics.body(prop.bodyId);
                if (body == nullptr) continue;
                appendPropShadow(*body, prop.shadowRadius);
            }

            // Player shadow gives immediate confirmation that the sun is a spatial light source.
            {
                const glm::dvec3 direction = safeNormalize(cameraPlanet);
                const glm::dvec3 groundPlanet = direction * vf::planetSurfaceRadius(planet, direction);
                const glm::dvec3 ground = toSurfacePoint(groundPlanet);
                const glm::dvec3 normal = safeNormalize(toSurfaceVector(vf::planetSurfaceNormal(planet, direction)));
                const glm::dvec3 ray = -sunSurfaceDirection;
                const double denominator = glm::dot(ray, normal);
                if (denominator < -0.04) {
                    const double t = glm::dot(ground - cameraSurface, normal) / denominator;
                    if (t >= 0.0 && t < 20.0) {
                        vf::appendDebugDisc(dynamicMesh, cameraSurface + ray * t + normal * 0.026, normal, 0.42, 0.30, {0.006F, 0.007F, 0.009F}, 18U);
                    }
                }
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

            // Helion is a real celestial body in the inertial simulation. For rasterization we
            // place a proxy at a finite local distance while preserving its real angular diameter.
            const double physicalSunDistance = glm::length(currentSun->position - camera.position());
            const double angularSunRadius = std::asin(std::clamp(currentSun->radiusMeters / std::max(physicalSunDistance, currentSun->radiusMeters), 0.0, 0.30));
            constexpr double sunVisualDistance = 500000.0;
            const double sunVisualRadius = std::max(350.0, std::tan(angularSunRadius) * sunVisualDistance);
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
                const double angularRadius = std::asin(std::clamp(currentCinder->radiusMeters / std::max(physicalDistance, currentCinder->radiusMeters), 0.0, 0.20));
                constexpr double visualDistance = 720000.0;
                const double visualRadius = std::max(55.0, std::tan(angularRadius) * visualDistance);
                vf::appendDebugSphere(dynamicMesh, cameraSurface + cinderSurfaceDirection * visualDistance, visualRadius, {0.62F, 0.30F, 0.22F}, 7U, 12U);
            }

            // Sparse star catalogue visualization: dozens of proxies, no world geometry or physics.
            for (int i = 0; i < 48; ++i) {
                const double a = 0.754877666 * static_cast<double>(i + 1);
                const double b = 1.324717957 * static_cast<double>(i + 3);
                const glm::dvec3 inertialDirection = safeNormalize({
                    std::sin(a * 4.7 + b),
                    std::sin(b * 3.1 - a * 0.7),
                    std::cos(a * 2.9 + b * 1.7),
                });
                const glm::dvec3 starSurfaceDirection = safeNormalize(toSurfaceVector(inverseAster * inertialDirection));
                vf::appendDebugSphere(
                    dynamicMesh,
                    cameraSurface + starSurfaceDirection * 900000.0,
                    38.0 + static_cast<double>(i % 5) * 9.0,
                    {8.88F, 8.91F, 9.0F},
                    4U,
                    7U);
            }

            renderer.setDynamicMesh(dynamicMesh);

            const auto [width, height] = platform.drawableSize();
            const float aspect = height > 0
                ? static_cast<float>(width) / static_cast<float>(height)
                : 16.0F / 9.0F;
            const glm::mat4 localViewProjection = makeLocalViewProjection(forwardSurface, upSurface, aspect);

            const auto environmentSample = celestial.sampleEnvironment(camera.position());
            const double sunElevation = glm::dot(camera.up(), sunWorldDirection);
            glm::vec3 sky{0.0F};
            if (environmentSample.pressurePa > 0.0) {
                const double pressureRatio = std::clamp(environmentSample.pressurePa / 101325.0, 0.0, 1.0);
                const double daylight = std::clamp((sunElevation + 0.08) / 0.36, 0.0, 1.0);
                const double twilight = std::clamp(1.0 - std::abs(sunElevation + 0.06) / 0.20, 0.0, 1.0);
                sky = glm::vec3(glm::clamp(
                    glm::dvec3{0.05, 0.18, 0.52} * pressureRatio * daylight
                        + glm::dvec3{0.42, 0.13, 0.035} * pressureRatio * twilight,
                    glm::dvec3{0.0},
                    glm::dvec3{1.0}));
            }

            const glm::vec3 sunColor{1.0F, 0.92F, 0.78F};
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
                      << " | WIND OFF"
                      << " | sleeping " << sleeping << '/' << props.size()
                      << " | vMax " << std::fixed << std::setprecision(3) << maxLinear
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
