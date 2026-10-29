#!/usr/bin/env python3
"""S01: 31-segment longitudinal bar area / gross annulus area, STATIC SCREEN ONLY.

Read two SHA256-locked historical inputs; no Abaqus, no code/constructability PASS.
D500 areas are counterfactual at the D400 diagnostic cage bar counts, not a D500 INP.
"""
import argparse
import csv
import hashlib
import math
from pathlib import Path

SOURCE = 'S01_PT_AXIAL_31SEG_SOURCE_20261026.csv'
DESIGN = 'S01_D400_31SEG_MIN_DIAM_SCREEN_20261024.csv'
SOURCE_SHA256 = 'd34331c9b1eacb25cd4ffa46d4430fbe8420965e683f7444cb6cfee207eef99e'
DESIGN_SHA256 = '267049d0ef16b5ea270c98943eade84adcb69f93d5a77c77824788480d94651f'
FIELDS = ('segment', 'bar_count', 'd400_mm', 'd500_mm', 'As_D400_m2',
          'As_D500_proxy_m2', 'annulus_A0_m2', 'annulus_A1_m2',
          'annulus_Amin_m2', 'rho_D400_Amin_pct', 'rho_D500_Amin_pct',
          'D400_u_historical_screen', 'D500_u_historical_screen')


def verified_rows(path, expected_sha):
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == expected_sha, f'INPUT_SHA256_MISMATCH: {path}'
    return list(csv.DictReader(data.decode('utf-8-sig').splitlines()))


def calculate(source, design):
    assert len(source) == len(design) == 31
    by_seg = {row['segment']: row for row in design}
    assert len(by_seg) == 31
    result = []
    for i, g in enumerate(source, 1):
        seg = f'CSEG_{i:02d}'
        assert g['segment'] == seg and seg in by_seg
        d = by_seg[seg]
        a0 = math.pi * (float(g['ro0_m'])**2 - float(g['ri0_m'])**2)
        a1 = math.pi * (float(g['ro1_m'])**2 - float(g['ri1_m'])**2)
        amin = min(a0, a1)
        as400 = float(g['As_long_m2'])
        diam400 = int(d['min_d400_d_mm'])
        diam500 = int(d['d500_repo_d_mm'])
        count = as400 / (math.pi * (diam400 / 1000)**2 / 4)
        assert abs(count - round(count)) < 1e-6, (seg, count)
        as500 = round(count) * math.pi * (diam500 / 1000)**2 / 4
        assert amin > as400 > 0 and amin > as500 > 0
        result.append(dict(zip(FIELDS, (
            seg, round(count), diam400, diam500,
            f'{as400:.12f}', f'{as500:.12f}', f'{a0:.12f}',
            f'{a1:.12f}', f'{amin:.12f}',
            f'{100*as400/amin:.9f}', f'{100*as500/amin:.9f}',
            d['min_d400_u'], d['d500_repo_u']))))
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input-dir', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    source = verified_rows(a.input_dir / SOURCE, SOURCE_SHA256)
    design = verified_rows(a.input_dir / DESIGN, DESIGN_SHA256)
    rows = calculate(source, design)
    with a.out.open('x', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    r400 = [float(x['rho_D400_Amin_pct']) for x in rows]
    r500 = [float(x['rho_D500_Amin_pct']) for x in rows]
    print('S01_STATIC_GEOMETRY_SCREEN_ONLY; NOT_STANDARD_NOT_ABAQUS_NOT_FATIGUE')
    print('D400_max_pct=', max(r400), 'at', rows[r400.index(max(r400))]['segment'])
    print('D500_max_pct=', max(r500), 'at', rows[r500.index(max(r500))]['segment'])
    print('D400_gt5pct=', sum(v > 5 for v in r400), 'D400_gt6pct=', sum(v > 6 for v in r400))
    print('D500_gt5pct=', sum(v > 5 for v in r500), 'D500_gt6pct=', sum(v > 6 for v in r500))
    print('OUTPUT_SHA256=', hashlib.sha256(a.out.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
