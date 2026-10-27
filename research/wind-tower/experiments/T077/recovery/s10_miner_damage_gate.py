#!/usr/bin/env python3
"""S10 conditional Miner accumulator for VERIFIED LOCAL STRESS only.

Inputs are stress-cycle bins with externally supplied, material-specific N_allow.
No built-in S-N/mean-stress model; no load-DEL conversion; no physical PASS.
Annual damage = 8760*3600 * sum_b p_b * mean_seeds(D_sample / duration_s).
Each bin probability is time fraction; seed runs must cover the same duration
within a bin. Use --self-test for exact synthetic known-answer tests.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path

FIELDS = ('material_id','bin_id','seed_id','bin_probability','duration_s',
          'stress_range_MPa','mean_stress_MPa','cycles','N_allow_cycles',
          'stress_owner','material_model_ref','stress_source_sha256')
SECONDS_PER_YEAR = 8760 * 3600


def _positive(v, name, allow_zero=False):
    x = float(v)
    if not math.isfinite(x) or (x < 0 if allow_zero else x <= 0):
        raise ValueError('invalid '+name)
    return x


def calculate(raw, years=20.0):
    years = _positive(years, 'years')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if reader.fieldnames is None or set(reader.fieldnames) != set(FIELDS):
        raise ValueError('required cycle input columns missing or unexpected')
    rows = list(reader)
    if not rows:
        raise ValueError('empty cycle data')
    samples = defaultdict(float)
    settings = {}
    probabilities = {}
    material_models = {}
    seen = set()
    for row in rows:
        material, bin_id, seed = (row[k].strip() for k in ('material_id','bin_id','seed_id'))
        if not all((material,bin_id,seed)):
            raise ValueError('missing material/bin/seed')
        if row['stress_owner'].strip() != 'VERIFIED_LOCAL_MATERIAL_STRESS':
            raise ValueError('load-level or unverified stress is forbidden')
        model = row['material_model_ref'].strip()
        sha = row['stress_source_sha256'].strip().lower()
        if not model or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise ValueError('missing material model or stress source SHA256')
        p = _positive(row['bin_probability'], 'bin_probability')
        if p > 1:
            raise ValueError('probability exceeds 1')
        duration = _positive(row['duration_s'], 'duration_s')
        rng = _positive(row['stress_range_MPa'], 'stress_range_MPa', True)
        mean = float(row['mean_stress_MPa'])
        if not math.isfinite(mean):
            raise ValueError('invalid mean stress')
        count = _positive(row['cycles'], 'cycles', True)
        nallow = _positive(row['N_allow_cycles'], 'N_allow_cycles')
        key = (material,bin_id,seed)
        meta = (p,duration,sha,model)
        if key in settings and settings[key] != meta:
            raise ValueError('inconsistent seed metadata')
        settings[key] = meta
        if (material,bin_id) in probabilities and probabilities[material,bin_id] != p:
            raise ValueError('inconsistent bin probability across seeds')
        probabilities[material,bin_id] = p
        if material in material_models and material_models[material] != model:
            raise ValueError('mixed material fatigue models')
        material_models[material] = model
        # Exact duplicate cycle rows are rejected; aggregate identical cycles first.
        identity = (key,rng,mean,count,nallow)
        if identity in seen:
            raise ValueError('duplicate cycle record')
        seen.add(identity)
        samples[key] += count/nallow
    out = []
    for material in sorted(material_models):
        bins = sorted({b for (m,b) in probabilities if m == material})
        p_sum = sum(probabilities[material,b] for b in bins)
        if abs(p_sum - 1.0) > 1e-8:
            raise ValueError(f'incomplete bin probabilities for {material}: {p_sum}')
        annual = 0.0
        for b in bins:
            keys = sorted(k for k in samples if k[0] == material and k[1] == b)
            durations = {settings[k][1] for k in keys}
            if len(durations) != 1:
                raise ValueError('seed duration mismatch')
            per_second = sum(samples[k]/settings[k][1] for k in keys)/len(keys)
            annual += probabilities[material,b] * per_second * SECONDS_PER_YEAR
        out.append({'material_id':material,'material_model_ref':material_models[material],
                    'bin_count':len(bins),'annual_damage_conditional':annual,
                    'design_years':years,'design_damage_conditional':annual*years,
                    'status':'CONDITIONAL_NO_PHYSICAL_PASS'})
    return {'source_sha256':hashlib.sha256(raw).hexdigest(),'row_count':len(rows),
            'seconds_per_year':SECONDS_PER_YEAR,'results':out}


def selftest():
    # Two bins p=.25/.75, two 100-second seeds each; synthetic Dsample 0.001/0.002/0.003/0.005.
    base = dict(material_id='SYNTH_STEEL',duration_s='100',
                stress_range_MPa='10',mean_stress_MPa='5',N_allow_cycles='1000',
                stress_owner='VERIFIED_LOCAL_MATERIAL_STRESS',
                material_model_ref='SYNTHETIC_TEST_ONLY',stress_source_sha256='a'*64)
    rows=[]
    for b,p,counts in [('B1',.25,[1,2]),('B2',.75,[3,5])]:
        for i,count in enumerate(counts):
            rows.append(dict(base,bin_id=b,seed_id=f'S{i+1}',
                             bin_probability=str(p),cycles=str(count)))
    def encode(items):
        s=io.StringIO(newline='')
        w=csv.DictWriter(s,fieldnames=FIELDS,lineterminator='\n')
        w.writeheader();w.writerows(items)
        return s.getvalue().encode()
    result=calculate(encode(rows),years=20)
    expected=SECONDS_PER_YEAR*(.25*.0015/100 + .75*.004/100)
    assert abs(result['results'][0]['annual_damage_conditional']-expected)<1e-10
    assert abs(result['results'][0]['design_damage_conditional']-20*expected)<1e-8
    tests=[dict(rows[0],stress_owner='LOAD_DEL'),
           dict(rows[0],stress_source_sha256='UNKNOWN'),
           dict(rows[0],N_allow_cycles='0')]
    for altered in tests:
        try: calculate(encode([altered]+rows[1:]))
        except ValueError: pass
        else: raise AssertionError('invalid stress input accepted')
    try: calculate(encode(rows+rows[:1]))
    except ValueError: pass
    else: raise AssertionError('duplicate cycles accepted')
    try: calculate(encode([dict(r,bin_probability='0.2') if r['bin_id']=='B1' else r for r in rows]))
    except ValueError: pass
    else: raise AssertionError('incomplete bin probability accepted')
    try: calculate(encode([dict(rows[0],duration_s='99')]+rows[1:]))
    except ValueError: pass
    else: raise AssertionError('different seed durations accepted')
    return {'status':'PASS_SYNTHETIC_ONLY','annual_expected':expected,
            'design_20y_expected':20*expected,'negative_tests':6}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--input',type=Path)
    ap.add_argument('--years',type=float,default=20)
    ap.add_argument('--output',type=Path)
    a=ap.parse_args()
    if a.self_test:
        print(json.dumps(selftest(),sort_keys=True))
    if a.input:
        result=calculate(a.input.read_bytes(),a.years)
        data=json.dumps(result,sort_keys=True,indent=2)+'\n'
        if a.output: a.output.write_text(data,encoding='utf-8')
        else: print(data)
    if not a.self_test and not a.input: ap.error('provide --self-test or --input')


if __name__=='__main__': main()
