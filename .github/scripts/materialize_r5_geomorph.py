from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing replacement anchor: {label}")
    return text.replace(old, new, 1)


# -----------------------------------------------------------------------------
# Global geomorph: preserve Priority-Flood / discharge authority, but expose a
# narrow continuous river centerline from the coarse hydrology graph and sharpen
# actual orogenic ridges instead of broad elevated slabs.
# -----------------------------------------------------------------------------
geomorph_path = Path("native/include/vf/world/PlanetGeomorph.hpp")
g = geomorph_path.read_text()

g = replace_once(
    g,
    "    double river{};\n    double floodplain{};",
    "    double river{};\n    double channel{};\n    double floodplain{};",
    "GlobalGeomorphSample channel field",
)

g = replace_once(
    g,
    "    std::vector<float> floodplain;\n    std::vector<float> incision;",
    "    std::vector<float> floodplain;\n    std::vector<float> incision;\n    std::vector<int> receiver;",
    "Field receiver member",
)

g = replace_once(
    g,
    "          elevation(kCount), continental(kCount), mountain(kCount), river(kCount),\n          floodplain(kCount), incision(kCount) {",
    "          elevation(kCount), continental(kCount), mountain(kCount), river(kCount),\n          floodplain(kCount), incision(kCount), receiver(kCount, -1) {",
    "Field receiver initialization",
)

g = replace_once(
    g,
    "        std::vector<double> discharge(kCount, 0.0);\n        std::vector<int> receiver(kCount, -1);\n        std::vector<float> localSlope(kCount, 0.0F);",
    "        std::vector<double> discharge(kCount, 0.0);\n        std::fill(receiver.begin(), receiver.end(), -1);\n        std::vector<float> localSlope(kCount, 0.0F);",
    "receiver local-to-member",
)

old_orogen = '''                const double ridgeCore = std::pow(smooth01(0.34, 0.88, ridge), 1.65);\n                const double range = orogen * (0.16 + 0.84 * ridgeCore);\n\n                double h = 0.0;\n                h += land * (280.0 + 720.0 * broad + 420.0 * province);\n                // Orogenic belts get modest broad uplift, while high elevation is concentrated\n                // on ridge cores. This avoids the previous several-kilometre-tall smooth slab.\n                h += orogen * 850.0 + range * (900.0 + 3600.0 * ridgeCore);\n                h += land * smooth01(0.55, 0.83, 0.5 + 0.5 * fbm(seed ^ 0xBB67AE8584CAA73BULL, d, 5.8, 4)) * 900.0;'''
new_orogen = '''                const double ridgeCore = std::pow(smooth01(0.34, 0.88, ridge), 1.82);\n                const double range = orogen * (0.08 + 0.92 * ridgeCore);\n                const double interRangeTrough = orogen * std::pow(1.0 - ridgeCore, 1.75);\n\n                double h = 0.0;\n                h += land * (260.0 + 680.0 * broad + 380.0 * province);\n                // R5 geomorph: convergent belts are signed ridge-and-valley systems. Broad\n                // tectonic uplift stays modest; most elevation is concentrated on ridge cores,\n                // while inter-range troughs are explicitly lowered so a mountain belt reads as\n                // peaks separated by valleys instead of one kilometre-scale table.\n                h += orogen * 520.0\n                    + range * (1250.0 + 5000.0 * std::pow(ridgeCore, 1.30))\n                    - interRangeTrough * 720.0;\n                h += land * smooth01(0.55, 0.83, 0.5 + 0.5 * fbm(seed ^ 0xBB67AE8584CAA73BULL, d, 5.8, 4)) * 720.0;'''
g = replace_once(g, old_orogen, new_orogen, "R5 signed orogen")

g = replace_once(
    g,
    "                mountain[id] = static_cast<float>(std::clamp(range, 0.0, 1.0));",
    "                mountain[id] = static_cast<float>(std::clamp(orogen * (0.12 + 0.88 * ridgeCore), 0.0, 1.0));",
    "R5 mountain authority",
)

old_sample = '''        s.mountain = std::clamp(bilinear(mountain,d), 0.0, 1.0);\n        s.river = std::clamp(bilinear(river,d), 0.0, 1.0);\n        s.floodplain = std::clamp(bilinear(floodplain,d), 0.0, 1.0);\n        s.incision = std::clamp(bilinear(incision,d), 0.0, 1.0);\n        return s;'''
new_sample = '''        s.mountain = std::clamp(bilinear(mountain,d), 0.0, 1.0);\n        s.river = std::clamp(bilinear(river,d), 0.0, 1.0);\n        s.floodplain = std::clamp(bilinear(floodplain,d), 0.0, 1.0);\n        s.incision = std::clamp(bilinear(incision,d), 0.0, 1.0);\n\n        // R5 geomorph: the 512x256 field chooses the real drainage graph, but a grid cell is\n        // tens of kilometres wide on an Earth-sized sphere. Reconstruct the centerline from\n        // each wet cell to its actual downhill receiver and measure geodesic distance to those\n        // flow segments. The result is a continuous sub-kilometre-to-kilometre river core while\n        // the broad `river` field remains available only for valley/floodplain shaping.\n        const glm::dvec3 q = glm::normalize(d);\n        const glm::dvec3 ref = std::abs(q.y) < 0.88\n            ? glm::dvec3{0.0, 1.0, 0.0}\n            : glm::dvec3{1.0, 0.0, 0.0};\n        const glm::dvec3 east = glm::normalize(glm::cross(ref, q));\n        const glm::dvec3 north = glm::normalize(glm::cross(q, east));\n        auto localMeters = [&](const glm::dvec3& pInput) {\n            const glm::dvec3 p = glm::normalize(pInput);\n            const double c = std::clamp(glm::dot(q, p), -1.0, 1.0);\n            const double angle = std::acos(c);\n            glm::dvec3 tangent = p - q * c;\n            const double tl = glm::length(tangent);\n            if (tl < 1.0e-12 || angle < 1.0e-12) return glm::dvec2{0.0};\n            tangent /= tl;\n            return glm::dvec2{glm::dot(tangent, east), glm::dot(tangent, north)}\n                * (angle * radius);\n        };\n\n        const double lon = std::atan2(q.z, q.x);\n        const double lat = std::asin(std::clamp(q.y, -1.0, 1.0));\n        const double gx = (lon + kPi) / (2.0 * kPi) * kWidth - 0.5;\n        const double gy = (lat + 0.5 * kPi) / kPi * kHeight - 0.5;\n        const int cx = static_cast<int>(std::floor(gx));\n        const int cy = static_cast<int>(std::floor(gy));\n        double channel = 0.0;\n        for (int oy = -2; oy <= 2; ++oy) {\n            const int sy = cy + oy;\n            if (sy < 0 || sy >= kHeight) continue;\n            for (int ox = -2; ox <= 2; ++ox) {\n                const int sx = cx + ox;\n                const int id = index(sx, sy);\n                const int rid = receiver[id];\n                const double strength = std::clamp(static_cast<double>(river[id]), 0.0, 1.0);\n                if (rid < 0 || strength < 0.30) continue;\n                const int rx = rid % kWidth;\n                const int ry = rid / kWidth;\n                const glm::dvec2 a = localMeters(directionAt(sx, sy));\n                const glm::dvec2 b = localMeters(directionAt(rx, ry));\n                const glm::dvec2 ab = b - a;\n                const double ab2 = glm::dot(ab, ab);\n                const double t = ab2 > 1.0\n                    ? std::clamp(-glm::dot(a, ab) / ab2, 0.0, 1.0)\n                    : 0.0;\n                const double distance = glm::length(a + ab * t);\n                const double halfWidth = 90.0 + 620.0 * std::pow(strength, 1.80);\n                const double core = 1.0 - smooth01(halfWidth * 0.32, halfWidth, distance);\n                channel = std::max(channel, core * (0.58 + 0.42 * strength));\n            }\n        }\n        s.channel = std::clamp(channel, 0.0, 1.0);\n        return s;'''
g = replace_once(g, old_sample, new_sample, "R5 hydrology centerline reconstruction")

geomorph_path.write_text(g)


# -----------------------------------------------------------------------------
# Planet surface: broad hydrology carves the valley, narrow channel owns water;
# coast gets an actual escarpment and highlands get a modest shelf signal.
# -----------------------------------------------------------------------------
surface_path = Path("native/src/world/PlanetSurface.cpp")
s = surface_path.read_text()

start = s.index("    // Hydrology remains the placement authority for valleys.")
end = s.index("\n\n    // Give hydrologically low coastal margins", start)
new_river = '''    // R5 river corridor: the Priority-Flood/discharge bake owns the broad valley, while\n    // `geomorph.channel` is reconstructed from the actual downhill receiver graph and owns\n    // the visible watercourse. This prevents a single coarse hydrology texel from becoming\n    // a blue plain tens of kilometres wide.\n    const double channelTexture = 0.5 + 0.5 * fbmSurface(\n        definition.seed ^ 0xC2B2AE3D27D4EB4FULL, w, 420.0, 3);\n    const double riverAuthority = std::pow(std::clamp(geomorph.river, 0.0, 1.0), 1.26)\n        * geomorphLandness;\n    const double channelCore = std::pow(std::clamp(geomorph.channel, 0.0, 1.0), 0.88)\n        * (0.90 + 0.10 * channelTexture) * geomorphLandness;\n    const double uplandCarve = smooth01(260.0, 2200.0, geomorph.elevationMeters);\n    elevation -= riverAuthority * (45.0 + 300.0 * uplandCarve);\n    elevation -= channelCore * (12.0 + 68.0 * uplandCarve);\n    elevation -= geomorph.incision * (35.0 + 175.0 * uplandCarve);'''
s = s[:start] + new_river + s[end:]

old_coast = '''    const double globalCoastBand = geomorphLandness\n        * (1.0 - smooth01(90.0, 680.0, std::abs(geomorph.elevationMeters)));\n    const double globalCoastRugged = globalCoastBand\n        * smooth01(0.46, 0.86, rangeRidgeB);\n    elevation += maxLand * 0.032 * globalCoastRugged;'''
new_coast = '''    const double globalCoastBand = geomorphLandness\n        * (1.0 - smooth01(70.0, 620.0, std::abs(geomorph.elevationMeters)));\n    const double globalCoastRugged = globalCoastBand\n        * smooth01(0.44, 0.84, rangeRidgeB);\n    const double coastEscarpment = globalCoastRugged\n        * (0.62 + 0.38 * smooth01(0.34, 0.86, rangeRidgeA));\n    elevation += maxLand * 0.058 * coastEscarpment;'''
s = replace_once(s, old_coast, new_coast, "R5 coastal escarpment")

s = replace_once(
    s,
    "    sample.river = std::max(geomorph.river * 0.44, channelCore);",
    "    sample.river = channelCore;",
    "R5 narrow river sample",
)
s = replace_once(
    s,
    "    sample.coastalCliff = std::max(coastalCliff, globalCoastRugged);",
    "    sample.coastalCliff = std::max(coastalCliff, coastEscarpment);",
    "R5 cliff sample",
)

s = s.replace("} else if (sample.river > 0.60) {", "} else if (sample.river > 0.44) {")

surface_path.write_text(s)


# -----------------------------------------------------------------------------
# Ecology: watercourses are now explicit. Never grow trees/grass in the channel.
# -----------------------------------------------------------------------------
ecology_path = Path("native/src/world/ProceduralEcology.cpp")
e = ecology_path.read_text()

e = replace_once(
    e,
    "            if (c.terrain.submerged(planet) || aboveSea < 18.0 || aboveSea > 2550.0) return;\n            if (c.radialAlignment < 0.935 || c.terrain.mountain > 0.76 || c.terrain.volcano > 0.72) return;",
    "            if (c.terrain.submerged(planet) || aboveSea < 18.0 || aboveSea > 2550.0) return;\n            // R5 river exclusion: a hydrology channel is water, not fertile ground under water.\n            if (c.terrain.river > 0.16 || c.terrain.wetland > 0.82) return;\n            if (c.radialAlignment < 0.935 || c.terrain.mountain > 0.76 || c.terrain.volcano > 0.72) return;",
    "R5 tree river exclusion",
)

e = replace_once(
    e,
    "            if (c.terrain.submerged(planet) || aboveSea < 7.0 || aboveSea > 2200.0) return;\n            if (c.radialAlignment < 0.955 || c.terrain.mountain > 0.62 || c.terrain.volcano > 0.58) return;",
    "            if (c.terrain.submerged(planet) || aboveSea < 7.0 || aboveSea > 2200.0) return;\n            if (c.terrain.river > 0.28) return;\n            if (c.radialAlignment < 0.955 || c.terrain.mountain > 0.62 || c.terrain.volcano > 0.58) return;",
    "R5 grass river exclusion",
)

ecology_path.write_text(e)


# -----------------------------------------------------------------------------
# Evidence camera: low, close viewpoints so terrain shape is visible at the LOD
# a player would actually inspect instead of flattening it from kilometres high.
# -----------------------------------------------------------------------------
main_path = Path("native/src/app/Main.cpp")
m = main_path.read_text()

m = replace_once(
    m,
    "    const std::array<double, 5> mountainRadii{42000.0, 65000.0, 90000.0, 125000.0, 165000.0};\n    const std::array<double, 5> highlandRadii{26000.0, 42000.0, 62000.0, 85000.0, 115000.0};\n    const std::array<double, 5> coastRadii{7000.0, 11000.0, 17000.0, 24000.0, 32000.0};\n    const std::array<double, 5> riverRadii{3200.0, 5200.0, 7800.0, 11000.0, 15500.0};",
    "    // R5 capture geometry: close low-angle evidence stays inside useful terrain LODs.\n    const std::array<double, 5> mountainRadii{18000.0, 26000.0, 38000.0, 52000.0, 70000.0};\n    const std::array<double, 5> highlandRadii{12000.0, 18000.0, 26000.0, 36000.0, 50000.0};\n    const std::array<double, 5> coastRadii{1800.0, 3000.0, 4500.0, 6500.0, 9000.0};\n    const std::array<double, 5> riverRadii{1200.0, 1800.0, 2600.0, 3600.0, 5200.0};",
    "R5 capture radii",
)

old_score = '''            if (mode == "coast") {\n                if (!terrain.submerged(planet)) continue;\n                score = std::abs(terrain.elevationMeters + 45.0) * 0.08\n                    + std::abs(standOffMeters - 15000.0) * 0.015;\n            } else if (mode == "river") {\n                if (terrain.submerged(planet)) continue;\n                score = -terrain.elevationMeters + terrain.river * 900.0\n                    + std::abs(standOffMeters - 7800.0) * 0.025;\n            } else {\n                if (terrain.submerged(planet)) continue;\n                score = terrain.elevationMeters - targetElevation\n                    + terrain.mountain * 480.0\n                    + standOffMeters * (mode == "mountain" ? 0.003 : 0.005);\n            }'''
new_score = '''            if (mode == "coast") {\n                if (!terrain.submerged(planet)) continue;\n                score = std::abs(terrain.elevationMeters + 30.0) * 0.06\n                    + std::abs(standOffMeters - 4500.0) * 0.020;\n            } else if (mode == "river") {\n                if (terrain.submerged(planet) || terrain.river > 0.16) continue;\n                score = std::abs(terrain.elevationMeters - targetElevation) * 0.18\n                    + terrain.river * 2200.0\n                    + std::abs(standOffMeters - 2600.0) * 0.035;\n            } else if (mode == "mountain") {\n                if (terrain.submerged(planet)) continue;\n                score = terrain.elevationMeters * 1.35\n                    + terrain.mountain * 1350.0\n                    + std::abs(standOffMeters - 32000.0) * 0.014;\n            } else {\n                if (terrain.submerged(planet)) continue;\n                score = terrain.elevationMeters * 0.95\n                    + terrain.mountain * 1050.0\n                    + std::abs(standOffMeters - 24000.0) * 0.018;\n            }'''
m = replace_once(m, old_score, new_score, "R5 capture vantage scores")

old_lifts = '''            const double targetLift = captureMode == "mountain" ? 950.0\n                : (captureMode == "highland" ? 520.0 : (captureMode == "coast" ? 130.0 : 80.0));\n            const double cameraLift = captureMode == "mountain" ? 3200.0\n                : (captureMode == "highland" ? 2400.0\n                : (captureMode == "coast" ? 1050.0 : 760.0));'''
new_lifts = '''            const double targetLift = captureMode == "mountain" ? 420.0\n                : (captureMode == "highland" ? 180.0 : (captureMode == "coast" ? 85.0 : 28.0));\n            const double cameraLift = captureMode == "mountain" ? 220.0\n                : (captureMode == "highland" ? 240.0\n                : (captureMode == "coast" ? 95.0 : 90.0));'''
m = replace_once(m, old_lifts, new_lifts, "R5 low-angle camera")

main_path.write_text(m)

print("R5 geomorph materialization complete")
