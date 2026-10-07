#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T073 — GB/T 50010 Appendix E.0.1 fiber-section audit for the He-aligned tower.

Purpose
-------
Keep all He (2024) SOURCE-DIRECT geometry/counts unchanged and evaluate the
combined concrete + ordinary longitudinal rebar + prestressing tendons by the
general Appendix E.0.1 strain-compatibility/equilibrium method.

This is NOT the previous E.0.3 simplified annular back-solve.  E.0.1 explicitly
permits concrete, ordinary reinforcement and prestressing reinforcement to be
discretized simultaneously.

Primary branch keeps the T053 source-model ordinary rebar identity S345 and its
reconstructed section area.  Since S345 is not an NB/T 10907 ordinary rebar
grade, results are labelled SOURCE-MODEL-CAPACITY-CHECK, not a code-direct
reinforcing-bar design.

Units: mm, MPa=N/mm2, N, N*mm.
"""
from __future__ import annotations
import csv, gzip, glob, json, math, os
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
GEOM=ROOT.parent/"T071"/"T071_input_geometry_31_segments.csv"
RADII=ROOT/"T073_T053_RBLONG_RADII.csv"
OUT_SUM=ROOT/"T073_E01_HE_LOCKED_PT_BUNDLE_SCAN.csv"
OUT_SEG=ROOT/"T073_E01_HE_LOCKED_31SEG_CONTROL.csv"
OUT_META=ROOT/"T073_E01_META.json"

# Source/reconstruction identities.
ABAR_MM2=490.874                  # T053 actual section = 0.000490874 m2, NOT He thesis direct.
ES=200000.0
FY_S345=345.0                    # source-model yield identity, symmetric capacity screen.
FYC_S345=345.0
EP=195000.0
FPY=1320.0
FPYC=390.0
SIGMA_P_INITIAL=1280.0           # later-lineage/source-model input, NOT He thesis direct.
PT_AREA_SINGLE_MM2=140.0         # T053 section area per one modeled position.
PT_RADIUS_MM=1750.0
PT_POSITIONS=36
ETAS=(0.70,0.80,0.85,0.90,1.00)
BFS=tuple(range(1,17))
NR=16
NTH=360
N_ZN=1500

def load_geom():
    with GEOM.open(encoding="utf-8-sig",newline="") as f:
        return {r["segment"]:r for r in csv.DictReader(f)}

def load_ring_centres(geom):
    rr={}
    with RADII.open(encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            rr.setdefault(f"CSEG_{int(r['segment']):02d}",[]).append(r)
    out={}
    for seg,rows in rr.items():
        n=int(float(geom[seg]["bars_each_row"]))
        expanded=[]
        for r in sorted(rows,key=lambda x:float(x["radius_m"])):
            reps=max(1,int(round(int(r["node_count_at_radius"])/n)))
            expanded += [float(r["radius_m"])*1000.0]*reps
        if len(expanded)!=4:
            raise RuntimeError(f"{seg}: expected 4 endpoint radii after multiplicity expansion, got {expanded}")
        out[seg]={
            "r_inner_mm":0.5*(expanded[0]+expanded[1]),
            "r_outer_mm":0.5*(expanded[2]+expanded[3]),
            "n_each":n,
        }
    return out

def concrete_params(seg):
    if seg in ("CSEG_01","CSEG_02"):
        fcu,fc=70.0,31.8
    else:
        fcu,fc=65.0,29.7
    n=2.0-(fcu-50.0)/60.0
    eps0=0.002+0.5*(fcu-50.0)*1e-5
    epscu=0.0033-(fcu-50.0)*1e-5
    return fcu,fc,n,eps0,epscu

def sigma_c(eps,fc,n,eps0):
    # compression positive, concrete tension ignored.
    e=np.asarray(eps)
    s=np.zeros_like(e,dtype=float)
    m=(e>0)&(e<=eps0)
    q=np.clip(1.0-e[m]/eps0,0.0,None)
    s[m]=fc*(1.0-q**n)
    s[e>eps0]=fc
    return s

def fiber_geometry(D_mm,di_mm):
    ro=D_mm/2.0; ri=di_mm/2.0
    dr=(ro-ri)/NR
    dth=2*math.pi/NTH
    rs=ri+(np.arange(NR)+0.5)*dr
    th=(np.arange(NTH)+0.5)*dth
    R,T=np.meshgrid(rs,th,indexing="ij")
    z=(R*np.sin(T)).ravel()
    area=(R*dr*dth).ravel()
    return z,area

def interaction_components(seg,g,ring,eta):
    D=float(g["D_m"])*1000.0
    di=float(g["di_m"])*1000.0
    ro=D/2.0
    fcu,fc,n,eps0,epscu=concrete_params(seg)
    zc,ac=fiber_geometry(D,di)

    # Two He-locked rings; counts are never changed.
    nbar=ring["n_each"]
    theta=2*math.pi*np.arange(nbar)/nbar
    zs=np.concatenate([
        ring["r_inner_mm"]*np.sin(theta),
        ring["r_outer_mm"]*np.sin(theta)
    ])
    As=np.full(zs.size,ABAR_MM2)
    z_s_tension_extreme=float(zs.min())

    # 36 T053 source-model PT positions. BF scales area only as a sensitivity.
    thp=2*math.pi*np.arange(PT_POSITIONS)/PT_POSITIONS
    zp=PT_RADIUS_MM*np.sin(thp)
    Ap1=np.full(PT_POSITIONS,PT_AREA_SINGLE_MM2)
    sigp0=SIGMA_P_INITIAL*eta

    # Neutral-axis scan; ultimate state is governed by concrete compression edge
    # eps_cu or outermost tensile ordinary bar strain 0.01.
    zn=np.concatenate([
        np.linspace(-3.0*ro,-ro,150,endpoint=False),
        np.linspace(-ro,0.999*ro,N_ZN-150)
    ])
    kc=epscu/(ro-zn)
    ks=np.where(zn>z_s_tension_extreme,0.01/(zn-z_s_tension_extreme),np.inf)
    kap=np.minimum(kc,ks)

    Nbase=np.empty_like(zn); Mbase=np.empty_like(zn)
    Npt1=np.empty_like(zn); Mpt1=np.empty_like(zn)

    # Chunk over NA states to limit memory.
    chunk=50
    for i in range(0,len(zn),chunk):
        sl=slice(i,min(i+chunk,len(zn)))
        zz=zn[sl,None]; kk=kap[sl,None]

        ec=kk*(zc[None,:]-zz)
        sc=sigma_c(ec,fc,n,eps0)
        Nc=(sc*ac[None,:]).sum(axis=1)
        Mc=(sc*ac[None,:]*zc[None,:]).sum(axis=1)

        es=kk*(zs[None,:]-zz)
        ss=np.clip(ES*es,-FY_S345,FYC_S345)
        sc_at_s=sigma_c(es,fc,n,eps0)
        # gross-concrete integral corrected at embedded bar locations.
        corr=(ss-sc_at_s)*As[None,:]
        Ns=corr.sum(axis=1)
        Ms=(corr*zs[None,:]).sum(axis=1)

        epsec=kk*(zp[None,:]-zz)
        # prestress tension stress positive; compression section strain reduces tension.
        sp=np.clip(sigp0-EP*epsec,sigp0-FPYC,FPY)
        Fp=-sp*Ap1[None,:]       # internal compression-positive sign
        Np=Fp.sum(axis=1)
        Mp=(Fp*zp[None,:]).sum(axis=1)

        Nbase[sl]=Nc+Ns
        Mbase[sl]=Mc+Ms
        Npt1[sl]=Np
        Mpt1[sl]=Mp

    return Nbase,Mbase,Npt1,Mpt1,{
        "D_mm":D,"di_mm":di,"fc":fc,"fcu":fcu,"n":n,"eps0":eps0,"epscu":epscu,
        "r_inner_bar_mm":ring["r_inner_mm"],"r_outer_bar_mm":ring["r_outer_mm"],
        "n_each":nbar,
    }

def upper_capacity(N,M):
    # Convert interaction samples to a stable upper M(N) interpolation.
    N=np.asarray(N); M=np.abs(np.asarray(M))
    ok=np.isfinite(N)&np.isfinite(M)
    N=N[ok]; M=M[ok]
    order=np.argsort(N); N=N[order]; M=M[order]
    # Bin by axial force (0.1% of range or at least 50 kN) and keep max M.
    span=max(float(N.max()-N.min()),1.0)
    bw=max(span/2500.0,5e4)
    bins=np.floor((N-N.min())/bw).astype(int)
    uniq=np.unique(bins)
    Nb=np.array([N[bins==b].mean() for b in uniq])
    Mb=np.array([M[bins==b].max() for b in uniq])
    order=np.argsort(Nb)
    return Nb[order],Mb[order]

def capacity_at(Nb,Mb,targetN):
    t=np.asarray(targetN)
    out=np.full_like(t,np.nan,dtype=float)
    m=(t>=Nb.min())&(t<=Nb.max())
    out[m]=np.interp(t[m],Nb,Mb)
    return out

def load_histories():
    # Workflow extracts all four T071 artifacts to T073/artifacts/A..D.
    files=sorted(glob.glob(str(ROOT/"artifacts"/"*"/"*31seg.csv.gz")))
    if len(files)!=4:
        raise RuntimeError(f"expected four T071 full-history gzip files, found {files}")
    byseg={}
    for p in files:
        with gzip.open(p,"rt",newline="") as f:
            for r in csv.DictReader(f):
                byseg.setdefault(r["segment"],[]).append(r)
    # Convert once to arrays.
    out={}
    for seg,rs in byseg.items():
        out[seg]={
            "time":np.array([float(r["time_s"]) for r in rs]),
            "N":np.array([-float(r["Fz_kN"]) for r in rs]), # compression positive, tension negative
            "M":np.array([float(r["M_kNm"]) for r in rs]),
        }
    return out

def evaluate_combo(hist,ea_mm,Nb,Mb,gN,gM):
    Nd=hist["N"]*gN*1000.0 # N
    Md=(hist["M"]*gM + (hist["N"]*gN)*ea_mm/1000.0)*1e6 # N mm
    Mc=capacity_at(Nb,Mb,Nd)
    util=np.where(np.isfinite(Mc)&(Mc>0),Md/Mc,np.inf)
    k=int(np.nanargmax(util))
    return {
        "max_util":float(util[k]),"time_s":float(hist["time"][k]),
        "N_design_kN":float(Nd[k]/1000.0),"M_design_kNm":float(Md[k]/1e6),
        "Mcap_kNm":float(Mc[k]/1e6) if np.isfinite(Mc[k]) else None,
    }

def main():
    geom=load_geom()
    rings=load_ring_centres(geom)
    hist=load_histories()

    rows=[]
    overall=[]
    combos={
        "uniform_1p40_screen":(1.40,1.40),
        "provisional_N1p35_M1p40":(1.35,1.40),
    }

    # Precompute base/one-BF PT interaction components for each seg/eta.
    for seg in sorted(geom):
        g=geom[seg]; ring=rings[seg]
        ea=max(20.0,float(g["D_m"])*1000.0/30.0)
        cache={}
        for eta in ETAS:
            cache[eta]=interaction_components(seg,g,ring,eta)
        for bf in BFS:
            for eta in ETAS:
                Nbase,Mbase,Np1,Mp1,meta=cache[eta]
                Nb,Mb=upper_capacity(Nbase+bf*Np1,Mbase+bf*Mp1)
                for cname,(gN,gM) in combos.items():
                    res=evaluate_combo(hist[seg],ea,Nb,Mb,gN,gM)
                    rows.append({
                        "segment":seg,"combo":cname,"BF":bf,"eta":eta,
                        "sigma_p0_MPa":SIGMA_P_INITIAL*eta,
                        "He_bars_each_row_LOCKED":ring["n_each"],
                        "Abar_mm2_T053_reconstructed":ABAR_MM2,
                        "r_inner_bar_mm_T053":round(ring["r_inner_mm"],3),
                        "r_outer_bar_mm_T053":round(ring["r_outer_mm"],3),
                        "PT_positions_T053":PT_POSITIONS,
                        "PT_radius_mm_T053":PT_RADIUS_MM,
                        "PT_area_per_position_mm2_times_BF":PT_AREA_SINGLE_MM2*bf,
                        "max_utilization":res["max_util"],
                        "control_time_s":res["time_s"],
                        "N_design_kN":res["N_design_kN"],
                        "M_design_kNm":res["M_design_kNm"],
                        "Mcap_kNm":res["Mcap_kNm"],
                    })

    # Aggregate worst eta and segment per BF/combo.
    for cname in combos:
        for bf in BFS:
            q=[r for r in rows if r["combo"]==cname and r["BF"]==bf]
            ctl=max(q,key=lambda r:r["max_utilization"])
            overall.append({
                "combo":cname,"BF":bf,
                "max_utilization_all_segments_eta":ctl["max_utilization"],
                "control_segment":ctl["segment"],"control_eta":ctl["eta"],
                "control_time_s":ctl["control_time_s"],
                "N_design_kN":ctl["N_design_kN"],"M_design_kNm":ctl["M_design_kNm"],
                "Mcap_kNm":ctl["Mcap_kNm"],
                "PASS_all_segments_eta":"PASS" if ctl["max_utilization"]<=1.0 else "FAIL",
            })

    # For each segment, report worst eta at the first BF that passes the whole tower,
    # otherwise BF=16.
    selected={}
    for cname in combos:
        qq=[r for r in overall if r["combo"]==cname and r["max_utilization_all_segments_eta"]<=1.0]
        selected[cname]=min((r["BF"] for r in qq),default=max(BFS))
    segout=[]
    for cname,bf in selected.items():
        for seg in sorted(geom):
            q=[r for r in rows if r["combo"]==cname and r["BF"]==bf and r["segment"]==seg]
            ctl=max(q,key=lambda r:r["max_utilization"])
            ctl=dict(ctl)
            ctl["selected_BF_for_combo"]=bf
            ctl["segment_PASS"]="PASS" if ctl["max_utilization"]<=1.0 else "FAIL"
            segout.append(ctl)

    with OUT_SUM.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(overall[0]));w.writeheader();w.writerows(overall)
    with OUT_SEG.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(segout[0]));w.writeheader();w.writerows(segout)

    meta={
        "method":"GB/T 50010 Appendix E.0.1 numerical strain compatibility/equilibrium",
        "ordinary_rebar_primary_identity":"T053 S345 source-model capacity check; He Table 3-2 counts LOCKED",
        "ordinary_bar_area_mm2":ABAR_MM2,
        "ordinary_bar_area_identity":"T053 reconstructed input, NOT He thesis direct",
        "pt_identity":"T053 36 positions, r=1.75m, 140mm2/position; BF sensitivity NOT He thesis direct",
        "sigma_p_initial_MPa":SIGMA_P_INITIAL,
        "etas":ETAS,"BFs":BFS,
        "fiber_mesh":{"nr":NR,"ntheta":NTH,"neutral_axis_states":N_ZN},
        "combos":{
            "uniform_1p40_screen":"screen only",
            "provisional_N1p35_M1p40":"secondary-corroborated pending original NB/T 10907 chapter 5 page archive"
        },
        "selected_BF":selected,
    }
    OUT_META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"selected_BF":selected,"overall_last":overall[-1]},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
