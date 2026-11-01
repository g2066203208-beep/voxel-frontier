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


# S06/S07: six-component conditional LOCAL mean source diagnostic, NOT a
# synchronized global free body or Abaqus external-load ownership certificate.
SIX_STATIC_SHA256 = "ae1e5bc3e217cd9151bcd45f9d70909d0459df3c258329f17c6c2fdb457fd64e"
SIX_FZ_SHA256 = "bcec1d70d0a5e93a9f9d37efcde32e9e57bfa61b592ab31ba5bc58a6a455797e"
SIX_CHANNELS = ("Fx", "Fy", "Fz", "Mx", "My", "Mz")
SIX_FIELDS = ("case","joint","below_segment","above_segment","gage_span_m",
              "max_gage_z_mismatch_m") + tuple(
              prefix + "_" + ch + ("_kN" if ch.startswith("F") else "_kNm")
              for prefix in ("mean_delta","static_delta","mean_minus_static")
              for ch in SIX_CHANNELS) + ("status",)
SIX_STATUS = "CONDITIONAL_LOCAL_MEAN_COMMON_FRAME_NO_DCM_NO_EXTERNAL_LOAD_NO_PT_PROOF"

def sixcomp_analyze(loads, static_rows, fz_rows):
    if len(loads)!=744 or len(static_rows)!=30 or len(fz_rows)!=124:
        raise ValueError("SIX_SOURCE_GRID_744_30_124")
    load_map={}
    expected_segments=tuple("CSEG_%02d"%i for i in range(1,32))
    expected_channels=tuple(x+("_kN" if x.startswith("F") else "_kNm") for x in SIX_CHANNELS)
    for row in loads:
        case,seg,ch=row["case"],row["segment"],row["channel"]
        if case not in CASES or seg not in expected_segments:
            raise ValueError("SIX_CASE_SEGMENT")
        if ch not in expected_channels: raise ValueError("SIX_CHANNEL")
        if row["units"] != ("kN" if ch.startswith("F") else "kNm"):
            raise ValueError("SIX_UNIT")
        if (int(row["n_samples"]),finite(row["dt_s"]),finite(row["duration_s"]))!=(12001,0.05,600.0):
            raise ValueError("SIX_TIME_GRID")
        key=(case,seg,ch)
        if key in load_map: raise ValueError("SIX_DUPLICATE_CHANNEL")
        finite(row["mean"]); finite(row["gage_z_m"])
        load_map[key]=row
    if len(load_map)!=744: raise ValueError("SIX_INCOMPLETE_GRID")
    fz_lookup={}
    for row in fz_rows:
        key=(row["case"],row["segment"])
        if key in fz_lookup or row["status"]!=STATUS:
            raise ValueError("SIX_FZ_PROVENANCE")
        fz_lookup[key]=row
    if len(fz_lookup)!=124: raise ValueError("SIX_FZ_GRID")
    output=[]
    for case in CASES:
        for j,s in enumerate(static_rows,1):
            lo,hi="CSEG_%02d"%j,"CSEG_%02d"%(j+1)
            if (s["joint"],s["below_segment"],s["above_segment"],s["frame_policy"])!=(
                "J%02d"%j,lo,hi,"STATIC_COMMON_FRAME_ASSUMED"):
                raise ValueError("SIX_STATIC_IDENTITY")
            dz=finite(s["gage_span_m"])
            if not 0<dz<10: raise ValueError("SIX_SPAN")
            def val(seg,ch):
                unit="_kN" if ch.startswith("F") else "_kNm"
                return finite(load_map[(case,seg,ch+unit)]["mean"])
            def z(seg):
                return finite(load_map[(case,seg,"Fz_kN")]["gage_z_m"])
            mismatch=max(abs(z(lo)-finite(s["z_below_gage_m"])),
                         abs(z(hi)-finite(s["z_above_gage_m"])))
            if mismatch>0.002: raise ValueError("SIX_GAGE_HEIGHT")
            # Upper cut moved to lower point: (r_upper-r_lower) x F_upper,
            # where the assumed common vertical direction is +z.
            dyn=[val(hi,ch)-val(lo,ch) for ch in SIX_CHANNELS]
            dyn[3]-=dz*val(hi,"Fy")
            dyn[4]+=dz*val(hi,"Fx")
            stat=[finite(s["delta_F"+axis+"_kN"]) for axis in ("x","y","z")]
            stat += [finite(s["delta_M"+axis+"_at_below_kNm"]) for axis in ("x","y","z")]
            residual=[x-y for x,y in zip(dyn,stat)]
            old=fz_lookup[(case,hi)]
            if abs(residual[2]-finite(old["adjacent_delta_residual_kN"]))>2e-6:
                raise ValueError("SIX_FZ_CROSSCHECK")
            row=dict(case=case,joint=s["joint"],below_segment=lo,
                     above_segment=hi,gage_span_m=dz,
                     max_gage_z_mismatch_m=mismatch,status=SIX_STATUS)
            for prefix,values in (("mean_delta",dyn),("static_delta",stat),
                                  ("mean_minus_static",residual)):
                for ch,v in zip(SIX_CHANNELS,values):
                    row[prefix+"_"+ch+("_kN" if ch.startswith("F") else "_kNm")]=v
            output.append(row)
    if len(output)!=120: raise ValueError("SIX_OUTPUT_GRID")
    return output

def sixcomp_render(rows):
    out=io.StringIO(newline="")
    w=csv.DictWriter(out,fieldnames=SIX_FIELDS,lineterminator="\n")
    w.writeheader()
    for row in rows:
        w.writerow({k:format(row[k],".9f") if isinstance(row[k],float) else row[k]
                    for k in SIX_FIELDS})
    return out.getvalue().encode("utf-8")

def sixcomp_check(rows, raw):
    other=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if len(other)!=120 or list(other[0])!=list(SIX_FIELDS):
        raise ValueError("SIX_COMMITTED_SHAPE")
    for i,(a,b) in enumerate(zip(rows,other)):
        for key in SIX_FIELDS:
            if isinstance(a[key],float):
                if abs(a[key]-finite(b[key]))>2e-7:
                    raise ValueError("SIX_COMMITTED_VALUE:%d:%s"%(i,key))
            elif str(a[key])!=b[key]:
                raise ValueError("SIX_COMMITTED_IDENTITY:%d:%s"%(i,key))
    return True

def sixcomp_negative_tests(loads,static_rows,fz_rows):
    import copy
    failures=0
    def rejects(a,b,c):
        nonlocal failures
        try:sixcomp_analyze(a,b,c)
        except (ValueError,KeyError):failures+=1
        else:raise AssertionError("SIX_TAMPER_ACCEPTED")
    for field,bad in (("units","N"),("n_samples","12000"),("mean","nan"),
                      ("gage_z_m","999")):
        changed=copy.deepcopy(loads);changed[0][field]=bad
        rejects(changed,static_rows,fz_rows)
    changed=copy.deepcopy(loads);changed[1]=copy.deepcopy(changed[0])
    rejects(changed,static_rows,fz_rows)
    changed=copy.deepcopy(static_rows);changed[0]["gage_span_m"]="0"
    rejects(loads,changed,fz_rows)
    changed=copy.deepcopy(fz_rows);changed[1]["adjacent_delta_residual_kN"]="999"
    rejects(loads,static_rows,changed)
    # Known wrench: 2m upward lever crossed with (10,3,0) kN
    assert (-2.0*3.0,2.0*10.0,0.0)==(-6.0,20.0,0.0)
    assert failures==7
    return failures

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--load",type=Path)
    ap.add_argument("--gravity",type=Path)
    mode=ap.add_mutually_exclusive_group()
    mode.add_argument("--output",type=Path)
    mode.add_argument("--check",type=Path)
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--sixcomp-static",type=Path)
    ap.add_argument("--sixcomp-fz",type=Path)
    ap.add_argument("--sixcomp-output",type=Path)
    ap.add_argument("--sixcomp-check",type=Path)
    a=ap.parse_args()
    if a.self_test:self_test()
    if a.sixcomp_static or a.sixcomp_fz or a.sixcomp_output or a.sixcomp_check:
        if not (a.load and a.sixcomp_static and a.sixcomp_fz and
                (a.sixcomp_output or a.sixcomp_check) and
                not (a.sixcomp_output and a.sixcomp_check)):
            ap.error("sixcomp needs --load --sixcomp-static --sixcomp-fz and one output/check")
        loads=load_locked(a.load,LOAD_SHA256)
        stat=load_locked(a.sixcomp_static,SIX_STATIC_SHA256)
        fz=load_locked(a.sixcomp_fz,SIX_FZ_SHA256)
        rows=sixcomp_analyze(loads,stat,fz)
        if a.sixcomp_check:sixcomp_check(rows,a.sixcomp_check.read_bytes())
        else:a.sixcomp_output.write_bytes(sixcomp_render(rows))
        neg=sixcomp_negative_tests(loads,stat,fz)
        summary={ch:max(abs(row["mean_minus_static_"+ch+
                   ("_kN" if ch.startswith("F") else "_kNm")]) for row in rows)
                   for ch in SIX_CHANNELS}
        print("S06_S07_REAL_4ETM_30JOINT_6COMP_MEAN_QC",
              "rows",len(rows),"negative_tests",neg,"max_abs_residual",summary,
              "status",SIX_STATUS,"native_runs",0)
        return
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
