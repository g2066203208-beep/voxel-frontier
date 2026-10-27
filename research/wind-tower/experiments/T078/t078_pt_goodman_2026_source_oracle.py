#!/usr/bin/env python3
"""Static SOURCE comparison: T078 prestress stages vs Qu et al. 2026 Eq.(1)-(2).

NOT a fatigue-life prediction for DTU10MW; delta_sigma is a hypothetical cycle
range, not a measured/rainflow-derived stress range. Does not mutate any INP.
REF023 DOI 10.3390/buildings16193854, publisher HTML §§2.1-2.2.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

PINNED_META_SHA256 = "50b5d23c9991955b8cfe304bdb1bc8519e07ad1b97a8f7500bb7e878eb69d2a1"
REF = "10.3390/buildings16193854"


def analyze(meta_path, delta_sigma_mpa, expected_sha256=PINNED_META_SHA256):
    raw = meta_path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != expected_sha256:
        raise ValueError(f"T078 source SHA mismatch: {sha} != {expected_sha256}")
    m = json.loads(raw)
    src, design = m["source_identity"], m["adopted_BF8"]
    area = float(design["Ap_mm2"])
    s0, se = float(src["sigma_initial_MPa"]), float(design["sigma_pe_MPa"])
    su = float(src["fpk_MPa"])
    p0, pe = float(design["P0_MN"]), float(design["Pe_MN"])
    loss = float(design["loss_total_MPa"])
    if not (0 < se < s0 < su and 0 < delta_sigma_mpa < su):
        raise ValueError("invalid material or hypothetical cycle range")
    if not (math.isclose(area*s0/1e6, p0, abs_tol=1e-8) and
            math.isclose(area*se/1e6, pe, abs_tol=1e-8) and
            math.isclose(s0-se, loss, abs_tol=1e-8)):
        raise ValueError("P0/Pe/loss not consistent with source area and stress")
    loss_components = ["loss_friction_MPa", "loss_anchor_joint_MPa",
                       "loss_elastic_MPa", "loss_relaxation_MPa",
                       "loss_shrink_creep_MPa"]
    if not math.isclose(sum(float(design[k]) for k in loss_components), loss, abs_tol=1e-8):
        raise ValueError("loss components do not close")
    def candidate(mean):
        factor = 1/(1-mean/su)
        corrected_range = delta_sigma_mpa*factor
        # REF023 Eq(1): log10 N = 13.95 - 3.5 log10(S_r), S_r in MPa.
        N = 10**(13.95-3.5*math.log10(corrected_range))
        return {"hypothetical_mean_stress_MPa": mean,
                "goodman_multiplier": factor,
                "hypothetical_corrected_range_MPa": corrected_range,
                "conditional_cycles_from_2026_paper_SN": N}
    at_initial, at_effective = candidate(s0), candidate(se)
    return {
        "input": str(meta_path), "input_sha256": sha, "source_git_blob": "99a750c22268febde268bcdbea46d7f21cfe34f8",
        "source_ref": REF, "reading_level": "publisher-indexed-HTML-selected-Sections-2.1-2.2-not-PDF",
        "input_stage_P0_MN": p0, "design_effective_Pe_MN": pe,
        "design_total_loss_MPa": loss, "design_total_loss_fraction": loss/s0,
        "design_relaxation_only_loss_MPa": float(design["loss_relaxation_MPa"]),
        "design_relaxation_only_fraction": float(design["loss_relaxation_MPa"])/s0,
        "hypothetical_fixed_cycle_range_MPa": delta_sigma_mpa,
        "stage_P0_as_cycle_mean_NOT_ACTUAL": at_initial,
        "stage_Pe_as_cycle_mean_NOT_ACTUAL": at_effective,
        "conditional_SN_damage_ratio_P0_mean_over_Pe_mean": at_effective["conditional_cycles_from_2026_paper_SN"]/at_initial["conditional_cycles_from_2026_paper_SN"],
        "status": "STATIC_METHOD_SENSITIVITY_ONLY_NO_NATIVE_NO_RAINFLOW_NO_LIFE_CLAIM",
        "hold": ["actual PT mean/range rainflow histories not provided", "strand-specific SN calibration not established",
                 "Pe is a design estimate, not native equilibrated tendon stress", "PT loss timing vs model initialization unresolved",
                 "2026 reference tower is 4.55MW with tied concrete segments; cannot validate 30 dry contact joints"]
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", type=Path, default=Path(__file__).with_name("T078_PRESTRESS_DESIGN_META.json"))
    ap.add_argument("--delta-sigma-mpa", type=float, default=20.0)
    ap.add_argument("--expected-sha256", default=PINNED_META_SHA256)
    args = ap.parse_args()
    print(json.dumps(analyze(args.meta, args.delta_sigma_mpa, args.expected_sha256), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
