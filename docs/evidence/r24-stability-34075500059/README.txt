R24 runtime stability evidence — real Vulkan framebuffer only

- ground/ground-spin-*.png: accelerated planet rotation while the player remains on the surface.
  Terrain and local props should remain fixed relative to the camera; lighting/shadows may change.
- shadows/contact-ground.png: downward ordinary-time contact-shadow/ecology placement inspection.
- space/earth-spin-*.png: inertial external observer; physical planet self-rotation remains visible.
- high-speed/*.png: production PlanetCamera flight plus real SDL forward input at a configured
  500 km/s target; runtime-summary must prove smooth-globe fallback.
- failed-captures/: every startup black/low-information framebuffer attempt is intentionally kept.
- runtime-summary.txt: streaming/mode/FPS/fatal diagnostics captured from the tested executable.

Bad, blank, ugly, detached-shadow or low-information frames are deliberately retained.
