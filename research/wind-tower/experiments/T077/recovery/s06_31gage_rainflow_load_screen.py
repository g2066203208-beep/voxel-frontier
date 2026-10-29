#!/usr/bin/env python3
"""Source-level rainflow/load-DEL screening of the 4x31 recovered T071/T072 CSVs.

DOES NOT compute material fatigue damage, a validated DLC1.2 DEL, joint stresses,
Abaqus response, or a global-frame dynamic free-body residual.
Reference-cycle convention: Nref = duration_s * 1 Hz = 600 cycles.
Requires numpy and pandas. No proprietary solver.
"""
from __future__ import annotations
import argparse
import csv
from collections import deque
import gzip
import hashlib
import io
import math
import statistics
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd

CHANNELS=('Fx_kN','Fy_kN','Fz_kN','Mx_kNm','My_kNm','Mz_kNm')
CASES=('U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06')
FIELDS=('case','segment','gage_z_m','channel','units','n_samples','dt_s','duration_s',
        'mean','std','min','max','p2p','rms_first_300s','rms_last_300s',
        'rainflow_equivalent_cycles','rainflow_half_cycles','rainflow_full_cycles',
        'DEL_m4_Nref_1Hz','DEL_m10_Nref_1Hz')


def sha(b): return hashlib.sha256(b).hexdigest()


def reversals(signal):
    """Endpoints and strict turning points after consecutive plateau removal."""
    x=np.asarray(signal,dtype=float)
    if x.ndim!=1 or len(x)<2 or not np.isfinite(x).all():
        raise ValueError('nonfinite/short/invalid series')
    keep=np.r_[True,np.diff(x)!=0]
    y=x[keep]
    if len(y)==1:return y
    d=np.diff(y)
    turns=np.r_[True,d[:-1]*d[1:]<0,True]
    return y[turns]


def rainflow_ranges(signal):
    """ASTM E1049 four-point stack form: residual endpoints are half cycles.

    Return list of (range,count). No cycle closure or artificial endpoint joining.
    """
    q=deque()
    cycles=[]
    for value in reversals(signal):
        q.append(float(value))
        while len(q)>=3:
            previous=abs(q[-2]-q[-3]);next_range=abs(q[-1]-q[-2])
            if previous>next_range:break
            if len(q)==3:
                if previous>0:cycles.append((previous,0.5))
                q.popleft()
            else:
                if previous>0:cycles.append((previous,1.0))
                # Delete the two enclosed turning points, retain the later endpoint.
                q[-3]=q[-1];q.pop();q.pop()
    while len(q)>1:
        r=abs(q[1]-q[0])
        if r>0:cycles.append((r,0.5))
        q.popleft()
    return cycles


def metrics(values):
    x=np.asarray(values,dtype=float)
    if x.shape!=(12001,) or not np.isfinite(x).all():raise ValueError('invalid samples')
    cycles=rainflow_ranges(x)
    if abs(sum(n for _,n in cycles)-(len(reversals(x))-1)/2)>1e-8:
        raise AssertionError("rainflow cycle-conservation failed")
    nref=600.0 # (700-100)s * 1Hz; not number of sampled points
    d4=(sum(n*r**4 for r,n in cycles)/nref)**(1/4)
    d10=(sum(n*r**10 for r,n in cycles)/nref)**(1/10)
    # 6001 points from 100..400 inclusive; 6000 from 400.05..700.
    # split at t=400.00 without overlap: 6000/6001 points.
    rms1=float(np.sqrt(np.mean(x[:6000]**2)))
    rms2=float(np.sqrt(np.mean(x[6000:]**2)))
    return (float(x.mean()),float(x.std(ddof=0)),float(x.min()),float(x.max()),
            float(np.ptp(x)),rms1,rms2,float(sum(n for _,n in cycles)),
            sum(n==0.5 for _,n in cycles),sum(n==1.0 for _,n in cycles),d4,d10)


def self_test():
    # Analytic half-cycle and full-cycle oracles; non-closed sequences retained.
    assert rainflow_ranges([0,1,0])==[(1,0.5),(1,0.5)]
    assert rainflow_ranges([0,3,1,2,0])==[(1,1.0),(3,0.5),(3,0.5)]
    assert rainflow_ranges([2,2,2])==[]
    assert rainflow_ranges([0,1,1,0])==[(1,0.5),(1,0.5)]
    assert rainflow_ranges([0,2,0,2,0])==[(2,0.5)]*4
    assert abs(sum(n*r**4 for r,n in rainflow_ranges([0,1,0]))-1)<1e-12
    for bad in ([0,float('nan'),1],[1],[[0,1],[2,3]]):
        try:rainflow_ranges(bad)
        except ValueError:pass
        else:raise AssertionError('invalid signal accepted')
    assert metrics(np.zeros(12001))[-2:]==(0.,0.)
    print('SELF_TEST PASS: ASTM stack/half/full/plateau/nonfinite/zero/DEL oracle')


def run(zip_dir,manifest,output,summary_output=None):
    self_test()
    entries=list(csv.DictReader(open(manifest,encoding='utf-8-sig',newline='')))
    if len(entries)!=16 or {(r['case'],r['batch']) for r in entries}!={(c,b) for c in CASES for b in 'ABCD'}:
        raise ValueError('manifest identity mismatch')
    out=[]
    for ent in entries:
        case,batch=ent['case'],ent['batch']
        prefix='T071' if case.startswith('U09') else 'T072'
        path=zip_dir/f'{prefix}-{case}-{batch}.zip'
        raw_zip=path.read_bytes()
        if sha(raw_zip)!=ent['zip_sha256']:raise ValueError('ZIP SHA mismatch: '+path.name)
        with zipfile.ZipFile(io.BytesIO(raw_zip)) as z:
            if z.testzip():raise ValueError('ZIP CRC mismatch: '+path.name)
            names=[n for n in z.namelist() if n.endswith('_31seg.csv.gz')]
            if len(names)!=1:raise ValueError('missing/ambiguous gzip: '+path.name)
            gz=z.read(names[0])
        if sha(gz)!=ent['gzip_sha256']:raise ValueError('gzip SHA mismatch: '+path.name)
        raw=gzip.decompress(gz)
        if sha(raw)!=ent['uncompressed_csv_sha256']:raise ValueError('CSV SHA mismatch: '+path.name)
        df=pd.read_csv(io.BytesIO(raw))
        req={'case','batch','segment','gage_z_m','time_s',*CHANNELS}
        if not req.issubset(df.columns):raise ValueError('missing channels')
        if len(df)!=int(ent['rows']) or set(df['case'])!={case} or set(df['batch'])!={batch}:
            raise ValueError('identity/rows mismatch')
        expected={f'CSEG_{i:02d}' for i in {'A':range(1,10),'B':range(10,19),'C':range(19,28),'D':range(28,32)}[batch]}
        if set(df['segment'])!=expected:raise ValueError('segment mismatch')
        for seg,part in df.groupby('segment',sort=True):
            if len(part)!=12001:raise ValueError('sample count mismatch')
            t=part['time_s'].to_numpy(dtype=float)
            if np.max(np.abs(t-(100+np.arange(12001)*.05)))>1e-7:
                raise ValueError('time-grid mismatch')
            z=part['gage_z_m'].to_numpy(dtype=float)
            if not np.isfinite(z).all() or np.ptp(z)>1e-8:raise ValueError('gage height mismatch')
            for ch in CHANNELS:
                data=part[ch].to_numpy(dtype=float)
                values=metrics(data)
                units='kN' if ch.startswith('F') else 'kNm'
                out.append((case,seg,float(z[0]),ch,units,12001,0.05,600.0,*values))
        print('VERIFIED',case,batch,'rows',len(df),'zip_sha256',sha(raw_zip))
    if len(out)!=4*31*6 or len({(r[0],r[1],r[3]) for r in out})!=len(out):
        raise ValueError('result cardinality mismatch')
    out.sort(key=lambda r:(CASES.index(r[0]),int(r[1].split('_')[1]),CHANNELS.index(r[3])))
    with open(output,'w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f,lineterminator='\n');writer.writerow(FIELDS)
        for row in out:
            writer.writerow([f'{v:.9f}' if isinstance(v,float) else v for v in row])
    print('PASS',len(out),'gage-channel metrics; CSV_SHA256',sha(output.read_bytes()))
    if summary_output is not None:
        summary_fields=('case','channel','n_gages','max_DEL_m4','gage_at_max_m4',
                        'max_DEL_m10','gage_at_max_m10','median_DEL_m4','median_DEL_m10')
        with open(summary_output,'w',encoding='utf-8',newline='') as f:
            writer=csv.writer(f,lineterminator='\n');writer.writerow(summary_fields)
            for case in CASES:
                for ch in CHANNELS:
                    sub=[r for r in out if r[0]==case and r[3]==ch]
                    top4=max(sub,key=lambda r:r[-2]);top10=max(sub,key=lambda r:r[-1])
                    writer.writerow([case,ch,len(sub),f'{top4[-2]:.9f}',top4[1],
                                     f'{top10[-1]:.9f}',top10[1],
                                     f'{statistics.median(r[-2] for r in sub):.9f}',
                                     f'{statistics.median(r[-1] for r in sub):.9f}'])
        print('SUMMARY 24 rows; SHA256',sha(summary_output.read_bytes()))
    for case in CASES:
        for ch in ('My_kNm','Mx_kNm','Fz_kN'):
            sub=[r for r in out if r[0]==case and r[3]==ch]
            top=max(sub,key=lambda r:r[-2]);top10=max(sub,key=lambda r:r[-1])
            print('TOP',case,ch,'m4',top[1],f'{top[-2]:.6f}', 'm10',top10[1],f'{top10[-1]:.6f}')
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--zip-dir',type=Path)
    p.add_argument('--manifest',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--summary-output',type=Path)
    args=p.parse_args()
    if args.self_test:self_test()
    else:
        if not (args.zip_dir and args.manifest and args.output):p.error('zip-dir, manifest and output required')
        run(args.zip_dir,args.manifest,args.output,args.summary_output)
