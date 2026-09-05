# Runtime visual evidence

This directory is the permanent review record for runtime test rounds.

Rules:

1. Evidence must be captured from the actual tested Vulkan runtime framebuffer. Generated or concept images are never accepted as test evidence.
2. Every runtime test round stores screenshots even when they look bad, are flat, are poorly framed, or expose a bug. Bad evidence is still useful evidence and must not be hidden.
3. Each round uses its own directory named by round/commit/date and contains screenshots plus `capture-info.txt` and the relevant runtime/Vulkan logs when available.
4. Terrain/geomorphology work must include views that actually show the morphology being tested. A horizon-only or ground-only frame is preserved as a failed capture and then followed by a corrected capture.
5. Celestial-motion work must include multiple timestamps or before/after frames from a fixed camera. A single Sun or Moon screenshot does not prove motion.
6. CI artifacts are supplemental. The screenshots the user is asked to review must also be committed here.

Initial imported evidence:

- `r21-legacy-2026-09-05/`: actual R21 Vulkan terrain/celestial screenshots from the earlier evidence run. They are intentionally preserved even though several are poor captures.
- `r22-bc88ea95/`: actual R22 Vulkan ground/traversal/aerial framebuffer captures and logs from the clean-mainline PR test.

Future rounds should add a new directory instead of overwriting old evidence.
