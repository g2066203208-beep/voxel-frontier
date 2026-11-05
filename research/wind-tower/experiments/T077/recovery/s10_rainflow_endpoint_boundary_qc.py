#!/usr/bin/env python3
"""S10: real 12001-sample gross-stress open vs assumed periodic rainflow.
This is a boundary-convention sensitivity, NOT local material fatigue or a physical PASS.
Reuses s10_control_cycle_export_compact.py's SHA-locked source and ASTM-style stack.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import s10_control_cycle_export_compact as prior


def check(ok, name):
    if not ok:
        raise ValueError(name)


def stats(cycles):
    check(all(math.isfinite(r) and math.isfinite(m) and r > 0 and n in (.5, 1.)
              for r, m, n in cycles), 'BAD_CYCLE')
    m4 = math.fsum(n * r ** 4 for r, m, n in cycles)
    h = sum(n == .5 for r, m, n in cycles)
    f = sum(n == 1. for r, m, n in cycles)
    return {'rows': len(cycles), 'half_rows': h, 'full_rows': f,
            'equivalent_cycles': f + h / 2, 'm4_MPa4_cycles': m4,
            'DEL4_MPa': (m4 / 600) ** .25 if m4 else 0.,
            'half_m4_fraction': math.fsum(n * r ** 4 for r, m, n in cycles if n == .5) / m4 if m4 else 0.}


def periodic_assumption(xs):
    """Cyclically rotate at global maximum; append start, pair equal residual halves.
    The wrap-around transition is ASSUMED, not observed; do not call it an ASTM
    uniquely required closure or a physical period of the wind response.
    """
    check(len(xs) >= 3 and all(math.isfinite(x) for x in xs), 'BAD_SERIES')
    check(max(xs) > min(xs), 'CONSTANT_SERIES')
    imax = max(range(len(xs)), key=xs.__getitem__)
    closed = xs[imax:] + xs[:imax] + [xs[imax]]
    raw = prior.rainflow(closed)
    half = [(r, m) for r, m, n in raw if n == .5]
    check(len(half) == 2, 'PERIODIC_RESIDUAL_NOT_TWO_HALVES')
    check(abs(half[0][0] - half[1][0]) < 1e-10 and
          abs(half[0][1] - half[1][1]) < 1e-10, 'PERIODIC_HALVES_NOT_PAIRABLE')
    cycles = [(r, m, n) for r, m, n in raw if n == 1.]
    cycles.append((half[0][0], half[0][1], 1.))
    return cycles, imax


def selftest():
    sample = [0., 4., 1., 3., 0.]
    a = prior.rainflow(sample)
    b, ix = periodic_assumption(sample)
    check(ix == 1 and stats(a)['half_rows'] == 2, 'OPEN_KNOWN')
    check(sorted((r, n) for r, m, n in b) == [(2., 1.), (4., 1.)], 'CLOSED_KNOWN')
    check(abs(stats(a)['m4_MPa4_cycles'] - 272.) < 1e-12, 'M4_KNOWN')
    check(abs(stats(b)['m4_MPa4_cycles'] - 272.) < 1e-12, 'CLOSED_M4_KNOWN')
    check(abs(stats(prior.rainflow(sample[::-1]))['m4_MPa4_cycles'] - 272.) < 1e-12, 'REVERSE_KNOWN')
    for bad in ([1., 1., 1.], [0., float('nan'), 1.], [0., 1.]):
        try:
            periodic_assumption(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('BAD_SERIES_ACCEPTED')
    return {'known_answers': 5, 'negative_rejections': 3}


def compute(root):
    tests = selftest()
    data = {case: prior.source(root, case) for case in prior.SRC}
    results = []
    for case, seg, az, area, I, radius, pe, p0, d4ref, d10ref, nref, href, fref in prior.CTRL:
        rows = data[case][seg]
        check(len(rows) == 12001, 'POINT_COUNT')
        check(all(abs(r[0] - (100 + i * .05)) <= 1e-7 for i, r in enumerate(rows)), 'TIME_GRID')
        theta = math.radians(az)
        xs = [.001 * (r[1] / area + radius / I * (math.sin(theta) * r[2] - math.cos(theta) * r[3]))
              for r in rows]
        opened = prior.rainflow(xs)
        periodic, imax = periodic_assumption(xs)
        open_stats = stats(opened)
        closed_stats = stats(periodic)
        full_only = stats([c for c in opened if c[2] == 1.])
        reversed_stats = stats(prior.rainflow(xs[::-1]))
        check(open_stats['rows'] == href + fref and open_stats['half_rows'] == href and
              open_stats['full_rows'] == fref and open_stats['equivalent_cycles'] == nref,
              'HISTORICAL_RAINFLOW_ORACLE')
        check(abs(open_stats['DEL4_MPa'] - d4ref) < 1e-8, 'HISTORICAL_DEL4_ORACLE')
        check(abs(reversed_stats['m4_MPa4_cycles'] - open_stats['m4_MPa4_cycles']) < 1e-7,
              'TIME_REVERSAL_INVARIANCE')
        check(closed_stats['half_rows'] == 0, 'PERIODIC_HALVES_LEFT')
        results.append({'case': case, 'segment': seg, 'azimuth_deg': az,
                        'samples': len(xs), 'time_start_s': rows[0][0], 'time_end_s': rows[-1][0],
                        'boundary_jump_end_minus_start_MPa': xs[-1] - xs[0],
                        'periodic_rotation_global_max_sample_index': imax,
                        'open': open_stats, 'assumed_periodic': closed_stats,
                        'drop_all_open_half_cycles_counterfactual': full_only,
                        'periodic_vs_open_DEL4_pct': 100 * (closed_stats['DEL4_MPa'] / open_stats['DEL4_MPa'] - 1),
                        'drop_half_vs_open_DEL4_pct': 100 * (full_only['DEL4_MPa'] / open_stats['DEL4_MPa'] - 1),
                        'time_reversed_open_m4_abs_diff': abs(reversed_stats['m4_MPa4_cycles'] - open_stats['m4_MPa4_cycles'])})
    return {'status': 'REAL_ETM_12001_POINT_GROSS_NOMINAL_ENDPOINT_CONVENTION_QC_NOT_MATERIAL_FATIGUE',
            'SOURCE': 'Two original GitHub Actions ZIPs, member GZIPs and CSVs, 3x12001 real points; all 3 SHA levels verified by imported prior.source',
            'READING_LEVEL': 'Full original ZIP/GZIP/CSV source bytes for 2 batches, 108009 rows each; 3 control histories rebuilt',
            'REF': 'Inherited T077 ASTM-style reversal-stack; no new primary literature page read',
            'STANDARD': 'No newly read licensed IEC/GB/NB clauses; no clause acceptance',
            'OFFICIAL': 'Historical GitHub Actions artifact IDs 11465219800 and 11483249910; original OpenFAST OUTB not re-read',
            'RUN': 'Python stdlib native non-production source-level QC; no structural solver',
            'FIG': '0', 'TAB': '3 control point open/assumed-periodic/half-drop comparisons',
            'algorithm': 'ASTM-style open rainflow with residual half counts; assumed periodic closure rotates at global maximum, wraps last-to-first and pairs two equal half cycles into one full; NOT an observed continuation',
            'Nref_cycles': 600, 'm_exponent': 4,
            'source_sha256': {case: {'zip': spec[2], 'gzip': spec[3], 'csv': spec[4]}
                              for case, spec in prior.SRC.items()},
            'prior_source_script_sha256': hashlib.sha256(Path(prior.__file__).read_bytes()).hexdigest(),
            'this_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'software': sys.version.split()[0], 'tests': {**tests, 'real_controls_oracle': 3,
                                                         'real_time_reversal': 3, 'source_sha_levels_per_batch': 3},
            'error_budget': {'DEL4_oracle_abs_MPa': 1e-8, 'time_grid_abs_s': 1e-7,
                             'periodic_pair_abs_MPa': 1e-10,
                             'physical_boundary_convention': 'UNQUANTIFIED: no observed continuation beyond 700s; assumed periodic closure is counterfactual',
                             'local_material_and_wind_bin': 'NOT_ESTIMATED'},
            'FAILURES': 'No local execution failures if all checks complete; original OUTB not re-read',
            'HOLD': 'Open residual convention is not a verified long-duration material stress history; ETM not DLC1.2; no local concrete/rebar/PT/steel stress, annual probabilities or Miner life; 0/12',
            'material_damage': None, 'physical_PASS': False, 'stage_PASS_count': 0,
            'results': results}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--zip-dir', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--self-test', action='store_true')
    args = p.parse_args()
    receipt = compute(args.zip_dir)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'status': receipt['status'], 'tests': receipt['tests'],
                      'results': [{'case': r['case'], 'segment': r['segment'],
                                   'open_DEL4': r['open']['DEL4_MPa'],
                                   'periodic_DEL4': r['assumed_periodic']['DEL4_MPa'],
                                   'periodic_vs_open_pct': r['periodic_vs_open_DEL4_pct'],
                                   'drop_half_vs_open_pct': r['drop_half_vs_open_DEL4_pct']}
                                  for r in receipt['results']]}, ensure_ascii=False))
