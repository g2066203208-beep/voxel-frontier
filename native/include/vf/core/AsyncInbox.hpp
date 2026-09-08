#pragma once

#include <algorithm>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

#include <concurrentqueue.h>

namespace vf::core {

// R24_ENGINE_FOUNDATION_V2
// Background workers never mutate authoritative ECS/world/render state directly. They publish
// immutable result packets into this preallocated MPMC inbox. The owning coordinator drains it at
// an explicit safe point. Capacity is hard-bounded so a runaway producer cannot grow memory forever.
template <class T>
class AsyncInbox final {
public:
    explicit AsyncInbox(std::size_t capacity)
        : capacity_(std::max<std::size_t>(1U, capacity)), queue_(capacity_) {}

    AsyncInbox(const AsyncInbox&) = delete;
    AsyncInbox& operator=(const AsyncInbox&) = delete;

    [[nodiscard]] bool tryPush(const T& value) {
        if (!reserveSlot()) return false;
        if (!queue_.try_enqueue(value)) {
            size_.fetch_sub(1U, std::memory_order_release);
            allocationPressureDrops_.fetch_add(1U, std::memory_order_relaxed);
            return false;
        }
        pushed_.fetch_add(1U, std::memory_order_relaxed);
        return true;
    }

    [[nodiscard]] bool tryPush(T&& value) {
        if (!reserveSlot()) return false;
        if (!queue_.try_enqueue(std::move(value))) {
            size_.fetch_sub(1U, std::memory_order_release);
            allocationPressureDrops_.fetch_add(1U, std::memory_order_relaxed);
            return false;
        }
        pushed_.fetch_add(1U, std::memory_order_relaxed);
        return true;
    }

    [[nodiscard]] bool tryPop(T& value) {
        if (!queue_.try_dequeue(value)) return false;
        size_.fetch_sub(1U, std::memory_order_release);
        popped_.fetch_add(1U, std::memory_order_relaxed);
        return true;
    }

    [[nodiscard]] std::size_t drain(std::span<T> output) {
        std::size_t count = 0U;
        while (count < output.size() && queue_.try_dequeue(output[count])) ++count;
        if (count != 0U) {
            size_.fetch_sub(count, std::memory_order_release);
            popped_.fetch_add(count, std::memory_order_relaxed);
        }
        return count;
    }

    [[nodiscard]] std::size_t size() const noexcept {
        return size_.load(std::memory_order_acquire);
    }
    [[nodiscard]] std::size_t capacity() const noexcept { return capacity_; }
    [[nodiscard]] std::uint64_t pushedCount() const noexcept {
        return pushed_.load(std::memory_order_relaxed);
    }
    [[nodiscard]] std::uint64_t poppedCount() const noexcept {
        return popped_.load(std::memory_order_relaxed);
    }
    [[nodiscard]] std::uint64_t capacityDrops() const noexcept {
        return capacityDrops_.load(std::memory_order_relaxed);
    }
    [[nodiscard]] std::uint64_t allocationPressureDrops() const noexcept {
        return allocationPressureDrops_.load(std::memory_order_relaxed);
    }

private:
    [[nodiscard]] bool reserveSlot() noexcept {
        std::size_t observed = size_.load(std::memory_order_relaxed);
        for (;;) {
            if (observed >= capacity_) {
                capacityDrops_.fetch_add(1U, std::memory_order_relaxed);
                return false;
            }
            if (size_.compare_exchange_weak(
                    observed,
                    observed + 1U,
                    std::memory_order_acq_rel,
                    std::memory_order_relaxed)) {
                return true;
            }
        }
    }

    const std::size_t capacity_;
    moodycamel::ConcurrentQueue<T> queue_;
    alignas(64) std::atomic<std::size_t> size_{};
    alignas(64) std::atomic<std::uint64_t> pushed_{};
    alignas(64) std::atomic<std::uint64_t> popped_{};
    alignas(64) std::atomic<std::uint64_t> capacityDrops_{};
    alignas(64) std::atomic<std::uint64_t> allocationPressureDrops_{};
};

} // namespace vf::core
