#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T080.24: read-only partial replay of T077 BF8 controller states using T075 compact rows.
STATIC arithmetic corroboration only. NOT four-case history, N-M capacity, Abaqus, or code compliance.
Usage:
 python t08024_partial_controller_replay.py BF8.csv T075_control_rows.csv T071_geometry.csv T078_meta.json
"""
import csv
import json
import math
import sys

def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def run(paths):
    bf, controls, geom, meta_path = paths
    b, c, g = read_csv(bf), read_csv(controls), read_csv(geom)
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    geom = {r["segment"]: r for r in g}
    pt = meta["adopted_BF8"]
    p0_kN = float(pt["P0_MN"]) * 1000.0
    if len(b) != 31 or len(geom) != 31 or len(c) != 310:
        raise ValueError("unexpected BF8/geometry/controller row count")
    matched, missing = [], []
    for x in b:
        seg, case = x["segment"], x["control_case"]
        gg, gp, t = (float(x[k]) for k in ("control_gamma_G", "control_gamma_P", "control_time_s"))
        if x["BF"] != "8" or seg not in geom:
            raise ValueError("BF or segment identity mismatch")
        rows = [y for y in c if y["segment"] == seg and y["case"] == case
                and abs(float(y["time_s"]) - t) <= 1e-7
                and abs(float(y["gamma_G"]) - gg) <= 1e-9]
        if not rows:
            missing.append({"segment": seg, "control_time_s": t,
                            "reason": "T075 compact controller does not retain this instant"})
            continue
        # Duplicate controller metrics may point to the same physical state.
        keys = ("G_Fz_kN", "Q_Fz_kN", "G_Mx_kNm", "Q_Mx_kNm", "G_My_kNm", "Q_My_kNm")
        for y in rows[1:]:
            if any(abs(float(y[k]) - float(rows[0][k])) > 1e-7 for k in keys):
                raise ValueError("contradictory T075 rows at identical state: " + seg)
        y = rows[0]
        n = -gg * (float(y["G_Fz_kN"]) + float(y["Q_Fz_kN"])) + (gp - 1.0) * p0_kN
        mx = gg * float(y["G_Mx_kNm"]) + 1.4 * float(y["Q_Mx_kNm"])
        my = gg * float(y["G_My_kNm"]) + 1.4 * float(y["Q_My_kNm"])
        mraw = math.hypot(mx, my)
        ea_mm = max(20.0, float(geom[seg]["D_m"]) * 1000.0 / 30.0)
        md = mraw + n * ea_mm / 1000.0
        n75 = float(y["N_comp_kN"])
        n_difference = n - n75
        predicted_difference = (1.4 - gg) * float(y["Q_Fz_kN"]) + (gp - 1.0) * p0_kN
        vals = [n, md, n_difference, predicted_difference]
        if not all(map(math.isfinite, vals)):
            raise ValueError("non-finite value: " + seg)
        matched.append({"segment": seg, "time_s": t, "gamma_G": gg, "gamma_P": gp,
                        "delta_N_kN": n - float(x["N_design_kN"]),
                        "delta_M_kNm": md - float(x["M_design_kNm"]),
                        "delta_N_vs_T075_kN": n_difference,
                        "delta_N_identity_kN": n_difference - predicted_difference})
    maxn = max((abs(x["delta_N_kN"]) for x in matched), default=float("inf"))
    maxm = max((abs(x["delta_M_kNm"]) for x in matched), default=float("inf"))
    maxi = max((abs(x["delta_N_identity_kN"]) for x in matched), default=float("inf"))
    out = {"status": "PARTIAL_STATIC_CORROBORATION_ONLY", "matched": len(matched),
           "missing": missing, "max_abs_N_residual_kN": maxn,
           "max_abs_M_residual_kNm": maxm, "max_abs_N_identity_residual_kN": maxi,
           "not_verified": ["31st controller", "four complete raw histories", "full-time negative N",
                            "HRB335 capacity", "exact eta", "Abaqus native", "standards"]}
    if len(matched) != 30 or len(missing) != 1 or max(maxn, maxm, maxi) > 1e-6:
        raise AssertionError(json.dumps(out, ensure_ascii=False))
    return out

if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    print(json.dumps(run(sys.argv[1:]), ensure_ascii=False, indent=2))
