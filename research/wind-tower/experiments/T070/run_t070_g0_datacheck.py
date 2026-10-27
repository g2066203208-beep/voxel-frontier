#!/usr/bin/env python3
"""S02: run frozen T070 native Abaqus Data Check and preserve its evidence.

Never edits T057/T070, never performs a production solve. Native G0 success
does NOT imply equilibrium, model V&V, or standards acceptance.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXPECTED_SHA256 = '9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9'
EXPECTED_NAME = 'BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp'
JOB = 'T070_G0_DATACHECK'
ERROR = re.compile(r'^\s*\*{3}\s*ERROR\b', re.I | re.M)
WARNING = re.compile(r'^\s*\*{3}\s*WARNING\b', re.I | re.M)
COMPLETED = re.compile(r'\bAbaqus\s+JOB\b[^\r\n]*\bCOMPLETED\b', re.I)


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def scan_log(text):
    return {
        'error_count': len(ERROR.findall(text)),
        'warning_count': len(WARNING.findall(text)),
        'error_lines': [x.strip()[:400] for x in text.splitlines() if ERROR.match(x)][:200],
        'warning_lines': [x.strip()[:400] for x in text.splitlines() if WARNING.match(x)][:200],
    }


def self_test():
    assert scan_log('***ERROR: one\n***WARNING: two\n *** WARNING: three')['warning_count'] == 2
    assert scan_log('***ERROR: one')['error_count'] == 1
    assert scan_log('***WARNING: one')['error_count'] == 0
    assert COMPLETED.search('Abaqus JOB T070_G0_DATACHECK COMPLETED')
    assert not COMPLETED.search('Abaqus JOB T070_G0_DATACHECK TERMINATED')
    print('PASS: log classifier self-test (not native Abaqus)')


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inp', type=Path, help='Original T070 G0/G1 observability INP')
    ap.add_argument('--out', type=Path, help='New, separate evidence directory; must not exist')
    ap.add_argument('--abaqus', default='abaqus', help='Native Abaqus launcher executable')
    ap.add_argument('--self-test', action='store_true', help='Test only log classification')
    ap.add_argument('--preflight-only', action='store_true', help='Validate input/launcher, do not execute')
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.inp is None or args.out is None:
        ap.error('--inp and --out are required unless --self-test')
    inp = args.inp.resolve(strict=True)
    out = args.out.resolve()
    if inp.name != EXPECTED_NAME:
        raise SystemExit(f'REFUSE: wrong input filename: {inp.name}')
    actual_sha = sha256(inp)
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(f'REFUSE: T070 input SHA mismatch: {actual_sha}')
    if out.exists():
        raise SystemExit(f'REFUSE: evidence directory already exists: {out}')
    if out == inp.parent or inp.parent in out.parents:
        raise SystemExit('REFUSE: evidence directory may not be inside input file path')
    executable = shutil.which(args.abaqus)
    out.mkdir(parents=True, exist_ok=False)
    manifest = {
        'stage': 'S02', 'input_role': 'R335 prototype-reconstruction diagnostic, NOT final code design',
        'source_input': str(inp), 'source_sha256': actual_sha,
        'parent_T057_sha256_from_register': 'c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db',
        'created_utc': utc_now(), 'native_executable': executable,
        'mode': 'Abaqus Data Check ONLY, no production RUN',
        'status': 'NOT_STARTED', 'warning_disposition': 'HUMAN_REVIEW_REQUIRED',
        'source_level': 'T070 frozen INP bytes SHA verified',
        'standard_level': 'No standard clause acceptance from this job',
        'official_level': 'Native solver only if Abaqus executable and job logs confirm',
        'run_level': 'No native run yet', 'fig': [], 'tab': [],
        'assumptions': ['T070 differs from T057 only in observability (historical source claim, not re-proved here)'],
        'error_budget': 'Data Check is syntax/consistency screening, not physics error budget',
        'hold': 'S01 design/PT identity and S03 physical equilibrium remain unverified',
    }
    result_code = 3
    if not executable:
        manifest['status'] = 'BLOCKED_NO_NATIVE_ABAQUS_EXECUTABLE'
        manifest['run_level'] = 'No native run; Abaqus executable not found'
    elif args.preflight_only:
        manifest['status'] = 'PREFLIGHT_ONLY_NOT_NATIVE_RUN'
        manifest['run_level'] = 'Native executable located, not invoked'
        result_code = 0
    else:
        command = [executable, f'job={JOB}', f'input={inp}', 'datacheck', 'cpus=1', 'interactive']
        manifest['command_argv'] = command
        manifest['start_utc'] = utc_now()
        with (out / 'launcher.stdout.log').open('w', encoding='utf-8') as stdout:
            with (out / 'launcher.stderr.log').open('w', encoding='utf-8') as stderr:
                try:
                    completed = subprocess.run(command, cwd=out, stdout=stdout, stderr=stderr, check=False)
                    manifest['process_returncode'] = completed.returncode
                except OSError as exc:
                    manifest['process_launch_error'] = str(exc)
                    manifest['process_returncode'] = -1
        manifest['end_utc'] = utc_now()
        extensions = ['.dat', '.msg', '.sta', '.log']
        logs = [out / (JOB + suffix) for suffix in extensions]
        logs += [out / 'launcher.stdout.log', out / 'launcher.stderr.log']
        found = [p for p in logs if p.is_file()]
        manifest['logs'] = {p.name: {'sha256': sha256(p), 'bytes': p.stat().st_size} for p in found}
        manifest['missing_required_logs'] = [p.name for p in logs[:4] if not p.is_file()]
        contents = {p.name: p.read_text(encoding='utf-8', errors='replace') for p in found}
        joined = '\n'.join(contents.values())
        manifest['diagnostics'] = scan_log(joined)
        manifest['native_completed_marker'] = bool(COMPLETED.search(joined))
        if manifest['process_returncode'] != 0 or manifest['diagnostics']['error_count']:
            manifest['status'] = 'NATIVE_DATACHECK_FAILED'
            result_code = 4
        elif manifest['missing_required_logs'] or not manifest['native_completed_marker']:
            manifest['status'] = 'NATIVE_DATACHECK_INCOMPLETE_EVIDENCE_HOLD'
            result_code = 5
        else:
            manifest['status'] = 'NATIVE_DATACHECK_COMPLETED_MANUAL_WARNING_REVIEW_REQUIRED'
            result_code = 0
        manifest['run_level'] = 'Native Data Check invoked; see logs; NOT equilibrium/physics PASS'
    (out / 'S02_G0_EVIDENCE_MANIFEST.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    print(json.dumps({'status': manifest['status'], 'manifest': str(out / 'S02_G0_EVIDENCE_MANIFEST.json')}, ensure_ascii=False))
    return result_code


if __name__ == '__main__':
    sys.exit(main())
