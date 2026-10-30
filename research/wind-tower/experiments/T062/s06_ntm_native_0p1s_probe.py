#!/usr/bin/env python3
"""One 0.1 s native OpenFAST channel/initialization probe, NOT NTM production.

Uses original SHA-verified 158 m source files, nine mapped CSEG gages,
and deliberately substitutes a steady 9.343881 m/s wind for the 436 MB
TurbSim BTS. Therefore native success is only an interface/channel test,
not a stochastic-wind or structural-physics validation.
Python 3.11 stdlib. No Abaqus, no 700 s run.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import math
import struct
import shutil
import sys
import zipfile

from s06_historical_outb_source_gate import outb_header, selected_samples

ETM = "U09p343881_ETM_S01"
NTM = "U09p343881_NTM_S01"
SOURCE_SHA = {
    "static_part001": "ddfa02734274ad5bd36e84d975d18544bb5360554e25d71d8689f32313a95267",
    "fst": "5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605",
    "ed": "6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65",
    "tower": "f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983",
    "servo": "103e7bd71209a095b833ca4ba62627ae7724870615112fdccfbff502076c966e",
    "inflow": "d204329f881836ffe0895b7d81aa28cae7540d5df56c754880db3d6c5c11d3a9",
    "discon": "8f5d7546420ee34838e66b63e4b26d64460be5d5492f99c60b6d1ef977ffc61a",
    "dll": "7aebb0d2166c0cc095d11c2b7bc13da136547c557b0f331dcdce84fe181802aa",
    "exe": "0cc8147fdda188365b8eacda8a831e74fafef59440d71185d66c3272af9e176a",
}
GAGES = [13,39,65,91,117,142,168,194,220]
LOAD_SUFFIX = ("FLxt","FLyt","FLzt","MLxt","MLyt","MLzt")

def digest(data):
    return hashlib.sha256(data).hexdigest()

def verify(label, data):
    got=digest(data)
    if got!=SOURCE_SHA[label]:
        raise ValueError(f"SOURCE_SHA256_MISMATCH {label} expected={SOURCE_SHA[label]} got={got}")
    return got

def replace_scalar(text, key, value, expected=None):
    pat=re.compile(r"^(\s*)\S+(\s+"+re.escape(key)+r"\b[^\r\n]*)$",re.M|re.I)
    hits=list(pat.finditer(text))
    if len(hits)!=1:
        raise ValueError(f"FIELD_CARDINALITY_{key} {len(hits)}")
    m=hits[0]
    original=text[m.start():m.end()].split()[0]
    if expected is not None and original!=str(expected):
        raise ValueError(f"FIELD_ORIGINAL_MISMATCH_{key} {original}")
    return text[:m.start()]+m.group(1)+str(value)+m.group(2)+text[m.end():]

def replace_gages(text, gages=GAGES):
    pat=re.compile(r"^([ \t]*)[0-9, \t]+?(\s+TwrGagNd\b[^\r\n]*)$",re.M|re.I)
    hits=list(pat.finditer(text))
    if len(hits)!=1:
        raise ValueError(f"TWGAGND_CARDINALITY {len(hits)}")
    m=hits[0]
    old=[int(v) for v in re.split(r"[\s,]+",text[m.start():m.end()].split("TwrGagNd")[0].strip()) if v]
    if old!=[1,3,5,7,9,13,15,17,20]:
        raise ValueError(f"UNEXPECTED_ORIGINAL_GAGES {old}")
    if not 1 <= len(gages) <= 9 or len(set(gages)) != len(gages):
        raise ValueError('BAD_BATCH_GAGE_COUNT')
    return text[:m.start()]+m.group(1)+",".join(map(str,gages))+m.group(2)+text[m.end():]

def selftest():
    s="700 TMax - stop\n0.05 DT_Out - output\n"
    assert replace_scalar(s,"TMax","0.1",expected="700").startswith("0.1 TMax")
    assert replace_scalar("3 WindType - x\r\n".replace("\r\n","\n"),"WindType","1",expected="3").startswith("1 WindType")
    assert replace_scalar("100 TStart - x\n","TStart","0",expected="100").startswith("0 TStart")
    for bad in ("700 TMax\n700 TMax\n","700 SomethingElse\n"):
        try:replace_scalar(bad,"TMax","0.1")
        except ValueError:pass
        else:raise AssertionError("BAD_SCALAR_ACCEPTED")
    ed="1,3,5,7,9,13,15,17,20 TwrGagNd - original\n"
    assert ",".join(map(str,GAGES)) in replace_gages(ed)
    try:replace_gages(ed.replace("20 TwrGagNd","21 TwrGagNd"))
    except ValueError:pass
    else:raise AssertionError("BAD_GAGE_SOURCE_ACCEPTED")
    try:verify("fst",b"tampered")
    except ValueError:pass
    else:raise AssertionError("BAD_SHA_ACCEPTED")
    print("SELFTEST_PASS scalar_field_cardinality original_gage_identity SHA_rejection")

def prepare(args):
    contract=json.loads(Path(args.contract).read_text(encoding="utf-8"))
    if contract["ElastoDyn"]["TwrNodes"]!=1120 or contract["ElastoDyn"]["TowerHt_m"]!=158.0:
        raise ValueError("CONTRACT_158M_IDENTITY_FAILURE")
    batch=int(args.batch)
    if batch not in (1,2,3,4) or [b['NTwGages'] for b in contract['batches']]!=[9,9,9,4]:
        raise ValueError('INVALID_BATCH_CONTRACT')
    gages=contract['batches'][batch-1]['TwrGagNd']
    if len(gages)!=contract['batches'][batch-1]['NTwGages'] or len(set(gages))!=len(gages):
        raise ValueError('BATCH_GAGE_IDENTITY_FAILURE')
    if contract['batches'][0]['TwrGagNd']!=GAGES:raise ValueError('BATCH1_CONTRACT_FAILURE')
    a=Path(args.archive1);b=Path(args.archive2);s=Path(args.supp)
    verify("static_part001",a.read_bytes())
    with zipfile.ZipFile(a) as z1, zipfile.ZipFile(b) as z2, zipfile.ZipFile(s) as zs:
        for z in (z1,z2,zs):
            if z.testzip() is not None:raise ValueError("ZIP_CRC_FAILURE")
        def read(member):
            for z in (z1,z2):
                try:return z.read(member)
                except KeyError:continue
            raise ValueError("SOURCE_MEMBER_MISSING "+member)
        source_root="CASES/"+ETM+"/"
        names=[n for z in (z1,z2) for n in z.namelist() if n.startswith(source_root) and not n.endswith("/")]
        if len(names)!=len(set(names)):raise ValueError("DUPLICATE_SOURCE_MEMBER")
        out=Path(args.outdir);out.mkdir(parents=True,exist_ok=True)
        for name in names:
            rel=name[len(source_root):]
            target=out/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(read(name))
        # The archived model resolves blade/airfoil references via ../Rotor, not case/Rotor.
        # Preserve the original shared CASES/Rotor tree in outdir.parent/Rotor.
        shared=sorted(set(n for z in (z1,z2) for n in z.namelist()
                          if n.startswith("CASES/Rotor/") and not n.endswith("/")))
        if not any(n.endswith("/DTU_10MW_ElastoDyn_Blades.dat") for n in shared):
            raise ValueError("SHARED_ROTOR_BLADE_SOURCE_MISSING")
        shared_hashes={}
        for name in shared:
            rel=name[len("CASES/Rotor/"):]
            target=out.parent/"Rotor"/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            data=read(name);target.write_bytes(data)
            shared_hashes[rel]=digest(data)
        if shared_hashes["DTU_10MW_ElastoDyn_Blades.dat"]!="6ad2426fd429f4e01008700d31d4b64d79358522bcf265ce12f7706e8a1f895d":
            raise ValueError("SHARED_ROTOR_BLADE_SHA256_MISMATCH")
        fst=read(source_root+"DTU_10MW_RWT.fst")
        ed=read(source_root+"DTU_10MW_RWT_ElastoDyn.dat")
        tower=read(source_root+"C02R3R2_158M_Tower.dat")
        servo=read(source_root+"Control/DTU_10MW_RWT_ServoDyn.dat")
        inflow=read("CASES/"+NTM+"/DTU_10MW_InflowWind.dat")
        discon=zs.read(source_root+"Control/DTU_10MW_RWT_DISCON.IN")
    originals={"fst":fst,"ed":ed,"tower":tower,"servo":servo,"inflow":inflow,"discon":discon,
               "dll":Path(args.dll).read_bytes(),"exe":Path(args.exe).read_bytes()}
    for label,data in originals.items():verify(label,data)
    fst_new=replace_scalar(fst.decode("utf-8-sig"),"TMax","0.1",expected="700")
    fst_new=replace_scalar(fst_new,"TStart","0",expected="100")
    ed_new=replace_gages(ed.decode("utf-8-sig"),gages)
    if batch==4:ed_new=replace_scalar(ed_new,'NTwGages','4',expected='9')
    # Original NTM InflowWind source uses CRLF; normalize derived diagnostic copy only.
    inflow_text=inflow.decode("utf-8-sig").replace("\r\n","\n")
    inflow_new=replace_scalar(inflow_text,"WindType","1",expected="3")
    inflow_new=replace_scalar(inflow_new,"HWindSpeed","9.343881")
    for rel,data in {
        "DTU_10MW_RWT.fst":fst_new.encode("utf-8"),
        "DTU_10MW_RWT_ElastoDyn.dat":ed_new.encode("utf-8"),
        "DTU_10MW_InflowWind.dat":inflow_new.encode("utf-8"),
        "Control/DTU_10MW_RWT_DISCON.IN":discon,
        "Control/libdiscon.dll":originals["dll"],
    }.items():
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    report={
        "case":NTM,"diagnostic_only":True,"native_model_height_m":158,
        "TMax_s":0.1,"DT_s":0.0125,"DT_Out_s":0.05,
        "gage_nodes":gages,"batch":batch,"source_sha256":SOURCE_SHA,
        "source_archives_sha256":{"part001":digest(a.read_bytes()),"part002":digest(b.read_bytes()),
                                  "supp":digest(s.read_bytes())},
        "shared_rotor_source_sha256":shared_hashes,
        "derived_sha256":{rel:digest((out/rel).read_bytes()) for rel in
                          ("DTU_10MW_RWT.fst","DTU_10MW_RWT_ElastoDyn.dat",
                           "DTU_10MW_InflowWind.dat","Control/DTU_10MW_RWT_DISCON.IN",
                           "Control/libdiscon.dll")},
        "modifications":["FST TMax 700 -> 0.1 s and TStart 100 -> 0 s (required for native initialization)",f"ED TwrGagNd original 9 -> batch{batch} {len(gages)}; NTwGages 9 -> {len(gages)}",
                         "InflowWind CRLF normalized in diagnostic child; WindType 3 -> 1, HWindSpeed -> 9.343881 m/s"],
        "source_reading_level":"Original SHA-pinned FST/ED/NTM InflowWind/Tower/Servo/ROSCO binary bytes",
        "STANDARD":"No authorized IEC/GB/NB clauses read",
        "REF":"Existing T062 original input identity and S06 gage mapping",
        "OFFICIAL":"OpenFAST v3.5.3 native executable SHA-pinned; steady-wind input is diagnostic substitution",
        "RUN":"0.1 s native attempt pending",
        "FIG":"none","TAB":"9 output gage channel contract",
        "HOLD":"Steady wind is NOT NTM; 0.1 s is NOT settled operating response, DLC1.2, 31-gage synchronous data, or material fatigue",
        "physical_pass":False
    }
    (out/"S06_0P1S_PREP_RECEIPT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("PREP_PASS",json.dumps({"case":NTM,"batch":batch,"gages":gages,"TMax":0.1,
                                   "shared_rotor_files":len(shared_hashes),
                                   "wind":"STEADY_DIAGNOSTIC_NOT_NTM","source_sha256_verified":len(originals)}))

def inspect(args):
    out=Path(args.outdir)
    prep=json.loads((out/"S06_0P1S_PREP_RECEIPT.json").read_text(encoding="utf-8"))
    exit_code=int(Path(args.exit_code_file).read_text().strip()) if Path(args.exit_code_file).exists() else None
    log=Path(args.log)
    log_text=log.read_text(encoding="utf-8",errors="replace") if log.exists() else ""
    outb=out/"DTU_10MW_RWT.outb"
    receipt={"case":NTM,"native_exit_code":exit_code,"native_log_sha256":digest(log.read_bytes()) if log.exists() else None,
             "native_log_tail":log_text[-5000:],"outb_present":outb.exists(),
             "source_sha256":prep["source_sha256"],"derived_sha256":prep["derived_sha256"],
             "wind":"STEADY_DIAGNOSTIC_NOT_NTM","physical_pass":False,
             "SOURCE":"original SHA-verified 158m OpenFAST inputs; 0.1s derived FST/ED/inflow",
             "REF":"T062 source mapping; no new journal full text",
             "STANDARD":"no authorized standard clauses read",
             "OFFICIAL":"OpenFAST v3.5.3 native executable, original controller DLL",
             "RUN":"0.1s native initialization attempt; see exit code and log SHA",
             "FIG":"none","TAB":"native nine-gage header and 3 time samples if produced",
             "error_budget":"0.05s output spacing; 3 samples expected; packed OUTB quantization 0.5/scale; no physical accuracy inference",
             "HOLD":"0.1s steady-wind diagnostic only, NOT NTM/31-gage production/ABAQUS or physics PASS"}
    ok=False
    try:
        if exit_code!=0:raise ValueError(f"OPENFAST_EXIT_{exit_code}")
        if not outb.exists():raise ValueError("OUTB_MISSING")
        raw=outb.read_bytes();h=outb_header(raw)
        if h["num_samples"]!=3 or abs(h["time_increment_s"]-0.05)>1e-8:
            raise ValueError(f"TIME_GRID_MISMATCH {h['num_samples']} {h['time_increment_s']}")
        ng=len(prep['gage_nodes'])
        required=[f"TwHt{i}{s}" for i in range(1,ng+1) for s in LOAD_SUFFIX]
        required += [f"TwHt{i}TPzi" for i in range(1,ng+1)]
        missing=[c for c in required if c not in h["channel_names"]]
        if missing:raise ValueError("MISSING_GAGE_CHANNELS "+",".join(missing))
        rows=[]
        j=h['channel_names'].index('TwHt1FLxt')-1
        scale=h['column_scales'][j];offset=h['column_offsets'][j]
        if scale==0:raise ValueError('BAD_NATIVE_PACKED_SCALE')
        for k in range(3):
            packed=struct.unpack_from('<h',raw,h['data_offset_bytes']+2*(k*h['num_output_channels']+j))[0]
            rows.append({'time_s':h['first_time_s']+k*h['time_increment_s'],
                         'channels':{'TwHt1FLxt':{'value':(packed-offset)/scale,'unit':h['channel_units'][j+1]}}})
        receipt['batch']=prep['batch']
        receipt['gage_nodes']=prep['gage_nodes']
        receipt["outb_sha256"]=digest(raw)
        receipt["header"]={k:h[k] for k in ("file_id","num_samples","num_output_channels",
                                          "first_time_s","time_increment_s")}
        receipt["native_gage_channels"]=len(required)
        receipt["sample_times_s"]=[r["time_s"] for r in rows]
        receipt["sample_first_gage"]=[r["channels"].get("TwHt1FLxt") for r in rows]
        receipt["channel_diagnostic_pass"]=True
        ok=True
    except Exception as exc:
        receipt["channel_diagnostic_pass"]=False
        receipt["failure"]=str(exc)
    Path(args.receipt).write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("NATIVE_0P1S_CHANNEL_DIAGNOSTIC",json.dumps({
        "pass":ok,"exit_code":exit_code,"failure":receipt.get("failure"),
        "outb_sha256":receipt.get("outb_sha256"),"samples":receipt.get("sample_times_s")}))
    if not ok:sys.exit(2)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--prepare",action="store_true")
    p.add_argument("--inspect",action="store_true")
    p.add_argument('--batch',type=int,default=1)
    for flag in ("archive1","archive2","supp","dll","exe","contract","outdir",
                 "log","exit-code-file","receipt"):
        p.add_argument("--"+flag)
    a=p.parse_args()
    if a.selftest:selftest()
    elif a.prepare:prepare(a)
    elif a.inspect:inspect(a)
    else:p.error("choose --selftest, --prepare or --inspect")
if __name__=="__main__":main()
