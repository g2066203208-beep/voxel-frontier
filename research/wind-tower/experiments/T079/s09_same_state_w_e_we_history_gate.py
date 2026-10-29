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

Input CSV has 13 columns below. Real data MUST be supplied with its exact
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
        if time in groups[key][sc]: raise ValueError('DUPLICATE_TIME')
        groups[key][sc][time]=value
    if not row_count: raise ValueError('EMPTY_INPUT')
    out=[]; summaries=[]
    for (c,point),scenarios in sorted(groups.items()):
        if set(scenarios)!=set(SCENARIOS): raise ValueError('MISSING_SCENARIO')
        grids={sc:tuple(sorted(scenarios[sc])) for sc in SCENARIOS}
        grid=grids['B']
        if len(grid)<3: raise ValueError('TOO_FEW_SAMPLES')
        if any(grids[sc]!=grid for sc in SCENARIOS):
            raise ValueError('UNALIGNED_TIME_GRID')
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
    return {'status':'SYNTHETIC_ANALYTIC_SELFTEST_PASS_NOT_NATIVE',
            'positive_analytic_assertions':8,'negative_rejections':11,
            'example':a,'synthetic_input_sha256':hashlib.sha256(raw).hexdigest()}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--input',type=Path)
    ap.add_argument('--expected-sha256')
    ap.add_argument('--output-csv',type=Path)
    ap.add_argument('--output-json',type=Path)
    args=ap.parse_args()
    if args.self_test: print(json.dumps(self_test(),sort_keys=True))
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
    if not args.self_test and not args.input:ap.error('use --self-test or --input')


if __name__=='__main__':main()
