#!/usr/bin/env python3
"""S07: source-verified ROSCO DISCON parameters vs archived 18-NTM operating summaries.
This is a deterministic SOURCE QC, not a runtime DLL identity or IEC DLC1.2 PASS.
No OpenFAST, TurbSim or Abaqus solver is invoked.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
from pathlib import Path

from s07_ntm18_original_control_input_gate import (
    Source, manifest_index, read_pinned, STATIC_SHA, SUPPLEMENT_SHA, sha,
)

ROOT = Path("research/wind-tower")
CONFIG_SHA = "be58d33306e6ac101d42b42c7f4d24ea5743662d1a9355aff9862b5a7e0aad45"
STATE_SHA = "0f577f3197870a1350c740c2e0c118073fb9b6f796b4c471765c6f616d5a1b04"
LOG_SHA = "46667b0a0d01467b7a0635c203db83e880dd26f67f663cfaf7ea82f760f881e1"
DISCON_SHA = "8f5d7546420ee34838e66b63e4b26d64460be5d5492f99c60b6d1ef977ffc61a"
KEYS = (
    "VS_ControlMode", "PC_ControlMode", "VS_RtPwr", "VS_RtTq", "VS_RtGnSp",
    "PC_RefSpd", "PC_MinPit", "PC_MaxPit", "PC_GS_angles", "PC_GS_KP",
    "PC_GS_KI", "VS_Rgn2K", "VS_MaxTq", "VS_MinTq", "VS_ConstPower",
    "PC_Switch", "F_LPFType", "F_LPFCornerFreq", "Y_ControlMode",
)
# Additional v2.6.0 registry keys omitted by the historical 17-key screen.
# Registry original source: NatLabRockies/ROSCO v2.6.0 tag 51629665...,
# ROSCO/rosco_registry/rosco_types.yaml SHA256 c83eb68c... .
# Do not treat a missing key as zero or infer it from a different controller key.
EXTENDED_PARAMETER_KEYS = {
    "VS_RefSpd": "rated generator speed [rad/s]",
    "VS_TSRopt": "region-2 optimal tip-speed ratio (registry says [rad]; unit requires caution)",
    "VS_GenEff": "generator mechanical-to-electrical efficiency fraction [-]",
    "WE_Mode": "wind-speed estimator mode {0,1}",
    "SS_Mode": "setpoint smoother mode {0,1}",
    "VS_MinOMSpd": "optimal-mode minimum generator speed [rad/s]",
    "VS_MaxRat": "maximum generator torque rate [N m/s]",
    "PC_MaxRat": "maximum pitch rate [rad/s]",
    "WE_GearboxRatio": "wind estimator gearbox ratio [-]",
}
KEYS = KEYS + tuple(EXTENDED_PARAMETER_KEYS)
NUM = re.compile(r"^[+-]?(?:(?:\d+\.?\d*|\.\d+)(?:[EeDd][+-]?\d+)?)$")
HEADER = [
    "case", "wind_speed_mps", "seed", "discon_sha256", "rosco_runtime_banner",
    "servo_pitch_mode", "servo_vs_mode", "discon_VS_ControlMode_raw",
    "discon_PC_ControlMode_raw", "discon_VS_RtPwr_raw", "discon_VS_RtTq_raw",
    "discon_VS_RtGnSp_raw", "discon_PC_RefSpd_raw", "discon_PC_MinPit_raw",
    "discon_PC_MaxPit_raw", "discon_PC_GS_angles_raw", "discon_PC_GS_KP_raw",
    "discon_PC_GS_KI_raw", "discon_VS_Rgn2K_raw", "discon_VS_MaxTq_raw",
    "discon_VS_MinTq_raw", "discon_VS_ConstPower_raw", "discon_PC_Switch_raw",
    "discon_F_LPFType_raw", "discon_F_LPFCornerFreq_raw",
    "discon_Y_ControlMode_raw", "GenPwr_mean_kW", "RotSpeed_mean_rpm",
    "BldPitch1_mean_deg", "GenTq_mean_kNm", "GenSpeed_mean_rpm",
    "rated_power_torque_speed_relerr", "mean_power_to_rated_fraction",
    "mean_torque_to_rated_fraction", "mean_genspeed_to_reference_fraction",
    "n_original_outb_samples",
    "runtime_dll_sha_verified", "formal_dlc12_reuse",
]

def require(condition, msg):
    if not condition:
        raise ValueError(msg)

def parse_discon(raw):
    text = raw.decode("utf-8-sig", errors="strict")
    parsed = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        if "!" not in line:
            continue
        value, comment = line.split("!", 1)
        if not value.strip():
            continue
        match = re.match(r"^\s*([A-Za-z][A-Za-z0-9_]*)\b", comment)
        if not match or match.group(1) not in KEYS:
            continue
        key = match.group(1)
        require(key not in parsed, "DUPLICATE_DISCON_KEY:" + key)
        parts = value.replace(",", " ").split()
        require(parts and all(NUM.fullmatch(x) for x in parts),
                "INVALID_DISCON_NUMERIC:" + key)
        parsed[key] = {"raw": value.strip(), "line": lineno,
                       "tokens": len(parts), "comment": comment.strip()}
    require(len(parsed) >= 6, "TOO_FEW_CONTROLLER_KEYS")
    return parsed

def read_rows(path, digest):
    raw = read_pinned(path, digest)
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    require(len(rows) == 18 and len({x["case"] for x in rows}) == 18,
            "INVALID_18CASE_SOURCE")
    return {x["case"]: x for x in rows}

def make(root):
    base = root / ROOT
    cfg = read_rows(base / "experiments/T062/S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv", CONFIG_SHA)
    state = read_rows(base / "experiments/T062/S07_18NTM_ORIGINAL_OPERATING_STATE_QC_20261101.csv", STATE_SHA)
    logs = read_rows(base / "experiments/T062/S07_18NTM_NATIVE_CONTROLLER_LOG_QC_20261101.csv", LOG_SHA)
    require(set(cfg) == set(state) == set(logs), "CROSS_SOURCE_CASE_MISMATCH")
    static = read_pinned(base / "archive/local-assets-20261004/file-manifest.json", STATIC_SHA)
    supp = read_pinned(base / "archive/local-assets-20261004-supplement/file-manifest.json", SUPPLEMENT_SHA)
    src = Source(root, {"static": manifest_index(static), "supp": manifest_index(supp)})
    try:
        raw, entry = src.get("supp", "openfast-36-r2",
            "CASES/U09p343881_ETM_S01/Control/DTU_10MW_RWT_DISCON.IN")
    finally:
        src.close()
    require(sha(raw) == DISCON_SHA and entry["bytes"] == len(raw),
            "DISCON_ORIGINAL_BYTE_IDENTITY")
    p = parse_discon(raw)
    for required in ("VS_RtPwr", "VS_RtTq", "PC_RefSpd"):
        require(required in p and p[required]["tokens"] == 1,
                "RATED_PARAMETER_MISSING_OR_ARRAY:" + required)
    rated_power_W = float(p["VS_RtPwr"]["raw"])
    rated_torque_Nm = float(p["VS_RtTq"]["raw"])
    reference_speed_radps = float(p["PC_RefSpd"]["raw"])
    require(all(math.isfinite(x) and x > 0 for x in
                (rated_power_W, rated_torque_Nm, reference_speed_radps)),
            "INVALID_RATED_PARAMETERS")
    rated_relerr = abs(rated_torque_Nm * reference_speed_radps -
                       rated_power_W) / rated_power_W
    rows = []
    for case in sorted(cfg):
        a, b, c = cfg[case], state[case], logs[case]
        require(a["discon_sha256"] == DISCON_SHA, "DISCON_CASE_SHA:" + case)
        require(a["servo_PCMode"] == "5" and a["servo_VSContrl"] == "5",
                "SERVO_BLADED_MODES:" + case)
        require(c["native_stdout_rosco_banner"] == "ROSCO-v2.6.0" and
                c["native_stdout_legacy_bladed_interface"] == "YES",
                "RUNTIME_LOG_BANNER:" + case)
        require(c["runtime_dll_identity_verified"] == "NO" and
                not c["manifest_dll_sha256"], "UNEXPECTED_DLL_IDENTITY:" + case)
        require(b["formal_DLC12_reuse"] == "HOLD_NOT_VERIFIED" and
                int(b["n_samples"]) == 12001, "OPERATING_SOURCE_STATUS:" + case)
        for k in ("GenPwr_mean", "RotSpeed_mean", "BldPitch1_mean", "GenTq_mean"):
            require(float(b[k]) == float(b[k]) and abs(float(b[k])) < 1e12,
                    "NONFINITE_OPERATING_SUMMARY:" + case + ":" + k)
        row = {
            "case": case, "wind_speed_mps": a["turb_URef_mps"],
            "seed": a["turb_seed1"], "discon_sha256": DISCON_SHA,
            "rosco_runtime_banner": c["native_stdout_rosco_banner"],
            "servo_pitch_mode": a["servo_PCMode"], "servo_vs_mode": a["servo_VSContrl"],
            "GenPwr_mean_kW": b["GenPwr_mean"],
            "RotSpeed_mean_rpm": b["RotSpeed_mean"],
            "BldPitch1_mean_deg": b["BldPitch1_mean"],
            "GenTq_mean_kNm": b["GenTq_mean"],
            "GenSpeed_mean_rpm": b["GenSpeed_mean"],
            "rated_power_torque_speed_relerr": f"{rated_relerr:.12g}",
            "mean_power_to_rated_fraction":
                f"{float(b['GenPwr_mean'])*1000/rated_power_W:.12g}",
            "mean_torque_to_rated_fraction":
                f"{float(b['GenTq_mean'])*1000/rated_torque_Nm:.12g}",
            "mean_genspeed_to_reference_fraction":
                f"{float(b['GenSpeed_mean'])*math.pi/30/reference_speed_radps:.12g}",
            "n_original_outb_samples": b["n_samples"],
            "runtime_dll_sha_verified": "NO",
            "formal_dlc12_reuse": "HOLD",
        }
        # Preserve the historical 18-case CSV schema. New v2.6.0 keys belong
        # exclusively in the separate 9-row original-DISCON supplement.
        for key in KEYS:
            if key in EXTENDED_PARAMETER_KEYS:
                continue
            row["discon_" + key + "_raw"] = p.get(key, {}).get("raw", "")
        rows.append(row)
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    data = buf.getvalue().encode("utf-8")
    groups = {}
    for speed in sorted({r["wind_speed_mps"] for r in rows}, key=float):
        subset = [r for r in rows if r["wind_speed_mps"] == speed]
        require(len(subset) == 6, "SEED_COVERAGE:" + speed)
        groups[speed] = {
            "seed_count": 6,
            "mean_power_kW": sum(float(r["GenPwr_mean_kW"]) for r in subset) / 6,
            "mean_pitch_deg": sum(float(r["BldPitch1_mean_deg"]) for r in subset) / 6,
            "mean_rotor_rpm": sum(float(r["RotSpeed_mean_rpm"]) for r in subset) / 6,
        }
    receipt = {
        "SOURCE": "Direct original 17,600-byte DISCON.IN ZIP member, source manifests; existing 18-case FST/ServoDyn, 18 OUTB-derived summaries and 18 original native ROSCO banner CSVs",
        "source_reading_level": "Original DISCON.IN bytes verified this run; existing OUTB summaries/log source rows SHA-pinned, NOT reread 18 OUTB binaries or 18 stdout raw ZIP members",
        "REF": "Existing T062 ROSCO-v2.6.0 historical stdout evidence and 12-stage plan; no new journal full text",
        "STANDARD": "IEC 61400-1/6:2025 authorized DLC1.2 clauses NOT read",
        "OFFICIAL": "Original archived DISCON/ServoDyn inputs and native OpenFAST stdout-derived evidence; not proof of identical historical DLL binaries",
        "RUN": "Python3 standard-library ZIP+CSV SHA source postprocessing and negative tests; no solver run",
        "FIG": "none", "TAB": "18-case original controller settings vs original OUTB summary CSV",
        "input_sha256": {"original_discon": DISCON_SHA, "original_manifest": STATIC_SHA,
            "supplement_manifest": SUPPLEMENT_SHA, "18case_input_csv": CONFIG_SHA,
            "18case_operating_csv": STATE_SHA, "18case_native_log_csv": LOG_SHA},
        "original_discon_bytes": len(raw),
        "parsed_discon_parameters": p, "recognized_parameter_count": len(p),
        "conditional_rated_power_torque_speed_identity": {
            "VS_RtPwr_assumed_W": rated_power_W,
            "VS_RtTq_assumed_Nm": rated_torque_Nm,
            "PC_RefSpd_assumed_rad_per_s": reference_speed_radps,
            "product_W": rated_torque_Nm * reference_speed_radps,
            "relative_residual": rated_relerr,
            "assumption": "ROSCO setting names interpreted in W, N-m and rad/s; OUTB source units kW, kN-m and rpm. Diagnostic unit contract only, not IEC compliance."
        },
        "group_sixseed_operating_summary": groups, "output_csv_sha256": sha(data),
        "assumptions": "Original DISCON values retained as raw tokens; additional W/N-m/rad-s to OUTB kW/kN-m/rpm ratios are CONDITIONAL on ROSCO unit semantics, not official certification; case labels do not prove DLC1.2",
        "error_budget": "Input SHA256 and source member length exact; rated identity floating arithmetic ~1e-15 plus source parameter decimal rounding; CSV means are packed-OUTB summaries with per-channel quantization in prior receipt; unit interpretation, controller dynamics and causal error NOT ESTIMATED",
        "negative_tests": "duplicate parameter, malformed numeric, missing key set, missing runtime banner, SHA and case-set fail closed",
        "HOLD": "18 historical per-case DLL binaries and NTM BTS not archived with SHA; DISCON text + ROSCO banner do not certify actual binary equality or 2025 IEC DLC1.2; no material IP stress",
        "formal_dlc12_approved": 0, "physical_pass": False,
        "native_earthquake_results": 0, "stages_passed": 0,
    }
    return data, receipt


def extended_source_qc(data, receipt):
    """Small non-duplicative original DISCON key table + conditional operating bands."""
    p = receipt["parsed_discon_parameters"]
    rows = []
    semantic_holds = []
    for key, unit in EXTENDED_PARAMETER_KEYS.items():
        obj = p.get(key)
        rows.append({
            "parameter": key, "source_line": str(obj["line"]) if obj else "",
            "status": "ORIGINAL_VALUE" if obj else "NOT_PRESENT_IN_ORIGINAL",
            "raw_value": obj["raw"] if obj else "",
            "numeric_tokens": str(obj["tokens"]) if obj else "",
            "v260_registry_semantics": unit,
            "original_discon_sha256": DISCON_SHA,
        })
        if not obj:
            continue
        require(obj["tokens"] == 1, "EXTENDED_PARAMETER_NOT_SCALAR:" + key)
        val = float(obj["raw"])
        require(math.isfinite(val), "EXTENDED_PARAMETER_NONFINITE:" + key)
        if key in ("WE_Mode", "SS_Mode"):
            require(val in (0.0, 1.0), "EXTENDED_MODE_OUT_OF_RANGE:" + key)
        elif key == "VS_GenEff":
            require(val > 0, "EXTENDED_EFFICIENCY_NONPOSITIVE")
            if val > 1:
                # Official registry uses a fraction [-]; never silently divide by 100.
                rows[-1]["status"] = "ORIGINAL_VALUE_SEMANTIC_HOLD"
                semantic_holds.append({"parameter": key, "source_line": obj["line"],
                    "raw_value": obj["raw"], "registry_expected": "0 < efficiency <= 1",
                    "reason": "Original source exceeds v2.6.0 fraction definition; unit/identity unresolved"})
        elif key in ("VS_RefSpd", "VS_TSRopt", "VS_MinOMSpd", "WE_GearboxRatio"):
            require(val > 0, "EXTENDED_POSITIVE_PARAMETER:" + key)
    buf = io.StringIO(newline="")
    columns = ["parameter", "source_line", "status", "raw_value",
               "numeric_tokens", "v260_registry_semantics", "original_discon_sha256"]
    writer = csv.DictWriter(buf, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    output = buf.getvalue().encode("utf-8")
    historic = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    require(len(historic) == 18, "EXTENDED_18CASE_CROSS_SOURCE")
    speed = float(p["VS_RefSpd"]["raw"]) if "VS_RefSpd" in p else None
    groups = {}
    for wind in sorted({r["wind_speed_mps"] for r in historic}, key=float):
        subset = [r for r in historic if r["wind_speed_mps"] == wind]
        require(len(subset) == 6, "EXTENDED_SEED_COVERAGE:" + wind)
        mean_gen_rpm = sum(float(r["GenSpeed_mean_rpm"]) for r in subset) / 6
        mean_pitch_deg = sum(float(r["BldPitch1_mean_deg"]) for r in subset) / 6
        groups[wind] = {
            "n": 6, "mean_gen_speed_rpm": mean_gen_rpm,
            "mean_pitch_deg": mean_pitch_deg,
            "mean_gen_speed_over_vs_reference": (
                mean_gen_rpm * math.pi / 30 / speed if speed else None),
            "reference_missing": speed is None,
        }
    result = {
        "SOURCE": "Original 17,600-byte DISCON.IN member read by make() and SHA256 verified; historical 18-row OUTB-derived source table regenerated in same invocation",
        "source_reading_level": "Original DISCON bytes; existing 18 OUTB summaries cross-checked, original 18 OUTB binaries not reread",
        "REF": "ROSCO v2.6.0 tagged registry semantics, previously SHA-pinned; no new journal full text",
        "STANDARD": "IEC 61400-1/6:2025 authorized DLC1.2 clauses not read",
        "OFFICIAL": "NatLabRockies/ROSCO v2.6.0 tag 51629665d22f92770f861daeebcebd47ab32abb1, ROSCO/rosco_registry/rosco_types.yaml",
        "RUN": "Python original ZIP read + SHA256 and conditional source-parameter validation; NO OpenFAST/Abaqus/fe-safe run",
        "FIG": "none", "TAB": "9-key original DISCON supplement, not duplicate 18-case source table",
        "input_sha256": receipt["input_sha256"],
        "official_registry_sha256_previous_read": "c83eb68cadccbbf9a2084cc14c9dc94f6731304179b6ffad30aa1d4df4b63b4c",
        "original_discon_bytes": receipt["original_discon_bytes"],
        "output_csv_sha256": sha(output),
        "parameters_present": sum(x["status"] != "NOT_PRESENT_IN_ORIGINAL" for x in rows),
        "semantic_holds": semantic_holds,
        "semantic_validation_pass": len(semantic_holds) == 0,
        "parameters_absent": [x["parameter"] for x in rows if x["status"] != "ORIGINAL_VALUE"],
        "operating_band_diagnostics": groups,
        "assumptions": "Six-seed averages are descriptive only; no timewise ROSCO internal state, no covariance or actual generator efficiency inferred from means. Missing original keys are NOT zero. Registry VS_GenEff is a fraction [-]; source values >1 are preserved verbatim as SEMANTIC_HOLD and NOT divided by 100. VS_TSRopt registry unit wording is retained, not independently certified.",
        "error_budget": "Original DISCON bytes/SHA exact; output CSV deterministic; floating group means have roundoff ~1e-14 relative plus previously documented packed-OUTB uncertainty; internal state/closed-loop dynamics and DLL binary uncertainty NOT ESTIMATED",
        "negative_tests": "parser rejects duplicate, malformed, insufficient keys; extended validator rejects non-scalar, invalid modes, efficiency outside (0,1], nonpositive speed, absent key never filled with zero",
        "HOLD": "Original 18 per-case BTS/DLL SHA not recovered, controller internal state not recorded, IEC2025 clauses and S01-S04 physics not passed",
        "formal_dlc12_approved": 0, "physical_pass": False,
        "native_earthquake_results": 0, "stages_passed": 0,
    }
    return output, result

def self_test():
    assert all("discon_" + k + "_raw" in HEADER
               for k in KEYS if k not in EXTENDED_PARAMETER_KEYS)
    assert all("discon_" + k + "_raw" not in HEADER
               for k in EXTENDED_PARAMETER_KEYS)
    good = b" 1 ! VS_ControlMode - test\n 2.0 3e-1 ! PC_GS_KP - test\n 0 ! PC_ControlMode\n 1 ! VS_RtPwr\n 2 ! VS_RtTq\n 3 ! PC_RefSpd\n"
    assert len(parse_discon(good)) == 6
    for bad in (good + b" 3 ! VS_ControlMode\n",
                good.replace(b"2.0 3e-1", b"not-a-number"),
                b" 1 ! VS_ControlMode\n"):
        try:
            parse_discon(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("MALFORMED_CONTROLLER_ACCEPTED")
    fixture = good + (b" 49.9 ! VS_RefSpd\n 7.5 ! VS_TSRopt\n"
                      b" 0.94 ! VS_GenEff\n 1 ! WE_Mode\n 0 ! SS_Mode\n")
    p = parse_discon(fixture)
    assert p["VS_RefSpd"]["raw"] == "49.9"
    assert p["VS_TSRopt"]["raw"] == "7.5"
    assert p["VS_GenEff"]["raw"] == "0.94"
    assert p["WE_Mode"]["raw"] == "1" and p["SS_Mode"]["raw"] == "0"
    assert "VS_MinOMSpd" not in p and p["PC_RefSpd"]["raw"] == "3"
    for key, val in (("VS_GenEff", "-1.1"), ("WE_Mode", "2"),
                     ("VS_RefSpd", "-3")):
        altered = fixture.replace(
            {"VS_GenEff": b"0.94", "WE_Mode": b"1", "VS_RefSpd": b"49.9"}[key]
            + b" ! " + key.encode(),
            val.encode() + b" ! " + key.encode())
        try:
            # Call the scalar validation on a minimal real-shaped receipt.
            pbad = parse_discon(altered)
            fake = {"parsed_discon_parameters": pbad,
                    "input_sha256": {"original_discon": DISCON_SHA},
                    "original_discon_bytes": len(altered)}
            extended_source_qc(
                ("case,wind_speed_mps,GenSpeed_mean_rpm,BldPitch1_mean_deg\n"
                 + "".join(f"C{i},{i//6},480,5\n" for i in range(18))).encode(),
                fake)
        except ValueError:
            pass
        else:
            raise AssertionError("EXTENDED_BAD_PARAMETER_ACCEPTED:" + key)
    # Out-of-registry efficiency is retained with explicit semantic HOLD.
    high_eff = fixture.replace(b"0.94 ! VS_GenEff", b"94 ! VS_GenEff")
    fake_receipt = {"parsed_discon_parameters": parse_discon(high_eff),
                    "input_sha256": {"original_discon": DISCON_SHA},
                    "original_discon_bytes": len(high_eff)}
    fake_csv = ("case,wind_speed_mps,GenSpeed_mean_rpm,BldPitch1_mean_deg\n"
                + "".join(f"C{i},{i//6},480,5\n" for i in range(18))).encode()
    _, flagged = extended_source_qc(fake_csv, fake_receipt)
    assert flagged["semantic_holds"][0]["raw_value"] == "94"
    assert not flagged["semantic_validation_pass"] and not flagged["physical_pass"]
    print("EXTENDED_DISCON_SELFTEST_PASS: 5 extracted keys, 3 invalid parameter rejections, 1 semantic HOLD")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--extended-out", type=Path)
    parser.add_argument("--extended-receipt", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        if args.repo_root is None:
            return
    require(args.repo_root and args.out and args.receipt, "MISSING_OUTPUT_PATHS")
    data, receipt = make(args.repo_root)
    require(bool(args.extended_out) == bool(args.extended_receipt),
            "EXTENDED_OUTPUT_PAIR_REQUIRED")
    if args.extended_out:
        ext_data, ext_receipt = extended_source_qc(data, receipt)
        args.extended_out.parent.mkdir(parents=True, exist_ok=True)
        args.extended_out.write_bytes(ext_data)
        args.extended_receipt.write_text(json.dumps(ext_receipt, ensure_ascii=False,
            sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print("S07_EXTENDED_DISCON_ORIGINAL_SOURCE_QC",
              json.dumps({"keys": len(EXTENDED_PARAMETER_KEYS),
                "present": ext_receipt["parameters_present"],
                "csv_sha256": ext_receipt["output_csv_sha256"],
                "formal_dlc12_approved": 0}, sort_keys=True))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(data)
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True,
                                      indent=2) + "\n", encoding="utf-8")
    print("S07_18NTM_DISCON_VS_OUTB_SOURCE_QC_NOT_DLC12",
          json.dumps({"cases": 18, "keys": receipt["recognized_parameter_count"],
                      "csv_sha256": receipt["output_csv_sha256"],
                      "formal_dlc12_approved": 0}, sort_keys=True))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("S07_DISCON_OPERATING_GATE_FAIL", type(exc).__name__, str(exc),
              file=sys.stderr)
        raise
