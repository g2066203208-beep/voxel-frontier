#!/usr/bin/env python3
"""S07 no-solver original Windows vs actual Linux derived-input byte parity.

Rebuilds the exact path/case/DLL transformations on a SHA-locked 2s ETM
source-preparation tree and checks their recorded hashes against the REAL
Linux v2.6.0 Actions artifact. This is input identity, NOT runtime equivalence.
"""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ARTIFACT_SHA = "51d2e0c5926f9aac4f9b24851a83e2f1e744584cc3a16371108b97280652cf5c"
BTS_SHA = "ad68a83a63f197c528c07502db8adff883e9c737863ef3c4cab99cfa76052147"
BLADE_SHA = "6ad2426fd429f4e01008700d31d4b64d79358522bcf265ce12f7706e8a1f895d"
AIRFOIL_SHA = "2994cb5f79282170019be0a8c48b60155905365cac4ac88b21dda58c16f925cb"
WRONG = b"Cylinder_AeroDyn15.dat"
RIGHT = b"Cylinder_Aerodyn15.dat"
QUOTED = re.compile(rb'"[^"\r\n]*\\[^"\r\n]*"')
BARE = re.compile(rb'(?<![A-Za-z0-9_.])(?:\.\.?\\)[^\s\r\n]+')
NUM = re.compile(rb'(?<![A-Za-z0-9_.])[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eEdD][-+]?\d+)?(?![A-Za-z0-9_.])')
DLL = re.compile(r'(?m)^(\s*)(?:"[^"\r\n]+"|\S+)(\s+DLL_FileName\b[^\r\n]*)$')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def require(ok, message):
    if not ok:
        raise ValueError(message)

def port(data):
    data = QUOTED.sub(lambda m: m.group(0).replace(b'\\', b'/'), data)
    return BARE.sub(lambda m: m.group(0).replace(b'\\', b'/'), data)

def change_dll(data):
    src = data.decode("utf-8-sig")
    edited, count = DLL.subn(lambda m: m.group(1) + '"libdiscon.so"' + m.group(2), src)
    require(count == 1, "S07_DLL_FILENAME_CARDINALITY_HOLD")
    require(re.search(r'(?m)^\s*"libdiscon.so"\s+DLL_FileName\b', edited),
            "S07_DLL_PATH_NOT_RELATIVE_TO_SERVO_DIRECTORY")
    return edited.encode("utf-8")

def numeric_cards_unchanged(source, derived, label):
    require(NUM.findall(source) == NUM.findall(derived),
            "S07_NUMERIC_CARD_CHANGED_" + label)
    return len(NUM.findall(source))

def artifact_member(archive, basename):
    matches = [n for n in archive.namelist() if Path(n).name == basename]
    require(len(matches) == 1, "S07_ARTIFACT_RECEIPT_CARDINALITY_" + basename)
    return json.loads(archive.read(matches[0]))

def strict_equal(actual, expected, label):
    require(actual == expected, "S07_ACTUAL_LINUX_RECEIPT_MISMATCH_" + label)

def audit(root, artifact):
    root = Path(root)
    require((root / "S06_0P1S_PREP_RECEIPT.json").is_file(),
            "S07_PREP_RECEIPT_MISSING")
    prep = json.loads((root / "S06_0P1S_PREP_RECEIPT.json").read_text())
    require(prep.get("case") == "U09p343881_ETM_S06" and
            prep.get("TMax_s") == 2.0 and prep.get("batch") == 1 and
            prep.get("etm_s06_bts_original_sha256") == BTS_SHA,
            "S07_PREP_SOURCE_OR_TIME_IDENTITY_HOLD")
    require(digest((root.parent / "Rotor/DTU_10MW_ElastoDyn_Blades.dat").read_bytes()) == BLADE_SHA,
            "S07_BLADE_SHA_HOLD")
    require(digest((root.parent / "Rotor/Airfoils/Cylinder_Aerodyn15.dat").read_bytes()) == AIRFOIL_SHA,
            "S07_AIRFOIL_SHA_HOLD")
    require(digest(Path(artifact).read_bytes()) == ARTIFACT_SHA,
            "S07_REAL_LINUX_ARTIFACT_SHA_HOLD")
    with zipfile.ZipFile(artifact) as z:
        require(z.testzip() is None, "S07_LINUX_ARTIFACT_CRC_HOLD")
        path_receipt = artifact_member(z, "s07_linux_path_port_receipt.json")
        dll_receipt = artifact_member(z, "s07_linux_derived_identity.json")
    require(path_receipt["source_model_modified"] is False and
            path_receipt["physics_parameter_modified"] is False and
            dll_receipt["source_equivalence"] is False and
            dll_receipt["physical_pass"] is False,
            "S07_NATIVE_RECEIPT_SEMANTICS_HOLD")
    path_rows, case_rows, originals, after_port, after_case = [], [], {}, {}, {}
    for p in sorted(root.parent.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in (".fst", ".dat", ".txt"):
            continue
        rel = p.relative_to(root.parent).as_posix()
        before = p.read_bytes()
        originals[rel] = before
        changed = port(before) if b'\\' in before else before
        after_port[rel] = changed
        if changed != before:
            path_rows.append({"file": rel, "source_sha256": digest(before),
                              "derived_sha256": digest(changed),
                              "backslash_count_removed": before.count(b'\\') - changed.count(b'\\')})
        hits = changed.count(WRONG)
        final = changed.replace(WRONG, RIGHT)
        after_case[rel] = final
        if hits:
            case_rows.append({"file": rel, "references_repaired": hits,
                              "source_sha256": digest(changed), "derived_sha256": digest(final)})
    require(path_rows and case_rows, "S07_NO_REAL_PATH_OR_CASE_REPAIR_HOLD")
    strict_equal(path_rows, path_receipt["files"], "PATH_PORT_ROWS")
    strict_equal(case_rows, path_receipt["case_sensitive_airfoil_repairs"], "AIRFOIL_CASE_ROWS")
    strict_equal(sum(x["references_repaired"] for x in case_rows),
                 path_receipt["case_sensitive_airfoil_reference_total"], "AIRFOIL_CASE_COUNT")
    servo = "batch1/Control/DTU_10MW_RWT_ServoDyn.dat"
    require(servo in after_case, "S07_SERVO_SOURCE_MISSING")
    strict_equal(digest(after_case[servo]), dll_receipt["source_servo_sha256"],
                 "PRE_DLL_SERVO_SHA")
    derived_servo = change_dll(after_case[servo])
    strict_equal(digest(derived_servo), dll_receipt["derived_linux_servo_sha256"],
                 "POST_DLL_SERVO_SHA")
    dll_file = root / "Control/libdiscon.dll"
    strict_equal(digest(dll_file.read_bytes()), dll_receipt["source_controller_sha256"],
                 "HISTORICAL_WINDOWS_DLL_SHA")
    numeric_total = 0
    for rel, source in originals.items():
        final = derived_servo if rel == servo else after_case[rel]
        numeric_total += numeric_cards_unchanged(source, final, rel)
    return {
        "stage": "S07", "status": "INPUT_BYTE_TRANSFORM_PARITY_ONLY_NOT_PHYSICS_PASS",
        "SOURCE": {"level": "DIRECT_SHA_LOCKED_RECONSTRUCTED_WINDOWS_SOURCE_BYTES_AND_REAL_LINUX_ACTIONS_ARTIFACT_RECEIPTS",
                   "real_linux_v260_artifact_sha256": ARTIFACT_SHA,
                   "original_bts_sha256": BTS_SHA,
                   "original_prep_source_sha256": prep["source_sha256"],
                   "original_shared_blade_sha256": BLADE_SHA,
                   "original_airfoil_sha256": AIRFOIL_SHA,
                   "original_windows_controller_sha256": digest(dll_file.read_bytes()),
                   "linux_controller_sha256_from_native_receipt_only": dll_receipt["linux_controller_sha256"]},
        "REF": "T062 S06 ETM original input contract and native Windows/Linux v2.6.0 pair receipts; no journal full-text read",
        "STANDARD": "No newly read authorized IEC/GB/NB clause",
        "OFFICIAL": "Actual OpenFAST v3.5.3/ROSCO v2.6.0 native Linux diagnostic receipt; original model source hash-locked",
        "RUN": {"native_solver_invoked": False, "real_source_input_rebuilt": True,
                "actual_linux_receipt_sha_matched": True,
                "path_port_files": len(path_rows), "airfoil_case_files": len(case_rows),
                "airfoil_case_references": sum(x["references_repaired"] for x in case_rows),
                "source_text_files_audited": len(originals),
                "numeric_tokens_unchanged": numeric_total,
                "servo_pre_post_sha_matched": True, "physical_pass": False},
        "FIG": "0",
        "TAB": {"path_port_files": path_rows, "case_sensitive_airfoil_repairs": case_rows,
                "source_servo_sha256": digest(after_case[servo]),
                "derived_servo_sha256": digest(derived_servo)},
        "ASSUMPTIONS": "Same source preparation tree and archived native Linux v2.6.0 receipt; compares deterministic input text transformations, NOT executable precision or dynamic initial state",
        "ERROR_BUDGET": "SHA256 exact for source/derived text and controller DLL; numeric token sequences exactly equal; no numerical physics error allocated",
        "HOLD": "Windows Intel single precision vs Linux GNU double precision, controller binary and initial state still not causally separated; no formal DLC1.2 or material fatigue acceptance",
        "physical_pass": False, "controller_equivalence_verified": False,
    }

def selftest():
    require(port(b'"./..\\Rotor\\blade.dat" BldFile\n1.2 DT\n') ==
            b'"./../Rotor/blade.dat" BldFile\n1.2 DT\n', "PORT_POSITIVE")
    require(port(b'1.2 DT\n') == b'1.2 DT\n', "PORT_NUMERIC_NOOP")
    require(change_dll(b'"Control/libdiscon.dll" DLL_FileName\n') ==
            b'"libdiscon.so" DLL_FileName\n', "DLL_POSITIVE")
    numeric_cards_unchanged(b'0.1 DT\n"foo\\bar" X\n', b'0.1 DT\n"foo/bar" X\n', "POSITIVE")
    bad = [
        lambda: change_dll(b'1.0 DT\n'),
        lambda: change_dll(b'"x" DLL_FileName\n"y" DLL_FileName\n'),
        lambda: numeric_cards_unchanged(b'0.1 DT\n', b'0.2 DT\n', "NEGATIVE"),
        lambda: strict_equal("a", "b", "NEGATIVE"),
        lambda: require(False, "NEGATIVE"),
    ]
    for i, fn in enumerate(bad):
        try: fn()
        except ValueError: pass
        else: raise AssertionError("S07_NEGATIVE_ACCEPTED_" + str(i))
    return {"positive_tests": 4, "negative_rejections": len(bad),
            "native_solver": False, "physical_pass": False}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path)
    ap.add_argument("--linux-artifact", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        print(json.dumps(selftest(), sort_keys=True))
    if args.root is None and args.linux_artifact is None and args.out is None and args.selftest:
        return
    if not (args.root and args.linux_artifact and args.out):
        ap.error("require --root --linux-artifact --out")
    result = audit(args.root, args.linux_artifact)
    require(not args.out.exists(), "S07_REFUSE_OVERWRITE")
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "run": result["RUN"]}, sort_keys=True))

if __name__ == "__main__":
    main()
