#!/usr/bin/env python3
"""Source-locked real ETM 12001-step gross section-stress rainflow range/mean.
NOT local material fatigue, native PT, annual damage, or design-wave verification.
Reuses T077's unclosed ASTM-style reversal-stack convention.
"""
import argparse,csv,gzip,hashlib,io,json,math,zipfile
from pathlib import Path

SRC={
'U09p343881_ETM_S06':('T071-U09-S06-B.zip','B','5acbb25968ce43892157545cded26973623f22b5a137839e5154b293aef167db','73ac606f43a1bf777fa303ca781a76a643dbe79bda52f7177886f417d07c5e20','43d4b07d6dbe63de3d6b12b5fc3093ce91ba8e0510eccc29aba0087732dcc734'),
'U11p4_ETM_S04':('T072-U11-S04-A.zip','A','c66a8a22693af0ed5c9cb8f68f51c48a24c046ba4e60cacdb1115040dd0007a9','1931fd91b7e7fc1304f928c404def83e7e7106f3359357642882b8101b55291d','3b6d048afdb86f955b413015e51a8b44fa662627f5cdb7eb92038b7c7fd30245')}
# Case,segment,angle,area,I,radius,Pe/A,P0/A,prior DEL4,DEL10,cycles,half,full
# Geometry: T071_input_geometry_31_segments.csv SHA256 fff6dfcc6bc094353ebee042392033e8df47e7fb792ccc1812c0962c9c43f800.
# Oracles: 1984-row S10 gross SHA256 16c9864ef7a344e5b97338c31ce26de6adb86c0f0f64942ef894fe9983926b2b.
# PT: 124-row P0/Pe SHA256 1d56cdf44971589dde25ab8075cdf50999a94eac47707eadfb4870cf74fc8f5d.
CTRL=[
('U09p343881_ETM_S06','CSEG_16',180,6.139535901042011,23.35406476985036,5.859999914623364/2,6.47501042349,8.40610769802,7.05273183802,17.1088699574,407.5,11,402),
('U09p343881_ETM_S06','CSEG_17',180,6.064916979817216,22.050939787425683,5.739999762550344/2,6.55467487633,8.50953115628,7.03716180072,17.0407934127,520.5,11,515),
('U11p4_ETM_S04','CSEG_04',0,6.621272170490614,46.54372507945731,7.774999642055314/2,6.00391555142,7.7945142068,7.16908904914,14.5371179573,628,14,621)]
COL=('case','segment','azimuth_deg','cycle_index','range_MPa','amplitude_MPa','mean_gross_MPa','mean_Pe_hypothesis_MPa','mean_P0_hypothesis_MPa','count','status')
STATUS='REAL_GROSS_NOMINAL_CYCLES_PT_MEAN_SHIFT_HYPOTHESIS_NOT_LOCAL_MATERIAL'
sha=lambda x:hashlib.sha256(x).hexdigest()

def rainflow(xs):
    if len(xs)<3 or not all(math.isfinite(v) for v in xs):raise ValueError('INVALID_STRESS')
    y=[xs[0]]
    for v in xs[1:]:
        if v!=y[-1]:y.append(v)
    if len(y)==1:return []
    rev=[y[0]]
    for i in range(1,len(y)-1):
        if (y[i]-y[i-1])*(y[i+1]-y[i])<0:rev.append(y[i])
    rev.append(y[-1]);stack=[];out=[]
    for v in rev:
        stack.append(v)
        while len(stack)>=3:
            a,b,c=stack[-3:]
            if abs(b-a)>abs(c-b):break
            if b!=a:out.append((abs(b-a),(a+b)/2,.5 if len(stack)==3 else 1.))
            if len(stack)==3:stack.pop(0)
            else:stack[-3:-1]=[]
    for a,b in zip(stack,stack[1:]):
        if a!=b:out.append((abs(b-a),(a+b)/2,.5))
    return out

def source(path,case):
    name,batch,zh,gh,ch=SRC[case];zraw=(path/name).read_bytes()
    if sha(zraw)!=zh:raise ValueError('ZIP_SHA_MISMATCH')
    with zipfile.ZipFile(io.BytesIO(zraw)) as z:
        if z.testzip():raise ValueError('ZIP_CRC')
        names=[x for x in z.namelist() if x.endswith('_31seg.csv.gz')]
        if len(names)!=1:raise ValueError('ZIP_MEMBER')
        gz=z.read(names[0])
    if sha(gz)!=gh:raise ValueError('GZIP_SHA_MISMATCH')
    raw=gzip.decompress(gz)
    if sha(raw)!=ch:raise ValueError('CSV_SHA_MISMATCH')
    target={c[1] for c in CTRL if c[0]==case};data={s:[] for s in target};n=0
    for r in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
        n+=1
        if r['case']!=case or r['batch']!=batch:raise ValueError('CASE_BATCH_MISMATCH')
        if r['segment'] in target:
            row=[float(r[k]) for k in ('time_s','Fz_kN','Mx_kNm','My_kNm')]
            if not all(map(math.isfinite,row)):raise ValueError('NONFINITE_SOURCE')
            data[r['segment']].append(row)
    if n!=9*12001:raise ValueError('BATCH_COUNT')
    for v in data.values():
        if len(v)!=12001 or any(abs(r[0]-(100+i*.05))>1e-7 for i,r in enumerate(v)):
            raise ValueError('TIME_GRID')
    return data

def run(root,out,receipt):
    data={}
    for case in SRC:
        for seg,rows in source(root,case).items():data[(case,seg)]=rows
    result=[];summ=[]
    for case,seg,az,area,I,R,pe,p0,d4ref,d10ref,nref,href,fref in CTRL:
        theta=math.radians(az)
        sig=[.001*(r[1]/area+R/I*(math.sin(theta)*r[2]-math.cos(theta)*r[3])) for r in data[(case,seg)]]
        cycles=rainflow(sig)
        for shift in (pe,p0):
            shifted=rainflow([x-shift for x in sig])
            if len(shifted)!=len(cycles) or any(n!=ns or abs(r-rs)>1e-10 or abs(m-shift-ms)>1e-10
                for (r,m,n),(rs,ms,ns) in zip(cycles,shifted)):
                raise ValueError('REAL_SHIFT_INVARIANCE')
        d4=(math.fsum(n*r**4 for r,m,n in cycles)/600)**.25
        d10=(math.fsum(n*r**10 for r,m,n in cycles)/600)**.1
        h=sum(n==.5 for _,_,n in cycles);f=sum(n==1 for _,_,n in cycles)
        eq=math.fsum(n for _,_,n in cycles)
        if (abs(d4-d4ref)>1e-8 or abs(d10-d10ref)>1e-8 or eq!=nref or h!=href or f!=fref):
            raise ValueError('PRIOR_1984_ROW_ORACLE_MISMATCH')
        summ.append(dict(case=case,segment=seg,azimuth_deg=az,cycle_rows=len(cycles),half=h,full=f,equivalent_cycles=eq,
                         DEL4_MPa=d4,DEL10_MPa=d10,Pe_offset_MPa=pe,P0_offset_MPa=p0))
        for i,(rng,mean,n) in enumerate(cycles,1):
            result.append(dict(case=case,segment=seg,azimuth_deg=az,cycle_index=i,range_MPa=rng,
                amplitude_MPa=rng/2,mean_gross_MPa=mean,mean_Pe_hypothesis_MPa=mean-pe,
                mean_P0_hypothesis_MPa=mean-p0,count=n,status=STATUS))
    f=io.StringIO(newline='');w=csv.DictWriter(f,fieldnames=COL,lineterminator='\n');w.writeheader()
    for row in result:w.writerow({k:format(v,'.12g') if isinstance(v,float) else v for k,v in row.items()})
    blob=f.getvalue().encode();out.write_bytes(blob)
    receipt.write_text(json.dumps(dict(status=STATUS,rows=len(result),output_sha256=sha(blob),controls=summ,
        zip_sha256={c:SRC[c][2] for c in SRC},csv_sha256={c:SRC[c][4] for c in SRC},
        native_Abaqus_runs=0,material_damage=None,physical_pass=False),indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(rows=len(result),sha256=sha(blob),controls=summ)))

def self_test():
    expected=sorted([(2.,2.,1.),(4.,2.,.5),(4.,2.,.5)])
    assert sorted(rainflow([0,4,1,3,0]))==expected
    assert sorted(rainflow([v+5 for v in [0,4,1,3,0]]))==sorted((r,m+5,n) for r,m,n in expected)
    assert rainflow([1,1,1])==[]
    for xs in ([0,float('nan'),1],[0,1]):
        try:rainflow(xs)
        except ValueError:pass
        else:raise AssertionError('bad stress accepted')
    print('S10_REAL_CYCLE_MEAN_SYNTHETIC_PASS')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');p.add_argument('--zip-dir',type=Path)
    p.add_argument('--out',type=Path);p.add_argument('--receipt',type=Path);a=p.parse_args()
    if a.self_test:self_test()
    if a.zip_dir:
        if not a.out or not a.receipt:p.error('--out/--receipt required')
        run(a.zip_dir,a.out,a.receipt)
    elif not a.self_test:p.error('--self-test or --zip-dir required')
