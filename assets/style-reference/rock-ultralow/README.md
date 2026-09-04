# Canonical ultra-low-poly rock

This directory is the approved Voxel Frontier low-poly modeling/material reference.

## Geometry

- 12 deliberately authored control vertices
- 20 triangles
- closed convex volume
- deliberately asymmetric silhouette
- broad stable base
- one flat normal per triangle / hard faceting
- no subdivision sphere and no high-poly-to-decimation workflow

## Material

The Slang reference shader demonstrates the intended zero-image-texture procedural stone material:

- base mineral palette;
- broad mineral color variation;
- oblique strata / veins;
- orientation-dependent weathering;
- restrained lichen;
- micro grain;
- subtle edge wear;
- rough directional/hemisphere lighting.

The GLB contains the actual geometry and a portable vertex-color approximation. `VF_rock_ULTRA_20tri_material.slang` is the canonical procedural-material source reference for the engine.

See `docs/ART_DIRECTION_LOW_POLY.md` for the authoritative project-wide rules.
