#!/usr/bin/env python3
"""S07 minimal RP/TP recovery contract for the archived T071/T072 31-gage runs.

Source audit and synthetic tests need Python 3.11 standard library only.
A future --capture reads an EXISTING OUTB using openfast_toolbox; it never
starts OpenFAST. RP is NOT a generic Euler angle; no Abaqus load is exported.
"""
import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import sys

T071_BLOB = "59e76a54ba4f64902ed0750e92eb5158a1da1e96"
T072_BLOB = "5baab0ea2299b6d36544b6d092f7503d8dcaf86c"
ED_BASE_SHA256 = "6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65"
CASES = ("U09p343881_ETM_S06", "U11p4_ETM_S04",
         "U19p202140_ETM_S04", "U19p202140_ETM_S06")
BATCHES = {
    "A": ((13,39,65,91,117,142,168,194,220), tuple(range(1,10))),
    "B": ((246,271,297,323,349,375,400,426,452), tuple(range(10,19))),
    "C": ((478,504,529,555,581,607,633,658,684), tuple(range(19,28))),
    "D": ((710,736,762,784,810,850,900,1000,1120),
          (28,29,30,31,"EX1","EX2","EX3","EX4","EX5")),
}
SUFFIX_UNIT = {
    "RPxi": "deg", "RPyi": "deg", "RPzi": "deg",
    "TPxi": "m", "TPyi": "m", "TPzi": "m",
}
# The additional channels are synchronized *internal section resultants* and
# local accelerations. They are NOT applied external forces or a global DCM.
DIAG_SUFFIX_UNIT = {
    "ALxt":"m/s^2", "ALyt":"m/s^2", "ALzt":"m/s^2",
    "FLxt":"kN", "FLyt":"kN", "FLzt":"kN",
    "MLxt":"kN-m", "MLyt":"kN-m", "MLzt":"kN-m",
}
DIAG_FIELDS = ("ALxt_mps2","ALyt_mps2","ALzt_mps2",
               "FLxt_kN","FLyt_kN","FLzt_kN",
               "MLxt_kNm","MLyt_kNm","MLzt_kNm")
FIELDS = ("case","batch","segment","gage_index","time_s",
          "RPxi_deg","RPyi_deg","RPzi_deg","TPxi_m","TPyi_m","TPzi_m")


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def source_gate(t071, t072):
    """Verify ORIGINAL committed workflow bytes and exact batch/node identity."""
    raw_a, raw_b = Path(t071).read_bytes(), Path(t072).read_bytes()
    if git_blob(raw_a) != T071_BLOB or git_blob(raw_b) != T072_BLOB:
        raise ValueError("S07_SOURCE_WORKFLOW_GIT_BLOB_MISMATCH")
    a, b = raw_a.decode("utf-8-sig"), raw_b.decode("utf-8-sig")
    for label, src in (("T071",a),("T072",b)):
        for required in ("TwrGagNd patch failed", "DTU_10MW_RWT.outb",
                         "FASTOutputFile", "path: extract/*"):
            if required not in src:
                raise ValueError("S07_SOURCE_CONTRACT_MISSING_"+label+"_"+required)
        if "OutList" in src or any(x in src for x in ("RPxi","RPyi","RPzi")):
            raise ValueError("S07_HISTORICAL_WORKFLOW_NOT_UNCHANGED_"+label)
    for batch,(nodes,segments) in BATCHES.items():
        m = re.search(r"- batch:\s*"+batch+
                      r"\s*\n\s*nodes:\s*\"([0-9,]+)\""+
                      r"\s*\n\s*segments:\s*\"([0-9A-Z,]+)\"", a)
        if m is None:
            raise ValueError("S07_T071_BATCH_MISSING_"+batch)
        got_nodes = tuple(int(x) for x in m.group(1).split(","))
        got_segments = tuple(int(x) if x.isdigit() else x
                             for x in m.group(2).split(","))
        if got_nodes != nodes or got_segments != segments:
            raise ValueError("S07_T071_GAGE_MAP_CHANGED_"+batch)
        n = re.search(r'(?m)^\s*"'+batch+r'":\(\[([0-9,]+)\],', b)
        if n is None or tuple(int(x) for x in n.group(1).split(",")) != nodes:
            raise ValueError("S07_T072_GAGE_MAP_CHANGED_"+batch)
    valid = sum(sum(isinstance(s,int) for s in x[1]) for x in BATCHES.values())
    assert valid == 31
    return {
        "stage":"S07_MINIMAL_RPTP_CAPTURE_CONTRACT_TESTED_NOT_DATA_RECOVERED",
        "SOURCE":{
            "reading_level":"Original T071/T072 full committed workflow text; no 31-gage OUTB bytes",
            "t071_git_blob_sha1":T071_BLOB, "t072_git_blob_sha1":T072_BLOB,
            "t071_sha256":hashlib.sha256(raw_a).hexdigest(),
            "t072_sha256":hashlib.sha256(raw_b).hexdigest(),
            "baseline_elastodyn_sha256":ED_BASE_SHA256},
        "REF":"Existing OpenFAST v3.5.3 ElastoDyn and 9-gage source-derived DCM receipt; no new paper full text",
        "STANDARD":"No newly read authorized IEC/GB/NB clauses",
        "OFFICIAL":"Historical GitHub Actions workflow bytes, NOT official native solver validation",
        "RUN":{"kind":"Static source audit + synthetic extractor tests only",
               "new_openfast_runs":0,"new_abaqus_runs":0},
        "FIG":"NONE: no physical-response plot",
        "TAB":{"cases":4,"batches_per_case":4,"valid_gages_per_case":31,
               "valid_series":124,"expected_samples_per_series":12001,
               "expected_new_rows":1488124,
               "new_RP_TP_components_per_row":6,
               "expected_new_RP_TP_scalar_positions":8928744,
               "time_start_s":100.0,"time_end_s":700.0,"dt_s":0.05,
               "required_suffix_units":SUFFIX_UNIT,
               "batch_gage_map":{k:{"nodes":v[0],"segments":v[1]}
                                 for k,v in BATCHES.items()}},
        "error_budget":{
            "static_identity":"Exact Git blob + exact integer node/segment mapping",
            "time_grid":"Absolute 1e-4 s acceptance for packed 0.05 s time grid",
            "RP_TP_physics":"UNBOUNDED until original 31-gage OUTB and v3.5.3 source-based inversion are checked",
            "external_load_ownership":"UNVERIFIED; internal section resultants cannot be applied as external loads"},
        "HOLD":"No archived 31-gage OUTB/RP/TP. This only specifies a fail-closed extraction of EXISTING OUTB; any OpenFAST rerun requires explicit approval. RP is not generic Euler. No signed free-body, gravity/inertia/RNA allocation, or Abaqus load export."
    }


def verify_patched_elastodyn(baseline, run_input, batch,
                             expected_baseline_sha256=ED_BASE_SHA256):
    """Check exact 31-gage node map and that ONLY TwrGagNd changed.

    This is input provenance, not proof an arbitrary OUTB was produced by it.
    The actual run/OUTB association still requires original job evidence.
    """
    if batch not in BATCHES:
        raise ValueError("S07_UNKNOWN_BATCH_FOR_ELASTODYN")
    baseline_sha = sha256_file(baseline)
    if baseline_sha != expected_baseline_sha256:
        raise ValueError("S07_BASELINE_ELASTODYN_SHA256_MISMATCH")
    base_lines = Path(baseline).read_text(encoding="utf-8-sig").splitlines()
    run_lines = Path(run_input).read_text(encoding="utf-8-sig").splitlines()
    if len(base_lines) != len(run_lines):
        raise ValueError("S07_ELASTODYN_UNEXPECTED_LINE_COUNT")
    pattern = re.compile(r"^\s*([0-9]+(?:\s*,\s*[0-9]+)*)\s+TwrGagNd\b")
    base_gages = [(i,tuple(int(n) for n in m.group(1).split(",")))
                  for i,line in enumerate(base_lines)
                  if (m := pattern.search(line))]
    run_gages = [(i,tuple(int(n) for n in m.group(1).split(",")))
                 for i,line in enumerate(run_lines)
                 if (m := pattern.search(line))]
    if len(base_gages)!=1 or base_gages[0][1]!=(1,3,5,7,9,13,15,17,20):
        raise ValueError("S07_BASELINE_GAGE_MAP_UNEXPECTED")
    if len(run_gages)!=1 or run_gages[0][0]!=base_gages[0][0]:
        raise ValueError("S07_PATCHED_GAGE_LINE_MISSING_OR_MOVED")
    if run_gages[0][1]!=BATCHES[batch][0]:
        raise ValueError("S07_PATCHED_GAGE_MAP_MISMATCH")
    changes=[i for i,(a,b) in enumerate(zip(base_lines,run_lines)) if a!=b]
    if changes != [base_gages[0][0]]:
        raise ValueError("S07_ELASTODYN_PHYSICS_CHANGED_OUTSIDE_GAGE_LINE")
    return {"baseline_elastodyn_sha256":baseline_sha,
            "patched_elastodyn_sha256":sha256_file(run_input),
            "verified_tower_gage_nodes":list(run_gages[0][1]),
            "changed_lines":1,
            "provenance_limit":"No original native run-log/OUTB-input binding established"}


def channel(data, prefix, unit):
    cols = list(data.keys()) if isinstance(data,dict) else list(data.columns)
    found = [name for name in cols if name.startswith(prefix)
             and (name == prefix or name[len(prefix)] in "_([")]
    if len(found) != 1:
        raise ValueError("S07_MISSING_OR_AMBIGUOUS_CHANNEL_"+prefix)
    name = found[0]
    if ("["+unit+"]" not in name and "("+unit+")" not in name):
        raise ValueError("S07_UNIT_NOT_VERIFIED_"+prefix)
    return data[name]


def extract_rows(data, case, batch, expected_n=12001, include_diagnostics=False):
    """Yield synchronized RP/TP, optionally AL/FL/ML; NO load ownership claim."""
    if case not in CASES or batch not in BATCHES:
        raise ValueError("S07_UNKNOWN_CASE_OR_BATCH")
    t = channel(data,"Time","s")
    if len(t) != expected_n:
        raise ValueError("S07_WRONG_TIME_COUNT")
    times = [float(x) for x in t]
    for i,v in enumerate(times):
        if not math.isfinite(v) or abs(v-(100.0+0.05*i))>1e-4:
            raise ValueError("S07_BAD_TIME_GRID")
    for gi,seg in enumerate(BATCHES[batch][1],1):
        if not isinstance(seg,int):
            continue
        required = dict(SUFFIX_UNIT)
        if include_diagnostics:
            required.update(DIAG_SUFFIX_UNIT)
        values = [channel(data,"TwHt"+str(gi)+suffix,unit)
                  for suffix,unit in required.items()]
        if any(len(v)!=expected_n for v in values):
            raise ValueError("S07_GAGE_LENGTH_MISMATCH")
        for i,time_s in enumerate(times):
            q = [float(v[i]) for v in values]
            if not all(math.isfinite(x) for x in q):
                raise ValueError("S07_NONFINITE_RP_TP")
            yield (case,batch,"CSEG_%02d"%seg,gi,time_s,*q)


def selftest():
    case = CASES[0]
    n=3
    data={"Time_[s]":[100.0,100.05,100.10]}
    for gi in range(1,10):
        for suffix,unit in SUFFIX_UNIT.items():
            data["TwHt%d%s_[%s]"%(gi,suffix,unit)] = [float(gi+j) for j in range(n)]
    # Synthetic 9-gage source with exactly the channel suffix/unit convention
    # independently seen in the archived T062 original OUTB receipt.
    for gi in range(1,10):
        for suffix,unit in DIAG_SUFFIX_UNIT.items():
            data["TwHt%d%s_(%s)"%(gi,suffix,unit)] = [float(10*gi+j) for j in range(n)]
    rows=list(extract_rows(data,case,"A",expected_n=n))
    paired=list(extract_rows(data,case,"A",expected_n=n,
                             include_diagnostics=True))
    assert len(paired)==27 and len(paired[0])==len(FIELDS)+len(DIAG_FIELDS)
    assert paired[0][-9:]==tuple([10.0]*9)
    assert paired[-1][-1]==92.0
    assert len(rows)==27 and rows[0][2]=="CSEG_01"
    assert rows[-1][2]=="CSEG_09" and rows[-1][4]==100.1
    faults=("missing","unit","time","nan","length","case","ambiguous")
    for fault in faults:
        bad={k:list(v) for k,v in data.items()}
        c=case
        if fault=="missing": del bad["TwHt1RPxi_[deg]"]
        elif fault=="unit":
            bad["TwHt1RPxi_[rad]"]=bad.pop("TwHt1RPxi_[deg]")
        elif fault=="time": bad["Time_[s]"][1]=100.07
        elif fault=="nan": bad["TwHt1RPxi_[deg]"][0]=float("nan")
        elif fault=="length": bad["TwHt1RPxi_[deg]"].pop()
        elif fault=="case": c="INVALID_CASE"
        else: bad["TwHt1RPxi_(deg)"]=list(bad["TwHt1RPxi_[deg]"])
        try:
            list(extract_rows(bad,c,"A",expected_n=n))
        except ValueError:
            pass
        else:
            raise AssertionError("S07_FAULT_NOT_REJECTED_"+fault)
    # Fail closed if any diagnostic channel is absent, mislabeled or nonfinite.
    for fault in ("missing_AL","bad_ML_unit","nonfinite_FL","short_AL"):
        bad={k:list(v) for k,v in data.items()}
        if fault=="missing_AL": del bad["TwHt1ALxt_(m/s^2)"]
        elif fault=="bad_ML_unit":
            bad["TwHt1MLxt_(Nm)"]=bad.pop("TwHt1MLxt_(kN-m)")
        elif fault=="nonfinite_FL": bad["TwHt1FLxt_(kN)"][0]=float("nan")
        else: bad["TwHt1ALxt_(m/s^2)"].pop()
        try: list(extract_rows(bad,case,"A",expected_n=n,
                               include_diagnostics=True))
        except ValueError: pass
        else: raise AssertionError("S07_PAIRED_FAULT_NOT_REJECTED_"+fault)
    # An unrelated 9-gage OUTB must not be relabeled as 31 concrete segments.
    # The actual original baseline SHA is exercised separately by CI.
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        base=Path(d)/"base.dat"; patched=Path(d)/"run.dat"
        base.write_text("header\n1,3,5,7,9,13,15,17,20  TwrGagNd  - source\nfooter\n")
        patched.write_text("header\n"+",".join(map(str,BATCHES["A"][0]))+
                           "  TwrGagNd  - T071\nfooter\n")
        got=verify_patched_elastodyn(base,patched,"A",sha256_file(base))
        assert got["verified_tower_gage_nodes"]==list(BATCHES["A"][0])
        for fault in ("swapped_batch","physics_change","extra_line","bad_base_sha"):
            if fault=="swapped_batch":
                op=lambda: verify_patched_elastodyn(base,patched,"B",sha256_file(base))
            elif fault=="physics_change":
                patched.write_text(patched.read_text().replace("footer","changed"))
                op=lambda: verify_patched_elastodyn(base,patched,"A",sha256_file(base))
            elif fault=="extra_line":
                patched.write_text(patched.read_text()+"extra\n")
                op=lambda: verify_patched_elastodyn(base,patched,"A",sha256_file(base))
            else:
                op=lambda: verify_patched_elastodyn(base,patched,"A","0"*64)
            try: op()
            except ValueError: pass
            else: raise AssertionError("S07_PROVENANCE_FAULT_NOT_REJECTED_"+fault)
            patched.write_text("header\n"+",".join(map(str,BATCHES["A"][0]))+
                               "  TwrGagNd  - T071\nfooter\n")
        fake=Path(d)/"fake.outb";fake.write_bytes(b"not an OUTB")
        for kwargs in (dict(),dict(expected_sha256="0"*64)):
            try: capture_existing_outb(fake,case,"A",Path(d)/"out.gz",**kwargs)
            except ValueError: pass
            else: raise AssertionError("S07_CAPTURE_WITHOUT_SOURCE_BINDING_ACCEPTED")
    return {"synthetic_valid_rows":27,"paired_synthetic_valid_rows":27,
            "paired_channels_per_gage":15,
            "negative_tests_passed":len(faults)+4+4+2,
            "native_solver_runs":0,"external_load_exports":0}


def capture_existing_outb(path, case, batch, output,
                          full_diagnostic=False, expected_sha256=None,
                          baseline_elastodyn=None, run_elastodyn=None):
    """Opt-in read of an EXISTING file; NEVER launches OpenFAST."""
    if not expected_sha256 or not re.fullmatch(r"[0-9a-f]{64}",expected_sha256):
        raise ValueError("S07_MANDATORY_ORIGINAL_OUTB_SHA256_REQUIRED")
    if baseline_elastodyn is None or run_elastodyn is None:
        raise ValueError("S07_MANDATORY_BASELINE_AND_PATCHED_ELASTODYN_REQUIRED")
    provenance=verify_patched_elastodyn(baseline_elastodyn,run_elastodyn,batch)
    source_sha=sha256_file(path)
    if source_sha!=expected_sha256:
        raise ValueError("S07_ORIGINAL_OUTB_SHA256_MISMATCH")
    try:
        from openfast_toolbox.io.fast_output_file import FASTOutputFile
    except ImportError as exc:
        raise RuntimeError("Install openfast_toolbox for existing OUTB reads") from exc
    df = FASTOutputFile(str(path)).toDataFrame()
    time_col = next((c for c in df.columns if c.startswith("Time")),None)
    if time_col is None:
        raise ValueError("S07_NO_TIME_COLUMN")
    # Original output is typically 0..700s; retain 100..700s only.
    window = df[(df[time_col]>=100.0-1e-4)&(df[time_col]<=700.0+1e-4)]
    out=Path(output)
    receipt_dest=out.with_name(out.name+".receipt.json")
    tmp=out.with_name(out.name+".tmp")
    protected={Path(x).resolve() for x in
               (path,baseline_elastodyn,run_elastodyn)}
    if any(x.resolve() in protected for x in (out,receipt_dest,tmp)):
        raise ValueError("S07_CAPTURE_OUTPUT_OVERLAPS_SOURCE")
    if any(x.exists() for x in (out,receipt_dest,tmp)):
        raise FileExistsError("S07_CAPTURE_WILL_NOT_OVERWRITE_EXISTING_OUTPUT")
    out.parent.mkdir(parents=True,exist_ok=True)
    count=0
    try:
        with gzip.open(tmp,"wt",newline="",encoding="utf-8") as f:
            writer=csv.writer(f,lineterminator="\n")
            writer.writerow(FIELDS+DIAG_FIELDS if full_diagnostic else FIELDS)
            for row in extract_rows(window,case,batch,
                                    include_diagnostics=full_diagnostic):
                writer.writerow(row)
                count+=1
        expected=12001*sum(isinstance(s,int) for s in BATCHES[batch][1])
        if count!=expected:
            raise ValueError("S07_WRONG_EXPORTED_ROW_COUNT")
        tmp.replace(out)
    finally:
        if tmp.exists(): tmp.unlink()
    receipt={"case":case,"batch":batch,"source_outb_sha256":source_sha,
             "expected_outb_sha256":expected_sha256,
             "elastodyn_input_provenance":provenance,
             "source_to_run_binding":"HOLD: independent original run evidence required",
             "diagnostic_channels_per_gage":15 if full_diagnostic else 6,
             "synchronized_acceleration_and_section_resultants":bool(full_diagnostic),
             "external_load_exports":0,"native_solver_runs":0,
             "source_outb_path":str(path),"output_sha256":sha256_file(out),
             "rows":count,"source_level":"EXISTING original OUTB read; no solver launched",
             "status":"S07_PAIRED_DIAGNOSTIC_CAPTURED_HOLD" if full_diagnostic
                      else "RP_TP_CAPTURED_NEEDS_DCM_AND_SIGNED_FREE_BODY",
             "HOLD":"Not an Abaqus external load; v3.5.3 DCM and inertia/gravity/RNA owner still need native checks"}
    receipt_path=out.with_name(out.name+".receipt.json")
    receipt_path.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    return receipt


def audit_original_nine_gage_receipt(path):
    """Validate the T062 OUTB-derived *receipt*, NOT the original OUTB bytes."""
    r=json.loads(Path(path).read_text(encoding="utf-8"))
    x=r["full_synchronous_native_series"]
    if (r["outb_sha256"]!=x["source_outb_sha256"] or
            x["gage_count"]!=9 or x["sample_count"]!=12001 or
            abs(x["time_start_s"]-100)>1e-8 or
            abs(x["time_end_s"]-700)>1e-8 or
            abs(x["time_increment_s"]-0.05)>1e-9):
        raise ValueError("S07_T062_ORIGINAL_RECEIPT_IDENTITY_OR_GRID_MISMATCH")
    cols=x["native_channel_summary"]
    expected={**SUFFIX_UNIT,**DIAG_SUFFIX_UNIT}
    for gi in range(1,10):
        for suffix,unit in expected.items():
            name="TwHt%d%s"%(gi,suffix)
            if name not in cols or cols[name].get("unit")!="("+unit+")":
                raise ValueError("S07_T062_ORIGINAL_CHANNEL_UNIT_MISMATCH_"+name)
    span=float(x["observed_TPzi_span_m"])
    if not math.isfinite(span) or span<=0 or span>=158:
        raise ValueError("S07_T062_GAGE_SPAN_INVALID")
    return {
        "SOURCE":{"reading_level":"T062 committed original OUTB-derived JSON receipt; original OUTB bytes NOT reread",
                  "receipt_sha256":sha256_file(path),
                  "historical_outb_declared_sha256":r["outb_sha256"]},
        "RUN":{"kind":"receipt-channel and time-grid check","native_solver_runs":0},
        "TAB":{"verified_gages":9,"verified_channels_per_gage":len(expected),
               "verified_channel_records":9*len(expected),
               "samples_per_gage":12001,"observed_gage_span_m":span},
        "HOLD":"T062 gage span is not full 158m coverage; 31-gage T071/T072 OUTB absent. RP angles not a verified global DCM; internal section resultants are not Abaqus external loads."
    }



def prepare_a_diagnostic_input(baseline_bytes, expected_base_sha=ED_BASE_SHA256):
    """Generate an OUTPUT-ONLY A-batch ElastoDyn diagnostic child.

    Exactly one TwrGagNd line and missing OutList channels may change.
    No OpenFAST run, no physics keyword change, no external-load conversion.
    """
    actual=hashlib.sha256(baseline_bytes).hexdigest()
    if actual != expected_base_sha:
        raise ValueError("S07_DIAG_PARENT_SHA256_MISMATCH")
    bom=b"\xef\xbb\xbf" if baseline_bytes.startswith(b"\xef\xbb\xbf") else b""
    text=baseline_bytes[len(bom):].decode("utf-8")
    lines=text.splitlines(keepends=True)
    newline="\r\n" if b"\r\n" in baseline_bytes else "\n"
    gage=[i for i,s in enumerate(lines) if re.match(
        r"^[ \t]*[0-9, \t]+[ \t]+TwrGagNd\b",s)]
    if len(gage)!=1 or not re.match(
        r"^[ \t]*1,3,5,7,9,13,15,17,20[ \t]+TwrGagNd\b",lines[gage[0]]):
        raise ValueError("S07_DIAG_PARENT_GAGE_LINE_UNEXPECTED")
    nt=[s for s in lines if re.match(r"^[ \t]*[0-9]+[ \t]+NTwGages\b",s)]
    if len(nt)!=1 or not re.match(r"^[ \t]*9[ \t]+NTwGages\b",nt[0]):
        raise ValueError("S07_DIAG_NTWGAGES_NOT_NINE")
    outlist=[i for i,s in enumerate(lines) if re.match(
        r"^[ \t]*OutList\b",s,re.I)]
    if len(outlist)!=1:
        raise ValueError("S07_DIAG_OUTLIST_AMBIGUOUS")
    ends=[i for i,s in enumerate(lines) if i>outlist[0] and
          re.match(r"^[ \t]*END(?:[ \t]|$)",s,re.I)]
    if len(ends)!=1:
        raise ValueError("S07_DIAG_END_AMBIGUOUS")
    end=ends[0]
    existing=[]
    for line in lines[outlist[0]+1:end]:
        m=re.match(r"""^[ \t]*["']([A-Za-z][A-Za-z0-9]*)["']""",line)
        if m: existing.append(m.group(1))
    required=["TwHt%d%s"%(gage_idx,suffix)
              for gage_idx in range(1,10)
              for suffix in tuple(SUFFIX_UNIT)+tuple(DIAG_SUFFIX_UNIT)]
    if len(required)!=135 or len(set(required))!=135:
        raise AssertionError("S07_DIAG_INTERNAL_CHANNEL_CONTRACT")
    if any(existing.count(x)>1 for x in required):
        raise ValueError("S07_DIAG_DUPLICATE_PARENT_CHANNEL")
    additions=[x for x in required if x not in existing]
    # The existing OutList is preserved byte-for-byte; only missing channels
    # are inserted before its sole END terminator.
    lines[gage[0]]=(
        ",".join(map(str,BATCHES["A"][0]))+
        "             TwrGagNd      - S07 A-batch diagnostic output only"+
        newline)
    lines[end:end]=['"'+x+'" - S07 paired diagnostic'+newline for x in additions]
    child=bom+"".join(lines).encode("utf-8")
    child_sha=hashlib.sha256(child).hexdigest()
    return child,{
        "stage":"S07_A_BATCH_DIAGNOSTIC_INPUT_STATIC_ONLY",
        "case":"U11p4_ETM_S04","batch":"A",
        "source_baseline_elastodyn_sha256":actual,
        "child_elastodyn_sha256":child_sha,
        "source_workflow_t072_git_blob":T072_BLOB,
        "baseline_fst_sha256_from_historical_T071":"5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605",
        "gage_nodes":list(BATCHES["A"][0]),
        "concrete_segments":list(BATCHES["A"][1]),
        "output_channels_required":required,
        "output_channels_required_count":135,
        "output_channels_already_present":135-len(additions),
        "output_channels_appended":len(additions),
        "changed_existing_lines":1,
        "SOURCE":"SHA256-locked parent ElastoDyn extracted from historical original case ZIP; not a recovered 31-gage OUTB",
        "REF":"Existing OpenFAST 3.5.3 ElastoDyn output nomenclature and T062 original 9-gage receipt; no new paper full text",
        "STANDARD":"No new authorized IEC/GB/NB original pages read",
        "OFFICIAL":"OpenFAST native output not run; this is only deterministic input construction",
        "RUN":{"openfast":0,"abaqus":0,"kind":"static input-only"},
        "FIG":"NONE","TAB":{"gage_count":9,"paired_channels_per_gage":15,"channel_count":135},
        "assumptions":["Output-only channels do not alter solver physics; requires native confirmation",
                       "U11p4_ETM_S04 BTS/Controller/FST and full case input identity not yet independently bound"],
        "error_budget":{"source_identity":"exact SHA256 match",
                        "output_identity":"exact deterministic bytes; no numerical response yet",
                        "native_physics":"UNDEFINED until a separate authorized diagnostic run"},
        "HOLD":"NOT A COMPLETE RUN PACKAGE. Missing same-run BTS/controller/FST byte binding, actual OpenFAST OUTB and RP/TP; no signed free-body or Abaqus load PASS."
    }


def emit_a_diagnostic_input(baseline, outdir, source_zip_sha256=None):
    outdir=Path(outdir)
    if outdir.exists() and any(outdir.iterdir()):
        raise ValueError("S07_DIAG_OUTPUT_DIR_NOT_EMPTY")
    child,receipt=prepare_a_diagnostic_input(Path(baseline).read_bytes())
    if source_zip_sha256:
        if not re.fullmatch(r"[0-9a-f]{64}",source_zip_sha256):
            raise ValueError("S07_DIAG_ZIP_SHA_INVALID")
        receipt["source_zip_sha256"]=source_zip_sha256
    outdir.mkdir(parents=True,exist_ok=True)
    target=outdir/"DTU_10MW_RWT_ElastoDyn.dat"
    target.write_bytes(child)
    if sha256_file(target)!=receipt["child_elastodyn_sha256"]:
        raise AssertionError("S07_DIAG_OUTPUT_BYTE_VERIFICATION_FAILED")
    (outdir/"S07_A_DIAGNOSTIC_INPUT_MANIFEST.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+"\n",
        encoding="utf-8")
    return receipt


def diagnostic_a_selftest():
    sample=(b"header\r\n9 NTwGages - count\r\n"
            b"1,3,5,7,9,13,15,17,20 TwrGagNd - original\r\n"
            b"OutList the following channels\r\n"
            b'"TwHt1FLxt" - original\r\nEND\r\nfooter\r\n')
    h=hashlib.sha256(sample).hexdigest()
    child,r=prepare_a_diagnostic_input(sample,h)
    assert r["output_channels_required_count"]==135
    assert r["output_channels_appended"]==134
    assert child.count(b"TwHt1FLxt")==1
    assert b"footer\r\n" in child and child.endswith(b"footer\r\n")
    assert child.count(b"TwHt9MLzt")==1
    assert child==prepare_a_diagnostic_input(sample,h)[0]
    faults=[
        (sample,"0"*64,"bad_sha"),
        (sample.replace(b"OutList",b"NoList"),h,"missing_outlist"),
        (sample.replace(b"9 NTwGages",b"8 NTwGages"),None,"bad_count"),
        (sample.replace(b"1,3,5,7,9,13,15,17,20",b"1,2,3,4,5,6,7,8,9"),None,"bad_parent"),
        (sample.replace(b"END",b"NOT_END"),None,"missing_end"),
        (sample.replace(b"END",b'"TwHt1FLxt" - duplicate\r\nEND'),None,"duplicate"),
    ]
    for raw,expected,name in faults:
        try: prepare_a_diagnostic_input(raw,expected or hashlib.sha256(raw).hexdigest())
        except ValueError: pass
        else: raise AssertionError("S07_DIAG_FAULT_ACCEPTED_"+name)
    return {"synthetic_child_sha256":r["child_elastodyn_sha256"],
            "positive_tests":4,"negative_tests":len(faults),
            "new_solver_runs":0}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--diagnostic-a-selftest",action="store_true")
    p.add_argument("--prepare-a-baseline",type=Path)
    p.add_argument("--prepare-a-dir",type=Path)
    p.add_argument("--source-zip-sha256")
    p.add_argument("--t062-receipt",type=Path,
                   help="audit existing 9-gage OUTB-derived receipt; no binary reread")
    p.add_argument("--t071",type=Path)
    p.add_argument("--t072",type=Path)
    p.add_argument("--source-audit",type=Path)
    p.add_argument("--outb",type=Path,help="EXISTING OUTB only, no solver")
    p.add_argument("--full-diagnostic",action="store_true",
                   help="capture RP/TP + AL + FL/ML in identical rows (NOT Abaqus loads)")
    p.add_argument("--expected-outb-sha256",
                   help="MANDATORY for capture: exact 64-char original OUTB SHA256")
    p.add_argument("--baseline-elastodyn",type=Path,
                   help="SHA-locked original ElastoDyn before gage-only patch")
    p.add_argument("--run-elastodyn",type=Path,
                   help="ElastoDyn from the same archived 31-gage run (identity preflight)")
    p.add_argument("--case")
    p.add_argument("--batch")
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.diagnostic_a_selftest:
        print("S07_A_DIAGNOSTIC_SELFTEST",json.dumps(diagnostic_a_selftest(),sort_keys=True))
    if a.prepare_a_baseline:
        if not a.prepare_a_dir:
            p.error("--prepare-a-dir required")
        print("S07_A_DIAGNOSTIC_INPUT",json.dumps(emit_a_diagnostic_input(
            a.prepare_a_baseline,a.prepare_a_dir,a.source_zip_sha256),sort_keys=True))
    if a.self_test:
        print("S07_SELFTEST",json.dumps(selftest(),sort_keys=True))
    if a.t062_receipt:
        print("S07_REAL_T062_RECEIPT_GATE",json.dumps(
            audit_original_nine_gage_receipt(a.t062_receipt),sort_keys=True))
    if a.source_audit or a.outb:
        if not a.t071 or not a.t072:
            p.error("--t071 and --t072 required")
        receipt=source_gate(a.t071,a.t072)
        if a.source_audit:
            a.source_audit.parent.mkdir(parents=True,exist_ok=True)
            a.source_audit.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",
                                      encoding="utf-8")
            print("S07_SOURCE_GATE",json.dumps(receipt["TAB"],sort_keys=True))
        if a.outb:
            if not a.case or not a.batch or not a.output:
                p.error("--case --batch --output required for existing OUTB capture")
            print("S07_EXISTING_OUTB_CAPTURE",json.dumps(
                capture_existing_outb(a.outb,a.case,a.batch,a.output,
                    full_diagnostic=a.full_diagnostic,
                    expected_sha256=a.expected_outb_sha256,
                    baseline_elastodyn=a.baseline_elastodyn,
                    run_elastodyn=a.run_elastodyn),sort_keys=True))
    if not (a.self_test or a.diagnostic_a_selftest or a.prepare_a_baseline or a.t062_receipt or a.source_audit or a.outb):
        p.error("choose --self-test, --source-audit or --outb")


if __name__=="__main__":
    main()
