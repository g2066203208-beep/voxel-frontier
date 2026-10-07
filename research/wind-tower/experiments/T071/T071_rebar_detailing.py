#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproducible construction-detailing checks for the 31 concrete segments.

This is deliberately separate from the strength check.  Geometry/detailing can
be checked now; NB/T 10907 shear/torsion demand still waits for valid distributed
158 m OpenFAST tower-gage histories.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
GEOM = ROOT / "T071_input_geometry_31_segments.csv"
OUT = ROOT / "T071_rebar_detailing_31_segments.csv"

PHI_LONG_MM = 25.0
ABAR_MM2 = math.pi * PHI_LONG_MM**2 / 4.0
PHI_HOOP_MM = 14.0
S_HOOP_MM = 80.0
PHI_TIE_MM = 6.0
S_TIE_Z_MM = 480.0
S_TIE_CIRC_MM = 500.0
COVER_CANDIDATE_MM = 30.0
FYV_MPA = 360.0  # HRB400 design value from NB/T 10907-2021 Table 4.1.2


def pct(value: float) -> float:
    return 100.0 * value


def main() -> None:
    with GEOM.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))

    result = []
    for row in rows:
        seg = row["segment"]
        # The source CSV stores the segment top and center only.  The 31-section
        # geometry is regular; use the adjacent bottom/top convention from T061.
        index = int(row["seg"])
        height_m = 3.64
        t_mm = float(row["wall_mm"])
        d_center_mm = float(row["D_m"]) * 1000.0
        ft_mpa = 2.14 if index <= 2 else 2.09  # NB/T 10907 Table 4.1.2
        rho_min_pct = max(0.20, 45.0 * ft_mpa / FYV_MPA)
        hoop_area_mm2 = math.pi * PHI_HOOP_MM**2 / 4.0
        rho_hoop_each_pct = pct(hoop_area_mm2 / (S_HOOP_MM * t_mm))
        rho_hoop_total_pct = 2.0 * rho_hoop_each_pct
        n_hoop_levels = math.ceil(height_m * 1000.0 / S_HOOP_MM) + 1
        circumference_mm = math.pi * d_center_mm
        n_ties_per_level = math.ceil(circumference_mm / S_TIE_CIRC_MM)
        n_tie_levels = math.ceil(height_m * 1000.0 / S_TIE_Z_MM)
        tie_area_mm2 = math.pi * PHI_TIE_MM**2 / 4.0
        longitudinal_area_each_row = float(row["bars_each_row"]) * ABAR_MM2
        outer_d_mm = float(row["outer_diameter_m"]) * 1000.0
        wall_area_mm2 = math.pi / 4.0 * (outer_d_mm**2 - (outer_d_mm - 2.0 * t_mm) ** 2)
        # The 31-segment longitudinal result is a reconstruction check.  It is
        # not a direct phi25 claim in He (2024).
        rho_long_each_row_pct = pct(longitudinal_area_each_row / wall_area_mm2)
        result.append(
            {
                "segment": seg,
                "index": index,
                "height_m": height_m,
                "wall_mm_He_table": t_mm,
                "D_center_mm_model": d_center_mm,
                "concrete": "C70" if index <= 2 else "C65",
                "ft_MPa_NBT10907": ft_mpa,
                "fyv_MPa_NBT10907": FYV_MPA,
                "rho_hoop_min_pct_max_0p20_45ft_fyv": round(rho_min_pct, 6),
                "hoop_diameter_mm_candidate": PHI_HOOP_MM,
                "hoop_spacing_mm_candidate": S_HOOP_MM,
                "hoop_layers": 2,
                "hoop_area_each_layer_mm2_per_m": round(1000.0 * hoop_area_mm2 / S_HOOP_MM, 6),
                "hoop_rho_each_layer_pct": round(rho_hoop_each_pct, 6),
                "hoop_rho_two_layers_pct": round(rho_hoop_total_pct, 6),
                "hoop_diameter_check": "PASS" if PHI_HOOP_MM >= 8 else "FAIL",
                "hoop_spacing_check": "PASS" if S_HOOP_MM <= min(200.0, t_mm) else "FAIL",
                "hoop_min_ratio_check_each_layer": "PASS" if rho_hoop_each_pct >= rho_min_pct else "FAIL",
                "hoop_levels_per_segment": n_hoop_levels,
                "tie_diameter_mm_candidate": PHI_TIE_MM,
                "tie_area_mm2": round(tie_area_mm2, 6),
                "tie_vertical_spacing_mm": S_TIE_Z_MM,
                "tie_circum_spacing_mm": S_TIE_CIRC_MM,
                "tie_grid_check": "PASS: <=500 mm construction candidate",
                "tie_levels_per_segment": n_tie_levels,
                "ties_per_level": n_ties_per_level,
                "cover_mm_candidate": COVER_CANDIDATE_MM,
                "longitudinal_bars_each_row_He_table": row["bars_each_row"],
                "longitudinal_Abar_mm2_reconstruction": round(ABAR_MM2, 6),
                "longitudinal_rho_each_row_pct_reconstruction": round(rho_long_each_row_pct, 6),
                "strength_N_M_V_T_status": "HOLD: correct distributed 158 m tower-gage histories required",
                "overall_detailing_status": "CONDITIONAL PASS: geometry/detailing candidate only; not final design",
            }
        )

    with OUT.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=result[0].keys())
        writer.writeheader()
        writer.writerows(result)
    print(f"wrote {OUT} ({len(result)} segments)")


if __name__ == "__main__":
    main()
