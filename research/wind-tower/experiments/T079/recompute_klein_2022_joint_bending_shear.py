#!/usr/bin/env python3
"""Recompute public experimental Table 2 and Eq.(10)/(13)/(14) of Klein et al.
2022, Structural Concrete 23(3), 1370-1384, DOI 10.1002/suco.202100710.

SOURCE: Wiley open-access original HTML, Section 4.4 Table 2, Section 4.3
Eqs 13-14 and Section 3.2 Eq 10. This is NOT a cyclic fatigue test,
not a seismic simulation, and not an Abaqus/contact model validation.
Python 3.8+ stdlib only. Strict input validation; no silent file overwrite.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

CSV_NAME = "KLEIN_2022_JOINT_BENDING_SHEAR_V1_V10_TABLE2.csv"
DOI = "10.1002/suco.202100710"
SOURCE_URL = "https://onlinelibrary.wiley.com/doi/10.1002/suco.202100710"

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def analyze(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 10:
        raise ValueError("Expected ten V1..V10 experimental steps")
    points = []
    for i, row in enumerate(rows, 1):
        if (row["step"] != "V%d" % i or row["source_doi"] != DOI
                or row["source_locator"] != "Table_2"):
            raise ValueError("Source identity or ordering mismatch at V%d" % i)
        v = float(row["head_shear_kN"])
        u = float(row["head_displacement_mm"])
        if not (math.isfinite(v) and math.isfinite(u) and v > 0 and u > 0):
            raise ValueError("Invalid Table 2 numeric value")
        if points and (v <= points[-1]["F_kN"] or u <= points[-1]["u_mm"]):
            raise ValueError("Unexpected non-increasing experiment sequence")
        points.append({"step": row["step"], "F_kN": v, "u_mm": u,
                       "secant_kN_per_mm": v / u})
    # Eq.(10), printed values in Eq.(13)/(14): units kN, m, kNm.
    p_plus_g_kN = 325.8
    r_m = 0.461
    d_outer_m = 0.963
    x_lever_m = 0.5 + 15 * 0.409 - 0.05
    m_dec_recalc = p_plus_g_kN * r_m ** 2 / d_outer_m
    f_dec_recalc = m_dec_recalc / x_lever_m
    m_dec_paper = 72.015
    f_dec_paper = 10.927
    crossing = next(p for p in points if p["F_kN"] > f_dec_paper)
    k1 = points[0]["secant_kN_per_mm"]
    k10 = points[-1]["secant_kN_per_mm"]
    assert crossing["step"] == "V4"
    assert abs(k1 - 1.8856015779092702) < 1e-10
    assert abs(k10 - 1.485724948684456) < 0.001
    return {
        "source_doi": DOI,
        "source_url": SOURCE_URL,
        "reading_level": "publisher_open_access_fulltext_HTML_selected_sections_and_original_Table_2",
        "csv_name": path.name,
        "csv_sha256": sha256(path),
        "steps": points,
        "k1_kN_per_mm": k1,
        "k10_kN_per_mm": k10,
        "k10_over_k1": k10 / k1,
        "secant_stiffness_drop_percent": 100 * (1 - k10 / k1),
        "source_prestress_plus_weight_kN": p_plus_g_kN,
        "source_radius_m_rounded": r_m,
        "source_outer_diameter_m_rounded": d_outer_m,
        "source_lever_m_from_printed_dimensions": x_lever_m,
        "Mdec_kNm_recomputed_from_printed_dimensions": m_dec_recalc,
        "Mdec_kNm_printed_in_paper": m_dec_paper,
        "Mdec_relative_rounding_gap_percent": 100 * (m_dec_recalc / m_dec_paper - 1),
        "Fdec_kN_recomputed_from_printed_dimensions": f_dec_recalc,
        "Fdec_kN_printed_in_paper": f_dec_paper,
        "Fdec_relative_rounding_gap_percent": 100 * (f_dec_recalc / f_dec_paper - 1),
        "first_step_above_printed_ideal_Fdec": crossing["step"],
        "first_step_above_printed_ideal_Fdec_kN": crossing["F_kN"],
        "status": "ORIGINAL_LITERATURE_TABLE_STATIC_RECOMPUTATION_ONLY",
        "physical_pass": False,
        "earthquake_runs": 0,
        "assumptions_and_limitations": [
            "F/u is a global head secant stiffness proxy, not joint tangent stiffness",
            "Ten increasing load/unload levels are not high-cycle fatigue data",
            "Ideal thin-ring decompression is not an experimental observed onset",
            "Published Eq13/14 values differ slightly from displayed rounded inputs",
            "Test uses one central tendon unlike circumferential PT of full tower",
            "Measured circumferential contact is nonuniform due to geometric imperfection",
            "No scale transfer to T057/T070, no code compliance, no native Abaqus"
        ],
        "error_budget": "Table 2 printed to 0.001; Eq 13/14 geometry rounded; test/FE/full tower uncertainty NEED_ESTIMATE"
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=Path(__file__).with_name(CSV_NAME))
    parser.add_argument("--out-json", type=Path, default=None)
    args = parser.parse_args()
    report = analyze(args.csv)
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.out_json is not None:
        if args.out_json.exists():
            raise FileExistsError("Refusing to overwrite existing output")
        args.out_json.write_text(payload, encoding="utf-8")
    print(payload, end="")

if __name__ == "__main__":
    main()
