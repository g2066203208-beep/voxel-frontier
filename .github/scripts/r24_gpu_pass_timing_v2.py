#!/usr/bin/env python3
"""Make Vulkan pass timestamps represent isolated pass cost instead of pipeline overlap."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "native/src/render/VulkanRenderer.cpp"
text = path.read_text(encoding="utf-8")
marker = "R24_GPU_PASS_TIMING_V2_ALL_COMMANDS"
if marker not in text:
    top = "VK_PIPELINE_STAGE_2_TOP_OF_PIPE_BIT"
    bottom = "VK_PIPELINE_STAGE_2_BOTTOM_OF_PIPE_BIT"
    tc, bc = text.count(top), text.count(bottom)
    if tc != 5 or bc != 5:
        raise SystemExit(f"unexpected timestamp stage counts top={tc} bottom={bc}")
    text = text.replace(top, "VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT")
    text = text.replace(bottom, "VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT")
    anchor = "    // Depth-first ordering: fill reverse-Z with opaque terrain, then shade sky only in pixels\n"
    if text.count(anchor) != 1:
        raise SystemExit(f"pass timing anchor count={text.count(anchor)}")
    text = text.replace(
        anchor,
        "    // R24_GPU_PASS_TIMING_V2_ALL_COMMANDS: diagnostic pass timestamps intentionally use\n"
        "    // ALL_COMMANDS boundaries so neighbouring graphics pipeline stages cannot leak into a\n"
        "    // named pass interval. Absolute performance certification still requires hardware GPU.\n"
        + anchor,
        1,
    )
    path.write_text(text, encoding="utf-8")
