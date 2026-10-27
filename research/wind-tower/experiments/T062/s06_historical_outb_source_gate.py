#!/usr/bin/env python3
"""Read-only SHA-pinned OpenFAST .outb source/channel inventory; NOT a physics RUN.

This checks one archived original OpenFAST file from the independent T062/36-case
archive, not the 16 T071/T072 derived CSV ZIPs. Python 3.11+ stdlib only.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile


def exact(stream, size):
    data = stream.read(size)
    if len(data) != size:
        raise ValueError(f"truncated OUTB header: expected {size}, got {len(data)}")
    return data


def unpack(stream, fmt):
    return struct.unpack("<" + fmt, exact(stream, struct.calcsize("<" + fmt)))


def outb_header(raw):
    f = io.BytesIO(raw)
    file_id = unpack(f, "h")[0]
    if file_id not in (1, 2, 3, 4):
        raise ValueError(f"unsupported OpenFAST FileID={file_id}")
    name_length = unpack(f, "h")[0] if file_id == 4 else 10
    n_channels, n_samples = unpack(f, "ii")
    if not (1 <= name_length <= 256 and 1 <= n_channels <= 4096 and 1 <= n_samples <= 10_000_000):
        raise ValueError("invalid OpenFAST header dimensions")
    first, second = unpack(f, "dd")
    # FileID=1 stores packed-time scale/offset, not first time/time increment.
    scales = unpack(f, "f" * n_channels)
    offsets = unpack(f, "f" * n_channels)
    description_length = unpack(f, "i")[0]
    if not (0 <= description_length <= 1_000_000):
        raise ValueError("invalid description length")
    description = exact(f, description_length).decode("utf-8", errors="replace")
    def names():
        return [exact(f, name_length).decode("ascii", errors="replace").replace("\x00", "").strip()
                for _ in range(n_channels + 1)]
    channel_names, units = names(), names()
    if len(set(channel_names)) != len(channel_names):
        raise ValueError("duplicate OpenFAST output channel names")
    data_offset = f.tell()
    expected_payload = n_samples * (2 * n_channels + (4 if file_id == 1 else 0))
    remaining = len(raw) - data_offset
    if remaining != expected_payload:
        raise ValueError(f"packed payload size mismatch: {remaining} vs {expected_payload}")
    return {
        "file_id": file_id, "num_output_channels": n_channels,
        "num_samples": n_samples,
        "first_time_s": first if file_id != 1 else None,
        "time_increment_s": second if file_id != 1 else None,
        "packed_time_scale_offset": [first, second] if file_id == 1 else None,
        "description_excerpt": description[:160],
        "channel_names": channel_names,
        "channel_units": units,
        "column_scales": scales,
        "column_offsets": offsets,
        "data_offset_bytes": data_offset,
        "packed_payload_bytes": remaining,
    }


def selected_samples(raw, header, channel_names, units, scales, offsets):
    """Decode three synchronous ORIGINAL packed-data instants, not a physics load map."""
    if header["file_id"] == 1:
        raise ValueError("FileID=1 packed-time layout requires separate decoder")
    selected = ([f"TwrBs{s}" for s in ("Fxt", "Fyt", "Fzt", "Mxt", "Myt", "Mzt")]
                + [f"TwHt{g}{s}" for g in (1, 9)
                   for s in ("FLxt", "FLyt", "FLzt", "MLxt", "MLyt", "MLzt",
                             "TPxi", "TPyi", "TPzi", "RPxi", "RPyi", "RPzi",
                             "ALxt", "ALyt", "ALzt")])
    if any(name not in channel_names for name in selected):
        raise ValueError("selected original channels missing")
    indices = {name: channel_names.index(name) - 1 for name in selected}
    n = header["num_output_channels"]
    nt = header["num_samples"]
    first, dt = header["first_time_s"], header["time_increment_s"]
    if dt <= 0 or first is None:
        raise ValueError("invalid output time grid")
    rows = []
    for tindex in sorted({0, nt // 2, nt - 1}):
        base = header["data_offset_bytes"] + tindex * n * 2
        values = {}
        for name, i in indices.items():
            scale = scales[i]
            if scale == 0:
                raise ValueError(f"zero packed scale for {name}")
            packed = struct.unpack_from("<h", raw, base + 2*i)[0]
            value = (packed - offsets[i]) / scale
            if not (-1e30 < value < 1e30):
                raise ValueError(f"nonfinite/unreasonable decoded value for {name}")
            values[name] = {"value": round(value, 9), "unit": units[i+1]}
        rows.append({"sample_index": tindex, "time_s": round(first + dt*tindex, 9),
                     "channels": values})
    return rows


def audit(zip_path, manifest_path, case, full_csv_gz=None, previous_receipt=None):
    entries = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    matches = [e for e in entries if e.get("relative_path") ==
               f"CASES/{case}/DTU_10MW_RWT.outb" and e.get("section") == "openfast-36-r2"]
    if len(matches) != 1:
        raise ValueError(f"expected one original OUTB manifest entry, found {len(matches)}")
    expected = matches[0]
    zip_name = expected["archive"].split("/")[-1]
    if Path(zip_path).name != zip_name:
        raise ValueError("archive filename disagrees with manifest")
    zbytes = Path(zip_path).read_bytes()
    with zipfile.ZipFile(io.BytesIO(zbytes)) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"archive CRC failure: {bad}")
        if expected["relative_path"] not in archive.namelist():
            raise ValueError("original OUTB member not present")
        raw = archive.read(expected["relative_path"])
    outb_sha = hashlib.sha256(raw).hexdigest()
    if outb_sha.lower() != expected["sha256"].lower():
        raise ValueError("original OUTB SHA256 differs from archival manifest")
    if len(raw) != expected["bytes"]:
        raise ValueError("original OUTB byte count differs from archival manifest")
    h = outb_header(raw)
    channel_names = h.pop("channel_names")
    names = set(channel_names)
    units = h.pop("channel_units")
    scales = h.pop("column_scales")
    offsets = h.pop("column_offsets")
    samples = selected_samples(raw, h, channel_names, units, scales, offsets)
    full_result = (full_synchronous_series(raw, h, channel_names, units, scales, offsets,
                   full_csv_gz, previous_receipt) if full_csv_gz is not None else None)
    required = [f"TwHt1{s}" for s in
                ("FLxt", "FLyt", "FLzt", "MLxt", "MLyt", "MLzt",
                 "TPxi", "TPyi", "TPzi", "RPxi", "RPyi", "RPzi",
                 "ALxt", "ALyt", "ALzt")]
    required += [f"TwrBs{s}" for s in ("Fxt", "Fyt", "Fzt", "Mxt", "Myt", "Mzt")]
    gages = [g for g in range(1, 32)
             if all(f"TwHt{g}{s}" in names for s in
                    ("FLxt", "FLyt", "FLzt", "MLxt", "MLyt", "MLzt"))]
    motion_gages = [g for g in range(1, 32)
                    if all(f"TwHt{g}{s}" in names for s in
                           ("TPxi", "TPyi", "TPzi", "RPxi", "RPyi", "RPzi",
                            "ALxt", "ALyt", "ALzt"))]
    return {
        "status": "SOURCE_HEADER_QC_ONLY_NOT_DYNAMIC_PHYSICS_PASS",
        "full_synchronous_native_series": full_result,
        "case": case,
        "archive_path": expected["canonical_archive"],
        "archive_sha256": hashlib.sha256(zbytes).hexdigest(),
        "archive_size_bytes": len(zbytes),
        "outb_member": expected["relative_path"],
        "outb_sha256": outb_sha,
        "outb_size_bytes": len(raw),
        "source_manifest_sha256": hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest(),
        "source_reading_level": ("original archived OUTB bytes: SHA256 + complete 12001x141 native-channel time series, three-instant parity and per-channel QC" if full_result is not None else "original archived OUTB bytes: SHA256 + binary header/channel names + three synchronous decoded packed-data samples"),
        "header": h,
        "required_21_channel_presence": {c: c in names for c in required},
        "full_six_component_gage_indices": gages,
        "full_position_rotation_acceleration_gage_indices": motion_gages,
        "first_30_channel_names": sorted(names)[:30],
        "selected_original_synchronous_samples": samples,
        "time_unit": next((units[i] for i, name in enumerate(["Time"] + list(names)) if name == "Time"), "not independently verified"),
        "hold": "Original 36-case archive is not proven identical to T071/T072 31-gage reruns; 9 gages are not 31; RP angles require OpenFAST frame/order/sign validation; load ownership and native Abaqus remain unverified.",
    }



def full_synchronous_series(raw, h, names, units, scales, offsets, csv_gz_path,
                            previous_receipt_path=None):
    """All 12001 instants: nine gages' native FL/ML/TP/RP/AL + tower-base wrench.

    IMPORTANT: RP angles remain native OpenFAST OUTPUT values; they are NOT
    interpreted as an Euler rotation matrix. The CSV is NOT an Abaqus load.
    """
    import csv
    import gzip
    import math
    suffixes = ("FLxt", "FLyt", "FLzt", "MLxt", "MLyt", "MLzt",
                "TPxi", "TPyi", "TPzi", "RPxi", "RPyi", "RPzi",
                "ALxt", "ALyt", "ALzt")
    base = tuple("TwrBs" + x for x in ("Fxt", "Fyt", "Fzt", "Mxt", "Myt", "Mzt"))
    selected = base + tuple("TwHt" + str(g) + s for g in range(1, 10) for s in suffixes)
    if h["file_id"] != 4:
        raise ValueError("full synchronous export requires verified FileID=4")
    if len(names) != h["num_output_channels"] + 1 or names[0] != "Time":
        raise ValueError("invalid time/channel index")
    if len(set(names)) != len(names) or any(c not in names for c in selected):
        raise ValueError("missing or duplicate full-series channel")
    if h["num_samples"] != 12001 or abs(h["first_time_s"] - 100.0) > 1e-10 or abs(h["time_increment_s"] - 0.05) > 1e-12:
        raise ValueError("source is not the expected 12001-point 100-700 s time grid")
    expected_units = {}
    for c in selected:
        if c.startswith("TwrBs"):
            expected_units[c] = "(kN-m)" if "M" in c[5:] else "(kN)"
        elif "FL" in c:
            expected_units[c] = "(kN)"
        elif "ML" in c:
            expected_units[c] = "(kN-m)"
        elif "TP" in c:
            expected_units[c] = "(m)"
        elif "RP" in c:
            expected_units[c] = "(deg)"
        else:
            expected_units[c] = "(m/s^2)"
    for c in selected:
        if units[names.index(c)] != expected_units[c]:
            raise ValueError("unexpected unit for " + c + ": " + units[names.index(c)])
    idx = [names.index(c) - 1 for c in selected]
    if any(scales[i] == 0 or not math.isfinite(scales[i]) or not math.isfinite(offsets[i]) for i in idx):
        raise ValueError("invalid packed-data scale/offset")
    sums = [0.0] * len(selected)
    sumsq = [0.0] * len(selected)
    lows = [math.inf] * len(selected)
    highs = [-math.inf] * len(selected)
    first_values = last_values = None
    parity = {}
    prior = None
    if previous_receipt_path is not None:
        prior = json.loads(Path(previous_receipt_path).read_text(encoding="utf-8"))
        if prior.get("outb_sha256") != hashlib.sha256(raw).hexdigest():
            raise ValueError("three-instant source receipt SHA mismatch")
        parity = {int(x["sample_index"]): x["channels"] for x in prior["selected_original_synchronous_samples"]}
        if set(parity) != {0, 6000, 12000}:
            raise ValueError("unexpected three-instant parity indices")
    # gzip mtime=0 ensures stable output bytes for the same Python/zlib environment.
    with Path(csv_gz_path).open("wb") as binary:
        with gzip.GzipFile(filename="", mode="wb", fileobj=binary, compresslevel=6, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as txt:
                writer = csv.writer(txt, lineterminator="\n")
                writer.writerow(("time_s",) + selected)
                for k in range(h["num_samples"]):
                    pos = h["data_offset_bytes"] + k * 2 * h["num_output_channels"]
                    packed = struct.unpack_from("<" + "h" * h["num_output_channels"], raw, pos)
                    vals = [(packed[i] - offsets[i]) / scales[i] for i in idx]
                    if not all(math.isfinite(v) for v in vals):
                        raise ValueError("nonfinite decoded full-series value")
                    t = h["first_time_s"] + k * h["time_increment_s"]
                    if k in parity:
                        for name, obj in parity[k].items():
                            if name not in selected:
                                continue
                            actual = vals[selected.index(name)]
                            # Previous receipt rounded to 9 decimal places.
                            if abs(actual - float(obj["value"])) > 5.1e-10:
                                raise ValueError("three-instant real-source parity failure: " + name)
                    writer.writerow((f"{t:.9f}",) + tuple(f"{v:.9f}" for v in vals))
                    if k == 0:
                        first_values = vals[:]
                    last_values = vals[:]
                    for j, v in enumerate(vals):
                        sums[j] += v
                        sumsq[j] += v*v
                        lows[j] = min(lows[j], v)
                        highs[j] = max(highs[j], v)
    n = h["num_samples"]
    summary = {}
    for j, name in enumerate(selected):
        mean = sums[j] / n
        rms = math.sqrt(sumsq[j] / n)
        summary[name] = {
            "unit": expected_units[name], "min": round(lows[j], 9),
            "max": round(highs[j], 9), "mean": round(mean, 9),
            "rms": round(rms, 9), "first": round(first_values[j], 9),
            "last": round(last_values[j], 9)
        }
    z_at_first = [summary[f"TwHt{g}TPzi"]["first"] for g in range(1, 10)]
    z_span = max(z_at_first) - min(z_at_first)
    return {
        "status": "FULL_ORIGINAL_SYNCHRONOUS_NATIVE_CHANNEL_QC_NOT_FRAME_OR_PHYSICS_PASS",
        "observed_TPzi_first_m_by_gage": z_at_first,
        "observed_TPzi_span_m": round(z_span, 9),
        "coverage_warning": "Native TPzi gage positions span only %.6f m in this OUTB; this 9-gage history must NOT be treated as full 158-m tower coverage until original TwrGagNd and TowerHt inputs are independently recovered." % z_span,
        "source_outb_sha256": hashlib.sha256(raw).hexdigest(),
        "sample_count": n, "gage_count": 9, "selected_channel_count": len(selected),
        "channel_value_count": n * len(selected),
        "time_start_s": h["first_time_s"],
        "time_end_s": h["first_time_s"] + (n-1)*h["time_increment_s"],
        "time_increment_s": h["time_increment_s"],
        "gzip_csv_sha256": hashlib.sha256(Path(csv_gz_path).read_bytes()).hexdigest(),
        "gzip_csv_size_bytes": Path(csv_gz_path).stat().st_size,
        "three_instant_parity": "PASS" if prior is not None else "NOT_CHECKED",
        "native_channel_summary": summary,
        "hold": "RP degrees not independently proven to be an Euler orientation; no global frame conversion, free-body decomposition, external Abaqus load, 31-gage equivalence, material stress or seismic solver PASS."
    }


def self_test():
    def fixed(s, n=10):
        return s.encode("ascii").ljust(n, b" ")
    n, nt = 3, 2
    raw = (struct.pack("<hii", 2, n, nt) + struct.pack("<dd", 100.0, 0.05)
           + struct.pack("<" + "f" * (2*n), *([1.0] * n + [0.0] * n))
           + struct.pack("<i", 4) + b"test"
           + b"".join(fixed(x) for x in ("Time", "A", "B", "C"))
           + b"".join(fixed(x) for x in ("(s)", "(kN)", "(m)", "(deg)"))
           + bytes(nt * n * 2))
    result = outb_header(raw)
    assert result["num_samples"] == 2 and result["num_output_channels"] == 3
    assert abs(result["time_increment_s"] - 0.05) < 1e-12
    try:
        outb_header(raw[:-1])
    except ValueError as e:
        assert "payload" in str(e)
    else:
        raise AssertionError("truncated binary payload was accepted")
    try:
        outb_header(b"\xff\xff" + raw[2:])
    except ValueError as e:
        assert "FileID" in str(e)
    else:
        raise AssertionError("invalid FileID was accepted")
    assert result["channel_names"] == ["Time", "A", "B", "C"]
    assert result["column_scales"] == (1.0, 1.0, 1.0)
    print("PASS: synthetic OpenFAST header, truncation rejection, invalid FileID rejection")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--zip-path", type=Path)
    p.add_argument("--manifest", type=Path)
    p.add_argument("--case", default="U09p343881_ETM_S01")
    p.add_argument("--output", type=Path)
    p.add_argument("--full-series-gzip", type=Path, help="12001 x 9 native-gage synchronous series; NOT an external load")
    p.add_argument("--previous-receipt", type=Path, help="SHA-bound three-instant source parity regression")
    args = p.parse_args()
    if args.self_test:
        self_test()
    if args.zip_path:
        if args.manifest is None:
            p.error("--manifest required with --zip-path")
        result = audit(args.zip_path, args.manifest, args.case,
                       args.full_series_gzip, args.previous_receipt)
        serialized = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(serialized, encoding="utf-8")
        print(serialized)


if __name__ == "__main__":
    main()
