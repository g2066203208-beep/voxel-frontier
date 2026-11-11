#!/usr/bin/env python3
"""Independent 5%-damped horizontal RotD response spectra from verified ESM CSV.
Source-level numerical method only: NOT a design spectrum or structural validation.
Input columns: time_s,HNE_m_s2,HNN_m_s2 (no resampling or filtering).
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import numpy as np

def read_pair(path):
    raw=Path(path).read_bytes()
    rows=list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    if len(rows)<20: raise ValueError("TOO_FEW_SAMPLES")
    for key in ("time_s","HNE_m_s2","HNN_m_s2"):
        if key not in rows[0]: raise ValueError("MISSING_COLUMN_"+key)
    a=np.array([[float(row[k]) for k in ("time_s","HNE_m_s2","HNN_m_s2")] for row in rows])
    if not np.isfinite(a).all(): raise ValueError("NONFINITE")
    dt=np.diff(a[:,0])
    if np.min(dt)<=0 or np.max(np.abs(dt-np.median(dt)))>1e-6*np.median(dt):
        raise ValueError("NONUNIFORM_TIME_GRID")
    if abs(a[0,0])>1e-9: raise ValueError("TIME_MUST_START_ZERO")
    return a,np.median(dt),hashlib.sha256(raw).hexdigest()

def sdof_displacement(ground,dt,period,damping=.05):
    """Average-acceleration Newmark beta=1/4 gamma=1/2, m=1, u0=v0=0.
    Input (n,2), return relative displacement history (n,2)."""
    if period<=0 or dt<=0 or not (0<=damping<1): raise ValueError("INVALID_PARAMETERS")
    w=2*math.pi/period; k=w*w; c=2*damping*w
    beta=.25; gamma=.5
    u=np.zeros(2); v=np.zeros(2); acc=-ground[0].copy()
    out=np.zeros_like(ground)
    den=k+gamma*c/(beta*dt)+1/(beta*dt*dt)
    for i in range(1,len(ground)):
        up=u+dt*v+dt*dt*(.5-beta)*acc
        vp=v+dt*(1-gamma)*acc
        an=(-ground[i]-c*vp-k*up)/(1+gamma*dt*c+beta*dt*dt*k)
        u=up+beta*dt*dt*an
        v=vp+gamma*dt*an
        acc=an
        out[i]=u
    return out

def rotd(ground,dt,period,step_deg=1):
    if not (0<step_deg<=45 and 180%step_deg==0): raise ValueError("INVALID_ANGLE_STEP")
    u=sdof_displacement(ground,dt,period)
    angles=np.deg2rad(np.arange(0,180,step_deg))
    peaks=[]
    for angle in angles:
        c,s=np.cos(angle),np.sin(angle)
        # RotD: each azimuth paired with its orthogonal direction
        peaks.extend([np.max(np.abs(c*u[:,0]+s*u[:,1])),
                      np.max(np.abs(-s*u[:,0]+c*u[:,1]))])
    peaks=np.asarray(peaks)*(2*math.pi/period)**2
    return np.percentile(peaks,50),np.max(peaks),len(peaks)

def self_test():
    t=np.arange(0,20,.005)
    a=np.column_stack((np.sin(2*np.pi*t),np.zeros_like(t)))
    r50,r100,n=rotd(a,.005,1.0)
    if n!=360 or not (0<r50<=r100): raise AssertionError("ROTD_ORDER")
    if abs(r100-np.max(np.abs(sdof_displacement(a,.005,1.0)[:,0]))*(2*np.pi)**2)>1e-10:
        raise AssertionError("AXIS_ROTATION_INVARIANCE")
    b=np.column_stack((-a[:,1],a[:,0]))
    q=rotd(b,.005,1.0)
    if max(abs(r50-q[0]),abs(r100-q[1]))>1e-10: raise AssertionError("90_DEG_INVARIANCE")
    for bad in (0,-1):
        try: sdof_displacement(a,.005,bad)
        except ValueError: pass
        else: raise AssertionError("MISSING_REJECTION")
    print("PASS: RotD order, 90-degree invariance, uniaxial peak, invalid-period rejection")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path)
    ap.add_argument("--output",type=Path)
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--periods",default="4,5,6,7,8,9,10")
    args=ap.parse_args()
    if args.self_test: self_test()
    if args.input:
        if not args.output: ap.error("--output required")
        a,dt,source_sha=read_pair(args.input)
        periods=[float(s) for s in args.periods.split(",")]
        if any(not math.isfinite(T) or T<=0 or dt/T>.05 for T in periods):
            raise ValueError("INVALID_PERIOD_OR_INSUFFICIENT_RESOLUTION")
        rows=[]
        for T in periods:
            r50,r100,n=rotd(a[:,1:],dt,T)
            rows.append({"period_s":T,"RotD50_PSA_m_s2":r50,
                         "RotD100_PSA_m_s2":r100,"angle_samples":n})
        args.output.write_text(json.dumps({"input_sha256":source_sha,"dt_s":dt,
            "damping_ratio":.05,"method":"Newmark average acceleration; 1 degree RotD",
            "status":"SOURCE_NUMERICAL_DIAGNOSTIC_ONLY","spectra":rows},indent=2)+"\n")
        print("WROTE",args.output,"input_sha256",source_sha)

if __name__=="__main__": main()
