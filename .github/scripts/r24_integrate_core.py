#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel, text):
    (ROOT / rel).write_text(text, encoding="utf-8")


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"missing replacement anchor: {label}")
    return text.replace(old, new, 1)


def replace_between(text, start, end, replacement, label):
    i = text.find(start)
    if i < 0:
        raise RuntimeError(f"missing start anchor: {label}")
    j = text.find(end, i)
    if j < 0:
        raise RuntimeError(f"missing end anchor: {label}")
    return text[:i] + replacement.rstrip() + "\n\n" + text[j:]


# ---------------------------------------------------------------------------
# CMake: compile the unified body registry, SSE LOD builder and celestial light.
# ---------------------------------------------------------------------------
cmake = read("native/CMakeLists.txt")
cmake = replace_once(
    cmake,
    "    src/world/PlanetClimateGrid.cpp\n",
    "    src/world/PlanetClimateGrid.cpp\n"
    "    src/world/PlanetaryBodySystem.cpp\n"
    "    src/world/PlanetLodMeshBuilder.cpp\n",
    "CMake planetary sources",
)
cmake = replace_once(
    cmake,
    "    src/world/CelestialSystem.cpp\n",
    "    src/world/CelestialSystem.cpp\n    src/world/CelestialLighting.cpp\n",
    "CMake celestial lighting",
)
write("native/CMakeLists.txt", cmake)


# ---------------------------------------------------------------------------
# PhysicsWorld: one solid surface, climate wind, shared ocean spectrum, and
# distributed displaced-volume buoyancy for sphere/box/capsule/convex hull.
# ---------------------------------------------------------------------------
physics_path = "native/src/physics/PhysicsWorld.cpp"
physics = read(physics_path)

buoyancy_helpers = r'''[[nodiscard]] double sphereSubmergedFraction(double radius, double centerDepthBelowSurface) noexcept {
    if (radius <= kEpsilon) return centerDepthBelowSurface > 0.0 ? 1.0 : 0.0;
    if (centerDepthBelowSurface <= -radius) return 0.0;
    if (centerDepthBelowSurface >= radius) return 1.0;
    const double capHeight = std::clamp(centerDepthBelowSurface + radius, 0.0, 2.0 * radius);
    const double capVolume = kPi * capHeight * capHeight * (radius - capHeight / 3.0);
    const double sphereVolume = (4.0 / 3.0) * kPi * radius * radius * radius;
    return std::clamp(capVolume / sphereVolume, 0.0, 1.0);
}

struct BuoyancyVolumeSample {
    double fraction{};
    glm::dvec3 centerOfBuoyancy{};
};

[[nodiscard]] std::pair<glm::dvec3, glm::dvec3> localShapeBounds(const CollisionShape& shape) noexcept {
    switch (shape.type) {
    case CollisionShapeType::Sphere:
        return {-glm::dvec3{shape.radius}, glm::dvec3{shape.radius}};
    case CollisionShapeType::Box:
        return {-shape.halfExtents, shape.halfExtents};
    case CollisionShapeType::Capsule: {
        const glm::dvec3 extent{shape.radius, shape.halfHeight + shape.radius, shape.radius};
        return {-extent, extent};
    }
    case CollisionShapeType::ConvexHull:
        if (shape.convexHullData) return {shape.convexHullData->localMinimum, shape.convexHullData->localMaximum};
        break;
    }
    return {-glm::dvec3{0.5}, glm::dvec3{0.5}};
}

[[nodiscard]] bool pointInsideLocalShape(const CollisionShape& shape, const glm::dvec3& p) noexcept {
    switch (shape.type) {
    case CollisionShapeType::Sphere:
        return glm::dot(p, p) <= shape.radius * shape.radius;
    case CollisionShapeType::Box:
        return std::abs(p.x) <= shape.halfExtents.x
            && std::abs(p.y) <= shape.halfExtents.y
            && std::abs(p.z) <= shape.halfExtents.z;
    case CollisionShapeType::Capsule: {
        const double segmentY = std::clamp(p.y, -shape.halfHeight, shape.halfHeight);
        const glm::dvec3 delta = p - glm::dvec3{0.0, segmentY, 0.0};
        return glm::dot(delta, delta) <= shape.radius * shape.radius;
    }
    case CollisionShapeType::ConvexHull: {
        if (!shape.convexHullData || shape.convexHullData->points.empty()) return false;
        // A support-function interior test. A point in a convex set must lie behind every support
        // plane. Fourteen well-separated directions are deterministic and avoid pretending the
        // hull's AABB is displaced fluid volume; exact CAD buoyancy can later provide tetrahedra.
        static const std::array<glm::dvec3, 14> directions{{
            {1,0,0},{-1,0,0},{0,1,0},{0,-1,0},{0,0,1},{0,0,-1},
            {1,1,1},{1,1,-1},{1,-1,1},{-1,1,1},
            {-1,-1,1},{-1,1,-1},{1,-1,-1},{-1,-1,-1}}};
        for (glm::dvec3 d : directions) {
            d = safeNormalize(d);
            double support = -std::numeric_limits<double>::infinity();
            for (const glm::dvec3& q : shape.convexHullData->points)
                support = std::max(support, glm::dot(q, d));
            if (glm::dot(p, d) > support + 1.0e-7) return false;
        }
        return true;
    }
    }
    return false;
}

[[nodiscard]] BuoyancyVolumeSample sampleSubmergedVolume(
    const RigidBody& body,
    const PhysicsEnvironment& environment,
    double timeSeconds) noexcept {
    BuoyancyVolumeSample result{};
    const auto [minimum, maximum] = localShapeBounds(body.collisionShape);
    constexpr int samplesPerAxis = 5;
    int insideCount = 0;
    int submergedCount = 0;
    glm::dvec3 submergedSum{};
    const glm::dvec3 oceanCenter = primaryOceanCenter(environment);

    for (int z = 0; z < samplesPerAxis; ++z) {
        for (int y = 0; y < samplesPerAxis; ++y) {
            for (int x = 0; x < samplesPerAxis; ++x) {
                const glm::dvec3 t{
                    (static_cast<double>(x) + 0.5) / samplesPerAxis,
                    (static_cast<double>(y) + 0.5) / samplesPerAxis,
                    (static_cast<double>(z) + 0.5) / samplesPerAxis};
                const glm::dvec3 local = minimum + (maximum - minimum) * t;
                if (!pointInsideLocalShape(body.collisionShape, local)) continue;
                ++insideCount;
                const glm::dvec3 world = body.position + body.orientation * local;
                const double radialDistance = glm::length(world - oceanCenter);
                if (radialDistance <= environment.oceanSurfaceRadiusAt(world, timeSeconds)) {
                    ++submergedCount;
                    submergedSum += world;
                }
            }
        }
    }
    if (insideCount == 0 || submergedCount == 0) return result;
    result.fraction = static_cast<double>(submergedCount) / static_cast<double>(insideCount);
    result.centerOfBuoyancy = submergedSum / static_cast<double>(submergedCount);
    return result;
}'''
physics = replace_between(
    physics,
    "[[nodiscard]] double sphereSubmergedFraction",
    "[[nodiscard]] double combineFriction",
    buoyancy_helpers,
    "buoyancy helpers",
)

# forward declaration is needed because buoyancy helper sits above the original center helper
physics = replace_once(
    physics,
    "[[nodiscard]] glm::dvec3 safeNormalize(\n",
    "[[nodiscard]] glm::dvec3 primaryOceanCenter(const PhysicsEnvironment& environment) noexcept;\n\n"
    "[[nodiscard]] glm::dvec3 safeNormalize(\n",
    "primary ocean center forward declaration",
)

new_environment = r'''double PhysicsEnvironment::gravityMagnitude(const glm::dvec3& position) const noexcept {
    if (celestialSystem != nullptr) return glm::length(celestialSystem->gravityAccelerationAt(position));
    const double radius = std::max(planet.radius, 1.0);
    const double distance = std::max(glm::length(position), radius * 0.25);
    const double ratio = radius / distance;
    return std::max(0.0, surfaceGravity) * ratio * ratio;
}

glm::dvec3 PhysicsEnvironment::gravityAcceleration(const glm::dvec3& position) const noexcept {
    if (celestialSystem != nullptr) return celestialSystem->gravityAccelerationAt(position);
    const glm::dvec3 outward = safeNormalize(position);
    return -outward * gravityMagnitude(position);
}

double PhysicsEnvironment::solidSurfaceRadius(const glm::dvec3& direction) const noexcept {
    return surfaceAuthority != nullptr
        ? surfaceAuthority->surfaceRadius(direction)
        : planetSurfaceRadius(planet, direction);
}

glm::dvec3 PhysicsEnvironment::solidSurfaceNormal(const glm::dvec3& direction) const noexcept {
    return surfaceAuthority != nullptr
        ? surfaceAuthority->surfaceNormal(direction)
        : planetSurfaceNormal(planet, direction);
}

double PhysicsEnvironment::oceanSurfaceRadiusAt(
    const glm::dvec3& position,
    double timeSeconds) const noexcept {
    if (!ocean.enabled) return -std::numeric_limits<double>::infinity();
    if (oceanSpectrum == nullptr) return ocean.surfaceRadius;

    const glm::dvec3 center = primaryOceanCenter(*this);
    glm::dvec3 local = position - center;
    const CelestialBody* primary = nullptr;
    if (celestialSystem != nullptr && primaryCelestialBodyId != 0U)
        primary = celestialSystem->body(primaryCelestialBodyId);
    if (primary != nullptr) local = glm::conjugate(glm::normalize(primary->orientation)) * local;
    const glm::dvec3 outward = safeNormalize(local);
    const double latitude = std::asin(std::clamp(outward.y, -1.0, 1.0));
    const double longitude = std::atan2(outward.z, outward.x);
    const double radius = std::max(1.0, planet.radius);
    const glm::dvec2 tangentCoordinates{
        radius * longitude * std::max(0.05, std::cos(latitude)),
        radius * latitude};
    const OceanSurfaceSample wave = oceanSpectrum->sample(
        tangentCoordinates, timeSeconds, std::max(0.1, gravityMagnitude(position)));
    return ocean.surfaceRadius + wave.heightMeters;
}

AtmosphereSample PhysicsEnvironment::sampleAtmosphere(const glm::dvec3& position, double timeSeconds) const noexcept {
    (void)timeSeconds;
    if (climateGrid != nullptr) {
        const glm::dvec3 center = primaryOceanCenter(*this);
        const glm::dvec3 offset = position - center;
        const double radius = glm::length(offset);
        if (radius <= kEpsilon) return {};
        glm::dvec3 bodyLocalDirectionValue = offset / radius;
        const CelestialBody* primary = nullptr;
        if (celestialSystem != nullptr && primaryCelestialBodyId != 0U)
            primary = celestialSystem->body(primaryCelestialBodyId);
        if (primary != nullptr)
            bodyLocalDirectionValue = bodyLocalDirection(*primary, bodyLocalDirectionValue);
        const double altitude = std::max(0.0, radius - solidSurfaceRadius(bodyLocalDirectionValue));
        if (planet.atmosphereHeight > 0.0 && altitude > planet.atmosphereHeight) {
            AtmosphereSample vacuum{};
            vacuum.temperatureK = 2.725;
            return vacuum;
        }
        const PlanetClimateSample climate = climateGrid->sample(bodyLocalDirectionValue, altitude);
        AtmosphereSample sample{};
        sample.temperatureK = climate.temperatureK;
        sample.pressurePa = climate.pressurePa;
        sample.densityKgPerM3 = climate.densityKgPerM3;
        sample.windVelocity = climate.windBodyLocalMps;
        if (primary != nullptr) {
            sample.windVelocity = primary->linearVelocity
                + celestialSurfaceVelocity(*primary, position) - primary->linearVelocity
                + primary->orientation * climate.windBodyLocalMps;
        }
        return sample;
    }

    if (celestialSystem != nullptr) {
        const auto celestialSample = celestialSystem->sampleEnvironment(position);
        AtmosphereSample sample{};
        sample.temperatureK = celestialSample.temperatureK;
        sample.pressurePa = celestialSample.pressurePa;
        sample.densityKgPerM3 = celestialSample.densityKgPerM3;
        sample.windVelocity = celestialSample.windVelocity;
        return sample;
    }

    AtmosphereSample sample{};
    const double altitude = std::max(0.0, glm::length(position) - planet.radius);
    if (planet.atmosphereHeight > 0.0 && altitude > planet.atmosphereHeight) {
        sample.temperatureK = 2.725;
        return sample;
    }
    const auto& model = atmosphere;
    const double baseTemperature = std::max(120.0, model.seaLevelTemperatureK + model.temperatureOffsetK);
    const double lapse = std::max(0.0, model.lapseRateKPerM);
    sample.temperatureK = std::max(120.0, baseTemperature - lapse * altitude);
    const double g = std::max(0.01, gravityMagnitude(position));
    const double basePressure = std::max(0.0, model.seaLevelPressurePa * model.pressureScale);
    if (lapse > 1.0e-8) {
        const double exponent = g * model.molarMassKgPerMol / (model.universalGasConstant * lapse);
        const double ratio = std::max(1.0e-6, sample.temperatureK / baseTemperature);
        sample.pressurePa = basePressure * std::pow(ratio, exponent);
    } else {
        const double specificGasConstant = model.universalGasConstant / model.molarMassKgPerMol;
        sample.pressurePa = basePressure * std::exp(-g * altitude / (specificGasConstant * sample.temperatureK));
    }
    const double specificGasConstant = model.universalGasConstant / model.molarMassKgPerMol;
    sample.densityKgPerM3 = sample.temperatureK > 0.0
        ? sample.pressurePa / (specificGasConstant * sample.temperatureK)
        : 0.0;
    const glm::dvec3 outward = safeNormalize(position);
    glm::dvec3 tangentWind = model.prevailingWind - outward * glm::dot(model.prevailingWind, outward);
    const double altitudeFade = planet.atmosphereHeight > 0.0
        ? std::exp(-altitude / std::max(1.0, planet.atmosphereHeight * 1.5))
        : 1.0;
    sample.windVelocity = tangentWind * weather.windMultiplier * altitudeFade;
    return sample;
}

glm::dvec3 PhysicsEnvironment::fluidVelocity(const glm::dvec3& position, double timeSeconds) const noexcept {
    if (!ocean.enabled) return {};
    const glm::dvec3 center = primaryOceanCenter(*this);
    glm::dvec3 localPosition = position - center;
    const CelestialBody* primary = nullptr;
    if (celestialSystem != nullptr && primaryCelestialBodyId != 0U)
        primary = celestialSystem->body(primaryCelestialBodyId);
    if (primary != nullptr)
        localPosition = glm::conjugate(glm::normalize(primary->orientation)) * localPosition;
    const glm::dvec3 outward = safeNormalize(localPosition);
    const glm::dvec3 east = safeNormalize(glm::dvec3{-outward.z, 0.0, outward.x}, {1.0, 0.0, 0.0});
    const glm::dvec3 north = safeNormalize(glm::cross(outward, east), {0.0, 0.0, 1.0});
    glm::dvec3 localVelocity = ocean.meanCurrent - outward * glm::dot(ocean.meanCurrent, outward);

    if (oceanSpectrum != nullptr) {
        const double latitude = std::asin(std::clamp(outward.y, -1.0, 1.0));
        const double longitude = std::atan2(outward.z, outward.x);
        const double radius = std::max(1.0, planet.radius);
        const glm::dvec2 tangentCoordinates{
            radius * longitude * std::max(0.05, std::cos(latitude)),
            radius * latitude};
        const OceanSurfaceSample wave = oceanSpectrum->sample(
            tangentCoordinates, timeSeconds, std::max(0.1, gravityMagnitude(position)));
        localVelocity += east * wave.tangentVelocityMps.x
            + north * wave.tangentVelocityMps.y
            + outward * wave.verticalVelocityMps;
    }

    if (primary == nullptr) return localVelocity;
    const glm::dvec3 worldOffset = position - primary->position;
    const glm::dvec3 omega = safeNormalize(primary->spinAxis) * primary->spinRateRadPerSecond;
    return primary->linearVelocity + glm::cross(omega, worldOffset)
        + primary->orientation * localVelocity;
}'''
physics = replace_between(
    physics,
    "double PhysicsEnvironment::gravityMagnitude",
    "PhysicsWorld::PhysicsWorld",
    new_environment,
    "physics environment methods",
)

new_buoyancy_forces = r'''    if (!rigidBody.buoyancy.enabled || !environment_.ocean.enabled
        || rigidBody.buoyancy.displacedVolume <= 0.0 || gravity <= 0.0) return;

    const BuoyancyVolumeSample submerged = sampleSubmergedVolume(
        rigidBody, environment_, simulationTime_);
    if (submerged.fraction <= 0.0) return;

    const glm::dvec3 oceanCenter = primaryOceanCenter(environment_);
    const glm::dvec3 outward = safeNormalize(submerged.centerOfBuoyancy - oceanCenter);
    const double displacedVolume = rigidBody.buoyancy.displacedVolume * submerged.fraction;
    const glm::dvec3 buoyancyForce = outward
        * (environment_.ocean.densityKgPerM3 * displacedVolume * gravity);
    rigidBody.addForceAtPoint(buoyancyForce, submerged.centerOfBuoyancy);

    const glm::dvec3 relativeWaterVelocity = rigidBody.velocityAtPoint(submerged.centerOfBuoyancy)
        - environment_.fluidVelocity(submerged.centerOfBuoyancy, simulationTime_);
    const double waterSpeed = glm::length(relativeWaterVelocity);
    if (waterSpeed > 1.0e-5) {
        const double waterDrag = 0.5 * environment_.ocean.densityKgPerM3 * waterSpeed * waterSpeed
            * std::max(0.0, rigidBody.buoyancy.fluidDragCoefficient)
            * std::max(0.0, rigidBody.buoyancy.fluidReferenceArea)
            * submerged.fraction;
        rigidBody.addForceAtPoint(
            -(relativeWaterVelocity / waterSpeed) * waterDrag,
            submerged.centerOfBuoyancy);
    }
}'''
start = "    if (!rigidBody.buoyancy.enabled || !environment_.ocean.enabled || rigidBody.buoyancy.displacedVolume <= 0.0) return;"
physics = replace_between(
    physics,
    start,
    "void PhysicsWorld::integrateBody",
    new_buoyancy_forces,
    "environment water forces",
)

new_planet_contact = r'''void PhysicsWorld::solvePlanetContact(RigidBody& rigidBody) {
    if (rigidBody.motionType != MotionType::Dynamic || rigidBody.sleeping) return;

    glm::dvec3 bodyCenter{};
    bool useProceduralPrimary = false;
    const CelestialBody* contactCelestialBody = nullptr;
    double nearestSurfaceGap = std::numeric_limits<double>::infinity();

    if (environment_.celestialSystem != nullptr) {
        for (const auto& celestialBody : environment_.celestialSystem->bodies()) {
            if (celestialBody.type == CelestialBodyType::Star) continue;
            const glm::dvec3 offset = rigidBody.position - celestialBody.position;
            const double distance = glm::length(offset);
            if (distance <= kEpsilon) continue;
            const glm::dvec3 radial = offset / distance;
            const bool procedural = celestialBody.id == environment_.primaryCelestialBodyId;
            const double radius = procedural
                ? environment_.solidSurfaceRadius(bodyLocalDirection(celestialBody, radial))
                : celestialBody.radiusMeters;
            const double gap = std::abs(distance - radius);
            if (gap < nearestSurfaceGap) {
                nearestSurfaceGap = gap;
                contactCelestialBody = &celestialBody;
                useProceduralPrimary = procedural;
            }
        }
        if (contactCelestialBody == nullptr) return;
        bodyCenter = contactCelestialBody->position;
    }

    glm::dvec3 radial = safeNormalize(rigidBody.position - bodyCenter);
    double surfaceRadius = 0.0;
    glm::dvec3 normal = radial;
    if (useProceduralPrimary || environment_.celestialSystem == nullptr) {
        const glm::dvec3 localDirection = contactCelestialBody != nullptr
            ? bodyLocalDirection(*contactCelestialBody, radial)
            : radial;
        surfaceRadius = environment_.solidSurfaceRadius(localDirection);
        const glm::dvec3 localNormal = environment_.solidSurfaceNormal(localDirection);
        normal = contactCelestialBody != nullptr
            ? safeNormalize(contactCelestialBody->orientation * localNormal, radial)
            : localNormal;
    } else {
        surfaceRadius = contactCelestialBody->radiusMeters;
    }

    glm::dvec3 surfacePoint = bodyCenter + radial * surfaceRadius;
    glm::dvec3 contactPoint = supportPoint(rigidBody.collisionShape, rigidBody.shapePose(), -normal);
    double penetration = -glm::dot(contactPoint - surfacePoint, normal);
    if (penetration <= 0.0) return;

    rigidBody.position += normal * penetration;
    radial = safeNormalize(rigidBody.position - bodyCenter, radial);
    if (useProceduralPrimary || environment_.celestialSystem == nullptr) {
        const glm::dvec3 localDirection = contactCelestialBody != nullptr
            ? bodyLocalDirection(*contactCelestialBody, radial)
            : radial;
        surfaceRadius = environment_.solidSurfaceRadius(localDirection);
        const glm::dvec3 localNormal = environment_.solidSurfaceNormal(localDirection);
        normal = contactCelestialBody != nullptr
            ? safeNormalize(contactCelestialBody->orientation * localNormal, radial)
            : localNormal;
    } else {
        normal = radial;
    }
    surfacePoint = bodyCenter + radial * surfaceRadius;
    contactPoint = supportPoint(rigidBody.collisionShape, rigidBody.shapePose(), -normal);

    const glm::dvec3 surfaceVelocity = contactCelestialBody != nullptr
        ? celestialSurfaceVelocity(*contactCelestialBody, contactPoint)
        : glm::dvec3{};
    glm::dvec3 relativePointVelocity = rigidBody.velocityAtPoint(contactPoint) - surfaceVelocity;
    const double normalVelocity = glm::dot(relativePointVelocity, normal);
    double normalImpulseMagnitude = 0.0;
    if (normalVelocity < 0.0) {
        const double restitution = std::clamp(rigidBody.material.restitution, 0.0, 1.0);
        const double targetSeparationSpeed = normalVelocity < -kRestitutionThreshold
            ? -restitution * normalVelocity : 0.0;
        const double inverseEffectiveMass = effectiveMassAgainstStatic(rigidBody, contactPoint, normal);
        normalImpulseMagnitude = (targetSeparationSpeed - normalVelocity) / inverseEffectiveMass;
        if (normalImpulseMagnitude > 0.0)
            rigidBody.applyImpulseAtPoint(normal * normalImpulseMagnitude, contactPoint);
    }

    relativePointVelocity = rigidBody.velocityAtPoint(contactPoint) - surfaceVelocity;
    const glm::dvec3 tangentVelocity = relativePointVelocity
        - normal * glm::dot(relativePointVelocity, normal);
    const double tangentSpeed = glm::length(tangentVelocity);
    if (tangentSpeed > 1.0e-7) {
        const glm::dvec3 tangent = tangentVelocity / tangentSpeed;
        const double supportingImpulse = std::max(
            normalImpulseMagnitude,
            rigidBody.mass * environment_.gravityMagnitude(rigidBody.position) * fixedDeltaSeconds_);
        const double maxFrictionImpulse = std::max(0.0, rigidBody.material.friction) * supportingImpulse;
        const double inverseEffectiveMass = effectiveMassAgainstStatic(rigidBody, contactPoint, tangent);
        const double stopImpulse = tangentSpeed / inverseEffectiveMass;
        rigidBody.applyImpulseAtPoint(
            -tangent * std::min(stopImpulse, maxFrictionImpulse), contactPoint);
    }

    rigidBody.angularVelocity *= std::exp(
        -std::max(0.0, rigidBody.material.rollingResistance) * 30.0 * fixedDeltaSeconds_);
}'''
physics = replace_between(
    physics,
    "void PhysicsWorld::solvePlanetContact",
    "void PhysicsWorld::solveBodyContacts",
    new_planet_contact,
    "unified planet contact",
)
write(physics_path, physics)


# ---------------------------------------------------------------------------
# Character controller: use the same surface authority and remove exaggerated
# 65 km/h sprint / ~2 m jump / strong airborne steering defaults.
# ---------------------------------------------------------------------------
cc_h = read("native/include/vf/player/CharacterController.hpp")
cc_h = replace_once(cc_h, "double walkSpeed{9.0};", "double walkSpeed{4.8};", "walk speed")
cc_h = replace_once(cc_h, "double sprintSpeed{18.0};", "double sprintSpeed{8.2};", "sprint speed")
cc_h = replace_once(cc_h, "double jumpSpeed{6.2};", "double jumpSpeed{4.7};", "jump speed")
cc_h = replace_once(cc_h, "double groundAcceleration{28.0};", "double groundAcceleration{38.0};", "ground acceleration")
cc_h = replace_once(cc_h, "double airAcceleration{7.0};", "double airAcceleration{1.6};", "air acceleration")
write("native/include/vf/player/CharacterController.hpp", cc_h)

cc = read("native/src/player/CharacterController.cpp")
old_query = '''        if (body != nullptr) {
            const glm::dvec3 localDirection = bodyLocalDirection(*body, radialDirection);
            surfaceRadius = planetSurfaceRadius(environment.planet, localDirection);
            sample.normal = bodyWorldNormal(*body, environment.planet, radialDirection);
        } else {
            surfaceRadius = planetSurfaceRadius(environment.planet, radialDirection);
            sample.normal = planetSurfaceNormal(environment.planet, radialDirection);
        }'''
new_query = '''        if (body != nullptr) {
            const glm::dvec3 localDirection = bodyLocalDirection(*body, radialDirection);
            surfaceRadius = environment.solidSurfaceRadius(localDirection);
            sample.normal = safeNormalize(
                glm::normalize(body->orientation) * environment.solidSurfaceNormal(localDirection),
                radialDirection);
        } else {
            surfaceRadius = environment.solidSurfaceRadius(radialDirection);
            sample.normal = environment.solidSurfaceNormal(radialDirection);
        }'''
cc = replace_once(cc, old_query, new_query, "character unified surface query")
write("native/src/player/CharacterController.cpp", cc)


# ---------------------------------------------------------------------------
# Existing celestial test must no longer assert that gravity becomes zero when
# leaving a reference-frame bubble. Bubbles are coordinate/streaming domains.
# ---------------------------------------------------------------------------
ct = read("native/tests/CelestialSystemTests.cpp")
old = '''    require(system.gameplayReferenceBodyAt(midpoint) == nullptr,
        "space outside every planetary SOI must not secretly belong to the primary planet");
    require(glm::length(system.gravityAccelerationAt(midpoint)) < 1.0e-9,
        "without a star, free interplanetary space outside SOIs must have negligible gameplay gravity");'''
new = '''    require(system.gameplayReferenceBodyAt(midpoint) == nullptr,
        "space outside every physics bubble must remain in the inertial frame");
    require(glm::length(system.gravityAccelerationAt(midpoint)) > 1.0e-6,
        "leaving a reference-frame bubble must not delete Newtonian gravity");'''
ct = replace_once(ct, old, new, "celestial bubble gravity test")
write("native/tests/CelestialSystemTests.cpp", ct)

print("R24 core source integration complete")
