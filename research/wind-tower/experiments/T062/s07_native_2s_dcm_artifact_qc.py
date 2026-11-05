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


# Source-byte-verified paired native t-axis/RP check (2026-11-05).
# This deliberately reuses the existing 161-row DCM audit; it does not run a solver.
import gzip
import io
import struct
import zipfile

PAIR_BUNDLE_SHA256 = '30ad5d9821af7c21999d2fbdf07271504cb202d1b36584d0a2a5c60348fa6251'
PAIR_PROBE_SHA256 = '238eb41bd4567e5c13bfc03759ac3945789742f71e23f5396aedefe15022aa48'
PAIR_OUTB_SHA256 = 'ca2b1e961520782b90f32de905b3597e3eee3543922259949d32c898a752f555'

def _pair_trans(a):
    return [list(row) for row in zip(*a)]

def _pair_smallrot(rp):
    a,b,c=rp
    s=a*a+b*b+c*c
    if s==0:
        return [[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]
    root=math.sqrt(1+s)
    den=s*root
    ab=a*b*(root-1); ac=a*c*(root-1); bc=b*c*(root-1)
    return [[(a*a*root+b*b+c*c)/den,(c*s+ab)/den,(-b*s+ac)/den],
            [(-c*s+ab)/den,(a*a+b*b*root+c*c)/den,(a*s+bc)/den],
            [(b*s+ac)/den,(-a*s+bc)/den,(a*a+b*b+c*c*root)/den]]

def _pair_matrix_error(Q,P):
    if len(Q)!=3 or len(P)!=3 or any(len(row)!=3 for row in Q+P):
        raise ValueError('PAIR_DCM_SHAPE')
    if not all(math.isfinite(x) for row in Q+P for x in row):
        raise ValueError('PAIR_DCM_NONFINITE')
    return max(abs(Q[i][j]-P[i][j]) for i in range(3) for j in range(3))

def paired_native_rp_dcm_bundle(raw):
    if sha(raw)!=PAIR_BUNDLE_SHA256:
        raise ValueError('PAIR_BUNDLE_SHA256_MISMATCH')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:
            raise ValueError('PAIR_ZIP_CRC')
        required={'s07_linux_dcm_audit.json','s07_native_dcm_raw.log.gz',
                  's07_linux_native_2s.outb.gz','work/batch1/S06_0P1S_PREP_RECEIPT.json'}
        if not required.issubset(set(z.namelist())):
            raise ValueError('PAIR_MISSING_MEMBERS')
        audit_raw=z.read('s07_linux_dcm_audit.json')
        validate(audit_raw)  # existing 161-row DCM/ownership/handedness validator and SHA
        audit=json.loads(audit_raw)
        probe=gzip.decompress(z.read('s07_native_dcm_raw.log.gz'))
        if sha(probe)!=PAIR_PROBE_SHA256:
            raise ValueError('PAIR_PROBE_SHA256')
        outb=gzip.decompress(z.read('s07_linux_native_2s.outb.gz'))
        if sha(outb)!=PAIR_OUTB_SHA256:
            raise ValueError('PAIR_OUTB_SHA256')
        prep=json.loads(z.read('work/batch1/S06_0P1S_PREP_RECEIPT.json'))
        if (prep.get('case'),prep.get('gage_nodes',[])[-1],
            prep.get('DT_Out_s'),prep.get('TMax_s'))!=('U09p343881_ETM_S06',220,.05,2.):
            raise ValueError('PAIR_GAGE_INPUT_IDENTITY')
    gs=[line.split() for line in probe.decode('ascii').splitlines() if line.startswith('G ')]
    if len(gs)!=161:
        raise ValueError('PAIR_NATIVE_G_ROW_COUNT')
    native=[]
    for i,g in enumerate(gs):
        if len(g)!=27 or g[0]!='G' or int(g[2])!=220 or abs(float(g[1])-i*.0125)>1e-10:
            raise ValueError('PAIR_G_GRID')
        v=list(map(float,g[3:]))
        if not all(map(math.isfinite,v)):
            raise ValueError('PAIR_G_NONFINITE')
        basis=[v[3:6],v[6:9],v[9:12]]  # native t1,-t3,t2
        to_iec=lambda x:[x[0],-x[2],x[1]]
        Q=[[to_iec(basis[j])[k] for j in range(3)] for k in range(3)]
        if _pair_matrix_error(Q,audit['rows'][i]['Q_IEC_local_to_global'])>1e-12:
            raise ValueError('PAIR_RAW_VS_AUDIT_DCM')
        native.append(Q)
    f=io.BytesIO(outb)
    def rd(fmt):
        return struct.unpack('<'+fmt,f.read(struct.calcsize('<'+fmt)))
    if rd('h')[0]!=4:
        raise ValueError('PAIR_FILEID4_REQUIRED')
    nlen=rd('h')[0]; nch,nt=rd('ii'); first,dt=rd('dd')
    if (nlen,nch,nt,first,dt)!=(9,295,41,0.,.05):
        raise ValueError('PAIR_OUTB_GRID')
    scales=rd(str(nch)+'f'); offsets=rd(str(nch)+'f')
    desc_len=rd('i')[0]
    if not 0<=desc_len<=100000:
        raise ValueError('PAIR_OUTB_DESC')
    f.read(desc_len)
    def names():
        return [f.read(nlen).decode('ascii').replace(chr(0),'').strip() for _ in range(nch+1)]
    channels=names(); units=names(); start=f.tell()
    if len(outb)-start!=nt*nch*2:
        raise ValueError('PAIR_OUTB_PAYLOAD')
    idx=[channels.index('TwHt9RP'+x)-1 for x in ('xi','yi','zi')]
    if any(units[j+1]!='(deg)' or not math.isfinite(scales[j]) or scales[j]==0
           or not math.isfinite(offsets[j]) for j in idx):
        raise ValueError('PAIR_RP_UNITS_SCALES')
    rad=math.pi/180
    half_lsb=[.5/abs(scales[j])*rad for j in idx]
    budget=2*math.sqrt(sum(x*x for x in half_lsb))  # local screening allowance
    rows=[]
    for k in range(nt):
        rp=[]
        for j in idx:
            packed=struct.unpack_from('<h',outb,start+2*(k*nch+j))[0]
            rp.append((packed-offsets[j])/scales[j]*rad)
        Q=native[k*4]; R=_pair_smallrot(rp)
        direct=_pair_matrix_error(Q,R)
        transposed=_pair_matrix_error(Q,_pair_trans(R))
        if transposed>budget+1e-12:
            raise ValueError('PAIR_TRANSPOSE_QUANTIZATION_EXCEEDED')
        rows.append({'time_s':round(k*dt,8),
                     'RP_norm_deg':math.sqrt(sum(x*x for x in rp))/rad,
                     'max_abs_Q_minus_R':direct,'max_abs_Q_minus_RT':transposed})
    return {'status':'NATIVE_2S_RP_TRANSPOSE_DCM_DIAGNOSTIC_PASS__PHYSICAL_HOLD',
            'source_zip_sha256':PAIR_BUNDLE_SHA256,
            'raw_native_taxis_sha256':PAIR_PROBE_SHA256,
            'original_outb_sha256':PAIR_OUTB_SHA256,
            'native_audit_sha256':EXPECTED_AUDIT_SHA256,
            'case':'U09p343881_ETM_S06','gage_node':220,
            'native_dcm_samples_checked':161,'native_rp_dcm_paired_samples':41,
            'dt_out_s':dt,'time_window_s':[0,2],
            'max_RP_norm_deg':max(x['RP_norm_deg'] for x in rows),
            'max_transpose_matrix_component_error':max(x['max_abs_Q_minus_RT'] for x in rows),
            'max_direct_matrix_component_error':max(x['max_abs_Q_minus_R'] for x in rows),
            'direct_exceeding_quant_budget_count':sum(x['max_abs_Q_minus_R']>budget for x in rows),
            'transpose_exceeding_quant_budget_count':sum(x['max_abs_Q_minus_RT']>budget for x in rows),
            'RP_half_LSB_rad':half_lsb,
            'candidate_matrix_quantization_screening_budget':budget,
            'max_native_raw_vs_derived_Q_error':0.,
            'first_last_rows':[rows[0],rows[-1]],
            'physical_pass':False,
            'limitations':'Same Linux-derived OpenFAST v3.5.3 2s startup with substituted ROSCO v2.9.0; node220 only. Not historical Windows 600s ETM/NTM or 31-station DCM; FL/ML include inertia/gravity, no wind-only ownership.'}

def paired_native_selftest(raw):
    result=paired_native_rp_dcm_bundle(raw)
    rejects=0
    for bad in (raw+b'X',raw[:150]+bytes([raw[150]^1])+raw[151:]):
        try:
            paired_native_rp_dcm_bundle(bad)
        except ValueError as e:
            if str(e)!='PAIR_BUNDLE_SHA256_MISMATCH':
                raise
            rejects+=1
        else:
            raise AssertionError('PAIR_TAMPER_ACCEPTED')
    for Q,P in [([[1,0,0],[0,1,0],[0,0,1]],
                 [[1,0,0],[0,1,0],[0,0,float('nan')]]),
                ([[1,0,0],[0,1,0]],[[1,0,0],[0,1,0],[0,0,1]])]:
        try:
            _pair_matrix_error(Q,P)
        except ValueError:
            rejects+=1
        else:
            raise AssertionError('PAIR_BAD_MATRIX_ACCEPTED')
    if result['direct_exceeding_quant_budget_count']!=40 or result['transpose_exceeding_quant_budget_count']!=0:
        raise AssertionError('PAIR_DIRECTION_ORACLE')
    return {'positive_real_bundle':1,'negative_rejections':rejects}

if __name__=='__main__':
    import sys
    if '--pair-bundle' in sys.argv:
        pos=sys.argv.index('--pair-bundle')
        if pos+1>=len(sys.argv):
            raise ValueError('PAIR_BUNDLE_PATH_REQUIRED')
        raw=Path(sys.argv[pos+1]).read_bytes()
        result=paired_native_rp_dcm_bundle(raw)
        if '--selftest' in sys.argv:
            result['tests']=paired_native_selftest(raw)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
    else:
        main()
