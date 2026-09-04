#include "vf/gameplay/PhysicsInteraction.hpp"
#include "vf/physics/PhysicsWorld.hpp"
#include "vf/platform/SdlPlatform.hpp"
#include "vf/player/CharacterController.hpp"
#include "vf/player/PlanetCamera.hpp"
#include "vf/render/PhysicsDebugMesh.hpp"
#include "vf/render/VulkanRenderer.hpp"
#include "vf/world/CelestialPhysicsFrame.hpp"
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
    return std::sqrt(vf::CelestialSystem::kGravitationalConstant * parentMassKg / std::max(1.0, radiusMeters));
}

[[nodiscard]] glm::dvec3 boxInertia(double mass, const glm::dvec3& halfExtents) {
    return {
        mass * (halfExtents.y * halfExtents.y + halfExtents.z * halfExtents.z) / 3.0,
        mass * (halfExtents.x * halfExtents.x + halfExtents.z * halfExtents.z) / 3.0,
        mass * (halfExtents.x * halfExtents.x + halfExtents.y * halfExtents.y) / 3.0,
    };
}

void appendMesh(vf::PlanetMesh& destination, const vf::PlanetMesh& source) {
    const std::uint32_t base = static_cast<std::uint32_t>(destination.vertices.size());
    destination.vertices.insert(destination.vertices.end(), source.vertices.begin(), source.vertices.end());
    destination.indices.reserve(destination.indices.size() + source.indices.size());
    for (const std::uint32_t index : source.indices) destination.indices.push_back(base + index);
}

struct PropVisual {
    std::uint32_t bodyId{};
    glm::dvec3 halfExtents{};
    glm::vec3 color{};
    glm::vec4 material{};
};

[[nodiscard]] glm::mat4 makeReverseZViewProjection(
    const glm::dvec3& forward,
    const glm::dvec3& up,
    float aspect) {
    aspect = std::max(aspect, 0.1F);
    const glm::mat4 view = glm::lookAtRH(
        glm::vec3{0.0F},
        glm::vec3(safeNormalize(forward, {0.0, 0.0, -1.0})),
        glm::vec3(safeNormalize(up)));

    constexpr float nearPlane = 0.05F;
    const float f = 1.0F / std::tan(glm::radians(68.0F) * 0.5F);
    glm::mat4 projection{0.0F};
    projection[0][0] = f / aspect;
    projection[1][1] = -f;
    projection[2][3] = -1.0F;
    projection[3][2] = nearPlane;
    return projection * view;
}

} // namespace

int main() {
    try {
        vf::SdlPlatform platform{"Voxel Frontier — Physical Planet R2 Character Controller", 1600, 900};
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
        aster.spinAxis = {0.0, 1.0, 0.0};
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
        cinder.gravityInfluenceRadiusMeters = cinder.radiusMeters + 550000.0;
        cinder.physicsBubbleRadiusMeters = cinder.radiusMeters + 800000.0;
        cinder.position = {0.0, 0.0, cinderOrbitRadius};
        cinder.orbitParentId = sunId;
        cinder.linearVelocity = {-circularOrbitSpeed(sun.massKg, cinderOrbitRadius), 0.0, 0.0};
        cinder.visibleAlbedo = {0.62, 0.30, 0.22};
        const std::uint32_t cinderId = celestial.addBody(cinder);

        vf::PlanetCamera camera{planet, &celestial, asterId};
        const vf::CelestialBody* initialAster = celestial.body(asterId);
        if (initialAster == nullptr) throw std::runtime_error("Aster failed to initialize");
        vf::CelestialPhysicsFrame asterFrame{asterId};

        const glm::dquat initialInverseAster = glm::conjugate(glm::normalize(initialAster->orientation));
        const glm::dvec3 initialCameraPlanet = initialInverseAster * (camera.position() - initialAster->position);
        const glm::dvec3 patchUp = safeNormalize(initialCameraPlanet);
        const glm::dvec3 patchEast = safeEast(patchUp);
        const glm::dvec3 patchZ = safeNormalize(glm::cross(patchEast, patchUp), {0.0, 0.0, -1.0});
        const glm::dvec3 patchOriginPlanet = patchUp * vf::planetSurfaceRadius(planet, patchUp);

        const auto toSurfacePoint = [&](const glm::dvec3& planetPoint) {
            const glm::dvec3 delta = planetPoint - patchOriginPlanet;
            return glm::dvec3{
                glm::dot(delta, patchEast),
                glm::dot(delta, patchUp),
                glm::dot(delta, patchZ),
            };
        };
        const auto toSurfaceVector = [&](const glm::dvec3& planetVector) {
            return glm::dvec3{
                glm::dot(planetVector, patchEast),
                glm::dot(planetVector, patchUp),
                glm::dot(planetVector, patchZ),
            };
        };
        const glm::dmat3 surfaceFromPlanet{
            toSurfaceVector({1.0, 0.0, 0.0}),
            toSurfaceVector({0.0, 1.0, 0.0}),
            toSurfaceVector({0.0, 0.0, 1.0}),
        };
        const glm::dquat surfaceFromPlanetRotation = glm::normalize(glm::quat_cast(surfaceFromPlanet));

        const auto planetSurfaceAtOffset = [&](double eastMeters, double zMeters) {
            const glm::dvec3 direction = safeNormalize(
                patchUp + patchEast * (eastMeters / planet.radius) + patchZ * (zMeters / planet.radius), patchUp);
            return direction * vf::planetSurfaceRadius(planet, direction);
        };

        glm::dvec3 lodCenterDirection = patchUp;
        auto buildTerrainLod = [&](const glm::dvec3& centerDirection) {
            vf::PlanetMesh mesh{};
            const glm::dvec3 centerUp = safeNormalize(centerDirection, patchUp);
            const glm::dvec3 centerEast = safeEast(centerUp);
            const glm::dvec3 centerNorth = safeNormalize(glm::cross(centerUp, centerEast), patchZ);

            struct Ring { double half; double inner; std::uint32_t resolution; double baseInset; double edgeInset; };
            const std::array<Ring, 4> rings{{
                {20000.0, 0.0, 200U, 0.0, 1.5},
                {180000.0, 18000.0, 180U, 1.0, 8.0},
                {900000.0, 160000.0, 144U, 7.0, 40.0},
                {2500000.0, 820000.0, 96U, 32.0, 150.0},
            }};

            for (const Ring& ring : rings) {
                const std::uint32_t stride = ring.resolution + 1U;
                const std::uint32_t base = static_cast<std::uint32_t>(mesh.vertices.size());
                for (std::uint32_t y = 0; y <= ring.resolution; ++y) {
                    const double fy = static_cast<double>(y) / static_cast<double>(ring.resolution);
                    const double northMeters = -ring.half + 2.0 * ring.half * fy;
                    for (std::uint32_t x = 0; x <= ring.resolution; ++x) {
                        const double fx = static_cast<double>(x) / static_cast<double>(ring.resolution);
                        const double eastMeters = -ring.half + 2.0 * ring.half * fx;
                        const glm::dvec3 direction = safeNormalize(
                            centerUp + centerEast * (eastMeters / planet.radius) + centerNorth * (northMeters / planet.radius), centerUp);
                        glm::dvec3 worldPoint = direction * vf::planetSurfaceRadius(planet, direction);
                        const glm::dvec3 normalPlanet = vf::planetSurfaceNormal(planet, direction);
                        const double edge = std::max(std::abs(eastMeters), std::abs(northMeters)) / ring.half;
                        const double edgeBlend = std::clamp((edge - 0.88) / 0.12, 0.0, 1.0);
                        worldPoint -= normalPlanet * (ring.baseInset + edgeBlend * ring.edgeInset);
                        const double normalizedHeight = vf::planetHeight(planet, direction) / planet.maxElevation;
                        vf::PlanetVertex vertex{};
                        vertex.position = glm::vec3(toSurfacePoint(worldPoint));
                        vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(normalPlanet)));
                        if (normalizedHeight < -0.15) vertex.color = {0.14F, 0.25F, 0.13F};
                        else if (normalizedHeight < 0.20) vertex.color = {0.18F, 0.39F, 0.16F};
                        else if (normalizedHeight < 0.58) vertex.color = {0.34F, 0.33F, 0.25F};
                        else vertex.color = {0.61F, 0.63F, 0.60F};
                        vertex.material = {0.0F, normalizedHeight > 0.55 ? 0.86F : 0.94F, 0.0F, 0.0F};
                        mesh.vertices.push_back(vertex);
                    }
                }

                for (std::uint32_t y = 0; y < ring.resolution; ++y) {
                    const double cy = -ring.half + 2.0 * ring.half * (static_cast<double>(y) + 0.5) / ring.resolution;
                    for (std::uint32_t x = 0; x < ring.resolution; ++x) {
                        const double cx = -ring.half + 2.0 * ring.half * (static_cast<double>(x) + 0.5) / ring.resolution;
                        if (ring.inner > 0.0 && std::max(std::abs(cx), std::abs(cy)) < ring.inner) continue;
                        const std::uint32_t i0 = base + y * stride + x;
                        const std::uint32_t i1 = i0 + 1U;
                        const std::uint32_t i2 = i0 + stride;
                        const std::uint32_t i3 = i2 + 1U;
                        mesh.indices.insert(mesh.indices.end(), {i0, i2, i1, i1, i2, i3});
                    }
                }
            }

            vf::PlanetMesh proxy = vf::buildPlanetSurface(planet, 48U);
            constexpr double proxyInset = 240.0;
            for (auto& vertex : proxy.vertices) {
                glm::dvec3 p = glm::dvec3(vertex.position);
                const double r = glm::length(p);
                if (r > proxyInset + 1.0) p *= (r - proxyInset) / r;
                vertex.position = glm::vec3(toSurfacePoint(p));
                vertex.normal = glm::vec3(safeNormalize(toSurfaceVector(glm::dvec3(vertex.normal))));
                vertex.material = {0.0F, 0.93F, 0.0F, 0.0F};
            }
            appendMesh(mesh, proxy);
            return mesh;
        };

        vf::PlanetMesh staticTerrain = buildTerrainLod(lodCenterDirection);
        renderer.uploadPlanetMesh(staticTerrain);

        // Planet-local physics is now centered on the planet in double precision. Rendering stays
        // camera-relative, so metre contacts and 6371 km coordinates no longer fight each other.
        vf::CelestialSystem localGravitySystem;
        vf::CelestialBody localGravityBody = aster;
        localGravityBody.position = {};
        localGravityBody.linearVelocity = {};
        localGravityBody.orbitParentId = 0U;
        localGravityBody.spinRateRadPerSecond = 0.0;
        localGravityBody.orientation = {1.0, 0.0, 0.0, 0.0};
        localGravityBody.atmosphere.enabled = false;
        localGravityBody.weather.windMultiplier = 0.0;
        const std::uint32_t localGravityId = localGravitySystem.addBody(localGravityBody);

        vf::PhysicsEnvironment environment{};
        environment.planet = planet;
        environment.surfaceGravity = 9.80665;
        environment.celestialSystem = &localGravitySystem;
        environment.primaryCelestialBodyId = localGravityId;
        environment.atmosphere.prevailingWind = {};
        environment.atmosphere.gustAmplitude = 0.0;
        environment.weather.windMultiplier = 0.0;
        environment.ocean.enabled = false;
        vf::PhysicsWorld physics{environment};
        vf::PhysicsInteraction interaction{physics};

        const glm::dvec3 pickupGroundPlanet = planetSurfaceAtOffset(0.0, 4.0);
        const glm::dvec3 pickupNormal = safeNormalize(
            vf::planetSurfaceNormal(planet, safeNormalize(pickupGroundPlanet)));
        glm::dvec3 pickupX = safeEast(pickupNormal);
        const glm::dvec3 pickupZ = safeNormalize(glm::cross(pickupX, pickupNormal), {0.0, 0.0, 1.0});
        const glm::dquat pickupOrientation = glm::normalize(glm::quat_cast(glm::dmat3{pickupX, pickupNormal, pickupZ}));

        struct PropSpec {
            double x;
            double z;
            glm::dvec3 half;
            double mass;
            double friction;
            glm::vec3 color;
            glm::vec4 material;
        };
        const std::array<PropSpec, 5> specs{{
            {0.0, 4.0, {0.60, 0.60, 0.60}, 12.0, 0.86, {0.32F, 0.35F, 0.38F}, {0.0F, 0.90F, 0.0F, 0.0F}},
            {-1.7, 5.2, {0.70, 0.45, 0.50}, 7.0, 0.80, {0.48F, 0.25F, 0.10F}, {0.0F, 0.66F, 0.0F, 0.0F}},
            {1.7, 5.2, {0.62, 0.48, 0.52}, 18.0, 0.58, {0.56F, 0.60F, 0.66F}, {1.0F, 0.18F, 0.0F, 0.0F}},
            {-1.0, 7.0, {0.48, 0.72, 0.48}, 9.0, 0.46, {0.10F, 0.43F, 0.92F}, {0.0F, 0.07F, 0.94F, 0.0F}},
            {1.0, 7.0, {0.48, 0.72, 0.48}, 9.0, 0.46, {0.96F, 0.50F, 0.12F}, {0.0F, 0.08F, 0.92F, 0.0F}},
        }};

        std::vector<PropVisual> props;
        props.reserve(specs.size() + 2U);
        for (const auto& spec : specs) {
            const glm::dvec3 groundPlanet = planetSurfaceAtOffset(spec.x, spec.z);
            const glm::dvec3 normal = safeNormalize(
                vf::planetSurfaceNormal(planet, safeNormalize(groundPlanet)));
            glm::dvec3 tangentX = safeEast(normal);
            const glm::dvec3 tangentZ = safeNormalize(glm::cross(tangentX, normal), {0.0, 0.0, 1.0});
            const glm::dquat orientation = glm::normalize(glm::quat_cast(glm::dmat3{tangentX, normal, tangentZ}));
            vf::RigidBodyDesc desc{};
            desc.mass = spec.mass;
            desc.position = groundPlanet + normal * (spec.half.y + 0.035);
            desc.orientation = orientation;
            desc.collisionShape = vf::CollisionShape::box(spec.half);
            desc.inertiaDiagonal = boxInertia(desc.mass, spec.half);
            desc.material.friction = spec.friction;
            desc.material.restitution = 0.0;
            desc.material.rollingResistance = 0.12;
            desc.linearDamping = 0.09;
            desc.angularDamping = 0.16;
            desc.aerodynamics.referenceArea = 0.0;
            props.push_back({physics.createRigidBody(desc), spec.half, spec.color, spec.material});
        }

        const auto addStaticTestBox = [&](double x, double z, const glm::dvec3& half, const glm::vec3& color) {
            const glm::dvec3 groundPlanet = planetSurfaceAtOffset(x, z);
            const glm::dvec3 normal = safeNormalize(vf::planetSurfaceNormal(planet, safeNormalize(groundPlanet)));
            const glm::dvec3 tangentX = safeEast(normal);
            const glm::dvec3 tangentZ = safeNormalize(glm::cross(tangentX, normal), {0.0, 0.0, 1.0});
            vf::RigidBodyDesc desc{};
            desc.motionType = vf::MotionType::Static;
            desc.mass = 0.0;
            desc.position = groundPlanet + normal * half.y;
            desc.orientation = glm::normalize(glm::quat_cast(glm::dmat3{tangentX, normal, tangentZ}));
            desc.collisionShape = vf::CollisionShape::box(half);
            desc.aerodynamics.referenceArea = 0.0;
            props.push_back({physics.createRigidBody(desc), half, color, {0.0F, 0.88F, 0.0F, 0.0F}});
        };
        addStaticTestBox(3.2, 6.5, {1.2, 0.18, 0.75}, {0.42F, 0.43F, 0.40F});
        addStaticTestBox(5.8, 10.0, {1.8, 1.35, 0.30}, {0.38F, 0.39F, 0.42F});

        vf::CharacterControllerSettings characterSettings{};
        characterSettings.walkSpeed = 9.0;
        characterSettings.sprintSpeed = 18.0;
        characterSettings.maxSlopeAngleRadians = glm::radians(50.0);
        characterSettings.stepHeight = 0.45;
        vf::CharacterController character{physics, characterSettings};
        character.resetFromEye(initialCameraPlanet, {}, true);

        std::cout << "Voxel Frontier physical planet R2\n";
        std::cout << "CharacterVirtual-style capsule | 50 deg slope | 0.45 m step | stick-to-floor\n";
        std::cout << "Planet-centered double physics | streamed terrain | physical shadows/glass/atmosphere\n";

        using Clock = std::chrono::steady_clock;
        auto previous = Clock::now();
        double diagnosticsTime = 0.0;
        std::uint64_t diagnosticsFrames = 0;
        double lodCooldown = 0.0;

        while (platform.pumpEvents()) {
            const auto now = Clock::now();
            const double dt = std::clamp(std::chrono::duration<double>(now - previous).count(), 1.0 / 500.0, 0.05);
            previous = now;
            celestial.step(dt);

            auto* currentAster = celestial.body(asterId);
            const auto* currentCinder = celestial.body(cinderId);
            const auto* currentSun = celestial.body(sunId);
            if (currentAster == nullptr || currentSun == nullptr) continue;
            currentAster->atmosphere.prevailingWind = {};
            currentAster->weather.windMultiplier = 0.0;
            currentAster->weather.stormIntensity = 0.0;

            if (platform.consumeResize()) renderer.requestResize();
            const auto& input = platform.input();
            vf::PlanetMovementInput movement{};
            movement.forward = (input.forward ? 1.0 : 0.0) - (input.backward ? 1.0 : 0.0);
            movement.right = (input.right ? 1.0 : 0.0) - (input.left ? 1.0 : 0.0);
            movement.vertical = (input.ascend ? 1.0 : 0.0) - (input.descend ? 1.0 : 0.0);
            movement.mouseDx = input.mouseCaptured ? static_cast<double>(input.mouseDx) : 0.0;
            movement.mouseDy = input.mouseCaptured ? static_cast<double>(input.mouseDy) : 0.0;
            movement.flightSpeedSteps = input.flightSpeedSteps;
            movement.sprint = input.sprint;
            movement.toggleFlight = input.toggleFlight;

            const bool wasFlightMode = camera.flightMode();
            camera.update(movement, dt);
            physics.advance(dt);

            glm::dquat inverseAster = glm::conjugate(glm::normalize(currentAster->orientation));
            glm::dvec3 cameraPlanet = inverseAster * (camera.position() - currentAster->position);
            glm::dvec3 localCameraVelocity = asterFrame.toLocalVelocity(*currentAster, camera.position(), camera.velocity());

            if (camera.physicsFrameBodyId() == asterId) {
                if (camera.flightMode()) {
                    character.resetFromEye(cameraPlanet, localCameraVelocity, false);
                } else {
                    if (wasFlightMode) character.resetFromEye(cameraPlanet, localCameraVelocity, false);
                    const glm::dvec3 forwardPlanet = safeNormalize(inverseAster * camera.forwardDirection(), {0.0, 0.0, -1.0});
                    const glm::dvec3 gravityUp = character.up();
                    const glm::dvec3 tangentForward = safeNormalize(
                        forwardPlanet - gravityUp * glm::dot(forwardPlanet, gravityUp),
                        patchZ);
                    const glm::dvec3 tangentRight = safeNormalize(glm::cross(tangentForward, gravityUp), patchEast);

                    vf::CharacterControllerInput characterInput{};
                    characterInput.forward = tangentForward;
                    characterInput.right = tangentRight;
                    characterInput.forwardAxis = movement.forward;
                    characterInput.rightAxis = movement.right;
                    characterInput.jump = input.ascend && !input.toggleFlight;
                    characterInput.sprint = input.sprint;
                    character.update(characterInput, dt);

                    const glm::dvec3 worldEye = asterFrame.toWorldPosition(*currentAster, character.eyePosition());
                    const glm::dvec3 worldVelocity = asterFrame.toWorldVelocity(
                        *currentAster, character.eyePosition(), character.linearVelocity());
                    camera.setExternalWorldState(worldEye, worldVelocity, character.grounded());
                    inverseAster = glm::conjugate(glm::normalize(currentAster->orientation));
                    cameraPlanet = inverseAster * (camera.position() - currentAster->position);
                }
            }

            const glm::dvec3 cameraSurface = toSurfacePoint(cameraPlanet);
            const glm::dvec3 forwardPlanet = safeNormalize(inverseAster * camera.forwardDirection(), {0.0, 0.0, -1.0});
            const glm::dvec3 forwardSurface = safeNormalize(toSurfaceVector(forwardPlanet), {0.0, 0.0, -1.0});
            const glm::dvec3 upSurface = safeNormalize(toSurfaceVector(inverseAster * camera.up()), {0.0, 1.0, 0.0});

            if (camera.physicsFrameBodyId() == asterId) {
                vf::PhysicsInteractionInput interactionInput{};
                interactionInput.rightPressed = input.rightPressed;
                interactionInput.leftPressed = input.leftPressed;
                interaction.update(cameraPlanet, forwardPlanet, interactionInput, dt);
            } else if (interaction.holding()) {
                interaction.drop();
            }

            lodCooldown = std::max(0.0, lodCooldown - dt);
            const double altitude = camera.altitude();
            if (camera.physicsFrameBodyId() == asterId && altitude < 800000.0 && lodCooldown <= 0.0) {
                const glm::dvec3 cameraDirection = safeNormalize(cameraPlanet, lodCenterDirection);
                const double arcDistance = std::acos(std::clamp(glm::dot(cameraDirection, lodCenterDirection), -1.0, 1.0)) * planet.radius;
                const double threshold = altitude < 20000.0 ? 8000.0
                    : (altitude < 100000.0 ? 40000.0 : (altitude < 350000.0 ? 120000.0 : 350000.0));
                if (arcDistance > threshold) {
                    lodCenterDirection = cameraDirection;
                    staticTerrain = buildTerrainLod(lodCenterDirection);
                    renderer.uploadPlanetMesh(staticTerrain);
                    lodCooldown = 0.45;
                }
            }

            const glm::dvec3 sunWorldDirection = safeNormalize(currentSun->position - camera.position());
            const glm::dvec3 sunSurfaceDirection = safeNormalize(toSurfaceVector(inverseAster * sunWorldDirection), {0.3, 0.8, -0.2});

            vf::PlanetMesh dynamicMesh{};
            for (const auto& prop : props) {
                const vf::RigidBody* body = physics.body(prop.bodyId);
                if (body == nullptr) continue;
                const glm::dvec3 renderPosition = toSurfacePoint(body->position);
                const glm::dquat renderOrientation = glm::normalize(surfaceFromPlanetRotation * body->orientation);
                vf::appendDebugBox(dynamicMesh, renderPosition, renderOrientation, prop.halfExtents, prop.color, prop.material);
            }

            if (currentCinder != nullptr) {
                const glm::dvec3 cinderDirection = safeNormalize(currentCinder->position - camera.position());
                const glm::dvec3 cinderSurfaceDirection = safeNormalize(toSurfaceVector(inverseAster * cinderDirection));
                const double distance = glm::length(currentCinder->position - camera.position());
                const double angularRadius = std::asin(std::clamp(currentCinder->radiusMeters / std::max(distance, currentCinder->radiusMeters), 0.0, 0.20));
                constexpr double visualDistance = 25000000.0;
                const double visualRadius = std::max(1800.0, std::tan(angularRadius) * visualDistance);
                vf::appendDebugSphere(dynamicMesh, cameraSurface + cinderSurfaceDirection * visualDistance,
                    visualRadius, {0.62F, 0.30F, 0.22F}, 9U, 16U, {0.0F, 0.82F, 0.0F, 0.0F});
            }
            renderer.setDynamicMesh(dynamicMesh);

            const auto [width, height] = platform.drawableSize();
            const float aspect = height > 0 ? static_cast<float>(width) / static_cast<float>(height) : 16.0F / 9.0F;
            const glm::mat4 viewProjection = makeReverseZViewProjection(forwardSurface, upSurface, aspect);

            const auto atmosphere = celestial.sampleEnvironment(camera.position());
            const double densityRatio = std::clamp(atmosphere.densityKgPerM3 / 1.225, 0.0, 1.2);
            const double physicalSunDistance = glm::length(currentSun->position - camera.position());
            const double irradiance = currentSun->luminosityWatts
                / (4.0 * kPi * std::max(1.0, physicalSunDistance * physicalSunDistance));
            const double sunElevation = glm::dot(camera.up(), sunWorldDirection);
            const double airMass = densityRatio / std::max(0.065, sunElevation + 0.14);
            const glm::dvec3 extinction = glm::dvec3{0.10, 0.22, 0.48} * std::max(0.0, airMass);

            vf::RenderFrameEnvironment renderEnvironment{};
            renderEnvironment.sunDirectionToLight = glm::vec3(sunSurfaceDirection);
            renderEnvironment.sunLinearColor = glm::vec3(glm::exp(-extinction));
            renderEnvironment.sunIntensity = static_cast<float>(3.0 * std::clamp(irradiance / 1361.0, 0.0, 3.0));
            renderEnvironment.skyAmbient = glm::vec3{0.035F, 0.060F, 0.105F}
                + glm::vec3{0.10F, 0.15F, 0.24F} * static_cast<float>(densityRatio);
            renderEnvironment.groundAmbient = glm::vec3{0.018F, 0.016F, 0.013F}
                + glm::vec3{0.030F, 0.042F, 0.022F} * static_cast<float>(densityRatio);
            renderEnvironment.exposure = 1.10F;
            renderEnvironment.cameraForward = glm::vec3(forwardSurface);
            renderEnvironment.planetCenter = toSurfacePoint(glm::dvec3{0.0});
            renderEnvironment.planetRadius = planet.radius;
            renderEnvironment.atmosphereHeight = planet.atmosphereHeight;
            renderEnvironment.atmosphereScaleHeight = aster.atmosphere.scaleHeightMeters;
            renderEnvironment.mieScale = 0.85F;
            renderEnvironment.flightSpeedMps = static_cast<float>(camera.flightSpeedMps());

            renderer.drawFrame(viewProjection, cameraSurface, renderEnvironment);

            diagnosticsTime += dt;
            ++diagnosticsFrames;
            if (diagnosticsTime >= 0.5) {
                std::size_t sleeping = 0;
                double maxLinear = 0.0;
                double maxAngular = 0.0;
                for (const auto& prop : props) {
                    const vf::RigidBody* body = physics.body(prop.bodyId);
                    if (body == nullptr || body->motionType != vf::MotionType::Dynamic) continue;
                    if (body->sleeping) ++sleeping;
                    maxLinear = std::max(maxLinear, glm::length(body->linearVelocity));
                    maxAngular = std::max(maxAngular, glm::length(body->angularVelocity));
                }
                const double fps = static_cast<double>(diagnosticsFrames) / diagnosticsTime;
                std::ostringstream title;
                title << "Voxel Frontier R2 | "
                      << (camera.flightMode() ? "FLIGHT" : (character.grounded() ? "CAPSULE-GROUNDED" : "CAPSULE-AIR"))
                      << " | SPEED " << std::fixed << std::setprecision(0) << camera.flightSpeedMps() << " m/s"
                      << " | ALT " << std::setprecision(2) << camera.altitude() / 1000.0 << " km"
                      << " | SLOPE<=50 | STEP 0.45m"
                      << " | WIND OFF | sleeping " << sleeping << '/' << specs.size()
                      << " | vMax " << std::setprecision(3) << maxLinear
                      << " | wMax " << maxAngular
                      << " | " << (interaction.holding() ? "HOLDING" : "HANDS FREE")
                      << " | tris " << renderer.triangleCount() << '+' << renderer.dynamicTriangleCount()
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
