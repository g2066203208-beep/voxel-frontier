#!/usr/bin/env python3
"""S01: independently inventory frozen ORIGINAL T057 INP; static FE mass only.

Reads actual 68 Parts/Instances, 35 solid C3D8R/C3D8I Parts, and 33 T3D2
Parts. 2x2x2 Gauss integration for true 8-node isoparametric hex volumes.
No Abaqus/solver, no geometry editing, no scientific S01/S04 PASS.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

EXPECTED_NAME = "BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp"
EXPECTED_SHA = "c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db"
T070_SHA_REGISTERED = "9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9"
OF70_SHA_REGISTERED = "f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983"
OF70_TOWER_KG = 1923663.610690804
SIGNS = ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
         (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))
G = (-1 / math.sqrt(3), 1 / math.sqrt(3))

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()

def new_part(name):
    return {"name":name,"nodes":{},"elements":[],"type":None,
            "sections":[],"elsets":{}}

def parse_inp(lines):
    parts={};translations={};densities={};rna_kg=None
    part=None;mode=None;mat=None;instance=None;elset=None
    for raw in lines:
        line=raw.strip()
        if not line or line.startswith("**"):continue
        if line.startswith("*"):
            mode=None
            upper=line.upper()
            def parameter(name):
                for item in line.split(",")[1:]:
                    if "=" in item:
                        k,v=item.split("=",1)
                        if k.strip().lower()==name.lower():return v.strip()
                return None
            if upper.startswith("*PART,"):
                name=parameter("name")
                if not name or name in parts:raise ValueError("duplicate/unnamed Part")
                part=new_part(name);parts[name]=part
            elif upper.startswith("*END PART"):part=None
            elif upper.startswith("*NODE") and part:mode="node"
            elif upper.startswith("*ELEMENT,") and part:
                mode="element";part["type"]=parameter("type")
            elif upper.startswith("*SOLID SECTION,") and part:
                name=parameter("elset")
                part["sections"].append({"elset":name,"material":parameter("material"),"area":None})
                mode="section"
            elif upper.startswith("*ELSET,") and part:
                elset=parameter("elset")
                if elset is None:raise ValueError("Elset missing name")
                part["elsets"].setdefault(elset,[])
                mode="elset_generate" if "GENERATE" in upper else "elset_list"
            elif upper.startswith("*INSTANCE,"):
                instance=parameter("part")
                if instance not in parts:raise ValueError("unknown Instance part "+str(instance))
                translations[instance]=[0.,0.,0.]
                mode="instance"
            elif upper.startswith("*MATERIAL,"):mat=parameter("name")
            elif upper.startswith("*DENSITY"):mode="density"
            elif upper.startswith("*MASS,") and part is None:mode="mass"
            continue
        fields=[x.strip() for x in line.split(",") if x.strip()]
        if mode=="node" and part:
            if len(fields)!=4:raise ValueError("bad Node line")
            nid=int(fields[0])
            if nid in part["nodes"]:raise ValueError("duplicate node")
            part["nodes"][nid]=tuple(map(float,fields[1:]))
        elif mode=="element" and part:
            eid=int(fields[0])
            if len(fields) not in (3,9):raise ValueError("unsupported element connectivity")
            part["elements"].append((eid,tuple(map(int,fields[1:]))))
        elif mode=="section" and part:
            part["sections"][-1]["area"]=float(fields[0]) if fields else None
            mode=None
        elif mode=="elset_generate" and part:
            if len(fields)!=3:raise ValueError("bad generate elset")
            lo,hi,step=map(int,fields)
            if step<=0 or lo>hi:raise ValueError("bad elset range")
            part["elsets"][elset].append(("range",lo,hi,step))
        elif mode=="elset_list" and part:
            part["elsets"][elset].extend(("id",int(v)) for v in fields)
        elif mode=="instance":
            if len(fields)==3:translations[instance]=list(map(float,fields))
            mode=None
        elif mode=="density":
            if mat is None:raise ValueError("Density without material")
            densities[mat]=float(fields[0]);mode=None
        elif mode=="mass":
            rna_kg=float(fields[0]);mode=None
    return parts,translations,densities,rna_kg

def in_elset(eid,ranges):
    return any((lo<=eid<=hi and (eid-lo)%step==0) if item=="range"
               else eid==lo for item,lo,*rest in ranges
               for hi,step in ([rest[0],rest[1]] if item=="range" else [(lo,1)]))

def hex_integral(xyz):
    if len(xyz)!=8:raise ValueError("C3D8 needs 8 nodes")
    volume=ymoment=0.;min_det=math.inf
    for r in G:
        for s in G:
            for t in G:
                j=[0.]*9; y=0.
                for k,(a,b,c) in enumerate(SIGNS):
                    dr=a*(1+b*s)*(1+c*t)/8
                    ds=b*(1+a*r)*(1+c*t)/8
                    dt=c*(1+a*r)*(1+b*s)/8
                    xk,yk,zk=xyz[k]
                    j[0]+=xk*dr;j[1]+=xk*ds;j[2]+=xk*dt
                    j[3]+=yk*dr;j[4]+=yk*ds;j[5]+=yk*dt
                    j[6]+=zk*dr;j[7]+=zk*ds;j[8]+=zk*dt
                    y+=(1+a*r)*(1+b*s)*(1+c*t)/8*yk
                det=(j[0]*(j[4]*j[8]-j[5]*j[7])
                    -j[1]*(j[3]*j[8]-j[5]*j[6])
                    +j[2]*(j[3]*j[7]-j[4]*j[6]))
                if not math.isfinite(det) or det<=0:raise ValueError("nonpositive hex Jacobian")
                volume+=det;ymoment+=det*y;min_det=min(min_det,det)
    return volume,ymoment,min_det

def integrate(parts,translations,densities,rna_kg):
    rows=[];totals={};minimum_j=math.inf
    for name,p in parts.items():
        sections=p["sections"]
        if not sections:raise ValueError("no section: "+name)
        if len(sections)>1 and not all(s["elset"] in p["elsets"] for s in sections):
            raise ValueError("missing multi-section elset: "+name)
        if name not in translations:raise ValueError("Part has no instance: "+name)
        off=translations[name][1]
        m=ym=volume=0.
        for eid,ids in p["elements"]:
            if len(sections)==1:sec=sections[0]
            else:
                hits=[s for s in sections if in_elset(eid,p["elsets"][s["elset"]])]
                if len(hits)!=1:raise ValueError("ambiguous section: "+name)
                sec=hits[0]
            density=densities.get(sec["material"])
            if density is None or density<=0:raise ValueError("missing density: "+name)
            xyz=[p["nodes"][nid] for nid in ids]
            if p["type"] in ("C3D8R","C3D8I"):
                v,yv,j=hex_integral(xyz);minimum_j=min(minimum_j,j)
                mass=density*v;my=density*(yv+v*off);volume+=v
            elif p["type"]=="T3D2":
                if sec["area"] is None or sec["area"]<=0:raise ValueError("missing rod area")
                length=math.dist(xyz[0],xyz[1])
                mass=density*sec["area"]*length
                my=mass*((xyz[0][1]+xyz[1][1])/2+off)
            else:raise ValueError("unsupported element type: "+str(p["type"]))
            m+=mass;ym+=my
        if m<=0:raise ValueError("zero mass Part")
        if name.startswith("CSEG_"):group="concrete"
        elif name.startswith("SSEG_"):group="steel_tower"
        elif name.startswith("RBLONG_"):group="longitudinal_rebar"
        elif name.startswith("PT_"):group="PT"
        elif name=="HOOP_TIE_CAGE_T046":group="hoops_and_ties"
        else:raise ValueError("unexpected Part: "+name)
        totals[group]=totals.get(group,0.)+m
        rows.append({"part":name,"group":group,"element_type":p["type"],
                     "element_count":len(p["elements"]),"node_count":len(p["nodes"]),
                     "mass_kg":m,"centroid_y_m":ym/m,"volume_m3_if_solid":volume})
    if rna_kg is None or rna_kg<=0:raise ValueError("missing RNA point MASS")
    return rows,totals,minimum_j

def self_test():
    nodes=((0,0,0),(1,0,0),(1,1,0),(0,1,0),
           (0,0,1),(1,0,1),(1,1,1),(0,1,1))
    v,y,j=hex_integral(nodes)
    assert abs(v-1)<1e-12 and abs(y-.5)<1e-12 and abs(j-.125)<1e-12
    assert abs(math.dist((0,0,0),(0,1,0))*.1*7850-785)<1e-12
    try:hex_integral(tuple(reversed(nodes)))
    except ValueError:pass
    else:raise AssertionError("inverted element accepted")
    assert in_elset(201456,[("range",1,201456,1)])
    assert not in_elset(201457,[("range",1,201456,1)])
    print("SELF_TEST_PASS: exact unit cube, T3D2, inverted Jacobian, elset; NOT Abaqus")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inp",type=Path)
    ap.add_argument("--out-dir",type=Path)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test:self_test();return
    if args.inp is None or args.out_dir is None:ap.error("--inp and --out-dir required")
    if args.inp.name!=EXPECTED_NAME:raise SystemExit("REFUSE: wrong original T057 name")
    if not args.inp.is_file():raise SystemExit("REFUSE: T057 input not present")
    actual=sha256(args.inp)
    if actual!=EXPECTED_SHA:raise SystemExit("REFUSE: T057 source SHA256 mismatch "+actual)
    if args.out_dir.exists():raise SystemExit("REFUSE: output directory exists")
    with args.inp.open(encoding="utf-8",errors="strict") as f:
        parts,translations,densities,rna=parse_inp(f)
    rows,totals,minj=integrate(parts,translations,densities,rna)
    counts={g:sum(r["element_count"] for r in rows if r["group"]==g) for g in totals}
    expected_counts={"concrete":13392,"steel_tower":1728,"longitudinal_rebar":5440,
                     "hoops_and_ties":213768,"PT":36}
    if counts!=expected_counts or len(parts)!=68:raise SystemExit("REFUSE: unexpected topology")
    tower=sum(totals.values())
    if abs(tower-1985489.1181173)>0.1:raise SystemExit("REFUSE: mass regression")
    ordinary=totals["longitudinal_rebar"]+totals["hoops_and_ties"]
    displaced=ordinary*2400/7850
    record={"evidence":"DIRECT_FROZEN_T057_INP_2X2X2_GAUSS_STATIC_NOT_SOLVER",
      "source_sha256_verified":actual,"source_git_blob_registered":"da0b5ce5258b4fff08b2389851e29c32c6e4abfc",
      "T070_sha256_registered_only":T070_SHA_REGISTERED,
      "OpenFAST_70station_sha256_registered_only":OF70_SHA_REGISTERED,
      "OpenFAST_70station_mass_kg_registered":OF70_TOWER_KG,
      "element_counts":counts,"parts":len(parts),"min_positive_jacobian":minj,
      "component_mass_kg":totals,"RNA_mass_kg":rna,"tower_without_RNA_kg":tower,
      "tower_with_RNA_kg":tower+rna,
      "gross_difference_from_OpenFAST_pct":100*(tower/OF70_TOWER_KG-1),
      "host_displaced_concrete_kg_COUNTERFACTUAL":displaced,
      "net_mass_kg_COUNTERFACTUAL":tower-displaced,
      "net_difference_from_OpenFAST_pct_COUNTERFACTUAL":100*((tower-displaced)/OF70_TOWER_KG-1),
      "assumptions":["no deduction of embedded steel volume in actual FE gross mass",
       "conditional host replacement uses 2400/7850 density ratio",
       "no physical equivalence inferred from mass proximity",
       "RNA mass included only in separate tower+RNA total"],
      "numeric_error_budget":"2x2x2 exact integration for trilinear hex determinant; 3x3x3 independent cross-check still pending",
      "physical_error_budget":"NEED_ESTIMATE: embedded host overlap, real OpenFAST mass/EI provenance, PT/contact/RNA/modal/mesh",
      "native_abaqus":"NOT_RUN","standard_clause_pass":False,"seismic_results":0,
      "fig":"NONE","tab":"S01_T057_FULL_MESH_PARTS.csv","stage":"S01_PARTIAL_HOLD_S04_BLOCKED_0_OF_12"}
    args.out_dir.mkdir(parents=True,exist_ok=False)
    with (args.out_dir/"S01_T057_FULL_MESH_PARTS.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (args.out_dir/"S01_T057_FULL_MESH_LEDGER.json").write_text(
        json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"source_sha256":actual,"tower_without_RNA_kg":tower,
      "gross_diff_pct":record["gross_difference_from_OpenFAST_pct"],
      "net_conditional_diff_pct":record["net_difference_from_OpenFAST_pct_COUNTERFACTUAL"],
      "status":"STATIC_NOT_SOLVER"},ensure_ascii=False))

if __name__=="__main__":main()
