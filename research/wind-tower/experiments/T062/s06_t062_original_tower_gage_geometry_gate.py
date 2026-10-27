#!/usr/bin/env python3
"""S06 source-identity gate: original ElastoDyn tower gage nodes vs archived OUTB TPzi.

Read-only, Python 3.11+ standard library. Source bytes and SHA are mandatory.
This is NOT OpenFAST/Abaqus production, material fatigue or structural physics PASS.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

CASE = "U09p343881_ETM_S01"
ED_MEMBER = f"CASES/{CASE}/DTU_10MW_RWT_ElastoDyn.dat"
FST_MEMBER = f"CASES/{CASE}/DTU_10MW_RWT.fst"
ED_SHA = "6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65"
FST_SHA = "5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605"
OUTB_SHA = "0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c"

def sha(b):
    return hashlib.sha256(b).hexdigest()

def field(source, name):
    hits = []
    for line in source.splitlines():
        m = re.match(r"^\s*(\S+)\s+" + re.escape(name) + r"\b", line, flags=re.I)
        if m:
            hits.append(m.group(1))
    if len(hits) != 1:
        raise ValueError(f"{name}: expected one unambiguous input value; got {hits}")
    return hits[0]

def audit_values(ed_text, receipt):
    tower_top = float(field(ed_text, "TowerHt"))
    tower_base = float(field(ed_text, "TowerBsHt"))
    nodes = int(field(ed_text, "TwrNodes"))
    n_gages = int(field(ed_text, "NTwGages"))
    gage_nodes = [int(v) for v in field(ed_text, "TwrGagNd").split(",")]
    if not (tower_top > tower_base >= 0 and nodes > 0):
        raise ValueError("invalid tower height or node count")
    if len(gage_nodes) != n_gages or n_gages != 9:
        raise ValueError("tower gage count disagrees with archived nine-channel receipt")
    if len(set(gage_nodes)) != len(gage_nodes) or not all(1 <= n <= nodes for n in gage_nodes):
        raise ValueError("duplicate or out-of-range TwrGagNd")
    if receipt.get("outb_sha256", "").lower() != OUTB_SHA:
        raise ValueError("OUTB source SHA mismatch")
    if receipt.get("case") != CASE:
        raise ValueError("OUTB case identity mismatch")
    stats = receipt["full_synchronous_native_series"]["native_channel_summary"]
    pitch = (tower_top - tower_base) / nodes
    rows = []
    for i, node in enumerate(gage_nodes, 1):
        key = f"TwHt{i}TPzi"
        actual = float(stats[key]["first"])
        predicted = tower_base + (node - 0.5) * pitch
        rows.append({"gage": i, "TwrGagNd": node,
                     "observed_TPzi_m": actual,
                     "predicted_midnode_z_m": predicted,
                     "residual_m": actual - predicted})
    max_error = max(abs(row["residual_m"]) for row in rows)
    # Exploratory source-identity tolerance, not an IEC or physical accuracy threshold.
    if max_error > 1e-5:
        raise ValueError(f"gage position mismatch > 1e-5 m: {max_error}")
    zspan = max(x["observed_TPzi_m"] for x in rows) - min(x["observed_TPzi_m"] for x in rows)
    return {
        "tower_top_m": tower_top, "tower_base_m": tower_base, "TwrNodes": nodes,
        "NTwGages": n_gages, "TwrGagNd": gage_nodes, "element_pitch_m": pitch,
        "gage_position_rows": rows, "max_absolute_midnode_residual_m": max_error,
        "observed_gage_z_span_m": zspan,
        "observed_span_fraction_of_158m": zspan / 158.0,
        "gage_node_coverage_fraction": max(gage_nodes) / nodes,
        "status": "SOURCE_GAGE_MAPPING_MATCH / FULL_TOWER_COVERAGE_HOLD",
        "conclusion": "The nine OUTB TPzi values agree with original tower node midpoint positions. "
                      "Their near-base concentration is a TwrGagNd selection effect; "
                      "it does not prove a 2.75-m tower or provide 158-m distributed loads.",
        "limitations": "No dynamic force ownership, RP angle orientation, 31-gage equivalence, "
                       "Abaqus native check, material fatigue, seismic RUN or standard clause PASS."
    }

def self_test():
    nodes = [1, 3, 5, 7, 9, 13, 15, 17, 20]
    ed = ("158.0 TowerHt\n0.0 TowerBsHt\n1120 TwrNodes\n9 NTwGages\n"
          + ",".join(map(str, nodes)) + " TwrGagNd\n")
    receipt = {"case": CASE, "outb_sha256": OUTB_SHA,
               "full_synchronous_native_series": {"native_channel_summary": {
                   f"TwHt{i}TPzi": {"first": round((n - .5) * 158 / 1120, 9)}
                   for i, n in enumerate(nodes, 1)}}}
    result = audit_values(ed, receipt)
    assert result["max_absolute_midnode_residual_m"] < 5e-10
    try:
        audit_values(ed.replace("1120 TwrNodes", "56 TwrNodes"), receipt)
    except ValueError:
        pass
    else:
        raise AssertionError("wrong node count not rejected")
    try:
        audit_values(ed, {**receipt, "outb_sha256": "0" * 64})
    except ValueError:
        pass
    else:
        raise AssertionError("wrong OUTB SHA not rejected")
    print("SELF_TEST_PASS: exact synthetic midpoint, wrong-node and wrong-SHA rejection")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--static-zip", type=Path)
    p.add_argument("--receipt", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return
    if not all([args.static_zip, args.receipt, args.out]):
        p.error("--static-zip, --receipt and --out required")
    with zipfile.ZipFile(args.static_zip) as z:
        bad = z.testzip()
        if bad:
            raise ValueError(f"ZIP CRC failed: {bad}")
        ed = z.read(ED_MEMBER)
        fst = z.read(FST_MEMBER)
    if sha(ed) != ED_SHA or sha(fst) != FST_SHA:
        raise ValueError("original FST/ElastoDyn SHA mismatch")
    receipt_bytes = args.receipt.read_bytes()
    result = audit_values(ed.decode("utf-8-sig"), json.loads(receipt_bytes))
    result.update({
        "SOURCE": "original static OpenFAST archive ElastoDyn/FST and original OUTB decoded receipt",
        "archive_path": str(args.static_zip), "archive_sha256": sha(args.static_zip.read_bytes()),
        "elastodyn_member": ED_MEMBER, "elastodyn_sha256": sha(ed),
        "fst_member": FST_MEMBER, "fst_sha256": sha(fst),
        "outb_sha256": OUTB_SHA, "receipt_sha256": sha(receipt_bytes),
        "OFFICIAL": "OpenFAST ElastoDyn input TwrNodes/TwrGagNd and tower midnode interpolation; "
                    "source-file numerical identity check only",
        "REF": "no new article read", "STANDARD": "no authorized standard clause read",
        "RUN": "Python source-data QC only, no physics solver",
        "FIG": "none", "TAB": "nine gage position rows",
        "error_budget": "1e-5 m exploratory midpoint comparison tolerance; "
                        "binary packing quantization and physical model uncertainty not certified"
    })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("ORIGINAL_SOURCE_GAGE_GEOMETRY_QC", json.dumps({
        k: result[k] for k in ("tower_top_m", "TwrNodes", "TwrGagNd",
                             "max_absolute_midnode_residual_m",
                             "observed_gage_z_span_m", "status")}))
    print("NO PHYSICS PASS")

if __name__ == "__main__":
    main()
