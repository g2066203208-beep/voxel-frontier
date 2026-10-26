#!/usr/bin/env python3
"""S01: source-locked D400 vs same-centerline phi25 longitudinal steel mass/EA.

Read-only deterministic calculation. Does not substitute T057 geometry or Abaqus,
OpenFAST load regeneration, code checks, or native model verification.
"""
import csv, hashlib, math, re, sys
from pathlib import Path

EXPECTED = '22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a'
RHO, E, G = 7850., 200e9, 9.81
A25 = math.pi * .025**2 / 4


def parse_segment(name, block):
    nodes = {}; edges = []; area = None; mode = None
    for raw in block.splitlines():
        s = raw.strip()
        if not s or s.startswith('**'): continue
        if s.startswith('*'):
            if s.upper().startswith('*NODE'): mode='node'
            elif s.upper().startswith('*ELEMENT, TYPE=T3D2'): mode='element'
            elif s.upper().startswith('*SOLID SECTION,'):
                assert 'HRB400_D400_DIAGNOSTIC' in s, (name, s)
                mode='area'
            else: mode=None
            continue
        if mode == 'node':
            v=s.split(','); nodes[int(v[0])] = tuple(map(float,v[1:4]))
        elif mode == 'element':
            v=s.split(','); edges.append((int(v[1]),int(v[2])))
        elif mode == 'area':
            assert area is None; area=float(s.split(',')[0]); mode=None
    assert area and len(edges) in (152,168,180,192,216)
    assert len(nodes) == 2*len(edges)
    lengths = [math.dist(nodes[a],nodes[b]) for a,b in edges]
    assert all(2.5<l<3.8 for l in lengths), (name, min(lengths),max(lengths))
    d=1000*math.sqrt(4*area/math.pi)
    return {'segment':int(name[-2:]),'bars':len(edges),'diameter_mm':d,'length_m':sum(lengths),
            'area_per_bar_m2':area,'mass_d400_kg':sum(lengths)*area*RHO,
            'mass_phi25_same_path_kg':sum(lengths)*A25*RHO,
            'ea_d400_GN':len(edges)*area*E/1e9,
            'ea_phi25_GN':len(edges)*A25*E/1e9}


def run(path):
    raw=Path(path).read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    if sha!=EXPECTED: raise ValueError(f'SOURCE SHA MISMATCH: {sha}')
    text=raw.decode('utf-8')
    parts={}
    for m in re.finditer(r'^\*Part, name=(RBLONG_\d\d)\n(.*?)^\*End Part',text,re.M|re.S):
        parts[m.group(1)] = parse_segment(m.group(1),m.group(2))
    if sorted(parts)!=[f'RBLONG_{i:02d}' for i in range(1,32)]: raise ValueError('not 31 RBLONG parts')
    rows=[parts[f'RBLONG_{i:02d}'] for i in range(1,32)]
    cumulative=0.
    for row in reversed(rows):
        delta=row['mass_d400_kg']-row['mass_phi25_same_path_kg']
        cumulative+=delta*G/1e6
        row['delta_mass_kg']=delta
        row['delta_gravity_below_segment_MN']=cumulative
        row['ea_ratio_longitudinal_only']=row['ea_d400_GN']/row['ea_phi25_GN']
    assert sum(r['bars'] for r in rows)==5440
    assert abs(sum(r['mass_d400_kg'] for r in rows)-253358.224)<.2
    assert 177000<sum(r['delta_mass_kg'] for r in rows)<178000
    return sha,rows


def main():
    sha,rows=run(sys.argv[1])
    w=csv.DictWriter(sys.stdout,fieldnames=list(rows[0]),lineterminator='\n')
    w.writeheader();w.writerows(rows)
    delta=sum(r['delta_mass_kg'] for r in rows)
    print(f'SOURCE_SHA256={sha}\nROWS={len(rows)}\nD400_LONG_MASS_KG={sum(r["mass_d400_kg"] for r in rows):.6f}\nSAME_PATH_PHI25_MASS_KG={sum(r["mass_phi25_same_path_kg"] for r in rows):.6f}\nDELTA_MASS_KG={delta:.6f}\nDELTA_BASE_GRAVITY_MN={delta*G/1e6:.9f}\nMAX_LONG_EA_RATIO={max(r["ea_ratio_longitudinal_only"] for r in rows):.6f}\nNO_NATIVE_ABAQUS_OR_OPENFAST_RUN=true',file=sys.stderr)
if __name__=='__main__':main()
