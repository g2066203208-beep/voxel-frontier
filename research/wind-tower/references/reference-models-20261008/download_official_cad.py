#!/usr/bin/env python3
"""Archive unchanged IEA Wind Task 37 CAD/STL ZIPs, NEVER regenerate geometry.

Run from repository root on GitHub Actions. Imports only actual official CAD blobs
from IEAWindSystems/IEA-15-240-RWT and checks content against original git blob SHA.
"""
import hashlib
import json
import os
import pathlib
import shutil
import struct
import sys
import urllib.parse
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[4]
BASE = ROOT / "research/wind-tower/references/reference-models-20261008"
PUBLIC = ROOT / "public/iea15-official"
BASE.mkdir(parents=True,exist_ok=True)
PUBLIC.mkdir(parents=True,exist_ok=True)
UPSTREAM = "IEAWindSystems/IEA-15-240-RWT"
UPSTREAM_BRANCH = "master"
API = f"https://api.github.com/repos/{UPSTREAM}/git/trees/{UPSTREAM_BRANCH}?recursive=1"
MAX_GIT_BYTES = 83 * 1024 * 1024
def request(url):
    return urllib.request.Request(url,headers={
        "User-Agent":"Wind-Tower-Academic-Source-Archive/1.0",
        "Accept":"application/vnd.github+json" if "api.github.com" in url else "*/*"})
with urllib.request.urlopen(request(API),timeout=90) as fh: tree=json.load(fh)
if tree.get("truncated"): raise RuntimeError("Official GitHub tree is truncated; aborting source identity check")
blobs={x["path"]:x for x in tree["tree"] if x.get("type")=="blob"}
inventory=BASE/"IEA15_ORIGINAL_CAD_INVENTORY.tsv"
inventory.write_text("path\tbytes\tgit_sha\tsource\n"+"\n".join(
    f'{p}\t{o.get("size","")}\t{o["sha"]}\thttps://github.com/{UPSTREAM}/blob/{UPSTREAM_BRANCH}/{urllib.parse.quote(p)}'
    for p,o in sorted(blobs.items()) if p.startswith("CAD/")
)+"\n",encoding="utf-8")
print("Official CAD blobs:",sum(p.startswith("CAD/") for p in blobs))
candidates=[
 "CAD/OpenSCAD/IEA-15-240-RWT.stl.zip",
 "CAD/OpenSCAD/IEA-15-240-RWT_blade.stl.zip",
 "CAD/OpenSCAD/IEA-15-240-RWT_tower.stl.zip",
 "CAD/OpenSCAD/IEA-15-240-RWT_monopile.stl.zip",
 "CAD/OpenSCAD/IEA-15-240-RWT_VolturnUS-S.stl.zip",
 "CAD/OpenSCAD/IEA-15-240-RWT_VolturnUS-S_tower.stl.zip",
 "CAD/OpenSCAD/IEA-15-240-RWT_VolturnUS-S_floater.stl.zip",
 "CAD/IEA-15-240-RWT_Solidworks.zip",
 "CAD/Generator_detail.zip",
]
header="source_path\tresult\tbytes\tgit_sha\tsha256\tarchive_path\tinformation"
results=[header]
def git_blob_sha(path):
    h=hashlib.sha1()
    size=path.stat().st_size
    h.update(f"blob {size}\\0".encode().replace(b"\\0",b"\0"))
    with path.open("rb") as fh:
        for block in iter(lambda:fh.read(1<<19),b""): h.update(block)
    return h.hexdigest()
def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda:fh.read(1<<19),b""): h.update(block)
    return h.hexdigest()
for original in candidates:
    info=blobs.get(original)
    if not info:
        print(original,"NOT-PUBLISHED",flush=True)
        results.append(f"{original}\tNOT_PUBLISHED\t0\t\t\t\tNot in official Git tree")
        continue
    sz=int(info.get("size",0))
    if sz>MAX_GIT_BYTES:
        print(original,"TOO-LARGE",sz,flush=True)
        results.append(f'{original}\tLINK_ONLY_GT_83MB\t{sz}\t{info["sha"]}\t\t\tOfficial GitHub source file is larger than a safe single Git blob')
        continue
    # Only original STL ZIP geometry is hosted as a web asset.
    # Native SolidWorks / generator archives remain in separate original-source archive.
    dest = (PUBLIC if "/OpenSCAD/" in original else BASE/"IEA15_original_CAD") / pathlib.Path(original).name
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and git_blob_sha(dest)==info["sha"]:
        status="ALREADY_VERIFIED"
    else:
        url=f"https://raw.githubusercontent.com/{UPSTREAM}/{UPSTREAM_BRANCH}/{urllib.parse.quote(original)}"
        temp=dest.with_suffix(dest.suffix+".part")
        temp.unlink(missing_ok=True)
        try:
            with urllib.request.urlopen(request(url),timeout=150) as src, temp.open("wb") as out:
                count=0
                while True:
                    block=src.read(1<<19)
                    if not block: break
                    out.write(block); count+=len(block)
                    if count>MAX_GIT_BYTES: raise ValueError("Exceeded 83MB import limit")
            if count!=sz or git_blob_sha(temp)!=info["sha"]: raise ValueError("Size or official Git blob SHA mismatch")
            if not zipfile.is_zipfile(temp): raise ValueError("Official source is not a ZIP")
            with zipfile.ZipFile(temp) as zf:
                if len(zf.namelist())<1: raise ValueError("ZIP archive empty")
                if "/OpenSCAD/" in original and not any(n.lower().endswith(".stl") for n in zf.namelist()):
                    raise ValueError("Official STL archive does not contain .stl")
            temp.replace(dest);status="ARCHIVED_SOURCE_UNMODIFIED"
        except Exception as err:
            temp.unlink(missing_ok=True)
            print("DOWNLOAD FAILED:",original,str(err)[:130],flush=True)
            results.append(f'{original}\tDOWNLOAD_FAILED\t{sz}\t{info["sha"]}\t\t\t{str(err)[:130]}')
            continue
    records=f'{original}\t{status}\t{sz}\t{info["sha"]}\t{sha256(dest)}\t{dest.relative_to(ROOT)}\tExact official unmodified bytes, verified against upstream Git blob SHA'
    results.append(records)
    print("VERIFIED",original,sz,flush=True)
(BASE/"IEA15_ORIGINAL_CAD_ARCHIVE_MANIFEST.tsv").write_text("\n".join(results)+"\n",encoding="utf-8")
