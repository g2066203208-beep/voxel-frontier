#!/usr/bin/env python3
"""S10 conditional Miner accumulator for VERIFIED LOCAL STRESS only.

Inputs are stress-cycle bins with externally supplied, material-specific N_allow.
No built-in S-N/mean-stress model; no load-DEL conversion; no physical PASS.
Annual damage = 8760*3600 * sum_b p_unconditional,b * mean_seeds(D_sample / duration_s).
If probabilities are conditional on operation, multiply by explicit operating_fraction.
The 2026-10-31 ERA5 source uses p_unconditional=n_bin/184080, with p_op=106900/184080.
Never multiply p_unconditional by operating hours again; never assume p_op=1.
Each bin probability is time fraction; seed runs must cover the same duration
within a bin. The predeclared expected_seeds_per_bin is checked against actual
unique seed IDs to reject silent incomplete sampling; it is NOT a convergence
or statistical sufficiency claim. Use --self-test for synthetic known answers.
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
          'expected_seeds_per_bin','stress_range_MPa','mean_stress_MPa','cycles','N_allow_cycles',
          'stress_owner','material_model_ref','stress_source_sha256',
          'model_branch','initial_state_sha256')
SECONDS_PER_YEAR = 8760 * 3600
ERA5_31BIN_SHA256 = 'e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102'


def validate_era5_probability_source(raw):
    """Check the actual 2005-2025 ERA5-derived 31-bin table; no life calculation."""
    digest = hashlib.sha256(raw).hexdigest()
    if digest != ERA5_31BIN_SHA256:
        raise ValueError('ERA5_31BIN_SOURCE_SHA_MISMATCH')
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    if len(rows) != 31:
        raise ValueError('ERA5_31BIN_ROW_COUNT')
    n_total = sum(int(r['hours']) for r in rows)
    n_op = sum(int(r['hours']) for r in rows if 4 <= int(r['bin_lower_mps']) < 25)
    if n_total != 184080 or n_op != 106900:
        raise ValueError('ERA5_31BIN_HOURS_MISMATCH')
    for i, r in enumerate(rows):
        if int(r['bin_lower_mps']) != i or (r['bin_upper_mps_exclusive'] != ('INF' if i == 30 else str(i + 1))):
            raise ValueError('ERA5_31BIN_ORDER_MISMATCH')
        p = float(r['p_all_hours'])
        q = float(r['p_conditional_4_to_25'])
        if abs(p-int(r['hours'])/n_total)>1e-12:
            raise ValueError('ERA5_UNCONDITIONAL_PROBABILITY_MISMATCH')
        expected = int(r['hours'])/n_op if 4 <= i < 25 else 0.0
        if abs(q-expected)>1e-12:
            raise ValueError('ERA5_CONDITIONAL_PROBABILITY_MISMATCH')
    return {'source_sha256':digest,'hours_total':n_total,'hours_operating':n_op,
            'operating_fraction':n_op/n_total,
            'conditional_overestimate_factor_if_8760h':n_total/n_op,
            'status':'REAL_ERA5_PROBABILITY_IDENTITY_QC_NOT_MATERIAL_DAMAGE'}


def _positive(v, name, allow_zero=False):
    x = float(v)
    if not math.isfinite(x) or (x < 0 if allow_zero else x <= 0):
        raise ValueError('invalid '+name)
    return x


def calculate(raw, years=20.0, operating_fraction=None, probability_basis='conditional'):
    years = _positive(years, 'years')
    if operating_fraction is None:
        raise ValueError('explicit operating_fraction required: do not assume 8760 operating hours')
    operating_fraction = _positive(operating_fraction, 'operating_fraction')
    if operating_fraction > 1:
        raise ValueError('operating_fraction exceeds 1')
    if probability_basis not in ('conditional', 'unconditional'):
        raise ValueError('probability_basis must be conditional or unconditional')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if reader.fieldnames is None or set(reader.fieldnames) != set(FIELDS):
        raise ValueError('required cycle input columns missing or unexpected')
    rows = list(reader)
    if not rows:
        raise ValueError('empty cycle data')
    samples = defaultdict(float)
    settings = {}
    probabilities = {}
    expected_seed_counts = {}
    material_models = {}
    material_branches = {}
    material_initial_states = {}
    global_branches = set()
    global_initial_states = set()
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
        branch = row['model_branch'].strip()
        if branch not in ('BF1_CURRENT','BF8_CODE_DESIGN'):
            raise ValueError('invalid or missing model_branch')
        initial_state_sha = row['initial_state_sha256'].strip().lower()
        if len(initial_state_sha) != 64 or any(c not in '0123456789abcdef' for c in initial_state_sha):
            raise ValueError('invalid initial_state_sha256')
        if material in material_branches and material_branches[material] != branch:
            raise ValueError('mixed BF1/BF8 model branches')
        if material in material_initial_states and material_initial_states[material] != initial_state_sha:
            raise ValueError('mixed initial state provenance for material')
        material_branches[material] = branch
        material_initial_states[material] = initial_state_sha
        global_branches.add(branch)
        global_initial_states.add(initial_state_sha)
        p = _positive(row['bin_probability'], 'bin_probability')
        if p > 1:
            raise ValueError('probability exceeds 1')
        duration = _positive(row['duration_s'], 'duration_s')
        declared = row['expected_seeds_per_bin'].strip()
        if not declared.isascii() or not declared.isdecimal() or not 1 <= int(declared) <= 10000:
            raise ValueError('invalid predeclared expected_seeds_per_bin')
        expected_seeds = int(declared)
        rng = _positive(row['stress_range_MPa'], 'stress_range_MPa', True)
        mean = float(row['mean_stress_MPa'])
        if not math.isfinite(mean):
            raise ValueError('invalid mean stress')
        count = _positive(row['cycles'], 'cycles', True)
        nallow = _positive(row['N_allow_cycles'], 'N_allow_cycles')
        key = (material,bin_id,seed)
        meta = (p,duration,sha,model,expected_seeds,branch,initial_state_sha)
        if key in settings and settings[key] != meta:
            raise ValueError('inconsistent seed metadata')
        settings[key] = meta
        if (material,bin_id) in probabilities and probabilities[material,bin_id] != p:
            raise ValueError('inconsistent bin probability across seeds')
        probabilities[material,bin_id] = p
        if ((material,bin_id) in expected_seed_counts and
                expected_seed_counts[material,bin_id] != expected_seeds):
            raise ValueError('inconsistent expected seed count within bin')
        expected_seed_counts[material,bin_id] = expected_seeds
        if material in material_models and material_models[material] != model:
            raise ValueError('mixed material fatigue models')
        material_models[material] = model
        # Exact duplicate cycle rows are rejected; aggregate identical cycles first.
        identity = (key,rng,mean,count,nallow)
        if identity in seen:
            raise ValueError('duplicate cycle record')
        seen.add(identity)
        samples[key] += count/nallow
    if len(global_branches) != 1 or len(global_initial_states) != 1:
        raise ValueError('mixed model branch or initial PT/gravity state across materials')
    out = []
    for material in sorted(material_models):
        bins = sorted({b for (m,b) in probabilities if m == material})
        p_sum = sum(probabilities[material,b] for b in bins)
        expected_probability = 1.0 if probability_basis == 'conditional' else operating_fraction
        if abs(p_sum - expected_probability) > 1e-8:
            raise ValueError(f'incomplete or double-counted {probability_basis} bin probabilities for {material}: {p_sum}, expected {expected_probability}')
        annual = 0.0
        seed_sampling_annual_variance = 0.0
        seed_sampling_estimable = True
        bin_breakdown = []
        for b in bins:
            keys = sorted(k for k in samples if k[0] == material and k[1] == b)
            declared_count = expected_seed_counts[material,b]
            if len(keys) != declared_count:
                raise ValueError('missing or excess seed in bin: '+material+'/'+b)
            durations = {settings[k][1] for k in keys}
            if len(durations) != 1:
                raise ValueError('seed duration mismatch')
            duration_s = next(iter(durations))
            rates = [samples[k]/duration_s for k in keys]
            per_second = sum(rates)/len(rates)
            # Sample variance (ddof=1) of INDEPENDENT seed damage rates.
            # This is Monte Carlo seed-sampling error only, NOT wind climate,
            # material S-N, stress-model, mesh or lifetime uncertainty.
            # n=1 is NOT a zero-variance estimate; keep SE unavailable.
            n_seed = len(rates)
            if n_seed >= 2:
                sample_var = math.fsum((x-per_second)**2 for x in rates)/(n_seed-1)
                mean_rate_se = math.sqrt(sample_var/n_seed)
                seed_cv = math.sqrt(sample_var)/per_second if per_second > 0 else (
                    0.0 if sample_var == 0 else None)
            else:
                sample_var = None
                mean_rate_se = None
                seed_cv = None
                seed_sampling_estimable = False
            # Conditional P(bin|operating) needs p_op; unconditional P(bin) does not.
            annual_weight = operating_fraction if probability_basis == 'conditional' else 1.0
            contribution = probabilities[material,b] * annual_weight * per_second * SECONDS_PER_YEAR
            annual += contribution
            weight_annual = probabilities[material,b] * annual_weight * SECONDS_PER_YEAR
            contribution_se = (weight_annual*mean_rate_se
                               if mean_rate_se is not None else None)
            if contribution_se is not None:
                seed_sampling_annual_variance += contribution_se**2
            bin_breakdown.append({
                'bin_id':b,'probability':probabilities[material,b],
                'expected_seeds':declared_count,'observed_seeds':len(keys),
                'duration_s':duration_s,'mean_damage_per_second':per_second,
                'min_seed_damage_per_second':min(rates),
                'max_seed_damage_per_second':max(rates),
                'seed_rate_sample_variance_per_second_squared':sample_var,
                'seed_mean_rate_standard_error_per_second':mean_rate_se,
                'seed_rate_coefficient_of_variation':seed_cv,
                'annual_contribution_standard_error_seed_sampling':contribution_se,
                'seed_sampling_estimable':n_seed >= 2,
                'annual_damage_contribution_conditional':contribution,
                'annual_damage_contribution':contribution})
        # Independent seed realizations across wind bins are assumed.
        # If any populated bin has only one seed, total uncertainty is
        # NOT ESTIMABLE; do not silently treat its variance as zero.
        annual_se = (math.sqrt(seed_sampling_annual_variance)
                     if seed_sampling_estimable else None)
        relative_se = (annual_se/annual if annual > 0 else None) if annual_se is not None else None
        out.append({'material_id':material,'material_model_ref':material_models[material],
                    'model_branch':material_branches[material],
                    'initial_state_sha256':material_initial_states[material],
                    'bin_count':len(bins),'bin_breakdown':bin_breakdown,
                    'annual_damage_conditional':annual,  # deprecated field name; corrected value
                    'annual_damage':annual,'probability_basis':probability_basis,
                    'operating_fraction':operating_fraction,
                    'design_years':years,'design_damage_conditional':annual*years,
                    'design_damage':annual*years,
                    'annual_damage_seed_sampling_standard_error':annual_se,
                    'annual_damage_seed_sampling_relative_standard_error':relative_se,
                    'design_damage_seed_sampling_standard_error':(
                        years*annual_se if annual_se is not None else None),
                    'annual_damage_seed_sampling_variance':(
                        seed_sampling_annual_variance if seed_sampling_estimable else None),
                    'seed_sampling_uncertainty_status':(
                        'ESTIMABLE_CONDITIONAL_INDEPENDENT_SEEDS_NOT_PHYSICAL_CI'
                        if seed_sampling_estimable else 'NOT_ESTIMABLE_BIN_WITH_N_LT_2'),
                    'seed_sampling_uncertainty_scope':(
                        'Independent equal-duration seeds within and across bins; '
                        'fixed wind probabilities, operating fraction and material law; '
                        'sample-variance SE only, no confidence interval or physical uncertainty'),
                    'status':'CONDITIONAL_NO_PHYSICAL_PASS'})
    return {'source_sha256':hashlib.sha256(raw).hexdigest(),'input_schema_version':4,
            'probability_basis':probability_basis,'operating_fraction':operating_fraction,
            'row_count':len(rows),
            'seconds_per_year':SECONDS_PER_YEAR,'results':out}


def selftest(probability_source=None):
    # Two bins p=.25/.75, two 100-second seeds each; synthetic Dsample 0.001/0.002/0.003/0.005.
    base = dict(material_id='SYNTH_STEEL',duration_s='100',expected_seeds_per_bin='2',
                stress_range_MPa='10',mean_stress_MPa='5',N_allow_cycles='1000',
                stress_owner='VERIFIED_LOCAL_MATERIAL_STRESS',
                material_model_ref='SYNTHETIC_TEST_ONLY',stress_source_sha256='a'*64,
                model_branch='BF1_CURRENT',initial_state_sha256='b'*64)
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
    # Conditional bin weights .25/.75, but only half the hours are operating.
    result=calculate(encode(rows),years=20,operating_fraction=.5)
    expected=.5*SECONDS_PER_YEAR*(.25*.0015/100 + .75*.004/100)
    legacy=calculate(encode(rows),years=20,operating_fraction=1)
    assert abs(legacy['results'][0]['annual_damage']-2*expected)<1e-10
    # Unconditional p_bin=.125/.375 must give the SAME annual damage.
    raw_unconditional=encode([dict(r,bin_probability=str(float(r['bin_probability'])*.5)) for r in rows])
    uncond=calculate(raw_unconditional,years=20,operating_fraction=.5,probability_basis='unconditional')
    assert abs(uncond['results'][0]['annual_damage']-expected)<1e-10
    assert abs(result['results'][0]['annual_damage']-uncond['results'][0]['annual_damage'])<1e-10
    assert abs(result['results'][0]['annual_damage_conditional']-expected)<1e-10
    assert abs(result['results'][0]['design_damage_conditional']-20*expected)<1e-8
    # Independent analytical oracle: B1 seed rates 1e-5,2e-5;
    # B2 seed rates 3e-5,5e-5. Sample SE(mean) = 5e-6,1e-5.
    # Annual SE = 8760*3600*.5*sqrt((.25*5e-6)^2+(.75*1e-5)^2).
    oracle_se=.5*SECONDS_PER_YEAR*math.sqrt((.25*5e-6)**2+(.75*1e-5)**2)
    x=result['results'][0]
    assert math.isclose(x['annual_damage_seed_sampling_standard_error'],oracle_se,rel_tol=1e-12)
    assert math.isclose(x['design_damage_seed_sampling_standard_error'],20*oracle_se,rel_tol=1e-12)
    assert math.isclose(uncond['results'][0]['annual_damage_seed_sampling_standard_error'],oracle_se,rel_tol=1e-12)
    assert x['seed_sampling_uncertainty_status'].startswith('ESTIMABLE_')
    # A bin with only one seed has unknown sampling variance, not zero.
    single=[dict(r,expected_seeds_per_bin=('1' if r['bin_id']=='B2' else '2'))
            for r in rows if not (r['bin_id']=='B2' and r['seed_id']=='S2')]
    one=calculate(encode(single),operating_fraction=.5)['results'][0]
    assert one['annual_damage_seed_sampling_standard_error'] is None
    assert one['design_damage_seed_sampling_standard_error'] is None
    assert one['seed_sampling_uncertainty_status']=='NOT_ESTIMABLE_BIN_WITH_N_LT_2'
    assert one['bin_breakdown'][1]['annual_contribution_standard_error_seed_sampling'] is None
    # Identical seed rates genuinely have zero estimated sampling spread.
    same=[dict(r,cycles=('1' if r['bin_id']=='B1' else '3')) for r in rows]
    equal=calculate(encode(same),operating_fraction=.5)['results'][0]
    assert equal['annual_damage_seed_sampling_standard_error']==0
    breakdown = result['results'][0]['bin_breakdown']
    assert len(breakdown) == 2
    assert [b['observed_seeds'] for b in breakdown] == [2,2]
    assert abs(sum(b['annual_damage_contribution_conditional'] for b in breakdown)-expected)<1e-10
    assert abs(breakdown[0]['min_seed_damage_per_second']-.00001)<1e-14
    assert abs(breakdown[1]['max_seed_damage_per_second']-.00005)<1e-14
    tests=[dict(rows[0],stress_owner='LOAD_DEL'),
           dict(rows[0],stress_source_sha256='UNKNOWN'),
           dict(rows[0],N_allow_cycles='0'),
           dict(rows[0],model_branch='UNIDENTIFIED'),
           dict(rows[0],initial_state_sha256='UNKNOWN')]
    for altered in tests:
        try: calculate(encode([altered]+rows[1:]),operating_fraction=.5)
        except ValueError: pass
        else: raise AssertionError('invalid stress input accepted')
    try: calculate(encode(rows+rows[:1]),operating_fraction=.5)
    except ValueError: pass
    else: raise AssertionError('duplicate cycles accepted')
    try: calculate(encode([dict(r,bin_probability='0.2') if r['bin_id']=='B1' else r for r in rows]),operating_fraction=.5)
    except ValueError: pass
    else: raise AssertionError('incomplete bin probability accepted')
    try: calculate(encode([dict(rows[0],duration_s='99')]+rows[1:]),operating_fraction=.5)
    except ValueError: pass
    else: raise AssertionError('different seed durations accepted')
    # Previously this missing-seed case was silently averaged as one seed,
    # even though the intended wind-bin sampling had two seeds.
    new_bad = [
        rows[:-1],
        [dict(r,expected_seeds_per_bin='3') if r['bin_id']=='B1' and r['seed_id']=='S1' else r for r in rows],
        [dict(r,expected_seeds_per_bin='3') if r['bin_id']=='B1' else r for r in rows],
        [dict(r,expected_seeds_per_bin='0') if r['bin_id']=='B1' else r for r in rows],
        [dict(r,expected_seeds_per_bin='2.0') if r['bin_id']=='B1' else r for r in rows],
    ]
    for i, bad in enumerate(new_bad):
        try: calculate(encode(bad),operating_fraction=.5)
        except ValueError: pass
        else: raise AssertionError('incomplete or invalid seed contract accepted: %d' % i)
    for args in ({}, {'operating_fraction':0}, {'operating_fraction':1.1},
                 {'operating_fraction':.5,'probability_basis':'invalid'},
                 {'operating_fraction':.5,'probability_basis':'unconditional'}):
        try: calculate(encode(rows),**args)
        except ValueError: pass
        else: raise AssertionError('missing/mismatched operating probability contract accepted')
    source_check = (validate_era5_probability_source(probability_source)
                    if probability_source is not None else None)
    return {'status':'PASS_SYNTHETIC_ONLY','annual_expected':expected,
            'design_20y_expected':20*expected,'negative_tests':13,
            'seed_contract_tests':5,'bin_contribution_checks':4,
            'probability_contract_negative_tests':5,
            'conditional_unconditional_equivalence':True,'operating_fraction':.5,
            'seed_sampling_analytic_standard_error':oracle_se,
            'seed_sampling_analytic_standard_error_match':True,
            'single_seed_uncertainty_not_estimable':True,
            'identical_seed_zero_variance':True,
            'real_era5_probability_qc':source_check}



def integration_selftest():
    """End-to-end SYNTHETIC stress history -> existing rainflow -> Miner.

    This fixture explicitly impersonates the manifest labels required by the
    two separate gates. It NEVER authenticates an ODB, material law or design
    S-N curve. No real stress may enter via this self-test.
    """
    import s10_local_stress_rainflow_gate as rf

    scales = {'concrete':100000.0, 'ordinary_rebar':200000.0,
              'prestressing_strand':400000.0, 'structural_steel':800000.0}
    basen = {2:100.0, 4:200.0, 6:300.0}
    rows, source_hashes, cycle_counts = [], [], {}
    raw_by_key = {}
    for cls, scale in scales.items():
        material = 'SYNTH_' + cls.upper()
        model = 'SYNTHETIC_' + cls.upper() + '_TEST_ONLY'
        for bin_id, p, base in [('B1', .25, [0,4,1,3,0]),
                                ('B2', .75, [0,6,0])]:
            for seed, offset in [('S01',0),('S02',10)]:
                duration = 4.0
                raw = ('time_s,stress_MPa\n' + ''.join(
                    f'{i*duration/(len(base)-1):g},{v+offset:g}\n'
                    for i,v in enumerate(base))).encode('utf-8')
                sha = hashlib.sha256(raw).hexdigest()
                meta = {'source_sha256':sha,
                        'stress_owner':'VERIFIED_LOCAL_MATERIAL_STRESS',
                        'material_id':material, 'material_class':cls,
                        'stress_location':'SYNTHETIC_FIXTURE_ONLY',
                        'stress_component':'S11',
                        'material_model_ref':model,
                        'initial_state':'VERIFIED_GRAVITY_EFFECTIVE_PT_INCLUDED',
                        'mean_stress_rule':'NONE_KEEP_MEAN'}
                ledger = rf.calculate(raw, meta)
                assert ledger['source_sha256']==sha
                assert abs(ledger['duration_s']-duration)<1e-12
                # Miner rejects exact duplicate rows. Merge identical
                # half-cycles while preserving range AND mean stress.
                grouped = defaultdict(float)
                for c in ledger['cycles']:
                    r,m,n = c['stress_range_MPa'],c['mean_stress_MPa'],c['cycles']
                    assert r in basen and math.isfinite(m)
                    grouped[(r,m)] += n
                assert len(grouped)==(2 if bin_id=='B1' else 1)
                assert abs(sum(grouped.values())-(2 if bin_id=='B1' else 1))<1e-12
                cycle_counts[material+'/'+bin_id+'/'+seed] = sum(grouped.values())
                source_hashes.append(sha)
                raw_by_key[cls,bin_id,seed] = (raw,meta)
                for (rng,mean),count in sorted(grouped.items()):
                    # Purely synthetic, independent known-answer lookup;
                    # distinct per material and sensitive to cycle mean.
                    n_allow = scale*basen[int(rng)]/(1+mean/100)
                    rows.append({'material_id':material,'bin_id':bin_id,
                        'seed_id':seed,'bin_probability':str(p),
                        'duration_s':str(duration),'expected_seeds_per_bin':'2',
                        'stress_range_MPa':str(rng),'mean_stress_MPa':str(mean),
                        'cycles':str(count),'N_allow_cycles':str(n_allow),
                        'stress_owner':'VERIFIED_LOCAL_MATERIAL_STRESS',
                        'material_model_ref':model,'stress_source_sha256':sha,
                         'model_branch':'BF1_CURRENT',
                         'initial_state_sha256':'b'*64})

    def encode(items):
        out = io.StringIO(newline='')
        writer = csv.DictWriter(out,fieldnames=FIELDS,lineterminator='\n')
        writer.writeheader()
        writer.writerows(items)
        return out.getvalue().encode('utf-8')

    raw_cycles = encode(rows)
    conditional = calculate(raw_cycles,years=20,operating_fraction=.5)
    uncond_rows = [dict(r,bin_probability=str(float(r['bin_probability'])*.5))
                   for r in rows]
    unconditional = calculate(encode(uncond_rows),years=20,
                              operating_fraction=.5,probability_basis='unconditional')
    expected, measured = {}, {}
    for cls,scale in scales.items():
        material = 'SYNTH_'+cls.upper()
        # Independent oracle: bin1 per-seed damage .0153/.0168 per scale;
        # bin2 .003433333333/.003766666667 per scale. Each run lasts 4 s.
        analytic = .5*SECONDS_PER_YEAR*(.25*.01605/4+.75*.0036/4)/scale
        expected[material]=analytic
    for x,y in zip(conditional['results'],unconditional['results']):
        assert x['material_id']==y['material_id']
        m=x['material_id']
        assert abs(x['annual_damage']-expected[m])<=1e-10*max(1,expected[m])
        assert abs(y['annual_damage']-expected[m])<=1e-10*max(1,expected[m])
        assert abs(x['design_damage']-20*expected[m])<=1e-9*max(1,expected[m])
        measured[m]=x['annual_damage']
    assert len(measured)==4 and len(rows)==24
    assert len(source_hashes)==16
    assert all(n==2 for k,n in cycle_counts.items() if '/B1/' in k)
    assert all(n==1 for k,n in cycle_counts.items() if '/B2/' in k)

    negative_tests=0
    def reject(fn, error):
        nonlocal negative_tests
        try:
            fn()
        except ValueError as exc:
            if error not in str(exc):
                raise AssertionError('unexpected rejection: '+str(exc))
            negative_tests+=1
        else:
            raise AssertionError('unsafe S10 synthetic bridge input accepted: '+error)

    src,meta=raw_by_key['concrete','B1','S01']
    reject(lambda:rf.calculate(src,dict(meta,source_sha256='0'*64)),
           'SHA256 mismatch')
    reject(lambda:rf.calculate(src,dict(meta,stress_owner='LOAD_DEL')),
           'unverified stress')
    reject(lambda:rf.calculate(src,dict(meta,initial_state='P0_ONLY')),
           'mean state not verified')
    reject(lambda:calculate(encode([dict(r,stress_owner='LOAD_DEL')
           if i==0 else r for i,r in enumerate(rows)]),
           operating_fraction=.5), 'unverified stress')
    reject(lambda:calculate(encode([dict(r,N_allow_cycles='0')
           if i==0 else r for i,r in enumerate(rows)]),
           operating_fraction=.5), 'N_allow_cycles')
    reject(lambda:calculate(encode(rows+[rows[0]]),operating_fraction=.5),
           'duplicate cycle')
    reject(lambda:calculate(encode([dict(r,bin_probability='.3')
           if r['bin_id']=='B1' else r for r in rows]),
           operating_fraction=.5), 'incomplete')
    reject(lambda:calculate(encode(rows[:-1]),operating_fraction=.5),
           'missing or excess seed')
    reject(lambda:calculate(encode([dict(r,material_model_ref='WRONG_MODEL')
           if i==0 else r for i,r in enumerate(rows)]),
           operating_fraction=.5), 'inconsistent seed metadata')
    reject(lambda:calculate(encode([dict(r,material_model_ref='WRONG_MODEL')
           if r['material_id']=='SYNTH_CONCRETE' and r['seed_id']=='S01'
           else r for r in rows]),operating_fraction=.5), 'mixed material')
    reject(lambda:calculate(encode([dict(r,model_branch='BF8_CODE_DESIGN')
            if i==0 else r for i,r in enumerate(rows)]),
            operating_fraction=.5), 'mixed BF1/BF8')
    reject(lambda:calculate(encode([dict(r,initial_state_sha256='c'*64)
            if i==0 else r for i,r in enumerate(rows)]),
            operating_fraction=.5), 'mixed initial state')
    reject(lambda:calculate(raw_cycles), 'operating_fraction required')

    return {'status':'PASS_SYNTHETIC_END_TO_END_ONLY',
            'material_classes':list(scales),'source_histories':len(source_hashes),
            'source_history_sha256':sorted(set(source_hashes)),
            'rainflow_merged_rows':len(rows),'negative_tests':negative_tests,
            'operating_fraction':.5,'conditional_unconditional_equal':True,
            'synthetic_annual_damage':measured,'analytic_annual_damage':expected,
            'synthetic_cycle_csv_sha256':hashlib.sha256(raw_cycles).hexdigest(),
            'local_material_stress_runs':0,'native_Abaqus_runs':0,
            'physical_pass':False,'material_life':None}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--integration-self-test',action='store_true')
    ap.add_argument('--wind-bin-source',type=Path,
                    help='optional SHA-locked actual 31-bin ERA5 source for self-test QC')
    ap.add_argument('--input',type=Path)
    ap.add_argument('--years',type=float,default=20)
    ap.add_argument('--operating-fraction',type=float,
                    help='P(operating) from the SAME wind probability source; required for --input')
    ap.add_argument('--probability-basis',choices=('conditional','unconditional'),default='conditional')
    ap.add_argument('--output',type=Path)
    a=ap.parse_args()
    if a.integration_self_test:
        print(json.dumps(integration_selftest(),sort_keys=True))
    if a.self_test:
        print(json.dumps(selftest(a.wind_bin_source.read_bytes()
                                 if a.wind_bin_source else None),sort_keys=True))
    if a.input:
        result=calculate(a.input.read_bytes(),a.years,
                         operating_fraction=a.operating_fraction,
                         probability_basis=a.probability_basis)
        data=json.dumps(result,sort_keys=True,indent=2)+'\n'
        if a.output: a.output.write_text(data,encoding='utf-8')
        else: print(data)
    if not a.self_test and not a.integration_self_test and not a.input:
        ap.error('provide --self-test, --integration-self-test or --input')


if __name__=='__main__': main()
