#!/usr/bin/env python3
"""Source-locked ESM horizontal orientation/energy screening, not design-wave or Abaqus PASS.

For simultaneous horizontal acceleration E,N, form Q=integral([E,N]^T[E,N])dt.
The eigenvectors of Q define energy-principal azimuths. The Euclidean PGA
is an orientation-independent *upper envelope*, not a single-axis response.
"""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

EXPECTED_SHA256 = 'a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34'
DT = 0.005
N = 32040
G = 9.80665
COLUMNS = ('time_s', 'HNE_acc_m_s2', 'HNN_acc_m_s2', 'HNZ_acc_m_s2')

def integrate(values, dt):
    return math.fsum((values[i-1] + values[i])*dt/2 for i in range(1, len(values)))

def quantile_time(q, t, frac):
    target = frac*q[-1]
    for i in range(1, len(q)):
        if q[i] >= target:
            d = q[i] - q[i-1]
            return t[i-1] if d == 0 else t[i-1]+(t[i]-t[i-1])*(target-q[i-1])/d
    raise ValueError('INVALID_ENERGY_QUANTILE')

def analyze(t, e, n):
    if len(t)<2 or len(t)!=len(e) or len(t)!=len(n):
        raise ValueError('SYNCHRONY')
    if not all(math.isfinite(v) for v in (*t,*e,*n)):
        raise ValueError('NONFINITE')
    dt = t[1]-t[0]
    if dt<=0 or any(abs(t[i]-(t[0]+i*dt))>1e-9 for i in range(len(t))):
        raise ValueError('TIME_GRID')
    ee=integrate([v*v for v in e],dt)
    nn=integrate([v*v for v in n],dt)
    en=integrate([x*y for x,y in zip(e,n)],dt)
    disc=math.hypot(ee-nn,2*en)
    lp=(ee+nn+disc)/2
    lm=(ee+nn-disc)/2
    if lm<=0:raise ValueError('DEGENERATE_HORIZONTAL_ENERGY')
    theta=(math.degrees(math.atan2(2*en,ee-nn))/2)%180
    q=[x*x+y*y for x,y in zip(e,n)]
    cumulative=[0.0]
    for i in range(1,len(q)):
        cumulative.append(cumulative[-1]+(q[i-1]+q[i])*dt/2)
    idx=max(range(len(q)),key=q.__getitem__)
    if not math.isclose(cumulative[-1],ee+nn,rel_tol=2e-12,abs_tol=1e-13):
        raise ValueError('ENERGY_TRACE_IDENTITY')
    return {
        'npts':len(t),'dt_s':dt,'horizontal_vector_pga_m_s2':math.sqrt(q[idx]),
        'horizontal_vector_pga_time_s':t[idx],
        'horizontal_arias_sum_m_s':math.pi*(ee+nn)/(2*G),
        'horizontal_husid_d5_95_s':quantile_time(cumulative,t,.95)-quantile_time(cumulative,t,.05),
        'energy_q_ee_m2_s3':ee,'energy_q_nn_m2_s3':nn,'energy_q_en_m2_s3':en,
        'energy_principal_azimuth_deg_from_HNE_mod180':theta,
        'energy_eigenvalue_major_m2_s3':lp,'energy_eigenvalue_minor_m2_s3':lm,
        'energy_major_minor_ratio':lp/lm,
        'design_wave_pass':False,'instrument_low_frequency_pass':False,'abaqus_e_we_run':0,
    }

def self_test():
    t=[0.,.5,1.,1.5,2.]
    e=[2.,2.,2.,2.,2.]
    n=[1.,-1.,1.,-1.,1.]
    x=analyze(t,e,n)
    assert math.isclose(x['energy_q_ee_m2_s3'],8.)
    assert math.isclose(x['energy_q_nn_m2_s3'],2.)
    assert math.isclose(x['energy_q_en_m2_s3'],0.,abs_tol=1e-12)
    assert math.isclose(x['energy_major_minor_ratio'],4.)
    assert math.isclose(x['horizontal_vector_pga_m_s2'],math.sqrt(5))
    assert math.isclose(x['horizontal_husid_d5_95_s'],1.8)
    # 90-degree orthogonal rotation preserves trace, eigenvalues, vector PGA, Husid.
    y=analyze(t,[-v for v in n],e)
    for k in ('horizontal_vector_pga_m_s2','horizontal_arias_sum_m_s',
              'horizontal_husid_d5_95_s','energy_eigenvalue_major_m2_s3',
              'energy_eigenvalue_minor_m2_s3'):
        assert math.isclose(x[k],y[k],rel_tol=1e-12,abs_tol=1e-12),k
    for args,code in [((t,e,[float('nan')]*5),'NONFINITE'),
                      ((t,e,n[:-1]),'SYNCHRONY'),
                      (([0,.5,1,1.4,2],e,n),'TIME_GRID'),
                      ((t,e,[2]*5),'DEGENERATE_HORIZONTAL_ENERGY')]:
        try:analyze(*args)
        except ValueError as exc:assert str(exc)==code,(str(exc),code)
        else:raise AssertionError('invalid input accepted: '+code)
    print('S08_ORIENTATION_SYNTHETIC_11_ASSERTIONS_4_NEGATIVE_PASS')

def run(path):
    raw=Path(path).read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    if sha!=EXPECTED_SHA256:raise ValueError('SOURCE_SHA_MISMATCH')
    rows=list(csv.DictReader(raw.decode('utf-8').splitlines()))
    if len(rows)!=N:raise ValueError('COUNT')
    if tuple(rows[0])!=COLUMNS:raise ValueError('COLUMNS')
    t=[];e=[];n=[]
    for i,row in enumerate(rows):
        vals=[float(row[k]) for k in COLUMNS]
        if not all(math.isfinite(v) for v in vals):raise ValueError('NONFINITE')
        if abs(vals[0]-i*DT)>1e-9:raise ValueError('TIME_GRID')
        t.append(vals[0]);e.append(vals[1]);n.append(vals[2])
    result=analyze(t,e,n)
    result['source_csv_sha256']=sha
    result['source']='ESM_v3_IT-2012-0008_IT.NVL_MP_HNE_HNN'
    result['interpretation']='orientation_invariant_energy_screen_NOT_structure_response'
    return result

if __name__=='__main__':
    self_test()
    if len(sys.argv)!=2:raise SystemExit('usage: script.py 3COMP_SI_CSV')
    print(json.dumps(run(sys.argv[1]),sort_keys=True,indent=2))
