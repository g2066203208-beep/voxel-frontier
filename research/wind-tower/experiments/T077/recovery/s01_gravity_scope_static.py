#!/usr/bin/env python3
"""Read-only, SHA-locked Abaqus INP gravity ownership check; NOT a native solve."""
import argparse
import hashlib
import json
import math
import re
import zipfile
from pathlib import Path

EXPECTED_SHA256 = '22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a'


def unique(pattern, content, flags=re.I | re.S):
    hits = list(re.finditer(pattern, content, flags))
    if len(hits) != 1:
        raise ValueError(f'Expected exactly one match, got {len(hits)}: {pattern[:80]}')
    return hits[0]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--inp', type=Path)
    group.add_argument('--zip', type=Path)
    p.add_argument('--member', default='D400.inp')
    args = p.parse_args()
    if args.inp:
        raw = args.inp.read_bytes()
    else:
        with zipfile.ZipFile(args.zip) as archive:
            raw = archive.read(args.member)
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA256:
        raise ValueError(f'INPUT SHA256 MISMATCH: {sha}')
    src = raw.decode('utf-8')
    pt = unique(r'^\*Part,\s*name=PT_36x15p2\s*$([\s\S]*?)^\*End Part\s*$', src, re.I | re.M).group(1)
    node_block = unique(r'^\*Node\s*$\n([\s\S]*?)(?=^\*)', pt, re.I | re.M).group(1)
    nodes = {}
    for line in node_block.splitlines():
        if not line.strip() or line.lstrip().startswith('**'):
            continue
        f = [v.strip() for v in line.split(',')]
        nodes[int(f[0])] = tuple(map(float, f[1:4]))
    el_block = unique(r'^\*Element,\s*type=T3D2\s*$\n([\s\S]*?)(?=^\*)', pt, re.I | re.M).group(1)
    elems = []
    for line in el_block.splitlines():
        if line.strip() and not line.lstrip().startswith('**'):
            f = [int(v.strip()) for v in line.split(',')]
            elems.append((f[0], f[1], f[2]))
    assert len(nodes) == 72 and len(elems) == 36
    sec = unique(r'^\*Solid Section,\s*elset=SET_PT_ALL_GEOM,\s*material=STRAND_1860\s*$\n\s*([\d.eE+-]+)', pt, re.I | re.M)
    area = float(sec.group(1))
    material = unique(r'^\*Material,\s*name=STRAND_1860\s*$([\s\S]*?)(?=^\*Material|^\*\*\s*BOUNDARY CONDITIONS)', src, re.I | re.M).group(1)
    density = float(unique(r'^\*Density\s*$\n\s*([\d.eE+-]+)', material, re.I | re.M).group(1))
    lengths = [math.dist(nodes[n1], nodes[n2]) for _, n1, n2 in elems]
    gravity = unique(r'^\*Step,\s*name=Gravity[^\n]*$([\s\S]*?)^\*End Step\s*$', src, re.I | re.M).group(1)
    dload = unique(r'^\*Dload\s*$\n\s*,\s*GRAV\s*,\s*([\d.eE+-]+)\s*,\s*([\d.eE+-]+)\s*,\s*([\d.eE+-]+)\s*,\s*([\d.eE+-]+)', gravity, re.I | re.M)
    g, dx, dy, dz = map(float, dload.groups())
    assert (dx, dy, dz) == (0.0, -1.0, 0.0) and g > 0
    mass = area * density * sum(lengths)
    rna_mass = float(unique(r'^\*Mass,\s*elset=RNA_R2_EQUIV_MASS\s*$\n\s*([\d.eE+-]+)', src, re.I | re.M).group(1))
    result = {
        'input_sha256': sha,
        'source_bytes': len(raw),
        'pt_element_type': 'T3D2',
        'pt_element_count': len(elems),
        'pt_length_each_m_minmax': [min(lengths), max(lengths)],
        'pt_area_each_m2': area,
        'pt_density_kg_m3': density,
        'pt_mass_kg': mass,
        'pt_gravity_weight_N': mass * g,
        'rna_point_mass_kg': rna_mass,
        'rna_gravity_weight_N': rna_mass * g,
        'gravity_keyword': ',GRAV',
        'gravity_direction': [dx, dy, dz],
        'gravity_scope': 'blank first field; all mass-contributing elements per Abaqus *DLOAD documentation',
        'evidence_level': 'STATIC SOURCE CHECK ONLY; no Abaqus native solver or reaction force',
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
