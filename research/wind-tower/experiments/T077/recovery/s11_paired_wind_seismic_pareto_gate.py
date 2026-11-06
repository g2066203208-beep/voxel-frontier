#!/usr/bin/env python3
"""S11 paired wind-only vs seismic-constrained Pareto screening, not a solver.

A single evaluated candidate table is reused for both fronts; the objectives
(mass and maximum of three material-specific wind fatigue damage ratios) are
IDENTICAL in the two comparisons. The only change is the verified seismic
feasibility gate. A previously wind-dominated design can enter the constrained
front when its dominator fails seismic constraints.

Production input must be independently reviewed NATIVE_VERIFIED W/E/WE, wind
fatigue and baseline records; SHA strings are identifiers, not proof of truth.
No synthetic example can be loaded through the production CLI.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

FIELDS = ('design_id','state_id','baseline_id','mass_t','baseline_mass_t',
          'D_concrete','D_PT','D_steel','D0_concrete','D0_PT','D0_steel',
          'wind_gate','seismic_gate','evidence_level',
          'W_run_sha256','E_run_sha256','WE_run_sha256','fatigue_run_sha256')
GATES = {'PASS','FAIL','UNKNOWN'}


def sha_ok(x):
    return len(x)==64 and all(c in '0123456789abcdef' for c in x)


def numeric(x, name, positive=False):
    try: v=float(x)
    except (ValueError,TypeError): raise ValueError('INVALID_NUMBER:'+name)
    if not math.isfinite(v) or v<0 or (positive and v==0):
        raise ValueError('INVALID_NUMBER:'+name)
    return v


def dominates(a,b):
    # No arbitrary tolerance: an engineering uncertainty budget must be
    # established from native V&V before physical Pareto interpretation.
    return (a['mass_ratio']<=b['mass_ratio'] and
            a['max_fatigue_ratio']<=b['max_fatigue_ratio'] and
            (a['mass_ratio']<b['mass_ratio'] or
             a['max_fatigue_ratio']<b['max_fatigue_ratio']))


def front(candidates):
    return sorted([a['design_id'] for a in candidates if not any(
        dominates(b,a) for b in candidates if b['design_id']!=a['design_id'])])


def calculate(raw, synthetic=False, uncertainty=None):
    reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if reader.fieldnames is None or tuple(reader.fieldnames)!=FIELDS:
        raise ValueError('COLUMNS_MISMATCH')
    rows=list(reader)
    if len(rows)<2: raise ValueError('INSUFFICIENT_CANDIDATES')
    ids=set(); baseline_ids=set(); states=set(); parsed=[]; baseline_values=set()
    for r in rows:
        d=r['design_id'].strip(); baseline=r['baseline_id'].strip()
        state=r['state_id'].strip()
        if not d or not baseline or not state or d in ids:
            raise ValueError('DUPLICATE_OR_MISSING_ID')
        ids.add(d);baseline_ids.add(baseline);states.add(state)
        if r['wind_gate'] not in GATES or r['seismic_gate'] not in GATES:
            raise ValueError('INVALID_GATE')
        if synthetic:
            if r['evidence_level']!='SYNTHETIC_TEST_ONLY':
                raise ValueError('SYNTHETIC_TEST_LEVEL_MISMATCH')
        else:
            if r['evidence_level']!='NATIVE_VERIFIED':
                raise ValueError('NO_NATIVE_EVIDENCE')
            if not all(sha_ok(r[k]) for k in FIELDS[-4:]):
                raise ValueError('MISSING_RUN_SHA256')
        m=numeric(r['mass_t'],'mass_t',True)
        m0=numeric(r['baseline_mass_t'],'baseline_mass_t',True)
        Ds=[numeric(r['D_'+k],'D_'+k) for k in ('concrete','PT','steel')]
        D0=[numeric(r['D0_'+k],'D0_'+k,True) for k in ('concrete','PT','steel')]
        baseline_values.add((m0,*D0))
        parsed.append({'design_id':d,'mass_ratio':m/m0,
                       'max_fatigue_ratio':max(dv/ref for dv,ref in zip(Ds,D0)),
                       'wind_gate':r['wind_gate'],'seismic_gate':r['seismic_gate'],
                       'material_ratios':dict(zip(('concrete','PT','steel'),
                                                   (dv/ref for dv,ref in zip(Ds,D0))))})
    if len(baseline_ids)!=1 or len(states)!=1 or len(baseline_values)!=1:
        raise ValueError('UNPAIRED_BASELINE_OR_OPERATING_STATE')
    baseline=next(iter(baseline_ids))
    if baseline not in ids: raise ValueError('BASELINE_NOT_IN_CANDIDATES')
    base=next(x for x in parsed if x['design_id']==baseline)
    if base['mass_ratio']!=1 or base['max_fatigue_ratio']!=1 or any(
            v!=1 for v in base['material_ratios'].values()):
        raise ValueError('BASELINE_SELF_IDENTITY_MISMATCH')
    wind=[r for r in parsed if r['wind_gate']=='PASS']
    joint=[r for r in wind if r['seismic_gate']=='PASS']
    wf=front(wind); sf=front(joint)
    result={'status':'SYNTHETIC_ALGORITHM_QC_ONLY' if synthetic else
            'PROVISIONAL_NEEDS_INDEPENDENT_NATIVE_REVIEW',
            'input_sha256':hashlib.sha256(raw).hexdigest(),
            'n_designs':len(parsed),'operating_state':next(iter(states)),
            'baseline_id':baseline,'wind_feasible':len(wind),
            'seismic_constrained_feasible':len(joint),
            'unknown_wind':sum(x['wind_gate']=='UNKNOWN' for x in parsed),
            'unknown_seismic':sum(x['seismic_gate']=='UNKNOWN' for x in wind),
            'wind_pareto':wf,'seismic_constrained_pareto':sf,
            'removed_from_front':sorted(set(wf)-set(sf)),
            'new_entrants_to_front':sorted(set(sf)-set(wf)),
            'objectives':'SAME mass/M0 and max(D_concrete/D0, D_PT/D0, D_steel/D0)',
            'caveat':'Not an optimization or a seismic/fatigue physical PASS; no uncertainty tolerance frozen.'}
    result['interval_pareto']=(interval_pareto(parsed,baseline,next(iter(states)),uncertainty,synthetic)
                               if uncertainty is not None else {'status':'NOT_EVALUATED_NO_QOI_BUDGET'})
    return result



def interval_pareto(parsed, baseline_id, state_id, budget, synthetic):
    """Conservative interval Pareto bracketing, not an optimization result.

    For independent axis-aligned intervals, upper(A)<=lower(B) in both
    objectives is a SUFFICIENT certificate that A dominates B for all
    realizations. lower(A)<=upper(B) with a strict inequality is only a
    POSSIBLE dominance relation. Hence core is a conservative subset and
    outer is a conservative superset of any realized Pareto front.
    Correlation and common baseline uncertainty are NOT modeled.
    """
    required={'schema_version','baseline_id','state_id','evidence_level',
              'budget_source_sha256','bounds'}
    if not isinstance(budget,dict) or set(budget)!=required:
        raise ValueError('UNCERTAINTY_SCHEMA_MISMATCH')
    if budget['schema_version']!=1 or budget['baseline_id']!=baseline_id or budget['state_id']!=state_id:
        raise ValueError('UNCERTAINTY_PAIRING_MISMATCH')
    level='SYNTHETIC_TEST_ONLY' if synthetic else 'INDEPENDENT_QOI_BUDGET'
    if budget['evidence_level']!=level:
        raise ValueError('UNCERTAINTY_EVIDENCE_MISMATCH')
    if not synthetic and not sha_ok(budget['budget_source_sha256']):
        raise ValueError('UNCERTAINTY_SOURCE_SHA_MISSING')
    by_id={r['design_id']:r for r in parsed}
    supplied=budget['bounds']
    if not isinstance(supplied,dict) or set(supplied)!=set(by_id):
        raise ValueError('UNCERTAINTY_DESIGN_SET_MISMATCH')
    intervals={}
    for design_id,row in by_id.items():
        obj=supplied[design_id]
        if not isinstance(obj,dict) or set(obj)!={'mass_ratio','max_fatigue_ratio'}:
            raise ValueError('UNCERTAINTY_OBJECTIVES_MISMATCH')
        intervals[design_id]={}
        for key in ('mass_ratio','max_fatigue_ratio'):
            pair=obj[key]
            if not isinstance(pair,list) or len(pair)!=2:
                raise ValueError('UNCERTAINTY_INTERVAL_SHAPE')
            lo=numeric(pair[0],'interval_lower_'+key)
            hi=numeric(pair[1],'interval_upper_'+key)
            point=row[key]
            tol=1e-12*max(1.0,abs(point))
            if lo>hi or lo>point+tol or hi<point-tol:
                raise ValueError('UNCERTAINTY_EXCLUDES_POINT_ESTIMATE')
            intervals[design_id][key]=(lo,hi)
    def all_realizations_dominates(a,b):
        ai,bi=intervals[a],intervals[b]
        return (all(ai[k][1]<=bi[k][0] for k in ('mass_ratio','max_fatigue_ratio'))
                and any(ai[k][1]<bi[k][0] for k in ('mass_ratio','max_fatigue_ratio')))
    def some_realization_dominates(a,b):
        ai,bi=intervals[a],intervals[b]
        return (all(ai[k][0]<=bi[k][1] for k in ('mass_ratio','max_fatigue_ratio'))
                and any(ai[k][0]<bi[k][1] for k in ('mass_ratio','max_fatigue_ratio')))
    def bracket(group):
        ids=[r['design_id'] for r in group]
        core=sorted(a for a in ids if not any(
            some_realization_dominates(b,a) for b in ids if b!=a))
        outer=sorted(a for a in ids if not any(
            all_realizations_dominates(b,a) for b in ids if b!=a))
        nominal=front(group)
        if not set(core)<=set(nominal) or not set(nominal)<=set(outer):
            raise AssertionError('INTERVAL_PARETO_BRACKET_BROKEN')
        return {'nominal':nominal,'guaranteed_nondominated_core':core,
                'not_guaranteed_dominated_outer':outer}
    wind=[r for r in parsed if r['wind_gate']=='PASS']
    joint=[r for r in wind if r['seismic_gate']=='PASS']
    return {'status':'SYNTHETIC_INTERVAL_QC_ONLY' if synthetic else
            'CONDITIONAL_INTERVAL_SCREENING_NEEDS_INDEPENDENT_REVIEW',
            'wind_only':bracket(wind),'seismic_constrained':bracket(joint),
            'budget_source_sha256':budget['budget_source_sha256'] or None,
            'assumptions':'axis-aligned closed intervals; conservative bounds; no correlation or baseline covariance',
            'physical_pass':False}


def self_test():
    # A dominates G in wind; A fails seismic, allowing G to enter constrained front.
    entries=[('BASE',1.0,1.0,'PASS','PASS'),
             ('A',.90,1.00,'PASS','FAIL'),
             ('B',1.00,.80,'PASS','PASS'),
             ('C',1.10,1.00,'PASS','PASS'),
             ('D',.95,.95,'PASS','PASS'),
             ('E',1.20,.70,'PASS','FAIL'),
             ('G',.92,1.10,'PASS','PASS')]
    rows=[]
    for d,m,f,w,s in entries:
        rows.append(dict(design_id=d,state_id='SYNTH_OPERATING',baseline_id='BASE',
                         mass_t=str(m*1000),baseline_mass_t='1000',
                         D_concrete=str(f*.01),D_PT=str(f*.02),D_steel=str(f*.03),
                         D0_concrete='.01',D0_PT='.02',D0_steel='.03',
                         wind_gate=w,seismic_gate=s,
                         evidence_level='SYNTHETIC_TEST_ONLY',
                         W_run_sha256='',E_run_sha256='',WE_run_sha256='',
                         fatigue_run_sha256=''))
    def encode(data):
        f=io.StringIO(newline='');w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator='\n')
        w.writeheader();w.writerows(data);return f.getvalue().encode()
    raw=encode(rows);r=calculate(raw,synthetic=True)
    assert r['wind_pareto']==['A','B','D','E']
    assert r['seismic_constrained_pareto']==['B','D','G']
    assert r['new_entrants_to_front']==['G']
    assert r['removed_from_front']==['A','E']
    bad=[]
    bad.append([dict(x,baseline_mass_t='900') if x['design_id']=='B' else x for x in rows])
    bad.append([dict(x,state_id='DIFFERENT') if x['design_id']=='B' else x for x in rows])
    bad.append([dict(x,D0_PT='0') if x['design_id']=='B' else x for x in rows])
    bad.append([dict(x,D_steel='nan') if x['design_id']=='B' else x for x in rows])
    bad.append([dict(x,wind_gate='YES') if x['design_id']=='B' else x for x in rows])
    bad.append(rows+rows[:1])
    bad.append([dict(x,evidence_level='NATIVE_VERIFIED') if x['design_id']=='B' else x for x in rows])
    bad.append([dict(x,baseline_id='OTHER') if x['design_id']=='B' else x for x in rows])
    for test in bad:
        try:calculate(encode(test),synthetic=True)
        except ValueError:pass
        else:raise AssertionError('accepted corrupted synthetic input')
    try:calculate(raw,synthetic=False)
    except ValueError:pass
    else:raise AssertionError('synthetic input promoted to native')
    # Independent analytical oracle: zero-width intervals reproduce the exact front.
    def make_budget(width):
        return {'schema_version':1,'baseline_id':'BASE','state_id':'SYNTH_OPERATING',
                'evidence_level':'SYNTHETIC_TEST_ONLY','budget_source_sha256':'',
                'bounds':{d:{'mass_ratio':[max(0.0,m-width),m+width],
                             'max_fatigue_ratio':[max(0.0,f-width),f+width]}
                          for d,m,f,_,_ in entries}}
    zero=calculate(raw,synthetic=True,uncertainty=make_budget(0.0))['interval_pareto']
    assert zero['wind_only']['guaranteed_nondominated_core']==r['wind_pareto']
    assert zero['wind_only']['not_guaranteed_dominated_outer']==r['wind_pareto']
    assert zero['seismic_constrained']['guaranteed_nondominated_core']==r['seismic_constrained_pareto']
    assert zero['seismic_constrained']['not_guaranteed_dominated_outer']==r['seismic_constrained_pareto']
    wide=calculate(raw,synthetic=True,uncertainty=make_budget(.05))['interval_pareto']
    assert wide['wind_only']['guaranteed_nondominated_core']==['B']
    assert wide['wind_only']['not_guaranteed_dominated_outer']==['A','B','BASE','D','E','G']
    assert wide['seismic_constrained']['guaranteed_nondominated_core']==['B']
    assert wide['seismic_constrained']['not_guaranteed_dominated_outer']==['B','BASE','D','G']
    # A nominally dominates G, but interval overlap prevents declaring G
    # dominated for all uncertainty realizations.
    assert 'G' not in r['wind_pareto'] and 'G' in wide['wind_only']['not_guaranteed_dominated_outer']
    import copy
    broken=[]
    q=make_budget(.05);q['baseline_id']='OTHER';broken.append(q)
    q=make_budget(.05);q['bounds'].pop('G');broken.append(q)
    q=make_budget(.05);q['bounds']['G']['mass_ratio']=[.99,1.01];broken.append(q)
    q=make_budget(.05);q['bounds']['B']['max_fatigue_ratio']=[.9,.7];broken.append(q)
    q=make_budget(.05);q['bounds']['B']['max_fatigue_ratio']=[float('nan'),1.0];broken.append(q)
    q=make_budget(.05);q['evidence_level']='INDEPENDENT_QOI_BUDGET';broken.append(q)
    q=make_budget(.05);q['bounds']['B']['mass_ratio']=[0.0];broken.append(q)
    for q in broken:
        try:calculate(raw,synthetic=True,uncertainty=q)
        except ValueError:pass
        else:raise AssertionError('accepted invalid uncertainty budget')
    return {'status':'PASS_SYNTHETIC_ONLY','negative_tests':len(bad)+1+len(broken),
            'positive_tests':4,'input_sha256':hashlib.sha256(raw).hexdigest(),
            'wind_front':r['wind_pareto'],
            'seismic_front':r['seismic_constrained_pareto'],
            'new_entrant':r['new_entrants_to_front'],
            'interval_oracle_zero_width':'PASS',
            'interval_oracle_0p05':wide,
            'native_runs':0,'physical_pass':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--input',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--uncertainty',type=Path,help='independently justified objective interval JSON; optional')
    a=p.parse_args()
    if a.self_test: print(json.dumps(self_test(),sort_keys=True))
    if a.input:
        budget=json.loads(a.uncertainty.read_text(encoding='utf-8')) if a.uncertainty else None
        result=calculate(a.input.read_bytes(),synthetic=False,uncertainty=budget)
        output=json.dumps(result,indent=2,sort_keys=True)+'\n'
        if a.output:a.output.write_text(output,encoding='utf-8')
        else:print(output)
    if a.uncertainty and not a.input:p.error('--uncertainty requires --input')
    if not a.self_test and not a.input:p.error('provide --self-test or --input')

if __name__=='__main__':main()
