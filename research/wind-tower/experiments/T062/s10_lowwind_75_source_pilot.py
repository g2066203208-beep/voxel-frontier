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


# Source-only extension: 30 low-wind bin/seed candidates from the SHA-locked
# U07p5 S01 pilot. These are derived candidates, NOT historical per-seed INP bytes.
GRID_PILOT_SHA = "e403ace85b2915fd4c9976e3cab0d9153da8c0b172b79a1544ce02098a198b33"
GRID_SOURCE_CSV = "S10_LOW_WIND_30SLOT_SOURCE_READINESS_20261104.csv"
GRID_RECEIPT_JSON = JSON_NAME

def _replace_unique_token(raw, key, old, new):
    lines = raw.splitlines(keepends=True)
    expr = re.compile(rb"^(\s*)(\S+)(\s+" + key.encode("ascii") + rb"\b.*)$")
    indices = []
    for i, line in enumerate(lines):
        body = line.rstrip(b"\r\n")
        if expr.match(body):
            indices.append(i)
    require(len(indices) == 1, "GRID_FIELD_NOT_UNIQUE_" + key)
    i = indices[0]
    body = lines[i].rstrip(b"\r\n")
    suffix = lines[i][len(body):]
    match = expr.match(body)
    require(match is not None and match.group(2) == old.encode("ascii"),
            "GRID_UNEXPECTED_FIELD_" + key)
    lines[i] = match.group(1) + new.encode("ascii") + match.group(3) + suffix
    return b"".join(lines)

def build_lowwind_grid(repo_root, pilot_override=None, csv_override=None, config_override=None):
    root = repo_root / ROOT / "experiments/T062"
    pilot = pilot_override if pilot_override is not None else (root / INP_NAME).read_bytes()
    grid_raw = csv_override if csv_override is not None else (root / GRID_SOURCE_CSV).read_bytes()
    config_raw = config_override if config_override is not None else (root / "S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv").read_bytes()
    require(sha(pilot) == GRID_PILOT_SHA, "GRID_PILOT_SHA")
    require(sha(config_raw) == CONFIG_SHA, "GRID_CONFIG_SHA")
    pilot_fields = gate.parse_keys(pilot, tuple(FIELDS))
    require(pilot_fields == {**FIELDS, "URef": "7.5"}, "GRID_PILOT_FIELDS")
    rows = list(csv.DictReader(io.StringIO(grid_raw.decode("utf-8-sig"))))
    config_rows = list(csv.DictReader(io.StringIO(config_raw.decode("utf-8-sig"))))
    seed_source = {}
    for row in config_rows:
        match = re.fullmatch(r"U09p343881_NTM_(S0[1-6])", row["case"])
        if match:
            require(match.group(1) not in seed_source, "GRID_DUPLICATE_HISTORICAL_SEED")
            seed_source[match.group(1)] = row["turb_seed1"]
    require(len(seed_source) == 6, "GRID_SIX_HISTORICAL_SEEDS")
    require(len(rows) == 30 and len({r["candidate_case_NOT_RUN"] for r in rows}) == 30,
            "GRID_30_UNIQUE_SLOTS")
    entries = []
    for row in rows:
        case = row["candidate_case_NOT_RUN"]
        match = re.fullmatch(r"U0([4-8])p5_NTM_(S0[1-6])", case)
        require(match is not None, "GRID_BAD_CASE")
        lower, seed_label = int(match.group(1)), match.group(2)
        uref = f"{lower}.5"
        seed = seed_source[seed_label]
        require(row["bin_lower_mps"] == str(lower)
                and row["bin_center_mps_NONNORMATIVE"] == uref
                and row["seed_label"] == seed_label
                and row["historical_seed1_CANDIDATE_ONLY"] == seed,
                "GRID_ROW_SOURCE_DRIFT")
        require(not row["new_BTS_sha256"] and not row["new_OUTB_sha256"]
                and not row["source_OUTB_sha256"], "GRID_FALSE_NATIVE_OUTPUT")
        candidate = _replace_unique_token(pilot, "URef", "7.5", uref)
        candidate = _replace_unique_token(candidate, "RandSeed1", "104729", seed)
        fields = gate.parse_keys(candidate, tuple(FIELDS))
        require(fields == {**FIELDS, "URef": uref, "RandSeed1": seed},
                "GRID_UNEXPECTED_INPUT_MUTATION")
        restored = _replace_unique_token(candidate, "URef", uref, "7.5")
        restored = _replace_unique_token(restored, "RandSeed1", seed, "104729")
        require(restored == pilot, "GRID_NOT_BYTE_REVERSIBLE")
        entries.append({"candidate_case_NOT_RUN": case, "URef_mps": uref,
                        "RandSeed1": seed, "derived_input_sha256": sha(candidate),
                        "input_bytes": len(candidate), "reverse_to_pilot": True,
                        "BTS_sha256": None, "OUTB_sha256": None,
                        "native_controller_state": "NOT_RUN"})
    require(len({x["derived_input_sha256"] for x in entries}) == 30,
            "GRID_NONUNIQUE_CANDIDATE_BYTES")
    require(next(x["derived_input_sha256"] for x in entries
                 if x["candidate_case_NOT_RUN"] == "U07p5_NTM_S01") == GRID_PILOT_SHA,
            "GRID_75_PILOT_REGRESSION")
    return {
        "SOURCE": "SHA-locked 7.5m/s S01 pilot derived from original 9.343881m/s S01 TurbSim INP; 30-slot planning CSV; original 18-case controller source CSV",
        "READING_LEVEL": "Exact existing pilot bytes and both existing CSV files directly read. Original five other seed-specific TurbSim INP bytes NOT read for this grid; seed labels are inherited metadata, not per-seed byte equivalence.",
        "REF": "Existing T062 18NTM source/ROSCO study and 21-year ERA5 bin plan; no new paper fulltext",
        "STANDARD": "IEC 61400-1/6 2025 authorized clauses NOT READ; 4.5..8.5m/s and six seeds NONNORMATIVE proposed coverage",
        "OFFICIAL": "Historical GitHub source archive receipt and original OpenFAST input identity, not controller/DLC certification",
        "RUN": "Python standard-library source-only byte patch and reverse checks; no TurbSim/OpenFAST/Abaqus execution",
        "FIG": 0, "TAB": "30 source-derived candidate INP SHA256 rows (in-memory, no 30-file proliferation)",
        "input_sha256": {"pilot_inp": GRID_PILOT_SHA, "planning_csv": sha(grid_raw),
                         "original_18case_config_csv": CONFIG_SHA},
        "assumptions": "Each candidate inherits ALL pilot TurbSim settings except URef and RandSeed1; other seeds are hypothetical paired designs, not exact original seed-specific parent inputs. Actual cut-in and DLL binary provenance unknown.",
        "error_budget": "Exact SHA256 and reverse byte identity; no physical, controller, IEC, low-frequency wind or site error budget established",
        "tests": {"30_unique": True, "5_bins_x_6_seeds": True,
                  "byte_reversal": "30/30", "pilot_75_regression": True},
        "entries": entries,
        "HOLD": "No actual 4-8m/s BTS/OUTB, no verified historical 36 DLL binary identity, no lowwind operating state or authorized IEC2025 DLC1.2 acceptance",
        "physical_pass": False, "formal_dlc12_verified_slots": 0, "stages_passed": 0
    }

def grid_negative_tests(repo_root):
    root = repo_root / ROOT / "experiments/T062"
    pilot = (root / INP_NAME).read_bytes()
    grid = (root / GRID_SOURCE_CSV).read_bytes()
    config = (root / "S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv").read_bytes()
    mutations = [
        {"pilot_override": pilot.replace(b"7.5", b"7.6", 1)},
        {"pilot_override": pilot + b"tamper"},
        {"csv_override": grid.replace(b"104729", b"104730", 1)},
        {"csv_override": grid.replace(b"U04p5_NTM_S01", b"U04p5_NTM_S02", 1)},
        {"csv_override": grid.replace(b"U04p5_NTM_S01", b"U03p5_NTM_S01", 1)},
        {"csv_override": grid.replace(b"NEED_TURBSIM_BTS_CONTROLLER_CUTIN_AND_DLC12_VALIDATION",
                                      b"PASS", 1).replace(b",,,,", b",fake,,,", 1)},
        {"config_override": config + b"tamper"},
        {"pilot_override": pilot.replace(b"RandSeed1", b"RandSeedX", 1)},
    ]
    for i, change in enumerate(mutations):
        try:
            build_lowwind_grid(repo_root, **change)
        except (ValueError, KeyError, AssertionError):
            pass
        else:
            raise AssertionError("GRID_NEGATIVE_ACCEPTED_" + str(i))
    return len(mutations)

def grid_command(repo_root, write):
    grid = build_lowwind_grid(repo_root)
    count = grid_negative_tests(repo_root)
    path = repo_root / ROOT / "experiments/T062" / GRID_RECEIPT_JSON
    receipt = json.loads(path.read_text(encoding="utf-8"))
    require(receipt["output_turbsim_inp_sha256"] == GRID_PILOT_SHA
            and receipt["status"] == "SOURCE_ONLY_CANDIDATE_NOT_RUN"
            and receipt["physical_pass"] is False, "GRID_PARENT_RECEIPT_DRIFT")
    if write:
        receipt["lowwind_30slot_candidate_grid_20261106"] = grid
        path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        require(receipt.get("lowwind_30slot_candidate_grid_20261106") == grid,
                "GRID_COMMITTED_RECEIPT_DRIFT")
    print("S10_LOWWIND_30_SOURCE_ONLY_GRID_PASS_NOT_DLC12",
          "30/30", "negative_tests=" + str(count),
          "pilot_sha=" + GRID_PILOT_SHA,
          "receipt_sha=" + sha(path.read_bytes()))


# S07 source-dependency gate: a TurbSim .inp alone does NOT rebind OpenFAST's
# historical absolute InflowWind BTS reference. This is a conditional source
# mismatch audit, NOT an executable new OpenFAST case or controller cut-in test.
DEPENDENCY_KEY = "lowwind_30slot_dependency_gate_20261106"
GRID_PLAN_SHA = "9d2e1403f9a230fc1cf97c191495ff7bdad552c6782b7403a6c8a1f7339fd475"

def _dependency_row(candidate, original):
    case = candidate["candidate_case_NOT_RUN"]
    match = re.fullmatch(r"U0[4-8]p5_NTM_(S0[1-6])", case)
    require(match is not None, "DEPENDENCY_CANDIDATE_ID")
    seed = match.group(1)
    parent = "U09p343881_NTM_" + seed
    require(original["case"] == parent, "DEPENDENCY_SEED_PARENT")
    require(original["inflow_WindType"] == "3", "DEPENDENCY_WINDTYPE")
    path = original["inflow_FileName_BTS"]
    require(re.match(r"^[A-Za-z]:\\", path) is not None,
            "DEPENDENCY_EXPECTED_HISTORICAL_ABSOLUTE_PATH")
    historical_bts = path.replace("\\", "/").split("/")[-1]
    require(historical_bts == parent + ".bts", "DEPENDENCY_PARENT_BTS_NAME")
    require(original["fst_sha256"] == FST_SHA, "DEPENDENCY_FST_IDENTITY")
    require(original["servo_sha256"] == SERVO_SHA, "DEPENDENCY_SERVO_IDENTITY")
    require(original["discon_sha256"] == DISCON_SHA, "DEPENDENCY_DISCON_IDENTITY")
    require(re.fullmatch(r"[0-9a-f]{64}", original["inflow_sha256"]) is not None,
            "DEPENDENCY_INFLOW_SHA")
    require(original["servo_DLL_FileName"].lower() == "libdiscon.dll",
            "DEPENDENCY_DLL_NAME")
    require(original["bts_archived_sha256"] == "" and
            original["formal_DLC12_reuse_verdict"] == "HOLD_NOT_VERIFIED",
            "DEPENDENCY_FALSE_HISTORICAL_PASS")
    require(candidate["source_OUTB_sha256"] == "" and
            candidate["new_BTS_sha256"] == "" and
            candidate["new_OUTB_sha256"] == "",
            "DEPENDENCY_FALSE_NEW_OUTPUT")
    require(candidate["readiness_status"] ==
            "NEED_TURBSIM_BTS_CONTROLLER_CUTIN_AND_DLC12_VALIDATION",
            "DEPENDENCY_FALSE_CANDIDATE_PASS")
    desired = case + ".bts"
    require(historical_bts != desired, "DEPENDENCY_EXPECTED_MISMATCH")
    return {
        "candidate_case_NOT_RUN": case,
        "parent_case": parent,
        "historical_inflow_sha256_INHERITED": original["inflow_sha256"],
        "historical_bts_basename_INHERITED": historical_bts,
        "required_candidate_bts_basename_NOT_GENERATED": desired,
        "inherited_inflow_is_windows_absolute": True,
        "would_reuse_wrong_wind_if_original_inflow_card_used_unchanged": True,
        "candidate_inflow_card_SHA256": None,
        "candidate_BTS_SHA256": None,
        "candidate_OUTB_SHA256": None,
        "dependency_status": "MUST_REBIND_AND_VERIFY_NEW_INFLOW_CARD_BTS_AND_DLL"
    }

def dependency_negative_tests(candidate, original):
    import copy
    variants = []
    def change(side, key, value):
        c, o = copy.deepcopy(candidate), copy.deepcopy(original)
        (c if side == "c" else o)[key] = value
        variants.append((c, o))
    change("o", "inflow_WindType", "1")
    change("o", "inflow_FileName_BTS", "inputs/" + original["case"] + ".bts")
    change("o", "inflow_FileName_BTS", r"C:\fake\U09p343881_NTM_S06.bts")
    change("o", "fst_sha256", "0" * 64)
    change("o", "servo_DLL_FileName", "wrong.dll")
    change("o", "bts_archived_sha256", "f" * 64)
    change("c", "new_BTS_sha256", "f" * 64)
    change("c", "readiness_status", "PASS")
    for i, (c, o) in enumerate(variants):
        try:
            _dependency_row(c, o)
        except (ValueError, KeyError):
            pass
        else:
            raise AssertionError("DEPENDENCY_NEGATIVE_ACCEPTED_" + str(i))
    return len(variants)

def build_dependency_gate(repo_root):
    root = repo_root / ROOT / "experiments/T062"
    plan_raw = gate.read_pinned(root / GRID_SOURCE_CSV, GRID_PLAN_SHA)
    historical_raw = gate.read_pinned(
        root / "S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv",
        CONFIG_SHA)
    plan = list(csv.DictReader(io.StringIO(plan_raw.decode("utf-8-sig"))))
    history = list(csv.DictReader(io.StringIO(historical_raw.decode("utf-8-sig"))))
    source = {r["case"]: r for r in history}
    require(len(plan) == 30 and len(source) == 18, "DEPENDENCY_SOURCE_ROWS")
    grid = build_lowwind_grid(repo_root)
    derived = {r["candidate_case_NOT_RUN"] for r in grid["entries"]}
    require({r["candidate_case_NOT_RUN"] for r in plan} == derived,
            "DEPENDENCY_CANDIDATE_GRID_DIVERGENCE")
    records = []
    for row in plan:
        match = re.fullmatch(r"U0[4-8]p5_NTM_(S0[1-6])",
                             row["candidate_case_NOT_RUN"])
        require(match is not None, "DEPENDENCY_CASE_PARSE")
        parent = "U09p343881_NTM_" + match.group(1)
        require(parent in source, "DEPENDENCY_PARENT_MISSING")
        records.append(_dependency_row(row, source[parent]))
    require(len(records) == 30 and
            len({r["candidate_case_NOT_RUN"] for r in records}) == 30,
            "DEPENDENCY_30_CASES")
    require(len({r["historical_inflow_sha256_INHERITED"]
                 for r in records}) == 6, "DEPENDENCY_SIX_ORIGINAL_INFLOW_CARDS")
    negatives = dependency_negative_tests(plan[0], source["U09p343881_NTM_S01"])
    return {
        "SOURCE": "Original 18NTM SHA-pinned source identity CSV and 30-slot source plan; 7.5 S01 exact TurbSim pilot verified by existing grid function",
        "READING_LEVEL": "18-case verified derived CSV (not re-read original InflowWind/FST/DLL raw members this round); 30-slot CSV and pilot raw bytes read. New candidate InflowWind/BTS/OUTB bytes DO NOT EXIST.",
        "REF": "T062 original-input gate; no new paper full-text reading",
        "STANDARD": "IEC 61400-1/6 2025 authorized clauses NOT READ; no DLC1.2 acceptance",
        "OFFICIAL": "Original OpenFAST source identity recorded in T062; this is not a runtime/ROSCO test",
        "RUN": "Python stdlib source-only dependency crosswalk; no TurbSim/OpenFAST/CAE run",
        "FIG": 0, "TAB": "30 candidate-to-original InflowWind BTS reference rows",
        "input_sha256": {"planning_csv": GRID_PLAN_SHA,
                         "original_18NTM_source_csv": CONFIG_SHA,
                         "pilot_turbsim_inp": GRID_PILOT_SHA},
        "assumptions": "IF an original 9.343881m/s InflowWind card is reused unchanged, it still points to the 9.343881m/s BTS, not to the 4.5..8.5m/s candidate. No candidate InflowWind card has been constructed or executed.",
        "error_budget": "Exact source token/path matching; original raw InflowWind bytes not independently rehashed this round; runtime, controller, turbulence and fatigue errors NEED_ESTIMATE",
        "negative_tests_rejected": negatives,
        "original_inflow_cards_unique": 6,
        "inherited_unrebound_references": len(records),
        "candidate_inflow_cards_verified": 0,
        "new_BTS_verified": 0,
        "new_OUTB_verified": 0,
        "records": records,
        "HOLD": "Must construct and SHA-lock each candidate InflowWind card, replace absolute original BTS reference, supply actual candidate BTS and consistent FST/ServoDyn/DISCON/DLL paths and original run-state evidence; no source-closed runnable low-wind case yet",
        "physical_pass": False, "formal_dlc12_verified_slots": 0,
        "stages_passed": 0
    }

def dependency_command(repo_root, write):
    path = repo_root / ROOT / "experiments/T062" / GRID_RECEIPT_JSON
    receipt = json.loads(path.read_text(encoding="utf-8"))
    computed = build_dependency_gate(repo_root)
    require(receipt.get("lowwind_30slot_candidate_grid_20261106") ==
            build_lowwind_grid(repo_root), "DEPENDENCY_GRID_RECEIPT_DRIFT")
    if write:
        receipt[DEPENDENCY_KEY] = computed
        path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    else:
        require(receipt.get(DEPENDENCY_KEY) == computed,
                "DEPENDENCY_COMMITTED_RECEIPT_DRIFT")
    print("S07_LOWWIND_INFLOW_DEPENDENCY_HOLD",
          "unrebound=30/30", "original_inflow_cards=6",
          "negative_tests=" + str(computed["negative_tests_rejected"]),
          "candidate_BTS=0", "DLC12_PASS=0")


# S07 source-only: recover the exact archived 9.343881 m/s S01 InflowWind
# card, rebind ONE BTS filename, and prove a byte-exact inverse. NOT RUN.
INFLOW_SOURCE_ZIP = "research/wind-tower/archive/local-assets-20261004/openfast-36-r2/part-001.zip"
INFLOW_SOURCE_MEMBER = "CASES/U09p343881_NTM_S01/DTU_10MW_InflowWind.dat"
INFLOW_SOURCE_SHA = "d204329f881836ffe0895b7d81aa28cae7540d5df56c754880db3d6c5c11d3a9"
INFLOW_SOURCE_BYTES = 6248
INFLOW_CHILD_FILE = "S07_U04p5_NTM_S01_InflowWind_NOT_RUN.dat"
INFLOW_RECEIPT_KEY = "lowwind_45_s01_exact_inflow_rebind_20261106"
INFLOW_NEW_BTS = "inputs/U04p5_NTM_S01.bts"

def rebind_exact_inflow(raw, old_path, new_path=INFLOW_NEW_BTS,
                        expected_sha=INFLOW_SOURCE_SHA, expected_size=INFLOW_SOURCE_BYTES):
    require(len(raw) == expected_size, "INFLOW_SOURCE_SIZE_MISMATCH")
    require(sha(raw) == expected_sha, "INFLOW_SOURCE_SHA_MISMATCH")
    fields = gate.parse_keys(raw, ("WindType", "FileName_BTS", "Filename", "RefHt", "HWindSpeed"))
    require(fields["WindType"] == "3", "INFLOW_WINDTYPE_NOT_BTS")
    require(fields["FileName_BTS"] == old_path, "INFLOW_ORIGINAL_BTS_PATH_DRIFT")
    require(old_path.endswith("\\U09p343881_NTM_S01.bts")
            and re.match(r"^[A-Za-z]:\\", old_path), "INFLOW_ORIGINAL_NOT_ABSOLUTE")
    require(new_path == INFLOW_NEW_BTS and
            re.fullmatch(r"inputs/U04p5_NTM_S01[.]bts", new_path),
            "INFLOW_CANDIDATE_PATH_UNAPPROVED")
    old = old_path.encode("utf-8")
    new = new_path.encode("utf-8")
    require(raw.count(old) == 1, "INFLOW_SOURCE_PATH_NOT_UNIQUE")
    child = raw.replace(old, new)
    after = gate.parse_keys(child, tuple(fields))
    require(after == {**fields, "FileName_BTS": new_path},
            "INFLOW_OTHER_FIELDS_CHANGED")
    require(child.count(new) == 1 and child.replace(new, old) == raw,
            "INFLOW_NOT_BYTE_REVERSIBLE")
    return child

def inflow_rebind_selftest():
    old = "C:" + chr(92) + "historical" + chr(92) + "inputs" + chr(92) + "U09p343881_NTM_S01.bts"
    raw = ('3 WindType\n"' + old + '" FileName_BTS ! historical\n'
           '161.368806 RefHt\n9.343881 HWindSpeed\n').encode()
    child = rebind_exact_inflow(raw, old, expected_sha=sha(raw), expected_size=len(raw))
    require(b"inputs/U04p5_NTM_S01.bts" in child and
            child.replace(INFLOW_NEW_BTS.encode(), old.encode()) == raw,
            "INFLOW_SELFTEST_POSITIVE")
    bads = [
        (raw, old, INFLOW_NEW_BTS, "0"*64, len(raw)),
        (raw, old, INFLOW_NEW_BTS, sha(raw), len(raw)+1),
        (raw.replace(b"3 WindType", b"1 WindType"), old, INFLOW_NEW_BTS, None, None),
        (raw + b'"x" FileName_BTS\n', old, INFLOW_NEW_BTS, None, None),
        (raw.replace(b"FileName_BTS", b"WrongKey"), old, INFLOW_NEW_BTS, None, None),
        (raw, old.replace("S01", "S02"), INFLOW_NEW_BTS, None, None),
        (raw, old, "../inputs/U04p5_NTM_S01.bts", None, None),
        (raw, old, r"C:\inputs\U04p5_NTM_S01.bts", None, None),
    ]
    for i, (source, old_ref, new_ref, hash_override, size_override) in enumerate(bads):
        try:
            rebind_exact_inflow(source, old_ref, new_ref,
                                hash_override or sha(source),
                                size_override if size_override is not None else len(source))
        except (ValueError, KeyError):
            pass
        else:
            raise AssertionError("INFLOW_NEGATIVE_ACCEPTED_" + str(i))
    print("S07_INFLOW_REBIND_SELFTEST_PASS_1_POSITIVE_8_NEGATIVE")

def inflow_rebind_command(repo_root, write):
    import zipfile
    source_zip = repo_root / INFLOW_SOURCE_ZIP
    require(source_zip.is_file(), "INFLOW_ARCHIVE_NOT_AVAILABLE")
    with zipfile.ZipFile(source_zip) as archive:
        require(INFLOW_SOURCE_MEMBER in archive.namelist(), "INFLOW_MEMBER_MISSING")
        raw = archive.read(INFLOW_SOURCE_MEMBER)
    require(len(raw) == INFLOW_SOURCE_BYTES and sha(raw) == INFLOW_SOURCE_SHA,
            "INFLOW_ORIGINAL_BYTES_NOT_VERIFIED")
    config_raw = gate.read_pinned(
        repo_root / ROOT / "experiments/T062/S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv",
        CONFIG_SHA)
    originals = list(csv.DictReader(io.StringIO(config_raw.decode("utf-8-sig"))))
    parent = next((r for r in originals if r["case"] == PARENT), None)
    require(parent is not None and parent["inflow_sha256"] == INFLOW_SOURCE_SHA
            and parent["inflow_WindType"] == "3", "INFLOW_PARENT_IDENTITY")
    old_path = parent["inflow_FileName_BTS"]
    child = rebind_exact_inflow(raw, old_path)
    inflow_rebind_selftest()
    root = repo_root / ROOT / "experiments/T062"
    output = root / INFLOW_CHILD_FILE
    receipt_path = root / GRID_RECEIPT_JSON
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    require(receipt["status"] == "SOURCE_ONLY_CANDIDATE_NOT_RUN"
            and receipt["physical_pass"] is False, "INFLOW_RECEIPT_PARENT_STATE")
    result = {
        "SOURCE": "Exact 6248-byte original 158m U09p343881_NTM_S01 InflowWind member in static openfast-36-r2 part-001 ZIP; exact original 18NTM identity CSV",
        "READING_LEVEL": "Full original archived InflowWind card bytes directly read and SHA256 verified; historical CSV cross-checked; new BTS/OUTB and original controller DLL bytes NOT read or generated",
        "REF": "Existing T062 18NTM source/ROSCO methods; no new paper original pages",
        "STANDARD": "IEC 61400-1/6 2025 authorized clauses NOT READ; NOT DLC1.2 normative acceptance",
        "OFFICIAL": "Original OpenFAST source card, not an official site wind or controller runtime certificate",
        "RUN": "Python stdlib ZIP source read, exact one-token BTS reference replacement, reverse-byte test; no TurbSim/OpenFAST/CAE execution",
        "FIG": 0,
        "TAB": "One source/child SHA pair, one old/new path, 1 positive and 8 negative synthetic tests",
        "input_sha256": {
            "archive_zip": sha(source_zip.read_bytes()),
            "source_inflow_card": INFLOW_SOURCE_SHA,
            "historical_18ntm_csv": CONFIG_SHA
        },
        "parent_member": INFLOW_SOURCE_MEMBER,
        "parent_bytes": len(raw),
        "parent_original_absolute_bts_path": old_path,
        "candidate_case_NOT_RUN": "U04p5_NTM_S01",
        "candidate_card_path": str(output.relative_to(repo_root)),
        "candidate_card_bytes": len(child),
        "candidate_card_sha256": sha(child),
        "candidate_relative_bts_path_NOT_PRESENT": INFLOW_NEW_BTS,
        "changed_fields": ["FileName_BTS"],
        "unchanged_fields": ["WindType", "Filename", "RefHt", "HWindSpeed"],
        "tests": {"parent_sha_and_size": "PASS", "original_18ntm_csv_identity": "PASS",
                  "unique_token": "PASS", "byte_exact_reverse": "PASS",
                  "synthetic_positive": 1, "synthetic_negative_rejected": 8},
        "assumptions": "A future staged OpenFAST case may place the new BTS at inputs/U04p5_NTM_S01.bts relative to the applicable runtime base directory. OpenFAST path resolution and FST/ServoDyn/DISCON/DLL wiring have NOT been executed or verified.",
        "error_budget": "Original and child bytes are SHA256 locked; inverse is byte-exact; runtime relative-path semantics, controller operating state, wind/structure and material-fatigue uncertainties NEED_ESTIMATE",
        "HOLD": "Candidate BTS does not exist; FST path/runtime base, DLL binary identity, control state, IEC2025 clauses and material local stresses remain unverified",
        "candidate_BTS_sha256": None,
        "candidate_OUTB_sha256": None,
        "physical_pass": False, "formal_dlc12_verified_slots": 0,
        "stages_passed": 0, "status": "SOURCE_ONLY_CANDIDATE_NOT_RUN"
    }
    if write:
        require(not output.exists() or output.read_bytes() == child,
                "INFLOW_EXISTING_CHILD_CONFLICT")
        output.write_bytes(child)
        receipt[INFLOW_RECEIPT_KEY] = result
        receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
                                encoding="utf-8")
    else:
        require(output.is_file() and output.read_bytes() == child,
                "INFLOW_COMMITTED_CHILD_DRIFT")
        require(receipt.get(INFLOW_RECEIPT_KEY) == result,
                "INFLOW_COMMITTED_RECEIPT_DRIFT")
    print("S07_INFLOW_SOURCE_REBIND_SOURCE_ONLY_NOT_RUN",
          "parent_sha=" + INFLOW_SOURCE_SHA,
          "child_sha=" + sha(child),
          "parent_bytes=" + str(len(raw)), "child_bytes=" + str(len(child)),
          "synthetic_negative=8", "BTS=0", "DLC12_PASS=0")
    fst_inflow_bts_chain_command(repo_root, write)



# S07: exact historical FST -> staged InflowWind -> proposed BTS path chain.
# The three possible relative-path bases are made co-located by construction;
# this is a source/layout contract, NOT an OpenFAST runtime or BTS existence test.
# The NTM logical FST is a duplicate-reference in the original manifest, not a ZIP member.
# Read its byte-identical canonical ETM S01 member from part-001.zip.
FST_CHAIN_LOGICAL_MEMBER = "CASES/U09p343881_NTM_S01/DTU_10MW_RWT.fst"
FST_CHAIN_SOURCE_MEMBER = "CASES/U09p343881_ETM_S01/DTU_10MW_RWT.fst"
FST_CHAIN_MANIFEST = "research/wind-tower/archive/local-assets-20261004/file-manifest.json"
FST_CHAIN_MANIFEST_SHA = "c9da25b3a967c9ed3b3a859666263c6964d8480798185e6e031539c38e4c3302"
FST_CHAIN_RECEIPT_KEY = "lowwind_45_s01_fst_inflow_bts_chain_20261106"
FST_CHAIN_CASE_ROOT = "CASES/U04p5_NTM_S01"
FST_CHAIN_FST_NAME = "DTU_10MW_RWT.fst"
FST_CHAIN_INFLOW_NAME = "DTU_10MW_InflowWind.dat"
FST_CHAIN_CHILD_SHA = "2ee0f78812f675448967a4bbf6d536310d995f5c219a45cf8e4cc488d675ad55"

def _s07_safe_relative(value):
    from pathlib import PurePosixPath
    require(bool(value) and not re.match(r"^[A-Za-z]:", value),
            "FST_CHAIN_WINDOWS_ABSOLUTE")
    require(chr(92) not in value, "FST_CHAIN_BACKSLASH_NOT_PORTABLE")
    p = PurePosixPath(value)
    require(not p.is_absolute() and value == p.as_posix()
            and all(x not in ("", ".", "..") for x in value.split("/")),
            "FST_CHAIN_UNSAFE_RELATIVE")
    return p

def inspect_fst_inflow_layout(fst, inflow,
                              fst_expected=FST_SHA,
                              inflow_expected=FST_CHAIN_CHILD_SHA):
    from pathlib import PurePosixPath
    require(sha(fst) == fst_expected, "FST_CHAIN_FST_SHA")
    require(sha(inflow) == inflow_expected, "FST_CHAIN_INFLOW_SHA")
    f = gate.parse_keys(fst, ("CompInflow", "InflowFile", "CompAero", "CompServo"))
    w = gate.parse_keys(inflow, ("WindType", "FileName_BTS"))
    require(f["CompInflow"] == "1", "FST_CHAIN_INFLOW_DISABLED")
    require(w["WindType"] == "3", "FST_CHAIN_NOT_TURBSIM_BTS")
    in_ref = _s07_safe_relative(f["InflowFile"])
    bts_ref = _s07_safe_relative(w["FileName_BTS"])
    require(in_ref.as_posix() == FST_CHAIN_INFLOW_NAME,
            "FST_CHAIN_INFLOW_MUST_COLOCATE_WITH_FST")
    require(bts_ref.as_posix() == INFLOW_NEW_BTS,
            "FST_CHAIN_BTS_REFERENCE_DRIFT")
    root = PurePosixPath(FST_CHAIN_CASE_ROOT)
    fst_path = root / FST_CHAIN_FST_NAME
    inflow_path = fst_path.parent / in_ref
    by_fst = fst_path.parent / bts_ref
    by_inflow = inflow_path.parent / bts_ref
    by_cwd = root / bts_ref
    require(by_fst == by_inflow == by_cwd,
            "FST_CHAIN_RELATIVE_BASES_DIVERGE")
    return {
        "source_FST_CompInflow": f["CompInflow"],
        "source_FST_CompAero": f["CompAero"],
        "source_FST_CompServo": f["CompServo"],
        "source_FST_InflowFile": f["InflowFile"],
        "candidate_Inflow_WindType": w["WindType"],
        "candidate_Inflow_FileName_BTS": w["FileName_BTS"],
        "staging_layout_NOT_CREATED": {
            "working_directory": root.as_posix(),
            "FST": fst_path.as_posix(),
            "InflowWind_copy_from_committed_candidate": inflow_path.as_posix(),
            "BTS_NOT_PRESENT": by_fst.as_posix()
        },
        "relative_BTS_from_FST_dir": by_fst.as_posix(),
        "relative_BTS_from_InflowWind_dir": by_inflow.as_posix(),
        "relative_BTS_from_explicit_cwd": by_cwd.as_posix(),
        "all_three_lexical_paths_equal": True
    }

def fst_inflow_bts_chain_selftest():
    fst = b'1 CompInflow\n"DTU_10MW_InflowWind.dat" InflowFile\n'
    inflow = b'3 WindType\n"inputs/U04p5_NTM_S01.bts" FileName_BTS\n'
    kw = {"fst_expected": sha(fst), "inflow_expected": sha(inflow)}
    require(inspect_fst_inflow_layout(fst, inflow, **kw)
            ["all_three_lexical_paths_equal"], "FST_CHAIN_POSITIVE")
    negatives = [
        (fst + b'"x" InflowFile\n', inflow),
        (fst.replace(b"1 CompInflow", b"0 CompInflow"), inflow),
        (fst.replace(b"DTU_10MW_InflowWind.dat", b"../DTU_10MW_InflowWind.dat"), inflow),
        (fst.replace(b"DTU_10MW_InflowWind.dat", b"/tmp/DTU_10MW_InflowWind.dat"), inflow),
        (fst.replace(b"DTU_10MW_InflowWind.dat", b"wind/DTU_10MW_InflowWind.dat"), inflow),
        (fst.replace(b"DTU_10MW_InflowWind.dat", b"C:/DTU_10MW_InflowWind.dat"), inflow),
        (fst, inflow.replace(b"3 WindType", b"1 WindType")),
        (fst, inflow.replace(b"U04p5_NTM_S01.bts", b"U09p343881_NTM_S01.bts")),
        (fst, inflow.replace(b"inputs/", b"../inputs/")),
    ]
    for i, (f, w) in enumerate(negatives):
        try:
            inspect_fst_inflow_layout(f, w, sha(f), sha(w))
        except (ValueError, KeyError):
            pass
        else:
            raise AssertionError("FST_CHAIN_NEGATIVE_ACCEPTED_" + str(i))
    print("S07_FST_INFLOW_BTS_SELFTEST_PASS_1_POSITIVE_9_NEGATIVE")

def _fst_canonical_manifest_gate(manifest_raw):
    require(sha(manifest_raw) == FST_CHAIN_MANIFEST_SHA, "FST_CHAIN_MANIFEST_SHA")
    rows = json.loads(manifest_raw)
    require(isinstance(rows, list), "FST_CHAIN_MANIFEST_NOT_LIST")
    logical = [r for r in rows if r.get("section") == "openfast-36-r2"
               and r.get("relative_path") == FST_CHAIN_LOGICAL_MEMBER]
    canonical = [r for r in rows if r.get("section") == "openfast-36-r2"
                 and r.get("relative_path") == FST_CHAIN_SOURCE_MEMBER]
    require(len(logical) == len(canonical) == 1, "FST_CHAIN_MANIFEST_CARDINALITY")
    l, c = logical[0], canonical[0]
    require(l["status"] == "duplicate-reference" and c["status"] == "included",
            "FST_CHAIN_MANIFEST_STATUS")
    require(l["canonical_member"] == c["canonical_member"] == FST_CHAIN_SOURCE_MEMBER,
            "FST_CHAIN_MANIFEST_CANONICAL_MEMBER")
    require(l["canonical_archive"] == c["canonical_archive"] == INFLOW_SOURCE_ZIP
            and c["archive"] == "openfast-36-r2/part-001.zip",
            "FST_CHAIN_MANIFEST_CANONICAL_ARCHIVE")
    require(l["sha256"].lower() == c["sha256"].lower() == FST_SHA
            and l["bytes"] == c["bytes"] == 7131,
            "FST_CHAIN_MANIFEST_BYTE_IDENTITY")
    return {"logical_NTM_member_not_in_ZIP": FST_CHAIN_LOGICAL_MEMBER,
            "logical_status": l["status"],
            "canonical_member_read_from_ZIP": FST_CHAIN_SOURCE_MEMBER,
            "canonical_status": c["status"], "canonical_bytes": c["bytes"],
            "canonical_sha256": FST_SHA, "manifest_sha256": sha(manifest_raw)}

def fst_inflow_bts_chain_command(repo_root, write):
    import zipfile
    manifest = _fst_canonical_manifest_gate(
        (repo_root / FST_CHAIN_MANIFEST).read_bytes())
    source_zip = repo_root / INFLOW_SOURCE_ZIP
    require(source_zip.is_file(), "FST_CHAIN_ARCHIVE_MISSING")
    with zipfile.ZipFile(source_zip) as archive:
        fst = archive.read(FST_CHAIN_SOURCE_MEMBER)
    require(sha(fst) == FST_SHA, "FST_CHAIN_ORIGINAL_SHA_MISMATCH")
    root = repo_root / ROOT / "experiments/T062"
    child = (root / INFLOW_CHILD_FILE).read_bytes()
    layout = inspect_fst_inflow_layout(fst, child)
    fst_inflow_bts_chain_selftest()
    receipt_path = root / GRID_RECEIPT_JSON
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    previous = receipt.get(INFLOW_RECEIPT_KEY, {})
    require(previous.get("candidate_card_sha256") == FST_CHAIN_CHILD_SHA,
            "FST_CHAIN_PARENT_RECEIPT_DRIFT")
    require(previous.get("input_sha256", {}).get("archive_zip") ==
            "ddfa02734274ad5bd36e84d975d18544bb5360554e25d71d8689f32313a95267",
            "FST_CHAIN_ZIP_RECEIPT_DRIFT")
    result = {
        "SOURCE": "Original manifest NTM S01 FST duplicate-reference resolved to exact SHA-identical canonical ETM S01 FST in part-001 ZIP; source-derived 4.5m/s S01 InflowWind candidate",
        "READING_LEVEL": "Original manifest logical NTM FST is duplicate-reference; SHA-identical canonical ETM S01 FST ZIP member read and SHA256 verified on GitHub runner; committed candidate InflowWind bytes re-read and SHA256 verified; BTS absent; OpenFAST runtime path resolution NOT executed",
        "REF": "Existing T062 original 18NTM source identity and InflowWind byte-exact patch; no new peer-reviewed full text",
        "STANDARD": "2025 IEC/GB licensed original clauses NOT READ; no formal DLC1.2 acceptance",
        "OFFICIAL": "Original archived OpenFAST v3.3.0-era FST input; staged path equality is a conditional lexical check, NOT OpenFAST executable validation",
        "RUN": "Python3 stdlib source ZIP/FST/candidate byte read, SHA256, 1 positive and 9 negative synthetic path tests; NO TurbSim/OpenFAST/Abaqus solver run",
        "FIG": 0, "TAB": "FST InflowFile and three candidate BTS lexical base resolutions",
        "input_sha256": {
            "source_archive_zip": previous["input_sha256"]["archive_zip"],
            "original_manifest": FST_CHAIN_MANIFEST_SHA,
            "original_fst": FST_SHA,
            "original_inflow": INFLOW_SOURCE_SHA,
            "committed_candidate_inflow": FST_CHAIN_CHILD_SHA
        },
        "source_FST_member": FST_CHAIN_SOURCE_MEMBER,
        "logical_NTM_FST_duplicate_reference": FST_CHAIN_LOGICAL_MEMBER,
        "canonical_manifest_gate": manifest,
        "layout": layout,
        "tests": {"original_fst_sha256": "PASS",
                  "candidate_inflow_sha256": "PASS",
                  "synthetic_positive": 1, "synthetic_negative_rejected": 9,
                  "three_lexical_bases_agree": "PASS"},
        "assumptions": "For a future staged run, launch with cwd=CASES/U04p5_NTM_S01, put FST and its referenced InflowWind copy together in that directory, and put the BTS in its inputs/ child directory. This makes FST-dir, InflowWind-dir and cwd interpretations identical; does NOT establish which base OpenFAST v3.3 uses.",
        "error_budget": "Source/candidate SHA exact, path equality exact under declared staging; executable path interpretation, missing BTS, DLL and operating-state errors NEED_ESTIMATE",
        "HOLD": "Staging layout is a plan only; BTS and OUTB absent; OpenFAST runtime path resolution, controller DLL identity/operation and 2025 IEC/GB licensed clauses unverified",
        "BTS_exists": False, "OUTB_exists": False,
        "physical_pass": False, "formal_dlc12_verified_slots": 0,
        "stages_passed": 0, "status": "SOURCE_LAYOUT_CONDITIONAL_NOT_RUN"
    }
    if write:
        receipt[FST_CHAIN_RECEIPT_KEY] = result
        receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
                                encoding="utf-8")
    else:
        require(receipt.get(FST_CHAIN_RECEIPT_KEY) == result,
                "FST_CHAIN_COMMITTED_RECEIPT_DRIFT")
    print("S07_FST_INFLOW_BTS_SOURCE_LAYOUT_CONDITIONAL_NOT_RUN",
          "fst_canonical=" + FST_CHAIN_SOURCE_MEMBER,
          "manifest_sha=" + FST_CHAIN_MANIFEST_SHA,
          "fst_sha=" + FST_SHA, "inflow_sha=" + FST_CHAIN_CHILD_SHA,
          "inflow_ref=" + layout["source_FST_InflowFile"],
          "bts_ref=" + layout["candidate_Inflow_FileName_BTS"],
          "three_bases_equal=1", "positive=1", "negative=9",
          "BTS=0", "OUTB=0", "DLC12_PASS=0")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--selftest",action="store_true")
    parser.add_argument("--grid-write",action="store_true")
    parser.add_argument("--grid-check",action="store_true")
    parser.add_argument("--dependency-write",action="store_true")
    parser.add_argument("--dependency-check",action="store_true")
    parser.add_argument("--inflow-rebind-write",action="store_true")
    parser.add_argument("--inflow-rebind-check",action="store_true")
    parser.add_argument("--repo-root",type=Path,default=Path("."))
    parser.add_argument("--out-dir",type=Path)
    args=parser.parse_args()
    if args.selftest: selftest(); return
    if args.inflow_rebind_write or args.inflow_rebind_check:
        require(not (args.inflow_rebind_write and args.inflow_rebind_check), "INFLOW_REBIND_MODE_CONFLICT")
        inflow_rebind_command(args.repo_root, args.inflow_rebind_write)
        return
    if args.dependency_write or args.dependency_check:
        require(not (args.dependency_write and args.dependency_check),
                'DEPENDENCY_MODE_CONFLICT')
        dependency_command(args.repo_root, args.dependency_write)
        return
    if args.grid_write or args.grid_check:
        require(not (args.grid_write and args.grid_check), 'GRID_MODE_CONFLICT')
        grid_command(args.repo_root, args.grid_write)
        return
    require(args.out_dir is not None,"OUT_DIR_REQUIRED")
    receipt=prepare(args.repo_root,args.out_dir)
    print("S10_75_PILOT_INPUT_PREPARED_NOT_RUN",receipt["output_turbsim_inp_sha256"])

if __name__=="__main__":
    main()
