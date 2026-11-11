#!/usr/bin/env python3
"""Real ESM NVL MP two-horizontal RotD100 sensitivity to EXTRA high-pass filters.
Not unprocessed ground motion, site target spectrum, or tower seismic response.
"""
import argparse,csv,hashlib
from pathlib import Path
import numpy as np
from scipy.signal import butter,sosfiltfilt
SOURCE_SHA='a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34'
REFERENCE_SHA='ea642b37ca39bde6c1e5b48168e50650adadb00311ca9f24a11102fea82d407c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(source,reference):
    if sha(source)!=SOURCE_SHA:raise ValueError('SOURCE_SHA_MISMATCH')
    if sha(reference)!=REFERENCE_SHA:raise ValueError('REFERENCE_SHA_MISMATCH')
    with source.open(newline='') as f:
        a=np.array([[float(r[k]) for k in ('time_s','HNE_acc_m_s2','HNN_acc_m_s2')] for r in csv.DictReader(f)])
    with reference.open(newline='') as f:
        rows=list(csv.DictReader(f))
    if a.shape!=(32040,3) or not np.isfinite(a).all() or not np.allclose(np.diff(a[:,0]),.005,atol=1e-11,rtol=0):
        raise ValueError('INVALID_TIME_GRID')
    t=np.array([float(r['period_s']) for r in rows]); b=np.array([float(r['RotD100_continuous_PSA_m_s2']) for r in rows]);
    if len(t)!=46 or not np.all(np.diff(t)>0):raise ValueError('INVALID_REFERENCE_PERIODS')
    return a[:,1:],t,b
def rotd100(acc,periods,dt=.005):
    w=2*np.pi/periods;k=w*w;c=.1*w
    q0=4/dt**2;q1=2/dt;q2=4/dt
    keff=k+q0+c*q1
    u=np.zeros((len(w),2));v=np.zeros_like(u);a=np.zeros_like(u);m=np.zeros(len(w))
    for ag in acc:
        rhs=-ag[None,:]+q0*u+q2*v+a+c[:,None]*(q1*u+v)
        un=rhs/keff[:,None]
        an=q0*(un-u)-q2*v-a
        v+=dt*(a+an)/2;u=un;a=an
        m=np.maximum(m,np.hypot(u[:,0],u[:,1]))
    return k*m
def run(source,reference,output):
    acc,t,b=load(source,reference);base=rotd100(acc,t)
    if np.max(np.abs(base-b))>5e-10:raise AssertionError('HISTORICAL_46_PERIOD_MISMATCH')
    series=[base]
    for fc in (.06,.08):
        sos=butter(4,fc,btype='highpass',fs=200,output='sos')
        series.append(rotd100(sosfiltfilt(sos,acc,axis=0),t))
    with output.open('w',newline='') as f:
        wr=csv.writer(f);wr.writerow(['period_s','MP_0p04_RotD100_m_s2','extra_HP0p06_RotD100_m_s2','extra_HP0p08_RotD100_m_s2','extra_HP0p06_delta_pct','extra_HP0p08_delta_pct'])
        for i,x in enumerate(t):
            a,b,c=(s[i] for s in series)
            wr.writerow([f'{x:.12f}',f'{a:.12g}',f'{b:.12g}',f'{c:.12g}',f'{100*(b/a-1):.8f}',f'{100*(c/a-1):.8f}'])
    print('PASS',len(t),'baseline_regression_max_abs',np.max(np.abs(base-load(source,reference)[2])),'csv_sha256',sha(output))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('reference',type=Path);p.add_argument('output',type=Path);x=p.parse_args();run(x.source,x.reference,x.output)
