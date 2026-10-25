#!/usr/bin/env python3
"""S01 PT/host axial elastic compatibility PRECHECK; not an Abaqus native result."""
import argparse, csv, hashlib, json, math, re
from collections import defaultdict
from pathlib import Path

X=(-.8611363115940526,-.3399810435848563,.3399810435848563,.8611363115940526)
W=(.3478548451374539,.6521451548625461,.6521451548625461,.3478548451374539)
def quad(f,a,b):
    m=(a+b)/2; h=(b-a)/2
    return h*sum(w*f(m+h*x) for x,w in zip(X,W))

def read_inp(path):
    parts={}; mats={}; part=None; mode=None; mat=None; elastic=False; stress=False; pt=[]
    for line in path.open(encoding="utf-8"):
        s=line.strip()
        if not s or s.startswith("**"): continue
        if s.upper().startswith("*PART,"):
            part=re.search(r"name\s*=\s*([^,]+)",s,re.I).group(1).strip()
            if re.fullmatch(r"CSEG_\d{2}",part):
                parts[part]={"rings":defaultdict(list),"mat":None}
            mode=None
        elif s.upper().startswith("*END PART"): part=None; mode=None
        elif part in parts and s.upper().startswith("*NODE"): mode="node"
        elif part in parts and s.upper().startswith("*SOLID SECTION"):
            parts[part]["mat"]=re.search(r"material\s*=\s*([^,]+)",s,re.I).group(1).strip()
            mode=None
        elif s.upper().startswith("*MATERIAL,"):
            mat=re.search(r"name\s*=\s*([^,]+)",s,re.I).group(1).strip()
            mode=None
        elif s.upper().startswith("*ELASTIC"): elastic=True; mode=None; continue
        elif s.upper().startswith("*INITIAL CONDITIONS, TYPE=STRESS"):
            stress=True; mode=None; continue
        elif s.startswith("*"): mode=None
        elif part in parts and mode=="node":
            v=[float(q) for q in s.split(",") if q.strip()]
            if len(v)>=4:
                parts[part]["rings"][round(v[2],8)].append(math.hypot(v[1],v[3]))
        if elastic and not s.startswith("*"):
            mats[mat]=float(s.split(",")[0]); elastic=False
        if stress and not s.startswith("*"):
            q=[x.strip() for x in s.split(",") if x.strip()]
            if q[0].upper()=="PT_36X15P2-1.SET_PT_ALL_ELEMS": pt.append(float(q[1]))
            stress=False
    return parts,mats,pt

def segment(name,p,mats):
    layers=[]
    for y,r in sorted(p["rings"].items()):
        if len(r)!=216 or len(set(round(x,5) for x in r))!=3:
            raise ValueError("Unexpected ring topology: "+name)
        layers.append((y,min(r),max(r)))
    if len(layers)!=4: raise ValueError("Unexpected axial layers: "+name)
    E=mats[p["mat"]]; factor=36*math.sin(2*math.pi/72)
    vol=0.; compliance=0.
    for (y0,ri0,ro0),(y1,ri1,ro1) in zip(layers[:-1],layers[1:]):
        def A(y):
            t=(y-y0)/(y1-y0)
            ri=ri0+(ri1-ri0)*t; ro=ro0+(ro1-ro0)*t
            return factor*(ro*ro-ri*ri)
        vol+=quad(A,y0,y1)
        compliance+=quad(lambda y:1/(E*A(y)),y0,y1)
    h=layers[-1][0]-layers[0][0]
    return {"segment":name,"height_m":h,"E_Pa":E,"material":p["mat"],
            "polygon_volume_m3":vol,"axial_compliance_m_per_N":compliance,
            "area_avg_compliance_m_per_N":h*h/(E*vol)}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("inp",type=Path); a.add_argument("--out",type=Path,default=Path("."))
    args=a.parse_args(); args.out.mkdir(parents=True,exist_ok=True)
    parts,mats,pt=read_inp(args.inp)
    if len(parts)!=31 or len(pt)!=1: raise ValueError("31 concrete parts and 1 PT initial stress required")
    rows=[segment(k,parts[k],mats) for k in sorted(parts)]
    if abs(sum(r["height_m"] for r in rows)-112)>1e-4: raise ValueError("Height mismatch")
    C=sum(r["axial_compliance_m_per_N"] for r in rows)
    A_pt=.04032; E_pt=195e9; L_pt=112.
    P_in=pt[0]*A_pt; K_pt=E_pt*A_pt/L_pt; P_eq=P_in/(1+K_pt*C)
    out={"classification":"STATIC ELASTIC PROXY ONLY / NOT NATIVE PHYSICS PASS",
         "input_sha256":hashlib.sha256(args.inp.read_bytes()).hexdigest(),
         "input_pt_stress_Pa":pt[0],"input_Pe_MN":P_in/1e6,
         "concrete_volume_m3":sum(r["polygon_volume_m3"] for r in rows),
         "concrete_stiffness_MN_per_m":1/C/1e6,
         "pt_stiffness_MN_per_m":K_pt/1e6,
         "geometric_axial_compliance_m_per_N":C,
         "area_avg_compliance_m_per_N":sum(r["area_avg_compliance_m_per_N"] for r in rows),
         "hypothetical_PT_after_compatibility_MN":P_eq/1e6,
         "hypothetical_delta_MN":(P_in-P_eq)/1e6,
         "hypothetical_tower_shortening_mm":P_eq*C*1000,
         "assumptions":"Uncracked concrete only, 31 segments in series, elastic initial stress at zero displacement, no steel/joints/gravity/creep/relaxation; Abaqus initialization semantics unverified",
         "model_form_error":"NEED-ESTIMATE; no Abaqus Data Check or S03 equilibrium"}
    with (args.out/"S01_PT_CONCRETE_31SEG_GEOMETRIC_COMPLIANCE.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    (args.out/"S01_PT_STAGE_COMPATIBILITY_STATIC_PROXY.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
if __name__=="__main__": main()
