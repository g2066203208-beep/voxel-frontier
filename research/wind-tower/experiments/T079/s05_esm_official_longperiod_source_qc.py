#!/usr/bin/env python3
"""S05: read *official* ESM v3 processing and SNR for IT-2012-0008/IT.NVL.
Source metadata audit ONLY. No spectrum matching, design wave or Abaqus PASS.
Usage: python s05_esm_official_longperiod_source_qc.py --outdir output
       python s05_esm_official_longperiod_source_qc.py --self-test
"""
import argparse
import datetime
import hashlib
import json
import math
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://esm-db.eu/esmws"
EVENT, NETWORK, STATION = "IT-2012-0008", "IT", "NVL"
F1 = 0.1604889710470726   # S08 35-element beam proxy, NOT verified Abaqus mode
SOURCE_ESM_SHA = "a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34"
OLD_LOW_CUT_HZ, OLD_HIGH_CUT_HZ = 0.04, 30.0
MAX_RESPONSE = 2_000_000

def sha(data):
    return hashlib.sha256(data).hexdigest()

def query_url(kind, instrument):
    params = dict(eventid=EVENT, network=NETWORK, station=STATION,
                  location="", instrument=instrument, indent="true")
    if kind == "details":
        params.update(processing="MP", ptarget="mp", group="all")
    elif kind != "snr":
        raise ValueError("UNKNOWN_SERVICE")
    return BASE + ("/waveform-details/1/query" if kind == "details"
                   else "/waveform-snr/1/query") + "?" + urllib.parse.urlencode(params)

def get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "wind-tower-S05-source-audit/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=22) as response:
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise ValueError("OVERSIZE_OFFICIAL_JSON")
            if not raw:
                raise ValueError("EMPTY_OFFICIAL_RESPONSE")
            return json.loads(raw), raw, int(response.status), None
    except urllib.error.HTTPError as exc:
        return None, None, exc.code, "HTTP_" + str(exc.code)
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return None, None, None, type(exc).__name__ + ":" + str(exc)[:160]

def validated_snr_at(data, frequency):
    """Log-frequency interpolation of official *reported* SNR values; no threshold."""
    if not isinstance(data, dict):
        raise ValueError("SNR_NOT_OBJECT")
    freqs = data.get("frequencies")
    if not isinstance(freqs, list) or len(freqs) < 2:
        raise ValueError("SNR_FREQUENCY_GRID")
    f = [float(x) for x in freqs]
    if any(not math.isfinite(x) or x <= 0 for x in f) or any(b <= a for a, b in zip(f, f[1:])):
        raise ValueError("SNR_INVALID_FREQUENCIES")
    if not (f[0] <= frequency <= f[-1]):
        raise ValueError("SNR_F1_OUT_OF_BAND")
    result = {}
    for name in ("U", "V", "W"):
        values = data.get(name)
        if not isinstance(values, list) or len(values) != len(f):
            raise ValueError("SNR_COMPONENT_LENGTH_" + name)
        v = [float(x) for x in values]
        if not all(math.isfinite(x) for x in v):
            raise ValueError("SNR_NONFINITE_" + name)
        import bisect
        i = min(max(bisect.bisect_left(f, frequency), 1), len(f)-1)
        t = math.log(frequency / f[i-1]) / math.log(f[i] / f[i-1])
        result[name] = {"reported_value_logfreq_interpolated": v[i-1] + t*(v[i]-v[i-1]),
                        "frequency_bracket_Hz": [f[i-1], f[i]],
                        "reported_bracket_values": [v[i-1], v[i]]}
    return result

def check_details(data, instrument):
    if not isinstance(data, dict):
        raise ValueError("DETAILS_NOT_OBJECT")
    event = data.get("event") or {}
    station = data.get("station") or {}
    orientation = data.get("asdf-orientation") or {}
    if event.get("event_id") != EVENT or station.get("station_code") != STATION:
        raise ValueError("OFFICIAL_EVENT_STATION_MISMATCH")
    if station.get("network_code") != NETWORK:
        raise ValueError("OFFICIAL_NETWORK_MISMATCH")
    if orientation.get("channel_code") != instrument:
        raise ValueError("OFFICIAL_INSTRUMENT_MISMATCH")
    filt = (data.get("settings") or {}).get("fourier_spectrum_filter") or {}
    low, high = filt.get("low_cut"), filt.get("high_cut")
    if not isinstance(low, list) or not isinstance(high, list) or len(low)!=3 or len(high)!=3:
        raise ValueError("OFFICIAL_FILTER_COMPONENTS_MISSING")
    low = [float(x) for x in low]; high = [float(x) for x in high]
    if any(not math.isfinite(x) or x<=0 for x in low+high):
        raise ValueError("OFFICIAL_FILTER_NONFINITE")
    return {"event": event, "station": station, "location": data.get("location"),
            "orientation": orientation, "instrument": data.get("asdf-instrument"),
            "quality": data.get("quality"), "workflow": data.get("workflow"),
            "processing_settings": data.get("settings"),
            "reported_low_cut_Hz": low, "reported_high_cut_Hz": high,
            "same_corners_as_archived_MP_DYNA":
                all(abs(x-OLD_LOW_CUT_HZ)<1e-9 for x in low)
                and all(abs(x-OLD_HIGH_CUT_HZ)<1e-9 for x in high)}

def self_test():
    f = [0.1, 0.2, 0.4]
    sample = {"frequencies": f, "U":[0,10,20], "V":[2,12,22], "W":[4,14,24]}
    v = validated_snr_at(sample, 0.2)
    assert v["U"]["reported_value_logfreq_interpolated"] == 10
    assert abs(validated_snr_at(sample, math.sqrt(.02))["U"]["reported_value_logfreq_interpolated"]-5)<1e-12
    for bad in ({"frequencies":[0.2,0.1],"U":[1,2],"V":[1,2],"W":[1,2]},
                {"frequencies":f,"U":[1],"V":[1,2,3],"W":[1,2,3]}):
        try: validated_snr_at(bad, 0.2)
        except ValueError: pass
        else: raise AssertionError("BAD_SNR_ACCEPTED")
    assert "eventid=IT-2012-0008" in query_url("details","HN")
    print("OFFICIAL_ESM_SNR_INTERPOLATION_AND_NEGATIVE_TEST_PASS")

def run(outdir):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    receipt = {
        "classification": "S05_OFFICIAL_ESM_PROCESSING_SNR_SOURCE_AUDIT_NOT_DESIGN_PASS",
        "UTC_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_reading_level": "Official ESM v3 JSON services; direct machine response if accessible",
        "SOURCE": {"event": EVENT, "network": NETWORK, "station": STATION,
                   "archived_processed_acceleration_csv_sha256": SOURCE_ESM_SHA,
                   "archived_MP_DYNA_filter_low_high_Hz": [OLD_LOW_CUT_HZ, OLD_HIGH_CUT_HZ]},
        "REF": "ESM v3 DOI 10.13127/esm.3; Boore & Bommer 2005 and Douglas & Boore 2011 (abstract-level, NOT filter acceptance rules)",
        "STANDARD": "No new authorized IEC/GB/NB clause read; NO standard PASS",
        "OFFICIAL": "https://esm-db.eu/esmws/waveform-details/1/ ; https://esm-db.eu/esmws/waveform-snr/1/",
        "RUN": "Python standard-library HTTP metadata fetch only; Abaqus E/WE=0",
        "FIG": None, "TAB": "this JSON receipt",
        "conditional_beam_proxy_f1_Hz": F1, "conditional_beam_proxy_T1_s": 1/F1,
        "f1_frequency_probe_Hz": [F1/2, F1, F1*2],
        "S05_PASS": False, "S08_PASS": False, "Abaqus_E_WE_RUN": 0,
        "assumptions": ["35-element linear beam f1 is a provisional screening period",
                        "ESM v3 current metadata may differ from archived MP ZIP; no silent substitution",
                        "reported SNR service quantity is not assigned unverified dB/linear units",
                        "no SNR acceptance threshold or design target spectrum is assumed"],
        "error_budget": {"frequency_interpolation": "log-frequency interpolation, not original frequency-bin observation",
                         "instrument_lowfreq_reliability": "NEED_METADATA_AND_INDEPENDENT_CRITERION",
                         "site_target_spectrum": "NOT_DEFINED"},
        "attempts": []}
    for instrument in ("HN", "HG"):
        entry = {"instrument": instrument}
        for kind in ("details", "snr"):
            url = query_url(kind, instrument)
            data, raw, status, err = get_json(url)
            rec = {"url": url, "HTTP_status": status, "error": err}
            if raw is not None:
                rec.update({"raw_response_sha256": sha(raw), "raw_bytes": len(raw)})
                (outdir / ("ESM_OFFICIAL_"+instrument+"_"+kind+".json")).write_bytes(raw)
                try:
                    if kind == "details":
                        rec["parsed"] = check_details(data, instrument)
                    else:
                        rec["reported_snr_at_provisional_f1"] = validated_snr_at(data, F1)
                        rec["reported_snr_at_half_f1"] = validated_snr_at(data, F1/2)
                        rec["reported_snr_at_twice_f1"] = validated_snr_at(data, F1*2)
                        rec["official_reported_cutoff_frequencies"] = data.get("cutoff_frequencies")
                        rec["official_signal_noise_windows"] = data.get("signal_noise_windows_fd")
                except (ValueError, TypeError, KeyError) as exc:
                    rec["parse_HOLD"] = type(exc).__name__+":"+str(exc)
            entry[kind] = rec
        receipt["attempts"].append(entry)
    valid = [a for a in receipt["attempts"]
             if a["details"].get("parsed") and a["snr"].get("reported_snr_at_provisional_f1")]
    receipt["source_level_status"] = (
        "OFFICIAL_PROCESSING_AND_SNR_RETRIEVED_NOT_DESIGN_PASS" if valid
        else "HOLD_OFFICIAL_STATION_DETAILS_OR_SNR_NOT_RETRIEVED")
    receipt["archive_vs_current_processing"] = [
        {"instrument":a["instrument"],
         "matches_archived_MP_DYNA_filter_corners":a["details"]["parsed"]["same_corners_as_archived_MP_DYNA"]}
        for a in valid]
    receipt["HOLD"] = ("No native Abaqus, no authorized site target, no accepted long-period reliability "
                       "criterion; if official v3 corners differ from archived source, require reprocessed "
                       "waveform identity before comparing. SNR values alone are not an engineering PASS.")
    output = outdir / "S05_ESM_IT2012_NVL_OFFICIAL_LOWFREQ_SOURCE_QC_20261102.json"
    output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False)+"\n")
    print("ESM_OFFICIAL_SOURCE_AUDIT",receipt["source_level_status"],
          [(a["instrument"],a["details"]["HTTP_status"],a["snr"]["HTTP_status"]) for a in receipt["attempts"]])
    print("RECEIPT",output)
    return receipt

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test: self_test()
    else: run(args.outdir)
