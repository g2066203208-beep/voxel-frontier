#!/usr/bin/env python3
"""Historical 158 m NTM tower-base REACTION FFT; NOT aerodynamic force, DLC1.2 or Miner.
Usage: python s06_ntm18_spectral_min.py source.csv.gz output_directory
Source: Actions artifact 13775054290, 18 original OUTB-derived 600 s histories.
"""
import csv,gzip,hashlib,sys
from collections import defaultdict
from pathlib import Path
import numpy as np
SHA='45cc308625ead8411d1565adc66c99e7ee8d0a979e5c3c6c18f23e744ba74dd1'
BINS=('U09p343881','U11p4','U19p202140')

def fft(x,lo=.05,detrend=False):
 x=np.asarray(x,dtype=float)
 if x.ndim!=1 or len(x)<200 or not np.isfinite(x).all():raise ValueError('bad series')
 if detrend:
  t=np.arange(len(x),dtype=float);t-=t.mean();x=x-x.mean()-t*np.dot(t,x)/np.dot(t,t)
 else:x=x-x.mean()
 n=len(x);f=np.fft.rfftfreq(n,.05);p=2*np.abs(np.fft.rfft(x))**2/n**2
 p[0]/=2
 if n%2==0:p[-1]/=2
 v=np.mean(x*x)
 if abs(p.sum()-v)>max(1e-8,v*1e-10):raise AssertionError('Parseval')
 q=p[(f>=lo)&(f<.25)].sum()
 return float(q/v),float(np.sqrt(q))

def welch(x):
 n=4096;w=np.hanning(n);a=[]
 for j in range(0,len(x)-n+1,2048):
  y=np.asarray(x[j:j+n]);y=y-y.mean();p=np.abs(np.fft.rfft(y*w))**2;p[1:-1]*=2;a.append(p)
 p=np.mean(a,axis=0);f=np.fft.rfftfreq(n,.05)
 return float(p[(f>=.05)&(f<.25)].sum()/p.sum())

def run(inp,out):
 b=Path(inp).read_bytes()
 if hashlib.sha256(b).hexdigest()!=SHA:raise ValueError('SOURCE SHA mismatch')
 cases=defaultdict(list)
 with gzip.open(inp,'rt',newline='') as f:
  rd=csv.DictReader(f)
  if rd.fieldnames!=['case','time_s','TwrBsFxt','TwrBsFyt','TwrBsFzt','TwrBsMxt','TwrBsMyt','TwrBsMzt']:raise ValueError('schema')
  for row in rd:
   case=row['case'];z=case.split('_NTM_S')
   if len(z)!=2 or z[0] not in BINS or z[1] not in ['%02d'%i for i in range(1,7)]:raise ValueError('case')
   v=[float(row[k]) for k in rd.fieldnames[1:]]
   if not np.isfinite(v).all():raise ValueError('nonfinite')
   cases[case].append(v)
 if len(cases)!=18 or any(len(v)!=12001 for v in cases.values()):raise ValueError('incomplete')
 rows=[]
 for case in sorted(cases):
  a=np.asarray(cases[case]);t=100+.05*np.arange(12001)
  if np.max(abs(a[:,0]-t))>1e-7:raise ValueError('time grid')
  for ch,j in [('TwrBsMxt',4),('TwrBsMyt',5)]:
   x=a[:12000,j];share,rms=fft(x)
   rows.append(dict(case=case,wind_bin=case.split('_NTM_S')[0],channel=ch,
    mean_kNm=float(x.mean()),share_005_025=share,band_rms_kNm=rms,
    welch_share=welch(x),detrend_share=fft(x,detrend=True)[0],
    cutoff004=fft(x,.04)[0],cutoff006=fft(x,.06)[0],cutoff008=fft(x,.08)[0],cutoff010=fft(x,.10)[0],
    half1=fft(x[:6000])[0],half2=fft(x[6000:])[0]))
 summary=[]
 for ch in ['TwrBsMxt','TwrBsMyt']:
  for group in BINS:
   z=[r for r in rows if r['channel']==ch and r['wind_bin']==group]
   q=[r['share_005_025'] for r in z]
   summary.append(dict(channel=ch,wind_bin=group,n=6,share_mean=np.mean(q),share_min=min(q),share_max=max(q),
    band_rms_mean_kNm=np.mean([r['band_rms_kNm'] for r in z]),reaction_mean_kNm=np.mean([r['mean_kNm'] for r in z])))
  hi=[r for r in rows if r['channel']==ch and r['wind_bin']==BINS[2]]
  mid=[r for r in rows if r['channel']==ch and r['wind_bin']==BINS[1]]
  for field in ['share_005_025','welch_share','detrend_share','cutoff004','cutoff006','cutoff008','cutoff010']:
   if min(r[field] for r in hi)<=max(r[field] for r in mid):raise AssertionError('nonseparation '+field)
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 for name,data in [('S06_NTM18_BASE_REACTION_SPECTRAL_36ROW_20261112.csv',rows),('S06_NTM18_BASE_REACTION_SPECTRAL_6ROW_20261112.csv',summary)]:
  with (out/name).open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader()
   w.writerows({k:('%.10f'%v if isinstance(v,(float,np.floating)) else v) for k,v in r.items()} for r in data)
 print('PASS 18 cases 36 channel histories 6 summary rows, Parseval, source SHA and seven strict-separation checks')
 return rows,summary

if __name__=='__main__':
 t=np.arange(12000)*.05
 assert abs(fft(3*np.cos(2*np.pi*.1*t)+4*np.sin(2*np.pi*.5*t))[0]-.36)<1e-10
 for bad in ([1,2,3],[float('nan')]*300):
  try:fft(bad)
  except ValueError:pass
  else:raise AssertionError('bad series accepted')
 if len(sys.argv)!=3:sys.exit('Usage: python script.py source.csv.gz output_directory')
 run(sys.argv[1],sys.argv[2])
