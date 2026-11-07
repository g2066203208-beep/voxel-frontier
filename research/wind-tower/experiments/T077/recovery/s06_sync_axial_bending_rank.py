#!/usr/bin/env python3
"""Historical 158 m ETM batch-A, synchronized Fz/My gross-section DEL4.
Non-CAE, no solver, no local-material Miner. Run with two SHA-locked original ZIPs.
python s06_sync_axial_bending_rank.py --u09 U09_A_original.zip --u11 U11_A_original.zip --out result.csv
"""
import argparse,csv,gzip,hashlib,io,math,zipfile
from pathlib import Path

SOURCES={
 'U09p343881_ETM_S06':('ebccacd12a6f5fb3e6098c5130a7ca355409c4f7d5be4169ab23e4b265cd477f','3280b3a8332719b163f776efa61999588717ba5c1d71394b32f002e3c9b93e56','cc65fc05f07d2068e56fc5589cb158ce51ea885f4bf2122ea8ac4672c6d1886e'),
 'U11p4_ETM_S04':('c66a8a22693af0ed5c9cb8f68f51c48a24c046ba4e60cacdb1115040dd0007a9','1931fd91b7e7fc1304f928c404def83e7e7106f3359357642882b8101b55291d','3b6d048afdb86f955b413015e51a8b44fa662627f5cdb7eb92038b7c7fd30245')}
# OpenFAST gross A/I rounded to 6 decimals, first 9 rows of 31-row source.
# Full source SHA256 8ae262435e13c0f10326acef7270b9962c943bb5f212171d830fe834f3a364ed
GEOM=[(7.010775,55.735042),(6.870036,52.448000),(6.729294,49.292833),(6.621272,46.543725),(6.567417,44.234386),(6.550177,42.029640),(6.561645,40.162865),(6.549198,38.321199),(6.495870,36.202293)]
FIELDS=['segment','z_m','theta_deg','U09_bending_DEL4_MPa','U09_joint_DEL4_MPa','U11_bending_DEL4_MPa','U11_joint_DEL4_MPa','U09_axial_effect_pct','U11_axial_effect_pct','bending_winner','joint_winner','bending_signed_gap_U09_minus_U11_MPa','joint_signed_gap_U09_minus_U11_MPa','gap_change_MPa','scope']
sha=lambda b:hashlib.sha256(b).hexdigest()
def demand(ok,msg):
 if not ok:raise ValueError(msg)
def rainflow(xs):
 demand(len(xs)>=3 and all(math.isfinite(x) for x in xs),'INVALID_STRESS')
 y=[xs[0]]
 for x in xs[1:]:
  if x!=y[-1]:y.append(x)
 if len(y)==1:return []
 rev=[y[0]]
 for i in range(1,len(y)-1):
  if (y[i]-y[i-1])*(y[i+1]-y[i])<0:rev.append(y[i])
 rev.append(y[-1]); stack=[]; out=[]
 for x in rev:
  stack.append(x)
  while len(stack)>=3:
   a,b,c=stack[-3:]
   if abs(b-a)>abs(c-b):break
   if b!=a:out.append((abs(b-a),.5 if len(stack)==3 else 1.))
   if len(stack)==3:stack.pop(0)
   else:stack[-3:-1]=[]
 for a,b in zip(stack,stack[1:]):
  if b!=a:out.append((abs(b-a),.5))
 return out
def del4(xs):
 return (math.fsum(n*r**4 for r,n in rainflow(xs))/600)**.25
def read_source(path,case):
 b=Path(path).read_bytes();expected=SOURCES[case];demand(sha(b)==expected[0],'ZIP_SHA')
 with zipfile.ZipFile(io.BytesIO(b)) as z:
  demand(z.testzip() is None,'ZIP_CRC')
  names=[n for n in z.namelist() if n.endswith('_31seg.csv.gz')]
  demand(len(names)==1,'ZIP_MEMBER');g=z.read(names[0])
 demand(sha(g)==expected[1],'GZIP_SHA');raw=gzip.decompress(g)
 demand(sha(raw)==expected[2],'CSV_SHA')
 out={i:[] for i in range(1,10)};count=0
 for row in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
  count+=1; s=int(row['segment'].split('_')[-1]);demand(1<=s<=9,'SEGMENT')
  demand(row['case']==case and row['batch']=='A' and int(row['gage_index'])==s,'IDENTITY')
  t=float(row['time_s']);fz=float(row['Fz_kN']);my=float(row['My_kNm']);z=float(row['gage_z_m'])
  demand(all(map(math.isfinite,(t,fz,my,z))),'NONFINITE')
  k=len(out[s]);demand(k<12001 and abs(t-(100+.05*k))<1e-7,'TIME_GRID')
  out[s].append((t,fz,my,z))
 demand(count==108009 and all(len(x)==12001 for x in out.values()),'ROW_COUNT')
 return out
def compute(a,b):
 result=[];worst=0.
 for i,(area,I) in enumerate(GEOM,1):
  demand(area>0 and I>0,'GEOMETRY');R=math.sqrt(2*I/area+area/(2*math.pi))
  aa=a[i];bb=b[i];demand(len(aa)==len(bb)==12001,'PAIR_COUNT')
  demand(max(abs(x[0]-y[0]) for x,y in zip(aa,bb))<1e-8,'PAIR_TIME')
  for theta in (0,180):
   pair=[]
   for rows in (aa,bb):
    sign=1 if theta==0 else -1
    axial=[.001*r[1]/area for r in rows]
    bend=[sign*(-.001*r[2]*R/I) for r in rows]
    d0=del4(bend);d1=del4([x+y for x,y in zip(axial,bend)])
    demand(d0>0 and d1>0,'ZERO_DEL');pair.append((d0,d1))
    worst=max(worst,abs(100*(d1/d0-1)))
   (b0,j0),(b1,j1)=pair
   result.append(dict(zip(FIELDS,[f'CSEG_{i:02d}',f'{aa[0][3]:.9f}',theta,f'{b0:.9f}',f'{j0:.9f}',f'{b1:.9f}',f'{j1:.9f}',f'{100*(j0/b0-1):.7f}',f'{100*(j1/b1-1):.7f}','U09' if b0>b1 else 'U11','U09' if j0>j1 else 'U11',f'{b0-b1:.9f}',f'{j0-j1:.9f}',f'{(j0-j1)-(b0-b1):.9f}','HISTORICAL_ETM_GROSS_NOMINAL_NOT_LOCAL_MATERIAL'])))
 return result,worst
def selftest():
 demand(abs(del4([0,4,1,3,0])-(272/600)**.25)<1e-12,'KNOWN_CYCLE')
 demand(abs(del4([x+3 for x in [0,4,1,3,0]])-del4([0,4,1,3,0]))<1e-12,'OFFSET_INVARIANT')
 for bad in ([1,2],[1,math.nan,2]):
  try:rainflow(bad)
  except ValueError:pass
  else:raise AssertionError('INVALID_ACCEPTED')
 for bad in [(0,1),(-1,1)]:
  try:demand(bad[0]>0 and bad[1]>0,'GEOMETRY')
  except ValueError:pass
  else:raise AssertionError('BAD_GEOMETRY_ACCEPTED')
 return '2 analytic positives, 4 negative refusals'
def main():
 p=argparse.ArgumentParser();p.add_argument('--u09',required=True);p.add_argument('--u11',required=True);p.add_argument('--out',required=True);x=p.parse_args()
 print('SELFTEST',selftest());a=read_source(x.u09,'U09p343881_ETM_S06');b=read_source(x.u11,'U11p4_ETM_S04')
 rows,worst=compute(a,b)
 demand(len(rows)==18,'RESULT_COUNT');demand(all(r['bending_winner']==r['joint_winner'] for r in rows),'RANK_CHANGED')
 # Historical independent m4 nominal-stress oracle, CSEG04 and CSEG06 at 0 degrees.
 r4=next(r for r in rows if r['segment']=='CSEG_04' and r['theta_deg']==0)
 r6=next(r for r in rows if r['segment']=='CSEG_06' and r['theta_deg']==0)
 demand(abs(float(r4['U11_joint_DEL4_MPa'])-7.16908904914)<2e-5,'ORACLE_U11_CSEG04')
 demand(abs(float(r6['U09_joint_DEL4_MPa'])-7.09146818687)<2e-5,'ORACLE_U09_CSEG06')
 with open(x.out,'w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator='\n');w.writeheader();w.writerows(rows)
 print('ROWS',len(rows),'MAX_ABS_AXIAL_EFFECT_PCT',worst,'OUTPUT_SHA256',sha(Path(x.out).read_bytes()))
 for r in rows:
  if r['segment'] in ('CSEG_05','CSEG_06') and r['theta_deg']==0:print('CONTROL_TRANSITION',r)
if __name__=='__main__':main()
