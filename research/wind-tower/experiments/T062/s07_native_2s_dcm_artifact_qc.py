#!/usr/bin/env python3
"""S07: independently QC the *archived* 2-second OpenFAST DCM audit JSON.

No solver, no Abaqus, no physics PASS. The audit JSON is derived from the
original 56 MB probe by the source-locked T062 parser; the probe itself was
not included in the archived CI artifact. This script checks the derived
series, not the underlying free-body reconstruction independently.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

EXPECTED_AUDIT_SHA256 = 'a49efaa80fd64f9b51986bbac0dbf36522c50fbc54a9b51b4f71df694a59e924'
EXPECTED_PROBE_SHA256 = '238eb41bd4567e5c13bfc03759ac3945789742f71e23f5396aedefe15022aa48'
EXPECTED_SOURCE_SHA256 = 'a8ea1a88dc22d5401ea450f376aa7f66e3242785f1e038a22933054aaaf4f7d3'
DT = 0.0125
N = 161

def sha(b):
    return hashlib.sha256(b).hexdigest()

def determinant(a):
    return (a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])
           -a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])
           +a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]))

def validate(raw, require_hash=True):
    digest = sha(raw)
    if require_hash and digest != EXPECTED_AUDIT_SHA256:
        raise ValueError('AUDIT_SHA256_MISMATCH')
    d = json.loads(raw)
    if (d.get('status') != 'SOURCE_LEDGER_QC_ONLY' or d.get('physical_pass') is not False
        or d.get('probe_sha256') != EXPECTED_PROBE_SHA256
        or d.get('source_sha256') != EXPECTED_SOURCE_SHA256):
        raise ValueError('AUDIT_PROVENANCE_OR_PHYSICS_FLAG_MISMATCH')
    rows = d['rows']
    if len(rows) != N:
        raise ValueError('BAD_ROW_COUNT')
    orth, determinants, flat = [], [], []
    for i, r in enumerate(rows):
        t = r['time_s']
        if not math.isfinite(t) or abs(t-i*DT) > 1e-12:
            raise ValueError(f'BAD_TIME_GRID_{i}')
        q = r['Q_IEC_local_to_global']
        f, m = r['F_IEC_kN'], r['M_IEC_kNm_at_gage']
        if (len(q)!=3 or any(len(a)!=3 for a in q) or len(f)!=3 or len(m)!=3
            or not all(math.isfinite(v) for a in q for v in a)
            or not all(math.isfinite(v) for v in f+m)):
            raise ValueError(f'BAD_DIMENSIONS_OR_NONFINITE_{i}')
        e = max(abs(sum(q[k][a]*q[k][b] for k in range(3))-(1.0 if a==b else 0.0))
                for a in range(3) for b in range(3))
        det = determinant(q)
        if e > 1e-12 or abs(det-1.0)>1e-12:
            raise ValueError(f'BAD_ORTHONORMALITY_OR_HANDEDNESS_{i}')
        if r['element_rows'] != 901 or r['source_ownership'] != 'INCLUDES_TOP_AND_TOWER_GRAVITY_INERTIA_NOT_WIND_ONLY':
            raise ValueError(f'OWNERSHIP_OR_ELEMENT_COUNT_{i}')
        orth.append(e)
        determinants.append(det)
        flat.append([t]+[v for a in q for v in a]+f+m)
    return {
        'status':'NATIVE_2S_DIAGNOSTIC_SERIES_QC_ONLY',
        'audit_sha256':digest,'probe_sha256':d['probe_sha256'],
        'source_sha256':d['source_sha256'], 'n':N,'dt_s':DT,
        'time_start_s':rows[0]['time_s'],'time_end_s':rows[-1]['time_s'],
        'max_QtQ_minus_I_component':max(orth),
        'max_abs_detQ_minus_1':max(abs(v-1.0) for v in determinants),
        'force_kN_min_max':[[min(x[10+j] for x in flat),max(x[10+j] for x in flat)] for j in range(3)],
        'moment_kNm_min_max':[[min(x[13+j] for x in flat),max(x[13+j] for x in flat)] for j in range(3)],
        'element_rows_each':901,'source_ownership':'INCLUDES_GRAVITY_AND_INERTIA_NOT_WIND_ONLY',
        'independent_raw_probe_reconstruction':False,'physical_pass':False
    },flat

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('audit_json',type=Path)
    ap.add_argument('--repeat',type=Path,help='second independently archived audit JSON')
    ap.add_argument('--csv',type=Path)
    ap.add_argument('--selftest',action='store_true')
    args=ap.parse_args()
    b=args.audit_json.read_bytes()
    result,flat=validate(b)
    if args.repeat:
        other=args.repeat.read_bytes()
        if other!=b: raise ValueError('REPEATED_NATIVE_AUDIT_NOT_BYTE_IDENTICAL')
        result['repeated_audit_byte_identical']=True
    if args.selftest:
        cases=[('bad time',lambda d:d['rows'][1].__setitem__('time_s',0.1)),
               ('bad DCM',lambda d:d['rows'][1]['Q_IEC_local_to_global'][0].__setitem__(0,0.7)),
               ('bad ownership',lambda d:d['rows'][1].__setitem__('element_rows',900)),
               ('nonfinite',lambda d:d['rows'][1]['F_IEC_kN'].__setitem__(0,float('nan'))),
               ('missing row',lambda d:d['rows'].pop())]
        for name,mut in cases:
            d=json.loads(b);mut(d)
            try:validate(json.dumps(d).encode(),require_hash=False)
            except ValueError:pass
            else:raise AssertionError('NEGATIVE_TEST_ACCEPTED_'+name)
        result['negative_tests_rejected']=len(cases)
    if args.csv:
        args.csv.parent.mkdir(parents=True,exist_ok=True)
        with args.csv.open('w',encoding='utf-8',newline='') as f:
            w=csv.writer(f,lineterminator='\n')
            w.writerow(['time_s']+[f'Q{i}{j}' for i in range(1,4) for j in range(1,4)]
                       +['Fx_kN','Fy_kN','Fz_kN','Mx_kNm','My_kNm','Mz_kNm'])
            w.writerows(flat)
        result['csv_sha256']=sha(args.csv.read_bytes())
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))

if __name__=='__main__':main()
