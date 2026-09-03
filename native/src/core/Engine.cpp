#include "vf/core/Engine.hpp"

#include <algorithm>

namespace vf {

Engine::Engine(std::uint64_t seed) noexcept : world_(seed) {}

void Engine::bootstrap() {
    // Small deterministic startup set. Streaming radius becomes camera-driven next.
    world_.warmup(2, 0, 2);
}

void Engine::tick(double deltaSeconds) noexcept {
    const auto clamped = std::clamp(deltaSeconds, 0.0, 0.1);
    elapsedSeconds_ += clamped;
    ++frameIndex_;
}

} // namespace vf
