#pragma once

#include <algorithm>
#include <cstddef>
#include <cstdint>

namespace vf::core {

struct FrameBudgetConfig {
    // 120 FPS is the minimum gameplay acceptance line. Rendering itself remains uncapped.
    double targetFrameMilliseconds{1000.0 / 120.0};
    double mainThreadStreamingMilliseconds{0.35};
    std::uint32_t maxGenerationDispatches{64U};
    std::uint32_t maxMeshingDispatches{64U};
    std::uint32_t maxUploadCommits{24U};
    std::uint32_t maxEvictions{64U};
    std::size_t maxUploadBytes{16U * 1024U * 1024U};
};

struct FrameBudgetUsage {
    std::uint32_t generationDispatches{};
    std::uint32_t meshingDispatches{};
    std::uint32_t uploadCommits{};
    std::uint32_t evictions{};
    std::size_t uploadBytes{};
};

// R24_ENGINE_FOUNDATION_V1
// Heavy systems do not get to consume arbitrary work just because queues are long.
// Every stage must reserve a bounded slice of the frame and defer excess work.
class FrameBudget final {
public:
    explicit FrameBudget(FrameBudgetConfig config = {}) noexcept : config_(sanitize(config)) {}

    void beginFrame() noexcept { usage_ = {}; }

    [[nodiscard]] bool reserveGeneration(std::uint32_t count = 1U) noexcept {
        return reserveCount(usage_.generationDispatches, count, config_.maxGenerationDispatches);
    }
    [[nodiscard]] bool reserveMeshing(std::uint32_t count = 1U) noexcept {
        return reserveCount(usage_.meshingDispatches, count, config_.maxMeshingDispatches);
    }
    [[nodiscard]] bool reserveUpload(std::size_t bytes) noexcept {
        if (usage_.uploadCommits >= config_.maxUploadCommits) return false;
        if (bytes > config_.maxUploadBytes - std::min(usage_.uploadBytes, config_.maxUploadBytes))
            return false;
        ++usage_.uploadCommits;
        usage_.uploadBytes += bytes;
        return true;
    }
    [[nodiscard]] bool reserveEviction(std::uint32_t count = 1U) noexcept {
        return reserveCount(usage_.evictions, count, config_.maxEvictions);
    }

    [[nodiscard]] const FrameBudgetConfig& config() const noexcept { return config_; }
    [[nodiscard]] const FrameBudgetUsage& usage() const noexcept { return usage_; }

private:
    [[nodiscard]] static FrameBudgetConfig sanitize(FrameBudgetConfig config) noexcept {
        config.targetFrameMilliseconds = std::max(config.targetFrameMilliseconds, 0.1);
        config.mainThreadStreamingMilliseconds = std::clamp(
            config.mainThreadStreamingMilliseconds, 0.0, config.targetFrameMilliseconds);
        config.maxGenerationDispatches = std::max(1U, config.maxGenerationDispatches);
        config.maxMeshingDispatches = std::max(1U, config.maxMeshingDispatches);
        config.maxUploadCommits = std::max(1U, config.maxUploadCommits);
        config.maxEvictions = std::max(1U, config.maxEvictions);
        config.maxUploadBytes = std::max<std::size_t>(64U * 1024U, config.maxUploadBytes);
        return config;
    }

    [[nodiscard]] static bool reserveCount(
        std::uint32_t& used,
        std::uint32_t requested,
        std::uint32_t limit) noexcept {
        if (requested > limit - std::min(used, limit)) return false;
        used += requested;
        return true;
    }

    FrameBudgetConfig config_{};
    FrameBudgetUsage usage_{};
};

} // namespace vf::core
