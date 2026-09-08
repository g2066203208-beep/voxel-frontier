#include "vf/core/AsyncInbox.hpp"

#include <array>
#include <atomic>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <thread>
#include <vector>

namespace {

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

struct ResultPacket {
    std::uint32_t producer{};
    std::uint32_t sequence{};
    std::uint64_t checksum{};
};

} // namespace

int main() {
    try {
        constexpr std::uint32_t producerCount = 4U;
        constexpr std::uint32_t itemsPerProducer = 50000U;
        constexpr std::uint64_t totalItems =
            static_cast<std::uint64_t>(producerCount) * itemsPerProducer;
        vf::core::AsyncInbox<ResultPacket> inbox{4096U, producerCount};

        std::array<std::atomic<std::uint64_t>, producerCount> retries{};
        std::vector<std::thread> producers;
        producers.reserve(producerCount);
        for (std::uint32_t producerId = 0; producerId < producerCount; ++producerId) {
            producers.emplace_back([&, producerId] {
                vf::core::AsyncInbox<ResultPacket>::Producer producer{inbox};
                for (std::uint32_t sequence = 0; sequence < itemsPerProducer; ++sequence) {
                    ResultPacket packet{
                        producerId,
                        sequence,
                        (static_cast<std::uint64_t>(producerId) << 32U)
                            ^ static_cast<std::uint64_t>(sequence)
                            ^ 0xD6E8FEB86659FD93ULL};
                    while (!producer.tryPush(packet)) {
                        retries[producerId].fetch_add(1U, std::memory_order_relaxed);
                        std::this_thread::yield();
                    }
                }
            });
        }

        std::array<std::uint32_t, producerCount> nextSequence{};
        std::uint64_t consumed = 0U;
        std::array<ResultPacket, 256U> batch{};
        while (consumed < totalItems) {
            const std::size_t count = inbox.drain(batch);
            if (count == 0U) {
                std::this_thread::yield();
                continue;
            }
            for (std::size_t i = 0; i < count; ++i) {
                const auto& packet = batch[i];
                require(packet.producer < producerCount, "MPMC packet producer id corrupted");
                require(packet.sequence == nextSequence[packet.producer],
                    "per-producer FIFO ordering violated");
                const std::uint64_t expectedChecksum =
                    (static_cast<std::uint64_t>(packet.producer) << 32U)
                    ^ static_cast<std::uint64_t>(packet.sequence)
                    ^ 0xD6E8FEB86659FD93ULL;
                require(packet.checksum == expectedChecksum, "MPMC packet payload torn/corrupted");
                ++nextSequence[packet.producer];
                ++consumed;
            }
        }
        for (auto& producer : producers) producer.join();

        for (const auto value : nextSequence)
            require(value == itemsPerProducer, "MPMC lost producer packets");
        require(inbox.size() == 0U, "MPMC inbox did not drain to zero");
        require(inbox.pushedCount() == totalItems, "MPMC push accounting mismatch");
        require(inbox.poppedCount() == totalItems, "MPMC pop accounting mismatch");

        std::uint64_t retryCount = 0U;
        for (const auto& retry : retries) retryCount += retry.load(std::memory_order_relaxed);
        std::cout << "R24 ASYNC INBOX PASS producers=" << producerCount
                  << " items=" << totalItems
                  << " capacity=" << inbox.capacity()
                  << " retries=" << retryCount
                  << " capacity_drops=" << inbox.capacityDrops()
                  << " allocation_pressure_drops=" << inbox.allocationPressureDrops()
                  << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "R24 ASYNC INBOX FAIL: " << error.what() << '\n';
        return 1;
    }
}
