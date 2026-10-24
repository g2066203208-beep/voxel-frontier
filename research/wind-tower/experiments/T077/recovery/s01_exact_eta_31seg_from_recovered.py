#!/usr/bin/env python3
"""S01 read-only sectional screening. Not native Abaqus, normative or design PASS.
Run from cloned repository, with 4 recovered S06 ZIPs:
python research/wind-tower/experiments/T077/recovery/s01_exact_eta_31seg_from_recovered.py --archives <four ZIP paths> --outdir <dir>
"""
from __future__ import annotations
import argparse, gzip, hashlib, io, json, math, sys, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

T077_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(T077_DIR))
import t077_formal_rebar as t077
e01 = t077.e01
ETA = 0.7702745023137976  # T078 design Pe, not native P_eq
NEEDED = {"case", "segment", "time_s", "Fx_kN", "Fy_kN", "Fz_kN", "Mx_kNm", "My_kNm", "Mz_kNm"}


def load_archives(paths):
    frames, sha = [], []
    for path in paths:
        p = Path(path)
        sha.append({"name": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
        with zipfile.ZipFile(p) as z:
            gzfiles = [n for n in z.namelist() if n.endswith("_31seg.csv.gz")]
            if len(gzfiles) != 4:
                raise RuntimeError(f"expected 4 batches per ZIP: {p}")
            for n in gzfiles:
                with gzip.open(io.BytesIO(z.read(n)), "rt") as f:
                    q = pd.read_csv(f)
                if q.columns.duplicated().any() or not NEEDED.issubset(q.columns):
                    raise RuntimeError(f"duplicate/missing header: {p}:{n}")
                frames.append(q[list(sorted(NEEDED))].copy())
    x = pd.concat(frames, ignore_index=True)
    if len(x) != 4 * 31 * 12001 or x.case.nunique() != 4 or x.segment.nunique() != 31:
        raise RuntimeError("case/segment/row count mismatch")
    if x[["case", "segment", "time_s"]].duplicated().any():
        raise RuntimeError("duplicate case/segment/time key")
    for (case, seg), q in x.groupby(["case", "segment"], sort=False):
        t = np.sort(q.time_s.to_numpy(float))
        if len(t) != 12001 or abs(t[0] - 100) > 1e-8 or abs(t[-1] - 700) > 1e-8 or not np.allclose(np.diff(t), 0.05, rtol=0, atol=1e-7):
            raise RuntimeError(f"bad time grid: {case}/{seg}")
    return x, sha


def evaluate(seg, geom, ring, qcases, gravity, fy, fyc, diameter, eta):
    e01.FY, e01.FYC = fy, fyc
    Nc, Mc, NsA, MsA, Np1, Mp1 = t077.capacity_components(seg, geom, ring, eta)
    A = math.pi * diameter**2 / 4
    Nb, Mb = t077.upper_capacity(Nc + A * NsA + 8 * Np1, Mc + A * MsA + 8 * Mp1)
    ea = max(t077.EA_MIN_MM, float(geom["D_m"]) * 1000 / 30)
    recs = []
    for case, q in qcases.items():
        r = t077.evaluate_one(seg, q, gravity, ea, Nb, Mb, 8, eta)
        recs.append({**r, "case": case})
    return max(recs, key=lambda r: r["util"])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--archives", nargs=4, required=True, help="four S06_RESTORED_*.zip archives")
    p.add_argument("--outdir", type=Path, required=True)
    a = p.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)
    x, sha = load_archives(a.archives)
    geom = t077.read_geom()
    rings = t077.read_rings(geom)
    gravity = t077.load_gravity()
    hist = pd.read_csv(T077_DIR / "T077_FORMAL_31SEG_REBAR_BF8.csv").set_index("segment")
    mainrows, scanrows, replay = [], [], []
    for seg in sorted(geom):
        g, ring = geom[seg], rings[seg]
        qcases = {case: q.sort_values("time_s").reset_index(drop=True)
                  for case, q in x[x.segment == seg].groupby("case")}
        gv = {c: float(gravity.loc[seg, c]) for c in ("Fx_kN", "Fy_kN", "Fz_kN", "Mx_kNm", "My_kNm", "Mz_kNm")}
        d500 = int(hist.loc[seg, "bar_d_mm"])
        old = evaluate(seg, g, ring, qcases, gv, 435, 410, d500, 1.0)
        replay.append({"segment": seg, "replayed_u": old["util"], "historical_u": float(hist.loc[seg, "max_utilization"]),
                       "abs_error": abs(old["util"] - float(hist.loc[seg, "max_utilization"]))})
        for tag, fy, fyc, d in (("HRB335_NOMINAL335_PHI25_NOT_CODE", 335, 335, 25),
                                ("HRB500_T077_DESIGN_ASSUMPTION", 435, 410, d500)):
            r = evaluate(seg, g, ring, qcases, gv, fy, fyc, d, ETA)
            mainrows.append({"segment": seg, "branch": tag, "diam_mm": d, "eta": ETA, **r})
        for tag, fy in (("HRB335_NOMINAL335_UPPER", 335), ("HRB335_300_SENSITIVITY_NOT_CODE", 300)):
            for d in (25, 28, 32, 36, 40, 50):
                r = evaluate(seg, g, ring, qcases, gv, fy, fy, d, ETA)
                cov, spacing = t077.constructability(g, ring, d)
                scanrows.append({"segment": seg, "branch": tag, "diam_mm": d, "eta": ETA,
                                 "geometric_cover_mm": cov, "geometric_clear_spacing_mm": spacing, **r})
    replay_df = pd.DataFrame(replay)
    if replay_df.abs_error.max() > 1e-8:
        raise RuntimeError(f"historical replay failed: {replay_df.abs_error.max()}")
    pd.DataFrame(mainrows).to_csv(a.outdir / "S01_EXACT_ETA_31SEG_BRANCH_SCREEN.csv", index=False)
    pd.DataFrame(scanrows).to_csv(a.outdir / "S01_HRB335_DIAMETER_SENSITIVITY.csv", index=False)
    replay_df.to_csv(a.outdir / "S01_HISTORICAL_ETA1_REPLAY.csv", index=False)
    manifest = {"status": "SCREEN-ONLY-NOT-CODE-NOT-ABAQUS", "eta": ETA, "archives": sha,
                "historical_replay_max_abs_util_error": float(replay_df.abs_error.max()),
                "mesh": {"NR": e01.NR, "NTH": e01.NTH, "NZ": e01.NZ},
                "T077_branch": "HRB500 435/410, original T077 diameters",
                "HRB335_branch": "nominal 335/335 is optimistic strength sensitivity, not verified code design"}
    (a.outdir / "S01_SCREEN_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"rows_main": len(mainrows), "rows_sensitivity": len(scanrows), **manifest}, indent=2))


if __name__ == "__main__":
    main()
