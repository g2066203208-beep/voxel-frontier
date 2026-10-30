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


# Three existing CI station pairs from the SAME Ridgecrest event, independent
# of the site-spectrum selection. No claim of three independent earthquakes.
def _rms_window(a,start,stop):
    if not 0<=start<stop<=len(a):raise ValueError('RMS_WINDOW')
    return math.sqrt(sum(x*x for x in a[start:stop])/(stop-start))

def station_triage(manifest_paths):
    if len(manifest_paths)!=3:raise ValueError('THREE_STATION_MANIFESTS_REQUIRED')
    periods=[.5,1.,2.,4.,6.,8.,10.]
    out={'status':'S05_THREE_STATION_SAME_EVENT_TRIAGE_NOT_DESIGN_PASS',
         'method':'Python stdlib Newmark beta=1/4 gamma=1/2, 5% damping; raw/pre20 mean/whole-window detrend',
         'periods_s':periods,'npts':20001,'dt_s':.01,'stations':[],
         'independent_event_count':1,'S05_PASS':False,'Abaqus_RUN':False,
         'target_spectrum_available':False,'source_low_frequency_band_validated':False,
         'notes':['Three station pairs are from one event; not three independent earthquakes.',
                  'PASC and RVR lack same-depth archived per-station miniSEED/StationXML receipts.',
                  'Signal-to-noise RMS and low detrend sensitivity are not design-wave acceptance.']}
    all_events=set()
    for mp in manifest_paths:
        mp=pathlib.Path(mp).resolve()
        m=json.loads(mp.read_text(encoding='utf-8'))
        pair=m['horizontal_components']
        if len(pair)!=2 or set(e['component'] for e in pair)!={'HNE','HNN'}:raise ValueError('HORIZONTAL_PAIR')
        station=pair[0]['station']
        if station!=pair[1]['station']:raise ValueError('STATION_MISMATCH')
        if any(e['rsn']!='NOT_PEER_RSN' for e in pair):raise ValueError('RSN_UNVERIFIED')
        if any(e['event']!=pair[0]['event'] for e in pair):raise ValueError('EVENT_MISMATCH')
        all_events.add(pair[0]['event'])
        item={'station':station,'source_accession':m['source_accession'],
              'manifest_path':str(mp),'manifest_sha256':sha(mp),
              'source_receipt_available':(mp.parent/'source_receipt.json').exists(),
              'components':[]}
        for e in pair:
            a,dt=load(mp.parent,e)
            if len(a)!=20001 or abs(dt-.01)>1e-12:raise ValueError('GRID_20001_0.01')
            offset=sum(a[:2000])/2000
            b=[x-offset for x in a]
            c=_linear_detrend(a)
            spec=[]
            for T in periods:
                r=sdof(a,dt,T,.05)['pseudo_sa_m_s2']
                q=sdof(b,dt,T,.05)['pseudo_sa_m_s2']
                l=sdof(c,dt,T,.05)['pseudo_sa_m_s2']
                spec.append({'period_s':T,'raw_psa_m_s2':r,
                             'pre20_psa_m_s2':q,'linear_psa_m_s2':l,
                             'raw_vs_pre20_rel':abs(r-q)/max(q,1e-12),
                             'linear_vs_pre20_rel':abs(l-q)/max(q,1e-12)})
            noise=_rms_window(b,0,2000);signal=_rms_window(b,3500,12000)
            item['components'].append({
                'component':e['component'],'source_csv_path':str(mp.parent/e['file']),
                'source_sha256':sha(mp.parent/e['file']),
                'pre20_offset_m_s2':offset,
                'raw_pga_g':max(map(abs,a))/G,'pre20_pga_g':max(map(abs,b))/G,
                'pre20_noise_rms_m_s2':noise,'post35to120_signal_rms_m_s2':signal,
                'signal_to_noise_rms_ratio':signal/max(noise,1e-12),
                'pre20_end_drift':drift(b,dt),
                'long_period_max_raw_vs_pre20_rel':max(x['raw_vs_pre20_rel'] for x in spec if x['period_s']>=4),
                'long_period_max_linear_vs_pre20_rel':max(x['linear_vs_pre20_rel'] for x in spec if x['period_s']>=4),
                'spectrum':spec})
        out['stations'].append(item)
    if len(all_events)!=1 or set(x['station'] for x in out['stations'])!={'CI.CLC','CI.PASC','CI.RVR'}:
        raise ValueError('THREE_STATIONS_ONE_EVENT')
    return out

def triage_selftest():
    assert abs(_rms_window([3.,4.],0,2)-math.sqrt(12.5))<1e-12
    for args in [([1.],0,2),([1.],1,1)]:
        try:_rms_window(*args)
        except ValueError as ex:assert str(ex)=='RMS_WINDOW'
        else:raise AssertionError('bad RMS window accepted')
    print('S05_THREE_STATION_TRIAGE_SYNTHETIC_TEST_PASS')



# S05 real-source two-event/four-pair long-period gate. Read-only secondary
# analysis of already-computed source spectra; NEVER a design accelerogram PASS.
def long_period_pair_gate(ridge, lone, target=None):
    """Return 16 paired horizontal geometric-mean PSA rows at 4/6/8/10s.
    Raw-vs-pre20 sensitivity is descriptive; NO arbitrary code threshold.
    Optional target must be separately sourced; even a small error is NOT PASS
    while low-frequency instrument response and site assumptions are unverified.
    """
    import re
    if ridge.get('independent_event_count') != 1 or ridge.get('source_low_frequency_band_validated') is not False or ridge.get('target_spectrum_available') is not False:
        raise ValueError('RIDGE_SOURCE_FLAGS')
    if lone.get('event_id') != 'ci39493944' or lone.get('low_frequency_validated') is not False or lone.get('Jiayu_site_spectrum_matched') is not False:
        raise ValueError('LONE_SOURCE_FLAGS')
    if lone.get('dt_s') != .01 or lone.get('npts') != 20001 or ridge.get('dt_s') != .01 or ridge.get('npts') != 20001:
        raise ValueError('SOURCE_TIME_GRID')
    if len(ridge.get('stations',[])) != 3 or {s['station'] for s in ridge['stations']} != {'CI.CLC','CI.PASC','CI.RVR'}:
        raise ValueError('RIDGE_STATIONS')
    if len(lone.get('components',[])) != 2 or not re.fullmatch('[a-f0-9]{64}',lone.get('source_raw_mseed_sha256','')):
        raise ValueError('LONE_SOURCE_PROVENANCE')
    periods=(4.,6.,8.,10.)
    if target is not None:
        if not target.get('source_document_id') or not target.get('site_evidence_ref') or target.get('damping_ratio') != .05:
            raise ValueError('TARGET_PROVENANCE_OR_DAMPING')
        if target.get('periods_s') != list(periods) or len(target.get('target_psa_m_s2',[])) != 4:
            raise ValueError('TARGET_PERIOD_GRID')
        if any(not math.isfinite(float(x)) or float(x)<=0 for x in target['target_psa_m_s2']):
            raise ValueError('TARGET_VALUES')
    rows=[]
    for event,station,components,receipt in (
        [('ci38457511',s['station'],s['components'],bool(s.get('source_receipt_available'))) for s in ridge['stations']]
        + [('ci39493944','CI.CLC',lone['components'],True)]
    ):
        if len(components)!=2:raise ValueError('PAIR_COUNT')
        def label(c):
            if event=='ci38457511':return c['component']
            return 'HNE' if '_HNE_' in c['original_csv'] else 'HNN' if '_HNN_' in c['original_csv'] else 'INVALID'
        pair={label(c):c for c in components}
        if set(pair)!={'HNE','HNN'}:raise ValueError('PAIR_LABELS')
        def source_hash(c):
            return c['source_sha256'] if event=='ci38457511' else c['original_sha256']
        if any(not re.fullmatch('[a-f0-9]{64}',source_hash(c)) for c in components):
            raise ValueError('SOURCE_SHA256')
        for period in periods:
            def extract(c):
                spec=c['spectrum'] if event=='ci38457511' else c['spectral_sensitivity_5pct_damping']
                matches=[x for x in spec if (x['period_s'] if event=='ci38457511' else x['T_s'])==period]
                if len(matches)!=1:raise ValueError('PERIOD_IDENTITY')
                x=matches[0]
                if event=='ci38457511':
                    return x['raw_psa_m_s2'],x['pre20_psa_m_s2'],x['linear_psa_m_s2']
                return x['raw_pseudo_sa_m_s2'],x['preevent20_pseudo_sa_m_s2'],x['linear_detrend_pseudo_sa_m_s2']
            a,b=extract(pair['HNE']),extract(pair['HNN'])
            if any(not math.isfinite(float(v)) or v<=0 for v in a+b):
                raise ValueError('PSA_NONPOSITIVE_OR_NONFINITE')
            gm=[math.sqrt(x*y) for x,y in zip(a,b)]
            drift=max(abs(c['pre20_end_drift']['end_displacement_m'] if event=='ci38457511'
                          else c['pre_event_mean_removed_drift']['end_displacement_m']) for c in components)
            if not math.isfinite(drift):raise ValueError('DRIFT_NONFINITE')
            row={'event_id':event,'station':station,'period_s':period,
                 'raw_pair_gm_psa_m_s2':gm[0],'pre20_pair_gm_psa_m_s2':gm[1],
                 'linear_pair_gm_psa_m_s2':gm[2],
                 'raw_vs_pre20_pair_relative_change':abs(gm[0]-gm[1])/gm[1],
                 'max_abs_pre20_end_displacement_m':drift,
                 'original_source_receipt_available':receipt,
                 'source_HNE_sha256':source_hash(pair['HNE']),
                 'source_HNN_sha256':source_hash(pair['HNN']),
                 'decision':'REJECT_RAW__HOLD_PRE20_NO_LOWFREQ_TARGET'}
            if target is not None:
                idx=periods.index(period)
                row['target_log_residual_diagnostic_only']=math.log(gm[1]/float(target['target_psa_m_s2'][idx]))
            rows.append(row)
    if len(rows)!=16:raise ValueError('EXPECTED_16_ROWS')
    return rows


def long_period_gate_selftest():
    # Adversarial checks on real report schema are performed in CI against
    # source SHA-locked reports; this small test checks target input rejection.
    t={'source_document_id':'SYNTHETIC_ONLY','site_evidence_ref':'NOT_SITE',
       'damping_ratio':.05,'periods_s':[4.,6.,8.,10.],
       'target_psa_m_s2':[1.,1.,1.,1.]}
    assert math.isclose(math.log(1./1.),0.)
    for bad in ({**t,'damping_ratio':.1},{**t,'periods_s':[4.,6.]},
                {**t,'target_psa_m_s2':[1.,0.,1.,1.]},
                {**t,'source_document_id':''}):
        # Validation is exercised with synthetic report shells; first check
        # is performed before any component access.
        r={'independent_event_count':1,'source_low_frequency_band_validated':False,
           'target_spectrum_available':False,'dt_s':.01,'npts':20001,
           'stations':[{'station':s} for s in ('CI.CLC','CI.PASC','CI.RVR')]}
        l={'event_id':'ci39493944','low_frequency_validated':False,
           'Jiayu_site_spectrum_matched':False,'dt_s':.01,'npts':20001,
           'components':[{},{}],'source_raw_mseed_sha256':'0'*64}
        try:long_period_pair_gate(r,l,bad)
        except ValueError as exc:
            assert str(exc).startswith('TARGET_'),str(exc)
        else:raise AssertionError('ACCEPTED_BAD_TARGET')
    print('S05_LONG_PERIOD_TARGET_GATE_SYNTHETIC_NEGATIVE_PASS 4')


def write_long_period_gate(ridge_path,lone_path,output_path,target_path=None):
    rpath=pathlib.Path(ridge_path);lpath=pathlib.Path(lone_path)
    ridge=json.loads(rpath.read_text(encoding='utf-8'))
    lone=json.loads(lpath.read_text(encoding='utf-8'))
    target=json.loads(pathlib.Path(target_path).read_text(encoding='utf-8')) if target_path else None
    rows=long_period_pair_gate(ridge,lone,target)
    fields=list(rows[0])
    with pathlib.Path(output_path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for row in rows:
            w.writerow({k:format(v,'.12g') if isinstance(v,float) else v for k,v in row.items()})
    print(json.dumps({'status':'S05_TWO_EVENTS_FOUR_PAIRS_SOURCE_QC_ONLY',
                      'input_report_sha256':{str(rpath):sha(rpath),str(lpath):sha(lpath)},
                      'output_csv_sha256':sha(output_path),'rows':len(rows),
                      'unique_events':len({r['event_id'] for r in rows}),
                      'target_supplied':bool(target),
                      'low_frequency_validated':False,'site_spectrum_PASS':False,
                      'Abaqus_RUN':0,'S05_PASS':False},sort_keys=True))


# ESM v3 MP: secondary 16-period passband-distance / integration-grid diagnostic.
# Ideal Butterworth gain at f=1/T is NOT an instrument transfer-function
# measurement and must NEVER be applied as a correction to response spectra.
_ESM_PERIODS_16=(.5,.75,1.,1.25,1.5,2.,2.5,3.,3.5,4.,5.,6.,7.,8.,9.,10.)
_ESM_DENSE_HEADER=('period_s','HNE_pseudoSa_m_s2','HNN_pseudoSa_m_s2',
    'horizontal_gm_pseudoSa_m_s2','HNE_2dt_pseudoSa_m_s2_DIAGNOSTIC',
    'HNN_2dt_pseudoSa_m_s2_DIAGNOSTIC',
    'max_component_dt2_relative_difference_DIAGNOSTIC','frequency_over_highpass_corner')

def esm_16period_passband_audit(source_csv, expected_sha256):
    """Read source-locked REAL ESM spectral CSV; return per-period diagnostics.
    Source DYNA: 2nd-order Butterworth HP corner=0.040Hz, dt=0.005s.
    Gain formula is hypothetical SINGLE-PASS magnitude at 1/T, not observed
    filtering, and PSA is broadband: gain must not be used to 'repair' PSA.
    """
    import re
    path=pathlib.Path(source_csv)
    if not re.fullmatch(r'[a-f0-9]{64}',expected_sha256 or '') or sha(path)!=expected_sha256:
        raise ValueError('ESM_DENSE_SOURCE_SHA256')
    with path.open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        if tuple(reader.fieldnames or ())!=_ESM_DENSE_HEADER:
            raise ValueError('ESM_DENSE_COLUMNS')
        raw=list(reader)
    if len(raw)!=16:raise ValueError('ESM_DENSE_ROW_COUNT')
    out=[]
    fc=.040
    for i,row in enumerate(raw):
        try:v={k:float(row[k]) for k in _ESM_DENSE_HEADER}
        except (TypeError,ValueError,KeyError) as e:raise ValueError('ESM_DENSE_NUMERIC') from e
        if any(not math.isfinite(z) for z in v.values()):
            raise ValueError('ESM_DENSE_NONFINITE')
        T=v['period_s']
        if T!=_ESM_PERIODS_16[i]:raise ValueError('ESM_DENSE_PERIOD_ORDER')
        e,n=v['HNE_pseudoSa_m_s2'],v['HNN_pseudoSa_m_s2']
        e2,n2=v['HNE_2dt_pseudoSa_m_s2_DIAGNOSTIC'],v['HNN_2dt_pseudoSa_m_s2_DIAGNOSTIC']
        if min(e,n,e2,n2)<=0:raise ValueError('ESM_DENSE_NONPOSITIVE_PSA')
        gm=math.sqrt(e*n)
        if not math.isclose(gm,v['horizontal_gm_pseudoSa_m_s2'],rel_tol=5e-10,abs_tol=1e-12):
            raise ValueError('ESM_DENSE_GM_MISMATCH')
        delta=max(abs(e2-e)/e,abs(n2-n)/n)
        if not math.isclose(delta,v['max_component_dt2_relative_difference_DIAGNOSTIC'],rel_tol=5e-9,abs_tol=1e-12):
            raise ValueError('ESM_DENSE_DT2_MISMATCH')
        ratio=1/(T*fc)
        if not math.isclose(ratio,v['frequency_over_highpass_corner'],rel_tol=5e-10,abs_tol=1e-10):
            raise ValueError('ESM_DENSE_CORNER_RATIO_MISMATCH')
        gain=1/math.sqrt(1+ratio**(-4)) # IDEAL single-pass 2nd-order HP only
        out.append({'period_s':T,'frequency_hz':1/T,
            'frequency_over_reported_0p040hz_corner':ratio,
            'ideal_single_pass_HP2_gain_AT_1_over_T_NOT_MEASURED':gain,
            'ideal_two_pass_HP2_gain_IF_FORWARD_BACKWARD_NOT_VERIFIED':gain*gain,
            'ideal_single_pass_HP2_attenuation_pct_AT_1_over_T':100*(1-gain),
            'ideal_two_pass_HP2_attenuation_pct_IF_FORWARD_BACKWARD':100*(1-gain*gain),
            'HNE_pseudoSa_m_s2_REAL_PROCESSED':e,
            'HNN_pseudoSa_m_s2_REAL_PROCESSED':n,
            'horizontal_gm_pseudoSa_m_s2_REAL_PROCESSED':gm,
            'dt_to_T':.005/T,'decimated_dt_to_T':.010/T,
            'max_component_dt2_rel_difference_NO_ANTIALIAS':delta,
            'record_duration_over_T_DIAGNOSTIC':(32040-1)*.005/T,
            'decision':'HOLD_INSTRUMENT_LOWFREQ_SNR_FILTER_HISTORY_AND_SITE_TARGET'})
    return out

def esm_16period_passband_selftest():
    with tempfile.TemporaryDirectory() as d:
        path=pathlib.Path(d)/'realistic_synthetic.csv'
        rows=[]
        for T in _ESM_PERIODS_16:
            e,n=1/T,1.1/T
            e2,n2=e*1.001,n*.999
            rows.append([T,e,n,math.sqrt(e*n),e2,n2,.001,1/(T*.04)])
        def write(rows,header=_ESM_DENSE_HEADER):
            with path.open('w',newline='') as f:
                w=csv.writer(f);w.writerow(header);w.writerows(rows)
            return sha(path)
        key=write(rows)
        result=esm_16period_passband_audit(path,key)
        assert len(result)==16 and all(x['decision'].startswith('HOLD_') for x in result)
        assert math.isclose(result[-1]['frequency_over_reported_0p040hz_corner'],2.5)
        assert math.isclose(result[-1]['ideal_single_pass_HP2_gain_AT_1_over_T_NOT_MEASURED'],
                            1/math.sqrt(1+2.5**(-4)),rel_tol=1e-14)
        tests=[('ESM_DENSE_SOURCE_SHA256',lambda:esm_16period_passband_audit(path,'0'*64))]
        def corrupted(change,err):
            original=[list(x) for x in rows]
            change(original)
            key=write(original)
            try:esm_16period_passband_audit(path,key)
            except ValueError as ex:assert str(ex)==err,(err,str(ex))
            else:raise AssertionError('ACCEPTED_'+err)
        for change,err in [
            (lambda x:x.pop(),'ESM_DENSE_ROW_COUNT'),
            (lambda x:x[1].__setitem__(0,.5),'ESM_DENSE_PERIOD_ORDER'),
            (lambda x:x[0].__setitem__(1,float('nan')),'ESM_DENSE_NONFINITE'),
            (lambda x:x[0].__setitem__(1,-1),'ESM_DENSE_NONPOSITIVE_PSA'),
            (lambda x:x[0].__setitem__(3,999),'ESM_DENSE_GM_MISMATCH'),
            (lambda x:x[0].__setitem__(6,.5),'ESM_DENSE_DT2_MISMATCH'),
            (lambda x:x[0].__setitem__(7,1),'ESM_DENSE_CORNER_RATIO_MISMATCH')]:
            corrupted(change,err)
        write(rows)
        try:esm_16period_passband_audit(path,'0'*64)
        except ValueError as ex:assert str(ex)=='ESM_DENSE_SOURCE_SHA256'
        else:raise AssertionError('ACCEPTED_BAD_SHA')
    print('S05_ESM_16PERIOD_PASSBAND_SYNTHETIC_PASS 16 analytic rows 8 rejects NOT_DESIGN_PASS')

def write_esm_16period_passband(source_csv, expected_sha256, output):
    rows=esm_16period_passband_audit(source_csv,expected_sha256)
    with pathlib.Path(output).open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k:format(v,'.12g') if isinstance(v,float) else v for k,v in row.items()})
    print(json.dumps({'status':'S05_ESM_16PERIOD_REAL_PROCESSED_SPECTRUM_BAND_DIAGNOSTIC_ONLY',
        'source_sha256':expected_sha256,'output_sha256':sha(output),
        'periods':len(rows),'max_dt2_relative_difference':max(x['max_component_dt2_rel_difference_NO_ANTIALIAS'] for x in rows),
        'minimum_frequency_over_highpass_corner':min(x['frequency_over_reported_0p040hz_corner'] for x in rows),
        'instrument_low_frequency_pass':False,'target_spectrum_pass':False,
        'Abaqus_E_WE_RUN':0,'S05_PASS':False},sort_keys=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');p.add_argument('--manifest');p.add_argument('--output')
    p.add_argument('--processed-manifest');p.add_argument('--spectral-stability',action='store_true')
    p.add_argument('--station-triage',action='store_true');p.add_argument('--triage-manifests',nargs=3)
    p.add_argument('--long-period-gate',action='store_true')
    p.add_argument('--triage-json');p.add_argument('--second-event-json');p.add_argument('--target-json')
    p.add_argument('--esm-band-csv');p.add_argument('--expected-source-sha256')
    a=p.parse_args()
    if a.self_test:
        esm_16period_passband_selftest()
        long_period_gate_selftest()
        self_test()
        stability_selftest()
        triage_selftest()
    elif a.esm_band_csv:
        if not a.expected_source_sha256 or not a.output:p.error('--esm-band-csv requires --expected-source-sha256 and --output')
        write_esm_16period_passband(a.esm_band_csv,a.expected_source_sha256,a.output)
    elif a.long_period_gate:
        if not a.triage_json or not a.second_event_json or not a.output:p.error('missing source reports/output')
        write_long_period_gate(a.triage_json,a.second_event_json,a.output,a.target_json)
    elif a.station_triage:
        if not a.triage_manifests or not a.output:p.error('--station-triage requires --triage-manifests (3) and --output')
        result=station_triage(a.triage_manifests)
        pathlib.Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print('S05_REAL_THREE_STATION_TRIAGE_NOT_DESIGN_PASS',[(s['station'],[(x['component'],x['pre20_end_drift']['end_displacement_m']) for x in s['components']]) for s in result['stations']])
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
