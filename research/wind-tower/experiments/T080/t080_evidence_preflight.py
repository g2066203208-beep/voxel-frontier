#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T080 G0 metadata cross-check. Not a finite-element/engineering verification.

Reads committed SOURCE audit records; no .inp decoding, no ODB, no native solver.
Static record consistency may PASS while all scientific entry gates stay HOLD.
Usage:
  python research/wind-tower/experiments/T080/t080_evidence_preflight.py
  python research/wind-tower/experiments/T080/t080_evidence_preflight.py --out /tmp/t080.json
  python research/wind-tower/experiments/T080/t080_evidence_preflight.py --self-test
  python research/wind-tower/experiments/T080/t080_evidence_preflight.py --require-ready

References:
  experiments/T057/T057_BUILD_AUDIT.json and T057_RAW_PHYSICS_AUDIT_20261007.json
  experiments/T070/T070_BUILD_AUDIT.json and T070_ROUNDTRIP_AUDIT.json
  experiments/T077/T077_FORMAL_REBAR_META.json
  experiments/T078/T078_PRESTRESS_DESIGN_META.json
  experiments/T079/ACADEMIC_REVIEW.md
  experiments/T080/T080_2_PHYSICS_IDENTITY_AND_SEISMIC_ENTRY_AUDIT_20261022.md
"""
import argparse
import json
import math
import sys
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent.parent
TOL = 1e-7


def get_data(name, filename):
    path = EXPERIMENTS / name / filename
    return json.loads(path.read_text(encoding="utf-8"))


def is_close(actual, expected, abs_tol=TOL):
    return math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=abs_tol)


def evaluate(data):
    build = data["T057_build"]
    raw = data["T057_raw"]
    child = data["T070_build"]
    roundtrip = data["T070_roundtrip"]
    rebar = data["T077"]
    pt = data["T078"]
    checks = []
    blockers = []

    def check(code, ok, detail, sources):
        checks.append({"id": code, "status": "PASS-STATIC-RECORD" if ok else "CONFLICT",
                       "detail": detail, "sources": sources})

    parent_sha = build["checks"]["output_sha256"]
    child_sha = child["output_sha256"]
    check("SC-01", all([
        parent_sha == raw["sha256"],
        parent_sha == child["parent_sha256"],
        parent_sha == roundtrip["expected_parent_sha256"],
        parent_sha == roundtrip["recovered_parent_sha256"],
        roundtrip["roundtrip_exact_parent"] is True,
        child_sha == roundtrip["t070_sha256"],
    ]), "T057/T070 registered hashes and exact-roundtrip record agree; no bytes independently rehashed.",
        ["T057_BUILD_AUDIT", "T057_RAW_PHYSICS_AUDIT", "T070_BUILD_AUDIT", "T070_ROUNDTRIP_AUDIT"])

    check("SC-02", build["checks"]["joint_contact_pairs"] ==
          raw["horizontal_joint_property_count"] ==
          pt["registered_assumptions"]["horizontal_joints"] == 30,
          "30 joint contacts match design-loss bookkeeping; contact physics not validated.",
          ["T057_BUILD_AUDIT", "T057_RAW_PHYSICS_AUDIT", "T078_PRESTRESS_DESIGN_META"])

    n_fe_bundles = raw["pt"]["element_count"]
    bf = pt["adopted_BF8"]["BF"]
    area_single = pt["source_identity"]["single_strand_area_mm2"]
    total_area = n_fe_bundles * bf * area_single
    check("SC-03", n_fe_bundles == pt["source_identity"]["position_count_reconstructed"] == 36
          and bf == pt["PT_quantity_selection"]["adopted_BF"] == 8
          and is_close(total_area, pt["adopted_BF8"]["Ap_mm2"])
          and build["checks"]["pt_bundle_area_0p00112"] is True,
          "FE 36 PT positions x 8 strands x 140 mm2 = 40320 mm2, only static topology and design arithmetic.",
          ["T057_RAW_PHYSICS_AUDIT", "T057_BUILD_AUDIT", "T078_PRESTRESS_DESIGN_META"])

    input_stress_pa = float(raw["prestress"]["initial_stress_block"][1].split(",")[1])
    sigma0 = pt["source_identity"]["sigma_initial_MPa"]
    p0 = total_area * sigma0 / 1_000_000.0
    loss_fields = ["loss_friction_MPa", "loss_anchor_joint_MPa",
                   "loss_elastic_MPa", "loss_relaxation_MPa",
                   "loss_shrink_creep_MPa"]
    actual_loss_sum = sum(float(pt["adopted_BF8"][field]) for field in loss_fields)
    designed = pt["adopted_BF8"]
    check("SC-04", is_close(input_stress_pa / 1e6, sigma0)
          and is_close(p0, designed["P0_MN"])
          and is_close(actual_loss_sum, designed["loss_total_MPa"])
          and is_close(sigma0 - actual_loss_sum, designed["sigma_pe_MPa"])
          and is_close(total_area * designed["sigma_pe_MPa"] / 1_000_000.0,
                       designed["Pe_MN"])
          and is_close(designed["eta"], designed["sigma_pe_MPa"] / sigma0),
          "Nominal PT load and code-design losses reconcile arithmetically; they are not the same initial physical state.",
          ["T057_RAW_PHYSICS_AUDIT", "T078_PRESTRESS_DESIGN_META"])

    check("SC-05", rebar["segments"] == 31
          and "HRB500" in rebar["ordinary_rebar"]["branch"]
          and build["checks"]["HRB335_sections"] > 0,
          "Recorded HRB335 physical branch differs from HRB500 code-design branch; not a PASS for design unity.",
          ["T057_BUILD_AUDIT", "T077_FORMAL_REBAR_META"])

    check("SC-06", raw["pt"]["element_type"] == "T3D2"
          and raw["pt"]["element_count"] == 36
          and raw["pt"]["has_intermediate_nodes"] is False
          and raw["pt"]["embedded_in_concrete"] is False,
          "Existing tendon topology captured; mechanical coupling and losses still require native V&V.",
          ["T057_RAW_PHYSICS_AUDIT"])

    blockers.append({
        "id": "G0-REBAR", "state": "HOLD",
        "why": "Physical HRB335/phi25 T057 and HRB500 segment-wise design T077 are separate configurations.",
        "exit": "Select and freeze a single physical branch; verify 31 sections and all rebar detailing in INP.",
        "basis": ["T057_BUILD_AUDIT", "T077_FORMAL_REBAR_META", "T080.2 ID-02/07"]})
    blockers.append({
        "id": "G0-PT", "state": "HOLD",
        "why": "T057 nominal input = %.6f MN, T078 proposed effective design = %.6f MN; gap = %.6f MN."
               % (p0, designed["Pe_MN"], p0 - designed["Pe_MN"]),
        "exit": "Resolve construction/loss path and native Gravity-PT-contact equilibrium without silently equating input to long-term effective state.",
        "basis": ["T057_RAW_PHYSICS_AUDIT", "T078_PRESTRESS_DESIGN_META", "T080.2 ID-04/05/06"]})
    blockers.append({
        "id": "G1-NATIVE", "state": "HOLD",
        "why": "T070 static instrumentation/roundtrip do not prove Abaqus native Data Check or physical equilibrium.",
        "exit": "Record native dat/msg/sta/odb; mass/CG/J, interface RF/RM, 30-mode/flex and mesh evidence.",
        "basis": ["T070_BUILD_AUDIT", "T070_ROUNDTRIP_AUDIT", "T070_G0_G1_RUNBOOK"]})
    blockers.append({
        "id": "G2-SITE", "state": "HOLD",
        "why": "Jiayu town benchmark does not establish soil class, site hazard, compatible seismic inputs or code compliance.",
        "exit": "Provide soil/foundation/hazard evidence, current standard clauses and real-record QC.",
        "basis": ["T079/ACADEMIC_REVIEW", "T079/RESEARCH_CARD"]})

    static_conflicts = [x["id"] for x in checks if x["status"] == "CONFLICT"]
    return {
        "schema": "t080-evidence-preflight-v1",
        "scope": "GitHub metadata cross-check only: NO .inp rehash, NO Abaqus, NO site/code verification",
        "model_sha256_from_prior_audit": {"T057": parent_sha, "T070": child_sha},
        "static_checks": checks,
        "static_conflicts": static_conflicts,
        "scientific_gates": blockers,
        "scientific_ready": False,
        "status": "CONFLICT-IN-STATIC-RECORDS" if static_conflicts else
                  "PASS-STATIC-RECORDS / PHYSICS-HOLD",
        "do_not_claim": ["NATIVE_SOLVER_PASS", "DESIGN_BRANCH_RECONCILED",
                         "SITE_SEISMIC_COMPLIANCE", "EARTHQUAKE_RESULT"]
    }


def load_project_data():
    return {
        "T057_build": get_data("T057", "T057_BUILD_AUDIT.json"),
        "T057_raw": get_data("T057", "T057_RAW_PHYSICS_AUDIT_20261007.json"),
        "T070_build": get_data("T070", "T070_BUILD_AUDIT.json"),
        "T070_roundtrip": get_data("T070", "T070_ROUNDTRIP_AUDIT.json"),
        "T077": get_data("T077", "T077_FORMAL_REBAR_META.json"),
        "T078": get_data("T078", "T078_PRESTRESS_DESIGN_META.json"),
    }


def self_test():
    data = load_project_data()
    result = evaluate(data)
    if result["static_conflicts"]:
        raise AssertionError("Registered metadata consistency checks failed: %r" %
                             result["static_conflicts"])
    assert result["scientific_ready"] is False
    assert all(item["state"] == "HOLD" for item in result["scientific_gates"])
    assert [v["id"] for v in result["static_checks"]] == [
        "SC-01", "SC-02", "SC-03", "SC-04", "SC-05", "SC-06"]
    assert "HRB500" in result["static_checks"][4]["detail"]
    assert "51.609600" in result["scientific_gates"][1]["why"]
    assert "39.753559" in result["scientific_gates"][1]["why"]
    print("T080 metadata fixture self-test: expected record consistency and physics HOLD")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Write audit JSON to path")
    parser.add_argument("--require-ready", action="store_true",
                        help="Return nonzero for any scientific HOLD (intentionally blocks production)")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    result = evaluate(load_project_data())
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload)
    if result["static_conflicts"]:
        return 2
    if args.require_ready and not result["scientific_ready"]:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
