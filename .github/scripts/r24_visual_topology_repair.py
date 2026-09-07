#!/usr/bin/env python3
from pathlib import Path

renderer = Path('native/src/render/VulkanRenderer.cpp')
text = renderer.read_text(encoding='utf-8')
old = '''    // All production opaque primitives are cull-safe: terrain and closed rock/tree meshes have
    // consistent outward winding, while grass explicitly emits both opposite-winding faces. Cull
    // backfaces before fragment generation; keep water/glass transparent geometry two-sided.
    raster.cullMode = VK_CULL_MODE_BACK_BIT;
    createColorPipeline(
        opaquePipeline_, sceneVertex, "vertexMain", opaqueFragment, "opaqueFragmentMain",
        &vertexInput, &reverseDepth, &opaqueBlend, scenePipelineLayout_);
'''
new = '''    // R24 visual-topology safety gate: the adaptive planetary terrain is a two-sided heightfield
    // until its LOD patch/skirt winding is proven cull-safe across every evidence view. Global
    // opaque backface culling exposed severe ribbon/curtain holes in mountain/rift/canyon/abyss
    // captures, so keep the production opaque pass two-sided. Closed props can regain culling later
    // through a separate prop pipeline after terrain winding is independently validated.
    raster.cullMode = VK_CULL_MODE_NONE;
    createColorPipeline(
        opaquePipeline_, sceneVertex, "vertexMain", opaqueFragment, "opaqueFragmentMain",
        &vertexInput, &reverseDepth, &opaqueBlend, scenePipelineLayout_);
'''
if old not in text:
    if new not in text:
        raise SystemExit('opaque culling anchor not found')
else:
    text = text.replace(old, new, 1)
renderer.write_text(text, encoding='utf-8')

# Keep an explicit source-level regression marker so future performance work cannot silently
# re-enable global opaque culling before terrain has its own cull-safe pipeline.
check = renderer.read_text(encoding='utf-8')
marker = 'R24 visual-topology safety gate'
if marker not in check:
    raise SystemExit('visual topology safety marker missing')
segment = check[check.index(marker):check.index(marker) + 900]
if 'raster.cullMode = VK_CULL_MODE_NONE;' not in segment:
    raise SystemExit('opaque pipeline is not two-sided after repair')
print('R24 VISUAL TOPOLOGY REPAIR materialized')
print(' - global opaque backface culling disabled for adaptive terrain safety')
print(' - transparent behavior unchanged')
print(' - next stage must validate/fix terrain patch winding before selective culling returns')
