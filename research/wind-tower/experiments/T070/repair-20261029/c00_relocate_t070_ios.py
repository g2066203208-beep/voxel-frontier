#!/usr/bin/env python3
"""C00: move three T070 integrated-output-section definitions inside Assembly.

A deterministic text-only repair of the single Abaqus 2025 G0 error.
NO physical changes; NOT an Abaqus syntax check or native Data Check.
"""
from __future__ import annotations
import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path

PARENT_SHA256 = '9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9'
PARENT_NAME = 'BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp'
CHILD_NAME = 'BASE001_T070_G0_IOS_ASSEMBLY_CHILD.inp'
IOS = (
    '*Integrated Output Section, name=IOS_T070_C31_TOP, surface=CSEG_31-1.SURF_TOP, ref node=62\n'
    '*Integrated Output Section, name=IOS_T070_S01_BOTTOM, surface=SSEG_01-1.SURF_BOTTOM, ref node=62\n'
    '*Integrated Output Section, name=IOS_T070_TOWER_BASE, surface=CSEG_01-1.SURF_BOTTOM\n'
)
COMMENT = '** T070 G1 integrated output sections — diagnostic only, no added constraint\n'
BEFORE = ('*End Assembly\n**\n' + COMMENT + IOS + '**\n** T057 HORIZONTAL JOINTS').encode('utf-8')
AFTER = ('**\n' + COMMENT + IOS + '*End Assembly\n**\n** T057 HORIZONTAL JOINTS').encode('utf-8')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relocate(parent: bytes, *, require_sha: bool = True) -> tuple[bytes, dict]:
    if require_sha and sha(parent) != PARENT_SHA256:
        raise ValueError('PARENT_SHA256_MISMATCH')
    if parent.count(BEFORE) != 1:
        raise ValueError('EXPECTED_EXACT_POST_ASSEMBLY_IOS_BLOCK_ONCE')
    if parent.count(b'*End Assembly\n') != 1:
        raise ValueError('ASSEMBLY_END_NOT_UNIQUE')
    for line in IOS.encode('utf-8').splitlines(keepends=True):
        if parent.count(line) != 1:
            raise ValueError('IOS_DEFINITION_MISSING_OR_DUPLICATED')
    child = parent.replace(BEFORE, AFTER, 1)
    if child == parent or child.count(AFTER) != 1 or child.count(BEFORE):
        raise AssertionError('NO_EFFECT_OR_DUPLICATE_REPAIR')
    if child.replace(AFTER, BEFORE, 1) != parent:
        raise AssertionError('EXACT_INVERSE_FAILED')
    if len(child) != len(parent):
        raise AssertionError('UNEXPECTED_BYTE_CHANGE')
    a = child.find(b'*End Assembly\n')
    section = child.find(IOS.encode('utf-8'))
    if section < 0 or section >= a:
        raise AssertionError('IOS_NOT_INSIDE_ASSEMBLY')
    if b'*End Assembly\n' in child[:section]:
        raise AssertionError('ASSEMBLY_CLOSED_BEFORE_IOS')
    # Only the 3 intended keywords may move; all three are still unique.
    for line in IOS.encode('utf-8').splitlines(keepends=True):
        if child.count(line) != 1:
            raise AssertionError('IOS_IDENTITY_CHANGED')
    for name in (b'IOS_T070_C31_TOP', b'IOS_T070_S01_BOTTOM', b'IOS_T070_TOWER_BASE'):
        if parent.count(name) != child.count(name):
            raise AssertionError('OUTPUT_SECTION_REFERENCE_CHANGED')
    before_lines = parent.decode('utf-8').splitlines(keepends=True)
    after_lines = child.decode('utf-8').splitlines(keepends=True)
    diff = ''.join(difflib.unified_diff(before_lines, after_lines, fromfile=PARENT_NAME,
                                        tofile=CHILD_NAME, n=4))
    if not diff or diff.count('@@ ') != 1:
        raise AssertionError('UNEXPECTED_DIFF_HUNKS')
    return child, {
        'schema': 1,
        'status': 'CHILD_GENERATED_STATIC_CHECKED_NATIVE_RECHECK_PENDING',
        'source': 'T070 frozen input; 2026-10-29 native G0 .dat line 482557',
        'parent_name': PARENT_NAME, 'parent_sha256': sha(parent),
        'parent_bytes': len(parent), 'child_name': CHILD_NAME,
        'child_sha256': sha(child), 'child_bytes': len(child),
        'inverse_recovers_parent_sha256': sha(child.replace(AFTER, BEFORE, 1)),
        'exact_inverse_pass': child.replace(AFTER, BEFORE, 1) == parent,
        'moved_sections': ['IOS_T070_C31_TOP', 'IOS_T070_S01_BOTTOM', 'IOS_T070_TOWER_BASE'],
        'original_failing_line': 482557,
        'assembly_level_static_check': True,
        'physical_parameters_modified': False,
        'original_failure': 'Abaqus 2025: INTEGRATEDOUTPUTSECTION after End Assembly; 1 FATAL',
        'native_datacheck': 'NOT_RUN_ON_CHILD',
        'standard_clause_validation': 'NOT_PERFORMED',
        'uncertainty': 'static byte/inverse exact; native parser/solver errors and physical errors unbounded',
        'source_read_level': 'full INP bytes via GitHub Actions checkout; official keyword level web; native .dat exact error',
        'output_contract': 'child .inp + manifest JSON + unified diff; original input never edited',
        'diff_sha256': sha(diff.encode('utf-8')),
        'diff': diff,
    }


def self_test() -> None:
    fake = (b'** test only\n*Assembly, name=Assembly\n'
            + BEFORE + b'\n*Step\n*End Step\n')
    child, m = relocate(fake, require_sha=False)
    assert m['exact_inverse_pass'] and m['parent_bytes'] == m['child_bytes']
    assert child.index(b'*Integrated Output Section') < child.index(b'*End Assembly')
    assert len(m['diff'].splitlines()) > 4
    bad = [
        (fake.replace(b'*End Assembly\n', b'*End Assembly\r\n'), 'EXPECTED_EXACT_POST_ASSEMBLY_IOS_BLOCK_ONCE'),
        (fake.replace(b'IOS_T070_C31_TOP', b'IOS_WRONG'), 'EXPECTED_EXACT_POST_ASSEMBLY_IOS_BLOCK_ONCE'),
        (fake + BEFORE, 'EXPECTED_EXACT_POST_ASSEMBLY_IOS_BLOCK_ONCE'),
        (fake.replace(b'*End Assembly\n', b'*End Assembly\n*End Assembly\n', 1), 'ASSEMBLY_END_NOT_UNIQUE'),
        (fake, 'PARENT_SHA256_MISMATCH'),
    ]
    for n, (input_bytes, expected) in enumerate(bad):
        try:
            relocate(input_bytes, require_sha=(n == 4))
        except ValueError as exc:
            if str(exc) != expected:
                raise AssertionError((n, expected, str(exc))) from exc
        else:
            raise AssertionError('accepted invalid input ' + str(n))
    # Tamper with an unrelated physics line while keeping IOS syntax: hash must fail.
    try:
        relocate(fake + b'** tampered physics\n')
    except ValueError as exc:
        assert str(exc) == 'PARENT_SHA256_MISMATCH'
    else:
        raise AssertionError('parent SHA not enforced')
    print('C00_SYNTHETIC_PASS 4 positive assertions + 6 negative refusals; NOT NATIVE')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('--parent', type=Path)
    ap.add_argument('--outdir', type=Path)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.parent or not args.outdir:
        ap.error('require --parent and --outdir')
    parent = args.parent.read_bytes()
    child, receipt = relocate(parent)
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / CHILD_NAME).write_bytes(child)
    (args.outdir / 'C00_IOS_REPAIR_MANIFEST.json').write_text(
        json.dumps({k:v for k,v in receipt.items() if k != 'diff'}, indent=2) + '\n',
        encoding='utf-8')
    (args.outdir / 'C00_IOS_REPAIR.patch').write_text(receipt['diff'], encoding='utf-8')
    print('C00_CHILD_GENERATED_STATIC_CHECKED_NATIVE_RECHECK_PENDING')
    print(json.dumps({k: receipt[k] for k in ('parent_sha256', 'child_sha256',
          'parent_bytes', 'child_bytes', 'diff_sha256', 'exact_inverse_pass')}, indent=2))


if __name__ == '__main__':
    main()
