#pragma once

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <queue>
#include <unordered_map>
#include <utility>
#include <vector>

#include <entt/entity/registry.hpp>

namespace vf::world {

struct WorldCellKey {
    std::uint32_t worldId{};
    std::int32_t x{};
    std::int32_t y{};
    std::int32_t z{};
    std::uint8_t lod{};

    [[nodiscard]] friend bool operator==(const WorldCellKey&, const WorldCellKey&) = default;
};

struct WorldCellKeyHash {
    [[nodiscard]] std::size_t operator()(const WorldCellKey& key) const noexcept {
        std::uint64_t h = 1469598103934665603ULL;
        const auto mix = [&h](std::uint64_t value) noexcept {
            h ^= value;
            h *= 1099511628211ULL;
        };
        mix(key.worldId);
        mix(static_cast<std::uint32_t>(key.x));
        mix(static_cast<std::uint32_t>(key.y));
        mix(static_cast<std::uint32_t>(key.z));
        mix(key.lod);
        return static_cast<std::size_t>(h);
    }
};

enum class StreamingStage : std::uint8_t {
    Unloaded,
    Requested,
    Generating,
    MeshingQueued,
    Meshing,
    UploadQueued,
    Uploading,
    Resident,
    EvictionQueued,
    Evicting,
    Failed
};

struct WorldCellAddress {
    WorldCellKey key{};
};

struct WorldCellStreaming {
    StreamingStage stage{StreamingStage::Unloaded};
    std::uint64_t revision{1U};
    std::uint64_t lastTouchedFrame{};
    float priority{};
    std::size_t estimatedBytes{};
    std::size_t residentCpuBytes{};
    std::size_t residentGpuBytes{};
};

struct StreamingWorkItem {
    entt::entity entity{entt::null};
    WorldCellKey key{};
    StreamingStage stage{StreamingStage::Unloaded};
    std::uint64_t revision{};
    float priority{};
    std::size_t estimatedBytes{};
};

struct StreamingDrainBudget {
    std::uint32_t maxItems{1U};
    std::size_t maxBytes{std::numeric_limits<std::size_t>::max()};
};

// R24_ENGINE_FOUNDATION_V1
// World streaming is a bounded, revisioned pipeline. Request spikes may grow the queues, but they
// never turn into an unbounded amount of work in one frame. Stale worker results are rejected by
// revision instead of mutating a chunk that has already been reprioritized/replaced.
class WorldPartition final {
public:
    [[nodiscard]] entt::entity requestCell(
        const WorldCellKey& key,
        float priority,
        std::size_t estimatedBytes,
        std::uint64_t frameIndex) {
        auto found = lookup_.find(key);
        if (found == lookup_.end()) {
            const entt::entity entity = registry_.create();
            registry_.emplace<WorldCellAddress>(entity, key);
            registry_.emplace<WorldCellStreaming>(
                entity,
                StreamingStage::Requested,
                1U,
                frameIndex,
                priority,
                estimatedBytes,
                0U,
                0U);
            lookup_.emplace(key, entity);
            enqueue(entity, StreamingStage::Requested);
            return entity;
        }

        const entt::entity entity = found->second;
        auto& streaming = registry_.get<WorldCellStreaming>(entity);
        streaming.lastTouchedFrame = frameIndex;
        streaming.priority = priority;
        streaming.estimatedBytes = estimatedBytes;

        if (streaming.stage == StreamingStage::Resident) return entity;

        // Re-requesting non-resident work invalidates stale worker output and moves the cell back to
        // the front of the request pipeline. Priority updates therefore never require in-place heap edits.
        ++streaming.revision;
        streaming.stage = StreamingStage::Requested;
        enqueue(entity, StreamingStage::Requested);
        return entity;
    }

    [[nodiscard]] std::vector<StreamingWorkItem> drainRequested(StreamingDrainBudget budget) {
        return drainQueue(requestQueue_, StreamingStage::Requested, StreamingStage::Generating, budget);
    }

    [[nodiscard]] std::vector<StreamingWorkItem> drainMeshing(StreamingDrainBudget budget) {
        return drainQueue(meshQueue_, StreamingStage::MeshingQueued, StreamingStage::Meshing, budget);
    }

    [[nodiscard]] std::vector<StreamingWorkItem> drainUploads(StreamingDrainBudget budget) {
        return drainQueue(uploadQueue_, StreamingStage::UploadQueued, StreamingStage::Uploading, budget);
    }

    [[nodiscard]] std::vector<StreamingWorkItem> drainEvictions(StreamingDrainBudget budget) {
        return drainQueue(evictionQueue_, StreamingStage::EvictionQueued, StreamingStage::Evicting, budget);
    }

    [[nodiscard]] bool completeGeneration(
        entt::entity entity,
        std::uint64_t revision,
        std::size_t generatedBytes) {
        auto* streaming = tryStreaming(entity);
        if (!streaming || streaming->revision != revision || streaming->stage != StreamingStage::Generating)
            return false;
        streaming->estimatedBytes = generatedBytes;
        streaming->stage = StreamingStage::MeshingQueued;
        enqueue(entity, StreamingStage::MeshingQueued);
        return true;
    }

    [[nodiscard]] bool completeMeshing(
        entt::entity entity,
        std::uint64_t revision,
        std::size_t meshBytes) {
        auto* streaming = tryStreaming(entity);
        if (!streaming || streaming->revision != revision || streaming->stage != StreamingStage::Meshing)
            return false;
        streaming->estimatedBytes = meshBytes;
        streaming->stage = StreamingStage::UploadQueued;
        enqueue(entity, StreamingStage::UploadQueued);
        return true;
    }

    [[nodiscard]] bool completeUpload(
        entt::entity entity,
        std::uint64_t revision,
        std::size_t cpuBytes,
        std::size_t gpuBytes) {
        auto* streaming = tryStreaming(entity);
        if (!streaming || streaming->revision != revision || streaming->stage != StreamingStage::Uploading)
            return false;
        streaming->residentCpuBytes = cpuBytes;
        streaming->residentGpuBytes = gpuBytes;
        streaming->estimatedBytes = 0U;
        streaming->stage = StreamingStage::Resident;
        return true;
    }

    [[nodiscard]] bool queueEviction(entt::entity entity, float priority = 0.0F) {
        auto* streaming = tryStreaming(entity);
        if (!streaming || streaming->stage != StreamingStage::Resident) return false;
        ++streaming->revision;
        streaming->priority = priority;
        streaming->estimatedBytes = streaming->residentCpuBytes + streaming->residentGpuBytes;
        streaming->stage = StreamingStage::EvictionQueued;
        enqueue(entity, StreamingStage::EvictionQueued);
        return true;
    }

    [[nodiscard]] bool completeEviction(entt::entity entity, std::uint64_t revision) {
        auto* streaming = tryStreaming(entity);
        if (!streaming || streaming->revision != revision || streaming->stage != StreamingStage::Evicting)
            return false;
        streaming->residentCpuBytes = 0U;
        streaming->residentGpuBytes = 0U;
        streaming->estimatedBytes = 0U;
        streaming->stage = StreamingStage::Unloaded;
        return true;
    }

    [[nodiscard]] std::optional<WorldCellStreaming> state(const WorldCellKey& key) const {
        const auto found = lookup_.find(key);
        if (found == lookup_.end()) return std::nullopt;
        if (!registry_.valid(found->second) || !registry_.all_of<WorldCellStreaming>(found->second))
            return std::nullopt;
        return registry_.get<WorldCellStreaming>(found->second);
    }

    [[nodiscard]] std::size_t cellCount() const noexcept { return lookup_.size(); }
    [[nodiscard]] std::size_t residentCount() const {
        std::size_t count = 0U;
        const auto view = registry_.view<const WorldCellStreaming>();
        for (const auto entity : view) {
            if (view.get<const WorldCellStreaming>(entity).stage == StreamingStage::Resident) ++count;
        }
        return count;
    }

    [[nodiscard]] entt::registry& registry() noexcept { return registry_; }
    [[nodiscard]] const entt::registry& registry() const noexcept { return registry_; }

private:
    struct QueueEntry {
        entt::entity entity{entt::null};
        StreamingStage stage{StreamingStage::Unloaded};
        std::uint64_t revision{};
        float priority{};
        std::size_t estimatedBytes{};
        std::uint64_t order{};
    };

    struct QueueCompare {
        [[nodiscard]] bool operator()(const QueueEntry& a, const QueueEntry& b) const noexcept {
            if (a.priority != b.priority) return a.priority < b.priority;
            return a.order > b.order;
        }
    };

    using Queue = std::priority_queue<QueueEntry, std::vector<QueueEntry>, QueueCompare>;

    [[nodiscard]] WorldCellStreaming* tryStreaming(entt::entity entity) {
        if (!registry_.valid(entity) || !registry_.all_of<WorldCellStreaming>(entity)) return nullptr;
        return &registry_.get<WorldCellStreaming>(entity);
    }

    void enqueue(entt::entity entity, StreamingStage stage) {
        const auto& streaming = registry_.get<WorldCellStreaming>(entity);
        QueueEntry entry{
            entity,
            stage,
            streaming.revision,
            streaming.priority,
            streaming.estimatedBytes,
            nextOrder_++};
        queueFor(stage).push(entry);
    }

    [[nodiscard]] Queue& queueFor(StreamingStage stage) {
        switch (stage) {
        case StreamingStage::Requested: return requestQueue_;
        case StreamingStage::MeshingQueued: return meshQueue_;
        case StreamingStage::UploadQueued: return uploadQueue_;
        case StreamingStage::EvictionQueued: return evictionQueue_;
        default: return requestQueue_;
        }
    }

    [[nodiscard]] std::vector<StreamingWorkItem> drainQueue(
        Queue& queue,
        StreamingStage queuedStage,
        StreamingStage activeStage,
        StreamingDrainBudget budget) {
        budget.maxItems = std::max(1U, budget.maxItems);
        std::vector<StreamingWorkItem> result;
        result.reserve(budget.maxItems);
        std::size_t usedBytes = 0U;

        while (!queue.empty() && result.size() < budget.maxItems) {
            const QueueEntry entry = queue.top();
            queue.pop();
            auto* streaming = tryStreaming(entry.entity);
            if (!streaming) continue;
            if (streaming->revision != entry.revision || streaming->stage != queuedStage) continue;

            const std::size_t bytes = streaming->estimatedBytes;
            if (!result.empty() && bytes > budget.maxBytes - std::min(usedBytes, budget.maxBytes)) {
                // Keep the highest-priority item queued for a later frame instead of silently dropping it.
                queue.push(entry);
                break;
            }
            streaming->stage = activeStage;
            usedBytes += bytes;
            const auto& address = registry_.get<WorldCellAddress>(entry.entity);
            result.push_back(StreamingWorkItem{
                entry.entity,
                address.key,
                activeStage,
                streaming->revision,
                streaming->priority,
                streaming->estimatedBytes});
        }
        return result;
    }

    entt::registry registry_{};
    std::unordered_map<WorldCellKey, entt::entity, WorldCellKeyHash> lookup_{};
    Queue requestQueue_{};
    Queue meshQueue_{};
    Queue uploadQueue_{};
    Queue evictionQueue_{};
    std::uint64_t nextOrder_{};
};

} // namespace vf::world
