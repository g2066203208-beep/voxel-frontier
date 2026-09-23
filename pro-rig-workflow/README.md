# Professional 2D Skeletal Animation Workflow

This folder turns the repository into a reproducible **professional 2D cutout / mesh-rig animation project**.

Benchmark workflow reference:
- Olga Zankevich — *Walking animation. Spine 2D animation* (Behance)
  https://www.behance.net/gallery/155118003/Walking-animation-Spine-2D-animation
- Godot official 2D Skeleton workflow
  https://docs.godotengine.org/en/stable/tutorials/animation/2d_skeletons.html

## What is reproduced

The workflow architecture is reproduced, not the unlicensed artwork itself:

**Source artwork → cutting → hidden-overlap completion → pivots → bone hierarchy → slots/draw order → mesh → weights → constraints → animation → QA → export.**

The original Behance artwork is NOT copied into this public repository unless the rights holder provides redistribution permission.

## Repository contract

Every production character must contain:

```
characters/<id>/
├── source/
│   └── SOURCE.md
├── parts/
│   ├── head/
│   ├── body/
│   ├── arms/
│   ├── legs/
│   ├── hair/
│   ├── clothes/
│   └── props/
├── rig/
│   └── project.x2d.json
├── animations/
│   ├── idle.json
│   ├── walk.json
│   └── action_*.json
├── qa/
│   └── QA.md
└── export/
```

The rig format target is `x2d-rig-v2`, defined in `spec/x2d-rig-v2.schema.json`.
