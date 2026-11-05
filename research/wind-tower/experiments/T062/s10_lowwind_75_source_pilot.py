#!/usr/bin/env python3
"""Source-only 7.5 m/s S01 TurbSim candidate; NEVER runs a solver."""
import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
import s07_ntm18_original_control_input_gate as gate

ROOT = Path("research/wind-tower")
PARENT = "U09p343881_NTM_S01"
CHILD = "U07p5_NTM_S01"
PARENT_INP_SHA = "260769db45090a9f24dc3d05a8d5b89d75279d06fe0898ce1c18b4be31de34a9"
CONFIG_SHA = "be58d33306e6ac101d42b42c7f4d24ea5743662d1a9355aff9862b5a7e0aad45"
FST_SHA = "5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605"
SERVO_SHA = "103e7bd71209a095b833ca4ba62627ae7724870615112fdccfbff502076c966e"
DISCON_SHA = "8f5d7546420ee34838e66b63e4b26d64460be5d5492f99c60b6d1ef977ffc61a"
INP_NAME = "S10_U07p5_NTM_S01_TURBSIM_PILOT_20261105.inp"
JSON_NAME = "S10_U07p5_NTM_S01_SOURCE_PILOT_RECEIPT_20261105.json"
FIELDS = {"URef":"9.343881", "RandSeed1":"104729", "TurbModel":"IECKAI",
          "IEC_WindType":"NTM", "NumGrid_Z":"51", "NumGrid_Y":"51",
          "TimeStep":"0.025", "AnalysisTime":"700.0",
          "HubHt":"161.368806", "IECstandard":"1-ED3", "IECturbc":"A"}

def require(value, message):
    if not value:
        raise ValueError(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def patch_uref(raw, expected_sha=PARENT_INP_SHA):
    require(sha(raw)==expected_sha, "PARENT_SHA_MISMATCH")
    text=raw.decode("utf-8-sig")
    before=gate.parse_keys(raw, tuple(FIELDS))
    for k,v in FIELDS.items():
        require(before[k]==v, "PARENT_FIELD_"+k)
    lines=text.splitlines(keepends=True)
    matches=[i for i,line in enumerate(lines) if re.match(r"^\s*\S+\s+URef(?=\s|$)",line)]
    require(len(matches)==1,"UREF_NOT_UNIQUE")
    i=matches[0]
    body=lines[i].rstrip("\r\n")
    ending=lines[i][len(body):]
    match=re.match(r"^(\s*)(\S+)(\s+URef\b.*)$",body)
    require(match is not None and match.group(2)==FIELDS["URef"],"UREF_PARSE")
    lines[i]=match.group(1)+"7.5"+match.group(3)+ending
    child="".join(lines).encode("utf-8")
    after=gate.parse_keys(child,tuple(FIELDS))
    require(after=={**FIELDS,"URef":"7.5"},"CHILD_FIELDS_CHANGED")
    lines[i]=match.group(1)+FIELDS["URef"]+match.group(3)+ending
    require("".join(lines).encode("utf-8")==raw,"NOT_BYTE_REVERSIBLE")
    return child

def prepare(repo_root,out_dir):
    root=repo_root/ROOT
    manifest=gate.read_pinned(root/"archive/local-assets-20261004/file-manifest.json",gate.STATIC_SHA)
    config=gate.read_pinned(root/"experiments/T062/S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv",CONFIG_SHA)
    rows=list(csv.DictReader(io.StringIO(config.decode("utf-8"))))
    require(len(rows)==18 and len({r["case"] for r in rows})==18,"CONFIG_CASE_COUNT")
    row=next((r for r in rows if r["case"]==PARENT),None)
    require(row is not None,"MISSING_PARENT_CASE")
    for k,v in {"turb_inp_sha256":PARENT_INP_SHA,"fst_sha256":FST_SHA,
                "servo_sha256":SERVO_SHA,"discon_sha256":DISCON_SHA}.items():
        require(row[k]==v,"CONFIG_IDENTITY_"+k)
    require(row["turb_seed1"]=="104729" and row["turb_URef_mps"]=="9.343881","PARENT_SEED_SPEED")
    require(row["bts_archived_sha256"]=="" and row["formal_DLC12_reuse_verdict"]=="HOLD_NOT_VERIFIED","FALSE_SOURCE_PASS")
    source=gate.Source(repo_root,{"static":gate.manifest_index(manifest)})
    try:
        raw,entry=source.get("static","turbSim-36","inputs/"+PARENT+".inp")
    finally:
        source.close()
    require(sha(raw)==PARENT_INP_SHA,"MANIFEST_CONFIG_DIVERGENCE")
    child=patch_uref(raw)
    dll_gate=audit_dll_source(manifest,(root/REF_DLL_PATH).read_bytes())
    receipt={
      "SOURCE":"Original 158m TurbSim .inp member, 36-case historical DLL exclusion manifest, and separate SHA-pinned repository reference DLL",
      "READING_LEVEL":"Original TurbSim parent bytes and original 36-case manifest read; repository reference DLL bytes SHA checked; 36 excluded historical DLL bytes NOT READ; historical FST/ServoDyn/DISCON SHA inherited",
      "REF":"T062 existing 18NTM source, operating-state and ROSCO v2.6.0 analysis; no new full-text paper",
      "STANDARD":"IEC 61400-1/6 2025 authorized clauses NOT READ; candidate is NOT normative DLC1.2",
      "OFFICIAL":"Repository reference DLL SHA-pinned; existing T077 S07 A-case ABI preflight is separate, not historical 36-case binary identity or IEC certification",
      "RUN":"Python stdlib source-only one-field reversible patch and 36-case DLL manifest/reference-byte audit; no solver/controller run",
      "FIG":"0","TAB":"One candidate input plus 36-case original DLL provenance and reference SHA crosswalk",
      "parent_case":PARENT,"candidate_case_NOT_RUN":CHILD,
      "parent_archive":entry["canonical_archive"],"parent_member":entry["canonical_member"],
      "input_sha256":{"static_manifest":gate.STATIC_SHA,"historical_config_csv":CONFIG_SHA,
                      "parent_turbsim_inp":PARENT_INP_SHA,"historical_fst":FST_SHA,
                      "historical_servodyn":SERVO_SHA,"historical_discon":DISCON_SHA},
      "output_turbsim_inp_sha256":sha(child),
      "changed_fields":{"URef_mps":{"from":9.343881,"to":7.5}},
      "unchanged_source_fields":{k:v for k,v in FIELDS.items() if k!="URef"},
      "required_observables_NOT_YET_CAPTURED":["Time","RotSpeed","GenSpeed","GenPwr","GenTq",
                                                 "BldPitch1","BldPitch2","BldPitch3"],
      "future_acceptance_NOT_EXECUTED":{
        "source":"Reference DLL SHA available; require new BTS, FST/ED/Inflow/ServoDyn/DISCON and explicit reference-DLL substitution approval; original 36 historical DLL hashes remain unavailable",
        "time":"At DT_Out=0.05s require 100-700s 12001 finite monotonically sampled outputs",
        "operating":"Report power, rotor/generator speed, torque and pitch min/p05/mean/p95/max, transient and state transitions",
        "heuristic_only":"GenPwr>1kW and RotSpeed>0.1rpm is NOT controller cut-in certification",
        "logs":"Retain original stdout, SrvD.sum, ROSCO banner, DLL hash, warnings/errors",
        "decision":"No fixed cut-in, no physical PASS, no IEC DLC1.2 or fatigue damage conclusion without real outputs"},
      "tests":{"source_sha":"EXACT","single_field_patch":"PASS","reverse_byte_identity":"PASS"},
      "ERROR_BUDGET":"Source byte SHA exact; source-field change deterministic; wind/physics/controller uncertainty NOT ESTIMATED",
      "HOLD":"No 7.5m/s BTS/OUTB; original historical DLL SHA unavailable (reference DLL SHA known); no runtime equivalence, operating-state evidence or licensed 2025 IEC clauses",
      "status":"SOURCE_ONLY_CANDIDATE_NOT_RUN","physical_pass":False,"stage_passed":0,
      "dll_identity_source_gate":dll_gate}
    out_dir.mkdir(parents=True,exist_ok=True)
    (out_dir/INP_NAME).write_bytes(child)
    (out_dir/JSON_NAME).write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return receipt


REF_DLL_PATH = "references/baselines-and-site-20261004/openfast-v330-adaptation/1FreeDecay/Control/libdiscon.dll"
REF_DLL_SHA = "7aebb0d2166c0cc095d11c2b7bc13da136547c557b0f331dcdce84fe181802aa"
REF_DLL_SIZE = 1122431
GEN_SHA = "01D733E04C33CCC5DB8415D481C96BC0799173F88520A7863FCC78E6BBD441F2"

def audit_dll_source(manifest_raw, ref_dll, expected_ref_sha=REF_DLL_SHA, expected_ref_size=REF_DLL_SIZE):
    """36 original DLL paths were excluded; a distinct repository reference DLL is SHA-pinned.
    Equality between original omitted DLLs and the reference DLL is NOT inferred from equal sizes.
    """
    entries=json.loads(manifest_raw.decode("utf-8"))
    require(isinstance(entries,list),"DLL_MANIFEST_NOT_ARRAY")
    originals, generators={},{}
    for e in entries:
        path=e.get("relative_path","")
        m=re.fullmatch(r"CASES/([^/]+)/Control/libdiscon[.]dll",path)
        if m:
            require(m.group(1) not in originals,"DLL_DUPLICATE_CASE")
            originals[m.group(1)]=e
        m=re.fullmatch(r"CASES/([^/]+)/Control/gen_discon[.]py",path)
        if m:
            require(m.group(1) not in generators,"GEN_DUPLICATE_CASE")
            generators[m.group(1)]=e
    require(len(originals)==36 and len(generators)==36,"DLL_36_CASE_COUNT")
    require(set(originals)==set(generators),"DLL_GENERATOR_CASE_MISMATCH")
    require(sum("_NTM_" in k for k in originals)==18 and
            sum("_ETM_" in k for k in originals)==18,"DLL_18_18_SPLIT")
    for e in originals.values():
        require(e.get("section")=="openfast-36-r2" and
                e.get("status")=="excluded-format" and e.get("bytes")==REF_DLL_SIZE and
                e.get("archive","")=="" and e.get("sha256","")=="","DLL_ORIGINAL_SOURCE_UNEXPECTED")
    for e in generators.values():
        require(e.get("section")=="openfast-36-r2" and
                e.get("bytes")==11567 and e.get("sha256","").upper()==GEN_SHA and
                e.get("status") in ("included","duplicate-reference"),"DLL_GENERATOR_IDENTITY")
    require(sum(e["status"]=="included" for e in generators.values())==1,"DLL_GENERATOR_CANONICAL_COUNT")
    require(len(ref_dll)==expected_ref_size and sha(ref_dll)==expected_ref_sha,"DLL_REFERENCE_SHA_OR_SIZE")
    return {
      "manifest_sha256":gate.STATIC_SHA,
      "original_case_count":36,"original_NTM":18,"original_ETM":18,
      "original_case_nominal_bytes_each":REF_DLL_SIZE,
      "original_case_manifest_status":"excluded-format",
      "original_case_sha256_verified":0,
      "generator_case_count":36,"generator_unique_sha256":GEN_SHA.lower(),
      "generator_included":1,"generator_duplicate_reference":35,
      "reference_path":REF_DLL_PATH,"reference_bytes":len(ref_dll),
      "reference_sha256":sha(ref_dll),
      "reference_byte_sha_verified":True,
      "historical_runtime_equivalence_verified":False,
      "verdict":"REFERENCE_DLL_AVAILABLE_AND_SHA_VERIFIED__HISTORICAL_36_DLL_BYTES_NOT_ARCHIVED",
      "HOLD":"Original 36 DLL files excluded from archived ZIPs; matching size and generator script do not prove identical binary; 7.5m/s BTS/OUTB not generated."
    }

def dll_source_selftest():
    data=[]
    for kind in ("NTM","ETM"):
        for i in range(1,19):
            case="U_TEST_"+kind+"_S"+str(i).zfill(2)
            data.append({"section":"openfast-36-r2","relative_path":"CASES/"+case+"/Control/libdiscon.dll",
                         "bytes":REF_DLL_SIZE,"status":"excluded-format","archive":"","sha256":""})
            data.append({"section":"openfast-36-r2","relative_path":"CASES/"+case+"/Control/gen_discon.py",
                         "bytes":11567,"status":"included" if kind=="NTM" and i==1 else "duplicate-reference",
                         "sha256":GEN_SHA})
    ref=b"synthetic_dll"
    expected=sha(ref)
    def test(rows, blob=ref):
        return audit_dll_source(json.dumps(rows).encode(),blob,expected,len(ref))
    require(test(data)["original_case_sha256_verified"]==0,"DLL_POSITIVE")
    import copy
    mutations=[]
    x=copy.deepcopy(data);x.pop(0);mutations.append(x)
    x=copy.deepcopy(data);x[0]["status"]="included";mutations.append(x)
    x=copy.deepcopy(data);x[0]["sha256"]="fake";mutations.append(x)
    x=copy.deepcopy(data);x[0]["bytes"]=REF_DLL_SIZE+1;mutations.append(x)
    x=copy.deepcopy(data);x[0]["archive"]="part-001.zip";mutations.append(x)
    x=copy.deepcopy(data);x[2]["relative_path"]=x[0]["relative_path"];mutations.append(x)
    x=copy.deepcopy(data);x.pop(1);mutations.append(x)
    x=copy.deepcopy(data);x[1]["sha256"]="0"*64;mutations.append(x)
    for i,x in enumerate(mutations):
        try: test(x)
        except ValueError: pass
        else: raise AssertionError("DLL_NEGATIVE_ACCEPTED_"+str(i))
    try: test(data,ref+b"x")
    except ValueError: pass
    else: raise AssertionError("DLL_REFERENCE_TAMPER_ACCEPTED")
    print("S10_DLL_SOURCE_SELFTEST_PASS_1_POSITIVE_9_NEGATIVE_NO_SOLVER")

def selftest():
    raw=("104729 RandSeed1\n9.343881 URef ! m/s\nIECKAI TurbModel\n"
         "NTM IEC_WindType\n51 NumGrid_Z\n51 NumGrid_Y\n0.025 TimeStep\n"
         "700.0 AnalysisTime\n161.368806 HubHt\n1-ED3 IECstandard\nA IECturbc\n").encode()
    child=patch_uref(raw,sha(raw))
    require(b"7.5 URef" in child and b"104729 RandSeed1" in child,"POSITIVE")
    variants=[raw+b"1 URef\n",raw.replace(b"URef",b"WrongKey"),
              raw.replace(b"9.343881",b"9.343882"),
              raw.replace(b"104729",b"104730"),
              raw.replace(b"IECKAI",b"IECXXX"),
              raw.replace(b"51 NumGrid_Y",b"50 NumGrid_Y"),
              raw.replace(b"700.0",b"600.0"),
              raw.replace(b"0.025",b"0.05")]
    for i,bad in enumerate(variants):
        try: patch_uref(bad,sha(bad))
        except ValueError: pass
        else: raise AssertionError("NEGATIVE_ACCEPTED_"+str(i))
    try: patch_uref(raw,"0"*64)
    except ValueError: pass
    else: raise AssertionError("SOURCE_SHA_TAMPER_ACCEPTED")
    dll_source_selftest()
    print("S10_75_SOURCE_PILOT_SELFTEST_PASS_1_POSITIVE_9_NEGATIVE_NO_SOLVER")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--selftest",action="store_true")
    parser.add_argument("--repo-root",type=Path,default=Path("."))
    parser.add_argument("--out-dir",type=Path)
    args=parser.parse_args()
    if args.selftest: selftest(); return
    require(args.out_dir is not None,"OUT_DIR_REQUIRED")
    receipt=prepare(args.repo_root,args.out_dir)
    print("S10_75_PILOT_INPUT_PREPARED_NOT_RUN",receipt["output_turbsim_inp_sha256"])

if __name__=="__main__":
    main()
