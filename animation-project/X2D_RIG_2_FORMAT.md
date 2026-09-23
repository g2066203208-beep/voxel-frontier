# X2D Rig 2.0 format

`project.json` stores:

- `source`: source name/repository/path/commit/license and source-authentic flag.
- `bones[]`: id, parent, default local transform, local rest Transform2D matrix.
- `meshes[]`: source texture, rest vertices, UVs, triangle indices and per-vertex bone-weight pairs.
- `animations{}`: named clips. Each clip has duration, loop flag and per-bone position / rotation keys.
- `modelOffsetX/Y`: view-only placement; not animation data.

Runtime skinning uses the standard 2D bind transform:

`skin_bone = current_global_bone * inverse(rest_global_bone)`

Each rest-space mesh vertex is transformed by all influencing bones and blended by normalized source weights.

The v0.2 converter never creates motion keys. It parses the keys from the original Godot `Animation` sub-resources mapped by the original `AnimationLibrary`.
