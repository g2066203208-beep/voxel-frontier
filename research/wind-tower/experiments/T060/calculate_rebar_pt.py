from __future__ import annotations

import csv
import math
from pathlib import Path

# He Zeyu 2024, PDF p.34, Table 3-2: top elevation, top OD, wall, bars per layer.
ROWS = [
    (3.64, 8.17, 280, 108), (7.28, 8.01, 280, 108),
    (10.92, 7.85, 280, 108), (14.56, 7.70, 282.5, 108),
    (18.20, 7.54, 287.5, 96), (21.84, 7.36, 295, 96),
    (25.48, 7.22, 302.5, 96), (29.12, 7.06, 307.5, 96),
    (32.76, 6.90, 312.5, 96), (36.40, 6.74, 320, 96),
    (40.04, 6.58, 327.5, 96), (43.68, 6.42, 332.5, 90),
    (47.32, 6.26, 337.5, 90), (50.96, 6.10, 345, 90),
    (54.60, 5.94, 352.5, 90), (58.24, 5.78, 357.5, 84),
    (61.88, 5.70, 360, 84), (65.52, 5.70, 360, 84),
    (69.16, 5.70, 360, 84), (72.78, 5.70, 340, 84),
    (76.44, 5.70, 320, 76), (80.08, 5.70, 320, 76),
    (83.72, 5.70, 320, 76), (87.36, 5.70, 320, 76),
    (91.00, 5.70, 290, 76), (94.64, 5.70, 260, 76),
    (98.28, 5.70, 260, 76), (101.92, 5.70, 260, 76),
    (105.56, 5.70, 354, 76), (109.20, 5.45, 414, 76),
    (112.00, 4.97, 500, 76),
]

BAR_AREA_MM2 = 0.000490873852123405 * 1_000_000
HOOP_AREA_MM2 = math.pi * 14**2 / 4
HOOP_SPACING_MM = 80


def calculate():
    output = []
    for index, (z_m, od_m, wall_mm, bars_layer) in enumerate(ROWS, 1):
        od_mm = od_m * 1000
        id_mm = od_mm - 2 * wall_mm
        concrete_area = math.pi / 4 * (od_mm**2 - id_mm**2)
        longitudinal_area = 2 * bars_layer * BAR_AREA_MM2
        one_hoop_ratio = 100 * HOOP_AREA_MM2 / (HOOP_SPACING_MM * wall_mm)
        output.append({
            "segment": index,
            "top_elevation_m": z_m,
            "top_outer_diameter_mm": od_mm,
            "wall_mm": wall_mm,
            "top_inner_diameter_mm": id_mm,
            "bars_inner": bars_layer,
            "bars_outer": bars_layer,
            "bars_total": 2 * bars_layer,
            "bar_area_mm2": round(BAR_AREA_MM2, 6),
            "longitudinal_area_mm2": round(longitudinal_area, 3),
            "concrete_annulus_area_mm2": round(concrete_area, 3),
            "longitudinal_ratio_percent": round(100 * longitudinal_area / concrete_area, 6),
            "hoop_area_one_bar_mm2": round(HOOP_AREA_MM2, 6),
            "hoop_spacing_candidate_mm": HOOP_SPACING_MM,
            "hoop_ratio_one_layer_percent": round(one_hoop_ratio, 6),
            "hoop_ratio_two_layers_percent": round(2 * one_hoop_ratio, 6),
        })
    assert len(output) == 31
    assert sum(row["bars_total"] for row in output) == 5440
    return output


if __name__ == "__main__":
    target = Path(__file__).with_name("longitudinal_rebar_segment_calculation.csv")
    rows = calculate()
    with target.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(target)
    print("longitudinal ratio %:", min(row["longitudinal_ratio_percent"] for row in rows),
          max(row["longitudinal_ratio_percent"] for row in rows))
    print("hoop single-layer ratio %:", min(row["hoop_ratio_one_layer_percent"] for row in rows),
          max(row["hoop_ratio_one_layer_percent"] for row in rows))
