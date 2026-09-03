cmake_minimum_required(VERSION 3.22)
project(voxel_frontier_engine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(vf_core STATIC
  src/Engine.cpp
  src/Mesher.cpp
  src/Raycast.cpp
)

target_include_directories(vf_core PUBLIC include)
target_compile_options(vf_core PRIVATE -Wall -Wextra -Wpedantic)

if(EMSCRIPTEN)
  target_compile_options(vf_core PRIVATE -O3 -msimd128)

  add_executable(vf_engine src/wasm_api.cpp)
  target_link_libraries(vf_engine PRIVATE vf_core)
  target_compile_options(vf_engine PRIVATE -O3 -msimd128)
  target_link_options(vf_engine PRIVATE
    -O3
    -msimd128
    -sMODULARIZE=1
    -sEXPORT_ES6=1
    -sENVIRONMENT=web,worker
    -sALLOW_MEMORY_GROWTH=1
    -sFILESYSTEM=0
    -sMALLOC=emmalloc
    "-sEXPORTED_FUNCTIONS=['_vf_engine_abi_version','_vf_terrain_height','_vf_fill_chunk','_vf_build_greedy_mesh','_vf_mesh_vertex_ptr','_vf_mesh_vertex_count','_vf_mesh_vertex_stride','_vf_mesh_index_ptr','_vf_mesh_index_count','_vf_raycast','_vf_hit_x','_vf_hit_y','_vf_hit_z','_vf_hit_normal_x','_vf_hit_normal_y','_vf_hit_normal_z','_vf_hit_distance','_vf_hit_block','_malloc','_free']"
    "-sEXPORTED_RUNTIME_METHODS=['HEAPU8','HEAPU32','HEAPF32']"
  )
  set_target_properties(vf_engine PROPERTIES OUTPUT_NAME "vf_engine" SUFFIX ".js")
else()
  enable_testing()
  add_executable(vf_engine_tests tests/engine_tests.cpp)
  target_link_libraries(vf_engine_tests PRIVATE vf_core)
  target_compile_options(vf_engine_tests PRIVATE -O3 -Wall -Wextra -Wpedantic)
  add_test(NAME vf_engine_tests COMMAND vf_engine_tests)
endif()
