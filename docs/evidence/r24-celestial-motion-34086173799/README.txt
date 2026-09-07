R24 celestial motion closure — real Vulkan framebuffer evidence

space-spin/: fixed inertial observer, real Aster mesh, 7200x simulated time. The body uses the same
production dvec3 N-body state and dquat spin; the sequence is intended to expose frozen/jumping frames.

escape/: production PlanetCamera starts 5 km inside the real Aster precision-bubble edge and crosses
it through ordinary flight input. After input release the camera is not target-teleported or moved by
a capture script. Its world velocity must retain the parent's orbital carrier rather than being damped
toward zero. runtime-summary.txt records frame ownership, inherited orbital component and effective
free-space time scale.

failed-captures/: all startup black/low-information frames are intentionally preserved.
