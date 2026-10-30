#!/usr/bin/env python3
"""Compare REAL 4x31 OpenFAST-derived Fz mean with archived static gravity reference.

Source-level ownership DIAGNOSTIC ONLY. The static reference and the wind
sectional Fz are OpenFAST internal resultants; no independently certified PT
stress/force is available. Adjacent differencing cancels ANY constant axial
force, including an erroneously injected PT force, so it CANNOT prove PT absence.
No Abaqus, no material life, no 2025 standard clause compliance.
"""
import argparse
import csv
import hashlib
import io
import math
from pathlib import Path

LOAD_SHA256 = "9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b"
GRAVITY_SHA256 = "ba43732de537854e0361d1aa4cc2792bf8b80ab3536115b6b2f1c9e2317dfe6f"
CASES = ("U09p343881_ETM_S06", "U11p4_ETM_S04",
         "U19p202140_ETM_S04", "U19p202140_ETM_S06")
CHANNELS = {"Fx_kN":"kN","Fy_kN":"kN","Fz_kN":"kN",
            "Mx_kNm":"kNm","My_kNm":"kNm","Mz_kNm":"kNm"}
PE_KN = 39753.5589546   # D400 provisional input, NOT verified equilibrated force
FIELDS = ("case","segment","gage_z_m","Fz_mean_kN",
          "static_gravity_Fz_kN","mean_minus_gravity_kN",
          "abs_mean_residual_over_Pe_pct","adjacent_observed_delta_Fz_kN",
          "adjacent_gravity_delta_Fz_kN","adjacent_delta_residual_kN",
          "status")
STATUS = "REAL_SOURCE_FZ_GRAVITY_QC_PT_OWNERSHIP_NOT_NATIVE_CERTIFIED"

def finite(v):
    x = float(v)
    if not math.isfinite(x):
        raise ValueError("NONFINITE")
    return x

def load_locked(path, expected):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("SOURCE_SHA256_MISMATCH:" + str(path))
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if not rows or any(None in r or None in r.values() for r in rows):
        raise ValueError("BAD_CSV")
    return rows

def analyze(loads, gravity):
    if len(loads) != 744 or len(gravity) != 30:
        raise ValueError("SOURCE_SHAPE_744_30")
    expected_segments = tuple("CSEG_%02d" % i for i in range(1,32))
    refs, joint_delta = {}, {}
    for i,j in enumerate(gravity, 1):
        below, above = expected_segments[i-1:i+1]
        if (j["joint"] != "J%02d" % i or j["below_segment"] != below
                or j["above_segment"] != above):
            raise ValueError("JOINT_ORDER_OR_SEGMENT")
        lo = finite(j["Fz_below_gravity_kN"])
        hi = finite(j["Fz_above_gravity_kN"])
        delta = finite(j["Fz_above_minus_below_kN"])
        if abs(hi-lo-delta) > 2e-8:
            raise ValueError("STATIC_GRAVITY_DELTA")
        for seg,v in ((below,lo),(above,hi)):
            if seg in refs and abs(refs[seg]-v)>2e-8:
                raise ValueError("STATIC_REFERENCE_DISCONTINUITY")
            refs[seg] = v
        joint_delta[above] = delta
    if set(refs) != set(expected_segments):
        raise ValueError("GRAVITY_31")
    all_keys, fz = set(), {}
    for r in loads:
        case,seg,ch = r["case"],r["segment"],r["channel"]
        if case not in CASES or seg not in refs or ch not in CHANNELS:
            raise ValueError("UNEXPECTED_LOAD_IDENTITY")
        if r["units"] != CHANNELS[ch] or int(r["n_samples"]) != 12001:
            raise ValueError("LOAD_UNITS_OR_SAMPLE_COUNT")
        if abs(finite(r["dt_s"])-.05)>1e-10 or abs(finite(r["duration_s"])-600)>1e-8:
            raise ValueError("LOAD_TIME_GRID")
        key = (case,seg,ch)
        if key in all_keys:
            raise ValueError("DUPLICATE_LOAD")
        all_keys.add(key)
        if ch == "Fz_kN":
            fz[(case,seg)] = (finite(r["mean"]),finite(r["gage_z_m"]))
    if len(all_keys)!=744 or len(fz)!=124:
        raise ValueError("INCOMPLETE_FZ")
    out=[]
    for case in CASES:
        previous=None
        for seg in expected_segments:
            mean,z=fz[(case,seg)]
            g=refs[seg]
            delta=mean-g
            row=dict(case=case,segment=seg,gage_z_m=z,Fz_mean_kN=mean,
                     static_gravity_Fz_kN=g,mean_minus_gravity_kN=delta,
                     abs_mean_residual_over_Pe_pct=100*abs(delta)/PE_KN,
                     adjacent_observed_delta_Fz_kN="",
                     adjacent_gravity_delta_Fz_kN="",
                     adjacent_delta_residual_kN="",status=STATUS)
            if previous is not None:
                obs=mean-previous
                grav=joint_delta[seg]
                row["adjacent_observed_delta_Fz_kN"]=obs
                row["adjacent_gravity_delta_Fz_kN"]=grav
                row["adjacent_delta_residual_kN"]=obs-grav
            previous=mean
            out.append(row)
    if len(out)!=124 or sum(r["adjacent_delta_residual_kN"]!="" for r in out)!=120:
        raise ValueError("OUTPUT_GRID")
    return out

def render(rows):
    s=io.StringIO(newline="")
    w=csv.DictWriter(s,fieldnames=FIELDS,lineterminator="\n")
    w.writeheader()
    for row in rows:
        w.writerow({k:(format(row[k],".9f") if isinstance(row[k],float)
                      else row[k]) for k in FIELDS})
    return s.getvalue().encode("utf-8")

def check(rows, committed):
    other=list(csv.DictReader(io.StringIO(committed.decode("utf-8-sig"))))
    if len(other)!=124 or list(other[0])!=list(FIELDS):
        raise ValueError("COMMITTED_TABLE_SHAPE")
    for i,(a,b) in enumerate(zip(rows,other)):
        for key in FIELDS:
            if isinstance(a[key],float):
                if not math.isclose(a[key],finite(b[key]),rel_tol=0,abs_tol=2e-8):
                    raise ValueError("COMMITTED_NUMERIC_MISMATCH:%d:%s"%(i,key))
            elif str(a[key]) != b[key]:
                raise ValueError("COMMITTED_IDENTITY_MISMATCH:%d:%s"%(i,key))
    return True

def self_test():
    # A uniform unknown PT offset is invisible to differences, so absolute
    # comparison + provenance is mandatory; never infer PT absence from delta.
    base=[-10.,-8.,-6.]
    for shift in (0.,-1.,-39753.5589546):
        observed=[v+shift for v in base]
        for i in (1,2):
            assert math.isclose(observed[i]-observed[i-1],base[i]-base[i-1],
                                abs_tol=1e-9)
        assert math.isclose(observed[0]-base[0],shift,abs_tol=1e-9)
    try:finite("nan")
    except ValueError:pass
    else:raise AssertionError("NAN_ACCEPTED")
    assert len(FIELDS)==11
    print("S10_FZ_GRAVITY_SYNTHETIC_OFFSET_IDENTIFIABILITY_AND_NONFINITE_PASS")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--load",type=Path)
    ap.add_argument("--gravity",type=Path)
    mode=ap.add_mutually_exclusive_group()
    mode.add_argument("--output",type=Path)
    mode.add_argument("--check",type=Path)
    ap.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    if a.self_test:self_test()
    if a.load or a.gravity or a.output or a.check:
        if not (a.load and a.gravity and (a.output or a.check)):
            ap.error("need --load --gravity and --output/--check")
        rows=analyze(load_locked(a.load,LOAD_SHA256),
                     load_locked(a.gravity,GRAVITY_SHA256))
        if a.check:check(rows,a.check.read_bytes())
        else:a.output.write_bytes(render(rows))
        diffs=[abs(r["adjacent_delta_residual_kN"]) for r in rows
               if r["adjacent_delta_residual_kN"]!=""]
        residuals=[abs(r["mean_minus_gravity_kN"]) for r in rows]
        print("S10_REAL_FZ_GRAVITY_124STATIONS_120JOINTS_NUMERIC_ONLY",
              "max_joint_delta_residual_kN",format(max(diffs),".12g"),
              "max_abs_mean_minus_gravity_kN",format(max(residuals),".12g"),
              "max_abs_residual_over_Pe_pct",format(max(residuals)/PE_KN*100,".12g"),
              "native_runs",0,"PT_ownership_certified",False)
    elif not a.self_test:
        ap.error("provide --self-test or real input paths")

if __name__=="__main__":
    main()
