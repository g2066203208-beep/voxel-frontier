#!/usr/bin/env python3
"""S06: native 2 s real-ETM TP/RP/AL cross-batch admission, NOT physical load mapping.
Reads raw OpenFAST v3.5.3 OUTB and SHA-locked derived ElastoDyn input per batch.
The RP angle triplet is not a direction cosine matrix (DCM).
"""
import argparse
import hashlib
import json
from pathlib import Path
from s06_historical_outb_source_gate import outb_header
from s06_native_4batch_common_channel_qc import decode, within_quant, overlap_topology
from s06_etm_2s_native_overlap import CASE, BTS_SHA, SAMPLES, DT_OUT, DURATION

ED = "DTU_10MW_RWT_ElastoDyn.dat"
SUFFIX = ("TPxi","TPyi","RPxi","RPyi","RPzi","ALxt","ALyt","ALzt")
PARENTS = {
"e8c1653486cc96eaa5f32a28b01701df080bd2f185f851abd4ebf54a13ef23c7",
"7cce15fcb6ef0a0e6f9138850e4c66745450655d50d1ee59a7171b1e1530ce0f",
"bd59ed51c843f1ca9e82b2d3cd1441b2055e2b222a36636becc31bd54400c060",
"4c524f1e524d049c816f5fa44dea01f9c1d8e3a2e8cf34ca13ff45487655c4c7"
}
def sha(b):
    return hashlib.sha256(b).hexdigest()

def reject(condition, name):
    if not condition:
        raise ValueError(name)

def qc(root, destination):
    entries=[]
    for batch in range(1,5):
        p=Path(root)/f"batch{batch}"
        receipt=json.loads((p/"S06_0P1S_PREP_RECEIPT.json").read_text(encoding="utf-8"))
        reject(receipt["case"]==CASE and receipt["TMax_s"]==DURATION and receipt["DT_Out_s"]==DT_OUT and receipt["overlap_mode"] is True,"CASE_TIME_IDENTITY")
        reject(receipt["etm_s06_bts_original_sha256"]==BTS_SHA,"BTS_SHA")
        parent=receipt.get("pose_parent_sha256")
        child=receipt.get("pose_child_sha256")
        reject(parent in PARENTS and isinstance(child,str) and len(child)==64 and parent!=child,"ED_PARENT_CHILD_SHA")
        reject(sha((p/ED).read_bytes())==child and receipt["derived_sha256"][ED]==child,"ED_CHILD_BYTES")
        reject((p/"native_exit_code.txt").read_text().strip()=="0","NATIVE_EXIT")
        stdout=(p/"native_stdout.log").read_bytes()
        reject(b"OpenFAST terminated normally." in stdout,"NATIVE_TERMINATION")
        raw=(p/"DTU_10MW_RWT.outb").read_bytes()
        h=outb_header(raw)
        reject(h["file_id"]==4 and h["num_samples"]==SAMPLES and abs(h["time_increment_s"]-DT_OUT)<1e-10 and abs(h["first_time_s"])<1e-10,"OUTB_TIME")
        names=h["channel_names"]
        for gi in range(1,10):
            for suffix in (*SUFFIX,"TPzi","FLxt","FLyt","FLzt","MLxt","MLyt","MLzt"):
                reject(f"TwHt{gi}{suffix}" in names,"MISSING_CHANNEL_"+str(batch)+"_"+str(gi)+"_"+suffix)
        entries.append((receipt,raw,h,sha(stdout)))
    nodes=[e[0]["gage_nodes"] for e in entries]
    pairs=overlap_topology(nodes)
    reject([(a+1,b+1,n) for a,b,n in pairs]==[(1,2,220),(2,3,426),(3,4,633)],"OVERLAP_TOPOLOGY")
    for field in ("fst","ed","tower","servo","discon","dll","exe"):
        reject(len({e[0]["source_sha256"][field] for e in entries})==1,"ORIGINAL_ID_"+field)
    reject(len({e[0]["etm_s06_inflow_original_sha256"] for e in entries})==1,"INFLOW_ID")
    rows=[];failures=[]
    for left,right,node in pairs:
        li=nodes[left].index(node)+1
        ri=nodes[right].index(node)+1
        for suffix in SUFFIX:
            l=f"TwHt{li}{suffix}";r=f"TwHt{ri}{suffix}"
            hl=entries[left][2];hr=entries[right][2]
            ul=hl["channel_units"][hl["channel_names"].index(l)]
            ur=hr["channel_units"][hr["channel_names"].index(r)]
            reject(ul==ur,"UNIT_MISMATCH_"+suffix)
            maximum=0.;budget_max=0.
            for k in range(SAMPLES):
                va,qa=decode(entries[left][1],hl,l,k)
                vb,qb=decode(entries[right][1],hr,r,k)
                good,budget=within_quant(va,qa,vb,qb)
                maximum=max(maximum,abs(va-vb));budget_max=max(budget_max,budget)
                if not good:failures.append({"node":node,"suffix":suffix,"time_s":k*DT_OUT,"difference":abs(va-vb),"budget":budget})
            rows.append({"node":node,"pair":f"{left+1}-{right+1}","suffix":suffix,"unit":ul,"max_abs_delta":maximum,"max_quant_budget":budget_max})
    result={
      "stage":"S06/S07","status":"POSE_CHANNEL_NUMERIC_PARITY_PASS_PHYSICAL_HOLD" if not failures else "POSE_CHANNEL_NUMERIC_PARITY_FAIL",
      "case":CASE,"samples":SAMPLES,"dt_s":DT_OUT,"TMax_s":DURATION,
      "bts_sha256":BTS_SHA,"original_input_sha256":entries[0][0]["source_sha256"],
      "parent_ed_sha256":[e[0]["pose_parent_sha256"] for e in entries],
      "child_ed_sha256":[e[0]["pose_child_sha256"] for e in entries],
      "outb_sha256":[sha(e[1]) for e in entries],
      "stdout_sha256":[e[3] for e in entries],
      "new_pose_channels_per_batch":72,"overlap_rows":rows,
      "overlap_comparisons":len(rows)*SAMPLES,"failure_count":len(failures),"failures":failures[:20],
      "SOURCE":"Four actual SHA-locked original OpenFAST v3.5.3 2s ETM input batches and decoded native OUTB",
      "REF":"Existing T062 gage mapping; no new journal original pages",
      "STANDARD":"No authorized IEC/GB/NB clauses read; no standards acceptance",
      "OFFICIAL":"OpenFAST v3.5.3 tagged ElastoDyn.f90/ElastoDyn_IO.f90 output semantics",
      "RUN":"Four 2s real ETM native diagnostics; only if runner logs and hashes present",
      "FIG":"none","TAB":"24 overlap rows x 41 times = 984 comparisons",
      "assumptions":"Output suffixes correspond to same physical tower nodes; RP are angular-position components in deg, not exact DCM",
      "error_budget":"1.1*(two packed OUTB half-LSB)+1e-8 per compared channel; physical pose/DCM and inertial force uncertainty unbounded",
      "HOLD":"0-2s startup only; no exact DCM, 100-700s proof, inertial ownership, 31-station global wrench, Abaqus, E/WE or fatigue life",
      "physical_pass":False
    }
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("S06_ETM_POSE_QC",json.dumps({"status":result["status"],"comparisons":result["overlap_comparisons"],"failures":result["failure_count"]}))
    reject(not failures,"POSE_NUMERIC_PARITY_FAIL")
    return result

def selftest():
    reject(len(SUFFIX)==8 and len(set(SUFFIX))==8,"SUFFIX_CARDINALITY")
    reject(len(PARENTS)==4,"PARENT_SHA_CARDINALITY")
    for name,invalid in (("SOURCE",False),("UNIT",0),("FINITE",float("nan"))):
        try: reject(invalid,name)
        except ValueError: pass
        else: raise AssertionError("NEGATIVE_REJECTION_FAILURE_"+name)
    print("POSE_SELFTEST_PASS 8_suffixes 4_parents 3_rejections")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true");p.add_argument("--qc",action="store_true")
    p.add_argument("--root");p.add_argument("--receipt")
    a=p.parse_args()
    if a.selftest:selftest()
    elif a.qc and a.root and a.receipt:qc(a.root,a.receipt)
    else:p.error("Use --selftest or --qc --root --receipt")
