# Public 2D Rig Pipeline — source-authentic only

## Correction

The earlier X2D Female/Male/Archer packages contained **pipeline-authored demo keyframes** and, for the sheet-based characters, heuristic part-to-bone mapping. They are **not source-authentic case animations** and must not be used as professional animation references. Those generated packages have been removed from the canonical `generated/` directory.

From now on this project follows one rule:

> A public case may be called an animation case only when the public source itself contains the rig and/or animation data we are reproducing.

## Case classes

### A. Native rig + native animation — valid professional animation reference
**Godot official Skeleton2D demo**
- Source: `godotengine/godot-demo-projects/2d/skeleton`
- License: MIT
- Native data: Skeleton2D/Bone2D hierarchy, Polygon2D mesh vertices, per-vertex bone weights, AnimationPlayer/AnimationTree.
- Source animation state names verified from the original project:
  - idle
  - walk
  - run
  - fly
  - fall
  - jump
  - land
  - land_hard
- Rule: preview/export may select or sequence these existing source clips, but must not replace their keyframes with newly authored motion.

### B. Public separated parts but no source rig/animation — asset reference only
**2DPIXX Archer**
- Contains actual separated PNGs such as head, torso, upper/lower arms, hands, upper/lower legs, feet, bow and arrows.
- License: CC BY 4.0.
- It is valid for studying part separation.
- It is **not** an animation-reference case unless an original rig/animation file is present.

**Female+Male Bones Sheet / 2D female and male bone-based sprites**
- CC0 separated-body-part references.
- Useful for part boundaries and, where encoded in filenames, pivots.
- They do not become professional animation examples just because this pipeline can attach bones to them.

## Professional pipeline

1. SOURCE ACQUISITION
   - Record exact source repository/page, author, license and upstream commit/hash.
2. SOURCE CLASSIFICATION
   - asset-only / rig-only / rig+animation.
3. NATIVE PRESERVATION
   - Keep the original scene/project data unchanged as the reference.
4. STRUCTURAL EXTRACTION
   - Extract exact bones, parents, rest transforms, meshes, UVs, weights, slots/attachments and animation keys from the native source.
5. LOSSLESS FEATURE GATE
   - Do not convert to X2D unless the X2D schema supports every feature required by that case.
6. IMPORT
   - Import extracted native data without guessing pivots or inventing keyframes.
7. VALIDATION
   - Bone count/names/parents, rest transforms, mesh vertex counts, weight sums, animation names/durations/key values.
8. VISUAL REGRESSION
   - Render the original native project and the imported X2D result at fixed timestamps and compare images.
9. EXPORT
   - Only after structural + visual validation may an importable package be published.

## Current feature gate

X2D Bone Player v0.1 supports rigid sprite attachments and transform keyframes only.

The Godot official Skeleton2D case uses weighted Polygon2D meshes. Therefore a lossless Godot importer is **blocked** until X2D adds:
- mesh vertices + triangles
- UVs
- multiple bone influences per vertex
- normalized weights
- rest transforms
- animation clip names and native keyframes

Until then, the Godot case remains the native correctness oracle and must not be flattened into a fake rigid-rig package.
