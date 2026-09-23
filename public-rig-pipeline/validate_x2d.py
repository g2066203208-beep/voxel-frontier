#!/usr/bin/env python3
import json, sys, zipfile
from pathlib import Path

def fail(msg):
    raise SystemExit("VALIDATION ERROR: " + msg)

def validate_dir(root: Path):
    pj=root/"project.json"
    if not pj.exists(): fail(f"{root}: missing project.json")
    j=json.loads(pj.read_text(encoding="utf-8"))
    duration=float(j.get("duration",0))
    if duration <= 0: fail("duration must be > 0")
    bones=j.get("bones",[])
    ids=[b["id"] for b in bones]
    if len(ids)!=len(set(ids)): fail("duplicate bone id")
    by={b["id"]:b for b in bones}
    for b in bones:
        p=b.get("parent")
        if p is not None and p not in by: fail(f"missing parent {p} for {b['id']}")
    for bid in ids:
        seen=set(); cur=bid
        while cur is not None:
            if cur in seen: fail(f"bone cycle at {bid}")
            seen.add(cur)
            cur=by[cur].get("parent") if cur in by else None
    for s in j.get("sprites",[]):
        if s.get("bone") not in by: fail(f"sprite references missing bone {s.get('bone')}")
        if not (root/s.get("image","")).exists(): fail(f"missing sprite image {s.get('image')}")
    for bid,keys in j.get("keyframes",{}).items():
        if bid not in by: fail(f"keyframes reference missing bone {bid}")
        last=-1e30
        for k in keys:
            t=float(k["time"])
            if t < last: fail(f"unsorted keyframes for {bid}")
            if t < 0 or t > duration+1e-6: fail(f"key time outside duration: {bid}@{t}")
            last=t
    return True

if __name__=="__main__":
    for arg in sys.argv[1:]:
        p=Path(arg)
        if p.suffix==".zip":
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                with zipfile.ZipFile(p) as z:z.extractall(td)
                validate_dir(Path(td))
        else:
            validate_dir(p)
        print("PASS",p)
