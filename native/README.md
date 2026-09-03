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

## Engine core

The current native core includes:

- fixed-step rigid-body physics
- sphere / box / capsule / convex-hull collision geometry
- GJK/EPA convex narrow phase
- persistent sequential-impulse contacts
- spring/damper, hinge, gear and distance constraints
- spherical planetary gravity and finite gameplay gravity fields
- per-body atmosphere/weather/magnetic/environment samples
- shallow water, buoyancy and gas helpers
- XPBD rope and tree physics
- low-cost spectral optics and electromagnetic/radiation helpers
- double-precision celestial orbit/spin state with planet-local precision frames

The preview branch remains a test branch until hardware behavior is verified in the actual Windows/Vulkan runtime.
