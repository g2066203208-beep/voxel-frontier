# Voxel Frontier — Low-Poly Ocean Rendering

## Goal

The ocean is a visible geometric surface that follows the same low-poly art direction as terrain, trees and rocks. It is not a flat blue plane, not a texture-only normal-map trick, and not a voxel/block water surface.

The current physical ocean in `Main.cpp` uses a mean surface radius of `planet.radius - 6 m` and density `997 kg/m^3`. The visible ocean uses the same mean sea level.

## Geometry

`OceanSurface.cpp` appends a separate contiguous ocean index range after opaque terrain/ecology geometry.

The visible runtime ocean uses 40 subdivisions per cube-sphere face, deliberately coarser than the 64-subdivision terrain. This leaves large facets that visibly participate in silhouette and lighting.

Interior patch vertices receive restrained deterministic tangent jitter while cube-face boundaries remain exact. Three seeded directional wave bands plus a small low-frequency set perturb the radial surface. This produces actual polygonal wave peaks/troughs rather than faking all movement in a texture.

The current first render stage keeps the waves deterministic/static. A later dedicated transparent water pass can add time-driven Gerstner/trochoidal displacement without changing the physical mean sea level.

## Shoreline and depth

The ocean mesh exists over the full sphere, but depth testing naturally hides it where terrain is above sea level. Where terrain is below sea level, the ocean surface is closer to the camera and becomes visible.

Each ocean vertex stores normalized water depth computed from:

`waterDepth = max(0, meanSeaElevation - terrainElevation)`

This gives the shader direct shoreline/depth information without requiring a screen-space depth texture.

## Procedural material

No bitmap textures are required.

The ocean material in `planet.slang` uses:

- shallow turquoise -> continental-shelf blue -> deep blue depth palette;
- macro and micro 3D noise for restrained color breakup;
- shoreline foam from real water depth plus seeded procedural breakup;
- water dielectric F0 ~ 0.0204 (IOR ~ 1.333);
- low roughness for broad faceted sun glints;
- derivative face normals from the actual polygonal wave surface;
- a stylized Fresnel-like cool grazing lift so distant facets read clearly without reflection textures.

The first implementation is intentionally opaque stylized water. Full refractive transparency needs a dedicated scene-color/depth pass and correct transparent ordering, so it is not faked with incorrect alpha blending in the existing single-pass renderer.

## References studied

- jklintan/Procedural-Water — directional trochoidal waves, noise ripples, Fresnel, depth/foam logic: https://github.com/jklintan/Procedural-Water
- tuxalin/water-shader — depth color, Fresnel reflection/refraction, shore foam: https://github.com/tuxalin/water-shader
- Jtfinlay/stylized-water-shader — depth-based color, shoreline foam and Fresnel stylized water: https://github.com/Jtfinlay/stylized-water-shader
- alyashour/Gerstner-waves — multi-wave geometric displacement reference: https://github.com/alyashour/Gerstner-waves

## Rules

1. Water geometry must remain visibly low-poly.
2. No normal-map dependency for the base ocean look.
3. Shoreline foam must follow actual terrain/water depth, not a painted ring.
4. Mean visual sea level must match the physical ocean level.
5. Water must not be described as "blocky" simply because it is low-poly.
6. A future transparent/refraction pass must use correct depth and render ordering instead of fake alpha shortcuts.
