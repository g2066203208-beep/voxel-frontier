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
        _nonempty(row,'frame_evidence'); _nonempty(row,'position_evidence')
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
        row['frame_evidence']='SYNTHETIC';row['force_owner']='EXTERNAL';write_row(row)
        try: transform_csv(inp,out)
        except ValueError: pass
        else: raise AssertionError('external ownership accepted')
    return 'PASS synthetic rotation/moment/reference/sign/invariance/invalid input/CLI gates'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--static-source',type=Path,help='real 30-row static source regression')
    p.add_argument('--input',type=Path,help='explicit dynamic source CSV (frame algebra only)')
    p.add_argument('--output',type=Path,help='frame algebra CSV (NOT external load)')
    a=p.parse_args()
    if a.self_test: print(selftest())
    if a.static_source: print('STATIC_REAL_SOURCE',static_source_regression(a.static_source))
    if a.input:
        if a.output is None: p.error('--input requires --output')
        print('DYNAMIC_FRAME_ONLY',transform_csv(a.input,a.output))
    if not (a.self_test or a.static_source or a.input): p.error('no action requested')


if __name__=='__main__': main()
