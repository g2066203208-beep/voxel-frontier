# Rendering Reference Study — Stylized Low-Poly Atmosphere

This note records the rendering techniques studied for Voxel Frontier's atmosphere pass. The goal is to learn rendering mechanisms, not copy scene layout or protected assets.

## Verified reference workflow: Ryan King Art — Stylized Low Poly Forest River

Public project/tutorial descriptions confirm:

- Blender Eevee render engine.
- 8K sky HDRI lighting.
- Mist Pass compositing for the blue fog/mist depth effect.
- Hand-painted low-poly trees, rocks and grass.
- Tree branch alpha and color textures.
- The tutorial explicitly separates Render Engine / Lighting (Part 2), Tree Texture Painting (Part 1), and Fog Compositing / Render Settings (Part 3).
- The linked HDRI is Poly Haven `Industrial Sunset 02 (Pure Sky)`: cool blue, partly cloudy sky with medium-contrast lighting and a low warm sun.

These facts explain why the reference has much more depth than flat-color geometry under a single light: structured environment luminance, warm directional light, depth fog, authored material variation, water response, and display color management all reinforce one another.

## Blender mechanisms studied

### World / HDRI environment lighting

Eevee's World contributes environment light via an internal light probe. Blender can separate very intense HDRI sun energy into a directional sun light so that sharp directional lighting and shadows are not forced through the low-frequency environment probe.

Voxel Frontier analogue: analytical sky/horizon diffuse + analytical environment specular + one real directional sun. No HDRI texture or cubemap is required.

### Mist Pass

Blender's Mist Pass has an explicit Start, Depth and Falloff. It is a depth layer intended to strengthen depth perception in compositing.

Voxel Frontier analogue: a 28 m crisp near-field followed by analytical Beer-Lambert extinction with stronger horizon path length. This avoids washing the entire frame with haze.

### Shadow Terminator

Blender's Eevee Shadow Terminator Normal Offset shifts the receiver along the shading normal, strongest at glancing light angles, to reduce abrupt low-poly shadow breaks.

Voxel Frontier analogue: the shadow receiver uses a small normal offset varying with NdotL before the depth comparison.

### AgX color management

Blender documents AgX as the successor to Filmic for wide dynamic range, with natural highlight roll-off and progressive desaturation at high exposure.

Voxel Frontier analogue: analytical AgX-style tone mapping in Slang, with a restrained punchy look so broad low-poly color fields retain contrast without becoming neon.

## GitHub real-time references studied

### Sascha Willems / Vulkan shadow mapping

The Vulkan shadow example uses a first light-space depth pass, a second scene pass, depth bias, and PCF filtering. Voxel Frontier follows the same architecture with one stable 512x512 directional shadow map, texel snapping and deterministic weighted 9-tap PCF.

### Google Filament

Filament's current tone-mapping source includes AgX and optional looks such as Punchy. Its renderer is also a useful reference for keeping shadowing, fog, indirect environment lighting and display tone mapping as separate layers instead of trying to encode all atmosphere into material color.

### IronWarrior / Roystan Toon Water Shader

This tutorial project demonstrates stylized animated water and shoreline foam driven by depth information. Voxel Frontier currently uses its own low-cost approach: low-poly geometric waves, water-depth payload, shallow/deep palette, Fresnel sky reflection and procedural shore foam. Screen-space refraction remains intentionally out of scope until a dedicated scene-color/depth water pass is justified.

## Current Voxel Frontier rendering stack

- Flat faceted low-poly surface normals for natural procedural materials.
- Physically coherent GGX direct light with per-material roughness/F0.
- Analytical sky hemisphere and ground bounce.
- Analytical environment specular so roughness remains visible outside the direct sun highlight.
- Low-angle sun color temperature derived from solar elevation.
- Stable 512x512 directional shadow map, receiver normal offset and deterministic 9-tap PCF.
- Foliage back-light transmission approximation.
- Low-roughness water Fresnel / sky reflection / depth palette / shore foam.
- Fullscreen analytical sky with a real sun disk and broad two-layer low-frequency cloud luminance field.
- Mist-Pass-like 28 m clear foreground followed by distance/horizon atmospheric extinction.
- Analytical AgX-style display tone mapping.

## Performance rule

The visual target must not be reached by hiding cost in high-frequency noise, large HDRIs, material texture sets, volumetric ray marching, SSR, or excessive geometry. Prefer broad analytical functions and existing per-vertex semantic data. Add a heavier pass only when it produces a clearly measurable visual gain that cannot be achieved more cheaply.
