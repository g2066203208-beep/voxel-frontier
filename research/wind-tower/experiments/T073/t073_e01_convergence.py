#!/usr/bin/env python3
from pathlib import Path
import csv, math, json
import numpy as np
import t073_e01_fixed_counts_feasible_map as m

ROOT=Path(__file__).resolve().parent
seg="CSEG_16"
D_BAR=46.0; BF=10; ETA=1.0
A=math.pi*D_BAR**2/4
targets={
 "uniform_1p40_screen":(22886.277822136057*1000,312573.15930185944*1e6),
 "provisional_N1p35_M1p40":(22068.91075705977*1000,312413.5002708073*1e6),
}
resolutions=[
 (8,180,750),
 (12,240,1000),
 (16,360,1500),
 (24,540,2200),
 (32,720,3000),
]
G=m.read_geom(); R=m.rings(G)
rows=[]
for nr,nt,nz in resolutions:
 m.NR=nr;m.NTH=nt;m.NZ=nz
 Nc,Mc,NsA,MsA,Np1,Mp1=m.components(seg,G[seg],R[seg],ETA)
 Nb,Mb=m.envelope(Nc+A*NsA+BF*Np1,Mc+A*MsA+BF*Mp1)
 for name,(Ntar,Mtar) in targets.items():
  if Ntar<Nb.min() or Ntar>Nb.max():
   cap=float("nan")
  else:
   cap=float(np.interp(Ntar,Nb,Mb))
  rows.append({"segment":seg,"bar_d_mm":D_BAR,"BF":BF,"eta":ETA,"NR":nr,"NTH":nt,"NZ":nz,
               "combo":name,"N_design_kN":Ntar/1000,"M_design_kNm":Mtar/1e6,
               "Mcap_kNm":cap/1e6,"utilization":Mtar/cap})
# relative to finest per combo
for name in targets:
 q=[r for r in rows if r["combo"]==name]
 ref=q[-1]["Mcap_kNm"]
 for r in q:r["Mcap_diff_vs_finest_pct"]=100*(r["Mcap_kNm"]/ref-1)
out=ROOT/"T073_E01_NUMERICAL_CONVERGENCE_CSEG16_D46_BF10.csv"
with out.open("w",newline="",encoding="utf-8") as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
meta={"purpose":"numerical convergence of borderline D46/BF10 candidate",
      "criterion":"do not freeze D46 if fine-grid utilization >=1 or discretization error is material",
      "finest":rows[-2:]}
(ROOT/"T073_E01_NUMERICAL_CONVERGENCE_META.json").write_text(json.dumps(meta,indent=2)+"\n")
print(json.dumps(meta,indent=2))
