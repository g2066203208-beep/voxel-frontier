#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <type_traits>

namespace vf::core {

// R24_ENGINE_FOUNDATION_V2
// Single-producer / single-consumer fixed ring for compact immutable frame snapshots.
// Producer never blocks on renderer lag: if all slots are still owned by the consumer it drops a
// snapshot instead of stalling simulation. T should contain compact values/handles, never giant meshes.
template <class T, std::size_t SlotCount = 3U>
class FrameSnapshotExchange final {
    static_assert(SlotCount >= 2U);
    static_assert(std::is_copy_assignable_v<T>);

public:
    [[nodiscard]] bool tryPublish(const T& snapshot) noexcept(std::is_nothrow_copy_assignable_v<T>) {
        const std::uint64_t produced = produced_.load(std::memory_order_relaxed);
        const std::uint64_t consumed = consumed_.load(std::memory_order_acquire);
        if (produced - consumed >= SlotCount) {
            dropped_.fetch_add(1U, std::memory_order_relaxed);
            return false;
        }
        slots_[produced % SlotCount] = snapshot;
        produced_.store(produced + 1U, std::memory_order_release);
        return true;
    }

    // Consumes only the newest available snapshot. Older unpublished-to-render frames are skipped;
    // render latency therefore stays bounded even when simulation temporarily outruns rendering.
    [[nodiscard]] bool tryConsumeLatest(T& destination) noexcept(std::is_nothrow_copy_assignable_v<T>) {
        const std::uint64_t produced = produced_.load(std::memory_order_acquire);
        const std::uint64_t consumed = consumed_.load(std::memory_order_relaxed);
        if (produced == consumed) return false;
        const std::uint64_t newestSequence = produced - 1U;
        destination = slots_[newestSequence % SlotCount];
        consumed_.store(produced, std::memory_order_release);
        return true;
    }

    [[nodiscard]] std::uint64_t producedCount() const noexcept {
        return produced_.load(std::memory_order_acquire);
    }
    [[nodiscard]] std::uint64_t consumedCount() const noexcept {
        return consumed_.load(std::memory_order_acquire);
    }
    [[nodiscard]] std::uint64_t droppedCount() const noexcept {
        return dropped_.load(std::memory_order_relaxed);
    }
    [[nodiscard]] std::size_t approximateBacklog() const noexcept {
        const auto produced = produced_.load(std::memory_order_acquire);
        const auto consumed = consumed_.load(std::memory_order_acquire);
        return static_cast<std::size_t>(produced - consumed);
    }

private:
    std::array<T, SlotCount> slots_{};
    alignas(64) std::atomic<std::uint64_t> produced_{};
    alignas(64) std::atomic<std::uint64_t> consumed_{};
    alignas(64) std::atomic<std::uint64_t> dropped_{};
};

} // namespace vf::core
