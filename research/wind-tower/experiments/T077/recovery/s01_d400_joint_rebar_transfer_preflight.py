#!/usr/bin/env python3
"""Read-only S01 joint rebar load-path inventory for Abaqus .inp.

Counts geometric alignment of longitudinal T3D2 ends at each of the 30
concrete segment interfaces. Geometric coincidence does NOT create nodal
connectivity across Abaqus part instances. No native solver/code PASS.
Usage: python s01_d400_joint_rebar_transfer_preflight.py candidate.inp > joints.csv
"""
import csv
import hashlib
import math
import re
import sys


def read_model(path):
    data = open(path, 'rb').read()
    parts, translations = {}, {}
    part = instance = mode = None
    for line in data.decode('utf-8').splitlines():
        s = line.strip()
        if s.startswith('*Part, name='):
            part = s.split('=', 1)[1].strip()
            if re.fullmatch(r'RBLONG_\d{2}', part):
                parts[part] = {'nodes': {}, 'edges': []}
            mode = None
            continue
        if s.startswith('*End Part'):
            part = mode = None
            continue
        if s.startswith('*Instance, name='):
            m = re.match(r'\*Instance, name=([^,]+), part=(.+)', s)
            if m:
                instance = m.group(1)
                translations[instance] = (0.0, 0.0, 0.0)
            continue
        if s.startswith('*End Instance'):
            instance = None
            continue
        if instance and s and not s.startswith('*'):
            try:
                xyz = tuple(map(float, s.split(',')))
                if len(xyz) == 3:
                    translations[instance] = xyz
            except ValueError:
                pass
        if part not in parts:
            continue
        if s.startswith('*'):
            mode = 'node' if s.lower() == '*node' else ('element' if s.lower().startswith('*element, type=t3d2') else None)
            continue
        if not s or s.startswith('**'):
            continue
        a = [v.strip() for v in s.split(',')]
        try:
            if mode == 'node':
                parts[part]['nodes'][int(a[0])] = tuple(map(float, a[1:4]))
            elif mode == 'element':
                parts[part]['edges'].append(tuple(map(int, a[1:3])))
        except (ValueError, IndexError):
            pass
    return data, parts, translations


def end_points(part, shift, top):
    nodes = part['nodes']
    ys = [p[1] for p in nodes.values()]
    target = max(ys) if top else min(ys)
    return [(x + shift[0], z + shift[2], y + shift[1])
            for x, y, z in nodes.values() if abs(y - target) < 1e-6]


def inventory(data, parts, shifts):
    assert len(parts) == 31, 'Expected exactly 31 longitudinal rebar parts'
    for i in range(1, 32):
        name = 'RBLONG_%02d' % i
        p = parts[name]
        assert len(p['nodes']) == 2 * len(p['edges'])
        assert name + '-1' in shifts
    # Only PT top anchorage equations exist in the studied input; do not
    # infer physical connection merely from similar bar coordinates.
    lines = data.decode('utf-8').splitlines()
    equation_blocks = [lines[i+1:i+6] for i, line in enumerate(lines)
                       if line.strip().lower() == '*equation']
    assert len(equation_blocks) == 108, 'Unexpected equation topology'
    assert not any('RBLONG_' in row for block in equation_blocks for row in block), 'Rebar equation detected'
    for i in range(1, 31):
        lo = 'RBLONG_%02d' % i
        hi = 'RBLONG_%02d' % (i+1)
        a = end_points(parts[lo], shifts[lo+'-1'], True)
        b = end_points(parts[hi], shifts[hi+'-1'], False)
        assert len(a) == len(parts[lo]['edges']) and len(b) == len(parts[hi]['edges'])
        assert max(abs(v[2]-b[0][2]) for v in a) < 1e-5, 'Segment elevations do not meet'
        dists = sorted(min(math.hypot(x-X, z-Z) for X, Z, _ in b) for x, z, _ in a)
        n = len(dists)
        yield [i, round(a[0][2], 6), len(a), len(b),
               sum(d < 1e-5 for d in dists),
               round(dists[0]*1000, 6),
               round((dists[(n-1)//2]+dists[n//2])*500, 6),
               round(dists[-1]*1000, 6),
               'NO_SHARED_NODES_DISTINCT_INSTANCES']


def main():
    data, parts, shifts = read_model(sys.argv[1])
    rows = list(inventory(data, parts, shifts))
    w = csv.writer(sys.stdout, lineterminator='\n')
    w.writerow(['joint_after_segment', 'elevation_m', 'lower_bar_ends',
                'upper_bar_ends', 'lower_ends_with_xy_match_0p01mm',
                'nearest_xy_min_mm', 'nearest_xy_median_mm',
                'nearest_xy_max_mm', 'abaqus_direct_bar_continuity'])
    w.writerows(rows)
    print('SOURCE_SHA256=' + hashlib.sha256(data).hexdigest(), file=sys.stderr)
    print('JOINTS=' + str(len(rows)), file=sys.stderr)
    print('COUNT_CHANGES=' + str(sum(r[2] != r[3] for r in rows)), file=sys.stderr)
    print('EXACT_XY_MATCH_JOINTS=' + str(sum(r[4] > 0 for r in rows)), file=sys.stderr)
    print('DIRECT_REBAR_CONTINUITY_JOINTS=0', file=sys.stderr)


if __name__ == '__main__':
    main()
