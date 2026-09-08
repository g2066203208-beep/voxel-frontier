# Third-party data

## Default master human mesh

- Source project: NAVER Anny — https://github.com/naver/anny
- Runtime file: `src/anny/data/mpfb2/3dobjs/base.obj`
- Origin: MakeHuman / MPFB2 data
- Asset license: CC0 as documented by the upstream project

This repository does not vendor the upstream mesh file; the demo fetches it from the public upstream GitHub raw URL at runtime. No SMPL/SMPL-X/FLAME assets or checkpoints are included.

## Three.js

The static demo loads Three.js ES modules from jsDelivr at runtime for rendering, orbit controls and GLB export. The geometry-generation logic itself is contained in `human-core.js` and does not depend on Three.js.
