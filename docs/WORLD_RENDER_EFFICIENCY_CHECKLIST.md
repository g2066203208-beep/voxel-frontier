# World render efficiency checklist

- [x] Static planet split into a small number of spatial draw ranges.
- [x] Frustum culling before draw submission.
- [x] Conservative planetary horizon rejection.
- [x] Projected-size rejection for tiny distant natural-asset ranges.
- [x] Back-face culling for closed static natural geometry.
- [x] Ocean cells fully buried under terrain omit indices.
- [x] Natural materials avoid bitmap/normal/AO texture dependencies.
- [x] Procedural meso/micro detail prefers hashes/analytic bands over multi-octave FBM.
- [x] Atmosphere uses analytic hemisphere light, ground bounce and mist instead of volumetric ray marching.
- [x] Batch-integrity test verifies contiguous index coverage and ocean dry-cell rejection.
- [ ] GPU-driven indirect/meshlet path: defer until object/range counts justify its synchronization and compatibility cost.
- [ ] Directional shadow map: add only after the no-extra-pass atmosphere baseline is validated visually and by profiling.
