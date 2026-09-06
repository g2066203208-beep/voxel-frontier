#include "vf/world/UniverseTime.hpp"

namespace vf {

void UniverseTime::advance(double realDeltaSeconds) noexcept {
    if (realDeltaSeconds <= 0.0) {
        return;
    }

    totalSeconds += realDeltaSeconds;
    physicsAccumulator += realDeltaSeconds;
    gameplayAccumulator += realDeltaSeconds;
    weatherAccumulator += realDeltaSeconds;
    climateAccumulator += realDeltaSeconds;
    orbitalAccumulator += realDeltaSeconds;
}

bool UniverseTime::consumePhysicsTick() noexcept {
    if (physicsAccumulator < physicsStepSeconds) return false;
    physicsAccumulator -= physicsStepSeconds;
    return true;
}

bool UniverseTime::consumeGameplayTick() noexcept {
    if (gameplayAccumulator < gameplayStepSeconds) return false;
    gameplayAccumulator -= gameplayStepSeconds;
    return true;
}

bool UniverseTime::consumeWeatherTick() noexcept {
    if (weatherAccumulator < weatherStepSeconds) return false;
    weatherAccumulator -= weatherStepSeconds;
    return true;
}

bool UniverseTime::consumeClimateTick() noexcept {
    if (climateAccumulator < climateStepSeconds) return false;
    climateAccumulator -= climateStepSeconds;
    return true;
}

bool UniverseTime::consumeOrbitalTick() noexcept {
    if (orbitalAccumulator < orbitalStepSeconds) return false;
    orbitalAccumulator -= orbitalStepSeconds;
    return true;
}

} // namespace vf
