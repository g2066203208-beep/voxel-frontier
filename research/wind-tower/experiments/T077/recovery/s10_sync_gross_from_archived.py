#!/usr/bin/env python3
"""Source-locked 4 ETM x 31 stations x 16 azimuths synchronous gross stress rainflow.
NOT material/local/PT fatigue, 20-year DLC1.2, coordinate-certified or Abaqus PASS.
Requires numpy+pandas and existing s06_31gage_rainflow_load_screen.py.
"""
import argparse,csv,gzip,hashlib,io,json,math,sys,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from s06_31gage_rainflow_load_screen import rainflow_ranges

CASES=('U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06')
BATCHES={'A':range(1,10),'B':range(10,19),'C':range(19,28),'D':range(28,32)}
ANGLES=tuple(22.5*i for i in range(16))
FIELDS=('case','segment','gage_z_m','section_z_m','delta_z_m','azimuth_deg','sigma_mean_MPa','sigma_min_MPa','sigma_max_MPa','sigma_max_time_s','sigma_peak_to_peak_MPa','DEL_m4_MPa','DEL_m10_MPa','rainflow_equivalent_cycles','rainflow_half_cycles','rainflow_full_cycles','n_samples','stress_class')
SUMMARY=('case','segment','gage_z_m','max_DEL_m4_MPa','azimuth_at_max_DEL4_deg','max_DEL_m10_MPa','azimuth_at_max_DEL10_deg','max_sigma_tension_MPa','azimuth_at_max_tension_deg','time_at_max_tension_s','min_sigma_compression_MPa','azimuth_at_min_compression_deg')
CLASS='SYNCHRONOUS_GROSS_ELASTIC_16AZIMUTH_NO_PT_NO_MATERIAL_LIFE'

def sha(b):return hashlib.sha256(b).hexdigest()
def read_csv(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def numeric(x):
    v=float(x)
    if not math.isfinite(v):raise ValueError('NONFINITE')
    return v

def geom_load(path):
    g={}
    for row in read_csv(path):
        s=row['segment'];d=numeric(row['D_m']);di=numeric(row['di_m'])
        if s in g or not 0<di<d:raise ValueError('GEOMETRY_IDENTITY')
        area=math.pi*(d*d-di*di)/4;inertia=math.pi*(d**4-di**4)/64
        if not math.isclose(area,numeric(row['A_m2']),rel_tol=1e-8):raise ValueError('GEOMETRY_AREA')
        if not math.isclose(inertia,numeric(row['I_m4']),rel_tol=1e-8):raise ValueError('GEOMETRY_INERTIA')
        g[s]=(numeric(row['z_center_m']),area,inertia,d/2)
    if set(g)!={f'CSEG_{i:02d}' for i in range(1,32)}:raise ValueError('GEOMETRY_31')
    return g

def del_rainflow(x):
    cycles=rainflow_ranges(x)
    d4=(math.fsum(n*r**4 for r,n in cycles)/600)**.25
    d10=(math.fsum(n*r**10 for r,n in cycles)/600)**.1
    return d4,d10,math.fsum(n for _,n in cycles),sum(n==.5 for _,n in cycles),sum(n==1 for _,n in cycles)

def render(rows,columns):
    s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=columns,lineterminator='\n');w.writeheader()
    for r in rows:w.writerow({k:format(v,'.12g') if isinstance(v,float) else v for k,v in r.items()})
    return s.getvalue().encode()

def self_test():
    assert rainflow_ranges([0,1,0])==[(1,.5),(1,.5)]
    assert rainflow_ranges([0,3,1,2,0])==[(1,1.),(3,.5),(3,.5)]
    assert math.isclose(del_rainflow([0,1,0])[0],600**(-.25))
    print('S10_SYNC_KNOWN_ANSWER_PASS_NO_MATERIAL')

def run(a):
    manifest=read_csv(a.manifest)
    if len(manifest)!=16 or {(r['case'],r['batch']) for r in manifest}!={(c,b) for c in CASES for b in 'ABCD'}:raise ValueError('MANIFEST_16')
    geom=geom_load(a.geometry)
    oracle={}
    if a.load_oracle:
        for row in read_csv(a.load_oracle):
            if row['channel'] in ('Fz_kN','Mx_kNm','My_kNm'):
                oracle[(row['case'],row['segment'],row['channel'])]=(numeric(row['DEL_m4_Nref_1Hz']),numeric(row['DEL_m10_Nref_1Hz']))
    out=[];control=[];verified=0;maxerr=0;maxoffset=0;source=[];total=0
    for e in manifest:
        case,batch=e['case'],e['batch'];prefix='T071' if case.startswith('U09') else 'T072'
        p=a.zip_dir/f'{prefix}-{case}-{batch}.zip';rawzip=p.read_bytes()
        if sha(rawzip)!=e['zip_sha256']:raise ValueError('ZIP_SHA_MISMATCH:'+p.name)
        with zipfile.ZipFile(io.BytesIO(rawzip)) as z:
            if z.testzip():raise ValueError('ZIP_CRC')
            names=[x for x in z.namelist() if x.endswith('_31seg.csv.gz')]
            if len(names)!=1:raise ValueError('GZIP_MEMBER')
            comp=z.read(names[0])
        if e.get('gzip_sha256') and sha(comp)!=e['gzip_sha256']:raise ValueError('GZIP_SHA_MISMATCH')
        raw=gzip.decompress(comp)
        if e.get('uncompressed_csv_sha256') and sha(raw)!=e['uncompressed_csv_sha256']:raise ValueError('CSV_SHA_MISMATCH')
        df=pd.read_csv(io.BytesIO(raw));required={'case','batch','segment','gage_index','gage_z_m','time_s','Fx_kN','Fy_kN','Fz_kN','Mx_kNm','My_kNm','Mz_kNm','V_kN','M_kNm','T_abs_kNm','N_comp_kN'}
        if set(df.columns)!=required or len(df)!=len(BATCHES[batch])*12001:raise ValueError('HISTORY_SHAPE')
        if not np.isfinite(df.select_dtypes(include='number').to_numpy()).all():raise ValueError('HISTORY_NONFINITE')
        for derived,computed in [('V_kN',np.hypot(df.Fx_kN,df.Fy_kN)),('M_kNm',np.hypot(df.Mx_kNm,df.My_kNm)),('T_abs_kNm',np.abs(df.Mz_kNm)),('N_comp_kN',np.maximum(0,-df.Fz_kN))]:
            if not np.allclose(df[derived],computed,atol=1e-6,rtol=1e-10):raise ValueError('DERIVED_WRENCH_'+derived)
        expected=[f'CSEG_{i:02d}' for i in BATCHES[batch]]
        if list(df.segment.drop_duplicates())!=expected or set(df.case)!={case} or set(df.batch)!={batch}:raise ValueError('SEGMENT_IDENTITY')
        for j,(seg,part) in enumerate(df.groupby('segment',sort=False),start=1):
            if len(part)!=12001 or set(part.gage_index)!={j}:raise ValueError('GAGE_LOCAL_INDEX')
            if np.max(np.abs(part.time_s.to_numpy()-(100+np.arange(12001)*.05)))>1e-7:raise ValueError('TIME_GRID')
            if np.ptp(part.gage_z_m)>1e-8:raise ValueError('GAGE_Z_DRIFT')
            z=float(part.gage_z_m.iloc[0]);zgeo,area,inertia,radius=geom[seg]
            maxoffset=max(maxoffset,abs(z-zgeo));n=part.Fz_kN.to_numpy();mx=part.Mx_kNm.to_numpy();my=part.My_kNm.to_numpy()
            for ch,values in [('Fz_kN',n),('Mx_kNm',mx),('My_kNm',my)]:
                key=(case,seg,ch)
                if key in oracle:
                    got=del_rainflow(values)[:2]
                    for v,ref in zip(got,oracle[key]):
                        maxerr=max(maxerr,abs(v-ref))
                        if not math.isclose(v,ref,rel_tol=5e-10,abs_tol=5e-8):raise ValueError('SOURCE_LOAD_DEL_ORACLE')
                    verified+=1
            rs=[]
            for angle in ANGLES:
                th=math.radians(angle)
                # sigma_z=Fz/A+(Mx*y-My*x)/I; x=Rcos(theta),y=Rsin(theta)
                # 0.001 converts kN/m² and kNm/m³ into MPa. No Pe/P0 added.
                sig=.001*n/area+.001*radius/inertia*(math.sin(th)*mx-math.cos(th)*my)
                d4,d10,ncy,half,full=del_rainflow(sig);imax=int(np.argmax(sig))
                rs.append(dict(case=case,segment=seg,gage_z_m=z,section_z_m=zgeo,delta_z_m=z-zgeo,azimuth_deg=angle,
                    sigma_mean_MPa=float(np.mean(sig)),sigma_min_MPa=float(np.min(sig)),sigma_max_MPa=float(sig[imax]),sigma_max_time_s=100+.05*imax,
                    sigma_peak_to_peak_MPa=float(np.ptp(sig)),DEL_m4_MPa=d4,DEL_m10_MPa=d10,
                    rainflow_equivalent_cycles=ncy,rainflow_half_cycles=half,rainflow_full_cycles=full,n_samples=12001,stress_class=CLASS))
            out.extend(rs);b4=max(rs,key=lambda r:r['DEL_m4_MPa']);b10=max(rs,key=lambda r:r['DEL_m10_MPa']);bt=max(rs,key=lambda r:r['sigma_max_MPa']);bc=min(rs,key=lambda r:r['sigma_min_MPa'])
            control.append(dict(case=case,segment=seg,gage_z_m=z,max_DEL_m4_MPa=b4['DEL_m4_MPa'],azimuth_at_max_DEL4_deg=b4['azimuth_deg'],
                max_DEL_m10_MPa=b10['DEL_m10_MPa'],azimuth_at_max_DEL10_deg=b10['azimuth_deg'],max_sigma_tension_MPa=bt['sigma_max_MPa'],
                azimuth_at_max_tension_deg=bt['azimuth_deg'],time_at_max_tension_s=bt['sigma_max_time_s'],
                min_sigma_compression_MPa=bc['sigma_min_MPa'],azimuth_at_min_compression_deg=bc['azimuth_deg']))
        total+=len(df);source.append(dict(case=case,batch=batch,artifact_id=e.get('artifact_id',''),zip_sha256=sha(rawzip),gzip_sha256=sha(comp),csv_sha256=sha(raw)))
        print('REAL_ZIP_VERIFIED',case,batch,len(df),file=sys.stderr)
    if total!=1488124 or len(control)!=124 or len(out)!=1984:raise ValueError('INCOMPLETE_4CASE_GRID')
    out.sort(key=lambda r:(CASES.index(r['case']),int(r['segment'][-2:]),r['azimuth_deg']))
    control.sort(key=lambda r:(CASES.index(r['case']),int(r['segment'][-2:])))
    full=render(out,FIELDS);summary=render(control,SUMMARY);a.out.write_bytes(full);a.summary.write_bytes(summary)
    receipt=dict(status='REAL_4CASE_31SEG_16AZ_SYNC_GROSS_RAINFLOW_NUMERIC_ONLY',source_zip_count=16,source_rows=total,
        geometry_sha256=sha(a.geometry.read_bytes()),manifest_sha256=sha(a.manifest.read_bytes()),
        source_records=source,output_rows=len(out),output_sha256=sha(full),summary_sha256=sha(summary),
        load_del_oracle_count=verified,load_del_oracle_max_abs_error=maxerr,max_gage_section_offset_m=maxoffset,
        max_DEL4=max(out,key=lambda r:r['DEL_m4_MPa']),max_tension=max(out,key=lambda r:r['sigma_max_MPa']),
        native_Abaqus_runs=0,material_fatigue_life=None,physical_pass=False,
        limitations='ETM 4-case screening only; not DLC1.2, not local material stress, not validated coordinate frame, no PT/connection/mean-stress model, no 20y damage')
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print('REAL_SYNCHRONOUS_NUMERIC_RESULT',json.dumps({k:receipt[k] for k in ('output_rows','output_sha256','summary_sha256','load_del_oracle_count','max_gage_section_offset_m')}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for x in ('zip-dir','manifest','geometry','out','summary','receipt','load-oracle'):p.add_argument('--'+x,type=Path)
    p.add_argument('--self-test',action='store_true');a=p.parse_args()
    if a.self_test:self_test()
    if a.zip_dir:
        if not all((a.manifest,a.geometry,a.out,a.summary,a.receipt)):p.error('missing input/output')
        run(a)
    elif not a.self_test:p.error('use --self-test or --zip-dir')
