cmake_minimum_required(VERSION 3.28)
project(VoxelFrontierNative VERSION 0.3.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)

option(VF_BUILD_RUNTIME "Build the native desktop runtime" ON)
option(VF_BUILD_TESTS "Build native engine tests" ON)

# Header-only graphics math. Pin the current stable GLM 1.0 line.
set(GLM_BUILD_TESTS OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    glm
    GIT_REPOSITORY https://github.com/g-truc/glm.git
    GIT_TAG 1.0.3
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(glm)

add_library(vf_engine STATIC
    src/core/Engine.cpp
    src/world/Chunk.cpp
    src/world/World.cpp
    src/world/PlanetSurface.cpp
    src/player/PlanetCamera.cpp
    src/physics/PhysicsWorld.cpp
    src/physics/ShallowWater.cpp
    src/physics/TreePhysics.cpp
    src/physics/GasChamber.cpp
)

target_include_directories(vf_engine PUBLIC include)
target_compile_features(vf_engine PUBLIC cxx_std_23)
target_link_libraries(vf_engine PUBLIC glm::glm)
target_compile_definitions(vf_engine PUBLIC GLM_FORCE_DEPTH_ZERO_TO_ONE GLM_FORCE_RADIANS)

if(MSVC)
    target_compile_options(vf_engine PRIVATE /W4 /permissive- /EHsc)
else()
    target_compile_options(vf_engine PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(VF_BUILD_RUNTIME)
    # Thin platform layer only. SDL does not provide our renderer/world/physics/gameplay.
    set(SDL_SHARED OFF CACHE BOOL "" FORCE)
    set(SDL_STATIC ON CACHE BOOL "" FORCE)
    set(SDL_TESTS OFF CACHE BOOL "" FORCE)
    set(SDL_TEST_LIBRARY OFF CACHE BOOL "" FORCE)
    set(SDL_EXAMPLES OFF CACHE BOOL "" FORCE)
    FetchContent_Declare(
        SDL3
        GIT_REPOSITORY https://github.com/libsdl-org/SDL.git
        GIT_TAG release-3.4.14
        GIT_SHALLOW TRUE
    )
    FetchContent_MakeAvailable(SDL3)

    # Pin Vulkan headers and volk to the same published Vulkan revision.
    set(VULKAN_HEADERS_ENABLE_TESTS OFF CACHE BOOL "" FORCE)
    set(VULKAN_HEADERS_ENABLE_MODULE OFF CACHE BOOL "" FORCE)
    FetchContent_Declare(
        VulkanHeaders
        GIT_REPOSITORY https://github.com/KhronosGroup/Vulkan-Headers.git
        GIT_TAG v1.4.350
        GIT_SHALLOW TRUE
    )
    FetchContent_MakeAvailable(VulkanHeaders)

    FetchContent_Declare(
        volk
        GIT_REPOSITORY https://github.com/zeux/volk.git
        GIT_TAG 1.4.350
        GIT_SHALLOW TRUE
    )
    FetchContent_MakeAvailable(volk)

    # Slang is a build-time shader compiler only. SPIR-V is embedded into the executable.
    if(WIN32)
        FetchContent_Declare(
            slang_bin
            URL https://github.com/shader-slang/slang/releases/download/v2026.16.1/slang-2026.16.1-windows-x86_64.zip
        )
        FetchContent_GetProperties(slang_bin)
        if(NOT slang_bin_POPULATED)
            FetchContent_Populate(slang_bin)
        endif()
        file(GLOB_RECURSE SLANGC_CANDIDATES "${slang_bin_SOURCE_DIR}/slangc.exe")
        list(LENGTH SLANGC_CANDIDATES SLANGC_COUNT)
        if(SLANGC_COUNT EQUAL 0)
            message(FATAL_ERROR "slangc.exe not found in Slang binary package")
        endif()
        list(GET SLANGC_CANDIDATES 0 SLANGC_EXECUTABLE)
    else()
        find_program(SLANGC_EXECUTABLE slangc REQUIRED)
    endif()

    set(VF_GENERATED_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated")
    set(VF_VERTEX_SPV "${VF_GENERATED_DIR}/planet.vert.spv")
    set(VF_FRAGMENT_SPV "${VF_GENERATED_DIR}/planet.frag.spv")
    set(VF_SHADER_HEADER "${VF_GENERATED_DIR}/PlanetShaders.hpp")

    add_custom_command(
        OUTPUT "${VF_VERTEX_SPV}" "${VF_FRAGMENT_SPV}"
        COMMAND ${CMAKE_COMMAND} -E make_directory "${VF_GENERATED_DIR}"
        COMMAND "${SLANGC_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/shaders/planet.slang"
                -target spirv -entry vertexMain -stage vertex -matrix-layout-column-major -O2 -o "${VF_VERTEX_SPV}"
        COMMAND "${SLANGC_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/shaders/planet.slang"
                -target spirv -entry fragmentMain -stage fragment -matrix-layout-column-major -O2 -o "${VF_FRAGMENT_SPV}"
        DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/shaders/planet.slang"
        VERBATIM
    )

    add_custom_command(
        OUTPUT "${VF_SHADER_HEADER}"
        COMMAND ${CMAKE_COMMAND}
            "-DVERT=${VF_VERTEX_SPV}"
            "-DFRAG=${VF_FRAGMENT_SPV}"
            "-DOUT=${VF_SHADER_HEADER}"
            -P "${CMAKE_CURRENT_SOURCE_DIR}/cmake/EmbedShaders.cmake"
        DEPENDS "${VF_VERTEX_SPV}" "${VF_FRAGMENT_SPV}" "${CMAKE_CURRENT_SOURCE_DIR}/cmake/EmbedShaders.cmake"
        VERBATIM
    )

    add_custom_target(vf_shaders DEPENDS "${VF_SHADER_HEADER}")

    add_executable(voxel_frontier
        src/app/Main.cpp
        src/platform/SdlPlatform.cpp
        src/render/VulkanRenderer.cpp
        "${VF_SHADER_HEADER}"
    )
    add_dependencies(voxel_frontier vf_shaders)
    target_include_directories(voxel_frontier PRIVATE include "${VF_GENERATED_DIR}")
    target_link_libraries(voxel_frontier PRIVATE
        vf_engine
        SDL3::SDL3-static
        Vulkan::Headers
        volk::volk
        glm::glm
    )
    target_compile_definitions(voxel_frontier PRIVATE
        VK_NO_PROTOTYPES
        GLM_FORCE_DEPTH_ZERO_TO_ONE
        GLM_FORCE_RADIANS
    )

    if(MSVC)
        target_compile_options(voxel_frontier PRIVATE /W4 /permissive- /EHsc)
    else()
        target_compile_options(voxel_frontier PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endif()

if(VF_BUILD_TESTS)
    enable_testing()
    add_executable(vf_engine_tests tests/EngineTests.cpp)
    target_link_libraries(vf_engine_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_engine_tests COMMAND vf_engine_tests)
endif()
