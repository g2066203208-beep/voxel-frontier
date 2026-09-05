#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <memory>
#include <mutex>
#include <numeric>
#include <queue>
#include <unordered_map>
#include <utility>
#include <vector>

#include <glm/glm.hpp>

namespace vf {

struct GlobalGeomorphSample {
    double elevationMeters{};
    double continentalness{};
    double mountain{};
    double river{};
    double floodplain{};
    double incision{};
};

namespace geomorph_detail {

constexpr int kWidth = 512;
constexpr int kHeight = 256;
constexpr int kCount = kWidth * kHeight;
constexpr double kPi = 3.1415926535897932384626433832795;

inline double smooth01(double a, double b, double v) noexcept {
    if (b <= a) return v >= b ? 1.0 : 0.0;
    double t = std::clamp((v - a) / (b - a), 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

inline std::uint64_t mix64(std::uint64_t x) noexcept {
    x += 0x9E3779B97F4A7C15ULL;
    x = (x ^ (x >> 30U)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27U)) * 0x94D049BB133111EBULL;
    return x ^ (x >> 31U);
}

inline double unit01(std::uint64_t seed, std::uint64_t channel) noexcept {
    return static_cast<double>(mix64(seed ^ (channel * 0xD6E8FEB86659FD93ULL)) & 0xFFFFFFULL)
        / static_cast<double>(0xFFFFFFULL);
}

inline double quintic(double x) noexcept {
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0);
}

inline double lattice(std::uint64_t seed, int x, int y, int z) noexcept {
    std::uint64_t h = seed;
    h ^= static_cast<std::uint64_t>(static_cast<std::int64_t>(x)) * 0x9E3779B185EBCA87ULL;
    h ^= static_cast<std::uint64_t>(static_cast<std::int64_t>(y)) * 0xC2B2AE3D27D4EB4FULL;
    h ^= static_cast<std::uint64_t>(static_cast<std::int64_t>(z)) * 0x165667B19E3779F9ULL;
    return unit01(mix64(h), 17U) * 2.0 - 1.0;
}

inline double valueNoise3(std::uint64_t seed, const glm::dvec3& p) noexcept {
    const int x0 = static_cast<int>(std::floor(p.x));
    const int y0 = static_cast<int>(std::floor(p.y));
    const int z0 = static_cast<int>(std::floor(p.z));
    const double tx = quintic(p.x - static_cast<double>(x0));
    const double ty = quintic(p.y - static_cast<double>(y0));
    const double tz = quintic(p.z - static_cast<double>(z0));
    auto lerp = [](double a, double b, double t) { return a + (b - a) * t; };
    const double a00 = lerp(lattice(seed,x0,y0,z0), lattice(seed,x0+1,y0,z0), tx);
    const double a10 = lerp(lattice(seed,x0,y0+1,z0), lattice(seed,x0+1,y0+1,z0), tx);
    const double a01 = lerp(lattice(seed,x0,y0,z0+1), lattice(seed,x0+1,y0,z0+1), tx);
    const double a11 = lerp(lattice(seed,x0,y0+1,z0+1), lattice(seed,x0+1,y0+1,z0+1), tx);
    return lerp(lerp(a00,a10,ty), lerp(a01,a11,ty), tz);
}

inline double fbm(std::uint64_t seed, const glm::dvec3& d, double frequency, int octaves) noexcept {
    double sum = 0.0, amp = 1.0, norm = 0.0;
    for (int i = 0; i < octaves; ++i) {
        sum += valueNoise3(mix64(seed + static_cast<std::uint64_t>(i) * 37ULL), d * frequency) * amp;
        norm += amp;
        amp *= 0.5;
        frequency *= 2.03;
    }
    return norm > 0.0 ? sum / norm : 0.0;
}

inline glm::dvec3 seededDirection(std::uint64_t seed, std::uint64_t channel) noexcept {
    const double y = unit01(seed, channel + 1U) * 2.0 - 1.0;
    const double a = unit01(seed, channel + 2U) * 2.0 * kPi;
    const double r = std::sqrt(std::max(0.0, 1.0 - y * y));
    return {std::cos(a) * r, y, std::sin(a) * r};
}

struct Plate {
    glm::dvec3 center{};
    glm::dvec3 pole{};
    double speed{};
};

struct Field {
    std::uint64_t seed{};
    double radius{};
    double maxElevation{};
    std::vector<float> elevation;
    std::vector<float> continental;
    std::vector<float> mountain;
    std::vector<float> river;
    std::vector<float> floodplain;
    std::vector<float> incision;

    explicit Field(std::uint64_t s, double r, double maxElev)
        : seed(s), radius(r), maxElevation(maxElev),
          elevation(kCount), continental(kCount), mountain(kCount), river(kCount),
          floodplain(kCount), incision(kCount) {
        bake();
    }

    static int index(int x, int y) noexcept {
        x %= kWidth;
        if (x < 0) x += kWidth;
        y = std::clamp(y, 0, kHeight - 1);
        return y * kWidth + x;
    }

    static glm::dvec3 directionAt(int x, int y) noexcept {
        const double lon = -kPi + (static_cast<double>(x) + 0.5) * (2.0 * kPi / kWidth);
        const double lat = -0.5 * kPi + (static_cast<double>(y) + 0.5) * (kPi / kHeight);
        const double c = std::cos(lat);
        return {c * std::cos(lon), std::sin(lat), c * std::sin(lon)};
    }

    void bake() {
        constexpr int kPlateCount = 20;
        std::array<Plate, kPlateCount> plates{};
        for (int i = 0; i < kPlateCount; ++i) {
            plates[i].center = seededDirection(seed, 100U + static_cast<std::uint64_t>(i) * 11U);
            plates[i].pole = seededDirection(seed, 500U + static_cast<std::uint64_t>(i) * 13U);
            plates[i].speed = 0.35 + 0.65 * unit01(seed, 900U + static_cast<std::uint64_t>(i) * 17U);
        }

        std::vector<float> base(kCount, 0.0F);
        std::vector<float> filled(kCount, 0.0F);
        std::vector<float> rainfall(kCount, 0.0F);

        for (int y = 0; y < kHeight; ++y) {
            for (int x = 0; x < kWidth; ++x) {
                const int id = index(x,y);
                const glm::dvec3 d = directionAt(x,y);
                const double macro = fbm(seed ^ 0x243F6A8885A308D3ULL, d, 1.15, 5);
                const double meso = fbm(seed ^ 0x13198A2E03707344ULL, d, 2.9, 4);
                const double coast = fbm(seed ^ 0xA4093822299F31D0ULL, d, 7.5, 3);
                const double cont = std::clamp(macro * 0.82 + meso * 0.25 + coast * 0.07 - 0.075, -1.0, 1.0);
                const double land = smooth01(-0.035, 0.075, cont);
                const double ocean = 1.0 - land;

                double best = -2.0, second = -2.0;
                int bi = 0, si = 1;
                for (int i = 0; i < kPlateCount; ++i) {
                    const double s = glm::dot(d, plates[i].center);
                    if (s > best) { second = best; si = bi; best = s; bi = i; }
                    else if (s > second) { second = s; si = i; }
                }
                const double gap = std::max(0.0, best - second);
                const double boundary = 1.0 - smooth01(0.008, 0.095, gap);
                glm::dvec3 n = plates[si].center - plates[bi].center;
                n -= d * glm::dot(n,d);
                const double nl = glm::length(n);
                if (nl > 1.0e-9) n /= nl; else n = {1.0,0.0,0.0};
                const glm::dvec3 vb = glm::cross(plates[bi].pole, d) * plates[bi].speed;
                const glm::dvec3 vs = glm::cross(plates[si].pole, d) * plates[si].speed;
                const double separation = glm::dot(vs - vb, n);
                const double conv = boundary * smooth01(0.025, 0.62, -separation);
                const double div = boundary * smooth01(0.025, 0.62, separation);

                const double ridge = 1.0 - std::abs(fbm(seed ^ 0x3C6EF372FE94F82BULL, d, 9.0, 4));
                const double broad = fbm(seed ^ 0x510E527FADE682D1ULL, d, 4.2, 5);
                const double province = fbm(seed ^ 0x6A09E667F3BCC909ULL, d, 11.0, 4);
                const double orogen = std::pow(std::clamp(conv * land, 0.0, 1.0), 1.05);
                const double ridgeCore = std::pow(smooth01(0.34, 0.88, ridge), 1.65);
                const double range = orogen * (0.16 + 0.84 * ridgeCore);

                double h = 0.0;
                h += land * (280.0 + 720.0 * broad + 420.0 * province);
                // Orogenic belts get modest broad uplift, while high elevation is concentrated
                // on ridge cores. This avoids the previous several-kilometre-tall smooth slab.
                h += orogen * 850.0 + range * (900.0 + 3600.0 * ridgeCore);
                h += land * smooth01(0.55, 0.83, 0.5 + 0.5 * fbm(seed ^ 0xBB67AE8584CAA73BULL, d, 5.8, 4)) * 900.0;
                h -= ocean * (2900.0 + 2700.0 * smooth01(0.05, 0.65, -cont));
                h += ocean * div * (900.0 + 1300.0 * ridge);
                h -= ocean * conv * 1700.0;
                h = std::clamp(h, -11000.0, std::max(5000.0, maxElevation));

                base[id] = static_cast<float>(h);
                filled[id] = static_cast<float>(h);
                continental[id] = static_cast<float>(cont);
                mountain[id] = static_cast<float>(std::clamp(range, 0.0, 1.0));
                const double wet = std::clamp((1.0 - std::abs(d.y)) * 0.55 + 0.45 * (0.5 + 0.5 * fbm(seed ^ 0x1F83D9ABFB41BD6BULL, d, 4.0, 3)), 0.05, 1.0);
                rainfall[id] = static_cast<float>(wet);
            }
        }

        using Node = std::pair<float,int>;
        std::priority_queue<Node, std::vector<Node>, std::greater<Node>> pq;
        std::vector<std::uint8_t> seen(kCount, 0U);
        int oceanSeeds = 0;
        for (int i = 0; i < kCount; ++i) {
            if (base[i] <= 0.0F) {
                pq.push({base[i], i});
                seen[i] = 1U;
                ++oceanSeeds;
            }
        }
        if (oceanSeeds == 0) {
            const auto it = std::min_element(base.begin(), base.end());
            const int id = static_cast<int>(std::distance(base.begin(), it));
            pq.push({*it,id}); seen[id] = 1U;
        }

        static constexpr int dx[8] = {-1,0,1,-1,1,-1,0,1};
        static constexpr int dy[8] = {-1,-1,-1,0,0,1,1,1};
        while (!pq.empty()) {
            const auto [e,id] = pq.top(); pq.pop();
            const int x = id % kWidth, y = id / kWidth;
            for (int k = 0; k < 8; ++k) {
                const int ny = y + dy[k];
                if (ny < 0 || ny >= kHeight) continue;
                const int ni = index(x + dx[k], ny);
                if (seen[ni]) continue;
                seen[ni] = 1U;
                const float raised = std::max(base[ni], e + 0.02F);
                filled[ni] = raised;
                pq.push({raised, ni});
            }
        }

        std::vector<int> order(kCount);
        std::iota(order.begin(), order.end(), 0);
        std::sort(order.begin(), order.end(), [&](int a, int b) { return filled[a] > filled[b]; });
        std::vector<double> discharge(kCount, 0.0);
        std::vector<int> receiver(kCount, -1);
        std::vector<float> localSlope(kCount, 0.0F);
        for (int i = 0; i < kCount; ++i) discharge[i] = std::max(0.01F, rainfall[i]);

        for (int id : order) {
            if (base[id] <= 0.0F) continue;
            const int x = id % kWidth, y = id / kWidth;
            float bestDrop = 0.0F;
            int bestN = -1;
            for (int k = 0; k < 8; ++k) {
                const int ny = y + dy[k];
                if (ny < 0 || ny >= kHeight) continue;
                const int ni = index(x + dx[k], ny);
                const float drop = filled[id] - filled[ni];
                if (drop > bestDrop) { bestDrop = drop; bestN = ni; }
            }
            receiver[id] = bestN;
            localSlope[id] = bestDrop;
            if (bestN >= 0) discharge[bestN] += discharge[id];
        }

        double maxQ = 1.0;
        for (double q : discharge) maxQ = std::max(maxQ, q);
        const double logMaxQ = std::log1p(maxQ);
        elevation = base;

        for (int id = 0; id < kCount; ++id) {
            if (base[id] <= 0.0F) continue;
            const double q = std::log1p(discharge[id]) / logMaxQ;
            const double r = smooth01(0.34, 0.79, q);
            const double s = smooth01(3.0, 240.0, static_cast<double>(localSlope[id]));
            const double carve = r * (90.0 + 620.0 * s);
            elevation[id] = static_cast<float>(elevation[id] - carve);
            river[id] = static_cast<float>(r);
            incision[id] = static_cast<float>(std::clamp(carve / 700.0, 0.0, 1.0));
            floodplain[id] = static_cast<float>(r * (1.0 - s));
            elevation[id] += static_cast<float>(floodplain[id] * 55.0);
        }

        // Two conservative thermal-relaxation passes. This is deliberately far weaker than the
        // hydraulic incision: it removes grid-scale spikes without erasing range silhouettes.
        std::vector<float> scratch = elevation;
        for (int pass = 0; pass < 2; ++pass) {
            scratch = elevation;
            for (int y = 1; y < kHeight - 1; ++y) {
                for (int x = 0; x < kWidth; ++x) {
                    const int id = index(x,y);
                    if (elevation[id] <= 0.0F) continue;
                    float mean = 0.0F;
                    for (int k = 0; k < 8; ++k) mean += elevation[index(x+dx[k], y+dy[k])];
                    mean *= 0.125F;
                    const float delta = mean - elevation[id];
                    if (std::abs(delta) > 180.0F) scratch[id] += delta * 0.08F;
                }
            }
            elevation.swap(scratch);
        }

        // Widen only the visibility mask of major valleys, not the hydraulic authority itself.
        std::vector<float> riverWide = river;
        for (int y = 1; y < kHeight - 1; ++y) {
            for (int x = 0; x < kWidth; ++x) {
                const int id = index(x,y);
                float nmax = river[id];
                for (int k = 0; k < 8; ++k) nmax = std::max(nmax, river[index(x+dx[k], y+dy[k])]);
                riverWide[id] = std::max(river[id], nmax * 0.58F);
            }
        }
        river.swap(riverWide);
    }

    template <typename Vec>
    static double bilinear(const Vec& values, const glm::dvec3& d) noexcept {
        const glm::dvec3 n = glm::normalize(d);
        const double lon = std::atan2(n.z, n.x);
        const double lat = std::asin(std::clamp(n.y, -1.0, 1.0));
        double fx = (lon + kPi) / (2.0 * kPi) * kWidth - 0.5;
        double fy = (lat + 0.5 * kPi) / kPi * kHeight - 0.5;
        const int x0 = static_cast<int>(std::floor(fx));
        const int y0 = static_cast<int>(std::floor(fy));
        const double tx = fx - std::floor(fx);
        const double ty = fy - std::floor(fy);
        const int yA = std::clamp(y0, 0, kHeight-1);
        const int yB = std::clamp(y0+1, 0, kHeight-1);
        const double a = static_cast<double>(values[index(x0,yA)]);
        const double b = static_cast<double>(values[index(x0+1,yA)]);
        const double c = static_cast<double>(values[index(x0,yB)]);
        const double e = static_cast<double>(values[index(x0+1,yB)]);
        return (a + (b-a)*tx) * (1.0-ty) + (c + (e-c)*tx) * ty;
    }

    GlobalGeomorphSample sample(const glm::dvec3& d) const noexcept {
        GlobalGeomorphSample s{};
        s.elevationMeters = bilinear(elevation,d);
        s.continentalness = bilinear(continental,d);
        s.mountain = std::clamp(bilinear(mountain,d), 0.0, 1.0);
        s.river = std::clamp(bilinear(river,d), 0.0, 1.0);
        s.floodplain = std::clamp(bilinear(floodplain,d), 0.0, 1.0);
        s.incision = std::clamp(bilinear(incision,d), 0.0, 1.0);
        return s;
    }
};

inline std::shared_ptr<const Field> fieldFor(std::uint64_t seed, double radius, double maxElevation) {
    struct Cache { std::mutex mutex; std::unordered_map<std::uint64_t, std::shared_ptr<const Field>> map; };
    static Cache cache;
    const std::uint64_t key = mix64(seed ^ static_cast<std::uint64_t>(radius) ^ (static_cast<std::uint64_t>(maxElevation) << 1U));
    thread_local std::uint64_t tlsKey = 0;
    thread_local std::shared_ptr<const Field> tlsField;
    if (tlsField && tlsKey == key) return tlsField;
    std::lock_guard<std::mutex> lock(cache.mutex);
    auto it = cache.map.find(key);
    if (it == cache.map.end()) it = cache.map.emplace(key, std::make_shared<Field>(seed, radius, maxElevation)).first;
    tlsKey = key;
    tlsField = it->second;
    return tlsField;
}

} // namespace geomorph_detail

inline GlobalGeomorphSample sampleGlobalGeomorph(
    std::uint64_t seed,
    double radius,
    double maxElevation,
    const glm::dvec3& direction) {
    return geomorph_detail::fieldFor(seed, radius, maxElevation)->sample(direction);
}

} // namespace vf
