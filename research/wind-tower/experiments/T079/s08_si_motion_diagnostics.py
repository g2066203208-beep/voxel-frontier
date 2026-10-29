#!/usr/bin/env python3
"""S08 real processed-wave numerical diagnostics; NOT a site/structural PASS.
Input: locked ESM v3 IT-2012-0008/NVL MP three-component SI CSV.
Trapezoidal integration; Arias intensity pi/(2g)*integral(a^2 dt), Husid 5-95%.
Raw integral drift is a numerical diagnostic, NOT measured ground displacement.
"""
import csv,hashlib,json,math,sys
from pathlib import Path
EXPECTED='a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34'
N=32040; DT=0.005; G=9.80665
KEYS=('HNE_acc_m_s2','HNN_acc_m_s2','HNZ_acc_m_s2')
def trap(y,dt):
    out=[0.0]
    for i in range(1,len(y)): out.append(out[-1]+(y[i-1]+y[i])*dt/2)
    return out
def quantile_time(c,t,q):
    target=q*c[-1]
    for i in range(1,len(c)):
        if c[i]>=target:
            d=c[i]-c[i-1]
            return t[i-1]+(t[i]-t[i-1])*(target-c[i-1])/d if d else t[i]
    return t[-1]
def metric(a,t):
    sq=trap([x*x for x in a],DT)
    ia=math.pi/(2*G)*sq[-1]
    t5=quantile_time(sq,t,.05);t95=quantile_time(sq,t,.95)
    v=trap(a,DT);d=trap(v,DT)
    mean=(v[-1]/(t[-1]-t[0]))
    va=trap([x-mean for x in a],DT);da=trap(va,DT)
    return dict(pga_m_s2=max(map(abs,a)),arias_intensity_m_s=ia,t5_s=t5,t95_s=t95,d595_s=t95-t5,
      raw_terminal_velocity_m_s=v[-1],raw_terminal_displacement_m=d[-1],
      mean_acceleration_m_s2=mean,mean_corrected_terminal_velocity_m_s=va[-1],
      mean_corrected_terminal_displacement_m=da[-1],
      raw_peak_abs_velocity_m_s=max(map(abs,v)),raw_peak_abs_displacement_m=max(map(abs,d)))
def run(p):
    raw=Path(p).read_bytes();h=hashlib.sha256(raw).hexdigest()
    if h!=EXPECTED:raise ValueError('SOURCE_SHA_MISMATCH')
    rows=list(csv.DictReader(raw.decode('utf-8').splitlines()))
    if len(rows)!=N:raise ValueError('COUNT')
    if set(rows[0])!={'time_s',*KEYS}:raise ValueError('CHANNELS')
    t=[];a={k:[] for k in KEYS}
    for i,row in enumerate(rows):
        ti=float(row['time_s'])
        if not math.isfinite(ti) or abs(ti-i*DT)>1e-9:raise ValueError('TIME_GRID')
        t.append(ti)
        for k in KEYS:
            v=float(row[k]);
            if not math.isfinite(v):raise ValueError('NONFINITE')
            a[k].append(v)
    return {'source_csv_sha256':h,'samples':N,'dt_s':DT,'g_m_s2':G,'algorithm':'trapezoid-square-arias-husid-mean-offset-diagnostic',
            'channels':{k:metric(a[k],t) for k in KEYS},'physical_pass':False,'target_spectrum_pass':False,'abaqus_run':0}
def self_test():
    assert trap([2,2,2],.5)==[0,1,2]
    assert abs(quantile_time([0,1,2],[0,1,2],.25)-.5)<1e-12
    x=metric([1.]*5,[i*.005 for i in range(5)])
    assert abs(x['raw_terminal_velocity_m_s']-.02)<1e-12
    assert abs(x['arias_intensity_m_s']-math.pi*.02/(2*G))<1e-12
    assert abs(x['mean_corrected_terminal_velocity_m_s'])<1e-12
    for bad in ('', 'bad'):
        try:float(bad)
        except ValueError:pass
        else:raise AssertionError('accepted malformed number')
    print('S08_DIAGNOSTICS_SYNTHETIC_PASS 4 positive assertions 2 malformed numeric rejections')
if __name__=='__main__':
    self_test()
    if len(sys.argv)!=2:raise SystemExit('usage: s08_si_motion_diagnostics.py SI_CSV')
    print(json.dumps(run(sys.argv[1]),indent=2,sort_keys=True))
