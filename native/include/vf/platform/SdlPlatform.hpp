#pragma once

#include <cstdint>
#include <string_view>
#include <utility>

struct SDL_Window;

namespace vf {

struct PlatformInput {
    bool forward{};
    bool backward{};
    bool left{};
    bool right{};
    bool sprint{};
    bool ascend{};
    bool descend{};
    bool toggleFlight{};
    bool leftPressed{};
    bool rightPressed{};
    bool mouseCaptured{true};
    float mouseDx{};
    float mouseDy{};
    double flightSpeedSteps{};
};

class SdlPlatform final {
public:
    SdlPlatform(std::string_view title, std::int32_t width, std::int32_t height);
    ~SdlPlatform();

    SdlPlatform(const SdlPlatform&) = delete;
    SdlPlatform& operator=(const SdlPlatform&) = delete;

    [[nodiscard]] bool pumpEvents();
    [[nodiscard]] SDL_Window* window() const noexcept { return window_; }
    [[nodiscard]] std::pair<std::int32_t, std::int32_t> drawableSize() const noexcept;
    [[nodiscard]] bool consumeResize() noexcept;
    [[nodiscard]] const PlatformInput& input() const noexcept { return input_; }
    void setWindowTitle(std::string_view title);

private:
    void setMouseCaptured(bool captured);
    void refreshKeyboardState();
    void updateSpaceDoubleTap(bool spaceDown);

    SDL_Window* window_{};
    bool resized_{true};
    PlatformInput input_{};
    bool spaceWasDown_{};
    bool suppressSpaceUntilRelease_{};
    std::uint64_t lastSpacePressNanoseconds_{};
};

} // namespace vf
