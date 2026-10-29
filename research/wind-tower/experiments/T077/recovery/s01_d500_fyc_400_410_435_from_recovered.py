#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S01 D500 compression design-strength *sensitivity* on real four-case ETM histories.

No Abaqus, no normative choice, no geometry/fatigue/seismic PASS.
fyc=410: historical T077 assumption, not substantiated by 2024 GB/T50010 table.
fyc=435: GB/T50010-2024 table 4.2.3-1 ordinary HRB500 compression design value.
fyc=400: special axial-compression rule, NOT automatically applicable to eccentric tower.
Both 400 and 435 are sensitivity boundaries pending member classification and NB/T10907.

Usage:
 python s01_d500_fyc_400_410_435_from_recovered.py \
   --archives <U09S06.zip> <U11S04.zip> <U19S04.zip> <U19S06.zip> \
   --outdir <output-directory>

This repo-native script was ADDED after an independent local port actually ran the
93-variant screen on 2026-10-25. Do not claim this exact script has run until
a full repository clone and the archives are available and its log is retained.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import pandas as pd
from s01_exact_eta_31seg_from_recovered import ETA, evaluate, load_archives, t077

FYC_VARIANTS = (400.0, 410.0, 435.0)
FY = 435.0

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archives", nargs=4, type=Path, required=True)
    p.add_argument("--outdir", type=Path, required=True)
    args=p.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    histories, archive_sha=load_archives(args.archives)
    geom=t077.read_geom()
    rings=t077.read_rings(geom)
    gravity=t077.load_gravity()
    old=pd.read_csv(Path(__file__).with_name(
        "S01_D400_31SEG_MIN_DIAM_SCREEN_20261024.csv")).set_index("segment")
    if len(geom)!=31 or len(old)!=31:
        raise RuntimeError("Expected 31-segment original geometry and D500 historical comparison")
    rows=[]
    for seg in sorted(geom):
        g,ring=geom[seg],rings[seg]
        d=int(old.loc[seg,"d500_repo_d_mm"])
        qcases={case:q.sort_values("time_s").reset_index(drop=True)
                for case,q in histories.loc[histories.segment==seg].groupby("case")}
        grav={col:float(gravity.loc[seg,col])
              for col in ("Fx_kN","Fy_kN","Fz_kN","Mx_kNm","My_kNm","Mz_kNm")}
        for fyc in FYC_VARIANTS:
            r=evaluate(seg,g,ring,qcases,grav,FY,fyc,d,ETA)
            if not math.isfinite(r["util"]):
                raise RuntimeError(f"Nonfinite capacity: {seg} fyc={fyc}")
            if fyc==410:
                baseline=float(old.loc[seg,"d500_repo_u"])
                if abs(r["util"]-baseline)>1e-7:
                    raise RuntimeError(f"Historical D500 regression mismatch {seg}: {r['util']} vs {baseline}")
            rows.append({"segment":seg,"diameter_mm":d,"fy_MPa":FY,"fyc_MPa":fyc,
                         "eta":ETA,**r,"scope":"SECTION_SCREEN_NOT_NORMATIVE_OR_NATIVE"})
    df=pd.DataFrame(rows)
    output=args.outdir/"S01_D500_FYC_400_410_435_93CASE_NATIVE_SOURCE_REPLAY.csv"
    df.to_csv(output,index=False)
    summary={"scientific_status":"CONDITIONAL_SECTION_SCREEN_ONLY",
             "note":"93 segment-strength combinations (31x3) at historical D500 diameters, NOT a six-diameter scan",
             "source":"T077/T073 native repository functions and four S06 recovered history ZIPs",
             "archives":archive_sha,"fy_MPa":FY,"fyc_variants_MPa":FYC_VARIANTS,
             "eta_design_not_native":ETA,
             "max_u_by_fyc":{str(v):float(df.loc[df.fyc_MPa==v,"util"].max()) for v in FYC_VARIANTS},
             "segments_over_1_by_fyc":{str(v):int((df.loc[df.fyc_MPa==v,"util"]>1).sum()) for v in FYC_VARIANTS},
             "output_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
             "HOLD":"NB/T10907 authorized 4.2/6.4/8 clauses, HRB500 member classification, rebar cage, PT native equilibrium, S03/S04 source discrepancy, Abaqus V&V"}
    (args.outdir/"S01_D500_FYC_SENSITIVITY_MANIFEST.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
