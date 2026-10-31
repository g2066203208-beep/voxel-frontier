#!/usr/bin/env python3
"""S07 source-only operating-state QC of 18 original 158m OpenFAST NTM OUTB.
NO new OpenFAST run, NO controller-DLL provenance, NO IEC DLC1.2 approval.
Python 3.11+ standard library; original OUTB bytes and manifest SHA required.
"""
import argparse
from array import array
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import sys
import zipfile

from s06_historical_outb_source_gate import outb_header
from s06_ntm_18case_original_outb_gate import CASES, entries

CHANNELS = ("RotSpeed", "BldPitch1", "BldPitch2", "BldPitch3",
            "GenPwr", "GenSpeed", "GenTq")
UNITS = {"RotSpeed": "(rpm)", "BldPitch1": "(deg)", "BldPitch2": "(deg)",
         "BldPitch3": "(deg)", "GenPwr": "(kW)", "GenSpeed": "(rpm)"}
PREFIX = ("case", "source_outb_sha256", "source_archive_sha256",
          "n_samples", "first_time_s", "last_time_s", "dt_s",
          "source_channel_count", "power_positive_1kW_fraction",
          "power_negative_below_minus1kW_fraction", "power_nonpositive_fraction",
          "rotor_at_or_below_0p1rpm_fraction", "pitch_abs_at_or_above_80deg_fraction",
          "power_rotor_active_fraction", "active_state_transitions_heuristic",
          "longest_inactive_heuristic_s", "max_interblade_pitch_spread_deg",
          "median_positive_speed_ratio", "threshold_quantization_ambiguous_samples",
          "max_quantization_half_step_in_native_units", "formal_DLC12_reuse")
HEADER = PREFIX + tuple(f"{c}_{stat}" for c in CHANNELS
                        for stat in ("min", "p05", "mean", "p95", "max"))

def sha(data):
    return hashlib.sha256(data).hexdigest()

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def decode(raw, h):
    require(h["file_id"] == 4 and h["num_samples"] == 12001,
            "UNEXPECTED_FILE_ID_OR_SAMPLE_COUNT")
    require(abs(h["first_time_s"] - 100.0) < 1e-7
            and abs(h["time_increment_s"] - .05) < 1e-10,
            "UNEXPECTED_NATIVE_TIME_GRID")
    names, units = h["channel_names"], h["channel_units"]
    require(len(names) == h["num_output_channels"] + 1
            and names[0] == "Time" and len(set(names)) == len(names),
            "DUPLICATE_OR_MISSING_CHANNEL_NAMES")
    require(all(c in names for c in CHANNELS), "MISSING_OPERATING_STATE_CHANNEL")
    for name, expected in UNITS.items():
        require(units[names.index(name)] == expected,
                "UNEXPECTED_CHANNEL_UNIT:" + name)
    packed = array("h")
    packed.frombytes(raw[h["data_offset_bytes"]:])
    if sys.byteorder != "little":
        packed.byteswap()
    n = h["num_output_channels"]
    require(len(packed) == n * 12001, "PACKED_SIZE")
    data, halfsteps = {}, {}
    for name in CHANNELS:
        j = names.index(name) - 1
        scale = h["column_scales"][j]
        offset = h["column_offsets"][j]
        require(math.isfinite(scale) and scale != 0 and math.isfinite(offset),
                "INVALID_SCALE_OR_OFFSET:" + name)
        values = [(v-offset)/scale for v in packed[j::n]]
        require(len(values) == 12001 and all(map(math.isfinite, values)),
                "INVALID_DECODE:" + name)
        data[name] = values
        halfsteps[name] = .5 / abs(scale)
    return data, halfsteps

def percentiles(vals):
    s = sorted(vals)
    n = len(s)
    def p(frac):
        index = (n-1)*frac
        low = int(index)
        upper = min(n-1,low+1)
        return s[low] + (index-low)*(s[upper]-s[low])
    return p(.05), p(.95)

def metrics(data, halfsteps, dt=.05):
    require(set(data) == set(CHANNELS) and set(halfsteps) == set(CHANNELS),
            "INCOMPLETE_CHANNEL_SET")
    n = len(data["RotSpeed"])
    require(n >= 3 and math.isfinite(dt) and dt > 0
            and all(len(x) == n and all(math.isfinite(v) for v in x)
                    for x in data.values()), "INVALID_TIME_SERIES")
    require(all(math.isfinite(v) and v > 0 for v in halfsteps.values()),
            "INVALID_QUANTIZATION")
    p, rot, gen = data["GenPwr"], data["RotSpeed"], data["GenSpeed"]
    pitches = [data["BldPitch1"], data["BldPitch2"], data["BldPitch3"]]
    active = [power > 1 and rpm > .1 for power,rpm in zip(p,rot)]
    lengths, streak = [], 0
    for is_active in active:
        if is_active:
            if streak:
                lengths.append(streak)
            streak = 0
        else:
            streak += 1
    if streak:
        lengths.append(streak)
    ratios = [g/r for g,r in zip(gen,rot) if g > .1 and r > .1]
    ambiguous = sum(abs(power-1) <= halfsteps["GenPwr"]
                    or abs(rpm-.1) <= halfsteps["RotSpeed"]
                    for power,rpm in zip(p,rot))
    row = {
        "power_positive_1kW_fraction": sum(x > 1 for x in p)/n,
        "power_negative_below_minus1kW_fraction": sum(x < -1 for x in p)/n,
        "power_nonpositive_fraction": sum(x <= 0 for x in p)/n,
        "rotor_at_or_below_0p1rpm_fraction": sum(x <= .1 for x in rot)/n,
        "pitch_abs_at_or_above_80deg_fraction": sum(
            max(abs(q[k]) for q in pitches) >= 80 for k in range(n))/n,
        "power_rotor_active_fraction": sum(active)/n,
        "active_state_transitions_heuristic": sum(
            active[k] != active[k-1] for k in range(1,n)),
        "longest_inactive_heuristic_s": max(lengths, default=0)*dt,
        "max_interblade_pitch_spread_deg": max(
            max(q[k] for q in pitches)-min(q[k] for q in pitches)
            for k in range(n)),
        "median_positive_speed_ratio": statistics.median(ratios) if ratios else "",
        "threshold_quantization_ambiguous_samples": ambiguous,
        "max_quantization_half_step_in_native_units": max(halfsteps.values()),
    }
    for name in CHANNELS:
        vals = data[name]
        q05, q95 = percentiles(vals)
        row.update({f"{name}_min": min(vals), f"{name}_p05": q05,
                    f"{name}_mean": math.fsum(vals)/n,
                    f"{name}_p95": q95, f"{name}_max": max(vals)})
    return row

def self_test():
    d = {k:[2.,2.,2.,2.,2.] for k in CHANNELS}
    d["GenPwr"] = [0.,0.,5.,5.,0.]
    d["RotSpeed"] = [0.,0.,5.,5.,0.]
    q = {k: .001 for k in CHANNELS}
    a = metrics(d,q)
    assert abs(a["power_rotor_active_fraction"]-.4) < 1e-14
    assert a["active_state_transitions_heuristic"] == 2
    assert abs(a["longest_inactive_heuristic_s"]-.1) < 1e-14
    assert a["GenPwr_mean"] == 2.
    assert percentiles([0,1,2,3,4]) == (.2,3.8)
    for bad, reason in [
        ({k:v for k,v in d.items() if k!="GenPwr"}, "MISSING"),
        ({**d,"GenPwr":[float("nan")]*5}, "NONFINITE"),
        ({**d,"GenPwr":[1.]}, "LENGTH"),
    ]:
        try:
            metrics(bad,q)
        except ValueError:
            pass
        else:
            raise AssertionError("NEGATIVE_TEST_ACCEPTED:"+reason)
    try:
        metrics(d,{**q,"GenPwr":0})
    except ValueError:
        pass
    else:
        raise AssertionError("ZERO_QUANTIZATION_ACCEPTED")
    print("SELFTEST_PASS_4_NEGATIVE_AND_KNOWN_ANSWER")

def build(args):
    manifest = args.manifest.read_bytes()
    source, manifest_sha = entries(args.manifest)
    config_raw = args.config.read_bytes()
    identity_raw = args.identity.read_bytes()
    config = {r["case"]:r for r in csv.DictReader(io.StringIO(config_raw.decode()))}
    identity = {r["case"]:r for r in csv.DictReader(io.StringIO(identity_raw.decode()))}
    require(set(config)==set(CASES) and set(identity)==set(CASES),
            "CONFIG_IDENTITY_CASE_MISMATCH")
    require(sha(config_raw)=="be58d33306e6ac101d42b42c7f4d24ea5743662d1a9355aff9862b5a7e0aad45",
            "ORIGINAL_CONFIG_SOURCE_CHANGED")
    require(sha(identity_raw)=="d57ff9e71b58b531b1aaa357ad7a57a86daf529e061f9d8996cf2453b04a7da5",
            "ORIGINAL_IDENTITY_SOURCE_CHANGED")
    rows, sources = [], []
    for case in CASES:
        e = source[case]
        archive = args.zip_dir / Path(e["canonical_archive"]).name
        archive_bytes = archive.read_bytes()
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as z:
            raw = z.read(e["relative_path"])
        actual_sha = sha(raw)
        require(len(raw)==int(e["bytes"]) and actual_sha==e["sha256"].lower()
                and actual_sha==identity[case]["outb_sha256"].lower(),
                "OUTB_SOURCE_IDENTITY_MISMATCH:"+case)
        require(config[case]["formal_DLC12_reuse_verdict"]=="HOLD_NOT_VERIFIED",
                "UNEXPECTED_FORMAL_DLC12_APPROVAL")
        h = outb_header(raw)
        data, halfsteps = decode(raw,h)
        row = metrics(data,halfsteps)
        row.update(case=case, source_outb_sha256=actual_sha,
                   source_archive_sha256=sha(archive_bytes),
                   n_samples=h["num_samples"], first_time_s=h["first_time_s"],
                   last_time_s=h["first_time_s"]+(h["num_samples"]-1)*h["time_increment_s"],
                   dt_s=h["time_increment_s"],
                   source_channel_count=h["num_output_channels"],
                   formal_DLC12_reuse="HOLD_NOT_VERIFIED")
        rows.append(row)
        sources.append({"case":case, "archive":str(e["canonical_archive"]),
                        "archive_sha256":sha(archive_bytes),
                        "outb_sha256":actual_sha, "outb_bytes":len(raw),
                        "max_packed_halfstep":max(halfsteps.values()),
                        "channel_units":{c:h["channel_units"][h["channel_names"].index(c)]
                                         for c in CHANNELS}})
        print("ORIGINAL_NTM_OPERATING_STATE_SOURCE_PASS",case,actual_sha, file=sys.stderr)
    require(len(rows)==18,"NOT_18_ROWS")
    out=io.StringIO(newline="")
    writer=csv.DictWriter(out,fieldnames=HEADER,lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k:(format(v,".12g") if isinstance(v,float) else v)
                         for k,v in row.items()})
    b=out.getvalue().encode()
    args.out.write_bytes(b)
    receipt={
        "status":"S07_18_ORIGINAL_NTM_OPERATING_STATE_SOURCE_NUMERIC_QC_NOT_DLC12",
        "SOURCE":"18 original OpenFAST 158m NTM OUTB packed binary files from SHA-pinned archive",
        "source_reading_level":"Original ZIP member bytes SHA256/size, 12001 synchronized packed samples x seven operating channels per case",
        "REF":"T062 18-case source identity and existing S07 original TurbSim/ServoDyn input QC; no new paper fulltext",
        "STANDARD":"No authorized IEC 61400-1/6:2025 DLC1.2 clause inspected; thresholds are diagnostics only",
        "OFFICIAL":"Original OpenFAST binary output channels and archived input source, not certified controller DLL",
        "RUN":"Python3 original OUTB postprocessing in GitHub Actions; no new OpenFAST/Abaqus/TurbSim run",
        "FIG":"none",
        "TAB":"18-row synchronized RotorSpeed/BldPitch1-3/GenPwr/GenSpeed/GenTq operating-state QC CSV",
        "HOLD":"Actual controller DLL version and runtime log, 18 BTS wind-field bytes, formal DLC1.2 configuration and complete operating-state/IEC checks unavailable; diagnostic activity is not shutdown certification",
        "input_sha256":{"manifest":manifest_sha,"config_csv":sha(config_raw),
                        "identity_csv":sha(identity_raw)},
        "script_sha256":sha(Path(__file__).read_bytes()),
        "output_csv_sha256":sha(b),
        "original_outb_verified":len(sources),
        "source_cases":sources,
        "summary":{"active_heuristic_fraction_min":min(r["power_rotor_active_fraction"] for r in rows),
                   "active_heuristic_fraction_max":max(r["power_rotor_active_fraction"] for r in rows),
                   "max_active_transitions":max(r["active_state_transitions_heuristic"] for r in rows),
                   "max_pitch_spread_deg":max(r["max_interblade_pitch_spread_deg"] for r in rows),
                   "total_quantization_ambiguous_samples":sum(r["threshold_quantization_ambiguous_samples"] for r in rows),
                   "formal_dlc12_approved":0},
        "assumptions":{"window_s":[100,700],"dt_s":.05,
                       "active_diagnostic":"GenPwr>1 kW AND RotSpeed>0.1 rpm",
                       "pitch_extreme_diagnostic":"any |BldPitch|>=80 deg",
                       "negative_power_diagnostic":"GenPwr<-1 kW",
                       "no_controller_state_or_stop_label_inferred":True},
        "numerical_error_budget":"Each channel native packed-int16 half-step 0.5/abs(scale) recorded per case; threshold ambiguity counted; 12-significant-digit CSV rounding; no physical or IEC acceptance tolerance",
        "physical_pass":False,"stages_passed":0
    }
    args.receipt.write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("PASS_ORIGINAL_NTM_OPERATING_STATE_18",sha(b),json.dumps(receipt["summary"],sort_keys=True))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--manifest",type=Path)
    ap.add_argument("--config",type=Path)
    ap.add_argument("--identity",type=Path)
    ap.add_argument("--zip-dir",type=Path)
    ap.add_argument("--out",type=Path)
    ap.add_argument("--receipt",type=Path)
    a=ap.parse_args()
    if a.self_test:
        self_test()
    else:
        require(all((a.manifest,a.config,a.identity,a.zip_dir,a.out,a.receipt)),
                "MISSING_INPUT_ARGUMENT")
        build(a)
