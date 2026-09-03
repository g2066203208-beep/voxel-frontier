# Voxel Frontier — Physics Architecture

## Goal

The world should behave like a coupled physical system rather than a set of scripted animations. Objects carry mass, inertia, momentum and material properties. The planet provides radial gravity, atmosphere, wind, temperature, pressure and liquids. Machines, trees, vehicles, balloons, boats and aircraft should all use the same underlying state instead of bespoke per-feature hacks.

The production physics remains custom C++ code. Mature engines and scientific tools are reference/validation sources, not runtime dependencies.

## Reference projects and equations

### Real-time rigid-body architecture

- NVIDIA PhysX 5.6 documentation: https://nvidia-omniverse.github.io/PhysX/physx/5.6.0/index.html
- Jolt Physics: https://github.com/jrouwe/JoltPhysics
- Bullet Physics: https://github.com/bulletphysics/bullet3
- Project Chrono multiphysics: https://www.projectchrono.org/

These provide comparison points for rigid bodies, sleeping, broadphase/narrowphase collision, contact constraints, joints, vehicles and multibody mechanisms.

### Atmosphere and aerodynamics

- NASA metric atmosphere model: https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/earth-atmosphere-equation-metric/
- NASA ideal-gas equation of state: https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/equation-of-state-ideal-gas-2/
- NASA drag equation: https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-equation/
- NASA lift equation: https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/lift-equation/

Current real-time force model uses dynamic pressure `q = 0.5 * rho * V^2` and coefficient-based drag/lift. Full CFD is intentionally not run around every object every frame.

### Buoyancy and water

- NASA Archimedes principle reference: https://www.grc.nasa.gov/www/k-12/WindTunnel/Activities/buoy_Archimedes.html
- OpenFOAM shallow-water solver reference: https://www.openfoam.com/documentation/user-guide/a-reference/a.1-standard-solvers

Buoyancy is computed from displaced fluid volume and local gravity. Large-scale local surface-water transport uses a conservative height-field/shallow-water style model. High-detail splashes and waves will be a separate GPU visual/interaction layer rather than a planet-wide 3D CFD solve.

## Fixed simulation clock

Physics advances at a fixed 120 Hz independent of render FPS:

```text
render frame dt
    -> accumulator
        -> 0..N fixed physics substeps
            -> forces
            -> velocity/inertia integration
            -> contacts/constraints
            -> sleeping
```

This keeps mechanical behavior deterministic enough for debugging and avoids changing gravity/friction response when frame rate changes.

## Rigid bodies

Each dynamic body owns:

- mass and inverse mass
- local inertia tensor diagonal and world-space transformed inertia
- position and quaternion orientation
- linear and angular velocity
- accumulated force and torque
- friction, restitution and rolling resistance
- aerodynamic reference properties
- displaced fluid volume and fluid drag properties
- awake/sleep state

The v1 integrator is semi-implicit/symplectic Euler. Angular integration includes the gyroscopic `omega x (I omega)` term. Collision v1 uses sphere bounds for body-body and planet contact, with impulse response and Coulomb-style friction limits. Production evolution will add broadphase, convex shapes, GJK/EPA/SAT, persistent manifolds and iterative warm-started constraints.

## Planet gravity

Gravity is radial and altitude-aware:

```text
g(r) = g_surface * (R / r)^2
acceleration = -normalize(position - planetCenter) * g(r)
```

This supports standing on any side of a spherical planet and naturally weakens gravity during ascent to space.

## Atmosphere, pressure, density and weather

Atmospheric state is sampled from position and time. The current baseline uses a lapse-rate/barometric model and ideal-gas density, then adds a deterministic tangent wind field with gust and storm modulation.

Per-point sample:

```text
AtmosphereSample
- temperature [K]
- static pressure [Pa]
- density [kg/m^3]
- wind velocity [m/s]
```

Weather state owns humidity, cloud cover, precipitation rate, storm intensity and wind multiplier. Later milestones will stream low-resolution weather cells over each planet and evolve pressure/temperature/humidity fronts asynchronously.

## Aerodynamics

A body experiences air-relative velocity:

```text
V_rel = bodyVelocity - windVelocity
q = 0.5 * rho * |V_rel|^2
Drag = q * Cd * A
Lift = q * Cl * A
```

This is suitable for aircraft, parachutes, sails, rotor/wing approximations and wind loading on trees/buildings. Later aircraft work should use multiple aerodynamic surfaces with local angle of attack, stall curves, control surfaces, propeller/rotor momentum models and compressibility corrections where needed.

## Water and buoyancy

A sealed/displacing body receives:

```text
F_buoyancy = rho_fluid * displacedVolume * |g|
```

Partial submergence currently uses a spherical-cap fraction for the body's collision sphere. Water-relative quadratic drag is also applied.

The local shallow-water grid conserves water volume and moves water according to hydraulic-head differences, so water naturally propagates from higher free-surface potential toward lower terrain. This is a gameplay-scale model, not a claim of full Navier–Stokes fidelity.

## Gas chambers and pneumatics

`GasChamber` implements ideal-gas pressure and density, isothermal/adiabatic compression, heat input, piston pressure force and buoyant lifting force. This is the basis for:

- balloons and airships
- sealed boat/submarine compartments
- ballast and variable-buoyancy devices
- compressed-air pistons
- pressure tanks and pneumatic machines
- flooding/air-loss gameplay later

## Trees and destructible physical objects

Trees are not intended to play a canned fall animation. The current tree model tracks trunk mass, length, cut fraction, remaining hinge resistance, gravitational torque, wind drag torque, angular velocity and fall direction.

Production path:

```text
standing rooted tree
 -> cut weakens stump section
 -> hinge dynamics released
 -> gravity + wind generate torque
 -> trunk rotates/falls
 -> final break spawns general rigid-body trunk/log segments
 -> branches/logs collide with terrain and other objects
```

## Mechanical systems roadmap

Next rigid-mechanics layers:

1. broadphase spatial acceleration and persistent contacts
2. convex/compound collision shapes
3. sequential-impulse constraint solver with warm starting
4. hinge, slider, ball, fixed and distance constraints
5. springs, dampers, motors, gears and clutches
6. wheel/tire and suspension forces
7. articulated machines and construction vehicles
8. aerodynamic surfaces, propellers, rotors and engines
9. breakable joints and structural load limits
10. network-friendly deterministic state replication

The objective is one shared physics graph: a motor drives a shaft, a gearbox changes torque, wheels exchange friction impulses with terrain, a vehicle body feels wind and gravity, a boat displaces water, a gas chamber changes buoyancy, and damage can break the same constraints that transmit load.

## Performance rules

- Physics cost is bounded by active local objects, not by the theoretical size of the universe.
- Sleeping bodies do almost no solver work.
- Distant planets do not simulate local rigid bodies/weather/fluid cells at full fidelity.
- Physics uses fixed-step job batches; rendering interpolates state.
- Full CFD/FEA is not run globally in real time. Reduced-order physically based models handle gameplay, with high-fidelity offline models used to validate coefficients/behavior where useful.
- GPU water/weather visuals must not become authoritative gameplay state unless deterministic readback/state transfer is designed explicitly.
