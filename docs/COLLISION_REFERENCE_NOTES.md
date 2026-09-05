# Terrain and character collision reference notes

This implementation is intentionally adapted to Voxel Frontier's analytical spherical terrain rather than copied from another engine.

## Jolt Physics CharacterVirtual

Reference: `jrouwe/JoltPhysics`, `Jolt/Physics/Character/CharacterVirtual.*` and `Samples/Tests/Character/CharacterVirtualTest.cpp`.

The mature ideas reused here are:

- keep a configurable character padding/contact margin;
- use predictive contact handling instead of allowing deep penetration first;
- distinguish supporting contacts from steep blocking contacts;
- keep **StickToFloor** and **WalkStairs** as separate operations;
- treat the lower region of the capsule as the supporting volume rather than relying on one center ray.

Voxel Frontier cannot directly call Jolt shape casts because its planet ground is an implicit procedural sphere-height field. The equivalent used here is a deterministic multi-probe lower-capsule footprint plus short movement substeps against the authoritative `samplePlanetTerrain`/`planetSurfaceNormal` query.

## Jolt Physics HeightFieldShape

Reference: `jrouwe/JoltPhysics`, `Jolt/Physics/Collision/Shape/HeightFieldShape.*`.

The relevant lesson is that terrain collision is a surface/triangle problem with supporting faces and normals, not a single radial sphere intersection. Voxel Frontier therefore resolves against the procedural surface normal and samples the capsule footprint instead of treating the planet as a smooth radial shell.

## WorldEngine

Reference: `Mindwerks/worldengine`.

WorldEngine separates large-scale plate/elevation generation from erosion, hydrology and biome/land-surface passes. Voxel Frontier follows the same ordering principle: tectonic authority first, then rolling relief / valleys / canyons / dry ridges and material classification as subordinate deterministic fields.

## FastNoiseLite

Reference: `Auburn/FastNoiseLite`.

FastNoiseLite provides mature examples of fBm, ridged fractals and domain-warp style noise composition. Voxel Frontier keeps its existing seamless 3-D value-noise implementation on the unit sphere but uses the same composition ideas for subordinate regional, ridged and fine landform bands.
