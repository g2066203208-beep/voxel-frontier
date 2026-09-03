# Voxel Frontier — Smooth Planet Terrain Architecture

## Decision

The production terrain is **not block-rendered voxel terrain**.

The visible world is always rendered as explicit GPU geometry: vertices + indexed triangles / meshlets.

The authoritative terrain representation is hybrid:

1. **Planet-scale base surface** — analytical/procedural sphere/ellipsoid + displacement, evaluated through hierarchical surface patches / clipmaps.
2. **Local volumetric detail** — sparse signed-distance/density fields only where true 3D topology is needed (caves, overhangs, excavation, filling, player deformation).
3. **Surface extraction** — local SDF/density data is converted to smooth triangle meshes; no visible cubes.
4. **Persistent edits** — store sparse edit operations / sparse field bricks, never a dense voxel grid for an entire planet.

## Why not pure polygon mesh as world truth?

A pure surface triangle mesh is excellent for rendering and planet-scale LOD, but arbitrary digging, tunnels, arches, undercuts and terrain addition require dynamic topology surgery, spatial remeshing and robust collision updates. That is substantially harder to make stable than editing a local implicit field.

Therefore the mesh is the **rendered result**, not the only source of truth for deformable terrain.

## Why not block voxels?

A voxel can be a scalar sample (density/SDF), not a visible cube. Astroneer publicly describes its terrain this way: 3D voxels store density, while the game renders a smooth surface rather than blocks.

Our implementation follows the smooth interpretation only.

## Representation ladder

### Interplanetary / orbital
- analytical planet metadata
- very low-cost sphere/ellipsoid proxy
- atmosphere proxy
- no local SDF allocation

### Regional / planetary surface
- cube-sphere or ellipsoidal surface patches
- quadtree/clipmap LOD driven by screen-space error
- shared regular patch topology where possible
- GPU procedural displacement from deterministic terrain functions
- indexed triangle or mesh-shader output

### Local high-detail surface
- high-resolution surface patches
- collision mesh / height query
- no dense global volume

### Local 3D/deformable zones
- sparse SDF/density bricks only near caves, deformation, resources or other true volumetric features
- narrow-band storage where practical
- smooth surface extraction using Dual Contouring / Marching Cubes family
- multiresolution transitions must be crack-free (Transvoxel-style transition cells or equivalent seam strategy)

## Meshing preference

For the first playable:
- planet surface: regular indexed patch mesh generated from procedural displacement;
- local volumetric terrain: start with a correct smooth isosurface extractor;
- evaluate Dual Contouring as the preferred long-term path for better feature preservation and potentially more compact topology;
- keep Marching Cubes as a simpler fallback/reference implementation;
- do not use Greedy Meshing for the production smooth terrain path because it is intended for axis-aligned/block surfaces.

## Sparse field strategy

Untouched terrain should be reproducible from `(planetSeed, position)` and occupy no persistent per-voxel storage.

Only deltas need persistence:
- brush CSG operations,
- deformation stamps,
- sparse field bricks,
- cave/resource metadata when not purely procedural.

A future GPU-friendly sparse hierarchy may borrow ideas from OpenVDB/NanoVDB, but the runtime format should be purpose-built and benchmarked instead of importing a large dependency by default.

## Rendering strategy

- camera-relative GPU coordinates;
- hierarchical double/64-bit CPU reference frames;
- constant/reused patch index topology;
- frustum + horizon culling;
- GPU-driven indirect drawing where measurements justify it;
- task/mesh shader path where supported, with indexed fallback;
- far geometry complexity proportional to projected screen size, not physical planet detail;
- strict CPU/GPU/upload/memory budgets per frame.

## Non-negotiable visual rule

The player must never see a block-grid aesthetic unless a specific gameplay object intentionally uses it. Natural terrain must read as a continuous sculptable surface from ground level to orbit.
