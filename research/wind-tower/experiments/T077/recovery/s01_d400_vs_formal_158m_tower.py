#!/usr/bin/env python3
"""S01/S06 static sensitivity only: source-locked D400 T3D2 vs 158m OpenFAST tower.

Not a validated composite EI, design-code pass, physical equilibrium, or permission
to reuse historic wind loads without a model-consistency decision.
"""
import argparse
import csv
import hashlib
import math
import re
from pathlib import Path

INP_SHA = "22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a"
TOWER_SHA = "f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983"
ES, EC, RHO = 200e9, 40.05e9, 7850.0  # screening assumptions, NOT calibrated

def read_locked(path, expected):
    b = Path(path).read_bytes()
    actual = hashlib.sha256(b).hexdigest()
    if actual != expected:
        raise ValueError(f"SHA256 mismatch {path}: {actual}")
    return b.decode("utf-8")

def tower_rows(path):
    rows = []
    for line in read_locked(path, TOWER_SHA).splitlines():
        fields = line.split()
        if len(fields) == 10 and all(re.fullmatch(r"[+-]?\d+\.\d+e[+-]\d+", s, re.I) for s in fields):
            rows.append([float(s) for s in fields])
    if len(rows) != 70 or abs(rows[61][0]*158-112) > .01:
        raise ValueError("wrong 158m tower station count or 112m interface")
    for i in range(31):
        a, b = rows[2*i:2*i+2]
        if abs(a[1]-b[1]) > 1e-6 or abs(a[2]-b[2]) > 1e-3:
            raise ValueError(f"tower station pair mismatch: {i+1}")
    return rows

def longitudinal_parts(path):
    s = read_locked(path, INP_SHA)
    parts = {}
    for m in re.finditer(r"^\*Part, name=(RBLONG_\d\d)\n(.*?)^\*End Part", s, re.M|re.S):
        name, block = m.groups()
        nodes, bars, area, mode = {}, [], None, None
        for raw in block.splitlines():
            line = raw.strip()
            if line.startswith("*"):
                up = line.upper()
                mode = ("node" if up.startswith("*NODE") else
                        "element" if up.startswith("*ELEMENT, TYPE=T3D2") else
                        "area" if up.startswith("*SOLID SECTION") else None)
                continue
            if not line or line.startswith("**"):
                continue
            if mode == "node":
                a = line.split(",")
                nodes[int(a[0])] = tuple(map(float, a[1:4]))
            elif mode == "element":
                a = line.split(",")
                bars.append((int(a[1]), int(a[2])))
            elif mode == "area":
                area = float(line.split(",")[0])
                mode = None
        if area is None or not bars:
            raise ValueError(f"missing T3D2/section {name}")
        Ix = Iz = length = 0.
        for n1, n2 in bars:
            p, q = nodes[n1], nodes[n2]
            x, z = (p[0]+q[0])/2, (p[2]+q[2])/2
            Ix += area*z*z
            Iz += area*x*x
            length += math.dist(p, q)
        parts[int(name[-2:])] = (len(bars), len(bars)*area, Ix, Iz, length*area*RHO)
    if sorted(parts) != list(range(1, 32)) or sum(p[0] for p in parts.values()) != 5440:
        raise ValueError("D400 31-segment/5440-bar identity failed")
    if abs(sum(p[4] for p in parts.values())-253358.22431) > .1:
        raise ValueError("D400 longitudinal mass regression failed")
    return parts

def run(inp, tower, output):
    t, parts = tower_rows(tower), longitudinal_parts(inp)
    rows = []
    for i in range(1, 32):
        a, b = t[2*i-2:2*i]
        count, As, Ix, Iz, mass = parts[i]
        if abs(Ix-Iz)/((Ix+Iz)/2) > 1e-5:
            raise ValueError(f"unbalanced rebar layout: {i}")
        Is = (Ix+Iz)/2
        rows.append(dict(segment=i, z_start_m=158*a[0], z_end_m=158*b[0],
            openfast_tmassden_kgpm=a[1], openfast_ei_Nm2=a[2],
            d400_bars=count, d400_rebar_As_m2=As, d400_rebar_Is_m4=Is,
            d400_longitudinal_mass_kg=mass,
            perfect_bond_delta_EI_pct=100*(ES-EC)*Is/a[2],
            hypothetical_added_longitudinal_mass_pct=100*As*RHO/a[1]))
    with open(output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print("SOURCE_INP_SHA256", INP_SHA)
    print("SOURCE_TOWER_SHA256", TOWER_SHA)
    print("OUTPUT_SHA256", hashlib.sha256(Path(output).read_bytes()).hexdigest())
    print("SEGMENTS", len(rows))
    for k in ("perfect_bond_delta_EI_pct", "hypothetical_added_longitudinal_mass_pct"):
        vals = [r[k] for r in rows]
        print(k, "min", min(vals), "max", max(vals), "mean", sum(vals)/len(vals))
    print("NOT PHYSICAL PASS; no native Abaqus/OpenFAST production run")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("d400_inp")
    p.add_argument("formal_158m_tower_dat")
    p.add_argument("output_csv")
    a = p.parse_args()
    run(a.d400_inp, a.formal_158m_tower_dat, a.output_csv)
