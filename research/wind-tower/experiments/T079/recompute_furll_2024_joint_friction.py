#!/usr/bin/env python3
"""Read published dry-joint test data, reproduce descriptive mu statistics.

SOURCE: Fürll et al. (2024), Structural Concrete 25(5), pp.3347–3360,
DOI 10.1002/suco.202300873, open-access HTML Section 4.3, Table 4.
This program is a literature DATA RECOMPUTATION, NOT a tower PT/contact
calibration, code compliance test, or Abaqus solver run.
"""
import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

DATA_NAME = "FURLL_2024_DRY_JOINT_T4_FRICTION_10TESTS.csv"
SOURCE_URL = "https://onlinelibrary.wiley.com/doi/10.1002/suco.202300873"
T057_REFERENCE_MU = 0.5   # historical frozen INP parameter, not changed
REFERENCE_RM_M = 0.255    # reconstructed approximate mean radius, not test metrology

def hash_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for buf in iter(lambda: f.read(1024 * 1024), b""):
            h.update(buf)
    return h.hexdigest()

def summarize(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 10:
        raise ValueError("expected exactly 10 published tests")
    mu = []
    recomputed_mu = []
    for i, row in enumerate(rows, 1):
        if int(row["test_id"]) != i or row["source_doi"] != "10.1002/suco.202300873":
            raise ValueError("test ordering/DOI mismatch")
        if row["source_locator"] != "Section_4.3_Table_4":
            raise ValueError("source locator mismatch")
        n = float(row["normal_force_N_kN"])
        moment = float(row["torsion_capacity_MT_kNm"])
        stated = float(row["reported_mu"])
        if not all(math.isfinite(x) for x in (n, moment, stated)) or min(n, moment, stated) <= 0:
            raise ValueError("invalid data")
        computed = moment / (n * REFERENCE_RM_M)
        if abs(computed - stated) > 0.001:
            raise ValueError("Eq(4) inconsistency: row %d"%i)
        mu.append(stated)
        recomputed_mu.append(computed)
    out = {
        "doi": "10.1002/suco.202300873",
        "source_url": SOURCE_URL,
        "locator": "Section 4.3, Equation (4), Table 4; Section 5 limitation",
        "input_file": path.name,
        "input_sha256": hash_file(path),
        "n_tests": len(mu),
        "reported_mu_mean": statistics.mean(mu),
        "reported_mu_sample_sd": statistics.stdev(mu),
        "reported_mu_min": min(mu),
        "reported_mu_max": max(mu),
        "mu_from_eq4_approx_mean": statistics.mean(recomputed_mu),
        "approx_reference_mean_radius_m": REFERENCE_RM_M,
        "frozen_T057_mu": T057_REFERENCE_MU,
        "ratio_mean_to_T057_mu": statistics.mean(mu)/T057_REFERENCE_MU,
        "status": "PUBLISHED_LAB_DATA_RECOMPUTED_NOT_NATIVE_OR_CODE_PASS",
        "assumptions": [
            "0.255m radius reconstructed from rounded test geometry/equation; not verified test radius measurement",
            "mu=0.5 in frozen T057 is NOT changed",
            "only prestress+bending+torsion evaluated; shear V not jointly tested in cited experiment",
            "mu is surface/roughness/pressure/history dependent; no model-specific calibration",
            "ratio 1.3106 is friction-coefficient ratio at fixed N, not tower shear or torque capacity ratio"
        ],
        "error_budget": "Test rounded reported mu values; physical transfer and 30 joints contact calibration NEED_ESTIMATE",
        "seismic_physical_RUN": 0
    }
    if abs(out["reported_mu_mean"]-0.6553)>1e-10:
        raise AssertionError("mean mismatch")
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=Path(__file__).with_name(DATA_NAME))
    parser.add_argument("--out-json", type=Path, default=None)
    args = parser.parse_args()
    result = summarize(args.csv)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out_json:
        if args.out_json.exists(): raise SystemExit("REFUSE: output exists")
        args.out_json.write_text(payload, encoding="utf-8")
    print(payload, end="")

if __name__=="__main__":
    main()
