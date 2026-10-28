#!/usr/bin/env python3
"""S10 local-stress rainflow and optional metal mean-stress transform.

ASTM E1049-style three-point stack; residual cycles are half cycles.
No local Abaqus stress, material S-N curves, annual damage or physical PASS.
Concrete/PT retain range+mean; Goodman is an optional steel hypothesis only.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

COLUMNS = ('time_s', 'stress_MPa')
REQUIRED = ('source_sha256', 'stress_owner', 'material_id', 'material_class',
            'stress_location', 'stress_component', 'material_model_ref',
            'initial_state', 'mean_stress_rule')
CLASSES = ('concrete', 'ordinary_rebar', 'prestressing_strand', 'structural_steel')


def reversals(values):
    """Keep endpoints and turning points; remove plateaus."""
    if len(values) < 3:
        raise ValueError('at least three stress samples required')
    compact = [values[0]]
    for v in values[1:]:
        if v != compact[-1]:
            compact.append(v)
    if len(compact) < 2:
        raise ValueError('constant stress history has no cycles')
    out = [compact[0]]
    for i in range(1, len(compact)-1):
        if (compact[i]-compact[i-1])*(compact[i+1]-compact[i]) < 0:
            out.append(compact[i])
    out.append(compact[-1])
    return out


def rainflow(values):
    """Return unrounded (range, mean, count) without amplitude grouping."""
    stack, cycles = [], []
    for v in reversals(values):
        stack.append(v)
        while len(stack) >= 3:
            older, middle, newest = stack[-3:]
            if abs(middle-older) > abs(newest-middle):
                break
            rng = abs(middle-older)
            if rng:
                cycles.append((rng, (middle+older)/2, 0.5 if len(stack)==3 else 1.0))
            if len(stack)==3:
                stack.pop(0)
            else:
                stack[-3:-1] = []
    for a,b in zip(stack, stack[1:]):
        if a != b:
            cycles.append((abs(b-a), (a+b)/2, 0.5))
    return cycles


def corrected_range(rng, mean, meta):
    """Optional Goodman for steel only; never a universal fatigue model."""
    rule = meta['mean_stress_rule']
    if rule == 'NONE_KEEP_MEAN':
        return rng
    if rule != 'GOODMAN_TENSION_ONLY':
        raise ValueError('unknown mean-stress rule')
    if meta['material_class'] not in ('ordinary_rebar', 'structural_steel'):
        raise ValueError('Goodman cannot be applied generically to concrete/PT')
    su = float(meta.get('ultimate_tensile_MPa', 'nan'))
    if not math.isfinite(su) or su <= 0 or mean >= su:
        raise ValueError('invalid ultimate strength or Goodman singularity')
    return rng/(1.0-max(mean,0.0)/su)


def calculate(raw, meta):
    if not isinstance(meta, dict) or any(not str(meta.get(k,'')).strip() for k in REQUIRED):
        raise ValueError('incomplete provenance manifest')
    if meta['material_class'] not in CLASSES:
        raise ValueError('unknown material class')
    if meta['stress_owner'] != 'VERIFIED_LOCAL_MATERIAL_STRESS':
        raise ValueError('load-level/unverified stress prohibited')
    if meta['initial_state'] != 'VERIFIED_GRAVITY_EFFECTIVE_PT_INCLUDED':
        raise ValueError('gravity/effective-PT mean state not verified')
    sha = hashlib.sha256(raw).hexdigest()
    if sha != meta['source_sha256']:
        raise ValueError('stress history SHA256 mismatch')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if reader.fieldnames is None or tuple(reader.fieldnames) != COLUMNS:
        raise ValueError('time/stress columns mismatch')
    ts, stress = [], []
    for row in reader:
        if None in row or any(row.get(k) is None for k in COLUMNS):
            raise ValueError('malformed stress history row')
        t,s = float(row['time_s']),float(row['stress_MPa'])
        if not math.isfinite(t) or not math.isfinite(s):
            raise ValueError('nonfinite time or stress')
        ts.append(t)
        stress.append(s)
    if len(ts)<3:
        raise ValueError('insufficient stress history')
    dts = [b-a for a,b in zip(ts,ts[1:])]
    if min(dts)<=0:
        raise ValueError('time must be strictly increasing')
    dt = dts[0]
    if max(abs(x-dt) for x in dts)>max(1e-9,1e-7*dt):
        raise ValueError('nonuniform time sampling')
    if meta['mean_stress_rule'] not in ('NONE_KEEP_MEAN','GOODMAN_TENSION_ONLY'):
        raise ValueError('unknown mean-stress rule')
    cycles = rainflow(stress)
    if not cycles:
        raise ValueError('no nonzero rainflow cycles')
    out = [{'stress_range_MPa':r,'mean_stress_MPa':m,'cycles':n,
            'equivalent_range_MPa':corrected_range(r,m,meta)}
           for r,m,n in cycles]
    return {'status':'NUMERICAL_QC_ONLY_NOT_FATIGUE_LIFE',
            'source_sha256':sha,'material_id':meta['material_id'],
            'material_class':meta['material_class'],
            'stress_location':meta['stress_location'],
            'material_model_ref':meta['material_model_ref'],
            'mean_stress_rule':meta['mean_stress_rule'],
            'n_samples':len(ts),'dt_s':dt,'duration_s':ts[-1]-ts[0],
            'n_reversals':len(reversals(stress)),
            'counted_cycles':sum(c['cycles'] for c in out),
            'cycles':out,'N_allow_cycles':'NEED_MATERIAL_SPECIFIC_SOURCE',
            'miner_damage':'NOT_COMPUTED'}


def self_test():
    def signature(xs):
        return sorted((round(a,9),round(b,9),c) for a,b,c in rainflow(xs))
    base=[0,4,1,3,0]
    expected=[(2.,2.,1.),(4.,2.,.5),(4.,2.,.5)]
    assert signature(base)==sorted(expected),signature(base)
    assert signature([0,4,4,1,1,3,0])==sorted(expected)
    assert signature([v+100 for v in base])==sorted((r,m+100,n) for r,m,n in expected)
    assert signature([2*v for v in base])==sorted((2*r,2*m,n) for r,m,n in expected)
    assert sum(c[2] for c in rainflow([0,1,0]))==1.0
    steel={'material_class':'structural_steel','mean_stress_rule':'GOODMAN_TENSION_ONLY',
           'ultimate_tensile_MPa':500}
    assert abs(corrected_range(100,100,steel)-125)<1e-12
    assert corrected_range(100,-100,steel)==100
    assert corrected_range(100,100,dict(steel,mean_stress_rule='NONE_KEEP_MEAN'))==100
    bad_rules=[
        lambda:rainflow([1,1,1]),
        lambda:corrected_range(10,100,dict(steel,material_class='concrete')),
        lambda:corrected_range(10,500,steel),
        lambda:corrected_range(10,1,dict(steel,ultimate_tensile_MPa=-1)),
        lambda:corrected_range(10,1,dict(steel,mean_stress_rule='MYSTERY'))]
    for fn in bad_rules:
        try:fn()
        except ValueError:pass
        else:raise AssertionError('invalid rainflow/mean-stress accepted')
    raw=b'time_s,stress_MPa\n0,0\n1,4\n2,1\n3,3\n4,0\n'
    manifest={'source_sha256':hashlib.sha256(raw).hexdigest(),
              'stress_owner':'VERIFIED_LOCAL_MATERIAL_STRESS','material_id':'SYNTHETIC',
              'material_class':'structural_steel','stress_location':'TEST_NODE',
              'stress_component':'S11','material_model_ref':'SYNTHETIC_TEST_ONLY',
              'initial_state':'VERIFIED_GRAVITY_EFFECTIVE_PT_INCLUDED',
              'mean_stress_rule':'NONE_KEEP_MEAN'}
    result=calculate(raw,manifest)
    assert result['counted_cycles']==2.0 and result['n_reversals']==5
    bad_inputs=[
        (raw,dict(manifest,stress_owner='LOAD_DEL')),
        (raw,dict(manifest,source_sha256='0'*64)),
        (raw,dict(manifest,initial_state='UNVERIFIED')),
        (raw.replace(b'2,1',b'2.5,1'),manifest),
        (raw.replace(b'2,1',b'2,nan'),manifest),
        (raw.replace(b'2,1',b'1,1'),manifest),
        (raw,dict(manifest,material_class='concrete',mean_stress_rule='GOODMAN_TENSION_ONLY'))]
    for bad,meta in bad_inputs:
        if bad is not raw and meta['source_sha256']==manifest['source_sha256']:
            meta=dict(meta,source_sha256=hashlib.sha256(bad).hexdigest())
        try:calculate(bad,meta)
        except ValueError:pass
        else:raise AssertionError('invalid source/physics accepted')
    return {'status':'PASS_SYNTHETIC_ONLY','analytic_cycles':expected,
            'counted_cycles':result['counted_cycles'],
            'source_sha256':manifest['source_sha256'],
            'negative_tests':len(bad_rules)+len(bad_inputs),
            'real_local_stress_runs':0,'material_life_runs':0}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--input',type=Path)
    ap.add_argument('--manifest',type=Path)
    ap.add_argument('--output',type=Path)
    a=ap.parse_args()
    if a.self_test:
        print(json.dumps(self_test(),sort_keys=True))
    if a.input or a.manifest or a.output:
        if not a.input or not a.manifest or not a.output:
            ap.error('--input, --manifest, --output required together')
        result=calculate(a.input.read_bytes(),json.loads(a.manifest.read_text()))
        a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
        print('S10_RAINFLOW_QC_ONLY',len(result['cycles']))
    if not a.self_test and not a.input:
        ap.error('provide --self-test or --input/--manifest/--output')


if __name__=='__main__':main()
