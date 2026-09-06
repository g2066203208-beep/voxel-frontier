# R24 Celestial Architecture

This document defines the production ownership boundaries for the R24 planetary/celestial stack.
It exists to prevent three concepts that look similar but have very different physics from being
collapsed into one coordinate system: orbital inertial hierarchy, rotating local physics, and
render/gameplay clocks.

## 1. Coordinate hierarchy

`CelestialSystem` stores authoritative celestial positions and linear velocities in double-precision
inertial world coordinates. Every `CelestialBody` also receives a runtime `referenceFrameId`.
The frame tree mirrors `orbitParentId`:

```text
inertial root
└─ Helion inertial frame
   └─ Aster inertial frame
      └─ Cinder inertial frame
```

The child frame stores parent-relative translation and velocity. These orbital frames intentionally
do **not** inherit the parent body's daily spin; otherwise a moon's orbit would rotate with the
planet surface once per day.

`ReferenceFrameSystem` supports general nested precision frames and composes:

- parent translation;
- parent rotation;
- parent linear velocity;
- parent angular velocity;
- the `omega × r` velocity term;
- local/world position, vector, orientation and velocity conversions.

Cycles or missing parent frames resolve as invalid states instead of recursing indefinitely.

## 2. Rotating planet-local physics is separate

`CelestialPhysicsFrame` remains the body-fixed rotating frame used for terrain, rigid bodies,
vehicles, aircraft and spacecraft close to a planet or moon. It subtracts orbital translation and
includes rotating-frame kinematics (surface `omega × r`, Coriolis and centrifugal terms).

This separation is deliberate:

```text
ReferenceFrameSystem
  = hierarchy / precision / parent-relative inertial coordinates

CelestialPhysicsFrame
  = rotating body-fixed local rigid-body physics
```

A future surface-cell or city frame may be parented below a planet inertial frame, while nearby
rigid bodies still use `CelestialPhysicsFrame` for contact solving.

## 3. Time ownership

R24 uses two cooperating time layers:

1. `CelestialSimulationClock` (`AstroTime.hpp`) converts wall time and time-warp into bounded,
   deterministic astronomical substeps while retaining excess queued time.
2. `UniverseTime` receives **simulated seconds** and keeps a high-precision `AstroTime` epoch plus
   independent physics, gameplay, weather and climate accumulators.

`CelestialSystem::step(deltaSeconds)` treats its input as simulated time. A direct large call is
fully consumed with orbital substeps no larger than 60 seconds; the old behavior that silently
clamped a call to 60 seconds and discarded the remainder is forbidden.

Default subsystem cadences are:

| subsystem | default cadence |
|---|---:|
| physics schedule | 1/120 s |
| gameplay schedule | 1/60 s |
| weather diagnostics | 60 s |
| global climate diagnostic | 900 s |
| celestial orbit integrator | <= 60 s Verlet substep |

The render loop is not an astronomical clock and should never be used as one.

## 4. Orbit integration

Major bodies remain a Cartesian N-body system integrated with symmetric velocity-Verlet
(kick-drift-kick). `orbitParentId` is an authoring/hierarchy relationship, not a force shortcut:
all massive bodies still perturb all other massive bodies.

Keplerian elements are only an initial-state authoring representation. Once converted to Cartesian
position/velocity, runtime motion is integrated dynamically.

## 5. Gravity ownership

R24 physical gravity is one Newtonian vector field. The legacy names
`gravityAccelerationAt()`, `gameplayGravityAccelerationAt()` and
`physicalGravityAccelerationAt()` remain for compatibility, but they now resolve to the same
superposed physical field.

`physicsBubbleRadiusMeters` and legacy influence-radius fields select local coordinate/streaming
ownership; they do not delete gravity. `gravityAccelerationRelativeTo()` subtracts external
common-mode acceleration at a planet-frame origin so local rigid-body physics keeps real local
gravity and tides without inheriting the planet's orbital acceleration.

## 6. Climate/weather ownership

`CelestialClimate` is only a low-cost global radiative-equilibrium diagnostic. It updates on the
multi-rate climate schedule.

Dynamic local weather belongs to `PlanetClimateGrid`, whose documented forcing includes solar
zenith, longwave cooling, surface heat capacity, moisture phase change, pressure gradients,
Coriolis acceleration and drag. `CelestialSystem` therefore does not synthesize a
`sin(simulationTime)` weather oscillator. The per-body `CelestialWeather` values are fallback /
authoring diagnostics and are only sanitized for numeric validity.

## 7. Regression guarantees

`CelestialSystemTests.cpp` now checks all of the following in addition to the older gravity,
atmosphere, orbit, magnetic-field and rotating-ground tests:

- nested reference-frame rotation and `omega × r` velocity composition;
- local/world position and velocity round trips;
- Sun/planet/moon reference-frame parenting;
- reference-frame synchronization after celestial integration;
- high-precision astronomical epoch retention;
- deterministic multi-rate tick counts;
- large celestial steps consume their complete simulated duration rather than dropping time.

`.github/workflows/r24-celestial-architecture.yml` builds the full native core test suite on every
R24 source change with the Vulkan runtime disabled, so architecture changes are compile- and
regression-gated before local Windows/Vulkan visual testing.

## 8. Next architecture boundaries

After this closure, the next safe extensions are:

1. bind `PlanetaryBodySystem` definitions explicitly to celestial body ids and surface authorities;
2. expose `PlanetClimateGrid` through the planet entity rather than constructing it ad hoc in the
   application layer;
3. add streaming surface/city frames below the inertial planet frame;
4. keep vehicles/aircraft/spacecraft switching through `CelestialPhysicsFrame`, never by changing
   the authoritative celestial coordinates;
5. add interpolation snapshots between astronomical fixed steps for visually smooth high time-warp
   rendering without changing the physics integrator.
