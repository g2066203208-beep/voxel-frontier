#!/usr/bin/env python3
"""Independent original ESM MP -> SI CSV oracle. Source QC only, never design PASS.

Usage: python s08_independent_original_zip_oracle.py ACTIONS_ARTIFACT.zip OUTPUT.csv
Source: ESM v3 DOI 10.13127/esm.3, IT-2012-0008 / NVL, MP three-component DYNA.
"""
import csv
import hashlib
import io
import json
import math
import pathlib
import sys
import zipfile

EXPECTED = {
    'HNE': 'f1c06ee4b201276657c3da627b24121e2b05377936ecc3adc11d78f7f3d3242a',
    'HNN': 'bfef0cf1623fbbd8c15f95ec49bb7a714d300fb98fea11d03b159a4e77ede275',
    'HNZ': '69443ba0a689d39ed202de7d40487a62ef39c969dc2605170cf9a211bce4fd81',
}
SOURCE_ZIP_SHA = 'dec0f0bf59bea4e6a5049c824b6656c7e7798eb5379beba5162aff7304b113c6'
SAMPLE_INDEX = (0, 1, 100, 1000, 12345, 16000, 20000, 32039)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(artifact_path, csv_path):
    with zipfile.ZipFile(artifact_path) as outer:
        source = outer.read('ESM_IT-2012-0008_NVL_MP_ACC_original.zip')
    if sha(source) != SOURCE_ZIP_SHA:
        raise ValueError('SOURCE_ZIP_SHA_MISMATCH')
    traces = {}
    with zipfile.ZipFile(io.BytesIO(source)) as inner:
        for name in inner.namelist():
            lines = inner.read(name).decode('utf-8').splitlines()
            header = {}
            start = None
            for i, line in enumerate(lines[:70]):
                if ':' not in line:
                    start = i
                    break
                key, val = line.split(':', 1)
                header[key.strip()] = val.strip()
            if start != 63 or header.get('EVENT_ID') != 'IT-2012-0008' or header.get('STATION_CODE') != 'NVL':
                raise ValueError('EVENT_STATION_OR_HEADER')
            if header.get('UNITS') != 'cm/s^2' or float(header['SAMPLING_INTERVAL_S']) != 0.005:
                raise ValueError('UNITS_OR_GRID')
            stream = header['STREAM']
            values = [float(token) * 0.01 for line in lines[start:] for token in line.split()]
            numeric_sha = sha(('\n'.join(lines[start:]) + '\n').encode())
            if stream not in EXPECTED or numeric_sha != EXPECTED[stream] or len(values) != 32040:
                raise ValueError('STREAM_SHA_OR_COUNT')
            traces[stream] = values
    if set(traces) != set(EXPECTED):
        raise ValueError('THREE_COMPONENTS_REQUIRED')
    raw = pathlib.Path(csv_path).read_bytes()
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
    if len(rows) != 32040:
        raise ValueError('CSV_ROWS')
    for index in SAMPLE_INDEX:
        row = rows[index]
        if not math.isclose(float(row['time_s']), index * 0.005, rel_tol=0, abs_tol=1e-10):
            raise ValueError('CSV_TIME_GRID')
        for stream in EXPECTED:
            if not math.isclose(float(row[stream + '_acc_m_s2']), traces[stream][index], rel_tol=2e-11, abs_tol=1e-12):
                raise ValueError('CSV_SOURCE_SAMPLE_MISMATCH')
    if any(not math.isfinite(float(value)) for row in rows for value in row.values()):
        raise ValueError('CSV_NONFINITE')
    return {'status': 'REAL_SOURCE_SI_EXPORT_ORACLE_PASS_NOT_DESIGN_PASS',
            'source_zip_sha256': sha(source), 'csv_sha256': sha(raw),
            'csv_bytes': len(raw), 'rows': len(rows),
            'sample_indices': list(SAMPLE_INDEX), 'independent_component_sample_checks': len(SAMPLE_INDEX) * 3,
            'source_numeric_sha256_by_stream': EXPECTED,
            'PGA_m_s2': {key: max(map(abs, values)) for key, values in traces.items()},
            'S08_PASS': False, 'Abaqus_E_WE_RUN': 0}


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: oracle.py ACTIONS_ARTIFACT.zip OUTPUT.csv')
    print(json.dumps(check(sys.argv[1], sys.argv[2]), sort_keys=True, indent=2))
