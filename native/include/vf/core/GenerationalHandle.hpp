#pragma once

#include <cstdint>
#include <limits>
#include <type_traits>

namespace vf::core {

// R24_ENGINE_FOUNDATION_V2
// Stable opaque IDs cross subsystem/thread boundaries. Raw pointers to world/GPU resources do not.
template <class Tag>
struct GenerationalHandle {
    std::uint32_t index{std::numeric_limits<std::uint32_t>::max()};
    std::uint32_t generation{};

    [[nodiscard]] constexpr bool valid() const noexcept {
        return index != std::numeric_limits<std::uint32_t>::max() && generation != 0U;
    }

    [[nodiscard]] friend constexpr bool operator==(
        const GenerationalHandle&,
        const GenerationalHandle&) noexcept = default;
};

static_assert(std::is_trivially_copyable_v<GenerationalHandle<struct HandleCompileCheckTag>>);

} // namespace vf::core
