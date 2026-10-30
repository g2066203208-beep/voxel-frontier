#!/usr/bin/env python3
"""Source-locked conditional gross-section PT offset on REAL 4 ETM x31x16 gross stresses.

This is an algebraic *counterfactual*, NOT a local concrete/rebar/PT stress,
contact solution, design check, or fatigue-life calculation. Fz/PT ownership
is not yet certified: if the wind-derived Fz already contains PT, subtraction
would double count. Uses P0/Pe as separate scenarios, never adds both.
"""
import argparse
import csv
import hashlib
import io
import math
from pathlib import Path

GEOM_SHA = "fff6dfcc6bc094353ebee042392033e8df47e7fb792ccc1812c0962c9c43f800"
GROSS_SHA = "16c9864ef7a344e5b97338c31ce26de6adb86c0f0f64942ef894fe9983926b2b"
PT_AREA_MM2 = 40320.0
P0_MPA = 1280.0
PE_MPA = 985.9513629616609  # D400 child input stress card, NOT native equilibrated
P0_MN = PT_AREA_MM2 * P0_MPA / 1e6
PE_MN = PT_AREA_MM2 * PE_MPA / 1e6
CASES = ("U09p343881_ETM_S06", "U11p4_ETM_S04",
         "U19p202140_ETM_S04", "U19p202140_ETM_S06")
ANGLES = tuple(22.5 * i for i in range(16))
COLUMNS = ("case","segment","A_gross_m2","PT_P0_MN","PT_Pe_MN",
           "uniform_P0_compression_MPa","uniform_Pe_compression_MPa",
           "PT_loss_shift_MPa","gross_max_sigma_MPa","Pe_shifted_max_sigma_MPa",
           "P0_shifted_max_sigma_MPa","n_of_16_angles_positive_peak_gross",
           "n_of_16_angles_positive_peak_Pe","n_of_16_angles_positive_peak_P0",
           "max_gross_DEL4_MPa","max_gross_DEL10_MPa","status")
STATUS = "COUNTERFACTUAL_UNIFORM_PT_SHIFT_NOT_LOCAL_OR_FATIGUE_OR_NATIVE"

def load(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("SOURCE_SHA256_MISMATCH:" + path.name)
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if not rows:
        raise ValueError("EMPTY_CSV")
    return rows

def finite(v):
    x = float(v)
    if not math.isfinite(x):
        raise ValueError("NONFINITE")
    return x

def offset(area):
    if not math.isfinite(area) or area <= 0:
        raise ValueError("AREA")
    return P0_MN / area, PE_MN / area

def calc(geom, gross):
    if len(geom) != 31:
        raise ValueError("GEOMETRY_31")
    areas = {}
    for row in geom:
        seg = row["segment"]
        if seg in areas:
            raise ValueError("DUPLICATE_SEGMENT")
        a = finite(row["A_m2"])
        d, di = finite(row["D_m"]), finite(row["di_m"])
        if not 0 < di < d or not math.isclose(a, math.pi*(d*d-di*di)/4, rel_tol=1e-8):
            raise ValueError("GEOMETRY_RING")
        areas[seg] = a
    if set(areas) != {f"CSEG_{i:02d}" for i in range(1, 32)}:
        raise ValueError("GEOMETRY_IDENTITIES")
    if len(gross) != 1984:
        raise ValueError("GROSS_1984")
    groups = {}
    for row in gross:
        key = (row["case"], row["segment"])
        if key[0] not in CASES or key[1] not in areas:
            raise ValueError("UNKNOWN_CASE_OR_SEGMENT")
        a = finite(row["azimuth_deg"])
        if a not in ANGLES:
            raise ValueError("AZIMUTH_NOT_IN_GRID")
        grp = groups.setdefault(key, [])
        if any(finite(z["azimuth_deg"]) == a for z in grp):
            raise ValueError("DUPLICATE_AZIMUTH")
        if row["stress_class"] != "SYNCHRONOUS_GROSS_ELASTIC_16AZIMUTH_NO_PT_NO_MATERIAL_LIFE":
            raise ValueError("WRONG_STRESS_OWNER")
        grp.append(row)
    if len(groups) != 124:
        raise ValueError("GROUP_124")
    out = []
    for case in CASES:
        for i in range(1, 32):
            seg = f"CSEG_{i:02d}"
            rows = groups.get((case, seg), [])
            if len(rows) != 16 or {finite(x["azimuth_deg"]) for x in rows} != set(ANGLES):
                raise ValueError("INCOMPLETE_16_ANGLES")
            a = areas[seg]
            p0, pe = offset(a)
            peaks = [finite(x["sigma_max_MPa"]) for x in rows]
            mins = [finite(x["sigma_min_MPa"]) for x in rows]
            means = [finite(x["sigma_mean_MPa"]) for x in rows]
            d4 = [finite(x["DEL_m4_MPa"]) for x in rows]
            d10 = [finite(x["DEL_m10_MPa"]) for x in rows]
            if any(mx < mn or not math.isfinite(me) or d <= 0 for mx,mn,me,d in zip(peaks,mins,means,d4)):
                raise ValueError("GROSS_STRESS_INVALID")
            # A constant shift does not change cycle ranges, DEL or range-based
            # rainflow. It DOES change stress means and nonlinear/contact physics.
            if any(not math.isclose((mx-pe)-(mn-pe), mx-mn, abs_tol=1e-11)
                   for mx,mn in zip(peaks,mins)):
                raise ValueError("CONSTANT_SHIFT_RANGE_IDENTITY")
            out.append({
                "case":case,"segment":seg,"A_gross_m2":a,
                "PT_P0_MN":P0_MN,"PT_Pe_MN":PE_MN,
                "uniform_P0_compression_MPa":p0,
                "uniform_Pe_compression_MPa":pe,
                "PT_loss_shift_MPa":p0-pe,
                "gross_max_sigma_MPa":max(peaks),
                "Pe_shifted_max_sigma_MPa":max(peaks)-pe,
                "P0_shifted_max_sigma_MPa":max(peaks)-p0,
                "n_of_16_angles_positive_peak_gross":sum(x>0 for x in peaks),
                "n_of_16_angles_positive_peak_Pe":sum(x>pe for x in peaks),
                "n_of_16_angles_positive_peak_P0":sum(x>p0 for x in peaks),
                "max_gross_DEL4_MPa":max(d4),
                "max_gross_DEL10_MPa":max(d10),
                "status":STATUS})
    return out

def render(rows):
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k:format(v,".12g") if isinstance(v,float) else v
                         for k,v in row.items()})
    return buf.getvalue().encode("utf-8")

def check(actual, expected):
    a = list(csv.DictReader(io.StringIO(actual.decode())))
    b = list(csv.DictReader(io.StringIO(expected.decode())))
    if len(a) != len(b):
        raise ValueError("RESULT_ROWS")
    for x,y in zip(a,b):
        if set(x) != set(y):
            raise ValueError("RESULT_COLUMNS")
        for k in x:
            if k in ("case","segment","status") or k.startswith("n_of_"):
                if x[k] != y[k]:
                    raise ValueError("RESULT_IDENTITY:"+k)
            elif not math.isclose(finite(x[k]),finite(y[k]),rel_tol=2e-10,abs_tol=1e-9):
                raise ValueError("RESULT_NUMERIC:"+k)

def self_test():
    assert math.isclose(P0_MN,51.6096,rel_tol=0,abs_tol=1e-12)
    assert math.isclose(PE_MN,39.75355895461417,rel_tol=0,abs_tol=1e-12)
    p0,pe = offset(6.0)
    assert p0 > pe > 0
    x = [-2.0,3.0,0.0,-1.0]
    assert math.isclose(max(v-pe for v in x),max(x)-pe,abs_tol=1e-12)
    assert math.isclose((max(x)-min(x)),
                        max(v-pe for v in x)-min(v-pe for v in x),abs_tol=1e-12)
    for bad in (0.0,-1.0,float("nan"),float("inf")):
        try:offset(bad)
        except ValueError:pass
        else:raise AssertionError("INVALID_AREA_ACCEPTED")
    try:check(b"case,segment\nA,B\n",b"case,segment\nA,C\n")
    except ValueError:pass
    else:raise AssertionError("TAMPERED_RESULT_ACCEPTED")
    print("S10_PT_UNIFORM_OFFSET_SYNTHETIC_9_ASSERTIONS_PASS_NOT_PHYSICS")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--geometry",type=Path)
    ap.add_argument("--gross",type=Path)
    ap.add_argument("--output",type=Path)
    ap.add_argument("--check",type=Path)
    ap.add_argument("--self-test",action="store_true")
    args = ap.parse_args()
    if args.self_test:self_test()
    if args.geometry or args.gross or args.output or args.check:
        if not args.geometry or not args.gross or bool(args.output)==bool(args.check):
            ap.error("need --geometry --gross and exactly one of --output/--check")
        rows = calc(load(args.geometry,GEOM_SHA),load(args.gross,GROSS_SHA))
        raw = render(rows)
        if args.check:check(raw,args.check.read_bytes())
        else:args.output.write_bytes(raw)
        print("S10_REAL_PT_COUNTERFACTUAL_NUMERIC_ONLY",len(rows),
              hashlib.sha256(raw).hexdigest(),
              "PE_MN",format(PE_MN,".12g"),
              "NATIVE_RUNS",0)
