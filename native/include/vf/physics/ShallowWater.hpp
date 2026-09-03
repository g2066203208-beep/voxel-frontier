#pragma once

#include <cstdint>
#include <vector>

#include <glm/glm.hpp>

namespace vf {

struct ShallowWaterCell {
    double bedElevation{};
    double waterDepth{};
    glm::dvec2 velocity{};
};

class ShallowWaterGrid final {
public:
    ShallowWaterGrid(std::uint32_t width, std::uint32_t height, double cellSizeMeters = 1.0);

    [[nodiscard]] std::uint32_t width() const noexcept { return width_; }
    [[nodiscard]] std::uint32_t height() const noexcept { return height_; }
    [[nodiscard]] double cellSizeMeters() const noexcept { return cellSizeMeters_; }

    [[nodiscard]] ShallowWaterCell& cell(std::uint32_t x, std::uint32_t y);
    [[nodiscard]] const ShallowWaterCell& cell(std::uint32_t x, std::uint32_t y) const;
    [[nodiscard]] double surfaceHeight(std::uint32_t x, std::uint32_t y) const;
    [[nodiscard]] double totalWaterVolume() const noexcept;

    void addWater(std::uint32_t x, std::uint32_t y, double depthMeters);
    void step(double deltaSeconds, double gravityMagnitude = 9.81);

    void setFlowCoefficient(double value) noexcept { flowCoefficient_ = value; }
    [[nodiscard]] double flowCoefficient() const noexcept { return flowCoefficient_; }

private:
    [[nodiscard]] std::size_t index(std::uint32_t x, std::uint32_t y) const;

    std::uint32_t width_{};
    std::uint32_t height_{};
    double cellSizeMeters_{1.0};
    double flowCoefficient_{0.45};
    std::vector<ShallowWaterCell> cells_;
};

} // namespace vf
