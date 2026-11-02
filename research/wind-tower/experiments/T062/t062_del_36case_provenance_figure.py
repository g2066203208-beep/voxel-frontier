#!/usr/bin/env python3
"""T062: regenerate source-locked 36-case My/Mx load-DEL ranking and Figure 3.

Only uses the ALREADY independently recomputed 36-case, 72-row archived OUTB
derived CSV. Never invents the missing historical CORRECTED OUTB or rainflow
ledger, and does not launch any OpenFAST simulation. The legacy values are
published historical claims, NOT additional verified data points from the
current 36-case source.

Output: 36-case paired table, six-group actual data figure (SVG), JSON receipt.
This is load-level screening, NOT material fatigue life.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import xml.sax.saxutils

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "recomputed-load-fatigue/05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv"
SOURCE_GIT_BLOB = "1b334e9afdbd792a2f4b1a41cdb150dc3698352d"
LEGACY_MY_CASE = "U11p4_ETM_S03"
LEGACY_MX_CASE = "U19p202140_ETM_S02"
LEGACY_MY_KNM = 28177.010
LEGACY_MX_KNM = 9715.431
CURRENT_MY_CASE = "U11p4_ETM_S04"
EXPECTED_MY_KNM = 26802.478501532034
EXPECTED_S03_KNM = 23005.397834265204
EXPECTED_MX_KNM = 9468.855047640667

GROUPS = [
    ("U09p343881_NTM", "9.344 m/s  NTM"),
    ("U09p343881_ETM", "9.344 m/s  ETM"),
    ("U11p4_NTM", "11.4 m/s  NTM"),
    ("U11p4_ETM", "11.4 m/s  ETM"),
    ("U19p202140_NTM", "19.202 m/s  NTM"),
    ("U19p202140_ETM", "19.202 m/s  ETM"),
]


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def read_cases(raw: bytes):
    if git_blob(raw) != SOURCE_GIT_BLOB:
        raise ValueError("SOURCE_GIT_BLOB_MISMATCH")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if len(rows) != 72:
        raise ValueError("SOURCE_NOT_72_ROWS")
    found = {}
    for r in rows:
        cid, channel = r["case_id"], r["channel"]
        if channel not in ("TwrBsMyt", "TwrBsMxt"):
            raise ValueError("UNKNOWN_CHANNEL")
        if not (r["source_column"].startswith(channel) and r["source_column"].endswith("_[kN-m]")):
            raise ValueError("UNEXPECTED_LOAD_UNIT")
        if float(r["m"]) != 4.0 or float(r["Neq"]) != 100000.0:
            raise ValueError("NORMALIZATION_CHANGED")
        if cid.split("_S")[-1] not in ("01","02","03","04","05","06"):
            raise ValueError("BAD_SEED")
        if (cid, channel) in found:
            raise ValueError("DUPLICATE_CASE_CHANNEL")
        value = float(r["DEL"])
        if not math.isfinite(value) or value <= 0:
            raise ValueError("INVALID_DEL")
        found[cid, channel] = value
    expected = {prefix + "_S%02d" % i for prefix, _ in GROUPS for i in range(1, 7)}
    actual = {cid for cid, _ in found}
    if actual != expected or any((c, channel) not in found for c in expected
                                 for channel in ("TwrBsMyt","TwrBsMxt")):
        raise ValueError("INCOMPLETE_36_CASE_MATRIX")
    myrank = sorted(expected, key=lambda c: (-found[c,"TwrBsMyt"], c))
    mxrank = sorted(expected, key=lambda c: (-found[c,"TwrBsMxt"], c))
    if myrank[0] != CURRENT_MY_CASE:
        raise ValueError("CURRENT_MAX_CASE_REGRESSION")
    for key, val in [
        ((CURRENT_MY_CASE, "TwrBsMyt"), EXPECTED_MY_KNM),
        ((LEGACY_MY_CASE, "TwrBsMyt"), EXPECTED_S03_KNM),
        ((LEGACY_MX_CASE, "TwrBsMxt"), EXPECTED_MX_KNM)
    ]:
        if not math.isclose(found[key], val, rel_tol=0, abs_tol=1e-8):
            raise ValueError("SOURCE_CONTROL_VALUE_REGRESSION")
    return found, myrank, mxrank


def pack_csv(found, myrank, mxrank):
    m_rank = {cid: i+1 for i,cid in enumerate(myrank)}
    x_rank = {cid: i+1 for i,cid in enumerate(mxrank)}
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["case_id","URef_label","turbulence","seed",
                "archived_My_DEL_kNm","archived_Mx_DEL_kNm",
                "archived_My_rank_36","archived_Mx_rank_36",
                "legacy_claim_role","source_status"])
    for prefix, _ in GROUPS:
        for i in range(1,7):
            cid = f"{prefix}_S{i:02d}"
            role = ("legacy_My_control_UNVERIFIED_SOURCE" if cid==LEGACY_MY_CASE
                    else "legacy_Mx_control_UNVERIFIED_SOURCE" if cid==LEGACY_MX_CASE
                    else "none")
            w.writerow([cid,prefix.split("_")[0],prefix.split("_")[1],f"S{i:02d}",
                f"{found[cid,'TwrBsMyt']:.12f}",f"{found[cid,'TwrBsMxt']:.12f}",
                m_rank[cid],x_rank[cid],role,"ARCHIVED_ORIGINAL_OUTB_RECOMPUTATION"])
    return buf.getvalue().encode("utf-8")


def svg_plot(found):
    """Publication-oriented display of six true recorded seeds per NTM/ETM group."""
    width, height = 1130, 620
    x0, plot_width = 260, 720
    y0, step = 146, 72
    def x(v): return x0 + v/30000*plot_width
    def t(xv,yv,text,size=14,fill="#203045",anchor="start",weight="normal"):
        return f'<text x="{xv:.2f}" y="{yv:.2f}" font-family="Arial, sans-serif" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{xml.sax.saxutils.escape(str(text))}</text>'
    z=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="36 archived OpenFAST load DELs for tower base My. Legacy claim requires different source.">',
       f'<rect width="{width}" height="{height}" fill="#ffffff"/>']
    z.append(t(36,41,"36 archived OpenFAST cases  |  tower-base My load-DEL",23,weight="bold"))
    z.append(t(36,67,"m=4, Neq=100,000; 600 s each. Six actual seeds in each turbulence/wind-speed group.",13,fill="#56677a"))
    for tick in (0,5,10,15,20,25,30):
        xx=x(tick*1000)
        z.append(f'<line x1="{xx:.2f}" x2="{xx:.2f}" y1="95" y2="540" stroke="#e6eaf0" stroke-width="1"/>')
        z.append(t(xx,563,tick,13,fill="#56677a",anchor="middle"))
    z.append(t(620,598,"My load-DEL  (MN·m)   —   source: current archived 36 OUTB, NOT historical CORRECTED series",12,fill="#56677a",anchor="middle"))
    for gi,(prefix,label) in enumerate(GROUPS):
        cy=y0+gi*step
        z.append(t(35,cy+5,label,16,weight="bold" if "ETM" in prefix else "normal"))
        v=[found[f'{prefix}_S{s:02d}','TwrBsMyt'] for s in range(1,7)]
        z.append(f'<line x1="{x(min(v)):.2f}" x2="{x(max(v)):.2f}" y1="{cy}" y2="{cy}" stroke="#b9c6d4" stroke-width="3"/>')
        for s in range(1,7):
            cid=f"{prefix}_S{s:02d}"
            xx=x(found[cid,"TwrBsMyt"])
            yy=cy+((s-3.5)*5.4)
            color="#197c83" if "ETM" in prefix else "#566f90"
            radius=6.5 if cid==CURRENT_MY_CASE else 4.8
            z.append(f'<circle cx="{xx:.2f}" cy="{yy:.2f}" r="{radius}" fill="{color}" stroke="#ffffff" stroke-width="1.4"/>')
        z.append(t(1030,cy+4,f"n=6  |  {sum(v)/6/1000:.2f} mean",12,fill="#536576"))
    hx=x(LEGACY_MY_KNM)
    z.append(f'<line x1="{hx:.2f}" x2="{hx:.2f}" y1="94" y2="540" stroke="#c36d32" stroke-dasharray="5,5" stroke-width="1.5"/>')
    z.append(f'<circle cx="{hx:.2f}" cy="{y0+3*step+1}" r="7" fill="#ffffff" stroke="#c36d32" stroke-width="2.3"/>')
    z.append(t(1000,105,"Historic S03=28.177",13,fill="#a55221",weight="bold"))
    z.append(t(1000,122,"UNVERIFIED source",11,fill="#a55221"))
    z.append(t(x(EXPECTED_MY_KNM)-5,y0+3*step-24,"S04=26.802 (current)",11,fill="#197c83",anchor="end"))
    z.append(t(37,540,"NTM: slate   |   ETM: teal   |   hollow orange marker: legacy claim, not an extra OUTB observation",11,fill="#536576"))
    z.append("</svg>\n")
    return ("\n".join(z)).encode("utf-8")


def build(source: bytes):
    found, myrank, mxrank = read_cases(source)
    csv_bytes = pack_csv(found, myrank, mxrank)
    svg_bytes = svg_plot(found)
    a = found[LEGACY_MY_CASE,"TwrBsMyt"]
    b = found[CURRENT_MY_CASE,"TwrBsMyt"]
    c = found[LEGACY_MX_CASE,"TwrBsMxt"]
    n_my = 100000*(a/LEGACY_MY_KNM)**4
    n_mx = 100000*(c/LEGACY_MX_KNM)**4
    if abs(n_my-n_mx) < 1000:
        raise AssertionError("NORMALIZATION_TEST_INCONCLUSIVE")
    result = {
        "status": "36_ARCHIVED_LOAD_DEL_IDENTITY_PASS_LEGACY_CORRECTED_SOURCE_HOLD",
        "source_path": str(SOURCE.relative_to(HERE)),
        "source_git_blob_sha1": SOURCE_GIT_BLOB,
        "source_file_sha256": digest(source),
        "source_reading_level": "T062 archival 36 case / 72 DEL derived table originally recomputed from 36 OUTB; original OUTBs not re-decoded by this script",
        "row_count": 72,"case_count":36,"m":4,"Neq":100000,
        "historical_my": {"case": LEGACY_MY_CASE, "claimed_kNm": LEGACY_MY_KNM,
            "current_same_case_kNm":a,"difference_kNm":LEGACY_MY_KNM-a,
            "difference_pct_of_current":100*(LEGACY_MY_KNM/a-1),
            "claim_exceeds_current_global_max_kNm":LEGACY_MY_KNM-b},
        "current_my": {"case":myrank[0],"DEL_kNm":b,
            "current_S03_DEL_kNm":a,"S04_over_S03_pct":100*(b/a-1),
            "top3":[{"case":cid,"DEL_kNm":found[cid,"TwrBsMyt"]} for cid in myrank[:3]]},
        "historical_mx": {"case":LEGACY_MX_CASE,"claimed_kNm":LEGACY_MX_KNM,
            "current_same_case_kNm":c,"difference_kNm":LEGACY_MX_KNM-c},
        "normalization_counterfactual": {
            "formula":"Neq_implied=100000*(DEL_current/DEL_historical)^4, fixed current fourth moment",
            "Neq_needed_for_legacy_My_S03":n_my,
            "Neq_needed_for_legacy_Mx_S02":n_mx,
            "single_global_Neq_cannot_reconcile_both":True,
            "uniform_Neq_change_cannot_reverse_S03_S04_rank":True},
        "prior_rainflow_crosscheck":"RAINFLOW_METHOD_SUMMARY.json: generic/OpenFAST ASTM same S04 max; OpenFAST Windap S04 also max",
        "candidate_claim":"current source supports S04 maximum; historical CORRECTED S03 is unverified distinct-source claim; no invented version-mismatch root cause",
        "source_sha_note":"source Git blob SHA1 validated; output SHA256 values below",
        "csv_sha256":digest(csv_bytes),"svg_sha256":digest(svg_bytes),
        "error_budget":"source DEL serialized float64; exact-key assertions 1e-8 kN-m; ranking gap >3000 kN-m S04-S03; historical true uncertainty UNKNOWN",
        "REF":"historic 2026-09 Word manuscript reported S03 and S02; original historical CSV/outb bytes not available in this run",
        "STANDARD":"no new IEC/GB authorized clause checked; m=4 and Neq=1e5 are diagnostic normalization",
        "OFFICIAL":"OpenFAST archived output source previously checked, no new simulation or native solve",
        "RUN":"Python deterministic postprocessing from existing archival 72-row DEL CSV",
        "FIG":"grouped 36-case actual load-DEL and legacy source-divergence marker",
        "TAB":"36-case paired rank CSV",
        "HOLD":"historical CORRECTED archive, original cycle ledger and ranking original source hashes missing; cannot certify legacy S03",
        "physical_pass":False,"material_fatigue_life":False,
    }
    receipt=(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
    return csv_bytes, svg_bytes, receipt


def self_test(source: bytes):
    read_cases(source)
    for tampered in (source.replace(b"U11p4_ETM_S04", b"U11p4_ETM_S03",1),
                     source.replace(b"100000.0",b"100001.0",1),
                     source[:-2]):
        try:
            read_cases(tampered)
        except ValueError as e:
            assert str(e) == "SOURCE_GIT_BLOB_MISMATCH"
        else:
            raise AssertionError("SOURCE_MUTATION_ACCEPTED")
    csv_bytes,svg_bytes,receipt=build(source)
    r=json.loads(receipt)
    assert r["case_count"]==36
    assert r["current_my"]["case"]==CURRENT_MY_CASE
    assert abs(r["historical_my"]["difference_kNm"]-5171.612165734794)<1e-8
    assert len(csv_bytes.splitlines())==37
    assert svg_bytes.startswith(b"<svg") and b"UNVERIFIED source" in svg_bytes
    print("T062_36CASE_SOURCE_LOCKED_ORACLE_PASS_NO_SIMULATION")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir",type=Path)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    source=SOURCE.read_bytes()
    if args.self_test:
        self_test(source)
        return
    if not args.output_dir:ap.error("--output-dir required")
    csv_bytes,svg_bytes,receipt=build(source)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,data in [
        ("T062_36CASE_MY_MX_ARCHIVED_RANK_20261102.csv",csv_bytes),
        ("FIG3_T062_36CASE_MY_DEL_SOURCE_CONFLICT_20261102.svg",svg_bytes),
        ("T062_36CASE_DEL_SOURCE_COMPARISON_20261102.json",receipt)
    ]:
        target=args.output_dir/name
        if target.exists() and target.read_bytes()!=data:
            raise ValueError("REFUSE_OVERWRITE_DIFFERENT_CONTENT:"+name)
        target.write_bytes(data)
    print(receipt.decode("utf-8"))


if __name__=="__main__":
    sys.exit(main())
