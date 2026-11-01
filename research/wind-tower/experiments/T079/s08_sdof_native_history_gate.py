#!/usr/bin/env python3
"""S08 nonproduction Abaqus ODB history extractor + independent 201-point oracle gate.

Native extraction: abaqus python s08_sdof_native_history_gate.py extract --odb pilot.odb --out native.csv
Validation: python s08_sdof_native_history_gate.py validate --native native.csv --oracle S08_SDOF_PRIMARY_BASE_ANALYTIC_20261101.csv --manifest native.csv.provenance.json
Self-test: python s08_sdof_native_history_gate.py selftest (mock ODB only).
"""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys

CHANNELS = ('U1', 'V1', 'A1', 'TU1', 'TV1', 'TA1')
NPTS = 201
DT = 0.01
# Diagnostic budgets: about 2x independent Newmark-vs-exact errors at dt=0.01.
# These are NOT acceptance limits for the 158m tower or physical V&V.
BUDGET = {'U1': 2.5e-4, 'V1': 1.8e-3, 'A1': 1.0e-2,
          'TU1': 2.5e-4, 'TV1': 1.8e-3, 'TA1': 1.0e-2}
ORACLE_COLUMNS = {'U1': 'U1_rel_m', 'V1': 'V1_rel_m_s',
                  'A1': 'A1_rel_m_s2', 'TU1': 'TU1_total_m',
                  'TV1': 'TV1_total_m_s', 'TA1': 'TA1_total_m_s2'}
KINEMATIC_BUDGET = {'TU1': 5e-4, 'TV1': 3.6e-3, 'TA1': 2e-2}

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def region_node_label(region):
    point = getattr(region, 'point', None)
    for key in ('nodeLabel', 'label'):
        val = getattr(point, key, None)
        if isinstance(val, int):
            return val
    match = re.search(r'\bNode\s+\S+\.(\d+)\s*$',
                      str(getattr(region, 'name', '')), re.I)
    return int(match.group(1)) if match else None

def extract_from_odb_object(odb):
    if 'BASE_X' not in odb.steps:
        raise ValueError('MISSING_STEP_BASE_X')
    candidates = [(name, region) for name, region in
                  odb.steps['BASE_X'].historyRegions.items()
                  if region_node_label(region) == 2]
    if len(candidates) != 1:
        raise ValueError('TOP_NODE_REGION_AMBIGUOUS_OR_MISSING:%d' % len(candidates))
    region_name, region = candidates[0]
    missing = [key for key in CHANNELS if key not in region.historyOutputs]
    if missing:
        raise ValueError('MISSING_HISTORY_CHANNELS:' + ','.join(missing))
    series = {}
    for key in CHANNELS:
        series[key] = list(region.historyOutputs[key].data)
        if len(series[key]) != NPTS:
            raise ValueError('HISTORY_COUNT_%s:%d' % (key, len(series[key])))
    rows = []
    for i in range(NPTS):
        t = i * DT
        row = {'time_s': t}
        for key in CHANNELS:
            ts, value = series[key][i]
            if not math.isfinite(float(ts)) or abs(float(ts) - t) > 1e-8:
                raise ValueError('HISTORY_TIME_MISMATCH:%s:%d' % (key, i))
            if not math.isfinite(float(value)):
                raise ValueError('HISTORY_NONFINITE:%s:%d' % (key, i))
            row[key] = float(value)
        rows.append(row)
    return region_name, rows

def read_numeric_csv(path, required):
    with open(path, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError('BAD_HEADER')
        if any(k not in reader.fieldnames for k in required):
            raise ValueError('MISSING_COLUMNS')
        rows = []
        for r in reader:
            vals = {}
            for key in required:
                raw = r.get(key)
                if raw is None or not raw.strip():
                    raise ValueError('EMPTY_VALUE:%s' % key)
                v = float(raw)
                if not math.isfinite(v):
                    raise ValueError('NONFINITE:%s' % key)
                vals[key] = v
            rows.append(vals)
    if len(rows) != NPTS:
        raise ValueError('ROW_COUNT:%d' % len(rows))
    for i, row in enumerate(rows):
        if abs(row['time_s'] - i * DT) > 1e-8:
            raise ValueError('TIME_GRID:%d' % i)
    return rows

def compare(native, oracle):
    if len(native) != NPTS or len(oracle) != NPTS:
        raise ValueError('ROW_COUNT')
    errors = {k: 0.0 for k in CHANNELS}
    identities = {k: 0.0 for k in ('TU1', 'TV1', 'TA1')}
    for i, (n, o) in enumerate(zip(native, oracle)):
        if abs(n['time_s'] - o['time_s']) > 1e-8:
            raise ValueError('TIME_MISMATCH:%d' % i)
        for key in CHANNELS:
            errors[key] = max(errors[key], abs(n[key] - o[ORACLE_COLUMNS[key]]))
        identities['TU1'] = max(identities['TU1'], abs(n['TU1'] - n['U1'] - o['ground_u_m']))
        identities['TV1'] = max(identities['TV1'], abs(n['TV1'] - n['V1'] - o['ground_v_m_s']))
        identities['TA1'] = max(identities['TA1'], abs(n['TA1'] - n['A1'] - o['ag_m_s2']))
    failures = ([k + '_ORACLE' for k in CHANNELS if errors[k] > BUDGET[k]] +
                [k + '_REL_TOTAL' for k in identities if identities[k] > KINEMATIC_BUDGET[k]])
    return {'diagnostic_pass': not failures, 'failures': failures,
            'max_abs_oracle_error': errors, 'max_abs_relative_total_residual': identities,
            'oracle_budget': BUDGET, 'identity_budget': KINEMATIC_BUDGET,
            'scope': '1Hz synthetic SDOF only; numerical screening, not T057/S08 physical PASS'}

def write_native(path, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['time_s'] + list(CHANNELS), lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: format(row[k], '.17g') for k in writer.fieldnames})

def cmd_extract(args):
    try:
        from odbAccess import openOdb
    except ImportError:
        raise RuntimeError('NEED_LICENSED_ABAQUS_PYTHON_ODBACCESS')
    odb = openOdb(path=os.path.abspath(args.odb), readOnly=True)
    try:
        region, rows = extract_from_odb_object(odb)
    finally:
        odb.close()
    write_native(args.out, rows)
    receipt = {'status': 'NATIVE_ODB_HISTORY_EXTRACTED_NOT_VALIDATED',
               'odb_path': os.path.abspath(args.odb), 'odb_sha256': sha256(args.odb),
               'native_csv_sha256': sha256(args.out), 'step': 'BASE_X',
               'region': region, 'channels': CHANNELS, 'samples': len(rows),
               'abaqus_python': sys.version, 'physical_PASS': False}
    with open(args.out + '.provenance.json', 'w', encoding='utf-8') as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps(receipt, sort_keys=True))

def cmd_validate(args):
    native = read_numeric_csv(args.native, ['time_s'] + list(CHANNELS))
    oracle_cols = ['time_s', 'ag_m_s2', 'ground_u_m', 'ground_v_m_s'] + list(ORACLE_COLUMNS.values())
    oracle = read_numeric_csv(args.oracle, oracle_cols)
    report = compare(native, oracle)
    report.update({'native_csv_sha256': sha256(args.native),
                   'oracle_csv_sha256': sha256(args.oracle),
                   'native_odb_run': False, 'physical_PASS': False})
    if args.manifest:
        with open(args.manifest, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        if manifest.get('native_csv_sha256') != report['native_csv_sha256']:
            raise ValueError('PROVENANCE_CSV_SHA_MISMATCH')
        if not re.fullmatch(r'[0-9a-f]{64}', str(manifest.get('odb_sha256', ''))):
            raise ValueError('PROVENANCE_MISSING_ODB_SHA')
        report['native_odb_run'] = True  # reported provenance, NOT independent physical verification
        report['odb_sha256_reported'] = manifest['odb_sha256']
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report['diagnostic_pass']:
        raise SystemExit(2)

def selftest():
    from types import SimpleNamespace as NS
    times = [i * DT for i in range(NPTS)]
    fake = lambda val: NS(data=list(zip(times, val)))
    zero = [0.] * NPTS
    def region(outputs=None, label=2):
        return NS(name='Node ASSEMBLY.%d' % label, point=NS(nodeLabel=label),
                  historyOutputs={k: fake(zero) for k in CHANNELS} if outputs is None else outputs)
    odb = NS(steps={'BASE_X': NS(historyRegions={'Node ASSEMBLY.2': region()})})
    name, rows = extract_from_odb_object(odb)
    assert name == 'Node ASSEMBLY.2' and len(rows) == NPTS
    oracle = [{**{'time_s': t, 'ag_m_s2': 0., 'ground_u_m': 0., 'ground_v_m_s': 0.},
               **{v: 0. for v in ORACLE_COLUMNS.values()}} for t in times]
    assert compare(rows, oracle)['diagnostic_pass']
    failures = 0
    def must_fail(fn):
        nonlocal failures
        try: fn()
        except (ValueError, KeyError): failures += 1
        else: raise AssertionError('BAD_INPUT_ACCEPTED')
    must_fail(lambda: extract_from_odb_object(NS(steps={})))
    must_fail(lambda: extract_from_odb_object(NS(steps={'BASE_X': NS(historyRegions={})})))
    must_fail(lambda: extract_from_odb_object(NS(steps={'BASE_X': NS(historyRegions={'a': region(), 'b': region()})})))
    missing = {k: fake(zero) for k in CHANNELS if k != 'TA1'}
    must_fail(lambda: extract_from_odb_object(NS(steps={'BASE_X': NS(historyRegions={'a': region(missing)})})))
    short = {k: fake(zero) for k in CHANNELS}
    short['U1'] = NS(data=list(zip(times[:-1], zero[:-1])))
    must_fail(lambda: extract_from_odb_object(NS(steps={'BASE_X': NS(historyRegions={'a': region(short)})})))
    shifted = {k: fake(zero) for k in CHANNELS}
    shifted['A1'] = NS(data=list(zip([t + .1 for t in times], zero)))
    must_fail(lambda: extract_from_odb_object(NS(steps={'BASE_X': NS(historyRegions={'a': region(shifted)})})))
    nonfinite = {k: fake(zero) for k in CHANNELS}
    nonfinite['A1'] = NS(data=list(zip(times, [float('nan')] + zero[1:])))
    must_fail(lambda: extract_from_odb_object(NS(steps={'BASE_X': NS(historyRegions={'a': region(nonfinite)})})))
    flipped = [dict(r) for r in rows]; flipped[40]['A1'] = 1.
    assert not compare(flipped, oracle)['diagnostic_pass']
    flipped = [dict(r) for r in rows]; flipped[40]['TA1'] = 1.
    assert not compare(flipped, oracle)['diagnostic_pass']
    assert failures == 7
    print('S08_SDOF_ODB_MOCK_SELFTEST_PASS', '201 samples',
          '7 rejected malformed ODB cases', '2 diagnostic failure detections', 'NO_ABAQUS_NATIVE_RUN')

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('extract'); e.add_argument('--odb', required=True); e.add_argument('--out', required=True)
    v = sub.add_parser('validate'); v.add_argument('--native', required=True)
    v.add_argument('--oracle', required=True); v.add_argument('--manifest')
    sub.add_parser('selftest')
    a = p.parse_args()
    if a.cmd == 'selftest': selftest()
    elif a.cmd == 'extract': cmd_extract(a)
    else: cmd_validate(a)

if __name__ == '__main__': main()
