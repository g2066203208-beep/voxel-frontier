#!/usr/bin/env python3
"""Reproduce historical S03/S04 load DEL from real OUTB and original 2026 script.

Executed original AST functions (sha locked), one AST comparator-only fix,
and independent pinned rainflow 3.2.0. No OpenFAST solver, no Abaqus.
"""
import argparse
import ast
import copy
import csv
import hashlib
import json
from pathlib import Path
import struct
from types import SimpleNamespace
import zipfile
from collections import Counter

HERE=Path(__file__).resolve().parent
WT=HERE.parents[1]
SUP=WT/"archive/local-assets-20261004-supplement"
OLD=HERE/"legacy-primary-recovered-20261102"
OLD_CODE=OLD/"rainflow_del_r1.py"
OLD_DEL=OLD/"05_LOAD_DEL_M4_ALL36.csv"
NEW_DEL=HERE/"recomputed-load-fatigue/05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv"
CODE_SHA="b7c2d50b391d90f69fef6aa72e5bdf4be5a843c72b4460147145a0df14110649"
from s06_historical_outb_source_gate import outb_header

def sha(b):return hashlib.sha256(b).hexdigest()

def historical_func(fix=False):
    raw=OLD_CODE.read_bytes()
    if sha(raw)!=CODE_SHA:raise ValueError("WRONG_HISTORICAL_CODE_SOURCE_SHA")
    tree=ast.parse(raw.decode())
    defs=[copy.deepcopy(n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ("reversals","rainflow")]
    if len(defs)!=2:raise ValueError("MISSING_ORIGINAL_FUNCTIONS")
    rain=next(n for n in defs if n.name=="rainflow")
    checks=[n for n in ast.walk(rain) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare)
       and isinstance(n.test.left,ast.Name) and n.test.left.id=="X"
       and len(n.test.ops)==1 and isinstance(n.test.ops[0],ast.Lt)
       and isinstance(n.test.comparators[0],ast.Name) and n.test.comparators[0].id=="Y"]
    if len(checks)!=1:raise ValueError("LEGACY_COMPARATOR_IDENTITY_CHANGED")
    if fix:
        checks[0].test.left=ast.Name(id="Y",ctx=ast.Load())
        checks[0].test.comparators=[ast.Name(id="X",ctx=ast.Load())]
    # Original reversal() only uses np.asarray(signal,float); exactly equivalent
    # for these iterable float series is a list of floats; no NumPy needed.
    ns={"np":SimpleNamespace(asarray=lambda a,dtype:[float(v) for v in a])}
    exec(compile(ast.fix_missing_locations(ast.Module(body=defs,type_ignores=[])),str(OLD_CODE),"exec"),ns)
    return ns["rainflow"]

def table(p,column):
    with p.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    return {(r["case_id"],r["channel"]):float(r[column]) for r in rows}

def series(case,part,manifest):
    member="CASES/"+case+"/DTU_10MW_RWT.outb"
    matches=[x for x in manifest if x.get("section")=="openfast-36-r2" and x.get("relative_path")==member]
    if len(matches)!=1 or not matches[0]["archive"].endswith("/"+part):raise ValueError("OUTB_MANIFEST_MISMATCH")
    p=SUP/"openfast-36-r2"/part
    with zipfile.ZipFile(p) as z:
        if z.testzip() is not None:raise ValueError("OUTB_ZIP_CRC_FAILURE")
        raw=z.read(member)
    if len(raw)!=int(matches[0]["bytes"]) or sha(raw)!=matches[0]["sha256"].lower():
        raise ValueError("OUTB_SHA_FAILURE")
    h=outb_header(raw)
    names=h["channel_names"]
    col=names.index("TwrBsMyt")-1
    if h["file_id"]!=4 or h["num_samples"]!=12001 or abs(h["first_time_s"]-100)>1e-8 or abs(h["time_increment_s"]-.05)>1e-9:
        raise ValueError("WRONG_OUTB_SAMPLE_WINDOW")
    n=h["num_output_channels"]; off=h["column_offsets"][col]; scale=h["column_scales"][col]
    if scale==0:raise ValueError("ZERO_OUTPUT_SCALE")
    data=[(struct.unpack_from("<h",raw,h["data_offset_bytes"]+2*(i*n+col))[0]-off)/scale
          for i in range(h["num_samples"])]
    return data,sha(raw),sha(p.read_bytes())

def multiset(a):
    return Counter((round(r,8),round(m,8),n) for r,m,n in a)

def delm4(a):
    return (sum(n*r**4 for r,m,n in a)/100000)**.25

def run():
    import rainflow
    if rainflow.__version__!="3.2.0":raise ValueError("REFERENCE_RAINFLOW_VERSION")
    old=historical_func(False);patched=historical_func(True)
    sample=[0,10,5,15]
    original_example=old(sample);patched_example=patched(sample)
    reference_example=[(float(r),float(m),float(n)) for r,m,n,i,j in rainflow.extract_cycles(sample) if r>0]
    if multiset(original_example)==multiset(reference_example) or multiset(patched_example)!=multiset(reference_example):
        raise ValueError("SYNTHETIC_TEST_MUST_SHOW_REVERSED_COMPARISON")
    old_del=table(OLD_DEL,"DEL_load_comparison")
    new_del=table(NEW_DEL,"DEL")
    manifest=json.loads((SUP/"file-manifest.json").read_text())
    results=[]
    for case,part in [("U11p4_ETM_S03","part-015.zip"),("U11p4_ETM_S04","part-016.zip")]:
        data,rawsha,zipsha=series(case,part,manifest)
        original=old(data)
        fixed=patched(data)
        reference=[(float(r),float(m),float(n)) for r,m,n,i,j in rainflow.extract_cycles(data) if r>0]
        legacy_target=old_del[case,"TwrBsMyt"]
        current_target=new_del[case,"TwrBsMyt"]
        old_value=delm4(original)
        fixed_value=delm4(fixed)
        ref_value=delm4(reference)
        if abs(old_value-legacy_target)>1e-5:raise AssertionError("LEGACY_DEL_NOT_REPRODUCED_"+case+":"+str(old_value))
        if abs(fixed_value-current_target)>1e-5:raise AssertionError("PATCHED_DEL_NOT_REPRODUCED_"+case+":"+str(fixed_value))
        if abs(ref_value-current_target)>1e-5:raise AssertionError("THIRD_PARTY_DEL_NOT_REPRODUCED_"+case+":"+str(ref_value))
        if multiset(fixed)!=multiset(reference):raise AssertionError("PATCHED_RANGES_MEANS_COUNTS_DIFFER_"+case)
        weighted_old=sum(x[2] for x in original);weighted_new=sum(x[2] for x in reference)
        if abs(weighted_old-weighted_new)>1e-9:raise AssertionError("WEIGHT_CONSERVATION_FAILED")
        results.append({"case":case,"original_outb_sha256":rawsha,"original_zip_sha256":zipsha,
          "n_samples":len(data),"original_function_DEL_kNm":old_value,
          "original_legacy_05_CSV_DEL_kNm":legacy_target,
          "one_comparator_fix_DEL_kNm":fixed_value,
          "independent_rainflow_3_2_DEL_kNm":ref_value,
          "current_T062_05_CSV_DEL_kNm":current_target,
          "legacy_cycle_rows":len(original),"patched_cycle_rows":len(fixed),"reference_cycle_rows":len(reference),
          "weighted_cycle_sum_original":weighted_old,"weighted_cycle_sum_corrected":weighted_new,
          "patched_full_cycle_range_mean_count_equal_independent_reference":True})
    return {"status":"T062_SOURCE_IDENTICAL_HISTORICAL_ALGORITHM_CAUSE_REPRODUCED",
      "historical_script_sha256":CODE_SHA,
      "identical_old_new_OUTB_sha_count":36,
      "pinned_rainflow_wheel_sha256":"cb6c254aa1a16a9e658ff3f39c6e5a77650d6c4e8304146169b36516d1f01660",
      "source_reading_level":"Original 2026-09 script AST executed with exact SHA; true S03/S04 original OpenFAST 7MB OUTB SHA validated; independent wheel 3.2.0",
      "root_cause":"Old X=previous range, Y=NEW range and incorrectly breaks on X<Y; must break when Y<X. One comparator-only change recovers independent reference on 2 real controls.",
      "original_source_unchanged":True,"one_line_patch_in_memory_only":True,
      "synthetic_counterexample":{"signal":sample,"original_cycles":original_example,"patched_cycles":patched_example,"independent_cycles":reference_example},
      "real_cases":results,
      "REF":"original September 2026 rainflow_del_r1.py and T062 independent source DEL",
      "STANDARD":"rainflow package declares ASTM algorithm, authorized ASTM text not read",
      "OFFICIAL":"real OpenFAST original FileID4 source verified; no new OpenFAST solver",
      "RUN":"GitHub Actions pure Python: exact original functions/patch/reference against two real OUTB",
      "FIG":"previous source-divergence figure requires revised causal caption",
      "TAB":"two control cases original/fix/reference with full cycle statistics",
      "error_budget":"DEL absolute 1e-5 kN-m and 1e-8 range/mean for multiset; physical error not evaluated",
      "HOLD":"Need whole-36-case crosscheck to claim original algorithm issue applies to all; not material S-N/Miner/20-year life",
      "material_fatigue_pass":False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,required=True);args=ap.parse_args()
    r=run();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2)[:8500])

if __name__=="__main__":main()
