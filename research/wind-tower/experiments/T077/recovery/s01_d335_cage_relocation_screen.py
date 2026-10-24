#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S01 D335 cage relocation: geometry and full-history conditional N-M re-screen.
Requires four S06_RESTORED_*.zip files. No native Abaqus, no code PASS.
Run:
python research/wind-tower/experiments/T077/recovery/s01_d335_cage_relocation_screen.py \
 --archives /path/to/S06_RESTORED_*_31SEG_20261024.zip \
 --out /path/to/S01_D335_CAGE_RELOCATED.csv
"""
from __future__ import annotations
import argparse
import csv
import math
from pathlib import Path
import numpy as np
import pandas as pd
from s01_exact_eta_31seg_from_recovered import ETA, e01, load_archives, t077

HOOP_D_MM = 14.0
HOOP_CENTER_SURFACE_OFFSET_MM = 37.0
MARGIN_MM = 5.0  # hypothetical clearance for a *numerical* layout, not a construction tolerance
PT_BF = 8
FY_ASSUMPTION_MPA = 300.0  # NOT VERIFIED against authorized standard text


def relocate(g, ring, d, margin_mm=MARGIN_MM):
    rin, rout, n = ring  # mm, mm, He locked bars per layer
    outer_surface = float(g["D_m"]) * 500.0
    inner_surface = float(g["di_m"]) * 500.0
    old_i = rin - inner_surface
    old_o = outer_surface - rout
    required = HOOP_CENTER_SURFACE_OFFSET_MM + (HOOP_D_MM + d) / 2 + margin_mm
    new_i, new_o = max(old_i, required), max(old_o, required)
    r_in = inner_surface + new_i
    r_out = outer_surface - new_o
    gap = min(new_i, new_o) - HOOP_CENTER_SURFACE_OFFSET_MM - (HOOP_D_MM + d) / 2
    cover = min(new_i, new_o) - d / 2
    interlayer = (outer_surface - inner_surface) - new_i - new_o - d
    circum = 2 * min(r_in, r_out) * math.sin(math.pi / n) - d
    if min(gap, cover, interlayer, circum) < -1e-8:
        raise ValueError(f"negative clearance: d={d}, ring={ring}, gap={gap}, interlayer={interlayer}")
    return (r_in, r_out, n), dict(
        old_inner_offset_mm=old_i, old_outer_offset_mm=old_o,
        new_inner_offset_mm=new_i, new_outer_offset_mm=new_o,
        shift_inner_mm=new_i-old_i, shift_outer_mm=new_o-old_o,
        hoop_long_clear_mm=gap, longitudinal_cover_mm=cover,
        interlayer_clear_mm=interlayer, circumferential_clear_mm=circum,
    )


def worst(seg, g, ring, d, qcases, gravity):
    e01.FY = FY_ASSUMPTION_MPA
    e01.FYC = FY_ASSUMPTION_MPA
    Nc, Mc, NsA, MsA, Np1, Mp1 = t077.capacity_components(seg, g, ring, ETA)
    A = math.pi * d**2 / 4
    Nb, Mb = t077.upper_capacity(Nc + A * NsA + PT_BF * Np1,
                                 Mc + A * MsA + PT_BF * Mp1)
    ea = max(t077.EA_MIN_MM, float(g["D_m"]) * 1000 / 30)
    recs = []
    for case, q in qcases.items():
        recs.append({"case": case, **t077.evaluate_one(
            seg, q, gravity, ea, Nb, Mb, PT_BF, ETA)})
    return max(recs, key=lambda rec: rec["util"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archives", nargs=4, type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    x, sha = load_archives(args.archives)
    geom = t077.read_geom()
    rings = t077.read_rings(geom)
    gravity = t077.load_gravity()
    dpath = Path(__file__).parent / "S01_EXACT_ETA_31SEG_BRANCH_SCREEN_20261024.csv"
    with dpath.open(encoding="utf-8-sig", newline="") as f:
        dmap = {r["segment"]: int(r["HRB335_assumed300_min_d"]) for r in csv.DictReader(f)}
    if set(dmap) != set(geom) or len(geom) != 31:
        raise ValueError("31-segment diameter/geometry identity mismatch")
    rows = []
    for seg in sorted(geom):
        g, ring, d = geom[seg], rings[seg], dmap[seg]
        new_ring, clearance = relocate(g, ring, d)
        cases = {case: q.sort_values("time_s").reset_index(drop=True)
                 for case, q in x[x.segment == seg].groupby("case")}
        gv = {col: float(gravity.loc[seg, col]) for col in (
            "Fx_kN", "Fy_kN", "Fz_kN", "Mx_kNm", "My_kNm", "Mz_kNm")}
        old = worst(seg, g, ring, d, cases, gv)
        new = worst(seg, g, new_ring, d, cases, gv)
        rows.append(dict(
            segment=seg, n_each_ring=ring[2], diameter_mm=d,
            eta_design=ETA, fy_MPa_unverified=FY_ASSUMPTION_MPA,
            wall_mm=(float(g["D_m"])-float(g["di_m"]))*500,
            **clearance, u_old=old["util"], u_relocated=new["util"],
            delta_u=new["util"]-old["util"],
            case_new=new["case"], time_new_s=new["time_s"],
            gammaG_new=new["gamma_G"], gammaP_new=new["gamma_P"]))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.out, index=False, float_format="%.10g")
    print("rows", len(rows), "max_relocated_u", max(r["u_relocated"] for r in rows),
          "max_abs_delta_u", max(abs(r["delta_u"]) for r in rows))
    print("SOURCE-ZIP-SHA256", sha)
    print("STATUS: CONDITIONAL SCREEN ONLY; no code/native/constructability PASS")


if __name__ == "__main__":
    main()
