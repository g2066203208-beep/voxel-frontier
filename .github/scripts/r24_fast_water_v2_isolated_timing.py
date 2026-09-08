#!/usr/bin/env python3
"""Materialize Fast Water V2 and isolate GPU pass timestamps.

TOP_OF_PIPE/BOTTOM_OF_PIPE timestamp pairs can include pipeline overlap from neighbouring passes.
For optimization evidence we deliberately use ALL_COMMANDS boundaries so each measured interval is
fully ordered. This is a diagnostic mode: absolute FPS is not certified from llvmpipe.
"""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
runpy.run_path(str(ROOT / ".github/scripts/r24_fast_water_v2_materialize.py"), run_name="__main__")

renderer_path = ROOT / "native/src/render/VulkanRenderer.cpp"
text = renderer_path.read_text(encoding="utf-8")
if "R24_GPU_PASS_TIMING_ISOLATED_ALL_COMMANDS" not in text:
    top = "VK_PIPELINE_STAGE_2_TOP_OF_PIPE_BIT"
    bottom = "VK_PIPELINE_STAGE_2_BOTTOM_OF_PIPE_BIT"
    top_count = text.count(top)
    bottom_count = text.count(bottom)
    if top_count != 5 or bottom_count != 5:
        raise SystemExit(f"unexpected timestamp boundary counts top={top_count} bottom={bottom_count}")
    text = text.replace(top, "VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT")
    text = text.replace(bottom, "VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT")
    anchor = "    // Depth-first ordering: fill reverse-Z with opaque terrain, then shade sky only in pixels\n"
    if text.count(anchor) != 1:
        raise SystemExit(f"timing marker anchor count={text.count(anchor)}")
    marker = (
        "    // R24_GPU_PASS_TIMING_ISOLATED_ALL_COMMANDS: diagnostic timestamps use ALL_COMMANDS\n"
        "    // boundaries so neighbouring graphics stages cannot leak into the named pass interval.\n"
    )
    text = text.replace(anchor, marker + anchor, 1)
    renderer_path.write_text(text, encoding="utf-8")
