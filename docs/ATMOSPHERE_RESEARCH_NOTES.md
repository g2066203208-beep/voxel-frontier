# Atmosphere research notes

The current stylized-atmosphere pass was informed by Blender 4.5 LTS EEVEE documentation and Vulkan-oriented rendering practices.

Key points carried into Voxel Frontier:

- Ambient occlusion is useful as a multiplicative visibility term that darkens locally occluded surfaces; the engine approximates this cheaply per material instead of adding an AO texture/pass.
- Mist/fog is primarily a depth cue. The engine uses analytic distance+horizon haze rather than EEVEE-style volumetric 3D textures and multiple samples.
- Material identity comes from different diffuse/specular response, not just different RGB values.
- Foliage receives restrained reverse-light transmission to avoid opaque green-rock shading.
- Water uses a much lower roughness and stronger grazing-angle sky reflection than soil, bark or rock.
- Static closed world geometry is back-face culled; spatial batches can be rejected before draw submission.

Blender references studied:

- EEVEE light settings and shadows: https://docs.blender.org/manual/en/4.5/render/eevee/light_settings.html
- Render passes / ambient occlusion: https://docs.blender.org/manual/en/4.5/render/layers/passes.html
- World mist settings: https://docs.blender.org/manual/en/4.5/render/eevee/world_settings.html
- EEVEE volumes and their memory/sample costs: https://docs.blender.org/manual/en/4.5/render/eevee/render_settings/volumes.html
- Object visibility and shadow visibility: https://docs.blender.org/manual/en/4.5/render/eevee/object_settings/object_data.html

The implementation intentionally does not attempt to reproduce Blender's full renderer. It extracts the visual principles while keeping the current Vulkan renderer low-overhead.