#!/usr/bin/env python3
"""L02: one-command, fail-closed T070-C00b Abaqus 2025 Data Check ONLY.

Reads the *real* frozen parent T070 and real failed L01 DAT, re-derives the
C00b child in a separate directory, and invokes the existing SHA-whitelisted
native G0 log collector. Never edits parent, runs Gravity, or starts production.

On an authorized Windows machine with Abaqus:
  python l02_native_single_entry.py --workdir D:/Codex-research-native/T070-20261029/L02_ONE_COMMAND --abaqus D:/Abaqus/Commands/abaqus.bat --execute

For GitHub-hosted CI (no Abaqus), use --preflight-only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
T070 = HERE.parent
SOURCE = T070 / "inputs" / "BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp"
L01_DAT = T070 / "local-20261029-l01" / "T070_C00_G0_DATACHECK.dat"
WRAPPER = HERE / "c00b_run_child_g0.py"
PARENT_SHA = "9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9"
L01_DAT_SHA = "60805bb07d8ccb5c5d922de57d910ab6417beed9dbe3d2ffb04b8c6efe7f8e57"
CHILD_NAME = "BASE001_T070_G0_CONTACT_GROUPS_C00B_CHILD.inp"
CHILD_SHA = "d5f0922a8f9af84cb3a0ab937f417c3f07c44a2deee40864bb074410686853ac"
NATIVE_MANIFEST = "S02_G0_EVIDENCE_MANIFEST.json"

from c00_relocate_t070_ios import relocate
from c00b_repair_l01_contact import repair, validate_native_l01


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def verify_sources(parent: bytes, dat: bytes):
    if sha(parent) != PARENT_SHA or len(parent) != 16_587_215:
        raise ValueError("REFUSE_PARENT_SOURCE_SHA_OR_LENGTH")
    if sha(dat) != L01_DAT_SHA or len(dat) != 144_319:
        raise ValueError("REFUSE_REAL_L01_DAT_SHA_OR_LENGTH")
    validate_native_l01(dat)
    c00, _ = relocate(parent)
    child, evidence = repair(c00)
    if sha(child) != CHILD_SHA or len(child) != 16_587_192:
        raise ValueError("REFUSE_C00B_CHILD_IDENTITY")
    if evidence["contact_pairs_preserved"] != 30 or not evidence["exact_inverse_pass"]:
        raise ValueError("REFUSE_CONTACT_TOPOLOGY_CHANGE")
    return child


def read_native_manifest(path: Path):
    if not path.is_file():
        return {"status": "MISSING_NATIVE_MANIFEST", "native_pass": False}
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("source_sha256") != CHILD_SHA:
        raise ValueError("NATIVE_COLLECTOR_WRONG_INPUT_SHA")
    status = result.get("status", "NO_STATUS")
    return {
        "status": status,
        "native_pass": status == "NATIVE_DATACHECK_COMPLETED_MANUAL_WARNING_REVIEW_REQUIRED",
        "error_count": result.get("diagnostics", {}).get("error_count"),
        "warning_count": result.get("diagnostics", {}).get("warning_count"),
        "native_completed_marker": result.get("native_completed_marker"),
        "native_logs": result.get("logs", {}),
        "missing_required_logs": result.get("missing_required_logs", []),
        "warning_disposition": "NEED_NATIVE_WARNING_REVIEW",
    }


def self_test():
    fake = {"source_sha256": CHILD_SHA, "status": "NATIVE_DATACHECK_FAILED",
            "diagnostics": {"error_count": 7, "warning_count": 129}}
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "manifest.json"
        p.write_text(json.dumps(fake), encoding="utf-8")
        assert read_native_manifest(p)["native_pass"] is False
        fake["source_sha256"] = "0" * 64
        p.write_text(json.dumps(fake), encoding="utf-8")
        try:
            read_native_manifest(p)
        except ValueError as e:
            assert str(e) == "NATIVE_COLLECTOR_WRONG_INPUT_SHA"
        else:
            raise AssertionError("ACCEPTED_WRONG_NATIVE_INPUT")
        assert read_native_manifest(p.parent/"nonexistent.json")["native_pass"] is False
    for bad_parent, bad_dat in [(b"fake", b""), (b"", b"fake")]:
        try:
            verify_sources(bad_parent, bad_dat)
        except ValueError:
            pass
        else:
            raise AssertionError("ACCEPTED_FORGED_EVIDENCE")
    print("L02_SINGLE_ENTRY_SYNTHETIC_REFUSAL_PASS_NOT_ABAQUS")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workdir", type=Path, help="new outside-repo directory")
    ap.add_argument("--abaqus", default="abaqus", help="actual Abaqus 2025 executable/bat")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute", action="store_true", help="explicit native G0 Data Check")
    mode.add_argument("--preflight-only", action="store_true", help="actual source SHA and child regeneration only")
    mode.add_argument("--self-test", action="store_true", help="synthetic negative gates; no real model")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.workdir is None:
        ap.error("--workdir required")
    work = args.workdir.resolve()
    source_root = HERE.parents[3]  # repository research/wind-tower parent or above
    if work == source_root or source_root in work.parents or work in SOURCE.resolve().parents:
        raise SystemExit("REFUSE_WORKDIR_IN_SOURCE_TREE")
    if work.exists():
        raise SystemExit("REFUSE_WORKDIR_EXISTS")
    # Fail *before* creating any artifacts if a native execution was requested
    # but the Abaqus executable is not accessible in this environment.
    executable = shutil.which(args.abaqus) if args.execute else None
    if args.execute and not executable:
        raise SystemExit("BLOCKED_NO_LOCAL_ABAQUS_2025_EXECUTABLE")
    if not SOURCE.is_file() or not L01_DAT.is_file() or not WRAPPER.is_file():
        raise SystemExit("BLOCKED_MISSING_FROZEN_SOURCE_OR_L01_DAT_OR_WRAPPER")
    child = verify_sources(SOURCE.read_bytes(), L01_DAT.read_bytes())
    work.mkdir(parents=True, exist_ok=False)
    input_dir = work / "input"
    output_dir = work / "native_g0"
    input_dir.mkdir()
    inp = input_dir / CHILD_NAME
    inp.write_bytes(child)
    assert sha(inp.read_bytes()) == CHILD_SHA
    receipt = {
        "stage": "S02_L02", "scope": "NATIVE_DATACHECK_ONLY_NOT_EQUILIBRIUM",
        "frozen_t070_sha256": PARENT_SHA, "l01_native_dat_sha256": L01_DAT_SHA,
        "c00b_child_sha256": CHILD_SHA, "c00b_child_bytes": len(child),
        "input_path": str(inp), "command_only_cpus": 1,
        "model_modified": False, "production_run": False,
        "native_abaqus_invoked": False,
        "source_levels": ["FROZEN_REAL_T070_INP", "REAL_FAILED_L01_NATIVE_DAT"],
        "standard": "NO_AUTHORIZED_CODE_CLAUSE_ACCEPTANCE",
        "fig": "NONE", "tab": "NATIVE_LOG_FILES_IF_RUN",
        "limitations": ["S01_PT_DESIGN_HOLD", "S03_EQUILIBRIUM_HOLD",
                        "S04_VV_HOLD", "S08_SEISMIC_HOLD", "S10_FATIGUE_HOLD"],
    }
    exit_code = 0
    if args.preflight_only:
        receipt["status"] = "REAL_SOURCE_C00B_PREFLIGHT_PASS_NO_ABAQUS"
    else:
        argv = [sys.executable, str(WRAPPER), "--inp", str(inp),
                "--out", str(output_dir), "--abaqus", executable]
        receipt["native_abaqus_invoked"] = True
        receipt["runner_argv"] = argv
        # stdout/stderr of the *collector* are kept separately; Abaqus raw
        # logs and their SHA are captured by the existing collector itself.
        completed = subprocess.run(argv, cwd=work, capture_output=True, text=True,
                                   check=False)
        (work / "collector.stdout.log").write_text(completed.stdout, encoding="utf-8")
        (work / "collector.stderr.log").write_text(completed.stderr, encoding="utf-8")
        receipt["collector_returncode"] = completed.returncode
        receipt["native_diagnostics"] = read_native_manifest(output_dir / NATIVE_MANIFEST)
        receipt["status"] = receipt["native_diagnostics"]["status"]
        exit_code = completed.returncode if completed.returncode != 0 else (
            0 if receipt["native_diagnostics"]["native_pass"] else 5
        )
    receipt_path = work / "L02_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "receipt": str(receipt_path),
                      "input_sha256": CHILD_SHA, "native_pass": receipt.get(
                          "native_diagnostics", {}).get("native_pass", False)},
                     ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
