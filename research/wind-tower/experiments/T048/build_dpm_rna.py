#!/usr/bin/env python3
"""
T048 - DTU 10 MW distributed-parameter RNA generator for Abaqus/Standard.

Outputs a self-contained parked/modal validation deck and can patch the current
BASE001 tower input by replacing the T045 R2 single-CG RNA blocks with a DPM
part.

No third-party Python packages are required.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BLADE_ST = ROOT / "research/wind-tower/references/baselines-and-site-20261004/dtu-hawc2-reference/data/DTU_10MW_RWT_Blade_st.dat"
ELASTODYN = ROOT / "research/wind-tower/references/baselines-and-site-20261004/openfast-v330-adaptation/0Linearization/Template_Servo/DTU_10MW_RWT_ElastoDyn.dat"
DEFAULT_BASE = ROOT / "research/wind-tower/experiments/T046/inputs/BASE001_T046_E1B_HOOP_TIE_NSM_REMOVE.inp"
OUTDIR = Path(__file__).resolve().parent / "generated"

# T038 R2 reconstruction using actual ElastoDyn BldNodes=51 integration.
OPENFAST_R2_BLADE_MASS = 41732.3469077132
RNA_TARGET_MASS = 676753.2907231401

FIELDS = [
    "r","m","x_cg","y_cg","ri_x","ri_y","x_sh","y_sh","E","G",
    "I_x","I_y","I_p","k_x","k_y","A","pitch","x_e","y_e"
]

def vadd(a,b): return tuple(x+y for x,y in zip(a,b))
def vsub(a,b): return tuple(x-y for x,y in zip(a,b))
def vmul(s,a): return tuple(s*x for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(a): return math.sqrt(dot(a,a))
def unit(a):
    n=norm(a)
    if n <= 0: raise ValueError("zero vector")
    return vmul(1.0/n,a)
def rodrigues(v,axis,ang):
    k=unit(axis); c=math.cos(ang); s=math.sin(ang)
    return vadd(vadd(vmul(c,v), vmul(s,cross(k,v))), vmul((1-c)*dot(k,v),k))

def mat_zero(): return [[0.0]*3 for _ in range(3)]
def mat_add(A,B):
    return [[A[i][j]+B[i][j] for j in range(3)] for i in range(3)]
def mat_scale(s,A):
    return [[s*A[i][j] for j in range(3)] for i in range(3)]
def tensor_from_basis(vals,basis):
    A=mat_zero()
    for lam,e in zip(vals,basis):
        for i in range(3):
            for j in range(3):
                A[i][j]+=lam*e[i]*e[j]
    return A

def parse_hawc2_st(path: Path):
    lines=path.read_text(encoding="utf-8",errors="replace").splitlines()
    start=None; n=None
    for i,line in enumerate(lines):
        s=line.strip()
        if s.startswith("$1"):
            parts=s.replace("\t"," ").split()
            n=int(parts[1]); start=i+1; break
    if start is None:
        raise RuntimeError("Cannot find HAWC2 $1 subset.")
    rows=[]
    for line in lines[start:]:
        s=line.strip()
        if not s or s.startswith(("#","r","-","$")): continue
        vals=s.replace("\t"," ").split()
        try:
            nums=[float(x) for x in vals[:19]]
        except ValueError:
            continue
        if len(nums)==19:
            rows.append(dict(zip(FIELDS,nums)))
            if len(rows)==n: break
    if len(rows)!=n:
        raise RuntimeError(f"Expected {n} blade rows, got {len(rows)}")
    return rows

def parse_elastodyn(path: Path):
    wanted={"NumBl","TipRad","HubRad","PreCone(1)","OverHang","ShftTilt","NacCMxn",
            "NacCMyn","NacCMzn","Twr2Shft","HubMass","HubIner","NacMass","NacYIner"}
    out={}
    for raw in path.read_text(encoding="utf-8",errors="replace").splitlines():
        s=raw.strip()
        if not s or s.startswith("-"): continue
        parts=s.split()
        if len(parts)<2: continue
        key=parts[1]
        if key in wanted:
            try: out[key]=float(parts[0])
            except ValueError: pass
    miss=wanted-set(out)
    if miss: raise RuntimeError(f"Missing ElastoDyn values: {sorted(miss)}")
    return out

def trapezoid_mass(rows):
    total=0.0
    for a,b in zip(rows[:-1],rows[1:]):
        L=b["r"]-a["r"]
        total += 0.5*L*(a["m"]+b["m"])
    return total

def nodal_integral(rows, keyfun):
    vals=[keyfun(x) for x in rows]
    if isinstance(vals[0],list):
        raise TypeError("matrix use separate helper")
    out=[0.0]*len(rows)
    for i,(a,b) in enumerate(zip(rows[:-1],rows[1:])):
        L=b["r"]-a["r"]; fa=vals[i]; fb=vals[i+1]
        out[i]   += L*(2.0*fa+fb)/6.0
        out[i+1] += L*(fa+2.0*fb)/6.0
    return out

def nodal_matrix_integral(rows, mats):
    out=[mat_zero() for _ in rows]
    for i,(a,b) in enumerate(zip(rows[:-1],rows[1:])):
        L=b["r"]-a["r"]
        out[i]=mat_add(out[i],mat_scale(L/6.0, mat_add(mat_scale(2,mats[i]),mats[i+1])))
        out[i+1]=mat_add(out[i+1],mat_scale(L/6.0, mat_add(mats[i],mat_scale(2,mats[i+1]))))
    return out

def local_frame(shaft, azimuth_deg, precone_deg):
    lateral=(1.0,0.0,0.0)
    up=unit(cross(shaft,lateral))
    az=math.radians(azimuth_deg)
    radial=unit(vadd(vmul(math.cos(az),up),vmul(math.sin(az),lateral)))
    pc=math.radians(precone_deg)
    span=unit(vadd(vmul(math.cos(pc),radial),vmul(math.sin(pc),shaft)))
    # c2-x is projected shaft direction (approximately flapwise); c2-y completes RHS frame.
    c2x=unit(vsub(shaft,vmul(dot(shaft,span),span)))
    c2y=unit(cross(span,c2x))
    return span,c2x,c2y

def station_geometry(row, rotor_apex, hubrad, span, c2x, c2y):
    ref=vadd(rotor_apex,vmul(hubrad+row["r"],span))
    elastic=vadd(ref,vadd(vmul(row["x_e"],c2x),vmul(row["y_e"],c2y)))
    cg=vadd(ref,vadd(vmul(row["x_cg"],c2x),vmul(row["y_cg"],c2y)))
    pitch=math.radians(row["pitch"])
    e1=unit(vadd(vmul(math.cos(pitch),c2x),vmul(math.sin(pitch),c2y)))
    e2=unit(cross(span,e1))
    e3=span
    return ref,elastic,cg,(e1,e2,e3)

def inertia_density_global(row,basis,mass_scale):
    # HAWC2 radii of gyration are about principal axes through the elastic center.
    m=row["m"]*mass_scale
    pitch=math.radians(row["pitch"])
    dx=row["x_cg"]-row["x_e"]; dy=row["y_cg"]-row["y_e"]
    # Coordinates of CG offset in principal (e1,e2).
    d1= dx*math.cos(pitch)+dy*math.sin(pitch)
    d2=-dx*math.sin(pitch)+dy*math.cos(pitch)
    J1e=m*row["ri_x"]**2
    J2e=m*row["ri_y"]**2
    J1g=max(J1e-m*d2*d2,0.0)
    J2g=max(J2e-m*d1*d1,0.0)
    J3g=J1g+J2g
    return tensor_from_basis((J1g,J2g,J3g),basis)

def fmt(x): return f"{x:.12e}"

def build_model(rows,ed):
    src_mass=trapezoid_mass(rows)
    mass_scale=OPENFAST_R2_BLADE_MASS/src_mass

    top=(0.0,158.0,0.0)
    tilt=math.radians(abs(ed["ShftTilt"]))
    shaft=unit((0.0,-math.sin(tilt),math.cos(tilt)))
    rotor_apex=vadd(vadd(top,(0.0,ed["Twr2Shft"],0.0)),vmul(ed["OverHang"],shaft))
    nac_cm=(ed["NacCMyn"],158.0+ed["NacCMzn"],ed["NacCMxn"])

    nodes=[]; beam_elems=[]; mass_elems=[]; rot_elems=[]; mpcs=[]; sections=[]; rigid_nodes=[]
    audit_nodes=[]

    TOP=900000; HUB=900001; NAC=900002
    nodes += [(TOP,*top),(HUB,*rotor_apex),(NAC,*nac_cm)]
    rigid_nodes += [HUB,NAC]

    # Hub and nacelle concentrated inertia tensors in the global Abaqus frame.
    hubJ=tensor_from_basis((0.0,0.0,ed["HubIner"]),((1,0,0),unit(cross(shaft,(1,0,0))),shaft))
    # Easier exact axial form: J = HubIner * shaft outer shaft.
    hubJ=[[ed["HubIner"]*shaft[i]*shaft[j] for j in range(3)] for i in range(3)]
    nacJ=[[0.0]*3 for _ in range(3)]; nacJ[1][1]=ed["NacYIner"]

    mass_elems.append((800001,HUB,ed["HubMass"],"HUB"))
    rot_elems.append((810001,HUB,hubJ,"HUB"))
    mass_elems.append((800002,NAC,ed["NacMass"],"NAC"))
    rot_elems.append((810002,NAC,nacJ,"NAC"))

    blade_mass_total=0.0
    for b in range(3):
        az=120.0*b
        span,c2x,c2y=local_frame(shaft,az,ed["PreCone(1)"])
        station=[]
        mats=[]
        for i,row in enumerate(rows):
            ref,elastic,cg,basis=station_geometry(row,rotor_apex,ed["HubRad"],span,c2x,c2y)
            station.append((ref,elastic,cg,basis))
            mats.append(inertia_density_global(row,basis,mass_scale))

        scaled=[dict(r, m=r["m"]*mass_scale) for r in rows]
        nodal_mass=nodal_integral(scaled,lambda x:x["m"])
        nodal_J=nodal_matrix_integral(rows,mats)

        for i,(row,geom) in enumerate(zip(rows,station)):
            ref,elastic,cg,basis=geom
            sn=100000+b*1000+i+1
            mn=200000+b*1000+i+1
            nodes.append((sn,*elastic)); nodes.append((mn,*cg))
            m=nodal_mass[i]; blade_mass_total+=m
            mass_elems.append((820000+b*1000+i+1,mn,m,f"B{b+1}"))
            rot_elems.append((830000+b*1000+i+1,mn,nodal_J[i],f"B{b+1}"))
            mpcs.append((mn,sn))
            audit_nodes.append({
                "blade":b+1,"station":i+1,"r":row["r"],
                "elastic_xyz":elastic,"mass_xyz":cg,"nodal_mass":m
            })
            if i==0: rigid_nodes.append(sn)

        for i in range(len(rows)-1):
            sn1=100000+b*1000+i+1; sn2=100000+b*1000+i+2
            el=300000+b*1000+i+1
            es=f"B{b+1}S{i+1:02d}"
            beam_elems.append((el,sn1,sn2,es))
            a=rows[i]; c=rows[i+1]
            mid={k:0.5*(a[k]+c[k]) for k in FIELDS}
            # segment orientation from midpoint principal axis
            _,_,_,basis=station_geometry(mid,rotor_apex,ed["HubRad"],span,c2x,c2y)
            e1=basis[0]
            pitch=math.radians(mid["pitch"])
            dsx=mid["x_sh"]-mid["x_e"]; dsy=mid["y_sh"]-mid["y_e"]
            sh1=dsx*math.cos(pitch)+dsy*math.sin(pitch)
            sh2=-dsx*math.sin(pitch)+dsy*math.cos(pitch)
            Kx=mid["k_x"]*mid["G"]*mid["A"]
            Ky=mid["k_y"]*mid["G"]*mid["A"]
            sections.append({
                "elset":es,"A":mid["A"],"I11":mid["I_x"],"I22":mid["I_y"],"J":mid["I_p"],
                "E":mid["E"],"G":mid["G"],"orient":e1,
                "K23":Ky,"K13":Kx,"sh1":sh1,"sh2":sh2
            })

    audit={
        "source_blade_mass_trapezoid_kg":src_mass,
        "target_openfast_blade_mass_kg":OPENFAST_R2_BLADE_MASS,
        "blade_mass_scale":mass_scale,
        "generated_three_blade_mass_kg":blade_mass_total,
        "hub_mass_kg":ed["HubMass"],
        "nacelle_mass_kg":ed["NacMass"],
        "generated_rna_mass_kg":blade_mass_total+ed["HubMass"]+ed["NacMass"],
        "target_rna_mass_kg":RNA_TARGET_MASS,
        "tower_top":top,"rotor_apex":rotor_apex,"nacelle_cm":nac_cm,
        "shaft_unit_abq":shaft,"blade_station_count":len(rows)
    }
    return nodes,beam_elems,mass_elems,rot_elems,mpcs,sections,rigid_nodes,audit_nodes,audit

def tensor_line(J):
    return (J[0][0],J[1][1],J[2][2],J[0][1],J[0][2],J[1][2])

def part_text(model):
    nodes,beams,masses,rots,mpcs,sections,rigid_nodes,_,_=model
    o=[]
    o += ["*Part, name=RNA_DPM","*Node"]
    for n,x,y,z in nodes: o.append(f"{n}, {fmt(x)}, {fmt(y)}, {fmt(z)}")
    o += ["*Nset, nset=RNA_TOP","900000,","*Nset, nset=RNA_RIGID"]
    for i in range(0,len(rigid_nodes),16):
        o.append(", ".join(str(x) for x in rigid_nodes[i:i+16])+",")
    if beams:
        o.append("*Element, type=B31")
        for e,n1,n2,es in beams: o.append(f"{e}, {n1}, {n2}")
        for e,n1,n2,es in beams:
            o += [f"*Elset, elset={es}",f"{e},"]
    for eid,node,mass,tag in masses:
        o += [f"*Element, type=MASS, elset=M_{eid}",f"{eid}, {node}",f"*Mass, elset=M_{eid}",fmt(mass)]
    for eid,node,J,tag in rots:
        I=tensor_line(J)
        o += [f"*Element, type=ROTARYI, elset=J_{eid}",f"{eid}, {node}",f"*Rotary Inertia, elset=J_{eid}",
              ", ".join(fmt(x) for x in I)]
    for s in sections:
        o += [f"*Beam General Section, section=GENERAL, elset={s['elset']}, rotary inertia=EXACT",
              f"{fmt(s['A'])}, {fmt(s['I11'])}, 0., {fmt(s['I22'])}, {fmt(s['J'])}",
              ", ".join(fmt(x) for x in s["orient"]),
              f"{fmt(s['E'])}, {fmt(s['G'])}",
              "*Transverse Shear Stiffness",
              f"{fmt(s['K23'])}, {fmt(s['K13'])}, 0.25",
              "*Shear Center",
              f"{fmt(s['sh1'])}, {fmt(s['sh2'])}"]
    for mn,sn in mpcs:
        o += ["*MPC",f"BEAM, {mn}, {sn}"]
    # The hub, nacelle mass point and three blade-root elastic-axis nodes form a rigid hub/nacelle backbone.
    o += ["*Rigid Body, ref node=900000, tie nset=RNA_RIGID","*End Part"]
    return "\n".join(o)+"\n"

def standalone_text(model):
    part=part_text(model)
    o=["*Heading","T048 DTU 10 MW distributed-parameter RNA standalone parked modal validation",part,
       "*Assembly, name=ASSEMBLY","*Instance, name=RNA_DPM_I, part=RNA_DPM","*End Instance","*End Assembly",
       "*Boundary","RNA_DPM_I.RNA_TOP, 1, 6, 0.",
       "*Step, name=MODAL, perturbation","*Frequency, eigensolver=Lanczos","30, , , ,",
       "*Output, field","*Node Output","U,","*End Step"]
    return "\n".join(o)+"\n"

def drop_old_r2_blocks(text):
    lines=text.splitlines()
    out=[]; i=0; dropped=0; drop_next_kin=False
    while i < len(lines):
        if lines[i].lstrip().startswith("*"):
            j=i+1
            while j<len(lines) and not lines[j].lstrip().startswith("*"): j+=1
            block=lines[i:j]
            joined="\n".join(block).upper()
            hdr=lines[i].upper()
            kill=("RNA_R2_EQUIV" in joined or "R2RNA" in joined)
            if drop_next_kin and hdr.startswith("*KINEMATIC"):
                kill=True; drop_next_kin=False
            if kill:
                if hdr.startswith("*COUPLING"): drop_next_kin=True
                dropped+=1
            else:
                out.extend(block)
            i=j
        else:
            out.append(lines[i]); i+=1
    if dropped==0:
        raise RuntimeError("No T045 R2 equivalent RNA blocks found; baseline not patched.")
    return "\n".join(out)+"\n",dropped

def patch_baseline(base_text, model):
    clean,dropped=drop_old_r2_blocks(base_text)
    part=part_text(model)
    idx=clean.lower().find("*assembly")
    if idx<0: raise RuntimeError("Baseline has no *Assembly.")
    clean=clean[:idx]+part+clean[idx:]
    end=clean.lower().find("*end assembly")
    if end<0: raise RuntimeError("Baseline has no *End Assembly.")
    endline=clean.find("\n",end)
    inst="*Instance, name=RNA_DPM_I, part=RNA_DPM\n*End Instance\n"
    # Insert instance immediately before end assembly.
    clean=clean[:end]+inst+clean[end:]
    endline=clean.lower().find("*end assembly")
    endline=clean.find("\n",endline)
    eq=[]
    for dof in range(1,7):
        eq += ["*Equation","2",f"RNA_DPM_I.RNA_TOP, {dof}, 1.0",f"SET_TOWER_TOP_O, {dof}, -1.0"]
    clean=clean[:endline+1]+"\n".join(eq)+"\n"+clean[endline+1:]
    return clean,dropped

def write_csv(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["blade","station","r","ex","ey","ez","mx","my","mz","nodal_mass"])
        w.writeheader()
        for x in rows:
            e=x["elastic_xyz"]; m=x["mass_xyz"]
            w.writerow({"blade":x["blade"],"station":x["station"],"r":x["r"],
                        "ex":e[0],"ey":e[1],"ez":e[2],"mx":m[0],"my":m[1],"mz":m[2],
                        "nodal_mass":x["nodal_mass"]})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--blade-st",type=Path,default=BLADE_ST)
    ap.add_argument("--elastodyn",type=Path,default=ELASTODYN)
    ap.add_argument("--outdir",type=Path,default=OUTDIR)
    ap.add_argument("--patch-baseline",type=Path,default=None)
    ap.add_argument("--patched-output",type=Path,default=None)
    args=ap.parse_args()

    rows=parse_hawc2_st(args.blade_st)
    ed=parse_elastodyn(args.elastodyn)
    model=build_model(rows,ed)
    *_,audit_nodes,audit=model
    args.outdir.mkdir(parents=True,exist_ok=True)
    (args.outdir/"RNA_DPM_PART.inp").write_text(part_text(model),encoding="utf-8")
    (args.outdir/"RNA_DPM_STANDALONE.inp").write_text(standalone_text(model),encoding="utf-8")
    (args.outdir/"RNA_DPM_AUDIT.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
    write_csv(args.outdir/"RNA_DPM_NODES.csv",audit_nodes)

    if args.patch_baseline:
        out=args.patched_output or (args.outdir/"BASE001_T048_DPM.inp")
        text=args.patch_baseline.read_text(encoding="utf-8",errors="replace")
        patched,dropped=patch_baseline(text,model)
        out.write_text(patched,encoding="utf-8")
        audit["baseline"]=str(args.patch_baseline)
        audit["old_r2_blocks_dropped"]=dropped
        audit["patched_output"]=str(out)
        (args.outdir/"RNA_DPM_AUDIT.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")

    print(json.dumps(audit,indent=2))

if __name__=="__main__":
    main()
