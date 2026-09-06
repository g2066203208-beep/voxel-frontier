from pathlib import Path

path = Path("native/src/app/Main.cpp")
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    text = text.replace(old, new, 1)


replace_once(
    '#include "vf/world/PlanetSurfaceAuthority.hpp"\n',
    '#include "vf/world/PlanetSurfaceAuthority.hpp"\n#include "vf/world/PlanetaryBodySystem.hpp"\n',
    "planetary include",
)

replace_once(
    '        vf::CelestialSystem celestial;\n',
    '        vf::PlanetaryBodySystem planetaryBodies;\n'
    '        vf::CelestialSystem& celestial = planetaryBodies.celestial();\n',
    "planetary registry root",
)

replace_once(
    '        const std::uint32_t asterId = celestial.addBody(aster);\n'
    '        vf::PlanetClimateGrid climateGrid{planet, {}, aster.spinRateRadPerSecond};\n'
    '        vf::OceanSpectrum oceanSpectrum{};\n',
    '        vf::PlanetaryBodyDescriptor asterDescriptor{};\n'
    '        asterDescriptor.celestial = aster;\n'
    '        asterDescriptor.solidSurface = true;\n'
    '        asterDescriptor.terrain = planet;\n'
    '        asterDescriptor.climateEnabled = true;\n'
    '        asterDescriptor.oceanEnabled = true;\n'
    '        const std::uint32_t asterId = planetaryBodies.addBody(std::move(asterDescriptor));\n'
    '        auto* asterSurface = planetaryBodies.surface(asterId);\n'
    '        auto* asterClimate = planetaryBodies.climate(asterId);\n'
    '        auto* asterOcean = planetaryBodies.ocean(asterId);\n'
    '        if (asterSurface == nullptr || asterClimate == nullptr || asterOcean == nullptr)\n'
    '            throw std::runtime_error("Aster planetary services failed to initialize");\n'
    '        vf::PlanetSurfaceAuthority& surfaceAuthority = *asterSurface;\n'
    '        vf::PlanetClimateGrid& climateGrid = *asterClimate;\n'
    '        vf::OceanSpectrum& oceanSpectrum = *asterOcean;\n',
    "Aster service registration",
)

replace_once(
    '        vf::PlanetSurfaceAuthority surfaceAuthority{planet};\n',
    '        // SurfaceAuthority is owned by PlanetaryBodySystem; hydrology is attached to the same\n'
    '        // object later, so render, collision, ecology and environment altitude cannot diverge.\n',
    "remove duplicate surface authority",
)

replace_once(
    '            celestialClock.advance(dt, [&](double astroDt) {\n'
    '                celestial.step(astroDt);\n'
    '                const auto* climateAster = celestial.body(asterId);\n'
    '                const auto* climateSun = celestial.body(sunId);\n'
    '                if (climateAster != nullptr && climateSun != nullptr) {\n'
    '                    const glm::dvec3 toSunWorld = safeNormalize(climateSun->position - climateAster->position);\n'
    '                    const glm::dvec3 toSunBody = safeNormalize(\n'
    '                        glm::conjugate(glm::normalize(climateAster->orientation)) * toSunWorld);\n'
    '                    const double starDistance = glm::length(climateSun->position - climateAster->position);\n'
    '                    const double stellarIrradiance = climateSun->luminosityWatts\n'
    '                        / (4.0 * kPi * std::max(1.0, starDistance * starDistance));\n'
    '                    climateGrid.step(astroDt, toSunBody, stellarIrradiance);\n'
    '                }\n'
    '            });\n',
    '            celestialClock.advance(dt, [&](double astroDt) {\n'
    '                // One authoritative step advances N-body/spin plus every registered planetary\n'
    '                // service on the same bounded simulated-time sequence.\n'
    '                planetaryBodies.step(astroDt);\n'
    '            });\n',
    "unified runtime step",
)

# Safety assertions: the old duplicated construction/update path must be completely gone.
for forbidden in (
    'vf::PlanetClimateGrid climateGrid{planet, {}, aster.spinRateRadPerSecond}',
    'vf::OceanSpectrum oceanSpectrum{}',
    'vf::PlanetSurfaceAuthority surfaceAuthority{planet}',
    'climateGrid.step(astroDt, toSunBody, stellarIrradiance)',
):
    if forbidden in text:
        raise RuntimeError(f"forbidden legacy runtime path remains: {forbidden}")

path.write_text(text, encoding="utf-8")
print("R24 Main.cpp migrated to PlanetaryBodySystem runtime ownership")
