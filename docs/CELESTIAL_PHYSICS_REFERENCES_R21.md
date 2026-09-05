# R21 Celestial / Planet Physics Reference Chain

This file records the scientific basis used for the R21 native implementation. The runtime remains game-optimized, but orbital state, gravity, spin and visible angular size are derived from physical quantities rather than scripted sky motion.

## Authoritative references

- NASA/JPL Solar System Dynamics, **Description of Orbits and Ephemerides**: https://ssd.jpl.nasa.gov/orbits_doc.html
- NASA/JPL Solar System Dynamics, **Astrodynamic Parameters (DE440 GM values)**: https://ssd.jpl.nasa.gov/astro_par.html
- NASA/JPL Solar System Dynamics, **Planetary Physical Parameters**: https://ssd.jpl.nasa.gov/planets/phys_par.html
- NASA/JPL Solar System Dynamics, **Planetary Satellite Physical Parameters**: https://ssd.jpl.nasa.gov/sats/phys_par/
- NASA Science, **Earth Facts**: https://science.nasa.gov/earth/facts/
- NASA Science, **Moon Facts**: https://science.nasa.gov/moon/facts/
- NASA NAIF, **SPICE Toolkit**: https://naif.jpl.nasa.gov/naif/toolkit
- NASA GISS, **ROCKE-3D 2.0**: https://www.giss.nasa.gov/pubs/abs/ts02400q.html
- Held & Hou (1980), *Nonlinear Axially Symmetric Circulations in a Nearly Inviscid Atmosphere*, JAS 37(3), DOI 10.1175/1520-0469(1980)037<0515:NASCIA>2.0.CO;2.

## Mature open-source engineering reference

- Tudat / TudatPy: https://github.com/tudat-team/tudatpy

The project does not copy Tudat or SPICE code. They are implementation/validation references for the separation between state propagation, reference frames, ephemerides and local gameplay physics.

## Equations implemented

### Newtonian N-body gravity

For body i:

    a_i = G * sum_{j != i} m_j (r_j - r_i) / |r_j-r_i|^3

The celestial integrator uses a kick-drift-kick / velocity-Verlet step. This is symplectic for the conservative Newtonian system and is materially more stable for long bound orbits than the previous per-body forward/semi-implicit Euler parent pull.

### Keplerian element initialization

Elliptic initial states use:

    M = E - e sin(E)
    x_p = a(cos E - e)
    y_p = a sqrt(1-e^2) sin E

and the corresponding perifocal velocity, followed by rotations through argument of periapsis, inclination and longitude of ascending node into the inertial frame.

The element set initializes the state only. Once the simulation starts, positions/velocities are propagated by N-body gravity, so the orbit is a trajectory and can be perturbed, consistent with JPL's description of real solar-system motion.

### Rotation

A rigid body's orientation is integrated from angular speed omega about a normalized spin axis. Aster uses the terrestrial sidereal rotation period and axial tilt. Luna uses the lunar sidereal period for synchronous rotation.

### Angular-size-preserving rendering

The physical Sun/Moon remain at physical positions and radii. For floating-point-safe local rendering, their sky meshes are visual proxies whose angular radius is preserved:

    alpha = asin(R / d)
    R_visual = tan(alpha) * d_visual

Thus the mesh is not a physics substitute or an arbitrary sky balloon: apparent size comes from the real radius and instantaneous physical distance.

### Uniform game time acceleration

The runtime can multiply simulation time by a single dimensionless time-scale. This does not change G, masses, orbital periods relative to one another, axial tilt or the equations of motion; it only maps real player seconds to simulation seconds so day/night and the Moon are observable during gameplay.

## Earth-like baseline constants used by R21

- Sun mass: 1.98847e30 kg
- Sun radius: 696,340 km
- Solar luminosity: 3.828e26 W
- Aster/Earth mean radius: 6371.0084 km
- Aster/Earth mass: 5.97217e24 kg
- Aster sidereal rotation: 0.99726968 d / 86164.0905 s
- Aster axial tilt: 23.4393 deg
- Aster orbit semi-major axis: 149,598,262 km
- Aster orbit eccentricity: 0.01671123
- Luna/Moon mean radius: 1737.4 km
- Luna/Moon mass: 7.34767309245735e22 kg (NASA Earth/Moon comparison value)
- Luna mean orbit distance: 384,400 km
- Luna orbit eccentricity: 0.0549
- Luna orbit inclination to ecliptic: 5.145 deg
- Luna sidereal orbital/rotation period: 27.32 d (implemented as 27.321661 d)

The initial orbital phase is an authored epoch choice; it does not change the above physical scale or propagation law.
