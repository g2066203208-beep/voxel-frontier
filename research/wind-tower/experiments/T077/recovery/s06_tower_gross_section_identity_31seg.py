#!/usr/bin/env python3
"""Source-locked 158m OpenFAST tower gross-section E/rho identity; STATIC ONLY.

Compares recovered 70-station tower properties to independently archived
31-segment geometric annuli. Neither source identifies mass ownership or
proves Abaqus/OpenFAST physical equivalence.
"""
import argparse
import csv
import hashlib
import io
import math
import re
from pathlib import Path

TOWER_SHA256 = 'f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983'
GEOMETRY_GIT_BLOB_SHA1 = '52fc85d4cfeac7319a7d994f9652fd61fdc89eb4'
FIELDS = ['segment', 'gross_area_m2', 'gross_I_m4', 'E_from_EA_GPa',
          'E_from_EI_GPa', 'rho_from_TMassDen_kgm3',
          'EA_vs_D400_gross_pct', 'EI_vs_D400_gross_pct',
          'mass_vs_D400_gross_pct', 'E_EA_vs_E_EI_pct']


def source_rows(tower_file, geometry_file):
    tower = Path(tower_file).read_bytes()
    if hashlib.sha256(tower).hexdigest() != TOWER_SHA256:
        raise ValueError('Recovered 158m tower SHA256 mismatch')
    geo = Path(geometry_file).read_bytes()
    git_blob = hashlib.sha1(b'blob ' + str(len(geo)).encode() + b'\0' + geo).hexdigest()
    if git_blob != GEOMETRY_GIT_BLOB_SHA1:
        raise ValueError('Historical 31-segment geometry Git blob SHA1 mismatch')
    numeric = re.compile(r'^[+-]?\d+\.\d+e[+-]\d+$', re.I)
    stations = []
    for line in tower.decode('utf-8').splitlines():
        fields = line.split()
        if len(fields) == 10 and all(numeric.fullmatch(x) for x in fields):
            stations.append([float(x) for x in fields])
    if len(stations) != 70:
        raise ValueError(f'Expected 70 tower stations; got {len(stations)}')
    with io.StringIO(geo.decode('utf-8')) as f:
        geometry = [row for row in csv.DictReader(f) if re.fullmatch(r'CSEG_\d{2}', row['part'])]
    if len(geometry) != 31:
        raise ValueError(f'Expected 31 concrete annuli; got {len(geometry)}')
    rows = []
    for i, g in enumerate(geometry):
        if g['part'] != f'CSEG_{i+1:02d}':
            raise ValueError('Out-of-order geometry')
        p, q = stations[2*i:2*i+2]
        if not (abs(p[1]-q[1]) < 1e-7 and abs(p[2]-q[2]) < 1e-4
                and abs(p[5]-q[5]) < 1e-2):
            raise ValueError(f'Tower station pair not constant: {i+1}')
        outer = (float(g['bottom_outer_diameter_m']) + float(g['top_outer_diameter_m']))/2
        inner = (float(g['bottom_inner_diameter_m']) + float(g['top_inner_diameter_m']))/2
        area = math.pi*(outer**2-inner**2)/4
        inertia = math.pi*(outer**4-inner**4)/64
        E_EA = p[5]/area/1e9
        E_EI = p[2]/inertia/1e9
        rho = p[1]/area
        Ec = 37.0 if i < 2 else 36.5  # D400 provisional INP material; NOT tower generator material
        rows.append([i+1, area, inertia, E_EA, E_EI, rho,
                     100*(E_EA/Ec-1), 100*(E_EI/Ec-1),
                     100*(rho/2400-1), 100*(E_EA/E_EI-1)])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tower_dat')
    ap.add_argument('geometry_csv')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    rows = source_rows(args.tower_dat, args.geometry_csv)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(FIELDS)
        for row in rows:
            w.writerow([row[0], *[f'{x:.6f}' for x in row[1:]]])
    for col in [3, 4, 5, 6, 7, 8, 9]:
        v = [row[col] for row in rows]
        print(f'{FIELDS[col]}: min={min(v):.6f}, max={max(v):.6f}, mean={sum(v)/len(v):.6f}')
    print('STATIC IDENTITY ONLY; SOURCE GENERATOR/REBAR/PT OWNERSHIP STILL HOLD')


if __name__ == '__main__':
    main()
