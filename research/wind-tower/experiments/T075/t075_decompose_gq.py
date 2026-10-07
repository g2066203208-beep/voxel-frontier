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
"""
from pathlib import Path
import csv,gzip,glob,json,math
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parent
GFILE=ROOT.parent/"T074"/"T074_158M_31SEG_GRAVITY_BASELINE.csv"
ART=ROOT/"artifacts"
OUT_GZ=ROOT/"T075_S06_31SEG_GQ_COMPONENT_COMBINATIONS.csv.gz"
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
    if len(fs)!=4: raise RuntimeError(f"expected 4 T071 histories, got {fs}")
    x=pd.concat([pd.read_csv(f) for f in fs],ignore_index=True)
    if x.segment.nunique()!=31: raise RuntimeError("full history segment count !=31")
    return x

def main():
    G=load_gravity(); X=load_total()
    rows=[]
    sums=[]
    comps=["Fx_kN","Fy_kN","Fz_kN","Mx_kNm","My_kNm","Mz_kNm"]
    for seg,q in X.groupby("segment",sort=True):
        q=q.sort_values("time_s").reset_index(drop=True)
        gv={c:float(G.loc[seg,c]) for c in comps}
        # variable operational/wind increment, signed component-by-component
        inc={c:q[c].to_numpy(float)-gv[c] for c in comps}
        for cname,meta in COMBOS.items():
            gg,gq=meta["gamma_G"],meta["gamma_Q"]
            d={c:gg*gv[c]+gq*inc[c] for c in comps}
            out=pd.DataFrame({
                "case":"U09p343881_ETM_S06","segment":seg,"time_s":q.time_s.to_numpy(float),
                "combo":cname,"gamma_G":gg,"gamma_Q":gq,
            })
            for c in comps:
                out["G_"+c]=gv[c]
                out["Q_"+c]=inc[c]
                out["D_"+c]=d[c]
            out["N_comp_kN"]=-out["D_Fz_kN"]
            out["V_kN"]=np.hypot(out["D_Fx_kN"],out["D_Fy_kN"])
            out["M_kNm"]=np.hypot(out["D_Mx_kNm"],out["D_My_kNm"])
            out["T_abs_kNm"]=np.abs(out["D_Mz_kNm"])
            rows.append(out)
            # independently summarized only for screening, not recombination
            sums.append({
                "segment":seg,"combo":cname,"gage_z_m":float(q.gage_z_m.iloc[0]),
                "Ncomp_max_kN":float(out.N_comp_kN.max()),
                "Mmax_kNm":float(out.M_kNm.max()),
                "Vmax_kN":float(out.V_kN.max()),
                "Tmax_kNm":float(out.T_abs_kNm.max()),
                "G_Fz_kN":gv["Fz_kN"],"G_Mx_kNm":gv["Mx_kNm"],"G_My_kNm":gv["My_kNm"],
            })
    Y=pd.concat(rows,ignore_index=True)
    Y.to_csv(OUT_GZ,index=False,compression="gzip")
    pd.DataFrame(sums).to_csv(OUT_SUM,index=False)
    meta={
        "method":"signed component-level G+Q effect decomposition",
        "equation":"D_i(t)=gamma_G*G_i + gamma_Q*(TOTAL_i(t)-G_i), i=Fx,Fy,Fz,Mx,My,Mz",
        "total_source":"T071 formal 158m U09p343881_ETM_S06 full 31-segment histories",
        "gravity_source":"T074 formal 158m fixed-DOF still-air/no-aero/no-servo gravity baseline",
        "combinations":COMBOS,
        "warning":"gamma values are not final NB/T Chapter-5 original-text closure; outputs are provisional but methodologically decomposed.",
        "rows":len(Y)
    }
    OUT_META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
