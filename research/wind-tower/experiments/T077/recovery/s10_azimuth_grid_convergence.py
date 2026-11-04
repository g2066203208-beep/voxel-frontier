#!/usr/bin/env python3
"""S06/S10: source-locked four-ETM 31-section 16/32/64 azimuth nominal-stress DEL grid QC.

This is an exploratory, signed OpenFAST source-frame gross-annulus elastic-stress screen.
It is NOT synchronized 31-gage physical V&V, DLC1.2, PT equilibrium or material fatigue.
No native solver or costly production simulation is invoked.
"""
import argparse, csv, gzip, hashlib, io, json, math, zipfile
from collections import deque
from pathlib import Path
import numpy as np
import pandas as pd

MANIFEST_SHA='dfc07558eb87002c3f54bb88671644519b77dfc38daf3971026f43686d4c2ed8'
BATCHES={'A':range(1,10),'B':range(10,19),'C':range(19,28),'D':range(28,32)}
CASES=('U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06')
GEOM='''7.010775,55.735042,4.124999738
6.870036,52.448000,4.044999962
6.729294,49.292833,3.964999954
6.621272,46.543725,3.887499861
6.567417,44.234386,3.809999931
6.550177,42.029640,3.724999882
6.561645,40.162865,3.644999917
6.549198,38.321199,3.569999943
6.495870,36.202293,3.489999864
6.461661,34.245816,3.409999956
6.444538,32.426400,3.329999926
6.396595,30.525988,3.249999832
6.319863,28.575457,3.169999938
6.259540,26.765364,3.089999943
6.213594,25.075501,3.009999799
6.139536,23.354065,2.929999952
6.064917,22.050940,2.869999890
6.039394,21.624956,2.849999889
6.039394,21.624956,2.849999889
5.882629,21.137021,2.849999890
5.567214,20.143430,2.849999753
5.408563,19.637680,2.849999856
5.408563,19.637680,2.849999856
5.408563,19.637680,2.849999856
5.169410,18.867732,2.849999896
4.686863,17.286466,2.849999766
4.443468,16.474821,2.849999735
4.443468,16.474821,2.849999735
5.201379,18.971181,2.849999783
6.262271,21.208697,2.787499890
6.823917,19.448040,2.604999797'''
GEOS=[tuple(map(float,row.split(','))) for row in GEOM.splitlines()]
def sha(b): return hashlib.sha256(b).hexdigest()
def ck(x,msg):
    if not x: raise ValueError(msg)
def turns(x):
    x=np.asarray(x,dtype=float)
    ck(x.ndim==1 and len(x)>1 and np.isfinite(x).all(),'BAD_SIGNAL')
    y=x[np.r_[True,np.diff(x)!=0]]
    if len(y)==1: return y
    d=np.diff(y)
    return y[np.r_[True,d[:-1]*d[1:]<0,True]]
def rainflow(x):
    q=deque(); cycles=[]
    for v in turns(x):
        q.append(float(v))
        while len(q)>=3:
            a=abs(q[-2]-q[-3]);b=abs(q[-1]-q[-2])
            if a>b: break
            if len(q)==3:
                if a>0: cycles.append((a,.5))
                q.popleft()
            else:
                if a>0: cycles.append((a,1.))
                q[-3]=q[-1];q.pop();q.pop()
    while len(q)>1:
        r=abs(q[1]-q[0])
        if r>0: cycles.append((r,.5))
        q.popleft()
    return cycles
def both_del(x):
    cy=rainflow(x)
    return tuple((math.fsum(n*r**m for r,n in cy)/600)**(1/m) for m in (4,10))
def stress(fz,mx,my,a,i,r,deg):
    ck(a>0 and i>0 and r>0,'GEOMETRY')
    t=math.radians(deg)
    return .001*(fz/a+(mx*r*math.sin(t)-my*r*math.cos(t))/i)
def selftest():
    ck(len(GEOS)==31,'GEOM_ROWS')
    ck(rainflow([0,1,0])==[(1,.5),(1,.5)],'HALF')
    ck(rainflow([0,3,1,2,0])==[(1,1.),(3,.5),(3,.5)],'FULL')
    ck(abs(stress(-1000,0,0,2,5,3,0)+.5)<1e-12,'AXIAL')
    ck(abs(stress(0,0,1000,2,5,3,0)+.6)<1e-12,'MOMENT')
    ck(abs(stress(0,1000,0,2,5,3,90)-.6)<1e-12,'ROTATION')
    ck(abs(both_del([0,1,0])[0]-(1/600)**.25)<1e-12,'DEL')
    for bad in ([0,float('nan')],[1],[[1,2],[3,4]]):
        try: rainflow(bad)
        except ValueError: pass
        else: raise AssertionError('INVALID_ACCEPTED')
    return '7 analytic checks and 3 invalid-signal rejections PASS'
def manifest_load(path):
    raw=Path(path).read_bytes()
    ck(sha(raw)==MANIFEST_SHA,'MANIFEST_SHA_MISMATCH')
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
    ck(len(rows)==16 and len({(r['case'],r['batch']) for r in rows})==16,'MANIFEST_ROWS')
    return {(r['case'],r['batch']):r for r in rows}
def run(src,manifest,out,chosen='all'):
    ck(selftest().startswith('7'),'SELFTEST')
    cases=CASES if chosen=='all' else (chosen,)
    ck(all(c in CASES for c in cases),'UNKNOWN_CASE')
    m=manifest_load(manifest); rows=[];sources=[]
    for case in cases:
        for batch,idxs in BATCHES.items():
            meta=m[(case,batch)]
            path=Path(src)/f'S06_{case}_{batch}_original.zip'; raw=path.read_bytes()
            ck(sha(raw)==meta['zip_sha256'],f'ZIP_SHA_MISMATCH:{case}:{batch}')
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                ck(z.testzip() is None,'ZIP_CRC')
                names=[n for n in z.namelist() if n.endswith('_31seg.csv.gz')]
                ck(len(names)==1,'GZIP_MEMBER')
                gz=z.read(names[0]);data=gzip.decompress(gz)
            ck(sha(gz)==meta['gzip_sha256'],'GZIP_SHA_MISMATCH')
            ck(sha(data)==meta['uncompressed_csv_sha256'],'CSV_SHA_MISMATCH')
            df=pd.read_csv(io.BytesIO(data))
            ck(len(df)==int(meta['rows'])==len(idxs)*12001,'ROW_COUNT')
            ck(set(df.case)=={case} and set(df.batch)=={batch},'CASE_BATCH')
            ck(set(df.segment)=={f'CSEG_{k:02d}' for k in idxs},'SEGMENTS')
            sources.append({'case':case,'batch':batch,'zip_sha256':sha(raw),'gzip_sha256':sha(gz),'csv_sha256':sha(data),'rows':len(df)})
            for k in idxs:
                p=df[df.segment==f'CSEG_{k:02d}']
                ck(len(p)==12001,'SAMPLES')
                t=p.time_s.to_numpy(float)
                ck(np.max(np.abs(t-(100+np.arange(12001)*.05)))<1e-7,'CLOCK')
                a,i,r=GEOS[k-1]
                fz=p.Fz_kN.to_numpy(float);mx=p.Mx_kNm.to_numpy(float);my=p.My_kNm.to_numpy(float)
                values=[(360*j/64,*both_del(stress(fz,mx,my,a,i,r,360*j/64))) for j in range(64)]
                d={'case':case,'segment':f'CSEG_{k:02d}','gage_z_m':round(float(p.gage_z_m.iloc[0]),9)}
                for mm,col in ((4,1),(10,2)):
                    for n in (16,32,64):
                        best=max(values[::64//n],key=lambda v:v[col])
                        d[f'DEL_m{mm}_N{n}_MPa']=round(best[col],9)
                        d[f'theta_m{mm}_N{n}_deg']=best[0]
                    d[f'gap_m{mm}_N16_to_N64_pct']=round(100*(d[f'DEL_m{mm}_N64_MPa']-d[f'DEL_m{mm}_N16_MPa'])/d[f'DEL_m{mm}_N64_MPa'],9)
                    d[f'gap_m{mm}_N32_to_N64_pct']=round(100*(d[f'DEL_m{mm}_N64_MPa']-d[f'DEL_m{mm}_N32_MPa'])/d[f'DEL_m{mm}_N64_MPa'],9)
                rows.append(d)
        ck(len([r for r in rows if r['case']==case])==31,'CASE_ROWS')
    ck(len(rows)==31*len(cases),'OUTPUT_ROWS')
    rows.sort(key=lambda d:(d['case'],d['segment']))
    out=Path(out)
    with out.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    stats={}
    for case in cases:
        sub=[r for r in rows if r['case']==case]
        stats[case]={
            'max_m4_N16_to_N64_pct':max(r['gap_m4_N16_to_N64_pct'] for r in sub),
            'max_m10_N16_to_N64_pct':max(r['gap_m10_N16_to_N64_pct'] for r in sub),
            'max_m4_N32_to_N64_pct':max(r['gap_m4_N32_to_N64_pct'] for r in sub),
            'max_m10_N32_to_N64_pct':max(r['gap_m10_N32_to_N64_pct'] for r in sub),
            'worst_m4_segment':max(sub,key=lambda r:r['gap_m4_N16_to_N64_pct'])['segment'],
            'max_DEL_m4_N64_MPa':max(r['DEL_m4_N64_MPa'] for r in sub),
            'max_DEL_m4_segment':max(sub,key=lambda r:r['DEL_m4_N64_MPa'])['segment']}
    return {'case_stats':stats,'source':sources,'manifest_sha256':MANIFEST_SHA,'output_sha256':sha(out.read_bytes()),'rows':len(rows),'selftest':selftest(),'status':'PARTIAL_SCREEN_ONLY_NO_MATERIAL_PASS'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-dir');p.add_argument('--manifest');p.add_argument('--output');p.add_argument('--case',default='all');p.add_argument('--selftest',action='store_true');a=p.parse_args()
    if a.selftest:print(selftest())
    else:print(json.dumps(run(a.source_dir,a.manifest,a.output,a.case),ensure_ascii=False,indent=2))
