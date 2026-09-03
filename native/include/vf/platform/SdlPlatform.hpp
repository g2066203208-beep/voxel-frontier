#pragma once

#include <cstdint>
#include <string_view>
#include <utility>

struct SDL_Window;

namespace vf {

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

private:
    SDL_Window* window_{};
    bool resized_{true};
};

} // namespace vf
