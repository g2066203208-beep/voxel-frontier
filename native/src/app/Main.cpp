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
#include <exception>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <vector>

#include <glm/common.hpp>
#include <glm/geometric.hpp>
#include <glm/gtc/quaternion.hpp>

namespace {

constexpr double kPi = 3.1415926535897932384626433832795;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-12) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] glm::dvec3 safeEast(const glm::dvec3& up) noexcept {
    glm::dvec3 east = glm::cross(glm::dvec3{0.0, 1.0, 0.0}, up);
    if (glm::dot(east, east) < 1.0e-8) east = glm::cross(glm::dvec3{1.0, 0.0, 0.0}, up);
    return safeNormalize(east, {1.0, 0.0, 0.0});
}

[[nodiscard]] double circularOrbitSpeed(double parentMassKg, double radiusMeters) {
    return std::sqrt(vf::CelestialSystem::kGravitationalConstant * parentMassKg
        / std::max(1.0, radiusMeters));
}

void rotateMesh(vf::PlanetMesh& mesh, const glm::dquat& rotationValue) {
    const glm::dquat rotation = glm::normalize(rotationValue);
    for (auto& vertex : mesh.vertices) {
        vertex.position = glm::vec3(rotation * glm::dvec3(vertex.position));
        vertex.normal = glm::normalize(glm::vec3(rotation * glm::dvec3(vertex.normal)));
    }
}

void appendMesh(vf::PlanetMesh& destination, const vf::PlanetMesh& source) {
    const std::uint32_t base = static_cast<std::uint32_t>(destination.vertices.size());
    destination.vertices.insert(destination.vertices.end(), source.vertices.begin(), source.vertices.end());
    destination.indices.reserve(destination.indices.size() + source.indices.size());
    for (const std::uint32_t index : source.indices) destination.indices.push_back(base + index);
}

struct StabilityProp {
    std::uint32_t bodyId{};
    glm::vec3 color{};
};

} // namespace

int main() {
    try {
        vf::SdlPlatform platform{"Voxel Frontier — Planet Stability Test", 1600, 900};
        vf::VulkanRenderer renderer{platform.window()};

        vf::PlanetDefinition planet{};
        planet.seed = 0x71A9F20DULL;
        planet.radius = 6000.0;
        planet.maxElevation = 360.0;
        planet.atmosphereHeight = 1100.0;

        // ---------------------------------------------------------------------
        // Inertial celestial layer. Aster really orbits and rotates here.
        // ---------------------------------------------------------------------
        vf::CelestialSystem celestial;

        vf::CelestialBody star{};
        star.type = vf::CelestialBodyType::Star;
        star.name = "Helion";
        star.radiusMeters = 4200.0;
        constexpr double starMu = 2.80e9;
        star.massKg = starMu / vf::CelestialSystem::kGravitationalConstant;
        star.position = {};
        star.spinAxis = safeNormalize({0.0, 1.0, 0.12});
        star.spinRateRadPerSecond = 2.0 * kPi / 900.0;
        const double asterOrbitRadius = 45000.0;
        star.luminosityWatts = 4.0 * kPi * asterOrbitRadius * asterOrbitRadius * 1320.0;
        const std::uint32_t starId = celestial.addBody(star);

        vf::CelestialBody aster{};
        aster.type = vf::CelestialBodyType::Planet;
        aster.name = "Aster";
        aster.radiusMeters = planet.radius;
        aster.massKg = 9.81 * aster.radiusMeters * aster.radiusMeters
            / vf::CelestialSystem::kGravitationalConstant;
        aster.gameplaySurfaceGravityMps2 = 9.81;
        aster.gravityFalloffStartRadiusMeters = planet.radius + planet.atmosphereHeight;
        aster.gravityFalloffPower = 7.0;
        aster.gravityInfluenceRadiusMeters = 15000.0;
        aster.physicsBubbleRadiusMeters = 18000.0;
        aster.position = {asterOrbitRadius, 0.0, 0.0};
        aster.orbitParentId = starId;
        aster.linearVelocity = {0.0, 0.0, circularOrbitSpeed(star.massKg, asterOrbitRadius)};
        aster.spinAxis = safeNormalize({0.08, 1.0, 0.03});
        aster.spinRateRadPerSecond = 2.0 * kPi / 1200.0;
        aster.visibleAlbedo = {0.30, 0.55, 0.32};
        aster.atmosphere.enabled = true;
        aster.atmosphere.heightMeters = planet.atmosphereHeight;
        aster.atmosphere.surfacePressurePa = 101325.0;
        aster.atmosphere.surfaceTemperatureK = 288.15;
        aster.atmosphere.scaleHeightMeters = 360.0;
        aster.atmosphere.lapseRateKPerM = 0.0065;
        aster.atmosphere.rayleighRgb = {0.16, 0.43, 1.00};
        aster.atmosphere.mieStrength = 0.11;
        aster.atmosphere.prevailingWind = {8.0, 0.0, 2.5};
        aster.weather.humidity = 0.58;
        aster.weather.cloudCover = 0.32;
        const std::uint32_t asterId = celestial.addBody(aster);

        vf::CelestialBody cinder{};
        cinder.type = vf::CelestialBodyType::Planet;
        cinder.name = "Cinder";
        cinder.radiusMeters = 2800.0;
        cinder.massKg = 3.7 * cinder.radiusMeters * cinder.radiusMeters
            / vf::CelestialSystem::kGravitationalConstant;
        cinder.gameplaySurfaceGravityMps2 = 3.7;
        cinder.gravityFalloffStartRadiusMeters = cinder.radiusMeters + 520.0;
        cinder.gravityFalloffPower = 7.0;
        cinder.gravityInfluenceRadiusMeters = 9000.0;
        cinder.physicsBubbleRadiusMeters = 11000.0;
        const double cinderOrbitRadius = 70000.0;
        cinder.position = {0.0, 0.0, cinderOrbitRadius};
        cinder.orbitParentId = starId;
        cinder.linearVelocity = {-circularOrbitSpeed(star.massKg, cinderOrbitRadius), 0.0, 0.0};
        cinder.spinAxis = safeNormalize({0.25, 1.0, -0.12});
        cinder.spinRateRadPerSecond = 2.0 * kPi / 820.0;
        cinder.visibleAlbedo = {0.62, 0.30, 0.22};
        cinder.atmosphere.enabled = true;
        cinder.atmosphere.heightMeters = 520.0;
        cinder.atmosphere.surfacePressurePa = 2200.0;
        cinder.atmosphere.surfaceTemperatureK = 238.0;
        cinder.atmosphere.scaleHeightMeters = 170.0;
        cinder.atmosphere.rayleighRgb = {0.70, 0.28, 0.12};
        const std::uint32_t cinderId = celestial.addBody(cinder);

        // ---------------------------------------------------------------------
        // One authoritative Aster-local physics space.
        // The local proxy has no orbit/spin and no wind. Nothing in this acceptance
        // scene is allowed to move merely because the planet moves in inertial space.
        // ---------------------------------------------------------------------
        vf::CelestialSystem localCelestial;
        vf::CelestialBody localAster = aster;
        localAster.position = {};
        localAster.linearVelocity = {};
        localAster.orientation = glm::dquat{1.0, 0.0, 0.0, 0.0};
        localAster.orbitParentId = 0U;
        localAster.spinRateRadPerSecond = 0.0;
        localAster.atmosphere.prevailingWind = {};
        localAster.weather.windMultiplier = 0.0;
        localAster.weather.stormIntensity = 0.0;
        const std::uint32_t localAsterId = localCelestial.addBody(localAster);

        vf::PhysicsEnvironment environment{};
        environment.planet = planet;
        environment.surfaceGravity = 9.81;
        environment.celestialSystem = &localCelestial;
        environment.primaryCelestialBodyId = localAsterId;
        environment.atmosphere.prevailingWind = {};
        environment.atmosphere.gustAmplitude = 0.0;
        environment.weather.windMultiplier = 0.0;
        environment.ocean.enabled = false;
        vf::PhysicsWorld physics{environment};

        vf::PlanetMesh staticPlanet = vf::buildPlanetSurface(planet, 192U);
        renderer.uploadPlanetMesh(staticPlanet);

        vf::PlanetCamera camera{planet, &celestial, asterId};
        vf::PhysicsInteraction interaction{physics};

        // Use the same local surface patch as the player start, but keep props a few
        // metres ahead so pickup testing is immediate.
        const glm::dvec3 patchUp = safeNormalize({0.72, 0.52, 0.46});
        const glm::dvec3 patchEast = safeEast(patchUp);
        const glm::dvec3 patchNorth = safeNormalize(glm::cross(patchUp, patchEast), {0.0, 0.0, 1.0});
        const auto localSurfacePoint = [&](double eastMeters, double northMeters, double heightMeters) {
            const glm::dvec3 direction = safeNormalize(
                patchUp
                    + patchEast * (eastMeters / planet.radius)
                    + patchNorth * (northMeters / planet.radius),
                patchUp);
            return direction * (vf::planetSurfaceRadius(planet, direction) + heightMeters);
        };

        const std::array<glm::vec3, 6> propColors{
            glm::vec3{0.82F, 0.27F, 0.22F},
            glm::vec3{0.24F, 0.62F, 0.92F},
            glm::vec3{0.28F, 0.78F, 0.38F},
            glm::vec3{0.90F, 0.68F, 0.18F},
            glm::vec3{0.64F, 0.32F, 0.86F},
            glm::vec3{0.24F, 0.78F, 0.76F},
        };
        std::vector<StabilityProp> props;
        props.reserve(propColors.size());

        for (std::size_t i = 0; i < propColors.size(); ++i) {
            const double radius = 0.34 + 0.045 * static_cast<double>(i);
            const double east = -3.2 + 1.28 * static_cast<double>(i);
            vf::RigidBodyDesc desc{};
            desc.mass = 4.0 + static_cast<double>(i) * 1.5;
            desc.position = localSurfacePoint(east, 7.0, radius + 0.008);
            desc.linearVelocity = {};
            desc.angularVelocity = {};
            desc.collisionShape = vf::CollisionShape::sphere(radius);
            const double inertia = 0.4 * desc.mass * radius * radius;
            desc.inertiaDiagonal = {inertia, inertia, inertia};
            desc.material.friction = 0.95;
            desc.material.restitution = 0.0;
            desc.material.rollingResistance = 0.30;
            desc.linearDamping = 0.10;
            desc.angularDamping = 0.18;
            desc.aerodynamics.referenceArea = 0.0;
            desc.buoyancy.enabled = false;
            props.push_back({physics.createRigidBody(desc), propColors[i]});
        }

        std::cout << "Voxel Frontier planet-local stability acceptance test\n";
        std::cout << "Acceptance: with no input, props must settle and remain still relative to Aster.\n";
        std::cout << "Controls: WASD, Shift, Space. Double-tap Space toggles creative flight.\n";
        std::cout << "Right click picks/drops a loose prop; left click throws a held prop.\n";

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
            const vf::CelestialBody* currentSun = celestial.body(starId);

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

            if (currentAster != nullptr && camera.physicsFrameBodyId() == asterId) {
                const glm::dquat inverseAster = glm::conjugate(glm::normalize(currentAster->orientation));
                const glm::dvec3 interactionOrigin = inverseAster * (camera.position() - currentAster->position);
                const glm::dvec3 interactionDirection = safeNormalize(inverseAster * camera.forwardDirection());
                vf::PhysicsInteractionInput interactionInput{};
                interactionInput.rightPressed = input.rightPressed;
                interactionInput.leftPressed = input.leftPressed;
                interaction.update(interactionOrigin, interactionDirection, interactionInput, dt);
            } else if (interaction.holding()) {
                interaction.drop();
            }

            physics.advance(dt);

            const glm::dvec3 renderOrigin = currentAster != nullptr ? currentAster->position : glm::dvec3{};
            const glm::dquat asterRotation = currentAster != nullptr
                ? glm::normalize(currentAster->orientation)
                : glm::dquat{1.0, 0.0, 0.0, 0.0};

            vf::PlanetMesh dynamicMesh{};
            for (const auto& prop : props) {
                const vf::RigidBody* body = physics.body(prop.bodyId);
                if (body == nullptr) continue;
                vf::appendDebugSphere(
                    dynamicMesh,
                    body->position,
                    body->collisionShape.radius,
                    prop.color,
                    8U,
                    12U);
            }
            rotateMesh(dynamicMesh, asterRotation);

            vf::PlanetMesh celestialMesh{};
            if (currentCinder != nullptr) {
                vf::appendCelestialBodyProxy(
                    celestialMesh,
                    currentCinder->position - renderOrigin,
                    currentCinder->orientation,
                    currentCinder->radiusMeters,
                    16U,
                    glm::vec3(currentCinder->visibleAlbedo));
            }
            if (currentSun != nullptr) {
                vf::appendCelestialBodyProxy(
                    celestialMesh,
                    currentSun->position - renderOrigin,
                    currentSun->orientation,
                    currentSun->radiusMeters,
                    14U,
                    {8.0F, 7.2F, 5.5F});
            }
            appendMesh(dynamicMesh, celestialMesh);
            renderer.setDynamicMesh(dynamicMesh);

            const vf::CelestialEnvironmentSample cameraEnvironment = celestial.sampleEnvironment(camera.position());
            glm::vec3 sky{0.0F};
            if (cameraEnvironment.pressurePa > 0.0) {
                const double pressureRatio = std::clamp(cameraEnvironment.pressurePa / 101325.0, 0.0, 1.0);
                sky = glm::vec3(0.05, 0.14, 0.34) * static_cast<float>(pressureRatio);
            }

            const auto [width, height] = platform.drawableSize();
            const float aspect = height > 0
                ? static_cast<float>(width) / static_cast<float>(height)
                : 16.0F / 9.0F;
            const glm::vec3 sunDirection = currentSun != nullptr
                ? glm::vec3(safeNormalize(currentSun->position - camera.position()))
                : glm::vec3{0.38F, 0.83F, 0.41F};

            renderer.drawFrame(
                sky,
                camera.viewProjection(aspect),
                camera.position() - renderOrigin,
                sunDirection,
                {1.0F, 0.94F, 0.82F},
                2.2F,
                asterRotation);

            diagnosticsTime += dt;
            ++diagnosticsFrames;
            if (diagnosticsTime >= 0.5) {
                std::size_t sleepingCount = 0U;
                double maxLinearSpeed = 0.0;
                double maxAngularSpeed = 0.0;
                for (const auto& prop : props) {
                    const vf::RigidBody* body = physics.body(prop.bodyId);
                    if (body == nullptr) continue;
                    if (body->sleeping) ++sleepingCount;
                    maxLinearSpeed = std::max(maxLinearSpeed, glm::length(body->linearVelocity));
                    maxAngularSpeed = std::max(maxAngularSpeed, glm::length(body->angularVelocity));
                }

                const double fps = diagnosticsTime > 0.0
                    ? static_cast<double>(diagnosticsFrames) / diagnosticsTime
                    : 0.0;
                std::ostringstream title;
                title << "Planet Stability | FPS " << std::fixed << std::setprecision(0) << fps
                      << " | " << (camera.flightMode() ? "FLIGHT" : (camera.grounded() ? "GROUNDED" : "AIRBORNE"))
                      << " | sleeping " << sleepingCount << "/" << props.size()
                      << " | vMax " << std::setprecision(4) << maxLinearSpeed
                      << " | wMax " << maxAngularSpeed
                      << " | " << (interaction.holding() ? "HOLDING" : "HANDS FREE");
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
