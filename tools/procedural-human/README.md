# Procedural Human v1

A compact, browser-first **master-mesh + interpretable deformation-field** human generator for `voxel-frontier`.

This is deliberately not a Blender/MakeHuman plug-in and not a text-to-3D model. A single fixed-topology master mesh is loaded, converted to an anatomical coordinate frame, and continuously deformed by mathematical basis functions for height, shoulder/chest/waist/hip proportions, torso and limb lengths, body-fat/muscle tendencies, head/neck proportions and related parameters.

## Run

Serve the repository with any static HTTP server and open:

`/tools/procedural-human/index.html`

The page works as a static GitHub-Pages-style app. No backend or GPU inference service is required.

## Current v1 pipeline

`CC0 master mesh -> axis canonicalization -> vertical landmark remap -> smooth anatomical deformation fields -> exact stature normalization -> anthropometric estimation -> Three.js preview -> OBJ/GLB export`

The male and female buttons are **parameter presets over the same topology**, not different meshes.

## Mathematical idea

For master vertices `V0`, v1 evaluates a compact deformation model:

`V(p) = H( V0 + sum_i w_i(y, region) * D_i(p_i) )`

where `w_i` are smooth anatomical region functions (Gaussian/smooth-step fields), `D_i` are interpretable width/depth/length changes and `H` is a piecewise vertical landmark remapping followed by exact height normalization. This keeps topology and vertex identity stable across every generated person.

The measurement pass estimates shoulder breadth and chest/waist/hip circumferences from robust cross-sections. A future inverse-fit pass can therefore solve parameters from target real-world measurements instead of only slider values.

## Source / licensing boundary

The runtime code in this folder is original project code. The default master mesh is fetched at runtime from NAVER Anny's MakeHuman/MPFB2 data path:

`naver/anny/src/anny/data/mpfb2/3dobjs/base.obj`

Anny documents its MakeHuman-derived data as CC0 while its program code is Apache-2.0. We intentionally consume only the CC0 master geometry here; this folder does **not** copy SMPL, SMPL-X, FLAME, AnthroNet or other restricted model assets/checkpoints.

Upstream reference: https://github.com/naver/anny

## v1 limitations

The deformation basis is geometry-driven and mesh-agnostic, so it is intentionally compact rather than scan-fitted. Face-specific landmarks, joint-aware muscle bulges, inverse anthropometric fitting, skeleton regression and learned nonlinear correction fields belong in later versions. The architecture is designed so those can be added without changing the master topology or the public parameter schema.
