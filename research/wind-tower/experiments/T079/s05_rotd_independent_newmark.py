#!/usr/bin/env python3
"""Independent 5%-damped horizontal RotD response spectra from verified ESM CSV.
Source-level numerical method only: NOT a design spectrum or structural validation.
Input columns: time_s,HNE_acc_m_s2,HNN_acc_m_s2 (S08 canonical) or\ntime_s,HNE_m_s2,HNN_m_s2 (legacy). SI m/s², no resampling/filtering.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import numpy as np

COLUMNS = (("HNE_acc_m_s2","HNN_acc_m_s2"),("HNE_m_s2","HNN_m_s2"))

def read_pair(path):
    raw=Path(path).read_bytes()
    reader=csv.DictReader(raw.decode("utf-8-sig").splitlines())
    headers=reader.fieldnames or []
    matches=[pair for pair in COLUMNS if all(k in headers for k in pair)]
    if "time_s" not in headers or len(matches)!=1:
        raise ValueError("MISSING_OR_AMBIGUOUS_SI_COLUMNS")
    rows=list(reader)
    if len(rows)<20: raise ValueError("TOO_FEW_SAMPLES")
    keys=("time_s",)+matches[0]
    try:
        a=np.array([[float(row[k]) for k in keys] for row in rows],dtype=float)
    except (TypeError,ValueError) as exc:
        raise ValueError("INVALID_NUMERIC_CELL") from exc
    if not np.isfinite(a).all(): raise ValueError("NONFINITE")
    dt=np.diff(a[:,0])
    step=float(np.median(dt))
    if step<=0 or np.max(np.abs(dt-step))>1e-6*step:
        raise ValueError("NONUNIFORM_TIME_GRID")
    if abs(a[0,0])>1e-9: raise ValueError("TIME_MUST_START_ZERO")
    return a,step,hashlib.sha256(raw).hexdigest()

def sdof_displacement(ground,dt,period,damping=.05):
    """Average-acceleration Newmark beta=1/4 gamma=1/2; zero initial u,v.
    Input is SI ground acceleration (n,2); output relative displacement (n,2).
    """
    ground=np.asarray(ground,dtype=float)
    if ground.ndim!=2 or ground.shape[1]!=2 or len(ground)<2 or not np.isfinite(ground).all():
        raise ValueError("INVALID_GROUND_ARRAY")
    if not all(math.isfinite(x) for x in (dt,period,damping)) or period<=0 or dt<=0 or not 0<=damping<1:
        raise ValueError("INVALID_PARAMETERS")
    w=2*math.pi/period; k=w*w; c=2*damping*w
    beta=.25; gamma=.5
    u=np.zeros(2); v=np.zeros(2); acc=-ground[0].copy()
    out=np.zeros_like(ground)
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
    """Boore (2010) nongeometric RotD50 and exact continuous-angle RotD100.
    GMRotD50 (geometric mean of orthogonal spectra) is a DIFFERENT quantity.
    """
    if not math.isfinite(step_deg) or not 0<step_deg<=45 or abs(180/step_deg-round(180/step_deg))>1e-9:
        raise ValueError("INVALID_ANGLE_STEP")
    u=sdof_displacement(ground,dt,period)
    angles=np.deg2rad(np.arange(round(180/step_deg))*step_deg)
    # A single component at each angle in [0,180) suffices.
    peaks=[np.max(np.abs(u[:,0]*np.cos(a)+u[:,1]*np.sin(a))) for a in angles]
    psa=(2*math.pi/period)**2
    # max_theta max_t |u_E*cos(theta)+u_N*sin(theta)| = max_t hypot(u_E,u_N).
    exact_100=np.max(np.linalg.norm(u,axis=1))*psa
    return float(np.median(peaks)*psa),float(exact_100),len(peaks)

def self_test():
    t=np.arange(0,20,.005)
    a=np.column_stack((np.sin(2*np.pi*t),np.zeros_like(t)))
    r50,r100,n=rotd(a,.005,1.0)
    assert n==180 and 0<r50<=r100
    assert abs(r100-np.max(np.abs(sdof_displacement(a,.005,1.0)[:,0]))*(2*np.pi)**2)<1e-10
    b=np.column_stack((-a[:,1],a[:,0]))
    q=rotd(b,.005,1.0)
    assert max(abs(r50-q[0]),abs(r100-q[1]))<1e-10
    for bad in (0,-1,float("nan")):
        try: sdof_displacement(a,.005,bad)
        except ValueError: pass
        else: raise AssertionError("MISSING_PERIOD_REJECTION")
    for bad in (0,7,float("nan")):
        try: rotd(a,.005,1.0,bad)
        except ValueError: pass
        else: raise AssertionError("MISSING_ANGLE_REJECTION")
    rng=np.random.default_rng(20261111)
    for count in (50,500,5000):
        history=rng.normal(size=(count,2))
        exact=np.max(np.linalg.norm(history,axis=1))
        theta=np.deg2rad(np.arange(180))
        grid=max(np.max(np.abs(history[:,0]*np.cos(v)+history[:,1]*np.sin(v))) for v in theta)
        assert grid<=exact*(1+1e-12)
        assert grid>=exact*math.cos(math.pi/360)-1e-12
    const=np.column_stack((np.full(20001,.3),np.zeros(20001)))
    disp=sdof_displacement(const,.005,1.0)
    assert abs(disp[-1,0]+.3/(2*math.pi)**2)<5e-6
    assert np.max(np.abs(disp[:,1]))==0
    print("PASS: RotD order, 90deg invariance, continuous-angle identity, angle bound, static equilibrium, 6 parameter rejections")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path)
    ap.add_argument("--output",type=Path)
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--periods",default="4,5,6,7,8,9,10")
    ap.add_argument("--expected-sha256")
    args=ap.parse_args()
    if args.self_test: self_test()
    if args.input:
        if not args.output: ap.error("--output required")
        a,dt,source_sha=read_pair(args.input)
        if args.expected_sha256 and source_sha.lower()!=args.expected_sha256.lower():
            raise ValueError("SOURCE_SHA256_MISMATCH")
        periods=[float(s) for s in args.periods.split(",")]
        if not periods or any(not math.isfinite(T) or T<=0 or dt/T>.05 for T in periods):
            raise ValueError("INVALID_PERIOD_OR_INSUFFICIENT_RESOLUTION")
        rows=[]
        for T in periods:
            r50,r100,n=rotd(a[:,1:],dt,T)
            rows.append({"period_s":T,"RotD50_PSA_m_s2":r50,
                         "RotD100_PSA_m_s2":r100,"angle_samples":n})
        args.output.write_text(json.dumps({"input_sha256":source_sha,"dt_s":dt,
            "damping_ratio":.05,"method":"Newmark beta=1/4; Boore2010 nongeometric RotD50; exact continuous-angle RotD100",
            "status":"SOURCE_NUMERICAL_DIAGNOSTIC_ONLY","spectra":rows},indent=2)+"\n")
        print("WROTE",args.output,"input_sha256",source_sha)

if __name__=="__main__": main()
