#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
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
    double plateau{};
    double river{};
    double channel{};
    double floodplain{};
    double incision{};
};

namespace geomorph_detail {

// R16 is an adaptation of the architecture used by owenyuwono/demiurge (MIT):
// cube-sphere authority -> tectonic uplift forcing -> per-step Priority-Flood ->
// MFD routing -> stream-power erosion/deposition -> thermal talus relaxation.
// We intentionally keep the implementation native/C++ and deterministic for Voxel Frontier.
// R18: match the mature erosion reference's 256^2 cubemap process grid. At Earth radius this
// puts the global process cell near the 40 km class instead of R16/R17's ~80 km class; local
// clipmaps still refine the baked field continuously down to metre scale.
constexpr int kRes = 256;
constexpr int kFaces = 6;
constexpr int kFaceCells = kRes * kRes;
constexpr int kCount = kFaces * kFaceCells;
constexpr double kPi = 3.1415926535897932384626433832795;
constexpr int kPlateCount = 24;
constexpr int kErosionSteps = 60;
constexpr double kMfdPower = 6.0;

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
    double sum = 0.0;
    double amp = 1.0;
    double norm = 0.0;
    for (int i = 0; i < octaves; ++i) {
        sum += valueNoise3(mix64(seed + static_cast<std::uint64_t>(i) * 37ULL), d * frequency) * amp;
        norm += amp;
        amp *= 0.5;
        frequency *= 2.0;
    }
    return norm > 0.0 ? sum / norm : 0.0;
}

inline double ridged(std::uint64_t seed, const glm::dvec3& d, double frequency, int octaves) noexcept {
    double sum = 0.0;
    double amp = 1.0;
    double norm = 0.0;
    for (int i = 0; i < octaves; ++i) {
        const double n = valueNoise3(mix64(seed + static_cast<std::uint64_t>(i) * 53ULL), d * frequency);
        const double r = 1.0 - std::abs(n);
        sum += r * r * amp;
        norm += amp;
        amp *= 0.5;
        frequency *= 2.0;
    }
    return norm > 0.0 ? sum / norm : 0.0;
}

inline glm::dvec3 seededDirection(std::uint64_t seed, std::uint64_t channel) noexcept {
    const double y = unit01(seed, channel + 1U) * 2.0 - 1.0;
    const double a = unit01(seed, channel + 2U) * 2.0 * kPi;
    const double r = std::sqrt(std::max(0.0, 1.0 - y * y));
    return {std::cos(a) * r, y, std::sin(a) * r};
}

inline int cellIndex(int face, int x, int y) noexcept {
    return face * kFaceCells + std::clamp(y, 0, kRes - 1) * kRes + std::clamp(x, 0, kRes - 1);
}

inline glm::dvec3 cubeDirection(int face, double u, double v) noexcept {
    glm::dvec3 p{};
    switch (face) {
    case 0: p = { 1.0, v, -u}; break;
    case 1: p = {-1.0, v,  u}; break;
    case 2: p = { u, 1.0, -v}; break;
    case 3: p = { u,-1.0,  v}; break;
    case 4: p = { u, v,  1.0}; break;
    default:p = {-u, v, -1.0}; break;
    }
    return glm::normalize(p);
}

inline glm::dvec3 directionAt(int face, int x, int y) noexcept {
    const double u = -1.0 + 2.0 * (static_cast<double>(x) + 0.5) / static_cast<double>(kRes);
    const double v = -1.0 + 2.0 * (static_cast<double>(y) + 0.5) / static_cast<double>(kRes);
    return cubeDirection(face, u, v);
}

struct CubeCoord { int face{}; double u{}; double v{}; };

inline CubeCoord toCube(const glm::dvec3& input) noexcept {
    const glm::dvec3 d = glm::normalize(input);
    const double ax = std::abs(d.x), ay = std::abs(d.y), az = std::abs(d.z);
    CubeCoord c{};
    if (ax >= ay && ax >= az) {
        if (d.x >= 0.0) { c.face = 0; c.u = -d.z / ax; c.v = d.y / ax; }
        else            { c.face = 1; c.u =  d.z / ax; c.v = d.y / ax; }
    } else if (ay >= ax && ay >= az) {
        if (d.y >= 0.0) { c.face = 2; c.u = d.x / ay; c.v = -d.z / ay; }
        else            { c.face = 3; c.u = d.x / ay; c.v =  d.z / ay; }
    } else {
        if (d.z >= 0.0) { c.face = 4; c.u =  d.x / az; c.v = d.y / az; }
        else            { c.face = 5; c.u = -d.x / az; c.v = d.y / az; }
    }
    c.u = std::clamp(c.u, -1.0, 1.0);
    c.v = std::clamp(c.v, -1.0, 1.0);
    return c;
}

inline int nearestCell(const glm::dvec3& d) noexcept {
    const CubeCoord c = toCube(d);
    const int x = std::clamp(static_cast<int>((c.u + 1.0) * 0.5 * kRes), 0, kRes - 1);
    const int y = std::clamp(static_cast<int>((c.v + 1.0) * 0.5 * kRes), 0, kRes - 1);
    return cellIndex(c.face, x, y);
}

inline glm::dvec3 directionForExtendedCell(int face, int x, int y) noexcept {
    const double u = -1.0 + 2.0 * (static_cast<double>(x) + 0.5) / static_cast<double>(kRes);
    const double v = -1.0 + 2.0 * (static_cast<double>(y) + 0.5) / static_cast<double>(kRes);
    return cubeDirection(face, u, v);
}

struct Plate {
    glm::dvec3 center{};
    glm::dvec3 pole{};
    double speed{};
    double baseElevation{};
    bool continental{};
};

struct Field {
    std::uint64_t seed{};
    double radius{};
    double maxElevation{};
    std::vector<std::array<int,8>> neighbors;
    std::vector<std::uint8_t> neighborCount;
    std::vector<float> elevation;
    std::vector<float> continental;
    std::vector<float> mountain;
    std::vector<float> plateau;
    std::vector<float> river;
    std::vector<float> floodplain;
    std::vector<float> incision;
    std::vector<float> hardness;
    std::vector<int> receiver;

    explicit Field(std::uint64_t s, double r, double maxElev)
        : seed(s), radius(r), maxElevation(maxElev),
          neighbors(kCount), neighborCount(kCount, 0U), elevation(kCount), continental(kCount),
          mountain(kCount), plateau(kCount), river(kCount), floodplain(kCount), incision(kCount), hardness(kCount),
          receiver(kCount, -1) {
        buildNeighborTable();
        bake();
    }

    void buildNeighborTable() {
        for (int face = 0; face < kFaces; ++face) {
            for (int y = 0; y < kRes; ++y) {
                for (int x = 0; x < kRes; ++x) {
                    const int id = cellIndex(face, x, y);
                    std::uint8_t count = 0;
                    for (int dy = -1; dy <= 1; ++dy) {
                        for (int dx = -1; dx <= 1; ++dx) {
                            if (dx == 0 && dy == 0) continue;
                            const int ni = nearestCell(directionForExtendedCell(face, x + dx, y + dy));
                            if (ni == id) continue;
                            bool duplicate = false;
                            for (std::uint8_t n = 0; n < count; ++n) duplicate = duplicate || neighbors[id][n] == ni;
                            if (!duplicate && count < 8U) neighbors[id][count++] = ni;
                        }
                    }
                    neighborCount[id] = count;
                }
            }
        }
    }

    static void spreadMax(
        const std::vector<std::array<int,8>>& neigh,
        const std::vector<std::uint8_t>& counts,
        std::vector<float>& field,
        int passes,
        float decay) {
        std::vector<float> tmp(field.size());
        for (int pass = 0; pass < passes; ++pass) {
            tmp = field;
            for (std::size_t i = 0; i < field.size(); ++i) {
                float best = field[i];
                for (std::uint8_t n = 0; n < counts[i]; ++n) best = std::max(best, field[neigh[i][n]] * decay);
                tmp[i] = best;
            }
            field.swap(tmp);
        }
    }

    void priorityFlood(const std::vector<float>& h, std::vector<float>& filled, const std::vector<std::uint8_t>& ocean) const {
        using Node = std::pair<float,int>;
        std::priority_queue<Node, std::vector<Node>, std::greater<Node>> heap;
        filled = h;
        std::vector<std::uint8_t> queued(kCount, 0U);
        std::vector<std::uint8_t> processed(kCount, 0U);
        int seedCount = 0;
        for (int i = 0; i < kCount; ++i) {
            if (ocean[i]) {
                heap.push({h[i], i});
                queued[i] = 1U;
                ++seedCount;
            }
        }
        if (seedCount == 0) {
            const auto it = std::min_element(h.begin(), h.end());
            const int id = static_cast<int>(std::distance(h.begin(), it));
            heap.push({*it, id});
            queued[id] = 1U;
        }
        std::uint64_t floodOrder = 0;
        while (!heap.empty()) {
            const auto [e, id] = heap.top(); heap.pop();
            if (processed[id]) continue;
            processed[id] = 1U;
            ++floodOrder;
            for (std::uint8_t k = 0; k < neighborCount[id]; ++k) {
                const int n = neighbors[id][k];
                if (processed[n]) continue;
                const float raised = std::max(filled[n], e + static_cast<float>(1.0e-7 * static_cast<double>(floodOrder)));
                if (raised > filled[n]) filled[n] = raised;
                if (!queued[n]) {
                    queued[n] = 1U;
                    heap.push({filled[n], n});
                }
            }
        }
    }

    void bake() {
        std::array<Plate, kPlateCount> plates{};
        for (int i = 0; i < kPlateCount; ++i) {
            plates[i].center = seededDirection(seed, 100U + static_cast<std::uint64_t>(i) * 11U);
            plates[i].pole = seededDirection(seed, 600U + static_cast<std::uint64_t>(i) * 13U);
            plates[i].speed = 0.38 + 0.72 * unit01(seed, 1100U + static_cast<std::uint64_t>(i) * 17U);
            plates[i].baseElevation = unit01(seed, 1700U + static_cast<std::uint64_t>(i) * 19U) * 2.0 - 1.0;
            plates[i].continental = unit01(seed, 2300U + static_cast<std::uint64_t>(i) * 23U) < 0.42;
        }

        std::vector<float> h0(kCount, 0.0F);
        std::vector<float> rainfall(kCount, 0.0F);
        std::vector<float> rawConv(kCount, 0.0F);
        std::vector<float> rawDiv(kCount, 0.0F);
        std::vector<float> rawCC(kCount, 0.0F);
        std::vector<float> uplift(kCount, 0.0F);
        std::vector<float> plateauDrive(kCount, 0.0F);
        std::vector<float> plateauDrive(kCount, 0.0F);

        for (int face = 0; face < kFaces; ++face) {
            for (int y = 0; y < kRes; ++y) {
                for (int x = 0; x < kRes; ++x) {
                    const int id = cellIndex(face, x, y);
                    const glm::dvec3 d = directionAt(face, x, y);
                    double best = -2.0, second = -2.0;
                    int bi = 0, si = 1;
                    for (int p = 0; p < kPlateCount; ++p) {
                        const double score = glm::dot(d, plates[p].center);
                        if (score > best) { second = best; si = bi; best = score; bi = p; }
                        else if (score > second) { second = score; si = p; }
                    }

                    const double gap = std::max(0.0, best - second);
                    const double boundary = 1.0 - smooth01(0.004, 0.085, gap);
                    glm::dvec3 normal = plates[si].center - plates[bi].center;
                    normal -= d * glm::dot(normal, d);
                    const double nl = glm::length(normal);
                    normal = nl > 1.0e-9 ? normal / nl : glm::dvec3{1.0, 0.0, 0.0};
                    const glm::dvec3 va = glm::cross(plates[bi].pole, d) * plates[bi].speed;
                    const glm::dvec3 vb = glm::cross(plates[si].pole, d) * plates[si].speed;
                    const double separation = glm::dot(vb - va, normal);
                    const double convergence = boundary * smooth01(0.018, 0.52, -separation);
                    const double divergence = boundary * smooth01(0.018, 0.52, separation);
                    rawConv[id] = static_cast<float>(convergence);
                    rawDiv[id] = static_cast<float>(divergence);
                    rawCC[id] = static_cast<float>(convergence * (plates[bi].continental && plates[si].continental ? 1.0 : 0.0));

                    const double macro = fbm(seed ^ 0x243F6A8885A308D3ULL, d, 1.15, 5);
                    const double meso = fbm(seed ^ 0x13198A2E03707344ULL, d, 2.7, 4);
                    const double coast = fbm(seed ^ 0xA4093822299F31D0ULL, d, 6.0, 3);
                    const double plateBias = plates[bi].continental ? 0.26 : -0.36;
                    const double cont = std::clamp(plateBias + macro * 0.58 + meso * 0.22 + coast * 0.06, -1.0, 1.0);
                    continental[id] = static_cast<float>(cont);
                    const double land = smooth01(-0.045, 0.090, cont);
                    const double interior = smooth01(0.05, 0.42, cont);
                    const double ocean = 1.0 - land;

                    const double und = fbm(seed ^ 0x510E527FADE682D1ULL, d, 3.5, 4);
                    const double basin = fbm(seed ^ 0x6A09E667F3BCC909ULL, d, 0.72, 3);
                    const double deep = smooth01(0.08, 0.72, -cont);
                    double h = land * (120.0 + 780.0 * interior + 520.0 * und + 260.0 * basin);
                    h -= ocean * (3000.0 + 2500.0 * deep);
                    h += ocean * divergence * (750.0 + 1250.0 * ridged(seed ^ 0xD1310BA698DFB5ACULL, d, 8.0, 4));
                    h -= ocean * convergence * 1350.0;
                    h += plates[bi].baseElevation * (land * 180.0 + ocean * 260.0);
                    h0[id] = static_cast<float>(std::clamp(h, -11000.0, 4200.0));

                    const double hardNoise = 0.5 + 0.5 * fbm(seed ^ 0x91E10DA5C79E7B1DULL, d, 8.5, 4);
                    hardness[id] = static_cast<float>(std::clamp(0.18 + 0.50 * hardNoise + 0.25 * convergence + 0.12 * divergence, 0.0, 1.0));
                    const double latitudeWet = std::clamp(1.0 - std::abs(d.y) * 0.72, 0.0, 1.0);
                    const double rainNoise = 0.5 + 0.5 * fbm(seed ^ 0x1F83D9ABFB41BD6BULL, d, 4.2, 3);
                    rainfall[id] = static_cast<float>(std::clamp(0.08 + 0.55 * latitudeWet + 0.37 * rainNoise, 0.05, 1.0));
                }
            }
        }

        // Demiurge terrainSampler uses active convergence decaying behind the front and a
        // separate CC-collision plateau term. Spread the boundary forcing over several cubemap
        // cells before erosion so the uplifted landmass is regional, not a one-cell wall.
        std::vector<float> convSpread = rawConv;
        std::vector<float> ccSpread = rawCC;
        // R18 process-scale orogeny. The doubled grid resolution makes these 8/14-cell
        // spreads roughly 300-550 km wide on Earth: regional belts rather than continent-wide
        // blankets. Ridged fields modulate the UPLIFT FORCING before erosion, never the final DEM.
        spreadMax(neighbors, neighborCount, convSpread, 8, 0.80F);
        spreadMax(neighbors, neighborCount, ccSpread, 14, 0.88F);

        for (int i = 0; i < kCount; ++i) {
            const glm::dvec3 d = directionAt(i / kFaceCells, i % kRes, (i % kFaceCells) / kRes);
            const double paleo = std::pow(ridged(seed ^ 0xB7E151628AED2A6BULL, d, 2.6, 4), 2.6);
            const double land = smooth01(-0.03, 0.10, continental[i]);
            const double primaryRidge = std::pow(ridged(seed ^ 0xD6E8FEB86659FD93ULL, d, 11.0, 4), 1.55);
            const double branchRidge = std::pow(ridged(seed ^ 0xA5A3564E27F8862FULL, d, 29.0, 3), 1.70);
            const double activeOrogen = convSpread[i]
                * (0.66 + 0.42 * primaryRidge + 0.18 * branchRidge);
            // Continental collision has a broad, resistant interior shoulder. It participates in
            // uplift and erosion rather than being flattened to an arbitrary post-bake altitude.
            const double collisionInterior = ccSpread[i]
                * (1.0 - 0.48 * static_cast<double>(rawConv[i]));
            plateauDrive[i] = static_cast<float>(std::clamp(land * collisionInterior, 0.0, 1.0));
            uplift[i] = static_cast<float>(std::clamp(
                land * (0.74 * activeOrogen + 0.86 * collisionInterior + 0.18 * paleo), 0.0, 1.0));
            hardness[i] = static_cast<float>(std::clamp(
                static_cast<double>(hardness[i]) + 0.16 * primaryRidge * convSpread[i]
                    + 0.20 * plateauDrive[i],
                0.0, 1.0));
        }

        std::vector<std::uint8_t> ocean(kCount, 0U);
        for (int i = 0; i < kCount; ++i) ocean[i] = h0[i] < 0.0F ? 1U : 0U;

        std::vector<float> work = h0;
        std::vector<float> filled(kCount);
        std::vector<int> order(kCount);
        std::iota(order.begin(), order.end(), 0);
        std::vector<std::array<int,8>> mfdNeighbor(kCount);
        std::vector<std::array<float,8>> mfdWeight(kCount);
        std::vector<std::uint8_t> mfdCount(kCount, 0U);
        std::vector<double> discharge(kCount, 0.0);
        std::vector<double> sediment(kCount, 0.0);
        std::vector<float> buf(kCount);
        std::vector<float> lastFilled(kCount);

        // 60 process iterations, close to the mature reference. Total maximum tectonic lift is
        // ~3.1 km before differential erosion, enough for coherent ranges without a post-bake peak stamp.
        constexpr double upliftRateMeters = 52.0;
        constexpr double dt = 0.0048;
        constexpr double k0 = 0.34;
        constexpr double mExp = 0.45;
        constexpr double depositionG = 1.45;
        constexpr double dhClamp = 22.0;

        for (int step = 0; step < kErosionSteps; ++step) {
            for (int i = 0; i < kCount; ++i) {
                if (!ocean[i]) work[i] += static_cast<float>(upliftRateMeters * uplift[i]);
            }

            priorityFlood(work, filled, ocean);
            lastFilled = filled;
            std::sort(order.begin(), order.end(), [&](int a, int b) {
                if (filled[a] != filled[b]) return filled[a] > filled[b];
                return a > b;
            });

            std::fill(mfdCount.begin(), mfdCount.end(), 0U);
            for (int id = 0; id < kCount; ++id) {
                if (ocean[id]) continue;
                double sumW = 0.0;
                std::array<double,8> raw{};
                std::uint8_t count = 0;
                for (std::uint8_t k = 0; k < neighborCount[id]; ++k) {
                    const int n = neighbors[id][k];
                    if (filled[n] < filled[id] || (filled[n] == filled[id] && n < id)) {
                        const double slope = std::max(1.0e-6, static_cast<double>(filled[id] - filled[n]));
                        const double rw = std::pow(slope, kMfdPower);
                        raw[count] = rw;
                        mfdNeighbor[id][count] = n;
                        sumW += rw;
                        ++count;
                    }
                }
                if (count == 0 || sumW < 1.0e-24) continue;
                mfdCount[id] = count;
                for (std::uint8_t k = 0; k < count; ++k) mfdWeight[id][k] = static_cast<float>(raw[k] / sumW);
            }

            for (int i = 0; i < kCount; ++i) discharge[i] = rainfall[i];
            for (const int id : order) {
                if (ocean[id]) continue;
                for (std::uint8_t k = 0; k < mfdCount[id]; ++k) {
                    const int n = mfdNeighbor[id][k];
                    if (!ocean[n]) discharge[n] += discharge[id] * static_cast<double>(mfdWeight[id][k]);
                }
            }

            std::fill(sediment.begin(), sediment.end(), 0.0);
            buf = work;
            for (const int id : order) {
                if (ocean[id]) continue;
                double slope = 0.0;
                for (std::uint8_t k = 0; k < mfdCount[id]; ++k) {
                    const int n = mfdNeighbor[id][k];
                    slope += static_cast<double>(mfdWeight[id][k]) * std::max(0.0, static_cast<double>(filled[id] - filled[n]));
                }
                const double erodibility = 1.0 + 1.1 * (0.5 - static_cast<double>(hardness[id]));
                const double erosionRate = dt * k0 * erodibility
                    * std::pow(std::max(0.05, discharge[id]), mExp)
                    * std::max(0.20, slope);
                const double deposition = dt * depositionG * sediment[id] / std::max(0.05, discharge[id]);
                double dh = std::clamp(deposition - erosionRate, -dhClamp, dhClamp);
                if (mfdCount[id] == 0) dh = std::max(dh, -3.0);
                buf[id] = static_cast<float>(work[id] + dh);
                const double outSediment = std::max(0.0, sediment[id] + erosionRate - deposition);
                for (std::uint8_t k = 0; k < mfdCount[id]; ++k) {
                    const int n = mfdNeighbor[id][k];
                    if (!ocean[n]) sediment[n] += outSediment * static_cast<double>(mfdWeight[id][k]);
                }
            }
            work.swap(buf);

            // Three talus passes per uplift/erosion step, matching the mature bake structure.
            for (int thermal = 0; thermal < 3; ++thermal) {
                buf = work;
                for (int id = 0; id < kCount; ++id) {
                    if (ocean[id]) continue;
                    // Same physical talus angle as the 128 grid: neighbour spacing halves at R18.
                    const double talus = (105.0 * 128.0 / static_cast<double>(kRes))
                        * (0.72 + 0.56 * hardness[id]);
                    for (std::uint8_t k = 0; k < neighborCount[id]; ++k) {
                        const int n = neighbors[id][k];
                        const double excess = static_cast<double>(work[id] - work[n]) - talus;
                        if (excess <= 0.0) continue;
                        const double transfer = excess * 0.0012;
                        buf[id] -= static_cast<float>(transfer);
                        buf[n] += static_cast<float>(transfer);
                    }
                }
                work.swap(buf);
            }
        }

        // Final hydrology after the uplift/erode loop. It supplies both the broad valley mask and
        // the dominant receiver used to reconstruct a narrow sub-grid river centerline at query time.
        priorityFlood(work, filled, ocean);
        std::sort(order.begin(), order.end(), [&](int a, int b) {
            if (filled[a] != filled[b]) return filled[a] > filled[b];
            return a > b;
        });
        std::fill(mfdCount.begin(), mfdCount.end(), 0U);
        std::fill(receiver.begin(), receiver.end(), -1);
        for (int id = 0; id < kCount; ++id) {
            if (ocean[id]) continue;
            double sumW = 0.0;
            std::array<double,8> raw{};
            std::uint8_t count = 0;
            for (std::uint8_t k = 0; k < neighborCount[id]; ++k) {
                const int n = neighbors[id][k];
                if (filled[n] < filled[id] || (filled[n] == filled[id] && n < id)) {
                    const double slope = std::max(1.0e-6, static_cast<double>(filled[id] - filled[n]));
                    const double rw = std::pow(slope, kMfdPower);
                    raw[count] = rw;
                    mfdNeighbor[id][count] = n;
                    sumW += rw;
                    ++count;
                }
            }
            if (count == 0 || sumW < 1.0e-24) continue;
            mfdCount[id] = count;
            double bestW = -1.0;
            int bestReceiver = -1;
            for (std::uint8_t k = 0; k < count; ++k) {
                const double w = raw[k] / sumW;
                mfdWeight[id][k] = static_cast<float>(w);
                if (w > bestW) { bestW = w; bestReceiver = mfdNeighbor[id][k]; }
            }
            receiver[id] = bestReceiver;
        }

        for (int i = 0; i < kCount; ++i) discharge[i] = rainfall[i];
        for (const int id : order) {
            if (ocean[id]) continue;
            for (std::uint8_t k = 0; k < mfdCount[id]; ++k) {
                const int n = mfdNeighbor[id][k];
                if (!ocean[n]) discharge[n] += discharge[id] * static_cast<double>(mfdWeight[id][k]);
            }
        }
        double maxQ = 1.0;
        for (double q : discharge) maxQ = std::max(maxQ, q);
        const double logMaxQ = std::log1p(maxQ);

        elevation = work;
        for (int id = 0; id < kCount; ++id) {
            if (ocean[id]) {
                elevation[id] = std::clamp(elevation[id], -11000.0F, -2.0F);
                continue;
            }
            const double qNorm = std::log1p(discharge[id]) / logMaxQ;
            double slope = 0.0;
            for (std::uint8_t k = 0; k < mfdCount[id]; ++k) {
                const int n = mfdNeighbor[id][k];
                slope += static_cast<double>(mfdWeight[id][k]) * std::max(0.0, static_cast<double>(filled[id] - filled[n]));
            }
            const double riverMask = smooth01(0.32, 0.74, qNorm);
            const double slopeScale = 128.0 / static_cast<double>(kRes);
            const double lowSlope = 1.0 - smooth01(35.0 * slopeScale, 280.0 * slopeScale, slope);
            river[id] = static_cast<float>(riverMask);
            floodplain[id] = static_cast<float>(riverMask * lowSlope);
            const double expectedUplifted = static_cast<double>(h0[id]) + upliftRateMeters * kErosionSteps * uplift[id];
            const double cut = std::max(0.0, expectedUplifted - static_cast<double>(elevation[id]));
            incision[id] = static_cast<float>(std::clamp(cut / 1500.0, 0.0, 1.0));

            float localMin = elevation[id];
            float localMax = elevation[id];
            for (std::uint8_t k = 0; k < neighborCount[id]; ++k) {
                localMin = std::min(localMin, elevation[neighbors[id][k]]);
                localMax = std::max(localMax, elevation[neighbors[id][k]]);
            }
            const double relief = static_cast<double>(localMax - localMin);
            const double reliefMountain = smooth01(240.0, 1800.0, relief);
            const double activeFront = std::clamp(
                0.82 * static_cast<double>(convSpread[id])
                    + 0.28 * static_cast<double>(rawConv[id]), 0.0, 1.0);
            mountain[id] = static_cast<float>(std::clamp(
                0.68 * activeFront + 0.52 * reliefMountain
                    - 0.22 * static_cast<double>(plateauDrive[id]),
                0.0, 1.0));
            const double broadLevel = 1.0 - smooth01(650.0, 2300.0, relief);
            plateau[id] = static_cast<float>(std::clamp(
                static_cast<double>(plateauDrive[id])
                    * smooth01(900.0, 2200.0, static_cast<double>(elevation[id]))
                    * (0.32 + 0.68 * broadLevel)
                    * (1.0 - 0.62 * static_cast<double>(incision[id])),
                0.0, 1.0));

            // Depositional broadening is geometry, not just a material label.
            elevation[id] += static_cast<float>(floodplain[id] * 22.0);
            elevation[id] = std::clamp(elevation[id], -11000.0F, static_cast<float>(std::max(5000.0, maxElevation)));
        }
    }

    template <typename Vec>
    double sampleBilinear(const Vec& values, const glm::dvec3& direction) const noexcept {
        const CubeCoord c = toCube(direction);
        const double gx = (c.u + 1.0) * 0.5 * kRes - 0.5;
        const double gy = (c.v + 1.0) * 0.5 * kRes - 0.5;
        const int x0 = static_cast<int>(std::floor(gx));
        const int y0 = static_cast<int>(std::floor(gy));
        const double tx = gx - std::floor(gx);
        const double ty = gy - std::floor(gy);
        auto corner = [&](int x, int y) -> double {
            return static_cast<double>(values[nearestCell(directionForExtendedCell(c.face, x, y))]);
        };
        const double a = corner(x0, y0);
        const double b = corner(x0 + 1, y0);
        const double d = corner(x0, y0 + 1);
        const double e = corner(x0 + 1, y0 + 1);
        return (a + (b - a) * tx) * (1.0 - ty) + (d + (e - d) * tx) * ty;
    }

    GlobalGeomorphSample sample(const glm::dvec3& input) const noexcept {
        const glm::dvec3 q = glm::normalize(input);
        GlobalGeomorphSample s{};
        s.elevationMeters = sampleBilinear(elevation, q);
        s.continentalness = std::clamp(sampleBilinear(continental, q), -1.0, 1.0);
        s.mountain = std::clamp(sampleBilinear(mountain, q), 0.0, 1.0);
        s.plateau = std::clamp(sampleBilinear(plateau, q), 0.0, 1.0);
        s.river = std::clamp(sampleBilinear(river, q), 0.0, 1.0);
        s.floodplain = std::clamp(sampleBilinear(floodplain, q), 0.0, 1.0);
        s.incision = std::clamp(sampleBilinear(incision, q), 0.0, 1.0);

        const glm::dvec3 ref = std::abs(q.y) < 0.88 ? glm::dvec3{0.0, 1.0, 0.0} : glm::dvec3{1.0, 0.0, 0.0};
        const glm::dvec3 east = glm::normalize(glm::cross(ref, q));
        const glm::dvec3 north = glm::normalize(glm::cross(q, east));
        auto localMeters = [&](const glm::dvec3& pInput) {
            const glm::dvec3 p = glm::normalize(pInput);
            const double c = std::clamp(glm::dot(q, p), -1.0, 1.0);
            const double angle = std::acos(c);
            glm::dvec3 tangent = p - q * c;
            const double tl = glm::length(tangent);
            if (tl < 1.0e-12 || angle < 1.0e-12) return glm::dvec2{0.0};
            tangent /= tl;
            return glm::dvec2{glm::dot(tangent, east), glm::dot(tangent, north)} * (angle * radius);
        };

        const CubeCoord cc = toCube(q);
        const double gx = (cc.u + 1.0) * 0.5 * kRes - 0.5;
        const double gy = (cc.v + 1.0) * 0.5 * kRes - 0.5;
        const int cx = static_cast<int>(std::floor(gx));
        const int cy = static_cast<int>(std::floor(gy));
        double channel = 0.0;
        for (int oy = -2; oy <= 2; ++oy) {
            for (int ox = -2; ox <= 2; ++ox) {
                const int id = nearestCell(directionForExtendedCell(cc.face, cx + ox, cy + oy));
                const int rid = receiver[id];
                const double strength = std::clamp(static_cast<double>(river[id]), 0.0, 1.0);
                if (rid < 0 || strength < 0.28) continue;
                const int faceA = id / kFaceCells;
                const int remA = id % kFaceCells;
                const int ax = remA % kRes;
                const int ay = remA / kRes;
                const int faceB = rid / kFaceCells;
                const int remB = rid % kFaceCells;
                const int bx = remB % kRes;
                const int by = remB / kRes;
                const glm::dvec2 a = localMeters(directionAt(faceA, ax, ay));
                const glm::dvec2 b = localMeters(directionAt(faceB, bx, by));
                const glm::dvec2 ab = b - a;
                const double ab2 = glm::dot(ab, ab);
                const double t = ab2 > 1.0 ? std::clamp(-glm::dot(a, ab) / ab2, 0.0, 1.0) : 0.0;
                const double distance = glm::length(a + ab * t);
                const double halfWidth = 80.0 + 520.0 * std::pow(strength, 1.75);
                const double core = 1.0 - smooth01(halfWidth * 0.28, halfWidth, distance);
                channel = std::max(channel, core * (0.54 + 0.46 * strength));
            }
        }
        s.channel = std::clamp(channel, 0.0, 1.0);
        return s;
    }
};

inline std::shared_ptr<const Field> fieldFor(std::uint64_t seed, double radius, double maxElevation) {
    struct Cache {
        std::mutex mutex;
        std::unordered_map<std::uint64_t, std::shared_ptr<const Field>> map;
    };
    static Cache cache;
    const std::uint64_t key = mix64(seed
        ^ static_cast<std::uint64_t>(radius)
        ^ (static_cast<std::uint64_t>(maxElevation) << 1U));
    thread_local std::uint64_t tlsKey = 0;
    thread_local std::shared_ptr<const Field> tlsField;
    if (tlsField && tlsKey == key) return tlsField;
    std::lock_guard<std::mutex> lock(cache.mutex);
    auto it = cache.map.find(key);
    if (it == cache.map.end()) {
        it = cache.map.emplace(key, std::make_shared<Field>(seed, radius, maxElevation)).first;
    }
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
