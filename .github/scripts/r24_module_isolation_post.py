#!/usr/bin/env python3
"""Post-materialization correctness fixes for strict module boundaries."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "native/src/app/Main.cpp"

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
print("R24 module isolation post-fixups applied")
