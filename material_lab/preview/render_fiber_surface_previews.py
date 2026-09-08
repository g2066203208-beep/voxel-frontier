#!/usr/bin/env python3
from pathlib import Path
import json, sys

ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path("build/generated-materials")

# This stage intentionally adds NO detached geometry.
# Wolf coat and moss volume must come from the same continuous displaced surface
# as the underlying material. Thin strands, floating cards, particle hairs and
# detached moss chips are forbidden by the painterly macro-form style.
def main():
    for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        mp=d/"manifest.json"
        if not mp.is_file():continue
        m=json.loads(mp.read_text());preset=m.get("preset")
        if preset=="vfPainterlyWolfFur":
            metrics={"renderer":"continuous_macro_coat_surface_v3","detachedGeometry":0,"thinStrands":0,"styleRule":"broad overlapping coat masses only"}
        elif preset=="vfPainterlyMoss":
            metrics={"renderer":"continuous_macro_moss_surface_v3","detachedGeometry":0,"thinStrokes":0,"styleRule":"broad overlapping moss mats only"}
        else:
            continue
        (d/"preview-fiber-metrics.json").write_text(json.dumps(metrics,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
