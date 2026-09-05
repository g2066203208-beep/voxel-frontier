# Voxel Frontier — Production Roadmap

## Core vision

Voxel Frontier is a native C++23 sandbox/RPG with finite spherical planets in a procedurally generated, effectively unbounded universe.

Non-negotiable rules:

- planets have finite physical size and real spherical surfaces;
- natural terrain is smooth triangle geometry, not visible block voxels;
- the player can traverse around a planet and move from ground to atmosphere to space without a loading-screen world swap;
- local gravity points toward the relevant celestial body;
- celestial bodies are world objects, not skybox decorations;
- universe generation is deterministic from coordinates/seeds;
- cost is bounded by local visibility/LOD/physics activity, not theoretical universe size;
- terrain editing uses sparse local volumetric/SDF data only where 3D topology is actually required.

## Authoritative production stack

- C++23
- Vulkan explicit renderer
- SDL3 thin platform layer
- Slang -> SPIR-V shaders
- CMake
- native Windows executable
- Linux + Windows CI

There is no production TypeScript/Three.js/WebGPU/WebAssembly/browser engine path anymore.

## Spatial and terrain architecture

```text
Universe
 -> Star System
 -> Planet reference frame
 -> Surface patch
 -> Local terrain/deformation field
```

Untouched planetary terrain:

```text
procedural planet function
 -> hierarchical cube-sphere / clipmap-friendly surface patches
 -> explicit indexed triangle geometry / meshlets
 -> Vulkan
```

Caves, overhangs, excavation and filling:

```text
procedural base
 + sparse local SDF/density edits
 -> local surface extraction
 -> seam-safe triangle mesh
```

See `docs/TERRAIN_ARCHITECTURE.md`.

## Multi-scale rendering

1. local: detailed surface mesh + sparse edited volumetric regions;
2. regional: procedural LOD surface patches;
3. orbital: low-cost planet proxy;
4. interplanetary: tiny analytical/proxy body;
5. stellar/deep-space: batched catalog/cluster representation.

Rendering work should use camera-relative coordinates, horizon/frustum culling, measured Hi-Z/occlusion where useful, indirect draw generation and mesh/task shaders only where hardware measurements justify them.

## Physics vision

The world is one coupled physical graph:

```text
planet gravity / atmosphere / weather / water
                  |
                  v
rigid bodies -> contacts -> constraints -> machines
     |              |            |
     |              |            +-> motors / gears / springs / joints
     |              +-> friction / impacts / structural loads
     +-> aero / buoyancy / fluid drag / pressure forces
```

Already implemented foundations:

- 120 Hz fixed-step rigid-body simulation;
- mass, inertia, momentum, force, torque and impulses;
- radial planetary gravity;
- atmosphere temperature/pressure/density/wind;
- sweep-and-prune broadphase;
- sphere / box / capsule / convex collision geometry and GJK/EPA support;
- persistent contact solving with friction/restitution;
- springs, distance constraints, hinges, motors, gears and break limits;
- local aerodynamic surfaces with angle-of-attack/stall behavior;
- shallow-water transport and buoyancy foundations;
- ideal-gas chamber foundations;
- XPBD rope physics;
- capsule character controller with radial gravity, slopes, steps and jumping.

Special-case demo systems are not production architecture. The obsolete tree-only simulator and standalone physics playground have been removed from the authoritative source tree; future vegetation/destruction must use generic material/fracture plus rigid-body systems.

See `docs/PHYSICS_ARCHITECTURE.md` for the lower-level solver design.

## Near-term technical order

1. finish and harden shape-aware contacts, manifold persistence and CCD/shape casts;
2. eliminate terrain-streaming GPU stalls and move toward persistent/double-buffered terrain resources;
3. hierarchical patch/clipmap terrain streaming with seam-safe incremental updates;
4. authoritative rendered water + multipoint hull buoyancy/torque;
5. gas chambers connected to real compartments, flooding and variable buoyancy;
6. generic material cutting/fracture -> rigid-body fragments, without object-specific physics hacks;
7. reusable instanced rigid-body rendering instead of CPU rebuilding debug geometry;
8. slider/ball/fixed/6-DOF constraints, clutch/differential, wheel/suspension/tire models;
9. propellers/rotors/control surfaces and vehicle/aircraft physical systems;
10. local weather cells, rainfall/catchments and physically coupled environmental gameplay.

## World milestones

### Spherical planet runtime

Current runtime already has a finite smooth spherical planet, radial movement, a physical capsule character controller, camera-relative Vulkan rendering, ground-to-space altitude traversal and multiple real celestial bodies. Remaining work is hierarchical patch LOD, seam-safe streaming, production water and large-scale world content.

### Sculptable terrain

- sparse local SDF/density bricks;
- persistent CSG/deformation deltas;
- Dual Contouring / Marching Cubes family evaluation;
- crack-free multiresolution transitions;
- caves/overhangs/excavation/filling;
- localized collision remeshing.

### Interplanetary travel

- multiple finite planets;
- analytical orbit/rotation state;
- reference-frame transitions;
- proxy -> planet LOD -> local terrain approach;
- seamless landing;
- persistent edits independent of procedural base terrain.

### Effectively unbounded universe

- deterministic star-sector generation;
- hierarchical sector streaming;
- compact unloaded-system metadata;
- long-distance traversal/warp design;
- persistent discoveries and edits.

## Gameplay after technical foundations

- terrain/resource interaction;
- inventory/crafting/tools;
- survival/oxygen/power/environment;
- base construction;
- machines and vehicles;
- creatures/NPC AI;
- progression/research;
- structures/anomalies;
- authoritative multiplayer.

## Mandatory test evidence

Every runtime test round must leave reviewable evidence in the repository and must show the user the screenshots even when the visual result is poor or the round fails.

- Use only real framebuffer captures from the tested Vulkan runtime. Never use generated/concept images as test evidence.
- Store each round under `docs/evidence/<round-or-commit>/` with the exact screenshots, capture metadata and relevant runtime/Vulkan logs.
- Terrain/geomorphology work must capture the actual landform(s) under test from a camera that makes the morphology readable; failed/flat/bad framing is still preserved rather than hidden.
- Celestial-motion work must capture a time sequence or before/after frames from a fixed camera so movement can be visually verified; a single Sun/Moon frame is not motion evidence.
- Evidence is part of the test deliverable, not an optional presentation step. A code result without the requested screenshots is incomplete.
- CI artifacts may supplement repository evidence, but artifact-only screenshots do not replace committed evidence for a test round the user is expected to review.

See `docs/evidence/README.md` for the evidence layout.

## Repository rule

Keep only the authoritative production path and documentation in `main`. Superseded experiments belong in Git history or dedicated archival tags/branches, not as dead parallel engines in the working tree.
