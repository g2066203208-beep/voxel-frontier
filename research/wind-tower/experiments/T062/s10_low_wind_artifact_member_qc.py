#!/usr/bin/env python3
"""Verify archived GitHub Actions artifact ZIP members; no solver or DLC claim.

Usage: python s10_low_wind_artifact_member_qc.py ORIGINAL_SERIES_ZIP NTM_DEL_ZIP CONTROLLER_ZIP
"""
import csv
import gzip
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

EXPECTED = (
    ("1592cfcf36c2ac1b4850008e8d3d5af049d408f52944dc2dfdab728024a19de6", 3),
    ("efb73c935440e4545d16724e5191a2b79a25cc76e5a2acf987fa048ea9f3f82a", 5),
    ("5320dc6f983aad81305933d91438fd416cd57bbe26a6b9ca81de9220fa2ca9a5", 8),
)
SPEEDS = ("U09p343881", "U11p4", "U19p202140")
SEEDS = tuple(f"S{i:02d}" for i in range(1, 7))
EXPECTED_CASES = {f"{u}_NTM_{s}" for u in SPEEDS for s in SEEDS}


def require_cases(cases):
    cases = set(cases)
    if cases != EXPECTED_CASES:
        raise ValueError(f"NTM_CASE_IDENTITY_MISMATCH missing={sorted(EXPECTED_CASES-cases)} extra={sorted(cases-EXPECTED_CASES)}")


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def main(paths):
    if len(paths) != 3:
        raise ValueError("EXPECTED_THREE_ZIP_PATHS")
    zs, metadata = [], []
    for path, (expected_sha, expected_members) in zip(paths, EXPECTED):
        b = Path(path).read_bytes()
        if sha256(b) != expected_sha:
            raise ValueError("ZIP_SHA256_MISMATCH " + str(path))
        z = zipfile.ZipFile(io.BytesIO(b))
        if z.testzip() is not None or len(z.namelist()) != expected_members:
            raise ValueError("ZIP_CRC_OR_MEMBER_COUNT")
        metadata.append({"artifact_zip_sha256": sha256(b), "zip_bytes": len(b), "member_count": len(z.namelist()), "crc": "PASS", "members": z.namelist()})
        zs.append(z)
    series, ntm, controller = zs
    receipt = json.loads(series.read("S06_T062_ORIGINAL_OUTB_CHANNEL_RECEIPT.json"))
    geometry = json.loads(series.read("S06_T062_ORIGINAL_GAGE_GEOMETRY_RECEIPT.json"))
    if receipt["case"] != "U09p343881_ETM_S01" or geometry["NTwGages"] != 9:
        raise ValueError("SERIES_IS_NOT_IDENTIFIED_ETM_9GAGE")
    gz = series.read("S06_T062_9GAGE_FULL_NATIVE_SERIES.csv.gz")
    if sha256(gz) != receipt["full_synchronous_native_series"]["gzip_csv_sha256"]:
        raise ValueError("GZIP_MEMBER_SHA256_MISMATCH")
    with gzip.GzipFile(fileobj=io.BytesIO(gz)) as stream:
        rows = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8", newline=""))
        count = 0
        first = last = None
        for row in rows:
            t = float(row["time_s"])
            if count == 0:
                first = t
            last = t
            count += 1
    if count != 12001 or first != 100.0 or last != 700.0:
        raise ValueError("ETM_NATIVE_TIME_WINDOW_MISMATCH")
    del_rows = list(csv.DictReader(io.StringIO(ntm.read("S06_18NTM_ORIGINAL_9GAGE_LOAD_DEL_20261031.csv").decode("utf-8-sig"))))
    ctrl_rows = list(csv.DictReader(io.StringIO(controller.read("S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv").decode("utf-8-sig"))))
    require_cases(x["case"] for x in del_rows)
    require_cases(x["case"] for x in ctrl_rows)
    if len(del_rows) != 1080 or len(ctrl_rows) != 18:
        raise ValueError("NTM_ROW_COUNT_MISMATCH")
    negatives = 0
    for fake in [set(), EXPECTED_CASES | {"U04p5_NTM_S01"}, EXPECTED_CASES - {"U11p4_NTM_S03"}]:
        try:
            require_cases(fake)
        except ValueError:
            negatives += 1
    if negatives != 3:
        raise AssertionError("NEGATIVE_REJECTION_FAILED")
    return {"artifact_metadata": metadata, "source_case": receipt["case"],
            "source_original_outb_sha256_inherited": receipt["outb_sha256"],
            "series_gzip_sha256": sha256(gz), "series_samples": count,
            "series_t0_s": first, "series_t1_s": last,
            "gage_z_span_m": geometry["observed_gage_z_span_m"],
            "ntm_del_rows": len(del_rows), "controller_rows": len(ctrl_rows),
            "ntm_cases": sorted(EXPECTED_CASES), "verified_4_to_8_mps_ntm_cases_in_these_artifacts": 0,
            "negative_rejections": negatives, "scope": "Three downloaded Actions artifacts only; ETM != NTM; nine near-base gages != 31 full tower segments; no BTS/OUTB recovered for 4-8m/s."}


if __name__ == "__main__":
    try:
        print(json.dumps(main(sys.argv[1:]), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as exc:
        print("SOURCE_ARTIFACT_QC_HOLD", str(exc), file=sys.stderr)
        sys.exit(2)
