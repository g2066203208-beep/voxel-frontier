#!/usr/bin/env python3
"""Execute Fast Water V2 with a hardened empty-mesh water-range migration.

The V2 patch was written when the renderer had one opaque/transparent zeroing site. The current
runtime correctly has two: static and dynamic frame meshes. Both need waterIndexCount cleared, so
materialization must migrate both sites instead of relying on a globally unique two-line anchor.
"""
from pathlib import Path

TARGET = Path(__file__).with_name("r24_fast_water_v2.py")
source = TARGET.read_text(encoding="utf-8")

old = r'''    renderer = replace_once(
        renderer,
        """        mesh.opaqueIndexCount = 0U;\n        mesh.transparentIndexCount = 0U;\n""",
        """        mesh.opaqueIndexCount = 0U;\n        mesh.waterIndexCount = 0U;\n        mesh.transparentIndexCount = 0U;\n""",
        "dynamic clear frame water",
    )
'''
new = r'''    empty_range_anchor = """        mesh.opaqueIndexCount = 0U;\n        mesh.transparentIndexCount = 0U;\n"""
    empty_range_replacement = """        mesh.opaqueIndexCount = 0U;\n        mesh.waterIndexCount = 0U;\n        mesh.transparentIndexCount = 0U;\n"""
    empty_range_count = renderer.count(empty_range_anchor)
    if empty_range_count != 2:
        raise SystemExit(f"empty static/dynamic frame water anchors count={empty_range_count}")
    renderer = renderer.replace(empty_range_anchor, empty_range_replacement)
'''

count = source.count(old)
if count != 1:
    raise SystemExit(f"Fast Water V2 source migration anchor count={count}")
source = source.replace(old, new, 1)

# Execute the hardened materializer without mutating the checked-in source script. This keeps the
# original historical patch auditable while the closure workflow uses the corrected semantics.
namespace = {"__name__": "__main__", "__file__": str(TARGET)}
exec(compile(source, str(TARGET), "exec"), namespace, namespace)
