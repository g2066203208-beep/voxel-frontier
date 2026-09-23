#!/usr/bin/env python3
import json, math, sys
from pathlib import Path

EPS=1e-4

def die(msg):
    raise SystemExit("X2D-RIG-V2 VALIDATION ERROR: "+msg)

def finite(v,name):
    if not isinstance(v,(int,float)) or not math.isfinite(v):
        die(f"{name} must be finite")

def main(path):
    p=Path(path)
    j=json.loads(p.read_text(encoding="utf-8"))
    if j.get("format")!="x2d-rig-v2": die("format must be x2d-rig-v2")

    bones=j.get("bones",[])
    ids=[b["id"] for b in bones]
    if len(ids)!=len(set(ids)): die("duplicate bone id")
    bmap={b["id"]:b for b in bones}
    for b in bones:
        for k in ("x","y","rotation"): finite(b[k],f"{b['id']}.{k}")
        parent=b.get("parent")
        if parent is not None and parent not in bmap:
            die(f"bone {b['id']} has missing parent {parent}")

    for bid in ids:
        seen=set(); cur=bid
        while cur is not None:
            if cur in seen: die(f"bone cycle at {bid}")
            seen.add(cur)
            cur=bmap[cur].get("parent") if cur in bmap else None

    slots=j.get("slots",[])
    sids=[s["id"] for s in slots]
    if len(sids)!=len(set(sids)): die("duplicate slot id")
    for s in slots:
        if s["bone"] not in bmap: die(f"slot {s['id']} references missing bone {s['bone']}")

    attachments=j.get("attachments",{})
    for s in slots:
        a=s.get("attachment")
        if a is not None and a not in attachments:
            die(f"slot {s['id']} references missing attachment {a}")

    for aid,a in attachments.items():
        if a.get("type")=="mesh":
            verts=a.get("vertices",[])
            tris=a.get("triangles",[])
            uvs=a.get("uvs",[])
            if len(verts)%2: die(f"{aid}: vertices must be x,y pairs")
            if len(uvs)!=len(verts): die(f"{aid}: UV count mismatch")
            n=len(verts)//2
            if len(tris)%3: die(f"{aid}: triangles must be triples")
            if any((not isinstance(i,int) or i<0 or i>=n) for i in tris):
                die(f"{aid}: triangle index out of range")
            weights=a.get("weights",[])
            if len(weights)!=n: die(f"{aid}: one weight list required per vertex")
            for vi,items in enumerate(weights):
                total=0.0
                for pair in items:
                    if len(pair)!=2: die(f"{aid}: weight item must be [bone,weight]")
                    bone,w=pair
                    if bone not in bmap: die(f"{aid}: missing weighted bone {bone}")
                    finite(w,f"{aid}.weight")
                    if w<0: die(f"{aid}: negative weight")
                    total+=w
                if abs(total-1.0)>1e-3:
                    die(f"{aid}: vertex {vi} weights sum to {total}, expected 1")

    for c in j.get("constraints",[]):
        for bone in c.get("bones",[]):
            if bone not in bmap: die(f"constraint {c['id']} missing bone {bone}")
        t=c.get("target")
        if t is not None and t not in bmap:
            die(f"constraint {c['id']} missing target {t}")

    for aname,a in j.get("animations",{}).items():
        d=a.get("duration")
        finite(d,f"animation {aname}.duration")
        if d<=0: die(f"animation {aname} duration must be > 0")

    print("PASS",p)

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: validate_rig_v2.py project.x2d.json")
    main(sys.argv[1])
