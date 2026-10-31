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
    "BldPitch1_mean_deg", "GenTq_mean_kNm", "n_original_outb_samples",
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
            "n_original_outb_samples": b["n_samples"],
            "runtime_dll_sha_verified": "NO",
            "formal_dlc12_reuse": "HOLD",
        }
        for key in KEYS:
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
        "group_sixseed_operating_summary": groups, "output_csv_sha256": sha(data),
        "assumptions": "DISCON numeric settings kept as literal raw tokens: no rad/s, W, N*m or degree conversion without verified unit semantics; case labels do not prove DLC1.2",
        "error_budget": "Input SHA256 and source member length exact; CSV means are archived packed-OUTB postprocessed summaries, with per-channel quantization bounds in prior receipt; parameter-to-response causal error and controller dynamics NOT ESTIMATED",
        "negative_tests": "duplicate parameter, malformed numeric, missing key set, missing runtime banner, SHA and case-set fail closed",
        "HOLD": "18 historical per-case DLL binaries and NTM BTS not archived with SHA; DISCON text + ROSCO banner do not certify actual binary equality or 2025 IEC DLC1.2; no material IP stress",
        "formal_dlc12_approved": 0, "physical_pass": False,
        "native_earthquake_results": 0, "stages_passed": 0,
    }
    return data, receipt

def self_test():
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
    print("S07_DISCON_PARAMETER_PARSER_SELFTEST_PASS: 3 negative cases")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        if args.repo_root is None:
            return
    require(args.repo_root and args.out and args.receipt, "MISSING_OUTPUT_PATHS")
    data, receipt = make(args.repo_root)
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
