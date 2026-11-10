#!/usr/bin/env python3
"""S07 near-base TP/RP small-angle closure; SOURCE QC only, not an exact DCM.
Usage: python s07_tp_rp_closure_compact.py POSE9.zip OUT.csv
Requires numpy, pandas; never runs OpenFAST or a structural solver.
"""
import csv, gzip, hashlib, io, math, sys, zipfile
import numpy as np
import pandas as pd

MEMBER='S07_18NTM_W_POSE9_FULLRATE_216018ROW.csv.gz'
SHA='2e113c83990d81b064636dca05308fc72676cb329033b9d603c8807d5cf0ecea'
FIELDS='case wind_ms seed n span_m rms_dx_um rms_dy_um rms_ex_um rms_ey_um rel_ex_pct rel_ey_pct corr_x corr_y max_abs_ex_um max_abs_ey_um wrong_sign_x_rel_pct wrong_sign_y_rel_pct demeaned_rel_ex_pct demeaned_rel_ey_pct'.split()

def compute(g):
    a=lambda s:g[[f'TwHt{i}{s}' for i in range(1,10)]].to_numpy(dtype=float)
    z,x,y=a('TPzi'),a('TPxi'),a('TPyi')
    rx,ry=np.deg2rad(a('RPxi')),np.deg2rad(a('RPyi'))
    if not all(np.isfinite(q).all() for q in (z,x,y,rx,ry)):raise ValueError('nonfinite')
    dz=np.diff(z,axis=1)
    if np.any(dz<=0):raise ValueError('height order')
    dx,dy=x[:,-1]-x[:,0],y[:,-1]-y[:,0]
    px=(dz*(ry[:,:-1]+ry[:,1:])*0.5).sum(axis=1)
    py=-(dz*(rx[:,:-1]+rx[:,1:])*0.5).sum(axis=1)
    return dx,dy,px,py,dz

def rms(a):return float(np.sqrt(np.mean(np.square(a))))
def pct(a,b):return 100*rms(a)/rms(b)
def test():
    n=8;z=np.linspace(.1,2.8,9);rx=np.linspace(-.0004,.0002,n);ry=np.linspace(.0001,.0008,n)
    g=pd.DataFrame()
    for i,h in enumerate(z,1):
        for name,v in [('TPzi',h),('TPxi',.01+ry*h),('TPyi',-.02-rx*h),('RPxi',np.rad2deg(rx)),('RPyi',np.rad2deg(ry))]:g[f'TwHt{i}{name}']=np.broadcast_to(v,(n,))
    dx,dy,px,py,_=compute(g)
    assert max(abs(dx-px))<1e-12 and max(abs(dy-py))<1e-12
    assert pct(dx+px,dx)>199 and pct(dy+py,dy)>199
    for col,val in [('TwHt5TPzi',-10),('TwHt2RPyi',float('nan'))]:
        bad=g.copy();bad.loc[0,col]=val
        try:compute(bad)
        except ValueError:continue
        raise AssertionError('malformed input not rejected')

def main(zip_path,out_path):
    test()
    with zipfile.ZipFile(zip_path) as z:
        raw=z.read(MEMBER)
    if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('SOURCE SHA mismatch')
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:df=pd.read_csv(f)
    if len(df)!=216018 or df.case.nunique()!=18:raise ValueError('source size')
    rows=[]
    for case,g in df.groupby('case',sort=True):
        if len(g)!=12001 or abs(g.time_s.iloc[0]-100)>1e-6 or abs(g.time_s.iloc[-1]-700)>1e-6 or not np.allclose(np.diff(g.time_s),.05,rtol=0,atol=1e-7):raise ValueError('time grid')
        dx,dy,px,py,dz=compute(g);ex,ey=dx-px,dy-py
        demean=lambda v:v-v.mean()
        row=[case,float(case.split('_')[0][1:].replace('p','.')),case.rsplit('_',1)[-1],len(g),float(np.mean(dz.sum(axis=1))),rms(dx)*1e6,rms(dy)*1e6,rms(ex)*1e6,rms(ey)*1e6,pct(ex,dx),pct(ey,dy),float(np.corrcoef(dx,px)[0,1]),float(np.corrcoef(dy,py)[0,1]),float(np.max(abs(ex)))*1e6,float(np.max(abs(ey)))*1e6,pct(dx+px,dx),pct(dy+py,dy),pct(demean(ex),demean(dx)),pct(demean(ey),demean(dy))]
        if not all(math.isfinite(float(v)) for v in row[1:2]+row[3:]):raise ValueError('bad result')
        rows.append(row)
    with open(out_path,'w',newline='',encoding='utf8') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(FIELDS)
        for row in rows:w.writerow([f'{v:.9f}' if isinstance(v,float) else v for v in row])
    print('SOURCE_PASS',len(df),'rows',len(rows),'cases; TEST 2 analytic + 2 reject; SHA256',hashlib.sha256(open(out_path,'rb').read()).hexdigest())
if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('usage: script POSE9.zip OUT.csv')
    main(sys.argv[1],sys.argv[2])
