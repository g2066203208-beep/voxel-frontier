#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S01 paired N-M screening at *fixed historical D500 control states*.

For each of 31 concrete segments, compare the D400 sectional interaction
capacity before/after the radial straight-T3D2 geometry sensitivity relocation.
The N/M load point is the historical D500 fyc=410 MPa controlling synchronous
N/M state from the full-precision 93-row archive, NOT necessarily the D400
controlling state. The unchanged D500 curve is independently replayed as a
regression check. This is NOT a full four-case D400 re-envelope, Abaqus run,
construction/detailing approval, or standard-compliance check.

Run after s01_d400_d500_straight_t3d2_exact.py:
python s01_d400_relayout_fixed_control_nm.py \
 --geometry <geometry-62-row.csv> --outdir <new-output-dir>
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
T077 = HERE.parent
sys.path.insert(0, str(T077))
import t077_formal_rebar as t077

ETA = 0.7702745023137976
D500_93_SHA256 = "db44bd44afab3aadd2ea3ee2f216a55e6b54e0c0a1338c39ba5c0ed364b3dfbf"
BRANCH_31_SHA256 = "e0a1f7d230a97f2e9575aba3178d42903cfcfa5d537a62f32d001c5544ebf855"
GEOMETRY_62_SHA256 = "85a462b18833993853e85b80b755c3097a2698cbc39c18fae5d4b4d226e5dcaf"
T057_SHA256 = "c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def capacity_at(seg, g, ring, diameter, fy, fyc, N_kN):
    """Exact T073/T077 discretization, one fixed axial demand; M in kNm."""
    e01 = t077.e01
    e01.FY, e01.FYC = float(fy), float(fyc)
    Nc, Mc, NsA, MsA, Np1, Mp1 = t077.capacity_components(seg, g, ring, ETA)
    A = math.pi * diameter ** 2 / 4.0
    Nb, Mb = t077.upper_capacity(
        Nc + A * NsA + 8 * Np1, Mc + A * MsA + 8 * Mp1
    )
    N = N_kN * 1000.0
    if not (Nb.min() <= N <= Nb.max()):
        raise ValueError(f"{seg}: fixed N={N_kN}kN outside N-M envelope")
    M = float(np.interp(N, Nb, Mb) / 1e6)
    if not math.isfinite(M) or M <= 0:
        raise ValueError(f"{seg}: invalid M capacity {M}")
    return M


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--geometry", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--d500-history", type=Path, default=HERE /
        "S01_D500_FYC_400_410_435_FIXED_DIAM_93_FULL_PRECISION_20261025.csv")
    ap.add_argument("--branch-csv", type=Path, default=HERE /
        "S01_D400_D500_UNMOVED_CAGE_CLEARANCE_31SEG_20261025.csv")
    a = ap.parse_args()

    for p, expected in (
        (a.geometry, GEOMETRY_62_SHA256),
        (a.d500_history, D500_93_SHA256),
        (a.branch_csv, BRANCH_31_SHA256),
    ):
        actual = digest(p)
        if actual != expected:
            raise ValueError(f"SHA256 mismatch: {p} actual={actual} expected={expected}")
    all93 = rows(a.d500_history)
    if len(all93) != 93:
        raise ValueError("expected 93 full precision historical D500 rows")
    fixed = {}
    for r in all93:
        if float(r["fyc_MPa"]) == 410.0:
            fixed[r["segment"]] = r
    if len(fixed) != 31:
        raise ValueError("expected 31 historical D500 fyc=410 fixed control states")
    branch = {r["segment"]: r for r in rows(a.branch_csv)}
    geometry = {r["segment"]: r for r in rows(a.geometry) if r["branch"] == "D400"}
    if len(branch) != 31 or len(geometry) != 31:
        raise ValueError("expected 31 unique D400 geometry and branch records")

    geom = t077.read_geom()
    rings = t077.read_rings(geom)
    if len(geom) != 31 or len(rings) != 31:
        raise ValueError("missing 31 T071/T073 original section geometry records")
    out = []
    max_replay = 0.0
    for seg in sorted(geom):
        r = fixed[seg]
        b = branch[seg]
        h = geometry[seg]
        d400, d500 = int(b["d400_screen_d_mm"]), int(b["d500_historical_d_mm"])
        if d400 != int(h["diameter_mm"]) or d500 != int(r["diam_mm"]):
            raise ValueError(f"{seg}: diameter source identity mismatch")
        if abs(float(r["eta"]) - ETA) > 1e-13:
            raise ValueError(f"{seg}: PT eta mismatch")
        N, M = float(r["N_kN"]), float(r["M_kNm"])
        old_ring = rings[seg]
        shift_mm = float(h["straight_endpoint_shift_for_5mm_mm"])
        delta = shift_mm  # t077/e01 ring radii are in mm
        new_ring = (old_ring[0] + delta, old_ring[1] - delta, old_ring[2])
        if new_ring[0] >= new_ring[1]:
            raise ValueError(f"{seg}: radial layers crossed")
        replay_mcap = capacity_at(seg, geom[seg], old_ring, d500, 435.0, 410.0, N)
        replay_u = M / replay_mcap
        replay_err = abs(replay_u - float(r["util"]))
        max_replay = max(max_replay, replay_err)
        if replay_err > 1e-7:
            raise ValueError(f"{seg}: T077 historical D500 regression failed: {replay_err}")

        m0 = capacity_at(seg, geom[seg], old_ring, d400, 360.0, 360.0, N)
        m1 = capacity_at(seg, geom[seg], new_ring, d400, 360.0, 360.0, N)
        u0, u1 = M / m0, M / m1
        original_full_envelope = float(b["d400_conditional_u"])
        if u0 > original_full_envelope + 1e-6:
            raise ValueError(
                f"{seg}: fixed D500 control is not bounded by historical D400 full envelope "
                f"({u0} > {original_full_envelope})"
            )
        out.append({
            "segment": seg,
            "fixed_state_source": "D500_FYC410_HISTORICAL_CONTROL",
            "case": r["case"],
            "time_s": r["time_s"],
            "gamma_G": r["gamma_G"],
            "gamma_P": r["gamma_P"],
            "N_design_kN": r["N_kN"],
            "M_design_kNm": r["M_kNm"],
            "d400_mm": d400,
            "shift_for_5mm_geometry_target_mm": f"{shift_mm:.9f}",
            "d400_Mcap_before_kNm": f"{m0:.9f}",
            "d400_Mcap_after_kNm": f"{m1:.9f}",
            "d400_u_before_at_fixed_D500_state": f"{u0:.12f}",
            "d400_u_after_at_fixed_D500_state": f"{u1:.12f}",
            "d400_u_change_fixed_state": f"{u1-u0:.12f}",
            "historical_D400_full_envelope_u_BEFORE_relayout": b["d400_conditional_u"],
            "d500_historical_u_regression_abs_error": f"{replay_err:.3g}",
            "status": "FIXED_STATE_SCREEN_ONLY_NOT_D400_REENVELOPE_NOT_CODE_OR_NATIVE_PASS",
        })
    a.outdir.mkdir(parents=True, exist_ok=True)
    outcsv = a.outdir / "S01_D400_31SEG_RELAYOUT_FIXED_D500_CONTROL_NM.csv"
    manifest = a.outdir / "S01_D400_31SEG_RELAYOUT_FIXED_D500_CONTROL_MANIFEST.json"
    if outcsv.exists() or manifest.exists():
        raise FileExistsError("refusing to overwrite output")
    with outcsv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    top = sorted(out, key=lambda x: float(x["d400_u_after_at_fixed_D500_state"]), reverse=True)
    meta = {
        "status": "DETERMINISTIC_FIXED_STATE_SCREEN_NOT_NORMATIVE_OR_NATIVE_PASS",
        "rows": len(out),
        "input_sha256": {
            "T057_frozen_parent_verified_in_upstream_geometry_step": T057_SHA256,
            "geometry_62": digest(a.geometry),
            "D500_93": digest(a.d500_history),
            "D400_D500_branch_31": digest(a.branch_csv),
            "T071_geom": digest(t077.GEOM),
            "T073_radii": digest(t077.RADII),
            "T073_section_algorithm": digest(Path(t077.e01.__file__)),
            "T077_formal_algorithm": digest(Path(t077.__file__)),
            "this_script": digest(Path(__file__)),
        },
        "result_csv_sha256": digest(outcsv),
        "D500_historical_replay_max_abs_util_error": max_replay,
        "fixed_state_count": len(out),
        "D400_fixed_state_after_relayout_u_gt_1_count": sum(
            float(x["d400_u_after_at_fixed_D500_state"]) > 1 for x in out),
        "max_fixed_state_u_after_relayout": float(top[0]["d400_u_after_at_fixed_D500_state"]),
        "max_fixed_state_segment": top[0]["segment"],
        "CSEG_02": next(x for x in out if x["segment"] == "CSEG_02"),
        "limitations": [
            "Historical fixed load points are D500 controls, not necessarily D400 controls",
            "Recomputed ring radii are T073 two-ring mean proxies of actual T057 four-radii bars",
            "No four-case D400 post-relayout envelope; cannot infer D400 ULS pass from u<1",
            "5 mm is non-normative geometry sensitivity, not code clearance",
            "No new INP, Abaqus, PT equilibrium, fatigue, seismic, or standard compliance",
        ],
        "physical_error_budget": "HOLD_NEEDS_NATIVE_AND_MODEL_CONVERGENCE",
        "new_INP": False,
        "native_Abaqus": "NOT_RUN",
    }
    manifest.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "rows": len(out),
        "max_fixed_state_u_after_relayout": meta["max_fixed_state_u_after_relayout"],
        "max_fixed_state_segment": meta["max_fixed_state_segment"],
        "D400_fixed_state_u_gt_1_count": meta["D400_fixed_state_after_relayout_u_gt_1_count"],
        "CSEG_02_u_before": meta["CSEG_02"]["d400_u_before_at_fixed_D500_state"],
        "CSEG_02_u_after": meta["CSEG_02"]["d400_u_after_at_fixed_D500_state"],
        "max_D500_replay_error": max_replay,
        "result_csv_sha256": meta["result_csv_sha256"],
        "status": meta["status"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
