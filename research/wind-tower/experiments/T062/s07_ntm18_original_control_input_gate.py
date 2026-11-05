#!/usr/bin/env python3
"""S07 source-only: inspect original 18 NTM TurbSim/FST/ServoDyn/DISCON archives.
No new OpenFAST/TurbSim/Abaqus run; no IEC 2025 or DLC1.2 compliance claim.
Run: python s07_ntm18_original_control_input_gate.py --repo-root . --out ...csv --receipt ...json
"""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = "research/wind-tower"
STATIC_SHA = "c9da25b3a967c9ed3b3a859666263c6964d8480798185e6e031539c38e4c3302"
SUPPLEMENT_SHA = "35235d543bae4b82b24260a16fae1885f8123ef3cf3d8482145c704ea1eaa392"
IDENTITY_SHA = "d57ff9e71b58b531b1aaa357ad7a57a86daf529e061f9d8996cf2453b04a7da5"
CASES = [f"{u}_NTM_S{i:02d}" for u in ("U09p343881", "U11p4", "U19p202140") for i in range(1, 7)]
TURB_KEYS = ("RandSeed1", "RandSeed2", "TurbModel", "IECstandard", "IECturbc",
             "IEC_WindType", "NumGrid_Z", "NumGrid_Y", "TimeStep", "AnalysisTime",
             "UsableTime", "HubHt", "RefHt", "URef", "GridHeight", "GridWidth", "PLExp")
FST_KEYS = ("TMax", "DT", "DT_Out", "CompAero", "CompServo", "CompInflow", "CompElast",
            "EDFile", "InflowFile", "ServoFile")
SERVO_KEYS = ("PCMode", "VSContrl", "HSSBrMode", "DLL_FileName", "DLL_InFile",
              "DLL_ProcName", "DLL_DT", "YCMode")
INFLOW_KEYS = ("WindType", "FileName_BTS", "Filename", "RefHt", "HWindSpeed")
HEADER = ["case", "nominal_case_U_mps", "turb_URef_mps", "turb_seed1", "turb_seed2",
          "turb_model", "turb_IECstandard", "turb_IECturbc", "turb_IEC_WindType",
          "turb_grid_z", "turb_grid_y", "turb_dt_s", "turb_analysis_s", "turb_usable_s",
          "turb_hub_m", "fst_TMax_s", "fst_DT_s", "fst_DT_Out_s", "fst_CompAero",
          "fst_CompServo", "servo_PCMode", "servo_VSContrl", "servo_DLL_FileName",
          "servo_DLL_InFile", "inflow_WindType", "inflow_FileName_BTS",
          "turb_inp_sha256", "turb_sum_sha256", "turb_dat_sha256",
          "inflow_sha256", "fst_sha256", "servo_sha256", "discon_sha256",
          "bts_archive_status", "bts_archived_sha256", "formal_DLC12_reuse_verdict"]

def sha(b):
    return hashlib.sha256(b).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def read_pinned(path, expected):
    raw = path.read_bytes()
    require(sha(raw) == expected, "SOURCE_SHA256_MISMATCH:" + str(path))
    return raw

def manifest_index(raw):
    rows = json.loads(raw)
    index = {}
    for row in rows:
        key = (row["section"], row["relative_path"])
        require(key not in index, "DUPLICATE_MANIFEST_ENTRY:" + str(key))
        index[key] = row
    return index

def parse_key(text, key):
    """OpenFAST/TurbSim standard first-value then key; comments after ! are ignored."""
    pattern = re.compile(r'^\s*("[^"]*"|[^\s]+)\s+' + re.escape(key) + r'(?=\s|$)', re.I)
    values = []
    for line in text.splitlines():
        line = line.split("!", 1)[0]
        match = pattern.match(line)
        if match:
            values.append(match.group(1).strip().strip('"').strip("'"))
    require(len(values) <= 1, "DUPLICATE_INPUT_KEY:" + key)
    return values[0] if values else ""

def parse_keys(raw, keys):
    text = raw.decode("utf-8-sig", errors="replace")
    require("\ufffd" not in text, "UNDECODABLE_SOURCE_INPUT")
    return {key: parse_key(text, key) for key in keys}


# Historical 158m source ServoDyn: exact bytes are inside static part-001.zip,
# NOT the v3.3 reference file. This checks a source card, not actual cut-in.
ORIGINAL_SERVO_SHA = "103e7bd71209a095b833ca4ba62627ae7724870615112fdccfbff502076c966e"
ORIGINAL_SERVO_BYTES = 12108
STARTUP_KEYS = ("PCMode", "VSContrl", "GenTiStr", "GenTiStp",
                "SpdGenOn", "TimGenOn", "TimGenOf", "DLL_FileName")

def inspect_servo_startup(raw, expected_sha=ORIGINAL_SERVO_SHA,
                          expected_bytes=ORIGINAL_SERVO_BYTES):
    import math
    require(len(raw) == expected_bytes, "SERVO_ORIGINAL_BYTE_COUNT")
    require(sha(raw) == expected_sha, "SERVO_ORIGINAL_SHA256")
    fields = parse_keys(raw, STARTUP_KEYS)
    require(all(fields.values()), "SERVO_MISSING_REQUIRED_FIELD")
    require(fields["PCMode"] == "5" and fields["VSContrl"] == "5",
            "SERVO_ORIGINAL_CONTROLLER_MODE_NOT_5_5")
    require(fields["GenTiStr"].lower() in ("true", "false") and
            fields["GenTiStp"].lower() in ("true", "false"),
            "SERVO_BOOLEAN_FLAG")
    for key in ("SpdGenOn", "TimGenOn", "TimGenOf"):
        require(re.fullmatch(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[EeDd][+-]?\d+)?",
                             fields[key]) is not None, "SERVO_NUMERIC_" + key)
        number = float(fields[key].replace("D", "E").replace("d", "e"))
        require(math.isfinite(number) and number >= 0, "SERVO_FINITE_NONNEG_" + key)
    require(Path(fields["DLL_FileName"]).name.lower() in ("libdiscon.dll", "libdiscon.so"),
            "SERVO_DLL_NAME")
    return {
        "SOURCE": "Original historical 158m OpenFAST ServoDyn member from SHA-locked static ZIP",
        "READING_LEVEL": "Original member bytes, not reference-card or derived CSV",
        "REF": "T062 18NTM original-input gate and 12-stage critical path",
        "STANDARD": "IEC 61400-1/6:2025 licensed clauses NOT READ; no normative cut-in inference",
        "OFFICIAL": "OpenFAST ServoDyn field labels in original source card; not ROSCO runtime validation",
        "RUN": "Python source-only SHA/field/semantic checks; no OpenFAST/Abaqus production run",
        "FIG": "0", "TAB": "8 original source-card fields",
        "source_member_sha256": sha(raw), "source_member_bytes": len(raw),
        "fields": fields,
        "field_semantics": {
            "GenTiStr": "True: generator start by TimGenOn; False: by SpdGenOn generator rpm",
            "GenTiStp": "True: stop by TimGenOf; False: when generator power zero",
            "SpdGenOn": "HSS generator speed in rpm, not wind speed m/s",
            "TimGenOn": "generator startup time s; not wind-speed cut-in",
            "TimGenOf": "generator stop time s; not wind-speed cut-out",
            "PCMode_VSContrl": "5/5 external DLL; source timers do not validate DLL internal control states"
        },
        "cut_in_verdict": "WIND_SPEED_CUT_IN_NOT_ESTABLISHED",
        "error_budget": "Byte length/SHA exact; field tokens exact; physical cut-in, hysteresis, controller runtime and wind-bin relevance NOT ESTIMATED",
        "HOLD": "Original controller DLL state and 4-8m/s operating validity not certified; no IEC2025/DLC1.2 or material fatigue PASS",
        "physical_pass": False, "stage_passed": 0
    }

def servo_startup_self_test():
    template = ("5 PCMode\n5 VSContrl\nTrue GenTiStr\nFalse GenTiStp\n"
                "9999.9 SpdGenOn\n0 TimGenOn\n9999.9 TimGenOf\n"
                '"libdiscon.dll" DLL_FileName\n')
    raw = template.encode()
    good = inspect_servo_startup(raw, sha(raw), len(raw))
    assert good["cut_in_verdict"] == "WIND_SPEED_CUT_IN_NOT_ESTABLISHED"
    bad = [
        (raw, "0"*64, len(raw)),
        (raw, sha(raw), len(raw)+1),
        (raw.replace(b"5 PCMode", b"0 PCMode"), None, None),
        (raw.replace(b"True GenTiStr", b"maybe GenTiStr"), None, None),
        (raw.replace(b"9999.9 SpdGenOn", b"NaN SpdGenOn"), None, None),
        (raw.replace(b"0 TimGenOn", b"-1 TimGenOn"), None, None),
        (raw.replace(b"9999.9 TimGenOf", b"9999.9 TimGenOf\\n1 TimGenOf"), None, None),
        (raw.replace(b"False GenTiStp\\n", b""), None, None)
    ]
    for b, h, n in bad:
        try:
            inspect_servo_startup(b, h or sha(b), n or len(b))
        except ValueError:
            pass
        else:
            raise AssertionError("SERVO_BAD_SOURCE_ACCEPTED")
    print("S07_ORIGINAL_SERVO_STARTUP_SELFTEST_PASS: 1 positive, 8 negative")

def nominal(case):
    match = re.fullmatch(r"U(09p343881|11p4|19p202140)_NTM_S0[1-6]", case)
    require(match is not None, "UNEXPECTED_CASE:" + case)
    return {"09p343881": 9.343881, "11p4": 11.4, "19p202140": 19.202140}[match.group(1)]

class Source:
    def __init__(self, root, indexes):
        self.root = root.resolve()
        self.indexes = indexes
        self.zips = {}
        self.read_count = 0
    def entry(self, manifest, section, member):
        record = self.indexes[manifest].get((section, member))
        require(record is not None, "MISSING_MANIFEST:" + section + ":" + member)
        return record
    def get(self, manifest, section, member):
        record = self.entry(manifest, section, member)
        require(record["status"] in ("included", "duplicate-reference"),
                "NOT_ARCHIVED:" + member)
        require(re.fullmatch(r"[0-9A-Fa-f]{64}", record.get("sha256", "")),
                "NO_SOURCE_SHA:" + member)
        rel = Path(record["canonical_archive"])
        path = (self.root / rel).resolve()
        require(path.is_relative_to(self.root), "UNSAFE_ARCHIVE_PATH")
        if path not in self.zips:
            require(path.is_file(), "MISSING_ARCHIVE:" + str(rel))
            self.zips[path] = zipfile.ZipFile(path)
        data = self.zips[path].read(record["canonical_member"])
        require(len(data) == record["bytes"], "SOURCE_BYTE_LENGTH_MISMATCH:" + member)
        require(sha(data) == record["sha256"].lower(), "ARCHIVED_MEMBER_SHA_MISMATCH:" + member)
        self.read_count += 1
        return data, record
    def close(self):
        for z in self.zips.values():
            z.close()

def build(root):
    base = root / ROOT
    static_raw = read_pinned(base / "archive/local-assets-20261004/file-manifest.json", STATIC_SHA)
    supp_raw = read_pinned(base / "archive/local-assets-20261004-supplement/file-manifest.json", SUPPLEMENT_SHA)
    identity_raw = read_pinned(base / "experiments/T062/S06_18NTM_INPUT_SOURCE_IDENTITY_20261031.csv", IDENTITY_SHA)
    identity = list(csv.DictReader(io.StringIO(identity_raw.decode("utf-8"))))
    require(len(identity) == 18 and {r["case"] for r in identity} == set(CASES), "IDENTITY_CASE_SET")
    by_case = {r["case"]: r for r in identity}
    src = Source(root, {"static": manifest_index(static_raw), "supp": manifest_index(supp_raw)})
    rows, missing, bts_status, seeds = [], Counter(), Counter(), {}
    try:
        discon, _ = src.get("supp", "openfast-36-r2",
                             "CASES/U09p343881_ETM_S01/Control/DTU_10MW_RWT_DISCON.IN")
        for case in CASES:
            prefix = "CASES/" + case + "/"
            fst, _ = src.get("static", "openfast-36-r2", prefix + "DTU_10MW_RWT.fst")
            ed, _ = src.get("static", "openfast-36-r2", prefix + "DTU_10MW_RWT_ElastoDyn.dat")
            servo, _ = src.get("static", "openfast-36-r2", prefix + "Control/DTU_10MW_RWT_ServoDyn.dat")
            inflow, _ = src.get("static", "openfast-36-r2", prefix + "DTU_10MW_InflowWind.dat")
            turb = {}
            for ext in ("inp", "sum", "dat"):
                turb[ext], _ = src.get("static", "turbSim-36", "inputs/" + case + "." + ext)
            i = by_case[case]
            for key, raw in (("fst_sha256", fst), ("elastodyn_sha256", ed),
                             ("servodyn_sha256", servo), ("inflowwind_sha256", inflow)):
                require(sha(raw) == i[key], "IDENTITY_ARCHIVE_DIVERGENCE:" + case + ":" + key)
            tk = parse_keys(turb["inp"], TURB_KEYS)
            fk = parse_keys(fst, FST_KEYS)
            sk = parse_keys(servo, SERVO_KEYS)
            ik = parse_keys(inflow, INFLOW_KEYS)
            for group, values in (("turb", tk), ("fst", fk), ("servo", sk), ("inflow", ik)):
                for key, value in values.items():
                    if not value:
                        missing[group + "." + key] += 1
            bts = src.entry("static", "turbSim-36", "inputs/" + case + ".bts")
            bts_status[bts["status"]] += 1
            require(bts["status"] == "prior-size-deferral-cancelled-see-transfer-ledger"
                    and not bts.get("sha256") and not bts.get("canonical_archive"),
                    "UNEXPECTED_BTS_ARCHIVE_STATE:" + case)
            seeds[case] = tk["RandSeed1"]
            row = {
                "case": case, "nominal_case_U_mps": f"{nominal(case):.6f}",
                "turb_URef_mps": tk["URef"], "turb_seed1": tk["RandSeed1"],
                "turb_seed2": tk["RandSeed2"], "turb_model": tk["TurbModel"],
                "turb_IECstandard": tk["IECstandard"], "turb_IECturbc": tk["IECturbc"],
                "turb_IEC_WindType": tk["IEC_WindType"],
                "turb_grid_z": tk["NumGrid_Z"], "turb_grid_y": tk["NumGrid_Y"],
                "turb_dt_s": tk["TimeStep"], "turb_analysis_s": tk["AnalysisTime"],
                "turb_usable_s": tk["UsableTime"], "turb_hub_m": tk["HubHt"],
                "fst_TMax_s": fk["TMax"], "fst_DT_s": fk["DT"],
                "fst_DT_Out_s": fk["DT_Out"], "fst_CompAero": fk["CompAero"],
                "fst_CompServo": fk["CompServo"], "servo_PCMode": sk["PCMode"],
                "servo_VSContrl": sk["VSContrl"],
                "servo_DLL_FileName": sk["DLL_FileName"],
                "servo_DLL_InFile": sk["DLL_InFile"],
                "inflow_WindType": ik["WindType"],
                "inflow_FileName_BTS": ik["FileName_BTS"] or ik["Filename"],
                "turb_inp_sha256": sha(turb["inp"]), "turb_sum_sha256": sha(turb["sum"]),
                "turb_dat_sha256": sha(turb["dat"]), "inflow_sha256": sha(inflow),
                "fst_sha256": sha(fst), "servo_sha256": sha(servo),
                "discon_sha256": sha(discon), "bts_archive_status": bts["status"],
                "bts_archived_sha256": "", "formal_DLC12_reuse_verdict": "HOLD_NOT_VERIFIED"
            }
            rows.append(row)
        require(len(rows) == 18 and src.read_count == 1 + 18 * 7, "SOURCE_READ_COUNT")
        for group in ("U09p343881", "U11p4", "U19p202140"):
            s = [seeds[c] for c in CASES if c.startswith(group)]
            # Missing or repeated RandSeed1 is a gate warning, never silently a six-seed PASS.
            if all(s) and len(set(s)) != 6:
                missing["duplicate_seed1_" + group] = 1
        out = io.StringIO(newline="")
        writer = csv.DictWriter(out, fieldnames=HEADER, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        data = out.getvalue().encode("utf-8")
        controller_text = discon.decode("utf-8-sig", errors="replace")
        receipt = {
            "stage": "S07_DLC12_HISTORICAL_SOURCE_CONFIGURATION_PREPARATION_ONLY",
            "SOURCE": "18 original archived TurbSim .inp/.sum/.dat, 18 archived FST/ED/ServoDyn/InflowWind, original DISCON.IN, two original SHA-pinned manifests and 18-case identity CSV",
            "source_reading_level": "THIS RUN: original ZIP member bytes read, length and SHA256 verified for 127 members; no original .bts bytes, native controller DLL execution, or 700s OpenFAST rerun",
            "REF": "Existing T062 source identity, 21-bin x 6-seed coverage and 12-stage plan; no new full paper read",
            "STANDARD": "IEC 61400-1/6 2025 authorized DLC1.2 clauses not read; configuration names do not prove IEC compliance",
            "OFFICIAL": "Original archived TurbSim/OpenFAST input text and historical manifest, NOT an official controller certification",
            "RUN": "Python 3 standard-library ZIP/source parser, self-test and SHA gates only; no production solver",
            "FIG": "none",
            "TAB": "18-row per-seed original TurbSim/FST/ServoDyn/InflowWind/DISCON source table",
            "input_sha256": {"static_manifest": STATIC_SHA, "supplement_manifest": SUPPLEMENT_SHA,
                             "18case_identity_csv": IDENTITY_SHA},
            "output_csv_sha256": sha(data),
            "original_members_verified": src.read_count,
            "source_zip_archives_opened": len(src.zips),
            "case_count": len(rows),
            "unique_sha_counts": {k: len({r[k] for r in rows}) for k in
                                  ("fst_sha256", "servo_sha256", "inflow_sha256",
                                   "turb_inp_sha256", "turb_sum_sha256", "turb_dat_sha256")},
            "source_config_by_case": {r["case"]: {
                "turb_URef_mps": r["turb_URef_mps"],
                "turb_seed1": r["turb_seed1"],
                "turb_model": r["turb_model"],
                "turb_IEC_WindType": r["turb_IEC_WindType"],
                "servo_DLL_FileName": r["servo_DLL_FileName"],
                "servo_DLL_InFile": r["servo_DLL_InFile"]} for r in rows},
            "bts_source_status": dict(bts_status),
            "missing_or_ambiguous_input_fields": dict(sorted(missing.items())),
            "discon_source_text_contains_ROSCO_marker": "rosco" in controller_text.lower(),
            "controller_identity_conclusion": "DISCON.IN source name and ServoDyn DLL references only; binary DLL provenance/version and actual controller algorithm unverified; never assert ROSCO from filenames",
            "assumptions": "Original 18 NTM nominal case labels are planning labels; 4-25m/s bins are diagnostic only; no unarchived BTS reconstructed",
            "numerical_error_budget": "Source-byte SHA256 and byte-length are exact checks; extracted values are strings with no interpolation; original wind-field realization, turbulence sampling, controller runtime and IEC/site uncertainty NOT ESTIMATED",
            "HOLD": "All 18 original BTS wind-field bytes lack archive SHA and are not recoverable from .inp/.sum/.dat by assertion; no IEC 2025 clauses or DLC1.2 controller/operating-state native proof; 0/18 formal reuse; no material Miner",
            "formal_dlc12_reuse_approved": 0,
            "physical_pass": False,
            "stages_passed": 0
        }
        return data, receipt
    finally:
        src.close()

def self_test():
    assert parse_key('  "NTM" IEC_WindType - test', 'IEC_WindType') == "NTM"
    assert parse_key('  42 RandSeed1 ! seed', 'RandSeed1') == "42"
    assert parse_key('  0.05 DT_Out ! output', 'DT_Out') == "0.05"
    assert parse_key('  "abc.dll" DLL_FileName', 'DLL_FileName') == "abc.dll"
    assert parse_key('  7 OtherKey', 'RandSeed1') == ""
    for bad in (' 1 RandSeed1\n 2 RandSeed1\n',):
        try:
            parse_key(bad, 'RandSeed1')
        except ValueError:
            pass
        else:
            raise AssertionError("DUPLICATE_KEY_ACCEPTED")
    for bad in ("U20_NTM_S01", "U09p343881_ETM_S01"):
        try:
            nominal(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("BAD_CASE_ACCEPTED")
    try:
        manifest_index(b'[{"section":"x","relative_path":"y"},{"section":"x","relative_path":"y"}]')
    except ValueError:
        pass
    else:
        raise AssertionError("DUPLICATE_MANIFEST_ACCEPTED")
    print("S07_NTM18_CONFIG_SELFTEST_PASS: positive parser and 4 negative rejection classes")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--receipt", type=Path)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--servo-startup-source", type=Path)
    p.add_argument("--servo-startup-receipt", type=Path)
    args = p.parse_args()
    if args.self_test:
        self_test()
        servo_startup_self_test()
        if not args.repo_root and not args.servo_startup_source:
            return
    if args.servo_startup_source:
        require(args.servo_startup_receipt is not None, "SERVO_RECEIPT_PATH_REQUIRED")
        record = inspect_servo_startup(args.servo_startup_source.read_bytes())
        args.servo_startup_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.servo_startup_receipt.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("S07_ORIGINAL_SERVO_SOURCE_PASS_NOT_CUTIN", json.dumps(record["fields"], sort_keys=True))
        return
    require(args.repo_root and args.out and args.receipt, "REQUIRED_ROOT_OUT_RECEIPT")
    data, receipt = build(args.repo_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(data)
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("S07_18NTM_ORIGINAL_INPUT_SOURCE_QC_PASS_NOT_DLC12",
          json.dumps({"cases": receipt["case_count"], "members": receipt["original_members_verified"],
                      "zips": receipt["source_zip_archives_opened"],
                      "unique": receipt["unique_sha_counts"],
                      "bts": receipt["bts_source_status"],
                      "missing": receipt["missing_or_ambiguous_input_fields"],
                      "csv_sha256": receipt["output_csv_sha256"],
                      "formal_reuse": 0}, sort_keys=True))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("S07_NTM18_SOURCE_GATE_FAIL", type(exc).__name__, str(exc), file=sys.stderr)
        raise
