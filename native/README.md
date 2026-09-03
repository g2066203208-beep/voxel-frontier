# Voxel Frontier Native Engine

`native/` is the only production engine/runtime path.

## Stack

- C++23
- SDL3 as a thin platform layer
- Vulkan + volk + Vulkan-Headers
- Slang compiled to embedded SPIR-V at build time
- GLM for math
- CMake

No browser runtime or third-party scene/physics engine is part of production.

## Current subsystems

```text
include/vf + src/
  gameplay/    physics playground and gameplay-side physical systems
  physics/     rigid bodies, broadphase, constraints, aero, water, gas, trees, collision geometry
  platform/    SDL3 window/input platform adapter
  player/      spherical-planet camera/controller (temporary non-rigidbody player)
  render/      Vulkan renderer and debug/physics geometry
  world/       procedural spherical triangle-surface planet
```

The old flat voxel `Chunk/World/Engine` bootstrap has been removed. Natural terrain is now the spherical triangle-surface path described in `../docs/TERRAIN_ARCHITECTURE.md`.

## Collision evolution

The active rigid-body world still uses sphere contacts while collision v3 is integrated. The new `CollisionGeometry` layer is intentionally isolated and regression-tested first:

- sphere, oriented box and capsule shape descriptions
- exact world AABB calculation for those primitives
- support mapping for future GJK/EPA
- sphere/sphere, sphere/box, sphere/capsule and capsule/capsule narrowphase
- 15-axis oriented-box SAT
- contact-manifold data structure with capacity for four contacts

The integration order is deliberate: validate shape geometry first, then replace sphere-only broadphase bounds and body contact generation, then add persistent manifold caching/warm starting, then add general convex GJK/EPA. This follows the same broadphase -> narrowphase -> manifold -> iterative-solver separation used by mature real-time rigid-body engines.

## Build

```powershell
cmake -S native -B build/native -A x64 -DVF_BUILD_RUNTIME=ON -DVF_BUILD_TESTS=ON
cmake --build build/native --config Release --parallel
ctest --test-dir build/native -C Release --output-on-failure
```

Executable: `voxel_frontier.exe`.
