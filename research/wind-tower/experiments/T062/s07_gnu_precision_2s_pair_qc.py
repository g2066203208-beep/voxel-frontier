#!/usr/bin/env python3
"""S07 same GNU/ROSCO v2.6.0 ETM S06 2s OFF/ON precision diagnostic.

Reads two native Actions artifact directories, not an Abaqus or DLC1.2 run.
Packed OUTB thresholds are encoding diagnostics, never physics tolerances.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import re

from s07_linux_v290_v260_2s_pair_qc import compare, parse_outb

def sha(data):
    return hashlib.sha256(data).hexdigest()

def need(condition, code):
    if not condition:
        raise ValueError(code)

def cache_flag(data):
    rows = re.findall(r"(?m)^DOUBLE_PRECISION:BOOL=(ON|OFF)$", data)
    need(len(rows) == 1, "DOUBLE_PRECISION_CACHE_CARDINALITY_HOLD")
    return rows[0]

def read_one(root, expected):
    root = Path(root)
    need(root.is_dir(), "ARTIFACT_DIRECTORY_MISSING")
    cache = (root / "s07_openfast_cmake_cache.txt").read_text(encoding="utf-8", errors="replace")
    flag = cache_flag(cache)
    need(flag == expected, "PRECISION_MATRIX_CACHE_MISMATCH")
    stdout = (root / "s07_linux_native_stdout.log").read_bytes()
    need(b"OpenFAST terminated normally." in stdout, "NATIVE_TERMINATION_HOLD")
    need(re.search(rb"Running ROSCO-v2\\.6\\.0", stdout) is not None, "ROSCO_VERSION_HOLD")
    precision = re.search(rb"Precision:\\s*(single|double)", stdout, re.IGNORECASE)
    need(precision is not None, "NATIVE_PRECISION_STDOUT_MISSING")
    need(precision.group(1).decode().lower() == ("single" if expected == "OFF" else "double"),
         "NATIVE_PRECISION_STDOUT_MISMATCH")
    compressed = (root / "s07_linux_native_2s.outb.gz").read_bytes()
    raw = gzip.decompress(compressed)
    need(0 < len(raw) < 100_000_000, "OUTB_RESOURCE_BOUND_HOLD")
    values = parse_outb(raw)
    identity = json.loads((root / "s07_linux_derived_identity.json").read_text())
    port = json.loads((root / "s07_linux_path_port_receipt.json").read_text())
    source_commit = (root / "s07_rosco_source_commit.log").read_text().strip()
    need(source_commit == "51629665d22f92770f861daeebcebd47ab32abb1", "ROSCO_SOURCE_COMMIT_HOLD")
    patch_sha = (root / "s07_native_input_hashes.log").read_text()
    need("0412e3d8bab3729ec488853e053297c17aab3863e746e4a3178286049b366f00" in patch_sha,
         "OPENFAST_PATCH_SOURCE_HOLD")
    return values, {
        "precision_cmake": flag, "native_precision_stdout": precision.group(1).decode(),
        "outb_sha256": sha(raw), "outb_bytes": len(raw),
        "compressed_outb_sha256": sha(compressed), "native_stdout_sha256": sha(stdout),
        "cmake_cache_sha256": sha(cache.encode()), "rosco_commit": source_commit,
        "controller_binary_sha256": identity["linux_controller_sha256"],
        "source_servo_sha256": identity["source_servo_sha256"],
        "derived_servo_sha256": identity["derived_linux_servo_sha256"],
        "original_windows_controller_sha256": identity["source_controller_sha256"],
        "port_files": port.get("files", []),
        "airfoil_repairs": port.get("case_sensitive_airfoil_repairs", []),
        "input_source_hash_log_sha256": sha(patch_sha.encode()),
        "reading_level": "ACTUAL_NATIVE_2S_OUTB_GZIP_STDOUT_CMAKE_CACHE_SOURCE_HASH_LOGS"
    }

def pair(single, double):
    a, ai = single
    b, bi = double
    for field in ("rosco_commit", "source_servo_sha256", "derived_servo_sha256",
                  "original_windows_controller_sha256", "port_files", "airfoil_repairs",
                  "input_source_hash_log_sha256"):
        need(ai[field] == bi[field], "INPUT_OR_SOURCE_NOT_PAIRED_" + field.upper())
    # Controller binary is recorded, not assumed byte-identical across independent builds.
    data = compare(a, b)
    return {
        "stage": "S07", "status": "GNU_PRECISION_2S_DIAGNOSTIC_ONLY_NOT_PHYSICS_PASS",
        "SOURCE": {"reading_level": "TWO_ACTUAL_GITHUB_ACTIONS_NATIVE_2S_ARTIFACTS", "single": ai, "double": bi},
        "REF": "Existing T062 original 2s OpenFAST and packed OUTB analysis; no new paper full text",
        "STANDARD": "No authorized IEC/GB/NB original clause read; no compliance conclusion",
        "OFFICIAL": "OpenFAST v3.5.3 tagged 6a7a543790f3cad4a65b87242a619ac5b34b4c0f; ROSCO v2.6.0 tagged 51629665d22f92770f861daeebcebd47ab32abb1",
        "RUN": "Two 2-second native OpenFAST diagnostics (OFF/ON), no 700s production and no Abaqus",
        "FIG": "0", "TAB": "295 channels x 41 samples, selected channels and tower-base six components",
        "assumptions": "Same Linux GNU toolchain, tagged sources, same wind BTS and input cards; only OpenFAST DOUBLE_PRECISION changes. Independently built ROSCO binaries are recorded, not presumed identical.",
        "error_budget": "1.1*(two packed OUTB half-LSB)+1e-8 is encoding threshold, NOT physical acceptance. Physical uncertainty and numeric precision sensitivity require interpretation.",
        "failure_record": "Any mismatched source, controller version, precision cache/stdout, OUTB identity/units/time grid or missing native log fails closed; retain raw Actions logs.",
        "HOLD": "Even a successful GNU single/double pilot cannot prove historical Windows Intel equivalence, official DLC1.2, structural V&V, material fatigue or seismic PASS.",
        "physical_pass": False, "stage_pass_count": "0/12", **data
    }

def selftest():
    need(cache_flag("A=1\\nDOUBLE_PRECISION:BOOL=OFF\\n") == "OFF", "CACHE_POSITIVE_HOLD")
    x = {f"C{i}": [0.0] * 41 for i in range(295)}
    u = {k: "(u)" for k in x}
    q = {k: 0.01 for k in x}
    a = (x, u, q)
    b = ({k: v.copy() for k, v in x.items()}, u, q)
    aa = {"rosco_commit": "same", "source_servo_sha256": "same", "derived_servo_sha256": "same",
          "original_windows_controller_sha256": "same", "port_files": [], "airfoil_repairs": [],
          "input_source_hash_log_sha256": "same", "controller_binary_sha256": "a"}
    bb = {**aa, "controller_binary_sha256": "b"}
    report = pair((a, aa), (b, bb))
    need(report["quantization_exceeding_samples"] == 0, "PAIR_POSITIVE_HOLD")
    rejected = 0
    bads = [
        lambda: cache_flag("DOUBLE_PRECISION:BOOL=ON\\nDOUBLE_PRECISION:BOOL=OFF"),
        lambda: cache_flag("DOUBLE_PRECISION:STRING=ON"),
        lambda: pair((a, aa), (b, {**bb, "derived_servo_sha256": "tampered"})),
        lambda: compare(a, ({**b[0], "EXTRA": [0.0]*41}, u, q)),
        lambda: compare(a, ({**b[0], "C0": [float("nan")]*41}, u, q)),
    ]
    for f in bads:
        try:
            f()
        except (ValueError, KeyError):
            rejected += 1
        else:
            raise AssertionError("NEGATIVE_TEST_ACCEPTED")
    need(rejected == 5, "NEGATIVE_COUNT_HOLD")
    return {"synthetic_positive": 2, "negative_rejections": rejected,
            "native_solver_invoked_by_selftest": False, "physical_pass": False}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--single", type=Path)
    p.add_argument("--double", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()
    if args.selftest:
        print(json.dumps(selftest(), sort_keys=True))
    if args.single or args.double or args.out:
        need(all((args.single, args.double, args.out)), "ALL_PAIR_ARGUMENTS_REQUIRED")
        result = pair(read_one(args.single, "OFF"), read_one(args.double, "ON"))
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps({"status": result["status"], "samples": result["samples"],
                          "channels": result["common_channels"],
                          "t0_exceeding": len(result["t0_exceeding_channels"]),
                          "exceeding_samples": result["quantization_exceeding_samples"],
                          "six_component_max_abs_delta": result["six_component_max_abs_delta"],
                          "physical_pass": False}, sort_keys=True))
    elif not args.selftest:
        p.error("provide --single --double --out or --selftest")

if __name__ == "__main__":
    main()
