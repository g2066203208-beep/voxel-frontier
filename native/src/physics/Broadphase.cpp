#include "vf/physics/Broadphase.hpp"

#include <algorithm>
#include <vector>

namespace vf {
namespace {

struct Proxy {
    std::size_t index{};
    Aabb bounds{};
};

[[nodiscard]] bool overlapsYZ(const Proxy& a, const Proxy& b) noexcept {
    return a.bounds.minimum.y <= b.bounds.maximum.y && a.bounds.maximum.y >= b.bounds.minimum.y
        && a.bounds.minimum.z <= b.bounds.maximum.z && a.bounds.maximum.z >= b.bounds.minimum.z;
}

} // namespace

std::vector<BroadphasePair> buildSweepAndPrunePairs(std::span<const RigidBody> bodies) {
    std::vector<Proxy> proxies;
    proxies.reserve(bodies.size());

    for (std::size_t i = 0; i < bodies.size(); ++i) {
        const auto& body = bodies[i];
        proxies.push_back({i, computeWorldAabb(body.collisionShape, body.shapePose())});
    }

    std::stable_sort(proxies.begin(), proxies.end(), [](const Proxy& a, const Proxy& b) {
        if (a.bounds.minimum.x != b.bounds.minimum.x) return a.bounds.minimum.x < b.bounds.minimum.x;
        return a.index < b.index;
    });

    std::vector<const Proxy*> active;
    active.reserve(proxies.size());
    std::vector<BroadphasePair> pairs;

    for (const auto& proxy : proxies) {
        std::erase_if(active, [&](const Proxy* candidate) {
            return candidate->bounds.maximum.x < proxy.bounds.minimum.x;
        });

        for (const Proxy* candidate : active) {
            if (!overlapsYZ(*candidate, proxy)) continue;
            const auto& a = bodies[candidate->index];
            const auto& b = bodies[proxy.index];
            if (a.motionType == MotionType::Static && b.motionType == MotionType::Static) continue;
            pairs.push_back({candidate->index, proxy.index});
        }

        active.push_back(&proxy);
    }

    return pairs;
}

} // namespace vf
