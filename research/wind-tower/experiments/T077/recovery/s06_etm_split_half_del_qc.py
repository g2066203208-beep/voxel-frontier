#!/usr/bin/env python3
"""Four ETM 31-gage source-only 300s/300s rainflow load-DEL variability.
Reuses original s06_31gage_rainflow_load_screen.py ASTM stack/half cycles.
Nref = duration * 1Hz. Boundary t=400s belongs to BOTH adjacent halves.
Historical exported CSV, NOT native OUTB, DLC1.2 or material fatigue.
"""
import argparse,csv,gzip,hashlib,io,math,statistics,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from s06_31gage_rainflow_load_screen import rainflow_ranges
CASES=('U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06')
CH=('Fx_kN','Fy_kN','Fz_kN','Mx_kNm','My_kNm','Mz_kNm')
def ck(x,msg):
 if not x:raise ValueError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def calc(x,m,nref):
 ck(len(x)>=2 and nref>0 and np.isfinite(x).all(),'INVALID_SIGNAL')
 cycles=rainflow_ranges(x)
 return (math.fsum(n*r**m for r,n in cycles)/nref)**(1/m)
def qc(x,m):
 ck(len(x)==12001,'SAMPLES')
 full=calc(x,m,600);a=calc(x[:6001],m,300);b=calc(x[6000:],m,300)
 split=((a**m+b**m)/2)**(1/m)
 return full,a,b,split,abs(split-full)/max(full,1e-12),abs(a-b)/max((a+b)/2,1e-12)
def selftest():
 ck(rainflow_ranges([0,1,0])==[(1,0.5),(1,0.5)],'ASTM_HALF')
 ck(rainflow_ranges([0,3,1,2,0])==[(1,1.),(3,0.5),(3,0.5)],'ASTM_FULL')
 ck(abs(calc(np.array([0.,1.,0.]),4,1)-1)<1e-12,'ORACLE')
 x=np.tile(np.array([0.,1.]),6001)[:12001];z=qc(x,4)
 ck(abs(z[0]-z[1])<1e-10 and abs(z[0]-z[2])<1e-10,'PERIODIC')
 rejected=0
 for f in (lambda:calc(np.array([0.,np.nan]),4,1),lambda:calc(np.array([1.]),4,1),lambda:calc(np.array([0.,1.]),4,0),lambda:qc(np.zeros(12000),4)):
  try:f()
  except ValueError:rejected+=1
  else:raise AssertionError('BAD_ACCEPTED')
 ck(rejected==4,'REJECTIONS');return {'positive':4,'negative_rejected':rejected}
def run(src,manifest,detail,summary):
 print('SELFTEST',selftest(),flush=True)
 records=[];entries=list(csv.DictReader(Path(manifest).open(encoding='utf-8-sig',newline='')))
 ck(len(entries)==16 and {(r['case'],r['batch']) for r in entries}=={(c,b) for c in CASES for b in 'ABCD'},'MANIFEST')
 for r in entries:
  case,batch=r['case'],r['batch'];p=Path(src)/f'S06_{case}_{batch}_original.zip'
  raw=p.read_bytes();ck(sha(raw)==r['zip_sha256'],'ZIP_SHA')
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   ck(z.testzip() is None,'ZIP_CRC');names=[n for n in z.namelist() if n.endswith('_31seg.csv.gz')]
   ck(len(names)==1,'GZIP_MEMBER');gz=z.read(names[0])
  ck(sha(gz)==r['gzip_sha256'],'GZIP_SHA');data=gzip.decompress(gz)
  ck(sha(data)==r['uncompressed_csv_sha256'],'CSV_SHA')
  df=pd.read_csv(io.BytesIO(data));ck(len(df)==int(r['rows']),'ROWS')
  ck({'case','batch','segment','time_s',*CH}<=set(df.columns),'HEADER')
  ck(set(df['case'])=={case} and set(df['batch'])=={batch},'IDENTITY')
  expect={f'CSEG_{i:02d}' for i in {'A':range(1,10),'B':range(10,19),'C':range(19,28),'D':range(28,32)}[batch]}
  ck(set(df['segment'])==expect,'SEGMENTS')
  for seg,part in df.groupby('segment',sort=True):
   t=part['time_s'].to_numpy(float)
   ck(len(t)==12001 and np.max(abs(t-(100+np.arange(12001)*.05)))<2e-8,'CLOCK')
   for ch in CH:
    x=part[ch].to_numpy(float)
    for m in (4,10):
     full,a,b,split,gap,imb=qc(x,m)
     records.append(dict(case=case,segment=seg,channel=ch,m=m,full_600s=full,first_300s=a,last_300s=b,split_power_average=split,boundary_gap_frac=gap,half_imbalance_frac=imb))
 ck(len(records)==1488,'CARDINALITY')
 records.sort(key=lambda r:(CASES.index(r['case']),int(r['segment'].split('_')[1]),CH.index(r['channel']),r['m']))
 with Path(detail).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');w.writeheader();w.writerows([{k:(f'{v:.10g}' if isinstance(v,float) else v) for k,v in r.items()} for r in records])
 rows=[]
 for case in CASES:
  for ch in CH:
   for m in (4,10):
    g=[r for r in records if (r['case'],r['channel'],r['m'])==(case,ch,m)]
    w=max(g,key=lambda r:r['half_imbalance_frac']);b=max(g,key=lambda r:r['boundary_gap_frac'])
    rows.append(dict(case=case,channel=ch,m=m,n_gages=31,median_half_imbalance_pct=100*statistics.median(r['half_imbalance_frac'] for r in g),max_half_imbalance_pct=100*w['half_imbalance_frac'],worst_half_gage=w['segment'],median_boundary_gap_pct=100*statistics.median(r['boundary_gap_frac'] for r in g),max_boundary_gap_pct=100*b['boundary_gap_frac'],worst_boundary_gage=b['segment']))
 with Path(summary).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows([{k:(f'{v:.6f}' if isinstance(v,float) else v) for k,v in r.items()} for r in rows])
 print('RESULT',{'detail_rows':len(records),'summary_rows':len(rows),'detail_sha256':sha(Path(detail).read_bytes()),'summary_sha256':sha(Path(summary).read_bytes()),'stage_pass':False},flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source-dir',type=Path);p.add_argument('--manifest',type=Path);p.add_argument('--detail',type=Path);p.add_argument('--summary',type=Path);p.add_argument('--selftest',action='store_true');a=p.parse_args()
 if a.selftest:print(selftest())
 else:
  ck(all((a.source_dir,a.manifest,a.detail,a.summary)),'ARGS');run(a.source_dir,a.manifest,a.detail,a.summary)
