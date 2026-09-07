#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def patch(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"anchor not found in {path}: {old[:120]!r}")
    text = text.replace(old, new, 1)
    p.write_text(text, encoding="utf-8")


# 1) Explicit interstellar creative-travel envelope. Physical celestial integration remains SI.
patch(
    "native/include/vf/player/PlanetCamera.hpp",
    """    void setCreativeFlightSpeedMps(double speedMetersPerSecond) noexcept {\n        creativeFlightSpeedMps_ = std::clamp(speedMetersPerSecond, 1.0, 2000000.0);\n    }\n""",
    """    static constexpr double kSpeedOfLightMps = 299792458.0;\n    static constexpr double kCreativeInterstellarBaseMaxMps = 1024.0 * kSpeedOfLightMps;\n    static constexpr double kCreativeInterstellarSprintMaxMps = 4096.0 * kSpeedOfLightMps;\n\n    void setCreativeFlightSpeedMps(double speedMetersPerSecond) noexcept {\n        creativeFlightSpeedMps_ = std::clamp(\n            speedMetersPerSecond, 1.0, kCreativeInterstellarBaseMaxMps);\n    }\n""",
)

patch(
    "native/src/player/PlanetCamera.cpp",
    """    if (std::abs(input.flightSpeedSteps) > 1.0e-9) {\n        creativeFlightSpeedMps_ = std::clamp(\n            creativeFlightSpeedMps_ * std::pow(2.0, input.flightSpeedSteps * 0.5),\n            1.0,\n            2000000.0);\n    }\n""",
    """    if (std::abs(input.flightSpeedSteps) > 1.0e-9) {\n        // Surface flight remains deliberately fine-grained. Once fully inertial, each wheel notch\n        // spans four speed bands so AU/stellar traversal does not require dozens of scroll events.\n        const double speedStepExponent = inPhysicsFrame_ ? 0.5 : 2.0;\n        creativeFlightSpeedMps_ = std::clamp(\n            creativeFlightSpeedMps_ * std::pow(2.0, input.flightSpeedSteps * speedStepExponent),\n            1.0,\n            kCreativeInterstellarBaseMaxMps);\n    }\n""",
)

patch(
    "native/src/player/PlanetCamera.cpp",
    """            const double targetSpeed = creativeFlightSpeedMps_ * (input.sprint ? 4.0 : 1.0);\n            const glm::dvec3 desired = moveLength > 1.0e-8 ? move * targetSpeed : glm::dvec3{};\n""",
    """            // Never apply interstellar warp speeds while still inside a rotating body's\n            // precision/terrain frame. This preserves collision and surface traversal stability.\n            const double localCreativeSpeed = std::min(creativeFlightSpeedMps_, 2000000.0);\n            const double targetSpeed = localCreativeSpeed * (input.sprint ? 4.0 : 1.0);\n            const glm::dvec3 desired = moveLength > 1.0e-8 ? move * targetSpeed : glm::dvec3{};\n""",
)

patch(
    "native/src/player/PlanetCamera.cpp",
    """            const double targetSpeed = creativeFlightSpeedMps_ * (input.sprint ? 4.0 : 1.0);\n            const glm::dvec3 desiredControl = moveLength > 1.0e-8\n                ? move * targetSpeed\n                : glm::dvec3{};\n""",
    """            const double requestedSpeed = std::min(\n                creativeFlightSpeedMps_ * (input.sprint ? 4.0 : 1.0),\n                kCreativeInterstellarSprintMaxMps);\n            double targetSpeed = requestedSpeed;\n\n            // Creative interstellar travel is intentionally non-relativistic gameplay warp, but\n            // it must still approach real celestial geometry safely. Limit closing speed against\n            // every body in the current travel direction so a single frame cannot tunnel through\n            // a star/planet. Moving away from a body does not unnecessarily throttle escape.\n            if (moveLength > 1.0e-8 && celestialSystem_ != nullptr) {\n                const glm::dvec3 moveDirection = safeNormalize(move);\n                constexpr double approachHorizonSeconds = 0.75;\n                constexpr double minimumApproachLimitMps = 100000.0;\n                for (const auto& candidate : celestialSystem_->bodies()) {\n                    const glm::dvec3 toBody = candidate.position - position_;\n                    const double centerDistance = glm::length(toBody);\n                    if (centerDistance <= 1.0e-6) continue;\n                    const double closingCosine = glm::dot(moveDirection, toBody / centerDistance);\n                    if (closingCosine <= 0.05) continue;\n                    const double clearance = std::max(0.0, centerDistance - candidate.radiusMeters);\n                    const double safeClosingSpeed = std::max(\n                        minimumApproachLimitMps,\n                        clearance / (approachHorizonSeconds * closingCosine));\n                    targetSpeed = std::min(targetSpeed, safeClosingSpeed);\n                }\n            }\n            const glm::dvec3 desiredControl = moveLength > 1.0e-8\n                ? move * targetSpeed\n                : glm::dvec3{};\n""",
)

# 2) Feed physical solar angular radius to the fullscreen star renderer.
patch(
    "native/include/vf/render/VulkanRenderer.hpp",
    """    float sunIntensity{2.2F};\n    glm::vec3 skyAmbient{0.10F, 0.16F, 0.26F};\n""",
    """    float sunIntensity{2.2F};\n    float sunAngularRadiusRadians{0.004675F};\n    glm::vec3 skyAmbient{0.10F, 0.16F, 0.26F};\n""",
)

patch(
    "native/src/render/VulkanRenderer.cpp",
    """    skyPush.data1 = glm::vec4(safeNormalizeFloat(environment.sunDirectionToLight), 0.0F);\n""",
    """    skyPush.data1 = glm::vec4(\n        safeNormalizeFloat(environment.sunDirectionToLight),\n        std::clamp(environment.sunAngularRadiusRadians, 0.0001F, 1.45F));\n""",
)

patch(
    "native/src/render/VulkanRenderer.cpp",
    """            / std::log10(2000000.0F)),\n""",
    """            / std::log10(3.06987476992e11F)),\n""",
)

# 3) Physically sized, procedural close-Sun disc/corona. This is live shader rendering, no image asset.
patch(
    "native/shaders/planet.slang",
    """    float3 background = float3(0.00035, 0.00045, 0.00075) + proceduralStars(ray);\n    float sunAngularRadius = 0.004675;\n    float sunDisc = smoothstep(cos(sunAngularRadius * 1.15), cos(sunAngularRadius * 0.85), dot(ray, sunDir));\n    if (!hitsGround) background += gPush.data3.yzw * sunDisc * 18.0;\n""",
    """    float3 background = float3(0.00035, 0.00045, 0.00075) + proceduralStars(ray);\n\n    // Physical apparent size: at Aster this is ~0.267 deg radius; flying toward Helion expands\n    // the exact same star continuously until the disc fills the view. The surface is procedural\n    // shader detail, not a billboard image: granulation, active cells, sunspots, limb and corona.\n    float sunAngularRadius = clamp(abs(gPush.data1.w), 0.0001, 1.45);\n    float3 helper = abs(sunDir.y) < 0.92 ? float3(0.0, 1.0, 0.0) : float3(1.0, 0.0, 0.0);\n    float3 sunRight = normalize(cross(helper, sunDir));\n    float3 sunUp = normalize(cross(sunDir, sunRight));\n    float sinRadius = max(sin(sunAngularRadius), 1.0e-5);\n    float2 solarPlane = float2(dot(ray, sunRight), dot(ray, sunUp)) / sinRadius;\n    float solarR = length(solarPlane);\n    float solarAngle = atan2(solarPlane.y, solarPlane.x);\n\n    float coronaEnvelope = exp(-max(solarR - 1.0, 0.0) * 4.8) * smoothstep(1.85, 0.92, solarR);\n    float coronaRays = 0.55 + 0.45 * terrainFbm2(float2(solarAngle * 3.2, solarR * 2.7) + 41.0);\n    float prominenceRadius = 1.055 + 0.050 * sin(solarAngle * 5.0 + 0.7)\n        + 0.025 * sin(solarAngle * 11.0 - 1.2);\n    float prominence = exp(-abs(solarR - prominenceRadius) * 48.0)\n        * pow(saturate(0.55 + 0.45 * sin(solarAngle * 7.0 + 2.3)), 5.0)\n        * smoothstep(0.96, 1.01, solarR) * smoothstep(1.18, 1.03, solarR);\n    if (!hitsGround && solarR < 1.85) {\n        background += float3(1.00, 0.22, 0.025) * coronaEnvelope * coronaRays * 0.72;\n        background += float3(1.00, 0.12, 0.012) * prominence * 3.2;\n    }\n\n    if (!hitsGround && solarR <= 1.0) {\n        float solarZ = sqrt(max(0.0, 1.0 - solarR * solarR));\n        float2 sphereUv = solarPlane / max(0.24 + 0.76 * solarZ, 0.16);\n        float granA = terrainFbm2(sphereUv * 34.0 + 5.3);\n        float granB = terrainFbm2(sphereUv * 73.0 - 17.9);\n        float cells = saturate(granA * 0.72 + granB * 0.28);\n        float activeNoise = terrainFbm2(sphereUv * 4.1 + 67.2);\n        float magnetic = terrainFbm2(sphereUv * 8.7 - 29.4);\n        float active = smoothstep(0.63, 0.86, activeNoise) * smoothstep(0.42, 0.78, magnetic);\n        float spots = smoothstep(0.78, 0.94, activeNoise) * smoothstep(0.70, 0.91, 1.0 - magnetic);\n        float limb = pow(saturate(solarZ), 0.34);\n        float3 solarColor = lerp(\n            float3(2.2, 0.34, 0.025),\n            float3(7.2, 2.15, 0.20),\n            saturate(cells * 0.78 + active * 0.42));\n        solarColor *= 0.58 + 0.58 * limb;\n        solarColor = lerp(solarColor, solarColor * float3(0.14, 0.10, 0.08), spots * 0.82);\n        solarColor += float3(5.0, 1.25, 0.12) * active * 0.85;\n        background += solarColor * max(float3(0.75, 0.62, 0.48), gPush.data3.yzw);\n    }\n""",
)

# 4) Production runtime: physical angular size, actual ground Moon proof, and a real automated Sun transit.
patch(
    "native/src/app/Main.cpp",
    """        const bool captureEscapeInheritance = [] {\n            const char* value = std::getenv(\"VF_CAPTURE_ESCAPE_INHERITANCE\");\n            return value != nullptr && std::string_view{value} == \"1\";\n        }();\n""",
    """        const bool captureEscapeInheritance = [] {\n            const char* value = std::getenv(\"VF_CAPTURE_ESCAPE_INHERITANCE\");\n            return value != nullptr && std::string_view{value} == \"1\";\n        }();\n        const bool captureSunTransit = [] {\n            const char* value = std::getenv(\"VF_CAPTURE_SUN_TRANSIT\");\n            return value != nullptr && std::string_view{value} == \"1\";\n        }();\n""",
)

patch(
    "native/src/app/Main.cpp",
    """        if (captureEscapeInheritance) {\n            // Start only five kilometres inside the real precision-bubble boundary. The camera is\n""",
    """        if (captureSunTransit) {\n            // Real gameplay transit starts just outside Aster's production precision bubble, keeps\n            // the inherited orbital carrier and then uses ordinary creative-flight input toward the\n            // physically located Sun. No teleport occurs after this initial deterministic CI pose.\n            const glm::dvec3 sunwardWorld = safeNormalize(\n                sun.position - initialAster->position, {1.0, 0.0, 0.0});\n            const double departureRadius = initialAster->physicsBubbleRadiusMeters + 5000.0;\n            const glm::dvec3 departureWorld = initialAster->position + sunwardWorld * departureRadius;\n            camera.setExternalWorldState(departureWorld, initialAster->linearVelocity, false);\n            camera.setFlightMode(true);\n            camera.setCreativeFlightSpeedMps(vf::PlanetCamera::kCreativeInterstellarBaseMaxMps);\n            camera.setViewDirectionWorld(sun.position - departureWorld, camera.up());\n            std::cout << \"R24 sun transit armed: base_max_c=1024 sprint_max_c=4096\"\n                      << \" departure_clearance_km=\"\n                      << (departureRadius - initialAster->radiusMeters) / 1000.0 << '\\n';\n        }\n\n        if (captureEscapeInheritance) {\n            // Start only five kilometres inside the real precision-bubble boundary. The camera is\n""",
)

patch(
    "native/src/app/Main.cpp",
    """            movement.toggleFlight = input.toggleFlight;\n\n            const bool wasFlightMode = camera.flightMode();\n""",
    """            movement.toggleFlight = input.toggleFlight;\n            if (captureSunTransit) {\n                camera.setViewDirectionWorld(\n                    currentSun->position - camera.position(), camera.up());\n                movement.forward = 1.0;\n                movement.right = 0.0;\n                movement.vertical = 0.0;\n                movement.sprint = true;\n                movement.toggleFlight = false;\n            }\n\n            const bool wasFlightMode = camera.flightMode();\n""",
)

patch(
    "native/src/app/Main.cpp",
    """            const double irradiance = currentSun->luminosityWatts\n                / (4.0 * kPi * std::max(1.0, physicalSunDistance * physicalSunDistance));\n""",
    """            const double irradiance = currentSun->luminosityWatts\n                / (4.0 * kPi * std::max(1.0, physicalSunDistance * physicalSunDistance));\n            const double sunAngularRadiusRadians = std::asin(std::clamp(\n                currentSun->radiusMeters / std::max(physicalSunDistance, currentSun->radiusMeters),\n                0.0, 1.0));\n""",
)

patch(
    "native/src/app/Main.cpp",
    """            renderEnvironment.sunIntensity = static_cast<float>(\n                3.0 * std::clamp(irradiance / 1361.0, 0.0, 3.0));\n""",
    """            renderEnvironment.sunIntensity = static_cast<float>(\n                3.0 * std::clamp(irradiance / 1361.0, 0.0, 3.0));\n            renderEnvironment.sunAngularRadiusRadians = static_cast<float>(sunAngularRadiusRadians);\n""",
)

patch(
    "native/src/app/Main.cpp",
    """            renderer.drawFrame(viewProjection, cameraSurface, renderEnvironment);\n\n            diagnosticsTime += dt;\n""",
    """            renderer.drawFrame(viewProjection, cameraSurface, renderEnvironment);\n\n            if (captureSunTransit && runtimeDiagnosticsStdout) {\n                const double sunClearance = std::max(\n                    0.0, physicalSunDistance - currentSun->radiusMeters);\n                std::cout << \"R24 sun transit: distance_AU=\"\n                          << physicalSunDistance / 149597870700.0\n                          << \" clearance_solar_radii=\" << sunClearance / currentSun->radiusMeters\n                          << \" speed_c=\" << glm::length(camera.velocity())\n                              / vf::PlanetCamera::kSpeedOfLightMps\n                          << \" angular_diameter_deg=\"\n                          << (2.0 * sunAngularRadiusRadians * 180.0 / kPi) << '\\n';\n                if (sunClearance <= currentSun->radiusMeters * 0.90)\n                    std::cout << \"R24 SUN_TRANSIT_ARRIVED\n\";\n            }\n\n            diagnosticsTime += dt;\n""",
)

# 5) Regression gate for the enormous but guarded creative travel range.
patch(
    "native/tests/InterplanetaryFlightTests.cpp",
    """void testCreativeFlightCanLandOnSolidGround() {\n""",
    """void testCreativeFlightSupportsGuardedInterstellarWarp() {\n    vf::PlanetDefinition terrain{};\n    terrain.radius = 100.0;\n    terrain.maxElevation = 0.0;\n    terrain.atmosphereHeight = 20.0;\n\n    vf::CelestialSystem celestial;\n    vf::CelestialBody home{};\n    home.radiusMeters = terrain.radius;\n    home.physicsBubbleRadiusMeters = 300.0;\n    const auto homeId = celestial.addBody(home);\n\n    vf::CelestialBody star{};\n    star.type = vf::CelestialBodyType::Star;\n    star.radiusMeters = 1.0e6;\n    star.position = {1.0e9, 0.0, 0.0};\n    star.massKg = 1.0e20;\n    celestial.addBody(star);\n\n    vf::PlanetCamera camera{terrain, &celestial, homeId};\n    camera.setExternalWorldState({1000.0, 0.0, 0.0}, {}, false);\n    camera.setFlightMode(true);\n    camera.setCreativeFlightSpeedMps(vf::PlanetCamera::kCreativeInterstellarBaseMaxMps);\n    camera.setViewDirectionWorld({1.0, 0.0, 0.0}, {0.0, 1.0, 0.0});\n\n    vf::PlanetMovementInput thrust{};\n    thrust.forward = 1.0;\n    thrust.sprint = true;\n    for (int frame = 0; frame < 8; ++frame) camera.update(thrust, 1.0 / 60.0);\n\n    require(vf::PlanetCamera::kCreativeInterstellarSprintMaxMps\n            >= 4095.0 * vf::PlanetCamera::kSpeedOfLightMps,\n        \"creative interstellar travel must expose the intended 4096c sprint envelope\");\n    require(camera.velocity().x > 0.25 * vf::PlanetCamera::kSpeedOfLightMps,\n        \"free-space creative flight must accelerate into a genuinely interstellar travel band\");\n    require(camera.position().x < star.position.x - star.radiusMeters,\n        \"forward-body approach governor must prevent a single update sequence tunnelling through the star\");\n}\n\nvoid testCreativeFlightCanLandOnSolidGround() {\n""",
)

patch(
    "native/tests/InterplanetaryFlightTests.cpp",
    """    testCreativeFlightPreservesParentOrbitalVelocityAfterBubbleExit();\n    testCreativeFlightCanLandOnSolidGround();\n""",
    """    testCreativeFlightPreservesParentOrbitalVelocityAfterBubbleExit();\n    testCreativeFlightSupportsGuardedInterstellarWarp();\n    testCreativeFlightCanLandOnSolidGround();\n""",
)

print("R24 interstellar Sun closure applied")
