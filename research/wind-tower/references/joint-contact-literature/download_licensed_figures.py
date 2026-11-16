#!/usr/bin/env python3
"""Archive ONLY pre-cleared CC-BY original publisher figures into research branch.
No invented figures, no unlicensed publisher screenshots, no PDF redistribution.
TSV filenames are relative to this script directory.
"""
import csv
import hashlib
import os
from pathlib import Path
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT=Path(__file__).resolve().parent
INDEX=ROOT/"figure_manifest.tsv"
OUT=ROOT/"images"
OUT.mkdir(parents=True,exist_ok=True)
ERR=[]
done=[]
with INDEX.open(encoding="utf-8-sig",newline="") as fh:
    rows=list(csv.DictReader(fh,delimiter="\t"))
for r in rows:
    name=r["filename"].strip()
    url=r["original_figure_url"].strip()
    lic=r["license"].strip()
    if "/" in name or "\\" in name or ".." in name or not name.lower().endswith((".png",".jpg",".jpeg")):
        ERR.append(f"{name}: unsafe filename")
        continue
    if lic not in ("CC BY 4.0",):
        ERR.append(f"{name}: license not pre-cleared: {lic}")
        continue
    if not url.startswith("https://"):
        ERR.append(f"{name}: only HTTPS sources allowed")
        continue
    dest=OUT/name
    if dest.exists():
        raw=dest.read_bytes()
        h=hashlib.sha256(raw).hexdigest()
        done.append((name,len(raw),h,"existing"))
        continue
    body=None
    for attempt in range(3):
        try:
            req=Request(url,headers={"User-Agent":"ResearchFigureArchiver/1.0 (CC-BY attribution; no scraping PDFs)","Accept":"image/png,image/jpeg,image/*;q=0.8"})
            with urlopen(req,timeout=30) as response:
                ctype=response.headers.get("Content-Type","").lower()
                body=response.read(8_000_001)
            if len(body)>8_000_000:
                raise RuntimeError("figure > 8MB")
            png=body.startswith(b"\x89PNG\r\n\x1a\n")
            jpg=body.startswith(b"\xff\xd8\xff")
            if not (png or jpg):
                raise RuntimeError(f"not a PNG or JPEG image: {ctype} prefix={body[:16]!r}")
            if (name.lower().endswith(".png") and not png) or (name.lower().endswith((".jpg",".jpeg")) and not jpg):
                raise RuntimeError(f"file extension does not match image type {ctype}")
            break
        except (URLError,HTTPError,TimeoutError,RuntimeError) as e:
            print(f"WARN {name} attempt={attempt+1}: {e}",file=sys.stderr)
            body=None
            time.sleep(2+attempt)
    if body is None:
        ERR.append(f"{name}: publisher image download failed")
        continue
    tmp=dest.with_name(dest.name+".tmp")
    tmp.write_bytes(body)
    tmp.replace(dest)
    h=hashlib.sha256(body).hexdigest()
    done.append((name,len(body),h,"downloaded"))
with (ROOT/"FIGURE_SHA256.tsv").open("w",encoding="utf-8",newline="") as fh:
    writer=csv.writer(fh,delimiter="\t")
    writer.writerow(["filename","bytes","sha256","status"])
    writer.writerows(done)
print(f"archived={len(done)} total_manifest={len(rows)}")
for row in done:
    print(*row,sep="\t")
for error in ERR:
    print("ERROR:",error,file=sys.stderr)
# The job can still commit the verified subset; failed sources remain visible.
if ERR:
    sys.exit(2)
