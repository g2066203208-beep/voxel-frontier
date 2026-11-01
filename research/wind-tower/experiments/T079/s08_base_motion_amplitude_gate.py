#!/usr/bin/env python3
"""S08: source-locked, solver-agnostic base-acceleration amplitude preparation.

ESM MP processed record only; NOT an approved design wave or Abaqus *BASE MOTION
validation. Generate *AMPLITUDE tables (not a solver load card) in mm/s^2.
Frame: HNE=East, HNN=North, HNZ=vertical-positive-up ASSUMED, pending
station header and structure-frame sign verification. The X/Y axes are a
chosen analysis frame, not a verified turbine/tower azimuth.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

EXPECTED_SHA = 'a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34'
EXPECTED_N = 32040
DT = 0.005
FIELDS = ('time_s', 'HNE_acc_m_s2', 'HNN_acc_m_s2', 'HNZ_acc_m_s2')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_source(path, require_real=True):
    data = Path(path).read_bytes()
    digest = sha256(data)
    if require_real and digest != EXPECTED_SHA:
        raise ValueError('SOURCE_SHA256_MISMATCH: expected locked real ESM SI CSV')
    reader = csv.DictReader(data.decode('utf-8-sig').splitlines())
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise ValueError('SOURCE_HEADER_MISMATCH')
    rows = []
    for line in reader:
        values = tuple(float(line[k]) for k in FIELDS)
        if not all(math.isfinite(v) for v in values):
            raise ValueError('NONFINITE_ACCELERATION_OR_TIME')
        rows.append(values)
    if len(rows) < 3 or (require_real and len(rows) != EXPECTED_N):
        raise ValueError('SAMPLE_COUNT_MISMATCH')
    for i, row in enumerate(rows):
        if abs(row[0] - i * DT) > 2e-10:
            raise ValueError('TIME_GRID_OR_ORDER_MISMATCH')
    return rows, digest


def rotate_accel(e, n, z, angle_deg):
    if not math.isfinite(angle_deg) or abs(angle_deg) > 360:
        raise ValueError('INVALID_ANALYSIS_AZIMUTH')
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return (c*e+s*n, -s*e+c*n, z)


def amplitude_bytes(rows, axis, azimuth_deg):
    if axis not in (0, 1, 2):
        raise ValueError('INVALID_AXIS')
    label = ('X', 'Y', 'Z')[axis]
    header = (f'** S08 diagnostic processed ESM MP; {label} acceleration mm/s^2; NOT DESIGN\n'
              f'** ENU assumed; X azimuth CCW from East={azimuth_deg:g}deg; Y=+90deg; Z=up assumed\n'
              f'*AMPLITUDE, NAME=S08_ESM_{label}_ACC_MM_S2, DEFINITION=TABULAR, TIME=TOTAL TIME\n')
    out = [header]
    for t, e, n, z in rows:
        a = rotate_accel(e, n, z, azimuth_deg)[axis] * 1000.0
        out.append(f'{t:.6f}, {a:.12g}\n')
    return ''.join(out).encode('ascii')


def check_amplitude(data, rows, axis, azimuth_deg):
    lines = [x for x in data.decode('ascii').splitlines() if x and not x.startswith('*')]
    if len(lines) != len(rows):
        raise ValueError('AMPLITUDE_ROW_COUNT_MISMATCH')
    max_abs_err = 0.0
    for line, (t, e, n, z) in zip(lines, rows):
        t1, a1 = (float(v.strip()) for v in line.split(','))
        exact = rotate_accel(e, n, z, azimuth_deg)[axis]*1000
        if abs(t1-t) > 1e-9:
            raise ValueError('AMPLITUDE_TIME_MISMATCH')
        err = abs(a1-exact)
        max_abs_err = max(max_abs_err, err)
        if err > 2e-8 + 1e-11*abs(exact):
            raise ValueError('AMPLITUDE_ROUNDTRIP_ERROR')
    return max_abs_err


def free_mass_relative_integrate(acc, dt):
    # Discrete free-mass oracle: u''=-a_ground, trapezoidal velocity/displacement.
    u = v = 0.0
    for prev, curr in zip(acc, acc[1:]):
        v_next = v - 0.5*(prev+curr)*dt
        u += 0.5*(v+v_next)*dt
        v = v_next
    return u, v


def self_test():
    for angle in (0, 30, 90, 180):
        for e, n, z in ((1.2, -0.8, 0.4), (0, 1, -2)):
            x, y, zz = rotate_accel(e, n, z, angle)
            assert math.isclose(x*x+y*y, e*e+n*n, rel_tol=2e-15, abs_tol=2e-15)
            assert zz == z
            assert math.isclose(rotate_accel(x,y,zz,-angle)[0], e, abs_tol=1e-14)
            assert math.isclose(rotate_accel(x,y,zz,-angle)[1], n, abs_tol=1e-14)
    assert rotate_accel(1,0,0,0)==(1,0,0)
    assert abs(rotate_accel(1,0,0,90)[1]+1)<1e-14
    u,v = free_mass_relative_integrate([2.0]*21, 0.005)
    assert math.isclose(u,-0.01,abs_tol=1e-15) and math.isclose(v,-0.2,abs_tol=1e-15)
    assert -2.0+2.0 == 0  # u'' + a_g: absolute acceleration of a free mass
    synthetic = [(i*DT, 1.2, -0.8, 0.4) for i in range(4)]
    for axis in range(3):
        blob = amplitude_bytes(synthetic, axis, 30)
        assert check_amplitude(blob, synthetic, axis, 30) < 1e-8
    for invalid in (float('nan'), float('inf'), 361):
        try: rotate_accel(1,0,0,invalid)
        except ValueError: pass
        else: raise AssertionError('bad azimuth accepted')
    for bad in ('time_s,HNE_acc_m_s2,HNN_acc_m_s2,HNZ_acc_m_s2\n0,0,0,0\n0.005,0,0,0\n0.010,0,0,nan\n',
                'time_s,HNE_acc_m_s2,HNN_acc_m_s2,HNZ_acc_m_s2\n0,0,0,0\n0.005,0,0,0\n0.009,0,0,0\n'):
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(mode='w+', suffix='.csv') as f:
            f.write(bad);f.flush()
            try: read_source(f.name, require_real=False)
            except ValueError: pass
            else: raise AssertionError('bad source accepted')
    print('S08_BASE_MOTION_SELF_TEST_PASS: frame orthogonality, sign, units, 3 amplitudes, 5 rejection cases')


def export(source, outdir, angle_deg):
    rows, source_sha = read_source(source)
    outdir.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for axis, label in enumerate('XYZ'):
        blob = amplitude_bytes(rows, axis, angle_deg)
        error = check_amplitude(blob, rows, axis, angle_deg)
        path = outdir/f'S08_ESM_{label}_ACC_MM_S2_AMP.inp'
        path.write_bytes(blob)
        values = [rotate_accel(e,n,z,angle_deg)[axis] for _,e,n,z in rows]
        artifacts.append({'axis':label, 'file':path.name, 'bytes':len(blob),
                          'sha256':sha256(blob), 'peak_abs_acc_m_s2':max(map(abs,values)),
                          'max_roundtrip_acc_mm_s2':error})
    report = {'source':'ESM v3 DOI 10.13127/esm.3; IT-2012-0008/NVL/MP processed',
              'source_sha256':source_sha, 'npts':len(rows), 'dt_s':DT,
              'last_time_s':rows[-1][0], 'azimuth_deg_CCW_from_East':angle_deg,
              'assumed_frame':'HNE East, HNN North, HNZ Up; not tower-local validated',
              'acceleration_units':'mm/s^2 (Abaqus model units MUST be confirmed)',
              'relative_equation':'M u_rel_ddot+C u_rel_dot+K u_rel=-M r a_ground',
              'not_generated':'No *BASE MOTION or *BOUNDARY card; do not attach before native semantics check',
              'source_status':'processed ESM MP; site target, low-frequency SNR and structural orientation HOLD',
              'Abaqus_E_WE_RUN':0,'S08_PASS':False,'artifacts':artifacts}
    (outdir/'S08_ESM_BASE_MOTION_AMPLITUDE_RECEIPT.json').write_text(
        json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'status':'REAL_ESM_3COMP_AMPLITUDE_NUMERIC_QC_PASS_NOT_DESIGN',
                      'source_sha256':source_sha,'npts':len(rows),'artifacts':artifacts},sort_keys=True))
    return report



# Explicit, opt-in T057 model-global Y-up / metre-second SI diagnostic branch.
# This is NOT a verified *BASE MOTION, *BOUNDARY, or seismic design load.
T057_FROZEN_INP_SHA256 = 'c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db'


def rotate_t057_yup_si(e, n, u, angle_deg):
    if not all(math.isfinite(v) for v in (e, n, u, angle_deg)) or abs(angle_deg) > 360:
        raise ValueError('INVALID_T057_ORIENTATION_OR_ACCELERATION')
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    # ENU -> right-handed model XYZ: Y=Up, Z=s E-c N; determinant +1.
    return (c*e+s*n, u, s*e-c*n)


def t057_amplitude_bytes(rows, axis, azimuth_deg):
    if axis not in (0, 1, 2):
        raise ValueError('INVALID_T057_AXIS')
    label = 'XYZ'[axis]
    header = (
        '** SOURCE-LOCKED ESM MP processed acceleration; NOT DESIGN / NOT ABAQUS-VALIDATED\n'
        '** T057 candidate Y=Up, SI m/s^2; E/N/U sign and structural azimuth ASSUMED\n'
        f'** X azimuth CCW from East={azimuth_deg:g} deg; Z=sin(theta)*E-cos(theta)*N\n'
        f'*AMPLITUDE, NAME=S08_T057_{label}_ACC_M_S2, DEFINITION=TABULAR, TIME=TOTAL TIME\n'
    )
    return (header + ''.join(
        f'{t:.6f}, {rotate_t057_yup_si(e,n,u,azimuth_deg)[axis]:.12g}\n'
        for t,e,n,u in rows
    )).encode('ascii')


def t057_check_amplitudes(blobs, rows, azimuth_deg):
    if len(blobs) != 3:
        raise ValueError('T057_NEEDS_THREE_SYNCHRONOUS_AXES')
    values = []
    max_roundtrip = 0.0
    max_time = 0.0
    for axis, blob in enumerate(blobs):
        lines = [x for x in blob.decode('ascii').splitlines()
                 if x and not x.startswith('*')]
        if len(lines) != len(rows):
            raise ValueError('T057_AMPLITUDE_ROW_COUNT_MISMATCH')
        vals = []
        for line, (t,e,n,u) in zip(lines, rows):
            parts = line.split(',')
            if len(parts) != 2:
                raise ValueError('T057_AMPLITUDE_WIDTH_MISMATCH')
            t1, a1 = (float(v.strip()) for v in parts)
            if not math.isfinite(t1) or not math.isfinite(a1):
                raise ValueError('T057_AMPLITUDE_NONFINITE')
            exact = rotate_t057_yup_si(e,n,u,azimuth_deg)[axis]
            terr, err = abs(t1-t), abs(a1-exact)
            max_time = max(max_time, terr)
            max_roundtrip = max(max_roundtrip, err)
            if terr > 1e-9 or err > 2e-11 + 1e-11*abs(exact):
                raise ValueError('T057_AMPLITUDE_ROUNDTRIP_MISMATCH')
            vals.append(a1)
        values.append(vals)
    max_norm_error = 0.0
    max_vector = 0.0
    for i, (_,e,n,u) in enumerate(rows):
        src_norm = math.hypot(e,n,u)
        mapped_norm = math.hypot(*(values[j][i] for j in range(3)))
        max_norm_error = max(max_norm_error, abs(mapped_norm-src_norm))
        max_vector = max(max_vector, src_norm)
    if max_norm_error > 3e-11:
        raise ValueError('T057_SYNCHRONOUS_VECTOR_NORM_MISMATCH')
    return {'max_roundtrip_acc_m_s2':max_roundtrip,
            'max_time_error_s':max_time,
            'max_synch_vector_norm_error_m_s2':max_norm_error,
            'max_synch_vector_peak_m_s2':max_vector}


def self_test_t057():
    for angle in (0, 30, 90, -45, 180):
        a = math.radians(angle)
        c, s = math.cos(a), math.sin(a)
        for e,n,u in ((1.2,-0.8,0.4),(0,1,-2)):
            x,y,z = rotate_t057_yup_si(e,n,u,angle)
            assert abs(c*x+s*z-e) < 2e-15
            assert abs(s*x-c*z-n) < 2e-15
            assert y == u
            assert abs(math.hypot(x,y,z)-math.hypot(e,n,u)) < 2e-15
            assert abs(c*c+s*s-1) < 2e-15
    assert rotate_t057_yup_si(1,2,3,0) == (1,3,-2)
    synthetic = [(i*DT, 1.2,-0.8,0.4) for i in range(4)]
    blobs = [t057_amplitude_bytes(synthetic,i,30) for i in range(3)]
    assert t057_check_amplitudes(blobs,synthetic,30)['max_synch_vector_norm_error_m_s2'] < 2e-11
    negatives = 0
    for invalid in (float('nan'),float('inf'),361):
        try: rotate_t057_yup_si(1,2,3,invalid)
        except ValueError: negatives += 1
        else: raise AssertionError('T057 invalid azimuth accepted')
    for fn in (
        lambda: t057_amplitude_bytes(synthetic,3,0),
        lambda: t057_check_amplitudes(blobs[:2],synthetic,30),
        lambda: t057_check_amplitudes([blobs[0].replace(b'1.2',b'999',1),*blobs[1:]],synthetic,30),
    ):
        try: fn()
        except ValueError: negatives += 1
        else: raise AssertionError('T057 invalid amplitude accepted')
    assert negatives == 6
    print('S08_T057_YUP_SI_SELFTEST_PASS: right-hand/inverse/norm, 3-axis roundtrip, 6 negative cases')


def export_t057_yup_si(source, outdir, angle_deg):
    rows, source_sha = read_source(source, require_real=True)
    outdir.mkdir(parents=True, exist_ok=True)
    blobs = [t057_amplitude_bytes(rows,i,angle_deg) for i in range(3)]
    qc = t057_check_amplitudes(blobs,rows,angle_deg)
    artifacts = []
    for axis, blob in enumerate(blobs):
        label = 'XYZ'[axis]
        filename = f'S08_ESM_T057_{label}_ACC_M_S2_AMP.inp'
        (outdir/filename).write_bytes(blob)
        artifacts.append({'axis':label,'filename':filename,'bytes':len(blob),
                          'sha256':sha256(blob)})
    sample_indices = (0,1,200,6734,6735,6736,32039)
    samples = [{'index':i,'time_s':rows[i][0],
                'xyz_m_s2':list(rotate_t057_yup_si(*rows[i][1:],angle_deg))}
               for i in sample_indices]
    report = {
        'SOURCE':'ESM v3 IT-2012-0008/NVL/MP processed three-component SI CSV; archived Actions 40847442979 artifact 12884814391',
        'SOURCE_SHA256':source_sha,'SOURCE_NPTS':len(rows),'SOURCE_DT_S':DT,
        'SOURCE_LAST_TIME_S':rows[-1][0],
        'T057_FROZEN_INP_SHA256':T057_FROZEN_INP_SHA256,
        'REF':'ESM v3 DOI 10.13127/esm.3',
        'STANDARD':'2025 IEC / GB site target spectrum and clauses NOT_VERIFIED',
        'OFFICIAL':'T057 original model audit indicates +Y vertical, gravity -Y; base-motion semantics not verified in native Abaqus',
        'RUN':'Python 3 deterministic full 32040x3 source-level amplitude and norm QC; native Abaqus E/WE=0',
        'FIG':'NONE','TAB':'7 synchronized original samples in receipt; full three-axis amplitude files remain in archived run artifact',
        'frame':'T057 candidate global XYZ right-handed Y-up; metre-second SI',
        'azimuth_deg_CCW_from_East':angle_deg,
        'assumptions':'HNE=East, HNN=North, HNZ=Up assumed; physical tower azimuth and HNZ sign unverified; no PGA scaling',
        'mapping':'X=cos(theta)*E+sin(theta)*N; Y=U; Z=sin(theta)*E-cos(theta)*N',
        'units':'m/s^2; no factor 1000; legacy Z-up/mm/s^2 is incompatible with this T057 branch',
        'artifacts':artifacts,'samples':samples,'error_budget':{
            **qc,'time_grid_tolerance_s':2e-10,
            'amplitude_roundtrip_tolerance_m_s2':'2e-11 + 1e-11*abs(a)',
            'vector_norm_tolerance_m_s2':3e-11,
            'physical_orientation_uncertainty':'NEED_ESTIMATE',
            'low_frequency_processing_uncertainty':'NEED_ESTIMATE'},
        'PASS':'FULL_SOURCE_STATIC_YUP_SI_NUMERIC_QC_ONLY',
        'HOLD':'NO DESIGN WAVE; station HNZ sign, physical azimuth, 0.040Hz highpass/long-period SNR, site target spectrum, mass/density consistency, native Abaqus BC/base-motion/PT/contact all unverified',
        'S08_PASS':False,'Abaqus_E_WE_RUN':0,
        'generated_keywords':'*AMPLITUDE only; no *BASE MOTION, *BOUNDARY, or production load cards'
    }
    receipt = outdir/'S08_ESM_T057_YUP_SI_AMPLITUDE_RECEIPT.json'
    receipt.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['PASS'],'npts':len(rows),'source_sha256':source_sha,
                      'qc':qc,'amplitude_sha256':[x['sha256'] for x in artifacts],
                      'receipt_sha256':sha256(receipt.read_bytes())},sort_keys=True))
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--source',type=Path)
    p.add_argument('--outdir',type=Path)
    p.add_argument('--azimuth-deg',type=float,default=0)
    p.add_argument('--frame',choices=('legacy-zup-mm','t057-yup-si'),default='legacy-zup-mm')
    p.add_argument('--confirm-t057-identity',action='store_true',help='explicitly acknowledge unverified T057 Y-up/SI assumptions')
    a=p.parse_args()
    if a.self_test:
        self_test()
        self_test_t057()
    if a.source or a.outdir:
        if not a.source or not a.outdir:p.error('--source and --outdir required together')
        if a.frame == 't057-yup-si':
            if not a.confirm_t057_identity:
                p.error('T057 Y-up/SI is provisional; add --confirm-t057-identity to acknowledge')
            export_t057_yup_si(a.source,a.outdir,a.azimuth_deg)
        else:
            export(a.source,a.outdir,a.azimuth_deg)
    elif not a.self_test:p.error('specify --self-test and/or --source --outdir')

if __name__=='__main__':main()
