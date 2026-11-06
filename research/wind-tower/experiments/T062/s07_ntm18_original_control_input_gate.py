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
        (raw.replace(b"9999.9 TimGenOf", b"9999.9 TimGenOf\n1 TimGenOf"), None, None),
        (raw.replace(b"False GenTiStp\n", b""), None, None)
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


# S06/S10 original DISCON low-wind controller source gate.
# The tagged ROSCO-v2.6.0 source has no automatic wind-speed cut-in
# implication from VS_MinOMSpd or the pitch shutdown switch.
import math
ORIGINAL_DISCON_SHA = "8f5d7546420ee34838e66b63e4b26d64460be5d5492f99c60b6d1ef977ffc61a"
ORIGINAL_DISCON_BYTES = 17600
LOWWIND_DISCON_KEYS = (
    "SD_Mode", "SD_MaxPit", "SD_CornerFreq", "PS_Mode", "PS_BldPitchMin_N",
    "PS_WindSpeeds", "PS_BldPitchMin", "VS_ControlMode", "WE_Mode",
    "VS_MinOMSpd", "VS_RefSpd", "VS_TSRopt", "WE_GearboxRatio",
    "WE_BladeRadius", "VS_MinTq", "PC_MaxRat",
)
DISCON_NUMBER = re.compile(r"[+-]?(?:(?:\d+\.?\d*|\.\d+)(?:[EeDd][+-]?\d+)?)")

def inspect_discon_lowwind(raw, expected_sha=ORIGINAL_DISCON_SHA,
                           expected_bytes=ORIGINAL_DISCON_BYTES):
    require(len(raw) == expected_bytes, "DISCON_LOW_WIND_BYTE_COUNT")
    require(sha(raw) == expected_sha, "DISCON_LOW_WIND_SHA256")
    txt = raw.decode("utf-8-sig", errors="strict")
    entries = {}
    for line_number, line in enumerate(txt.splitlines(), 1):
        if "!" not in line:
            continue
        val, comment = line.split("!", 1)
        match = re.match(r"\s*([A-Za-z][A-Za-z0-9_]*)\b", comment)
        if not match or not val.strip():
            continue
        key = match.group(1)
        if key not in LOWWIND_DISCON_KEYS:
            continue
        require(key not in entries, "DISCON_LOW_WIND_DUPLICATE:" + key)
        tokens = val.replace(",", " ").split()
        require(tokens and all(DISCON_NUMBER.fullmatch(v) for v in tokens),
                "DISCON_LOW_WIND_NONNUMERIC:" + key)
        numbers = [float(v.replace("D", "E").replace("d", "e")) for v in tokens]
        require(all(math.isfinite(v) for v in numbers), "DISCON_LOW_WIND_NONFINITE:" + key)
        entries[key] = {"line": line_number, "raw": val.strip(), "values": numbers}
    required = ("SD_Mode", "PS_Mode", "VS_ControlMode", "WE_Mode",
                "VS_MinOMSpd", "VS_TSRopt", "WE_GearboxRatio")
    require(all(k in entries for k in required), "DISCON_LOW_WIND_MISSING_REQUIRED")
    def scalar(k):
        require(len(entries[k]["values"]) == 1, "DISCON_LOW_WIND_NONSCALAR:" + k)
        return entries[k]["values"][0]
    require(scalar("SD_Mode") in (0, 1), "DISCON_LOW_WIND_SD_MODE")
    require(scalar("PS_Mode") in (0, 1), "DISCON_LOW_WIND_PS_MODE")
    require(scalar("VS_ControlMode") in (0, 1, 2, 3), "DISCON_LOW_WIND_VS_MODE")
    require(scalar("WE_Mode") in (0, 1, 2), "DISCON_LOW_WIND_WE_MODE")
    for key in ("VS_MinOMSpd", "VS_TSRopt", "WE_GearboxRatio"):
        require(scalar(key) > 0, "DISCON_LOW_WIND_NONPOSITIVE:" + key)
    boundary = None
    if "WE_BladeRadius" in entries:
        require(scalar("WE_BladeRadius") > 0, "DISCON_LOW_WIND_RADIUS")
        boundary = (scalar("VS_MinOMSpd") * scalar("WE_BladeRadius") /
                    (scalar("VS_TSRopt") * scalar("WE_GearboxRatio")))
    return {
        "SOURCE": "Original 158m 17600-byte DISCON.IN supplementary ZIP member",
        "READING_LEVEL": "Exact original bytes/SHA and tagged ROSCO-v2.6.0 executable source lines",
        "REF": "T062 existing original DISCON and 18NTM controller source receipts",
        "STANDARD": "IEC 61400-1/6:2025 licensed clauses NOT READ",
        "OFFICIAL": {
            "Controllers.f90": "v2.6.0 lines 92-95: Shutdown called only when SD_Mode=1",
            "ControllerBlocks.f90": "v2.6.0 lines 52-54: TSR generator speed reference clamp; lines 401-416: pitch-triggered shutdown",
            "ReadSetParameters.f90": "v2.6.0 lines 231-245 and 360-363: actual controller flags and shutdown parameters",
        },
        "RUN": "Python original member parsing and negative tests, NO production solver",
        "FIG": "0", "TAB": "original low-wind controller keys and conditional five-bin diagnostic",
        "original_discon_sha256": sha(raw), "original_discon_bytes": len(raw),
        "parameters": entries,
        "original_SD_Mode": scalar("SD_Mode"),
        "original_PS_Mode": scalar("PS_Mode"),
        "original_VS_ControlMode": scalar("VS_ControlMode"),
        "original_WE_Mode": scalar("WE_Mode"),
        "rosco_pitch_shutdown_branch_enabled": scalar("SD_Mode") == 1,
        "conditional_tsr_min_reference_boundary_mps_NOT_CUTIN": boundary,
        "diagnostic_bins": [
            {"center_mps": u, "below_reference_clamp_boundary_IF_WIND_ESTIMATE_EQUALS_CENTER":
             u < boundary if boundary is not None else None}
            for u in (4.5, 5.5, 6.5, 7.5, 8.5)
        ],
        "cut_in_verdict": "NOT_ESTABLISHED_FROM_DISCON_OR_SERVODYN",
        "assumptions": "Conditional TSR reference clamp uses estimated wind equal to bin center; not actual wind-speed cut-in. SD_Mode=0 disables only ROSCO pitch shutdown branch, not other OpenFAST stop/brake logic.",
        "ERROR_BUDGET": "SHA and numeric tokens exact, algebraic floating roundoff negligible; DLL identity, wind estimator bias, turbulence and physical cut-in unknown",
        "HOLD": "4-8m/s original BTS/OUTB, controller DLL identity/runtime state, IEC2025 clauses and S01-S04 physics unverified",
        "physical_pass": False, "stage_passed": 0,
    }

def discon_lowwind_self_test():
    template = ("0 ! SD_Mode - no shutdown\n1 ! PS_Mode\n2 ! VS_ControlMode\n"
                "2 ! WE_Mode\n36.6 ! VS_MinOMSpd\n7.5 ! VS_TSRopt\n"
                "50 ! WE_GearboxRatio\n89.15 ! WE_BladeRadius\n0.9 ! SD_MaxPit\n")
    raw = template.encode()
    good = inspect_discon_lowwind(raw, sha(raw), len(raw))
    assert not good["rosco_pitch_shutdown_branch_enabled"]
    assert abs(good["conditional_tsr_min_reference_boundary_mps_NOT_CUTIN"] -
               36.6 * 89.15 / (7.5 * 50)) < 1e-12
    bad = [
        (raw, "0" * 64, len(raw)),
        (raw, sha(raw), len(raw) + 1),
        (raw.replace(b"0 ! SD_Mode", b"2 ! SD_Mode"), None, None),
        (raw.replace(b"2 ! VS_ControlMode", b"NaN ! VS_ControlMode"), None, None),
        (raw.replace(b"2 ! WE_Mode", b"4 ! WE_Mode"), None, None),
        (raw.replace(b"50 ! WE_GearboxRatio", b"0 ! WE_GearboxRatio"), None, None),
        (raw + b"1 ! SD_Mode\n", None, None),
        (raw.replace(b"0 ! SD_Mode - no shutdown\n", b""), None, None),
        (raw.replace(b"89.15 ! WE_BladeRadius", b"-1 ! WE_BladeRadius"), None, None),
    ]
    for source, digest, length in bad:
        try:
            inspect_discon_lowwind(source, digest if digest is not None else sha(source),
                                   length if length is not None else len(source))
        except ValueError:
            pass
        else:
            raise AssertionError("DISCON_LOW_WIND_BAD_SOURCE_ACCEPTED")
    print("S07_ORIGINAL_DISCON_LOWWIND_SELFTEST_PASS: 1 positive, 9 negative")


# S07: source-only FST module graph and ServoDyn -> DISCON -> DLL identity.
# Reuses the original SHA-pinned manifests and archive Source.get(); no solver.
def module_graph_safe_reference(value):
    from pathlib import PurePosixPath
    value = value.strip().strip('"').strip("'").replace("\\", "/")
    require(value and not value.startswith("/") and not re.match(r"^[A-Za-z]:", value),
            "MODULE_ABSOLUTE_OR_EMPTY_REFERENCE")
    parts = PurePosixPath(value).parts
    require(all(x not in ("..", "") for x in parts), "MODULE_PATH_TRAVERSAL")
    return value

def module_graph_source_lookup(source, member):
    # Preserve original case identity, then the SHA-identical canonical ETM
    # archive alias; never silently select another wind-speed or seed.
    import posixpath
    cases = ("CASES/U09p343881_NTM_S01/", "CASES/U09p343881_ETM_S01/")
    normalized = member.strip().strip('"').strip("'").replace("\\", "/")
    if (not normalized or normalized.startswith("/") or
            re.match(r"^[A-Za-z]:", normalized)):
        return {"status": "UNRESOLVED_EXTERNAL_OR_TRAVERSAL_REFERENCE",
                "reference": member, "reason": "ABSOLUTE_OR_EMPTY"}
    candidates = []
    for case in cases:
        # Historical AeroFile is ../Rotor/..., legitimately resolving to
        # CASES/Rotor from the case FST directory. Bound to CASES/ and
        # never reinterpret this as a path for a future staged candidate.
        alternatives = (normalized,) if ".." in normalized.split("/") else (
            normalized, "Control/" + normalized)
        for rel in alternatives:
            full = posixpath.normpath(case + rel)
            if not full.startswith("CASES/"):
                return {"status": "UNRESOLVED_EXTERNAL_OR_TRAVERSAL_REFERENCE",
                        "reference": member, "reason": "ESCAPES_CASES_ROOT"}
            if full not in candidates:
                candidates.append(full)
    name = normalized
    found = []
    for manifest in ("static", "supplement"):
        idx = source.indexes[manifest]
        for full in candidates:
            row = idx.get(("openfast-36-r2", full))
            if row and row.get("status") in ("included", "duplicate-reference"):
                found.append((manifest, full, row))
    if not found:
        return {"status": "MISSING_ARCHIVED_MEMBER", "reference": member,
                "tried": candidates}
    # The original NTM InflowWind differs from the ETM card even when their
    # filenames match. Resolve the NTM case FIRST; only use the ETM alias
    # when the NTM member is absent (e.g. the deduplicated original FST).
    preferred = [x for x in found if x[1].startswith(cases[0])]
    selected = preferred if preferred else found
    hashes = {r["sha256"].lower() for _, _, r in selected}
    require(len(hashes) == 1, "MODULE_AMBIGUOUS_SAME_CASE_HASHES:" + name)
    manifest, full, row = selected[0]
    raw, verified = source.get(manifest, "openfast-36-r2", full)
    return {"status": "ARCHIVED_SOURCE_SHA_VERIFIED",
            "reference": member, "logical_member": full,
            "canonical_member": verified["canonical_member"],
            "archive": verified["canonical_archive"],
            "sha256": sha(raw), "bytes": len(raw),
            "manifest": manifest, "_raw": raw}

def module_graph_self_test():
    assert module_graph_safe_reference("Control/DISCON.IN") == "Control/DISCON.IN"
    rejected = ("", "/etc/passwd", "../bad.dat", "Control/../bad.dat",
                "C:\\\\Users\\bad.dat", "C:/Users/bad.dat")
    for value in rejected:
        try: module_graph_safe_reference(value)
        except ValueError: pass
        else: raise AssertionError("MODULE_GRAPH_UNSAFE_PATH_ACCEPTED:" + value)
    raw = b'1 CompServo\n"Control/Srv.dat" ServoFile\n'
    assert parse_keys(raw, ("CompServo", "ServoFile"))["ServoFile"] == "Control/Srv.dat"
    try: parse_keys(raw + b'"Other.dat" ServoFile\n', ("ServoFile",))
    except ValueError: pass
    else: raise AssertionError("MODULE_GRAPH_DUPLICATE_KEY_ACCEPTED")
    print("S07_MODULE_GRAPH_SELFTEST_PASS_1_POSITIVE_7_NEGATIVE_NO_SOLVER")

def build_module_graph(repo_root):
    base = repo_root / ROOT
    static = read_pinned(base / "archive/local-assets-20261004/file-manifest.json", STATIC_SHA)
    supp = read_pinned(base / "archive/local-assets-20261004-supplement/file-manifest.json", SUPPLEMENT_SHA)
    source = Source(repo_root, {"static": manifest_index(static),
                                "supplement": manifest_index(supp)})
    try:
        fst, fst_entry = source.get("static", "openfast-36-r2",
                                  "CASES/U09p343881_NTM_S01/DTU_10MW_RWT.fst")
        require(sha(fst) == "5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605",
                "MODULE_GRAPH_ORIGINAL_FST_SHA")
        flag_to_field = (("CompElast", "EDFile"), ("CompInflow", "InflowFile"),
                         ("CompAero", "AeroFile"), ("CompServo", "ServoFile"),
                         ("CompHydro", "HydroFile"), ("CompSub", "SubFile"),
                         ("CompMooring", "MooringFile"), ("CompIce", "IceFile"))
        fst_keys = tuple(k for pair in flag_to_field for k in pair)
        fields = parse_keys(fst, fst_keys)
        graph = []
        for flag, field in flag_to_field:
            active = fields[flag] not in ("", "0", "False", "false")
            ref = fields[field]
            row = {"flag": flag, "flag_value": fields[flag],
                   "file_field": field, "reference": ref, "active": active}
            if active:
                row["source"] = (module_graph_source_lookup(source, ref)
                                 if ref else {"status": "MISSING_FST_FILE_FIELD"})
            else:
                row["source"] = {"status": "INACTIVE_OR_NOT_PRESENT"}
            graph.append(row)
        servo_row = next(x for x in graph if x["file_field"] == "ServoFile")
        servo_source = servo_row["source"]
        require(servo_source.get("sha256") == ORIGINAL_SERVO_SHA,
                "MODULE_GRAPH_ORIGINAL_SERVO_SHA")
        servo_raw = servo_source.pop("_raw")
        servo = parse_keys(servo_raw, ("DLL_FileName", "DLL_InFile",
                                       "PCMode", "VSContrl", "DLL_ProcName"))
        discon = module_graph_source_lookup(source, servo["DLL_InFile"])
        require(discon.get("sha256") ==
                "8f5d7546420ee34838e66b63e4b26d64460be5d5492f99c60b6d1ef977ffc61a",
                "MODULE_GRAPH_ORIGINAL_DISCON_SHA")
        discon.pop("_raw")
        dll = module_graph_source_lookup(source, servo["DLL_FileName"])
        dll.pop("_raw", None)
        # Excluded original DLL cannot be verified from a separate reference DLL.
        for row in graph:
            row["source"].pop("_raw", None)
        verified = sum(x["source"]["status"] == "ARCHIVED_SOURCE_SHA_VERIFIED"
                       for x in graph if x["active"])
        unresolved = [x["file_field"] for x in graph if x["active"] and
                      x["source"]["status"] != "ARCHIVED_SOURCE_SHA_VERIFIED"]
        return {
            "SOURCE": "Original SHA-locked FST, ServoDyn and DISCON archive members; static and supplement manifests",
            "READING_LEVEL": "Original ZIP member bytes re-read for archived sources; original DLL may be excluded; no executable runtime",
            "REF": "Existing T062 18NTM source identity and controller-source audits",
            "STANDARD": "IEC/GB 2025 licensed clauses NOT READ; not DLC1.2 acceptance",
            "OFFICIAL": "Historical OpenFAST v3.3-era input cards; source-level graph only",
            "RUN": "Python3 stdlib original ZIP/manifest SHA and field audit, no solver",
            "FIG": 0, "TAB": "FST active module graph and ServoDyn-DISCON-DLL crosswalk",
            "input_sha256": {"static_manifest": STATIC_SHA,
                             "supplement_manifest": SUPPLEMENT_SHA,
                             "original_fst": sha(fst),
                             "original_servo": sha(servo_raw),
                             "original_discon": discon["sha256"]},
            "original_fst_canonical_member": fst_entry["canonical_member"],
            "fst_modules": graph, "servo_controller_fields": servo,
            "discon_source": discon, "dll_source": dll,
            "active_module_source_verified": verified,
            "unresolved_active_modules": unresolved,
            "assumptions": "Archived original 9.343881m/s S01 module cards are reference only; proposed 4.5m/s staged case not assembled",
            "error_budget": "SHA/bytes exact for archived members; runtime paths, DLL ABI, wind/structural errors NEED_ESTIMATE",
            "HOLD": "New BTS/OUTB absent, DLL binary/runtime identity and controller state not proven, all module runtime paths untested",
            "status": "SOURCE_MODULE_GRAPH_ONLY_NOT_RUN",
            "physical_pass": False, "formal_dlc12_verified_slots": 0,
            "stages_passed": 0
        }
    finally:
        source.close()



# S07 source-only AeroDyn15 downstream blade/airfoil graph.
# The original FST references CASES/Rotor/ (10088 bytes), NOT the
# case-local 9774-byte AeroDyn card. Never conflate these variants.
def aero_references(raw):
    import posixpath
    text = raw.decode("utf-8-sig", errors="strict")
    declared = parse_key(text, "NumAFfiles")
    require(not declared or re.fullmatch(r"[0-9]+", declared),
            "AERO_INVALID_NUM_AFFILES")
    refs = []
    for lineno, line in enumerate(text.splitlines(), 1):
        left = line.split("!", 1)[0].strip()
        if not left:
            continue
        # OpenFAST may use quoted file values or unquoted standalone AF rows.
        match = re.search(r"""(?:"([^"]+\.dat)"|'([^']+\.dat)'|(?<!\S)([^\s"'!]+\.dat))(?=\s|$)""", left, re.I)
        if not match:
            continue
        token = next(v for v in match.groups() if v is not None)
        token = token.replace("\\", "/")
        require(not token.startswith("/") and not re.match(r"^[A-Za-z]:", token),
                "AERO_ABSOLUTE_REFERENCE")
        path = posixpath.normpath(posixpath.join("CASES/Rotor", token))
        require(path.startswith("CASES/Rotor/") and ".." not in path.split("/"),
                "AERO_PATH_ESCAPE")
        role = "airfoil" if "/Airfoils/" in path else "blade"
        refs.append({"line": lineno, "reference": token, "resolved": path, "role": role})
    # Three blade slots may legitimately reference the same blade geometry;
    # repeated airfoil table entries remain a source-identity ambiguity.
    airfoil_paths = [r["resolved"] for r in refs if r["role"] == "airfoil"]
    require(len(airfoil_paths) == len(set(airfoil_paths)),
            "AERO_DUPLICATE_AIRFOIL_REFERENCE")
    require(any(r["role"] == "blade" for r in refs), "AERO_BLADE_REFERENCE_MISSING")
    require(any(r["role"] == "airfoil" for r in refs), "AERO_AIRFOIL_REFERENCE_MISSING")
    if declared:
        require(sum(r["role"] == "airfoil" for r in refs) == int(declared),
                "AERO_AIRFOIL_DECLARED_COUNT_MISMATCH")
    return refs, int(declared) if declared else None

def aero_portable_case_patch(original, verified_references):
    """Fix only a verified unique case-only filename mismatch; no solver claims."""
    aliases = [x for x in verified_references if not x["case_sensitive_path_match"]]
    require(len(aliases) == 1, "AERO_PORTABLE_ALIAS_NOT_UNIQUE")
    item = aliases[0]
    original_token = item["reference"].encode("ascii")
    canonical = item["manifest_path"].split("CASES/Rotor/", 1)
    require(len(canonical) == 2, "AERO_PORTABLE_MANIFEST_OUTSIDE_ROTOR")
    canonical_token = canonical[1].encode("ascii")
    require(original_token != canonical_token and
            original_token.lower() == canonical_token.lower() and
            len(original_token) == len(canonical_token),
            "AERO_PORTABLE_NOT_CASE_ONLY")
    require(original.count(original_token) == 1,
            "AERO_PORTABLE_ORIGINAL_TOKEN_NOT_UNIQUE")
    refs_before, declared_before = aero_references(original)
    require(any(x["line"] == item["line"] and
                x["reference"] == item["reference"] for x in refs_before),
            "AERO_PORTABLE_REFERENCE_LINE_MISMATCH")
    candidate = original.replace(original_token, canonical_token, 1)
    require(len(candidate) == len(original), "AERO_PORTABLE_LENGTH_CHANGED")
    require(candidate.replace(canonical_token, original_token, 1) == original,
            "AERO_PORTABLE_NOT_REVERSIBLE")
    refs_after, declared_after = aero_references(candidate)
    require(declared_after == declared_before and len(refs_after) == len(refs_before),
            "AERO_PORTABLE_REFERENCE_COUNT_CHANGED")
    differences = [(a, b) for a, b in zip(refs_before, refs_after) if a != b]
    require(len(differences) == 1 and differences[0][0]["line"] == item["line"] and
            differences[0][1]["reference"] == canonical_token.decode("ascii"),
            "AERO_PORTABLE_UNEXPECTED_REFERENCE_CHANGE")
    byte_diffs = [i for i, (a, b) in enumerate(zip(original, candidate)) if a != b]
    require(len(byte_diffs) == 1, "AERO_PORTABLE_EXPECTED_ONE_BYTE_DIFF")
    # Every candidate reference must now be an exact, case-sensitive original
    # archive path; this is still not an executable runtime path test.
    verified_paths = {x["manifest_path"] for x in verified_references}
    require(all(x["resolved"] in verified_paths for x in refs_after),
            "AERO_PORTABLE_REMAINING_UNRESOLVED_PATH")
    return candidate, {
        "original_sha256": sha(original),
        "candidate_sha256": sha(candidate),
        "original_bytes": len(original),
        "candidate_bytes": len(candidate),
        "changed_reference_line": item["line"],
        "from": original_token.decode("ascii"),
        "to": canonical_token.decode("ascii"),
        "changed_byte_offset_zero_based": byte_diffs[0],
        "changed_byte_old_hex": format(original[byte_diffs[0]], "02x"),
        "changed_byte_new_hex": format(candidate[byte_diffs[0]], "02x"),
        "exact_reverse": True,
        "all_references_case_sensitive": True,
        "changed_reference_count": 1,
        "physical_pass": False,
        "status": "SOURCE_ONLY_PORTABLE_CANDIDATE_NOT_RUN",
    }


def aero_dependency_self_test():
    good = (b'1 NumAFfiles\n"DTU_10MW_AeroDyn15_blade.dat" ADBlFile(1)\n'
            b'"Airfoils/Cylinder_Aerodyn15.dat"\n')
    refs, declared = aero_references(good)
    assert declared == 1 and len(refs) == 2
    bad = [
        good.replace(b'1 NumAFfiles', b'2 NumAFfiles'),
        good.replace(b'Airfoils/Cylinder_Aerodyn15.dat', b'../outside.dat'),
        good.replace(b'Airfoils/Cylinder_Aerodyn15.dat', b'/tmp/outside.dat'),
        good.replace(b'Airfoils/Cylinder_Aerodyn15.dat', b'C:/outside.dat'),
        good.replace(b'1 NumAFfiles', b'bad NumAFfiles'),
        good + b'"Airfoils/Cylinder_Aerodyn15.dat"\n',
        good.replace(b'DTU_10MW_AeroDyn15_blade.dat', b'not_a_blade.txt'),
        good.replace(b'Airfoils/Cylinder_Aerodyn15.dat', b'not_an_airfoil.txt'),
    ]
    for raw in bad:
        try:
            aero_references(raw)
        except ValueError:
            pass
        else:
            raise AssertionError("AERO_BAD_REFERENCE_ACCEPTED")
    source = good.replace(b"Cylinder_Aerodyn15", b"Cylinder_AeroDyn15")
    verified = [
        {"line": 2, "reference": "DTU_10MW_AeroDyn15_blade.dat",
         "manifest_path": "CASES/Rotor/DTU_10MW_AeroDyn15_blade.dat",
         "case_sensitive_path_match": True},
        {"line": 3, "reference": "Airfoils/Cylinder_AeroDyn15.dat",
         "manifest_path": "CASES/Rotor/Airfoils/Cylinder_Aerodyn15.dat",
         "case_sensitive_path_match": False},
    ]
    patched, proof = aero_portable_case_patch(source, verified)
    assert patched == good and proof["exact_reverse"]
    assert proof["changed_reference_count"] == 1
    for bad_source, bad_refs in [
        (good, verified),
        (source + b'\\n"Airfoils/Cylinder_AeroDyn15.dat"\\n', verified),
        (source, verified + [verified[1]]),
        (source, [{**verified[0], "case_sensitive_path_match": False}, verified[1]]),
        (source, [{**verified[1], "manifest_path": "CASES/Rotor/../outside.dat"},
                  verified[0]]),
        (source, [{**verified[1], "manifest_path": "CASES/Rotor/Airfoils/OTHER.dat"},
                  verified[0]]),
    ]:
        try:
            aero_portable_case_patch(bad_source, bad_refs)
        except ValueError:
            pass
        else:
            raise AssertionError("AERO_PORTABLE_BAD_PATCH_ACCEPTED")
    print("S07_AERODYN_DEPENDENCY_SELFTEST_PASS_1_POSITIVE_8_NEGATIVE; PORTABLE_PATCH_1_POSITIVE_6_NEGATIVE_NO_SOLVER")

def build_aero_dependency(repo_root, candidate_out=None):
    base = repo_root / ROOT
    static = read_pinned(base / "archive/local-assets-20261004/file-manifest.json", STATIC_SHA)
    supp = read_pinned(base / "archive/local-assets-20261004-supplement/file-manifest.json", SUPPLEMENT_SHA)
    source = Source(repo_root, {"static": manifest_index(static),
                                "supplement": manifest_index(supp)})
    try:
        shared = "CASES/Rotor/DTU_10MW_RWT_AeroDyn15.dat"
        case_local = "CASES/U09p343881_NTM_S01/Rotor/DTU_10MW_RWT_AeroDyn15.dat"
        card, card_meta = source.get("static", "openfast-36-r2", shared)
        other, other_meta = source.get("static", "openfast-36-r2", case_local)
        require(sha(card) == "e258d2e8fc7664b93f3e6a792c46ec38bea327859f95c3b200391e9f2bb1a568",
                "AERO_SHARED_FST_REFERENCED_CARD_SHA")
        require(sha(other) == "7ebaa0bdf25076041a98ee25ae0577f2d02be61569092965e47be5f875bbcc6d",
                "AERO_CASE_LOCAL_CARD_SHA")
        require(sha(card) != sha(other), "AERO_DISTINCT_VARIANTS_COLLAPSED")
        refs, declared = aero_references(card)
        checked = []
        for item in refs:
            # Historical Windows-origin cards can differ from archived paths
            # only by letter case. Verify unique alias against SHA-pinned
            # manifest, but NEVER call that a portable runtime path PASS.
            key = ("openfast-36-r2", item["resolved"])
            if key in source.indexes["static"]:
                manifest_path = item["resolved"]
            else:
                aliases = [member for (section, member) in source.indexes["static"]
                           if section == "openfast-36-r2"
                           and member.casefold() == item["resolved"].casefold()]
                require(len(aliases) == 1,
                        "AERO_MISSING_OR_AMBIGUOUS_CASE_ALIAS:" + item["resolved"])
                manifest_path = aliases[0]
            raw, entry = source.get("static", "openfast-36-r2", manifest_path)
            checked.append(dict(item, sha256=sha(raw), bytes=len(raw),
                                manifest_path=manifest_path,
                                case_sensitive_path_match=(manifest_path == item["resolved"]),
                                canonical_member=entry["canonical_member"],
                                archive=entry["canonical_archive"]))
        candidate, portable_proof = aero_portable_case_patch(card, checked)
        if candidate_out is not None:
            candidate_out.parent.mkdir(parents=True, exist_ok=True)
            candidate_out.write_bytes(candidate)
            require(candidate_out.read_bytes() == candidate, "AERO_PORTABLE_WRITE_READBACK")
        portable_proof["candidate_repository_path"] = (
            str(candidate_out) if candidate_out is not None else "NOT_WRITTEN")
        portable_proof["source_original_shared_card_sha256"] = sha(card)
        portable_proof["case_local_alternative_sha256"] = sha(other)
        portable_proof["original_archive_member"] = card_meta["canonical_member"]
        return {
            "portable_candidate": portable_proof,
            "SOURCE": "Original FST-selected shared CASES/Rotor AeroDyn15 card, downstream blade/airfoil original ZIP members, SHA-pinned manifest",
            "READING_LEVEL": "Exact archived ZIP member bytes and per-file SHA256, not inferred from filenames alone",
            "REF": "T062 original module graph; 12-stage S07 input identity gate",
            "STANDARD": "IEC 61400-1/6:2025 licensed clauses not read; NOT formal DLC1.2",
            "OFFICIAL": "Original historical OpenFAST AeroDyn15 input syntax; source-only, no executable validation",
            "RUN": "Python3 standard-library source parser, negative tests and original SHA checks; no solver",
            "FIG": 0, "TAB": "FST-selected AeroDyn15 card, blade and airfoil dependencies",
            "input_sha256": {"static_manifest": STATIC_SHA, "supplement_manifest": SUPPLEMENT_SHA,
                             "shared_aerodyn_card": sha(card), "case_local_alternative": sha(other)},
            "fst_selected_shared_aerodyn": {"path": shared, "sha256": sha(card),
                                             "bytes": len(card), "canonical_member": card_meta["canonical_member"]},
            "noninterchangeable_case_local_aerodyn": {"path": case_local,
                "sha256": sha(other), "bytes": len(other),
                "canonical_member": other_meta["canonical_member"]},
            "declared_NumAFfiles": declared, "references": checked,
            "case_only_manifest_alias_count": sum(not x["case_sensitive_path_match"] for x in checked),
            "runtime_portability": "HOLD_ON_CASE_SENSITIVE_HOST_IF_ANY_CASE_ALIAS; source SHA checks do not fix original paths",
            "source_members_verified": source.read_count,
            "assumptions": "The original FST ..\\\\Rotor reference resolves to shared CASES/Rotor; candidate staging paths remain NOT_RUN",
            "error_budget": "Source bytes, hashes, counts and lexical relative paths exact; runtime file resolution, aero loads, controller DLL and physical errors NOT ESTIMATED",
            "HOLD": "Original AeroDyn card case-sensitive path aliases (if any) require portable staging; new BTS/OUTB and original DLL absent; native OpenFAST not tested",
            "status": "AERODYN_DEPENDENCY_SOURCE_ONLY_NOT_RUN",
            "physical_pass": False, "formal_dlc12_verified_slots": 0, "stages_passed": 0
        }
    finally:
        source.close()


# S07 portable source package (source-only; no binary packaging or solver).
def s07_portable_resolve(parent, token):
    import posixpath
    require(isinstance(token, str) and token and "\\x00" not in token,
            "S07_PORTABLE_EMPTY_OR_NUL")
    normalized = token.strip().strip('"').strip("'").replace("\\\\", "/").replace("\\", "/")
    require(normalized and not normalized.startswith("/") and
            not re.match(r"^[A-Za-z]:", normalized),
            "S07_PORTABLE_ABSOLUTE")
    result = posixpath.normpath(posixpath.join(parent, normalized))
    require(result.startswith("CASES/") and
            result != "CASES" and not result.startswith("CASES/../"),
            "S07_PORTABLE_ESCAPE")
    return result


def s07_portable_package_self_test():
    case = "CASES/U04p5_NTM_S01"
    assert s07_portable_resolve(case, "Control\\\\DTU_10MW_RWT_ServoDyn.dat") == case + "/Control/DTU_10MW_RWT_ServoDyn.dat"
    assert s07_portable_resolve(case, "..\\\\Rotor\\\\DTU_10MW_RWT_AeroDyn15.dat") == "CASES/Rotor/DTU_10MW_RWT_AeroDyn15.dat"
    assert s07_portable_resolve(case, "inputs/U04p5_NTM_S01.bts") == case + "/inputs/U04p5_NTM_S01.bts"
    rejected = ("", "/tmp/evil", "C:\\\\evil.dat", "../../../evil", "../..", "\\x00", "/etc/passwd")
    for token in rejected:
        try:
            s07_portable_resolve(case, token)
        except ValueError:
            pass
        else:
            raise AssertionError("S07_PORTABLE_BAD_PATH_ACCEPTED:" + repr(token))
    print("S07_PORTABLE_LAYOUT_SELFTEST_PASS_3_POSITIVE_7_NEGATIVE_NOT_RUN")


def build_s07_portable_package(repo_root):
    """Stage plan, not a runnable package. Re-read exact archive members and
    both committed candidates; unresolved runtime/binary paths remain HOLD."""
    base = repo_root / ROOT
    static = read_pinned(base / "archive/local-assets-20261004/file-manifest.json", STATIC_SHA)
    supp = read_pinned(base / "archive/local-assets-20261004-supplement/file-manifest.json", SUPPLEMENT_SHA)
    source = Source(repo_root, {"static": manifest_index(static),
                                "supplement": manifest_index(supp)})
    case = "CASES/U04p5_NTM_S01"
    old = "CASES/U09p343881_NTM_S01"
    rows = []
    def add(dest, raw, origin, role, status="ARCHIVED_SOURCE_SHA_VERIFIED"):
        require(dest.startswith("CASES/") and dest not in {r["staged_path"] for r in rows},
                "S07_PORTABLE_DUPLICATE_OR_UNSAFE_DEST:" + dest)
        rows.append({"staged_path": dest, "role": role, "status": status,
                     "source": origin, "sha256": sha(raw), "bytes": len(raw)})
    def from_archive(dest, original, role, manifest="static"):
        raw, record = source.get(manifest, "openfast-36-r2", original)
        add(dest, raw, {"archive": record["canonical_archive"],
                        "member": record["canonical_member"],
                        "logical": original}, role)
        return raw
    try:
        fst = from_archive(case + "/DTU_10MW_RWT.fst",
                           old + "/DTU_10MW_RWT.fst", "FST_original_unchanged")
        require(sha(fst) == "5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605",
                "S07_PORTABLE_FST_SHA")
        keys = ("CompElast", "EDFile", "CompInflow", "InflowFile",
                "CompAero", "AeroFile", "CompServo", "ServoFile")
        fields = parse_keys(fst, keys)
        require([fields[k] for k in ("CompElast", "CompInflow", "CompAero", "CompServo")] == ["1", "1", "2", "1"],
                "S07_PORTABLE_ACTIVE_MODULE_FLAGS")
        dest = {key: s07_portable_resolve(case, fields[key])
                for key in ("EDFile", "InflowFile", "AeroFile", "ServoFile")}
        ed = from_archive(dest["EDFile"], old + "/" + fields["EDFile"].replace("\\", "/"),
                          "ElastoDyn_original")
        inflow_path = base / "experiments/T062/S07_U04p5_NTM_S01_InflowWind_NOT_RUN.dat"
        inflow = read_pinned(inflow_path, "2ee0f78812f675448967a4bbf6d536310d995f5c219a45cf8e4cc488d675ad55")
        add(dest["InflowFile"], inflow, {"repository_file": str(inflow_path.relative_to(repo_root))},
            "InflowWind_candidate", "SOURCE_ONLY_CANDIDATE_NOT_RUN")
        aero_path = base / "experiments/T062/S07_SHARED_AERODYN15_PORTABLE_NOT_RUN.dat"
        aero = read_pinned(aero_path, "a2e50140ee04759e9034fc1a51977d7f16c09e25f7c42559dc03ac92d2b2e10f")
        add(dest["AeroFile"], aero, {"repository_file": str(aero_path.relative_to(repo_root))},
            "AeroDyn15_portable_candidate", "SOURCE_ONLY_CANDIDATE_NOT_RUN")
        servo = from_archive(dest["ServoFile"],
                             old + "/" + fields["ServoFile"].replace("\\", "/"),
                             "ServoDyn_original")
        control_dir = case + "/Control"
        sf = parse_keys(servo, ("DLL_FileName", "DLL_InFile", "DLL_ProcName",
                                "PCMode", "VSContrl"))
        require(sf["PCMode"] == sf["VSContrl"] == "5" and sf["DLL_ProcName"] == "DISCON",
                "S07_PORTABLE_SERVO_CONTROLLER_ID")
        discon_dest = s07_portable_resolve(control_dir, sf["DLL_InFile"])
        discon = from_archive(discon_dest,
                              old + "/Control/" + sf["DLL_InFile"].replace("\\", "/"),
                              "DISCON_original", "supplement")
        require(sha(discon) == "8f5d7546420ee34838e66b63e4b26d64460be5d5492f99c60b6d1ef977ffc61a",
                "S07_PORTABLE_DISCON_SHA")
        # Controller may reference an external Cp/Ct/Cq performance table.
        # Read only active value text before '!' comments; do not invent files.
        discon_refs = []
        for line in discon.decode("utf-8-sig", errors="strict").splitlines():
            active = line.split("!", 1)[0]
            for token in re.findall(r'[A-Za-z0-9_./\\-]+\.(?:txt|dat|csv)\b', active, re.I):
                staged = s07_portable_resolve(control_dir, token)
                if staged not in {r["staged_path"] for r in rows}:
                    original = staged.replace(case + "/", old + "/", 1)
                    from_archive(staged, original, "DISCON_external_table")
                discon_refs.append({"token": token, "staged_path": staged})
        # ElastoDyn references are an independent downstream dependency.
        ed_refs = parse_keys(ed, ("TwrFile", "BldFile(1)", "BldFile(2)", "BldFile(3)"))
        require(ed_refs["TwrFile"] and ed_refs["BldFile(1)"],
                "S07_PORTABLE_ED_DOWNSTREAM_MISSING")
        for key in ("TwrFile", "BldFile(1)", "BldFile(2)", "BldFile(3)"):
            token = ed_refs[key] or ed_refs["BldFile(1)"]
            resolved = s07_portable_resolve(case, token)
            if resolved in {r["staged_path"] for r in rows}:
                continue
            original = resolved.replace(case + "/", old + "/", 1) if resolved.startswith(case + "/") else resolved
            from_archive(resolved, original, "ElastoDyn_" + key)
        aero_refs, n_airfoil = aero_references(aero)
        require(n_airfoil == 6 and len(aero_refs) == 9,
                "S07_PORTABLE_AERO_REFERENCE_COUNT")
        for item in aero_refs:
            resolved = item["resolved"]
            if resolved not in {r["staged_path"] for r in rows}:
                from_archive(resolved, resolved, "AeroDyn_" + item["role"])
        bts = s07_portable_resolve(case, parse_keys(inflow, ("FileName_BTS",))["FileName_BTS"])
        require(bts == case + "/inputs/U04p5_NTM_S01.bts",
                "S07_PORTABLE_BTS_LAYOUT")
        dll = s07_portable_resolve(control_dir, sf["DLL_FileName"])
        missing = [
            {"staged_path": bts, "role": "new_TurbSim_BTS", "status": "NOT_GENERATED", "sha256": None},
            {"staged_path": dll, "role": "historical_controller_binary", "status": "NOT_ARCHIVED", "sha256": None},
        ]
        return {
            "SOURCE": "Original historical FST/ElastoDyn/ServoDyn/DISCON and rotor archive members; committed exact-byte candidate cards",
            "READING_LEVEL": "Direct SHA-checked original ZIP members and committed candidate bytes, no executable test",
            "REF": "Existing T062 S07 module, AeroDyn and InflowWind source gates",
            "STANDARD": "IEC 61400-1/6 2025 licensed clauses NOT READ; not DLC1.2 acceptance",
            "OFFICIAL": "Original OpenFAST input syntax, not certified runtime behavior",
            "RUN": "Python3 stdlib SHA/source and lexical path checks, 3 positive/7 negative; no OpenFAST/TurbSim/Abaqus solver",
            "FIG": 0, "TAB": "staged source file and missing dependency rows",
            "input_sha256": {"static_manifest": STATIC_SHA, "supplement_manifest": SUPPLEMENT_SHA,
                             "original_fst": sha(fst), "original_elastodyn": sha(ed),
                             "original_servo": sha(servo), "original_discon": sha(discon),
                             "candidate_inflow": sha(inflow), "candidate_aerodyn": sha(aero)},
            "staged_case": case, "files": rows, "missing_files": missing,
            "elastodyn_references": ed_refs, "discon_external_references": discon_refs, "fst_references": fields,
            "controller_references": sf, "aero_unique_references": sorted({x["resolved"] for x in aero_refs}),
            "assumptions": "FST is unchanged from original 9.343881 m/s case; module/ElastoDyn paths resolved lexically with proposed CASES sibling Rotor; no runtime path semantics proven",
            "error_budget": "Archive/candidate bytes and SHA exact; lexical path exact for declared layout; DLL ABI, BTS data, runtime, aerodynamic/structural error NEED_ESTIMATE",
            "HOLD": "Controller binary not archived, new BTS/OUTB absent, controller operational state and IEC2025/DLC1.2 unverified",
            "status": "SOURCE_ONLY_STATIC_PACKAGE_MANIFEST_NOT_RUN",
            "physical_pass": False, "formal_dlc12_verified_slots": 0, "stages_passed": 0
        }
    finally:
        source.close()




# Reuse the existing T077 S07 A-case PE/ABI source gate; never duplicate its parser.
def s07_reference_abi_crosswalk_records(abi, assembly, pilot):
    refsha = '7aebb0d2166c0cc095d11c2b7bc13da136547c557b0f331dcdce84fe181802aa'
    require(abi['SOURCE']['dll_sha256'] == refsha, 'CROSSWALK_ABI_SHA_MISMATCH')
    pe = abi['TAB']['dll_pe']
    require(pe['machine'] == 'AMD64' and pe['optional_header'] == 'PE32+' and
            pe['discon_export'] is True and 'DISCON' in pe['discon_case_variants'],
            'CROSSWALK_PE_EXPORT_NOT_VERIFIED')
    dll = assembly['TAB']['files']['CASES/U11p4_ETM_S04/Control/libdiscon.dll']
    require(dll['sha256'] == refsha and dll['bytes'] == 1122431, 'CROSSWALK_ASSEMBLY_DLL_MISMATCH')
    gate = pilot['dll_identity_source_gate']
    require(gate['reference_sha256'] == refsha and gate['historical_runtime_equivalence_verified'] is False,
            'CROSSWALK_HISTORICAL_IDENTITY_UNPROVEN')
    package = pilot['lowwind_45_s01_portable_package_20261106']
    missing = package['missing_files']
    require(len(missing) == 2 and any('libdiscon.dll' in str(x) for x in missing) and
            any('.bts' in str(x).lower() for x in missing), 'CROSSWALK_MISSING_INPUTS_NOT_RETAINED')
    return {
        'SOURCE':'T077 existing original A-case ABI/assembly receipts and T062 existing 4.5 S01 source receipt',
        'READING_LEVEL':'prior real-byte PE source gate (T077) + direct receipt crosswalk; no historical DLL bytes',
        'REF':'T077/recovery/s07_a_native_binary_abi_gate.py and S07_A_NATIVE_BINARY_ABI_RECEIPT.json',
        'STANDARD':'IEC/GB2025 authorized clauses NOT READ',
        'OFFICIAL':'Windows PE export/architecture source evidence, not controller runtime certification',
        'RUN':'Python3 stdlib JSON crosswalk and negative tests; no solver',
        'FIG':0,'TAB':'one SHA-locked reference DLL across T077 and T062; two unresolved runtime files',
        'reference_dll_sha256':refsha,'reference_pe':pe,
        'reference_dll_bytes':1122431,'historical_dll_bytes_verified':0,
        'historical_runtime_equivalence_verified':False,'abi_runtime_verified':False,
        'candidate_case':'U04p5_NTM_S01','candidate_dll_status':'REFERENCE_AVAILABLE_NOT_HISTORICAL',
        'ERROR_BUDGET':'receipt fields and SHA exact; runtime ABI/controller equivalence/physical response NEED_ESTIMATE',
        'HOLD':'original 36-case DLL excluded from archived ZIP; new 4.5 S01 BTS absent',
        'status':'EXISTING_T077_REFERENCE_ABI_REUSED_NOT_RUN','physical_pass':False,
        'formal_dlc12_verified_slots':0,'stages_passed':0
    }

def s07_reference_abi_crosswalk_self_test(abi, assembly, pilot):
    import copy
    s07_reference_abi_crosswalk_records(abi, assembly, pilot)
    mutations = [
        (abi, 'SOURCE', 'dll_sha256', '0'*64),
        (abi, 'TAB', 'dll_pe', dict(abi['TAB']['dll_pe'], discon_export=False)),
        (assembly, 'TAB', 'files', {}),
        (pilot, 'dll_identity_source_gate', 'historical_runtime_equivalence_verified', True),
        (pilot, 'lowwind_45_s01_portable_package_20261106', 'missing_files', [])
    ]
    for i,(obj,key,field,value) in enumerate(mutations):
        aa,bb,cc=copy.deepcopy(abi),copy.deepcopy(assembly),copy.deepcopy(pilot)
        target={id(abi):aa,id(assembly):bb,id(pilot):cc}[id(obj)]
        target[key][field]=value
        try: s07_reference_abi_crosswalk_records(aa,bb,cc)
        except (ValueError, KeyError, TypeError, AssertionError): pass
        else: raise AssertionError('S07_CROSSWALK_BAD_INPUT_ACCEPTED_'+str(i))
    print('S07_REFERENCE_ABI_CROSSWALK_SELFTEST_PASS_1_POSITIVE_5_NEGATIVE')

def build_s07_reference_abi_crosswalk(repo_root):
    base = repo_root / ROOT
    d = base / 'experiments/T077/recovery/S07_U11p4_ETM_S04_A'
    abi = json.loads((d/'S07_A_NATIVE_BINARY_ABI_RECEIPT.json').read_text(encoding='utf-8'))
    assembly = json.loads((d/'S07_A_ASSEMBLY_RECEIPT.json').read_text(encoding='utf-8'))
    pilot = json.loads((base/'experiments/T062/S10_U07p5_NTM_S01_SOURCE_PILOT_RECEIPT_20261105.json').read_text(encoding='utf-8'))
    s07_reference_abi_crosswalk_self_test(abi, assembly, pilot)
    return s07_reference_abi_crosswalk_records(abi, assembly, pilot)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--receipt", type=Path)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--servo-startup-source", type=Path)
    p.add_argument("--servo-startup-receipt", type=Path)
    p.add_argument("--discon-lowwind-source", type=Path)
    p.add_argument("--discon-lowwind-receipt", type=Path)
    p.add_argument("--module-graph-receipt", type=Path)
    p.add_argument("--aero-dependency-receipt", type=Path)
    p.add_argument("--aero-portable-candidate", type=Path)
    p.add_argument("--portable-package-receipt", type=Path)
    p.add_argument("--reference-abi-crosswalk-receipt", type=Path)
    args = p.parse_args()
    if args.self_test:
        self_test()
        servo_startup_self_test()
        discon_lowwind_self_test()
        module_graph_self_test()
        aero_dependency_self_test()
        s07_portable_package_self_test()
        if not args.repo_root and not args.servo_startup_source and not args.discon_lowwind_source:
            return
    if args.reference_abi_crosswalk_receipt:
        record = build_s07_reference_abi_crosswalk(args.repo_root or Path('.'))
        args.reference_abi_crosswalk_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.reference_abi_crosswalk_receipt.write_text(json.dumps(record, indent=2, ensure_ascii=False)+'\\n', encoding='utf-8')
        print('S07_REFERENCE_ABI_CROSSWALK_SOURCE_ONLY_NOT_HISTORICAL',json.dumps({'reference_sha256':record['reference_dll_sha256'],'historical_dll_bytes_verified':0,'missing':2},sort_keys=True))
        return
    if args.portable_package_receipt:
        record = build_s07_portable_package(args.repo_root or Path('.'))
        args.portable_package_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.portable_package_receipt.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print('S07_PORTABLE_PACKAGE_SOURCE_ONLY', json.dumps({'source_files': len(record['files']), 'missing': len(record['missing_files']), 'status': record['status']}, sort_keys=True))
        return
    if args.aero_dependency_receipt:
        record = build_aero_dependency(args.repo_root or Path("."), args.aero_portable_candidate)
        args.aero_dependency_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.aero_dependency_receipt.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("S07_AERODYN_SOURCE_ONLY", json.dumps({"references": len(record["references"]), "verified": record["source_members_verified"], "declared_NumAFfiles": record["declared_NumAFfiles"], "portable_candidate_sha256": record["portable_candidate"]["candidate_sha256"], "portable_candidate_status": record["portable_candidate"]["status"]}, sort_keys=True))
        return
    if args.module_graph_receipt:
        record = build_module_graph(args.repo_root or Path('.'))
        args.module_graph_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.module_graph_receipt.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print('S07_MODULE_GRAPH_SOURCE_ONLY', json.dumps({'verified':record['active_module_source_verified'], 'unresolved':record['unresolved_active_modules'], 'dll':record['dll_source']['status']}, sort_keys=True))
        return
    if args.servo_startup_source:
        require(args.servo_startup_receipt is not None, "SERVO_RECEIPT_PATH_REQUIRED")
        record = inspect_servo_startup(args.servo_startup_source.read_bytes())
        args.servo_startup_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.servo_startup_receipt.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("S07_ORIGINAL_SERVO_SOURCE_PASS_NOT_CUTIN", json.dumps(record["fields"], sort_keys=True))
        return
    if args.discon_lowwind_source:
        require(args.discon_lowwind_receipt is not None, "DISCON_LOWWIND_RECEIPT_REQUIRED")
        record = inspect_discon_lowwind(args.discon_lowwind_source.read_bytes())
        args.discon_lowwind_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.discon_lowwind_receipt.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("S07_ORIGINAL_DISCON_LOWWIND_SOURCE_QC_PASS_NOT_CUTIN",
              json.dumps({"SD_Mode": record["original_SD_Mode"],
                          "PS_Mode": record["original_PS_Mode"],
                          "VS_ControlMode": record["original_VS_ControlMode"],
                          "WE_Mode": record["original_WE_Mode"],
                          "tsr_reference_clamp_mps_NOT_CUTIN": record["conditional_tsr_min_reference_boundary_mps_NOT_CUTIN"],
                          "diagnostic_bins": record["diagnostic_bins"]}, sort_keys=True))
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
