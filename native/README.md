# Voxel Frontier Native Engine

Voxel Frontier is moving to a fully custom native desktop engine. No Unreal Engine, Unity, Godot, Three.js or browser runtime is part of the production path.

## Production stack

- C++23 game/engine code
- SDL 3.4.14 only as a thin OS/window/input/gamepad/audio platform layer
- Vulkan 1.4 headers + volk 1.4.350 as the explicit GPU API/loader layer
- CMake build system
- Direct native Windows executable

SDL is not used as a scene, world, physics, gameplay or rendering engine. Those systems belong to Voxel Frontier.

## Engine ownership

The project will implement its own:

- engine loop and timing
- memory arenas and allocators
- task/job scheduler
- streamed region/chunk world
- voxel compression and palettes
- terrain/biome generation
- greedy/meshlet voxel meshing
- renderer and resource lifetime management
- GPU-driven culling and indirect drawing
- player controller and collision
- physics needed by gameplay
- entity/component model
- AI/pathfinding
- inventory/crafting/combat/RPG systems
- save format and async streaming
- networking protocol and authoritative server
- tooling/profiling/debug overlays required by the project

## Current milestone

The first native milestone establishes a deterministic, testable foundation before gameplay content is migrated:

1. 32×32×32 contiguous chunks
2. correct negative world/chunk coordinate mapping
3. dirty-chunk and neighbor invalidation
4. deterministic seeded terrain
5. SDL3 native window lifecycle
6. Vulkan 1.3+ device/surface/swapchain path with Vulkan 1.4 preferred
7. explicit synchronization and direct swapchain presentation
8. Linux core tests + Windows runtime compilation in GitHub Actions

The next milestone adds the real voxel render path: asynchronous chunk jobs, greedy meshing, GPU vertex/index buffers, camera matrices, depth buffer, shader pipeline, frustum culling and first-person movement.

## Windows build

From the repository root:

```powershell
cmake -S native -B build/native -A x64 -DVF_BUILD_RUNTIME=ON -DVF_BUILD_TESTS=ON
cmake --build build/native --config Release --parallel
ctest --test-dir build/native -C Release --output-on-failure
```

The executable is named `voxel_frontier.exe`.
