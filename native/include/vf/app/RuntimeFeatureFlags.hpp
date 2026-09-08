#pragma once

#include <cstdlib>
#include <iostream>
#include <string_view>

namespace vf {

// R24 modular runtime feature gates.
//
// The intent is strict subsystem decoupling: a disabled feature must stop scheduling its
// expensive work without making unrelated systems disappear. Terrain rendering/synthesis is
// therefore separate from the mathematical planet surface authority used by collision/gravity.
// This makes A/B performance isolation possible without changing gameplay coordinates.
struct RuntimeFeatureFlags {
    bool terrainRender{true};
    bool terrainStreaming{true};
    bool waterRender{true};
    bool ecologyRender{true};
    bool skyRender{true};
    bool shadowRender{true};
    bool physicsSimulation{true};
    bool celestialSimulation{true};
    bool weatherSimulation{true};
    bool uiRender{true};

    [[nodiscard]] static bool readFlag(const char* name, bool fallback = true) noexcept {
        const char* value = std::getenv(name);
        if (value == nullptr || *value == '\0') return fallback;
        const std::string_view text{value};
        if (text == "0" || text == "false" || text == "FALSE" || text == "off" || text == "OFF")
            return false;
        if (text == "1" || text == "true" || text == "TRUE" || text == "on" || text == "ON")
            return true;
        return fallback;
    }

    [[nodiscard]] static RuntimeFeatureFlags fromEnvironment() noexcept {
        RuntimeFeatureFlags flags{};
        flags.terrainRender = readFlag("VF_MODULE_TERRAIN", true);
        flags.terrainStreaming = readFlag("VF_MODULE_TERRAIN_STREAMING", true);
        flags.waterRender = readFlag("VF_MODULE_WATER", true);
        flags.ecologyRender = readFlag("VF_MODULE_ECOLOGY", true);
        flags.skyRender = readFlag("VF_MODULE_SKY", true);
        flags.shadowRender = readFlag("VF_MODULE_SHADOWS", true);
        flags.physicsSimulation = readFlag("VF_MODULE_PHYSICS", true);
        flags.celestialSimulation = readFlag("VF_MODULE_CELESTIAL", true);
        flags.weatherSimulation = readFlag("VF_MODULE_WEATHER", true);
        flags.uiRender = readFlag("VF_MODULE_UI", true);
        return flags;
    }

    [[nodiscard]] bool terrainWorkEnabled() const noexcept {
        return terrainRender && terrainStreaming;
    }

    void print(std::ostream& stream = std::cout) const {
        stream << "R24 MODULES"
               << " terrain=" << (terrainRender ? 1 : 0)
               << " terrain_streaming=" << (terrainStreaming ? 1 : 0)
               << " water=" << (waterRender ? 1 : 0)
               << " ecology=" << (ecologyRender ? 1 : 0)
               << " sky=" << (skyRender ? 1 : 0)
               << " shadows=" << (shadowRender ? 1 : 0)
               << " physics=" << (physicsSimulation ? 1 : 0)
               << " celestial=" << (celestialSimulation ? 1 : 0)
               << " weather=" << (weatherSimulation ? 1 : 0)
               << " ui=" << (uiRender ? 1 : 0)
               << '\n';
    }
};

} // namespace vf
