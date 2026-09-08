cmake_minimum_required(VERSION 3.28)
project(VoxelFrontierFoundation LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)

set(TF_BUILD_BENCHMARKS OFF CACHE BOOL "" FORCE)
set(TF_BUILD_PROFILER OFF CACHE BOOL "" FORCE)
set(TF_BUILD_CUDA OFF CACHE BOOL "" FORCE)
set(TF_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(TF_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(TF_BUILD_MODULES OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    Taskflow
    GIT_REPOSITORY https://github.com/taskflow/taskflow.git
    GIT_TAG v4.1.0
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(Taskflow)

set(ENTT_INSTALL OFF CACHE BOOL "" FORCE)
set(ENTT_BUILD_TESTING OFF CACHE BOOL "" FORCE)
set(ENTT_BUILD_TESTBED OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    EnTT
    GIT_REPOSITORY https://github.com/skypjack/entt.git
    GIT_TAG v4.0.0
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(EnTT)

add_executable(vf_engine_foundation_tests
    ../tests/EngineFoundationTests.cpp
)
target_include_directories(vf_engine_foundation_tests PRIVATE ../include)
target_link_libraries(vf_engine_foundation_tests PRIVATE Taskflow::Taskflow EnTT::EnTT)
target_compile_features(vf_engine_foundation_tests PRIVATE cxx_std_23)

if(MSVC)
    target_compile_options(vf_engine_foundation_tests PRIVATE /W4 /permissive- /EHsc)
else()
    target_compile_options(vf_engine_foundation_tests PRIVATE -Wall -Wextra -Wpedantic)
endif()

enable_testing()
add_test(NAME vf_engine_foundation_tests COMMAND vf_engine_foundation_tests)
