#!/usr/bin/env python3
"""S07: verify four reconstructed 2s ETM input directories against 23 archived SHA256 identities.
NO OpenFAST/Abaqus solver execution. Only exact input provenance, not DCM or physics PASS.
"""
import argparse
import hashlib
import json
from pathlib import Path

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def check(expected, actual, label):
    if expected != actual:
        raise ValueError("INPUT_IDENTITY_SHA256_MISMATCH " + label)

def unique_identities(items):
    keys = [(x["kind"], x["name"]) for x in items]
    if len(keys) != len(set(keys)):
        raise ValueError("DUPLICATE_SOURCE_IDENTITY")
    if len(items) != 23:
        raise ValueError("SOURCE_IDENTITY_COUNT_MISMATCH")
    for x in items:
        if len(x["sha256"]) != 64:
            raise ValueError("INVALID_SOURCE_SHA256")
    return items

def selftest():
    check("a" * 64, "a" * 64, "positive")
    for fn in (
        lambda: check("a" * 64, "b" * 64, "negative"),
        lambda: unique_identities([{"kind": "x", "name": "a", "sha256": "a" * 64}] * 23),
        lambda: unique_identities([]),
    ):
        try:
            fn()
        except ValueError:
            pass
        else:
            raise AssertionError("NEGATIVE_TEST_ACCEPTED")
    print("S07_INPUT_GATE_SELFTEST_PASS three_negative_rejections")

def audit(a):
    receipt = json.loads(Path(a.source_receipt).read_text(encoding="utf-8"))
    historical = json.loads(Path(a.historical_qc).read_text(encoding="utf-8"))
    ids = unique_identities(receipt["s07_native_2s_bundle_gate_20261103"]["required_source_identities_not_in_output_zip"])
    if historical["status"] != "NUMERICAL_PARITY_PASS" or len(historical["derived_input_sha256"]) != 4:
        raise ValueError("HISTORICAL_NATIVE_RECEIPT_IDENTITY")
    root = Path(a.root)
    archives = {"part001": Path(a.archive1), "part002": Path(a.archive2), "supp": Path(a.supp)}
    mapping = {}
    for name, path in archives.items():
        mapping[("source_archive", name)] = path
    mapping[("wind", "ETM_S06.bts")] = Path(a.bts)
    mapping[("original_component", "tower")] = root / "batch1/C02R3R2_158M_Tower.dat"
    mapping[("original_component", "servo")] = root / "batch1/Control/DTU_10MW_RWT_ServoDyn.dat"
    mapping[("original_component", "exe")] = Path(a.exe)
    for b in range(1, 5):
        mapping[("derived_ed", f"batch{b}/DTU_10MW_RWT_ElastoDyn.dat")] = root / f"batch{b}/DTU_10MW_RWT_ElastoDyn.dat"
    for name in ("DTU_10MW_RWT.fst", "DTU_10MW_InflowWind.dat", "Control/libdiscon.dll"):
        mapping[("derived_common", name)] = root / "batch1" / name
    for x in ids:
        if x["kind"] == "shared_rotor":
            mapping[(x["kind"], x["name"])] = root / "Rotor" / x["name"]
    if set(mapping) != {(x["kind"], x["name"]) for x in ids}:
        raise ValueError("SOURCE_MAPPING_NOT_EXHAUSTIVE")
    actual = {}
    for x in ids:
        key = (x["kind"], x["name"])
        path = mapping[key]
        if not path.is_file():
            raise ValueError("SOURCE_FILE_MISSING " + x["name"])
        got = sha256(path)
        check(x["sha256"], got, x["name"])
        actual[x["kind"] + "/" + x["name"]] = got
    # Historical four-batch native receipt is a reference only: no native solver run here.
    for b in range(1, 5):
        p = root / f"batch{b}"
        prep = json.loads((p / "S06_0P1S_PREP_RECEIPT.json").read_text(encoding="utf-8"))
        if prep["case"] != "U09p343881_ETM_S06" or prep["TMax_s"] != 2.0 or not prep["overlap_mode"]:
            raise ValueError("PREP_CASE_OR_DURATION_MISMATCH")
        if prep["etm_s06_bts_original_sha256"] != historical["bts_sha256"]:
            raise ValueError("PREP_WIND_IDENTITY_MISMATCH")
        if prep["source_sha256"] != historical["original_input_sha256"]:
            raise ValueError("PREP_ORIGINAL_SOURCE_IDENTITY_MISMATCH")
        for name, expected in historical["derived_input_sha256"][b-1].items():
            check(expected, sha256(p / name), f"batch{b}/{name}")
        for name, expected in prep["source_archives_sha256"].items():
            check(expected, sha256(archives[name]), "archive/" + name)
        for name, expected in prep["shared_rotor_source_sha256"].items():
            check(expected, sha256(root / "Rotor" / name), "rotor/" + name)
    result = {
        "status": "ALL_23_RECONSTRUCTED_INPUT_IDENTITIES_SHA256_PASS__NO_SOLVER",
        "identity_count": len(ids),
        "sha256": actual,
        "historical_qc_status": historical["status"],
        "SOURCE": "Three actual archived source ZIPs, exact LFS BTS/exe, controller and four reconstructed input directories",
        "REF": "T062 historical 2s four-batch native QC and S07 original-output-only artifact receipt",
        "STANDARD": "No new authorized IEC/GB/NB clause read",
        "OFFICIAL": "Historical OpenFAST v3.5.3/ROSCO Windows binaries, verified only by bytes, NOT executed",
        "RUN": "Four 2s input PREPARATIONS ONLY; native solver runs=0",
        "FIG": "0",
        "TAB": "23 exact SHA256 identities and four historical derived-source maps",
        "assumptions": "2s reconstructed inputs replicate historical prep identity; historical 2s OUTB is not new DCM evidence",
        "error_budget": "Exact SHA256 equality; no physical dynamics, frame, force ownership or 600s uncertainty estimate",
        "HOLD": "No patched complete OpenFAST diagnostic binary and no actual t1/-t3/t2 DCM; S07 physical HOLD",
        "stage_pass": False, "physical_pass": False,
    }
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--root")
    p.add_argument("--source-receipt")
    p.add_argument("--historical-qc")
    p.add_argument("--archive1")
    p.add_argument("--archive2")
    p.add_argument("--supp")
    p.add_argument("--exe")
    p.add_argument("--bts")
    p.add_argument("--out")
    a = p.parse_args()
    if a.selftest:
        selftest()
        return
    for key in ("root", "source_receipt", "historical_qc", "archive1", "archive2", "supp", "exe", "bts", "out"):
        if not getattr(a, key):
            p.error("missing --" + key.replace("_", "-"))
    result = audit(a)
    target = Path(a.out)
    if target.exists():
        raise ValueError("REFUSE_OVERWRITE")
    target.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "identities": result["identity_count"],
                      "physical_pass": False}, sort_keys=True))

if __name__ == "__main__":
    main()
