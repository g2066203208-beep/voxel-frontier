#pragma once

#include "vf/world/PlanetSurface.hpp"

#include <cstdint>
#include <vector>

#include <glm/glm.hpp>

namespace vf::detail {

inline constexpr double kPi = 3.1415926535897932384626433832795;
inline constexpr double kTau = 2.0 * kPi;
inline constexpr double kGoldenAngle = 2.3999632297286533222315555066336;
inline constexpr float kTerrainMaterialMarker = 1.25F;
inline constexpr float kBarkMaterialMarker = -1.0F;
inline constexpr float kFoliageMaterialMarker = -2.0F;
inline constexpr float kRockMaterialMarker = -3.0F;
inline constexpr float kOceanMaterialMarker = -4.0F;

struct SurfaceFrame {
    glm::dvec3 east{1.0, 0.0, 0.0};
    glm::dvec3 north{0.0, 0.0, 1.0};
    glm::dvec3 up{0.0, 1.0, 0.0};
};

struct LocalVertex {
    glm::dvec3 position{};
    glm::vec3 material{};
};

struct LocalMesh {
    std::vector<LocalVertex> vertices;
    std::vector<std::uint32_t> indices;
};

struct Placement {
    glm::dvec3 direction{};
    double clearanceMeters{0.0};
};

[[nodiscard]] std::uint64_t hashChannel(std::uint64_t seed, std::uint64_t channel) noexcept;
[[nodiscard]] double random01(std::uint64_t seed, std::uint64_t channel) noexcept;
[[nodiscard]] double randomSigned(std::uint64_t seed, std::uint64_t channel) noexcept;
[[nodiscard]] double seedPhase(std::uint64_t seed, std::uint64_t channel) noexcept;
[[nodiscard]] double valueNoise3(std::uint64_t seed, const glm::dvec3& p) noexcept;
[[nodiscard]] double centeredFbm(std::uint64_t seed, const glm::dvec3& p, unsigned octaves) noexcept;
[[nodiscard]] double terrainMoisture(const PlanetDefinition&, const glm::dvec3&) noexcept;
[[nodiscard]] double terrainTemperature(const PlanetDefinition&, const glm::dvec3&, double normalizedHeight) noexcept;
[[nodiscard]] glm::vec3 terrainMaterialData(const PlanetDefinition&, const glm::dvec3&, double normalizedHeight) noexcept;
[[nodiscard]] glm::vec3 proxyColor(const glm::vec3&, const glm::dvec3&);
[[nodiscard]] SurfaceFrame frameForDirection(const glm::dvec3&);
[[nodiscard]] glm::dvec3 transformLocalPoint(const glm::dvec3&, const glm::dvec3&, const SurfaceFrame&, double yaw, double leanEast, double leanNorth) noexcept;
[[nodiscard]] glm::dvec3 transformLocalVector(const glm::dvec3&, const SurfaceFrame&, double yaw, double leanEast, double leanNorth) noexcept;
void appendLocalMesh(PlanetMesh&, const LocalMesh&, const glm::dvec3&, const SurfaceFrame&, double yaw, double leanEast, double leanNorth);
void appendTriangle(LocalMesh&, std::uint32_t, std::uint32_t, std::uint32_t);
void appendQuadBest(LocalMesh&, std::uint32_t, std::uint32_t, std::uint32_t, std::uint32_t);
[[nodiscard]] LocalMesh buildStylizedTree(std::uint64_t seed);
[[nodiscard]] std::vector<Placement> scatterTrees(PlanetMesh&, const PlanetDefinition&);
void scatterRocks(PlanetMesh&, const PlanetDefinition&, const std::vector<Placement>& treePlacements);

} // namespace vf::detail
