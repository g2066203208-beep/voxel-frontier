#pragma once

#include "vf/world/World.hpp"

#include <cstdint>

namespace vf {

class Engine final {
public:
    explicit Engine(std::uint64_t seed = 0x564f58454c46524fULL) noexcept;

    void bootstrap();
    void tick(double deltaSeconds) noexcept;

    [[nodiscard]] World& world() noexcept { return world_; }
    [[nodiscard]] const World& world() const noexcept { return world_; }
    [[nodiscard]] std::uint64_t frameIndex() const noexcept { return frameIndex_; }
    [[nodiscard]] double elapsedSeconds() const noexcept { return elapsedSeconds_; }

private:
    World world_;
    std::uint64_t frameIndex_{};
    double elapsedSeconds_{};
};

} // namespace vf
