#!/usr/bin/env python3
"""Read-only, arithmetic PT identity preflight. NEVER a native Abaqus acceptance."""
import argparse
import json
import re
from decimal import Decimal as D
from pathlib import Path


def d(x):
    return D(str(x))


def near(a, b, tol="0.000001"):
    return abs(d(a) - d(b)) <= D(tol)


def evaluate(meta, raw, t070):
    src = meta["source_identity"]
    ass = meta["registered_assumptions"]
    a = meta["adopted_BF8"]
    ap = d(src["position_count_reconstructed"]) * d(a["BF"]) * d(src["single_strand_area_mm2"])
    sigma0 = d(src["sigma_initial_MPa"])
    ep = d(src["Ep_MPa"])
    length_mm = d(raw["pt"]["element_length_min"]) * 1000
    match = re.search(r"(\d+(?:\.\d+)?)\s*mm\b", ass["anchorage"])
    if not match:
        raise ValueError("No parseable anchorage setback in source metadata")
    delta_mm = d(match.group(1))
    # This source ledger states 30 joints x 2 mm; neither is an observed displacement.
    delta_mm += d(ass["horizontal_joints"]) * d(ass["joint_compression_mm_each_adopted"])
    loss_anchor = ep * delta_mm / length_mm
    losses = ["loss_friction_MPa", "loss_anchor_joint_MPa", "loss_elastic_MPa",
              "loss_relaxation_MPa", "loss_shrink_creep_MPa"]
    loss_total = sum((d(a[k]) for k in losses), D(0))
    pe = ap * (sigma0 - loss_total) / D(1000000)
    p0 = ap * sigma0 / D(1000000)
    checks = {
        "T057_PT_element_count_36": raw["pt"]["element_count"] == 36,
        "T057_PT_112m_single_element": near(raw["pt"]["element_length_min"], 112) and near(raw["pt"]["element_length_max"], 112) and not raw["pt"]["has_intermediate_nodes"],
        "T057_PT_not_embedded": not raw["pt"]["embedded_in_concrete"],
        "T057_nominal_1280_initial_stress": "1.28e+09" in " ".join(raw["prestress"]["initial_stress_block"]),
        "T070_parent_hash_identity": t070["parent_sha256"] == raw["sha256"],
        "Ap_recomputed": near(ap, a["Ap_mm2"]),
        "P0_recomputed": near(p0, a["P0_MN"]),
        "anchor_joint_loss_recomputed": near(loss_anchor, a["loss_anchor_joint_MPa"]),
        "total_loss_recomputed": near(loss_total, a["loss_total_MPa"]),
        "sigma_pe_recomputed": near(sigma0 - loss_total, a["sigma_pe_MPa"]),
        "Pe_recomputed": near(pe, a["Pe_MN"]),
        "eta_recomputed": near(pe / p0, a["eta"], "0.000000001"),
    }
    return {
        "status": "PASS-STATIC-PT-IDENTITY-ONLY" if all(checks.values()) else "HOLD-STATIC-INCONSISTENCY",
        "native_equilibrium": "HOLD-NO-ABAQUS-RUN",
        "checks": checks,
        "P0_MN": float(p0),
        "Pe_design_MN": float(pe),
        "P0_minus_Pe_MN": float(p0 - pe),
        "sigma_initial_MPa": float(sigma0),
        "sigma_effective_design_MPa": float(sigma0 - loss_total),
        "delta_l_assumed_mm": float(delta_mm),
        "anchor_joint_loss_MPa": float(loss_anchor),
        "component_force_losses_MN": {k: float(d(a[k]) * ap / D(1000000)) for k in losses},
        "joint_1mm_sensitivity_MN": float(ep * d(ass["horizontal_joints"]) / length_mm * ap / D(1000000)),
        "notes": ["Inputs are T078 CODE-DESIGN assumptions, not observed settlement.",
                  "An initial stress equal to Pe/Ap would not by itself reproduce construction history.",
                  "Do not treat this arithmetic check as native stress/contact equilibrium."],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = p.parse_args()
    root = args.root
    def load(relative):
        return json.loads((root / relative).read_text(encoding="utf-8"))
    result = evaluate(
        load("experiments/T078/T078_PRESTRESS_DESIGN_META.json"),
        load("experiments/T057/T057_RAW_PHYSICS_AUDIT_20261007.json"),
        load("experiments/T070/T070_BUILD_AUDIT.json"),
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS-STATIC-PT-IDENTITY-ONLY" else 2)


if __name__ == "__main__":
    main()
