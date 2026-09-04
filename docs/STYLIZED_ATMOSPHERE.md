# Stylized Atmosphere and Low-Poly Lighting

This pass is designed for a low-poly world where silhouette and polygon planes carry most of the visual information. The shader therefore avoids texture stacks, volumetric ray marching and high-frequency procedural noise.

## Lighting stack

The current natural-material shader combines:

- direct sun with GGX specular and per-material roughness/F0;
- analytic sky-hemisphere ambient light;
- analytic ground-bounce tint;
- very cheap material-local occlusion factors;
- foliage back-light transmission;
- shallow/deep water colour and Fresnel sky reflection;
- analytic distance/horizon mist;
- one compact filmic tone-mapping curve.

No additional descriptor set, 3D volume texture, normal map, AO texture or environment cubemap is required by this pass.

## Atmosphere derivation

Atmosphere density is derived from the camera radius relative to the rendered planetary surface and decays exponentially with height. Solar elevation is derived per fragment from the local planetary up vector and the sun direction. This keeps day/twilight response spatially coherent without adding uniforms.

The mist function uses camera-to-surface distance and a horizon factor. It intentionally approximates the visual role of a mist/atmospheric-depth pass rather than attempting physically complete participating-media simulation.

## Material differentiation

- Terrain: very high roughness; slope/elevation/mineral transitions; green-biased ground bounce.
- Bark: high roughness, low F0, branch-local longitudinal fibres/fissures, dark cavity response.
- Foliage: high roughness, strong canopy self-darkening and restrained reverse-light transmission.
- Rock: variable high roughness, weak mineral specular, strata/lichen breakup and underside darkening.
- Ocean: low roughness, dielectric F0 near water, depth palette, shore foam and strong grazing sky reflection.

## Performance rules

1. Polygon shape and face normals do the detail work first.
2. Broad colour flow gets at most one smooth value-noise sample.
3. Meso/micro breakup uses hashes or analytic bands.
4. Atmospheric depth is analytic, not volumetric ray marching.
5. Invisible world batches are rejected before draw submission by frustum/horizon/projected-size tests.
6. Closed static natural geometry uses back-face culling.
7. Ocean cells fully buried under terrain do not generate indices.

## References studied

- Blender 4.5 LTS EEVEE documentation: shadows, Ambient Occlusion, world mist, volumetrics and object visibility.
- Khronos Vulkan examples: dynamic state, indirect rendering and GPU-driven rendering progression.
- meshoptimizer: cluster/meshlet and visibility-oriented geometry processing.
- Mature procedural low-poly/tree/terrain repositories already listed in `PLANET_LOWPOLY_ECOLOGY.md`.

The implementation deliberately takes the visual principles rather than copying Blender's full renderer: EEVEE volumetrics use 3D textures and multiple samples, which is unnecessary for the current stylized world target.