from pathlib import Path

HYDRO = Path('native/include/vf/world/RegionalHydrology.hpp')
TEST = Path('native/tests/R24HydrologicCanyonTests.cpp')


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected one anchor in {path}, found {count}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


replace_once(
    HYDRO,
'''        priorityFlood();
        accumulateDrainage();
''',
'''        priorityFlood();
        accumulateDrainage();
        calibrateStreamPowerReference();
''',
    'calibrate stream power after routing',
)

replace_once(
    HYDRO,
'''    [[nodiscard]] RegionalHydrologySample cellSample(
        std::uint32_t x,
        std::uint32_t y) const noexcept {
''',
'''    [[nodiscard]] double cellSlope(std::uint32_t x, std::uint32_t y) const noexcept {
        const std::size_t cell = index(x, y);
        const std::size_t downstream = downstream_[cell];
        if (downstream == kNoCell) return 0.0;
        const std::uint32_t dx = static_cast<std::uint32_t>(downstream % config_.resolution);
        const std::uint32_t dy = static_cast<std::uint32_t>(downstream / config_.resolution);
        const int ix = static_cast<int>(dx) - static_cast<int>(x);
        const int iy = static_cast<int>(dy) - static_cast<int>(y);
        const double distance = cellSizeMeters_ * ((ix != 0 && iy != 0) ? std::sqrt(2.0) : 1.0);
        return std::max(0.0, filled_[cell] - filled_[downstream]) / std::max(1.0, distance);
    }

    [[nodiscard]] double rawStreamPower(std::uint32_t x, std::uint32_t y) const noexcept {
        const std::size_t cell = index(x, y);
        const double count = static_cast<double>(elevation_.size());
        const double areaFraction = std::clamp(accumulation_[cell] / count, 0.0, 1.0);
        const double channel = smooth01(
            config_.riverHeadAccumulationFraction,
            config_.fullChannelAccumulationFraction,
            areaFraction);
        if (channel <= 0.0) return 0.0;
        const double slope = cellSlope(x, y);
        // Detachment-limited stream-power ordering: A^0.5 * S, gated by the actual channel network.
        return channel * std::sqrt(areaFraction) * slope;
    }

    void calibrateStreamPowerReference() {
        std::vector<double> active;
        active.reserve(elevation_.size() / 8U);
        for (std::uint32_t y = 1U; y + 1U < config_.resolution; ++y) {
            for (std::uint32_t x = 1U; x + 1U < config_.resolution; ++x) {
                const double value = rawStreamPower(x, y);
                if (value > 1.0e-15 && std::isfinite(value)) active.push_back(value);
            }
        }
        if (active.empty()) {
            streamPowerReference_ = 1.0e-12;
            return;
        }
        // Use a robust upper-channel reference rather than a hard-coded global slope scale. This
        // keeps the ordering physical while making the finite gameplay incision budget adapt to the
        // actual routed DEM. Isolated extreme cells cannot define the scale.
        const std::size_t rank = std::min(
            active.size() - 1U,
            static_cast<std::size_t>(0.90 * static_cast<double>(active.size() - 1U)));
        std::nth_element(active.begin(), active.begin() + rank, active.end());
        streamPowerReference_ = std::max(active[rank], 1.0e-12);
    }

    [[nodiscard]] RegionalHydrologySample cellSample(
        std::uint32_t x,
        std::uint32_t y) const noexcept {
''',
    'stream power calibration helpers',
)

replace_once(
    HYDRO,
'''        const std::size_t downstream = downstream_[cell];
        double slope = 0.0;
        if (downstream != kNoCell) {
            const std::uint32_t dx = static_cast<std::uint32_t>(downstream % config_.resolution);
            const std::uint32_t dy = static_cast<std::uint32_t>(downstream / config_.resolution);
            const int ix = static_cast<int>(dx) - static_cast<int>(x);
            const int iy = static_cast<int>(dy) - static_cast<int>(y);
            const double distance = cellSizeMeters_ * ((ix != 0 && iy != 0) ? std::sqrt(2.0) : 1.0);
            slope = std::max(0.0, filled_[cell] - filled_[downstream]) / std::max(1.0, distance);
        }
        const double fullChannelArea = std::max(
            config_.fullChannelAccumulationFraction, 1.0e-7);
        const double normalizedArea = std::clamp(areaFraction / fullChannelArea, 0.0, 1.0);
        const double areaPower = std::sqrt(normalizedArea); // stream-power m = 0.5
        const double normalizedSlope = std::clamp(slope / 0.075, 0.0, 1.0); // n = 1
        const double streamPower = areaPower * normalizedSlope;
        // A small channel-floor term keeps Priority-Flood flats connected after depression filling;
        // the large canyon component still requires both accumulated drainage area and real slope.
        const double incisionResponse = std::clamp(0.12 + 0.88 * streamPower, 0.0, 1.0);
        const double incision = config_.maxIncisionMeters * channel * incisionResponse;
''',
'''        const double slope = cellSlope(x, y);
        const double weightedStreamPower = channel * std::sqrt(areaFraction) * slope;
        const double incisionResponse = std::clamp(
            weightedStreamPower / std::max(streamPowerReference_, 1.0e-12),
            0.0,
            1.0);
        const double incision = config_.maxIncisionMeters * incisionResponse;
''',
    'replace hard-coded slope normalization',
)

replace_once(
    HYDRO,
'''    double cellSizeMeters_{};
    std::vector<double> elevation_;
''',
'''    double cellSizeMeters_{};
    double streamPowerReference_{1.0e-12};
    std::vector<double> elevation_;
''',
    'stream power reference member',
)

replace_once(
    TEST,
'''    require(maxChannel > 0.80, "Priority-Flood accumulation must create strong regional channels");
    require(maxIncision > 900.0, "stream-power channels must create kilometre-scale canyon incision");
''',
'''    std::cout << "R24 hydrologic canyon diagnostics"
              << " | max_channel=" << maxChannel
              << " max_incision_m=" << maxIncision
              << " max_authority_cut_m=" << maxAuthorityCut
              << " max_canyon=" << maxCanyon << '\\n';
    require(maxChannel > 0.80, "Priority-Flood accumulation must create strong regional channels");
    require(maxIncision > 900.0, "stream-power channels must create kilometre-scale canyon incision");
''',
    'pre-gate diagnostics',
)

text = HYDRO.read_text(encoding='utf-8')
for marker in ('calibrateStreamPowerReference();', 'rawStreamPower(', 'streamPowerReference_'):
    if marker not in text:
        raise SystemExit(f'missing calibrated stream-power marker: {marker}')
if 'slope / 0.075' in text:
    raise SystemExit('legacy hard-coded stream-power slope scale still present')

print('R24 hydrologic stream power calibrated to routed DEM')
