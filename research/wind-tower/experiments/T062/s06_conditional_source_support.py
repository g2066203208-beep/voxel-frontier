#!/usr/bin/env python3
"""Reproducible historical NTM source-support sensitivity; NOT DLC or operating-state evidence."""
import argparse,csv,hashlib,io
from pathlib import Path
ERA='experiments/T062/S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv'
COV='experiments/T062/S10_ERA5_21BIN_6SEED_NTM_SOURCE_COVERAGE_20261031.csv'
LOCK={ERA:'e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102',
      COV:'d4e25023f343ea76f2de5ce90c7d24dd985df770ec9f4747d203391010431e67'}
HEADER=['lower_threshold_mps','diagnostic_upper_mps_exclusive','era5_hours_in_window','archived_NTM_supported_hours','unsupported_hours','conditional_supported_pct','supported_bins','additional_bins_for_90pct_hour_coverage','new_six_seed_slots_for_90pct','scope']
def read(root,name):
    raw=(root/'research/wind-tower'/name).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LOCK[name]:raise ValueError('SOURCE_SHA_MISMATCH')
    return list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
def analyze(era,cov):
    if len(era)!=31 or len(cov)!=126:raise ValueError('ROW_COUNT')
    hours={}
    for r in era:
        b=int(r['bin_lower_mps']);h=int(r['hours'])
        if b in hours or not 0<=b<=30 or h<0:raise ValueError('ERA_DUPLICATE_OR_INVALID')
        hours[b]=h
    if set(hours)!=set(range(31)) or sum(hours.values())!=184080:raise ValueError('ERA_SUPPORT')
    slots={}
    for r in cov:
        b=int(r['bin_lower_mps']);s=r['seed_id']
        if not 4<=b<25 or s not in [f'S{i:02d}' for i in range(1,7)]:raise ValueError('BIN_SEED')
        d=slots.setdefault(b,{})
        if s in d:raise ValueError('DUPLICATE_SEED')
        if int(r['era5_21y_hours'])!=hours[b]:raise ValueError('HOUR_MISMATCH')
        ok=r['source_coverage_status']=='ARCHIVED_NTM_SCREEN_ONLY'
        if r['source_coverage_status'] not in ('ARCHIVED_NTM_SCREEN_ONLY','NO_ARCHIVED_NTM_SOURCE'):raise ValueError('SOURCE_STATUS')
        ids=[r[k].strip() for k in ('historical_case_id','outb_sha256','fst_sha256')]
        if (ok!=all(ids)) or (not ok and any(ids)):raise ValueError('IDENTITY')
        if r['formal_DLC12_status']!='NOT_VALIDATED':raise ValueError('FORMAL_STATUS')
        d[s]=ok
    if set(slots)!=set(range(4,25)) or any(len(v)!=6 for v in slots.values()):raise ValueError('INCOMPLETE_MATRIX')
    if any(0<sum(v.values())<6 for v in slots.values()):raise ValueError('PARTIAL_BIN')
    known={b for b,v in slots.items() if all(v.values())}
    if known!={9,11,19}:raise ValueError('KNOWN_BIN_IDENTITY')
    rows=[]
    for t in list(range(4,13))+[19]:
        H=sum(hours[b] for b in range(t,25))
        K=sum(hours[b] for b in known if b>=t)
        missing=sorted((hours[b] for b in range(t,25) if b not in known),reverse=True)
        n=0;total=K
        while total*10<H*9 and n<len(missing):total+=missing[n];n+=1
        if not H or total*10<H*9:raise ValueError('COVERAGE_TARGET')
        rows.append([t,25,H,K,H-K,f'{100*K/H:.6f}',';'.join(map(str,sorted(b for b in known if b>=t))),n,6*n,'RETROSPECTIVE_ERA5_SOURCE_SUPPORT_NOT_OPERATING_STATE_OR_DLC12'])
    return rows
def selftest():
    h=[6438,18372,25202,27168,26927,24769,19994,14467,9245,5736,3149,1426,674,283,126,61,26,14,1,2]+[0]*11
    e=[dict(bin_lower_mps=str(i),hours=str(v)) for i,v in enumerate(h)]
    c=[]
    for b in range(4,25):
        for s in range(1,7):
            ok=b in (9,11,19)
            c.append(dict(bin_lower_mps=str(b),seed_id=f'S{s:02d}',era5_21y_hours=str(h[b]),source_coverage_status='ARCHIVED_NTM_SCREEN_ONLY' if ok else 'NO_ARCHIVED_NTM_SOURCE',historical_case_id='case' if ok else '',outb_sha256='a'*64 if ok else '',fst_sha256='b'*64 if ok else '',formal_DLC12_status='NOT_VALIDATED'))
    r=analyze(e,c)
    assert [(r[i][2],r[i][3]) for i in (0,5,6,8)]==[(106900,7164),(11498,7164),(5762,1428),(1187,2)]
    assert r[0][7:9]==[5,30]
    for mode,expect in [('duplicate','DUPLICATE_SEED'),('hours','HOUR_MISMATCH'),('identity','IDENTITY'),('formal','FORMAL_STATUS')]:
        bad=[x.copy() for x in c]
        if mode=='duplicate':bad[1]['seed_id']='S01'
        if mode=='hours':bad[0]['era5_21y_hours']='0'
        if mode=='identity':bad[0]['historical_case_id']='orphan'
        if mode=='formal':bad[0]['formal_DLC12_status']='VALIDATED'
        try:analyze(e,bad)
        except ValueError as err:assert expect in str(err)
        else:raise AssertionError('REJECTION_FAILED '+mode)
    print('SELFTEST_PASS 10 rows; 5 positive oracles; 4 negative refusals')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));ap.add_argument('--selftest',action='store_true');ap.add_argument('--write',action='store_true');a=ap.parse_args()
    if a.selftest:selftest();return
    rows=analyze(read(a.root,ERA),read(a.root,COV))
    data=','.join(HEADER)+'\n'+'\n'.join(','.join(map(str,r)) for r in rows)+'\n'
    if a.write:
        dest=a.root/'research/wind-tower/experiments/T062/S06_NTM18_CONDITIONAL_SUPPORT_THRESHOLD_10ROW_20261112.csv'
        dest.write_text(data,encoding='utf-8',newline='')
        print('CSV_SHA256',hashlib.sha256(data.encode()).hexdigest())
    else:print(data,end='')
if __name__=='__main__':main()
