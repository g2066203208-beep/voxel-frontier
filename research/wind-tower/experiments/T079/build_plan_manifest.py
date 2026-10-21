"""Generate a plan manifest only. Does not create motions or simulation results."""
from pathlib import Path
import json
from collections import Counter

root = Path(__file__).resolve().parent
levels = [
    ("FREQUENT_RESEARCH", 0.18, "GB/T50011 6-degree building-table benchmark; wind-tower applicability pending"),
    ("DESIGN_RESEARCH", 0.05 * 9.80665, "proposed intermediate research level based on basic design acceleration; target spectrum pending"),
    ("RARE_RESEARCH", 1.25, "GB/T50011 6-degree building-table benchmark; wind-tower applicability pending"),
]
cases = []

def add_case(case_id, family, level=None, pga=None, note=None, gm=None, angle=None, seed=None, state=None):
    cases.append({
        "case_id": case_id, "family": family, "status": "planned", "ready_to_run": False,
        "earthquake_level": level, "provisional_pga_m_s2": pga, "pga_basis": note,
        "ground_motion_slot": gm, "actual_record_id": None, "record_sha256": None,
        "horizontal_pair_rotation_deg": angle, "wind_seed_slot": seed, "actual_wind_seed": None,
        "wind_input_sha256": None, "wind_speed_m_s": None, "operating_state": state,
        "accepted_model_id": None, "accepted_model_sha256": None,
        "target_spectrum_id": None, "structural_damping": None,
        "aerodynamic_damping_model": None, "earthquake_arrival_s": None,
        "result_path": None,
    })

for level, pga, note in levels:
    for n in range(1, 8):
        gm = f"GM{n:02d}"
        for angle in (0, 90):
            prefix = f"{level}_{gm}_A{angle:03d}"
            add_case(prefix + "_E_P", "E_PARKED", level, pga, note, gm, angle, state="parked_feathered_azimuth_to_freeze")
            for seed in range(1, 4):
                add_case(prefix + f"_WE_O_W{seed:02d}", "WE_OPERATING", level, pga, note, gm, angle, f"W{seed:02d}", "operating_controller_to_freeze")
            add_case(prefix + "_WE_P_WP01", "WE_PARKED", level, pga, note, gm, angle, "WP01", "parked_feathered_azimuth_to_freeze")
for seed in range(1, 4):
    add_case(f"W_ONLY_O_W{seed:02d}", "W_ONLY_OPERATING", seed=f"W{seed:02d}", state="operating_controller_to_freeze")
add_case("W_ONLY_P_WP01", "W_ONLY_PARKED", seed="WP01", state="parked_feathered_azimuth_to_freeze")
add_case("G_PT_EQUILIBRIUM", "G_PT_BASELINE", state="preload_equilibrium")

counts = dict(Counter(c["family"] for c in cases))
assert len(cases) == 215 and len({c["case_id"] for c in cases}) == 215
assert counts["E_PARKED"] == 42 and counts["WE_OPERATING"] == 126 and counts["WE_PARKED"] == 42
assert all(c["ready_to_run"] is False and c["result_path"] is None for c in cases)

manifest = {
    "title": "嘉鱼10MW混塔地震与风震研究计划",
    "created_date": "2026-10-21", "timezone": "Asia/Shanghai", "status": "proposal_not_simulation_results",
    "site_reanalysis_point": {"longitude_deg": 113.925, "latitude_deg": 30.2, "is_verified_geotechnical_site": False},
    "town_level_basis": {"name": "嘉鱼县", "intensity": 6, "basic_acceleration_g": 0.05, "design_group": 1,
                        "source": "https://gf.cabr-fire.com/article-15954.htm"},
    "provisional_soil_class": "II_research_assumption_not_verified",
    "soil_spectrum_sensitivity": ["I1", "III"],
    "foundation_baseline": "fixed_base_assumption_not_site_certification",
    "source_repo": "https://github.com/g2066203208-beep/voxel-frontier",
    "source_commit": "262d5b781e677057315c5cad09e3394b74436cde",
    "record_policy": "GM01-GM07 are unbound slots, not real record identifiers. Use paired real motions with provenance and reliable long-period bandwidth.",
    "execution_policy": "Validate first, execute one level before expansion. This manifest is not a complete code-compliance load-case list.",
    "required_gates": ["freeze_rebar_and_model", "native_data_check", "gravity_effective_PT_equilibrium", "RNA_seismic_validation",
                       "site_spectrum_and_standard_mapping", "bind_real_records_and_check_spectra", "wind_load_inertia_audit", "numerical_convergence"],
    "main_case_count": len(cases), "counts_by_family": counts,
    "separate_pilot_RNA_case_count": 12,
    "pilot_RNA_definition": "3 actual motion pairs x 2 orientations x R0/R1; records and accepted models not yet bound",
    "fine_nonlinear_selection": "6-12 control cases after screening; does not replace code-required cases or support fragility statistics alone",
    "extensions": ["vertical_component", "45_degree_rotation", "arrival_phase", "additional_wind_speeds", "SSI_with_verified_parameters", "effective_PT_uncertainty"],
    "task_id": "T079",
    "canonical_record_path": "research/wind-tower/experiments/T079",
    "matrix_classification": "proposed_screening_budget_not_code_compliance_matrix",
    "wind_sample_limit": "3 operating slots and 1 parked slot are preliminary screening choices only; reuse REF132 and audit seismic-specific combination/sampling clauses before production; expand for convergence.",
    "formal_run_registry_entries": 0,
    "cases": cases,
}
(root / "planned_cases.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"main_cases": len(cases), "counts": counts, "ready_to_run": 0, "results": 0}, ensure_ascii=False))
