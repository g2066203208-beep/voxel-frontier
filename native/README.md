# Voxel Frontier Native

Native C++23 / SDL3 / Vulkan gameplay runtime.

## Windows quick start

From VS Code use the provided **Voxel Frontier - Debug** launch configuration, or run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-game.ps1
```

The launcher configures, builds, runs CTest, and only then starts the executable.

## Current preview controls

- **W / A / S / D** — move
- **Shift** — faster movement
- **Space** — jump while grounded / ascend while creative flight is enabled
- **Ctrl** — descend while creative flight is enabled
- **Double-tap Space** — toggle Minecraft-style creative flight
- **Right click** — pick up the nearest loose dynamic physics object; right click again to drop it
- **Left click while holding an object** — throw it in the view direction
- **Esc** — release/capture the mouse

Constrained machine components are deliberately not pickable. A held loose body temporarily becomes kinematic; dropping or throwing restores normal dynamic simulation.

## Planet-local physics preview

The nearby Aster gameplay scene is simulated in an Aster-local precision space rather than in star-centric 45 km coordinates. Celestial orbit/spin remains in double-precision inertial world space, while terrain contacts, sleeping loose bodies, ropes, mechanisms and grabbed props stay in small local coordinates. This avoids feeding orbital translation through ordinary ground contact solving and avoids large-world float cancellation in debug rendering.

Creative flight bypasses gravity but **does not bypass solid planet surfaces**. Descending into the terrain clamps the camera to the same surface used for walking/jumping; disabling flight while touching the surface returns to `Grounded`.

## R24 celestial architecture

R24 now has two deliberately separate frame layers:

- `ReferenceFrameSystem` mirrors the inertial star → planet → moon hierarchy and supports nested translation, rotation, linear/angular velocity, `omega × r`, and local/world conversions.
- `CelestialPhysicsFrame` is the rotating body-fixed frame used for nearby terrain and rigid-body simulation.

Every `CelestialBody` receives a runtime inertial `referenceFrameId` that is synchronized after orbital integration. Planet spin is **not** inserted into the orbital parent hierarchy, so moon/planet orbits cannot accidentally rotate with a parent's day/night cycle.

Time is also split by responsibility. `CelestialSimulationClock` converts wall time/time-warp into deterministic astronomical substeps; `UniverseTime` records a high-precision astronomical epoch and independent physics/gameplay/weather/climate schedules. `CelestialSystem::step()` consumes an entire requested simulated interval in <=60 s Verlet substeps, rather than silently dropping everything after the first 60 seconds.

The detailed contract is documented in [`../docs/R24_CELESTIAL_ARCHITECTURE.md`](../docs/R24_CELESTIAL_ARCHITECTURE.md).

## Engine core

The current native core includes:

- fixed-step rigid-body physics
- sphere / box / capsule / convex-hull collision geometry
- GJK/EPA convex narrow phase
- persistent sequential-impulse contacts
- spring/damper, hinge, gear and distance constraints
- spherical planetary gravity with one unified Newtonian celestial field
- per-body atmosphere/weather/magnetic/environment samples
- causal low-resolution `PlanetClimateGrid` weather/climate forcing (no synthetic time sine weather oscillator)
- shallow water, buoyancy and gas helpers
- XPBD rope physics
- low-cost spectral optics and electromagnetic/radiation helpers
- double-precision N-body celestial orbit/spin state
- hierarchical inertial celestial reference frames plus rotating planet-local physics frames
- high-precision astronomical epoch and multi-rate subsystem scheduling

The old tree-specific prototype and its standalone physics playground were removed from the authoritative source tree. Future vegetation, cutting and destruction must be built on the generic material/fracture and rigid-body systems rather than reintroducing a special-case tree simulator.

The preview branch remains a test branch until hardware behavior is verified in the actual Windows/Vulkan runtime.
