#!/usr/bin/env python3
"""PDF page-geometry and text-layer gate; not a physics/CAE verification."""
import fitz, hashlib, json, statistics, sys
from pathlib import Path
def audit(path):
    src=Path(path); doc=fitz.open(src)
    if not doc: raise ValueError("empty PDF")
    rows=[]
    for i,p in enumerate(doc):
        rect=p.rect; words=p.get_text("words"); txt=p.get_text()
        off=sum(x0 < -.5 or y0 < -.5 or x1 > rect.width+.5 or y1 > rect.height+.5 for x0,y0,x1,y1,*_ in words)
        rows.append({"page":i+1,"characters":len(txt),"words":len(words),"off_page_words":off})
    return {"source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"pages":len(doc),
            "zero_text_pages":[r["page"] for r in rows if not r["characters"]],
            "off_page_words_total":sum(r["off_page_words"] for r in rows),
            "off_page_pages":[r["page"] for r in rows if r["off_page_words"]],
            "page_sizes_pt":sorted([list(v) for v in {(round(p.rect.width,2),round(p.rect.height,2)) for p in doc}]),
            "characters_min":min(r["characters"] for r in rows),
            "characters_median":statistics.median(r["characters"] for r in rows),
            "page124_contains_both":len(doc)>=124 and all(s in doc[123].get_text() for s in ("39.78%","87.39%")),
            "rows":rows}
if __name__=="__main__":
    print(json.dumps(audit(sys.argv[1]),ensure_ascii=False,indent=2))
