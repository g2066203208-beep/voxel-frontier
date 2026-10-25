#!/usr/bin/env python3
"""S01 diagnostic: full 3D finite T3D2 tie-to-longitudinal proximity.
Static geometry only. Not Abaqus, detailing, construction or standard PASS.
Requires NumPy, SHA-locked diagnostic INP and its original generator manifest.
"""
import argparse, csv, hashlib, json, math, re
from pathlib import Path
import numpy as np

EXPECTED_INP="0965b234b948178b486389550594425c9959ef9ccf5fbd69522485ec9c662217"

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(ok,msg):
    if not ok: raise RuntimeError(msg)

def parse_part(body):
    n=re.search(r"(?ms)^\*Node\r?\n(.*?)(?=^\*)",body)
    e=re.search(r"(?ms)^\*Element, type=T3D2\s*\n(.*?)(?=^\*)",body)
    check(n is not None and e is not None,"Missing T3D2/Node")
    nodes=np.array([list(map(float,l.split(","))) for l in n.group(1).splitlines() if l.strip()])
    els=np.array([list(map(int,l.split(","))) for l in e.group(1).splitlines() if l.strip()])
    ids=nodes[:,0].astype(int)
    check(ids.min()==1 and ids.max()==len(ids) and len(set(ids))==len(ids),"noncontiguous node IDs")
    nd=np.zeros((len(ids)+1,3)); nd[ids]=nodes[:,1:]
    return nd,els

def distances(p,q,a,b):
    # Exact minimum of two finite straight segments: interior/interior
    # stationary point, plus four endpoint-to-opposite-segment cases.
    u=(q-p)[:,None,:];v=(b-a)[None,:,:];w=p[:,None,:]-a[None,:,:]
    A=np.sum(u*u,axis=2);B=np.sum(u*v,axis=2);C=np.sum(v*v,axis=2)
    D=np.sum(u*w,axis=2);E=np.sum(v*w,axis=2)
    den=A*C-B*B
    check(float(den.min())>1e-12,"degenerate or parallel pair")
    ss=(B*E-C*D)/den;tt=(A*E-B*D)/den
    good=(ss>=0)&(ss<=1)&(tt>=0)&(tt<=1)
    d2=np.full_like(ss,np.inf)
    tmp=np.sum((w+ss[:,:,None]*u-tt[:,:,None]*v)**2,axis=2)
    d2[good]=tmp[good]
    for point in (p,q):
        ww=point[:,None,:]-a[None,:,:]
        t=np.clip(np.sum(ww*v,axis=2)/C,0,1)
        d2=np.minimum(d2,np.sum((ww-t[:,:,None]*v)**2,axis=2))
    for point in (a,b):
        ww=p[:,None,:]-point[None,:,:]
        t=np.clip(-np.sum(ww*u,axis=2)/A,0,1)
        d2=np.minimum(d2,np.sum((ww+t[:,:,None]*u)**2,axis=2))
    return np.sqrt(np.maximum(d2,0))

def plane_count(p,q,a,b,r):
    # Independent cross-check: all ties are horizontal, intersect bar at tie Y.
    t=(p[:,1,None]-a[None,:,1])/(b[None,:,1]-a[None,:,1])
    valid=(t>=0)&(t<=1)
    bar=a[None,:,[0,2]]+t[:,:,None]*(b-a)[None,:,[0,2]]
    start=p[:,None,[0,2]];end=q[:,None,[0,2]];v=end-start
    f=np.clip(np.sum((bar-start)*v,axis=2)/np.sum(v*v,axis=2),0,1)
    d=np.linalg.norm(bar-(start+f[:,:,None]*v),axis=2);d[~valid]=np.inf
    return int(np.count_nonzero(d.min(axis=1)<r+0.003-1e-6))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--inp",type=Path,required=True)
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--outdir",type=Path,required=True)
    args=ap.parse_args()
    check(sha(args.inp)==EXPECTED_INP,"candidate INP SHA256 mismatch")
    manifest=json.loads(args.manifest.read_text())
    check(manifest["candidate_sha256"]==EXPECTED_INP and manifest["reverse_patch_exact_parent"],"manifest identity mismatch")
    check(len(manifest["sections"])==31,"31 segment manifest required")
    info={int(x["segment"].split("_")[-1]):x for x in manifest["sections"]}
    s=args.inp.read_text()
    parts={m.group(1):m.group(2) for m in re.finditer(r"(?ms)^\*Part, name=([^\r\n]+)\r?\n(.*?)^\*End Part",s)}
    h,e=parse_part(parts["HOOP_TIE_CAGE_T046"])
    check(len(e)==213768,"hoop/tie element count changed")
    ties=h[e[201456:,1:]]
    check(ties.shape==(12312,2,3),"tie count changed")
    check(float(np.max(abs(ties[:,0,1]-ties[:,1,1])))<1e-12,"ties not horizontal")
    rows=[];old_count=new_count=0
    for i in range(1,32):
        name=f"RBLONG_{i:02d}";nd,els=parse_part(parts[name])
        check(len(els)==info[i]["bar_elements"],"rod count differs")
        m=re.search(r"(?ms)^\*Instance, name="+name+r"-1, part="+name+r"\s*\n(.*?)^\*End Instance",s)
        check(m is not None,"missing instance "+name)
        tr=np.array([float(x.strip()) for x in m.group(1).strip().split(",")]) if m.group(1).strip() else np.zeros(3)
        a=nd[els[:,1]]+tr;b=nd[els[:,2]]+tr
        delta=info[i]["shift_mm"]/1000
        r=np.linalg.norm(a[:,[0,2]],axis=1);mid=(r.min()+r.max())/2
        signs=np.where(r<mid,1,-1)
        ao=a.copy();bo=b.copy()
        for xyz in (ao,bo):
            rr=np.linalg.norm(xyz[:,[0,2]],axis=1)
            xyz[:,[0,2]]-=signs[:,None]*delta*xyz[:,[0,2]]/rr[:,None]
        y0=min(a[:,1].min(),b[:,1].min());y1=max(a[:,1].max(),b[:,1].max())
        ids=np.where((ties[:,0,1]>=y0+1e-7)&(ties[:,0,1]<=y1-1e-7))[0]
        p=ties[ids,0];q=ties[ids,1]
        old=distances(p,q,ao,bo).min(axis=1)
        new=distances(p,q,a,b).min(axis=1)
        old_rad=math.sqrt(0.000490874/math.pi)
        new_rad=info[i]["diameter_mm"]/2000
        old_gap=(old-old_rad-0.003)*1000
        new_gap=(new-new_rad-0.003)*1000
        on=int((old_gap<-1e-6).sum());nn=int((new_gap<-1e-6).sum())
        check(on==plane_count(p,q,ao,bo,old_rad),"original 2D/3D mismatch")
        check(nn==plane_count(p,q,a,b,new_rad),"D400 2D/3D mismatch")
        old_count+=on;new_count+=nn
        rows.append(dict(segment=f"CSEG{i:02d}",tie_elements=len(ids),
            longitudinal_elements=len(els),D400_diameter_mm=info[i]["diameter_mm"],
            radial_shift_mm=info[i]["shift_mm"],
            old_min_surface_gap_mm=float(old_gap.min()),
            D400_min_surface_gap_mm=float(new_gap.min()),
            old_ties_with_centerline_sphere_overlap=on,
            D400_ties_with_centerline_sphere_overlap=nn,
            D400_ties_below_5mm_gap=int((new_gap<5).sum()),
            D400_ties_below_10mm_gap=int((new_gap<10).sum()),
            independent_2d_counts_match=True))
    check(sum(r["tie_elements"] for r in rows)==12312,"unaccounted ties")
    check(not args.outdir.exists(),"refuse overwrite output")
    args.outdir.mkdir(parents=True)
    output=args.outdir/"S01_D400_31SEG_TIE_LONGITUDINAL_3D_PROXIMITY.csv"
    with output.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    result=dict(status="STATIC_FE_CENTERLINE_PROXIMITY_ONLY_HOLD",
        inp_sha256=sha(args.inp),manifest_sha256=sha(args.manifest),
        segment_count=31,tie_elements=12312,longitudinal_elements=5440,
        original_overlap_tie_count=old_count,D400_overlap_tie_count=new_count,
        additional_overlap_ties=new_count-old_count,
        D400_min_surface_gap_mm=min(r["D400_min_surface_gap_mm"] for r in rows),
        original_min_surface_gap_mm=min(r["old_min_surface_gap_mm"] for r in rows),
        D400_ties_below_5mm_gap=sum(r["D400_ties_below_5mm_gap"] for r in rows),
        independent_2d_plane_crosscheck="ALL_31_SEGMENTS_COUNTS_MATCH",
        csv_sha256=sha(output),
        interpretation="Idealized embedded T3D2 centerline overlap is NOT proof of physical construction collision; no code, native or physics PASS.",
        standard="NB/T10907-2021 authorized 4.2/6.4/8 NOT READ",
        native_abaqus="NOT_RUN",physical_error_budget="NOT_ESTIMATED",stage="S01_PARTIAL_HOLD")
    (args.outdir/"S01_D400_TIE_LONGITUDINAL_3D_MANIFEST.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
