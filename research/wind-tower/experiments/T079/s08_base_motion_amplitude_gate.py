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


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--source',type=Path)
    p.add_argument('--outdir',type=Path)
    p.add_argument('--azimuth-deg',type=float,default=0)
    a=p.parse_args()
    if a.self_test:self_test()
    if a.source or a.outdir:
        if not a.source or not a.outdir:p.error('--source and --outdir required together')
        export(a.source,a.outdir,a.azimuth_deg)
    elif not a.self_test:p.error('specify --self-test and/or --source --outdir')

if __name__=='__main__':main()
