#!/usr/bin/env python3
"""T080.36: fail-closed time-window gate for T077 gzipped 31-segment histories.

Supplement to T080.34 source-grid gate. This is a data-identity test, NOT
Abaqus verification, design-code acceptance, or a physical response result.
A manifest must be backed by independently verified exporter/OpenFAST metadata.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

FIELDS = ('case', 'segment', 'time_s')
SHA = set('0123456789abcdef')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def valid_sha(s) -> bool:
    return isinstance(s, str) and len(s) == 64 and set(s.lower()) <= SHA


def check(root: Path, meta: Path, manifest: Path | None) -> dict:
    out = {'status': 'HOLD', 'scope': 'H-TIME SOURCE WINDOW ONLY; NOT CAE/CODE PASS',
           'issues': [], 'case_results': {}, 'files': []}
    try:
        cases = json.loads(meta.read_text(encoding='utf-8'))['load_cases']
        if not isinstance(cases, list) or not cases or len(set(cases)) != len(cases):
            raise ValueError('invalid load_cases')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        out['issues'].append(f'BAD-META: {exc}')
        return out
    if manifest is None or not manifest.is_file():
        out['issues'].append('MISSING-H-TIME-MANIFEST: no independently sourced window definition')
        return out
    try:
        data = json.loads(manifest.read_text(encoding='utf-8'))
        specs = data['cases']
        if set(specs) != set(cases):
            raise ValueError('manifest cases differ from T077 load_cases')
        for case in cases:
            s = specs[case]
            for field in ('first_time_s','last_time_s','step_s','samples_per_segment','tolerance_s',
                          'openfast_input_sha256','exporter_sha256','source_note'):
                if field not in s:
                    raise ValueError(f'{case}: missing {field}')
            if not (valid_sha(s['openfast_input_sha256']) and valid_sha(s['exporter_sha256'])
                    and isinstance(s['source_note'], str) and s['source_note'].strip()):
                raise ValueError(f'{case}: missing valid source identity')
            t0, t1, dt, tol = (float(s[k]) for k in ('first_time_s','last_time_s','step_s','tolerance_s'))
            n = s['samples_per_segment']
            if (not all(math.isfinite(v) for v in (t0,t1,dt,tol)) or dt <= 0 or tol < 0
                    or tol >= dt/4 or not isinstance(n,int) or isinstance(n,bool) or n < 2):
                raise ValueError(f'{case}: invalid window/step/count/tolerance')
            if abs(t1 - (t0+(n-1)*dt)) > tol:
                raise ValueError(f'{case}: manifest endpoints inconsistent with sample count')
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        out['issues'].append(f'INVALID-H-TIME-MANIFEST: {exc}')
        return out
    files = sorted(root.glob('**/*31seg.csv.gz'))
    if not files:
        out['issues'].append('MISSING-SOURCE: no *31seg.csv.gz')
        return out
    # One expected index for every (case,segment,sample); memory grows with samples.
    # Using integer grid indices also detects missing or repeated samples in any order.
    seen = {case: {f'CSEG_{i:02d}': set() for i in range(1,32)} for case in cases}
    for path in files:
        try:
            digest = sha256(path)
        except OSError as exc:
            out['issues'].append(f'UNREADABLE-SOURCE: {path}: {exc}')
            continue
        out['files'].append({'path': str(path), 'sha256': digest})
        try:
            with gzip.open(path, 'rt', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                header = reader.fieldnames or []
                if len(header) != len(set(header)) or not set(FIELDS).issubset(header):
                    out['issues'].append(f'BAD-HEADER: {path}')
                    continue
                for lineno, row in enumerate(reader,2):
                    case, seg = row.get('case'), row.get('segment')
                    if case not in seen or seg not in seen[case]:
                        out['issues'].append(f'BAD-IDENTITY: {path}:{lineno}')
                        continue
                    try:
                        t = float(row['time_s'])
                        if not math.isfinite(t):
                            raise ValueError('nonfinite time')
                        s = specs[case]
                        t0, dt, tol = (float(s[k]) for k in ('first_time_s','step_s','tolerance_s'))
                        idx = round((t-t0)/dt)
                        if not (0 <= idx < s['samples_per_segment'] and
                                abs(t-(t0+idx*dt)) <= tol):
                            raise ValueError('outside declared sample grid')
                        if idx in seen[case][seg]:
                            raise ValueError('duplicate time index')
                        seen[case][seg].add(idx)
                    except (ValueError, TypeError, KeyError) as exc:
                        if len(out['issues']) < 50:
                            out['issues'].append(f'BAD-TIME: {path}:{lineno}: {exc}')
        except (OSError, EOFError, UnicodeError, csv.Error) as exc:
            out['issues'].append(f'CORRUPT-SOURCE: {path}: {exc}')
    for case in cases:
        n = specs[case]['samples_per_segment']
        counts = {seg:len(indices) for seg,indices in seen[case].items()}
        out['case_results'][case] = {'expected_samples_per_segment': n,
                                      'observed_min': min(counts.values()),
                                      'observed_max': max(counts.values()),
                                      'segments_complete': sum(v == n for v in counts.values())}
        if any(v != n for v in counts.values()):
            out['issues'].append(f'INCOMPLETE-WINDOW: {case}: {out["case_results"][case]}')
    out['status'] = 'PASS-H-TIME-SOURCE-ONLY' if not out['issues'] else 'HOLD'
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--meta', type=Path, required=True)
    p.add_argument('--manifest', type=Path)
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    result = check(a.root, a.meta, a.manifest)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if a.out:
        a.out.write_text(encoded, encoding='utf-8')
    print(encoded, end='')
    return 0 if result['status'].startswith('PASS') else 2

if __name__ == '__main__':
    raise SystemExit(main())
