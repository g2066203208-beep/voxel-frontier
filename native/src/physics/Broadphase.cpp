#include "vf/physics/Broadphase.hpp"

#include <algorithm>
#include <vector>

namespace vf {
namespace {

struct Proxy {
    std::size_t index{};
    double minX{};
    double maxX{};
    double minY{};
    double maxY{};
    double minZ{};
    double maxZ{};
};

[[nodiscard]] bool overlapsYZ(const Proxy& a, const Proxy& b) noexcept {
    return a.minY <= b.maxY && a.maxY >= b.minY
        && a.minZ <= b.maxZ && a.maxZ >= b.minZ;
}

} // namespace

std::vector<BroadphasePair> buildSweepAndPrunePairs(std::span<const RigidBody> bodies) {
    std::vector<Proxy> proxies;
    proxies.reserve(bodies.size());

    for (std::size_t i = 0; i < bodies.size(); ++i) {
        const auto& body = bodies[i];
        const double r = std::max(0.0, body.collisionRadius);
        proxies.push_back({
            i,
            body.position.x - r,
            body.position.x + r,
            body.position.y - r,
            body.position.y + r,
            body.position.z - r,
            body.position.z + r,
        });
    }

    std::stable_sort(proxies.begin(), proxies.end(), [](const Proxy& a, const Proxy& b) {
        if (a.minX != b.minX) return a.minX < b.minX;
        return a.index < b.index;
    });

    std::vector<const Proxy*> active;
    active.reserve(proxies.size());
    std::vector<BroadphasePair> pairs;

    for (const auto& proxy : proxies) {
        std::erase_if(active, [&](const Proxy* candidate) {
            return candidate->maxX < proxy.minX;
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
