#pragma once

#include <cstdint>

namespace vf {

struct StaticMeshUploadDecision {
    std::uint32_t slot{};
    bool upload{};
};

// Two immutable DEVICE_LOCAL slots are enough for a single graphics queue with two frames in
// flight. A new generation alternates to the other slot; all subsequent frames share the resident
// slot read-only. The renderer waits the current frame fence before asking for a decision, so the
// alternate slot is never overwritten while that same frame still references it. Queue submission
// order then guarantees the one transfer for a generation precedes every later draw using it.
class StaticMeshUploadScheduler final {
public:
    [[nodiscard]] StaticMeshUploadDecision adopt(std::uint64_t generation) noexcept {
        if (initialized_ && generation == residentGeneration_)
            return {residentSlot_, false};

        residentSlot_ = initialized_ ? (residentSlot_ ^ 1U) : 0U;
        residentGeneration_ = generation;
        initialized_ = true;
        ++uploadCount_;
        return {residentSlot_, true};
    }

    void reset() noexcept {
        initialized_ = false;
        residentGeneration_ = 0U;
        residentSlot_ = 0U;
        uploadCount_ = 0U;
    }

    [[nodiscard]] bool initialized() const noexcept { return initialized_; }
    [[nodiscard]] std::uint32_t residentSlot() const noexcept { return residentSlot_; }
    [[nodiscard]] std::uint64_t residentGeneration() const noexcept { return residentGeneration_; }
    [[nodiscard]] std::uint64_t uploadCount() const noexcept { return uploadCount_; }

private:
    bool initialized_{};
    std::uint32_t residentSlot_{};
    std::uint64_t residentGeneration_{};
    std::uint64_t uploadCount_{};
};

} // namespace vf
