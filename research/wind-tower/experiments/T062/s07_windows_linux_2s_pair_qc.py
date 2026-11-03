#!/usr/bin/env python3
"""S07: SHA-pinned 2 s Windows-vs-Linux native OUTB difference inventory.

Controller/toolchain comparison only; not controller equivalence, mapping or fatigue PASS.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile
from s06_historical_outb_source_gate import outb_header
from s06_native_4batch_common_channel_qc import decode, within_quant

WIN_ZIP_SHA = '7fcae2bf57be571cacc6d3d9b82f1a254257ce59fdb946a1cfb56d3639eb9f1b'
WIN_OUTB_SHA = 'c3f40b400f827fbcdd49e9a63f5bb2295a5c0f368a9644b90b591d66b7bb0242'
WIN_MEMBER = 'work/batch1/DTU_10MW_RWT.outb'
WIN_BTS_SHA = 'ad68a83a63f197c528c07502db8adff883e9c737863ef3c4cab99cfa76052147'
IMPORTANT = ('GenSpeed', 'BldPitch1', 'BldPitch2', 'BldPitch3', 'GenTq',
             'TwrBsFxt', 'TwrBsFyt', 'TwrBsFzt', 'TwrBsMxt', 'TwrBsMyt', 'TwrBsMzt')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def sample_grid(h):
    if h['file_id'] != 4 or h['num_samples'] != 41 or h['first_time_s'] is None:
        raise ValueError('S07_2S_FILEID_OR_SAMPLE_COUNT_HOLD')
    if abs(h['first_time_s']) > 1e-10 or abs(h['time_increment_s'] - .05) > 1e-10:
        raise ValueError('S07_2S_OUTPUT_TIME_GRID_HOLD')
    return [h['first_time_s'] + i*h['time_increment_s'] for i in range(41)]

def channel_metrics(a, qa, b, qb):
    if not (len(a) == len(b) == len(qa) == len(qb) == 41):
        raise ValueError('S07_CHANNEL_SERIES_LENGTH_HOLD')
    errors = [x-y for x,y in zip(a,b)]
    budgets = []
    for x,y,qx,qy in zip(a,b,qa,qb):
        if not all(math.isfinite(v) for v in (x,y,qx,qy)) or qx <= 0 or qy <= 0:
            raise ValueError('S07_NONFINITE_OR_BAD_QUANTIZATION_HOLD')
        _,limit=within_quant(x,qx,y,qy)
        budgets.append(limit)
    return {'max_abs_delta':max(map(abs,errors)),
            'rms_delta':math.sqrt(sum(v*v for v in errors)/len(errors)),
            'mean_delta':sum(errors)/len(errors),
            'max_quantization_budget':max(budgets),
            'exceeds_packed_quantization_count':sum(abs(e)>q for e,q in zip(errors,budgets)),
            'windows_min_max':[min(a),max(a)],'linux_min_max':[min(b),max(b)]}

def audit(win_zip,linux_outb,derived_receipt):
    if sha(win_zip)!=WIN_ZIP_SHA:
        raise ValueError('WINDOWS_ORIGINAL_ARTIFACT_SHA256_MISMATCH')
    with zipfile.ZipFile(io.BytesIO(win_zip)) as z:
        if WIN_MEMBER not in z.namelist() or z.testzip() is not None:
            raise ValueError('WINDOWS_ARCHIVE_MEMBER_OR_CRC_HOLD')
        original=z.read(WIN_MEMBER)
        prep=json.loads(z.read('work/batch1/S06_0P1S_PREP_RECEIPT.json'))
    if sha(original)!=WIN_OUTB_SHA:
        raise ValueError('WINDOWS_OUTB_SHA256_MISMATCH')
    if (prep.get('case')!='U09p343881_ETM_S06' or prep.get('batch')!=1
        or prep.get('etm_s06_bts_original_sha256')!=WIN_BTS_SHA):
        raise ValueError('WINDOWS_SOURCE_WIND_IDENTITY_HOLD')
    if (derived_receipt.get('source_equivalence') is not False
        or derived_receipt.get('physical_pass') is not False
        or not all(len(derived_receipt.get(k,''))==64 for k in
          ('source_controller_sha256','linux_controller_sha256','source_servo_sha256','derived_linux_servo_sha256'))):
        raise ValueError('LINUX_DERIVED_IDENTITY_RECEIPT_HOLD')
    hw=outb_header(original);hl=outb_header(linux_outb)
    tw=sample_grid(hw);tl=sample_grid(hl)
    if any(abs(x-y)>1e-10 for x,y in zip(tw,tl)):
        raise ValueError('WINDOWS_LINUX_SAMPLE_TIME_ALIGNMENT_HOLD')
    names=set(hw['channel_names'][1:]) & set(hl['channel_names'][1:])
    if not set(IMPORTANT).issubset(names):
        raise ValueError('S07_MISSING_CRITICAL_COMMON_CONTROL_OR_TOWER_CHANNELS')
    rows=[]
    for name in sorted(names):
        iw=hw['channel_names'].index(name);il=hl['channel_names'].index(name)
        uw=hw['channel_units'][iw];ul=hl['channel_units'][il]
        if uw!=ul:
            raise ValueError('S07_WINDOWS_LINUX_UNIT_MISMATCH_'+name)
        w=[decode(original,hw,name,i) for i in range(41)]
        l=[decode(linux_outb,hl,name,i) for i in range(41)]
        row={'channel':name,'unit':uw,'group':('CONTROL' if name in IMPORTANT[:5]
             else 'TOWER_BASE' if name in IMPORTANT[5:] else 'OTHER')}
        row.update(channel_metrics([v for v,q in w],[q for v,q in w],
                                   [v for v,q in l],[q for v,q in l]))
        rows.append(row)
    exceed=[r for r in rows if r['exceeds_packed_quantization_count']]
    return {
      'stage':'S07','status':'WINDOWS_LINUX_2S_PAIRED_DIAGNOSTIC_ONLY',
      'windows_zip_sha256':sha(win_zip),'windows_batch1_outb_sha256':sha(original),
      'linux_batch1_outb_sha256':sha(linux_outb),'original_bts_sha256':WIN_BTS_SHA,
      'historical_controller_sha256':derived_receipt['source_controller_sha256'],
      'substituted_linux_controller_sha256':derived_receipt['linux_controller_sha256'],
      'derived_servo_sha256':derived_receipt['derived_linux_servo_sha256'],
      'source_servo_sha256':derived_receipt['source_servo_sha256'],
      'samples':41,'dt_s':.05,'common_channels':len(rows),
      'quantization_exceeding_channels':len(exceed),
      'quantization_exceeding_samples':sum(r['exceeds_packed_quantization_count'] for r in rows),
      'channels':rows,
      'SOURCE':'Windows OpenFAST-v3.5.3 Intel 2021 Actions artifact #13080759167 and actual Linux OpenFAST-v3.5.3 GNU + ROSCO v2.9.0 OUTB',
      'REF':'T062 S06_ETM_NATIVE_2S_OVERLAP_QC_20261101.json and S07 native DCM audit',
      'STANDARD':'No authorized IEC/GB clause reviewed here',
      'OFFICIAL':'OpenFAST v3.5.3; ROSCO v2.9.0 Linux diagnostic substitution',
      'RUN':'2s 41-point per channel native paired output, no long run',
      'FIG':'none','TAB':'per-channel max/rms/mean difference and packed quantization budget',
      'ASSUMPTIONS':'Common source BTS and restored batch1; different controller binary/toolchain; 2s initialization only',
      'ERROR_BUDGET':'1.1*(two OUTB half-LSB)+1e-8 per sample; not an acceptable physical/controller equivalence tolerance',
      'HOLD':'2s difference cannot establish historical controller state equivalence; 600s DLC1.2, cross-batch load map, physical response and material life unverified',
      'controller_equivalence_verified':False,'physical_pass':False}

def selftest():
    a=[float(i) for i in range(41)];q=[.01]*41
    x=channel_metrics(a,q,a,q)
    assert x['exceeds_packed_quantization_count']==0 and x['max_abs_delta']==0
    b=a.copy();b[20]+=.2
    y=channel_metrics(a,q,b,q)
    assert y['exceeds_packed_quantization_count']==1 and y['max_abs_delta']>.19
    for bad in [(a[:-1],q,a,q),(a,q,a,[0]*41),(a,q,[float('nan')]*41,q)]:
        try:channel_metrics(*bad)
        except ValueError:pass
        else:raise AssertionError('S07_NEGATIVE_NOT_REJECTED')
    try:sample_grid({'file_id':4,'num_samples':41,'first_time_s':0.,'time_increment_s':.1})
    except ValueError:pass
    else:raise AssertionError('S07_BAD_DT_ACCEPTED')
    return {'positive_equal':True,'positive_divergence':True,'negative_rejections':4,
            'native_run':False,'physical_pass':False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--windows-zip',type=Path)
    p.add_argument('--linux-outb',type=Path)
    p.add_argument('--derived-receipt',type=Path)
    p.add_argument('--out',type=Path)
    p.add_argument('--selftest',action='store_true')
    a=p.parse_args()
    if a.selftest:print(json.dumps(selftest(),sort_keys=True))
    if not (a.windows_zip and a.linux_outb and a.derived_receipt and a.out):
        if a.selftest:return
        p.error('provide --windows-zip --linux-outb --derived-receipt --out')
    result=audit(a.windows_zip.read_bytes(),a.linux_outb.read_bytes(),
                 json.loads(a.derived_receipt.read_text()))
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='channels'},sort_keys=True))

if __name__=='__main__':main()
