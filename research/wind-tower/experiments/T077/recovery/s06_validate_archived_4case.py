#!/usr/bin/env python3
"""Fail-closed S06 archive QC: 16 T071/T072 ZIPs, 124 segment histories, 31 historical controls.
This is NOT OpenFAST/Abaqus validation or an applicable-code check. Python stdlib only.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import zipfile
from collections import Counter
from pathlib import Path

HEADER = ('case,batch,segment,gage_index,gage_z_m,time_s,Fx_kN,Fy_kN,Fz_kN,'
          'Mx_kNm,My_kNm,Mz_kNm,V_kN,M_kNm,T_abs_kNm,N_comp_kN').split(',')
WRENCH = ('Fx_kN', 'Fy_kN', 'Fz_kN', 'Mx_kNm', 'My_kNm', 'Mz_kNm')
EXPECTED_SEG = {'A': range(1, 10), 'B': range(10, 19), 'C': range(19, 28), 'D': range(28, 32)}
EXPECTED_CASES = {'U09p343881_ETM_S06', 'U11p4_ETM_S04',
                  'U19p202140_ETM_S04', 'U19p202140_ETM_S06'}

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def read_rows(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def check(root, manifest_path, control_path, gravity_path):
    manifest = read_rows(manifest_path)
    if len(manifest) != 16 or {(x['case'], x['batch']) for x in manifest} != {
        (c, b) for c in EXPECTED_CASES for b in 'ABCD'}:
        raise ValueError('Manifest must contain exactly four cases x A/B/C/D')
    controls = {}
    case_seg = Counter()
    rows_total = 0
    for entry in manifest:
        case, batch = entry['case'], entry['batch']
        prefix = 'T071' if case.startswith('U09') else 'T072'
        path = root / f'{prefix}-{case}-{batch}.zip'
        data = path.read_bytes()
        if sha256(data) != entry['zip_sha256']:
            raise ValueError(f'ZIP SHA-256 mismatch: {path.name}')
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if archive.testzip() is not None:
                raise ValueError(f'ZIP CRC failed: {path.name}')
            gz_files = [n for n in archive.namelist() if n.endswith('_31seg.csv.gz')]
            if len(gz_files) != 1:
                raise ValueError(f'ZIP must contain one history: {path.name}')
            compressed = archive.read(gz_files[0])
            if sha256(compressed) != entry['gzip_sha256']:
                raise ValueError(f'GZIP SHA-256 mismatch: {path.name}')
            csv_hash = hashlib.sha256()
            def decoded_lines():
                with gzip.GzipFile(fileobj=io.BytesIO(compressed), mode='rb') as gz:
                    for line in gz:
                        csv_hash.update(line)
                        yield line.decode('utf-8')
            reader = csv.reader(decoded_lines())
            if next(reader) != HEADER:
                raise ValueError(f'Unexpected or duplicate CSV header: {path.name}')
            seen = Counter()
            prev_index = {}
            heights = {}
            expected = {f'CSEG_{n:02d}' for n in EXPECTED_SEG[batch]}
            for fields in reader:
                if len(fields) != len(HEADER):
                    raise ValueError(f'CSV field width: {path.name}')
                rec = dict(zip(HEADER, fields))
                seg = rec['segment']
                if rec['case'] != case or rec['batch'] != batch or seg not in expected:
                    raise ValueError(f'Case/batch/segment mismatch: {path.name}')
                t = float(rec['time_s'])
                index = round((t - 100.0) / 0.05)
                if not math.isfinite(t) or not 0 <= index <= 12000 or abs(t - (100.0 + index*0.05)) > 1e-7:
                    raise ValueError(f'Invalid time: {path.name}/{seg}/{t}')
                if index != prev_index.get(seg, -1) + 1:
                    raise ValueError(f'Missing/duplicate/non-monotonic sample: {path.name}/{seg}/{t}')
                prev_index[seg] = index
                z = float(rec['gage_z_m'])
                if not math.isfinite(z) or not 0 < z < 112.1:
                    raise ValueError(f'Invalid gage coordinate: {path.name}/{seg}')
                if seg in heights and abs(z - heights[seg]) > 1e-9:
                    raise ValueError(f'Gage height drift: {path.name}/{seg}')
                heights[seg] = z
                values = {k: float(rec[k]) for k in WRENCH}
                if not all(math.isfinite(v) for v in values.values()):
                    raise ValueError(f'Nonfinite 6DOF: {path.name}/{seg}/{t}')
                derived = {'V_kN': math.hypot(values['Fx_kN'], values['Fy_kN']),
                           'M_kNm': math.hypot(values['Mx_kNm'], values['My_kNm']),
                           'T_abs_kNm': abs(values['Mz_kNm']),
                           'N_comp_kN': max(0.0, -values['Fz_kN'])}
                for k, v in derived.items():
                    actual = float(rec[k])
                    if not math.isfinite(actual) or abs(actual-v) > max(1e-7, 1e-10*max(1, abs(v))):
                        raise ValueError(f'Derived-column mismatch: {path.name}/{seg}/{t}/{k}')
                seen[seg] += 1
                case_seg[(case, seg)] += 1
                rows_total += 1
                if case == 'U09p343881_ETM_S06' and 652.09 <= t <= 652.76:
                    controls[(seg, round(t, 2))] = values
            if set(seen) != expected or any(n != 12001 for n in seen.values()):
                raise ValueError(f'Incomplete 31-segment batch: {path.name}')
            if sum(seen.values()) != int(entry['rows']):
                raise ValueError(f'Batch row-count mismatch: {path.name}')
            if csv_hash.hexdigest() != entry['uncompressed_csv_sha256']:
                raise ValueError(f'Uncompressed CSV SHA-256 mismatch: {path.name}')
    if rows_total != 1488124 or len(case_seg) != 124 or any(n != 12001 for n in case_seg.values()):
        raise ValueError(f'Incomplete 4x31x12001 grid: rows={rows_total}, pairs={len(case_seg)}')
    gravity = {r['segment']: r for r in read_rows(gravity_path)}
    historical = read_rows(control_path)
    if len(historical) != 31 or len({r['segment'] for r in historical}) != 31:
        raise ValueError('Historical control CSV must contain 31 unique segments')
    max_fz = max_mres = 0.0
    for r in historical:
        seg = r['segment']
        values = controls[(seg, round(float(r['time_s']), 2))]
        fz_err = abs(values['Fz_kN'] - float(r['Fz_back_kN']))
        g = gravity[seg]
        gg = float(r['gammaG'])
        dm_x = gg*float(g['Mx_kNm']) + 1.4*(values['Mx_kNm'] - float(g['Mx_kNm']))
        dm_y = gg*float(g['My_kNm']) + 1.4*(values['My_kNm'] - float(g['My_kNm']))
        mres_err = abs(math.hypot(dm_x, dm_y) - float(r['M_factored_resultant_back_kNm']))
        max_fz = max(max_fz, fz_err)
        max_mres = max(max_mres, mres_err)
    if max_fz > 1e-6 or max_mres > 1e-6:
        raise ValueError(f'Historical control roundtrip mismatch: Fz={max_fz}, Mres={max_mres}')
    return {'status':'PASS-CSV-ARCHIVE-IDENTITY-ONLY / NATIVE-HOLD',
            'zip_count':16, 'case_segment_count':124, 'time_samples_per_segment':12001,
            'rows':rows_total, 't_start_s':100, 't_end_s':700, 'dt_s':0.05,
            'historical_control_points':31, 'max_abs_Fz_roundtrip_kN':max_fz,
            'max_abs_Mres_roundtrip_kNm':max_mres,
            'manifest_sha256':sha256(Path(manifest_path).read_bytes()),
            'control_csv_sha256':sha256(Path(control_path).read_bytes()),
            'gravity_csv_sha256':sha256(Path(gravity_path).read_bytes()),
            'warning':'No source OUTB hash, S03/S04 source-divergence closure, Abaqus or normative PASS'}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip-dir', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--historical-control', type=Path, required=True)
    parser.add_argument('--gravity', type=Path, required=True)
    args=parser.parse_args()
    print(json.dumps(check(args.zip_dir, args.manifest, args.historical_control, args.gravity), indent=2))
