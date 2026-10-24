#!/usr/bin/env python3
"""Read-only T077 31-segment full-history provenance preflight.

Requires original gzipped CSV files; does not run Abaqus or compute capacity.
A passing result establishes only source-grid consistency, not physical validity.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import sys

FIELDS = ('Fx_kN','Fy_kN','Fz_kN','Mx_kNm','My_kNm','Mz_kNm')
KEYS = ('case','segment','time_s')


def audit(root: Path, meta: Path) -> dict:
    expected = set(json.loads(meta.read_text(encoding='utf-8'))['load_cases'])
    files = sorted(root.glob('**/*31seg.csv.gz'))
    report = {'status': 'HOLD', 'files': [], 'expected_cases': sorted(expected),
              'cases_found': [], 'segment_counts': {}, 'issues': [],
              'identical_duplicate_rows': 0, 'conflicting_duplicate_rows': 0,
              'unique_rows': 0, 'scope': 'SOURCE-GRID ONLY / NOT CAE OR CODE ACCEPTANCE'}
    if not files:
        report['issues'].append('MISSING-SOURCE: no *31seg.csv.gz under ' + str(root))
        return report
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE states (case_id TEXT, segment TEXT, time REAL, payload TEXT, PRIMARY KEY(case_id,segment,time))')
    required = set(KEYS + FIELDS)
    for path in files:
        sha = hashlib.sha256()
        with path.open('rb') as fh:
            for chunk in iter(lambda: fh.read(1024*1024), b''):
                sha.update(chunk)
        info = {'path': str(path), 'sha256': sha.hexdigest(), 'rows_read': 0}
        report['files'].append(info)
        try:
            with gzip.open(path, 'rt', encoding='utf-8-sig', newline='') as fh:
                reader = csv.DictReader(fh)
                header = reader.fieldnames or []
                # DictReader silently overwrites duplicate column names with the
                # last occurrence; reject ambiguous six-component provenance.
                if len(header) != len(set(header)):
                    report['issues'].append('DUPLICATE-HEADER: ' + str(path))
                    continue
                if not required.issubset(header):
                    report['issues'].append('BAD-COLUMNS: ' + str(path))
                    continue
                for line_no, row in enumerate(reader, 2):
                    info['rows_read'] += 1
                    # DictReader silently stores surplus CSV cells under None.
                    # Reject both surplus and missing cells before parsing six forces.
                    if None in row or any(value is None for value in row.values()):
                        if len(report['issues']) < 40:
                            report['issues'].append(f'BAD-ROW-WIDTH: {path}:{line_no}')
                        continue
                    try:
                        seg = row['segment']; case = row['case']; t = float(row['time_s'])
                        values = [float(row[c]) for c in FIELDS]
                        if not (math.isfinite(t) and all(map(math.isfinite, values))):
                            raise ValueError('nonfinite')
                        if not (seg.startswith('CSEG_') and seg[5:].isdigit() and 1 <= int(seg[5:]) <= 31):
                            raise ValueError('segment out of 01..31')
                        payload = ','.join(format(v, '.17g') for v in values)
                        try:
                            db.execute('INSERT INTO states VALUES (?,?,?,?)', (case, seg, t, payload))
                        except sqlite3.IntegrityError:
                            old = db.execute('SELECT payload FROM states WHERE case_id=? AND segment=? AND time=?',
                                             (case, seg, t)).fetchone()[0]
                            if old == payload:
                                report['identical_duplicate_rows'] += 1
                            else:
                                report['conflicting_duplicate_rows'] += 1
                                if len(report['issues']) < 40:
                                    report['issues'].append(f'CONFLICTING-DUPLICATE: {case}/{seg}/{t:.17g} in {path}:{line_no}')
                    except (ValueError, TypeError, KeyError) as exc:
                        if len(report['issues']) < 40:
                            report['issues'].append(f'INVALID-ROW: {path}:{line_no}: {exc}')
        except (OSError, EOFError, UnicodeError, csv.Error) as exc:
            report['issues'].append(f'CORRUPT-SOURCE: {path}: {exc}')
    db.commit()
    found = {r[0] for r in db.execute('SELECT DISTINCT case_id FROM states')}
    report['cases_found'] = sorted(found)
    for missing in sorted(expected - found):
        report['issues'].append('MISSING-CASE: ' + missing)
    for extra in sorted(found - expected):
        report['issues'].append('UNREGISTERED-CASE: ' + extra)
    for case in sorted(expected):
        groups = list(db.execute('SELECT segment, COUNT(*) FROM states WHERE case_id=? GROUP BY segment ORDER BY segment', (case,)))
        report['segment_counts'][case] = {seg: count for seg, count in groups}
        missing_segs = [f'CSEG_{i:02d}' for i in range(1,32) if f'CSEG_{i:02d}' not in report['segment_counts'][case]]
        if missing_segs:
            report['issues'].append('MISSING-SEGMENTS: ' + case + ': ' + ','.join(missing_segs))
        if len(groups) == 31:
            # Every segment must carry exactly the same time grid for synchronized N/M/V/T.
            signatures = {}
            for seg, _ in groups:
                h = hashlib.sha256()
                for (t,) in db.execute('SELECT time FROM states WHERE case_id=? AND segment=? ORDER BY time', (case,seg)):
                    h.update((format(t,'.17g')+'\n').encode())
                signatures[seg] = h.hexdigest()
            if len(set(signatures.values())) != 1:
                report['issues'].append('TIME-GRID-MISMATCH: ' + case)
            if min(count for _,count in groups) < 2:
                report['issues'].append('INSUFFICIENT-TIME-SAMPLES: ' + case)
    report['unique_rows'] = db.execute('SELECT COUNT(*) FROM states').fetchone()[0]
    if report['identical_duplicate_rows']:
        report['issues'].append('DUPLICATE-KEYS-PRESENT: identical duplicates require explicit provenance decision')
    if report['conflicting_duplicate_rows']:
        report['issues'].append('CONFLICTING-KEYS-PRESENT: T077 keep=first would silently discard conflicting values')
    report['status'] = 'PASS-SOURCE-GRID-ONLY' if not report['issues'] else 'HOLD'
    db.close()
    return report


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--meta', type=Path, required=True)
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    report = audit(a.root, a.meta)
    result = json.dumps(report, ensure_ascii=False, indent=2)
    if a.out:
        a.out.write_text(result+'\n', encoding='utf-8')
    print(result)
    return 0 if report['status'].startswith('PASS') else 2


if __name__ == '__main__':
    sys.exit(main())
