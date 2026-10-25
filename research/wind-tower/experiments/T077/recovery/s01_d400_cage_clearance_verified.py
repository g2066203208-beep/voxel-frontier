"""S01 static 31-segment bar/hoop geometric gap (m). NOT Abaqus/standard PASS.
Usage: python s01_d400_cage_clearance_verified.py candidate.inp > result.csv
"""
import collections, csv, hashlib, math, re, sys
import numpy as np
raw = open(sys.argv[1], 'rb').read()
parts, shifts = {}, {}
part = mode = inst = None
for line in raw.decode('utf-8').splitlines():
    if line.startswith('*Part, name='):
        part = line.split('=', 1)[1].strip()
        parts[part] = {'nodes': {}, 'bars': [], 'area': None}
    elif line.startswith('*End Part'):
        part = mode = None
    elif part:
        if line.startswith('*'):
            mode = ('node' if line.lower() == '*node' else
                    'bar' if line.lower().startswith('*element, type=t3d2') else
                    'area' if line.lower().startswith('*solid section, elset=set_all,') else None)
        elif line and not line.startswith('**'):
            a = line.split(',')
            try:
                if mode == 'node' and len(a) >= 4:
                    parts[part]['nodes'][int(a[0])] = tuple(map(float, a[1:4]))
                elif mode == 'bar' and len(a) >= 3:
                    parts[part]['bars'].append(tuple(map(int, a[:3])))
                elif mode == 'area':
                    parts[part]['area'] = float(a[0]); mode = None
            except ValueError:
                pass
    if line.startswith('*Instance, name='):
        m = re.search(r'name=([^,]+), part=(.+)', line)
        if m:
            inst = m.group(1); shifts[inst] = 0.0
    elif inst and line.startswith('*End Instance'):
        inst = None
    elif inst and not line.startswith('*') and not line.startswith('**') and line.strip():
        try:
            shifts[inst] = float(line.split(',')[1])
        except (ValueError, IndexError):
            pass
cage = parts['HOOP_TIE_CAGE_T046']
levels = collections.defaultdict(list)
for nid, (x, y, z) in cage['nodes'].items():
    levels[round(y, 7)].append((nid, x, z, math.hypot(x, z)))
edges = {frozenset((a, b)) for _, a, b in cage['bars']}
rings = {}
for y, pts in levels.items():
    assert len(pts) == 144, ('hoop node count', y, len(pts))
    pts.sort(key=lambda p: p[3]); pair = []
    for group in (pts[:72], pts[72:]):
        group.sort(key=lambda p: math.atan2(p[2], p[1]))
        assert all(frozenset((group[k][0], group[(k+1) % 72][0])) in edges for k in range(72))
        pair.append(np.array([(p[1], p[2]) for p in group]))
    rings[y] = pair

def poly_gap(points, poly):
    v = np.roll(poly, -1, axis=0) - poly
    w = points[:, None, :] - poly[None, :, :]
    t = np.clip(np.sum(w * v[None, :, :], axis=2) / np.sum(v*v, axis=1)[None, :], 0, 1)
    return np.linalg.norm(w - t[:, :, None] * v[None, :, :], axis=2).min(axis=1)

out = csv.writer(sys.stdout)
out.writerow(['segment', 'bar_diameter_mm', 'bar_count', 'hoop_levels', 'pairs', 'negative_pairs', 'minimum_gap_mm'])
for seg in range(1, 32):
    name = f'RBLONG_{seg:02d}'; p = parts[name]; dy = shifts[name + '-1']
    bars = []
    for _, n1, n2 in p['bars']:
        x1, y1, z1 = p['nodes'][n1]; x2, y2, z2 = p['nodes'][n2]
        assert y2 > y1
        bars.append((x1, y1 + dy, z1, x2, y2 + dy, z2))
    diam = math.sqrt(4*p['area']/math.pi)
    threshold = (diam + .014)/2
    n = nlevel = neg = 0; worst = float('inf')
    for y, (inner, outer) in rings.items():
        if not (bars[0][1]+1e-6 <= y <= bars[0][4]-1e-6):
            continue
        xy = np.array([[b[0]+(b[3]-b[0])*(y-b[1])/(b[4]-b[1]),
                        b[2]+(b[5]-b[2])*(y-b[1])/(b[4]-b[1])] for b in bars])
        gap = np.minimum(poly_gap(xy, inner), poly_gap(xy, outer)) - threshold
        n += len(bars); nlevel += 1
        neg += int(np.count_nonzero(gap < -1e-6)); worst = min(worst, float(gap.min()))
    out.writerow([seg, round(diam*1000, 6), len(bars), nlevel, n, neg, round(worst*1000, 6)])
print('SOURCE_SHA256=' + hashlib.sha256(raw).hexdigest(), file=sys.stderr)
print('HOOP_LEVELS=' + str(len(rings)), file=sys.stderr)
