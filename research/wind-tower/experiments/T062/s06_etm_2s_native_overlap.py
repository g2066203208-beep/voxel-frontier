#!/usr/bin/env python3
"""S06: 2 s real ETM BTS, four native OpenFAST overlap batches (DIAGNOSTIC ONLY).
Uses the SHA-pinned T062 158 m preparer; never launches 700 s production.
Requires exact original U09p343881_ETM_S06 BTS; no synthesized wind.
Python 3.11 stdlib; independent 41-point packed-OUTB quantization QC.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import zipfile

from s06_ntm_native_0p1s_probe import prepare as prepare_steady, replace_scalar, digest
from s06_historical_outb_source_gate import outb_header
from s06_native_4batch_common_channel_qc import (
    decode, within_quant, overlap_topology, SUFFIX, BASE
)

CASE = "U09p343881_ETM_S06"
BTS_SHA = "ad68a83a63f197c528c07502db8adff883e9c737863ef3c4cab99cfa76052147"
SAMPLES = 41
DT_OUT = 0.05
DURATION = 2.0

def read_etm_inflow(archive1, archive2):
    member = "CASES/" + CASE + "/DTU_10MW_InflowWind.dat"
    for src in (archive1, archive2):
        with zipfile.ZipFile(src) as z:
            if member in z.namelist():
                return z.read(member)
    raise ValueError("ETM_S06_INFLOW_SOURCE_MISSING")

def patch_bts_path(s):
    pattern = r'(?m)^\\s*"[^"\\r\\n]*U09p343881_ETM_S06\\.bts"\\s+FileName_BTS\\b'
    changed, n = re.subn(pattern, '"U09p343881_ETM_S06.bts" FileName_BTS', s)
    if n != 1:
        raise ValueError("ETM_S06_BTS_FIELD_CARDINALITY_" + str(n))
    return changed

def prep(args):
    if not args.overlap or args.batch not in (1, 2, 3, 4):
        raise ValueError("ETM_2S_REQUIRES_FOUR_OVERLAP_BATCHES")
    bts = Path(args.bts)
    if not bts.is_file():
        raise ValueError("REAL_BTS_MISSING")
    bts_sha = digest(bts.read_bytes())
    if bts_sha != BTS_SHA:
        raise ValueError("REAL_BTS_SHA256_MISMATCH " + bts_sha)
    # The original T062 preparer verifies FST, ED, tower, controller, executable
    # and archive bytes, then copies all rotor and controller dependencies.
    prepare_steady(args)
    out = Path(args.outdir)
    fst = out / "DTU_10MW_RWT.fst"
    fst.write_text(replace_scalar(fst.read_text(encoding="utf-8"), "TMax", "2.0", expected="0.1"), encoding="utf-8")
    original = read_etm_inflow(args.archive1, args.archive2)
    etm_sha = digest(original)
    inflow = original.decode("utf-8-sig").replace("\\r\\n", "\\n")
    inflow = replace_scalar(inflow, "WindType", "3", expected="3")
    inflow = patch_bts_path(inflow)
    (out / "DTU_10MW_InflowWind.dat").write_text(inflow, encoding="utf-8")
    (out / (CASE + ".bts")).write_bytes(bts.read_bytes())
    receipt = out / "S06_0P1S_PREP_RECEIPT.json"
    r = json.loads(receipt.read_text(encoding="utf-8"))
    r.update({
        "case": CASE, "wind": "REAL_ETM_S06_BTS_2S_DIAGNOSTIC",
        "TMax_s": DURATION, "DT_Out_s": DT_OUT, "expected_samples": SAMPLES,
        "etm_s06_inflow_original_sha256": etm_sha,
        "etm_s06_bts_original_sha256": bts_sha,
        "derived_sha256": {**r["derived_sha256"],
            "DTU_10MW_RWT.fst": digest(fst.read_bytes()),
            "DTU_10MW_InflowWind.dat": digest((out / "DTU_10MW_InflowWind.dat").read_bytes())},
        "modifications": [
            "T062 SHA-verified original source restored",
            "TMax=2s, TStart=0; four overlapping gage batches",
            "Replace STEADY diagnostic InflowWind with original ETM_S06 WindType=3 and local BTS filename",
            "Use byte-verified original S06 BTS; no interpolation or synthesized wind"],
        "RUN": "2s real ETM native pilot pending", "physical_pass": False,
        "HOLD": "Startup 0-2s not equilibrated 100-700s; not DLC1.2, full RP/TP/DCM, external force ownership, Abaqus, or fatigue PASS"
    })
    receipt.write_text(json.dumps(r, indent=2, ensure_ascii=False)+"\\n", encoding="utf-8")
    print("ETM_2S_PREP_PASS", json.dumps({"batch":args.batch,"bts_sha256":bts_sha,"etm_inflow_sha256":etm_sha,"derived_sha256":r["derived_sha256"]}))

def selftest():
    assert len(BTS_SHA) == 64
    assert patch_bts_path('"/old/U09p343881_ETM_S06.bts" FileName_BTS') == '"U09p343881_ETM_S06.bts" FileName_BTS'
    for bad in ('"other.bts" FileName_BTS', '"x/U09p343881_ETM_S06.bts" FileName_BTS\\n"x/U09p343881_ETM_S06.bts" FileName_BTS'):
        try: patch_bts_path(bad)
        except ValueError: pass
        else: raise AssertionError("BAD_BTS_CARDINALITY_ACCEPTED")
    assert not within_quant(1, .001, 2, .001)[0]
    assert within_quant(1, .001, 1.001, .001)[0]
    print("ETM_2S_SELFTEST_PASS BTS_cardinality duplicate_rejection packed_quantization")

def qc(root, dest):
    data = []
    for batch in range(1, 5):
        p = Path(root) / ("batch" + str(batch))
        r = json.loads((p / "S06_0P1S_PREP_RECEIPT.json").read_text(encoding="utf-8"))
        if (r["case"],r["TMax_s"],r["DT_Out_s"],r["overlap_mode"]) != (CASE,DURATION,DT_OUT,True):
            raise ValueError("PREP_CONTRACT_MISMATCH_BATCH_" + str(batch))
        if r["etm_s06_bts_original_sha256"] != BTS_SHA:
            raise ValueError("BTS_SOURCE_MISMATCH")
        if (p / "native_exit_code.txt").read_text().strip() != "0":
            raise ValueError("NATIVE_EXIT_NONZERO")
        stdout = (p / "native_stdout.log").read_bytes()
        if b"OpenFAST terminated normally." not in stdout:
            raise ValueError("NATIVE_TERMINATION_MISSING")
        raw = (p / "DTU_10MW_RWT.outb").read_bytes()
        h = outb_header(raw)
        if h["file_id"] != 4 or h["num_samples"] != SAMPLES or abs(h["time_increment_s"] - DT_OUT) > 1e-10 or abs(h["first_time_s"]) > 1e-10:
            raise ValueError("OUTB_TIME_GRID_BATCH_" + str(batch))
        for gi in range(1,10):
            for suffix in SUFFIX:
                if f"TwHt{gi}{suffix}" not in h["channel_names"]:
                    raise ValueError(f"MISSING_GAGE_{batch}_{gi}_{suffix}")
        data.append((r,raw,h,stdout))
    overlap_topology([x[0]["gage_nodes"] for x in data])
    for key in ("fst","ed","tower","servo","discon","dll","exe"):
        if len({x[0]["source_sha256"][key] for x in data}) != 1:
            raise ValueError("ORIGINAL_SOURCE_IDENTITY_" + key)
    for key in ("DTU_10MW_RWT.fst","DTU_10MW_InflowWind.dat","Control/libdiscon.dll"):
        if len({x[0]["derived_sha256"][key] for x in data}) != 1:
            raise ValueError("DERIVED_SOURCE_IDENTITY_" + key)
    if len({x[0]["etm_s06_inflow_original_sha256"] for x in data}) != 1:
        raise ValueError("ETM_INFLOW_SOURCE_IDENTITY")
    common = sorted(set.intersection(*(set(x[2]["channel_names"][1:]) for x in data)))
    common = [c for c in common if not re.match(r"^TwHt[0-9]+", c)]
    if not set(BASE).issubset(common) or len(common)<10:
        raise ValueError("COMMON_CHANNELS_MISSING")
    errors = []; common_rows=[]; overlap_rows=[]
    for channel in common:
        units = {x[2]["channel_units"][x[2]["channel_names"].index(channel)] for x in data}
        if len(units) != 1: raise ValueError("COMMON_UNIT_MISMATCH_" + channel)
        maximum = 0.; budget_max = 0.
        for k in range(SAMPLES):
            va,qa = decode(data[0][1],data[0][2],channel,k)
            for j in range(1,4):
                vb,qb = decode(data[j][1],data[j][2],channel,k)
                good,budget = within_quant(va,qa,vb,qb)
                maximum = max(maximum,abs(va-vb));budget_max=max(budget_max,budget)
                if not good:errors.append({"kind":"COMMON","channel":channel,"batch":j+1,"time_s":k*DT_OUT,"delta":abs(va-vb),"budget":budget})
        common_rows.append({"channel":channel,"unit":next(iter(units)),"max_abs_delta":maximum,"max_quant_budget":budget_max})
    for left,right,node in overlap_topology([x[0]["gage_nodes"] for x in data]):
        li = data[left][0]["gage_nodes"].index(node)+1
        ri = data[right][0]["gage_nodes"].index(node)+1
        for suffix in SUFFIX:
            name_l=f"TwHt{li}{suffix}";name_r=f"TwHt{ri}{suffix}"
            units={data[left][2]["channel_units"][data[left][2]["channel_names"].index(name_l)],
                   data[right][2]["channel_units"][data[right][2]["channel_names"].index(name_r)]}
            if len(units)!=1:raise ValueError("OVERLAP_UNIT_MISMATCH")
            maximum=0.;budget_max=0.
            for k in range(SAMPLES):
                va,qa=decode(data[left][1],data[left][2],name_l,k)
                vb,qb=decode(data[right][1],data[right][2],name_r,k)
                good,budget=within_quant(va,qa,vb,qb)
                maximum=max(maximum,abs(va-vb));budget_max=max(budget_max,budget)
                if not good:errors.append({"kind":"OVERLAP","node":node,"suffix":suffix,"time_s":k*DT_OUT,"delta":abs(va-vb),"budget":budget})
            overlap_rows.append({"node":node,"suffix":suffix,"pair":f"{left+1}-{right+1}","unit":next(iter(units)),"max_abs_delta":maximum,"max_quant_budget":budget_max})
    receipt = {
        "stage":"S06_2S_REAL_ETM_FOUR_BATCH_NATIVE_OVERLAP_DIAGNOSTIC",
        "status":"NUMERICAL_PARITY_PASS" if not errors else "HOLD_NUMERICAL_PARITY_FAIL",
        "case":CASE,"TMax_s":DURATION,"samples":SAMPLES,"dt_out_s":DT_OUT,
        "bts_sha256":BTS_SHA,"inflow_original_sha256":data[0][0]["etm_s06_inflow_original_sha256"],
        "original_input_sha256":data[0][0]["source_sha256"],
        "derived_input_sha256":[x[0]["derived_sha256"] for x in data],
        "outb_sha256":[digest(x[1]) for x in data],
        "native_stdout_sha256":[digest(x[3]) for x in data],
        "common_channel_count":len(common),"common_comparisons":len(common)*SAMPLES*3,
        "overlap_comparisons":len(overlap_rows)*SAMPLES,
        "max_common_delta":max(x["max_abs_delta"] for x in common_rows),
        "max_overlap_delta":max(x["max_abs_delta"] for x in overlap_rows),
        "common_table":common_rows,"overlap_table":overlap_rows,
        "failure_count":len(errors),"first_failures":errors[:30],
        "SOURCE":"Original SHA-pinned 158m FST/ED/Tower/ROSCO, original ETM_S06 InflowWind and BTS",
        "REF":"T062 original 31-gage contract; no new journal full text",
        "STANDARD":"No authorized IEC/GB/NB clauses read; no standards acceptance",
        "OFFICIAL":"Native OpenFAST v3.5.3 executable and original ROSCO controller",
        "RUN":"Four separate 2s native OpenFAST startup runs with identical BTS, 31 distinct CSEG gages and 3 overlapping boundary nodes",
        "FIG":"none","TAB":"common_table; overlap_table; exact comparison counts",
        "error_budget":"Per comparison 1.1*(packed OUTB half-LSB from both outputs)+1e-8, channel units; no dynamic or structural uncertainty bound",
        "HOLD":"0-2s startup only; 100-700s physical synchronization, RP/TP/DCM, load/inertia ownership, DLC1.2, Abaqus and material fatigue not accepted",
        "physical_pass":False
    }
    Path(dest).parent.mkdir(parents=True,exist_ok=True)
    Path(dest).write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\\n",encoding="utf-8")
    print("ETM_2S_NATIVE_OVERLAP_QC",json.dumps({"status":receipt["status"],"common_comparisons":receipt["common_comparisons"],"overlap_comparisons":receipt["overlap_comparisons"],"failures":len(errors)}))
    if errors: raise ValueError("REAL_ETM_2S_CROSS_BATCH_PARITY_FAIL")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selftest",action="store_true")
    ap.add_argument("--prepare",action="store_true")
    ap.add_argument("--qc",action="store_true")
    for arg in ("archive1","archive2","supp","dll","exe","contract","outdir","bts","root","receipt"):
        ap.add_argument("--"+arg)
    ap.add_argument("--batch",type=int,default=1)
    ap.add_argument("--overlap",action="store_true")
    args=ap.parse_args()
    if args.selftest:selftest()
    elif args.prepare:prep(args)
    elif args.qc:qc(args.root,args.receipt)
    else:ap.error("Choose --selftest, --prepare, or --qc")
if __name__=="__main__":main()
