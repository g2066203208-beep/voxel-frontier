#include "vf/world/PerceptualResidencyPolicy.hpp"

#include <iostream>
#include <stdexcept>

namespace {

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

} // namespace

int main() {
    try {
        using namespace vf;

        // A nearby interactable boulder must be a real detailed object with active physics.
        const auto nearBoulder = decidePerceptualResidency({
            5.0, 1.2, 0.25, 1080.0, 1.1868238913561442,
            0.0, 1.0, 96.0, true, false, false});
        require(nearBoulder.tier == SceneRepresentationTier::Detailed,
            "near interactable object must be detailed");
        require(nearBoulder.sourceCellsRequired && nearBoulder.individualEntitiesRequired,
            "near detailed object must require source residency");
        require(nearBoulder.physicsActive, "near interactable object must have physics");

        // The same tiny object at long range should vanish rather than consume a draw/entity slot.
        const auto farBoulder = decidePerceptualResidency({
            5000.0, 1.2, 0.25, 1080.0, 1.1868238913561442,
            0.0, 1.0, 96.0, true, false, false});
        require(farBoulder.tier != SceneRepresentationTier::Detailed,
            "far tiny object must not retain detail");
        require(!farBoulder.sourceCellsRequired && !farBoulder.physicsActive,
            "far tiny object must not keep source cells or physics");

        // A mountain should remain visible from 100 km, but only as a cheap aggregate proxy.
        const auto mountain100km = decidePerceptualResidency({
            100000.0, 3000.0, 350.0, 1080.0, 1.1868238913561442,
            0.0, 1.0, 96.0, false, false, true});
        require(mountain100km.tier == SceneRepresentationTier::ClusterProxy
                || mountain100km.tier == SceneRepresentationTier::MacroProxy,
            "distant mountain should remain visible through an aggregate proxy");
        require(!mountain100km.sourceCellsRequired && !mountain100km.individualEntitiesRequired,
            "distant mountain proxy must not require source chunks/entities");
        require(!mountain100km.physicsActive && !mountain100km.highQualityMaterial,
            "distant mountain proxy must not pay physics/full-material cost");

        // At extreme range the landmark survives only as a horizon proxy, still without source data.
        const auto mountain1000km = decidePerceptualResidency({
            1000000.0, 3000.0, 350.0, 1080.0, 1.1868238913561442,
            0.0, 1.0, 96.0, false, false, true});
        require(mountain1000km.tier == SceneRepresentationTier::MacroProxy
                || mountain1000km.tier == SceneRepresentationTier::HorizonProxy,
            "extreme-range landmark should degrade to macro/horizon representation");
        require(!mountain1000km.sourceCellsRequired && !mountain1000km.physicsActive,
            "extreme-range landmark must stay proxy-only");

        // Motion must never increase representation cost for the same scene contribution.
        const auto slowCity = decidePerceptualResidency({
            50000.0, 5000.0, 500.0, 1080.0, 1.1868238913561442,
            0.0, 1.0, 96.0, false, false, true});
        const auto fastCity = decidePerceptualResidency({
            50000.0, 5000.0, 500.0, 1080.0, 1.1868238913561442,
            1.0, 1.0, 96.0, false, false, true});
        require(static_cast<int>(fastCity.tier) <= static_cast<int>(slowCity.tier),
            "high-speed traversal must not increase scene representation detail");
        require(fastCity.minimumUpdatePeriodFrames >= slowCity.minimumUpdatePeriodFrames,
            "high-speed traversal must not update distant proxies more often");

        // Occlusion should kill non-gameplay work regardless of distance/size.
        const auto occluded = decidePerceptualResidency({
            200.0, 20.0, 2.0, 1080.0, 1.1868238913561442,
            0.0, 1.0, 96.0, false, true, false});
        require(occluded.tier == SceneRepresentationTier::Culled,
            "occluded non-interactive object should be culled");
        require(!occluded.sourceCellsRequired && !occluded.physicsActive,
            "culled object must have zero residency/physics requirement");

        std::cout << "R24 PERCEPTUAL RESIDENCY PASS"
                  << " near_px=" << nearBoulder.projectedDiameterPixels
                  << " mountain100km_px=" << mountain100km.projectedDiameterPixels
                  << " mountain1000km_px=" << mountain1000km.projectedDiameterPixels
                  << " slow_city_tier=" << static_cast<int>(slowCity.tier)
                  << " fast_city_tier=" << static_cast<int>(fastCity.tier)
                  << '\n';
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "R24 PERCEPTUAL RESIDENCY FAIL: " << e.what() << '\n';
        return 1;
    }
}
