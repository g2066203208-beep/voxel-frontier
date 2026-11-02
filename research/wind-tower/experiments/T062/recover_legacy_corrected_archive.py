#!/usr/bin/env python3
"""Restore original Sep-2026 rainflow/DEL evidence from the 2026-10-04 PRIMARY ZIP.

This is deliberately NOT the 2026-10-04-supplement/36xOUTB archive.
All extracted original bytes are checked against the primary file-manifest.json
SHA256 and length, and the embedded SHA256_MANIFEST_CORRECTED.csv is used
to compare original historical OUTB hashes with the supplement source.
No OpenFAST rerun or physical/material-fatigue validity is inferred.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

WT = Path(__file__).resolve().parents[2]
OLD_DIR = WT / "archive/local-assets-20261004"
NEW_DIR = WT / "archive/local-assets-20261004-supplement"
ORIG_ZIP = OLD_DIR / "openfast-36-r2/part-001.zip"
ORIG_MANIFEST = OLD_DIR / "file-manifest.json"
NEW_MANIFEST = NEW_DIR / "file-manifest.json"
FILES = (
    "03_RAINFLOW_CYCLE_LEDGER.csv",
    "05_LOAD_DEL_M4_ALL36.csv",
    "07_DEL_CONTROL_RANKING.csv",
    "SHA256_MANIFEST_CORRECTED.csv",
    "rainflow_del_r1.py",
    "analyze_r2_corrected.py",
    "02_CHANNEL_MAPPING_QA_RAINFLOW.csv",
    "finalize_rainflow_del.py",
    "CHANNEL_INDEXING_CORRECTION.md",
    "11_METHOD_AND_EVIDENCE.md",
)
REQUIRED = {"03_RAINFLOW_CYCLE_LEDGER.csv": 5585315,
            "05_LOAD_DEL_M4_ALL36.csv": 11583,
            "07_DEL_CONTROL_RANKING.csv": 11795,
            "SHA256_MANIFEST_CORRECTED.csv": 116189,
            "finalize_rainflow_del.py": 7019,
            "rainflow_del_r1.py": 6852}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def csv_rows(raw):
    errors = []
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            text = raw.decode(encoding)
            return list(csv.DictReader(io.StringIO(text))), encoding
        except UnicodeError as e:
            errors.append(str(e))
    raise ValueError("CSV_DECODE_REJECTED:" + "; ".join(errors))


def original_entry(entries, name):
    x = [e for e in entries if e.get("section") == "openfast-36-r2"
         and e.get("relative_path") == name and e.get("status") == "included"]
    if len(x) != 1 or x[0].get("canonical_archive") != (
            "research/wind-tower/archive/local-assets-20261004/openfast-36-r2/part-001.zip"):
        raise ValueError("PRIMARY_MANIFEST_IDENTITY_MISSING_OR_AMBIGUOUS:" + name)
    return x[0]


def get_member(z, entries, name):
    e = original_entry(entries, name)
    # Original archive packing varies; use exact or unique trailing path.
    names = [n for n in z.namelist() if n == e["canonical_member"]
             or n.endswith("/" + e["canonical_member"])]
    if len(names) != 1:
        raise ValueError("ORIGINAL_ZIP_MEMBER_AMBIGUOUS:" + name + ":" + str(names))
    b = z.read(names[0])
    if len(b) != int(e["bytes"]) or sha(b).lower() != e["sha256"].lower():
        raise ValueError("PRIMARY_ZIP_SOURCE_SHA_MISMATCH:" + name)
    if name in REQUIRED and len(b) != REQUIRED[name]:
        raise ValueError("ORIGINAL_FILE_SIZE_REGRESSION:" + name)
    return b


def original_outb_hashes(embedded_manifest):
    entries, enc = csv_rows(embedded_manifest)
    if not entries:
        raise ValueError("EMPTY_ORIGINAL_EMBEDDED_MANIFEST")
    fields = set(entries[0])
    if not {"relative_path", "sha256"}.issubset(fields):
        raise ValueError("ORIGINAL_EMBEDDED_SHA_MANIFEST_SCHEMA_UNEXPECTED:" + str(fields))
    selected={}
    for e in entries:
        path = e["relative_path"].replace("\\", "/")
        if path.endswith("/DTU_10MW_RWT.outb"):
            case_match=re.search(r"CASES/([^/]+)/DTU_10MW_RWT\.outb$", path, re.I)
            if case_match is None:
                raise ValueError("UNEXPECTED_HISTORICAL_OUTB_PATH:" + path)
            case=case_match.group(1)
            hs=e["sha256"].strip().lower()
            if not re.fullmatch(r"[0-9a-f]{64}", hs) or case in selected:
                raise ValueError("INVALID_OR_DUPLICATE_HISTORICAL_OUTB_SHA")
            selected[case]={"sha256":hs,"path":path}
    return selected,enc,len(entries)


def current_outb_hashes(manifest):
    selected={}
    for e in manifest:
        if e.get("section") != "openfast-36-r2":continue
        path=e.get("relative_path","").replace("\\","/")
        m=re.fullmatch(r"CASES/([^/]+)/DTU_10MW_RWT\.outb",path)
        if not m: continue
        case=m.group(1); hs=e.get("sha256","").strip().lower()
        if case in selected or not re.fullmatch("[0-9a-f]{64}",hs):
            raise ValueError("MALFORMED_CURRENT_OUTB_MANIFEST")
        selected[case]={"sha256":hs,"path":path}
    if len(selected) != 36:raise ValueError("CURRENT_OUTB_NOT_36")
    return selected


def run(outdir):
    orig_entries=json.loads(ORIG_MANIFEST.read_bytes())
    new_entries=json.loads(NEW_MANIFEST.read_bytes())
    with zipfile.ZipFile(ORIG_ZIP) as z:
        bad=z.testzip()
        if bad is not None:raise ValueError("PRIMARY_ZIP_CRC_ERROR:"+bad)
        by_name={name:get_member(z,orig_entries,name) for name in FILES}
    old_hashes,old_enc,old_total=original_outb_hashes(by_name["SHA256_MANIFEST_CORRECTED.csv"])
    new_hashes=current_outb_hashes(new_entries)
    cases=sorted(set(old_hashes)|set(new_hashes))
    comparison=[]
    for case in cases:
        a=old_hashes.get(case); b=new_hashes.get(case)
        state=("MATCHED_SOURCE_SHA" if a and b and a["sha256"]==b["sha256"]
               else "DIFFERENT_SOURCE_SHA" if a and b else "MISSING_ONE_SOURCE")
        comparison.append({"case":case,
            "legacy_original_outb_sha256":a["sha256"] if a else "",
            "current_supplement_outb_sha256":b["sha256"] if b else "",
            "identity":state})
    ledger,enc=csv_rows(by_name["03_RAINFLOW_CYCLE_LEDGER.csv"])
    delta,enc5=csv_rows(by_name["05_LOAD_DEL_M4_ALL36.csv"])
    rank,enc7=csv_rows(by_name["07_DEL_CONTROL_RANKING.csv"])
    # Original source may use different column names than the T062 recomputation;
    # do not silently normalize or fabricate missing case/channel labels.
    preserved={
        "original_archive":str(ORIG_ZIP.relative_to(WT)),
        "original_archive_sha256":sha(ORIG_ZIP.read_bytes()),
        "original_manifest_sha256":sha(ORIG_MANIFEST.read_bytes()),
        "current_manifest_sha256":sha(NEW_MANIFEST.read_bytes()),
        "original_file_manifest_entries_verified":len(FILES),
        "source_files":[{"name":n,"sha256":sha(b),"bytes":len(b)}
                        for n,b in by_name.items()],
        "old_embedded_manifest_rows":old_total,
        "legacy_outb_sha_count":len(old_hashes),
        "current_outb_sha_count":len(new_hashes),
        "matched_old_current_outb":sum(x["identity"]=="MATCHED_SOURCE_SHA" for x in comparison),
        "different_old_current_outb":sum(x["identity"]=="DIFFERENT_SOURCE_SHA" for x in comparison),
        "missing_one_source":sum(x["identity"]=="MISSING_ONE_SOURCE" for x in comparison),
        "original_embedded_manifest_encoding":old_enc,
        "legacy_ledger":{"rows":len(ledger),"encoding":enc,"columns":list(ledger[0]) if ledger else [],
                         "first_rows":ledger[:2]},
        "legacy_del":{"rows":len(delta),"encoding":enc5,
                      "columns":list(delta[0]) if delta else [],"first_rows":delta[:3]},
        "legacy_rank":{"rows":len(rank),"encoding":enc7,
                      "columns":list(rank[0]) if rank else [],"first_rows":rank[:3]},
        "source_reading_level":"actual original 2026-10-04 part-001 ZIP bytes CRC and SHA verified; embedded corrected manifest 36-case original OUTB SHA compared to actual current supplement manifest",
        "claim_limit":"Source identities and original CSV are restored; does not independently re-run the historical DEL algorithm or prove material fatigue",
        "physical_pass":False,"s10_material_life_pass":False,
        "standard":"No new authorized IEC/GB material clause read",
        "original_ledger_source_recovered":True,
        "ref":"2026-09 R2Z74 original thesis used these historical 03/05/07 CSV",
        "run":"GitHub Actions Python stdlib ZIP/CSV/SHA source-level processing only",
        "fig":"None; original historical evidence ledger and rankings",
        "tab":"Original 03/05/07 CSV, 36-case old vs current OUTB source hashes",
    }
    outdir.mkdir(parents=True,exist_ok=True)
    p=outdir/"LEGACY_PRIMARY_36OUTB_SHA_COMPARISON_20261102.csv"
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["case","legacy_original_outb_sha256","current_supplement_outb_sha256","identity"],lineterminator="\n")
        w.writeheader();w.writerows(comparison)
    # Keep 5.5MB real ledger as temporary CI artifact, NOT a duplicate repo commit.
    for name,b in by_name.items():
        (outdir/name).write_bytes(b)
    rec=outdir/"LEGACY_PRIMARY_RECOVERY_RECEIPT_20261102.json"
    rec.write_text(json.dumps(preserved,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:preserved[k] for k in (
      "legacy_outb_sha_count","current_outb_sha_count","matched_old_current_outb",
      "different_old_current_outb","legacy_ledger","legacy_del","legacy_rank"
    )},ensure_ascii=False,indent=2)[:8000])
    return preserved


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    run(args.output_dir)


if __name__=="__main__":
    main()
