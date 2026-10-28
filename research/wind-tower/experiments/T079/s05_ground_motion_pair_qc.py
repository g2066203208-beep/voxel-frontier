#!/usr/bin/env python3
"""S05 paired accelerogram QC: source hashes, sampling, units, drift and elastic SDOF.
No real PEER record is bundled; no site-spectrum/standard/Abaqus physics PASS.
"""
import argparse,csv,hashlib,json,math,pathlib,tempfile
G=9.80665
UNITS={'m/s2':1.,'cm/s2':.01,'g':G}
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def load(root,m):
    for k in ('file','sha256','rsn','event','station','component','unit','dt_s'):
        if k not in m or m[k] in ('',None):raise ValueError('MISSING_'+k)
    if m['unit'] not in UNITS:raise ValueError('UNIT')
    p=(root/m['file']).resolve()
    if not p.is_relative_to(root.resolve()) or not p.is_file():raise ValueError('PATH')
    if sha(p)!=m['sha256']:raise ValueError('SHA256')
    with p.open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f)
        if r.fieldnames!=['time_s','accel']:raise ValueError('HEADER')
        rows=[(float(z['time_s']),float(z['accel'])*UNITS[m['unit']] ) for z in r]
    if len(rows)<10 or not all(math.isfinite(t) and math.isfinite(a) for t,a in rows):raise ValueError('SAMPLES')
    dt=float(m['dt_s'])
    if dt<=0 or not math.isfinite(dt):raise ValueError('DT')
    if abs(rows[0][0])>1e-7 or any(abs(rows[i][0]-rows[i-1][0]-dt)>max(1e-8,dt*1e-5) for i in range(1,len(rows))):raise ValueError('TIME_GRID')
    return [a for t,a in rows],dt

def sdof(a,dt,T,zeta):
    """Newmark average acceleration, zero initial state, unit mass, relative DOF."""
    if T<=0 or dt<=0 or not 0<=zeta<1:raise ValueError('OSCILLATOR')
    w=2*math.pi/T;k=w*w;c=2*zeta*w
    u=v=0.;q=-a[0];peak=abs(u);absolute_peak=abs(q+a[0]);den=1+.5*dt*c+.25*dt*dt*k
    for ag in a[1:]:
        up=u+dt*v+.25*dt*dt*q;vp=v+.5*dt*q
        nq=(-ag-c*vp-k*up)/den
        u=up+.25*dt*dt*nq;v=vp+.5*dt*nq;q=nq
        peak=max(peak,abs(u));absolute_peak=max(absolute_peak,abs(q+ag))
    return {'period_s':T,'sd_m':peak,'pseudo_sa_m_s2':k*peak,'absolute_sa_m_s2':absolute_peak}

def drift(a,dt):
    v=u=0.
    for x,y in zip(a,a[1:]):
        vn=v+(x+y)*dt/2;u+=(v+vn)*dt/2;v=vn
    return {'end_velocity_m_s':v,'end_displacement_m':u}

def inspect(manifest):
    p=pathlib.Path(manifest).resolve();m=json.loads(p.read_text(encoding='utf-8'))
    if len(m.get('horizontal_components',[]))!=2:raise ValueError('PAIR_COUNT')
    if not m.get('source_database') or not m.get('source_accession'):raise ValueError('PROVENANCE')
    e1,e2=m['horizontal_components']
    if any(e1[k]!=e2[k] for k in ('rsn','event','station')):raise ValueError('PAIR_IDENTITY')
    if e1['component']==e2['component']:raise ValueError('DUPLICATE_COMPONENT')
    records=[load(p.parent,e) for e in (e1,e2)]
    if len(records[0][0])!=len(records[1][0]) or abs(records[0][1]-records[1][1])>1e-10:raise ValueError('PAIR_GRID')
    zeta=float(m['damping_ratio']);periods=m.get('periods_s',[.1,.2,.5,1.,2.,4.,6.,10.])
    if not periods or any(T<=0 or not math.isfinite(T) for T in periods):raise ValueError('PERIODS')
    out={'status':'SOURCE_QC_ONLY_NOT_SITE_SPECTRUM_PASS','manifest_sha256':sha(p),'source_database':m['source_database'],
         'source_accession':m['source_accession'],'event':e1['event'],'station':e1['station'],'rsn':e1['rsn'],
         'dt_s':records[0][1],'npts':len(records[0][0]),'damping_ratio':zeta,'components':[],
         'PEER_record_authenticated':False,'site_spectrum_match_PASS':False,'Abaqus_RUN':False,'S05_PASS':False,
         'HOLD':'Independently verify source RSN, usable low-frequency band, target spectrum, site and code.'}
    for e,(a,dt) in zip((e1,e2),records):
        out['components'].append({'component':e['component'],'file':e['file'],'sha256':sha(p.parent/e['file']),
            'original_unit':e['unit'],'pga_m_s2':max(map(abs,a)),'pga_g':max(map(abs,a))/G,
            'mean_m_s2':sum(a)/len(a),'uncorrected_drift':drift(a,dt),
            'spectrum':[sdof(a,dt,T,zeta) for T in periods]})
    return out

def self_test():
    # Harmonic input vs exact undamped oscillator IVP: second-order dt convergence.
    w=2*math.pi/1.2;om=2*math.pi/.7;tend=1.4
    exact=om*math.sin(w*tend)/(w*(w*w-om*om))-math.sin(om*tend)/(w*w-om*om)
    def uend(dt):
        a=[math.sin(om*i*dt) for i in range(round(tend/dt)+1)];u=v=0.;q=-a[0];k=w*w
        for ag in a[1:]:
            up=u+dt*v+.25*dt*dt*q;vp=v+.5*dt*q;nq=(-ag-k*up)/(1+.25*dt*dt*k)
            u=up+.25*dt*dt*nq;v=vp+.5*dt*nq;q=nq
        return u
    e1=abs(uend(.01)-exact);e2=abs(uend(.005)-exact)
    assert 3.8<e1/e2<4.2,(e1,e2)
    assert sdof([0.]*101,.01,1.,.05)['pseudo_sa_m_s2']==0
    with tempfile.TemporaryDirectory() as d:
        root=pathlib.Path(d);records=[]
        for j in range(2):
            p=root/f'h{j}.csv'
            with p.open('w',newline='') as f:
                wr=csv.writer(f);wr.writerow(['time_s','accel'])
                for i in range(101):wr.writerow([f'{i*.02:.8f}',f'{math.sin(i*.02+j):.12g}'])
            records.append({'file':p.name,'sha256':sha(p),'rsn':'SYNTHETIC','event':'TEST','station':'TEST','component':f'H{j}','unit':'m/s2','dt_s':.02})
        m={'source_database':'SYNTHETIC','source_accession':'NOT_REAL','damping_ratio':.05,'horizontal_components':records}
        mp=root/'manifest.json';mp.write_text(json.dumps(m))
        assert inspect(mp)['S05_PASS'] is False
        for field,bad,err in [('sha256','0'*64,'SHA256'),('station','wrong','PAIR_IDENTITY'),('component','H0','DUPLICATE_COMPONENT')]:
            orig=records[1][field];records[1][field]=bad;mp.write_text(json.dumps(m))
            try:inspect(mp)
            except ValueError as x:assert str(x)==err,(x,err)
            else:raise AssertionError('accepted corrupted '+field)
            records[1][field]=orig
        p=root/'h1.csv';p.write_bytes(p.read_bytes().replace(b'0.02000000',b'0.03000000',1))
        records[1]['sha256']=sha(p);mp.write_text(json.dumps(m))
        try:inspect(mp)
        except ValueError as x:assert str(x)=='TIME_GRID'
        else:raise AssertionError('accepted corrupt time grid')
    print(json.dumps({'selftest':'PASS','analytic_error_dt_0.01_m':e1,'analytic_error_dt_0.005_m':e2,
                      'error_ratio':e1/e2,'negative_tests':4,'real_ground_motions':0,'Abaqus_RUN':False}))


# Independent source-processing sensitivity: NO target spectrum, NO design acceptance.
_CLC_RAW={'HNE':'fb0c91fe588ccb4f6bed3d4ac77c4bc148231d8e5df6be19aa9cf3bc3d4c25ef',
          'HNN':'d6250274d578b87e4310eadcca5a910dd38cd69ad639dbca435af8e8a0d81e30'}
_CLC_PRE={'HNE':'271a962d1dec9199f51f6b605996b80f8bb072b29dd57e47e57ceb31b9507583',
          'HNN':'dc2b7879d18ffbb799c0d04d91ab42e8e469680c5dab943cb28e1357027401cd'}
_LONG_PERIODS=(.5,1.,2.,4.,6.,8.,10.)

def _linear_detrend(a):
    n=len(a);center=(n-1)/2;mean=sum(a)/n
    slope=sum((i-center)*(x-mean) for i,x in enumerate(a))/(n*(n*n-1)/12)
    return [x-mean-slope*(i-center) for i,x in enumerate(a)]

def spectral_stability(raw_manifest,pre_manifest):
    """Three processing scenarios on one hash-locked CI.CLC event/station pair.
    This reports SDOF sensitivity, not a validated low-frequency instrument band.
    """
    rp=pathlib.Path(raw_manifest).resolve();pp=pathlib.Path(pre_manifest).resolve()
    mr=json.loads(rp.read_text());mp=json.loads(pp.read_text())
    er={e['component']:e for e in mr['horizontal_components']}
    ep={e['component']:e for e in mp['horizontal_components']}
    if set(er)!=set(ep) or set(er)!={'HNE','HNN'}:raise ValueError('PAIR_COMPONENTS')
    if mr['source_accession']!='USGS:ci38457511;FDSN:CI.CLC:HN*:2019-07-06':raise ValueError('SOURCE_IDENTITY')
    out={'status':'S05_REAL_RECORD_BASELINE_SPECTRAL_SENSITIVITY_NOT_DESIGN_PASS',
         'source_accession':mr['source_accession'],'station':'CI.CLC','rsn':'NOT_PEER_RSN',
         'raw_manifest_sha256':sha(rp),'pre20_manifest_sha256':sha(pp),
         'damping_ratio':.05,'periods_s':list(_LONG_PERIODS),
         'method':'Newmark average acceleration, zero initial state, pseudoSa=w^2*max(abs(relative_u))',
         'processing':['raw','pre_event_20s_mean_removed','whole_window_linear_detrend_DIAGNOSTIC_ONLY'],
         'components':[],'usable_low_frequency_band_validated':False,
         'target_response_spectrum_defined':False,'S05_PASS':False,'Abaqus_RUN':False,
         'HOLD':'Baseline and low-frequency reliability not validated; no target spectrum; do not use as design accelerogram.'}
    for name in ('HNE','HNN'):
        r,p=er[name],ep[name]
        if any(r[k]!=p[k] for k in ('event','station','rsn','component')):raise ValueError('RAW_PRE_PAIR_IDENTITY')
        if r['sha256']!=_CLC_RAW[name] or p['sha256']!=_CLC_PRE[name]:raise ValueError('SOURCE_HASH_LOCK')
        a,dt=load(rp.parent,r);b,dt2=load(pp.parent,p)
        if dt!=.01 or dt2!=dt or len(a)!=20001 or len(b)!=len(a):raise ValueError('SOURCE_GRID')
        delta=[x-y for x,y in zip(a,b)];offset=sum(delta)/len(delta)
        offset_err=max(abs(x-offset) for x in delta)
        if offset_err>2e-8 or abs(sum(b[:2000])/2000)>2e-8:raise ValueError('PRE20_NOT_DC_ONLY')
        c=_linear_detrend(a)
        rows=[]
        for T in _LONG_PERIODS:
            sa_raw=sdof(a,dt,T,.05)['pseudo_sa_m_s2']
            sa_pre=sdof(b,dt,T,.05)['pseudo_sa_m_s2']
            sa_lin=sdof(c,dt,T,.05)['pseudo_sa_m_s2']
            rows.append({'period_s':T,'raw_pseudo_sa_m_s2':sa_raw,
                         'pre20_pseudo_sa_m_s2':sa_pre,'linear_pseudo_sa_m_s2':sa_lin,
                         'raw_vs_pre20_relative_change':abs(sa_raw-sa_pre)/max(sa_pre,1e-12),
                         'linear_vs_pre20_relative_change':abs(sa_lin-sa_pre)/max(sa_pre,1e-12)})
        out['components'].append({'component':name,'raw_sha256':sha(rp.parent/r['file']),
          'pre20_sha256':sha(pp.parent/p['file']),'npts':len(a),'dt_s':dt,
          'removed_dc_m_s2':offset,'constant_offset_max_residual_m_s2':offset_err,
          'drift':{'raw':drift(a,dt),'pre20':drift(b,dt),'linear_DIAGNOSTIC':drift(c,dt)},
          'spectrum':rows,
          'max_raw_vs_pre20_relative_change_T_ge_4s':max(x['raw_vs_pre20_relative_change'] for x in rows if x['period_s']>=4),
          'max_linear_vs_pre20_relative_change_T_ge_4s':max(x['linear_vs_pre20_relative_change'] for x in rows if x['period_s']>=4)})
    return out

def stability_selftest():
    x=[.7+.001*i for i in range(100)]
    assert max(abs(v) for v in _linear_detrend(x))<1e-12
    assert sdof([0.]*101,.01,10.,.05)['pseudo_sa_m_s2']==0
    assert abs(drift([1.]*101,.01)['end_displacement_m']-.5)<1e-12
    print('S05_SPECTRAL_STABILITY_SYNTHETIC_TEST_PASS 3')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');p.add_argument('--manifest');p.add_argument('--output')
    p.add_argument('--processed-manifest');p.add_argument('--spectral-stability',action='store_true')
    a=p.parse_args()
    if a.self_test:
        self_test()
        stability_selftest()
    elif a.spectral_stability:
        if not a.manifest or not a.processed_manifest or not a.output:
            p.error('--spectral-stability requires --manifest, --processed-manifest and --output')
        result=spectral_stability(a.manifest,a.processed_manifest)
        pathlib.Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print('REAL_CI_CLC_BASELINE_SPECTRAL_SENSITIVITY_NOT_DESIGN_PASS',
              [(x['component'],x['max_raw_vs_pre20_relative_change_T_ge_4s']) for x in result['components']])
    else:
        if not a.manifest or not a.output:p.error('--manifest and --output required')
        result=inspect(a.manifest);pathlib.Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print('SOURCE_QC_ONLY',a.output)
