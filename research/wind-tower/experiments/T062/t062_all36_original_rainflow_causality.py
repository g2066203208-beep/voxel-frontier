#!/usr/bin/env python3
"""All 36 OpenFAST archived originals: legacy rainflow versus one-line fix and
independent rainflow 3.2.0. SHA-locked source; 72 load channel results.
No OpenFAST production simulation, no Abaqus, no material-fatigue life.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct
import zipfile
from collections import Counter

HERE=Path(__file__).resolve().parent
WT=HERE.parents[1]
SUP=WT/"archive/local-assets-20261004-supplement"
OLD_MANIFEST=WT/"archive/local-assets-20261004/file-manifest.json"
from t062_legacy_rainflow_root_cause_gate import historical_func,table,multiset,delm4
from s06_historical_outb_source_gate import outb_header

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_case(entry):
    archive=SUP/"openfast-36-r2"/entry["archive"].split("/")[-1]
    member=entry["relative_path"]
    with zipfile.ZipFile(archive) as z:
        bad=z.testzip()
        if bad:raise ValueError("BAD_ORIGINAL_OUTB_ZIP_CRC:"+str(bad))
        raw=z.read(member)
    if len(raw)!=int(entry["bytes"]) or sha(raw)!=entry["sha256"].lower():
        raise ValueError("ORIGINAL_OUTB_SOURCE_SHA_MISMATCH:"+member)
    h=outb_header(raw)
    if h["file_id"]!=4 or h["num_samples"]!=12001 or abs(h["first_time_s"]-100)>1e-8 or abs(h["time_increment_s"]-.05)>1e-9:
        raise ValueError("OUTB_GRID_WRONG:"+member)
    values={}
    nc=h["num_output_channels"]
    for channel in ("TwrBsMxt","TwrBsMyt"):
        col=h["channel_names"].index(channel)-1
        off=h["column_offsets"][col];scl=h["column_scales"][col]
        if scl==0:raise ValueError("OUTPUT_SCALE_ZERO:"+member)
        values[channel]=[(struct.unpack_from("<h",raw,h["data_offset_bytes"]+2*(i*nc+col))[0]-off)/scl for i in range(h["num_samples"])]
    return values,sha(raw)

def out_csv(rows,fieldnames):
    import io
    dst=io.StringIO(newline="")
    w=csv.DictWriter(dst,fieldnames=fieldnames,lineterminator="\n")
    w.writeheader();w.writerows(rows)
    return dst.getvalue().encode()

def run():
    import rainflow
    if rainflow.__version__!="3.2.0":raise ValueError("REFERENCE_VERSION_CHANGED")
    orig=historical_func(False);patched=historical_func(True)
    current=json.loads((SUP/"file-manifest.json").read_text())
    legacy=json.loads(OLD_MANIFEST.read_text())
    current_entries=sorted([e for e in current if e.get("section")=="openfast-36-r2"
                         and e.get("relative_path","").endswith("/DTU_10MW_RWT.outb")],key=lambda e:e["relative_path"])
    if len(current_entries)!=36:raise ValueError("OUTB_NOT_36")
    legacy_manifest_verified=json.loads((HERE/"legacy-primary-recovered-20261102/LEGACY_PRIMARY_RECOVERY_RECEIPT_20261102.json").read_text())
    if legacy_manifest_verified["matched_old_current_outb"]!=36 or legacy_manifest_verified["different_old_current_outb"]!=0:
        raise ValueError("LEGACY_SOURCE_IDENTITY_NOT_PROVEN")
    old_table=table(HERE/"legacy-primary-recovered-20261102/05_LOAD_DEL_M4_ALL36.csv","DEL_load_comparison")
    ref_table=table(HERE/"recomputed-load-fatigue/05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv","DEL")
    result=[]
    for e in current_entries:
        case=e["relative_path"].split("/")[1]
        series_map,hashvalue=read_case(e)
        for channel in ("TwrBsMxt","TwrBsMyt"):
            values=series_map[channel]
            old=orig(values)
            corr=patched(values)
            reference=[(float(r),float(m),float(n)) for r,m,n,i,j in rainflow.extract_cycles(values) if r>0]
            if multiset(corr)!=multiset(reference):
                raise AssertionError("CYCLE_MULTISETS_DIFFER:"+case+"_"+channel)
            d1,d2,d3=delm4(old),delm4(corr),delm4(reference)
            h=old_table[case,channel];n=ref_table[case,channel]
            if abs(d1-h)>1e-5 or abs(d2-n)>1e-5 or abs(d3-n)>1e-5:
                raise AssertionError("DEL_REPRODUCTION_FAILED:"+case+"_"+channel+
                    " values="+str((d1,h,d2,n,d3)))
            old_n=sum(c[2] for c in old);ref_n=sum(c[2] for c in reference)
            if abs(old_n-ref_n)>1e-9:
                raise AssertionError("WEIGHT_SUM_CHANGED:"+case+"_"+channel)
            result.append({"case":case,"channel":channel,"outb_sha256":hashvalue,
               "original_legacy_DEL_kNm":format(d1,".12f"),
               "original_legacy_CSV_DEL_kNm":format(h,".12f"),
               "one_line_fixed_DEL_kNm":format(d2,".12f"),
               "third_party_reference_DEL_kNm":format(d3,".12f"),
               "independent_current_CSV_DEL_kNm":format(n,".12f"),
               "old_rows":len(old),"fixed_rows":len(corr),
               "ref_rows":len(reference),"weighted_cycle_count":old_n,
               "original_minus_corrected_DEL_kNm":format(d1-d2,".12f")})
    if len(result)!=72:raise ValueError("RESULT_NOT_72")
    oldtop=sorted(result,key=lambda x:-float(x["original_legacy_DEL_kNm"]))[0]
    newtop=sorted(result,key=lambda x:-float(x["one_line_fixed_DEL_kNm"]))[0]
    rec={"status":"T062_ALL_36_OUTB_72_CHANNEL_OLD_RAINFLOW_BUG_CAUSALLY_VERIFIED",
       "outb_cases":36,"del_channels":72,"same_sha_old_vs_current_OUTB":36,
       "historical_code_sha256":"b7c2d50b391d90f69fef6aa72e5bdf4be5a843c72b4460147145a0df14110649",
       "old_source_manifest_sha256":sha(OLD_MANIFEST.read_bytes()),
       "current_source_manifest_sha256":sha((SUP/"file-manifest.json").read_bytes()),
       "reference":"third-party independently published rainflow 3.2.0, pinned wheel SHA256 cb6c254aa1a16a9e658ff3f39c6e5a77650d6c4e8304146169b36516d1f01660",
       "one_line_cause":"legacy X=old range/Y=new range; 'if X<Y:break' reversed; correct 'if Y<X:break' in memory only",
       "all_72_original_DEL_match_legacy_05":True,
       "all_72_one_line_fixed_DEL_match_T062_new":True,
       "all_72_corrected_full_cycle_multisets_match_reference":True,
       "all_72_weighted_count_conserved":True,
       "legacy_max_global":{"case":oldtop["case"],"channel":oldtop["channel"],"del_kNm":oldtop["original_legacy_DEL_kNm"]},
       "corrected_max_global":{"case":newtop["case"],"channel":newtop["channel"],"del_kNm":newtop["one_line_fixed_DEL_kNm"]},
       "min_legacy_to_corrected_ratio":min(float(x["original_legacy_DEL_kNm"])/float(x["one_line_fixed_DEL_kNm"]) for x in result),
       "max_legacy_to_corrected_ratio":max(float(x["original_legacy_DEL_kNm"])/float(x["one_line_fixed_DEL_kNm"]) for x in result),
       "source_reading_level":"36 actual FileID4 12001-sample archived original OUTB bytes each SHA+CRC checked; original September rainflow exact AST with hash; installed independent 3.2.0",
       "SOURCE":"primary archived original script and old DEL/embedded SHA; supplement 36 original OUTB independently verified",
       "REF":"historical Word load-level claim and T062 archival independently recalculated DEL",
       "STANDARD":"No authorized ASTM/IEC/GB design clause inspected, algorithm implementation only",
       "OFFICIAL":"original OpenFAST v3.5.3 files, no production solver",
       "RUN":"GitHub Actions 72-case-channel original/fixed/independent algorithm postprocess",
       "FIG":"Update Chapter 3 figure to mark previous wrong historical algorithm, not distinct raw source",
       "TAB":"complete per-case and per-channel 72-row reference comparison",
       "error_budget":"DEL <=1e-5 kN-m absolute, cycle range/mean multiset rounded 1e-8, source raw int16 quantization unchanged; structural/material physical uncertainty not closed",
       "HOLD":"Only load-level rainflow algorithm corrected. DLC1.2 coverage and material fatigue life remain unverified",
       "physical_pass":False,"material_life_pass":False}
    fields=list(result[0])
    csvdata=out_csv(result,fields)
    rec["all_72_comparison_csv_sha256"]=sha(csvdata)
    return csvdata,(json.dumps(rec,indent=2,ensure_ascii=False,sort_keys=True)+"\n").encode()

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output-dir",type=Path,required=True);args=ap.parse_args()
    csvdata,rec=run()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/"T062_ALL36_RAINFLOW_CAUSAL_DEL_COMPARE_20261102.csv").write_bytes(csvdata)
    (args.output_dir/"T062_ALL36_RAINFLOW_CAUSAL_RECEIPT_20261102.json").write_bytes(rec)
    print(rec.decode())

if __name__=="__main__":main()
