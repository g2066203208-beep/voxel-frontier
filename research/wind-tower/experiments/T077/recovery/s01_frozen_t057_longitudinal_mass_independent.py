#!/usr/bin/env python3
"""Read-only 31-segment T057 longitudinal T3D2 mass audit (NOT Abaqus)."""
import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

PARENT_SHA = "c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db"
EXPECTED_PARENT_MASS_KG = 75831.70211016893

def calculate(source, require_parent):
    instances = {}
    for m in re.finditer(r"^\*Instance,\s*name=([^,\n]+),\s*part=([^\n]+)\n(.*?)^\*End Instance", source, re.M | re.S):
        lines = [v.strip() for v in m.group(3).splitlines() if v.strip() and not v.startswith("**")]
        assert len(lines) <= 1, (m.group(2), lines)
        instances[m.group(2).strip()] = [float(v) for v in lines[0].split(",")] if lines else [0., 0., 0.]
    rows = []
    for m in re.finditer(r"^\*Part,\s*name=(RBLONG_\d+)\s*\n(.*?)^\*End Part", source, re.M | re.S):
        name, body = m.group(1), m.group(2)
        n = re.search(r"^\*Node\s*\n(.*?)(?=^\*)", body, re.M | re.S)
        e = re.search(r"^\*Element,\s*type=T3D2\s*\n(.*?)(?=^\*)", body, re.M | re.S)
        sec = re.search(r"^\*Solid Section,\s*elset=([^,\n]+),\s*material=([^\n]+)\n\s*([\d.eE+-]+)", body, re.M)
        assert n and e and sec and name in instances, name
        if require_parent:
            assert sec.group(2).strip() == "HRB335_T057", (name, sec.group(2))
            assert float(sec.group(3)) == 0.000490874, name
        nodes = {}
        for line in n.group(1).splitlines():
            if not line.strip() or line.startswith("**"):
                continue
            v = [float(z) for z in line.split(",")]
            assert len(v) == 4
            nodes[int(v[0])] = v[1:]
        translation = instances[name]
        length = first_y = 0.
        count = 0
        for line in e.group(1).splitlines():
            if not line.strip() or line.startswith("**"):
                continue
            _, a, b = [int(z) for z in line.split(",")]
            p = [nodes[a][i] + translation[i] for i in range(3)]
            q = [nodes[b][i] + translation[i] for i in range(3)]
            L = math.dist(p, q)
            assert L > 0
            length += L
            first_y += L * (p[1] + q[1]) / 2
            count += 1
        mass = 7850. * float(sec.group(3)) * length
        rows.append(dict(segment=name, elements=count, area_m2=float(sec.group(3)),
                         length_m=length, mass_kg=mass, cg_y_m=first_y / length))
    rows.sort(key=lambda r: r["segment"])
    assert len(rows) == 31
    mass = sum(r["mass_kg"] for r in rows)
    return rows, dict(segments=len(rows), elements=sum(r["elements"] for r in rows),
                      mass_kg=mass, cg_y_m=sum(r["mass_kg"]*r["cg_y_m"] for r in rows)/mass,
                      density_kg_m3=7850, native_abaqus="NOT_RUN")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--expect-frozen-parent", action="store_true")
    args = ap.parse_args()
    raw = args.inp.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if args.expect_frozen_parent:
        assert sha == PARENT_SHA, (sha, PARENT_SHA)
    rows, totals = calculate(raw.decode("utf-8"), args.expect_frozen_parent)
    if args.expect_frozen_parent:
        assert totals["elements"] == 5440
        assert abs(totals["mass_kg"] - EXPECTED_PARENT_MASS_KG) < 1e-4
    args.outdir.mkdir(parents=True, exist_ok=True)
    csv_file = args.outdir / "S01_T057_PARENT_RBLONG_31SEG_EXACT_MASS.csv"
    with csv_file.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = dict(source_sha256=sha, source_bytes=len(raw),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  csv_sha256=hashlib.sha256(csv_file.read_bytes()).hexdigest(),
                  totals=totals,
                  parent_reconstruction_difference_kg=totals["mass_kg"]-EXPECTED_PARENT_MASS_KG if args.expect_frozen_parent else None,
                  evidence_level="Direct T057 raw source + independent Python static line integration; NOT native Abaqus",
                  hold="S01 materials/detailing/PT equilibrium; S02 native Data Check NOT RUN")
    (args.outdir/"S01_T057_PARENT_RBLONG_31SEG_EXACT_MASS_MANIFEST.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
