#!/usr/bin/env python3
"""18 archived OpenFAST W base REACTION histories: shared horizontal-origin certificate.
Usage: python s06_shared_origin_certificate.py ORIGINAL_ARTIFACT.zip OUTPUT_DIR
The shift is hypothetical; this is not an external wind force or W/E/WE result.
"""
import csv,gzip,hashlib,io,json,math,sys,zipfile
from pathlib import Path
G='S06_18NTM_W_BASE6_FULLRATE_216018ROW.csv.gz'
M='S06_18NTM_W_BASE6_COINCIDENT_ENVELOPES_18ROW.csv'
GS='45cc308625ead8411d1565adc66c99e7ee8d0a979e5c3c6c18f23e744ba74dd1'
MS='ec1d5153635547c0ea24dba6ac62f65325dc50716b61e4c5c767ba489ec7444c'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):
 with zipfile.ZipFile(p) as z:g=z.read(G);m=z.read(M)
 if sha(g)!=GS or sha(m)!=MS:raise ValueError('SOURCE_SHA_MISMATCH')
 metric=list(csv.DictReader(io.StringIO(m.decode())));cases={}
 with gzip.open(io.BytesIO(g),'rt',newline='') as f:
  rd=csv.DictReader(f)
  if rd.fieldnames!=['case','time_s','TwrBsFxt','TwrBsFyt','TwrBsFzt','TwrBsMxt','TwrBsMyt','TwrBsMzt']:raise ValueError('HEADER')
  for row in rd:
   v=[float(row[k]) for k in rd.fieldnames[1:]]
   if not all(map(math.isfinite,v)):raise ValueError('NONFINITE')
   cases.setdefault(row['case'],[]).append((v[0],v[3],v[4],v[5]))
 if len(cases)!=18 or len(metric)!=18 or set(cases)!={x['case'] for x in metric}:raise ValueError('CASES')
 for name,rows in cases.items():
  if len(rows)!=12001 or any(abs(t-100-0.05*i)>2e-8 for i,(t,*_) in enumerate(rows)):raise ValueError('TIME_GRID '+name)
 return cases,metric
def peak(rows,d):return max(math.hypot(x,y)+d*abs(f) for t,f,x,y in rows)
def shifted(rows,dx,dy):return max(math.hypot(x-dy*f,y+dx*f) for t,f,x,y in rows)
def cert(ref,rows,d):
 _,f0,x0,y0=ref;n0=math.hypot(x0,y0);root=float('inf');margin=float('inf');worst=0
 for t,f,x,y in rows:
  a=n0*n0-x*x-y*y
  if a<=0:raise ValueError('BAD_CHAMPION')
  b=2*math.hypot(f0*x0-f*x,f0*y0-f*y);c=abs(f0*f0-f*f)
  r=2*a/(b+math.sqrt(b*b+4*a*c)) if b+c else float('inf')
  root=min(root,r)
  gap=(a-b*d-c*d*d)/(n0+d*abs(f0)+math.hypot(x,y)+d*abs(f))
  if gap<margin:margin=gap;worst=t
 return root,margin,worst
def test():
 a=[(100,-10,3,4),(100.05,-2,-6,8)]
 assert peak(a,1)==15 and shifted(a,0,0)==10
 oracle=max(shifted(a,math.cos(2*math.pi*j/4096),math.sin(2*math.pi*j/4096)) for j in range(4096))
 assert 0<=peak(a,1)-oracle<1e-5
 assert cert((100,-10,20,0),[(100,-10,10,0)],0.1)[1]>0
 assert cert((100,-10,20,0),[(100,-10,10,0)],10)[1]<0
 try:cert((100,-10,5,0),[(100,-10,6,0)],0)
 except ValueError:pass
 else:raise AssertionError('BAD_CHAMPION_ACCEPTED')
def main(archive,out):
 test();cases,metric=load(archive)
 p={n:peak(r,0) for n,r in cases.items()};champ=max(p,key=p.get)
 ref=max(cases[champ],key=lambda r:math.hypot(r[2],r[3]));d=.77;rows=[]
 for n,r in cases.items():
  if n==champ:continue
  radius,margin,t=cert(ref,r,d)
  rows.append(dict(challenger=n,original_peak_kNm=f'{p[n]:.9f}',shared_sufficient_radius_m=f'{radius:.9f}',shared_cert_margin_at_0p77_kNm=f'{margin:.9f}',worst_challenger_time_s=f'{t:.2f}',independent_0p1_upper_kNm=f'{peak(r,.1):.9f}'))
 rows.sort(key=lambda r:float(r['shared_sufficient_radius_m']))
 def independent_gap(d):
  low=max(max(0,math.hypot(x,y)-d*abs(f)) for t,f,x,y in cases[champ])
  return low-max(peak(r,d) for n,r in cases.items() if n!=champ)
 lo,hi=0.,1.
 for _ in range(42):
  mid=(lo+hi)/2
  if independent_gap(mid)>0:lo=mid
  else:hi=mid
 em=max(float(x['xy_quantization_bound_kNm']) for x in metric)
 ef=max(float(x['xyz_quantization_bound_kN']) for x in metric)
 margin=min(float(r['shared_cert_margin_at_0p77_kNm']) for r in rows)
 if margin<=2*(em+d*ef):raise AssertionError('QUANTIZATION_HOLD')
 out.mkdir(parents=True,exist_ok=True)
 with (out/'S06_W_BASE_SHARED_ORIGIN_CERT_17ROW_20261112.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 receipt=dict(source_gzip_sha256=GS,source_metrics_sha256=MS,rows=216018,cases=18,champion=champ,champion_t0_s=ref[0],champion_original_peak_kNm=p[champ],runner_up=rows[0]['challenger'],shared_origin_sufficient_radius_m=float(rows[0]['shared_sufficient_radius_m']),independent_casewise_radius_m=lo,certified_radius_with_quantization_m=d,min_shared_margin_at_0p77_kNm=margin,max_Mxy_quant_error_kNm=em,max_Fz_quant_error_kN=ef,two_case_quant_error_at_0p77_kNm=2*(em+d*ef),source_type='OpenFAST base reaction, NOT external wind force',limits='Shared horizontal origin only; hypothetical d; no same-state WE, DLC1.2 or material fatigue')
 (out/'S06_W_BASE_SHARED_ORIGIN_CERT_RECEIPT_20261112.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt,indent=2));print('CSV_SHA256',sha((out/'S06_W_BASE_SHARED_ORIGIN_CERT_17ROW_20261112.csv').read_bytes()))
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('usage: script archive.zip output_dir')
 main(Path(sys.argv[1]),Path(sys.argv[2]))
