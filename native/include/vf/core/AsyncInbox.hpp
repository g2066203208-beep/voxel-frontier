#pragma once

#include <algorithm>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <span>
#include <utility>

#include <concurrentqueue.h>

namespace vf::core {

// R24_ENGINE_FOUNDATION_V2
// Background workers never mutate authoritative ECS/world/render state directly. They publish
// immutable result packets into this preallocated MPMC inbox. The owning coordinator drains it at
// an explicit safe point. Capacity is hard-bounded so a runaway producer cannot grow memory forever.
template <class T>
class AsyncInbox final {
public:
    class Producer final {
    public:
        explicit Producer(AsyncInbox& inbox)
            : inbox_(&inbox), token_(inbox.queue_) {}

        Producer(const Producer&) = delete;
        Producer& operator=(const Producer&) = delete;

        [[nodiscard]] bool tryPush(const T& value) {
            return inbox_->tryPushWithToken(token_, value);
        }
        [[nodiscard]] bool tryPush(T&& value) {
            return inbox_->tryPushWithToken(token_, std::move(value));
        }

    private:
        AsyncInbox* inbox_{};
        moodycamel::ProducerToken token_;
    };

    explicit AsyncInbox(std::size_t capacity, std::size_t expectedProducers = 8U)
        : capacity_(std::max<std::size_t>(1U, capacity)),
          expectedProducers_(std::max<std::size_t>(1U, expectedProducers)),
          // This overload computes the extra block reserve needed for explicit producers.
          queue_(capacity_, expectedProducers_, 0U) {}

    AsyncInbox(const AsyncInbox&) = delete;
    AsyncInbox& operator=(const AsyncInbox&) = delete;

    // Convenience path for rare producers. Worker threads should create one long-lived Producer
    // during thread/job-context setup so their producer metadata is initialized outside hot frames.
    [[nodiscard]] bool tryPush(const T& value) {
        if (!reserveSlot()) return false;
        if (!queue_.try_enqueue(value)) return rollbackAllocationPressure();
        pushed_.fetch_add(1U, std::memory_order_relaxed);
        return true;
    }
    [[nodiscard]] bool tryPush(T&& value) {
        if (!reserveSlot()) return false;
        if (!queue_.try_enqueue(std::move(value))) return rollbackAllocationPressure();
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
        const std::size_t count = queue_.try_dequeue_bulk(output.begin(), output.size());
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
    [[nodiscard]] std::size_t expectedProducers() const noexcept { return expectedProducers_; }
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
    template <class U>
    [[nodiscard]] bool tryPushWithToken(moodycamel::ProducerToken& token, U&& value) {
        if (!reserveSlot()) return false;
        if (!queue_.try_enqueue(token, std::forward<U>(value))) return rollbackAllocationPressure();
        pushed_.fetch_add(1U, std::memory_order_relaxed);
        return true;
    }

    [[nodiscard]] bool rollbackAllocationPressure() noexcept {
        size_.fetch_sub(1U, std::memory_order_release);
        allocationPressureDrops_.fetch_add(1U, std::memory_order_relaxed);
        return false;
    }

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
    const std::size_t expectedProducers_;
    moodycamel::ConcurrentQueue<T> queue_;
    alignas(64) std::atomic<std::size_t> size_{};
    alignas(64) std::atomic<std::uint64_t> pushed_{};
    alignas(64) std::atomic<std::uint64_t> popped_{};
    alignas(64) std::atomic<std::uint64_t> capacityDrops_{};
    alignas(64) std::atomic<std::uint64_t> allocationPressureDrops_{};
};

} // namespace vf::core
