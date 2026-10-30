#!/usr/bin/env python3
"""S06 original 18 NTM OUTB: SHA-locked 9-gage/base load rainflow.
Postprocesses EXISTING 36-case OpenFAST outputs; no solver run, no Abaqus,
no DLC1.2 certification, no 31-gage equivalence, no material life.
Python 3.11+ standard library only.
"""
import argparse
from array import array
from collections import deque
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import zipfile

from s06_historical_outb_source_gate import outb_header

BASE = ("Fxt", "Fyt", "Fzt", "Mxt", "Myt", "Mzt")
GAGE = ("FLxt", "FLyt", "FLzt", "MLxt", "MLyt", "MLzt")
CASES = tuple(f"{u}_NTM_S{s:02d}"
              for u in ("U09p343881", "U11p4", "U19p202140")
              for s in range(1, 7))
FIELDS = ("case", "source_archive", "outb_sha256", "channel", "unit",
          "n_samples", "t0_s", "t1_s", "dt_s", "mean", "min", "max",
          "std", "rainflow_equivalent_cycles", "DEL_m4_Nref600",
          "DEL_m10_Nref600", "quantization_half_step_unit")
NREF = 600.0

def sha(b):
    return hashlib.sha256(b).hexdigest()

def reversals(x):
    if len(x) < 2 or not all(math.isfinite(v) for v in x):
        raise ValueError("NONFINITE_OR_SHORT_SERIES")
    y = [x[0]]
    for v in x[1:]:
        if v != y[-1]:
            y.append(v)
    if len(y) == 1:
        return y
    return [y[0]] + [y[i] for i in range(1, len(y)-1)
                      if (y[i]-y[i-1])*(y[i+1]-y[i]) < 0] + [y[-1]]

def rainflow(x):
    q, cycles = deque(), []
    turns = reversals(x)
    for v in turns:
        q.append(v)
        while len(q) >= 3:
            a, b = abs(q[-2]-q[-3]), abs(q[-1]-q[-2])
            if a > b:
                break
            if len(q) == 3:
                if a > 0:
                    cycles.append((a, .5))
                q.popleft()
            else:
                if a > 0:
                    cycles.append((a, 1.))
                q[-3] = q[-1]
                q.pop()
                q.pop()
    while len(q) > 1:
        a = abs(q[1]-q[0])
        if a > 0:
            cycles.append((a, .5))
        q.popleft()
    if abs(math.fsum(n for _, n in cycles) - (len(turns)-1)/2) > 1e-7:
        raise ValueError("RAINFLOW_CYCLE_CONSERVATION")
    return cycles

def self_test():
    assert rainflow([0,1,0]) == [(1,.5),(1,.5)]
    assert rainflow([0,3,1,2,0]) == [(1,1.),(3,.5),(3,.5)]
    assert rainflow([4,4,4]) == []
    assert math.isclose((math.fsum(n*r**4 for r,n in rainflow([0,1,0]))/NREF)**.25,
                        NREF**(-.25), rel_tol=1e-13)
    for invalid in ([0,float("nan")], [1], [1,float("inf")]):
        try:
            rainflow(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("bad input accepted")
    print("PASS: known-answer half/full cycles, plateau, DEL, invalid input")

def entries(manifest):
    raw = manifest.read_bytes()
    data = json.loads(raw)
    found = {}
    for e in data:
        m = re.fullmatch(r"CASES/(U[^/]+_NTM_S\d\d)/DTU_10MW_RWT\.outb",
                         e.get("relative_path", ""))
        if e.get("section") == "openfast-36-r2" and m:
            case = m.group(1)
            if case in found:
                raise ValueError("DUPLICATE_NTM_SOURCE")
            found[case] = e
    if set(found) != set(CASES):
        raise ValueError("NOT_18_NTM_CASES")
    return found, sha(raw)

def unpack_columns(raw, h, names, units, scales, offsets):
    if h["file_id"] != 4 or h["num_samples"] != 12001:
        raise ValueError("UNSUPPORTED_NATIVE_GRID")
    if abs(h["first_time_s"] - 100.) > 1e-7 or abs(h["time_increment_s"] - .05) > 1e-10:
        raise ValueError("TIME_WINDOW_NOT_100_TO_700")
    selected = ["TwrBs"+s for s in BASE]
    selected += [f"TwHt{g}{s}" for g in range(1,10) for s in GAGE]
    if len(set(names)) != len(names) or not all(c in names for c in selected):
        raise ValueError("NATIVE_CHANNEL_MISSING_OR_DUPLICATE")
    n = h["num_output_channels"]
    payload = raw[h["data_offset_bytes"]:]
    packed = array("h")
    packed.frombytes(payload)
    if sys.byteorder != "little":
        packed.byteswap()
    if len(packed) != 12001*n:
        raise ValueError("PACKED_PAYLOAD_SIZE")
    for channel in selected:
        i = names.index(channel)-1
        scale = scales[i]
        if not math.isfinite(scale) or scale == 0 or not math.isfinite(offsets[i]):
            raise ValueError("INVALID_PACKED_SCALE")
        vals = [(v-offsets[i])/scale for v in packed[i::n]]
        if not all(math.isfinite(v) for v in vals):
            raise ValueError("DECODE_NONFINITE")
        yield channel, units[i+1], vals, .5/abs(scale)

def main(a):
    source, manifest_sha = entries(a.manifest)
    if a.list_archives:
        for case in CASES:
            print(source[case]["canonical_archive"])
        return
    if a.zip_dir is None or a.out is None or a.receipt is None:
        raise ValueError("ZIP_DIR_OUTPUT_RECEIPT_REQUIRED")
    rows, sources = [], []
    for case in CASES:
        e = source[case]
        path = a.zip_dir / Path(e["archive"]).name
        zbytes = path.read_bytes()
        with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
            raw = z.read(e["relative_path"])  # CRC checked by zipfile
        if len(raw) != int(e["bytes"]) or sha(raw).lower() != e["sha256"].lower():
            raise ValueError("ORIGINAL_OUTB_SHA_OR_SIZE_MISMATCH:"+case)
        h = outb_header(raw)
        names, units = h.pop("channel_names"), h.pop("channel_units")
        scales, offsets = h.pop("column_scales"), h.pop("column_offsets")
        case_count = 0
        for channel, unit, vals, quant in unpack_columns(raw,h,names,units,scales,offsets):
            cyc = rainflow(vals)
            m = math.fsum(vals)/len(vals)
            variance = math.fsum((v-m)**2 for v in vals)/len(vals)
            row = dict(case=case, source_archive=path.name, outb_sha256=sha(raw),
                       channel=channel, unit=unit, n_samples=len(vals),
                       t0_s=100, t1_s=700, dt_s=.05, mean=m, min=min(vals),
                       max=max(vals), std=math.sqrt(variance),
                       rainflow_equivalent_cycles=math.fsum(n for _,n in cyc),
                       DEL_m4_Nref600=(math.fsum(n*r**4 for r,n in cyc)/NREF)**.25,
                       DEL_m10_Nref600=(math.fsum(n*r**10 for r,n in cyc)/NREF)**.1,
                       quantization_half_step_unit=quant)
            rows.append(row)
            case_count += 1
        if case_count != 60:
            raise ValueError("NOT_60_CHANNELS")
        sources.append(dict(case=case, outb_sha256=sha(raw),
                            archive_sha256=sha(zbytes), archive=path.name,
                            bytes=len(raw), file_id=h["file_id"],
                            n_samples=h["num_samples"], n_channels=h["num_output_channels"]))
        print("ORIGINAL_NTM_SHA_AND_60_CHANNELS_PASS",case,sha(raw),file=sys.stderr)
    if len(rows) != 1080:
        raise ValueError("NOT_1080_ROWS")
    stream = io.StringIO(newline="")
    w = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    for row in rows:
        w.writerow({k:format(v, ".12g") if isinstance(v,float) else v
                    for k,v in row.items()})
    result = stream.getvalue().encode("utf-8")
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(result)
    receipt = dict(status="ORIGINAL_NTM_18CASE_9GAGE_60CHANNEL_SOURCE_RAINFLOW_NUMERIC_ONLY",
                   source_reading_level="18 original archived OUTB byte streams, verified SHA256 and full 12001-sample packed-channel decode",
                   manifest_sha256=manifest_sha,
                   script_sha256=sha(Path(__file__).read_bytes()),
                   result_sha256=sha(result), result_rows=len(rows),
                   original_outb_count=len(sources), sources=sources,
                   assumptions={"Nref":600,"m":[4,10],"sample_window_s":[100,700],
                                "gage_count":9,"base_channels":6,"gage_load_channels":54},
                   numerical_error_budget="packed int16 quantization half step = 0.5/abs(channel scale), recorded per row; CSV 12 significant digits; rainflow count conservation 1e-7",
                   SOURCE="GitHub archived 36-case source manifest + 18 original NTM OUTB, SHA256 checked",
                   REF="T062 historical source parser; T077 ASTM-style range-count method",
                   STANDARD="No authorized IEC/GB clauses checked; Nref and m are diagnostic conventions",
                   OFFICIAL="OpenFAST binary file output format, not a design-standard compliance check",
                   RUN="GitHub Actions source postprocessing only; native Abaqus=0; OpenFAST new solve=0",
                   FIG="none",TAB="18x60 original native load-channel statistics and DEL CSV",
                   physical_pass=False,
                   HOLD="Nine original OUTB tower gages are not the 31-gage reruns; source identity, tower reference frames, DLC1.2/IEC bins, PT and local material stresses not closed. Not 20-year damage.")
    a.receipt.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("PASS_ORIGINAL_NTM_18_CASES_1080_ROWS",receipt["result_sha256"])

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path)
    p.add_argument("--zip-dir",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--receipt",type=Path)
    p.add_argument("--list-archives",action="store_true")
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        self_test()
    else:
        if a.manifest is None:
            p.error("--manifest required")
        main(a)
