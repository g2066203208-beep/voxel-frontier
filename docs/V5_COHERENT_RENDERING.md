# V5 Coherent Rendering

V5 is an anti-fragmentation pass. The target is not smoother or more realistic geometry; it is a cleaner low-poly image where a few broad planes, shadow masses and material regions carry the scene.

## Geometry

- Runtime terrain requests may remain high, but visible terrain is capped at 44 subdivisions per cube face.
- Analytic planet height/physics are unchanged by this visual LOD.
- Interior terrain vertex jitter is only 7% of a cell; large random jitter is avoided because it can make diagonal terrain creases more visible rather than less.
- Fine elevation noise is subordinate to semantic continent/mountain/valley/basin forms.
- Ocean base tessellation is 32 subdivisions per cube face, with dry cells still omitted entirely.

## Shadows

- One 512x512 directional depth map remains the only natural-world shadow map.
- The shadow projection is snapped in light-plane world space to one shadow texel. Camera motion inside a texel therefore does not slide the shadow map continuously across geometry.
- A deterministic 9-tap tent PCF kernel replaces the previous four binary samples. There is no temporal/random shadow jitter.
- Direct sunlight/specular are shadowed; analytic sky and ground bounce remain visible in shadow.

## Materials

- Broad smooth value noise controls macro color only.
- Terrain no longer uses cell-scale mineral/meso speckle to trigger rock patches.
- Foliage no longer applies per-face hash breakup.
- Rock grain and lichen are broad low-frequency regions instead of pixel-like hashes.
- Shore foam is a coherent band/flow function instead of a random binary cell mask.

## Performance intent

The visual cleanup also reduces work: visible base terrain triangles fall from 49,152 at 64 subdivisions to 23,232 at the 44-subdivision cap, a 52.7% reduction. Ocean base tessellation falls from 36 to 32 subdivisions per face before dry-cell rejection. The only deliberate per-fragment increase is shadow filtering from four to nine depth reads for one sun light.

## References studied

- Blender EEVEE shadow filtering and resolution guidance: PCF is used to blur shadow aliasing; random/jittered soft shadows have a higher performance cost.
- Blender Shadow Terminator guidance: low-poly geometry is especially sensitive to abrupt shadow breaks.
- LowPolyTerrainBuilder: measured terrain diagonal crease behaviour and found vertex jitter does not solve geometry creases and can make them marginally worse; broader/gentler geometry relative to cell size is the effective fix.
