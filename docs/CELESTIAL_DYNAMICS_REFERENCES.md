# Celestial dynamics references

This document records the production references and implementation boundary for Voxel Frontier's celestial-motion layer. It is deliberately narrower than the terrain/visual experiment notes from R16-R21.

## 1. Orbital elements are an initial-state representation

Voxel Frontier accepts classical Keplerian/orbital elements as an authoring representation and converts them to an inertial Cartesian position/velocity at the authored epoch. After initialization, runtime motion is propagated in Cartesian space.

Authoritative references:

- NASA GMAT Mathematical Specifications, section 4.1.3, "Keplerian Elements to Cartesian State". The GMAT documentation explicitly treats the transformation as `a, e, i, Ω, ω, ν/mean-anomaly-derived anomaly -> r, v`.
  - https://ntrs.nasa.gov/api/citations/20080031744/downloads/20080031744.pdf
- NASA Science, "Basics of Space Flight – Planetary Orbits", describing the six orbital elements used to specify an orbit.
  - https://science.nasa.gov/learn/basics-of-space-flight/chapter5-1/
- JPL Solar System Dynamics FAQ, explaining that orbital elements describe an osculating orbit at a specified epoch and that two-body propagation can diverge from actual perturbed trajectories, especially as time from the epoch increases.
  - https://ssd.jpl.nasa.gov/faq.html
- JPL Horizons documentation, which exposes both Cartesian state vectors and osculating orbital-element tables as representations of the same celestial state.
  - https://ssd.jpl.nasa.gov/horizons/manual.html

Production consequence:

- `KeplerianElements` is not a permanent animation track.
- `keplerianState()` produces an inertial `OrbitalState`.
- Runtime celestial bodies then evolve under the same N-body Cartesian integration as every other massive body.

## 2. Newtonian mutual gravity, not parent-only Euler motion

The old production step advanced only a body's `orbitParentId` relationship with a sequential velocity/position update. That makes the parent immutable and prevents mutual perturbation.

R22 replaces that step with pairwise Newtonian acceleration:

```text
a_i += G m_j (r_j - r_i) / |r_j - r_i|^3
a_j -= G m_i (r_j - r_i) / |r_j - r_i|^3
```

The gameplay gravity system remains separate: finite game gravity wells, atmosphere ownership, and local planet-centered physics frames are still allowed for gameplay stability. The N-body propagator operates only on celestial-body inertial position/velocity.

## 3. Velocity-Verlet / kick-drift-kick integration

The runtime uses a symmetric velocity-Verlet step:

```text
v(t+h/2) = v(t) + 0.5 h a(t)
r(t+h)   = r(t) + h v(t+h/2)
v(t+h)   = v(t+h/2) + 0.5 h a(t+h)
```

Reference:

- W. C. Swope, H. C. Andersen, P. H. Berens, K. R. Wilson (1982), Journal of Chemical Physics 76(1), 637–649, DOI 10.1063/1.442716. This is the standard velocity-Verlet formulation used for Hamiltonian particle dynamics.
- HALMD documentation provides the same half-kick / drift / half-kick equations and identifies velocity Verlet as a symplectic integrator.
  - https://halmd.org/doc/testing/modules/mdsim/integrators/verlet.html

Production boundary:

- R22 preserves the pre-existing `CelestialSystem::step()` safety contract: one call advances at most 60 simulated seconds.
- R21's experiment-only allowance of up to four simulated days per call was not promoted because, with 60-second substeps, a single caller error or extreme time warp could force thousands of O(N^2) celestial substeps in one frame.
- Long-duration/high-accuracy ephemeris is not the goal of this gameplay runtime. If that becomes a requirement, it should be a separate measured subsystem rather than silently increasing per-frame work.

## 4. Permanent regression gates

`native/tests/CelestialSystemTests.cpp` now permanently checks:

- existing surface gravity / atmosphere ownership behavior;
- free interplanetary gameplay gravity behavior;
- bounded orbital motion and spin;
- Keplerian-state vis-viva energy identity;
- mutual movement of two massive bodies, proving the propagator is no longer parent-only;
- magnetic dipole falloff;
- rotating-surface velocity transfer into rigid-body contact.

The permanent CI paths are:

- `.github/workflows/native-desktop.yml` — Linux core tests + Windows runtime/tests;
- `.github/workflows/visual-vulkan.yml` — real Vulkan framebuffer regression using Mesa Lavapipe/Xvfb and uploaded ground/traversal/aerial captures.

One-shot R16-R21 materialization/capture workflows are not part of the R22 mainline design.