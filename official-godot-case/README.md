# X2D Official Godot Skeleton Case

This is the canonical source-authentic animation validation case.

Upstream:
- Repository: godotengine/godot-demo-projects
- Path: 2d/skeleton
- Pinned commit: a3b5c113112f77291d5f3d1360f33a882fdc52f7
- License: MIT

The APK build copies the official demo unchanged, then adds only a showcase controller/scene.
The showcase controller disables the gameplay controller and selects the original AnimationPlayer clips:
idle, walk, run, fly, fall, jump, land, land_hard.

It does NOT generate replacement keyframes.

The original player.tscn remains the authoritative rig:
Skeleton2D + Bone2D + Polygon2D mesh + UV + per-vertex bone weights + AnimationPlayer/AnimationTree.
