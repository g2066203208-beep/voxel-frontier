#pragma once

#include <array>
#include <cstddef>
#include <memory_resource>
#include <span>

namespace vf::core {

// R24_ENGINE_FOUNDATION_V2
// Per-frame transient allocations are carved from a fixed linear arena and released together.
// This prevents thousands of tiny command/visibility/streaming packets from churning the system heap.
template <std::size_t CapacityBytes = 2U * 1024U * 1024U>
class FrameArena final {
public:
    FrameArena()
        : resource_(storage_.data(), storage_.size(), std::pmr::null_memory_resource()) {}

    FrameArena(const FrameArena&) = delete;
    FrameArena& operator=(const FrameArena&) = delete;

    void reset() noexcept { resource_.release(); }

    [[nodiscard]] std::pmr::memory_resource* resource() noexcept { return &resource_; }
    [[nodiscard]] constexpr std::size_t capacityBytes() const noexcept { return CapacityBytes; }

    template <class T>
    [[nodiscard]] std::pmr::polymorphic_allocator<T> allocator() noexcept {
        return std::pmr::polymorphic_allocator<T>{&resource_};
    }

private:
    alignas(std::max_align_t) std::array<std::byte, CapacityBytes> storage_{};
    std::pmr::monotonic_buffer_resource resource_;
};

} // namespace vf::core
