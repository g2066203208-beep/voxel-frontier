#!/usr/bin/env python3
"""S10 independent 16/32/64 azimuth-grid sensitivity on ONE recovered 31-segment ETM case.
No solver; conditional gross annular linear stress, not PT/joint/material fatigue or DLC1.2.
Signed source-frame formula sigma[MPa]=1e-3*(Fz/A+(Mx*r*sin(theta)-My*r*cos(theta))/I).
The 16-angle baseline exists already; this computes the NEW 32/64 grid sensitivity.
"""
import argparse,csv,gzip,hashlib,io,math,zipfile,json
from collections import deque
from pathlib import Path
import numpy as np
import pandas as pd
CASE='U09p343881_ETM_S06'
BATCHES={'A':range(1,10),'B':range(10,19),'C':range(19,28),'D':range(28,32)}
ZIP_SHA={'A':'ebccacd12a6f5fb3e6098c5130a7ca355409c4f7d5be4169ab23e4b265cd477f',
'B':'5acbb25968ce43892157545cded26973623f22b5a137839e5154b293aef167db',
'C':'f202176ca1b1849f2de2b278c5cc1aab2a70892bfbee5163c70950f36920b9ab',
'D':'8ac68a5cdc2da3eceadbc2ca6507ae2ded953610fcc4d21f58169a0775fa17ab'}
# Geometry (A m2, I m4, outer radius m) transcribed from source-locked T077
# S10_4ETM_31SEG_NOMINAL_COMPONENT_STRESS_DEL_M4_20261102.csv;
# upstream gross-section CSV SHA256 fff6dfcc6bc094353ebee042392033e8df47e7fb792ccc1812c0962c9c43f800.
GEOM='''7.010775,55.735042,4.124999738
6.870036,52.448000,4.044999962
6.729294,49.292833,3.964999954
6.621272,46.543725,3.887499861
6.567417,44.234386,3.809999931
6.550177,42.029640,3.724999882
6.561645,40.162865,3.644999917
6.549198,38.321199,3.569999943
6.495870,36.202293,3.489999864
6.461661,34.245816,3.409999956
6.444538,32.426400,3.329999926
6.396595,30.525988,3.249999832
6.319863,28.575457,3.169999938
6.259540,26.765364,3.089999943
6.213594,25.075501,3.009999799
6.139536,23.354065,2.929999952
6.064917,22.050940,2.869999890
6.039394,21.624956,2.849999889
6.039394,21.624956,2.849999889
5.882629,21.137021,2.849999890
5.567214,20.143430,2.849999753
5.408563,19.637680,2.849999856
5.408563,19.637680,2.849999856
5.408563,19.637680,2.849999856
5.169410,18.867732,2.849999896
4.686863,17.286466,2.849999766
4.443468,16.474821,2.849999735
4.443468,16.474821,2.849999735
5.201379,18.971181,2.849999783
6.262271,21.208697,2.787499890
6.823917,19.448040,2.604999797'''
GEOS=[tuple(map(float,row.split(','))) for row in GEOM.splitlines()]
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(x,msg):
 if not x:raise ValueError(msg)
def turns(x):
 x=np.asarray(x,dtype=float);ck(x.ndim==1 and len(x)>1 and np.isfinite(x).all(),'BAD_SIGNAL')
 y=x[np.r_[True,np.diff(x)!=0]]
 if len(y)==1:return y
 d=np.diff(y);return y[np.r_[True,d[:-1]*d[1:]<0,True]]
def rainflow(x):
 q=deque();cycles=[]
 for v in turns(x):
  q.append(float(v))
  while len(q)>=3:
   a=abs(q[-2]-q[-3]);b=abs(q[-1]-q[-2])
   if a>b:break
   if len(q)==3:
    if a>0:cycles.append((a,.5))
    q.popleft()
   else:
    if a>0:cycles.append((a,1.))
    q[-3]=q[-1];q.pop();q.pop()
 while len(q)>1:
  r=abs(q[1]-q[0])
  if r>0:cycles.append((r,.5))
  q.popleft()
 return cycles
def both_del(x):
 cy=rainflow(x)
 return tuple((math.fsum(n*r**m for r,n in cy)/600)**(1/m) for m in (4,10))
def stress(fz,mx,my,a,i,r,deg):
 ck(a>0 and i>0 and r>0,'GEOMETRY');t=math.radians(deg)
 return .001*(fz/a+(mx*r*math.sin(t)-my*r*math.cos(t))/i)
def selftest():
 ck(len(GEOS)==31,'GEOM_ROWS')
 ck(rainflow([0,1,0])==[(1,.5),(1,.5)],'HALF')
 ck(rainflow([0,3,1,2,0])==[(1,1.),(3,.5),(3,.5)],'FULL')
 ck(abs(stress(-1000,0,0,2,5,3,0)+.5)<1e-12,'AXIAL')
 ck(abs(stress(0,0,1000,2,5,3,0)+.6)<1e-12,'MOMENT')
 ck(abs(stress(0,1000,0,2,5,3,90)-.6)<1e-12,'ROTATION')
 for bad in ([0,float('nan')],[1],[[1,2],[3,4]]):
  try:rainflow(bad)
  except ValueError:pass
  else:raise AssertionError('INVALID_ACCEPTED')
 ck(abs(both_del([0,1,0])[0]-(1/600)**.25)<1e-12,'DEL')
 return '7 analytic checks and 3 invalid-signal rejections PASS'
def run(src,out):
 rows=[];sources=[];ck(selftest().startswith('7'),'SELFTEST')
 for batch,idxs in BATCHES.items():
  p=Path(src)/f'S06_{CASE}_{batch}_original.zip';raw=p.read_bytes()
  ck(sha(raw)==ZIP_SHA[batch],'ZIP_SHA_MISMATCH_'+batch)
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   ck(z.testzip() is None,'ZIP_CRC');names=[n for n in z.namelist() if n.endswith('_31seg.csv.gz')]
   ck(len(names)==1,'GZIP_MEMBER');gz=z.read(names[0]);data=gzip.decompress(gz)
  df=pd.read_csv(io.BytesIO(data));ck(len(df)==len(idxs)*12001,'ROW_COUNT')
  ck(set(df.case)=={CASE} and set(df.batch)=={batch},'CASE_BATCH')
  ck(set(df.segment)=={f'CSEG_{k:02d}' for k in idxs},'SEGMENTS')
  sources.append({'batch':batch,'zip_sha256':sha(raw),'gzip_sha256':sha(gz),'csv_sha256':sha(data),'rows':len(df)})
  for k in idxs:
   p=df[df.segment==f'CSEG_{k:02d}'];ck(len(p)==12001,'SAMPLES')
   t=p.time_s.to_numpy(float);ck(np.max(np.abs(t-(100+np.arange(12001)*.05)))<1e-7,'CLOCK')
   a,i,r=GEOS[k-1];fz=p.Fz_kN.to_numpy(float);mx=p.Mx_kNm.to_numpy(float);my=p.My_kNm.to_numpy(float)
   values=[]
   for j in range(64):
    deg=360*j/64
    v=both_del(stress(fz,mx,my,a,i,r,deg));values.append((deg,*v))
   d={'case':CASE,'segment':f'CSEG_{k:02d}','gage_z_m':round(float(p.gage_z_m.iloc[0]),9)}
   for m,col in ((4,1),(10,2)):
    for n in (16,32,64):
     best=max(values[::64//n],key=lambda v:v[col]);d[f'DEL_m{m}_N{n}_MPa']=round(best[col],9);d[f'theta_m{m}_N{n}_deg']=best[0]
    d[f'gap_m{m}_N16_to_N64_pct']=round(100*(d[f'DEL_m{m}_N64_MPa']-d[f'DEL_m{m}_N16_MPa'])/d[f'DEL_m{m}_N64_MPa'],9)
    d[f'gap_m{m}_N32_to_N64_pct']=round(100*(d[f'DEL_m{m}_N64_MPa']-d[f'DEL_m{m}_N32_MPa'])/d[f'DEL_m{m}_N64_MPa'],9)
   rows.append(d)
 ck(len(rows)==31,'OUTPUT_ROWS');rows.sort(key=lambda d:d['segment']);out=Path(out)
 with out.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 return {'source':sources,'case':CASE,'output_sha256':sha(out.read_bytes()),'rows':31,
  'm4_max_grid_gap_16_to_64_pct':max(x['gap_m4_N16_to_N64_pct'] for x in rows),
  'm4_max_grid_gap_32_to_64_pct':max(x['gap_m4_N32_to_N64_pct'] for x in rows),
  'm10_max_grid_gap_16_to_64_pct':max(x['gap_m10_N16_to_N64_pct'] for x in rows),
  'm10_max_grid_gap_32_to_64_pct':max(x['gap_m10_N32_to_N64_pct'] for x in rows),
  'worst_m4':max(rows,key=lambda d:d['gap_m4_N16_to_N64_pct']),
  'largest_m4_64':max(rows,key=lambda d:d['DEL_m4_N64_MPa']),
  'selftest':selftest(),'status':'PARTIAL_SCREEN_ONLY_NO_MATERIAL_PASS'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source-dir');p.add_argument('--output');p.add_argument('--selftest',action='store_true');a=p.parse_args()
 if a.selftest:print(selftest())
 else:print(json.dumps(run(a.source_dir,a.output),ensure_ascii=False,indent=2))
