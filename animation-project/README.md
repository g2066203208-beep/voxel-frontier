# X2D Animation Project

This directory is the entry point for the GitHub-only 2D skeletal-animation workflow.

## Canonical modules

- `bone-player/` — Android APK player/editor runtime.
  - v0.2 schema: rigid sprites + Polygon mesh + UV + multi-bone vertex weights + rest transforms + named animation clips.
- `public-rig-pipeline/` — source ingestion, audit, deterministic conversion and validation.
- `official-godot-case/` — native Godot Skeleton2D oracle/reference app.
- `.github/workflows/build-x2d-bone-player.yml` — builds the v0.2 APK and the importable source-authentic case.
- `.github/workflows/build-official-godot-skeleton-case.yml` — builds the native Godot reference APK.

## Non-negotiable provenance rule

A public animation is called source-authentic only if its keyframes come from the public source itself.
The pipeline may convert representation, but it must not invent replacement keyframes and then label them as source animation.

## First acceptance case

Godot official Skeleton2D demo, pinned to:

`godotengine/godot-demo-projects@a3b5c113112f77291d5f3d1360f33a882fdc52f7`

Source data imported by the converter:
- 16 Bone2D nodes
- 7 Polygon2D meshes
- UV coordinates
- per-vertex multi-bone weights
- rest transforms
- 8 original animation clips: fall, fly, idle, jump, land, land_hard, run, walk

The CI gate checks source commit, clip names, non-empty bones/meshes, normalized vertex weights, ZIP integrity and APK integrity.

## Deliverables

- `bone-player/releases/X2DBonePlayer-v0.2-mesh-weight-debug.apk`
- `bone-player/releases/GodotOfficialSkeleton2D-source-authentic.x2d.zip`
- `official-godot-case/releases/X2D-Godot-Official-Skeleton-Case-v0.2.apk`

## Validation philosophy

The native Godot APK is the correctness oracle. The X2D package is generated from the same pinned source without authored motion. Differences between the native oracle and the X2D player are implementation bugs to fix, not animation changes to hide.
