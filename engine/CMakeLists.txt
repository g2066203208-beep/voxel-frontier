cmake_minimum_required(VERSION 3.22)
project(voxel_frontier_engine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(vf_engine
  src/Engine.cpp
  src/wasm_api.cpp
)

target_include_directories(vf_engine PRIVATE include)

target_compile_options(vf_engine PRIVATE
  -Wall
  -Wextra
  -Wpedantic
)

if(EMSCRIPTEN)
  target_compile_options(vf_engine PRIVATE
    -O3
    -msimd128
  )

  target_link_options(vf_engine PRIVATE
    -O3
    -msimd128
    -sMODULARIZE=1
    -sEXPORT_ES6=1
    -sENVIRONMENT=web,worker
    -sALLOW_MEMORY_GROWTH=1
    -sFILESYSTEM=0
    "-sEXPORTED_FUNCTIONS=['_vf_engine_abi_version','_vf_terrain_height','_vf_fill_chunk','_malloc','_free']"
    "-sEXPORTED_RUNTIME_METHODS=['HEAPU8']"
  )

  set_target_properties(vf_engine PROPERTIES
    OUTPUT_NAME "vf_engine"
    SUFFIX ".js"
  )
endif()
