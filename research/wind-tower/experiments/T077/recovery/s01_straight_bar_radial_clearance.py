#!/usr/bin/env python3
"""Read-only, realizable straight-T3D2 radial relocation screening for S01.

Unlike the earlier ring-by-ring virtual relocation, this applies ONE radial
translation to BOTH endpoints of every longitudinal T3D2 within each segment.
A constant displacement of endpoints preserves each bar as a straight T3D2.
0/1/5 mm targets are numerical sensitivity cases, NOT code requirements.
No INP generated; no confinement/anchorage/constructability/native PASS.

Run in the same folder as s01_native_inp_cage_polygon_clearance.py:
python s01_straight_bar_radial_clearance.py --inp /path/T057.inp --out /path/summary.csv
"""
import argparse
import csv
import hashlib
import math
from pathlib import Path
from s01_native_inp_cage_polygon_clearance import (
    get_hoops, get_bars, instance_yshift, part_section, polygon_distance_m
)

T057_SHA256 = "c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db"
TARGETS_MM = (0., 1., 5.)
HOOP_D_MM = 14.


def make_samples(bars, yshift, hoops):
    samples = []
    for a, b in bars:
        ra, rb = math.hypot(a[0], a[2]), math.hypot(b[0], b[2])
        if min(ra, rb) <= 0 or abs(a[1] - b[1]) < 1e-12:
            raise ValueError("degenerate T3D2")
        layers = set()
        ya, yb = a[1] + yshift, b[1] + yshift
        for y, _, ri, ro in hoops:
            if y < min(ya, yb) - 1e-6 or y > max(ya, yb) + 1e-6:
                continue
            t = (y - ya) / (yb - ya)
            if t < 0 or t > 1:
                continue
            x, z = a[0] + t * (b[0] - a[0]), a[2] + t * (b[2] - a[2])
            r = math.hypot(x, z)
            inner = abs(r - ri) < abs(r - ro)
            layers.add(inner)
            sign = 1 if inner else -1
            ux = sign * ((1 - t) * a[0] / ra + t * b[0] / rb)
            uz = sign * ((1 - t) * a[2] / ra + t * b[2] / rb)
            samples.append((x, z, ux, uz, ri if inner else ro,
                            ri - .037 if inner else ro + .037, inner, y))
        if len(layers) > 1:
            raise ValueError("one bar switches between inner/outer hoop layers")
    return samples


def evaluate(samples, delta, diameter, detail=False):
    minimum, cover = float("inf"), float("inf")
    layers = {}
    for x, z, ux, uz, ring, wall, inner, y in samples:
        xx, zz = x + delta * ux, z + delta * uz
        r = math.hypot(xx, zz)
        clearance = 1000 * polygon_distance_m(r, math.atan2(zz, xx), ring) - (14 + diameter) / 2
        minimum = min(minimum, clearance)
        if detail:
            cover = min(cover, (r - wall if inner else wall - r) * 1000 - diameter / 2)
            v = layers.setdefault(y, [float("-inf"), float("inf")])
            if inner:
                v[0] = max(v[0], r)
            else:
                v[1] = min(v[1], r)
    if not detail:
        return minimum
    # Conservative radial lower bound even for differing azimuths; not full
    # three-dimensional rebar collision or anchorage validation.
    separation = min(((outer - inner) * 1000 - diameter
                      for inner, outer in layers.values()
                      if math.isfinite(inner) and math.isfinite(outer)),
                     default=float("nan"))
    return minimum, cover, separation


def shift_for(samples, diameter, target):
    if evaluate(samples, 0., diameter) >= target:
        return 0.
    lo, hi = 0., .08
    if evaluate(samples, hi, diameter) < target:
        raise ValueError("80mm radial search bound insufficient")
    for _ in range(33):
        mid = (lo + hi) / 2
        if evaluate(samples, mid, diameter) >= target:
            hi = mid
        else:
            lo = mid
    return hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--diameters", type=Path, default=Path(__file__).with_name(
        "S01_EXACT_ETA_31SEG_BRANCH_SCREEN_20261024.csv"))
    args = ap.parse_args()
    raw = args.inp.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != T057_SHA256:
        raise ValueError("T057 input SHA256 differs: " + digest)
    inp = raw.decode("utf-8")
    hoops, n_nodes, n_edges = get_hoops(part_section(inp, "HOOP_TIE_CAGE_T046"))
    with args.diameters.open(encoding="utf-8-sig", newline="") as f:
        diameters = {r["segment"]: int(r["HRB335_assumed300_min_d"])
                     for r in csv.DictReader(f)}
    if len(diameters) != 31:
        raise ValueError("expected 31 diameters")
    rows = []
    for i in range(1, 32):
        seg, name = f"CSEG_{i:02d}", f"RBLONG_{i:02d}"
        bars, _ = get_bars(part_section(inp, name))
        samples = make_samples(bars, instance_yshift(inp, name), hoops)
        if not samples:
            raise ValueError("no intersections: " + seg)
        d = diameters[seg]
        shifts = {target: shift_for(samples, d, target) for target in TARGETS_MM}
        actual, cover, interlayer = evaluate(samples, shifts[5.], d, detail=True)
        if actual < 5 - 1e-6:
            raise ValueError("5mm target not achieved: " + seg)
        rows.append(dict(segment=seg, diameter_mm=d, bar_elements=len(bars),
                         bar_hoop_plane_samples=len(samples),
                         initial_min_clear_mm=evaluate(samples, 0., d),
                         straight_shift_for_0mm_mm=1000 * shifts[0.],
                         straight_shift_for_1mm_mm=1000 * shifts[1.],
                         straight_shift_for_5mm_mm=1000 * shifts[5.],
                         achieved_min_clear_5mm_mm=actual,
                         conservative_min_interlayer_clear_5mm_mm=interlayer,
                         min_cover_5mm_mm=cover,
                         scope="GEOMETRY_SCREEN_ONLY_NO_CODE_OR_NATIVE_PASS"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("SOURCE", digest, "HOOP_NODES", n_nodes, "HOOP_EDGES", n_edges)
    print("BAR_RING_SAMPLES", sum(x["bar_hoop_plane_samples"] for x in rows))
    print("UNMOVED_NEGATIVE", sum(x["initial_min_clear_mm"] < 0 for x in rows))
    print("MAX_STRAIGHT_SHIFT_5mm", max(x["straight_shift_for_5mm_mm"] for x in rows))
    print("MIN_CONSERVATIVE_INTERLAYER", min(x["conservative_min_interlayer_clear_5mm_mm"] for x in rows))
    print("STATUS: GEOMETRY SCREEN ONLY, NOT NATIVE OR CONSTRUCTION PASS")


if __name__ == "__main__":
    main()
