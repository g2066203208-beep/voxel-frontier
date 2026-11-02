#!/usr/bin/env python3
"""S07 original OpenFAST 2s artifact source-identity gate. No solver execution."""
import argparse, hashlib, io, json, sys, zipfile
from pathlib import Path

ZIP_SHA = "7fcae2bf57be571cacc6d3d9b82f1a254257ce59fdb946a1cfb56d3639eb9f1b"
OUTB = (
 "c3f40b400f827fbcdd49e9a63f5bb2295a5c0f368a9644b90b591d66b7bb0242",
 "be9dd3b6dd611925cf5c314200ed4e1c111218bd4464d6cccf0ee1f73bb3b902",
 "867553e8ef29806fccdaad24bb3938493138b31b616c9a9446e81cbefe53bbd7",
 "701575bd988177b7c0c666640b49981c653d77738893909cb307fccdf172c855",
)
BTS_SHA = "ad68a83a63f197c528c07502db8adff883e9c737863ef3c4cab99cfa76052147"
CASE = "U09p343881_ETM_S06"

def sha(b): return hashlib.sha256(b).hexdigest()

def audit(raw, check_zip=True):
    if check_zip and sha(raw) != ZIP_SHA: raise ValueError("ARCHIVE_SHA256_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        expected={"research/wind-tower/experiments/T062/S06_ETM_NATIVE_2S_OVERLAP_QC_20261101.json"}
        for n in range(1,5):
            expected.update(f"work/batch{n}/{x}" for x in (
                "DTU_10MW_RWT.outb","native_exit_code.txt","native_stdout.log",
                "S06_0P1S_PREP_RECEIPT.json"))
        if len(names)!=len(set(names)) or set(names)!=expected:
            raise ValueError("ARCHIVE_MEMBER_IDENTITY_MISMATCH")
        if any(p.startswith("/") or ".." in Path(p).parts for p in names):
            raise ValueError("UNSAFE_ZIP_PATH")
        summary=json.loads(z.read(next(x for x in names if x.endswith("OVERLAP_QC_20261101.json"))))
        if (summary["case"],summary["samples"],summary["TMax_s"])!=(CASE,41,2):
            raise ValueError("NATIVE_SUMMARY_IDENTITY_MISMATCH")
        batches=[]
        for n in range(1,5):
            p=f"work/batch{n}/"
            h=sha(z.read(p+"DTU_10MW_RWT.outb"))
            if h!=OUTB[n-1]: raise ValueError("OUTB_SHA256_MISMATCH")
            r=json.loads(z.read(p+"S06_0P1S_PREP_RECEIPT.json"))
            log=z.read(p+"native_stdout.log").decode("utf-8")
            code=z.read(p+"native_exit_code.txt").decode().strip()
            if (r["case"],r["batch"],r["TMax_s"],r["DT_Out_s"])!=(CASE,n,2.0,0.05):
                raise ValueError("BATCH_INPUT_IDENTITY_MISMATCH")
            if r["etm_s06_bts_original_sha256"]!=BTS_SHA:
                raise ValueError("BTS_IDENTITY_MISMATCH")
            if code!="0" or any(x not in log for x in (
                "OpenFAST-v3.5.3","Intel(R) Fortran Compiler 2021",
                "Using legacy Bladed DLL interface","OpenFAST terminated normally.")):
                raise ValueError("NATIVE_LOG_IDENTITY_MISMATCH")
            batches.append((n,h,r))
        r=batches[0][2]
        missing=[]
        def add(kind,name,h):
            if len(h)!=64: raise ValueError("SOURCE_SHA_MISSING")
            missing.append({"kind":kind,"name":name,"sha256":h,"in_output_zip":False})
        for n,_,rr in batches:
            add("derived_ed",f"batch{n}/DTU_10MW_RWT_ElastoDyn.dat",
                rr["derived_sha256"]["DTU_10MW_RWT_ElastoDyn.dat"])
        for name in ("DTU_10MW_RWT.fst","DTU_10MW_InflowWind.dat","Control/libdiscon.dll"):
            add("derived_common",name,r["derived_sha256"][name])
        add("wind","ETM_S06.bts",BTS_SHA)
        for name in ("tower","servo","exe"):
            add("original_component",name,r["source_sha256"][name])
        for name,h in sorted(r["shared_rotor_source_sha256"].items()):
            add("shared_rotor",name,h)
        for name,h in sorted(r["source_archives_sha256"].items()):
            add("source_archive",name,h)
        return {
            "stage":"S07","status":"OUTPUT_ZIP_VERIFIED__NATIVE_RERUN_INPUT_BUNDLE_HOLD",
            "artifact_id":13080759167,"artifact_sha256":sha(raw),
            "member_count":len(names),"native_outb_count":4,
            "native_samples_per_batch":41,"native_samples_total":164,
            "outb_sha256":[h for _,h,_ in batches],
            "missing_identity_count":len(missing),"missing_identities":missing,
            "runnable_bundle_in_this_zip":False,"native_exact_dcm_obtained":False,
            "SOURCE":"Original Actions artifact 13080759167; 17 raw ZIP members and 4 OUTB SHA256; batch preparation receipts.",
            "REF":"T062 2s overlap receipt and source-locked ElastoDyn diagnostic.",
            "STANDARD":"No new authorized IEC/GB/NB text.",
            "OFFICIAL":"Historical OpenFAST-v3.5.3 Windows Intel/ROSCO DLL; not a newly built diagnostic binary.",
            "RUN":"Actual ZIP byte validation only; 0 new native OpenFAST runs.",
            "FIG":"0","TAB":"4 source-verified OUTB and 23 missing source identities",
            "assumptions":"Output ZIP is not the original source bundle; missing here does not imply missing from all archives.",
            "error_budget":"SHA256 exact; 2s packed OUTB error inherited; DCM and full 600s state uncertainty unbounded.",
            "HOLD":"Need original SHA-locked model+ETM BTS+compatible controller/runtime and patched OpenFAST build; no exact native DCM.",
            "physical_pass":False
        }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--out",type=Path)
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--require-runnable",action="store_true")
    a=p.parse_args()
    raw=a.archive.read_bytes()
    result=audit(raw)
    if a.selftest:
        rejects=0
        for bad in (raw+b"X",raw[:100]+bytes([raw[100]^1])+raw[101:]):
            try: audit(bad)
            except ValueError as e:
                if str(e)!="ARCHIVE_SHA256_MISMATCH": raise
                rejects+=1
            else: raise AssertionError("TAMPER_ACCEPTED")
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            content={k:z.read(k) for k in z.namelist()}
        del content["work/batch4/native_stdout.log"]
        b=io.BytesIO()
        with zipfile.ZipFile(b,"w") as z:
            for k,v in content.items():z.writestr(k,v)
        try: audit(b.getvalue(),check_zip=False)
        except ValueError as e:
            if str(e)!="ARCHIVE_MEMBER_IDENTITY_MISMATCH": raise
            rejects+=1
        else: raise AssertionError("MISSING_MEMBER_ACCEPTED")
        if rejects!=3: raise AssertionError("NEGATIVE_COUNT")
        result["tests"]={"positive_real_zip":"PASS","negative_rejections":rejects}
    if a.out:
        if a.out.exists(): raise ValueError("REFUSE_OVERWRITE")
        a.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":result["status"],"native_samples":164,
                      "missing_identities":len(result["missing_identities"]),
                      "tests":result.get("tests"),"physical_pass":False},sort_keys=True))
    if a.require_runnable:
        print("S07_NATIVE_RERUN_HOLD_MISSING_INPUT_BUNDLE",file=sys.stderr)
        return 3
    return 0

if __name__=="__main__": sys.exit(main())
