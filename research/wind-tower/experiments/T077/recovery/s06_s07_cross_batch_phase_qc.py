#!/usr/bin/env python3
"""S06/S07 16-archive six-component phase fingerprint, NOT synchronized load proof.

Read historical T071/T072 CSV.gz, not native OUTB. A/B/C/D are separate
OpenFAST runs; high first-difference correlation cannot license splicing,
frame rotation, external wind loads or fatigue/earthquake conclusions.
"""
import argparse,csv,gzip,hashlib,io,math,zipfile
from pathlib import Path
import numpy as np

CASES=('U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06')
COMP=('Fx_kN','Fy_kN','Fz_kN','Mx_kNm','My_kNm','Mz_kNm')
MANIFEST_SHA='dfc07558eb87002c3f54bb88671644519b77dfc38daf3971026f43686d4c2ed8'
N=12001

def check(x,msg):
 if not x:raise ValueError(msg)
def sha(x):return hashlib.sha256(x).hexdigest()
def manifest(path):
 raw=Path(path).read_bytes();check(sha(raw)==MANIFEST_SHA,'MANIFEST_SHA')
 r=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
 check(len(r)==16 and {(v['case'],v['batch']) for v in r}=={(c,b) for c in CASES for b in 'ABCD'},'MANIFEST_16')
 return {(v['case'],v['batch']):v for v in r}
def read_zip(path,case,batch,rec):
 raw=Path(path).read_bytes();check(sha(raw)==rec['zip_sha256'],'ZIP_SHA')
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  names=[n for n in z.namelist() if n.endswith('.csv.gz')];check(len(names)==1,'ZIP_MEMBERS')
  gz=z.read(names[0]);check(sha(gz)==rec['gzip_sha256'],'GZIP_SHA')
 plain=gzip.decompress(gz);check(sha(plain)==rec['uncompressed_csv_sha256'],'CSV_SHA')
 rd=csv.DictReader(io.StringIO(plain.decode('utf-8')))
 check(set(COMP+('case','batch','segment','time_s'))<=set(rd.fieldnames or []),'HEADER')
 d={};count=0
 for r in rd:
  count+=1;check(r['case']==case and r['batch']==batch,'CASE_BATCH')
  s=int(r['segment'].split('_')[1]);check(r['segment']==f'CSEG_{s:02d}' and 'ABCD'[(s-1)//9]==batch,'SEGMENT')
  a=d.setdefault(s,[]);check(len(a)<N and abs(float(r['time_s'])-(100+len(a)*.05))<2e-8,'CLOCK')
  v=[float(r[k]) for k in COMP];check(all(map(math.isfinite,v)),'NONFINITE');a.append(v)
 check(count==int(rec['rows']) and len(d)==(4 if batch=='D' else 9) and all(len(v)==N for v in d.values()),'COUNT')
 return {s:np.asarray(v,dtype=np.float64) for s,v in d.items()}
def corr(a,b,lag=0):
 a=np.diff(a);b=np.diff(b)
 if lag>0:a,b=a[lag:],b[:-lag]
 if lag<0:a,b=a[:lag],b[-lag:]
 a=a-a.mean();b=b-b.mean();den=np.linalg.norm(a)*np.linalg.norm(b)
 check(den>1e-20,'ZERO_VARIANCE');return float(np.dot(a,b)/den)
def selftest():
 t=np.arange(2000,dtype=float);x=np.sin(t*.013)+.1*np.sin(t*.31)
 check(abs(corr(x,x)-1)<1e-12 and corr(x,-x)<-.999999999999,'CORRELATION')
 check(corr(x,np.r_[x[2:],0,0],2)>.999999,'LAG_SIGN')
 rejected=0
 for f in (lambda:corr(np.ones(20),np.ones(20)),lambda:check(False,'BAD')):
  try:f()
  except ValueError:rejected+=1
  else:raise AssertionError('BAD_ACCEPTED')
 check(rejected==2,'NEGATIVE_TEST');return (3,rejected)
def run(src,man,out):
 m=manifest(man);rows=[];all_r=[];zero=0
 for case in CASES:
  d={}
  for b in 'ABCD':
   v=read_zip(Path(src)/f'S06_{case}_{b}_original.zip',case,b,m[case,b]);check(not(set(d)&set(v)),'DUPLICATE');d.update(v)
  check(set(d)==set(range(1,32)),'31_GAGES')
  for j in (9,18,27):
   rr=[];diffs=[];lags=[]
   for k in range(6):
    def r(i,lag=0):return corr(d[i][:,k],d[i+1][:,k],lag)
    r0=r(j);rr.append(r0);all_r.append(r0)
    diffs.append(r0-min(r(j-1),r(j+1)))
    lags.append(max(range(-3,4),key=lambda lag:r(j,lag)))
   is_zero=int(all(x==0 for x in lags));zero+=6*is_zero
   rows.append([case,f'J{j:02d}',*(f'{v:.12f}' for v in rr),is_zero,f'{min(diffs):.12f}'])
 check(len(rows)==12,'ROWS')
 p=Path(out);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['case','boundary',*('r_diff_'+k for k in COMP),'best_lag_zero_6of6','min_delta_vs_within_neighbor']);w.writerows(rows)
 print({'rows':len(rows),'component_correlations':len(all_r),'min_r':min(all_r),'median_r':float(np.median(all_r)),'best_lag_zero':zero,'csv_sha256':sha(p.read_bytes()),'selftest':selftest(),'physics_pass':False})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source-dir');p.add_argument('--manifest');p.add_argument('--output');p.add_argument('--selftest',action='store_true');a=p.parse_args()
 print('SELFTEST',selftest())
 if not a.selftest:
  check(bool(a.source_dir and a.manifest and a.output),'ARGS');run(a.source_dir,a.manifest,a.output)
