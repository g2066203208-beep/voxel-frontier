#!/usr/bin/env python3
"""Independent source-locked 46-period ESM RotD angular-grid reconciliation.
Reads genuine processed MP SI acceleration; does not infer a design spectrum.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
from s05_rotd_independent_newmark import read_pair,sdof_displacement

SOURCE_SHA='a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34'
PERIODS=(1.246191552573,1.25,1.327181952929,1.413435946139,1.5,1.505295614839,1.603125273730,1.707312914444,1.818271744320,1.936441825175,2.,2.062291818592,2.196320844623,2.339060461298,2.491076772777,2.5,2.652972674518,2.825390244353,3.,3.009013288965,3.204570055858,3.412836121583,3.5,3.634637467666,3.870853756445,4.,4.122421819804,4.390339374641,4.675668979804,4.979542250191,5.,5.303164344725,5.647818746007,6.,6.014872350595,6.230957762865,6.405780890106,6.822094704635,7.,7.265464891391,7.737649852935,8.,8.240522270994,8.776076533496,9.,9.346436644298)

def angular_peaks(u,step):
    if step not in (.5,1.):raise ValueError('ANGLE_STEP_NOT_SUPPORTED')
    theta=np.deg2rad(np.arange(int(180/step))*step)
    direction=np.vstack((np.cos(theta),np.sin(theta)))
    peaks=np.zeros(len(theta))
    for i in range(0,len(u),2048):
        proj=u[i:i+2048]@direction
        peaks=np.maximum(peaks,np.max(np.abs(proj),axis=0))
    return float(np.median(peaks)),float(np.max(peaks))

def evaluate(acc,dt,period):
    u=sdof_displacement(acc,dt,period)
    p1,g1=angular_peaks(u,1.)
    p05,g05=angular_peaks(u,.5)
    factor=(2*math.pi/period)**2
    return [p1*factor,p05*factor,float(np.max(np.linalg.norm(u,axis=1))*factor),g05*factor]

def self_test():
    t=np.arange(0,8,.02)
    a=np.column_stack((np.sin(t),np.cos(t)))
    r=evaluate(a,.02,2.)
    rot=evaluate(np.column_stack((-a[:,1],a[:,0])),.02,2.)
    assert all(abs(x-y)<1e-10 for x,y in zip(r,rot))
    assert r[2]>=r[3]>=max(r[0],r[1])>0
    for bad in (0,.25,2):
        try:angular_peaks(a,bad)
        except ValueError:pass
        else:raise AssertionError('BAD_ANGLE_ACCEPTED')
    print('SELF_TEST_PASS_90DEG_EXACT_ROTD100_AND_THREE_ANGLE_REJECTIONS')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--summary',required=True,type=Path)
    p.add_argument('--reference',type=Path)
    p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if a.self_test:self_test()
    source,dt,sha=read_pair(a.input)
    if sha!=SOURCE_SHA or source.shape!=(32040,3) or abs(dt-.005)>1e-10:
        raise ValueError('OFFICIAL_SOURCE_SHA_OR_GRID_MISMATCH')
    acc=source[:,1:]
    rows=[]
    for T in PERIODS:
        p1,p05,p100,g100=evaluate(acc,dt,T)
        rows.append(dict(period_s=format(T,'.12f'),RotD50_1deg_PSA_m_s2=format(p1,'.12g'),
            RotD50_0p5deg_PSA_m_s2=format(p05,'.12g'),RotD100_continuous_PSA_m_s2=format(p100,'.12g'),
            RotD100_0p5deg_grid_PSA_m_s2=format(g100,'.12g')))
    with a.output.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    report={'source_sha256':sha,'source_samples':len(acc),'dt_s':dt,'damping_ratio':.05,
        'period_count':len(rows),'historical_reference_sha256':None,
        'status':'REAL_ESM_PROCESSED_SOURCE_NUMERICAL_QC_NOT_SITE_OR_STRUCTURAL_PASS'}
    if a.reference:
        raw=a.reference.read_bytes();report['historical_reference_sha256']=hashlib.sha256(raw).hexdigest()
        ref=list(csv.DictReader(raw.decode('utf8').splitlines()))
        if len(ref)!=len(rows):raise ValueError('REFERENCE_ROW_COUNT')
        d50=[];d100=[]
        for i,(x,y) in enumerate(zip(rows,ref)):
            if abs(float(x['period_s'])-float(y['period_s']))>1e-10:raise ValueError('REFERENCE_PERIOD_MISMATCH')
            d50.append(abs(float(x['RotD50_0p5deg_PSA_m_s2'])-float(y['RotD50_PSA_m_s2'])))
            d100.append(abs(float(x['RotD100_0p5deg_grid_PSA_m_s2'])-float(y['RotD100_PSA_m_s2'])))
        report.update(reference_max_abs_RotD50_m_s2=max(d50),reference_max_abs_RotD100_m_s2=max(d100))
    report['max_RotD50_1deg_vs_0p5deg_pct']=max(100*abs(float(r['RotD50_1deg_PSA_m_s2'])-float(r['RotD50_0p5deg_PSA_m_s2']))/float(r['RotD50_0p5deg_PSA_m_s2']) for r in rows)
    report['max_RotD100_exact_vs_grid_pct']=max(100*(float(r['RotD100_continuous_PSA_m_s2'])-float(r['RotD100_0p5deg_grid_PSA_m_s2']))/float(r['RotD100_continuous_PSA_m_s2']) for r in rows)
    a.summary.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report))

if __name__=='__main__':main()
