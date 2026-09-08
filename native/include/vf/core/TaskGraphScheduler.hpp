#pragma once

#include <array>
#include <atomic>
#include <cstdint>
#include <functional>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

#include <taskflow/taskflow.hpp>

namespace vf::core {

enum class EnginePhase : std::uint8_t {
    Input,
    SimulationPrepare,
    SimulationFixed,
    SimulationPost,
    WorldStreaming,
    Visibility,
    RenderExtract,
    RenderPrepare,
    Housekeeping,
    Count
};

struct FrameExecutionContext {
    std::uint64_t frameIndex{};
    double wallDeltaSeconds{};
    double fixedDeltaSeconds{1.0 / 120.0};
    std::uint32_t simulationStepIndex{};
    std::uint32_t simulationStepCount{};
    double interpolationAlpha{};
};

struct SchedulerConfig {
    // On a six-core minimum target this should normally be five workers, leaving one core for the
    // platform/render submission thread. Zero selects hardware_concurrency()-1 automatically.
    std::uint32_t workerCount{};
};

// R24_ENGINE_FOUNDATION_V1
// Coarse engine systems are expressed once as a reusable dependency graph. Taskflow then executes
// each phase with work stealing while hard phase barriers preserve deterministic ownership rules.
class TaskGraphScheduler final {
public:
    using TaskFunction = std::function<void(FrameExecutionContext&)>;

    explicit TaskGraphScheduler(SchedulerConfig config = {})
        : workerCount_(resolveWorkerCount(config.workerCount)), executor_(workerCount_) {
        for (std::size_t i = 0; i < phaseBegin_.size(); ++i) {
            phaseBegin_[i] = graph_.emplace([] {}).name("phase.begin");
            phaseEnd_[i] = graph_.emplace([] {}).name("phase.end");
        }
    }

    TaskGraphScheduler(const TaskGraphScheduler&) = delete;
    TaskGraphScheduler& operator=(const TaskGraphScheduler&) = delete;

    void addTask(EnginePhase phase, std::string name, TaskFunction function) {
        if (sealed_) throw std::logic_error("TaskGraphScheduler is already sealed");
        if (!function) throw std::invalid_argument("TaskGraphScheduler task must be callable");
        const auto phaseIndex = static_cast<std::size_t>(phase);
        if (phaseIndex >= static_cast<std::size_t>(EnginePhase::Count))
            throw std::out_of_range("TaskGraphScheduler phase out of range");

        tf::Task task = graph_.emplace([this, fn = std::move(function)] {
            FrameExecutionContext* context = activeContext_.load(std::memory_order_acquire);
            if (context == nullptr) throw std::logic_error("TaskGraphScheduler executed without frame context");
            fn(*context);
        }).name(name);
        tasks_[phaseIndex].push_back(task);
    }

    void seal() {
        if (sealed_) return;
        constexpr std::size_t phaseCount = static_cast<std::size_t>(EnginePhase::Count);
        for (std::size_t i = 0; i < phaseCount; ++i) {
            if (tasks_[i].empty()) {
                phaseBegin_[i].precede(phaseEnd_[i]);
            } else {
                for (auto& task : tasks_[i]) {
                    phaseBegin_[i].precede(task);
                    task.precede(phaseEnd_[i]);
                }
            }
            if (i + 1U < phaseCount) phaseEnd_[i].precede(phaseBegin_[i + 1U]);
        }
        sealed_ = true;
    }

    void execute(FrameExecutionContext& context) {
        if (!sealed_) seal();
        FrameExecutionContext* expected = nullptr;
        if (!activeContext_.compare_exchange_strong(
                expected, &context, std::memory_order_acq_rel, std::memory_order_acquire)) {
            throw std::logic_error("TaskGraphScheduler does not permit overlapping frame execution");
        }
        try {
            executor_.run(graph_).get();
        } catch (...) {
            activeContext_.store(nullptr, std::memory_order_release);
            throw;
        }
        activeContext_.store(nullptr, std::memory_order_release);
    }

    [[nodiscard]] std::uint32_t workerCount() const noexcept { return workerCount_; }
    [[nodiscard]] bool sealed() const noexcept { return sealed_; }

private:
    [[nodiscard]] static std::uint32_t resolveWorkerCount(std::uint32_t requested) noexcept {
        if (requested > 0U) return requested;
        const std::uint32_t hardware = std::max(1U, std::thread::hardware_concurrency());
        return hardware > 1U ? hardware - 1U : 1U;
    }

    std::uint32_t workerCount_{1U};
    tf::Executor executor_;
    tf::Taskflow graph_;
    std::array<tf::Task, static_cast<std::size_t>(EnginePhase::Count)> phaseBegin_{};
    std::array<tf::Task, static_cast<std::size_t>(EnginePhase::Count)> phaseEnd_{};
    std::array<std::vector<tf::Task>, static_cast<std::size_t>(EnginePhase::Count)> tasks_{};
    std::atomic<FrameExecutionContext*> activeContext_{nullptr};
    bool sealed_{};
};

} // namespace vf::core
