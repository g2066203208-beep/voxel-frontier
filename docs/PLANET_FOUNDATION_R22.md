# Voxel Frontier — Planet Foundation R22

## Authority

- Production authority remains `main` until a reviewed/green integration is merged.
- R16–R21 are experimental terrain/celestial branches and evidence history, not production authority.
- R21 is a descendant of the current `main`, but it must not be merged wholesale: it contains revision-specific materialization scripts, evidence workflows, screenshot camera logic, and a monolithic experimental geomorph bake.
- R22 starts cleanly from `main` and selectively promotes only validated mechanisms.

## Scientific/gameplay contract

The planet is not an independent terrain noise generator. The intended causal graph is:

```text
star mass/radius/luminosity/spectrum
        +
orbital elements + epoch
        +
rotation period + obliquity
        +
atmosphere + hydrosphere
        -> radiative forcing / seasonality / circulation surrogate
        -> temperature / wind / moisture / precipitation / snow-ice

planet mass/radius/age/interior heat/composition
        -> tectonic activity / crust / plate kinematics / volcanism

tectonics + climate + hydrology + ice + lithology + time
        -> geomorphology
        -> final DEM / local terrain / materials / ecology
```

Random fields may seed reproducible initial conditions and unresolved residual detail. They may not directly choose the existence/location of a mountain, river, coast, plateau, glacier, or desert when a modeled physical driver exists.

## Gate A — celestial mechanics (this PR)

Promote from R21 only:

1. Keplerian elements -> inertial Cartesian state at an authored epoch.
2. Pairwise Newtonian gravity for celestial propagation.
3. Second-order kick-drift-kick leapfrog / velocity-Verlet stepping with bounded substeps.
4. Regression tests including the vis-viva specific-energy identity.

Do not merge the old parent-only sequential Euler orbital updater back into the runtime path.

Validation must cover:

- Linux and Windows builds/tests;
- bounded two-body orbital-radius/energy error over long intervals;
- total linear momentum / barycentre invariance for an isolated N-body system;
- Earthlike star-planet and planet-moon periods within declared tolerances;
- spin orientation evolution independent from translational orbit integration.

Reference implementation anchor: REBOUND documents LEAPFROG as a standard second-order symplectic N-body integrator: https://rebound.hanno-rein.de/integrators/leapfrog/

## Gate B — physical system preset

Replace ad-hoc celestial setup in `Main.cpp` with a reusable authored physical profile/preset. For the Earthlike test world, it must contain at minimum:

- star: mass, radius, luminosity;
- planet: mass, mean radius, sidereal rotation period, obliquity, albedo/greenhouse inputs;
- orbit: semi-major axis, eccentricity, inclination, node, periapsis argument, mean anomaly/epoch;
- moon: mass, radius, inclined eccentric orbit, sidereal/synchronous spin definition;
- barycentric initialization after composing the system.

The rendering representation may use camera-relative/local proxy meshes for precision, but body direction, angular size, illumination, and motion must derive from the physical state.

## Gate C — climate forcing interface

`CelestialSystem::stellarIrradianceAt()` already provides physically scaled stellar flux. The next interface must additionally expose local/seasonal forcing needed by terrain/climate:

- substellar direction in planet body coordinates;
- latitude and solar declination;
- local day length / daily-mean insolation;
- orbital distance and season phase;
- angular rotation rate / Coriolis scale;
- surface gravity and atmospheric column inputs.

The current sinusoidal transient weather and latitude+FBM geomorph rainfall are not acceptable as the authority for long-term terrain climate.

Scientific anchor: Adams et al. (2025), 93 ROCKE-3D Earth-analog GCMs, shows climate outcomes depend strongly on rotation period, obliquity, eccentricity and longitude of periapsis: https://www.giss.nasa.gov/pubs/abs/ad05100p.html

## Gate D — geomorph architecture cleanup

Do **not** promote R21 `PlanetGeomorph.hpp` wholesale. Split the global process bake into testable modules/data products:

1. plate/crust authority;
2. tectonic forcing (convergence/divergence/uplift/trench/ridge/volcanism);
3. lithology/hardness;
4. climate forcing fields;
5. depression handling;
6. flow routing/accumulation;
7. fluvial erosion/deposition;
8. thermal hillslope relaxation;
9. derived landform metrics/masks.

Hydrology anchors:

- Barnes, Lehman & Mulla (2014), Priority-Flood depression filling: https://doi.org/10.1016/j.cageo.2013.04.024
- Freeman (1991), multiple-flow-direction divergent catchment routing: https://doi.org/10.1016/0098-3004(91)90048-I

Demiurge is a useful MIT-licensed implementation reference for a bake-and-query procedural planet, but its code/parameters are not scientific authority and must not be copied blindly: https://github.com/owenyuwono/demiurge

## Gate E — geometry-first landform acceptance

A semantic mask is never enough to claim a landform exists. Evidence selection and tests must measure final DEM geometry.

- mountain: coherent ridge/peak network plus kilometre-class local relief at Earth scale;
- river: continuous downhill drainage/channel path with contributing area and an actual channel/valley geometry at the rendered scale;
- coast: measured sign change across the final sea-level DEM (submerged and emergent terrain in the same local neighbourhood);
- plateau: broad high low-relief interior plus a measurable escarpment/drop to lower terrain;
- glacier: temperature/accumulation/ablation-compatible ice domain, not latitude alone.

Every experimental visual revision must retain real Vulkan evidence even when it fails visually.

## Repository hygiene

- Do not add a new materialize workflow for every terrain revision.
- Keep one reusable visual-regression/evidence workflow with parameterized capture modes.
- Do not put screenshot-only camera behavior into the production runtime path.
- Keep `main` free of abandoned parallel engines and revision-specific scripts.
- Remove stale README claims when the corresponding production behavior has been retired.

## R22 completion definition

R22 is complete only when:

1. Gate A is green on Linux + Windows and has long-horizon conservation tests;
2. Earthlike Sun/Aster/Luna initialization is moved into a reusable physical-system definition and is barycentric;
3. the planet definition exposes the physical inputs required by the climate/terrain causal chain;
4. long-term terrain rainfall/temperature no longer come from arbitrary latitude+noise formulas;
5. geomorph bake is modular rather than a 700+ line header-only subsystem;
6. mountain/river/coast/plateau evidence uses final geometry metrics and real Vulkan captures;
7. only then is the cleaned R22 branch eligible to replace the relevant experimental R21 work in `main`.
