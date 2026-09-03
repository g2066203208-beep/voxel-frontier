cmake_minimum_required(VERSION 3.28)
project(VoxelFrontierNative VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)

option(VF_BUILD_RUNTIME "Build the native desktop runtime" ON)
option(VF_BUILD_TESTS "Build native engine tests" ON)

add_library(vf_engine STATIC
    src/core/Engine.cpp
    src/world/Chunk.cpp
    src/world/World.cpp
)

target_include_directories(vf_engine PUBLIC include)
target_compile_features(vf_engine PUBLIC cxx_std_23)

if(MSVC)
    target_compile_options(vf_engine PRIVATE /W4 /permissive- /EHsc)
else()
    target_compile_options(vf_engine PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(VF_BUILD_RUNTIME)
    FetchContent_Declare(
        SDL3
        GIT_REPOSITORY https://github.com/libsdl-org/SDL.git
        GIT_TAG release-3.4.14
        GIT_SHALLOW TRUE
    )
    FetchContent_MakeAvailable(SDL3)

    FetchContent_Declare(
        volk
        GIT_REPOSITORY https://github.com/zeux/volk.git
        GIT_TAG 1.4.304
        GIT_SHALLOW TRUE
    )
    FetchContent_MakeAvailable(volk)

    add_executable(voxel_frontier
        src/app/Main.cpp
        src/platform/SdlPlatform.cpp
        src/render/VulkanRenderer.cpp
    )
    target_include_directories(voxel_frontier PRIVATE include)
    target_link_libraries(voxel_frontier PRIVATE vf_engine SDL3::SDL3 volk)
    target_compile_definitions(voxel_frontier PRIVATE SDL_MAIN_USE_CALLBACKS=0)

    if(WIN32)
        set_property(TARGET voxel_frontier PROPERTY WIN32_EXECUTABLE FALSE)
    endif()
endif()

if(VF_BUILD_TESTS)
    enable_testing()
    add_executable(vf_engine_tests tests/EngineTests.cpp)
    target_link_libraries(vf_engine_tests PRIVATE vf_engine)
    add_test(NAME vf_engine_tests COMMAND vf_engine_tests)
endif()
