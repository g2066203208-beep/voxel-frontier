#!/usr/bin/env python3
"""Time-aligned 4-case x 31-segment annular no-tension-kern SCREEN (not contact)."""
import argparse,csv,gzip,hashlib,io,math,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
PE_KN=39753.559;P0_KN=51609.600
CASES=('U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06')
HEADER=['case','segment','gage_z_m','area_m2','I_m4','outer_radius_m','samples','dt_s','Pe_min_fullcontact_sigma_MPa','Pe_at_time_s','Pe_at_time_Next_kN','Pe_at_time_Mres_kNm','Pe_fraction_fullcontact_tension','Pe_peak_fullcontact_tension_MPa','P0_fraction_fullcontact_tension','P0_peak_fullcontact_tension_MPa','noPT_fraction_fullcontact_tension','noPT_peak_fullcontact_tension_MPa']
def sha(b):return hashlib.sha256(b).hexdigest()
def annulus(ri,ro):
 if not 0<ri<ro:raise ValueError('invalid annulus')
 return math.pi*(ro*ro-ri*ri),math.pi/4*(ro**4-ri**4)
def sigma(n,m,pt,a,I,ro):return ((n+pt)/a-m*ro/I)/1000.
def oracle():
 a,I=annulus(2.,3.);n=1000.;mk=n*I/(a*3)
 assert abs(sigma(n,mk,0,a,I,3))<1e-12
 assert sigma(n,0,0,a,I,3)>0 and sigma(0,mk,0,a,I,3)<0
 assert sigma(n,mk,P0_KN,a,I,3)>sigma(n,mk,PE_KN,a,I,3)
def run(zips,manifest,geometry,output):
 oracle();g={r['segment']:r for r in csv.DictReader(open(geometry,encoding='utf-8-sig',newline=''))}
 assert len(g)==31
 entries=list(csv.DictReader(open(manifest,encoding='utf-8-sig',newline='')))
 if len(entries)!=16 or {(r['case'],r['batch']) for r in entries}!={(c,b) for c in CASES for b in 'ABCD'}:raise ValueError('manifest 4x4 mismatch')
 result=[]
 for ent in entries:
  case,batch=ent['case'],ent['batch'];prefix='T071' if case.startswith('U09') else 'T072';path=Path(zips)/f'{prefix}-{case}-{batch}.zip'
  data=path.read_bytes()
  if sha(data)!=ent['zip_sha256']:raise ValueError('ZIP SHA mismatch '+path.name)
  with zipfile.ZipFile(io.BytesIO(data)) as z:
   if z.testzip() is not None:raise ValueError('ZIP CRC mismatch')
   names=[n for n in z.namelist() if n.endswith('_31seg.csv.gz')]
   if len(names)!=1:raise ValueError('ambiguous history')
   gz=z.read(names[0])
  if ent.get('gzip_sha256') and sha(gz)!=ent['gzip_sha256']:raise ValueError('gzip SHA mismatch')
  raw=gzip.decompress(gz)
  if ent.get('uncompressed_csv_sha256') and sha(raw)!=ent['uncompressed_csv_sha256']:raise ValueError('CSV SHA mismatch')
  df=pd.read_csv(io.BytesIO(raw))
  required={'case','batch','segment','gage_z_m','time_s','Fz_kN','Mx_kNm','My_kNm'}
  if not required.issubset(df.columns):raise ValueError('missing columns')
  if len(df)!=int(ent.get('rows',len(df))) or df['case'].nunique()!=1 or df['case'].iloc[0]!=case or df['batch'].nunique()!=1 or df['batch'].iloc[0]!=batch:raise ValueError('row/identity mismatch')
  expected={f'CSEG_{i:02d}' for i in {'A':range(1,10),'B':range(10,19),'C':range(19,28),'D':range(28,32)}[batch]}
  if set(df.segment)!=expected:raise ValueError('segment coverage mismatch')
  for seg,group in df.groupby('segment',sort=True):
   if len(group)!=12001:raise ValueError('time sample count')
   times=group.time_s.to_numpy(); z_m=group.gage_z_m.to_numpy()
   if not np.isfinite(group[['time_s','gage_z_m','Fz_kN','Mx_kNm','My_kNm']].to_numpy()).all():raise ValueError('nonfinite')
   if np.max(np.abs(times-(100+np.arange(12001)*0.05)))>1e-7 or np.ptp(z_m)>1e-8:raise ValueError('time/height discontinuity')
   h=float(z_m[0]);geo=g[seg];y0=float(geo['y0_m']);y1=float(geo['y1_m'])
   if not y0-0.05<=h<=y1+0.05:raise ValueError('gage outside segment')
   frac=(h-y0)/(y1-y0)
   ri=float(geo['ri0_m'])+frac*(float(geo['ri1_m'])-float(geo['ri0_m']))
   ro=float(geo['ro0_m'])+frac*(float(geo['ro1_m'])-float(geo['ro0_m']))
   area,I=annulus(ri,ro)
   n=-group.Fz_kN.to_numpy();m=np.hypot(group.Mx_kNm.to_numpy(),group.My_kNm.to_numpy())
   vals=[sigma(n,m,pt,area,I,ro) for pt in (PE_KN,P0_KN,0.)]
   idx=int(np.argmin(vals[0]));rec=[case,seg,f'{h:.9f}',f'{area:.9f}',f'{I:.9f}',f'{ro:.9f}',12001,'0.05',f'{vals[0][idx]:.9f}',f'{times[idx]:.2f}',f'{n[idx]:.6f}',f'{m[idx]:.6f}']
   for v in vals:rec.extend((f'{np.mean(v< -1e-10):.9f}',f'{max(0.,-np.min(v)):.9f}'))
   result.append(rec)
 if len(result)!=124:raise ValueError('expected 124 segments')
 result.sort(key=lambda r:(CASES.index(r[0]),int(r[1].split('_')[1])))
 with open(output,'w',encoding='utf-8',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(HEADER);w.writerows(result)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--zip-dir',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--geometry',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=run(a.zip_dir,a.manifest,a.geometry,a.output)
 for case in CASES:
  x=[r for r in rows if r[0]==case]
  print(case,'n=',len(x),'Pe_flagged=',sum(float(r[12])>0 for r in x),'P0_flagged=',sum(float(r[14])>0 for r in x),'max_Pe_proxy_tension_MPa=',max(float(r[13]) for r in x))
