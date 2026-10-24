#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S01 exact D400/D500 straight-T3D2 cage geometry sensitivity (NOT design PASS).

Uses the frozen T057 coordinates and the real 72-chord hoop polygons.
Each longitudinal T3D2 receives one radial shift applied consistently to BOTH
endpoints; no independent ring-by-ring relocation or bent single element.
5 mm is a sensitivity target, NOT a normative minimum. No INP/ODB is emitted.

Run:
 python s01_d400_d500_straight_t3d2_exact.py --inp /path/T057.inp --outdir /tmp/s01_geometry
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from s01_native_inp_cage_polygon_clearance import (
    get_bars, get_hoops, instance_yshift, part_section
)
from s01_straight_bar_radial_clearance import make_samples, evaluate, shift_for

T057_SHA256 = "c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db"
SOURCE_CSV_SHA256 = "e0a1f7d230a97f2e9575aba3178d42903cfcfa5d537a62f32d001c5544ebf855"
BRANCHES = {
    "D400": ("d400_screen_d_mm", "d400_derived_unmoved_clear_mm", "d400_conditional_u"),
    "D500": ("d500_historical_d_mm", "d500_derived_unmoved_clear_mm", "d500_historical_conditional_u"),
}
TARGET_MM = 5.0  # geometry sensitivity only, not a code requirement


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inp", type=Path, required=True)
    p.add_argument("--outdir", type=Path, required=True)
    p.add_argument("--branches", type=Path, default=Path(__file__).with_name(
        "S01_D400_D500_UNMOVED_CAGE_CLEARANCE_31SEG_20261025.csv"))
    args = p.parse_args()
    inp_raw = args.inp.read_bytes()
    csv_raw = args.branches.read_bytes()
    assert sha256(inp_raw) == T057_SHA256, "frozen T057 source SHA256 mismatch"
    assert sha256(csv_raw) == SOURCE_CSV_SHA256, "branch CSV SHA256 mismatch"
    inp = inp_raw.decode("utf-8")
    hoops, hoop_nodes, hoop_edges = get_hoops(part_section(inp, "HOOP_TIE_CAGE_T046"))
    assert (hoop_nodes, hoop_edges) == (201456, 201456)
    records = list(csv.DictReader(csv_raw.decode("utf-8-sig").splitlines()))
    assert len(records) == 31 and len({r["segment"] for r in records}) == 31
    by_seg = {r["segment"]: r for r in records}

    results = []
    sample_count = 0
    for i in range(1, 32):
        seg = f"CSEG_{i:02d}"
        name = f"RBLONG_{i:02d}"
        bars, node_count = get_bars(part_section(inp, name))
        samples = make_samples(bars, instance_yshift(inp, name), hoops)
        assert samples, f"no bar/hoop samples for {seg}"
        sample_count += len(samples)
        source = by_seg[seg]
        for branch, (d_col, gap_col, u_col) in BRANCHES.items():
            d = int(source[d_col])
            gap0 = evaluate(samples, 0.0, d)
            recorded = float(source[gap_col])
            # Recorded baseline was rounded to 6 decimal places.
            assert abs(gap0 - recorded) < 0.00002, (
                f"{seg}/{branch}: geometry baseline differs: {gap0} vs {recorded}"
            )
            shift_m = shift_for(samples, d, TARGET_MM)
            gap5, cover_proxy, radial_separation_proxy = evaluate(
                samples, shift_m, d, detail=True
            )
            assert gap5 >= TARGET_MM - 0.00001, f"{seg}/{branch}: gap target not met"
            assert all(math.isfinite(x) for x in (gap5, cover_proxy, radial_separation_proxy))
            results.append({
                "segment": seg,
                "branch": branch,
                "diameter_mm": d,
                "bar_elements": len(bars),
                "bar_nodes": node_count,
                "bar_hoop_samples": len(samples),
                "unmoved_min_clearance_mm": f"{gap0:.9f}",
                "straight_endpoint_shift_for_5mm_mm": f"{shift_m*1000:.9f}",
                "achieved_min_clearance_mm": f"{gap5:.9f}",
                "cover_proxy_mm": f"{cover_proxy:.9f}",
                "interlayer_radial_clearance_proxy_mm": f"{radial_separation_proxy:.9f}",
                "conditional_NM_utilization_before_relayout": source[u_col],
                "status": "GEOMETRY_SENSITIVITY_ONLY_NO_NATIVE_OR_CODE_PASS",
            })
    assert sample_count == 245760, f"unexpected unique hoop-plane sample count: {sample_count}"
    assert len(results) == 62
    assert {branch: sum(
        float(r["unmoved_min_clearance_mm"]) < 0 for r in results if r["branch"] == branch
    ) for branch in BRANCHES} == {"D400": 28, "D500": 28}

    args.outdir.mkdir(parents=True, exist_ok=True)
    csv_path = args.outdir / "S01_D400_D500_31SEG_STRAIGHT_T3D2_EXACT_GEOMETRY.csv"
    json_path = args.outdir / "S01_D400_D500_31SEG_STRAIGHT_T3D2_EXACT_MANIFEST.json"
    if csv_path.exists() or json_path.exists():
        raise FileExistsError("refuse to overwrite existing output")
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    summary = {}
    for branch in BRANCHES:
        group = [r for r in results if r["branch"] == branch]
        summary[branch] = {
            "unmoved_negative_segments": sum(float(r["unmoved_min_clearance_mm"]) < 0 for r in group),
            "max_straight_endpoint_shift_mm": max(float(r["straight_endpoint_shift_for_5mm_mm"]) for r in group),
            "min_achieved_gap_mm": min(float(r["achieved_min_clearance_mm"]) for r in group),
            "min_cover_proxy_mm": min(float(r["cover_proxy_mm"]) for r in group),
            "min_interlayer_radial_clearance_proxy_mm": min(
                float(r["interlayer_radial_clearance_proxy_mm"]) for r in group),
        }
    manifest = {
        "source_inp_sha256": sha256(inp_raw),
        "source_branch_csv_sha256": sha256(csv_raw),
        "script_sha256": sha256(Path(__file__).read_bytes()),
        "result_csv_sha256": sha256(csv_path.read_bytes()),
        "unique_bar_hoop_samples": sample_count,
        "evaluated_branch_samples": sample_count * len(BRANCHES),
        "rows": len(results),
        "target_mm": TARGET_MM,
        "target_is_normative": False,
        "straight_t3d2_endpoint_relocation": True,
        "new_inp_emitted": False,
        "native_abaqus_run": "NOT_RUN",
        "rebar_strength_rerun_after_relayout": "NOT_RUN",
        "standard_material_and_detailing": "HOLD",
        "PT_gravity_contact_equilibrium": "HOLD",
        "physical_error_budget": "NEED_ESTIMATE",
        "result": summary,
    }
    json_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
