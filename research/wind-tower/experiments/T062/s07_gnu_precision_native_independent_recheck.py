#!/usr/bin/env python3
"""Independent reparse of original GNU single/double 2s OUTB against saved 295-row tables.
No Abaqus, OpenFAST invocation, or DLC1.2 production. Python >=3.10 stdlib.
Run: python s07_gnu_precision_native_independent_recheck.py --single single.zip
     --double double.zip --csv S07_GNU_PRECISION_2S_295_CHANNELS.csv
     --json S07_GNU_PRECISION_ORIGINAL_ARTIFACT_2S_295CH_NUMERIC_QC.json --out receipt.json
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import struct
import zipfile
from pathlib import Path

ZIP_SHA = {
    "single": "983bce8ca81981ff5fd00e5261dbfb2c0b6e18b074aa4eb1ff425e6851fb9735",
    "double": "d8a5dec02b3dc4b536061f5bfcfd80e3bd472f322e83c5e7b1ee705508017c7c",
}
OUTB_SHA = {
    "single": "d0ac71b498b2764587a91b8523bbd72c9dad84a48a1b632e0b1922a3470e3c39",
    "double": "be43d3ad2a278fbd1afe91753382d681f5eb2d8c8b401ccd78d23eb5765136c8",
}
SIX = ("TwrBsFxt", "TwrBsFyt", "TwrBsFzt", "TwrBsMxt", "TwrBsMyt", "TwrBsMzt")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def parse_native_outb(raw):
    f = io.BytesIO(raw)

    def take(fmt):
        size = struct.calcsize("<" + fmt)
        b = f.read(size)
        require(len(b) == size, "TRUNCATED_OUTB_HEADER")
        return struct.unpack("<" + fmt, b)

    file_id, = take("h")
    name_len, = take("h")
    channels, samples = take("ii")
    t0, dt = take("dd")
    require((file_id, channels, samples) == (4, 295, 41), "OUTB_FORMAT_OR_DIMENSION_HOLD")
    require(1 <= name_len <= 256 and abs(t0) < 1e-10 and abs(dt - .05) < 1e-10,
            "OUTB_TIME_GRID_HOLD")
    scale = take("f" * channels)
    offset = take("f" * channels)
    desc_len, = take("i")
    require(0 <= desc_len <= 1000000, "OUTB_DESCRIPTION_LENGTH_HOLD")
    require(len(f.read(desc_len)) == desc_len, "OUTB_DESCRIPTION_TRUNCATED")
    names, units = [], []
    for target in (names, units):
        for _ in range(channels + 1):
            b = f.read(name_len)
            require(len(b) == name_len, "OUTB_CHANNEL_NAME_TRUNCATED")
            target.append(b.decode("ascii").replace("\x00", "").strip())
    payload = f.read()
    require(len(payload) == 2 * channels * samples, "OUTB_PAYLOAD_LENGTH_HOLD")
    packed = struct.unpack("<" + "h" * (channels * samples), payload)
    values, half_lsb, unit_map = {}, {}, {}
    for j, name in enumerate(names[1:]):
        require(math.isfinite(scale[j]) and scale[j] != 0, "OUTB_SCALE_HOLD")
        values[name] = [(packed[i * channels + j] - offset[j]) / scale[j]
                        for i in range(samples)]
        half_lsb[name] = .5 / abs(scale[j])
        unit_map[name] = units[j + 1]
    require(len(values) == channels, "DUPLICATE_CHANNEL_HOLD")
    return values, half_lsb, unit_map


def load_zip(path, label):
    raw = path.read_bytes()
    require(sha(raw) == ZIP_SHA[label], "ZIP_SHA256_HOLD_" + label)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        require(z.testzip() is None, "ZIP_CRC_HOLD_" + label)
        outb = gzip.decompress(z.read("s07_linux_native_2s.outb.gz"))
        require(sha(outb) == OUTB_SHA[label], "OUTB_SHA256_HOLD_" + label)
        stdout = z.read("s07_linux_native_stdout.log")
        require(b"OpenFAST terminated normally." in stdout and
                b"Running ROSCO-v2.6.0" in stdout, "NATIVE_LOG_HOLD_" + label)
        cache = z.read("s07_openfast_cmake_cache.txt")
        flag = b"OFF" if label == "single" else b"ON"
        require(b"DOUBLE_PRECISION:BOOL=" + flag in cache, "CMAKE_PRECISION_HOLD_" + label)
        identity = json.loads(z.read("s07_linux_derived_identity.json"))
        port = json.loads(z.read("s07_linux_path_port_receipt.json"))
        source_hashes = z.read("s07_native_input_hashes.log")
    return parse_native_outb(outb), (identity, port, source_hashes)


def audit(single_zip, double_zip, csv_path, json_path):
    (a, aq, au), sa = load_zip(single_zip, "single")
    (b, bq, bu), sb = load_zip(double_zip, "double")
    require(set(a) == set(b) and au == bu, "CHANNEL_UNIT_IDENTITY_HOLD")
    for key in ("source_servo_sha256", "derived_linux_servo_sha256",
                "source_controller_sha256", "linux_controller_sha256"):
        require(sa[0][key] == sb[0][key], "SOURCE_IDENTITY_HOLD_" + key)
    require(sa[1:] == sb[1:], "SOURCE_PORT_OR_PATCH_HASH_HOLD")
    saved = json.loads(json_path.read_text(encoding="utf-8"))
    with csv_path.open(newline="", encoding="utf-8") as f:
        csv_rows = {r["channel"]: r for r in csv.DictReader(f)}
    json_rows = {r["channel"]: r for r in saved["rows"]}
    require(set(a) == set(csv_rows) == set(json_rows), "295_SAVED_CHANNELS_HOLD")
    counts = [0] * 41
    comparisons = 0
    fields = ("max_abs_delta", "rms_delta", "mean_delta", "quantization_budget",
              "exceed_count", "first_exceed_s", "delta_t0", "delta_t2")
    for name in sorted(a):
        delta = [x - y for x, y in zip(a[name], b[name])]
        require(len(delta) == 41 and all(math.isfinite(x) for x in delta),
                "NONFINITE_OR_LENGTH_HOLD")
        budget = 1.1 * (aq[name] + bq[name]) + 1e-8
        flags = [abs(x) > budget for x in delta]
        counts = [x + int(y) for x, y in zip(counts, flags)]
        actual = {
            "max_abs_delta": max(map(abs, delta)),
            "rms_delta": math.sqrt(sum(x*x for x in delta)/41),
            "mean_delta": sum(delta)/41,
            "quantization_budget": budget,
            "exceed_count": sum(flags),
            "first_exceed_s": next((round(i*.05, 10) for i, x in enumerate(flags) if x), None),
            "delta_t0": delta[0],
            "delta_t2": delta[-1],
        }
        for row in (csv_rows[name], json_rows[name]):
            require(row["unit"] == au[name], "UNIT_MISMATCH_" + name)
            for field in fields:
                observed = row[field]
                if observed == "" or observed is None:
                    observed = None
                elif field == "exceed_count":
                    observed = int(observed)
                else:
                    observed = float(observed)
                expected = actual[field]
                if expected is None or observed is None:
                    require(expected is None and observed is None,
                            "FIRST_EXCEED_MISMATCH_" + name)
                else:
                    require(abs(expected-observed) <= max(1e-11, 1e-10*abs(expected)),
                            "SAVED_NUMERIC_MISMATCH_" + name + "_" + field)
                comparisons += 1
    require(counts == saved["exceeding_channels_by_time"], "41_TIME_COUNTS_HOLD")
    require(sum(counts) == saved["quantization_exceeding_samples"] == 10284,
            "TOTAL_EXCEED_COUNT_HOLD")
    require(sum(row["exceed_count"] > 0 for row in json_rows.values()) ==
            saved["quantization_exceeding_channels"] == 266, "CHANNEL_EXCEED_HOLD")
    t0 = sorted(name for name in a if abs(a[name][0] - b[name][0]) >
                1.1 * (aq[name] + bq[name]) + 1e-8)
    require(t0 == sorted(saved["t0_exceeding_channels"]) and len(t0) == 21,
            "T0_CHANNEL_SET_HOLD")
    return {
        "stage": "S07",
        "status": "NATIVE_OUTB_INDEPENDENT_REPARSE_SAVED_TABLE_MATCH_NOT_PHYSICS_PASS",
        "SOURCE": {"reading_level": "TWO_ACTUAL_NATIVE_GITHUB_ACTIONS_ZIP_AND_OUTB_BYTES",
                   "actions_run": 41632768388, "zip_sha256": ZIP_SHA, "outb_sha256": OUTB_SHA,
                   "csv_sha256": sha(csv_path.read_bytes()),
                   "json_sha256": sha(json_path.read_bytes())},
        "REF": "Existing T062 source; no new paper full-text reading",
        "STANDARD": "No authorized IEC/GB/NB original clause read",
        "OFFICIAL": "OpenFAST v3.5.3 and ROSCO v2.6.0 native stdout/CMake",
        "RUN": "Read-only Python standard-library native OUTB reparse, no new solver",
        "FIG": "0", "TAB": "295 rows, eight fields per row, CSV and JSON, 41 time counts",
        "assumptions": "Same derived ServoDyn and controller binary hashes; single/double OpenFAST build",
        "error_budget": "1.1*(sum of packed OUTB half-LSB)+1e-8 is encoding only; "
                        "saved metric comparison tolerance max(1e-11,1e-10*abs(value))",
        "failure_record": "Original Actions workflow failed after native solver, paired job skipped; "
                          "single DCM inertia/gravity ownership remains HOLD",
        "HOLD": "No inertial load ownership or validated DLC1.2, fatigue, or seismic physical PASS",
        "physical_pass": False, "stage_pass_count": "0/12",
        "native_crc_pass": True, "paired_source_sha_pass": True,
        "compared_channels": len(a), "numeric_field_comparisons": comparisons,
        "exceeding_pairs": sum(counts), "t0_exceeding_channels": len(t0),
        "time_counts_match": True,
        "six_component_max_abs_delta": {k: json_rows[k]["max_abs_delta"] for k in SIX},
    }


def main():
    p = argparse.ArgumentParser()
    for arg in ("single", "double", "csv", "json", "out"):
        p.add_argument("--" + arg, required=True, type=Path)
    args = p.parse_args()
    result = audit(args.single, args.double, args.csv, args.json)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": result["status"], "compared_channels": result["compared_channels"],
                      "numeric_field_comparisons": result["numeric_field_comparisons"],
                      "exceeding_pairs": result["exceeding_pairs"],
                      "t0_exceeding_channels": result["t0_exceeding_channels"],
                      "physical_pass": False}, sort_keys=True))


if __name__ == "__main__":
    main()
