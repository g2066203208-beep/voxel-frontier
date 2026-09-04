# Voxel Frontier — Authoritative Low-Poly Art Direction

Status: **authoritative**

This document freezes the approved visual/modeling direction for Voxel Frontier. Future procedural models, hand-authored low-poly assets, terrain forms, rocks, vegetation, props, vehicles and architecture should follow these principles unless a later design decision explicitly replaces them.

## 1. Core rule

**Low-poly is not “low resolution.” Low-poly means high visual abstraction with the fewest meaningful planes.**

The modeling objective is:

> Use the minimum number of vertices and faces required to communicate the object’s silhouette, weight, structure and material character. Every face must earn its existence.

Do **not** treat a coarse regular grid, a heavily subdivided sphere, or an automatically decimated high-poly mesh as the default art solution.

### Approved reference asset

The canonical reference rock is stored under:

`assets/style-reference/rock-ultralow/`

It uses **12 control vertices / 20 triangles** and is deliberately built from a small set of silhouette-defining points rather than from a subdivided sphere.

## 2. Modeling workflow

### Step A — Study real form and strong stylized references first

Before implementation, inspect reliable references and mature implementations. Do not invent a modeling method from scratch when a proven mechanism exists.

Relevant references used for the canonical rock:

- `Erkaman/gl-rock` — procedural rock generation by flattening/scraping portions of a base volume and adding procedural material variation. Its key observation is that natural rocks combine rounded volume with deliberately flatter regions; the implementation projects vertices toward randomly defined planes/disks and later applies procedural Perlin-based surface variation.
- `pavelkouril/unity-lowpoly-shader` — demonstrates the importance of true face normals for a flat-shaded low-poly appearance instead of interpolated smooth normals.

These are references for principles and implementation ideas, not assets to copy.

### Step B — Design the silhouette before surface detail

Start with the object’s most important large-scale characteristics:

- overall width / height / depth ratio;
- dominant mass;
- asymmetry;
- top profile;
- base contact / weight;
- major cuts, shoulders and protrusions;
- negative space where applicable.

For a rock, first ask what 10–20 control points are needed to describe the silhouette. Do not begin by adding hundreds of vertices.

### Step C — Place only meaningful control points

Control points should not be uniformly distributed. A good low-poly object deliberately varies face scale:

- large quiet planes where the form is simple;
- smaller planes only where the silhouette or structural transition needs them;
- stronger asymmetry than a primitive sphere/cube;
- broad, stable base where the object needs visual weight;
- a small number of designed breaks and chips rather than uniform noise.

### Step D — Build clean, closed, economical topology

For convex rock/boulder archetypes, a convex hull over deliberately placed control points is a valid starting method because it gives a closed non-self-intersecting volume with very little topology.

For non-convex objects, use explicit structural construction instead of adding random detail.

The canonical rock target is 20 triangles. This number is **not a quota**: if an object reads correctly with fewer faces, use fewer; if a larger object needs more silhouette-defining planes, add only what is justified.

### Step E — Evaluate silhouette first

Before material work, render the object as a single neutral color and check it from multiple angles.

Reject the mesh if:

- it looks like a noisy sphere;
- it looks uniformly faceted with no hierarchy;
- the base is unstable or point-like;
- the silhouette depends on material to look interesting;
- many faces can be deleted without changing the read;
- large planes do not follow the intended mass / fracture logic.

### Step F — Use true flat shading for faceted assets

For a triangle with positions `p0`, `p1`, `p2`, compute one face normal:

```text
n = normalize(cross(p1 - p0, p2 - p0))
```

All three corners of that triangle use the same normal for a deliberately faceted surface.

Do not average these normals across hard structural planes. Smooth normals erase the low-poly plane hierarchy and make an economical mesh look like a low-resolution blob.

## 3. Procedural material workflow

The approved style does **not** rely on image textures to create character. External textures may be used later when justified, but the default rock material should be reproducible entirely from shader mathematics.

The material must be layered. A single random RGB per face is not an acceptable stone material.

### Layer 1 — Base mineral family

Choose a restrained stone palette, e.g. slate / warm gray / muted brown. This establishes the material identity.

### Layer 2 — Macro mineral variation

Use low-frequency world/local-position functions or coherent 3D noise to create broad color regions. The variation should read as mineral composition, not television static.

Principle:

```text
large spatial wavelength
+ low amplitude
= believable mineral color variation
```

### Layer 3 — Strata / veins

Use oriented position fields to form broad oblique strata and narrow darker/lighter mineral bands. Avoid perfect horizontal cake layers.

Example family:

```text
sin(k * (z + ax + by) + macro_field)
```

### Layer 4 — Orientation-dependent weathering

Material must react to geometry. Upward-facing planes may be slightly bleached, dusted or warmer; protected/downward-facing planes may remain darker.

Use face/world normal terms rather than random face IDs.

### Layer 5 — Restrained lichen / surface growth

If the biome allows it, mix a very small amount of muted lichen color only where orientation and a broad procedural mask agree. Do not paint the whole rock green.

### Layer 6 — Micro grain

Add high-frequency variation with very small amplitude to stop large planes from looking like plastic. Micro detail must not alter the silhouette.

### Layer 7 — Edge wear

Use barycentric coordinates or geometric edge distance to create a subtle lightening/desaturation near exposed edges. This is not a cartoon outline; it should be barely visible and physically motivated as wear.

### Layer 8 — Rough-stone lighting

The visible low-poly character should come mainly from **geometry + flat normals + directional light**.

Use:

- diffuse / rough response;
- hemisphere/sky ambient;
- weak broad specular at most;
- no glossy plastic look;
- no black outline as a default.

## 4. Terrain / coastline implication

This art direction must not be confused with coarse streaming LOD.

A jagged coastline caused by 3 km or 20 km grid cells is **not** stylized low-poly art. Coastlines, ridgelines, cliffs, roads and other important silhouettes must keep sufficient geometric precision.

Correct order:

```text
accurate important silhouette / structural lines
→ stylized meaningful polygon planes
→ flat-shaded material treatment
→ performance LOD after the art form is correct
```

Incorrect order:

```text
very coarse regular grid
→ call the aliasing “low-poly”
```

LOD exists for performance; it must not define the art design.

## 5. Procedural generation rules

A procedural generator should expose meaningful art controls, not just noise strength:

- archetype / silhouette family;
- width-height-depth ratios;
- asymmetry bias;
- base flattening;
- shoulder / top offsets;
- major fracture / scrape planes;
- optional concavity/chip controls where topology supports them;
- face-count budget;
- material mineral palette;
- strata direction / scale;
- weathering strength;
- lichen probability / biome response;
- deterministic seed.

Randomness must vary an authored design space. It must not be allowed to create arbitrary ugly topology and call it variety.

## 6. Asset budgets

Budgets are guides, never targets to fill.

- tiny ground stones: often 8–16 triangles;
- normal gameplay rocks: roughly 12–30 triangles;
- hero boulders: roughly 20–60 triangles if silhouette demands it;
- larger cliffs / terrain structures: use feature-aware adaptive topology, not uniform tessellation.

Always prefer fewer faces when the silhouette and plane hierarchy remain equally strong.

## 7. Visual acceptance gate

A low-poly asset is not accepted because it compiles or because its triangle count is low.

Before promoting an asset/modeling change:

1. render the real geometry;
2. inspect at least front/three-quarter/side or allow interactive rotation;
3. inspect the silhouette without material;
4. inspect face readability under directional light;
5. inspect the procedural material at close and medium distance;
6. verify no unnecessary subdivision, smooth-normal mush, random-noise silhouette, intersections or floating parts;
7. keep a screenshot/reference render in the asset folder for visual regression.

## 8. Canonical reference rock contents

`assets/style-reference/rock-ultralow/VF_rock_ULTRA_20tri.glb`
: Binary model asset. 20 triangles, flat-shaded geometry, baked vertex-color preview of the procedural palette.

`assets/style-reference/rock-ultralow/VF_rock_ULTRA_20tri.obj`
: Text model asset with explicit per-face normals and `s off` for easy inspection/import.

`assets/style-reference/rock-ultralow/VF_rock_ULTRA_20tri_material.slang`
: Canonical zero-image-texture procedural stone material reference for the Vulkan/Slang renderer. Implements broad mineral variation, oblique strata/veins, orientation-dependent weathering, restrained lichen and micro grain.

`assets/style-reference/rock-ultralow/VF_rock_ULTRA_20tri_preview.svg`
: Approved visual reference render of the actual 20-triangle silhouette/facet hierarchy.

## 9. Non-negotiable summary

- **Minimum meaningful faces, maximum readable form.**
- **Silhouette first.**
- **Every face must contribute.**
- **Flat face normals for deliberate faceting.**
- **Procedural material is layered and geometry-aware, not random face colors.**
- **No external texture is required for the canonical stone look.**
- **LOD is a performance system, not an art substitute.**
- **Important outlines remain precise even in a low-poly style.**
- **References are studied before implementation.**
- **Actual rendered visual inspection is mandatory before acceptance.**
