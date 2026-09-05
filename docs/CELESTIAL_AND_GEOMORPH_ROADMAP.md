# Voxel Frontier — Celestial + Geomorphology Production Roadmap

Date: 2026-09-06

This roadmap replaces the idea of treating celestial motion as a sky animation or treating terrain as a collection of independent noise masks. The production target is a deterministic, physically coherent planetary system whose large-scale terrain forms come from causal geological/hydrological fields, while rendering and local editing remain game-budgeted.

## 1. External reference stack

No single open-source project is the right template for the whole game. Use a reference stack, with each project studied only for the subsystem it does exceptionally well.

### Celestial / planetary reference stack

1. **OpenSpace** — primary architecture reference for universe-scale navigation, planetary scene graphs, tiled globe LOD, double-precision large-scale coordinates, body rendering and continuous surface-to-space traversal.
2. **REBOUND** — primary numerical-dynamics reference for N-body gravity and integrator selection. Important reference integrators: WHFast / other symplectic methods for long planetary propagation, IAS15 for high-accuracy general-force propagation, and hybrid methods such as MERCURIUS / TRACE for close encounters.
3. **NASA NAIF SPICE / CSPICE** — primary reference for ephemeris/state-vector interfaces, time systems, reference frames, body-fixed/inertial transforms and event geometry. Voxel Frontier does not need to become a SPICE client for procedural systems, but should copy the separation of time/frame/state responsibilities.
4. **Tudat / Orekit** — secondary references for force-model composition, propagation interfaces, maneuvers, perturbations and validation patterns.

### Terrain / geomorphology reference stack

1. **OpenSpace RenderableGlobe + Cesium Native** — primary references for globe subdivision, tile/patch selection, screen-space LOD, data streaming and planet-scale precision.
2. **Geometry Clipmaps / GPU Geometry Clipmaps** — primary local-ground rendering reference for nested regular grids, incremental updates and stable close-to-horizon throughput.
3. **FastScape / fastscapelib + Landlab** — primary scientific references for causal landscape evolution: drainage, stream-power incision, hillslope transport, erosion/deposition and process composition.
4. **Godot Voxel Tools (Zylann/godot_voxel)** — primary reference for local editable smooth volumetric terrain, sparse streamed blocks, SDF representation, smooth meshing and Transvoxel LOD transitions.
5. **FastNoise2** — high-performance SIMD reference for deterministic residual/micro detail only. Noise is not allowed to decide continents, mountains, rivers, canyons, coasts or plate boundaries.

## 2. Celestial system target architecture

### 2.1 Reference-frame hierarchy

Use explicit frames rather than one giant world transform:

```text
Universe barycentric inertial frame
  -> star-system barycentric frame
    -> body-centered inertial frame
      -> body-fixed rotating frame
        -> local ENU/tangent frame
          -> camera-relative render frame
```

Authoritative states use double precision. GPU rendering uses camera-relative floating-point values. Local gameplay physics runs in the local body frame and is re-based without changing the physical state.

### 2.2 Time model

Create one monotonic simulation epoch (`AstroTime`) stored as high-precision seconds from a defined epoch. Do not derive orbital state from frame count.

Separate:
- simulation time;
- wall-clock/UI time;
- time-warp multiplier;
- fixed dynamics substeps;
- render interpolation.

### 2.3 State model

Every body has an authoritative Cartesian state:

```text
position [m]
velocity [m/s]
orientation quaternion
angular velocity [rad/s]
mass / GM
shape/radii
reference-frame parent metadata
```

Keplerian elements are initialization/serialization input, not the continuously accumulated source of truth.

### 2.4 Integrator tiers

Do not force one integrator on every object.

**Tier A — major stars/planets/moons:**
- symplectic long-term propagation;
- fixed or block timesteps;
- conserve energy/angular momentum over long runs;
- use a WHFast/Wisdom-Holman style architecture as the primary reference.

**Tier B — close encounters / unusual force models / validation:**
- high-accuracy adaptive path inspired by IAS15;
- used selectively, not every frame for the whole universe.

**Tier C — ships, debris, gameplay objects:**
- local body-centered/reference-frame simulation;
- force evaluation only from relevant active bodies;
- asleep/unloaded objects can switch to analytical or coarse propagation and resynchronize on activation.

The current velocity-Verlet implementation is a good correctness baseline but is not the final universe-scale integration architecture.

### 2.5 Rotation and astronomy

Implement explicitly:
- axial tilt;
- sidereal rotation period;
- body-fixed transform;
- orbital plane orientation;
- moon/planet phase geometry;
- physically derived day/night terminator;
- eclipse/occultation geometry;
- star angular size from physical radius and distance.

Later extensions:
- precession/nutation where gameplay-visible;
- J2/oblateness for selected bodies;
- tides / tidal locking;
- radiation pressure / atmospheric drag for spacecraft where useful.

### 2.6 Celestial LOD

Physics and rendering have independent LOD.

```text
very far: analytical state + impostor/point light
far: low-poly body proxy
orbital: ellipsoid + atmosphere + coarse surface tiles
near surface: full terrain patch hierarchy
local: collision / hydrology / vegetation / editable SDF
```

A celestial body must remain the same object through these LOD transitions.

## 3. Geomorphology system target architecture

### 3.1 Main rule

Large landforms must emerge from large-scale causal fields. The production generator must not create a `canyon` or `river` merely because a narrow noise mask has a high value.

### 3.2 Planet genesis pipeline

```text
seed
 -> planetary constants (radius, gravity, sea level, atmosphere, heat)
 -> spherical plate graph
 -> crust class / crust age / buoyancy
 -> plate velocity field from Euler poles
 -> convergent / divergent / transform boundaries
 -> long-wavelength tectonic elevation
 -> ridge / trench / orogen / rift / hotspot construction
 -> climate fields
 -> drainage / lake fill / flow accumulation
 -> fluvial incision + hillslope diffusion + deposition
 -> glacier / dune / wetland process masks
 -> residual stochastic detail
 -> materials / biomes
```

### 3.3 Tectonics

Replace the current inexpensive nearest-two-plate surrogate with a reusable spherical plate graph generated once per planet seed.

Store deterministic plate metadata:
- spherical polygon/cell;
- Euler pole;
- angular speed;
- crust type;
- crust age/density proxy;
- buoyancy;
- optional hotspot tracks.

At boundaries derive relative tangential velocity and classify:
- convergent;
- divergent;
- transform.

Use boundary type plus crust classes to create coherent belts instead of local bumps:
- continent-continent convergence -> broad orogen + plateau;
- ocean-continent convergence -> trench + volcanic arc + coastal mountain belt;
- ocean-ocean convergence -> trench + island arc;
- divergence -> rift or mid-ocean ridge;
- transform -> linear fault valleys/ridges with limited vertical relief.

### 3.4 Hydrology must be real topology

The current cheap river proxy must be replaced as terrain authority.

For each regional DEM tile or cached low-resolution planetary field:
1. depression fill / breach;
2. downhill flow direction;
3. flow accumulation / contributing area;
4. river-head threshold;
5. channel width/depth from discharge proxy;
6. stream-power incision;
7. sediment deposition in low-gradient reaches/deltas;
8. lake/wetland identification from closed/low-gradient basins.

This guarantees rivers do not run uphill and makes valleys/canyons follow the same drainage network.

### 3.5 Erosion / landscape evolution

Use FastScape/Landlab as scientific algorithm references, not as runtime dependencies by default.

Implement a deterministic, game-budgeted subset:
- stream-power fluvial incision;
- nonlinear or linear hillslope diffusion;
- sediment deposition/transport proxy;
- optional glacial smoothing/incision in cold high regions;
- thermal/weathering proxy for talus/rock slopes.

Run expensive evolution when a planet/region is generated or cached, not continuously every render frame.

### 3.6 Climate and process-controlled landforms

Derive climate from latitude, stellar irradiance, elevation, continentality and simplified circulation/orographic effects.

Landforms then follow actual conditions:
- dunes: arid + sediment supply + persistent wind + low vegetation;
- wetlands: low gradient + high water table / flow accumulation;
- glaciers: cold accumulation zone + gravity-driven downslope flow;
- canyons: high incision relative to uplift/hillslope widening;
- deltas: high sediment flux entering low-energy water;
- coastal cliffs: resistant/high-relief shoreline exposed to wave/tectonic forcing.

### 3.7 Noise policy

FastNoise2 may provide:
- sub-kilometre roughness;
- rock-scale variation;
- stochastic material breakup;
- seed-stable residual variation.

It may not decide:
- continent position;
- plate boundaries;
- primary mountain chains;
- trenches;
- main river networks;
- primary coastlines.

## 4. Planet rendering / streaming architecture

### 4.1 Planet scale

Use a six-face cube-sphere quadtree with a shared regular patch topology. Select patches with projected screen-space error and horizon/frustum culling. This follows the proven globe pattern in OpenSpace/Cesium while fitting the existing Vulkan renderer.

### 4.2 Ground scale

Near the player, either:
- continue refining cube-sphere patches with geomorphing; or
- introduce a local tangent-frame geometry clipmap fed by the same terrain function/cache.

The clipmap path is preferred only if profiling shows it materially reduces CPU/GPU terrain-streaming cost and can be made seam-safe at the transition to the spherical patch hierarchy.

### 4.3 GPU pipeline

Target:
- immutable/shared patch index topology;
- persistent mapped/staging resources;
- double/triple buffered patch payloads;
- asynchronous generation jobs;
- Vulkan indirect draws;
- GPU culling where measurements justify it;
- mesh/task shaders as an optional fast path, not a hard dependency;
- no device-wide idle during normal streaming.

### 4.4 Local caves/deformation

Do not voxelize the whole planet.

Use sparse local SDF bricks only where 3D topology is required. Study Zylann/godot_voxel for:
- streamed sparse blocks;
- SDF storage;
- Transvoxel transition cells;
- re-meshing only edited regions.

The SDF surface replaces the base height surface locally and blends back to the analytical/procedural planet surface at the brick boundary.

## 5. What is wrong with the current R21-style terrain approach

The current code has useful building blocks (seeded plates, Euler-pole-like plate motion, multiple spatial scales, climate hints and named morphology fields), but it still synthesizes many named landforms directly from local procedural masks.

Examples of production issues:
- `river` is a sinusoidal/channel proxy rather than a downhill drainage network;
- `canyon` is a narrow ridged noise mask conditioned by aridity rather than fluvial incision;
- `dunes`, `wetland`, `glacier` are primarily scalar masks, not the result of transport/flow fields;
- one point can have a high semantic label without the camera seeing a coherent large-scale shape;
- separate labels can overlap without a causal geomorphic history.

Therefore do not keep tuning the amplitudes. Replace the authority layer progressively with process-derived fields while retaining the useful deterministic sampling/render interfaces.

## 6. Implementation order

### R23 — Reference-frame + time foundation
- introduce explicit celestial frames and `AstroTime`;
- separate dynamics tick from render interpolation;
- camera-relative render transform;
- tests for frame transforms and precision.

### R24 — Celestial integrator upgrade
- retain Verlet as regression baseline;
- add production symplectic major-body integrator inspired by REBOUND WHFast/Wisdom-Holman;
- long-duration conservation tests;
- fixed-camera Sun/Moon/planet motion screenshot sequences committed to evidence.

### R25 — Planet patch LOD
- cube-sphere quadtree;
- screen-space error;
- horizon/frustum culling;
- shared patch mesh + geomorphing;
- orbital-to-ground continuity screenshots.

### R26 — Tectonic authority rewrite
- persistent spherical plate graph;
- boundary classification;
- crust metadata;
- coherent orogen/ridge/trench/rift/hotspot fields;
- global diagnostic maps and rendered screenshots.

### R27 — Hydrology authority
- DEM flow routing;
- flow accumulation;
- real river/lake network;
- river incision and valley/canyon derivation;
- downhill invariant tests.

### R28 — Landscape evolution
- FastScape/Landlab-inspired erosion/deposition subset;
- hillslope diffusion;
- sediment/delta handling;
- glacial/wind-process hooks.

### R29 — Local SDF terrain
- sparse editable bricks;
- smooth meshing;
- crack-free Transvoxel-style LOD transitions;
- collision rebuild for edited regions.

### R30 — GPU streaming hardening
- persistent resources;
- bounded async generation budget;
- indirect draw/culling;
- optional mesh shader path;
- full ground->orbit stress test.

## 7. Mandatory evidence for every round

Every R23+ test round must commit and show the user the real Vulkan framebuffer captures whether they look good or bad.

Minimum evidence matrix:
- ground view;
- regional oblique view;
- high-altitude/orbital view;
- terrain diagnostic relevant to that round;
- celestial fixed-camera sequence when celestial code changes;
- capture metadata + runtime/Vulkan logs.

Generated images are never test evidence.
