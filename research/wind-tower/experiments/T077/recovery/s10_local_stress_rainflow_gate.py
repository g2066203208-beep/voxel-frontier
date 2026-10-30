#!/usr/bin/env python3
"""S10 local-stress rainflow and optional metal mean-stress transform.

ASTM E1049-style three-point stack; residual cycles are half cycles.
No local Abaqus stress, material S-N curves, annual damage or physical PASS.
Concrete retains range+mean. Steel Goodman is optional; REF023 Qu2026 PT
Goodman + Qu Eq(1) is opt-in SECONDARY METHOD ONLY; Paulson 1983 original\nA-1L and observed stress domains are checked independently, never design life.
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

# REF023 Qu et al., Buildings 2026 16(19):3854, open HTML section 2.2,
# Eqs (1)-(2). Paulson/Frank/Breen 1983 original report pp57-62 NOW READ.
# Original A-1L uses RAW stress range in ksi; Qu Goodman is NOT from Paulson.
# Neither Qu+Goodman nor the A-1L comparison is a validated tower design S-N.
PT_REF = 'REF023_QU2026_PT_EQ1_EQ2_PAULSON_SECONDARY'
PT_SOURCE = 'https://www.mdpi.com/2075-5309/16/19/3854'
PT_SCOPE = 'SECONDARY_METHOD_COMPARISON_ONLY'
PT_PRIMARY_SOURCE = 'https://library.ctr.utexas.edu/digitized/texasarchive/phase2/300-1-ctr.pdf'
PT_PRIMARY_REPORT = 'FHWA/TX-82/54+300-1'
KSI_TO_MPA = 6.894757293168361


def pt_paulson1983_primary_domain(raw_range_MPa, mean_MPa, qu_equivalent_MPa):
    """Paulson 1983 printed p57 Table5-2 and p62 Table5-5.

    Dataset A: 75<=Smin<=165 ksi, 22<=Sr<=81 ksi (391 tests).
    15.2mm-only dataset F: 50<=Smin<=97, 26<=Sr<=69 ksi (26 tests).
    A-1L: log10(N)=10.97-3.50*log10(raw Sr/ksi), NOT Goodman-corrected.
    Checking Qu's corrected range within A bounds is an EXTRA guard, not
    evidence that Paulson experimentally validated Qu's Goodman transform.
    """
    sr = raw_range_MPa / KSI_TO_MPA
    smin = (mean_MPa - raw_range_MPa / 2) / KSI_TO_MPA
    seq = qu_equivalent_MPa / KSI_TO_MPA
    if not all(math.isfinite(x) for x in (sr, smin, seq)):
        raise ValueError('PT_PAULSON_NONFINITE_STRESS')
    if not (75 <= smin <= 165 and 22 <= sr <= 81):
        raise ValueError('PT_PAULSON_A_DATASET_OUTSIDE_TESTED_DOMAIN')
    if not 22 <= seq <= 81:
        raise ValueError('PT_QU_GOODMAN_EQUIVALENT_OUTSIDE_PRIMARY_A_RANGE')
    return {
        'raw_range_ksi': sr,
        'minimum_stress_ksi': smin,
        'qu_equivalent_range_ksi': seq,
        'primary_A1L_log10_N_raw_range_only': 10.97 - 3.5 * math.log10(sr),
        'observed_15p2mm_subset_F_domain_match': (
            50 <= smin <= 97 and 26 <= sr <= 69),
        'primary_source_report': PT_PRIMARY_REPORT,
    }


def pt_qu2026_log10_cycles(equivalent_range_MPa):
    """Qu 2026 Eq(1): lg(N) = 13.95 - 3.5 lg(delta_sigma_G in MPa)."""
    x = float(equivalent_range_MPa)
    if not math.isfinite(x) or x <= 0:
        raise ValueError('PT_EQ1_INVALID_RANGE')
    log_n = 13.95 - 3.5 * math.log10(x)
    if not math.isfinite(log_n) or abs(log_n) > 100:
        raise ValueError('PT_EQ1_EXTRAPOLATION_OVERFLOW')
    return log_n


def pt_qu2026_corrected_range(rng, mean, meta):
    """Qu 2026 Eq(2), 1860 MPa strand ONLY, strictly method comparison."""
    if meta['material_class'] != 'prestressing_strand':
        raise ValueError('PT_MODEL_MATERIAL_MISMATCH')
    if (meta.get('material_model_ref') != PT_REF or
            meta.get('material_model_source_url') != PT_SOURCE or
            meta.get('model_scope') != PT_SCOPE):
        raise ValueError('PT_MODEL_SOURCE_SCOPE_NOT_LOCKED')
    su = float(meta.get('ultimate_tensile_MPa', 'nan'))
    if not math.isfinite(su) or abs(su - 1860.0) > 1e-9:
        raise ValueError('PT_1860_GRADE_UNVERIFIED_FOR_MODEL')
    if (not math.isfinite(rng) or not math.isfinite(mean) or rng <= 0 or
            mean <= rng / 2 or mean + rng / 2 >= su):
        raise ValueError('PT_CYCLE_OUTSIDE_POSITIVE_TENSION_BELOW_UTS')
    equivalent = rng / (1.0 - mean / su)
    pt_paulson1983_primary_domain(rng, mean, equivalent)
    return equivalent



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
    if rule == 'QU2026_PT_GOODMAN':
        return pt_qu2026_corrected_range(rng, mean, meta)
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
    if meta['mean_stress_rule'] not in (
            'NONE_KEEP_MEAN','GOODMAN_TENSION_ONLY','QU2026_PT_GOODMAN'):
        raise ValueError('unknown mean-stress rule')
    cycles = rainflow(stress)
    if not cycles:
        raise ValueError('no nonzero rainflow cycles')
    pt_method = meta['mean_stress_rule'] == 'QU2026_PT_GOODMAN'
    out = []
    for r,m,n in cycles:
        equiv = corrected_range(r,m,meta)
        row = {'stress_range_MPa':r,'mean_stress_MPa':m,'cycles':n,
               'equivalent_range_MPa':equiv}
        if pt_method:
            original = pt_paulson1983_primary_domain(r, m, equiv)
            row['paulson1983_primary_A1L_log10_N_raw_only'] = original[
                'primary_A1L_log10_N_raw_range_only']
            row['paulson1983_raw_range_ksi'] = original['raw_range_ksi']
            row['paulson1983_minimum_stress_ksi'] = original['minimum_stress_ksi']
            row['paulson1983_15p2mm_F_domain_match'] = original[
                'observed_15p2mm_subset_F_domain_match']
            log_n = pt_qu2026_log10_cycles(equiv)
            # Log-domain damage avoids overflow in N=10**logN.
            row['log10_N_allow_secondary_only'] = log_n
            row['sample_damage_secondary_only'] = n * 10**(-log_n)
        out.append(row)
    return {'status':'NUMERICAL_QC_ONLY_NOT_FATIGUE_LIFE',
            'source_sha256':sha,'material_id':meta['material_id'],
            'material_class':meta['material_class'],
            'stress_location':meta['stress_location'],
            'material_model_ref':meta['material_model_ref'],
            'mean_stress_rule':meta['mean_stress_rule'],
            'n_samples':len(ts),'dt_s':dt,'duration_s':ts[-1]-ts[0],
            'n_reversals':len(reversals(stress)),
            'counted_cycles':sum(c['cycles'] for c in out),
            'cycles':out,'N_allow_cycles':'NOT_APPROVED_FOR_DESIGN',
            'secondary_pt_sample_damage': (
                math.fsum(x['sample_damage_secondary_only'] for x in out)
                if pt_method else None),
            'secondary_pt_source': PT_SOURCE if pt_method else None,
            'secondary_pt_scope': PT_SCOPE if pt_method else None,
            'paulson1983_primary_source': PT_PRIMARY_SOURCE if pt_method else None,
            'paulson1983_primary_report': PT_PRIMARY_REPORT if pt_method else None,
            'paulson1983_goodman_validated_by_original': False,
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
    # Synthetic range=200 MPa, mean=930 MPa, Su=1860 MPa -> Qu
    # Goodman equivalent=400 MPa. Raw min=830 MPa, inside Paulson A
    # observed domain but OUTSIDE 15.2mm-only F minimum-stress domain.
    # Earlier 100 MPa synthetic example was below original A Sr lower bound.
    ptmeta = dict(manifest,material_class='prestressing_strand',
                  material_model_ref=PT_REF,material_model_source_url=PT_SOURCE,
                  model_scope=PT_SCOPE,ultimate_tensile_MPa=1860,
                  mean_stress_rule='QU2026_PT_GOODMAN')
    assert abs(pt_qu2026_corrected_range(200,930,ptmeta)-400)<1e-12
    expected_log_n = 13.95 - 3.5*math.log10(400)
    assert abs(pt_qu2026_log10_cycles(400)-expected_log_n)<1e-12
    original = pt_paulson1983_primary_domain(200,930,400)
    primary_log_n = 10.97 - 3.5*math.log10(200/KSI_TO_MPA)
    assert abs(original['primary_A1L_log10_N_raw_range_only']-primary_log_n)<1e-12
    assert not original['observed_15p2mm_subset_F_domain_match']
    assert abs(primary_log_n - (
        10.97+3.5*math.log10(KSI_TO_MPA)-3.5*math.log10(200)))<1e-12
    pt_raw=b'time_s,stress_MPa\n0,830\n1,1030\n2,830\n'
    ptmeta['source_sha256']=hashlib.sha256(pt_raw).hexdigest()
    ptresult=calculate(pt_raw,ptmeta)
    assert ptresult['counted_cycles']==1.0
    assert len(ptresult['cycles'])==2
    assert abs(ptresult['secondary_pt_sample_damage'] -
               10**(-expected_log_n)) < 1e-17
    assert ptresult['miner_damage']=='NOT_COMPUTED'
    pt_bad=[
        dict(ptmeta,material_class='concrete'),
        dict(ptmeta,material_model_ref='UNREVIEWED'),
        dict(ptmeta,model_scope='DESIGN_PASS'),
        dict(ptmeta,ultimate_tensile_MPa=1800),
        dict(ptmeta,material_model_source_url='UNKNOWN'),
    ]
    for bad in pt_bad:
        try:calculate(pt_raw,bad)
        except ValueError:pass
        else:raise AssertionError('invalid PT material/source accepted')
    pt_bad_cycles = [
        (100,40), (100,1810), (0,930), (200,float('nan')),
        (100,930), # raw range 14.5ksi below 22ksi primary A boundary
        (600,930), # raw range above 81ksi
        (200,600), # raw Smin below 75ksi
        (300,1500), # raw Smin above 165ksi
        (400,1300), # Qu equivalent range above 81ksi
    ]
    for badrange,badmean in pt_bad_cycles:
        try:pt_qu2026_corrected_range(badrange,badmean,ptmeta)
        except ValueError:pass
        else:raise AssertionError('invalid PT cycle accepted')
    return {'status':'PASS_SYNTHETIC_ONLY','analytic_cycles':expected,
            'pt_eq1_eq2_analytic_log10_N':expected_log_n,
            'pt_eq1_eq2_synthetic_sample_damage':ptresult['secondary_pt_sample_damage'],
            'pt_source_level':'PAULSON1983_PRIMARY_P57_P58_P62_READ_QU2026_GOODMAN_SECONDARY',
            'pt_paulson_primary_A1L_log10_N_raw_only':primary_log_n,
            'pt_paulson_15p2mm_subset_domain_match':False,
            'pt_negative_tests':len(pt_bad)+len(pt_bad_cycles),
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
