#!/usr/bin/env python3
"""S08 independent 3-axis ground-acceleration oracle (not tower seismic response).

Exact state transition for an underdamped SDOF under piecewise-LINEAR ground
acceleration, independently compared with Newmark average-acceleration.
Relative displacement: u'' + 2*zeta*omega*u' + omega^2*u = -ag(t).
Initially u=v=0, q=-ag(0). Rotations, turbine orientation, site spectrum,
wave scaling, native Abaqus input semantics and structural safety remain HOLD.

Python >=3.10 standard library; --real-source requires exact archived ESM SI
CSV SHA. Outputs 18 numeric comparisons (3 channels x 6 periods), not a design
wave or an Abaqus model result. Values are sampled at input timestamps.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

REAL_SHA = 'a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34'
REAL_N = 32040
DT = 0.005
DAMPING = 0.05
PERIODS = (0.5, 1.0, 2.0, 4.0, 6.0, 10.0)
COMP = ('HNE_acc_m_s2', 'HNN_acc_m_s2', 'HNZ_acc_m_s2')
HEADER = ('time_s',) + COMP
OUT = ('component','period_s','npts','dt_s','zeta',
       'exact_peak_rel_displacement_m','newmark_peak_rel_displacement_m',
       'exact_psa_m_s2','newmark_psa_m_s2','newmark_vs_exact_relative_error',
       'max_abs_sampled_displacement_difference_m','exact_peak_abs_acceleration_m_s2',
       'input_sha256','status')

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def read_source(raw, strict=True):
    if strict and digest(raw)!=REAL_SHA:
        raise ValueError('REAL_SOURCE_SHA256_MISMATCH')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if tuple(reader.fieldnames or ()) != HEADER:
        raise ValueError('SOURCE_HEADER_OR_DUPLICATES')
    result=[[],[],[]]
    n=0
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValueError('CSV_WIDTH')
        values=[float(row[c]) for c in HEADER]
        if not all(math.isfinite(v) for v in values):
            raise ValueError('NONFINITE')
        if abs(values[0]-n*DT)>2e-10:
            raise ValueError('TIME_GRID')
        for j in range(3):result[j].append(values[j+1])
        n+=1
    if n<3 or (strict and n!=REAL_N):
        raise ValueError('NPTS')
    return result

def _check(acc,dt,T,zeta):
    if (len(acc)<2 or not all(math.isfinite(v) for v in (dt,T,zeta))
        or dt<=0 or T<=0 or not 0<=zeta<1 or not all(math.isfinite(v) for v in acc)):
        raise ValueError('OSCILLATOR_INPUT')

def exact_piecewise_linear(acc,dt,T,zeta=DAMPING):
    """Exact endpoint state for linearly interpolated ag on each interval.

    For ag=a0+s*tau: up=A+B*tau, B=-s/k, A=(-a0-c*B)/k;
    homogeneous state is propagated with exp(A_sys*dt). No Newmark calls.
    """
    _check(acc,dt,T,zeta)
    w=2*math.pi/T;k=w*w;c=2*zeta*w
    wd=w*math.sqrt(1-zeta*zeta); decay=math.exp(-zeta*w*dt)
    co=math.cos(wd*dt); si=math.sin(wd*dt)
    m11=decay*(co+zeta*w*si/wd);m12=decay*si/wd
    m21=-decay*k*si/wd;m22=decay*(co-zeta*w*si/wd)
    u=v=0.0; peak=0.0; peak_abs_acc=0.0
    history=[0.0]
    for a0,a1 in zip(acc,acc[1:]):
        slope=(a1-a0)/dt
        B=-slope/k
        A=(-a0-c*B)/k
        hu=u-A;hv=v-B
        u=m11*hu+m12*hv+A+B*dt
        v=m21*hu+m22*hv+B
        peak=max(peak,abs(u))
        peak_abs_acc=max(peak_abs_acc,abs(-c*v-k*u))
        history.append(u)
    return {'sd_m':peak,'psa_m_s2':k*peak,'peak_absolute_acc_m_s2':peak_abs_acc,'history':history}

def newmark_average(acc,dt,T,zeta=DAMPING):
    _check(acc,dt,T,zeta)
    w=2*math.pi/T;k=w*w;c=2*zeta*w
    u=v=0.0;q=-acc[0]
    den=1+.5*c*dt+.25*k*dt*dt
    peak=0.0;history=[0.0]
    for ag in acc[1:]:
        up=u+dt*v+.25*dt*dt*q
        vp=v+.5*dt*q
        nq=(-ag-c*vp-k*up)/den
        u=up+.25*dt*dt*nq
        v=vp+.5*dt*nq;q=nq
        peak=max(peak,abs(u));history.append(u)
    return {'sd_m':peak,'psa_m_s2':k*peak,'history':history}

def evaluate(raw):
    traces=read_source(raw,strict=True)
    results=[]
    for channel,trace in zip(COMP,traces):
        for T in PERIODS:
            exact=exact_piecewise_linear(trace,DT,T)
            nm=newmark_average(trace,DT,T)
            ref=exact['psa_m_s2']
            err=abs(nm['psa_m_s2']-ref)/ref
            point_err=max(abs(a-b) for a,b in zip(exact['history'],nm['history']))
            if not (math.isfinite(err) and err<0.02):
                raise ValueError('NEWMARK_EXACT_DISAGREEMENT')
            results.append(dict(component=channel,period_s=T,npts=len(trace),dt_s=DT,zeta=DAMPING,
                exact_peak_rel_displacement_m=exact['sd_m'],newmark_peak_rel_displacement_m=nm['sd_m'],
                exact_psa_m_s2=ref,newmark_psa_m_s2=nm['psa_m_s2'],
                newmark_vs_exact_relative_error=err,
                max_abs_sampled_displacement_difference_m=point_err,
                exact_peak_abs_acceleration_m_s2=exact['peak_absolute_acc_m_s2'],
                input_sha256=digest(raw),
                status='S08_REAL_WAVE_SDOF_NUMERIC_ORACLE_PASS_NO_NATIVE_OR_SITE_PASS'))
    return results

def render(rows):
    buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=OUT,lineterminator='\n')
    w.writeheader();w.writerows(rows)
    return buf.getvalue().encode('utf-8')

def self_test():
    dt=.0025;T=1.25;z=.05; ag=1.5
    n=1001;trace=[ag]*n;t=(n-1)*dt
    w=2*math.pi/T;wd=w*math.sqrt(1-z*z)
    analytic=-ag/w**2*(1-math.exp(-z*w*t)*(math.cos(wd*t)+z*w/wd*math.sin(wd*t)))
    exact=exact_piecewise_linear(trace,dt,T,z)
    assert abs(exact['history'][-1]-analytic)<3e-12,('CONSTANT_FORCING_ANALYTIC',exact['history'][-1],analytic)
    def run(step):
        tt=[i*step for i in range(round(2.0/step)+1)]
        aa=[math.sin(2*math.pi*x/0.73)+.2*math.cos(2*math.pi*x/1.35) for x in tt]
        ex=exact_piecewise_linear(aa,step,T,z)
        nm=newmark_average(aa,step,T,z)
        return abs(ex['history'][-1]-nm['history'][-1])
    e1,e2=run(.02),run(.01)
    assert e2>0 and 3.6<e1/e2<4.4,('SECOND_ORDER_NEWMARK',e1,e2)
    sine=[math.sin(2*math.pi*i*.005/.9) for i in range(1001)]
    ex=exact_piecewise_linear(sine,.005,1.1)
    neg=exact_piecewise_linear([-x for x in sine],.005,1.1)
    scale=exact_piecewise_linear([1000*x for x in sine],.005,1.1)
    assert max(abs(a+b) for a,b in zip(ex['history'],neg['history']))<1e-13
    assert abs(scale['psa_m_s2']/ex['psa_m_s2']-1000)<1e-9
    assert exact_piecewise_linear([0.0]*100,.01,1)['sd_m']==0
    zero=('time_s,'+','.join(COMP)+'\n'+''.join(f'{i*DT:.3f},0,0,0\n' for i in range(3))).encode()
    read_source(zero,strict=False)
    for corrupted,expected in [
        (zero.replace(b'0.010',b'0.011'),'TIME_GRID'),
        (zero.replace(b'0,0,0',b'0,nan,0',1),'NONFINITE'),
        (zero.replace(b'time_s',b'bad_time'),'SOURCE_HEADER_OR_DUPLICATES'),
    ]:
        try:read_source(corrupted,strict=False)
        except ValueError as err:assert str(err)==expected,(str(err),expected)
        else:raise AssertionError('INVALID_CSV_ACCEPTED '+expected)
    for a,d,T0,z0 in [([1],.01,1.,.05),([0,0],0,1.,.05),([0,0],.01,0,.05),
                      ([0,0],.01,1.,1),([0,float('nan')],.01,1.,.05)]:
        try:exact_piecewise_linear(a,d,T0,z0)
        except ValueError as err:assert str(err)=='OSCILLATOR_INPUT'
        else:raise AssertionError('INVALID_OSCILLATOR_ACCEPTED')
    print('S08_EXACT_PIECEWISE_LINEAR_ANALYTIC_PASS',repr(analytic))
    print('S08_NEWMARK_SECOND_ORDER_CONVERGENCE_PASS',repr(e1/e2))
    print('S08_SIGN_UNIT_SCALING_ZERO_AND_8_NEGATIVE_TESTS_PASS')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--real-source',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--receipt',type=Path)
    a=p.parse_args()
    if a.self_test:self_test()
    if a.real_source or a.output or a.receipt:
        if not (a.real_source and a.output and a.receipt):
            p.error('--real-source --output --receipt required together')
        if len({x.resolve() for x in (a.real_source,a.output,a.receipt)})!=3:
            raise ValueError('INPUT_OUTPUT_OVERLAP')
        raw=a.real_source.read_bytes();res=evaluate(raw)
        csv_bytes=render(res)
        a.output.write_bytes(csv_bytes)
        receipt={'status':'INDEPENDENT_SDOF_PIECEWISE_LINEAR_REAL_ESM_QC_ONLY',
            'source_sha256':digest(raw),'source_npts':REAL_N,'dt_s':DT,'damping_ratio':DAMPING,
            'components':list(COMP),'periods_s':list(PERIODS),'comparison_rows':len(res),
            'reference_method':'exact underdamped SDOF state transition for piecewise-linear sampled ag',
            'compared_method':'Newmark average-acceleration beta=1/4 gamma=1/2',
            'relative_error_threshold_diagnostic':0.02,
            'maximum_relative_psa_discrepancy':max(r['newmark_vs_exact_relative_error'] for r in res),
            'output_csv_sha256':digest(csv_bytes),'output_csv_bytes':len(csv_bytes),
            'source_original_zip_sha256':'dec0f0bf59bea4e6a5049c824b6656c7e7798eb5379beba5162aff7304b113c6',
            'SOURCE':'ESM v3 DOI 10.13127/esm.3 IT-2012-0008/NVL/MP processed accelerogram; numerical SI CSV',
            'REF':'exact linear ODE solution derived explicitly in script; Newmark beta=1/4 gamma=1/2',
            'STANDARD':'NO_AUTHORIZED_SITE_OR_IEC_GB_CLAUSE_CLAIM',
            'OFFICIAL':'ESM public processed record; low-frequency instrument chain NOT VERIFIED',
            'RUN':'Python stdlib only; no structural solver','FIG':'NONE','TAB':'18-row SDOF comparison CSV',
            'assumptions':['5% illustrative oscillator damping, NOT tower damping',
                 'zero initial relative displacement and velocity',
                 'piecewise-linear interpolated ground acceleration between measured samples',
                 'no wave scaling or seismic target spectrum match'],
            'error_budget':'numerical integrator discrepancy reported per record/period; input, site, material and structural errors NOT BOUNDED',
            'S08_native_structural_RUN':0,'S05_site_design_PASS':False,'S08_physics_PASS':False}
        a.receipt.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        print('S08_REAL_ESM_INDEPENDENT_SDOF_18_ROWS_PASS_NOT_TOWER_OR_SITE',len(res),receipt['maximum_relative_psa_discrepancy'],receipt['output_csv_sha256'])
    if not a.self_test and not a.real_source:p.error('specify --self-test and/or --real-source')

if __name__=='__main__':main()
