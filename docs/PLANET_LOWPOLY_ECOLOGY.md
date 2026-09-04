# Voxel Frontier — Low-Poly Planet Ecology

## Visual contract

The natural planet is a continuous displaced surface, not block terrain. "Low-poly" means deliberate polygon planes and silhouettes, not random decimation noise and not visible voxel cubes.

Trees, rocks and terrain are deterministic from `planetSeed`. Random variation is bounded and habitat-aware so a seed always reproduces the same world.

## Terrain

`PlanetSurface.cpp` keeps cube-sphere topology for deterministic planet LOD, but the visible surface is deliberately faceted:

- seamless 3D directional fBm/ridged/basin displacement;
- bounded interior patch jitter while cube-face edges stay exact;
- deterministic alternating quad diagonals to break the repeated grid direction;
- derivative face normals in `planet.slang` for readable low-poly planes;
- the same `planetHeight()` remains authoritative for physics height queries.

Ecology is attached only to high-detail surface meshes (`subdivisionsPerFace >= 24`). The existing low-LOD/test mesh remains terrain-only; the current runtime 64x64 face mesh receives trees and rocks.

## Tree placement

Trees are not uniform random scatter. Candidate directions use a deterministic Fibonacci/golden-angle sequence with seed jitter, then pass:

- elevation-band filter;
- moisture filter;
- pseudo-latitude/elevation temperature filter;
- slope filter;
- low-frequency grove-density mask;
- bounded stochastic acceptance;
- minimum-distance rejection between accepted trees.

This creates groves plus open ground rather than evenly spaced rows or visual confetti.

Each accepted tree varies deterministically in maturity, trunk height/radius, crown scale, branch length/radius, trunk wobble, yaw and a very small lean.

## Tree geometry

The runtime tree generator follows the accepted compact stylized broadleaf/oak direction:

- one heavy 8-sided trunk;
- three short, thick primary limbs;
- aggressive branch taper; no long bare whips;
- each side branch opens one local quad in the trunk surface and stitches its collar directly to the four shared opening vertices;
- branch strips use four-sided rings and quality-aware quad diagonals;
- branch tips terminate inside the canopy;
- six overlapping 20-triangle icosahedral canopy masses form the crown.

The wood is one continuous indexed mesh. It is not a set of intersecting branch cylinders, does not use boolean-union branch solids, and is not created by high-poly remesh then decimation.

## Rock placement and geometry

Rock candidates are filtered by elevation, slope, moisture/dryness and an independent broken-ground field. Accepted rocks use minimum rock-to-rock spacing and an additional tree-footprint exclusion so rocks do not spawn through trunks.

Each rock is a direct low-poly solid:

- 12 vertices / 20 triangles from an icosahedral base;
- non-uniform X/Y/Z scale;
- deterministic per-vertex radial variation;
- flattened lower half and slight ground embed;
- bounded scale, yaw and lean variation.

Every face is intended to contribute to silhouette or lighting.

## Procedural materials

No bitmap texture is required for current natural terrain, bark, foliage or rocks.

To preserve the existing Vulkan vertex ABI, `PlanetVertex::color` stays a `float3`. Debug/celestial meshes continue to use literal `[0,1]` RGB. Primary natural geometry packs a material marker plus local parameters into this existing channel.

`planet.slang` decodes four material families:

### Terrain

- macro/meso/mineral 3D noise;
- moisture + temperature + elevation grass/soil palette;
- slope/elevation rock exposure;
- cold/high-area stone/snow transition;
- matte high-roughness dielectric response.

### Bark

- branch-local circumferential/longitudinal coordinates;
- macro pigment variation;
- longitudinal fibres;
- Voronoi/Worley-style fissures;
- micro breakup;
- restrained specular and high roughness.

The bark pattern follows each branch instead of world vertical.

### Foliage

- body-space procedural variation;
- deep/mid/sunlit greens;
- radial-up-facing lift using the rotating planet frame;
- high roughness to avoid plastic green crown lobes.

### Rock

- macro mineral variation;
- fine grains;
- restrained strata/banding;
- subtle lichen-like breakup;
- very high roughness and flat face normals.

## Reference implementation directions studied

- GrandPiaf/Biome-and-Vegetation-PCG — height/moisture biome logic and Poisson/minimum-distance vegetation distribution: https://github.com/GrandPiaf/Biome-and-Vegetation-PCG
- udit/poisson-disc-sampling — practical minimum-distance / Bridson-style distribution reference: https://github.com/udit/poisson-disc-sampling
- pajama-studio/lowpoly-tree-generator — semantic low-poly trunk/branch/canopy clustering and faceted tree art direction: https://github.com/pajama-studio/lowpoly-tree-generator
- hugomarques13/TreeGenerator — low-poly pruning/simplification and procedural bark direction: https://github.com/hugomarques13/TreeGenerator
- TheBeautifulOrc/TBO-Tree-Gen — continuous branch/junction mesh direction rather than visible intersecting tubes: https://github.com/TheBeautifulOrc/TBO-Tree-Gen
- acfaruk/proc-rock — procedural rock form/material cues: https://github.com/acfaruk/proc-rock
- shader-slang/slang — Slang to SPIR-V/Vulkan toolchain: https://github.com/shader-slang/slang

## Non-negotiable rules

1. No visible block-grid terrain unless intentionally used by gameplay.
2. No uniform random tree/rock confetti.
3. No unbounded random size/rotation variation.
4. No thin spaghetti branches or intersecting branch tubes.
5. No glossy plastic bark, leaves, soil or rocks.
6. No bitmap dependency for the base natural-material pass.
7. Terrain and ecology must be deterministic from the planet seed.
