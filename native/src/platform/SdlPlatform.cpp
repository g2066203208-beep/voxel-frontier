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
}

SdlPlatform::~SdlPlatform() {
    if (window_) SDL_DestroyWindow(window_);
    SDL_Quit();
}

bool SdlPlatform::pumpEvents() {
    SDL_Event event{};
    while (SDL_PollEvent(&event)) {
        switch (event.type) {
        case SDL_EVENT_QUIT:
            return false;
        case SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED:
        case SDL_EVENT_WINDOW_RESIZED:
            resized_ = true;
            break;
        case SDL_EVENT_KEY_DOWN:
            if (event.key.key == SDLK_ESCAPE) return false;
            break;
        default:
            break;
        }
    }
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

} // namespace vf
