#!/usr/bin/env python3
from pathlib import Path

cmake = Path('native/CMakeLists.txt')
text = cmake.read_text(encoding='utf-8')
marker = 'R24_ENGINE_FOUNDATION_V1'
if marker in text:
    print('R24 engine foundation already integrated')
    raise SystemExit(0)

anchor = '''FetchContent_MakeAvailable(glm)\n\nadd_library(vf_engine STATIC'''
insert = '''FetchContent_MakeAvailable(glm)\n\n# R24_ENGINE_FOUNDATION_V1: production C++ task graph + data-oriented ECS foundation.\nset(TF_BUILD_BENCHMARKS OFF CACHE BOOL \"\" FORCE)\nset(TF_BUILD_PROFILER OFF CACHE BOOL \"\" FORCE)\nset(TF_BUILD_CUDA OFF CACHE BOOL \"\" FORCE)\nset(TF_BUILD_TESTS OFF CACHE BOOL \"\" FORCE)\nset(TF_BUILD_EXAMPLES OFF CACHE BOOL \"\" FORCE)\nset(TF_BUILD_MODULES OFF CACHE BOOL \"\" FORCE)\nFetchContent_Declare(\n    Taskflow\n    GIT_REPOSITORY https://github.com/taskflow/taskflow.git\n    GIT_TAG v4.1.0\n    GIT_SHALLOW TRUE\n)\nFetchContent_MakeAvailable(Taskflow)\n\nset(ENTT_INSTALL OFF CACHE BOOL \"\" FORCE)\nset(ENTT_BUILD_TESTING OFF CACHE BOOL \"\" FORCE)\nset(ENTT_BUILD_TESTBED OFF CACHE BOOL \"\" FORCE)\nFetchContent_Declare(\n    EnTT\n    GIT_REPOSITORY https://github.com/skypjack/entt.git\n    GIT_TAG v4.0.0\n    GIT_SHALLOW TRUE\n)\nFetchContent_MakeAvailable(EnTT)\n\nadd_library(vf_engine STATIC'''
if anchor not in text:
    raise SystemExit('dependency anchor not found')
text = text.replace(anchor, insert, 1)

old_link = 'target_link_libraries(vf_engine PUBLIC glm::glm)'
new_link = 'target_link_libraries(vf_engine PUBLIC glm::glm Taskflow::Taskflow EnTT::EnTT)'
if old_link not in text:
    raise SystemExit('vf_engine link anchor not found')
text = text.replace(old_link, new_link, 1)

old_tests = '''    add_executable(vf_static_mesh_upload_scheduler_tests tests/StaticMeshUploadSchedulerTests.cpp)\n    target_link_libraries(vf_static_mesh_upload_scheduler_tests PRIVATE vf_engine)\n    add_test(NAME vf_static_mesh_upload_scheduler_tests COMMAND vf_static_mesh_upload_scheduler_tests)\n\n    if(VF_BUILD_RUNTIME)'''
new_tests = '''    add_executable(vf_static_mesh_upload_scheduler_tests tests/StaticMeshUploadSchedulerTests.cpp)\n    target_link_libraries(vf_static_mesh_upload_scheduler_tests PRIVATE vf_engine)\n    add_test(NAME vf_static_mesh_upload_scheduler_tests COMMAND vf_static_mesh_upload_scheduler_tests)\n\n    add_executable(vf_engine_foundation_tests tests/EngineFoundationTests.cpp)\n    target_link_libraries(vf_engine_foundation_tests PRIVATE vf_engine Taskflow::Taskflow EnTT::EnTT)\n    add_test(NAME vf_engine_foundation_tests COMMAND vf_engine_foundation_tests)\n\n    if(VF_BUILD_RUNTIME)'''
if old_tests not in text:
    raise SystemExit('test anchor not found')
text = text.replace(old_tests, new_tests, 1)

cmake.write_text(text, encoding='utf-8')
print('R24 engine foundation integrated into native build')
