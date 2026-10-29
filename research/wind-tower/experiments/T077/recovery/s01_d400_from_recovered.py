#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S01 HRB400 fatigue-aware design branch: full four-case N-M *screen*, NOT a code/native PASS.

Reproduce using existing repository T077/T073/T071/T074 inputs and four recovered
S06 ZIPs. Does not modify the frozen T057/T070 INP or launch Abaqus.
Example:
python research/wind-tower/experiments/T077/recovery/s01_d400_from_recovered.py \
  --archives <U09S06.zip> <U11S04.zip> <U19S04.zip> <U19S06.zip> \
  --outdir <output-directory>

The first 2026-10-24 result was independently calculated from the archived
s01_pt_rebar_screen.py port (SHA256 8e692d4d83d59e903fbcfb2b41abb0176b6e8f9b2e4f86bf12ce7edb3180b10a).
THIS repo-native script is submitted for future exact-source rerun; do not claim it
was executed until its own RUN log is attached.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from s01_exact_eta_31seg_from_recovered import ETA, evaluate, load_archives, t077

DIAMS = (25, 28, 32, 36, 40, 50)
FY_D400 = 360.0
FYC_D400 = 360.0  # public GB/T50010/T071 source; authoritative clause still HOLD


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archives", nargs=4, required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)

    x, archives = load_archives(a.archives)
    geom = t077.read_geom()
    rings = t077.read_rings(geom)
    gravity = t077.load_gravity()
    previous = pd.read_csv(
        Path(__file__).with_name("S01_EXACT_ETA_31SEG_BRANCH_SCREEN_20261024.csv")
    ).set_index("segment")
    if len(geom) != 31 or len(previous) != 31:
        raise RuntimeError("31 segment geometry/reference required")

    allrows, summary, replay = [], [], []
    for seg in sorted(geom):
        g, ring = geom[seg], rings[seg]
        qcases = {
            case: q.sort_values("time_s").reset_index(drop=True)
            for case, q in x.loc[x.segment == seg].groupby("case")
        }
        grav = {
            col: float(gravity.loc[seg, col])
            for col in ("Fx_kN", "Fy_kN", "Fz_kN", "Mx_kNm", "My_kNm", "Mz_kNm")
        }

        # Exact implementation regression, not physical V&V.
        d500 = int(previous.loc[seg, "HRB500_d"])
        ref = float(previous.loc[seg, "HRB500_T077_u"])
        old = evaluate(seg, g, ring, qcases, grav, 435.0, 410.0, d500, ETA)
        err = abs(old["util"] - ref)
        replay.append({"segment": seg, "reference_D500_u": ref,
                       "rerun_D500_u": old["util"], "abs_diff": err})

        results = []
        for d in DIAMS:
            r = evaluate(seg, g, ring, qcases, grav, FY_D400, FYC_D400, d, ETA)
            if not math.isfinite(r["util"]):
                raise RuntimeError(f"nonfinite capacity: {seg}, phi{d}")
            allrows.append({"segment": seg, "branch": "D400_SCREEN_ONLY",
                            "diam_mm": d, "fy_MPa": FY_D400,
                            "fyc_MPa": FYC_D400, "eta": ETA, **r})
            results.append((d, r))

        eligible = [(d, r) for d, r in results if r["util"] <= 1.0]
        chosen = eligible[0] if eligible else None
        summary.append({
            "segment": seg,
            "min_d400_d_mm": chosen[0] if chosen else "NONE<=50",
            "min_d400_u": chosen[1]["util"] if chosen else None,
            "d400_u_phi50": results[-1][1]["util"],
            "d500_repo_d_mm": d500,
            "d500_repo_u": ref,
        })

    replay_df = pd.DataFrame(replay)
    max_err = float(replay_df.abs_diff.max())
    # Reproduction tolerance for displayed reference rounded to 9 decimals;
    # not a physics error tolerance.
    if max_err > 1e-6:
        raise RuntimeError(f"T077 D500 regression mismatch: {max_err}")

    files = {
        "full": a.outdir / "S01_D400_31SEG_SIX_DIAM_EXACT_ETA_SCREEN.csv",
        "summary": a.outdir / "S01_D400_31SEG_MIN_DIAM_SCREEN.csv",
        "regression": a.outdir / "S01_D500_REGRESSION.csv",
    }
    pd.DataFrame(allrows).to_csv(files["full"], index=False)
    pd.DataFrame(summary).to_csv(files["summary"], index=False)
    replay_df.to_csv(files["regression"], index=False)
    manifest = {
        "scientific_status": "SCREEN_ONLY_NOT_STANDARD_NOT_ABAQUS",
        "model_family": "T057/T070 reference only; no new INP created",
        "assumed_strength_MPa": {"D400_fy": FY_D400, "D400_fyc": FYC_D400},
        "eta_T078_design_not_native": ETA,
        "archives": archives,
        "regression_max_abs_u_error": max_err,
        "outputs": {k: {"name": v.name, "sha256": hashlib.sha256(v.read_bytes()).hexdigest()}
                    for k, v in files.items()},
        "limitations": [
            "No authorized 2024 GB/T50010 and NB/T10907 material/clause reconciliation",
            "No D400 cage clearance/anchorage/hoop compatibility or actual native INP",
            "No T070 gravity/PT/contact G0/G1 native verification",
            "No independent material fatigue or seismic result",
        ],
    }
    (a.outdir / "S01_D400_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"records": len(allrows), "segments": len(summary),
                      "regression_max_abs_u_error": max_err,
                      "D400_min_d_counts": pd.DataFrame(summary)["min_d400_d_mm"]
                          .value_counts().to_dict()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
