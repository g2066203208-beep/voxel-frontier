# R24 Unified Planetary Physics

R24 is a convergence pass: terrain, water, atmosphere, gravity and celestial light must stop being independent visual tricks and become one queryable physical world.

## External references used before implementation

- Eric Bruneton, *Precomputed Atmospheric Scattering: a New Implementation* (2017): reusable planetary atmosphere formulation, real solar spectrum support, ozone and tests. https://ebruneton.github.io/precomputed_atmospheric_scattering/
- Epic Games, *Niagara Fluids / Fluid Simulation Overview*: shallow-water height fields are appropriate for broad real-time water surfaces, while 3-D FLIP is reserved for local high-cost liquid interactions. https://dev.epicgames.com/documentation/unreal-engine/fluid-simulation-in-unreal-engine---overview
- Epic Games, *Water System*: one water-body pipeline should serve rendering, physics, ripples and wakes instead of disconnected surface and gameplay representations. https://dev.epicgames.com/documentation/unreal-engine/water-system-in-unreal-engine
- NASA Earth Observatory, *Climate and Earth’s Energy Budget*: about 29% of incoming solar energy is reflected, about 23% absorbed by atmosphere and about 48% absorbed at the surface; equilibrium requires outgoing thermal radiation plus convection/latent heat to balance absorbed energy. https://science.nasa.gov/earth/earth-observatory/climate-and-earths-energy-budget/
- ECMWF IFS documentation and primitive-equation practice: horizontal pressure-gradient, Coriolis and physical tendencies are the correct causal source of atmospheric motion; a fixed authored wind vector is not a weather model. https://www.ecmwf.int/en/publications/ifs-documentation
- JONSWAP deep-water spectrum: R24 uses a finite deterministic JONSWAP-shaped packet for shared physics/render wave state. It is not yet a GPU FFT ocean; the architecture keeps the spectrum explicit so a Tessendorf/FFT implementation can replace the sampler without changing gameplay queries.
- Cesium Native terrain selection principles: screen-space geometric error and hierarchical patch selection are the target for R24 terrain LOD; square distance rings are a temporary R23 artifact and are not the final planetary LOD contract.
- REBOUND/WHFast is the long-duration celestial validation target. Runtime R24 keeps fixed celestial substeps while the gravity law is moved back to physical inverse-square behavior; reference-frame bubbles are precision/streaming domains, never gravity cutoffs.

## New contracts

### PlanetSurfaceAuthority

`PlanetSurfaceAuthority` is the only allowed final solid-surface height query. The global deterministic terrain is the base. If a regional Priority-Flood hydrology bake is present, its incision becomes part of the same height returned to renderer, collision and ecology. This removes the R23 failure where a visible river valley could be lower than the collision surface.

### PlanetClimateGrid

A low-resolution global field advances temperature, moisture and horizontal wind from physical causes:

1. local solar zenith angle and stellar irradiance set incoming shortwave energy;
2. atmosphere/cloud/surface albedo determine reflected and absorbed shortwave energy;
3. Stefan-Boltzmann longwave cooling with a grey one-layer greenhouse term removes heat;
4. ocean and land use different surface heat capacities;
5. horizontal thermal diffusion transports heat;
6. temperature/geopotential gradients accelerate air;
7. Coriolis acceleration and Rayleigh drag turn and limit the flow;
8. evaporation, saturation and condensation create humidity, cloud and precipitation.

This is a game-budget reduced climate model, not a claim to reproduce ECMWF forecasts. Its important property is causality: no `sin(time)` weather clock and no arbitrary world-space prevailing wind are required.

### OceanSpectrum

The ocean physics sampler uses the standard deep-water dispersion relation `omega^2 = g k` and a discrete JONSWAP-shaped frequency spectrum normalized so `Hs = 4 sigma`. A later Vulkan FFT path should consume the same spectrum parameters. Near-shore rivers/lakes remain a shallow-water problem; local splashes can use FLIP/particles.

## R24 gates

- hydrology displacement must be identical through the final surface authority;
- illuminated climate cells must warm relative to night-side cells under the same initial state;
- pressure/thermal gradients must create non-zero winds without authored gust sine waves;
- the wave spectrum must reproduce configured significant wave height within the discrete tolerance;
- physical gravity must remain inverse-square outside the atmosphere; physics/reference bubbles may not change the law;
- every runtime change must still retain real Vulkan framebuffer evidence, including failed/blank captures.
