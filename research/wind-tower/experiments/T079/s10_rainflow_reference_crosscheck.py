#!/usr/bin/env python3
"""Independent S10 rainflow cycle and diagnostic Miner crosscheck.

Compares the existing local stress rainflow implementation against the
separately distributed MIT-licensed 'rainflow' 3.2.0 package by
Piotr Janiszewski (https://github.com/iamlikeme/rainflow).
This is algorithm verification with synthetic input, NOT tower stress or
material-fatigue verification; no ASTM normative conformance is claimed.

The GitHub Actions job installs the pinned 3.2.0 PyPI wheel with its SHA256.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s10_local_material_fatigue_gate import rainflow as project_rainflow
from s10_local_material_fatigue_gate import cycles_to_failure

LIBRARY = 'rainflow'
VERSION = '3.2.0'
WHEEL_SHA256 = 'cb6c254aa1a16a9e658ff3f39c6e5a77650d6c4e8304146169b36516d1f01660'


def independent_cycles(values):
    import rainflow as reference
    if getattr(reference, '__version__', None) != VERSION:
        raise ValueError('REFERENCE_VERSION_MISMATCH')
    # Zero-range cycles are uninformative for fatigue and intentionally
    # excluded from both algorithms.
    return [(float(r), float(m), float(c))
            for r, m, c, _start, _end in reference.extract_cycles(values)
            if r > 0]


def normalized(cycles):
    """Multiset of (range, mean, half/full weight), independent of cycle order."""
    return Counter((round(r, 9), round(m, 9), c) for r, m, c in cycles)


def cases():
    yield 'constant', [0.0] * 20
    yield 'single_excursion', [0, 10, 0]
    yield 'closed_cycles', [0, 10, 0, 10, 0]
    yield 'nested', [0, 10, 5, 8, 0]
    yield 'end_half_cycle', [0, 6, -2, 9]
    yield 'plateaus', [0, 0, 5, 5, 3, 3, -2, -2, 0, 0]
    yield 'equal_amplitude', [0, 10, 0, -10, 0, 10, 0]
    rng = random.Random(20261102)
    for i in range(40):
        n = 8 + i * 4
        yield 'integer_random_%02d' % i, [rng.choice([-16, -10, -4, 0, 0, 3, 7, 14]) for _ in range(n)]
    for i in range(10):
        n = 50 + 7*i
        yield 'multitone_%02d' % i, [
            7*math.sin(2*math.pi*j/(11+i)) +
            2*math.sin(2*math.pi*j/(3+i/10)) +
            0.1*j/n for j in range(n)]


def run():
    import rainflow as reference
    if getattr(reference, '__version__', None) != VERSION:
        raise ValueError('REFERENCE_VERSION_MISMATCH')
    curve = [(1e-12, 1e12), (100, 1e3)]  # SYNTHETIC ONLY; span tiny multitone reversals
    details = []
    for name, series in cases():
        actual = project_rainflow(series)
        expected = independent_cycles(series)
        if normalized(actual) != normalized(expected):
            raise AssertionError('RANGE_MEAN_COUNT_MISMATCH: ' + name +
                                 ' actual=' + str(normalized(actual)) +
                                 ' reference=' + str(normalized(expected)))
        n_a = sum(c for _, _, c in actual)
        n_b = sum(c for _, _, c in expected)
        if not math.isclose(n_a, n_b, rel_tol=0, abs_tol=1e-12):
            raise AssertionError('CYCLE_COUNT_MISMATCH: '+name)
        d_a = sum(c/cycles_to_failure(r, curve) for r, _, c in actual)
        d_b = sum(c/cycles_to_failure(r, curve) for r, _, c in expected)
        if not math.isclose(d_a, d_b, rel_tol=1e-12, abs_tol=1e-18):
            raise AssertionError('SYNTHETIC_DAMAGE_MISMATCH: '+name)
        details.append((name, len(series), len(actual), n_a, d_a))
    # Fail closed if a future edit weakens this into a trivial smoke test.
    if len(details) != 57 or sum(n for _, n, _, _, _ in details) < 4000:
        raise AssertionError('REFERENCE_COVERAGE_REGRESSION')
    p = Path(__file__).resolve().parent / 's10_local_material_fatigue_gate.py'
    return {
        'status': 'INDEPENDENT_ALGORITHM_QC_PASS_NOT_MATERIAL_FATIGUE',
        'reference': 'iamlikeme/rainflow',
        'reference_version': VERSION,
        'reference_wheel_sha256': WHEEL_SHA256,
        'project_algorithm_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
        'case_count': len(details),
        'total_input_points': sum(n for _, n, _, _, _ in details),
        'total_weighted_cycles': sum(n for _, _, _, n, _ in details),
        'range_mean_count_multisets_equal': True,
        'synthetic_damage_equal': True,
        'scope': 'SYNTHETIC_ONLY_NO_ODB_NO_SN_STANDARD_NO_PHYSICAL_PASS'
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true', required=True)
    parser.parse_args()
    print(json.dumps(run(), ensure_ascii=False, sort_keys=True, indent=2))
