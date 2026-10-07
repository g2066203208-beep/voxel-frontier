#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T077 — Formal NB/T 10907-2021 Table 5.2.5 + GB/T 50010 Appendix E.0.1
31-segment longitudinal reinforcement closure.

Locked:
- 158 m / 31 concrete segments.
- He Table 3-2 longitudinal counts per layer.
- T053 longitudinal-bar ring centrelines.
- PT geometry: 36 symmetric positions, r=1.75 m, 140 mm2 per modeled position.
- HRB500 code-design branch: fy=435 MPa, f'y=410 MPa.

Formal load combination for persistent normal-operation ULS:
- vertical load gamma_G = 1.35 (unfavourable) / 1.0 (favourable);
- wind-turbine horizontal force/bending/torsion and wind load gamma_Q = 1.4;
- prestress gamma_P = 1.2 (unfavourable) / 1.0 (favourable).
NB/T 10907 explanation 5.2.4 says the small turbine operational vertical load is
uniformly treated as gravity, so the entire vertical component is factored by gamma_G.

Prestress implementation:
The E.0.1 interaction curve already contains the baseline effective prestress sigma_p0.
To avoid double-counting, gamma_P is represented as only the additional action effect
(gamma_P-1)*P0, applied concentrically because the reconstructed 36-position PT ring is
symmetric. Both 1.0 and 1.2 branches are evaluated and the worse one governs.

All capacity checks preserve simultaneous N-M state at each time step.
"""
from pathlib import Path
import csv, glob, json, math
import numpy as np
import pandas as pd
import sys

ROOT=Path(__file__).resolve().parent
T073=ROOT.parent/"T073"
sys.path.insert(0,str(T073))
import t073_e01_fixed_counts_feasible_map as e01

GEOM=ROOT.parent/"T071"/"T071_input_geometry_31_segments.csv"
RADII=T073/"T073_T053_RBLONG_RADII.csv"
GFILE=ROOT.parent/"T074"/"T074_158M_31SEG_GRAVITY_BASELINE.csv"
ART=ROOT/"artifacts"

OUT_MAP=ROOT/"T077_FORMAL_HRB500_FIXED_HE_COUNTS_MAP.csv"
OUT_SEG_BF1=ROOT/"T077_FORMAL_31SEG_REBAR_BF1.csv"
OUT_SEG_BF8=ROOT/"T077_FORMAL_31SEG_REBAR_BF8.csv"
OUT_BF=ROOT/"T077_FORMAL_MIN_DIAMETER_BY_PT_BF.csv"
OUT_META=ROOT/"T077_FORMAL_REBAR_META.json"
OUT_REPORT=ROOT/"T077_FORMAL_REBAR_REPORT.md"

# Code-design ordinary reinforcement.
e01.FY=435.0
e01.FYC=410.0
# Keep source/later-lineage PT properties used by T073.
ETAS=(0.70,0.80,0.85,0.90,1.00)
DIAMS=(25,28,32,36,40,50)
BFS=tuple(range(1,17))
GAMMA_G=(1.35,1.00)
GAMMA_P=(1.20,1.00)
GAMMA_Q=1.40
EA_MIN_MM=20.0

def read_geom():
    with GEOM.open(encoding="utf-8-sig",newline="") as f:
        return {r["segment"]:r for r in csv.DictReader(f)}

def read_rings(geom):
    rr={}
    with RADII.open(encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            rr.setdefault(f"CSEG_{int(r['segment']):02d}",[]).append(r)
    out={}
    for seg,rows in rr.items():
        n=int(float(geom[seg]["bars_each_row"]))
        ex=[]
        for r in sorted(rows,key=lambda x:float(x["radius_m"])):
            ex += [float(r["radius_m"])*1000.0]*max(1,int(round(int(r["node_count_at_radius"])/n)))
        if len(ex)!=4:
            raise RuntimeError((seg,ex))
        out[seg]=(0.5*(ex[0]+ex[1]),0.5*(ex[2]+ex[3]),n)
    return out

def load_gravity():
    g=pd.read_csv(GFILE)
    if len(g)!=31 or g.segment.nunique()!=31:
        raise RuntimeError("gravity baseline must contain 31 unique segments")
    return g.set_index("segment")

def load_histories():
    files=sorted(glob.glob(str(ART/"**"/"*31seg.csv.gz"),recursive=True))
    if not files:
        raise RuntimeError("no 31-segment histories found")
    frames=[]
    for f in files:
        q=pd.read_csv(f)
        # Some artifact files contain only a batch subset.
        need={"case","segment","time_s","Fx_kN","Fy_kN","Fz_kN","Mx_kNm","My_kNm","Mz_kNm"}
        if not need.issubset(q.columns):
            continue
        frames.append(q[list(need)].copy())
    if not frames:
        raise RuntimeError("no valid history frames")
    x=pd.concat(frames,ignore_index=True)
    # Deduplicate in case an artifact is present twice.
    x=x.drop_duplicates(subset=["case","segment","time_s"],keep="first")
    cases=sorted(x["case"].unique())
    if "U09p343881_ETM_S06" not in cases:
        raise RuntimeError(f"S06 missing; found {cases}")
    if x.segment.nunique()!=31:
        raise RuntimeError(f"segment count !=31: {x.segment.nunique()}")
    return x,cases

def capacity_components(seg,g,ring,eta):
    # Reuse the validated E.0.1 discretization from T073.
    return e01.components(seg,g,ring,eta)

def upper_capacity(N,M):
    return e01.envelope(N,M)

def constructability(g,ring,d):
    return e01.constructability(g,ring,d)

def evaluate_one(seg, q, gv, ea_mm, Nb, Mb, bf, eta):
    """Return worst simultaneous state over formal gamma branches for one case+segment."""
    # Baseline effective prestress force represented by the capacity curve.
    p0_kN=e01.SIGP_INIT*eta*e01.PT_A1*e01.NPT*bf/1000.0
    best=None
    total={c:q[c].to_numpy(float) for c in ["Fx_kN","Fy_kN","Fz_kN","Mx_kNm","My_kNm","Mz_kNm"]}
    for gg in GAMMA_G:
        # Per NB/T explanation 5.2.4, whole vertical load is treated as gravity.
        Dfz=gg*total["Fz_kN"]
        # Other components: permanent gravity effect + 1.4 operational/wind increment.
        Dfx=gg*gv["Fx_kN"] + GAMMA_Q*(total["Fx_kN"]-gv["Fx_kN"])
        Dfy=gg*gv["Fy_kN"] + GAMMA_Q*(total["Fy_kN"]-gv["Fy_kN"])
        Dmx=gg*gv["Mx_kNm"] + GAMMA_Q*(total["Mx_kNm"]-gv["Mx_kNm"])
        Dmy=gg*gv["My_kNm"] + GAMMA_Q*(total["My_kNm"]-gv["My_kNm"])
        for gp in GAMMA_P:
            # baseline P0 is already in the interaction curve; add only extra factored effect.
            Ncomp=-Dfz + (gp-1.0)*p0_kN
            Mres=np.hypot(Dmx,Dmy)
            Md=(Mres + Ncomp*ea_mm/1000.0)*1e6
            Nd=Ncomp*1000.0
            cap=np.full_like(Nd,np.nan,dtype=float)
            m=(Nd>=Nb.min())&(Nd<=Nb.max())
            cap[m]=np.interp(Nd[m],Nb,Mb)
            util=np.where(np.isfinite(cap)&(cap>0),Md/cap,np.inf)
            k=int(np.nanargmax(util))
            rec={
                "util":float(util[k]),
                "time_s":float(q["time_s"].iloc[k]),
                "gamma_G":gg,
                "gamma_P":gp,
                "N_design_kN":float(Ncomp[k]),
                "M_design_kNm":float(Md[k]/1e6),
                "Mcap_kNm":float(cap[k]/1e6) if np.isfinite(cap[k]) else None,
            }
            if best is None or rec["util"]>best["util"]:
                best=rec
    return best

def main():
    geom=read_geom()
    rings=read_rings(geom)
    G=load_gravity()
    X,cases=load_histories()
    rows=[]

    # Cache interaction components for each segment/eta.
    C={(seg,eta):capacity_components(seg,geom[seg],rings[seg],eta)
       for seg in sorted(geom) for eta in ETAS}

    for seg in sorted(geom):
        g=geom[seg]
        ring=rings[seg]
        ea=max(EA_MIN_MM,float(g["D_m"])*1000.0/30.0)
        gv={c:float(G.loc[seg,c]) for c in ["Fx_kN","Fy_kN","Fz_kN","Mx_kNm","My_kNm","Mz_kNm"]}
        qcases={case:X[(X.case==case)&(X.segment==seg)].sort_values("time_s").reset_index(drop=True)
                for case in cases}
        qcases={k:v for k,v in qcases.items() if len(v)}
        for d in DIAMS:
            A=math.pi*d*d/4.0
            cov,clr=constructability(g,ring,d)
            for bf in BFS:
                worst=None
                for eta in ETAS:
                    Nc,Mc,NsA,MsA,Np1,Mp1=C[(seg,eta)]
                    Nb,Mb=upper_capacity(Nc+A*NsA+bf*Np1,Mc+A*MsA+bf*Mp1)
                    for case,q in qcases.items():
                        rec=evaluate_one(seg,q,gv,ea,Nb,Mb,bf,eta)
                        rec.update({"case":case,"eta":eta})
                        if worst is None or rec["util"]>worst["util"]:
                            worst=rec
                rows.append({
                    "segment":seg,
                    "He_bars_each_layer_LOCKED":ring[2],
                    "bar_d_mm":d,
                    "Abar_mm2":A,
                    "As_total_two_layers_mm2":2*ring[2]*A,
                    "BF":bf,
                    "max_utilization":worst["util"],
                    "control_case":worst["case"],
                    "control_eta":worst["eta"],
                    "control_time_s":worst["time_s"],
                    "control_gamma_G":worst["gamma_G"],
                    "control_gamma_P":worst["gamma_P"],
                    "N_design_kN":worst["N_design_kN"],
                    "M_design_kNm":worst["M_design_kNm"],
                    "Mcap_kNm":worst["Mcap_kNm"],
                    "min_net_cover_mm_if_T053_centrelines_fixed":cov,
                    "min_clear_bar_spacing_mm":clr,
                    "PASS":"PASS" if worst["util"]<=1.0 else "FAIL",
                })

    R=pd.DataFrame(rows)
    R.to_csv(OUT_MAP,index=False)

    # Minimum passing standard diameter independently for each segment and BF.
    mins=[]
    for bf in BFS:
        for seg in sorted(geom):
            q=R[(R.BF==bf)&(R.segment==seg)&(R.PASS=="PASS")]
            if len(q):
                r=q.sort_values("bar_d_mm").iloc[0].to_dict()
                r["status"]="PASS"
            else:
                # preserve worst available phi50 row for transparent failure reporting.
                r=R[(R.BF==bf)&(R.segment==seg)&(R.bar_d_mm==max(DIAMS))].iloc[0].to_dict()
                r["status"]="NONE<=50"
            mins.append(r)
    M=pd.DataFrame(mins)

    def schedule(bf,path):
        s=M[M.BF==bf].copy().sort_values("segment")
        s.to_csv(path,index=False)
        return s

    S1=schedule(1,OUT_SEG_BF1)
    S8=schedule(8,OUT_SEG_BF8)

    # Whole-tower summary by BF: maximum required diameter and governing segment.
    bfr=[]
    for bf in BFS:
        s=M[M.BF==bf]
        fails=(s.status!="PASS").sum()
        if fails:
            bfr.append({"BF":bf,"whole_tower_status":"FAIL","max_required_d_mm":"NONE<=50",
                        "governing_segment":"","governing_utilization":float(s.max_utilization.max()),
                        "failed_segments":int(fails)})
        else:
            mx=float(s.bar_d_mm.max())
            gg=s[s.bar_d_mm==mx].sort_values("max_utilization",ascending=False).iloc[0]
            bfr.append({"BF":bf,"whole_tower_status":"PASS","max_required_d_mm":int(mx),
                        "governing_segment":gg.segment,"governing_utilization":float(gg.max_utilization),
                        "failed_segments":0})
    B=pd.DataFrame(bfr)
    B.to_csv(OUT_BF,index=False)

    meta={
        "status":"FORMAL-NBT10907-CH5-COMBO + GBT50010-E01",
        "load_cases":cases,
        "segments":31,
        "NB_T_10907_2021":{
            "table":"5.2.5",
            "design_situation":"persistent / normal-operation / basic combination",
            "gamma_vertical_load":[1.35,1.0],
            "gamma_wind_turbine_horizontal_bending_torsion":1.4,
            "gamma_wind":1.4,
            "gamma_prestress":[1.2,1.0],
            "vertical_treatment":"entire vertical component factored as vertical/gravity load per explanation 5.2.4",
        },
        "ordinary_rebar":{
            "branch":"HRB500 code redesign; He counts locked",
            "fy_MPa":435.0,"fy_compression_MPa":410.0,
            "diameters_scanned_mm":DIAMS,
        },
        "prestress":{
            "positions":e01.NPT,"radius_mm":e01.PT_R,"area_single_mm2":e01.PT_A1,
            "sigma_initial_MPa":e01.SIGP_INIT,"eta":ETAS,"BF":BFS,
            "gammaP_method":"capacity curve contains baseline P0; only (gammaP-1)*P0 added to demand, concentric symmetric PT ring",
        },
        "source_model_PT_BF1_schedule_file":OUT_SEG_BF1.name,
        "BF8_sensitivity_schedule_file":OUT_SEG_BF8.name,
        "whole_tower_BF_summary_file":OUT_BF.name,
    }
    OUT_META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    def md_schedule(s,title):
        cols=["segment","He_bars_each_layer_LOCKED","bar_d_mm","max_utilization","control_case","control_eta","control_gamma_G","control_gamma_P"]
        lines=[f"## {title}","", "|segment|bars/layer|d (mm)|util|case|eta|γG|γP|","|---|---:|---:|---:|---|---:|---:|---:|"]
        for _,r in s[cols].iterrows():
            lines.append(f"|{r.segment}|{int(r.He_bars_each_layer_LOCKED)}|{int(r.bar_d_mm)}|{r.max_utilization:.4f}|{r.control_case}|{r.control_eta:.2f}|{r.control_gamma_G:.2f}|{r.control_gamma_P:.2f}|")
        return lines

    lines=[
        "# T077 — Formal 31-segment longitudinal reinforcement closure","",
        "Basis: NB/T 10907-2021 Table 5.2.5 + explanation 5.2.4; GB/T 50010 Appendix E.0.1.",
        "He Table 3-2 bar counts are unchanged. Results below are HRB500 CODE-DESIGN, not a claim that He (2024) published HRB500 or these diameters.","",
        "## Whole-tower PT bundle-factor scan","",
        "|BF|status|max required d (mm)|governing segment|util|failed segments|",
        "|---:|---|---:|---|---:|---:|",
    ]
    for _,r in B.iterrows():
        lines.append(f"|{int(r.BF)}|{r.whole_tower_status}|{r.max_required_d_mm}|{r.governing_segment}|{r.governing_utilization:.4f}|{int(r.failed_segments)}|")
    lines += [""] + md_schedule(S1,"BF=1 source-model-area branch") + [""] + md_schedule(S8,"BF=8 sensitivity branch")
    OUT_REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(meta,ensure_ascii=False,indent=2))
    print(B.to_string(index=False))

if __name__=="__main__":
    main()
