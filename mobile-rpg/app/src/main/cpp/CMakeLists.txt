cmake_minimum_required(VERSION 3.22.1)
project(Faithbound LANGUAGES C CXX)

add_library(native_app_glue STATIC
    ${ANDROID_NDK}/sources/android/native_app_glue/android_native_app_glue.c)
target_include_directories(native_app_glue PUBLIC
    ${ANDROID_NDK}/sources/android/native_app_glue)

add_library(faithbound SHARED game.cpp)

target_compile_features(faithbound PRIVATE cxx_std_20)
target_compile_options(faithbound PRIVATE
    -Wall -Wextra -Wno-unused-parameter
    $<$<CONFIG:Release>:-O3;-flto>
    $<$<CONFIG:Debug>:-O2>)

target_link_options(faithbound PRIVATE
    "-uANativeActivity_onCreate"
    $<$<CONFIG:Release>:-flto>)

target_link_libraries(faithbound
    native_app_glue
    android
    jnigraphics
    log
    EGL
    GLESv3)
