#!/usr/bin/env python3
"""Source-only S07 controller audit: verify 18 native ServoDyn sums and OpenFAST stdout.
Never infer a runtime DLL SHA from an excluded archive entry or a matching file size.
No OpenFAST, Abaqus, or 700s simulation is launched.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path("research/wind-tower")
MANIFEST_SHA = "c9da25b3a967c9ed3b3a859666263c6964d8480798185e6e031539c38e4c3302"
DLL_SHA = "7aebb0d2166c0cc095d11c2b7bc13da136547c557b0f331dcdce84fe181802aa"
DLL_PATH = ROOT / "references/baselines-and-site-20261004/openfast-v330-adaptation/1FreeDecay/Control/libdiscon.dll"
CASES = [f"{wind}_NTM_S{seed:02d}" for wind in ("U09p343881", "U11p4", "U19p202140") for seed in range(1, 7)]
FIELDS = ["case", "srvd_sum_sha256", "stdout_sha256", "srvd_bytes", "stdout_bytes",
          "srvd_controller_hits", "stdout_controller_hits", "stdout_warning_lines",
          "stdout_error_lines", "manifest_dll_status", "manifest_dll_bytes",
          "manifest_dll_sha256", "runtime_dll_identity_verified", "formal_dlc12_reuse",
          "native_stdout_rosco_banner", "native_stdout_legacy_bladed_interface"]
TOKENS = re.compile(r"rosco|discon|dll|controller|servo|bladed|dynamic library|version", re.I)
WARN = re.compile(r"\bwarning\b", re.I)
ERROR = re.compile(r"\b(error|fatal|aborted)\b", re.I)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def require(test, message):
    if not test:
        raise ValueError(message)

def index_manifest(raw):
    require(sha(raw) == MANIFEST_SHA, "MANIFEST_SHA256_MISMATCH")
    rows = json.loads(raw)
    idx = {}
    for r in rows:
        key = (r["section"], r["relative_path"])
        require(key not in idx, "DUPLICATE_MANIFEST_ENTRY")
        idx[key] = r
    return idx

def get_original(idx, root, archives, case, filename):
    member = f"CASES/{case}/{filename}"
    rec = idx.get(("openfast-36-r2", member))
    require(rec is not None, "MISSING_MANIFEST:" + member)
    require(rec["status"] in ("included", "duplicate-reference"), "SOURCE_NOT_ARCHIVED:" + member)
    require(re.fullmatch("[0-9A-Fa-f]{64}", rec.get("sha256", "")), "MISSING_MEMBER_SHA:" + member)
    rel = Path(rec["canonical_archive"])
    full = (root / rel).resolve()
    require(full.is_relative_to(root.resolve()), "UNSAFE_ARCHIVE_PATH")
    if full not in archives:
        require(full.is_file(), "MISSING_ZIP:" + str(rel))
        archives[full] = zipfile.ZipFile(full)
    raw = archives[full].read(rec["canonical_member"])
    require(len(raw) == rec["bytes"], "MEMBER_LENGTH_MISMATCH:" + member)
    require(sha(raw) == rec["sha256"].lower(), "MEMBER_SHA256_MISMATCH:" + member)
    return raw, rec

def scan(raw):
    s = raw.decode("utf-8-sig", errors="replace")
    lines = s.splitlines()
    hits = [(i + 1, line.strip()[:260]) for i, line in enumerate(lines) if TOKENS.search(line)]
    return {
        "controller_hits": len(hits),
        "warning_lines": sum(bool(WARN.search(x)) for x in lines),
        "error_lines": sum(bool(ERROR.search(x)) for x in lines),
        "excerpts": [{"line": n, "text": v} for n, v in hits[:12]],
        "replacement_characters": s.count("\ufffd"),
    }

def build(root):
    base = root / ROOT
    idx = index_manifest((base / "archive/local-assets-20261004/file-manifest.json").read_bytes())
    dll = (root / DLL_PATH).read_bytes()
    require(len(dll) == 1122431 and sha(dll) == DLL_SHA, "REFERENCE_DLL_SHA256_MISMATCH")
    archives = {}
    rows, excerpts = [], {}
    try:
        for case in CASES:
            srvd, sr = get_original(idx, root, archives, case, "DTU_10MW_RWT.SrvD.sum")
            stdout, so = get_original(idx, root, archives, case, "openfast_stdout.log")
            d = idx.get(("openfast-36-r2", f"CASES/{case}/Control/libdiscon.dll"))
            require(d is not None and d["status"] == "excluded-format", "ORIGINAL_DLL_MANIFEST_CHANGED:" + case)
            require(not d.get("sha256"), "UNEXPECTED_ORIGINAL_DLL_SHA:" + case)
            require(d["bytes"] == 1122431, "ORIGINAL_DLL_LENGTH_CHANGED:" + case)
            a, b = scan(srvd), scan(stdout)
            stdout_text = stdout.decode("utf-8-sig", errors="replace")
            rosco_banners = re.findall(r"(?m)^\\s*Running (ROSCO-v[0-9]+(?:\\.[0-9]+){1,3})\\s*$", stdout_text)
            legacy_lines = re.findall(r"(?m)^\\s*Using legacy Bladed DLL interface\\.\\s*$", stdout_text)
            require(len(rosco_banners) == 1 and len(legacy_lines) == 1, "CONTROLLER_NATIVE_BANNER_MISSING_OR_DUPLICATE:" + case)
            rows.append({
                "case": case, "srvd_sum_sha256": sha(srvd), "stdout_sha256": sha(stdout),
                "srvd_bytes": len(srvd), "stdout_bytes": len(stdout),
                "srvd_controller_hits": a["controller_hits"], "stdout_controller_hits": b["controller_hits"],
                "stdout_warning_lines": b["warning_lines"], "stdout_error_lines": b["error_lines"],
                "manifest_dll_status": d["status"], "manifest_dll_bytes": d["bytes"],
                "manifest_dll_sha256": "", "runtime_dll_identity_verified": "NO",
                "formal_dlc12_reuse": "HOLD",
                "native_stdout_rosco_banner": rosco_banners[0],
                "native_stdout_legacy_bladed_interface": "YES"
            })
            excerpts[case] = {"srvd": a, "stdout": b}
    finally:
        for z in archives.values():
            z.close()
    require(len(rows) == 18 and len({r["case"] for r in rows}) == 18, "CASE_COVERAGE")
    require(all(r["native_stdout_rosco_banner"] == "ROSCO-v2.6.0" for r in rows), "MIXED_ROSCO_BANNER")
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    out = buf.getvalue().encode("utf-8")
    receipt = {
        "SOURCE": "Original 18 NTM OpenFAST .SrvD.sum and openfast_stdout.log ZIP members, pinned static manifest; separate repository reference controller DLL",
        "source_reading_level": "36 original ZIP member bytes checked against manifest member SHA256 and length; one independent reference DLL bytes checked; no original per-case DLL bytes",
        "REF": "T062 original FST/ServoDyn/TurbSim audit; T077 S07 A-case static DLL/ABI receipt; no new journal fulltext",
        "STANDARD": "No authorized IEC 61400-1/6:2025 clause read; no DLC1.2 certification",
        "OFFICIAL": "18 original OpenFAST stdout logs print Running ROSCO-v2.6.0; separate reference DLL not proven identical to original per-case runtime binary",
        "RUN": "Python3 stdlib SHA/ZIP text parser only; no OpenFAST/TurbSim/Abaqus native production run",
        "FIG": "none",
        "TAB": "18-row original controller log source QC CSV and limited original text excerpts in this receipt",
        "HOLD": "All 18 original stdout logs explicitly print ROSCO-v2.6.0 and legacy Bladed DLL interface; 18 per-case libdiscon.dll remain excluded-format without SHA; distinct reference DLL SHA verified but runtime binary equality and exact build unproven; BTS and IEC compliance unresolved",
        "input_sha256": {"static_manifest": MANIFEST_SHA, "reference_dll": DLL_SHA},
        "reference_dll_bytes": len(dll),
        "original_per_case_dll_manifest": {"excluded_format": 18, "original_sha256_available": 0, "nominal_bytes_each": 1122431},
        "source_logs_verified": 36, "case_count": 18,
        "archives_opened": len(archives),
        "summary": {
            "srvd_controller_hits": sum(int(r["srvd_controller_hits"]) for r in rows),
            "stdout_controller_hits": sum(int(r["stdout_controller_hits"]) for r in rows),
            "stdout_warning_lines": sum(int(r["stdout_warning_lines"]) for r in rows),
            "stdout_error_lines": sum(int(r["stdout_error_lines"]) for r in rows),
            "runtime_dll_sha_verified": 0, "formal_dlc12_reuse_approved": 0,
            "native_stdout_rosco_v2_6_0_banners": sum(r["native_stdout_rosco_banner"] == "ROSCO-v2.6.0" for r in rows),
            "native_stdout_legacy_bladed_interface": sum(r["native_stdout_legacy_bladed_interface"] == "YES" for r in rows),
        },
        "excerpts_by_case": excerpts,
        "output_csv_sha256": sha(out),
        "numerical_error_budget": "Exact member byte lengths and SHA256; keyword counts deterministic by UTF-8 replacement decoding; not a diagnostic of warning severity or actual DLL load; physics error NEED_ESTIMATE",
        "assumptions": "Controller keyword matches are text evidence only; DLL size equality does not prove binary identity; 18 NTM cases are historical screening",
        "physical_pass": False, "stages_passed": 0, "native_earthquake_results": 0
    }
    return out, receipt

def selftest():
    x = b"test"
    assert sha(x) == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    a = scan(b"DISCON dll\nWARNING: x\nError: y\n")
    assert a["controller_hits"] == 1 and a["warning_lines"] == 1 and a["error_lines"] == 1
    for bad in (b"", b"{}", b"[]"):
        try:
            index_manifest(bad)
        except ValueError as e:
            assert str(e) == "MANIFEST_SHA256_MISMATCH"
        else:
            raise AssertionError("MANIFEST_NEGATIVE_TEST_FAILED")
    print("S07_NATIVE_LOG_PARSER_SELFTEST_AND_3_NEGATIVE_TESTS_PASS")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path, default=Path("."))
    p.add_argument("--out", type=Path)
    p.add_argument("--receipt", type=Path)
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        selftest()
        return
    require(a.out is not None and a.receipt is not None, "OUTPUT_PATHS_REQUIRED")
    csv_bytes, receipt = build(a.repo_root)
    a.out.write_bytes(csv_bytes)
    a.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("S07_NATIVE_18_CONTROLLER_LOG_SOURCE_QC_NOT_RUNTIME_DLL_PASS", receipt["summary"], receipt["output_csv_sha256"])

if __name__ == "__main__":
    main()
