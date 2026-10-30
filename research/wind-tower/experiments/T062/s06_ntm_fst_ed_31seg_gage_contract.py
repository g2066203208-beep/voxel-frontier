#!/usr/bin/env python3
"""Read original 158 m FST/ElastoDyn bytes; plan (not execute) 31 CSEG gage batches.

No OpenFAST/Abaqus run, no DLC1.2/material fatigue/physics PASS.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

CASE = "U09p343881_ETM_S01"  # NTM FST/ED identity is cross-linked by 18-case SHA matrix.
FST = f"CASES/{CASE}/DTU_10MW_RWT.fst"
ED = f"CASES/{CASE}/DTU_10MW_RWT_ElastoDyn.dat"
EXPECTED = {
    "archive": "ddfa02734274ad5bd36e84d975d18544bb5360554e25d71d8689f32313a95267",
    "fst": "5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605",
    "ed": "6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65",
}
def sha(data):
    return hashlib.sha256(data).hexdigest()

def value(text, key, required=True):
    hits = [m.group(1).strip() for line in text.splitlines()
            if (m := re.match(r"^\s*(.*?)\s+" + re.escape(key) + r"\b", line, re.I))]
    if len(hits) != 1:
        if not required and not hits:
            return None
        raise ValueError(f"{key}: expected exactly one field, got {len(hits)}")
    return hits[0].split(" - ")[0].strip()

def make_plan(fst, ed, geom):
    height = float(value(ed, "TowerHt"))
    base = float(value(ed, "TowerBsHt"))
    nodes = int(value(ed, "TwrNodes"))
    ng = int(value(ed, "NTwGages"))
    gages = [int(v) for v in re.split(r"[\s,]+", value(ed, "TwrGagNd")) if v]
    if abs(height-158)>1e-6 or abs(base)>1e-6 or nodes!=1120:
        raise ValueError("UNEXPECTED_158M_ELASTODYN_GEOMETRY")
    if ng!=9 or len(gages)!=9 or len(set(gages))!=9:
        raise ValueError("ORIGINAL_NINE_GAGE_CONFIGURATION_MISMATCH")
    if "DTU_10MW_RWT_ElastoDyn.dat" not in (value(fst, "EDFile") or ""):
        raise ValueError("FST_EDFILE_MISMATCH")
    pitch=(height-base)/nodes
    rows=[]
    for row in csv.DictReader(io.StringIO(geom)):
        if not re.fullmatch(r"CSEG_?\d+", row["part"]):
            continue
        low=float(row["bottom_y_m"])
        high=float(row["top_y_m"])
        target=(low+high)/2
        node=round((target-base)/pitch+0.5)
        node=max(1,min(nodes,node))
        actual=base+(node-0.5)*pitch
        rows.append({"segment":row["part"],"z_bottom_m":low,"z_top_m":high,
                     "target_mid_z_m":target,"ED_node":node,"ED_node_z_m":actual,
                     "mapping_error_m":actual-target})
    if len(rows)!=31 or len({r["ED_node"] for r in rows})!=31:
        raise ValueError("CSEG_COUNT_OR_NODE_COLLISION")
    if max(r["z_top_m"] for r in rows)>112.01 or min(r["z_bottom_m"] for r in rows)<0:
        raise ValueError("CONCRETE_TOWER_SPAN_INVALID")
    # The source version has nine tower gage output slots; four independent
    # diagnostic configurations are needed for 31 stations (9+9+9+4).
    for i,r in enumerate(rows):
        r["batch"]=i//9+1
        r["slot"]=i%9+1
    batches=[{"batch":i,"NTwGages":len(b),"TwrGagNd":[r["ED_node"] for r in b],
              "segments":[r["segment"] for r in b]} for i in range(1,5)
             if (b:=[r for r in rows if r["batch"]==i])]
    if [x["NTwGages"] for x in batches]!=[9,9,9,4]:
        raise ValueError("BATCH_CAPACITY_FAILURE")
    contract={
        "FST":{k:value(fst,k,required=False) for k in
               ("EDFile","InflowFile","TMax","DT","DT_Out","CompElast","CompInflow","CompAero","CompServo")},
        "ElastoDyn":{"TowerHt_m":height,"TowerBsHt_m":base,"TwrNodes":nodes,
                     "original_NTwGages":ng,"original_TwrGagNd":gages,
                     "tower_node_pitch_m":pitch},
        "batches":batches,
        "max_midpoint_mapping_error_m":max(abs(r["mapping_error_m"]) for r in rows),
        "stage":"S06_PREPARATION_ONLY / NO_NATIVE_31GAGE_OUTPUT",
        "limitations":"Four output configurations are NOT four validated synchronized native histories; "
                      "repeat-run state/seed/controller determinism, channel identity, wind loads, "
                      "reference frame and six-component ownership require native verification. "
                      "No production solve is authorized.",
        "STANDARD":"No authorized IEC/GB/NB clause read in this run",
        "OFFICIAL":"OpenFAST ElastoDyn nine-gage limit: upstream OpenFAST discussions #3087/#3241; "
                   "check exact executable version before applying",
        "REF":"No journal article full text read",
        "RUN":"Python source-byte extraction and geometry mapping only",
        "FIG":"none",
        "TAB":"31 CSEG-to-ED-node rows and four planned gage batches",
        "error_budget":"mapping error is reported per segment; no interpolation of physical load histories; "
                       "dynamic/structural model error unknown",
        "physical_pass":False
    }
    return rows,contract

def selftest():
    ed="158 TowerHt\n0 TowerBsHt\n1120 TwrNodes\n9 NTwGages\n1,3,5,7,9,13,15,17,20 TwrGagNd\n"
    fst='"DTU_10MW_RWT_ElastoDyn.dat" EDFile\n'
    geom="part,bottom_y_m,top_y_m\n"+"".join(
        f"CSEG_{i:02d},{(i-1)*112/31},{i*112/31}\n" for i in range(1,32))
    rows,contract=make_plan(fst,ed,geom)
    assert len(rows)==31 and len(contract["batches"])==4
    for bad in (ed.replace("1120 TwrNodes","1119 TwrNodes"),
                ed.replace("9 NTwGages","31 NTwGages")):
        try:make_plan(fst,bad,geom)
        except ValueError:pass
        else:raise AssertionError("BAD_ELASTODYN_ACCEPTED")
    try:make_plan('"wrong.dat" EDFile\n',ed,geom)
    except ValueError:pass
    else:raise AssertionError("WRONG_EDFILE_ACCEPTED")
    print("SELFTEST_PASS 31_CSEG FOUR_BATCHES INVALID_GEOMETRY_GAGES_EDFILE_REJECTED")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--zip",type=Path)
    p.add_argument("--geometry",type=Path)
    p.add_argument("--outdir",type=Path)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:selftest();return
    if not a.zip or not a.geometry or not a.outdir:
        p.error("--zip --geometry --outdir required")
    raw=a.zip.read_bytes()
    if sha(raw)!=EXPECTED["archive"]:
        raise ValueError("ARCHIVE_SHA256_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip():raise ValueError("ZIP_CRC_FAILURE")
        fst=z.read(FST);ed=z.read(ED)
    if sha(fst)!=EXPECTED["fst"] or sha(ed)!=EXPECTED["ed"]:
        raise ValueError("FST_OR_ED_SHA256_MISMATCH")
    geometry=a.geometry.read_bytes()
    rows,contract=make_plan(fst.decode("utf-8-sig"),ed.decode("utf-8-sig"),
                            geometry.decode("utf-8-sig"))
    contract["SOURCE"]={"archive_sha256":sha(raw),"fst_sha256":sha(fst),
                        "ed_sha256":sha(ed),"geometry_sha256":sha(geometry),
                        "reading_level":"Original ZIP byte stream and FST/ED original text; "
                                        "31 CSEG source geometry; no new OUTB/solver",
                        "cross_case":"18 NTM FST/ED hashes match these two exact source hashes "
                                     "per existing S06_18NTM_INPUT_SOURCE_IDENTITY_20261031.csv"}
    a.outdir.mkdir(parents=True,exist_ok=True)
    cp=a.outdir/"S06_31CSEG_ORIGINAL_ED_GAGE_MAPPING_20261031.csv"
    with cp.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    contract["TAB_sha256"]=sha(cp.read_bytes())
    jp=a.outdir/"S06_NTM_ORIGINAL_FST_ED_31GAGE_CONTRACT_20261031.json"
    jp.write_text(json.dumps(contract,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("SOURCE_FST_ED_31CSEG_MAPPING_PASS",json.dumps({
        "rows":len(rows),"batches":[x["NTwGages"] for x in contract["batches"]],
        "max_mapping_error_m":contract["max_midpoint_mapping_error_m"],
        "FST":contract["FST"],"csv_sha256":contract["TAB_sha256"],
        "receipt_sha256":sha(jp.read_bytes()),"physical_pass":False}))
if __name__=="__main__":main()
