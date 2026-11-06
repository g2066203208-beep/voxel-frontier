#!/usr/bin/env python3
"""S09 synchronized B/W/E/WE structural-response comparison (NOT a solver).

B=baseline, W=wind only, E=earthquake only, WE=wind+earthquake, all with
IDENTICAL model, prestress/gravity initial state, operating mode, wind seed,
earthquake record identity, trigger, response point, coordinate and units.

Delta_E_given_W(t)=WE(t)-W(t).
Delta_E_given_B(t)=E(t)-B(t).
R(t)=WE(t)-W(t)-E(t)+B(t): an algebraic nonadditivity diagnostic, NOT proof
of aeroelastic interaction or physical coupled dynamics. If E is parked while
WE is operating, DO NOT feed them into the same comparison.

All QoIs sharing a comparison_id must also share the same physical-state identity\nand exact time grid, even if their units and point IDs differ.\n\nInput CSV has 13 columns below. Real data MUST be supplied with its exact
SHA256. No synthetic test or passing CSV check confers native/physics PASS.
Python 3.11+ standard library only.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path

FIELDS = ('comparison_id','scenario','model_sha256','initial_state_sha256',
          'operating_mode','wind_seed','earthquake_id','trigger_time_s',
          'point_id','qoi','unit','time_s','value')
SCENARIOS = ('B','W','E','WE')
OUT_FIELDS = ('comparison_id','point_id','qoi','unit','time_s','B','W','E','WE',
              'delta_E_given_W','delta_E_given_B','nonadditivity_residual')


def is_sha(x):
    return isinstance(x,str) and len(x)==64 and all(c in '0123456789abcdef' for c in x)


def finite(x,name):
    try: v=float(x)
    except (ValueError,TypeError): raise ValueError('INVALID_'+name) from None
    if not math.isfinite(v): raise ValueError('NONFINITE_'+name)
    return v


def parse(raw):
    if not isinstance(raw,bytes): raise ValueError('INPUT_MUST_BE_BYTES')
    try: s=raw.decode('utf-8-sig')
    except UnicodeError: raise ValueError('INVALID_UTF8') from None
    reader=csv.DictReader(io.StringIO(s))
    if reader.fieldnames is None or tuple(reader.fieldnames)!=FIELDS:
        raise ValueError('INVALID_OR_DUPLICATE_HEADER')
    groups=defaultdict(lambda: defaultdict(dict))
    metadata={}
    comparison_meta={}
    row_count=0
    for row in reader:
        row_count+=1
        if None in row or None in row.values(): raise ValueError('BAD_ROW_WIDTH')
        if any(not row[k].strip() for k in FIELDS): raise ValueError('EMPTY_FIELD')
        c=row['comparison_id']; sc=row['scenario']
        if sc not in SCENARIOS: raise ValueError('BAD_SCENARIO')
        if not is_sha(row['model_sha256']) or not is_sha(row['initial_state_sha256']):
            raise ValueError('UNVERIFIED_MODEL_OR_INITIAL_STATE_SHA')
        trigger=finite(row['trigger_time_s'],'TRIGGER')
        time=finite(row['time_s'],'TIME')
        value=finite(row['value'],'RESPONSE')
        if trigger < 0 or time < 0: raise ValueError('NEGATIVE_TIME')
        point=(row['point_id'],row['qoi'])
        key=(c,point)
        meta=tuple(row[k] for k in ('model_sha256','initial_state_sha256',
            'operating_mode','wind_seed','earthquake_id','trigger_time_s','unit'))
        if key in metadata and metadata[key]!=meta:
            raise ValueError('MISMATCHED_SAME_STATE_OR_UNITS')
        metadata[key]=meta
        # Same comparison_id is one physical experiment across all response points.
        # Units may differ by QoI, but model/initial state/mode/seed/quake/trigger may not.
        common=meta[:-1]
        if c in comparison_meta and comparison_meta[c]!=common:
            raise ValueError('CROSS_POINT_MODEL_STATE_MISMATCH')
        comparison_meta[c]=common
        if time in groups[key][sc]: raise ValueError('DUPLICATE_TIME')
        groups[key][sc][time]=value
    if not row_count: raise ValueError('EMPTY_INPUT')
    out=[]; summaries=[]
    comparison_grids={}
    for (c,point),scenarios in sorted(groups.items()):
        if set(scenarios)!=set(SCENARIOS): raise ValueError('MISSING_SCENARIO')
        grids={sc:tuple(sorted(scenarios[sc])) for sc in SCENARIOS}
        grid=grids['B']
        if len(grid)<3: raise ValueError('TOO_FEW_SAMPLES')
        if any(grids[sc]!=grid for sc in SCENARIOS):
            raise ValueError('UNALIGNED_TIME_GRID')
        if c in comparison_grids and comparison_grids[c]!=grid:
            raise ValueError('CROSS_POINT_TIME_GRID_MISMATCH')
        comparison_grids[c]=grid
        dts=[b-a for a,b in zip(grid,grid[1:])]
        if min(dts)<=0: raise ValueError('NONMONOTONE_TIME')
        dt=dts[0]
        if any(abs(d-dt)>max(1e-9,abs(dt)*1e-7) for d in dts):
            raise ValueError('NONUNIFORM_TIME_GRID')
        vals={sc:[scenarios[sc][t] for t in grid] for sc in SCENARIOS}
        dEW=[we-w for we,w in zip(vals['WE'],vals['W'])]
        dEB=[e-b for e,b in zip(vals['E'],vals['B'])]
        residual=[x-y for x,y in zip(dEW,dEB)]
        peak=lambda x:max(abs(v) for v in x)
        peak_idx=max(range(len(grid)),key=lambda i:abs(residual[i]))
        peak_we=peak(vals['WE']);peak_w=peak(vals['W'])
        summary={'comparison_id':c,'point_id':point[0],'qoi':point[1],
            'unit':metadata[c,point][-1],'n_samples':len(grid),'dt_s':dt,
            'model_sha256':metadata[c,point][0],
            'initial_state_sha256':metadata[c,point][1],
            'operating_mode':metadata[c,point][2],
            'wind_seed':metadata[c,point][3],
            'earthquake_id':metadata[c,point][4],
            'trigger_time_s':float(metadata[c,point][5]),
            'peak_abs_WE':peak_we,'peak_abs_W':peak_w,
            'difference_of_absolute_peaks':peak_we-peak_w,
            'peak_abs_delta_E_given_W':peak(dEW),
            'peak_abs_delta_E_given_B':peak(dEB),
            'peak_abs_nonadditivity':abs(residual[peak_idx]),
            'time_peak_abs_nonadditivity_s':grid[peak_idx],
            'rms_nonadditivity':math.sqrt(math.fsum(v*v for v in residual)/len(residual)),
            'status':'ALGEBRA_ONLY_NOT_PHYSICAL_INTERACTION'}
        summaries.append(summary)
        for i,t in enumerate(grid):
            out.append((c,point[0],point[1],summary['unit'],t,
                        *(vals[sc][i] for sc in SCENARIOS),dEW[i],dEB[i],residual[i]))
    return out,summaries,row_count


def render(rows):
    s=io.StringIO(newline='')
    w=csv.writer(s,lineterminator='\n')
    w.writerow(OUT_FIELDS)
    for row in rows:
        w.writerow([f'{x:.12g}' if isinstance(x,float) else x for x in row])
    return s.getvalue().encode('utf-8')


def self_test():
    meta=['SYNTHETIC_PAIR','', 'a'*64,'b'*64,'OPERATING','SEED01',
          'SYNTHETIC_QUAKE','2.0','TOWER_BASE','Mx','kNm']
    baseline=[2,2,2,2,2]
    wind=[0,1,0,-1,0]
    quake=[0,0,2,0,0]
    interact=[0,0,.5,0,0]
    v={'B':baseline,'W':[2+x for x in wind],
       'E':[2+x for x in quake],
       'WE':[2+x+y+z for x,y,z in zip(wind,quake,interact)]}
    s=io.StringIO(newline=''); w=csv.writer(s,lineterminator='\n');w.writerow(FIELDS)
    for sc in SCENARIOS:
        for i,x in enumerate(v[sc]):
            r=meta.copy();r[1]=sc
            w.writerow(r+[str(i),str(x)])
    raw=s.getvalue().encode(); rows,sums,n=parse(raw)
    a=sums[0]
    assert n==20 and len(rows)==5
    assert a['peak_abs_WE']==4.5 and a['peak_abs_W']==3
    assert a['difference_of_absolute_peaks']==1.5
    assert a['peak_abs_delta_E_given_W']==2.5
    assert a['peak_abs_nonadditivity']==.5
    assert a['time_peak_abs_nonadditivity_s']==2
    assert abs(a['rms_nonadditivity']-math.sqrt(.25/5))<1e-14
    assert len(render(rows).splitlines())==6
    def rejected(data,code):
        try:parse(data)
        except ValueError as e:
            assert str(e)==code,(str(e),code)
        else:raise AssertionError('ACCEPTED_INVALID_'+code)
    header=','.join(FIELDS)+'\n'
    lines=raw.decode().splitlines(keepends=True)
    def mutate_line(idx,col,value):
        x=lines.copy();fields=x[idx].rstrip('\n').split(',')
        fields[FIELDS.index(col)]=value;x[idx]=','.join(fields)+'\n'
        return ''.join(x).encode()
    rejected(mutate_line(2,'initial_state_sha256','c'*64),'MISMATCHED_SAME_STATE_OR_UNITS')
    rejected(mutate_line(2,'operating_mode','PARKED'),'MISMATCHED_SAME_STATE_OR_UNITS')
    rejected(mutate_line(2,'unit','N'),'MISMATCHED_SAME_STATE_OR_UNITS')
    rejected(mutate_line(2,'value','nan'),'NONFINITE_RESPONSE')
    rejected(mutate_line(2,'model_sha256','UNKNOWN'),'UNVERIFIED_MODEL_OR_INITIAL_STATE_SHA')
    rejected(mutate_line(2,'time_s','999'),'UNALIGNED_TIME_GRID')
    rejected(mutate_line(2,'time_s','0'),'DUPLICATE_TIME')
    rejected((header+''.join(x for x in lines[1:] if ',WE,' not in x)).encode(),'MISSING_SCENARIO')
    rejected(mutate_line(2,'wind_seed','SEED02'),'MISMATCHED_SAME_STATE_OR_UNITS')
    rejected(mutate_line(2,'trigger_time_s','2.1'),'MISMATCHED_SAME_STATE_OR_UNITS')
    rejected(mutate_line(2,'earthquake_id','OTHER'),'MISMATCHED_SAME_STATE_OR_UNITS')
    # Cross-point adversarial fixture: the old per-point-only gate accepted
    # incompatible model states and shifted grids under the SAME comparison_id.
    def second_point(mutator=None):
        cloned=[]
        for line in lines[1:]:
            cells=line.rstrip('\n').split(',')
            cells[FIELDS.index('point_id')]='TOWER_TOP'
            cells[FIELDS.index('qoi')]='Uy'
            cells[FIELDS.index('unit')]='m'
            if mutator: mutator(cells)
            cloned.append(','.join(cells)+'\n')
        return (''.join(lines)+''.join(cloned)).encode()
    two=second_point()
    cross_rows,cross_summaries,cross_n=parse(two)
    assert cross_n==40 and len(cross_rows)==10 and len(cross_summaries)==2
    assert {s['point_id'] for s in cross_summaries}=={'TOWER_BASE','TOWER_TOP'}
    def mutate_all(field,value):
        def apply(cells):
            i=FIELDS.index(field)
            cells[i]=value(cells[i]) if callable(value) else value
        return apply
    for field,value in [('model_sha256','c'*64),
                        ('initial_state_sha256','d'*64),
                        ('operating_mode','PARKED'),
                        ('wind_seed','SEED02'),
                        ('earthquake_id','OTHER'),
                        ('trigger_time_s','2.5')]:
        rejected(second_point(mutate_all(field,value)),
                 'CROSS_POINT_MODEL_STATE_MISMATCH')
    rejected(second_point(mutate_all('time_s',lambda x:str(float(x)+0.1))),
             'CROSS_POINT_TIME_GRID_MISMATCH')
    return {'status':'SYNTHETIC_ANALYTIC_SELFTEST_PASS_NOT_NATIVE',
            'positive_analytic_assertions':11,'negative_rejections':18,
            'cross_point_positive_assertions':3,'cross_point_negative_rejections':7,
            'example':a,'synthetic_input_sha256':hashlib.sha256(raw).hexdigest()}



# S08 real ESM-derived beam-proxy admission: this is an E-only, downsampled
# source, never a fabricated B/W/E/WE set or an accepted S09 physical pair.
PROXY_FIELDS = ('direction','time_s','top_relative_u_m','top_absolute_acc_m_s2',
                'base_elastic_shear_N','base_elastic_moment_Nm')
PROXY_DIRECTIONS = ('HNE','HNN')
PROXY_SOURCE_SHA256 = 'c6763281ca366b16849321b7542024af111d78ebb6ee470c912dda060b51ba22'
PROXY_RECEIPT_SHA256 = '02730b484864b02cf1d7c83826ac819ef768fd7979cb4723c2962fd0a85ed939'


def proxy_sampling_qc(raw, peak_receipt, expected_n=1602):
    """Compare actual 0.1-s S08 E proxy with its original 0.005-s peak receipt."""
    try:
        decoded=raw.decode('utf-8-sig')
    except UnicodeError:
        raise ValueError('PROXY_INVALID_UTF8') from None
    rd=csv.DictReader(io.StringIO(decoded))
    if tuple(rd.fieldnames or ())!=PROXY_FIELDS:
        raise ValueError('PROXY_HEADER_MISMATCH')
    by_dir={k:[] for k in PROXY_DIRECTIONS}
    for row in rd:
        if None in row or None in row.values():
            raise ValueError('PROXY_ROW_WIDTH')
        if row['direction'] not in by_dir:
            raise ValueError('PROXY_UNKNOWN_DIRECTION')
        vals=[finite(row[k],'PROXY_'+k) for k in PROXY_FIELDS[1:]]
        by_dir[row['direction']].append(vals)
    summary=[]
    source_peaks={x['direction']:x for x in peak_receipt['peak_summary']}
    if set(source_peaks)!=set(PROXY_DIRECTIONS):
        raise ValueError('PROXY_PEAK_RECEIPT_DIRECTIONS')
    mapping={
        'top_relative_u_m':'peak_top_relative_displacement_m',
        'top_absolute_acc_m_s2':'peak_top_absolute_acceleration_m_s2',
        'base_elastic_shear_N':'peak_base_elastic_shear_kN',
        'base_elastic_moment_Nm':'peak_base_elastic_moment_kNm'}
    for direction in PROXY_DIRECTIONS:
        rows=by_dir[direction]
        if len(rows)!=expected_n:
            raise ValueError('PROXY_NPTS_MISMATCH')
        grid=[x[0] for x in rows]
        if abs(grid[0])>1e-12 or any(abs(t-i*.1)>1e-8 for i,t in enumerate(grid)):
            raise ValueError('PROXY_NONUNIFORM_OR_SHIFTED_GRID')
        for j,key in enumerate(PROXY_FIELDS[2:],start=1):
            i=max(range(len(rows)),key=lambda k:abs(rows[k][j]))
            sampled=abs(rows[i][j]);full=abs(float(source_peaks[direction][mapping[key]]))
            if key in ('base_elastic_shear_N','base_elastic_moment_Nm'):
                full*=1000.
            if not math.isfinite(full) or full<=0:
                raise ValueError('PROXY_INVALID_FULL_PEAK')
            if sampled>full*(1+1e-6):
                raise ValueError('PROXY_SAMPLED_PEAK_EXCEEDS_FULL')
            summary.append({'direction':direction,'qoi':key,'sampled_peak_abs':sampled,
                            'full_resolution_peak_abs':full,'peak_loss_pct':100*(1-sampled/full),
                            'sampled_peak_time_s':grid[i]})
    return {'status':'REAL_ESM_BEAM_PROXY_DOWNSAMPLED_E_ONLY_NOT_S09_PAIRED',
            'source_nrows':sum(map(len,by_dir.values())),
            'samples_per_direction':expected_n,'sampled_dt_s':.1,
            'original_ground_dt_s':.005,'sample_interval_ratio':20,
            'max_peak_loss_pct':max(x['peak_loss_pct'] for x in summary),
            'peak_comparison':summary,'S09_pair_admissible':False,
            'initial_state_sha256':None,'actual_wind_W_WE':False,
            'HOLD':'E-only 0.1s sampled linear beam proxy; no same-state B/W/WE, no validated initial state; use full-resolution source for future pairing'}


def proxy_sampling_self_test():
    def fixture(shift=False,missing=False):
        s=io.StringIO();wr=csv.writer(s,lineterminator='\n');wr.writerow(PROXY_FIELDS)
        for direction in PROXY_DIRECTIONS if not missing else ('HNE',):
            for i in range(3):
                wr.writerow([direction, i*.1+(.02 if shift and i==1 else 0),
                             .1*(i+1),.2*(i+1),100*(i+1),1000*(i+1)])
        return s.getvalue().encode()
    receipt={'peak_summary':[{'direction':d,
         'peak_top_relative_displacement_m':.4,
         'peak_top_absolute_acceleration_m_s2':.8,
         'peak_base_elastic_shear_kN':.4,
         'peak_base_elastic_moment_kNm':4.} for d in PROXY_DIRECTIONS]}
    got=proxy_sampling_qc(fixture(),receipt,expected_n=3)
    assert got['source_nrows']==6 and len(got['peak_comparison'])==8
    assert abs(got['max_peak_loss_pct']-25)<1e-10
    def rejected(raw,ref,code):
        try:proxy_sampling_qc(raw,ref,expected_n=3)
        except ValueError as e:assert str(e)==code,(e,code)
        else:raise AssertionError('PROXY_ACCEPTED_INVALID_'+code)
    rejected(fixture(shift=True),receipt,'PROXY_NONUNIFORM_OR_SHIFTED_GRID')
    rejected(fixture(missing=True),receipt,'PROXY_NPTS_MISMATCH')
    rejected(fixture().replace(b'0.30000000000000004',b'nan'),receipt,'NONFINITE_PROXY_top_relative_u_m')
    bad={'peak_summary':[dict(x) for x in receipt['peak_summary']]}
    bad['peak_summary'][0]['peak_top_relative_displacement_m']=.01
    rejected(fixture(),bad,'PROXY_SAMPLED_PEAK_EXCEEDS_FULL')
    rejected(fixture().replace(b'direction,time_s',b'dir,time_s'),receipt,'PROXY_HEADER_MISMATCH')
    rejected(fixture().replace(b'HNN',b'UNKNOWN'),receipt,'PROXY_UNKNOWN_DIRECTION')
    return {'positive':3,'negative':6,'synthetic_max_peak_loss_pct':25.0}


def run_proxy_sampling(history_path,receipt_path,output_path):
    history=history_path.read_bytes();receipt_bytes=receipt_path.read_bytes()
    if hashlib.sha256(history).hexdigest()!=PROXY_SOURCE_SHA256:
        raise ValueError('PROXY_SOURCE_SHA256_MISMATCH')
    if hashlib.sha256(receipt_bytes).hexdigest()!=PROXY_RECEIPT_SHA256:
        raise ValueError('PROXY_RECEIPT_SHA256_MISMATCH')
    receipt=json.loads(receipt_bytes)
    if receipt['source_esm_sha256']!='a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34':
        raise ValueError('PROXY_ESM_IDENTITY_MISMATCH')
    result=proxy_sampling_qc(history,receipt)
    result.update({'SOURCE':'T079/real-records archived S08 ESM 158m beam-proxy history and original full-rate peak receipt',
       'REF':'Existing T079 reduced linear beam proxy, not original OpenFAST/earthquake structural validation',
       'STANDARD':'2025 IEC/GB authorized site clauses NOT READ in this run',
       'OFFICIAL':'ESM processed earthquake provenance inherited from S08 receipt; not independently downloaded in this run',
       'RUN':'Python stdlib source-level history comparison; no new beam/OpenFAST/native seismic solve',
       'FIG':0,'TAB':'8 sampled-versus-full-peak comparisons in this JSON',
       'source_history_sha256':PROXY_SOURCE_SHA256,'source_receipt_sha256':PROXY_RECEIPT_SHA256,
       'source_esm_sha256':receipt['source_esm_sha256'],
       'source_tower_sha256':receipt['source_tower_sha256'],
       'reading_level':'GitHub original derived CSV 3204 rows plus S08 original 0.005s peak summary; original ESM waveform not re-read',
       'assumptions':['S08 output every 20 samples; original peak receipt derived from 0.005s computation',
                      '0.1s sample-grid peak <= original full-grid peak; not a resampling error bound'],
       'error_budget':{'numeric':'float64 peak arithmetic; full-grid receipt is prior-run not independently recomputed',
                       'downsampled_time_resolution_s':.1,'native_model_uncertainty':'UNQUANTIFIED',
                       'inter_sample_peak_and_spectral_aliasing':'NOT_BOUNDED_BY_THIS_PEAK_COMPARISON'},
       'failed_cases':'six synthetic negative tests in proxy_sampling_self_test',
       'physics_PASS':False,'S09_PASS':False,'native_E_WE_RUN':0})
    output_path.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--input',type=Path)
    ap.add_argument('--expected-sha256')
    ap.add_argument('--output-csv',type=Path)
    ap.add_argument('--output-json',type=Path)
    ap.add_argument('--proxy-history',type=Path)
    ap.add_argument('--proxy-peak-receipt',type=Path)
    ap.add_argument('--proxy-output-json',type=Path)
    args=ap.parse_args()
    if args.self_test: print(json.dumps({'paired':self_test(),'proxy_sampling':proxy_sampling_self_test()},sort_keys=True))
    if args.input:
        if not (args.expected_sha256 and is_sha(args.expected_sha256)):
            ap.error('real input requires expected exact SHA256')
        if not (args.output_csv and args.output_json):
            ap.error('both outputs required')
        raw=args.input.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        if sha!=args.expected_sha256:raise ValueError('INPUT_SHA256_MISMATCH')
        if any(p.resolve()==args.input.resolve() for p in (args.output_csv,args.output_json)):
            raise ValueError('INPUT_OUTPUT_OVERLAP')
        rows,summaries,n=parse(raw)
        result={'input_sha256':sha,'input_rows':n,'output_rows':len(rows),
                'summaries':summaries,'native_Abaqus_RUN':0,'physics_PASS':False,
                'scope':'SAME_STATE_ALGEBRA_ONLY_NOT_PHYSICAL_COUPLING'}
        csv_bytes=render(rows)
        args.output_csv.write_bytes(csv_bytes)
        result['output_csv_sha256']=hashlib.sha256(csv_bytes).hexdigest()
        args.output_json.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        print(json.dumps(result,sort_keys=True))
    if args.proxy_history:
        if not args.proxy_peak_receipt or not args.proxy_output_json:
            ap.error('--proxy-history requires --proxy-peak-receipt and --proxy-output-json')
        print(json.dumps(run_proxy_sampling(args.proxy_history,args.proxy_peak_receipt,args.proxy_output_json),sort_keys=True))
    if not args.self_test and not args.input and not args.proxy_history:ap.error('use --self-test, --input or --proxy-history')


if __name__=='__main__':main()
