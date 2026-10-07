#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T075 — Separate formal 158 m S06 tower section effects into permanent gravity
G and operational/wind increment Q(t), then form component-level provisional
NB/T 10907 Chapter-5 combinations.

IMPORTANT:
- gamma values 1.35/1.0 and 1.40 remain SECONDARY-CORROBORATED until original
  NB/T 10907 Chapter 5 pages are archived.
- This script fixes the prior methodological error of multiplying total N and
  total M by unrelated factors.
- Combination is performed on signed six-component section actions first:
    S_d(t) = gamma_G * G + gamma_Q * [S_total(t)-G]
  then resultants N/M/V/T are computed.
- The committed controller table is an auditable compact projection only.
  Capacity/design calculations must evaluate the complete time history.
"""
from pathlib import Path
import glob,json
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parent
GFILE=ROOT.parent/"T074"/"T074_158M_31SEG_GRAVITY_BASELINE.csv"
ART=ROOT/"artifacts"
OUT_CTL=ROOT/"T075_S06_31SEG_GQ_CONTROL_ROWS.csv"
OUT_SUM=ROOT/"T075_S06_31SEG_GQ_COMBINATION_SUMMARY.csv"
OUT_META=ROOT/"T075_GQ_DECOMPOSITION_META.json"

COMBOS={
    "G1p35_Q1p40":{"gamma_G":1.35,"gamma_Q":1.40,"identity":"SECONDARY-CORROBORATED / PRIMARY-TEXT-HOLD"},
    "G1p00_Q1p40":{"gamma_G":1.00,"gamma_Q":1.40,"identity":"SECONDARY-CORROBORATED / favorable-G branch / PRIMARY-TEXT-HOLD"},
}

def load_gravity():
    g=pd.read_csv(GFILE)
    if len(g)!=31 or g.segment.nunique()!=31:
        raise RuntimeError("gravity baseline must contain 31 unique segments")
    return g.set_index("segment")

def load_total():
    fs=sorted(glob.glob(str(ART/"*"/"*31seg.csv.gz")))
    if len(fs)!=4:
        raise RuntimeError(f"expected 4 T071 histories, got {fs}")
    x=pd.concat([pd.read_csv(f) for f in fs],ignore_index=True)
    if x.segment.nunique()!=31:
        raise RuntimeError("full history segment count !=31")
    return x

def controller_rows(out, gage_z_m):
    """Keep simultaneous signed state at the five controlling response instants."""
    metrics=[
        ("Ncomp_max","N_comp_kN","max"),
        ("Ncomp_min","N_comp_kN","min"),
        ("M_max","M_kNm","max"),
        ("V_max","V_kN","max"),
        ("T_max","T_abs_kNm","max"),
    ]
    rows=[]
    keep_cols=[
        "case","segment","time_s","combo","gamma_G","gamma_Q",
        "N_comp_kN","V_kN","M_kNm","T_abs_kNm",
        "G_Fx_kN","G_Fy_kN","G_Fz_kN","G_Mx_kNm","G_My_kNm","G_Mz_kNm",
        "Q_Fx_kN","Q_Fy_kN","Q_Fz_kN","Q_Mx_kNm","Q_My_kNm","Q_Mz_kNm",
        "D_Fx_kN","D_Fy_kN","D_Fz_kN","D_Mx_kNm","D_My_kNm","D_Mz_kNm",
    ]
    for label,col,mode in metrics:
        idx=out[col].idxmax() if mode=="max" else out[col].idxmin()
        r=out.loc[idx,keep_cols].to_dict()
        r["control_metric"]=label
        r["control_value"]=float(out.loc[idx,col])
        r["gage_z_m"]=float(gage_z_m)
        rows.append(r)
    return rows

def main():
    G=load_gravity()
    X=load_total()
    controls=[]
    sums=[]
    comps=["Fx_kN","Fy_kN","Fz_kN","Mx_kNm","My_kNm","Mz_kNm"]

    for seg,q in X.groupby("segment",sort=True):
        q=q.sort_values("time_s").reset_index(drop=True)
        gv={c:float(G.loc[seg,c]) for c in comps}
        inc={c:q[c].to_numpy(float)-gv[c] for c in comps}

        for cname,meta in COMBOS.items():
            gg,gq=meta["gamma_G"],meta["gamma_Q"]
            d={c:gg*gv[c]+gq*inc[c] for c in comps}
            out=pd.DataFrame({
                "case":"U09p343881_ETM_S06",
                "segment":seg,
                "time_s":q.time_s.to_numpy(float),
                "combo":cname,
                "gamma_G":gg,
                "gamma_Q":gq,
            })
            for c in comps:
                out["G_"+c]=gv[c]
                out["Q_"+c]=inc[c]
                out["D_"+c]=d[c]

            out["N_comp_kN"]=-out["D_Fz_kN"]
            out["V_kN"]=np.hypot(out["D_Fx_kN"],out["D_Fy_kN"])
            out["M_kNm"]=np.hypot(out["D_Mx_kNm"],out["D_My_kNm"])
            out["T_abs_kNm"]=np.abs(out["D_Mz_kNm"])

            controls.extend(controller_rows(out,float(q.gage_z_m.iloc[0])))
            sums.append({
                "segment":seg,
                "combo":cname,
                "gage_z_m":float(q.gage_z_m.iloc[0]),
                "Ncomp_max_kN":float(out.N_comp_kN.max()),
                "Ncomp_min_kN":float(out.N_comp_kN.min()),
                "Mmax_kNm":float(out.M_kNm.max()),
                "Vmax_kN":float(out.V_kN.max()),
                "Tmax_kNm":float(out.T_abs_kNm.max()),
                "G_Fz_kN":gv["Fz_kN"],
                "G_Mx_kNm":gv["Mx_kNm"],
                "G_My_kNm":gv["My_kNm"],
            })

    C=pd.DataFrame(controls)
    S=pd.DataFrame(sums)
    if len(C)!=31*len(COMBOS)*5:
        raise RuntimeError(f"controller row count mismatch: {len(C)}")
    if len(S)!=31*len(COMBOS):
        raise RuntimeError(f"summary row count mismatch: {len(S)}")

    C.to_csv(OUT_CTL,index=False)
    S.to_csv(OUT_SUM,index=False)
    meta={
        "method":"signed component-level G+Q effect decomposition",
        "equation":"D_i(t)=gamma_G*G_i + gamma_Q*(TOTAL_i(t)-G_i), i=Fx,Fy,Fz,Mx,My,Mz",
        "total_source":"T071 formal 158m U09p343881_ETM_S06 full 31-segment histories",
        "gravity_source":"T074 formal 158m fixed-DOF still-air/no-aero/no-servo gravity baseline",
        "combinations":COMBOS,
        "warning":"gamma values remain evidence-gated until primary Chapter-5 text is archived; compact controller rows are audit output only; final capacity evaluation must use full histories.",
        "controller_rows":len(C),
        "summary_rows":len(S),
        "segments":int(S.segment.nunique()),
    }
    OUT_META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
