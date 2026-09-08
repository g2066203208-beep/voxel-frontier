#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>

namespace vf {

enum class SceneRepresentationTier : std::uint8_t {
    Culled,
    HorizonProxy,
    MacroProxy,
    ClusterProxy,
    Detailed
};

struct PerceptualResidencyInput {
    double distanceMeters{1.0};
    double boundingRadiusMeters{1.0};
    // Conservative world-space deviation of the currently available proxy from the full source.
    double proxyGeometricErrorMeters{1.0};
    double viewportHeightPixels{1080.0};
    double verticalFovRadians{1.1868238913561442}; // 68 degrees
    double motionWeight{};                         // 0 = inspect, 1 = fast transit
    double importance{1.0};                       // landmarks/gameplay can raise this above 1
    double interactionRadiusMeters{96.0};
    bool potentiallyInteractive{};
    bool occluded{};
    bool persistentLandmark{};
};

struct PerceptualResidencyDecision {
    SceneRepresentationTier tier{SceneRepresentationTier::Culled};
    double projectedDiameterPixels{};
    double screenSpaceErrorPixels{};
    double perceptualScore{};

    // The key decoupling contract: distant visibility does not imply source-cell/entity residency.
    bool sourceCellsRequired{};
    bool individualEntitiesRequired{};
    bool physicsActive{};
    bool dynamicShadows{};
    bool highQualityMaterial{};
    bool virtualTextureFeedback{};

    // Distant proxy state is intentionally refreshed much less frequently than near gameplay state.
    std::uint32_t minimumUpdatePeriodFrames{120U};
};

[[nodiscard]] inline double sceneProjectionScalePixels(
    double viewportHeightPixels,
    double verticalFovRadians) noexcept {
    const double h = std::max(1.0, viewportHeightPixels);
    const double fov = std::clamp(verticalFovRadians, 0.05, 3.05);
    return h / (2.0 * std::tan(fov * 0.5));
}

// R24_PERCEPTUAL_RESIDENCY_V1
// "Visible" and "fully loaded" are separate concepts. The policy selects the cheapest representation
// that can still contribute useful pixels. Far scenery can therefore remain visible through compact
// HLOD/macro/horizon proxies while its source chunks, individual entities, physics and expensive
// materials stay completely non-resident.
[[nodiscard]] inline PerceptualResidencyDecision decidePerceptualResidency(
    const PerceptualResidencyInput& input) noexcept {
    PerceptualResidencyDecision result{};

    const double distance = std::max(0.05, input.distanceMeters);
    const double radius = std::max(0.001, input.boundingRadiusMeters);
    const double error = std::max(0.0, input.proxyGeometricErrorMeters);
    const double projection = sceneProjectionScalePixels(
        input.viewportHeightPixels, input.verticalFovRadians);

    result.projectedDiameterPixels = (2.0 * radius * projection) / distance;
    result.screenSpaceErrorPixels = (error * projection) / distance;

    const double motion = std::clamp(input.motionWeight, 0.0, 1.0);
    const double importance = std::clamp(input.importance, 0.1, 8.0);
    const double motionSuppression = 1.0 + 4.0 * motion;

    // Diameter controls how much screen real estate the object owns. SSE prevents a very large but
    // geometrically inaccurate proxy from staying too coarse. Motion deliberately suppresses detail
    // because fine structure cannot be inspected while traversing quickly.
    result.perceptualScore = importance
        * std::max(result.projectedDiameterPixels * 0.35, result.screenSpaceErrorPixels * 3.0)
        / motionSuppression;

    const bool interactionBubble = input.potentiallyInteractive
        && distance <= std::max(0.0, input.interactionRadiusMeters);

    if (input.occluded && !interactionBubble && !input.persistentLandmark) {
        result.tier = SceneRepresentationTier::Culled;
    } else if (interactionBubble || result.perceptualScore >= 72.0) {
        result.tier = SceneRepresentationTier::Detailed;
    } else if (result.perceptualScore >= 12.0) {
        result.tier = SceneRepresentationTier::ClusterProxy;
    } else if (result.perceptualScore >= 1.0) {
        result.tier = SceneRepresentationTier::MacroProxy;
    } else if (result.perceptualScore >= 0.12 || input.persistentLandmark) {
        result.tier = SceneRepresentationTier::HorizonProxy;
    } else {
        result.tier = SceneRepresentationTier::Culled;
    }

    switch (result.tier) {
        case SceneRepresentationTier::Detailed:
            result.sourceCellsRequired = true;
            result.individualEntitiesRequired = true;
            result.physicsActive = interactionBubble;
            result.dynamicShadows = true;
            result.highQualityMaterial = true;
            result.virtualTextureFeedback = true;
            result.minimumUpdatePeriodFrames = 1U;
            break;
        case SceneRepresentationTier::ClusterProxy:
            // Prebuilt/generated cluster proxy: source actors/cells remain unloaded.
            result.sourceCellsRequired = false;
            result.individualEntitiesRequired = false;
            result.physicsActive = false;
            result.dynamicShadows = result.projectedDiameterPixels >= 32.0 && motion < 0.45;
            result.highQualityMaterial = false;
            result.virtualTextureFeedback = true;
            result.minimumUpdatePeriodFrames = motion < 0.35 ? 2U : 4U;
            break;
        case SceneRepresentationTier::MacroProxy:
            result.sourceCellsRequired = false;
            result.individualEntitiesRequired = false;
            result.physicsActive = false;
            result.dynamicShadows = false;
            result.highQualityMaterial = false;
            result.virtualTextureFeedback = false;
            result.minimumUpdatePeriodFrames = motion < 0.35 ? 8U : 16U;
            break;
        case SceneRepresentationTier::HorizonProxy:
            result.sourceCellsRequired = false;
            result.individualEntitiesRequired = false;
            result.physicsActive = false;
            result.dynamicShadows = false;
            result.highQualityMaterial = false;
            result.virtualTextureFeedback = false;
            result.minimumUpdatePeriodFrames = 32U;
            break;
        case SceneRepresentationTier::Culled:
            result.sourceCellsRequired = false;
            result.individualEntitiesRequired = false;
            result.physicsActive = false;
            result.dynamicShadows = false;
            result.highQualityMaterial = false;
            result.virtualTextureFeedback = false;
            result.minimumUpdatePeriodFrames = 120U;
            break;
    }

    return result;
}

} // namespace vf
