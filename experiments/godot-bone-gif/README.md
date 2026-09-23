# Godot Skeleton2D -> GIF (GitHub-only demo)

This branch proves the full automation path the user asked for:

1. GitHub Actions checks out this repository.
2. The workflow sparse-clones the official Godot `2d/skeleton` demo.
3. It downloads the latest stable Godot editor build for Linux.
4. It patches the demo controller so the rig walks right, then left, then idles automatically.
5. Godot Movie Maker renders deterministic frames from the real Skeleton2D/AnimationTree project.
6. FFmpeg converts the captured movie into an animated GIF.
7. GitHub Actions uploads the GIF as an artifact.

No local PC interaction is required after the workflow is committed.

## Output

Artifact name: `godot-skeleton2d-gif`

Expected file:

```
godot_skeleton2d_demo.gif
```

## Why this demo

This uses Godot's official Skeleton2D project rather than a hand-faked frame animation, so the produced GIF is driven by an actual 2D skeletal rig and animation system.

The next step is to replace the demo robot assets/rig with the user's separated character artwork while keeping the same GitHub Actions render pipeline.
