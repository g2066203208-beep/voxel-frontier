#!/usr/bin/env python3
"""S06 -> S10: real 4-case x 31-gage single-channel nominal stress DEL bridge.

This is a *linear gross-section scaling* of already-counted individual load
rainflow DELs, NOT a combined bending stress history, steel/concrete/PT local
stress, Miner damage, or lifetime prediction. No peak-vector composition.
Uses only source-locked public small CSVs. Python >=3.10 standard library.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

LOAD_SHA = "9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b"
GEOM_SHA = "fff6dfcc6bc094353ebee042392033e8df47e7fb792ccc1812c0962c9c43f800"
CHANNELS = ("Fx_kN", "Fy_kN", "Fz_kN", "Mx_kNm", "My_kNm", "Mz_kNm")
CASES = ("U09p343881_ETM_S06", "U11p4_ETM_S04",
         "U19p202140_ETM_S04", "U19p202140_ETM_S06")
CLASS = "ONE_CHANNEL_GROSS_ELASTIC_PROXY_NO_MATERIAL_LIFE"
FIELDS = ("case", "segment", "gage_z_m", "section_z_m", "delta_z_m",
          "gross_area_m2", "gross_I_m4", "outer_radius_m",
          "Fz_DEL4_nominal_MPa", "Mx_DEL4_nominal_MPa", "My_DEL4_nominal_MPa",
          "Fz_DEL10_nominal_MPa", "Mx_DEL10_nominal_MPa", "My_DEL10_nominal_MPa",
          "source_class")

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def read_csv(raw):
    r = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if not r.fieldnames or len(r.fieldnames) != len(set(r.fieldnames)):
        raise ValueError("BAD_HEADER")
    out = list(r)
    if not out or any(None in x or None in x.values() for x in out):
        raise ValueError("BAD_ROW_WIDTH")
    return out

def number(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError("NONNUMERIC") from None
    if not math.isfinite(v):
        raise ValueError("NONFINITE")
    return v

def gross(D, di):
    if not (math.isfinite(D) and math.isfinite(di) and D > di > 0):
        raise ValueError("BAD_GROSS_GEOMETRY")
    return math.pi * (D * D - di * di) / 4, math.pi * (D**4 - di**4) / 64

def nominal(del_load, factor):
    if del_load < 0 or factor <= 0:
        raise ValueError("NEGATIVE_DEL_OR_FACTOR")
    return 0.001 * del_load * factor  # kN/m² -> MPa; kNm/m³ -> MPa

def compute(loads, geom):
    if len(loads) != 744 or len(geom) != 31:
        raise ValueError("WRONG_SOURCE_ROW_COUNT")
    geo = {}
    for g in geom:
        seg = g["segment"]
        if seg in geo or seg not in {f"CSEG_{i:02d}" for i in range(1, 32)}:
            raise ValueError("DUPLICATE_OR_BAD_SEGMENT")
        D, di = number(g["D_m"]), number(g["di_m"])
        A, I = gross(D, di)
        if (not math.isclose(A, number(g["A_m2"]), rel_tol=1e-8) or
            not math.isclose(I, number(g["I_m4"]), rel_tol=1e-8)):
            raise ValueError("SECTION_IDENTITY_MISMATCH")
        geo[seg] = (D, di, A, I, number(g["z_center_m"]))
    grouped = {}
    for r in loads:
        case, seg, channel = r["case"], r["segment"], r["channel"]
        if case not in CASES or seg not in geo or channel not in CHANNELS:
            raise ValueError("UNKNOWN_CASE_SEGMENT_CHANNEL")
        key = (case, seg)
        slot = grouped.setdefault(key, {})
        if channel in slot:
            raise ValueError("DUPLICATE_CASE_SEGMENT_CHANNEL")
        if (int(number(r["n_samples"])) != 12001 or
            not math.isclose(number(r["dt_s"]), .05, abs_tol=1e-10) or
            not math.isclose(number(r["duration_s"]), 600., abs_tol=1e-9)):
            raise ValueError("TIME_GRID_NOT_600S")
        if r["units"] != ("kN" if channel.endswith("_kN") else "kNm"):
            raise ValueError("LOAD_UNIT_MISMATCH")
        slot[channel] = r
    if len(grouped) != 124:
        raise ValueError("INCOMPLETE_CASE_SEGMENT_GRID")
    out = []
    for case in CASES:
        for i in range(1, 32):
            seg = f"CSEG_{i:02d}"
            slot = grouped.get((case, seg), {})
            if set(slot) != set(CHANNELS):
                raise ValueError("MISSING_SIX_COMPONENTS")
            z = number(slot["Fz_kN"]["gage_z_m"])
            if any(abs(number(v["gage_z_m"]) - z) > 1e-7 for v in slot.values()):
                raise ValueError("INCONSISTENT_GAGE_HEIGHT")
            D, di, A, I, zgeo = geo[seg]
            factors = {"Fz_kN": 1 / A, "Mx_kNm": D / (2 * I),
                       "My_kNm": D / (2 * I)}
            d = dict(case=case, segment=seg, gage_z_m=z, section_z_m=zgeo,
                     delta_z_m=z-zgeo, gross_area_m2=A, gross_I_m4=I,
                     outer_radius_m=D/2)
            for exponent in (4, 10):
                for name, label in (("Fz_kN", "Fz"), ("Mx_kNm", "Mx"), ("My_kNm", "My")):
                    load_del = number(slot[name][f"DEL_m{exponent}_Nref_1Hz"])
                    d[f"{label}_DEL{exponent}_nominal_MPa"] = nominal(load_del, factors[name])
            d["source_class"] = CLASS
            out.append(d)
    return out

def render(rows):
    stream = io.StringIO(newline="")
    w = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\\n")
    w.writeheader()
    for row in rows:
        w.writerow({k: format(v, ".12g") if isinstance(v, float) else v
                    for k, v in row.items()})
    return stream.getvalue().encode()

def self_test():
    A, I = gross(2., 1.)
    assert math.isclose(A, 3 * math.pi / 4, rel_tol=1e-14)
    assert math.isclose(I, 15 * math.pi / 64, rel_tol=1e-14)
    assert math.isclose(nominal(100, 1/A), .1/A, rel_tol=1e-14)
    assert math.isclose(nominal(100, 1/I), .1/I, rel_tol=1e-14)
    assert math.isclose(nominal(100, 1/I)/nominal(10, 1/I), 10)
    for bad in ((-1., 1.), (1., -1.), (1., 0.)):
        try:
            nominal(*bad)
        except ValueError:
            pass
        else:
            raise AssertionError("ACCEPTED_BAD_DEL")
    for bad in ((1., 2.), (2., 2.), (float("nan"), 1.)):
        try:
            gross(*bad)
        except ValueError:
            pass
        else:
            raise AssertionError("ACCEPTED_BAD_GEOMETRY")
    print("S10_NOMINAL_SINGLE_CHANNEL_ANALYTIC_SELFTEST_PASS_NOT_MATERIAL")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--loads", type=Path)
    p.add_argument("--geometry", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--receipt", type=Path)
    a = p.parse_args()
    if a.self_test:
        self_test()
    if a.loads or a.geometry or a.output or a.receipt:
        if not all((a.loads, a.geometry, a.output, a.receipt)):
            p.error("require loads, geometry, output and receipt")
        loadraw, georaw = a.loads.read_bytes(), a.geometry.read_bytes()
        if digest(loadraw) != LOAD_SHA or digest(georaw) != GEOM_SHA:
            raise ValueError("SOURCE_SHA256_MISMATCH")
        rows = compute(read_csv(loadraw), read_csv(georaw))
        data = render(rows)
        a.output.write_bytes(data)
        control = {}
        for field in ("Fz_DEL4_nominal_MPa", "Mx_DEL4_nominal_MPa",
                      "My_DEL4_nominal_MPa"):
            x = max(rows, key=lambda r: r[field])
            control[field] = {"case": x["case"], "segment": x["segment"],
                              "value_MPa": x[field]}
        receipt = dict(status="REAL_4CASE_31SEG_COMPONENT_NOMINAL_DEL_ONLY",
            loads_sha256=LOAD_SHA, geometry_sha256=GEOM_SHA,
            output_sha256=digest(data), rows=len(rows),
            controls=control, native_Abaqus_runs=0, material_fatigue_life=None,
            physical_pass=False, independent_events=0,
            method="one-channel rainflow DEL linear gross-section conversion",
            assumptions="A,I,D from T071 gross OpenFAST geometry; same segment gage at offset; Nref=600",
            limitations="no synchronous combined stress; no steel/concrete/PT local stress; m4/m10 are screening exponents not material SN; four ETM samples not DLC1.2 design distribution")
        a.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True)+"\\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    if not a.self_test and not a.loads:
        p.error("use --self-test or source inputs")

if __name__ == "__main__":
    main()
