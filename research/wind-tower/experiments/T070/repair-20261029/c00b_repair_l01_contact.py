#!/usr/bin/env python3
"""C00b: exact-byte L01 native G0 parser repair; no Abaqus/production RUN.

Source = frozen T070 parent -> C00 IOS child -> C00b contact child.
Changes ONLY (1) an empty data line after 30 contact assignments, and
(2) invalid direct contact field identifiers -> Abaqus/Standard group keys.
C00b is STATIC_ONLY; native G0 must be run by authorized local Abaqus.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

from c00_relocate_t070_ios import (
    PARENT_NAME, PARENT_SHA256, CHILD_NAME as C00_NAME, relocate, sha,
)

C00_SHA256 = "a0b885031393bee3e2904d80a72139b0027621f0814e6323c639d30a35ff2715"
C00B_NAME = "BASE001_T070_G0_CONTACT_GROUPS_C00B_CHILD.inp"
NATIVE_L01_DAT_SHA256 = "60805bb07d8ccb5c5d922de57d910ab6417beed9dbe3d2ffb04b8c6efe7f8e57"

# Keep the preceding *CONTACT PROPERTY ASSIGNMENT's 30 explicit surface pairs
# and HJOINT_HARD_MU05_T057 property completely unchanged.
BLANK_BEFORE = b"** END T057 HORIZONTAL JOINT CONTACT\n\n** \n"
BLANK_AFTER = b"** END T057 HORIZONTAL JOINT CONTACT\n** \n"
OUTPUT_BEFORE = b"*Contact Output\nCPRESS,COPEN,CSHEAR1,CSHEAR2,CSLIP1,CSLIP2\n"
OUTPUT_AFTER = b"*Contact Output\nCSTRESS,CDISP,CFORCE\n"

# L01 native .dat contains 7 FATALS. The source DAT is read and hashed;
# these messages are not fabricated by a Python fixture.
L01_ERRORS = (
    "A blank data line cannot be specified under *CONTACT PROPERTY",
    "OUTPUT REQUEST CPRESS IS NOT AVAILABLE FOR THIS OPTION",
    "OUTPUT REQUEST COPEN IS NOT AVAILABLE FOR THIS OPTION",
    "OUTPUT REQUEST CSHEAR1 IS NOT AVAILABLE FOR THIS OPTION",
    "OUTPUT REQUEST CSHEAR2 IS NOT AVAILABLE FOR THIS OPTION",
    "OUTPUT REQUEST CSLIP1 IS NOT AVAILABLE FOR THIS OPTION",
    "OUTPUT REQUEST CSLIP2 IS NOT AVAILABLE FOR THIS OPTION",
)


def validate_native_l01(raw: bytes) -> None:
    if sha(raw) != NATIVE_L01_DAT_SHA256:
        raise ValueError("L01_NATIVE_DAT_SHA256_MISMATCH")
    text = raw.decode("utf-8", errors="replace")
    for msg in L01_ERRORS:
        if text.count(msg) != 1:
            raise ValueError("L01_NATIVE_ERROR_IDENTITY_MISMATCH: " + msg)
    if "7 FATAL ERRORS" not in text:
        raise ValueError("L01_NATIVE_FATAL_COUNT_MISMATCH")


def _pairs(data: bytes) -> tuple[tuple[bytes, ...], tuple[bytes, ...]]:
    start = b"*Contact Inclusions\n"
    mid = b"*Contact Property Assignment\n"
    end = b"** END T057 HORIZONTAL JOINT CONTACT\n"
    if any(data.count(x) != 1 for x in (start, mid, end)):
        raise ValueError("CONTACT_BLOCK_KEYWORD_IDENTITY")
    inclusion = data.split(start, 1)[1].split(mid, 1)[0].splitlines()
    assignments = data.split(mid, 1)[1].split(end, 1)[0].splitlines()
    if len(inclusion) != 30 or len(assignments) != 30:
        raise ValueError("CONTACT_PAIR_COUNT_NOT_30")
    for x, y in zip(inclusion, assignments):
        if y != x + b", HJOINT_HARD_MU05_T057":
            raise ValueError("CONTACT_PAIR_OR_PROPERTY_IDENTITY")
    return tuple(inclusion), tuple(assignments)


def repair(c00: bytes, *, require_sha: bool = True) -> tuple[bytes, dict]:
    if require_sha and sha(c00) != C00_SHA256:
        raise ValueError("C00_CHILD_SHA256_MISMATCH")
    before_pairs = _pairs(c00)
    if c00.count(BLANK_BEFORE) != 1 or c00.count(OUTPUT_BEFORE) != 1:
        raise ValueError("L01_EXACT_TWO_EDIT_ANCHORS_MISSING_OR_DUPLICATED")
    if c00.count(BLANK_AFTER) or c00.count(OUTPUT_AFTER):
        raise ValueError("C00B_ALREADY_APPLIED")
    c00b = c00.replace(BLANK_BEFORE, BLANK_AFTER, 1).replace(
        OUTPUT_BEFORE, OUTPUT_AFTER, 1
    )
    if _pairs(c00b) != before_pairs:
        raise AssertionError("CONTACT_PAIRS_CHANGED")
    if c00b.count(BLANK_AFTER) != 1 or c00b.count(OUTPUT_AFTER) != 1:
        raise AssertionError("C00B_OUTPUT_NOT_UNIQUE")
    inverse = c00b.replace(OUTPUT_AFTER, OUTPUT_BEFORE, 1).replace(
        BLANK_AFTER, BLANK_BEFORE, 1
    )
    if inverse != c00:
        raise AssertionError("C00B_EXACT_INVERSE_FAILED")
    if c00b.count(b"*End Assembly\n") != 1:
        raise AssertionError("ASSEMBLY_IDENTITY_CHANGED")
    if c00b.index(b"*Integrated Output Section") > c00b.index(b"*End Assembly\n"):
        raise AssertionError("IOS_REGRESSION")
    if c00b.count(b"*Surface Interaction, name=HJOINT_HARD_MU05_T057\n") != 1:
        raise AssertionError("CONTACT_PROPERTY_CHANGED")
    if c00b.count(b"*Friction\n0.5,\n") != 1:
        raise AssertionError("FRICTION_CHANGED")
    # The source DAT's empty data line is not an intentional blank
    # contact-property assignment. All 30 assignment rows remain.
    if b"\n\n" in c00b.split(b"*Contact Property Assignment\n", 1)[1].split(
        b"*Material,", 1
    )[0]:
        raise AssertionError("BLANK_CONTACT_DATA_REMAINS")
    a = c00.decode("utf-8").splitlines(keepends=True)
    b = c00b.decode("utf-8").splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(a, b, fromfile=C00_NAME,
                                        tofile=C00B_NAME, n=3))
    if diff.count("@@ ") != 2:
        raise AssertionError("UNEXPECTED_DIFF_HUNKS")
    receipt = {
        "schema": 1,
        "status": "C00B_STATIC_REPAIR_NATIVE_RECHECK_PENDING",
        "frozen_t070_name": PARENT_NAME,
        "frozen_t070_sha256": PARENT_SHA256,
        "c00_name": C00_NAME,
        "c00_sha256": sha(c00),
        "c00_bytes": len(c00),
        "c00b_name": C00B_NAME,
        "c00b_sha256": sha(c00b),
        "c00b_bytes": len(c00b),
        "c00b_inverse_sha256": sha(inverse),
        "exact_inverse_pass": inverse == c00,
        "contact_pairs_preserved": len(before_pairs[0]),
        "friction_mu_preserved": 0.5,
        "edits": [
            "remove exactly one empty data line after 30 CONTACT PROPERTY ASSIGNMENT rows",
            "replace 6 direct field component names by Standard general-contact CSTRESS,CDISP,CFORCE group keys",
        ],
        "expected_contact_output_groups": ["CSTRESS", "CDISP", "CFORCE"],
        "observability_limits": [
            "CSTRESS requests pressure/contact shear group; components depend on formulation",
            "CDISP requests COPEN/CSLIP group; values only where contact tracking reports",
            "CFORCE requests contact force group; verify actual ODB field keys in native run",
            "contact friction, opening and 30 pair identities unchanged",
        ],
        "diff_sha256": sha(diff.encode("utf-8")),
        "source_read_level": "full frozen parent bytes; actual L01 native DAT bytes; Abaqus 2025 keyword and Standard general-contact official documentation",
        "standard": "no authorized NB/T10907 or IEC/GB design clause validated",
        "ref": "no new paper full text",
        "official": [
            "https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-contactpropertyassignment.htm",
            "https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-contactoutput.htm",
            "https://docs.software.vt.edu/abaqusv2025/English/SIMACAEITNRefMap/simaitn-c-contactgeneralstd.htm",
        ],
        "run": "Python byte-level static verification; Abaqus 2025 C00b G0 NOT RUN",
        "fig": "none",
        "tab": "30 unchanged contact pair rows and two diff hunks",
        "assumptions": "Abaqus Standard accepts group keys for general contact; needs native recheck",
        "uncertainty": "byte inverse exact; parser and physical/contact errors NEED_ESTIMATE",
        "hold": "Abaqus 2025 native Data Check on C00b plus warning and ODB output inspection",
        "native_datacheck": "NOT_RUN_ON_C00B",
        "diff": diff,
    }
    return c00b, receipt


def self_test() -> None:
    pairs = [f"CSEG_{i:02d}-1.SURF_TOP, CSEG_{i+1:02d}-1.SURF_BOTTOM".encode()
             for i in range(1, 31)]
    inc = b"\n".join(pairs) + b"\n"
    ass = b"\n".join(x + b", HJOINT_HARD_MU05_T057" for x in pairs) + b"\n"
    fake = (b"*Assembly, name=Assembly\n"
            b"*Integrated Output Section, name=TEST\n*End Assembly\n"
            b"*Surface Interaction, name=HJOINT_HARD_MU05_T057\n"
            b"*Friction\n0.5,\n*Contact\n*Contact Inclusions\n" + inc
            + b"*Contact Property Assignment\n" + ass + BLANK_BEFORE
            + b"*Material, name=TEST\n"
            # Keep synthetic edits separated by > 2*n=6 context lines.
            # Real 16.6 MB input has two hunks; the short fixture formerly
            # merged them and falsely failed the two-hunk invariant.
            + (b"** C00b synthetic spacing only\n" * 10)
            + b"*Step\n" + OUTPUT_BEFORE
            + b"*End Step\n")
    out, m = repair(fake, require_sha=False)
    assert m["exact_inverse_pass"] and m["contact_pairs_preserved"] == 30
    assert out.count(OUTPUT_AFTER) == 1 and out.count(BLANK_AFTER) == 1
    assert m["diff_sha256"] == sha(m["diff"].encode())
    negatives = (
        fake + b"** physics tamper\n",
        fake.replace(BLANK_BEFORE, BLANK_AFTER),
        fake.replace(OUTPUT_BEFORE, OUTPUT_AFTER),
        fake.replace(b"*Contact Property Assignment\n",
                     b"*Contact Property Assignment\n\n"),
        fake.replace(b"CSEG_30-1.SURF_TOP, CSEG_31-1.SURF_BOTTOM,"
                     b" HJOINT_HARD_MU05_T057",
                     b"CSEG_30-1.SURF_TOP, CSEG_31-1.SURF_BOTTOM,"
                     b" WRONG_PROPERTY"),
        fake.replace(b"*Friction\n0.5,\n", b"*Friction\n0.6,\n"),
        fake + OUTPUT_BEFORE,
    )
    for n, bad in enumerate(negatives):
        try:
            repair(bad, require_sha=(n == 0))
        except (ValueError, AssertionError):
            pass
        else:
            raise AssertionError(f"negative test {n} accepted")
    print("C00B_SYNTHETIC_PASS 4 positive + 7 negative; NOT ABAQUS")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--parent", type=Path)
    ap.add_argument("--native-dat", type=Path)
    ap.add_argument("--outdir", type=Path)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.parent or not args.native_dat or not args.outdir:
        ap.error("require --parent --native-dat --outdir")
    native_raw = args.native_dat.read_bytes()
    validate_native_l01(native_raw)
    c00, _ = relocate(args.parent.read_bytes())
    child, manifest = repair(c00)
    manifest["l01_native_dat_sha256"] = sha(native_raw)
    manifest["l01_native_error_count"] = 7
    manifest["l01_native_error_messages"] = list(L01_ERRORS)
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / C00B_NAME).write_bytes(child)
    (args.outdir / "C00B_L01_CONTACT_REPAIR_MANIFEST.json").write_text(
        json.dumps({k: v for k, v in manifest.items() if k != "diff"},
                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (args.outdir / "C00B_L01_CONTACT_REPAIR.patch").write_text(
        manifest["diff"], encoding="utf-8"
    )
    print("C00B_STATIC_CHILD_READY_NATIVE_RECHECK_PENDING")
    print(json.dumps({k: manifest[k] for k in (
        "frozen_t070_sha256", "c00_sha256", "c00b_sha256", "c00b_bytes",
        "exact_inverse_pass", "contact_pairs_preserved",
        "l01_native_dat_sha256", "diff_sha256"
    )}, indent=2))


if __name__ == "__main__":
    main()
