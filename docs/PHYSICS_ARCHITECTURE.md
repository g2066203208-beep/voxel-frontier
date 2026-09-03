# Voxel Frontier — Physics Architecture

## Goal

Voxel Frontier should behave as one coupled physical world rather than a collection of scripted effects. Mass, inertia, momentum, contacts, constraints, atmosphere, wind, liquids, gas chambers, machines, trees, vehicles and aircraft must share physical state and exchange forces through common interfaces.

The production implementation remains custom C++ code. Mature engines, scientific solvers and primary technical references are used as architecture/validation references rather than runtime dependencies.

## Reference baseline

### Rigid-body collision and solver architecture

Primary engineering references:

- Jolt Physics architecture and collision system: https://jrouwe.github.io/JoltPhysics/
- NVIDIA PhysX 5.6 documentation: https://nvidia-omniverse.github.io/PhysX/physx/5.6.0/index.html
- Bullet Physics source/documentation: https://github.com/bulletphysics/bullet3
- Bullet persistent contact manifold documentation: https://pybullet.org/Bullet/BulletFull/classbtPersistentManifold.html
- Erin Catto / Box2D publications: https://box2d.org/publications/
  - Sequential Impulses (GDC 2006)
  - Contact Manifolds (GDC 2007)
  - Computing Distance using GJK (GDC 2010)
  - Understanding Constraints (GDC 2014)
  - Dynamic Bounding Volume Hierarchies (GDC 2019)

Architecture conclusions adopted from these references:

```text
body shapes
 -> broadphase coarse bounds
 -> narrowphase exact primitive / convex tests
 -> persistent contact manifold
 -> iterative velocity/position constraint solver
 -> sleep/island management
```

Jolt explicitly separates AABB broadphase queries from detailed narrowphase shape queries and uses GJK/EPA for general convex narrowphase. Bullet keeps persistent contact caches with up to four points and reduces them while preserving deep/well-spread contacts. Catto's work is the reference for sequential-impulse contact/constraint solving and warm starting.

### Atmosphere and aerodynamics

- NASA metric atmosphere model: https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/earth-atmosphere-equation-metric/
- NASA ideal-gas equation of state: https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/equation-of-state-ideal-gas-2/
- NASA drag equation: https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-equation/
- NASA lift equation: https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/lift-equation/

### Water and buoyancy

- Archimedes principle reference: https://www.grc.nasa.gov/www/k-12/WindTunnel/Activities/buoy_Archimedes.html
- OpenFOAM shallow-water solver family: https://www.openfoam.com/documentation/user-guide/a-reference/a.1-standard-solvers

## Current simulation clock

Authoritative gameplay physics advances at a fixed 120 Hz. Render frame time only feeds an accumulator.

```text
render dt
 -> accumulator
 -> 0..N fixed 1/120 s steps
 -> forces
 -> integrate velocities / orientation
 -> contacts
 -> mechanical constraints
 -> sleep
```

A hard substep cap prevents a long render stall from causing an unbounded catch-up spiral.

## Current rigid bodies

Implemented body state:

- static / dynamic / kinematic motion type
- mass and inverse mass
- diagonal local inertia and world transformed inverse inertia
- world position and quaternion orientation
- linear and angular velocity
- accumulated force and torque
- force-at-point and impulse-at-point application
- linear momentum and kinetic energy diagnostics
- friction, restitution and rolling resistance
- aerodynamic and buoyancy properties
- sleeping state

Integration is semi-implicit/symplectic Euler with angular gyroscopic torque handling.

## Collision status

### Runtime v2 (currently authoritative in `PhysicsWorld`)

- sweep-and-prune broadphase
- sphere body/body contacts
- sphere/planet contact
- restitution
- Coulomb-style friction impulse
- positional penetration correction

This is intentionally not described as a finished production collision system.

### Collision v3 geometry layer (implemented and isolated for validation)

`CollisionGeometry` now defines:

- `Sphere`
- oriented `Box`
- `Capsule`
- exact world AABB generation for these primitives
- support mapping suitable for a later Minkowski/GJK path
- contact manifold storage with capacity for four contacts
- sphere/sphere narrowphase
- sphere/box narrowphase
- sphere/capsule narrowphase
- capsule/capsule narrowphase
- oriented box/box 15-axis separating-axis test

The box/box implementation follows the standard OBB SAT family: three face axes from A, three face axes from B and nine pairwise cross-product axes. It is tested independently before being wired into the live body solver.

### Next collision integration gate

Do not add approximate one-off collision hacks. The next production step is:

1. add a shape to each rigid body while retaining a conservative bounding radius only where useful;
2. generate real AABBs from shape + pose for broadphase;
3. replace sphere-only `solveBodyContacts` generation with `CollisionGeometry` narrowphase;
4. apply contact impulses at contact points so angular response comes from the contact lever arm;
5. cache manifolds by stable body/subshape pair;
6. warm-start cached normal/tangent impulses;
7. reduce contacts to at most four well-spread points;
8. add general convex GJK distance/intersection + EPA penetration depth using the existing support-map API;
9. add box/capsule and arbitrary convex pairs through GJK/EPA rather than an approximation;
10. add CCD/shape casts for high-speed objects.

This order mirrors the separation used by Jolt/Bullet/PhysX and avoids coupling gameplay code directly to collision algorithms.

## Mechanical constraints — implemented

The repository already has:

- distance constraints
- spring/damper constraints
- hinge anchor and axis constraints
- powered hinge motors
- viscous + Coulomb hinge friction
- gear ratio constraints
- break force / break torque limits
- iterative constraint solving
- persistent motor/distance impulses used for warm starting

Still missing from the general constraint library:

- slider/prismatic
- ball/socket
- fixed/weld
- cone/swing-twist
- 6-DOF
- rack/pinion and pulley
- clutch/differential
- wheel suspension/tire contact model

## Planet gravity

Gravity is radial and altitude-aware:

```text
g(r) = g_surface * (R / r)^2
acceleration = -normalize(position - center) * g(r)
```

This supports standing on any side of a spherical planet and continuous ascent toward space.

## Atmosphere and weather — implemented foundation

An atmosphere sample provides:

- temperature [K]
- pressure [Pa]
- density [kg/m^3]
- local wind velocity [m/s]

The baseline uses a lapse-rate/barometric atmosphere plus ideal-gas density and deterministic tangent gusts/storm modulation. Weather state currently includes humidity, cloud cover, precipitation rate, storm intensity and wind multiplier.

Future weather work should evolve low-resolution pressure/temperature/humidity cells rather than scripting rain/wind independently.

## Aerodynamics — implemented foundation

Body-relative air velocity is:

```text
V_rel = body velocity - local wind
q = 0.5 * rho * |V_rel|^2
```

The runtime includes coefficient-based body drag/lift and separate local aerodynamic surfaces with angle-of-attack and finite stall behavior. Future aircraft work should build wings, control surfaces, propellers and rotors from multiple local surfaces/actuator models instead of one global aircraft force.

## Water and buoyancy — implemented foundation

Current body buoyancy uses displaced volume and local gravity. Partial immersion is still evaluated using the body's legacy spherical collision envelope, which must be upgraded after shape integration.

The shallow-water grid is local, conservative and moves water according to hydraulic/free-surface head differences. It is appropriate for gameplay-scale terrain flow; it is not a claim of planet-wide real-time Navier–Stokes fidelity.

Next water integration:

- render authoritative shallow-water surface cells
- couple rainfall to local catchments
- sample several buoyancy points/volumes on hulls
- apply buoyancy and fluid drag at those points to create roll/pitch moments
- let water current impart momentum to bodies
- connect sealed compartments and flooding state to displaced volume

## Gas chambers / pneumatics — implemented foundation

`GasChamber` supports ideal-gas pressure/density, isothermal/adiabatic compression, heat input, pressure force and buoyant lifting force.

Next integration must connect chamber mass/pressure/volume to actual rigid-body compartments so balloons, airships, ballast tanks and pneumatic pistons no longer use independent scripted values.

## Trees and destruction — implemented foundation

The tree model already tracks cut fraction, remaining hinge resistance, trunk mass/geometry, gravity torque, wind torque, angular motion and preferred fall direction.

The current playground automatically advances a demonstration cut. Production interaction still needs:

```text
player/tool collision
 -> cut position + material removal
 -> remaining stump section / strength
 -> hinge release
 -> gravity + wind fall
 -> final fracture
 -> spawn trunk/log rigid bodies
 -> general collision with terrain/objects
```

## Player physics — not yet authoritative

The current player is still `PlanetCamera` motion rather than a rigid-body/capsule controller. This is temporary. The production player should use a capsule shape, sweep/slide contact handling, radial gravity, ground friction, slope/step handling, water forces and vehicle constraints; the camera should follow that physical state.

## Dynamic rendering performance

The current physics playground streams a small dynamic debug mesh. That is acceptable for diagnostics only. Production rigid bodies must move toward reusable static meshes plus per-instance transforms/material IDs, indirect draws and meshlet/GPU culling. Per-frame CPU reconstruction of full triangle meshes must not scale with every mechanical part.

## Performance rules

- physics cost scales with active local bodies/cells, not universe size;
- sleeping bodies do minimal solver work;
- distant planets do not run local rigid bodies/weather/water at full fidelity;
- broadphase bounds are conservative and cheap; narrowphase is paid only for candidates;
- contact manifolds persist so resting stacks do not rediscover contacts from scratch every step;
- full CFD/FEA is not run globally at gameplay frequency;
- GPU visuals are not authoritative gameplay state unless deterministic state transfer is explicitly designed.
