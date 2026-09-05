#include "vf/player/PlanetCamera.hpp"

// Keep every V14 movement/reference-frame implementation byte-for-byte; only the public class name
// is adapted so PlanetCamera can add deterministic safe-spawn policy without rewriting 24 kB of
// proven camera code.
#define PlanetCamera PlanetCameraV14
#include "PlanetCameraV14.inc"
#undef PlanetCamera
