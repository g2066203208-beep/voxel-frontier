# Voxel Frontier Procedural Material Lab

This directory is the **code-only source of truth** for Voxel Frontier materials.

## Production rule

The game material pipeline is procedural:

`seed + material parameters + environment state -> generated PBR fields -> runtime/preview shading`

PNG files are **build artifacts for CI inspection only**. They are not authored source assets and are not the long-term runtime material architecture.

No image-generation model output is accepted as a production material source.

## Locked visual direction: `VF_PAINTERLY_PLANETARY_V1`

The approved direction is strong hand-painted / sculptural stylization rather than scanned realism, vector-flat graphics, or generic noise textures.

Shared visual rules:

- macro form and silhouette read before micro detail;
- real Height/displacement carries the visible form instead of relying on Normal-map fakery;
- broad painted planes and controlled warm/cool variation replace photographic micro-noise;
- small detached decoration, floating fragments, arbitrary engravings and decorative cross scratches are forbidden;
- roughness is semantic to the material category, not random noise;
- every category has its own procedural shape grammar rather than recoloring the rock generator;
- material-sphere review must show tactile 3D relief; a smooth sphere with only shaded texture is a visual failure.

### Reference guardrail

`VF_PAINTERLY_PLANETARY_V1` uses **The Long Dark** only as an art-direction reference for the qualities we want to preserve: moving-concept-art readability, hand-painted imperfection, simplified shape/color/line, and large angular environmental masses. We do **not** copy its textures or assets.

Voxel Frontier keeps its own signature on top of those principles:

- sandstone uses oversized interlocking strata, thick chamfered shoulders, narrow ink-dark fractures, warm ochre faces and restrained cool-violet shadow planes;
- bark is one continuous wooden skin: irregular calligraphic vertical ridges, shallow carved furrows, localized peel/scar accents and sparse knot distortion; dark grooves must never read as open gaps through the surface;
- dirt reads as continuous ground mass with broad hand-painted warm/cool planes plus visible compacted clods, shallow pits, crumbs and sparse erosion marks;
- stone wall uses irregular proud masonry blocks, broad hand-painted stone faces and clearly recessed but non-black mortar;
- moss grows as a continuous mat of overlapping cushion colonies and raised soft tufts over a darker substrate;
- wolf fur combines dense soft underfur with longer directional guard-hair clumps, using cool charcoal/grey-brown/cream banding instead of generic brown fur;
- leaves, snow and water keep their existing category-specific silhouette language;
- displacement must create a readable silhouette at material-sphere scale without producing paper-thin fins, floating layers or self-intersection-like spikes.

## Approved nine-category master set

The production master set is intentionally stable:

- `vf_painted_layered_sandstone_master` -> `vfLayeredSandstonePainted`
- `vf_painterly_dirt_master` -> `vfPainterlyDirt`
- `vf_painterly_bark_master` -> `vfPainterlyBark`
- `vf_painterly_leaves_master` -> `vfPainterlyLeaves`
- `vf_painterly_snow_master` -> `vfPainterlySnow`
- `vf_painterly_water_master` -> `vfPainterlyWater`
- `vf_painterly_stone_wall_master` -> `vfPainterlyStoneWall`
- `vf_painterly_moss_master` -> `vfPainterlyMoss`
- `vf_painterly_wolf_fur_master` -> `vfPainterlyWolfFur`

Each is a category baseline, not a final catalog of variants.

## Repository architecture

- `material_lab/request.json`
  - deterministic nine-master production bake request;
  - uses stable material names with no experiment/version suffixes.
- `material_lab/meshova/bake-request.ts`
  - exact production preset whitelist.
- `material_lab/meshova/recipes/vf-painterly-core.ts`
  - shared deterministic periodic fields and PBR finalization only;
  - contains no category-specific art direction.
- `material_lab/meshova/recipes/vf-layered-sandstone-painted.ts`
- `material_lab/meshova/recipes/vf-painterly-dirt.ts`
- `material_lab/meshova/recipes/vf-painterly-bark.ts`
- `material_lab/meshova/recipes/vf-painterly-leaves.ts`
- `material_lab/meshova/recipes/vf-painterly-snow.ts`
- `material_lab/meshova/recipes/vf-painterly-water.ts`
- `material_lab/meshova/recipes/vf-painterly-stone-wall.ts`
- `material_lab/meshova/recipes/vf-painterly-moss.ts`
- `material_lab/meshova/recipes/vf-painterly-wolf-fur.ts`
  - isolated category recipes so later changes cannot accidentally contaminate another material family.
- `material_lab/preview/render_material_previews.py`
  - deterministic studio renderer using real PBR maps and Height displacement.
- `material_lab/preview/render_sandstone_mesh_preview.py`
  - true tessellated UV-mesh/Z-buffer preview for the strongly tactile opaque masters, so extreme Height visibly changes silhouette.
- `.github/workflows/procedural-materials.yml`
  - requires the exact approved recipe file set;
  - rejects raster source assets and unstable production naming;
  - requires exactly nine production masters and all six core PBR maps for each.

## Hygiene rules

The production recipe directory is an exact allow-list. Unregistered experiments do not belong there.

Forbidden production-source patterns include:

- `*cartoon*`
- `*experimental*`
- `*draft*`
- `*backup*`
- `*old*`
- version-suffixed experiment recipe files such as `*-v2.ts`
- committed PNG/JPG/WebP/TGA source textures inside `material_lab/`

Rejected work remains recoverable through Git history, not through dormant files in the active source tree.

## Adding a new production material

1. build it procedurally from code and a deterministic seed;
2. generate BaseColor, Normal, Roughness, Height, AO and Metallic;
3. render it with the standard displaced material sphere;
4. inspect silhouette, shape language, seams, cracks/fragments and PBR response;
5. visually approve it against `VF_PAINTERLY_PLANETARY_V1`;
6. add its preset and source file deliberately to the production allow-list;
7. keep its stable production name free of iteration suffixes.

## Runtime direction

The final game architecture should not swap static texture sets for weather states. Surface appearance is intended to be composed from procedural base material plus continuous environment/interactivity state, for example:

- wetness;
- frost;
- snow coverage/depth/compression;
- mud;
- dust;
- moss;
- burn/wear/damage.

These states blend material properties by channel rather than blindly multiplying every PBR map. PNG bakes remain development/CI validation output, not the runtime source of truth.
