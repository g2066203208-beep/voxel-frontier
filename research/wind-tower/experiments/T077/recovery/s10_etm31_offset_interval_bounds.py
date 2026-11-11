#!/usr/bin/env python3
"""Rigorous count intervals for additive stress-offset screening (not material fatigue)."""
import argparse
import csv
import hashlib
import math
from collections import Counter
from pathlib import Path

SOURCE_SHA256 = '36c0a8a97db36885159fff79cc61daced9c939ab688f98ce1c6b860a89ac91d3'
CASES = ('U09p343881_ETM_S06', 'U11p4_ETM_S04',
         'U19p202140_ETM_S04', 'U19p202140_ETM_S06')

def bounds(peaks, q, delta):
    """Guaranteed count interval if each true peak differs by at most delta MPa."""
    if not peaks or not all(math.isfinite(x) for x in peaks):
        raise ValueError('nonfinite/empty peaks')
    if not math.isfinite(q) or not math.isfinite(delta) or delta < 0:
        raise ValueError('invalid q/delta')
    return (sum(x > q + delta for x in peaks),
            sum(x > q - delta for x in peaks))

def read_source(path):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('source SHA256 mismatch')
    with Path(path).open(newline='', encoding='utf-8-sig') as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != 124 or set(r['case'] for r in rows) != set(CASES):
        raise ValueError('expected four ETM cases and 124 rows')
    keys = [(r['case'], r['segment']) for r in rows]
    if len(set(keys)) != 124 or Counter(r['case'] for r in rows) != Counter({c:31 for c in CASES}):
        raise ValueError('duplicate/missing case-segment')
    peaks = [float(r['max_sigma_tension_MPa']) for r in rows]
    if not all(math.isfinite(x) for x in peaks):
        raise ValueError('nonfinite peak')
    return peaks

def self_test():
    assert bounds([19.9, 20.0, 20.1], 20.0, 0) == (1, 1)
    assert bounds([19.9, 20.0, 20.1], 20.0, .1) == (0, 2)
    for bad in (-1, float('nan'), float('inf')):
        try: bounds([1], 0, bad)
        except ValueError: pass
        else: raise AssertionError('invalid delta accepted')
    for bad in ([], [float('nan')]):
        try: bounds(bad, 0, .1)
        except ValueError: pass
        else: raise AssertionError('invalid peaks accepted')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('source', nargs='?')
    ap.add_argument('--self-test', action='store_true')
    a = ap.parse_args()
    self_test()
    if a.self_test and not a.source:
        print('SELF_TEST_PASS')
    elif a.source:
        peaks = read_source(a.source)
        print('q_MPa,delta_assumed_MPa,guaranteed_min,possible_max')
        for q in (20.0, 22.5, 25.0):
            for delta in (0.0, .1, .5, 1.0):
                lo, hi = bounds(peaks, q, delta)
                print(f'{q:g},{delta:g},{lo},{hi}')
    else:
        ap.error('source or --self-test required')
