cmake_minimum_required(VERSION 3.28)
project(VoxelFrontierNative VERSION 0.8.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)

option(VF_BUILD_RUNTIME "Build the native desktop runtime" ON)
option(VF_BUILD_TESTS "Build native engine tests" ON)

set(GLM_BUILD_TESTS OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    glm
    GIT_REPOSITORY https://github.com/g-truc/glm.git
    GIT_TAG 1.0.3
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(glm)

add_library(vf_engine STATIC
    src/world/PlanetSurface.cpp
    src/world/OceanSurface.cpp
    src/world/PlanetProcedural.cpp
    src/world/PlanetVisibility.cpp
    src/world/ProceduralTree.cpp
    src/world/PlanetEcology.cpp
    src/world/CelestialSystem.cpp
    src/player/PlanetCamera.cpp
    src/physics/PhysicsWorld.cpp
    src/physics/Broadphase.cpp
    src/physics/CollisionGeometry.cpp
    src/physics/GjkEpa.cpp
    src/physics/AerodynamicSurface.cpp
    src/physics/ShallowWater.cpp
    src/physics/TreePhysics.cpp
    src/physics/GasChamber.cpp
    src/physics/SpectralOptics.cpp
    src/physics/ElectromagneticRadiation.cpp
    src/render/PhysicsDebugMesh.cpp
    src/gameplay/PhysicsPlayground.cpp
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

    if(WIN32)
        FetchContent_Declare(
            slang_bin
            URL https://github.com/shader-slang/slang/releases/download/v2026.16.1/slang-2026.16.1-windows-x86_64.zip
        )
        FetchContent_MakeAvailable(slang_bin)
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
    set(VF_SKY_VERTEX_SPV "${VF_GENERATED_DIR}/sky.vert.spv")
    set(VF_SKY_FRAGMENT_SPV "${VF_GENERATED_DIR}/sky.frag.spv")
    set(VF_SHADOW_VERTEX_SPV "${VF_GENERATED_DIR}/shadow.vert.spv")
    set(VF_SHADER_HEADER "${VF_GENERATED_DIR}/PlanetShaders.hpp")

    add_custom_command(
        OUTPUT "${VF_VERTEX_SPV}" "${VF_FRAGMENT_SPV}" "${VF_SKY_VERTEX_SPV}" "${VF_SKY_FRAGMENT_SPV}" "${VF_SHADOW_VERTEX_SPV}"
        COMMAND ${CMAKE_COMMAND} -E make_directory "${VF_GENERATED_DIR}"
        COMMAND "${SLANGC_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/shaders/planet.slang"
                -target spirv -entry vertexMain -stage vertex -fvk-use-entrypoint-name
                -matrix-layout-column-major -O2 -o "${VF_VERTEX_SPV}"
        COMMAND "${SLANGC_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/shaders/planet.slang"
                -target spirv -entry fragmentMain -stage fragment -fvk-use-entrypoint-name
                -matrix-layout-column-major -O2 -o "${VF_FRAGMENT_SPV}"
        COMMAND "${SLANGC_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/shaders/sky.slang"
                -target spirv -entry skyVertexMain -stage vertex -fvk-use-entrypoint-name
                -matrix-layout-column-major -O2 -o "${VF_SKY_VERTEX_SPV}"
        COMMAND "${SLANGC_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/shaders/sky.slang"
                -target spirv -entry skyFragmentMain -stage fragment -fvk-use-entrypoint-name
                -matrix-layout-column-major -O2 -o "${VF_SKY_FRAGMENT_SPV}"
        COMMAND "${SLANGC_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/shaders/shadow.slang"
                -target spirv -entry shadowVertexMain -stage vertex -fvk-use-entrypoint-name
                -matrix-layout-column-major -O2 -o "${VF_SHADOW_VERTEX_SPV}"
        DEPENDS
            "${CMAKE_CURRENT_SOURCE_DIR}/shaders/planet.slang"
            "${CMAKE_CURRENT_SOURCE_DIR}/shaders/sky.slang"
            "${CMAKE_CURRENT_SOURCE_DIR}/shaders/shadow.slang"
        VERBATIM
    )

    add_custom_command(
        OUTPUT "${VF_SHADER_HEADER}"
        COMMAND ${CMAKE_COMMAND}
            "-DVERT=${VF_VERTEX_SPV}"
            "-DFRAG=${VF_FRAGMENT_SPV}"
            "-DSKY_VERT=${VF_SKY_VERTEX_SPV}"
            "-DSKY_FRAG=${VF_SKY_FRAGMENT_SPV}"
            "-DSHADOW_VERT=${VF_SHADOW_VERTEX_SPV}"
            "-DOUT=${VF_SHADER_HEADER}"
            -P "${CMAKE_CURRENT_SOURCE_DIR}/cmake/EmbedShaders.cmake"
        DEPENDS
            "${VF_VERTEX_SPV}"
            "${VF_FRAGMENT_SPV}"
            "${VF_SKY_VERTEX_SPV}"
            "${VF_SKY_FRAGMENT_SPV}"
            "${VF_SHADOW_VERTEX_SPV}"
            "${CMAKE_CURRENT_SOURCE_DIR}/cmake/EmbedShaders.cmake"
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

    add_executable(vf_planet_physics_tests tests/PlanetPhysicsTests.cpp)
    target_link_libraries(vf_planet_physics_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_planet_physics_tests COMMAND vf_planet_physics_tests)

    add_executable(vf_camera_input_tests tests/CameraInputTests.cpp)
    target_link_libraries(vf_camera_input_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_camera_input_tests COMMAND vf_camera_input_tests)

    add_executable(vf_collision_geometry_tests tests/CollisionGeometryTests.cpp)
    target_link_libraries(vf_collision_geometry_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_collision_geometry_tests COMMAND vf_collision_geometry_tests)

    add_executable(vf_convex_hull_tests tests/ConvexHullTests.cpp)
    target_link_libraries(vf_convex_hull_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_convex_hull_tests COMMAND vf_convex_hull_tests)

    add_executable(vf_gjk_epa_tests tests/GjkEpaTests.cpp)
    target_link_libraries(vf_gjk_epa_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_gjk_epa_tests COMMAND vf_gjk_epa_tests)

    add_executable(vf_contact_solver_tests tests/ContactSolverTests.cpp)
    target_link_libraries(vf_contact_solver_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_contact_solver_tests COMMAND vf_contact_solver_tests)

    add_executable(vf_gas_chamber_tests tests/GasChamberTests.cpp)
    target_link_libraries(vf_gas_chamber_tests PRIVATE vf_engine)
    add_test(NAME vf_gas_chamber_tests COMMAND vf_gas_chamber_tests)

    add_executable(vf_mechanics_tests tests/MechanicsTests.cpp)
    target_link_libraries(vf_mechanics_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_mechanics_tests COMMAND vf_mechanics_tests)

    add_executable(vf_physics_mesh_tests tests/PhysicsMeshTests.cpp)
    target_link_libraries(vf_physics_mesh_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_physics_mesh_tests COMMAND vf_physics_mesh_tests)

    add_executable(vf_celestial_system_tests tests/CelestialSystemTests.cpp)
    target_link_libraries(vf_celestial_system_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_celestial_system_tests COMMAND vf_celestial_system_tests)

    add_executable(vf_spectral_optics_tests tests/SpectralOpticsTests.cpp)
    target_link_libraries(vf_spectral_optics_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_spectral_optics_tests COMMAND vf_spectral_optics_tests)

    add_executable(vf_electromagnetic_radiation_tests tests/ElectromagneticRadiationTests.cpp)
    target_link_libraries(vf_electromagnetic_radiation_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_electromagnetic_radiation_tests COMMAND vf_electromagnetic_radiation_tests)

    add_executable(vf_planet_render_batch_tests tests/PlanetRenderBatchTests.cpp)
    target_link_libraries(vf_planet_render_batch_tests PRIVATE vf_engine glm::glm)
    add_test(NAME vf_planet_render_batch_tests COMMAND vf_planet_render_batch_tests)

    if(VF_BUILD_RUNTIME)
        add_executable(vf_shader_contract_tests
            tests/ShaderContractTests.cpp
            "${VF_SHADER_HEADER}"
        )
        add_dependencies(vf_shader_contract_tests vf_shaders)
        target_include_directories(vf_shader_contract_tests PRIVATE "${VF_GENERATED_DIR}")
        add_test(NAME vf_shader_contract_tests COMMAND vf_shader_contract_tests)
    endif()
endif()
