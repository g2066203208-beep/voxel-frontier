# Production Workflow

## Stage 0 — Source and rights

Record source, author, license/permission and whether redistribution is allowed.

Gate:
- no unknown-license source files in the public repository;
- references may be linked without mirroring source artwork.

## Stage 1 — Character decomposition

Cut by **motion function**, not by visual decoration.

Minimum structure:
- face base;
- front / side / back hair groups;
- torso / pelvis;
- upper arm / forearm / hand;
- thigh / calf / foot;
- garment body / sleeves / skirt layers;
- independent props.

Every joint-facing edge must include hidden overlap / bleed so rotation or deformation never reveals a gap.

## Stage 2 — Rest pose

Define:
- canvas;
- origin;
- local transforms;
- pivots;
- parent-child bone hierarchy;
- attachment rest transforms.

No animation is authored before the rest pose passes visual reconstruction.

## Stage 3 — Slots and draw order

Each visual part belongs to a slot.

Slots define:
- bone ownership;
- default draw order;
- attachment;
- clipping/masking relationship.

Draw-order changes are animated separately from bone transforms.

## Stage 4 — Mesh

Use rigid sprites only where rigid motion is correct.

Mesh candidates:
- torso clothing;
- hair masses;
- skirts;
- sleeves;
- cheeks / mouth region;
- soft bags and ribbons.

Store:
- vertices;
- triangles;
- UVs;
- per-vertex bone weights.

## Stage 5 — Weight painting

Requirements:
- weights per vertex sum to 1.0 ± tolerance;
- deformation must not collapse elbows/knees;
- shoulders/hips use multi-bone blending;
- hair/skirt use distributed chains rather than one rigid bone.

## Stage 6 — Constraints

Supported target constraints:
- two-bone IK;
- transform constraint;
- path constraint;
- aim/look-at;
- spring/jiggle/secondary motion.

Constraints are evaluated after base pose and before final attachment draw.

## Stage 7 — Animation

Professional timelines include:
- bone translate / rotate / scale;
- slot color / visibility;
- attachment switches;
- draw order;
- mesh deform;
- constraint mix;
- events.

Curves:
- linear;
- stepped;
- cubic Bezier.

Required baseline clips:
- idle;
- blink;
- walk;
- turn/look;
- one interaction/action clip.

## Stage 8 — QA

Automated checks:
- broken parents;
- cycles;
- missing files;
- invalid pivots;
- invalid keyframe time;
- unsorted keys;
- bad draw-order references;
- mesh index errors;
- invalid UV range;
- negative/NaN weights;
- weight sum errors;
- constraint target errors.

Visual checks:
- no seam exposure;
- no part pop;
- no elbow/knee disconnection;
- no layer inversion;
- no clipping during extreme keyframes.

## Stage 9 — Export

Targets:
- X2D Bone Player package;
- Godot project;
- GIF/MP4 preview;
- Android APK playback.

The repository must preserve provenance and must distinguish:
- source-authored animation;
- converted animation;
- demo-authored animation.
