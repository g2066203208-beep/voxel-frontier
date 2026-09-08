#!/usr/bin/env python3
"""Post-materialization correctness fixes for strict module boundaries."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "native/src/app/Main.cpp"
RENDER_CPP = ROOT / "native/src/render/VulkanRenderer.cpp"

text = MAIN.read_text(encoding="utf-8")
old = '''            if (refreshDynamicScene) {
                renderer.setDynamicMesh(dynamicMesh);
                dynamicSceneAccumulator = 0.0;
            } else if (!runtimeFeatures.dynamicSceneRender) {
                renderer.clearDynamicMesh();
            }'''
new = '''            if (refreshDynamicScene) {
                renderer.setDynamicMesh(dynamicMesh);
                dynamicSceneAccumulator = 0.0;
            }'''
if old in text:
    text = text.replace(old, new, 1)

old = '''            renderEnvironment.transparentEnabled = runtimeFeatures.geometryRender
                && runtimeFeatures.waterRender;'''
new = '''            // The transparent pass is generic infrastructure. Water is removed at mesh-build
            // time, so disabling water never disables future glass/particles/translucent props.
            renderEnvironment.transparentEnabled = runtimeFeatures.geometryRender;'''
if old in text:
    text = text.replace(old, new, 1)

MAIN.write_text(text, encoding="utf-8")

# The legacy renderer declared the static-object quaternion inside the shadow-pass block and then
# reused it in the later opaque/transparent draw lambda. Once shadows became an optional module,
# that accidental ownership became a compile-time dependency. Promote the transform to renderer
# base data so every render client consumes it independently.
text = RENDER_CPP.read_text(encoding="utf-8")
marker = '''    // R24_MODULE_ISOLATION_MATRIX_V1: shadow rasterization is a true optional client.
    if (environment.shadowsEnabled) {'''
outer = '''    // Shared scene transform is renderer-base data, not shadow-module state.
    const glm::dquat rotation = glm::normalize(staticObjectRotation);

    // R24_MODULE_ISOLATION_MATRIX_V1: shadow rasterization is a true optional client.
    if (environment.shadowsEnabled) {'''
if marker in text and outer not in text:
    text = text.replace(marker, outer, 1)
RENDER_CPP.write_text(text, encoding="utf-8")

print("R24 module isolation post-fixups applied")
