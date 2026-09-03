#include "vf/gameplay/PhysicsInteraction.hpp"
#include "vf/gameplay/PhysicsPlayground.hpp"
#include "vf/physics/PhysicsWorld.hpp"
#include "vf/physics/SpectralOptics.hpp"
#include "vf/platform/SdlPlatform.hpp"
#include "vf/player/PlanetCamera.hpp"
#include "vf/render/VulkanRenderer.hpp"
#include "vf/world/CelestialSystem.hpp"
#include "vf/world/PlanetSurface.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <sstream>

#include <glm/common.hpp>
#include <glm/geometric.hpp>

namespace {

constexpr double kPi = 3.1415926535897932384626433832795;

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double lengthSquared = glm::dot(value, value);
    if (lengthSquared <= 1.0e-12) return fallback;
    return value / std::sqrt(lengthSquared);
}

[[nodiscard]] double circularOrbitSpeed(double parentMassKg, double radiusMeters) {
    return std::sqrt(vf::CelestialSystem::kGravitationalConstant * parentMassKg
        / std::max(1.0, radiusMeters));
}

[[nodiscard]] bool hasLineOfSightToStar(
    const vf::CelestialSystem& celestial,
    const glm::dvec3& observer,
    std::uint32_t starId) noexcept {
    const auto* star = celestial.body(starId);
    if (star == nullptr) return false;

    const glm::dvec3 toStar = star->position - observer;
    const double starDistance = glm::length(toStar);
    if (starDistance <= 1.0e-9) return true;
    const glm::dvec3 ray = toStar / starDistance;

    for (const auto& body : celestial.bodies()) {
        if (body.id == starId || body.type == vf::CelestialBodyType::Star) continue;
        const glm::dvec3 toCenter = body.position - observer;
        const double alongRay = glm::dot(toCenter, ray);
        if (alongRay <= 1.0e-5 || alongRay >= starDistance) continue;
        const glm::dvec3 closest = observer + ray * alongRay;
        if (glm::length(closest - body.position) < body.radiusMeters) return false;
    }
    return true;
}

[[nodiscard]] float atmosphereOpticalStrength(const vf::CelestialBody& body) noexcept {
    if (!body.atmosphere.enabled || body.atmosphere.surfacePressurePa <= 0.0) return 0.0F;
    const double pressureRatio = body.atmosphere.surfacePressurePa / 101325.0;
    const double strength = 0.18 + 0.26 * std::sqrt(std::clamp(pressureRatio, 0.0, 2.0))
        + 0.35 * std::clamp(body.atmosphere.mieStrength, 0.0, 1.0);
    return static_cast<float>(std::clamp(strength, 0.12, 0.72));
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

[[nodiscard]] double stellarIrradianceAt(
    const vf::CelestialBody& star,
    const glm::dvec3& position) noexcept {
    const glm::dvec3 delta = star.position - position;
    const double distanceSquared = std::max(
        glm::dot(delta, delta),
        star.radiusMeters * star.radiusMeters);
    return star.luminosityWatts / (4.0 * kPi * distanceSquared);
}

} // namespace

int main() {
    try {
        vf::SdlPlatform platform{"Voxel Frontier — Stable Planet Physics Preview", 1600, 900};
        vf::VulkanRenderer renderer{platform.window()};

        vf::PlanetDefinition planet{};
        planet.seed = 0x71A9F20DULL;
        planet.radius = 6000.0;
        planet.maxElevation = 360.0;
        planet.atmosphereHeight = 1100.0;

        // ---------------------------------------------------------------------
        // High-precision inertial celestial simulation.
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

        vf::CelestialBody primary{};
        primary.type = vf::CelestialBodyType::Planet;
        primary.name = "Aster";
        primary.radiusMeters = planet.radius;
        primary.massKg = 9.81 * primary.radiusMeters * primary.radiusMeters
            / vf::CelestialSystem::kGravitationalConstant;
        primary.gameplaySurfaceGravityMps2 = 9.81;
        primary.gravityFalloffStartRadiusMeters = planet.radius + planet.atmosphereHeight;
        primary.gravityFalloffPower = 7.0;
        primary.gravityInfluenceRadiusMeters = 15000.0;
        primary.physicsBubbleRadiusMeters = 18000.0;
        primary.position = {asterOrbitRadius, 0.0, 0.0};
        primary.orbitParentId = starId;
        primary.linearVelocity = {0.0, 0.0, circularOrbitSpeed(star.massKg, asterOrbitRadius)};
        primary.spinAxis = safeNormalize({0.08, 1.0, 0.03});
        primary.spinRateRadPerSecond = 2.0 * kPi / 1200.0;
        primary.visibleAlbedo = {0.30, 0.55, 0.32};
        primary.atmosphere.enabled = true;
        primary.atmosphere.heightMeters = planet.atmosphereHeight;
        primary.atmosphere.surfacePressurePa = 101325.0;
        primary.atmosphere.surfaceTemperatureK = 288.15;
        primary.atmosphere.scaleHeightMeters = 360.0;
        primary.atmosphere.lapseRateKPerM = 0.0065;
        primary.atmosphere.rayleighRgb = {0.16, 0.43, 1.00};
        primary.atmosphere.mieStrength = 0.11;
        primary.atmosphere.prevailingWind = {8.0, 0.0, 2.5};
        primary.climate.meanTemperatureK = 288.15;
        primary.climate.bondAlbedo = 0.30;
        primary.climate.greenhouseFactor = 1.12;
        primary.weather.humidity = 0.58;
        primary.weather.cloudCover = 0.32;
        primary.magneticField.enabled = true;
        primary.magneticField.equatorialSurfaceFieldTesla = 32.0e-6;
        const std::uint32_t primaryId = celestial.addBody(primary);

        vf::CelestialBody secondary{};
        secondary.type = vf::CelestialBodyType::Planet;
        secondary.name = "Cinder";
        secondary.radiusMeters = 2800.0;
        secondary.massKg = 3.7 * secondary.radiusMeters * secondary.radiusMeters
            / vf::CelestialSystem::kGravitationalConstant;
        secondary.gameplaySurfaceGravityMps2 = 3.7;
        secondary.gravityFalloffStartRadiusMeters = secondary.radiusMeters + 520.0;
        secondary.gravityFalloffPower = 7.0;
        secondary.gravityInfluenceRadiusMeters = 9000.0;
        secondary.physicsBubbleRadiusMeters = 11000.0;
        const double cinderOrbitRadius = 70000.0;
        secondary.position = {0.0, 0.0, cinderOrbitRadius};
        secondary.orbitParentId = starId;
        secondary.linearVelocity = {-circularOrbitSpeed(star.massKg, cinderOrbitRadius), 0.0, 0.0};
        secondary.spinAxis = safeNormalize({0.25, 1.0, -0.12});
        secondary.spinRateRadPerSecond = 2.0 * kPi / 820.0;
        secondary.visibleAlbedo = {0.62, 0.30, 0.22};
        secondary.atmosphere.enabled = true;
        secondary.atmosphere.heightMeters = 520.0;
        secondary.atmosphere.surfacePressurePa = 2200.0;
        secondary.atmosphere.surfaceTemperatureK = 238.0;
        secondary.atmosphere.molarMassKgPerMol = 0.043;
        secondary.atmosphere.scaleHeightMeters = 170.0;
        secondary.atmosphere.lapseRateKPerM = 0.004;
        secondary.atmosphere.rayleighRgb = {0.70, 0.28, 0.12};
        secondary.atmosphere.mieStrength = 0.22;
        secondary.atmosphere.prevailingWind = {4.0, 0.0, -1.0};
        secondary.climate.meanTemperatureK = 238.0;
        secondary.climate.bondAlbedo = 0.22;
        secondary.climate.greenhouseFactor = 1.04;
        secondary.weather.humidity = 0.12;
        secondary.weather.cloudCover = 0.08;
        secondary.magneticField.enabled = true;
        secondary.magneticField.equatorialSurfaceFieldTesla = 7.0e-6;
        const std::uint32_t secondaryId = celestial.addBody(secondary);

        // ---------------------------------------------------------------------
        // Aster-local gameplay physics.
        //
        // This is deliberately NOT the 45 km star-centric world. All nearby contacts,
        // sleeping bodies, ropes and pickup objects stay at ~6 km coordinates, so float debug
        // geometry never loses millimetres by subtracting two large already-rounded numbers.
        // ---------------------------------------------------------------------
        vf::CelestialSystem localCelestial;
        vf::CelestialBody localAster = primary;
        localAster.position = {};
        localAster.linearVelocity = {};
        localAster.orientation = glm::dquat{1.0, 0.0, 0.0, 0.0};
        localAster.orbitParentId = 0U;
        localAster.spinRateRadPerSecond = 0.0;
        const std::uint32_t localPrimaryId = localCelestial.addBody(localAster);

        vf::PhysicsEnvironment environment{};
        environment.planet = planet;
        environment.surfaceGravity = 9.81;
        environment.ocean.enabled = true;
        environment.ocean.surfaceRadius = planet.radius - 80.0;
        environment.ocean.densityKgPerM3 = 997.0;
        environment.celestialSystem = &localCelestial;
        environment.primaryCelestialBodyId = localPrimaryId;
        vf::PhysicsWorld physics{environment};

        vf::PlanetMesh staticPlanet = vf::buildPlanetSurface(planet, 192U);
        renderer.uploadPlanetMesh(staticPlanet);

        vf::PlanetCamera camera{planet, &celestial, primaryId};
        const auto* initialAster = celestial.body(primaryId);
        const glm::dvec3 initialAsterPosition = initialAster != nullptr ? initialAster->position : glm::dvec3{};
        const glm::dquat initialAsterOrientation = initialAster != nullptr
            ? glm::normalize(initialAster->orientation)
            : glm::dquat{1.0, 0.0, 0.0, 0.0};
        const glm::dvec3 cameraLocal = glm::conjugate(initialAsterOrientation)
            * (camera.position() - initialAsterPosition);
        const glm::dvec3 cameraForwardLocal = glm::conjugate(initialAsterOrientation)
            * camera.forwardDirection();
        const glm::dvec3 tangentForwardLocal = safeNormalize(
            cameraForwardLocal - safeNormalize(cameraLocal) * glm::dot(cameraForwardLocal, safeNormalize(cameraLocal)),
            {0.0, 0.0, 1.0});
        const glm::dvec3 playgroundDirectionLocal = safeNormalize(
            cameraLocal + tangentForwardLocal * 22.0,
            safeNormalize(cameraLocal));

        vf::PhysicsPlayground playground{physics, planet, playgroundDirectionLocal};
        vf::PhysicsInteraction interaction{physics};

        const vf::GameSpectrum sunSpectrum = vf::blackbodySpectrum(5772.0);
        const glm::dvec3 sunLinearRgb = vf::spectrumToLinearSrgb(sunSpectrum);
        const double sunMax = std::max({sunLinearRgb.x, sunLinearRgb.y, sunLinearRgb.z, 1.0e-6});
        const glm::vec3 sunDisplayColor = glm::vec3(glm::clamp(
            sunLinearRgb / sunMax,
            glm::dvec3{0.0},
            glm::dvec3{1.0}));

        std::cout << "Voxel Frontier stable planet physics preview\n";
        std::cout << "GPU: " << renderer.gpuName() << '\n';
        std::cout << "Controls: WASD move, Space jump/up, Ctrl down, Shift fast.\n";
        std::cout << "Double-tap Space: creative flight. Right click: pickup/drop. Left click: throw held item.\n";
        std::cout << "Nearby rigid bodies simulate in Aster-local coordinates; celestial motion remains inertial doubles.\n";

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
            const auto* aster = celestial.body(primaryId);
            const auto* cinder = celestial.body(secondaryId);
            const auto* sun = celestial.body(starId);

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

            // First-person interaction is expressed directly in Aster-local coordinates. This
            // keeps pickup/drop/throw in exactly the same precision domain as rigid-body contacts.
            if (aster != nullptr && camera.physicsFrameBodyId() == primaryId) {
                const glm::dquat inverseAster = glm::conjugate(glm::normalize(aster->orientation));
                const glm::dvec3 interactionOrigin = inverseAster * (camera.position() - aster->position);
                const glm::dvec3 interactionDirection = safeNormalize(inverseAster * camera.forwardDirection());
                vf::PhysicsInteractionInput interactionInput{};
                interactionInput.rightPressed = input.rightPressed;
                interactionInput.leftPressed = input.leftPressed;
                interaction.update(interactionOrigin, interactionDirection, interactionInput, dt);
            } else if (interaction.holding()) {
                interaction.drop();
            }

            physics.advance(dt);
            playground.update(dt);

            const vf::CelestialEnvironmentSample cameraEnvironment = celestial.sampleEnvironment(camera.position());
            const vf::CelestialBody* atmosphereBody = celestial.body(cameraEnvironment.bodyId);
            const bool cameraHasSun = hasLineOfSightToStar(celestial, camera.position(), starId);

            glm::vec3 sky{0.0F};
            if (atmosphereBody != nullptr
                && atmosphereBody->atmosphere.enabled
                && cameraEnvironment.pressurePa > 0.0) {
                const double pressureRatio = std::clamp(
                    cameraEnvironment.pressurePa
                        / std::max(1.0, atmosphereBody->atmosphere.surfacePressurePa),
                    0.0,
                    1.0);
                const glm::dvec3 sunDirection = sun != nullptr
                    ? safeNormalize(sun->position - camera.position())
                    : glm::dvec3{0.0, 1.0, 0.0};
                const double solarElevation = glm::dot(camera.up(), sunDirection);
                const double daylight = cameraHasSun
                    ? std::clamp((solarElevation + 0.10) / 0.45, 0.0, 1.0)
                    : 0.0;
                const double twilight = std::clamp(
                    1.0 - std::abs(solarElevation + 0.06) / 0.18,
                    0.0,
                    1.0);
                const glm::dvec3 rayleigh = atmosphereBody->atmosphere.rayleighRgb
                    * pressureRatio * (0.008 + 0.30 * daylight);
                const glm::dvec3 mie = glm::dvec3{1.0, 0.72, 0.48}
                    * atmosphereBody->atmosphere.mieStrength * pressureRatio
                    * (0.08 * daylight + 0.05 * twilight);
                sky = glm::vec3(glm::clamp(rayleigh + mie, glm::dvec3{0.0}, glm::dvec3{1.0}));
            }

            const glm::dvec3 renderOrigin = aster != nullptr ? aster->position : glm::dvec3{};
            const glm::dquat asterRotation = aster != nullptr
                ? glm::normalize(aster->orientation)
                : glm::dquat{1.0, 0.0, 0.0, 0.0};

            // Local debug geometry is generated from small Aster-local values and receives only a
            // rotation before upload. It never goes through a 45,000 m float translation.
            vf::PlanetMesh dynamicMesh = playground.buildDebugMesh();
            rotateMesh(dynamicMesh, asterRotation);

            // Celestial proxies are authored relative to the render origin BEFORE conversion to
            // float vertex positions. This is the complementary fix for large-world precision.
            vf::PlanetMesh celestialMesh{};
            if (cinder != nullptr) {
                vf::appendCelestialBodyProxy(
                    celestialMesh,
                    cinder->position - renderOrigin,
                    cinder->orientation,
                    cinder->radiusMeters,
                    16U,
                    glm::vec3(cinder->visibleAlbedo));
            }
            if (sun != nullptr) {
                vf::appendCelestialBodyProxy(
                    celestialMesh,
                    sun->position - renderOrigin,
                    sun->orientation,
                    sun->radiusMeters,
                    14U,
                    glm::vec3(sunDisplayColor) * 12.0F);
            }

            for (const auto& body : celestial.bodies()) {
                if (body.type == vf::CelestialBodyType::Star
                    || !body.atmosphere.enabled
                    || body.atmosphere.heightMeters <= 0.0) {
                    continue;
                }
                const double outerRadius = body.radiusMeters + body.atmosphere.heightMeters;
                const double cameraRadius = glm::length(camera.position() - body.position);
                if (cameraRadius <= outerRadius * 0.985) continue;
                vf::appendAtmosphereProxy(
                    celestialMesh,
                    body.position - renderOrigin,
                    outerRadius,
                    14U,
                    glm::vec3(body.atmosphere.rayleighRgb),
                    atmosphereOpticalStrength(body));
            }
            appendMesh(dynamicMesh, celestialMesh);
            renderer.setDynamicMesh(dynamicMesh);

            const auto [width, height] = platform.drawableSize();
            const float aspect = height > 0
                ? static_cast<float>(width) / static_cast<float>(height)
                : 16.0F / 9.0F;
            const glm::vec3 sunDirectionToLight = sun != nullptr
                ? glm::vec3(safeNormalize(sun->position - camera.position()))
                : glm::vec3{0.38F, 0.83F, 0.41F};
            const double irradiance = sun != nullptr && cameraHasSun
                ? stellarIrradianceAt(*sun, camera.position())
                : 0.0;
            const float sunIntensity = static_cast<float>(
                2.2 * std::clamp(irradiance / 1320.0, 0.0, 4.0));

            renderer.drawFrame(
                sky,
                camera.viewProjection(aspect),
                camera.position() - renderOrigin,
                sunDirectionToLight,
                sunDisplayColor,
                sunIntensity,
                asterRotation);

            diagnosticsTime += dt;
            ++diagnosticsFrames;
            if (diagnosticsTime >= 1.0) {
                const double fps = diagnosticsTime > 0.0
                    ? static_cast<double>(diagnosticsFrames) / diagnosticsTime
                    : 0.0;
                const double gravity = glm::length(cameraEnvironment.gravityAcceleration);
                const vf::CelestialBody* gravityBody = celestial.gameplayReferenceBodyAt(camera.position());
                std::ostringstream title;
                title << "Voxel Frontier v7.1 | FPS " << std::fixed << std::setprecision(0) << fps
                      << " | " << (camera.flightMode() ? "FLIGHT" : (camera.grounded() ? "GROUNDED" : "AIRBORNE"))
                      << " | g " << std::setprecision(2) << gravity
                      << " | " << (gravityBody != nullptr ? gravityBody->name : std::string{"0g"})
                      << " | " << (interaction.holding() ? "HOLDING" : "HANDS FREE")
                      << " | contacts " << physics.lastContactPointCount();
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
