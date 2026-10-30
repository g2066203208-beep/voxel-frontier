#!/usr/bin/env python3
"""Four independent 0.1s STEADY-wind OpenFAST diagnostic reruns: common-channel parity.
NOT the original NTM turbulent field, 700s histories, material fatigue or physics PASS.
Python 3.11 standard library. All failure evidence stays in Actions artifacts.
"""
import argparse, hashlib, json, math, re, struct
from pathlib import Path
from s06_historical_outb_source_gate import outb_header

SUFFIX=('FLxt','FLyt','FLzt','MLxt','MLyt','MLzt','TPzi')
BASE=('TwrBsFxt','TwrBsFyt','TwrBsFzt','TwrBsMxt','TwrBsMyt','TwrBsMzt')
def sha(b): return hashlib.sha256(b).hexdigest()
def decode(raw,h,name,k):
    i=h['channel_names'].index(name)-1
    scale=h['column_scales'][i];offset=h['column_offsets'][i]
    if not math.isfinite(scale) or scale==0 or not math.isfinite(offset):
        raise ValueError('BAD_PACKED_SCALE_'+name)
    q=struct.unpack_from('<h',raw,h['data_offset_bytes']+2*(k*h['num_output_channels']+i))[0]
    value=(q-offset)/scale
    if not math.isfinite(value):raise ValueError('NONFINITE_'+name)
    return value,.5/abs(scale)
def within_quant(a,qa,b,qb):
    budget=1.1*(qa+qb)+1e-8
    return abs(a-b)<=budget,budget
def selftest():
    assert within_quant(1.,.01,1.01,.01)[0]
    assert not within_quant(1.,.01,1.1,.01)[0]
    try:within_quant(1.,0.,2.,0.)
    except Exception:pass
    else:assert not within_quant(1.,0.,2.,0.)[0]
    print('SELFTEST_PASS known_equal_within_LSB known_different_rejected')
def run(root,out):
    data=[]
    for b in range(1,5):
        p=Path(root)/f'batch{b}'
        prep=json.loads((p/'S06_0P1S_PREP_RECEIPT.json').read_text(encoding='utf-8'))
        if prep.get('batch')!=b or prep.get('TMax_s')!=.1 or prep.get('DT_Out_s')!=.05:
            raise ValueError(f'BATCH_{b}_PREP_MISMATCH')
        if (p/'native_exit_code.txt').read_text().strip()!='0':
            raise ValueError(f'BATCH_{b}_NATIVE_NONZERO')
        if b'OpenFAST terminated normally.' not in (p/'native_stdout.log').read_bytes():
            raise ValueError(f'BATCH_{b}_NATIVE_LOG_MISSING_NORMAL_TERMINATION')
        raw=(p/'DTU_10MW_RWT.outb').read_bytes();h=outb_header(raw)
        if h['file_id']!=4 or h['num_samples']!=3 or h['first_time_s']!=0.0 or abs(h['time_increment_s']-.05)>1e-12:
            raise ValueError(f'BATCH_{b}_TIME_GRID')
        ng=len(prep['gage_nodes'])
        if ng!=([9,9,9,4][b-1]):raise ValueError(f'BATCH_{b}_GAGE_COUNT')
        for i in range(1,ng+1):
            for suffix in SUFFIX:
                name=f'TwHt{i}{suffix}'
                if name not in h['channel_names']:raise ValueError(f'BATCH_{b}_MISSING_{name}')
        data.append((prep,raw,h))
    if len({tuple(d[0]['gage_nodes']) for d in data})!=4:
        raise ValueError('DUPLICATED_GAGE_BATCHES')
    for k in ('fst','tower','servo','inflow','discon','dll','exe'):
        if len({d[0]['source_sha256'][k] for d in data})!=1:
            raise ValueError('ORIGINAL_SOURCE_IDENTITY_MISMATCH_'+k)
    for k in ('DTU_10MW_RWT.fst','DTU_10MW_InflowWind.dat',
              'Control/DTU_10MW_RWT_DISCON.IN','Control/libdiscon.dll'):
        if len({d[0]['derived_sha256'][k] for d in data})!=1:
            raise ValueError('DERIVED_DYNAMIC_INPUT_MISMATCH_'+k)
    common=set.intersection(*(set(h['channel_names'][1:]) for _,_,h in data))
    common=sorted(c for c in common if not re.match(r'^TwHt[0-9]+',c))
    if len(common)<10 or not set(BASE).issubset(common):
        raise ValueError('INSUFFICIENT_COMMON_NON_GAGE_CHANNELS')
    failures=[];rows=[]
    for name in common:
        units={h['channel_units'][h['channel_names'].index(name)] for _,_,h in data}
        if len(units)!=1:raise ValueError('UNIT_MISMATCH_'+name)
        md=0.;mb=0.
        for k in range(3):
            a,qa=decode(data[0][1],data[0][2],name,k)
            for b in range(1,4):
                v,qv=decode(data[b][1],data[b][2],name,k)
                ok,budget=within_quant(a,qa,v,qv)
                md=max(md,abs(a-v));mb=max(mb,budget)
                if not ok:failures.append({'channel':name,'batch':b+1,'time_s':k*.05,
                                            'abs_delta':abs(a-v),'budget':budget})
        rows.append({'channel':name,'unit':next(iter(units)),
                     'max_abs_difference':md,'max_pair_budget':mb})
    result={
      'stage':'S06_NATIVE_FOUR_BATCH_0P1S_DIAGNOSTIC_ONLY',
      'status':'NUMERICAL_CHANNEL_PARITY_PASS' if not failures else 'HOLD_CHANNEL_PARITY_FAIL',
      'batch_gage_nodes':[d[0]['gage_nodes'] for d in data],
      'native_outb_sha256':[sha(d[1]) for d in data],
      'native_stdout_sha256':[sha((Path(root)/f'batch{i}'/'native_stdout.log').read_bytes()) for i in range(1,5)],
      'time_grid_s':[0,.05,.1],'common_channel_count':len(common),
      'paired_channel_samples':len(common)*3*3,
      'max_abs_common_difference':max(x['max_abs_difference'] for x in rows),
      'max_pair_quantization_budget':max(x['max_pair_budget'] for x in rows),
      'common_channel_table':rows,'failure_count':len(failures),'first_failures':failures[:12],
      'SOURCE':'Four original-input-SHA-pinned OpenFAST v3.5.3 diagnostic OUTBs; original NTM InflowWind deliberately replaced by STEADY wind; original BTS not used',
      'REF':'T062 31-segment original ElastoDyn gage contract; no new journal full text',
      'STANDARD':'No new authorized IEC/GB/NB clauses',
      'OFFICIAL':'SHA-pinned native OpenFAST executable and ROSCO DLL',
      'RUN':'Four separate 0.1s native initialization runs; compare non-gage common channels only',
      'FIG':'none','TAB':'common_channel_table in this receipt',
      'error_budget':'1.1*(packed half-LSB batch1 + batchN) + 1e-8 in channel native unit; structural/controller internal-state errors unknown',
      'HOLD':'Does not verify true NTM seed wind, full controller internal state, 700s 31-station synchronization, 6-component mapping or Abaqus physics',
      'physical_pass':False}
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    Path(out).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('S06_FOUR_BATCH_COMMON_CHANNEL_RESULT',json.dumps({
      'status':result['status'],'common_channels':len(common),
      'paired_samples':result['paired_channel_samples'],
      'failure_count':len(failures),'max_abs_difference':result['max_abs_common_difference']}))
    if failures:raise ValueError('FOUR_BATCH_COMMON_CHANNEL_PARITY_FAILED')
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root');p.add_argument('--out');p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if a.self_test:selftest()
    else:
        if not a.root or not a.out:p.error('--root and --out required')
        run(a.root,a.out)
if __name__=='__main__':main()
