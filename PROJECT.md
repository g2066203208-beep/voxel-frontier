# Voxel Frontier — Native Engine Roadmap

## Core vision — CURRENT

Voxel Frontier is a native C++23 exploration game with finite spherical planets inside an effectively unbounded procedurally generated universe.

Non-negotiable world rules:
- Every planet has finite physical size and a real spherical surface.
- The player can walk continuously around a planet with no world-edge seam.
- Local gravity points toward the active planet's center.
- The player can climb to high altitude, leave the atmosphere, enter space, and later land again without a loading-screen world swap.
- Celestial bodies seen in the sky are real world objects, not decorative skybox images.
- The universe is generated deterministically from coordinates/seeds, so an effectively unbounded number of stars and planets can exist without being loaded simultaneously.
- Distant celestial bodies use progressively cheaper representations; physical terrain/details only stream when needed.
- The renderer must support extreme scale while keeping CPU/GPU/memory cost bounded by the local visibility/LOD budget rather than by total universe size.

## Spatial architecture

Use hierarchical reference frames instead of one giant float coordinate system:

Universe -> Star System -> Planet Local Frame -> Surface Patch -> Voxel/Terrain Cell

- Universe/system positions use 64-bit integer or double-precision coordinates.
- Rendering uses camera-relative/local-origin coordinates to keep GPU float precision stable.
- Rebase/switch local frames seamlessly as the player travels between planets.
- Planet orbital/rotation state is analytical and deterministic; inactive systems do not require full simulation.

## Planet representation

Production direction: cube-sphere + six face quadtrees / clipmap-style LOD.

Each planet:
- has six logical cube faces projected onto a sphere;
- maintains hierarchical surface patches;
- refines patches near the camera and collapses distant patches;
- keeps seam-safe adjacency across cube-face boundaries;
- supports high-detail deformable/voxel terrain only around the player;
- supports low-detail radial/height or procedural representations at medium distance;
- collapses to very cheap planetary proxy/impostor geometry at orbital/interplanetary distance.

This avoids loading or meshing an entire planet while preserving a real spherical surface.

## Multi-scale rendering

Target representation ladder:

1. Foot-scale / local terrain
   - deformable voxel/SDF or dense terrain patches
   - collision, caves, resources, player edits
2. Surface / regional distance
   - simplified mesh patches generated from the same deterministic planet function
   - aggressive geometric LOD
3. Orbital distance
   - low-poly sphere/cube-sphere proxy + procedural material/normal data
4. Interplanetary distance
   - tiny proxy / billboard / analytical sphere with atmosphere halo
5. Stellar / deep-space distance
   - point/cluster/catalog representation

All levels describe the same persistent planet identity and parameters. A distant proxy must transition continuously into the real planet as the player approaches.

## Visibility/performance strategy

- CPU coarse culling by hierarchical spatial cells / star-system bounds.
- GPU frustum and optional Hi-Z occlusion culling for local scene content.
- Multi-draw indirect / GPU-generated draw lists for large patch counts.
- Mesh/task shader path where supported and measured beneficial; conventional indexed fallback remains available.
- Distant planets/stars are batched into tiny GPU buffers and do not own full terrain meshes.
- Asynchronous streaming/generation jobs with strict per-frame CPU, upload, and memory budgets.
- Never scale cost with the theoretical number of planets in the universe.

## Seamless atmosphere and space transition

There is no separate 'planet level' and 'space level'.

- Player position is always represented in the hierarchy of reference frames.
- Gravity magnitude/direction is evaluated from nearby celestial bodies and transitions smoothly.
- Atmosphere rendering is based on planet radius, altitude and sun direction.
- Terrain LOD progressively collapses as altitude increases.
- Nearby planet is kept in high/medium LOD; remote planets remain proxies.
- Crossing the atmosphere boundary does not teleport, reload, or change maps.

## Engine foundation

### Foundation completed
- C++23 native runtime
- SDL3 thin desktop platform layer
- Vulkan native renderer bootstrap
- deterministic seeded chunk/world foundation
- correct negative coordinate conversion
- dirty owner/neighbor invalidation
- Linux/Windows native CI and executable production
- VS Code/CMake one-click development setup

### Engine milestone 1 — first playable spherical planet
- hierarchical universe/system/planet/local coordinate frames
- camera-relative rendering origin
- finite procedural planet definition (radius, seed, atmosphere, gravity)
- cube-sphere six-face patch topology
- quadtree patch LOD and seam-safe neighbors
- visible spherical terrain from ground to orbit
- first-person movement with radial up/gravity
- walk continuously around the globe
- altitude-driven LOD transition
- leave surface into space without scene load
- at least one second real celestial body visible as a cheap proxy
- CPU/GPU profiler overlay and frame budgets

### Engine milestone 2 — real interplanetary travel
- multiple finite planets in one star system
- physical/analytical orbits and rotation
- deep-space camera/reference-frame transitions
- distant-body proxy renderer
- approach transition from proxy -> planetary LOD -> local terrain
- seamless landing on another planet
- deterministic celestial catalog
- save/load of planet edits independent of procedural base terrain

### Engine milestone 3 — effectively unbounded universe
- deterministic star-sector generation
- hierarchical sector streaming
- unloaded systems represented only by compact metadata/seeds
- galaxy/starfield LOD aggregation
- long-distance travel/warp design without loading every intermediate system
- persistent discoveries and player modifications

## Gameplay systems

After spherical-planet traversal is technically stable:
1. terrain deformation and resource extraction
2. inventory and item stacks
3. crafting and tools
4. survival / oxygen / power / environment
5. base building
6. vehicles and traversal machines
7. creatures and AI
8. progression and research
9. procedural structures and anomalies
10. multiplayer authoritative server

## Tooling

- custom profiler/debug overlay
- planet/patch/LOD visualizer
- coordinate-frame visualizer
- procedural seed inspector
- content compiler
- shader compiler/cache
- asset database
- automated precision/LOD/seam/performance regression tests

The old browser build is retained only as a historical prototype and is not the production architecture.
