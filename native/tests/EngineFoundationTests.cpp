#include "vf/core/FrameBudget.hpp"
#include "vf/core/FrameClock.hpp"
#include "vf/core/TaskGraphScheduler.hpp"
#include "vf/world/WorldPartition.hpp"

#include <algorithm>
#include <atomic>
#include <cassert>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <vector>

namespace {

void testFixedStepClock() {
    vf::core::FixedStepClock clock{{120.0, 0.050, 8U}};
    auto a = clock.advance(1.0 / 240.0);
    assert(a.simulationSteps == 0U);
    auto b = clock.advance(1.0 / 240.0);
    assert(b.simulationSteps == 1U);
    assert(b.interpolationAlpha < 1.0e-9);

    auto c = clock.advance(1.0 / 60.0);
    assert(c.simulationSteps == 2U);

    auto d = clock.advance(0.5);
    // Wall time is clamped to 50 ms, so a stall cannot create an unbounded catch-up spiral.
    assert(d.acceptedFrameSeconds <= 0.0500001);
    assert(d.simulationSteps <= 8U);
}

void testFrameBudget() {
    vf::core::FrameBudget budget{{1000.0 / 120.0, 0.35, 4U, 3U, 2U, 2U, 1024U}};
    budget.beginFrame();
    assert(budget.reserveGeneration());
    assert(budget.reserveGeneration(3U));
    assert(!budget.reserveGeneration());
    assert(budget.reserveMeshing(3U));
    assert(!budget.reserveMeshing());
    assert(budget.reserveUpload(512U));
    assert(budget.reserveUpload(512U));
    assert(!budget.reserveUpload(1U));
    assert(budget.reserveEviction(2U));
    assert(!budget.reserveEviction());
}

void testTaskGraphPhases() {
    vf::core::TaskGraphScheduler scheduler{{4U}};
    std::atomic<int> phase{0};
    std::atomic<int> parallelCount{0};
    std::atomic<bool> failed{false};

    scheduler.addTask(vf::core::EnginePhase::Input, "input", [&](auto&) {
        if (phase.load(std::memory_order_acquire) != 0) failed.store(true);
        phase.store(1, std::memory_order_release);
    });
    for (int i = 0; i < 32; ++i) {
        scheduler.addTask(vf::core::EnginePhase::SimulationFixed, "sim", [&](auto&) {
            if (phase.load(std::memory_order_acquire) != 1) failed.store(true);
            parallelCount.fetch_add(1, std::memory_order_relaxed);
        });
    }
    scheduler.addTask(vf::core::EnginePhase::SimulationPost, "sim-post", [&](auto&) {
        if (parallelCount.load(std::memory_order_acquire) != 32) failed.store(true);
        phase.store(2, std::memory_order_release);
    });
    scheduler.addTask(vf::core::EnginePhase::WorldStreaming, "stream", [&](auto&) {
        if (phase.load(std::memory_order_acquire) != 2) failed.store(true);
        phase.store(3, std::memory_order_release);
    });
    scheduler.addTask(vf::core::EnginePhase::RenderExtract, "extract", [&](auto&) {
        if (phase.load(std::memory_order_acquire) != 3) failed.store(true);
        phase.store(4, std::memory_order_release);
    });
    scheduler.addTask(vf::core::EnginePhase::Housekeeping, "housekeeping", [&](auto&) {
        if (phase.load(std::memory_order_acquire) != 4) failed.store(true);
        phase.store(5, std::memory_order_release);
    });
    scheduler.seal();

    vf::core::FrameExecutionContext context{};
    for (std::uint64_t frame = 0; frame < 100U; ++frame) {
        phase.store(0, std::memory_order_release);
        parallelCount.store(0, std::memory_order_release);
        context.frameIndex = frame;
        scheduler.execute(context);
        assert(!failed.load());
        assert(phase.load() == 5);
    }
    assert(scheduler.workerCount() == 4U);
}

void testWorldPartitionStress() {
    using namespace vf::world;
    WorldPartition partition;
    constexpr std::size_t cellCount = 100000U;

    const auto begin = std::chrono::steady_clock::now();
    for (std::size_t i = 0; i < cellCount; ++i) {
        WorldCellKey key{};
        key.worldId = 1U;
        key.x = static_cast<std::int32_t>(i % 1000U);
        key.y = static_cast<std::int32_t>((i / 1000U) % 100U);
        key.z = static_cast<std::int32_t>(i / 100000U);
        key.lod = static_cast<std::uint8_t>(i % 6U);
        const float priority = static_cast<float>((i * 7919U) % 100000U);
        (void)partition.requestCell(key, priority, 64U * 1024U, 1U);
    }
    const auto requestDone = std::chrono::steady_clock::now();
    assert(partition.cellCount() == cellCount);

    auto generation = partition.drainRequested({128U, 128U * 64U * 1024U});
    assert(generation.size() == 128U);
    for (std::size_t i = 1; i < generation.size(); ++i)
        assert(generation[i - 1U].priority >= generation[i].priority);

    for (std::size_t i = 0; i < 64U; ++i)
        assert(partition.completeGeneration(generation[i].entity, generation[i].revision, 48U * 1024U));
    auto meshing = partition.drainMeshing({64U, 64U * 48U * 1024U});
    assert(meshing.size() == 64U);
    for (const auto& item : meshing)
        assert(partition.completeMeshing(item.entity, item.revision, 96U * 1024U));

    // Upload bytes are a hard budget: 512 KiB permits only five 96 KiB chunks.
    auto uploads = partition.drainUploads({64U, 512U * 1024U});
    assert(!uploads.empty());
    assert(uploads.size() <= 5U);
    std::size_t uploadBytes = 0U;
    for (const auto& item : uploads) {
        uploadBytes += item.estimatedBytes;
        assert(partition.completeUpload(item.entity, item.revision, 48U * 1024U, item.estimatedBytes));
    }
    assert(uploadBytes <= 512U * 1024U);
    assert(partition.residentCount() == uploads.size());

    // Revision invalidation: a stale worker must not be able to commit after the cell is re-requested.
    WorldCellKey staleKey{7U, 1, 2, 3, 0U};
    const auto staleEntity = partition.requestCell(staleKey, 10.0F, 1024U, 5U);
    auto staleBatch = partition.drainRequested({1U, 4096U});
    assert(staleBatch.size() == 1U);
    const auto staleRevision = staleBatch.front().revision;
    (void)partition.requestCell(staleKey, 100.0F, 2048U, 6U);
    assert(!partition.completeGeneration(staleEntity, staleRevision, 2048U));

    const auto end = std::chrono::steady_clock::now();
    const double requestMs = std::chrono::duration<double, std::milli>(requestDone - begin).count();
    const double totalMs = std::chrono::duration<double, std::milli>(end - begin).count();
    std::cout << "R24 FOUNDATION STRESS cells=" << cellCount
              << " request_ms=" << requestMs
              << " total_ms=" << totalMs
              << " generation_batch=" << generation.size()
              << " mesh_batch=" << meshing.size()
              << " upload_batch=" << uploads.size()
              << " resident=" << partition.residentCount() << '\n';
}

} // namespace

int main() {
    testFixedStepClock();
    testFrameBudget();
    testTaskGraphPhases();
    testWorldPartitionStress();
    std::cout << "R24 ENGINE FOUNDATION PASS\n";
    return 0;
}
