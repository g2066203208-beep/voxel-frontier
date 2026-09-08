#!/usr/bin/env python3
from pathlib import Path
import json, sys

ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path("build/generated-materials")

# Fiber/vegetation-like surfaces use a few broad polygon cards/fins that are built
# inside render_sandstone_mesh_preview.py and share the same z-buffer as the shell.
# The whole root edge of every card lies on the displaced surface: cards may lift
# and cross the silhouette, but detached/floating pieces and strand-like strokes
# are forbidden by the painterly macro-form style.
def main():
    for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        mp=d/"manifest.json"
        if not mp.is_file():continue
        m=json.loads(mp.read_text());preset=m.get("preset")
        mesh=d/"preview-mesh-metrics.json"
        mesh_metrics=json.loads(mesh.read_text()) if mesh.is_file() else {}
        if preset=="vfPainterlyWolfFur":
            metrics={"renderer":"attached_macro_fur_cards_v1","macroCards":int(mesh_metrics.get("macroCards",15)),"thinStrands":0,"floatingCards":0,"rootAttachment":"full-edge flush to displaced surface","styleRule":"few broad folded coat clumps and silhouette fins"}
        elif preset=="vfPainterlyMoss":
            metrics={"renderer":"attached_macro_moss_cards_v1","macroCards":int(mesh_metrics.get("macroCards",11)),"thinStrokes":0,"floatingCards":0,"rootAttachment":"full-edge flush to displaced surface","styleRule":"few oversized lifted moss carpet lobes"}
        else:
            continue
        (d/"preview-fiber-metrics.json").write_text(json.dumps(metrics,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
