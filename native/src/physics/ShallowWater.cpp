#include "vf/physics/ShallowWater.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace vf {

ShallowWaterGrid::ShallowWaterGrid(std::uint32_t width, std::uint32_t height, double cellSizeMeters)
    : width_(width), height_(height), cellSizeMeters_(std::max(0.01, cellSizeMeters)), cells_(static_cast<std::size_t>(width) * height) {
    if (width_ == 0 || height_ == 0) throw std::invalid_argument("ShallowWaterGrid dimensions must be non-zero");
}

std::size_t ShallowWaterGrid::index(std::uint32_t x, std::uint32_t y) const {
    if (x >= width_ || y >= height_) throw std::out_of_range("ShallowWaterGrid cell out of range");
    return static_cast<std::size_t>(y) * width_ + x;
}

ShallowWaterCell& ShallowWaterGrid::cell(std::uint32_t x, std::uint32_t y) {
    return cells_[index(x, y)];
}

const ShallowWaterCell& ShallowWaterGrid::cell(std::uint32_t x, std::uint32_t y) const {
    return cells_[index(x, y)];
}

double ShallowWaterGrid::surfaceHeight(std::uint32_t x, std::uint32_t y) const {
    const auto& value = cell(x, y);
    return value.bedElevation + value.waterDepth;
}

double ShallowWaterGrid::totalWaterVolume() const noexcept {
    const double cellArea = cellSizeMeters_ * cellSizeMeters_;
    double volume = 0.0;
    for (const auto& cellValue : cells_) volume += std::max(0.0, cellValue.waterDepth) * cellArea;
    return volume;
}

void ShallowWaterGrid::addWater(std::uint32_t x, std::uint32_t y, double depthMeters) {
    auto& value = cell(x, y);
    value.waterDepth = std::max(0.0, value.waterDepth + depthMeters);
}

void ShallowWaterGrid::step(double deltaSeconds, double gravityMagnitude) {
    const double dt = std::clamp(deltaSeconds, 0.0, 0.05);
    if (dt <= 0.0) return;
    const double gravity = std::max(0.0, gravityMagnitude);
    const double coefficient = std::max(0.0, flowCoefficient_);

    std::vector<double> depthDelta(cells_.size(), 0.0);
    std::vector<glm::dvec2> momentumHint(cells_.size(), glm::dvec2{});

    const auto exchange = [&](std::uint32_t ax, std::uint32_t ay, std::uint32_t bx, std::uint32_t by, const glm::dvec2& direction) {
        const std::size_t ia = index(ax, ay);
        const std::size_t ib = index(bx, by);
        const double headA = cells_[ia].bedElevation + cells_[ia].waterDepth;
        const double headB = cells_[ib].bedElevation + cells_[ib].waterDepth;
        const double headDifference = headA - headB;
        if (std::abs(headDifference) < 1.0e-8) return;

        const bool aToB = headDifference > 0.0;
        const std::size_t donor = aToB ? ia : ib;
        const std::size_t receiver = aToB ? ib : ia;
        const glm::dvec2 flowDirection = aToB ? direction : -direction;
        const double availableDepth = std::max(0.0, cells_[donor].waterDepth);
        if (availableDepth <= 0.0) return;

        // Height-field shallow-water style flux: hydraulic-head difference drives flow,
        // while a strict donor cap keeps the explicit update non-negative and conservative.
        const double characteristicSpeed = std::sqrt(gravity * std::abs(headDifference));
        const double requestedDepth = coefficient * characteristicSpeed * dt / std::max(0.01, cellSizeMeters_);
        const double transferDepth = std::min(availableDepth * 0.24, requestedDepth);
        if (transferDepth <= 0.0) return;

        depthDelta[donor] -= transferDepth;
        depthDelta[receiver] += transferDepth;
        momentumHint[donor] += flowDirection * transferDepth;
        momentumHint[receiver] += flowDirection * transferDepth;
    };

    for (std::uint32_t y = 0; y < height_; ++y) {
        for (std::uint32_t x = 0; x < width_; ++x) {
            if (x + 1 < width_) exchange(x, y, x + 1, y, {1.0, 0.0});
            if (y + 1 < height_) exchange(x, y, x, y + 1, {0.0, 1.0});
        }
    }

    for (std::size_t i = 0; i < cells_.size(); ++i) {
        auto& value = cells_[i];
        value.waterDepth = std::max(0.0, value.waterDepth + depthDelta[i]);
        const double depth = std::max(0.01, value.waterDepth);
        const glm::dvec2 targetVelocity = momentumHint[i] * (cellSizeMeters_ / (depth * dt));
        const double blend = 1.0 - std::exp(-4.0 * dt);
        value.velocity += (targetVelocity - value.velocity) * blend;
        value.velocity *= std::exp(-0.8 * dt);
    }
}

} // namespace vf
