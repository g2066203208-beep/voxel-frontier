# Voxel Frontier

Voxel Frontier is an original native PC sandbox/RPG built around finite spherical planets, seamless ground-to-space traversal, procedural triangle-surface terrain and a shared physically based simulation.

## Production stack

- C++23 for engine and gameplay
- Vulkan 1.4-class explicit rendering path (1.3 minimum runtime path where required)
- SDL3 only for platform/window/input/audio access
- Slang -> embedded SPIR-V shaders
- CMake native builds
- GitHub Actions Linux correctness gates + Windows executable build/tests

There is no production browser, TypeScript, Three.js, WebGPU, WebAssembly, Unity, Unreal or Godot runtime path in this repository anymore. Historical browser/WASM prototypes were removed after the native migration became authoritative.

## World architecture

The rendered natural world is not a block-voxel surface.

```text
Planet
 -> procedural spherical surface patches
 -> explicit vertices / triangle mesh
 -> Vulkan rendering

Local excavations / caves / destructive terrain
 -> sparse local signed-distance data
 -> surface extraction
 -> triangle mesh
```

See `docs/TERRAIN_ARCHITECTURE.md`.

## Physics architecture

The project owns a custom fixed-step physics stack. The current runtime already contains:

- 120 Hz fixed simulation stepping
- rigid-body mass, inertia, momentum, force, torque and impulses
- radial altitude-aware planetary gravity
- sphere contacts, restitution, Coulomb-style friction and sleeping
- sweep-and-prune broadphase
- distance, spring-damper, hinge, motor and gear constraints
- break force / break torque limits
- atmosphere temperature, pressure, density and deterministic wind/gust state
- aerodynamic body forces and local aerodynamic surfaces with angle-of-attack/stall behavior
- shallow-water transport and fluid buoyancy/drag foundations
- ideal-gas chamber / pneumatic foundations
- physically driven tree-hinge fall model
- visible in-world physics playground

Collision v3 adds an isolated, testable shape/narrowphase foundation for sphere, oriented box and capsule primitives, AABB generation, support mapping and 15-axis OBB SAT. General convex GJK/EPA and persistent multi-point manifolds are the next integration layer rather than ad-hoc approximate collision code.

See `docs/PHYSICS_ARCHITECTURE.md`.

## Repository layout

```text
.github/workflows/    native CI only
.vscode/              native CMake launch/tasks/settings
native/
  include/vf/         public engine interfaces
  src/                native engine/runtime implementation
  shaders/            Slang shaders
  tests/              Release-active regression tests
docs/                 authoritative architecture documents
scripts/              Windows bootstrap/run helpers
PROJECT.md             product/technical direction
```

## Windows build

```powershell
cmake -S native -B build/native -A x64 -DVF_BUILD_RUNTIME=ON -DVF_BUILD_TESTS=ON
cmake --build build/native --config Release --parallel
ctest --test-dir build/native -C Release --output-on-failure
```

The executable is `voxel_frontier.exe`.
