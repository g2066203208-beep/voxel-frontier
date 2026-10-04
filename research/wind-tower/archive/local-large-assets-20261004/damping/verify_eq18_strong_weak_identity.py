from pathlib import Path
import csv, math
import numpy as np
ROOT=Path(r"C:\Users\tt\Documents\Codex\2026-08-30\turbsim"); BASE=ROOT/'outputs'/'damping_final_20260902_CORRECTED'
sh=list(csv.DictReader((BASE/'HISTORICAL_FORMAL_MODE_SHAPES_BY_ELEVATION.csv').open(encoding='utf-8-sig')))
ei=list(csv.DictReader((BASE/'HISTORICAL_FORMAL_EI_SEGMENTS.csv').open(encoding='utf-8-sig')))
segs={}
for r in ei: segs.setdefault(r['segment'],[]).append((float(r['global_elevation_m']),float(r['EI_Nm2'])))
for s in segs: segs[s].sort()
order=sorted(segs,key=lambda s:min(x[0] for x in segs[s]))
inc={r['segment']:float(r['rebar_EI_increment_Nm2']) for r in csv.DictReader((BASE/'FORMAL_EFFECTIVE_EI_SEGMENTS.csv').open(encoding='utf-8-sig'))}
def dpoly(x,xp,fp,d,deg=5):
 idx=np.argsort(abs(xp-x))[:min(len(xp),deg+2)]; xs=xp[idx]; fs=fp[idx]; sc=max(np.ptp(xs),1.0); t=(xs-x)/sc; c=np.polynomial.polynomial.polyfit(t,fs,min(deg,len(idx)-1)); return float(np.polynomial.polynomial.polyval(0,np.polynomial.polynomial.polyder(c,d))/sc**d)
def fitseg(za,zb,z,y):
 idx=np.where((z>=za-4)&(z<=zb+4))[0]; idx=idx[np.argsort(abs(z[idx]-(za+zb)/2))[:min(len(idx),8)]]; xs=z[idx]; sc=max(np.ptp(xs),1.0); t=(xs-(za+zb)/2)/sc; return np.polynomial.polynomial.polyfit(t,y[idx],min(5,len(idx)-1)),(za+zb)/2,sc
rows=[]
for mode,field in [(1,'U1_norm'),(2,'U3_norm'),(3,'U1_norm'),(4,'U3_norm')]:
 rr=[r for r in sh if int(r['mode'])==mode]; z=np.array([float(r['elevation_m']) for r in rr]); y=np.array([float(r[field]) for r in rr]); o=np.argsort(z);z=z[o];y=y[o]
 for branch in ('WALL_ONLY_EI','FORMAL_EFFECTIVE_EI'):
  strong=weak=bulk=boundary=0.0
  for s in order:
   za,zb=min(x[0] for x in segs[s]),max(x[0] for x in segs[s]); zg=np.linspace(za,zb,max(32,int((zb-za)/0.25)+1)); ew=np.interp(zg,*zip(*segs[s])); ee=ew+(inc[s] if branch=='FORMAL_EFFECTIVE_EI' and s.startswith('CSEG_') else 0.)
   co,xc,sc=fitseg(za,zb,z,y); tt=(zg-xc)/sc; yy=np.polynomial.polynomial.polyval(tt,co); yp=np.polynomial.polynomial.polyval(tt,np.polynomial.polynomial.polyder(co,1))/sc; c2=np.polynomial.polynomial.polyder(co,2)/sc**2; cur=np.polynomial.polynomial.polyval(tt,c2); ec=np.polynomial.polynomial.polyfit(tt,ee,1); qc=np.polynomial.polynomial.polymul(ec,c2); q=np.polynomial.polynomial.polyval(tt,qc); qp=np.polynomial.polynomial.polyval(tt,np.polynomial.polynomial.polyder(qc,1))/sc; qpp=np.polynomial.polynomial.polyval(tt,np.polynomial.polynomial.polyder(qc,2))/sc**2
   strong+=float(np.trapezoid(yy*qpp,zg)); b=float(np.trapezoid(ee*cur**2,zg)); bd=float(yy[-1]*qp[-1]-yp[-1]*q[-1] - (yy[0]*qp[0]-yp[0]*q[0])); bulk+=b; boundary+=bd; weak+=b+bd
  rows.append([mode,branch,strong,weak,strong-weak,bulk,boundary,abs(strong-weak)/max(abs(strong),abs(weak),1e-30)])
with (BASE/'EQ18_STRONG_WEAK_IDENTITY.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['mode','EI_branch','strong_integral','weak_integral','difference','bulk_curvature_energy','all_segment_boundary_terms','relative_difference']);w.writerows(rows)
print(BASE/'EQ18_STRONG_WEAK_IDENTITY.csv')
