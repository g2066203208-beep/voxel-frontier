#include "vf/core/FrameBudget.hpp"
#include "vf/core/FrameClock.hpp"
#include "vf/core/TaskGraphScheduler.hpp"
#include "vf/world/WorldPartition.hpp"

#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <stdexcept>

namespace {

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

void testFixedStepClock() {
    vf::core::FixedStepClock clock{{120.0, 0.050, 8U}};
    const auto a = clock.advance(1.0 / 240.0);
    require(a.simulationSteps == 0U, "240 Hz half-step should not advance simulation");
    const auto b = clock.advance(1.0 / 240.0);
    require(b.simulationSteps == 1U, "two 240 Hz frames should produce one 120 Hz step");
    require(b.interpolationAlpha < 1.0e-9, "fixed-step interpolation remainder should close");

    const auto c = clock.advance(1.0 / 60.0);
    require(c.simulationSteps == 2U, "60 Hz wall frame should produce two 120 Hz simulation steps");

    const auto d = clock.advance(0.5);
    require(d.acceptedFrameSeconds <= 0.0500001, "wall-time clamp failed");
    require(d.simulationSteps <= 8U, "simulation catch-up bound failed");
}

void testFrameBudget() {
    vf::core::FrameBudget budget{{
        1000.0 / 120.0,
        0.35,
        4U,
        3U,
        2U,
        2U,
        1024U * 1024U}};
    budget.beginFrame();
    require(budget.reserveGeneration(), "generation reservation 1 failed");
    require(budget.reserveGeneration(3U), "generation reservation to budget failed");
    require(!budget.reserveGeneration(), "generation budget allowed overflow");
    require(budget.reserveMeshing(3U), "meshing reservation to budget failed");
    require(!budget.reserveMeshing(), "meshing budget allowed overflow");
    require(budget.reserveUpload(512U * 1024U), "first upload reservation failed");
    require(budget.reserveUpload(512U * 1024U), "second upload reservation failed");
    require(!budget.reserveUpload(1U), "upload budget allowed overflow");
    require(budget.reserveEviction(2U), "eviction reservation to budget failed");
    require(!budget.reserveEviction(), "eviction budget allowed overflow");
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
        require(!failed.load(), "task graph phase barrier violated");
        require(phase.load() == 5, "task graph did not reach housekeeping");
    }
    require(scheduler.workerCount() == 4U, "scheduler worker count mismatch");
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
        key.z = 0;
        key.lod = static_cast<std::uint8_t>(i % 6U);
        const float priority = static_cast<float>((i * 7919U) % 100000U);
        (void)partition.requestCell(key, priority, 64U * 1024U, 1U);
    }
    const auto requestDone = std::chrono::steady_clock::now();
    require(partition.cellCount() == cellCount, "world partition lost or merged requested cells");

    auto generation = partition.drainRequested({128U, 128U * 64U * 1024U});
    require(generation.size() == 128U, "generation drain ignored item budget");
    for (std::size_t i = 1; i < generation.size(); ++i)
        require(generation[i - 1U].priority >= generation[i].priority, "generation priority order broken");

    for (std::size_t i = 0; i < 64U; ++i)
        require(
            partition.completeGeneration(generation[i].entity, generation[i].revision, 48U * 1024U),
            "generation completion rejected valid worker result");

    auto meshing = partition.drainMeshing({64U, 64U * 48U * 1024U});
    require(meshing.size() == 64U, "meshing queue failed to receive generated cells");
    for (const auto& item : meshing)
        require(
            partition.completeMeshing(item.entity, item.revision, 96U * 1024U),
            "meshing completion rejected valid worker result");

    // Upload bytes are a hard budget: 512 KiB permits only five 96 KiB chunks.
    auto uploads = partition.drainUploads({64U, 512U * 1024U});
    require(!uploads.empty(), "upload queue received no meshed cells");
    require(uploads.size() == 5U, "upload byte budget did not stop at five 96 KiB chunks");
    std::size_t uploadBytes = 0U;
    for (const auto& item : uploads) {
        uploadBytes += item.estimatedBytes;
        require(
            partition.completeUpload(item.entity, item.revision, 48U * 1024U, item.estimatedBytes),
            "upload completion rejected valid worker result");
    }
    require(uploadBytes <= 512U * 1024U, "upload drain exceeded byte budget");
    require(partition.residentCount() == uploads.size(), "resident accounting mismatch");

    // Revision invalidation is tested in isolation so backlog priority cannot select another cell.
    WorldPartition stalePartition;
    const WorldCellKey staleKey{7U, 1, 2, 3, 0U};
    const auto staleEntity = stalePartition.requestCell(staleKey, 10.0F, 1024U, 5U);
    auto staleBatch = stalePartition.drainRequested({1U, 4096U});
    require(staleBatch.size() == 1U, "isolated stale test did not dispatch cell");
    const auto staleRevision = staleBatch.front().revision;
    (void)stalePartition.requestCell(staleKey, 100.0F, 2048U, 6U);
    require(
        !stalePartition.completeGeneration(staleEntity, staleRevision, 2048U),
        "stale worker result was incorrectly accepted");

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
    try {
        testFixedStepClock();
        testFrameBudget();
        testTaskGraphPhases();
        testWorldPartitionStress();
        std::cout << "R24 ENGINE FOUNDATION PASS\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "R24 ENGINE FOUNDATION FAIL: " << error.what() << '\n';
        return 1;
    }
}
