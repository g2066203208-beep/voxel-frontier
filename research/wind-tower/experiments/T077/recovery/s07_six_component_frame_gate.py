#!/usr/bin/env python3
"""S07 six-component frame/point transport gate; NOT a wind load owner or Abaqus export.

All input forces kN, moments kN*m, positions m. R maps local components to
inertial/global components (columns = local basis in global axes). A force and
its free moment are at source origin A. At target origin B:
  F_B = R F_A; M_B = R M_A + (A-B) cross F_B.

The transformed SECTION_RESULTANT is still an internal section resultant; it
must NOT be applied as an Abaqus external force without a signed free-body,
gravity/inertia/RNA decomposition and independent physics verification.
"""
import argparse
import csv
import hashlib
import io
import math
from pathlib import Path

# Original 30-line historical static source, read from GitHub PR #42.
SOURCE_GIT_BLOB_SHA1 = 'fa38f2097f8380796c5f71add9a64066f9e8a4e8'
SOURCE_SHA256 = 'ae1e5bc3e217cd9151bcd45f9d70909d0459df3c258329f17c6c2fdb457fd64e'
OUTPUT_FIELDS = ('case_id','time_s','gage_id','frame_gate','ownership_gate',
                 'Fx_global_kN','Fy_global_kN','Fz_global_kN',
                 'Mx_target_global_kNm','My_target_global_kNm','Mz_target_global_kNm')
INPUT_FIELDS = ('case_id','time_s','gage_id','force_owner','frame_evidence',
                'position_evidence','Fx_local_kN','Fy_local_kN','Fz_local_kN',
                'Mx_local_kNm','My_local_kNm','Mz_local_kNm',
                'source_x_m','source_y_m','source_z_m',
                'target_x_m','target_y_m','target_z_m',
                'R00','R01','R02','R10','R11','R12','R20','R21','R22')


def vector(v):
    if len(v) != 3:
        raise ValueError('expected 3 components')
    out = tuple(float(x) for x in v)
    if not all(math.isfinite(x) for x in out):
        raise ValueError('nonfinite vector')
    return out


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def dot(a, b):
    return sum(x*y for x,y in zip(a,b))


def norm(a):
    return math.sqrt(dot(a,a))


def matmul(R, v):
    return tuple(dot(row,v) for row in R)


def transpose(R):
    return tuple(tuple(R[j][i] for j in range(3)) for i in range(3))


def rotation(rows, tolerance=1e-8):
    """Reject reflections, shears and unverified/nonfinite rotation entries."""
    if len(rows) != 3:
        raise ValueError('rotation needs 3 rows')
    R = tuple(vector(row) for row in rows)
    for i in range(3):
        for j in range(3):
            expected = 1.0 if i==j else 0.0
            if abs(dot(R[i], R[j])-expected) > tolerance:
                raise ValueError('rotation not orthonormal')
    det = dot(R[0], cross(R[1],R[2]))
    if abs(det-1.0) > tolerance:
        raise ValueError('rotation determinant not +1 (reflection?)')
    return R


def transport(F_local, M_local, R, source, target):
    """Six-component passive frame transform and exact moment reference shift."""
    F, M, A, B = map(vector,(F_local,M_local,source,target))
    R = rotation(R)
    f, m = matmul(R,F), matmul(R,M)
    lever = tuple(x-y for x,y in zip(A,B))
    couple = cross(lever,f)
    return f, tuple(x+y for x,y in zip(m,couple))


def git_blob_sha1(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def static_source_regression(path):
    """Real historical 30-row static diagnostic, NOT dynamic frame proof."""
    raw = Path(path).read_bytes()
    if git_blob_sha1(raw) != SOURCE_GIT_BLOB_SHA1 or hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('static SOURCE SHA mismatch')
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    if len(rows) != 30:
        raise ValueError('expected 30 real historical static rows')
    I = ((1,0,0),(0,1,0),(0,0,1))
    max_off_axis = 0.0
    min_axial, max_axial = math.inf, -math.inf
    for idx, row in enumerate(rows,1):
        if row['joint'] != f'J{idx:02d}' or row['frame_policy'] != 'STATIC_COMMON_FRAME_ASSUMED':
            raise ValueError('historical static source identity/frame mismatch')
        dz = float(row['gage_span_m'])
        if dz <= 0 or not math.isfinite(dz):
            raise ValueError('invalid gage span')
        # The source's already-transported upper-minus-lower static cut difference.
        dF = vector([row[f'delta_F{x}_kN'] for x in ('x','y','z')])
        dM = vector([row[f'delta_M{x}_at_below_kNm'] for x in ('x','y')]+
                    [row['delta_Mz_at_below_kNm']])
        f, m = transport(dF,dM,I,(0,0,0),(0,0,0))
        max_off_axis=max(max_off_axis,abs(f[0]),abs(f[1]),*(abs(x) for x in m))
        min_axial=min(min_axial,f[2]); max_axial=max(max_axial,f[2])
    if max_off_axis > 5e-8 or not (400 < min_axial < 450 and 600 < max_axial < 650):
        raise AssertionError('historical static gravity regression failed')
    return {'rows':len(rows),'min_delta_Fz_kN':min_axial,
            'max_delta_Fz_kN':max_axial,'max_off_axis_kN_or_kNm':max_off_axis,
            'source_sha256':hashlib.sha256(raw).hexdigest(),
            'source_git_blob_sha1':git_blob_sha1(raw)}


def _nonempty(row, key):
    v=row[key].strip()
    if not v or v.upper() in ('UNKNOWN','NA','N/A','UNVERIFIED'):
        raise ValueError('missing '+key+' provenance')
    return v


def transform_csv(input_path, output_path):
    """Transforms only; explicit provenance fields and no Abaqus export route."""
    raw=Path(input_path).read_bytes()
    with io.StringIO(raw.decode('utf-8-sig')) as f:
        reader=csv.DictReader(f)
        if reader.fieldnames is None or set(reader.fieldnames)!=set(INPUT_FIELDS):
            raise ValueError('missing or unexpected S07 columns')
        records=list(reader)
    if not records:
        raise ValueError('empty S07 dynamic input')
    seen=set(); out=[]; last_time={}
    for row in records:
        case=_nonempty(row,'case_id'); gage=_nonempty(row,'gage_id')
        if _nonempty(row,'force_owner')!='SECTION_RESULTANT':
            raise ValueError('force owner must be SECTION_RESULTANT; no external-load export')
        frame_proof=_nonempty(row,'frame_evidence')
        if frame_proof != 'SYNTHETIC_KNOWN_ROTATION' and not frame_proof.startswith('DCM_SOURCE_VERIFIED:'):
            raise ValueError('frame_evidence requires independently verified DCM; RP angles alone are not DCM')
        _nonempty(row,'position_evidence')
        t=float(row['time_s'])
        if not math.isfinite(t):
            raise ValueError('nonfinite time')
        key=(case,gage)
        if key in last_time and t <= last_time[key]:
            raise ValueError('duplicate or nonmonotone time per case/gage')
        last_time[key]=t
        uniq=(case,gage,t)
        if uniq in seen:
            raise ValueError('duplicate sample')
        seen.add(uniq)
        F=[row[f'{x}_local_kN'] for x in ('Fx','Fy','Fz')]
        M=[row[f'{x}_local_kNm'] for x in ('Mx','My','Mz')]
        A=[row[f'source_{x}_m'] for x in ('x','y','z')]
        B=[row[f'target_{x}_m'] for x in ('x','y','z')]
        R=[[row[f'R{i}{j}'] for j in range(3)] for i in range(3)]
        f,m=transport(F,M,R,A,B)
        out.append((case,f'{t:.9f}',gage,'ALGEBRA_ONLY_SOURCE_ASSERTED',
                    'SECTION_RESULTANT_NOT_EXTERNAL',*(f'{x:.9f}' for x in f+m)))
    with Path(output_path).open('w',encoding='utf-8',newline='') as h:
        w=csv.writer(h,lineterminator='\n');w.writerow(OUTPUT_FIELDS);w.writerows(out)
    return {'rows':len(out),'input_sha256':hashlib.sha256(raw).hexdigest(),
            'output_sha256':hashlib.sha256(Path(output_path).read_bytes()).hexdigest(),
            'status':'FRAME_ALGEBRA_ONLY_NOT_ABAQUS_LOAD'}


def selftest():
    import tempfile
    from pathlib import Path
    I=((1,0,0),(0,1,0),(0,0,1))
    R=((0,-1,0),(1,0,0),(0,0,1))
    f,m=transport((2,3,5),(7,11,13),R,(2,1,4),(1,0,0))
    assert f==(-3,2,5)
    assert m==(-14,-10,18)  # R*M=(-11,7,13), lever cross F=(-3,-17,5)
    # Inverse frame and origin shift recover original local wrench.
    lever=(1,1,4)
    unshifted=tuple(x-y for x,y in zip(m,cross(lever,f)))
    assert matmul(transpose(R),f)==(2,3,5)
    assert matmul(transpose(R),unshifted)==(7,11,13)
    # Path independence of two successive reference-point translations.
    f_mid,m_mid=transport((2,3,5),(7,11,13),R,(2,1,4),(0,0,2))
    f_end,m_end=transport(f_mid,m_mid,I,(0,0,2),(1,0,0))
    assert f_end==f and m_end==m
    # Deterministic 1000-sample moving-origin path-independence regression.
    import random
    rng=random.Random(20261028)
    for _ in range(1000):
        Fr=[rng.uniform(-100,100) for _ in range(3)]
        Mr=[rng.uniform(-1000,1000) for _ in range(3)]
        Ar=[rng.uniform(-50,50) for _ in range(3)]
        Br=[rng.uniform(-50,50) for _ in range(3)]
        Cr=[rng.uniform(-50,50) for _ in range(3)]
        f1,m1=transport(Fr,Mr,R,Ar,Br)
        f2,m2=transport(f1,m1,I,Br,Cr)
        f3,m3=transport(Fr,Mr,R,Ar,Cr)
        assert max(abs(x-y) for x,y in zip(f2+m2,f3+m3)) < 1e-10
    # Move to a common origin before summing: 2 forces cancel, moments only
    # cancel if both are at the same origin with their proper couples.
    aF,aM=transport((10,0,0),(0,0,0),I,(0,0,2),(0,0,0))
    bF,bM=transport((-10,0,0),(0,-20,0),I,(0,0,0),(0,0,0))
    assert all(abs(x+y)<1e-12 for x,y in zip(aF,bF))
    assert all(abs(x+y)<1e-12 for x,y in zip(aM,bM))
    for bad in (((-1,0,0),(0,1,0),(0,0,1)),
                ((1,0,0),(0,1,0),(0,0,2)),
                ((float('nan'),0,0),(0,1,0),(0,0,1))):
        try: rotation(bad)
        except ValueError: pass
        else: raise AssertionError('invalid rotation accepted')
    try: transport((float('nan'),0,0),(0,0,0),I,(0,0,0),(0,0,0))
    except ValueError: pass
    else: raise AssertionError('NaN force accepted')
    with tempfile.TemporaryDirectory() as d:
        inp=Path(d)/'input.csv';out=Path(d)/'out.csv'
        row={k:'' for k in INPUT_FIELDS}
        row.update(case_id='SYNTH',time_s='0',gage_id='G1',force_owner='SECTION_RESULTANT',
                   frame_evidence='SYNTHETIC_KNOWN_ROTATION',position_evidence='SYNTHETIC_KNOWN_ORIGIN')
        for k,v in zip(('Fx','Fy','Fz'),(2,3,5)): row[k+'_local_kN']=str(v)
        for k,v in zip(('Mx','My','Mz'),(7,11,13)): row[k+'_local_kNm']=str(v)
        for k,v in zip(('x','y','z'),(2,1,4)):
            row['source_'+k+'_m']=str(v)
        for k,v in zip(('x','y','z'),(1,0,0)):
            row['target_'+k+'_m']=str(v)
        for i in range(3):
            for j in range(3): row[f'R{i}{j}']=str(R[i][j])
        def write_row(r):
            with inp.open('w',encoding='utf-8',newline='') as h:
                w=csv.DictWriter(h,fieldnames=INPUT_FIELDS,lineterminator='\n');w.writeheader();w.writerow(r)
        write_row(row)
        assert transform_csv(inp,out)['rows']==1
        row['frame_evidence']='UNKNOWN';write_row(row)
        try: transform_csv(inp,out)
        except ValueError: pass
        else: raise AssertionError('missing provenance accepted')
        row['frame_evidence']='RP_AS_EULER';write_row(row)
        try: transform_csv(inp,out)
        except ValueError as e: assert 'verified DCM' in str(e)
        else: raise AssertionError('RP pseudo-Euler orientation accepted')
        row['frame_evidence']='SYNTHETIC';row['force_owner']='EXTERNAL';write_row(row)
        try: transform_csv(inp,out)
        except ValueError: pass
        else: raise AssertionError('external ownership accepted')
    return 'PASS synthetic rotation/moment/reference/sign/invariance/invalid input/CLI gates'



# The v3.5.3 source uses AngPosEF components in degrees for TwHt*RP*i.
# These are NOT a supplied 3x3 direction cosine matrix. Do not silently
# reinterpret the three outputs as an exact Euler orientation.
V353_ELASTODYN_GIT_BLOB = '2bcfb11fc40712febb5a8b5c2947c87e2aabb7b1'
V353_ELASTODYN_SHA256 = 'a8ea1a88dc22d5401ea450f376aa7f66e3242785f1e038a22933054aaaf4f7d3'
T062_OUTB_SHA256 = '0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c'
V353_SOURCE_SIGNATURES = (
    'm%AllOuts( TwHtRPxi(I) ) =  m%RtHS%AngPosEF(1,p%TwrGagNd(I))*R2D',
    'm%AllOuts( TwHtRPyi(I) ) = -m%RtHS%AngPosEF(3,p%TwrGagNd(I))*R2D',
    'm%AllOuts( TwHtRPzi(I) ) =  m%RtHS%AngPosEF(2,p%TwrGagNd(I))*R2D',
    'FrcFGagT = FrcONcRt - p%YawBrMass*( p%Gravity*m%CoordSys%z2 + LinAccEO )',
    'TmpVec2  = FTTower(:,J) - p%MassT(J)*( p%Gravity*m%CoordSys%z2 + LinAccET(:,J) )',
    'm%AllOuts( TwHtFLxt(I) ) =     DOT_PRODUCT( FrcFGagT, m%CoordSys%t1(p%TwrGagNd(I),:) )',
    'm%AllOuts( TwHtTPxi(I) ) =      m%RtHS%rT(1,p%TwrGagNd(I))',
    'm%AllOuts( TwHtALxt(I) ) =      DOT_PRODUCT( LinAccET(:,p%TwrGagNd(I)), m%CoordSys%t1(p%TwrGagNd(I),:) )',
)

def v353_original_source_contract(official_source, historical_receipt):
    """Read original v3.5.3 Fortran + original T062 OUTB receipt, no physics RUN.

    TwHtRP* are angle-vector components (deg), not a proven exact Euler DCM.
    TwHtFL*/ML* are tower internal section resultants, already integrating
    gravity, inertial acceleration and tower-top terms (see source lines).
    """
    import json
    raw = Path(official_source).read_bytes()
    if git_blob_sha1(raw) != V353_ELASTODYN_GIT_BLOB or hashlib.sha256(raw).hexdigest() != V353_ELASTODYN_SHA256:
        raise ValueError('official ElastoDyn v3.5.3 Git blob/SHA mismatch')
    source = raw.decode('utf-8')
    missing = [s for s in V353_SOURCE_SIGNATURES if s not in source]
    if missing:
        raise ValueError('official v3.5.3 output/source contract changed: ' + repr(missing))
    receipt_raw = Path(historical_receipt).read_bytes()
    receipt = json.loads(receipt_raw.decode('utf-8'))
    if receipt.get('case') != 'U09p343881_ETM_S01' or receipt.get('outb_sha256') != T062_OUTB_SHA256:
        raise ValueError('T062 OUTB source identity mismatch')
    full = receipt['full_synchronous_native_series']
    if full['sample_count'] != 12001 or full['gage_count'] != 9:
        raise ValueError('T062 sample count or gage identity mismatch')
    stats = full['native_channel_summary']
    units = {
        'FLxt':'(kN)', 'FLyt':'(kN)', 'FLzt':'(kN)',
        'MLxt':'(kN-m)', 'MLyt':'(kN-m)', 'MLzt':'(kN-m)',
        'TPxi':'(m)', 'TPyi':'(m)', 'TPzi':'(m)',
        'RPxi':'(deg)', 'RPyi':'(deg)', 'RPzi':'(deg)',
        'ALxt':'(m/s^2)', 'ALyt':'(m/s^2)', 'ALzt':'(m/s^2)',
    }
    rows = []
    for g in range(1,10):
        sample = {}
        for suffix, unit in units.items():
            entry = stats.get(f'TwHt{g}{suffix}')
            if entry is None or entry.get('unit') != unit:
                raise ValueError(f'missing or incorrect original unit for TwHt{g}{suffix}')
            value = float(entry['first'])
            if not math.isfinite(value):
                raise ValueError('nonfinite original channel first sample')
            sample[suffix] = value
        rows.append({
            'gage':g, 'TPzi_m':sample['TPzi'],
            'RPxi_deg':sample['RPxi'], 'RPyi_deg':sample['RPyi'],
            'RPzi_deg':sample['RPzi'], 'FLxt_kN':sample['FLxt'],
            'FLyt_kN':sample['FLyt'], 'FLzt_kN':sample['FLzt'],
            'MLyt_kNm':sample['MLyt'],
        })
    return {
        'source_version':'OpenFAST ElastoDyn v3.5.3 original Fortran',
        'official_source_git_blob_sha1':git_blob_sha1(raw),
        'official_source_sha256':hashlib.sha256(raw).hexdigest(),
        'outb_sha256':T062_OUTB_SHA256,
        'historical_receipt_sha256':hashlib.sha256(receipt_raw).hexdigest(),
        'verified_gages':len(rows),
        'verified_native_channels':len(rows)*len(units),
        'first_sample_gages':rows,
        'first_sample_axial_delta_gage9_minus_gage1_kN':rows[-1]['FLzt_kN']-rows[0]['FLzt_kN'],
        'frame_status':'RP_ANGULAR_POSITION_VECTOR_DEG / EXACT_DCM_NOT_PROVEN',
        'owner_status':'SECTION_RESULTANT_INCLUDES_GRAVITY_INERTIA_TOP_TERMS / NOT_PURE_AERODYNAMIC_EXTERNAL',
        'physics_status':'HOLD_NO_VERIFIED_DCM_OR_SIGNED_FREE_BODY',
    }


# Source-level S07 readiness audit for the already recovered four-case 31-gage
# CSVs. This does NOT attempt to invent missing dynamic orientation channels.
S07_31_MANIFEST_BLOB = '24723fb07c760ea22dbed043031ceff7939f1ac6'
S07_T071_WORKFLOW_BLOB = '59e76a54ba4f64902ed0750e92eb5158a1da1e96'
S07_T072_WORKFLOW_BLOB = '5baab0ea2299b6d36544b6d092f7503d8dcaf86c'
S07_31_CASES = ('U09p343881_ETM_S06', 'U11p4_ETM_S04',
                'U19p202140_ETM_S04', 'U19p202140_ETM_S06')
S07_31_BATCH_GAGES = {'A':9, 'B':9, 'C':9, 'D':4}
S07_31_MANIFEST_COLUMNS = ('case','batch','run_id','artifact_id',
                           'zip_sha256','gzip_sha256','uncompressed_csv_sha256','rows')
S07_31_SIX = ('Fx_kN','Fy_kN','Fz_kN','Mx_kNm','My_kNm','Mz_kNm')


def _s07_validate_manifest_rows(raw):
    reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if tuple(reader.fieldnames or ()) != S07_31_MANIFEST_COLUMNS:
        raise ValueError('S07_31_MANIFEST_HEADER_MISMATCH')
    rows=list(reader)
    if len(rows)!=16:
        raise ValueError('S07_31_EXPECT_16_SOURCE_ARTIFACTS')
    expected={(case,batch) for case in S07_31_CASES for batch in S07_31_BATCH_GAGES}
    found=set()
    total=0
    for r in rows:
        if None in r or any(v is None for v in r.values()):
            raise ValueError('S07_31_MALFORMED_SOURCE_ROW')
        key=(r['case'],r['batch'])
        if key not in expected or key in found:
            raise ValueError('S07_31_UNKNOWN_OR_DUPLICATE_CASE_BATCH')
        found.add(key)
        run='37582521146' if r['case']==S07_31_CASES[0] else '37622366681'
        if r['run_id']!=run or not r['artifact_id'].isdigit() or int(r['artifact_id'])<=0:
            raise ValueError('S07_31_RUN_OR_ARTIFACT_ID_MISMATCH')
        for field in ('zip_sha256','gzip_sha256','uncompressed_csv_sha256'):
            s=r[field]
            if len(s)!=64 or any(c not in '0123456789abcdef' for c in s):
                raise ValueError('S07_31_INVALID_SOURCE_SHA256')
        n=12001*S07_31_BATCH_GAGES[r['batch']]
        if not r['rows'].isdigit() or int(r['rows'])!=n:
            raise ValueError('S07_31_BAD_SAMPLE_COUNT')
        total+=n
    if found!=expected or total!=1488124:
        raise ValueError('S07_31_COVERAGE_OR_TOTAL_MISMATCH')
    return rows,total


def audit_31_gage_frame_readiness(manifest, t071, t072):
    """Read exact historical workflow and artifact manifest; fail closed on DCM."""
    import json
    raw=Path(manifest).read_bytes()
    a=Path(t071).read_bytes()
    b=Path(t072).read_bytes()
    for data, expected, label in ((raw,S07_31_MANIFEST_BLOB,'manifest'),
                                  (a,S07_T071_WORKFLOW_BLOB,'T071'),
                                  (b,S07_T072_WORKFLOW_BLOB,'T072')):
        if git_blob_sha1(data)!=expected:
            raise ValueError('S07_31_SOURCE_GIT_BLOB_CHANGED_'+label)
    rows,total=_s07_validate_manifest_rows(raw)
    for data,label in ((a,'T071'),(b,'T072')):
        source=data.decode('utf-8-sig')
        # The source workflow actually exports six local-frame resultants.
        if not all(c in source for c in S07_31_SIX):
            raise ValueError('S07_31_MISSING_SIX_EXTRACTED_CHANNELS_'+label)
        if not all(c in source for c in ('FLxt','FLyt','FLzt','MLxt','MLyt','MLzt')):
            raise ValueError('S07_31_MISSING_ELASTODYN_OUTPUT_MAPPING_'+label)
        # No TwHt*RP* columns are extracted in either historical workflow.
        if any(c in source for c in ('RPxi','RPyi','RPzi')):
            raise ValueError('S07_31_WORKFLOW_ORIENTATION_CONTRACT_CHANGED_'+label)
    # Negative tests on actual-source rows: count, duplicate, SHA, case/run.
    for change in ('count','duplicate','sha','run'):
        altered=[dict(r) for r in rows]
        if change=='count': altered[0]['rows']='108008'
        elif change=='duplicate': altered[1]['batch']='A'
        elif change=='sha': altered[0]['zip_sha256']='UNKNOWN'
        else: altered[0]['run_id']='0'
        buf=io.StringIO(newline='')
        writer=csv.DictWriter(buf,fieldnames=S07_31_MANIFEST_COLUMNS,lineterminator='\n')
        writer.writeheader();writer.writerows(altered)
        try: _s07_validate_manifest_rows(buf.getvalue().encode())
        except ValueError: pass
        else: raise AssertionError('S07_31_NEGATIVE_TEST_NOT_REJECTED_'+change)
    return {
      'stage':'S07_SOURCE_31GAGE_PROVENANCE_CHECKED_DCM_UNAVAILABLE_HOLD',
      'SOURCE':{
        'manifest_git_blob_sha1':git_blob_sha1(raw),
        'manifest_sha256':hashlib.sha256(raw).hexdigest(),
        't071_workflow_git_blob_sha1':git_blob_sha1(a),
        't071_workflow_sha256':hashlib.sha256(a).hexdigest(),
        't072_workflow_git_blob_sha1':git_blob_sha1(b),
        't072_workflow_sha256':hashlib.sha256(b).hexdigest(),
        'reading_level':'original committed 16-artifact SHA manifest and full T071/T072 extraction workflow source; NOT 16 ZIP bytes or original OUTB reread'},
      'OFFICIAL':'OpenFAST v3.5.3 ElastoDyn FL/ML are section resultants; v3.5.3 source contract checked separately in existing S07 gate',
      'REF':'existing S07 source contracts; no new peer-reviewed full text',
      'STANDARD':'NONE: no authorized IEC/GB clauses read in this audit',
      'RUN':{'kind':'Python source-contract audit, NOT native OpenFAST/Abaqus',
             'historical_actions_runs':[37582521146,37622366681],
             'negative_tests_passed':4,'native_solver_runs':0},
      'FIG':'NONE: no physical response figures',
      'TAB':{'cases':len(S07_31_CASES),'source_artifacts':len(rows),
             'gages_per_case':31,'case_gage_series':124,
             'samples_per_gage':12001,'time_start_s':100.0,'time_end_s':700.0,
             'sample_dt_s':0.05,'total_six_component_time_rows':total,
             'extracted_local_force_moment_components':list(S07_31_SIX),
             'extracted_dynamic_RP_orientation_channels':0,
             'global_wrench_export_rows':0},
      'error_budget':{'manifest_count':'exact integer checks, no numerical rounding',
                      'frame_rotation':'UNBOUNDED_FOR_31_GAGES_NO_SYNCHRONOUS_DCM',
                      'free_body_inertia_and_gravity':'UNVERIFIED',
                      'material_fatigue':'NOT_COMPUTED'},
      'HOLD':'Recovered four-case 31-gage CSVs contain FL/ML but no synchronized RP/DCM. The workflows do not prove whether original OUTB has RP. Require source-verified RP/DCM for all 31 gages at each time and signed free-body/inertia/gravity ownership before any Abaqus external load mapping; do not rerun high-cost solver here.'
    }




def archive_inventory_gate(manifest, t071, t072, nine_receipt, actions071, actions072):
    """Source/archive availability only: NEVER a recovered 31-gage DCM."""
    import json
    import copy
    source=[Path(x).read_bytes() for x in (manifest,t071,t072)]
    for raw,expected in zip(source,(S07_31_MANIFEST_BLOB,
                                    S07_T071_WORKFLOW_BLOB,S07_T072_WORKFLOW_BLOB)):
        if git_blob_sha1(raw)!=expected:
            raise ValueError('S07_ARCHIVE_GIT_SOURCE_CHANGED')
    rows,total=_s07_validate_manifest_rows(source[0])
    a,b=(x.decode('utf-8-sig') for x in source[1:])
    base_sha='6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65'
    original=Path(nine_receipt).read_bytes()
    nine=json.loads(original)
    if (nine.get('SOURCE',{}).get('elastodyn_input_sha256')!=base_sha
        or nine.get('RUN',{}).get('gages')!=9
        or len(nine.get('TAB',{}).get('first_sample',[]))!=9
        or any(len(x.get('RP_deg',[]))!=3 for x in nine['TAB']['first_sample'])):
        raise ValueError('S07_ORIGINAL_9GAGE_RP_PROOF_MISSING')
    checks=(
        (a,('base_elastodyn_sha256',base_sha,
            'Copy-Item "$base/DTU_10MW_RWT_ElastoDyn.dat"',
            'TwrGagNd patch failed','path: extract/*','DTU_10MW_RWT.outb')),
        (b,('base/CASES/U09p343881_ETM_S01/*',
            'TwrGagNd patch failed','path: extract/*','DTU_10MW_RWT.outb')))
    for src,need in checks:
        if not all(token in src for token in need) or 'OutList' in src:
            raise ValueError('S07_ORIGINAL_OUTLIST_INVARIANCE_UNPROVEN')
        if any(token in src for token in ('RPxi','RPyi','RPzi')):
            raise ValueError('S07_HISTORICAL_EXPORT_CONTRACT_CHANGED')
    raws=[Path(actions071).read_bytes(),Path(actions072).read_bytes()]
    snapshots=[json.loads(raw) for raw in raws]
    def verify(data):
        seen={}
        for idx,n in enumerate((4,12)):
            if data[idx].get('total_count')!=n or len(data[idx].get('artifacts',[]))!=n:
                raise ValueError('S07_ACTIONS_COUNT_MISMATCH')
            for item in data[idx]['artifacts']:
                if item.get('expired') is not False or item.get('size_in_bytes',0)<=0:
                    raise ValueError('S07_ACTIONS_EXPIRED_OR_EMPTY')
                if str(item['id']) in seen:
                    raise ValueError('S07_ACTIONS_DUPLICATE_ID')
                seen[str(item['id'])]=item
        for r in rows:
            item=seen.get(r['artifact_id'])
            expected=('T071-' if r['run_id']=='37582521146' else 'T072-')+r['case']+'-'+r['batch']
            if item is None or item['name']!=expected:
                raise ValueError('S07_ACTIONS_MANIFEST_MISMATCH')
        if len(seen)!=16:
            raise ValueError('S07_ACTIONS_EXTRA_ARTIFACT')
    verify(snapshots)
    for fault in ('missing','expired','id'):
        bad=copy.deepcopy(snapshots)
        if fault=='missing': bad[0]['artifacts'].pop()
        elif fault=='expired': bad[0]['artifacts'][0]['expired']=True
        else: bad[0]['artifacts'][0]['id']=-1
        try: verify(bad)
        except ValueError: pass
        else: raise AssertionError('S07_ARCHIVE_TAMPER_NOT_REJECTED_'+fault)
    return {
      'source_level':'real Actions artifact metadata + original workflow bytes + original 9-gage OUTB-derived receipt; 31-gage OUTB bytes NOT read',
      'nine_gage_receipt_sha256':hashlib.sha256(original).hexdigest(),
      'actions_api_sha256':[hashlib.sha256(x).hexdigest() for x in raws],
      'base_elastodyn_sha256':base_sha,
      'artifacts_matched':16,'four_case_31gage_local_rows':total,
      'original_31gage_OUTB_RP_TP_expected_from_unchanged_OutList':True,
      'retained_31gage_OUTB_in_T071_T072_artifacts':False,
      'retained_synchronous_RP_TP_rows':0,
      'negative_tests_passed':3,
      'original_31gage_OUTB_directly_read':False,
      'error_budget':'No source 31-gage RP/TP, DCM or external-load physics error estimate possible',
      'HOLD':'Ephemeral 31-gage OUTB was not uploaded; existing CSV has no synchronous RP/TP. Find a separate original OUTB copy or request an explicitly approved minimal data-capture rerun.'
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--official-v353-source',type=Path)
    p.add_argument('--outb-receipt',type=Path)
    p.add_argument('--contract-json',type=Path)
    p.add_argument('--static-source',type=Path,help='real 30-row static source regression')
    p.add_argument('--input',type=Path,help='explicit dynamic source CSV (frame algebra only)')
    p.add_argument('--output',type=Path,help='frame algebra CSV (NOT external load)')
    p.add_argument('--source-31-manifest',type=Path)
    p.add_argument('--t071-workflow',type=Path)
    p.add_argument('--t072-workflow',type=Path)
    p.add_argument('--source-31-receipt',type=Path)
    p.add_argument('--nine-gage-source-receipt',type=Path)
    p.add_argument('--actions071-json',type=Path)
    p.add_argument('--actions072-json',type=Path)
    a=p.parse_args()
    if a.self_test: print(selftest())
    if a.official_v353_source or a.outb_receipt:
        if not (a.official_v353_source and a.outb_receipt):
            p.error('--official-v353-source and --outb-receipt must be supplied together')
        import json
        receipt=v353_original_source_contract(a.official_v353_source,a.outb_receipt)
        print('V353_SOURCE_CONTRACT',json.dumps({k:v for k,v in receipt.items() if k!='first_sample_gages'},sort_keys=True))
        if a.contract_json:
            a.contract_json.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    if a.static_source: print('STATIC_REAL_SOURCE',static_source_regression(a.static_source))
    if a.input:
        if a.output is None: p.error('--input requires --output')
        print('DYNAMIC_FRAME_ONLY',transform_csv(a.input,a.output))
    if a.source_31_manifest or a.t071_workflow or a.t072_workflow or a.source_31_receipt:
        if not (a.source_31_manifest and a.t071_workflow and a.t072_workflow):
            p.error('S07 31-gage audit requires manifest and both historical workflows')
        import json
        receipt=audit_31_gage_frame_readiness(a.source_31_manifest,a.t071_workflow,a.t072_workflow)
        if any((a.nine_gage_source_receipt,a.actions071_json,a.actions072_json)):
            if not all((a.nine_gage_source_receipt,a.actions071_json,a.actions072_json)):
                p.error('archive inventory requires original nine-gage receipt and both Actions JSON')
            receipt['archival_recovery']=archive_inventory_gate(
                a.source_31_manifest,a.t071_workflow,a.t072_workflow,
                a.nine_gage_source_receipt,a.actions071_json,a.actions072_json)
            receipt['HOLD']=receipt['archival_recovery']['HOLD']
            receipt['RUN']['negative_tests_passed']+=receipt['archival_recovery']['negative_tests_passed']

        print('S07_31_SOURCE_READINESS',json.dumps(receipt['TAB'],sort_keys=True))
        if a.source_31_receipt:
            a.source_31_receipt.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    if not (a.self_test or a.static_source or a.input or a.official_v353_source or a.source_31_manifest): p.error('no action requested')


if __name__=='__main__': main()
