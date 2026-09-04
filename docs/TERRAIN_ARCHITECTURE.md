# Voxel Frontier — Smooth Planet Terrain Architecture

## Decision

The production terrain is **not block-rendered voxel terrain**.

The visible world is always rendered as explicit GPU geometry: vertices + indexed triangles / meshlets.

The authoritative terrain representation is hybrid:

1. **Planet-scale base surface** — analytical/procedural sphere/ellipsoid + displacement, evaluated through hierarchical surface patches / clipmaps.
2. **Local volumetric detail** — sparse signed-distance/density fields only where true 3D topology is needed (caves, overhangs, excavation, filling, player deformation).
3. **Surface extraction** — local SDF/density data is converted to smooth triangle meshes; no visible cubes.
4. **Persistent edits** — store sparse edit operations / sparse field bricks, never a dense voxel grid for an entire planet.

## Scientific morphology model

The default Earthlike world is **seeded and deterministic, not unstructured random noise**. Randomness is used only to choose reproducible initial conditions (plate cell centers, Euler poles, crust class, hotspots and residual detail phases). Once `planetSeed` is fixed, `(seed, position)` always returns the same terrain.

The game generator intentionally models the first-order causal relationships that dominate Earth-scale morphology while avoiding a real-time geological simulation:

- spherical Voronoi-like plate cells approximate tectonic plates;
- each plate has a seeded Euler pole, so its surface velocity is tangential rigid rotation (`v ~ omega x r`);
- convergent boundaries preferentially create mountain belts on continental crust and trenches where oceanic crust participates;
- divergent oceanic boundaries are raised into mid-ocean ridges;
- continental crust sits higher than oceanic crust, with a smooth shelf/slope transition around sea level;
- plate-interior broad uplift creates plateaus/basins;
- volcanic relief combines convergent volcanic arcs with deterministic mantle-hotspot proxies;
- small multi-scale roughness is subordinate to tectonic morphology and may not decide where continents, ridges or trenches exist;
- close-range river networks are refined from downhill terrain drainage/flow accumulation rather than allowed to run uphill.

This is a **game-optimized geological surrogate**, not a reconstruction of the real present-day Earth. The target is scientific plausibility, readable gameplay and deterministic performance.

### External scientific anchors

- USGS, *This Dynamic Earth — Understanding Plate Motions*: divergent boundaries and seafloor spreading create mid-ocean ridges; convergent plate interactions are associated with mountain building and subduction-zone morphology. https://pubs.usgs.gov/gip/dynamic/understanding.html
- USGS, *This Dynamic Earth — Developing the Theory*: earthquakes/volcanism concentrate along trenches and submarine mountain systems, and the global mid-ocean ridge is a major tectonic landform. https://pubs.usgs.gov/gip/dynamic/developing.html
- NOAA Ocean Exploration, *What is a mid-ocean ridge?*: mid-ocean ridges occur along divergent plate boundaries where new ocean floor is created. https://oceanexplorer.noaa.gov/ocean-fact/mid-ocean-ridge/
- NOAA, *Ocean Floor Features*: continental shelf/slope, abyssal plain, mid-ocean ridge and ocean trench are treated as distinct large-scale bathymetric provinces. https://oceanservice.noaa.gov/education/tutorial_currents/05conveyor1.html (background collection) and NOAA Ocean Exploration resources.
- O'Callaghan & Mark (1984) D8 drainage concept, subsequently used widely for DEM flow direction/accumulation: water routes to the steepest lower neighboring cell; accumulated contributing area is used to extract drainage networks.

## Why not pure polygon mesh as world truth?

A pure surface triangle mesh is excellent for rendering and planet-scale LOD, but arbitrary digging, tunnels, arches, undercuts and terrain addition require dynamic topology surgery, spatial remeshing and robust collision updates. That is substantially harder to make stable than editing a local implicit field.

Therefore the mesh is the **rendered result**, not the only source of truth for deformable terrain.

## Why not block voxels?

A voxel can be a scalar sample (density/SDF), not a visible cube. Astroneer publicly describes its terrain this way: 3D voxels store density, while the game renders a smooth surface rather than blocks.

Our implementation follows the smooth interpretation only.

## Representation ladder

### Interplanetary / orbital
- analytical planet metadata
- very low-cost sphere/ellipsoid proxy
- atmosphere proxy
- no local SDF allocation

### Regional / planetary surface
- cube-sphere or ellipsoidal surface patches
- quadtree/clipmap LOD driven by screen-space error
- shared regular patch topology where possible
- deterministic tectonic/morphology displacement
- indexed triangle or mesh-shader output

### Local high-detail surface
- high-resolution surface patches
- collision mesh / height query
- local hydrology refinement for rivers/canyons
- no dense global volume

### Local 3D/deformable zones
- sparse SDF/density bricks only near caves, deformation, resources or other true volumetric features
- narrow-band storage where practical
- smooth surface extraction using Dual Contouring / Marching Cubes family
- multiresolution transitions must be crack-free (Transvoxel-style transition cells or equivalent seam strategy)

## Ocean model

The ocean uses one mean sea-level geoid shared by rendering and physics. Terrain continues underneath the water, so continental shelves, slopes, abyssal basins, mid-ocean ridges, seamounts and trenches remain real terrain rather than a flat ocean floor.

Rendering may draw a continuous water shell under land because opaque terrain depth hides it; this is much cheaper than rebuilding coastline polygons every terrain update. Near the player, the same water material path can add waves, foam, refraction and shore interaction without changing the authoritative bathymetry.

Physics uses seawater density/viscosity and a sea-level surface for buoyancy. Local rivers/lakes use the same fluid/material system instead of separate special-purpose water physics.

## Meshing preference

For the first playable:
- planet surface: regular indexed patch mesh generated from deterministic displacement;
- local volumetric terrain: start with a correct smooth isosurface extractor;
- evaluate Dual Contouring as the preferred long-term path for better feature preservation and potentially more compact topology;
- keep Marching Cubes as a simpler fallback/reference implementation;
- do not use Greedy Meshing for the production smooth terrain path because it is intended for axis-aligned/block surfaces.

## Sparse field strategy

Untouched terrain should be reproducible from `(planetSeed, position)` and occupy no persistent per-voxel storage.

Only deltas need persistence:
- brush CSG operations,
- deformation stamps,
- sparse field bricks,
- cave/resource metadata when not purely procedural.

A future GPU-friendly sparse hierarchy may borrow ideas from OpenVDB/NanoVDB, but the runtime format should be purpose-built and benchmarked instead of importing a large dependency by default.

## Rendering strategy

- camera-relative GPU coordinates;
- hierarchical double/64-bit CPU reference frames;
- constant/reused patch index topology;
- frustum + horizon culling;
- GPU-driven indirect drawing where measurements justify it;
- task/mesh shader path where supported, with indexed fallback;
- far geometry complexity proportional to projected screen size, not physical planet detail;
- strict CPU/GPU/upload/memory budgets per frame;
- no device-wide GPU idle in normal terrain streaming.

## Non-negotiable visual rule

The player must never see a block-grid aesthetic unless a specific gameplay object intentionally uses it. Natural terrain must read as a continuous sculptable surface from ground level to orbit.
