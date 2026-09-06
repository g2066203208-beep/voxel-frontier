# R24 Planetary Body Runtime

`PlanetaryBodySystem` is the service-level owner that closes the gap between a celestial body and the
planet-scale systems that exist on that same body. It is intentionally built above
`CelestialSystem`; it does not replace N-body physics or the reference-frame architecture.

## Ownership contract

A `PlanetaryBodyDescriptor` creates one celestial body and may attach:

- one `PlanetSurfaceAuthority` for the authoritative solid radius/elevation;
- one `PlanetClimateGrid` for causal local temperature, pressure, humidity, cloud, precipitation and wind;
- one `OceanSpectrum` for an ocean attached to that same solid surface.

The runtime stores the normalized `PlanetDefinition`. Any surface/climate/ocean service uses the
exact `CelestialBody::radiusMeters`; an arbitrary duplicate terrain radius in authored input is not
allowed to diverge.

An ocean cannot exist as a detached render-only water service. If `oceanEnabled` is requested,
`PlanetaryBodySystem` guarantees a solid `PlanetSurfaceAuthority` is also created.

## Time integration

`PlanetClimateGrid::step()` deliberately bounds one numerical update to at most 600 simulated
seconds for stability. Passing a multi-hour `deltaSeconds` once would therefore lose climate time.

`PlanetaryBodySystem::step()` now owns the cross-service synchronization policy:

```text
requested simulated interval
        |
        +-- <= 60 s celestial N-body/spin substep
        |
        +-- recompute current strongest-star body-local direction
        |
        +-- <= 60 s PlanetClimateGrid step
        |
        `-- repeat until the full interval is consumed
```

This makes `step(1200)` numerically equivalent to twenty `step(60)` calls for the celestial and
planet-service integration sequence. It also prevents a whole interval from being forced by only
the final sun direction.

## Unified environment query

`PlanetaryBodySystem::sampleEnvironment(worldPosition)` starts from the celestial environment and
then applies the registered higher-authority planet services:

1. celestial gravity, body ownership and magnetic field remain authoritative from `CelestialSystem`;
2. if a `PlanetSurfaceAuthority` exists, altitude is measured from its actual displaced terrain,
   not from a bare spherical radius;
3. if a `PlanetClimateGrid` exists inside the atmosphere, local solved temperature, pressure,
   density, relative humidity, cloud and precipitation replace the fallback global values;
4. climate wind is converted through `CelestialPhysicsFrame::toWorldVelocity()`, so orbital
   translation and planetary `omega × r` surface motion are added exactly once.

This is the query that gameplay, aircraft, vehicles and later ecology should prefer for registered
planetary bodies. `CelestialSystem::sampleEnvironment()` remains the lower-level fallback for bodies
without planet services.

## Regression gates

`vf_planetary_body_system_tests` checks:

- celestial radius == terrain/surface-service radius;
- surface/climate/ocean service ownership and const access;
- terrain-relative altitude in the unified environment;
- `PlanetClimateGrid` pressure/temperature/humidity overriding fallback celestial atmosphere data;
- a 1200 s direct planetary step matching twenty 60 s steps for orbit/spin/climate state;
- an ocean descriptor cannot create water without an authoritative surface.

The R24 celestial GitHub Actions workflow runs this test as part of the complete core CTest suite and
again inside the explicit R24 celestial/planetary gate set.
