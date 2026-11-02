#!/usr/bin/env python3
"""S10 local-material stress fatigue *method gate* (not design verification).

Input JSON manifest defines records with CSV time_s,stress_MPa and SHA256, and
material-specific, independently sourced stress-range S-N points. There is no
built-in concrete/PT/rebar/steel S-N curve. No mean-stress correction is made:
outputs are conditional range-only diagnostics and are NEVER material PASS.

Records must be Abaqus local material stress histories, not OpenFAST load DEL,
CDP damage or peak/envelope tables. Annualization requires explicit bin hours
and independent seed IDs. All samples must have uniform time grids.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import tempfile

SECONDS_PER_HOUR = 3600.0


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def reversals(values):
    """Turning points, preserving the first and last finite sample."""
    if len(values) < 3 or not all(math.isfinite(x) for x in values):
        raise ValueError('NONFINITE_OR_SHORT_HISTORY')
    dedup = [values[0]]
    for x in values[1:]:
        if x != dedup[-1]:
            dedup.append(x)
    if len(dedup) == 1:
        return [dedup[0]]
    out = [dedup[0]]
    for i in range(1, len(dedup) - 1):
        if (dedup[i] - dedup[i-1]) * (dedup[i+1] - dedup[i]) < 0:
            out.append(dedup[i])
    out.append(dedup[-1])
    return out


def rainflow(values):
    """ASTM E1049-style reversal stack: (stress range, mean, count).

    End effects are retained as half cycles. No closed-loop assumption or
    automatic sequence repetition is introduced.
    """
    points = reversals(values)
    if len(points) < 2:
        return []
    stack = []
    cycles = []
    for p in points:
        stack.append(p)
        while len(stack) >= 3:
            older = abs(stack[-2] - stack[-3])
            newer = abs(stack[-1] - stack[-2])
            if newer < older:
                break
            count = 0.5 if len(stack) == 3 else 1.0
            if older > 0:
                cycles.append((older, (stack[-3] + stack[-2]) / 2, count))
            if len(stack) == 3:
                stack.pop(0)
            else:
                del stack[-3:-1]
    for a, b in zip(stack, stack[1:]):
        if a != b:
            cycles.append((abs(b-a), (a+b)/2, 0.5))
    return cycles


def cycles_to_failure(stress_range, points):
    """Log-log interpolation, no extrapolation of supplied material S-N data."""
    if stress_range <= 0:
        raise ValueError('NONPOSITIVE_STRESS_RANGE')
    ordered = sorted((float(p[0]), float(p[1])) for p in points)
    if len(ordered) < 2 or any(s <= 0 or n <= 0 for s,n in ordered):
        raise ValueError('INVALID_SN_POINTS')
    if any(ordered[i][0] >= ordered[i+1][0] or ordered[i][1] <= ordered[i+1][1] for i in range(len(ordered)-1)):
        raise ValueError('SN_NOT_STRICTLY_DECREASING')
    if not ordered[0][0] <= stress_range <= ordered[-1][0]:
        raise ValueError('SN_OUT_OF_RANGE_NO_EXTRAPOLATION')
    for (s0,n0),(s1,n1) in zip(ordered,ordered[1:]):
        if s0 <= stress_range <= s1:
            t = math.log(stress_range/s0) / math.log(s1/s0)
            return math.exp(math.log(n0) + t * math.log(n1/n0))
    raise AssertionError('SN_INTERPOLATION')


def read_history(root, item):
    p = (root / item['path']).resolve()
    if not p.is_relative_to(root) or not p.is_file():
        raise ValueError('SOURCE_PATH')
    if digest(p) != item['sha256']:
        raise ValueError('SOURCE_SHA256')
    with p.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ['time_s', 'stress_MPa']:
            raise ValueError('STRESS_HEADER')
        rows = [(float(r['time_s']), float(r['stress_MPa'])) for r in reader]
    if len(rows) < 3 or not all(math.isfinite(t) and math.isfinite(s) for t,s in rows):
        raise ValueError('STRESS_SAMPLES')
    dt = rows[1][0]-rows[0][0]
    if dt <= 0 or any(abs((rows[i][0]-rows[i-1][0])-dt) > max(1e-10, dt*1e-7) for i in range(1,len(rows))):
        raise ValueError('TIME_GRID')
    duration = rows[-1][0]-rows[0][0]
    if duration <= 0:
        raise ValueError('DURATION')
    return [s for _,s in rows], duration, dt


def analyze(manifest_path):
    p = Path(manifest_path).resolve()
    m = json.loads(p.read_text(encoding='utf-8'))
    if m.get('mean_stress_policy') != 'IGNORE_MEAN_DIAGNOSTIC_ONLY':
        raise ValueError('MEAN_STRESS_POLICY_REQUIRED')
    if m.get('history_kind') != 'LOCAL_MATERIAL_STRESS_ABAQUS':
        raise ValueError('NOT_LOCAL_MATERIAL_STRESS')
    curves = m['curves']
    bins = m['annual_bin_hours']
    if any(float(h) <= 0 for h in bins.values()) or sum(map(float,bins.values())) > 8760:
        raise ValueError('ANNUAL_HOURS')
    seen = set()
    results = []
    for item in m['records']:
        key = (item['material'], item['location'], item['bin'], item['seed'])
        if key in seen:
            raise ValueError('DUPLICATE_RECORD')
        seen.add(key)
        if item['bin'] not in bins or item['material'] not in curves:
            raise ValueError('MISSING_BIN_OR_CURVE')
        curve = curves[item['material']]
        if curve.get('source') in (None, '', 'UNKNOWN') or curve.get('kind') != 'RANGE_SN_DIAGNOSTIC':
            raise ValueError('CURVE_PROVENANCE_OR_KIND')
        samples, duration, dt = read_history(p.parent, item)
        cycles = rainflow(samples)
        d = sum(count/cycles_to_failure(rng,curve['stress_range_MPa_N']) for rng,_,count in cycles)
        results.append(dict(material=item['material'],location=item['location'],bin=item['bin'],seed=item['seed'],
                            n_samples=len(samples),dt_s=dt,duration_s=duration,cycle_count=sum(c[2] for c in cycles),
                            range_max_MPa=max((c[0] for c in cycles),default=0.0),
                            damage_per_record=d,damage_per_hour=d*SECONDS_PER_HOUR/duration,
                            source_sha256=item['sha256']))
    groups = {}
    for r in results:
        key = (r['material'],r['location'],r['bin'])
        groups.setdefault(key,[]).append(r)
    annual = {}
    for (mat,loc,b),rows in groups.items():
        annual[(mat,loc,b)] = sum(r['damage_per_hour'] for r in rows)/len(rows)*float(bins[b])
    return {'status':'S10_METHOD_TEST_ONLY_NOT_MATERIAL_PASS',
            'manifest_sha256':digest(p),
            'mean_stress_policy':'IGNORED_UNACCEPTABLE_FOR_FINAL_DESIGN',
            'records':results,
            'annualized_diagnostic_by_bin':[{'material':k[0],'location':k[1],'bin':k[2], 'damage':v} for k,v in sorted(annual.items())],
            'annualized_diagnostic_by_material_location':[
                {'material':mat,'location':loc,'damage':sum(v for (mm,ll,_),v in annual.items() if mm==mat and ll==loc)}
                for mat,loc in sorted(set((k[0],k[1]) for k in annual))],
            'hold':['No material-specific validated S-N/mean-stress law','No real Abaqus local stress histories',
                    'No validated long-term wind-bin probabilities/seed convergence','No physical model V&V']}


def self_test():
    # Exact reversal-count oracles; these are synthetic signals, NOT tower stresses.
    assert rainflow([0,0,0,0]) == []
    assert rainflow([0,10,0]) == [(10,5,0.5),(10,5,0.5)]
    assert sum(c for r,mean,c in rainflow([0,10,0,10,0]) if r==10) == 2
    assert sum(c for r,mean,c in rainflow([0,10,5,8,0]) if r==3) == 1
    assert math.isclose(cycles_to_failure(20,[(10,1e6),(40,1e4)]),1e5,rel_tol=1e-12)
    for bad in [5,41]:
        try:cycles_to_failure(bad,[(10,1e6),(40,1e4)])
        except ValueError as e:assert str(e)=='SN_OUT_OF_RANGE_NO_EXTRAPOLATION'
        else:raise AssertionError('EXTRAPOLATION_ACCEPTED')
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        path=root/'local.csv'
        with path.open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['time_s','stress_MPa'])
            for t,s in enumerate([0,10,0,10,0]):w.writerow([t,s])
        manifest={'history_kind':'LOCAL_MATERIAL_STRESS_ABAQUS',
                  'mean_stress_policy':'IGNORE_MEAN_DIAGNOSTIC_ONLY',
                  'annual_bin_hours':{'U10':3600},
                  'curves':{'TEST_STEEL':{'kind':'RANGE_SN_DIAGNOSTIC','source':'SYNTHETIC_TEST_ONLY',
                            'stress_range_MPa_N':[[5,2e6],[20,2e4]]}},
                  'records':[{'material':'TEST_STEEL','location':'SYNTHETIC_NODE', 'bin':'U10',
                              'seed':'S01','path':path.name,'sha256':digest(path)}]}
        mp=root/'manifest.json';mp.write_text(json.dumps(manifest),encoding='utf-8')
        out=analyze(mp)
        expected=2/cycles_to_failure(10,[[5,2e6],[20,2e4]])
        assert math.isclose(out['records'][0]['damage_per_record'],expected,rel_tol=1e-12)
        assert math.isclose(out['annualized_diagnostic_by_bin'][0]['damage'],expected/4*3600*3600,rel_tol=1e-12)
        manifest['records'][0]['sha256']='0'*64;mp.write_text(json.dumps(manifest))
        try:analyze(mp)
        except ValueError as e:assert str(e)=='SOURCE_SHA256'
        else:raise AssertionError('CORRUPTED_INPUT_ACCEPTED')
    return {'status':'SELF_TEST_PASS','tests':['constant','half_cycles','closed_triangles','nested_cycle',
             'loglog_SN','no_extrapolation','annual_hours','source_sha256_rejection'],
            'synthetic_damage_per_record':expected,'synthetic_annualized_damage':expected/4*3600*3600}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--output',type=Path)
    a=parser.parse_args()
    if a.self_test:
        print(json.dumps(self_test(),indent=2))
    else:
        if a.manifest is None:parser.error('--manifest is required unless --self-test')
        result=analyze(a.manifest)
        payload=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
        if a.output:a.output.write_text(payload,encoding='utf-8')
        else:print(payload)

if __name__=='__main__':main()
