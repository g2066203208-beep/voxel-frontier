# Voxel Frontier

Voxel Frontier is an original native PC sandbox/RPG built around finite spherical planets, seamless ground-to-space traversal, procedural triangle-surface terrain, and a shared physically based simulation.

## Production stack

- C++23 for engine and gameplay
- Vulkan explicit rendering
- SDL3 only for platform/window/input/audio access
- Slang -> SPIR-V shaders
- CMake native builds
- GitHub Actions Linux correctness gates, Windows executable build/tests, and real Vulkan visual regression

There is no production browser, TypeScript, Three.js, WebGPU, WebAssembly, Unity, Unreal, or Godot runtime path in this repository. Historical browser/WASM prototypes were removed after the native migration became authoritative.

## World architecture

The rendered natural world is not a visible block-voxel surface.

```text
Universe
 -> star system
 -> finite spherical planet
 -> hierarchical procedural surface patches
 -> explicit indexed triangle geometry
 -> Vulkan rendering

Local caves / overhangs / excavation / destructive edits
 -> sparse local SDF or density edits
 -> seam-safe local surface extraction
 -> triangle mesh
```

Untouched planetary terrain remains procedural and deterministic. Expensive volumetric data is reserved for places where true 3D topology is required rather than filling the whole planet with voxels.

See `PROJECT.md` and `docs/TERRAIN_ARCHITECTURE.md`.

## Physics architecture

The project owns a custom fixed-step physics stack. The current runtime contains:

- 120 Hz fixed simulation stepping
- rigid-body mass, inertia, momentum, force, torque, and impulses
- radial planetary gravity plus planet-centered local physics frames
- atmosphere temperature, pressure, density, wind, and gust state
- sweep-and-prune broadphase
- sphere, oriented box, capsule, and general convex collision support
- GJK/EPA narrowphase and persistent contact solving
- friction, restitution, sleeping, and stable terrain contact
- distance, spring-damper, hinge, motor, and gear constraints
- break force / break torque limits
- aerodynamic body forces and local aerodynamic surfaces with angle-of-attack/stall behavior
- shallow-water and buoyancy/drag foundations
- ideal-gas chamber / pneumatic foundations
- XPBD rope foundations
- radial-gravity capsule character controller with slopes, steps, and jumping
- celestial spin, atmosphere/climate coupling, and bounded Newtonian N-body orbital propagation
- Keplerian orbital elements -> Cartesian inertial initial-state conversion for authored celestial systems

Old tree-only physics demos and standalone in-world physics playground code are not production architecture. Vegetation, fracture, destruction, machines, and vehicles are expected to use the shared generic rigid-body/material/constraint systems.

See `docs/PHYSICS_ARCHITECTURE.md` and `docs/CELESTIAL_DYNAMICS_REFERENCES.md`.

## Repository layout

```text
.github/workflows/    permanent native CI / visual regression
.vscode/              native CMake launch/tasks/settings
native/
  include/vf/         public engine interfaces
  src/                native engine/runtime implementation
  shaders/            Slang shaders
  tests/              Release-active regression tests
docs/                 authoritative architecture / evidence documents
scripts/              Windows bootstrap/run helpers
PROJECT.md             product and technical direction
```

## Windows build

```powershell
cmake -S native -B build/native -A x64 -DVF_BUILD_RUNTIME=ON -DVF_BUILD_TESTS=ON
cmake --build build/native --config Release --parallel
ctest --test-dir build/native -C Release --output-on-failure
```

The executable is `voxel_frontier.exe`.

## CI evidence

Pull requests targeting `main` run native correctness checks. Changes under `native/**` also run the real Vulkan visual regression path, which builds the Linux runtime against Lavapipe/Xvfb and uploads ground, traversal, and aerial framebuffer captures as workflow artifacts. This keeps visual proof attached to production changes instead of relying on one-off experiment workflows.