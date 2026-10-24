#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only T057 native INP geometry audit: T3D2 longitudinal lines vs 72-chord hoops.

Computes at every existing hoop ring plane the nearest distance between the
longitudinal line interpolation and the actual 72-segment hoop polygon, less
the two nominal bar radii. Also screens hypothetical relocated longitudinal
centrelines. NO new Abaqus model is generated; no contact/constructability PASS.
Example:
python research/wind-tower/experiments/T077/recovery/s01_native_inp_cage_polygon_clearance.py \
 --inp research/wind-tower/experiments/T057/inputs/BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp \
 --out /tmp/S01_T057_INP_CAGE_POLYGON_31SEG.csv
"""
from __future__ import annotations
import argparse, csv, hashlib, math, re
from collections import defaultdict
from pathlib import Path

HOOP_DIAM_MM = 14.0
HOOP_SURFACE_OFFSET_M = 0.037
TARGET_GAP_MM = 5.0
HOOP_CHORDS = 72
STEP = 2 * math.pi / HOOP_CHORDS


def part_section(text: str, name: str) -> str:
    start = text.index("*Part, name=" + name + "\n")
    end = text.index("*End Part", start)
    return text[start:end]


def section_rows(part: str, keyword: str):
    k = part.index(keyword) + len(keyword)
    for line in part[k:].splitlines():
        if line.startswith("*"):
            break
        a = [v.strip() for v in line.split(",")]
        if len(a) >= 3 and a[0]:
            yield a


def get_hoops(part: str):
    rings = {}
    node_count = 0
    for a in section_rows(part, "*Node\n"):
        if len(a) != 4:
            continue
        x, y, z = map(float, a[1:4])
        key = round(y, 5)
        r = math.hypot(x, z)
        if key not in rings:
            rings[key] = [y, 0, float("inf"), -float("inf")]
        q = rings[key]
        q[1] += 1
        q[2] = min(q[2], r)
        q[3] = max(q[3], r)
        node_count += 1
    if len(rings) != 1399 or node_count != 201456 or any(v[1] != 144 for v in rings.values()):
        raise ValueError("T057 hoop node/ring identity changed; audit not applicable")
    # The first 201456 T3D2 elements must form two 72-chord polygons per ring.
    checked = 0
    for a in section_rows(part, "*Element, type=T3D2\n"):
        if len(a) != 3:
            continue
        eid, n1, n2 = map(int, a)
        if eid > 201456:
            break
        k = eid - 1
        ring = k // 144
        layer = (k % 144) // 72
        j = k % 72
        expected1 = ring * 144 + layer * 72 + j + 1
        expected2 = ring * 144 + layer * 72 + (1 if j == 71 else j + 2)
        if n1 != expected1 or n2 != expected2:
            raise ValueError(f"hoop chord topology mismatch at element {eid}")
        checked += 1
    if checked != 201456:
        raise ValueError(f"hoop chord count changed: {checked}")
    return sorted(rings.values(), key=lambda x: x[0]), node_count, checked


def instance_yshift(text: str, name: str) -> float:
    k = text.index(f"*Instance, name={name}-1, part={name}")
    q = text[k:text.index("*End Instance", k)].splitlines()
    for line in q[1:]:
        if line.strip() and not line.startswith("*"):
            return float(line.split(",")[1])
    return 0.0


def get_bars(part: str):
    nodes = {}
    for a in section_rows(part, "*Node\n"):
        if len(a) == 4:
            nodes[int(a[0])] = tuple(map(float, a[1:4]))
    bars = []
    for a in section_rows(part, "*Element, type=T3D2\n"):
        if len(a) == 3:
            bars.append((nodes[int(a[1])], nodes[int(a[2])]))
    return bars, len(nodes)


def polygon_distance_m(r: float, theta: float, radius: float) -> float:
    # Exact distance to nearest straight chord of a regular 72-gon,
    # with vertex 1 at azimuth 0 and chord 1 spanning azimuth 0..5 degrees.
    delta = ((theta % STEP) + STEP) % STEP - STEP / 2
    x = r * math.cos(delta)
    y = r * math.sin(delta)
    return math.hypot(x - radius * math.cos(STEP / 2),
                      max(0.0, abs(y) - radius * math.sin(STEP / 2)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--diameters", type=Path, default=Path(__file__).with_name(
        "S01_EXACT_ETA_31SEG_BRANCH_SCREEN_20261024.csv"))
    args = ap.parse_args()
    raw = args.inp.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8")
    hoops, hoop_nodes, hoop_elements = get_hoops(part_section(text, "HOOP_TIE_CAGE_T046"))
    with args.diameters.open(encoding="utf-8-sig", newline="") as f:
        diam = {r["segment"]: int(r["HRB335_assumed300_min_d"]) for r in csv.DictReader(f)}
    if len(diam) != 31:
        raise ValueError("31 diameters expected")
    out = []
    for i in range(1, 32):
        partname = f"RBLONG_{i:02d}"
        seg = f"CSEG_{i:02d}"
        bars, nn = get_bars(part_section(text, partname))
        shift = instance_yshift(text, partname)
        d = diam[seg]
        mn25 = mnold = mnnew = float("inf")
        maxshift = 0.0
        nplane = nsample = 0
        for y, count, ri, ro in hoops:
            active = 0
            for a, b in bars:
                ya, yb = a[1] + shift, b[1] + shift
                if not (min(ya, yb) - 1e-6 <= y <= max(ya, yb) + 1e-6):
                    continue
                t = (y - ya) / (yb - ya)
                if not (0 <= t <= 1):
                    continue
                active += 1
                x = a[0] + t * (b[0] - a[0])
                z = a[2] + t * (b[2] - a[2])
                r, theta = math.hypot(x, z), math.atan2(z, x)
                inner = abs(r - ri) < abs(r - ro)
                hoop_r = ri if inner else ro
                dist_old = polygon_distance_m(r, theta, hoop_r) * 1000
                surface_r = (ri - HOOP_SURFACE_OFFSET_M) if inner else (ro + HOOP_SURFACE_OFFSET_M)
                old_offset = (r - surface_r if inner else surface_r - r) * 1000
                required = 37.0 + (HOOP_DIAM_MM + d) / 2 + TARGET_GAP_MM
                new_offset = max(old_offset, required)
                rnew = surface_r + new_offset / 1000 if inner else surface_r - new_offset / 1000
                dist_new = polygon_distance_m(rnew, theta, hoop_r) * 1000
                mn25 = min(mn25, dist_old - (HOOP_DIAM_MM + 25) / 2)
                mnold = min(mnold, dist_old - (HOOP_DIAM_MM + d) / 2)
                mnnew = min(mnnew, dist_new - (HOOP_DIAM_MM + d) / 2)
                maxshift = max(maxshift, new_offset - old_offset)
                nsample += 1
            if active:
                nplane += 1
        if nplane == 0 or not all(math.isfinite(x) for x in (mn25, mnold, mnnew)):
            raise ValueError(f"no valid intersections: {seg}")
        out.append(dict(segment=seg, diameter_mm=d, bar_elements=len(bars),
                        hoop_planes=nplane, bar_hoop_plane_samples=nsample,
                        min_original_phi25_clear_mm=mn25,
                        min_unmoved_candidate_clear_mm=mnold,
                        min_relocated_candidate_clear_mm=mnnew,
                        max_radial_shift_mm=maxshift))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)
    print("T057 INP SHA256", sha256, "hoop nodes", hoop_nodes,
          "verified hoop edges", hoop_elements, "bar elements", sum(r["bar_elements"] for r in out))
    print("unmoved clashes", sum(r["min_unmoved_candidate_clear_mm"] < 0 for r in out),
          "relocated clashes", sum(r["min_relocated_candidate_clear_mm"] < 0 for r in out))
    print("STATUS: GEOMETRIC POLYGON SCREEN ONLY, NOT NATIVE/CONSTRUCTION PASS")


if __name__ == "__main__":
    main()
