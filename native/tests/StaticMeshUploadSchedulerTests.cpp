#include "vf/render/StaticMeshUploadScheduler.hpp"

#include <cstdlib>
#include <iostream>
#include <string_view>

namespace {
[[noreturn]] void fail(std::string_view message) {
    std::cerr << "R24 STATIC UPLOAD SCHEDULER TEST FAILURE: " << message << '\n';
    std::exit(1);
}
void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}
} // namespace

int main() {
    vf::StaticMeshUploadScheduler scheduler;

    const auto first = scheduler.adopt(1U);
    require(first.upload && first.slot == 0U, "first generation must upload exactly once into slot 0");

    const auto secondFrameSameGeneration = scheduler.adopt(1U);
    require(!secondFrameSameGeneration.upload && secondFrameSameGeneration.slot == 0U,
        "second frame must share resident generation without another upload");
    require(scheduler.uploadCount() == 1U,
        "one static generation must produce one CPU staging/GPU transfer, not one per frame");

    const auto secondGeneration = scheduler.adopt(2U);
    require(secondGeneration.upload && secondGeneration.slot == 1U,
        "new generation must alternate to the other immutable slot");
    require(!scheduler.adopt(2U).upload,
        "all frames must share the second resident generation read-only");

    const auto thirdGeneration = scheduler.adopt(3U);
    require(thirdGeneration.upload && thirdGeneration.slot == 0U,
        "third generation must safely rotate back to the retired slot");
    require(scheduler.uploadCount() == 3U,
        "upload count must equal generation changes exactly");

    scheduler.reset();
    require(!scheduler.initialized() && scheduler.uploadCount() == 0U,
        "generation overflow/reset must clear scheduler state");

    std::cout << "R24 static upload scheduler tests passed generations=3 uploads=3 duplicate_frame_uploads=0\n";
    return 0;
}
