# Voxel Frontier Procedural Material Lab

This directory is the **code-only source of truth** for Voxel Frontier materials.

## Production rule

The game material pipeline is procedural:

`seed + material parameters + environment state -> generated PBR fields -> runtime/preview shading`

PNG files are **build artifacts for CI inspection only**. They are not authored source assets and are not the long-term runtime material architecture.

No image-generation model output is accepted as a production material source.

## Locked visual direction: `VF_PAINTERLY_PLANETARY_V1`

The approved direction is strong hand-painted / sculptural stylization rather than scanned realism, vector-flat graphics, or generic noise textures.

For rock materials:

- large, readable sculptural masses dominate the surface;
- real Height/displacement must carry macro form, not just Normal-map fakery;
- broad chiseled planes and layered geology are preferred over smooth spherical relief;
- cracks are sparse, narrow, geologically plausible, and subordinate to the main rock mass;
- do not generate decorative cross scratches, arbitrary engraved symbols, or full closed crack networks;
- do not generate tiny detached/floating rubble as surface decoration;
- color uses designed warm/cool painted planes and controlled variation rather than photographic micro-noise;
- micro detail is restrained; silhouette and macro relief must read first;
- roughness is mostly matte and semantic, with variation only where the material state calls for it.

The current approved production implementation is:

- style: `VF_PAINTERLY_PLANETARY_V1`
- preset: `vfLayeredSandstonePainted`
- master request: `vf_painted_layered_sandstone_master`
- production recipe: `material_lab/meshova/recipes/vf-layered-sandstone-painted.ts`

## Repository architecture

- `material_lab/request.json`
  - deterministic production bake request;
  - uses stable material names, never experiment suffixes such as `v7`, `v12`, `final2`, etc.
- `material_lab/meshova/bake-request.ts`
  - explicit production preset whitelist;
  - rejected and experimental styles cannot be invoked through the production baker.
- `material_lab/meshova/recipes/`
  - contains only production-approved recipe source;
  - rejected cartoon, realistic, draft, backup, and legacy material implementations are removed from the active tree and remain recoverable only through Git history.
- `material_lab/preview/render_material_previews.py`
  - deterministic standard preview renderer;
  - reads real PBR maps and real Height displacement;
  - displacement behavior is selected from manifest preset metadata, never guessed from material filenames.
- `.github/workflows/procedural-materials.yml`
  - enforces source hygiene, production preset allowlisting, required PBR outputs, dimensions, style manifest, deterministic previews, and artifact packaging.

## Hygiene rules

Do not commit experimental style recipes into the production recipe directory.

Forbidden production-source patterns include:

- `*cartoon*`
- `*experimental*`
- `*draft*`
- `*backup*`
- `*old*`
- version-suffixed experiment recipe files such as `*-v2.ts`
- committed PNG/JPG/WebP/TGA texture source assets inside `material_lab/`

Experiments belong in Git history or a temporary external work area. Once a direction is rejected, its source is removed from the active material tree.

## Adding a new production material

A new material is not production-ready merely because it can bake.

It must first satisfy the locked visual contract, then be added deliberately to the production preset registry. The approved sequence is:

1. build the procedural material from code and deterministic seed;
2. generate BaseColor, Normal, Roughness, Height, AO, and Metallic;
3. render with the standard displaced material sphere;
4. inspect macro silhouette, cracks, floating fragments, seams, and PBR response;
5. only after visual approval, register the preset in `bake-request.ts`;
6. extend the CI allowlist at the same time;
7. keep the stable production name free of iteration/version suffixes.

No rejected prototype may remain registered beside production materials.

## Runtime direction

The final game architecture should not swap static texture sets for weather states. Surface appearance is intended to be composed from procedural base material plus continuous environment/interactivity state, for example:

- wetness;
- frost;
- snow coverage/depth/compression;
- mud;
- dust;
- moss;
- burn/wear/damage.

These states should blend material properties by channel rather than blindly multiplying every PBR map. PNG bakes remain a development and CI validation output, not the core runtime dependency.
