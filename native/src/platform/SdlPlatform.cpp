#include "vf/platform/SdlPlatform.hpp"

#include <SDL3/SDL.h>

#include <stdexcept>
#include <string>

namespace vf {

SdlPlatform::SdlPlatform(std::string_view title, std::int32_t width, std::int32_t height) {
    if (!SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_GAMEPAD | SDL_INIT_AUDIO)) {
        throw std::runtime_error(std::string{"SDL_Init failed: "} + SDL_GetError());
    }

    window_ = SDL_CreateWindow(
        std::string{title}.c_str(),
        width,
        height,
        SDL_WINDOW_VULKAN | SDL_WINDOW_RESIZABLE | SDL_WINDOW_HIGH_PIXEL_DENSITY);
    if (!window_) {
        const std::string error = SDL_GetError();
        SDL_Quit();
        throw std::runtime_error("SDL_CreateWindow failed: " + error);
    }

    setMouseCaptured(true);
}

SdlPlatform::~SdlPlatform() {
    if (window_) SDL_DestroyWindow(window_);
    SDL_Quit();
}

void SdlPlatform::setMouseCaptured(bool captured) {
    input_.mouseCaptured = captured;
    if (window_) {
        if (!SDL_SetWindowRelativeMouseMode(window_, captured)) {
            SDL_Log("SDL_SetWindowRelativeMouseMode failed: %s", SDL_GetError());
        }
    }
}

void SdlPlatform::updateSpaceDoubleTap(bool spaceDown) {
    if (spaceDown && !spaceWasDown_) {
        constexpr std::uint64_t kDoubleTapWindowNanoseconds = 420000000ULL;
        const std::uint64_t now = SDL_GetTicksNS();
        if (lastSpacePressNanoseconds_ != 0U
            && now >= lastSpacePressNanoseconds_
            && now - lastSpacePressNanoseconds_ <= kDoubleTapWindowNanoseconds) {
            input_.toggleFlight = true;
            lastSpacePressNanoseconds_ = 0U;
        } else {
            lastSpacePressNanoseconds_ = now;
        }
    }
    spaceWasDown_ = spaceDown;
}

void SdlPlatform::refreshKeyboardState() {
    int keyCount = 0;
    const bool* keys = SDL_GetKeyboardState(&keyCount);
    if (!keys || keyCount <= 0) return;

    const auto down = [keys, keyCount](SDL_Scancode code) {
        const int index = static_cast<int>(code);
        return index >= 0 && index < keyCount && keys[index];
    };

    input_.forward = down(SDL_SCANCODE_W);
    input_.backward = down(SDL_SCANCODE_S);
    input_.left = down(SDL_SCANCODE_A);
    input_.right = down(SDL_SCANCODE_D);
    input_.sprint = down(SDL_SCANCODE_LSHIFT) || down(SDL_SCANCODE_RSHIFT);
    input_.ascend = down(SDL_SCANCODE_SPACE);
    input_.descend = down(SDL_SCANCODE_LCTRL) || down(SDL_SCANCODE_RCTRL);
    updateSpaceDoubleTap(input_.ascend);
}

bool SdlPlatform::pumpEvents() {
    input_.mouseDx = 0.0F;
    input_.mouseDy = 0.0F;
    input_.toggleFlight = false;
    input_.leftPressed = false;
    input_.rightPressed = false;

    SDL_Event event{};
    while (SDL_PollEvent(&event)) {
        switch (event.type) {
        case SDL_EVENT_QUIT:
            return false;
        case SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED:
        case SDL_EVENT_WINDOW_RESIZED:
            resized_ = true;
            break;
        case SDL_EVENT_MOUSE_MOTION:
            if (input_.mouseCaptured) {
                input_.mouseDx += event.motion.xrel;
                input_.mouseDy += event.motion.yrel;
            }
            break;
        case SDL_EVENT_MOUSE_BUTTON_DOWN: {
            const bool wasCaptured = input_.mouseCaptured;
            if (!wasCaptured) {
                setMouseCaptured(true);
                break;
            }
            if (event.button.button == SDL_BUTTON_LEFT) input_.leftPressed = true;
            if (event.button.button == SDL_BUTTON_RIGHT) input_.rightPressed = true;
            break;
        }
        case SDL_EVENT_KEY_DOWN:
            if (!event.key.repeat && event.key.scancode == SDL_SCANCODE_ESCAPE) {
                setMouseCaptured(!input_.mouseCaptured);
            }
            break;
        default:
            break;
        }
    }

    // Continuous movement and the Space rising edge come from the same physical-key state.
    // This avoids event timestamp/layout differences and makes Minecraft-style double-tap flight
    // deterministic even if the frame containing the key event stalls.
    refreshKeyboardState();
    return true;
}

std::pair<std::int32_t, std::int32_t> SdlPlatform::drawableSize() const noexcept {
    int width = 0;
    int height = 0;
    if (window_) (void)SDL_GetWindowSizeInPixels(window_, &width, &height);
    return {width, height};
}

bool SdlPlatform::consumeResize() noexcept {
    const bool value = resized_;
    resized_ = false;
    return value;
}

void SdlPlatform::setWindowTitle(std::string_view title) {
    if (window_) SDL_SetWindowTitle(window_, std::string{title}.c_str());
}

} // namespace vf
