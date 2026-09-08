#include "vf/world/VelocityAwareLodPolicy.hpp"

#include <iostream>
#include <stdexcept>

namespace {

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

} // namespace

int main() {
    try {
        const vf::VelocityLodDecision inspect = vf::decideVelocityAwareLod({
            0.0, 0.0, 1.0, 4.0, 3.0, 1100U, 520.0});
        const vf::VelocityLodDecision explore = vf::decideVelocityAwareLod({
            120.0, 0.15, 0.10, 4.0, 3.0, 1100U, 520.0});
        const vf::VelocityLodDecision fast = vf::decideVelocityAwareLod({
            800.0, 0.8, 0.05, 4.0, 3.0, 1100U, 520.0});
        const vf::VelocityLodDecision transit = vf::decideVelocityAwareLod({
            3200.0, 2.6, 0.01, 4.0, 3.0, 1100U, 520.0});

        require(inspect.fineDetailAllowed, "stationary stable camera should allow fine refinement");
        require(!explore.fineDetailAllowed, "moving camera should hold fine refinement");
        require(!fast.fineDetailAllowed, "fast travel should prohibit fine refinement");
        require(!transit.fineDetailAllowed, "transit should prohibit fine refinement");

        require(inspect.targetScreenErrorPixels < explore.targetScreenErrorPixels,
            "screen-space error must relax as speed rises");
        require(explore.targetScreenErrorPixels < fast.targetScreenErrorPixels,
            "screen-space error must continue relaxing at fast speed");
        require(fast.targetScreenErrorPixels <= transit.targetScreenErrorPixels,
            "transit screen-space error must be coarsest");

        require(inspect.nearFieldCellMeters < explore.nearFieldCellMeters,
            "near-field cells must become coarser as speed rises");
        require(explore.nearFieldCellMeters < fast.nearFieldCellMeters,
            "fast travel must further coarsen cells");
        require(fast.nearFieldCellMeters <= transit.nearFieldCellMeters,
            "transit cells must be coarsest");

        require(inspect.maxLeafPatches > explore.maxLeafPatches,
            "leaf budget must shrink as speed rises");
        require(explore.maxLeafPatches > fast.maxLeafPatches,
            "fast travel must further shrink leaf budget");
        require(fast.maxLeafPatches >= transit.maxLeafPatches,
            "transit leaf budget must be smallest");

        require(explore.forwardPrefetchMeters > inspect.forwardPrefetchMeters,
            "moving camera should prefetch farther ahead");
        require(fast.forwardPrefetchMeters > explore.forwardPrefetchMeters,
            "fast travel should prefetch farther ahead");
        require(transit.forwardPrefetchMeters > fast.forwardPrefetchMeters,
            "transit should maximize forward coverage");

        const vf::VelocityLodDecision rapidTurn = vf::decideVelocityAwareLod({
            0.0, 2.8, 0.0, 4.0, 3.0, 1100U, 520.0});
        require(rapidTurn.motionWeight > 0.95,
            "rapid camera rotation must reduce detail even without translation");
        require(!rapidTurn.fineDetailAllowed,
            "rapid camera rotation must block fine refinement");

        std::cout << "R24 VELOCITY LOD PASS"
                  << " inspect_leaf=" << inspect.maxLeafPatches
                  << " explore_leaf=" << explore.maxLeafPatches
                  << " fast_leaf=" << fast.maxLeafPatches
                  << " transit_leaf=" << transit.maxLeafPatches
                  << " transit_prefetch_m=" << transit.forwardPrefetchMeters
                  << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "R24 VELOCITY LOD FAIL: " << error.what() << '\n';
        return 1;
    }
}
