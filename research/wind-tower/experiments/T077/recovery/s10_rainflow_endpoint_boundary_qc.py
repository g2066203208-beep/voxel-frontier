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



# Four-ETM 31-section source-only extension.  Existing 3-control mode unchanged.
FULL_MANIFEST_SHA = 'dfc07558eb87002c3f54bb88671644519b77dfc38daf3971026f43686d4c2ed8'
FULL_GEOMETRY_SHA = 'fff6dfcc6bc094353ebee042392033e8df47e7fb792ccc1812c0962c9c43f800'
FULL_BASELINE_SHA = '16c9864ef7a344e5b97338c31ce26de6adb86c0f0f64942ef894fe9983926b2b'
FULL_CASES = ('U09p343881_ETM_S06', 'U11p4_ETM_S04',
              'U19p202140_ETM_S04', 'U19p202140_ETM_S06')
FULL_BATCHES = {'A': range(1, 10), 'B': range(10, 19),
                'C': range(19, 28), 'D': range(28, 32)}


def full_grid_selftest():
    """Independent exact m4 partition and invalid-cycle checks; not physical V&V."""
    a = [0., 4., 1., 3., 0.]
    open_c = prior.rainflow(a)
    left = prior.rainflow(a[:3])
    right = prior.rainflow(a[2:])
    assert abs(stats(open_c)['m4_MPa4_cycles'] - 272.) < 1e-12
    assert abs(stats(left)['m4_MPa4_cycles'] + stats(right)['m4_MPa4_cycles'] - 217.) < 1e-12
    assert abs((217. / 272.) ** .25 - 0.9450889979585868) < 1e-12
    assert len(a[:3]) + len(a[2:]) - 1 == len(a)
    for bad in ([(1., 0., .5)], [(float('nan'), 0., .5)], [(1., 0., .75)]):
        try:
            stats(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('BAD_CYCLE_ACCEPTED')
    return {'known_answer_and_partition': 4, 'negative_rejections': 3}


def compute_full_grid(root, manifest_path, geometry_path, baseline_path):
    """124 fixed-azimuth section series, 16 source ZIPs, 12001 points each.

    The two 300s intervals share exactly one boundary *sample*, not an
    overlapping time increment. Summed m4 is normalized by 600 cycles.
    """
    import csv
    import gzip
    import io
    import zipfile

    tests = full_grid_selftest()
    def locked_rows(path, expected, label):
        raw = Path(path).read_bytes()
        check(hashlib.sha256(raw).hexdigest() == expected, label + '_SHA')
        return list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))

    manifest_rows = locked_rows(manifest_path, FULL_MANIFEST_SHA, 'MANIFEST')
    geometry_rows = locked_rows(geometry_path, FULL_GEOMETRY_SHA, 'GEOMETRY')
    baseline_rows = locked_rows(baseline_path, FULL_BASELINE_SHA, 'BASELINE')
    check(len(manifest_rows) == 16 and len(geometry_rows) == 31 and
          len(baseline_rows) == 1984, 'SOURCE_ROW_COUNTS')
    manifest = {(r['case'], r['batch']): r for r in manifest_rows}
    check(len(manifest) == 16 and
          set(manifest) == {(c, b) for c in FULL_CASES for b in FULL_BATCHES},
          'SOURCE_MANIFEST_GRID')
    geom = {}
    for g in geometry_rows:
        seg = g['segment']
        check(seg not in geom, 'DUPLICATE_GEOMETRY')
        area, inertia, radius = float(g['A_m2']), float(g['I_m4']), float(g['D_m']) / 2
        check(all(math.isfinite(v) and v > 0 for v in (area, inertia, radius)),
              'BAD_GEOMETRY')
        geom[seg] = (area, inertia, radius)
    check(set(geom) == {f'CSEG_{k:02d}' for k in range(1, 32)}, 'GEOMETRY_GRID')
    selected, counts = {}, {}
    for r in baseline_rows:
        case, seg = r['case'], r['segment']
        key = (case, seg)
        check(case in FULL_CASES and seg in geom, 'BASELINE_ID')
        check(int(r['n_samples']) == 12001, 'BASELINE_SAMPLES')
        az, d4 = float(r['azimuth_deg']), float(r['DEL_m4_MPa'])
        check(math.isfinite(az) and math.isfinite(d4) and d4 > 0,
              'BAD_BASELINE_DEL')
        counts[key] = counts.get(key, 0) + 1
        if key not in selected or d4 > selected[key][1]:
            selected[key] = (az, d4)
    check(len(selected) == 124 and all(counts[k] == 16 for k in selected),
          'BASELINE_16AZ_GRID')

    out, sources = [], []
    for case in FULL_CASES:
        for batch, segnums in FULL_BATCHES.items():
            meta = manifest[(case, batch)]
            zpath = Path(root) / f'S06_{case}_{batch}_original.zip'
            raw = zpath.read_bytes()
            check(hashlib.sha256(raw).hexdigest() == meta['zip_sha256'],
                  'ZIP_SHA:' + case + ':' + batch)
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                check(z.testzip() is None, 'ZIP_CRC')
                members = [name for name in z.namelist()
                           if name.endswith('_31seg.csv.gz')]
                check(len(members) == 1, 'ZIP_MEMBER')
                gz = z.read(members[0])
            check(hashlib.sha256(gz).hexdigest() == meta['gzip_sha256'],
                  'GZIP_SHA')
            decoded = gzip.decompress(gz)
            check(hashlib.sha256(decoded).hexdigest() ==
                  meta['uncompressed_csv_sha256'], 'CSV_SHA')
            groups = {f'CSEG_{k:02d}': [] for k in segnums}
            count = 0
            for row in csv.DictReader(io.StringIO(decoded.decode('utf-8-sig'))):
                count += 1
                check(row['case'] == case and row['batch'] == batch,
                      'CASE_BATCH_ID')
                seg = row['segment']
                check(seg in groups, 'BATCH_SEGMENT_ID')
                values = tuple(float(row[col]) for col in
                               ('time_s', 'Fz_kN', 'Mx_kNm', 'My_kNm'))
                check(all(map(math.isfinite, values)), 'NONFINITE_SOURCE')
                groups[seg].append(values)
            check(count == int(meta['rows']) == 12001 * len(segnums),
                  'SOURCE_BATCH_ROWS')
            sources.append({'case': case, 'batch': batch,
                            'artifact_id': int(meta['artifact_id']),
                            'zip_sha256': meta['zip_sha256'],
                            'gzip_sha256': meta['gzip_sha256'],
                            'csv_sha256': meta['uncompressed_csv_sha256'],
                            'source_rows': count})
            for seg in groups:
                rows = groups[seg]
                check(len(rows) == 12001, 'SECTION_SAMPLE_COUNT')
                check(all(abs(row[0] - (100. + i * .05)) <= 1e-7
                          for i, row in enumerate(rows)), 'TIME_GRID')
                az, oracle = selected[(case, seg)]
                a, I, radius = geom[seg]
                theta = math.radians(az)
                s, c = math.sin(theta), math.cos(theta)
                xs = [.001 * (row[1] / a +
                              radius / I * (s * row[2] - c * row[3]))
                      for row in rows]
                opened = stats(prior.rainflow(xs))
                periodic, imax = periodic_assumption(xs)
                closed = stats(periodic)
                first = stats(prior.rainflow(xs[:6001]))
                second = stats(prior.rainflow(xs[6000:]))
                check(abs(opened['DEL4_MPa'] - oracle) < 1e-7,
                      'BASELINE_16AZ_DEL4_ORACLE:' + case + ':' + seg)
                check(closed['half_rows'] == 0, 'CLOSED_RESIDUAL_HALF')
                split_m4 = first['m4_MPa4_cycles'] + second['m4_MPa4_cycles']
                split_d4 = (split_m4 / 600.) ** .25
                out.append({
                    'case': case, 'segment': seg,
                    'fixed_azimuth_deg_from_16az_max_m4': az,
                    'time_start_s': 100., 'time_split_s': 400., 'time_end_s': 700.,
                    'samples': 12001,
                    'open_DEL4_MPa': opened['DEL4_MPa'],
                    'historical_16az_oracle_DEL4_MPa': oracle,
                    'open_half_cycle_rows': opened['half_rows'],
                    'open_half_m4_fraction': opened['half_m4_fraction'],
                    'assumed_periodic_DEL4_MPa': closed['DEL4_MPa'],
                    'assumed_periodic_vs_open_pct':
                        100 * (closed['DEL4_MPa'] / opened['DEL4_MPa'] - 1),
                    'split_two_300s_DEL4_MPa': split_d4,
                    'split_two_300s_vs_open_pct':
                        100 * (split_d4 / opened['DEL4_MPa'] - 1),
                    'first_300s_DEL4_Nref300_MPa':
                        (first['m4_MPa4_cycles'] / 300.) ** .25,
                    'second_300s_DEL4_Nref300_MPa':
                        (second['m4_MPa4_cycles'] / 300.) ** .25,
                    'first_half_rows': first['half_rows'],
                    'second_half_rows': second['half_rows'],
                    'unobserved_boundary_jump_MPa': xs[-1] - xs[0],
                    'periodic_rotation_max_index': imax})
    check(len(out) == 124 and len(sources) == 16, 'FULL_GRID_RESULT_COUNT')
    summary = {}
    for case in FULL_CASES:
        subset = [r for r in out if r['case'] == case]
        check(len(subset) == 31, 'CASE_SEGMENTS')
        worst_periodic = max(subset,
                             key=lambda r: abs(r['assumed_periodic_vs_open_pct']))
        worst_split = max(subset,
                          key=lambda r: abs(r['split_two_300s_vs_open_pct']))
        summary[case] = {
            'sections': len(subset),
            'max_abs_periodic_vs_open_pct':
                abs(worst_periodic['assumed_periodic_vs_open_pct']),
            'periodic_worst_segment': worst_periodic['segment'],
            'max_abs_split_vs_open_pct':
                abs(worst_split['split_two_300s_vs_open_pct']),
            'split_worst_segment': worst_split['segment'],
            'max_abs_open_oracle_MPa':
                max(abs(r['open_DEL4_MPa'] -
                        r['historical_16az_oracle_DEL4_MPa']) for r in subset)}
    return {
        'status': 'FOUR_REAL_ETM_31_SECTION_FIXED_AZIMUTH_BOUNDARY_QC_NOT_MATERIAL_FATIGUE',
        'SOURCE': '16 SHA-locked historical GitHub Actions ZIP/GZIP/CSV exports; not original OUTB',
        'REF': 'T077 historical ASTM-style reversal-stack rainflow; no new paper full text',
        'STANDARD': 'No newly read licensed IEC/GB/NB clauses; no compliance decision',
        'OFFICIAL': 'GitHub Actions historical source archive; 2025 IEC clause HOLD',
        'RUN': 'Non-solver Python source-level rainflow, 124x12001 observed samples',
        'FIG': 0, 'TAB': '124 section-case JSON rows',
        'manifest_sha256': FULL_MANIFEST_SHA,
        'geometry_sha256': FULL_GEOMETRY_SHA,
        'baseline_16az_sha256': FULL_BASELINE_SHA,
        'source_files': sources,
        'algorithm': 'fixed azimuth selected from preexisting 16-angle m4 maximum; open half cycles n=0.5; hypothetical cyclic wrap; two independently rainflow-counted 300s windows sharing one boundary sample, summed m4/Nref600',
        'assumptions': 'linear gross annulus nominal stress, historical OpenFAST local axes assumed fixed, ETM only, no PT or material mean-stress correction, Nref=600, m=4',
        'ERROR_BUDGET': 'ZIP/GZIP/CSV SHA exact, historical 16az DEL4 oracle abs <1e-7MPa, time abs 1e-7s; boundary true continuation, physical axes, local materials, long-term probability unquantified',
        'HOLD': 'Neither hypothetical cyclic closure nor 300s splitting is physical truth; cross-batch state, original OUTB, DLC1.2, material local stresses, annual Miner and earthquake all unvalidated',
        'FAILURES': 'No failure claimed until native CI logs inspected',
        'software': sys.version.split()[0],
        'tests': {**tests, 'source_zip_gzip_csv_sha': 16,
                  'historical_16az_oracle': 124},
        'physical_PASS': False, 'stage_PASS_count': 0,
        'case_summary': summary, 'results': out}




if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--zip-dir', type=Path)
    p.add_argument('--receipt', type=Path)
    p.add_argument('--self-test', action='store_true')
    p.add_argument('--full-grid', action='store_true')
    p.add_argument('--manifest', type=Path)
    p.add_argument('--geometry', type=Path)
    p.add_argument('--baseline', type=Path)
    args = p.parse_args()
    if args.self_test and not args.zip_dir:
        print(json.dumps({'original': selftest(), 'full_grid': full_grid_selftest()}))
        sys.exit(0)
    if not args.zip_dir or not args.receipt:
        p.error('--zip-dir and --receipt are required for source calculation')
    if args.full_grid:
        if not all((args.manifest, args.geometry, args.baseline)):
            p.error('--full-grid requires --manifest, --geometry and --baseline')
        receipt = compute_full_grid(args.zip_dir, args.manifest,
                                    args.geometry, args.baseline)
        summary = {'status': receipt['status'], 'case_summary': receipt['case_summary'],
                   'rows': len(receipt['results']), 'tests': receipt['tests']}
    else:
        receipt = compute(args.zip_dir)
        summary = {'status': receipt['status'], 'tests': receipt['tests'],
                   'results': [{'case': r['case'], 'segment': r['segment'],
                                'open_DEL4': r['open']['DEL4_MPa'],
                                'periodic_DEL4': r['assumed_periodic']['DEL4_MPa'],
                                'periodic_vs_open_pct': r['periodic_vs_open_DEL4_pct'],
                                'drop_half_vs_open_pct': r['drop_half_vs_open_DEL4_pct']}
                               for r in receipt['results']]}
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n',
                            encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))
