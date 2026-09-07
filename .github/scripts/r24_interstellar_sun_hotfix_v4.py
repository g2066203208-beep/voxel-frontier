#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def patch(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"anchor not found in {path}: {old[:140]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# Interstellar creative motion is allowed to cross astronomical distances in one rendered frame.
# Distance-based target-speed limiting alone therefore cannot guarantee that a fast residual carrier
# does not tunnel through a celestial body. Sweep the whole previous->proposed segment against a
# safety sphere. Stars stop at 2R center distance (one stellar radius above the photosphere), while
# planets/moons keep a much tighter 2% / 2 km clearance so normal approaches still work.
patch(
    "native/src/player/PlanetCamera.cpp",
    """        position_ += velocity_ * dt;\n        if (const auto* newFrame = celestialSystem_->physicsReferenceBodyAt(position_)) enterPhysicsFrame(*newFrame);\n        return;\n""",
    """        const glm::dvec3 previousPosition = position_;\n        glm::dvec3 proposedPosition = position_ + velocity_ * dt;\n        if (flightMode_) {\n            const glm::dvec3 segment = proposedPosition - previousPosition;\n            const double segmentLengthSquared = glm::dot(segment, segment);\n            if (segmentLengthSquared > 1.0e-12) {\n                double earliestHit = 1.0;\n                const CelestialBody* hitBody = nullptr;\n                double hitSafeRadius = 0.0;\n                for (const auto& candidate : celestialSystem_->bodies()) {\n                    const double safeRadius = candidate.type == CelestialBodyType::Star\n                        ? candidate.radiusMeters * 2.0\n                        : candidate.radiusMeters + std::max(2000.0, candidate.radiusMeters * 0.02);\n                    if (safeRadius <= 0.0) continue;\n                    const glm::dvec3 relativeStart = previousPosition - candidate.position;\n                    const double c = glm::dot(relativeStart, relativeStart) - safeRadius * safeRadius;\n                    if (c <= 0.0) continue;\n                    const double b = glm::dot(relativeStart, segment);\n                    const double discriminant = b * b - segmentLengthSquared * c;\n                    if (discriminant < 0.0) continue;\n                    const double root = (-b - std::sqrt(discriminant)) / segmentLengthSquared;\n                    if (root >= 0.0 && root <= earliestHit) {\n                        earliestHit = root;\n                        hitBody = &candidate;\n                        hitSafeRadius = safeRadius;\n                    }\n                }\n                if (hitBody != nullptr) {\n                    const double backedOffHit = std::max(0.0, earliestHit - 1.0e-7);\n                    proposedPosition = previousPosition + segment * backedOffHit;\n                    const glm::dvec3 contactNormal = safeNormalize(\n                        proposedPosition - hitBody->position, {1.0, 0.0, 0.0});\n                    // Snap exactly outside the safety sphere to remove floating-point ambiguity at\n                    // AU scale, then remove only inward relative velocity. Tangential/orbital motion\n                    // is preserved so the player can skim around a star instead of being frozen.\n                    proposedPosition = hitBody->position + contactNormal * hitSafeRadius;\n                    const glm::dvec3 relativeVelocity = velocity_ - hitBody->linearVelocity;\n                    const double inwardSpeed = glm::dot(relativeVelocity, contactNormal);\n                    if (inwardSpeed < 0.0) {\n                        velocity_ -= contactNormal * inwardSpeed;\n                        if (inertialFlightCarrierValid_)\n                            inertialFlightControlVelocity_ = velocity_ - inertialFlightCarrierVelocity_;\n                    }\n                }\n            }\n        }\n        position_ = proposedPosition;\n        if (const auto* newFrame = celestialSystem_->physicsReferenceBodyAt(position_)) enterPhysicsFrame(*newFrame);\n        return;\n""",
)

# Arrival is intentionally one stellar radius above the photosphere. At this distance the physical
# solar angular diameter is 60 degrees: close enough to inspect surface structure without clipping
# inside the star.
patch(
    "native/src/app/Main.cpp",
    """                if (sunClearance <= currentSun->radiusMeters * 0.90)\n                    std::cout << \"R24 SUN_TRANSIT_ARRIVED\\n\";\n""",
    """                if (sunClearance <= currentSun->radiusMeters * 1.05)\n                    std::cout << \"R24 SUN_TRANSIT_ARRIVED\\n\";\n""",
)

# Keep close-Sun texture visible after ACES. The former HDR values intentionally overpowered the
# tone mapper and produced a featureless white framebuffer at close range.
shader = ROOT / "native/shaders/planet.slang"
text = shader.read_text(encoding="utf-8")
replacements = {
    "float3(1.00, 0.22, 0.025) * coronaEnvelope * coronaRays * 0.72":
        "float3(0.72, 0.16, 0.018) * coronaEnvelope * coronaRays * 0.42",
    "float3(1.00, 0.12, 0.012) * prominence * 3.2":
        "float3(1.00, 0.10, 0.010) * prominence * 1.35",
    "float3(2.2, 0.34, 0.025),\n            float3(7.2, 2.15, 0.20),":
        "float3(0.95, 0.22, 0.018),\n            float3(2.15, 0.78, 0.10),",
    "float3(5.0, 1.25, 0.12) * active * 0.85":
        "float3(1.35, 0.38, 0.055) * active * 0.62",
    "max(float3(0.75, 0.62, 0.48), gPush.data3.yzw)":
        "max(float3(0.62, 0.52, 0.42), gPush.data3.yzw * 0.72)",
}
for old, new in replacements.items():
    if new in text:
        continue
    if old not in text:
        raise SystemExit(f"solar tone anchor not found: {old!r}")
    text = text.replace(old, new, 1)
shader.write_text(text, encoding="utf-8")

# Regression: a huge inherited inertial carrier must not tunnel through a star in one frame.
test_path = ROOT / "native/tests/InterplanetaryFlightTests.cpp"
test_text = test_path.read_text(encoding="utf-8")
function = r'''void testInterstellarCreativeSweepCannotTunnelThroughStar() {
    vf::PlanetDefinition terrain{};
    terrain.radius = 100.0;
    terrain.maxElevation = 0.0;
    terrain.atmosphereHeight = 10.0;

    vf::CelestialSystem celestial;
    vf::CelestialBody home{};
    home.type = vf::CelestialBodyType::Planet;
    home.radiusMeters = 100.0;
    home.massKg = 1.0e12;
    home.physicsBubbleRadiusMeters = 250.0;
    const auto homeId = celestial.addBody(home);

    vf::CelestialBody star{};
    star.type = vf::CelestialBodyType::Star;
    star.radiusMeters = 1000.0;
    star.massKg = 1.0e20;
    star.position = {100000.0, 0.0, 0.0};
    const auto starId = celestial.addBody(star);
    require(starId != 0U, "swept-star regression requires a registered star");

    vf::PlanetCamera camera{terrain, &celestial, homeId};
    // Place the player well outside the home bubble with an intentionally absurd inherited carrier
    // that would cross the star and its 2R safety envelope in a single 50 ms frame.
    camera.setExternalWorldState({90000.0, 0.0, 0.0}, {500000.0, 0.0, 0.0}, false);
    camera.setFlightMode(true);
    vf::PlanetMovementInput idle{};
    camera.update(idle, 0.05);

    const auto* liveStar = celestial.body(starId);
    require(liveStar != nullptr, "swept-star regression star must remain valid");
    const double distance = glm::length(camera.position() - liveStar->position);
    require(distance >= liveStar->radiusMeters * 2.0 - 1.0e-3,
        "creative interstellar sweep must stop outside the 2R stellar inspection envelope");
    const glm::dvec3 outward = glm::normalize(camera.position() - liveStar->position);
    require(glm::dot(camera.velocity() - liveStar->linearVelocity, outward) >= -1.0e-6,
        "stellar sweep contact must remove residual inward velocity instead of repeatedly tunnelling");
}'''
if function not in test_text:
    anchor = "\n} // namespace\n\nint main() {"
    if anchor not in test_text:
        raise SystemExit("interplanetary test namespace anchor missing")
    test_text = test_text.replace(anchor, "\n\n" + function + "\n\n} // namespace\n\nint main() {", 1)
call = "    testInterstellarCreativeSweepCannotTunnelThroughStar();\n"
if call not in test_text:
    anchor = "    testPhysicalGravityInsidePhysicsBubbleRemainsBallistic();\n"
    if anchor not in test_text:
        raise SystemExit("interplanetary test main anchor missing")
    test_text = test_text.replace(anchor, anchor + call, 1)
test_path.write_text(test_text, encoding="utf-8")

print("R24 interstellar Sun closure hotfix V4 applied")
