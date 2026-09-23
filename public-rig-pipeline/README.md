# Public 2D Rig Pipeline

This folder is the reproducible source-of-truth for the X2D Bone Player examples.

## Rule: no guessed black-box conversion

The pipeline separates five stages:

1. **SOURCE** — download the original public asset from the recorded URL.
2. **PARTS** — extract transparent parts without changing the source artwork.
3. **RIG MAP** — explicit, reviewable bone hierarchy + pivot/rest-pose mapping.
4. **ANIMATION** — source animation is preserved when it exists; otherwise any added demo motion is explicitly marked `demo_authored`.
5. **VALIDATE + PACK** — validate hierarchy, cycles, missing images, pivot values and keyframe time range, then create the APK-importable ZIP.

The original license and source URL are copied into every generated package.

## Why Godot is a reference, not silently converted

The official Godot Skeleton2D demo uses Polygon2D/Skeleton2D deformation and weights. X2D Bone Player v0.1 is a rigid cutout player, so pretending the two formats are equivalent would be wrong. The GitHub pipeline downloads/archives the Godot demo as a native professional reference. A later X2D format revision will add mesh vertices + weights before a lossless importer is enabled.

## Outputs

- `CC0_Female_BoneSheet_Wave.x2d.zip` — importable into X2D Bone Player.
- `CC0_Male_BoneSheet_Idle.x2d.zip` — importable into X2D Bone Player.
- `public_source_inventory.zip` — file inventories for the CC0 pivot archive, Archer source, and Godot official Skeleton2D demo.
- contact sheets used for QA.

The generated motion in the first two packages is deliberately simple and is labeled as pipeline-authored. The character art is the public CC0 source.
