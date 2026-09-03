#pragma once

#include <cstddef>
#include <span>
#include <vector>

#include "vf/physics/PhysicsWorld.hpp"

namespace vf {

struct BroadphasePair {
    std::size_t bodyIndexA{};
    std::size_t bodyIndexB{};
};

[[nodiscard]] std::vector<BroadphasePair> buildSweepAndPrunePairs(std::span<const RigidBody> bodies);

} // namespace vf
