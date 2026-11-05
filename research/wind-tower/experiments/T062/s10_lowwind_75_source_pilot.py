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
    receipt={
      "SOURCE":"Original 158m TurbSim .inp member from SHA-pinned historical ZIP; original 18-case source identity CSV",
      "READING_LEVEL":"Original TurbSim input member bytes and parent SHA checked in this run; historical FST/ServoDyn/DISCON SHA inherited from original source CSV, not reread",
      "REF":"T062 existing 18NTM source, operating-state and ROSCO v2.6.0 analysis; no new full-text paper",
      "STANDARD":"IEC 61400-1/6 2025 authorized clauses NOT READ; candidate is NOT normative DLC1.2",
      "OFFICIAL":"Historical TurbSim input-card syntax, not controller DLL binary identity or IEC certification",
      "RUN":"Python stdlib source-only one-field reversible patch; no TurbSim/OpenFAST/Abaqus/controller run",
      "FIG":"0","TAB":"One original-source candidate TurbSim input and source/acceptance receipt",
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
        "source":"Before native pilot require exact new BTS, FST/ED/Inflow/ServoDyn/DISCON and actual DLL SHA256",
        "time":"At DT_Out=0.05s require 100-700s 12001 finite monotonically sampled outputs",
        "operating":"Report power, rotor/generator speed, torque and pitch min/p05/mean/p95/max, transient and state transitions",
        "heuristic_only":"GenPwr>1kW and RotSpeed>0.1rpm is NOT controller cut-in certification",
        "logs":"Retain original stdout, SrvD.sum, ROSCO banner, DLL hash, warnings/errors",
        "decision":"No fixed cut-in, no physical PASS, no IEC DLC1.2 or fatigue damage conclusion without real outputs"},
      "tests":{"source_sha":"EXACT","single_field_patch":"PASS","reverse_byte_identity":"PASS"},
      "ERROR_BUDGET":"Source byte SHA exact; source-field change deterministic; wind/physics/controller uncertainty NOT ESTIMATED",
      "HOLD":"No 7.5m/s BTS/OUTB, runtime controller DLL SHA, operating-state evidence or licensed 2025 IEC clauses",
      "status":"SOURCE_ONLY_CANDIDATE_NOT_RUN","physical_pass":False,"stage_passed":0}
    out_dir.mkdir(parents=True,exist_ok=True)
    (out_dir/INP_NAME).write_bytes(child)
    (out_dir/JSON_NAME).write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return receipt

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
