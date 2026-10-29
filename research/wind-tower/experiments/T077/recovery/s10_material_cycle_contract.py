#!/usr/bin/env python3
"""S10 load-screening -> local material-stress cycle interface. NO life/physical PASS.

Python stdlib. Load DEL is a *screening* input, not a material stress or S-N curve.
A separate, genuinely local Abaqus/fe-safe stress history is mandatory for cycles.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

EXPECTED_CASES = ('U09p343881_ETM_S06', 'U11p4_ETM_S04',
                  'U19p202140_ETM_S04', 'U19p202140_ETM_S06')
CHANNEL_UNITS = dict(Fx_kN='kN', Fy_kN='kN', Fz_kN='kN',
                     Mx_kNm='kNm', My_kNm='kNm', Mz_kNm='kNm')
MATERIALS = ('concrete', 'rebar', 'pt_strand', 'steel_tower')
REQUIRED = ('case', 'segment', 'gage_z_m', 'channel', 'units', 'n_samples',
            'dt_s', 'duration_s', 'mean', 'std', 'min', 'max', 'p2p',
            'rainflow_equivalent_cycles', 'rainflow_half_cycles',
            'rainflow_full_cycles', 'DEL_m4_Nref_1Hz', 'DEL_m10_Nref_1Hz')


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def load_screen(data):
    text = data.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError('BAD_HEADER')
    if any(c not in reader.fieldnames for c in REQUIRED):
        raise ValueError('MISSING_COLUMNS')
    seen, counts, maxima = set(), Counter(), {}
    for row in reader:
        if None in row or None in row.values():
            raise ValueError('BAD_WIDTH')
        case, seg, channel = row['case'], row['segment'], row['channel']
        if case not in EXPECTED_CASES or seg not in {f'CSEG_{i:02d}' for i in range(1, 32)}:
            raise ValueError('BAD_IDENTITY')
        if row['units'] != CHANNEL_UNITS.get(channel):
            raise ValueError('BAD_CHANNEL_UNITS')
        key = (case, seg, channel)
        if key in seen:
            raise ValueError('DUPLICATE_IDENTITY')
        seen.add(key)
        vals = [float(row[c]) for c in ('gage_z_m', 'dt_s', 'duration_s', 'mean',
                'std', 'min', 'max', 'p2p', 'rainflow_equivalent_cycles',
                'rainflow_half_cycles', 'rainflow_full_cycles',
                'DEL_m4_Nref_1Hz', 'DEL_m10_Nref_1Hz')]
        if not all(map(math.isfinite, vals)):
            raise ValueError('NONFINITE')
        z, dt, dur, avg, std, lo, hi, p2p, equiv, half, full, d4, d10 = vals
        if int(row['n_samples']) != 12001 or abs(dt - .05) > 1e-9 or abs(dur - 600) > 1e-7:
            raise ValueError('BAD_GRID')
        if not (0 <= z <= 112 and lo <= avg <= hi and std >= 0 and d4 >= 0 and d10 >= 0):
            raise ValueError('BAD_RANGE')
        if abs((hi-lo)-p2p) > 2e-6:
            raise ValueError('P2P_MISMATCH')
        if any(abs(v-round(v)) > 1e-7 or v < 0 for v in (half, full)):
            raise ValueError('BAD_CYCLE_COUNTS')
        if abs(equiv-(full+.5*half)) > 1e-7:
            raise ValueError('RAINFLOW_COUNT_MISMATCH')
        counts[case] += 1
        m = maxima.get(channel)
        if m is None or d4 > m['load_DEL_m4_1Hz']:
            maxima[channel] = {'case':case, 'segment':seg,
                'load_DEL_m4_1Hz':d4, 'unit':row['units']}
    if len(seen) != 744 or any(counts[c] != 186 for c in EXPECTED_CASES):
        raise ValueError('INCOMPLETE_4x31x6')
    return {'source_sha256':sha256(data), 'rows':len(seen),
        'cases':dict(sorted(counts.items())), 'max_load_DEL_by_channel':maxima,
        'status':'LOAD_SCREEN_ONLY_NOT_MATERIAL_DAMAGE',
        'no_local_stress':True, 'material_life_years':None}


def reversals(y):
    if len(y) < 3:
        raise ValueError('NEED_AT_LEAST_3_SAMPLES')
    out = [y[0]]
    for i in range(1, len(y)-1):
        if (y[i]-y[i-1])*(y[i+1]-y[i]) < 0:
            out.append(y[i])
    if y[-1] != out[-1]:
        out.append(y[-1])
    return out


def rainflow(y):
    """ASTM-style reversal stack; returns (range_MPa, mean_MPa, 0.5/1.0)."""
    stack, cycles = [], []
    for p in reversals(y):
        stack.append(p)
        while len(stack) >= 3:
            x, z = abs(stack[-2]-stack[-3]), abs(stack[-1]-stack[-2])
            if z < x:
                break
            if len(stack) == 3:
                if x:
                    cycles.append((x, (stack[-3]+stack[-2])/2, .5))
                del stack[0]
            else:
                if x:
                    cycles.append((x, (stack[-3]+stack[-2])/2, 1.))
                del stack[-3:-1]
    for a,b in zip(stack, stack[1:]):
        if a != b:
            cycles.append((abs(a-b), (a+b)/2, .5))
    return cycles


def stress_cycles(data):
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig')))
    needed = ('case','segment','material','point_id','time_s','stress_MPa')
    if reader.fieldnames is None or set(reader.fieldnames) != set(needed):
        raise ValueError('STRESS_SCHEMA')
    groups = defaultdict(list)
    for row in reader:
        if None in row or None in row.values():
            raise ValueError('STRESS_WIDTH')
        if row['material'] not in MATERIALS or row['case'] not in EXPECTED_CASES:
            raise ValueError('UNAPPROVED_MATERIAL_OR_CASE')
        if row['segment'] not in {f'CSEG_{i:02d}' for i in range(1,32)} or not row['point_id']:
            raise ValueError('BAD_STRESS_POINT')
        t,s = float(row['time_s']),float(row['stress_MPa'])
        if not (math.isfinite(t) and math.isfinite(s)):
            raise ValueError('NONFINITE_STRESS')
        groups[tuple(row[k] for k in needed[:4])].append((t,s))
    if not groups:
        raise ValueError('EMPTY_STRESS')
    out=[]
    for key,ts in sorted(groups.items()):
        if len(ts)<3:
            raise ValueError('SHORT_STRESS')
        steps=[b[0]-a[0] for a,b in zip(ts,ts[1:])]
        dt=steps[0]
        if dt<=0 or any(abs(v-dt)>max(1e-9,abs(dt)*1e-7) for v in steps):
            raise ValueError('NONUNIFORM_OR_UNSORTED_TIME')
        for rng,mean,n in rainflow([s for _,s in ts]):
            out.append(dict(zip(needed[:4],key),range_MPa=rng,
                            mean_MPa=mean,count=n,damage=None))
    return out


def selftest():
    assert rainflow([0,2,0]) == [(2,1,.5),(2,1,.5)]
    assert sum(c[2] for c in rainflow([0,2,0,2,0])) == 2
    assert rainflow([1,1,1]) == []
    try:
        stress_cycles(b'case,segment,material,point_id,time_s,stress_MPa\n'
                      b'U11p4_ETM_S04,CSEG_01,unknown,P1,0,0\n')
    except ValueError as e:
        assert str(e)=='UNAPPROVED_MATERIAL_OR_CASE'
    else:
        raise AssertionError('unknown material accepted')
    good=('case,segment,material,point_id,time_s,stress_MPa\n'
          'U11p4_ETM_S04,CSEG_01,rebar,bar01,0,0\n'
          'U11p4_ETM_S04,CSEG_01,rebar,bar01,0.1,2\n'
          'U11p4_ETM_S04,CSEG_01,rebar,bar01,0.2,0\n').encode()
    assert sum(x['count'] for x in stress_cycles(good))==1
    try:
        stress_cycles(good.replace(b'0.2,0',b'0.3,0'))
    except ValueError as e:
        assert str(e)=='NONUNIFORM_OR_UNSORTED_TIME'
    else:
        raise AssertionError('bad time accepted')
    assert not any(x['damage'] is not None for x in stress_cycles(good))
    return 'SELFTEST_PASS: 7 assertions incl ASTM ranges, cycle sum, rejection and no-damage'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--load-summary',type=Path)
    ap.add_argument('--stress-csv',type=Path)
    ap.add_argument('--output-json',type=Path)
    ap.add_argument('--output-cycles',type=Path)
    args=ap.parse_args()
    if args.self_test:
        print(selftest())
    result={'gate':'S10_INPUT_CONTRACT_ONLY','status':'NO_MATERIAL_LIFE',
            'stress_cycles_available':False,'source_level':'DERIVED_OPENFAST_LOAD_DEL'}
    if args.load_summary:
        result['load_screen']=load_screen(args.load_summary.read_bytes())
    if args.stress_csv:
        cycles=stress_cycles(args.stress_csv.read_bytes())
        result['stress_cycles_available']=True
        result['stress_input_sha256']=sha256(args.stress_csv.read_bytes())
        result['cycles_count']=len(cycles)
        if args.output_cycles:
            with args.output_cycles.open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=('case','segment','material','point_id',
                         'range_MPa','mean_MPa','count','damage'))
                writer.writeheader();writer.writerows(cycles)
    if args.output_json:
        args.output_json.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    if not (args.self_test or args.load_summary or args.stress_csv):
        ap.error('need --self-test and/or a source input')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()
