#!/usr/bin/env python3
"""Compare falsifiable 158m OpenFAST tower property ownership hypotheses.
Static SOURCE-LOCKED test only: never infer a historical generator from a fit.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from s01_s06_r335_pt_tower_identity_inverse import load, SOURCES


def rms(values):
    return math.sqrt(sum(x*x for x in values)/len(values))


def compare(base):
    raw = {key: load(base, key) for key in SOURCES}  # enforces Git blob SHA and 31 rows
    g, c, e, r = (raw[key][0] for key in ("gross", "counts", "ea", "rebar"))
    actual = []
    for j, (gi, ci, ei, ri) in enumerate(zip(g, c, e, r), 1):
        if (int(gi["segment"]), int(ci["segment"].split("_")[-1]),
                int(ei["segment"]), int(ri["segment"])) != (j, j, j, j):
            raise ValueError("SEGMENT_ALIGNMENT")
        a, inertia = float(gi["gross_area_m2"]), float(gi["gross_I_m4"])
        n, diameter = int(ci["bar_count"]), float(ci["d400_mm"])
        if a <= 0 or inertia <= 0 or n <= 0 or diameter <= 0:
            raise ValueError("INVALID_GEOMETRY")
        as25 = n*math.pi*.025**2/4
        is25 = float(ri["d400_rebar_Is_m4"])*(25/diameter)**2
        actual.append(dict(seg=j, A=a, I=inertia, As=as25, Is=is25,
                           EA=float(ei["TwEAStff_N"]),
                           EI=float(ri["openfast_ei_Nm2"]),
                           mass=float(ei["TMassDen_kgpm"]),
                           group="C70" if j <= 2 else "C65"))
    mean = lambda xs: sum(xs)/len(xs)
    group_constants = {}
    for group in ("C70", "C65"):
        rows = [x for x in actual if x["group"] == group]
        group_constants[group] = dict(
            E_from_EA_Pa=mean([x["EA"]/x["A"] for x in rows]),
            E_from_EI_Pa=mean([x["EI"]/x["I"] for x in rows]),
            density_kgpm3=mean([x["mass"]/x["A"] for x in rows]))
    models = {name: {k: [] for k in ("EA", "EI", "mass")} for name in (
        "physical_gross_only", "uniform_40GPa_2560kgm3",
        "gross_group_fitted_6parameters", "R335_phi25_PT_gross_additive",
        "R335_phi25_PT_displace_rebar",
        "R335_phi25_PT_displace_rebar_and_PT")}
    for x in actual:
        ec = (37 if x["group"] == "C70" else 36.5)*1e9
        es, rho_c, rho_s, apt = 200e9, 2400., 7850., .04032
        a, i, as25, is25 = (x[k] for k in ("A", "I", "As", "Is"))
        fit = group_constants[x["group"]]
        candidates = {
            "physical_gross_only": (ec*a, ec*i, rho_c*a),
            "uniform_40GPa_2560kgm3": (40e9*a, 40e9*i, 2560*a),
            "gross_group_fitted_6parameters": (
                fit["E_from_EA_Pa"]*a, fit["E_from_EI_Pa"]*i,
                fit["density_kgpm3"]*a),
            "R335_phi25_PT_gross_additive": (
                ec*a+es*as25, ec*i+es*is25, rho_c*a+rho_s*(as25+apt)),
            "R335_phi25_PT_displace_rebar": (
                ec*(a-as25)+es*as25, ec*(i-is25)+es*is25,
                rho_c*(a-as25)+rho_s*(as25+apt)),
            "R335_phi25_PT_displace_rebar_and_PT": (
                ec*(a-as25)+es*as25, ec*(i-is25)+es*is25,
                rho_c*(a-as25-apt)+rho_s*(as25+apt))}
        for name, (ea, ei, mass) in candidates.items():
            for key, pred in (("EA", ea), ("EI", ei), ("mass", mass)):
                models[name][key].append(100*(pred/x[key]-1))
    result = {
        "status": "STATIC_HYPOTHESIS_COMPARISON_NOT_GENERATOR_PROOF",
        "source_sha256": {SOURCES[k][0]: raw[k][1] for k in SOURCES},
        "segment_count": len(actual),
        "tower_source_sha256_historical": "f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983",
        "group_fitted_effective_properties": group_constants,
        "rms_relative_error_percent": {
            name: {key: rms(values) for key, values in errors.items()}
            for name, errors in models.items()},
        "max_abs_relative_error_percent": {
            name: {key: max(map(abs, values)) for key, values in errors.items()}
            for name, errors in models.items()},
        "assumptions": {
            "phi25_bar_count": "same as archived R335 counts; radii proxied by D400 Is scaling",
            "R335_material": "Ec=37GPa for CSEG01-02, 36.5GPa otherwise; Es=200GPa",
            "PT_area_m2": .04032, "concrete_density_kgm3": 2400,
            "steel_density_kgm3": 7850,
            "group_fit": "C70/C65 separately; EA, EI and mass fitted independently (six free coefficients); descriptive, not independent prediction",
            "gross_additive": "double-counts displaced concrete volume; intentionally tests existing embedded-style input arithmetic",
            "volume_corrected": "assumes perfect composite volume replacement, which need not match ElastoDyn model convention"},
        "limitations": [
            "Cannot establish original tower generator or mass/EI ownership from numerical fit.",
            "D400 Is-based radius proxy is not a recovered R335 bar-location ledger.",
            "Does not include PT tangent stiffness, ring/tie steel, joints, RNA, modal calibration or native solver.",
            "SOURCE/STATIC RUN/TAB only; REF/STANDARD/OFFICIAL reading unchanged; no FIG; physical error budget NEED_ESTIMATE.",
            "S01/S06 HOLD, S02-S04 BLOCKED, no earthquake result."]}
    if result["segment_count"] != 31:
        raise ValueError("EXPECTED_31_SEGMENTS")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    result = compare(args.base)
    data = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)+"\n"
    if args.json:
        if args.json.exists():
            raise FileExistsError("REFUSE_OVERWRITE_JSON")
        args.json.write_text(data, encoding="utf-8")
    print(data)
    print("STATIC ONLY; S01/S06 HOLD; NO NATIVE ABAQUS/OPENFAST PASS")


if __name__ == "__main__":
    main()
